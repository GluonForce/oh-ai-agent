"""Organisation and delivery-model domain models.

The organisation profile captures the context required under PDCA
Section 4 (PLAN) before any OH workflow can be generated, including
confirmation that a suitable and sufficient risk assessment has been
undertaken and that workers have been consulted.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class DeliveryModel(StrEnum):
    """OH service delivery models."""

    OHP_LED = "ohp_led"  # Occupational Health Physician-led
    OHN_LED = "ohn_led"  # Occupational Health Nurse-led
    TECHNICIAN = "technician"  # Technician-delivered
    MIXED = "mixed"  # Combination
    NONE = "none"  # No OH service currently in place


class AssessmentScope(StrEnum):
    """Whether the assessment covers a staff group or an individual."""

    STAFF_GROUP = "staff_group"
    INDIVIDUAL = "individual"


ANONYMOUS_ORG_NAME = "Anonymous organisation"


class OrganisationProfile(BaseModel):
    """Captures the organisational context that shapes workflow generation.

    Includes PDCA PLAN-phase confirmations: risk assessment undertaken
    and workers consulted, per HSWA duties.
    """

    name: str = Field(
        default=ANONYMOUS_ORG_NAME,
        min_length=1,
        max_length=256,
        description="Organisation name. Use Anonymous organisation for anonymised use.",
    )
    sector: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Industry sector (e.g. 'NHS', 'manufacturing', 'construction').",
    )
    tasks: list[str] = Field(
        default_factory=list,
        description="Key tasks performed by the workforce relevant to hazard exposure.",
    )
    workforce_size: int | None = Field(default=None, ge=1)
    workforce_characteristics: str | None = Field(
        default=None,
        max_length=1024,
        description="E.g. shift patterns, age demographics, vulnerable groups.",
    )
    assessment_scope: AssessmentScope = Field(
        default=AssessmentScope.STAFF_GROUP,
        description="Staff group (population) vs individual worker risk context.",
    )
    pre_existing_conditions: list[str] = Field(
        default_factory=list,
        description=(
            "Relevant pre-existing conditions that may increase individual risk "
            "(e.g. asthma/COPD for respiratory hazards, eczema for skin hazards)."
        ),
    )
    multi_site: bool = False
    site_count: int = Field(default=1, ge=1)
    delivery_model: DeliveryModel = DeliveryModel.MIXED
    existing_surveillance: str | None = Field(
        default=None,
        max_length=2048,
        description="Description of current health surveillance arrangements.",
    )
    risk_assessment_confirmed: bool = Field(
        default=False,
        description=(
            "Duty holder confirms a suitable and sufficient risk assessment "
            "has been undertaken in accordance with the Management Regulations."
        ),
    )
    workers_consulted: bool = Field(
        default=False,
        description=(
            "Duty holder confirms workers have been consulted on perceived "
            "hazards and the practicality of controls (HSWA duty)."
        ),
    )

    @field_validator("name", mode="before")
    @classmethod
    def normalise_anonymous_name(cls, value: object) -> str:
        if value is None:
            return ANONYMOUS_ORG_NAME
        text = str(value).strip()
        return text if text else ANONYMOUS_ORG_NAME
