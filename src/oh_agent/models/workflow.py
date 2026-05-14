"""Workflow, benchmarking, and gap-analysis models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from oh_agent.models.hazard import HazardProfile
from oh_agent.models.organisation import OrganisationProfile

# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


class WorkflowComponent(StrEnum):
    """Discrete components that can appear in an OH workflow."""

    HEALTH_QUESTIONNAIRE = "health_questionnaire"
    CLINICAL_ASSESSMENT = "clinical_assessment"
    BIOLOGICAL_MONITORING = "biological_monitoring"
    LUNG_FUNCTION_TEST = "lung_function_test"
    AUDIOMETRY = "audiometry"
    SKIN_ASSESSMENT = "skin_assessment"
    VISION_SCREENING = "vision_screening"
    FITNESS_FOR_TASK = "fitness_for_task"
    HEALTH_EDUCATION = "health_education"
    REFERRAL = "referral"
    REVIEW_APPOINTMENT = "review_appointment"
    RECORD_KEEPING = "record_keeping"


class WorkflowStep(BaseModel):
    """A single step in a generated workflow."""

    order: int = Field(..., ge=1)
    component: WorkflowComponent
    description: str
    responsible_role: str = Field(
        ...,
        description="Who should carry out this step (e.g. 'OHP', 'OHN', 'OH Technician').",
    )
    frequency: str = Field(
        ...,
        description="How often this step should be performed (e.g. 'baseline + annual').",
    )
    regulatory_basis: str = Field(
        ...,
        description="The regulation, ACoP, or guidance underpinning this step.",
    )
    delegation_notes: str | None = Field(
        default=None,
        description="Governance notes on safe delegation and supervision requirements.",
    )


class GovernancePrompt(BaseModel):
    """Governance prompt for safe delegation and supervision."""

    prompt_text: str
    applicable_roles: list[str]
    regulatory_reference: str


class WorkflowRequest(BaseModel):
    """Input payload to generate a workflow."""

    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)
    additional_context: str | None = Field(default=None, max_length=4096)


class WorkflowResponse(BaseModel):
    """Complete generated workflow with provenance metadata."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    hazard_summary: str
    steps: list[WorkflowStep]
    governance_prompts: list[GovernancePrompt] = Field(default_factory=list)
    sources_cited: list[str] = Field(
        default_factory=list,
        description="Authoritative sources underpinning the workflow.",
    )
    disclaimers: list[str] = Field(default_factory=list)
    model_used: str = ""
    knowledge_chunks_used: int = 0


# ---------------------------------------------------------------------------
# Benchmarking & Gap Analysis
# ---------------------------------------------------------------------------


class ComplianceRating(StrEnum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class GapItem(BaseModel):
    """A single gap identified during analysis."""

    area: str
    current_state: str
    required_state: str
    rating: ComplianceRating
    recommendation: str
    regulatory_reference: str


class GapAnalysis(BaseModel):
    """Structured gap analysis output."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    gaps: list[GapItem] = Field(default_factory=list)
    overall_rating: ComplianceRating = ComplianceRating.NOT_ASSESSED
    sources_cited: list[str] = Field(default_factory=list)


class BenchmarkResult(BaseModel):
    """Benchmarking of current practice against regulatory minimums."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    areas_assessed: list[str]
    compliant_areas: list[str]
    non_compliant_areas: list[str]
    recommendations: list[str]
    sources_cited: list[str] = Field(default_factory=list)
