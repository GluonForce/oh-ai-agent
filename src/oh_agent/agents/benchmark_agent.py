"""PDCA CHECK, REVIEW, and ACT phase agents.

- ComplianceAuditAgent (CHECK): Evaluates statutory OH services
- TrendAnalysisAgent (REVIEW): Analyses anonymised surveillance data
- ImprovementPlanAgent (ACT): Generates improvement actions
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI
from uuid_extensions import uuid7

from oh_agent.agents.guardrails import SYSTEM_GUARDRAIL_PROMPT, check_output
from oh_agent.config import Settings
from oh_agent.knowledge.retriever import KnowledgeRetriever, RetrievedChunk
from oh_agent.models.audit import AuditEntry, AuditEventType
from oh_agent.models.hazard import HazardProfile
from oh_agent.models.organisation import OrganisationProfile
from oh_agent.models.workflow import (
    ComplianceAuditItem,
    ComplianceAuditResponse,
    ComplianceRating,
    ImprovementAction,
    ImprovementPlanResponse,
    TrendAnalysisResponse,
    TrendFinding,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_COMPLIANCE_AUDIT_PROMPT = """\
Perform a statutory compliance audit (CHECK phase) of the following \
organisation's occupational health arrangements against UK regulatory \
requirements.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Delivery model: {delivery_model}
- Existing surveillance: {existing_surveillance}

## Hazards
{hazards_block}

## Retrieved knowledge
{knowledge_context}

## Instructions
Assess compliance across these areas:
1. All exposed employees appropriately identified and included
2. Surveillance intervals are being met
3. Governance and oversight arrangements are in place
4. Competence of surveillance providers
5. Record keeping and retention
6. Referral and escalation pathways

For each area provide: area, question, current_state, required_state, \
rating (compliant/partially_compliant/non_compliant), recommendation, \
regulatory_reference.

Also set overall_rating and three booleans: \
employee_coverage_assessed, interval_adherence_assessed, governance_assessed.

Respond ONLY with valid JSON:
{{
  "audit_items": [...],
  "overall_rating": "...",
  "employee_coverage_assessed": true,
  "interval_adherence_assessed": true,
  "governance_assessed": true,
  "sources_cited": [...]
}}"""

_TREND_ANALYSIS_PROMPT = """\
Analyse the following anonymised surveillance data to identify trends \
(REVIEW phase) for occupational health risk management.

## Organisation
- Name: {org_name}
- Sector: {sector}

## Hazards
{hazards_block}

## Surveillance Summary
{surveillance_summary}

## Retrieved knowledge
{knowledge_context}

## Instructions
Identify:
1. Early signs of work-related illness
2. Patterns or clusters within departments or tasks
3. Indicators of control failure or emerging risk

For each finding provide: category (early_illness_sign / cluster / \
control_failure / emerging_risk), description, affected_area, \
severity (low/medium/high), recommended_action, regulatory_reference.

Also provide control_effectiveness_indicators.

Respond ONLY with valid JSON:
{{
  "findings": [...],
  "control_effectiveness_indicators": [...],
  "sources_cited": [...]
}}"""

_IMPROVEMENT_PLAN_PROMPT = """\
Generate an improvement action plan (ACT phase) based on the following \
surveillance findings for occupational health risk management.

## Organisation
- Name: {org_name}
- Sector: {sector}

## Hazards
{hazards_block}

## Surveillance Findings
{surveillance_findings}

## Retrieved knowledge
{knowledge_context}

## Instructions
Generate improvement actions that may include:
- Introduction or review of engineering controls
- Reduction of exposure duration or task redesign
- Review of PPE or RPE adequacy
- Modification of processes where health risk is identified
- Changes to surveillance frequency

For each action provide: action_type (engineering_control / \
exposure_reduction / ppe_review / process_modification / \
surveillance_change / training), description, priority \
(low/medium/high/critical), regulatory_basis, expected_outcome.

Also provide management_review_items covering:
- Ongoing legal compliance confirmation
- Adequacy of OH resources and competence
- Strategic occupational health objectives

Respond ONLY with valid JSON:
{{
  "actions": [...],
  "management_review_items": [...],
  "sources_cited": [...]
}}"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_hazards(hazards: list[HazardProfile]) -> str:
    return "\n".join(
        f"- [{h.category.value}] {h.hazard_phrase} "
        f"(exposure: {h.exposure_level.value}, freq: {h.exposure_frequency.value})"
        for h in hazards
    )


