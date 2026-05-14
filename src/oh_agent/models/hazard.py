"""Hazard, exposure, and risk assessment domain models.

Updated to align with the PDCA-framework spec: risk assessment
confirmation is required before any workflow generation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class HazardCategory(StrEnum):
    """Top-level hazard categories aligned to UK regulatory frameworks."""

    CHEMICAL = "chemical"
    BIOLOGICAL = "biological"
    PHYSICAL = "physical"
    ERGONOMIC = "ergonomic"
    PSYCHOSOCIAL = "psychosocial"
    NOISE = "noise"
    VIBRATION = "vibration"
    RADIATION = "radiation"
    DUST = "dust"
    SKIN = "skin"


class ExposureLevel(StrEnum):
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ExposureFrequency(StrEnum):
    RARE = "rare"
    OCCASIONAL = "occasional"
    FREQUENT = "frequent"
    CONTINUOUS = "continuous"


class ExposureDuration(StrEnum):
    """Duration of individual exposure episodes."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    FULL_SHIFT = "full_shift"


class HazardProfile(BaseModel):
    """A single hazard with its risk-profiling attributes."""

    category: HazardCategory
    hazard_phrase: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Standardised hazard phrase or free-text description.",
    )
    substance_or_agent: str | None = Field(
        default=None,
        max_length=256,
        description="Specific substance, agent, or stressor.",
    )
    exposure_level: ExposureLevel = ExposureLevel.MODERATE
    exposure_frequency: ExposureFrequency = ExposureFrequency.FREQUENT
    exposure_duration: ExposureDuration = ExposureDuration.MEDIUM
    potential_health_effects: str | None = Field(
        default=None,
        max_length=1024,
        description="Potential health effects from this exposure.",
    )
    existing_controls: str | None = Field(
        default=None,
        max_length=1024,
        description="Existing control measures and their reliability.",
    )
    workplace_exposure_limit: str | None = Field(
        default=None,
        description="Published WEL or OEL if applicable.",
    )
    notes: str | None = Field(default=None, max_length=2048)


class RiskAssessmentConfirmation(BaseModel):
    """Mandatory confirmation that duty holder has conducted risk assessment.

    Per the PDCA spec (Section 4 — PLAN), the tool must require
    confirmation before any OH workflow is generated.
    """

    risk_assessment_completed: bool = Field(
        ...,
        description="Duty holder confirms suitable and sufficient risk assessment per Management Regulations.",
    )
    risk_assessment_date: str | None = Field(
        default=None,
        description="Date the risk assessment was last completed/reviewed.",
    )
    workers_consulted: bool = Field(
        ...,
        description=(
            "Confirmation that workers have been consulted on perceived hazards and control practicality (HSWA duty)."
        ),
    )
    assessor_name: str | None = Field(
        default=None,
        max_length=256,
        description="Name or role of the person who conducted the risk assessment.",
    )
    additional_notes: str | None = Field(
        default=None,
        max_length=2048,
    )
