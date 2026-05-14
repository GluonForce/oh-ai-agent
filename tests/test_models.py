"""Tests for Pydantic domain models."""

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
)
from oh_agent.models.organisation import DeliveryModel, OrganisationProfile
from oh_agent.models.workflow import (
    AssuranceCheckItem,
    BenchmarkResult,
    ComplianceRating,
    GapAnalysis,
    GapItem,
    GovernancePrompt,
    ImprovementAction,
    RiskProfileSummary,
    SurveillanceProvision,
    SurveillanceType,
    TrendInsight,
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
            HazardProfile(
                category=HazardCategory.CHEMICAL,
                hazard_phrase="",
            )

    def test_defaults(self) -> None:
        hp = HazardProfile(
            category=HazardCategory.NOISE,
            hazard_phrase="Continuous noise above 85 dB(A)",
        )
        assert hp.exposure_level == ExposureLevel.MODERATE
        assert hp.exposure_frequency == ExposureFrequency.FREQUENT
        assert hp.exposure_duration == ExposureDuration.MEDIUM
        assert hp.substance_or_agent is None
        assert hp.potential_health_effects is None
        assert hp.existing_controls is None

    def test_new_fields(self) -> None:
        hp = HazardProfile(
            category=HazardCategory.NOISE,
            hazard_phrase="Continuous noise above 85 dB(A)",
            exposure_duration=ExposureDuration.LONG,
            potential_health_effects="Noise-induced hearing loss (NIHL)",
            existing_controls="Ear defenders provided, limited compliance observed",
        )
        assert hp.exposure_duration == ExposureDuration.LONG
        assert "NIHL" in (hp.potential_health_effects or "")
        assert "Ear defenders" in (hp.existing_controls or "")


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

    def test_pdca_confirmations_default_false(self) -> None:
        org = OrganisationProfile(name="Test", sector="test")
        assert org.risk_assessment_confirmed is False
        assert org.workers_consulted is False

    def test_pdca_confirmations_set(self) -> None:
        org = OrganisationProfile(
            name="Test",
            sector="test",
            risk_assessment_confirmed=True,
            workers_consulted=True,
        )
        assert org.risk_assessment_confirmed is True
        assert org.workers_consulted is True


class TestWorkflowModels:
    def test_workflow_step(self) -> None:
        step = WorkflowStep(
            order=1,
            component=WorkflowComponent.SKIN_ASSESSMENT,
            description="Baseline skin assessment for wet work exposure",
            responsible_role="OHN",
            frequency="baseline + annual",
            regulatory_basis="COSHH Regulation 11",
        )
        assert step.order == 1
        assert step.component == WorkflowComponent.SKIN_ASSESSMENT

    def test_workflow_request_requires_hazards(self) -> None:
        org = OrganisationProfile(name="Test", sector="test")
        with pytest.raises(ValidationError):
            WorkflowRequest(organisation=org, hazards=[])

    def test_workflow_response_defaults(self) -> None:
        resp = WorkflowResponse(
            request_id="test-123",
            organisation_name="Test",
            hazard_summary="wet work",
            steps=[],
        )
        assert resp.generated_at is not None
        assert resp.disclaimers == []
        assert resp.model_used == ""
        assert resp.risk_profile is None
        assert resp.surveillance_provisions == []
        assert resp.assurance_checks == []
        assert resp.trend_insights == []
        assert resp.improvement_actions == []

    def test_governance_prompt(self) -> None:
        gp = GovernancePrompt(
            prompt_text="Technician-delivered audiometry must be supervised by OHN.",
            applicable_roles=["OH Technician"],
            regulatory_reference="HSG61",
        )
        assert "Technician" in gp.applicable_roles[0]


class TestPDCAModels:
    def test_risk_profile_summary(self) -> None:
        rps = RiskProfileSummary(
            hazard_summary="Chemical exposure to isocyanates",
            risk_assessment_confirmed=True,
            workers_consulted=True,
            key_risks=["Occupational asthma", "Sensitisation"],
            regulatory_drivers=["COSHH Reg 11", "Management Regulations"],
        )
        assert rps.risk_assessment_confirmed is True
        assert len(rps.key_risks) == 2

    def test_surveillance_provision(self) -> None:
        sp = SurveillanceProvision(
            surveillance_type=SurveillanceType.SPIROMETRY,
            description="Lung function testing for isocyanate-exposed workers",
            frequency="baseline + 6-monthly",
            competence_required="Qualified OHN with spirometry training",
            referral_pathway="Refer to OHP if FEV1 decline >15%",
            retention_period="40 years (COSHH)",
            regulatory_basis="COSHH Regulation 11",
        )
        assert sp.surveillance_type == SurveillanceType.SPIROMETRY
        assert "40 years" in (sp.retention_period or "")

    def test_assurance_check_item(self) -> None:
        aci = AssuranceCheckItem(
            area="Employee coverage",
            question="Have all exposed employees been identified and included?",
            status=ComplianceRating.NOT_ASSESSED,
        )
        assert aci.status == ComplianceRating.NOT_ASSESSED

    def test_trend_insight(self) -> None:
        ti = TrendInsight(
            area="Respiratory surveillance",
            observation="3 workers showed FEV1 decline >10%",
            implication="Possible control failure for isocyanate exposure",
            recommended_action="Review engineering controls and RPE adequacy",
        )
        assert "FEV1" in ti.observation

    def test_improvement_action(self) -> None:
        ia = ImprovementAction(
            area="Engineering controls",
            action="Install local exhaust ventilation at spray booth",
            rationale="Current controls insufficient to maintain exposure below WEL",
            priority="high",
            regulatory_reference="COSHH Reg 7",
        )
        assert ia.priority == "high"

    def test_full_pdca_workflow_response(self) -> None:
        resp = WorkflowResponse(
            request_id="test-pdca",
            organisation_name="Test Org",
            hazard_summary="noise exposure",
            risk_profile=RiskProfileSummary(
                hazard_summary="noise exposure",
                risk_assessment_confirmed=True,
                workers_consulted=True,
                key_risks=["NIHL"],
                regulatory_drivers=["Control of Noise at Work Regs 2005"],
            ),
            surveillance_provisions=[
                SurveillanceProvision(
                    surveillance_type=SurveillanceType.AUDIOMETRY,
                    description="Pure tone audiometry",
                    frequency="baseline + annual",
                    competence_required="Trained audiometry technician",
                    regulatory_basis="L108",
                ),
            ],
            steps=[],
            assurance_checks=[
                AssuranceCheckItem(
                    area="Employee coverage",
                    question="All exposed workers included?",
                ),
            ],
            improvement_actions=[
                ImprovementAction(
                    area="Hearing protection",
                    action="Review HPD adequacy",
                    rationale="New noise survey data",
                ),
            ],
        )
        assert resp.risk_profile is not None
        assert len(resp.surveillance_provisions) == 1
        assert len(resp.assurance_checks) == 1
        assert len(resp.improvement_actions) == 1


class TestBenchmarkModels:
    def test_gap_item(self) -> None:
        gi = GapItem(
            area="Health surveillance programme",
            current_state="Annual questionnaires only",
            required_state="Biological monitoring + lung function",
            rating=ComplianceRating.NON_COMPLIANT,
            recommendation="Implement spirometry and biological monitoring",
            regulatory_reference="COSHH Reg 11",
        )
        assert gi.rating == ComplianceRating.NON_COMPLIANT

    def test_gap_analysis_defaults(self) -> None:
        ga = GapAnalysis(
            request_id="test-456",
            organisation_name="Test Org",
        )
        assert ga.overall_rating == ComplianceRating.NOT_ASSESSED
        assert ga.gaps == []

    def test_benchmark_result(self) -> None:
        br = BenchmarkResult(
            request_id="test-789",
            organisation_name="Test Org",
            areas_assessed=["surveillance", "record keeping"],
            compliant_areas=["record keeping"],
            non_compliant_areas=["surveillance"],
            recommendations=["Implement biological monitoring"],
        )
        assert len(br.non_compliant_areas) == 1


class TestAuditModels:
    def test_audit_entry_defaults(self) -> None:
        entry = AuditEntry(event_type=AuditEventType.WORKFLOW_REQUESTED)
        assert entry.id is not None
        assert entry.timestamp is not None
        assert entry.actor == "system"
        assert entry.detail == {}

    def test_audit_entry_with_detail(self) -> None:
        entry = AuditEntry(
            event_type=AuditEventType.GUARDRAIL_TRIGGERED,
            request_id="req-123",
            detail={"violations": ["clinical decision detected"]},
            guardrails_applied=["clinical_decision_check"],
        )
        assert entry.request_id == "req-123"
        assert len(entry.guardrails_applied) == 1

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
        assert restored.sources_used == entry.sources_used
