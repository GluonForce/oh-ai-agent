"""Tests for Pydantic domain models (PDCA framework)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from oh_agent.models.audit import AuditEntry, AuditEventType
from oh_agent.models.hazard import (
    ExposureDuration,
    ExposureFrequency,
    ExposureLevel,
    HazardCategory,
    HazardProfile,
    RiskAssessmentConfirmation,
)
from oh_agent.models.organisation import DeliveryModel, OrganisationProfile
from oh_agent.models.workflow import (
    ComplianceAuditItem,
    ComplianceAuditResponse,
    ComplianceRating,
    GovernancePrompt,
    ImprovementAction,
    ImprovementPlanResponse,
    PDCAPhase,
    SurveillanceRequirement,
    SurveillanceType,
    TrendAnalysisResponse,
    TrendFinding,
    WorkflowComponent,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStep,
)


class TestHazardProfile:
    def test_valid_hazard(self) -> None:
        hp = HazardProfile(
            category=HazardCategory.CHEMICAL,
            hazard_phrase="H334 — May cause allergy or asthma",
            exposure_level=ExposureLevel.HIGH,
            exposure_frequency=ExposureFrequency.FREQUENT,
        )
        assert hp.category == HazardCategory.CHEMICAL
        assert hp.exposure_level == ExposureLevel.HIGH

    def test_empty_hazard_phrase_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HazardProfile(category=HazardCategory.CHEMICAL, hazard_phrase="")

    def test_defaults(self) -> None:
        hp = HazardProfile(
            category=HazardCategory.NOISE,
            hazard_phrase="Continuous noise above 85 dB(A)",
        )
        assert hp.exposure_level == ExposureLevel.MODERATE
        assert hp.exposure_frequency == ExposureFrequency.FREQUENT
        assert hp.exposure_duration == ExposureDuration.MEDIUM
        assert hp.potential_health_effects is None
        assert hp.existing_controls is None

    def test_new_fields(self) -> None:
        hp = HazardProfile(
            category=HazardCategory.SKIN,
            hazard_phrase="Wet work exposure",
            exposure_duration=ExposureDuration.FULL_SHIFT,
            potential_health_effects="Occupational dermatitis",
            existing_controls="Barrier cream, gloves provided",
        )
        assert hp.exposure_duration == ExposureDuration.FULL_SHIFT
        assert hp.potential_health_effects == "Occupational dermatitis"


class TestRiskAssessmentConfirmation:
    def test_valid_confirmation(self) -> None:
        ra = RiskAssessmentConfirmation(
            risk_assessment_completed=True,
            workers_consulted=True,
            risk_assessment_date="2024-01-15",
            assessor_name="H&S Manager",
        )
        assert ra.risk_assessment_completed is True
        assert ra.workers_consulted is True

    def test_requires_both_fields(self) -> None:
        with pytest.raises(ValidationError):
            RiskAssessmentConfirmation(risk_assessment_completed=True)


class TestOrganisationProfile:
    def test_valid_organisation(self, sample_organisation: OrganisationProfile) -> None:
        assert sample_organisation.name == "Acme Manufacturing Ltd"
        assert sample_organisation.sector == "manufacturing"
        assert sample_organisation.delivery_model == DeliveryModel.OHN_LED

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrganisationProfile(name="", sector="test")

    def test_negative_workforce_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrganisationProfile(name="Test", sector="test", workforce_size=0)


class TestWorkflowModels:
    def test_workflow_step_with_pdca_phase(self) -> None:
        step = WorkflowStep(
            order=1,
            pdca_phase=PDCAPhase.DO,
            component=WorkflowComponent.SKIN_ASSESSMENT,
            description="Baseline skin assessment for wet work exposure",
            responsible_role="OHN",
            frequency="baseline + annual",
            regulatory_basis="COSHH Regulation 11",
        )
        assert step.pdca_phase == PDCAPhase.DO

    def test_surveillance_requirement(self) -> None:
        sr = SurveillanceRequirement(
            surveillance_type=SurveillanceType.SKIN_CHECK,
            description="Visual skin inspection for dermatitis",
            frequency="baseline + 6-monthly",
            competence_required="Trained OH technician under OHN supervision",
            referral_pathway="Refer to dermatologist if persistent",
            retention_period="40 years (COSHH)",
            regulatory_basis="COSHH Regulation 11",
        )
        assert sr.surveillance_type == SurveillanceType.SKIN_CHECK
        assert sr.retention_period == "40 years (COSHH)"

    def test_workflow_request_requires_risk_assessment(self) -> None:
        org = OrganisationProfile(name="Test", sector="test")
        ra = RiskAssessmentConfirmation(
            risk_assessment_completed=True,
            workers_consulted=True,
        )
        req = WorkflowRequest(
            organisation=org,
            hazards=[HazardProfile(category="chemical", hazard_phrase="test hazard")],
            risk_assessment=ra,
        )
        assert req.risk_assessment.risk_assessment_completed is True

    def test_workflow_request_requires_hazards(self) -> None:
        org = OrganisationProfile(name="Test", sector="test")
        ra = RiskAssessmentConfirmation(risk_assessment_completed=True, workers_consulted=True)
        with pytest.raises(ValidationError):
            WorkflowRequest(organisation=org, hazards=[], risk_assessment=ra)

    def test_workflow_response_defaults(self) -> None:
        resp = WorkflowResponse(
            request_id="test-123",
            organisation_name="Test",
            hazard_summary="wet work",
            steps=[],
        )
        assert resp.risk_assessment_confirmed is True
        assert resp.workers_consulted is True
        assert resp.surveillance_requirements == []

    def test_governance_prompt(self) -> None:
        gp = GovernancePrompt(
            prompt_text="Technician-delivered audiometry must be supervised by OHN.",
            applicable_roles=["OH Technician"],
            regulatory_reference="HSG61",
        )
        assert "Technician" in gp.applicable_roles[0]


class TestComplianceAuditModels:
    def test_audit_item(self) -> None:
        item = ComplianceAuditItem(
            area="Employee coverage",
            question="Are all exposed employees identified?",
            current_state="Only production floor workers included",
            required_state="All workers with hazard exposure must be included",
            rating=ComplianceRating.PARTIALLY_COMPLIANT,
            recommendation="Include maintenance and cleaning staff",
            regulatory_reference="COSHH Reg 11",
        )
        assert item.rating == ComplianceRating.PARTIALLY_COMPLIANT

    def test_audit_response_defaults(self) -> None:
        resp = ComplianceAuditResponse(
            request_id="test-456",
            organisation_name="Test Org",
        )
        assert resp.overall_rating == ComplianceRating.NOT_ASSESSED
        assert resp.employee_coverage_assessed is False


class TestTrendAnalysisModels:
    def test_trend_finding(self) -> None:
        tf = TrendFinding(
            category="early_illness_sign",
            description="Increased skin complaints in Q3",
            affected_area="Assembly line",
            severity="medium",
            recommended_action="Review detergent concentration",
        )
        assert tf.category == "early_illness_sign"

    def test_response_defaults(self) -> None:
        resp = TrendAnalysisResponse(
            request_id="test-789",
            organisation_name="Test Org",
        )
        assert resp.findings == []
        assert resp.control_effectiveness_indicators == []


class TestImprovementPlanModels:
    def test_improvement_action(self) -> None:
        action = ImprovementAction(
            action_type="engineering_control",
            description="Install automated dispensing system",
            priority="high",
            regulatory_basis="COSHH hierarchy of controls",
            expected_outcome="Reduce manual contact with solvents by 80%",
        )
        assert action.priority == "high"

    def test_response_defaults(self) -> None:
        resp = ImprovementPlanResponse(
            request_id="test-abc",
            organisation_name="Test Org",
        )
        assert resp.actions == []
        assert resp.management_review_items == []


class TestAuditModels:
    def test_audit_entry_defaults(self) -> None:
        entry = AuditEntry(event_type=AuditEventType.WORKFLOW_REQUESTED)
        assert entry.id is not None
        assert entry.timestamp is not None

    def test_new_pdca_event_types(self) -> None:
        for et in [
            AuditEventType.RISK_ASSESSMENT_CONFIRMED,
            AuditEventType.COMPLIANCE_AUDIT_REQUESTED,
            AuditEventType.COMPLIANCE_AUDIT_GENERATED,
            AuditEventType.TREND_ANALYSIS_REQUESTED,
            AuditEventType.TREND_ANALYSIS_GENERATED,
            AuditEventType.IMPROVEMENT_PLAN_REQUESTED,
            AuditEventType.IMPROVEMENT_PLAN_GENERATED,
        ]:
            entry = AuditEntry(event_type=et)
            assert entry.event_type == et

    def test_audit_serialization_roundtrip(self) -> None:
        entry = AuditEntry(
            event_type=AuditEventType.WORKFLOW_GENERATED,
            request_id="req-456",
            sources_used=["HSG61", "EH40"],
            model_used="gpt-4o",
        )
        json_str = entry.model_dump_json()
        restored = AuditEntry.model_validate_json(json_str)
        assert restored.request_id == entry.request_id
