"""Benchmarking and gap-analysis agent — PDCA CHECK phase.

Compares an organisation's current OH practice against regulatory
minimum requirements using the Plan-Do-Check-Act framework and
generates actionable findings.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from uuid_extensions import uuid7

from oh_agent.agents.llm_client import LLMClient, create_llm_client

from oh_agent.agents.guardrails import (
    GuardrailViolation,
    SYSTEM_GUARDRAIL_PROMPT,
    check_parsed_content,
)
from oh_agent.config import Settings
from oh_agent.knowledge.retriever import KnowledgeRetriever, RetrievedChunk
from oh_agent.models.audit import AuditEntry, AuditEventType
from oh_agent.models.hazard import HazardProfile
from oh_agent.models.organisation import OrganisationProfile
from oh_agent.models.workflow import (
    AssuranceCheckItem,
    BenchmarkResult,
    ComplianceAuditResponse,
    ComplianceRating,
    GapAnalysis,
    GapItem,
    ImprovementAction,
    ImprovementPlanResponse,
    TrendAnalysisResponse,
    TrendInsight,
)

logger = logging.getLogger(__name__)

_BENCHMARK_PROMPT = """\
Benchmark the following organisation's occupational health practice \
against UK regulatory minimum requirements using a PDCA framework.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Delivery model: {delivery_model}
- Existing surveillance: {existing_surveillance}
- Risk assessment confirmed: {risk_assessment_confirmed}
- Workers consulted: {workers_consulted}

## Hazards
{hazards_block}

## Retrieved knowledge
{knowledge_context}

## Instructions
Assess compliance across these areas, aligned to PDCA phases:
- PLAN: risk assessment adequacy, risk profiling, worker consultation
- DO: health surveillance programme, surveillance frequency, competence \
and delegation, referral pathways, record keeping and retention periods
- CHECK: employee coverage, interval compliance, governance and oversight, \
trend analysis capability
- ACT: control measure review processes, management review, training

Respond ONLY with valid JSON:
{{
  "areas_assessed": ["..."],
  "compliant_areas": ["..."],
  "non_compliant_areas": ["..."],
  "recommendations": ["..."],
  "sources_cited": ["..."]
}}"""

_GAP_ANALYSIS_PROMPT = """\
Perform a structured gap analysis of the following organisation's \
occupational health arrangements against UK regulatory requirements, \
using a PDCA framework.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Delivery model: {delivery_model}
- Existing surveillance: {existing_surveillance}
- Risk assessment confirmed: {risk_assessment_confirmed}
- Workers consulted: {workers_consulted}

## Hazards
{hazards_block}

## Retrieved knowledge
{knowledge_context}

## Instructions
For each gap found, provide:
- area: the compliance area (prefix with PDCA phase: PLAN/DO/CHECK/ACT)
- current_state: what the organisation currently does
- required_state: what UK regulations require
- rating: one of "compliant", "partially_compliant", "non_compliant"
- recommendation: actionable improvement step
- regulatory_reference: specific regulation or guidance

Also provide an overall_rating.

