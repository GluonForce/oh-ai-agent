"""Authoritative source registry.

Only sources that meet the evidence-base criteria defined in the spec
are permitted.  Every retrieved chunk carries its source provenance.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    HSE_GUIDANCE = "hse_guidance"
    ACOP = "acop"
    REGULATORY_FRAMEWORK = "regulatory_framework"
    PEER_REVIEWED = "peer_reviewed"
    STRUCTURED_REVIEW = "structured_review"
    VALIDATED_WORKFLOW = "validated_workflow"


class KnowledgeSource(BaseModel):
    """Metadata for an authoritative source document."""

    id: str
    title: str = Field(..., min_length=1)
    source_type: SourceType
    url: str | None = None
    publication_date: str | None = None
    authority: str = Field(
        ...,
        description="Publishing body (e.g. 'HSE', 'Faculty of Occupational Medicine').",
    )
    version: str | None = None
    description: str | None = None


# Pre-registered authoritative sources from the spec
AUTHORITATIVE_SOURCES: list[KnowledgeSource] = [
    KnowledgeSource(
        id="hse-hs-g-61",
        title="Health Surveillance at Work (HSG61)",
        source_type=SourceType.HSE_GUIDANCE,
        authority="HSE",
        url="https://www.hse.gov.uk/pubns/books/hsg61.htm",
        description="Core HSE guidance on health surveillance requirements.",
    ),
    KnowledgeSource(
        id="hse-coshh-acop-l5",
        title="Workplace Exposure Limits (EH40)",
        source_type=SourceType.ACOP,
        authority="HSE",
        url="https://www.hse.gov.uk/pubns/books/eh40.htm",
        description="Approved workplace exposure limits for substances hazardous to health.",
    ),
    KnowledgeSource(
        id="hse-coshh-essentials",
        title="COSHH Essentials",
        source_type=SourceType.HSE_GUIDANCE,
        authority="HSE",
        url="https://www.hse.gov.uk/coshh/essentials/",
        description="Practical guidance on controlling exposure to hazardous substances.",
    ),
    KnowledgeSource(
        id="hse-skin-at-work",
        title="Skin at Work (INDG233)",
        source_type=SourceType.HSE_GUIDANCE,
        authority="HSE",
        url="https://www.hse.gov.uk/skin/",
        description="Guidance on preventing occupational skin disease.",
    ),
    KnowledgeSource(
        id="hse-noise-at-work",
        title="Controlling Noise at Work (L108)",
        source_type=SourceType.ACOP,
        authority="HSE",
        url="https://www.hse.gov.uk/pubns/books/l108.htm",
        description="ACoP and guidance on the Control of Noise at Work Regulations 2005.",
    ),
    KnowledgeSource(
        id="hse-hand-arm-vibration",
        title="Hand-Arm Vibration (L140)",
        source_type=SourceType.ACOP,
        authority="HSE",
        url="https://www.hse.gov.uk/pubns/books/l140.htm",
        description="ACoP on the Control of Vibration at Work Regulations 2005.",
    ),
    KnowledgeSource(
        id="fom-standards",
        title="Faculty of Occupational Medicine Standards",
        source_type=SourceType.PEER_REVIEWED,
        authority="Faculty of Occupational Medicine",
        description="Professional standards for occupational health practice in the UK.",
    ),
]
