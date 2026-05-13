"""Workflow generation agent.

Generates hazard-specific, risk-profiled, evidence-based OH workflows
by combining organisation profile + hazard data with knowledge-base
retrieval and LLM reasoning, then applying compliance guardrails.
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
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

_WORKFLOW_USER_TEMPLATE = """\
Generate a compliant occupational health workflow for the following \
organisation and hazard profile.

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

## Retrieved knowledge (use these as evidence basis)
{knowledge_context}

## Instructions
1. Generate a step-by-step workflow with each step containing:
   - order (integer)
   - component (one of: health_questionnaire, clinical_assessment, \
biological_monitoring, lung_function_test, audiometry, \
skin_assessment, vision_screening, fitness_for_task, \
health_education, referral, review_appointment, record_keeping)
   - description
   - responsible_role (e.g. OHP, OHN, OH Technician)
   - frequency (e.g. baseline + annual)
   - regulatory_basis (specific regulation/guidance)
   - delegation_notes (if applicable)
2. Include governance prompts for safe delegation.
3. Cite all sources used.
4. Respond ONLY with valid JSON matching this schema:
{{
  "steps": [...],
  "governance_prompts": [{{"prompt_text": "...", "applicable_roles": [...], "regulatory_reference": "..."}}],
  "sources_cited": [...]
}}"""


def _build_hazards_block(request: WorkflowRequest) -> str:
    lines: list[str] = []
    for i, h in enumerate(request.hazards, 1):
        lines.append(
            f"{i}. [{h.category.value}] {h.hazard_phrase} "
            f"(exposure: {h.exposure_level.value}, frequency: {h.exposure_frequency.value})"
        )
        if h.substance_or_agent:
            lines.append(f"   Substance/agent: {h.substance_or_agent}")
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
    """Extract JSON from an LLM response, tolerating markdown fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)  # type: ignore[no-any-return]


class WorkflowAgent:
    """Generates OH workflows via LLM + RAG with guardrails."""

    def __init__(
        self,
        settings: Settings,
        retriever: KnowledgeRetriever | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._client = client or OpenAI(api_key=settings.openai_api_key or "not-set")

    def generate(self, request: WorkflowRequest) -> tuple[WorkflowResponse, list[AuditEntry]]:
        """Generate a workflow and return it with its audit trail."""
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

        steps = [WorkflowStep(**s) for s in parsed.get("steps", [])]
        governance = [GovernancePrompt(**g) for g in parsed.get("governance_prompts", [])]
        sources = parsed.get("sources_cited", [])

        hazard_summary = "; ".join(h.hazard_phrase for h in request.hazards)

        response = WorkflowResponse(
            request_id=request_id,
            organisation_name=org.name,
            hazard_summary=hazard_summary,
            steps=steps,
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
                detail={"steps_count": len(steps), "sources_cited": sources},
                sources_used=sources,
                model_used=self._settings.llm_model,
                guardrails_applied=(guardrail_result.violations if not guardrail_result.passed else []),
            )
        )

        return response, audit_entries