Respond ONLY with valid JSON:
{{
  "gaps": [{{
    "area": "...",
    "current_state": "...",
    "required_state": "...",
    "rating": "...",
    "recommendation": "...",
    "regulatory_reference": "..."
  }}],
  "overall_rating": "...",
  "sources_cited": ["..."]
}}"""


def _format_hazards(hazards: list[HazardProfile]) -> str:
    lines: list[str] = []
    for h in hazards:
        line = (
            f"- [{h.category.value}] {h.hazard_phrase} "
            f"(exposure: {h.exposure_level.value}, freq: {h.exposure_frequency.value}, "
            f"duration: {h.exposure_duration.value})"
        )
        lines.append(line)
        if h.potential_health_effects:
            lines.append(f"  Health effects: {h.potential_health_effects}")
        if h.existing_controls:
            lines.append(f"  Controls: {h.existing_controls}")
    return "\n".join(lines)


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


class BenchmarkAgent:
    """Assesses current OH practice against regulatory minimums using PDCA."""

    def __init__(
        self,
        settings: Settings,
        retriever: KnowledgeRetriever | None = None,
        client: LLMClient | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._client = client if client is not None else create_llm_client(settings)

    def _retrieve(self, query: str) -> list[RetrievedChunk]:
        if self._retriever and self._retriever.collection_count > 0:
            return self._retriever.query(query)
        return []

    def benchmark(
        self,
        organisation: OrganisationProfile,
        hazards: list[HazardProfile],
    ) -> tuple[BenchmarkResult, list[AuditEntry]]:
        request_id = str(uuid7())
        audit: list[AuditEntry] = []

        audit.append(
            AuditEntry(
                event_type=AuditEventType.BENCHMARK_REQUESTED,
                request_id=request_id,
                detail={"organisation": organisation.name},
            )
        )

        chunks = self._retrieve(f"{organisation.sector} health surveillance benchmark")

        prompt = _BENCHMARK_PROMPT.format(
            org_name=organisation.name,
            sector=organisation.sector,
            delivery_model=organisation.delivery_model.value,
            existing_surveillance=organisation.existing_surveillance or "None described",
            risk_assessment_confirmed=organisation.risk_assessment_confirmed,
            workers_consulted=organisation.workers_consulted,
            hazards_block=_format_hazards(hazards),
            knowledge_context=_format_knowledge(chunks),
        )

        raw = self._client.complete(
            [
                {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        parsed = _parse_json(raw)
        guardrail_result = check_parsed_content(parsed)
        if not guardrail_result.passed:
            raise GuardrailViolation(guardrail_result.violations)
        result = BenchmarkResult(
            request_id=request_id,
            organisation_name=organisation.name,
            areas_assessed=parsed.get("areas_assessed", []),
            compliant_areas=parsed.get("compliant_areas", []),
            non_compliant_areas=parsed.get("non_compliant_areas", []),
            recommendations=parsed.get("recommendations", []),
            sources_cited=parsed.get("sources_cited", []),
        )

        audit.append(
            AuditEntry(
                event_type=AuditEventType.BENCHMARK_GENERATED,
                request_id=request_id,
                detail={"compliant": len(result.compliant_areas), "non_compliant": len(result.non_compliant_areas)},
                sources_used=result.sources_cited,
                model_used=self._settings.llm_model,
            )
        )
        return result, audit

    def gap_analysis(
        self,
        organisation: OrganisationProfile,
        hazards: list[HazardProfile],
    ) -> tuple[GapAnalysis, list[AuditEntry]]:
        request_id = str(uuid7())
        audit: list[AuditEntry] = []

        audit.append(
            AuditEntry(
                event_type=AuditEventType.GAP_ANALYSIS_REQUESTED,
                request_id=request_id,
                detail={"organisation": organisation.name},
            )
        )

        chunks = self._retrieve(f"{organisation.sector} gap analysis regulatory compliance")

        prompt = _GAP_ANALYSIS_PROMPT.format(
            org_name=organisation.name,
            sector=organisation.sector,
            delivery_model=organisation.delivery_model.value,
            existing_surveillance=organisation.existing_surveillance or "None described",
            risk_assessment_confirmed=organisation.risk_assessment_confirmed,
            workers_consulted=organisation.workers_consulted,
            hazards_block=_format_hazards(hazards),
            knowledge_context=_format_knowledge(chunks),
        )

        raw = self._client.complete(
            [
                {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        parsed = _parse_json(raw)
        guardrail_result = check_parsed_content(parsed)
        if not guardrail_result.passed:
            raise GuardrailViolation(guardrail_result.violations)
        gaps = [GapItem(**g) for g in parsed.get("gaps", [])]
        overall = parsed.get("overall_rating", "not_assessed")

        result = GapAnalysis(
            request_id=request_id,
            organisation_name=organisation.name,
            gaps=gaps,
            overall_rating=ComplianceRating(overall),
            sources_cited=parsed.get("sources_cited", []),
        )

        audit.append(
            AuditEntry(
                event_type=AuditEventType.GAP_ANALYSIS_GENERATED,
                request_id=request_id,
                detail={"gaps_found": len(gaps), "overall_rating": overall},
                sources_used=result.sources_cited,
                model_used=self._settings.llm_model,
            )
        )
        return result, audit


# ---------------------------------------------------------------------------
# CHECK — Compliance Audit Agent
# ---------------------------------------------------------------------------

_COMPLIANCE_AUDIT_PROMPT = """\
Conduct a structured compliance audit of the following organisation's \
occupational health arrangements against UK statutory requirements, \
using a PDCA framework.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Delivery model: {delivery_model}
- Existing surveillance: {existing_surveillance}
- Risk assessment confirmed: {risk_assessment_confirmed}
- Workers consulted: {workers_consulted}

