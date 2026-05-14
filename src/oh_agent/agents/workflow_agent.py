"""PDCA Workflow generation agent (PLAN + DO phases).

Generates statutory OH workflows structured around the PDCA framework,
requiring risk assessment confirmation before any workflow is produced.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI
from uuid_extensions import uuid7

from oh_agent.agents.guardrails import (
    SYSTEM_GUARDRAIL_PROMPT,
    append_disclaimers,
    check_output,
)
from oh_agent.config import Settings
from oh_agent.knowledge.retriever import KnowledgeRetriever, RetrievedChunk
from oh_agent.models.audit import AuditEntry, AuditEventType
from oh_agent.models.workflow import (
    GovernancePrompt,
    SurveillanceRequirement,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

_WORKFLOW_USER_TEMPLATE = """\
Generate a PDCA-structured statutory occupational health workflow.

IMPORTANT: The duty holder has confirmed completion of a suitable and \
sufficient risk assessment and that workers have been consulted.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Tasks: {tasks}
- Workforce size: {workforce_size}
- Multi-site: {multi_site} ({site_count} site(s))
- Delivery model: {delivery_model}
- Workforce characteristics: {workforce_chars}
- Existing surveillance: {existing_surveillance}

## Hazards
{hazards_block}

## Additional context
{additional_context}

## Retrieved knowledge (use as evidence basis)
{knowledge_context}

## Instructions
Generate a workflow structured by PDCA phases:

1. PLAN steps: Confirm risk profile, identify exposed workers
2. DO steps: Define statutory OH provision including:
   - Type of health surveillance required
   - Surveillance frequency based on exposure and guidance
   - Competence required to undertake and interpret surveillance
   - Referral and escalation pathways
   - Statutory retention periods for health records
3. CHECK steps: Audit and assurance activities
4. ACT steps: Review and continuous improvement triggers

For each step provide:
- order (integer)
- pdca_phase (one of: plan, do, check, act)
- component (one of: health_questionnaire, clinical_assessment, \
biological_monitoring, lung_function_test, audiometry, \
skin_assessment, vision_screening, fitness_for_task, \
health_education, referral, review_appointment, record_keeping)
- description
- responsible_role
- frequency
- regulatory_basis
- delegation_notes (if applicable)

Also generate surveillance_requirements array with:
- surveillance_type, description, frequency, competence_required, \
referral_pathway, retention_period, regulatory_basis

Include governance_prompts and sources_cited.

