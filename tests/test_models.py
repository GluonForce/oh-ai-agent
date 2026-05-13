"""Tests for Pydantic domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from oh_agent.models.audit import AuditEntry, AuditEventType
from oh_agent.models.hazard import (
    ExposureFrequency,
    ExposureLevel,
    HazardCategory,
    HazardProfile,
)
from oh_agent.models.organisation import DeliveryModel, OrganisationProfile
from oh_agent.models.workflow import (
    BenchmarkResult,
    ComplianceRating,
    GapAnalysis,
    GapItem,
    GovernancePrompt,
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
        assert hp.substance_or_agent is None


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

    def test_governance_prompt(self) -> None:
        gp = GovernancePrompt(
            prompt_text="Technician-delivered audiometry must be supervised by OHN.",
            applicable_roles=["OH Technician"],
            regulatory_reference="HSG61",
        )
        assert "Technician" in gp.applicable_roles[0]


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