## Hazards
{hazards_block}

## Retrieved knowledge
{knowledge_context}

## Instructions
Assess compliance across these areas:
1. Employee coverage — are all exposed employees identified and included?
2. Interval adherence — are surveillance intervals meeting regulatory minimums?
3. Governance — is there adequate oversight, delegation, and competence assurance?

For each audit item, provide:
- area: the compliance area
- question: the audit question
- status: one of "compliant", "partially_compliant", "non_compliant", "not_assessed"
- finding: what was found
- recommendation: actionable improvement step
- regulatory_reference: specific regulation or guidance

Also provide an overall_rating and boolean flags for each assessment area.

Respond ONLY with valid JSON:
{{
  "audit_items": [{{
    "area": "...",
    "question": "...",
    "status": "...",
    "finding": "...",
    "recommendation": "...",
    "regulatory_reference": "..."
  }}],
  "overall_rating": "compliant|partially_compliant|non_compliant|not_assessed",
  "employee_coverage_assessed": true,
  "interval_adherence_assessed": true,
  "governance_assessed": true,
  "sources_cited": ["..."]
}}"""


class ComplianceAuditAgent:
    """Evaluates statutory OH compliance (CHECK phase)."""

    def __init__(
        self,
        settings: Settings,
        retriever: KnowledgeRetriever | None = None,
        client: LLMClient | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._client = client if client is not None else create_llm_client(settings)

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

        chunks = self._retrieve(f"{organisation.sector} compliance audit statutory requirements")

        prompt = _COMPLIANCE_AUDIT_PROMPT.format(
            org_name=organisation.name,
            sector=organisation.sector,
            delivery_model=organisation.delivery_model.value,
            existing_surveillance=organisation.existing_surveillance or "None described",
            risk_assessment_confirmed=organisation.risk_assessment_confirmed,
            workers_consulted=organisation.workers_consulted,
            hazards_block=_format_hazards(hazards),
            knowledge_context=_format_knowledge(chunks),
        )

        raw = self._client.complete(
            [
                {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        parsed = _parse_json(raw)
        guardrail_result = check_parsed_content(parsed)
        if not guardrail_result.passed:
            raise GuardrailViolation(guardrail_result.violations)
        audit_items = [AssuranceCheckItem(**item) for item in parsed.get("audit_items", [])]
        overall = parsed.get("overall_rating", "not_assessed")

        result = ComplianceAuditResponse(
            request_id=request_id,
            organisation_name=organisation.name,
            audit_items=audit_items,
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
                detail={"audit_items_count": len(audit_items), "overall_rating": overall},
                sources_used=result.sources_cited,
                model_used=self._settings.llm_model,
            )
        )
        return result, audit


# ---------------------------------------------------------------------------
# REVIEW — Trend Analysis Agent
# ---------------------------------------------------------------------------

_TREND_ANALYSIS_PROMPT = """\
Analyse the following anonymised surveillance data for an organisation's \
occupational health programme. Identify trends, patterns, and implications \
using a PDCA framework.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Delivery model: {delivery_model}
- Existing surveillance: {existing_surveillance}

