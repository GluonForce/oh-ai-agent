"""Hazard and exposure domain models.

Hazard classification follows the standardised hazard-phrase approach
referenced in the spec, supplemented by additional logic to capture risks
not adequately covered by existing H-phrase classifications.
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


class HazardProfile(BaseModel):
    """A single hazard with its risk-profiling attributes."""

    category: HazardCategory
    hazard_phrase: str = Field(
        ...,
        min_length=1,
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
    workplace_exposure_limit: str | None = Field(
        default=None,
        description="Published WEL or OEL if applicable.",
    )
    notes: str | None = Field(default=None, max_length=2048)
