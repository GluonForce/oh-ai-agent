"""Workflow generation agent — PDCA-aligned.

Generates hazard-specific, risk-profiled, evidence-based OH workflows
structured around Plan-Do-Check-Act, by combining organisation profile
+ hazard data with knowledge-base retrieval and LLM reasoning, then
applying compliance guardrails.
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
    AssuranceCheckItem,
    GovernancePrompt,
    ImprovementAction,
    RiskProfileSummary,
    SurveillanceProvision,
    TrendInsight,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

_WORKFLOW_USER_TEMPLATE = """\
Generate a PDCA-structured (Plan-Do-Check-Act) occupational health \
workflow for the following organisation and hazard profile.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Tasks: {tasks}
- Workforce size: {workforce_size}
- Multi-site: {multi_site} ({site_count} site(s))
- Delivery model: {delivery_model}
- Workforce characteristics: {workforce_chars}
- Existing surveillance: {existing_surveillance}
- Risk assessment confirmed: {risk_assessment_confirmed}
- Workers consulted: {workers_consulted}

## Hazards
{hazards_block}

## Additional context
{additional_context}

## Retrieved knowledge (use these as evidence basis)
{knowledge_context}

## Instructions — PDCA Framework
Generate a structured workflow following Plan-Do-Check-Act. Respond \
ONLY with valid JSON matching this schema:

{{
  "risk_profile": {{
    "hazard_summary": "...",
    "risk_assessment_confirmed": true/false,
    "workers_consulted": true/false,
    "key_risks": ["..."],
    "regulatory_drivers": ["e.g. COSHH Reg 11", "Control of Noise at Work Regs 2005"]
  }},
  "surveillance_provisions": [{{
    "surveillance_type": "audiometry|spirometry|skin_check|havs_questionnaire|\
biological_monitoring|vision_screening|health_questionnaire|clinical_examination|\
fitness_assessment",
    "description": "...",
    "frequency": "e.g. baseline + annual",
    "competence_required": "e.g. qualified OHN with audiometry training",
    "referral_pathway": "e.g. refer to OHP if abnormal findings",
    "retention_period": "e.g. 40 years (COSHH)",
    "regulatory_basis": "specific regulation/guidance",
    "delegation_notes": "if applicable"
  }}],
  "steps": [{{
    "order": 1,
    "component": "health_questionnaire|clinical_assessment|\
biological_monitoring|lung_function_test|audiometry|skin_assessment|\
vision_screening|fitness_for_task|health_education|referral|\
review_appointment|record_keeping",
    "description": "...",
    "responsible_role": "e.g. OHP, OHN, OH Technician",
    "frequency": "e.g. baseline + annual",
    "regulatory_basis": "specific regulation/guidance",
    "delegation_notes": "if applicable"
  }}],
  "assurance_checks": [{{
    "area": "e.g. Employee coverage",
    "question": "Have all exposed employees been identified and included?",
    "status": "not_assessed",
    "finding": null,
    "recommendation": "...",
    "regulatory_reference": "..."
  }}],
  "trend_insights": [{{
    "area": "...",
    "observation": "...",
    "implication": "...",
    "recommended_action": "..."
  }}],
  "improvement_actions": [{{
    "area": "...",
    "action": "...",
    "rationale": "...",
    "priority": "high|medium|low",
    "regulatory_reference": "..."
  }}],
  "governance_prompts": [{{"prompt_text": "...", "applicable_roles": [...], "regulatory_reference": "..."}}],
  "sources_cited": [...]
}}"""


def _build_hazards_block(request: WorkflowRequest) -> str:
    lines: list[str] = []
    for i, h in enumerate(request.hazards, 1):
        lines.append(
            f"{i}. [{h.category.value}] {h.hazard_phrase} "
            f"(exposure: {h.exposure_level.value}, frequency: {h.exposure_frequency.value}, "
            f"duration: {h.exposure_duration.value})"
        )
        if h.substance_or_agent:
            lines.append(f"   Substance/agent: {h.substance_or_agent}")
        if h.workplace_exposure_limit:
            lines.append(f"   WEL: {h.workplace_exposure_limit}")
        if h.potential_health_effects:
            lines.append(f"   Potential health effects: {h.potential_health_effects}")
        if h.existing_controls:
            lines.append(f"   Existing controls: {h.existing_controls}")
    return "\n".join(lines)


def _build_knowledge_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(No knowledge-base documents available — use built-in regulatory knowledge.)"
    parts: list[str] = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {c.source_title} ({c.source_id})\n{c.text}\n")
    return "\n".join(parts)


def _parse_llm_response(raw: str) -> dict[str, Any]:
    """Extract JSON from an LLM response, tolerating markdown fences."""
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
        """Generate a PDCA workflow and return it with its audit trail."""
        request_id = str(uuid7())
        audit_entries: list[AuditEntry] = []

        audit_entries.append(
            AuditEntry(
                event_type=AuditEventType.WORKFLOW_REQUESTED,
                request_id=request_id,
                detail={"organisation": request.organisation.name, "hazard_count": len(request.hazards)},
            )
        )

        # Retrieve relevant knowledge
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
            risk_assessment_confirmed=org.risk_assessment_confirmed,
            workers_consulted=org.workers_consulted,
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

        # Guardrail check
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
            logger.warning("Guardrails triggered for request %s: %s", request_id, guardrail_result.violations)

        # Parse structured response
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

        # PLAN
        risk_profile_data = parsed.get("risk_profile")
        risk_profile = RiskProfileSummary(**risk_profile_data) if risk_profile_data else None

        # DO
        surveillance = [SurveillanceProvision(**s) for s in parsed.get("surveillance_provisions", [])]
        steps = [WorkflowStep(**s) for s in parsed.get("steps", [])]
        governance = [GovernancePrompt(**g) for g in parsed.get("governance_prompts", [])]

        # CHECK
        assurance = [AssuranceCheckItem(**a) for a in parsed.get("assurance_checks", [])]
        trends = [TrendInsight(**t) for t in parsed.get("trend_insights", [])]

        # ACT
        improvements = [ImprovementAction(**ia) for ia in parsed.get("improvement_actions", [])]

        sources = parsed.get("sources_cited", [])
        hazard_summary = "; ".join(h.hazard_phrase for h in request.hazards)

        response = WorkflowResponse(
            request_id=request_id,
            organisation_name=org.name,
            hazard_summary=hazard_summary,
            risk_profile=risk_profile,
            surveillance_provisions=surveillance,
            steps=steps,
            assurance_checks=assurance,
            trend_insights=trends,
            improvement_actions=improvements,
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
                detail={
                    "steps_count": len(steps),
                    "surveillance_provisions_count": len(surveillance),
                    "assurance_checks_count": len(assurance),
                    "improvement_actions_count": len(improvements),
                    "sources_cited": sources,
                },
                sources_used=sources,
                model_used=self._settings.llm_model,
                guardrails_applied=(guardrail_result.violations if not guardrail_result.passed else []),
            )
        )

        return response, audit_entries
