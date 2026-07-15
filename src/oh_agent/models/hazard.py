"""Hazard and exposure domain models.

Hazard classification follows the standardised hazard-phrase approach
referenced in the spec, supplemented by additional logic to capture risks
not adequately covered by existing H-phrase classifications.

The risk profile is structured around five dimensions specified in the
PDCA-aligned spec (Section 4 — PLAN):
  1. Type of hazard
  2. Level, duration, and frequency of exposure
  3. Workforce characteristics (including vulnerability)
  4. Potential health effects
  5. Existing control measures and their reliability
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


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
    SKIN = "skin"  # e.g. wet work, dermal exposure


class ExposureLevel(StrEnum):
    """Qualitative exposure band used for risk profiling."""

    NEGLIGIBLE = "negligible"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ExposureFrequency(StrEnum):
    """How often the exposure occurs."""

    RARE = "rare"
    OCCASIONAL = "occasional"
    FREQUENT = "frequent"
    CONTINUOUS = "continuous"


class ExposureDuration(StrEnum):
    """Typical duration of each exposure episode."""

    BRIEF = "brief"  # minutes
    SHORT = "short"  # up to 1 hour
    MEDIUM = "medium"  # 1-4 hours
    LONG = "long"  # 4-8 hours
    EXTENDED = "extended"  # >8 hours / shift


class SurveillanceLevel(StrEnum):
    """Lower- vs higher-level health surveillance (HSE distinction)."""

    LOWER = "lower"
    HIGHER = "higher"


class HazardProfile(BaseModel):
    """A single hazard with its risk-profiling attributes.

    Aligned to PDCA Section 4 — risk profile dimensions.
    """

    category: HazardCategory
    hazard_phrase: str | None = Field(
        default=None,
        max_length=512,
        description="Standardised hazard phrase (e.g. H-phrase) or free-text description.",
    )
    substance_or_agent: str | None = Field(
        default=None,
        max_length=256,
        description="Specific substance, agent, or stressor (e.g. 'isocyanates', 'hand-arm vibration').",
    )
    exposure_level: ExposureLevel = ExposureLevel.MODERATE
    exposure_frequency: ExposureFrequency = ExposureFrequency.FREQUENT
    exposure_duration: ExposureDuration = ExposureDuration.MEDIUM
    workplace_exposure_limit: str | None = Field(
        default=None,
        description="Published WEL or OEL if applicable.",
    )
    potential_health_effects: str | None = Field(
        default=None,
        max_length=1024,
        description="Known or expected health effects from this hazard exposure.",
    )
    existing_controls: str | None = Field(
        default=None,
        max_length=1024,
        description="Current control measures in place and their assessed reliability.",
    )
    hand_washes_per_day: int | None = Field(
        default=None,
        ge=0,
        description=(
            "For skin/wet-work hazards: typical hand washes per day. "
            "HSE treats >20 washes/day as high risk needing higher-level surveillance."
        ),
    )
    surveillance_level: SurveillanceLevel | None = Field(
        default=None,
        description="Lower- or higher-level health surveillance recommended for this hazard.",
    )
    notes: str | None = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def requires_hazard_description(self) -> HazardProfile:
        """Require either a hazard phrase or a specific substance/agent."""
        if not any(value and value.strip() for value in (self.hazard_phrase, self.substance_or_agent)):
            raise ValueError("At least one of hazard_phrase or substance_or_agent must be non-empty.")
        return self


class RiskAssessmentConfirmation(BaseModel):
    """Mandatory confirmation that duty holder has conducted risk assessment.

    Per the PDCA spec (Section 4 — PLAN), the tool must require
    confirmation before any OH workflow is generated.
    """

    risk_assessment_completed: bool = Field(
        ...,
        description=("Duty holder confirms suitable and sufficient risk assessment per Management Regulations."),
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
    additional_notes: str | None = Field(default=None, max_length=2048)