Respond ONLY with valid JSON:
{{
  "steps": [...],
  "surveillance_requirements": [...],
  "governance_prompts": [{{"prompt_text": "...", \
"applicable_roles": [...], "regulatory_reference": "..."}}],
  "sources_cited": [...]
}}"""


def _build_hazards_block(request: WorkflowRequest) -> str:
    lines: list[str] = []
    for i, h in enumerate(request.hazards, 1):
        lines.append(
            f"{i}. [{h.category.value}] {h.hazard_phrase} "
            f"(exposure: {h.exposure_level.value}, "
            f"freq: {h.exposure_frequency.value}, "
            f"duration: {h.exposure_duration.value})"
        )
        if h.substance_or_agent:
            lines.append(f"   Substance/agent: {h.substance_or_agent}")
        if h.potential_health_effects:
            lines.append(f"   Health effects: {h.potential_health_effects}")
        if h.existing_controls:
            lines.append(f"   Controls: {h.existing_controls}")
        if h.workplace_exposure_limit:
            lines.append(f"   WEL: {h.workplace_exposure_limit}")
    return "\n".join(lines)


def _build_knowledge_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(No knowledge-base documents available — use built-in regulatory knowledge.)"
    parts: list[str] = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {c.source_title} ({c.source_id})\n{c.text}\n")
    return "\n".join(parts)


def _parse_llm_response(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)  # type: ignore[no-any-return]


class WorkflowAgent:
    """Generates PDCA-structured OH workflows via LLM + RAG with guardrails."""

    def __init__(
        self,
        settings: Settings,
        retriever: KnowledgeRetriever | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        if client is not None:
            self._client = client
        else:
            from oh_agent.agents.llm_client import create_llm_client

            self._client = create_llm_client(settings)

    def generate(self, request: WorkflowRequest) -> tuple[WorkflowResponse, list[AuditEntry]]:
        request_id = str(uuid7())
        audit_entries: list[AuditEntry] = []

        # Validate risk assessment confirmation (PLAN gate)
        if not request.risk_assessment.risk_assessment_completed:
            raise ValueError(
                "Risk assessment must be confirmed before workflow generation. "
                "The duty holder must complete a suitable and sufficient risk assessment."
            )
        if not request.risk_assessment.workers_consulted:
            raise ValueError(
                "Worker consultation must be confirmed before workflow generation. "
                "Workers must be consulted on perceived hazards and control practicality."
            )

        audit_entries.append(
            AuditEntry(
                event_type=AuditEventType.RISK_ASSESSMENT_CONFIRMED,
                request_id=request_id,
                detail={
                    "organisation": request.organisation.name,
                    "risk_assessment_date": request.risk_assessment.risk_assessment_date,
                    "workers_consulted": request.risk_assessment.workers_consulted,
                },
            )
        )
        audit_entries.append(
            AuditEntry(
                event_type=AuditEventType.WORKFLOW_REQUESTED,
                request_id=request_id,
                detail={
                    "organisation": request.organisation.name,
                    "hazard_count": len(request.hazards),
                },
            )
        )

        chunks: list[RetrievedChunk] = []
        if self._retriever and self._retriever.collection_count > 0:
            query = f"{request.organisation.sector} {' '.join(h.hazard_phrase for h in request.hazards)}"
            chunks = self._retriever.query(query)
            audit_entries.append(
                AuditEntry(
                    event_type=AuditEventType.KNOWLEDGE_RETRIEVED,
                    request_id=request_id,
                    detail={"chunks_retrieved": len(chunks)},
                    sources_used=[c.source_id for c in chunks],
                )
            )

        org = request.organisation
        user_prompt = _WORKFLOW_USER_TEMPLATE.format(
            org_name=org.name,
            sector=org.sector,
            tasks=", ".join(org.tasks) if org.tasks else "Not specified",
            workforce_size=org.workforce_size or "Not specified",
            multi_site=org.multi_site,
            site_count=org.site_count,
            delivery_model=org.delivery_model.value,
            workforce_chars=org.workforce_characteristics or "Not specified",
            existing_surveillance=org.existing_surveillance or "None described",
            hazards_block=_build_hazards_block(request),
            additional_context=request.additional_context or "None",
            knowledge_context=_build_knowledge_context(chunks),
        )

        try:
            completion = self._client.chat.completions.create(
                model=self._settings.llm_model,
                temperature=self._settings.llm_temperature,
                max_tokens=self._settings.llm_max_tokens,
                messages=[
                    {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw_output = completion.choices[0].message.content or ""
        except Exception as exc:
            logger.exception("LLM call failed")
            audit_entries.append(
                AuditEntry(
                    event_type=AuditEventType.ERROR,
                    request_id=request_id,
                    detail={"error": str(exc)},
                )
            )
            raise

        guardrail_result = check_output(raw_output)
        if not guardrail_result.passed:
            audit_entries.append(
                AuditEntry(
                    event_type=AuditEventType.GUARDRAIL_TRIGGERED,
                    request_id=request_id,
                    detail={"violations": guardrail_result.violations},
                    guardrails_applied=["clinical_decision_check", "prohibited_phrase_check"],
                )
            )

        try:
            parsed = _parse_llm_response(raw_output)
        except (json.JSONDecodeError, KeyError) as exc:
            audit_entries.append(
                AuditEntry(
                    event_type=AuditEventType.ERROR,
                    request_id=request_id,
                    detail={"error": f"Failed to parse LLM response: {exc}", "raw_output": raw_output[:500]},
                )
            )
            raise ValueError(f"LLM returned unparseable response: {exc}") from exc

        steps = [WorkflowStep(**s) for s in parsed.get("steps", [])]
        surveillance = [SurveillanceRequirement(**sr) for sr in parsed.get("surveillance_requirements", [])]
        governance = [GovernancePrompt(**g) for g in parsed.get("governance_prompts", [])]
        sources = parsed.get("sources_cited", [])

        hazard_summary = "; ".join(h.hazard_phrase for h in request.hazards)

        response = WorkflowResponse(
            request_id=request_id,
            organisation_name=org.name,
            hazard_summary=hazard_summary,
            risk_assessment_confirmed=True,
            workers_consulted=True,
            steps=steps,
            surveillance_requirements=surveillance,
            governance_prompts=governance,
            sources_cited=sources,
            disclaimers=list(append_disclaimers("").replace("\n\n---\n**Important Notices:**\n", "").split("\n- ")),
            model_used=self._settings.llm_model,
            knowledge_chunks_used=len(chunks),
        )

        audit_entries.append(
            AuditEntry(
                event_type=AuditEventType.WORKFLOW_GENERATED,
                request_id=request_id,
                detail={"steps_count": len(steps), "surveillance_count": len(surveillance)},
                sources_used=sources,
                model_used=self._settings.llm_model,
            )
        )

        return response, audit_entries
