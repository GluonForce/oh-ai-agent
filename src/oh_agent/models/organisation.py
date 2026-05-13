"""Organisation and delivery-model domain models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DeliveryModel(StrEnum):
    """OH service delivery models."""

    OHP_LED = "ohp_led"  # Occupational Health Physician-led
    OHN_LED = "ohn_led"  # Occupational Health Nurse-led
    TECHNICIAN = "technician"  # Technician-delivered
    MIXED = "mixed"  # Combination


class OrganisationProfile(BaseModel):
    """Captures the organisational context that shapes workflow generation."""

    name: str = Field(..., min_length=1, max_length=256)
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
    multi_site: bool = False
    site_count: int = Field(default=1, ge=1)
    delivery_model: DeliveryModel = DeliveryModel.MIXED
    existing_surveillance: str | None = Field(
        default=None,
        max_length=2048,
        description="Description of current health surveillance arrangements.",
    )
