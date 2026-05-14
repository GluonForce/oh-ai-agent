"""Workflow, benchmarking, and gap-analysis models — PDCA-aligned.

The workflow response is structured around the Plan-Do-Check-Act
framework consistent with HSE expectations for health risk management.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from oh_agent.models.hazard import HazardProfile, RiskAssessmentConfirmation
from oh_agent.models.organisation import OrganisationProfile


class PDCAPhase(StrEnum):
    PLAN = "plan"
    DO = "do"
    CHECK = "check"
    ACT = "act"


# ---------------------------------------------------------------------------
# Shared enumerations
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


class SurveillanceType(StrEnum):
    """Types of health surveillance/monitoring (PDCA DO phase)."""

    AUDIOMETRY = "audiometry"
    SPIROMETRY = "spirometry"
    SKIN_CHECK = "skin_check"
    HAVS_QUESTIONNAIRE = "havs_questionnaire"
    BIOLOGICAL_MONITORING = "biological_monitoring"
    VISION_SCREENING = "vision_screening"
    HEALTH_QUESTIONNAIRE = "health_questionnaire"
    CLINICAL_EXAMINATION = "clinical_examination"
    FITNESS_ASSESSMENT = "fitness_assessment"


class ComplianceRating(StrEnum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


# ---------------------------------------------------------------------------
# PDCA — PLAN phase
# ---------------------------------------------------------------------------


class RiskProfileSummary(BaseModel):
    """Summary of the risk profile produced in the PLAN phase."""

    hazard_summary: str
    risk_assessment_confirmed: bool = False
    workers_consulted: bool = False
    key_risks: list[str] = Field(default_factory=list)
    regulatory_drivers: list[str] = Field(
        default_factory=list,
        description="Primary legislation/regulations driving OH requirements (e.g. COSHH, Noise at Work).",
    )


# ---------------------------------------------------------------------------
# PDCA — DO phase
# ---------------------------------------------------------------------------


class SurveillanceProvision(BaseModel):
    """A single statutory OH surveillance provision (DO phase)."""

    surveillance_type: SurveillanceType
    description: str
    frequency: str = Field(..., description="Surveillance frequency based on exposure and regulatory guidance.")
    competence_required: str = Field(
        ..., description="Competence required to undertake and interpret this surveillance."
    )
    referral_pathway: str | None = Field(
        default=None,
        description="Referral and escalation pathway when abnormal findings occur.",
    )
    retention_period: str | None = Field(
        default=None,
        description="Statutory retention period for health records (e.g. COSHH: 40 years).",
    )
    regulatory_basis: str = Field(..., description="The regulation, ACoP, or guidance underpinning this provision.")
    delegation_notes: str | None = Field(
        default=None,
        description="Governance notes on safe delegation and supervision requirements.",
    )


class WorkflowStep(BaseModel):
    """A single step in a generated workflow."""

    order: int = Field(..., ge=1)
    pdca_phase: PDCAPhase = PDCAPhase.DO
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


# ---------------------------------------------------------------------------
# PDCA — CHECK phase
# ---------------------------------------------------------------------------


class AssuranceCheckItem(BaseModel):
    """A single assurance/audit check item (CHECK phase)."""

    area: str
    question: str
    status: ComplianceRating = ComplianceRating.NOT_ASSESSED
    finding: str | None = None
    recommendation: str | None = None
    regulatory_reference: str | None = None


class TrendInsight(BaseModel):
    """An insight from anonymised surveillance data analysis (CHECK/Review)."""

    area: str
    observation: str
    implication: str
    recommended_action: str | None = None


# ---------------------------------------------------------------------------
# PDCA — ACT phase
# ---------------------------------------------------------------------------


class ImprovementAction(BaseModel):
    """A continuous-improvement action (ACT phase)."""

    area: str
    action: str
    rationale: str
    priority: str = Field(default="medium", description="high / medium / low")
    regulatory_reference: str | None = None


# ---------------------------------------------------------------------------
# Workflow request / response
# ---------------------------------------------------------------------------


class WorkflowRequest(BaseModel):
    """Input payload to generate a PDCA-structured workflow."""

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

    # PLAN
    risk_profile: RiskProfileSummary | None = None

    # DO — detailed surveillance provisions
    surveillance_provisions: list[SurveillanceProvision] = Field(default_factory=list)
    # DO — step-by-step workflow (retained for backwards compatibility)
    steps: list[WorkflowStep] = Field(default_factory=list)

    # CHECK
    assurance_checks: list[AssuranceCheckItem] = Field(default_factory=list)
    trend_insights: list[TrendInsight] = Field(default_factory=list)

    # ACT
    improvement_actions: list[ImprovementAction] = Field(default_factory=list)

    # Governance
    governance_prompts: list[GovernancePrompt] = Field(default_factory=list)

    # Provenance
    sources_cited: list[str] = Field(
        default_factory=list,
        description="Authoritative sources underpinning the workflow.",
    )
    disclaimers: list[str] = Field(default_factory=list)
    model_used: str = ""
    knowledge_chunks_used: int = 0


# ---------------------------------------------------------------------------
# Benchmarking & Gap Analysis (PDCA CHECK)
# ---------------------------------------------------------------------------


class GapItem(BaseModel):
    """A single gap identified during analysis."""

    area: str
    current_state: str
    required_state: str
    rating: ComplianceRating
    recommendation: str
    regulatory_reference: str


class GapAnalysis(BaseModel):
    """Structured gap analysis output (PDCA CHECK phase)."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    gaps: list[GapItem] = Field(default_factory=list)
    overall_rating: ComplianceRating = ComplianceRating.NOT_ASSESSED
    sources_cited: list[str] = Field(default_factory=list)


class BenchmarkResult(BaseModel):
    """Benchmarking of current practice against regulatory minimums (PDCA CHECK)."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    areas_assessed: list[str]
    compliant_areas: list[str]
    non_compliant_areas: list[str]
    recommendations: list[str]
    sources_cited: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# CHECK — Compliance Audit (replaces benchmark/gap-analysis endpoints)
# ---------------------------------------------------------------------------


class ComplianceAuditRequest(BaseModel):
    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)


class ComplianceAuditResponse(BaseModel):
    """Structured compliance audit output (CHECK phase)."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    audit_items: list[AssuranceCheckItem] = Field(default_factory=list)
    overall_rating: ComplianceRating = ComplianceRating.NOT_ASSESSED
    employee_coverage_assessed: bool = False
    interval_adherence_assessed: bool = False
    governance_assessed: bool = False
    sources_cited: list[str] = Field(default_factory=list)
    model_used: str = ""


# ---------------------------------------------------------------------------
# REVIEW — Trend Analysis
# ---------------------------------------------------------------------------


class TrendAnalysisRequest(BaseModel):
    organisation: OrganisationProfile
    hazards: list[HazardProfile] = Field(..., min_length=1)
    surveillance_summary: str = Field(
        ...,
        min_length=1,
        description="Summary of anonymised surveillance data to analyse.",
    )


class TrendAnalysisResponse(BaseModel):
    """Trend analysis output (REVIEW phase)."""

    request_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organisation_name: str
    findings: list[TrendInsight] = Field(default_factory=list)
    control_effectiveness_indicators: list[str] = Field(default_factory=list)
    sources_cited: list[str] = Field(default_factory=list)
    model_used: str = ""


# ---------------------------------------------------------------------------
# ACT — Improvement Plan
# ---------------------------------------------------------------------------


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