## Hazards
{hazards_block}

## Surveillance data summary
{surveillance_summary}

## Retrieved knowledge
{knowledge_context}

## Instructions
For each finding, provide:
- area: the surveillance/health area
- observation: what the data shows
- implication: clinical or regulatory significance
- recommended_action: suggested follow-up

Also provide control effectiveness indicators.

Respond ONLY with valid JSON:
{{
  "findings": [{{
    "area": "...",
    "observation": "...",
    "implication": "...",
    "recommended_action": "..."
  }}],
  "control_effectiveness_indicators": ["..."],
  "sources_cited": ["..."]
}}"""


class TrendAnalysisAgent:
    """Analyses anonymised surveillance data for trends (REVIEW phase)."""

    def __init__(
        self,
        settings: Settings,
        retriever: KnowledgeRetriever | None = None,
        client: LLMClient | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._client = client if client is not None else create_llm_client(settings)

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
            delivery_model=organisation.delivery_model.value,
            existing_surveillance=organisation.existing_surveillance or "None described",
            hazards_block=_format_hazards(hazards),
            surveillance_summary=surveillance_summary,
            knowledge_context=_format_knowledge(chunks),
        )

        raw = self._client.complete(
            [
                {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        parsed = _parse_json(raw)
        guardrail_result = check_parsed_content(parsed)
        if not guardrail_result.passed:
            raise GuardrailViolation(guardrail_result.violations)
        findings = [TrendInsight(**f) for f in parsed.get("findings", [])]

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


# ---------------------------------------------------------------------------
# ACT — Improvement Plan Agent
# ---------------------------------------------------------------------------

_IMPROVEMENT_PLAN_PROMPT = """\
Generate improvement actions based on the following surveillance findings \
for an organisation's occupational health programme, using a PDCA framework.

## Organisation
- Name: {org_name}
- Sector: {sector}
- Delivery model: {delivery_model}
- Existing surveillance: {existing_surveillance}

## Hazards
{hazards_block}

## Surveillance findings
{surveillance_findings}

## Retrieved knowledge
{knowledge_context}

## Instructions
For each improvement action, provide:
- area: the area requiring improvement
- action: specific actionable step
- rationale: evidence-based justification
- priority: high / medium / low
- regulatory_reference: relevant regulation or guidance

Also provide management review items.

Respond ONLY with valid JSON:
{{
  "actions": [{{
    "area": "...",
    "action": "...",
    "rationale": "...",
    "priority": "high|medium|low",
    "regulatory_reference": "..."
  }}],
  "management_review_items": ["..."],
  "sources_cited": ["..."]
}}"""


class ImprovementPlanAgent:
    """Generates improvement actions from surveillance findings (ACT phase)."""

    def __init__(
        self,
        settings: Settings,
        retriever: KnowledgeRetriever | None = None,
        client: LLMClient | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._client = client if client is not None else create_llm_client(settings)

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

        chunks = self._retrieve(f"{organisation.sector} improvement plan continuous improvement")

        prompt = _IMPROVEMENT_PLAN_PROMPT.format(
            org_name=organisation.name,
            sector=organisation.sector,
            delivery_model=organisation.delivery_model.value,
            existing_surveillance=organisation.existing_surveillance or "None described",
            hazards_block=_format_hazards(hazards),
            surveillance_findings=surveillance_findings,
            knowledge_context=_format_knowledge(chunks),
        )

        raw = self._client.complete(
            [
                {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        parsed = _parse_json(raw)
        guardrail_result = check_parsed_content(parsed)
        if not guardrail_result.passed:
            raise GuardrailViolation(guardrail_result.violations)
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