def _format_knowledge(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(No knowledge-base documents available.)"
    return "\n".join(f"[{i}] {c.source_title}: {c.text}" for i, c in enumerate(chunks, 1))


def _parse_json(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)  # type: ignore[no-any-return]


def _call_llm(
    client: OpenAI,
    settings: Settings,
    prompt: str,
) -> str:
    completion = client.chat.completions.create(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    raw = completion.choices[0].message.content or ""
    check_output(raw)
    return raw


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


class ComplianceAuditAgent:
    """CHECK phase: evaluates statutory OH compliance."""

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

    def _retrieve(self, query: str) -> list[RetrievedChunk]:
        if self._retriever and self._retriever.collection_count > 0:
            return self._retriever.query(query)
        return []

    def audit(
        self,
        organisation: OrganisationProfile,
        hazards: list[HazardProfile],
    ) -> tuple[ComplianceAuditResponse, list[AuditEntry]]:
        request_id = str(uuid7())
        audit: list[AuditEntry] = []

        audit.append(
            AuditEntry(
                event_type=AuditEventType.COMPLIANCE_AUDIT_REQUESTED,
                request_id=request_id,
                detail={"organisation": organisation.name},
            )
        )

        chunks = self._retrieve(f"{organisation.sector} statutory compliance audit")

        prompt = _COMPLIANCE_AUDIT_PROMPT.format(
            org_name=organisation.name,
            sector=organisation.sector,
            delivery_model=organisation.delivery_model.value,
            existing_surveillance=organisation.existing_surveillance or "None described",
            hazards_block=_format_hazards(hazards),
            knowledge_context=_format_knowledge(chunks),
        )

        raw = _call_llm(self._client, self._settings, prompt)
        parsed = _parse_json(raw)

        items = [ComplianceAuditItem(**item) for item in parsed.get("audit_items", [])]
        overall = parsed.get("overall_rating", "not_assessed")

        result = ComplianceAuditResponse(
            request_id=request_id,
            organisation_name=organisation.name,
            audit_items=items,
            overall_rating=ComplianceRating(overall),
            employee_coverage_assessed=parsed.get("employee_coverage_assessed", False),
            interval_adherence_assessed=parsed.get("interval_adherence_assessed", False),
            governance_assessed=parsed.get("governance_assessed", False),
            sources_cited=parsed.get("sources_cited", []),
            model_used=self._settings.llm_model,
        )

        audit.append(
            AuditEntry(
                event_type=AuditEventType.COMPLIANCE_AUDIT_GENERATED,
                request_id=request_id,
                detail={"items_count": len(items), "overall_rating": overall},
                sources_used=result.sources_cited,
                model_used=self._settings.llm_model,
            )
        )
        return result, audit


class TrendAnalysisAgent:
    """REVIEW phase: analyses anonymised surveillance data for trends."""

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

    def _retrieve(self, query: str) -> list[RetrievedChunk]:
        if self._retriever and self._retriever.collection_count > 0:
            return self._retriever.query(query)
        return []

    def analyse(
        self,
        organisation: OrganisationProfile,
        hazards: list[HazardProfile],
        surveillance_summary: str,
    ) -> tuple[TrendAnalysisResponse, list[AuditEntry]]:
        request_id = str(uuid7())
        audit: list[AuditEntry] = []

        audit.append(
            AuditEntry(
                event_type=AuditEventType.TREND_ANALYSIS_REQUESTED,
                request_id=request_id,
                detail={"organisation": organisation.name},
            )
        )

        chunks = self._retrieve(f"{organisation.sector} surveillance trend analysis")

        prompt = _TREND_ANALYSIS_PROMPT.format(
            org_name=organisation.name,
            sector=organisation.sector,
            hazards_block=_format_hazards(hazards),
            surveillance_summary=surveillance_summary,
            knowledge_context=_format_knowledge(chunks),
        )

        raw = _call_llm(self._client, self._settings, prompt)
        parsed = _parse_json(raw)

        findings = [TrendFinding(**f) for f in parsed.get("findings", [])]

        result = TrendAnalysisResponse(
            request_id=request_id,
            organisation_name=organisation.name,
            findings=findings,
            control_effectiveness_indicators=parsed.get("control_effectiveness_indicators", []),
            sources_cited=parsed.get("sources_cited", []),
            model_used=self._settings.llm_model,
        )

        audit.append(
            AuditEntry(
                event_type=AuditEventType.TREND_ANALYSIS_GENERATED,
                request_id=request_id,
                detail={"findings_count": len(findings)},
                sources_used=result.sources_cited,
                model_used=self._settings.llm_model,
            )
        )
        return result, audit


class ImprovementPlanAgent:
    """ACT phase: generates improvement actions from surveillance findings."""

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

    def _retrieve(self, query: str) -> list[RetrievedChunk]:
        if self._retriever and self._retriever.collection_count > 0:
            return self._retriever.query(query)
        return []

    def plan(
        self,
        organisation: OrganisationProfile,
        hazards: list[HazardProfile],
        surveillance_findings: str,
    ) -> tuple[ImprovementPlanResponse, list[AuditEntry]]:
        request_id = str(uuid7())
        audit: list[AuditEntry] = []

        audit.append(
            AuditEntry(
                event_type=AuditEventType.IMPROVEMENT_PLAN_REQUESTED,
                request_id=request_id,
                detail={"organisation": organisation.name},
            )
        )

        chunks = self._retrieve(f"{organisation.sector} improvement actions control measures")

        prompt = _IMPROVEMENT_PLAN_PROMPT.format(
            org_name=organisation.name,
            sector=organisation.sector,
            hazards_block=_format_hazards(hazards),
            surveillance_findings=surveillance_findings,
            knowledge_context=_format_knowledge(chunks),
        )

        raw = _call_llm(self._client, self._settings, prompt)
        parsed = _parse_json(raw)

        actions = [ImprovementAction(**a) for a in parsed.get("actions", [])]

        result = ImprovementPlanResponse(
            request_id=request_id,
            organisation_name=organisation.name,
            actions=actions,
            management_review_items=parsed.get("management_review_items", []),
            sources_cited=parsed.get("sources_cited", []),
            model_used=self._settings.llm_model,
        )

        audit.append(
            AuditEntry(
                event_type=AuditEventType.IMPROVEMENT_PLAN_GENERATED,
                request_id=request_id,
                detail={"actions_count": len(actions)},
                sources_used=result.sources_cited,
                model_used=self._settings.llm_model,
            )
        )
        return result, audit
