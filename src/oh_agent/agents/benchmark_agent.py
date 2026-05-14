"""Benchmarking and gap-analysis agent.

Compares an organisation's current OH practice against regulatory
minimum requirements and generates actionable findings.
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
    BenchmarkResult,
    ComplianceRating,
    GapAnalysis,
    GapItem,
)

logger = logging.getLogger(__name__)

_BENCHMARK_PROMPT = """\
Benchmark the following organisation's occupational health practice \
against UK regulatory minimum requirements.

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
Assess compliance across these areas: health surveillance programme, \
risk assessment integration, record keeping, competency and delegation, \
referral pathways, and worker communication.

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
occupational health arrangements against UK regulatory requirements.

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
For each gap found, provide:
- area: the compliance area
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


class BenchmarkAgent:
    """Assesses current OH practice against regulatory minimums."""

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
            hazards_block=_format_hazards(hazards),
            knowledge_context=_format_knowledge(chunks),
        )

        completion = self._client.chat.completions.create(
            model=self._settings.llm_model,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = completion.choices[0].message.content or ""
        check_output(raw)

        parsed = _parse_json(raw)
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
            hazards_block=_format_hazards(hazards),
            knowledge_context=_format_knowledge(chunks),
        )

        completion = self._client.chat.completions.create(
            model=self._settings.llm_model,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_GUARDRAIL_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = completion.choices[0].message.content or ""
        check_output(raw)

        parsed = _parse_json(raw)
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
