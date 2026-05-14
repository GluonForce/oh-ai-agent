"""Workflow, surveillance, compliance audit, trend analysis, and improvement models.

Structured around the PDCA (Plan-Do-Check-Act) framework defined in the spec.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from oh_agent.models.hazard import HazardProfile, RiskAssessmentConfirmation
from oh_agent.models.organisation import OrganisationProfile

# ---------------------------------------------------------------------------
# PDCA Phase
# ---------------------------------------------------------------------------


class PDCAPhase(StrEnum):
    PLAN = "plan"
    DO = "do"
    CHECK = "check"
    ACT = "act"


# ---------------------------------------------------------------------------
# DO — Statutory OH Provision (Workflow)
# ---------------------------------------------------------------------------


class SurveillanceType(StrEnum):
    AUDIOMETRY = "audiometry"
    SPIROMETRY = "spirometry"
    SKIN_CHECK = "skin_check"
    HAVS_QUESTIONNAIRE = "havs_questionnaire"
    BIOLOGICAL_MONITORING = "biological_monitoring"
    VISION_SCREENING = "vision_screening"
    HEALTH_QUESTIONNAIRE = "health_questionnaire"
    CLINICAL_ASSESSMENT = "clinical_assessment"
    FITNESS_FOR_TASK = "fitness_for_task"
    OTHER = "other"


class WorkflowComponent(StrEnum):
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


class SurveillanceRequirement(BaseModel):
    """A specific surveillance activity within the DO phase."""

    surveillance_type: SurveillanceType
    description: str
    frequency: str = Field(..., description="Surveillance frequency based on exposure and regulatory guidance.")
    competence_required: str = Field(
        ..., description="Competence required to undertake and interpret this surveillance."
    )
    referral_pathway: str = Field(
        default="",
        description="Referral and escalation pathways.",
    )
    retention_period: str = Field(
        default="",
        description="Statutory retention period for health records (e.g. 40 years for COSHH).",
    )
    regulatory_basis: str = Field(..., description="The regulation, ACoP, or guidance underpinning this requirement.")


class WorkflowStep(BaseModel):
    """A single step in a generated PDCA workflow."""

    order: int = Field(..., ge=1)
    pdca_phase: PDCAPhase
    component: WorkflowComponent
    description: str
    responsible_role: str = Field(
        ...,
        description="Who should carry out this step (e.g. 'OHP', 'OHN', 'OH Technician').",
    )
    frequency: str
    regulatory_basis: str
    delegation_notes: str | None = None


class GovernancePrompt(BaseModel):
    prompt_text: str
    applicable_roles: list[str]
    regulatory_reference: str


class WorkflowRequest(BaseModel):
    """Input payload to generate a PDCA workflow — requires risk assessment confirmation."""

    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)
    risk_assessment: RiskAssessmentConfirmation
    additional_context: str | None = Field(default=None, max_length=4096)


class WorkflowResponse(BaseModel):
    """Complete PDCA-structured workflow with provenance metadata."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    hazard_summary: str
    risk_assessment_confirmed: bool = True
    workers_consulted: bool = True
    steps: list[WorkflowStep]
    surveillance_requirements: list[SurveillanceRequirement] = Field(default_factory=list)
    governance_prompts: list[GovernancePrompt] = Field(default_factory=list)
    sources_cited: list[str] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    model_used: str = ""
    knowledge_chunks_used: int = 0


# ---------------------------------------------------------------------------
# CHECK — Compliance Audit
# ---------------------------------------------------------------------------


class ComplianceRating(StrEnum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class ComplianceAuditItem(BaseModel):
    """A single item assessed during the CHECK phase."""

    area: str
    question: str
    current_state: str
    required_state: str
    rating: ComplianceRating
    recommendation: str
    regulatory_reference: str


class ComplianceAuditRequest(BaseModel):
    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)


class ComplianceAuditResponse(BaseModel):
    """Structured compliance audit output (CHECK phase)."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    audit_items: list[ComplianceAuditItem] = Field(default_factory=list)
    overall_rating: ComplianceRating = ComplianceRating.NOT_ASSESSED
    employee_coverage_assessed: bool = False
    interval_adherence_assessed: bool = False
    governance_assessed: bool = False
    sources_cited: list[str] = Field(default_factory=list)
    model_used: str = ""


# ---------------------------------------------------------------------------
# REVIEW — Trend Analysis
# ---------------------------------------------------------------------------


class TrendFinding(BaseModel):
    """A single finding from anonymised surveillance trend analysis."""

    category: str = Field(..., description="e.g. 'early illness sign', 'cluster', 'control failure'")
    description: str
    affected_area: str = Field(default="", description="Department, task, or role affected.")
    severity: str = Field(default="", description="Low / Medium / High")
    recommended_action: str = ""
    regulatory_reference: str = ""


class TrendAnalysisRequest(BaseModel):
    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)
    surveillance_summary: str = Field(
        ...,
        min_length=1,
        description="Summary of anonymised surveillance data or findings to analyse.",
    )


class TrendAnalysisResponse(BaseModel):
    """Trend analysis output (REVIEW phase)."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    findings: list[TrendFinding] = Field(default_factory=list)
    control_effectiveness_indicators: list[str] = Field(default_factory=list)
    sources_cited: list[str] = Field(default_factory=list)
    model_used: str = ""


# ---------------------------------------------------------------------------
# ACT — Improvement Actions
# ---------------------------------------------------------------------------


class ImprovementAction(BaseModel):
    """A recommended improvement action from the ACT phase."""

    action_type: str = Field(
        ...,
        description=(
            "e.g. 'engineering_control', 'exposure_reduction', "
            "'ppe_review', 'process_modification', 'surveillance_change'"
        ),
    )
    description: str
    priority: str = Field(default="medium", description="low / medium / high / critical")
    regulatory_basis: str = ""
    expected_outcome: str = ""


class ImprovementPlanRequest(BaseModel):
    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)
    surveillance_findings: str = Field(
        ...,
        min_length=1,
        description="Summary of surveillance findings or trend analysis results.",
    )


class ImprovementPlanResponse(BaseModel):
    """Improvement plan output (ACT phase)."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    actions: list[ImprovementAction] = Field(default_factory=list)
    management_review_items: list[str] = Field(default_factory=list)
    sources_cited: list[str] = Field(default_factory=list)
    model_used: str = ""
