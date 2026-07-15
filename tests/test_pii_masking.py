"""Tests for PII masking (OpenAI Privacy Filter placeholder taxonomy)."""

from __future__ import annotations

from oh_agent.config import Settings
from oh_agent.models.hazard import HazardCategory, HazardProfile, RiskAssessmentConfirmation
from oh_agent.models.organisation import OrganisationProfile
from oh_agent.models.workflow import WorkflowRequest
from oh_agent.privacy.pii_masking import (
    PiiMaskingService,
    mask_text_regex,
    mask_workflow_request,
)


class TestRegexMasking:
    def test_masks_email(self) -> None:
        text = "Contact maya.chen@example.com for follow-up"
        assert "[PRIVATE_EMAIL]" in mask_text_regex(text)
        assert "maya.chen@example.com" not in mask_text_regex(text)

    def test_masks_uk_mobile(self) -> None:
        text = "Call me on 07700 900123 please"
        assert "[PRIVATE_PHONE]" in mask_text_regex(text)

    def test_masks_secret_key(self) -> None:
        text = "api_key=sk-abcdefghijklmnopqrstuvwxyz"
        assert "[SECRET]" in mask_text_regex(text)

    def test_masks_account_like_card(self) -> None:
        text = "Card 4829-1037-5581-9921 on file"
        assert "[ACCOUNT_NUMBER]" in mask_text_regex(text)

    def test_masks_person_title(self) -> None:
        text = "Assessor Dr. Jane Smith completed the review"
        assert "[PRIVATE_PERSON]" in mask_text_regex(text)

    def test_disabled_service_passthrough(self) -> None:
        svc = PiiMaskingService(enabled=False)
        assert svc.mask("test@example.com") == "test@example.com"

    def test_opf_fallback_to_regex(self) -> None:
        svc = PiiMaskingService(enabled=True, provider="opf")
        # opf not installed in default test env → soft-fail to regex
        out = svc.mask("email me at alice@example.com")
        assert "[PRIVATE_EMAIL]" in (out or "")


class TestRequestMasking:
    def test_masks_workflow_free_text(self) -> None:
        settings = Settings(pii_masking_enabled=True, pii_provider="regex")
        request = WorkflowRequest(
            organisation=OrganisationProfile(
                name="Acme",
                sector="manufacturing",
                existing_surveillance="Contact bob@factory.test about rates",
            ),
            hazards=[
                HazardProfile(
                    category=HazardCategory.CHEMICAL,
                    substance_or_agent="isocyanates",
                    notes="Worker John Doe reported symptoms",
                )
            ],
            risk_assessment=RiskAssessmentConfirmation(
                risk_assessment_completed=True,
                workers_consulted=True,
                assessor_name="Dr. Jane Smith",
            ),
            additional_context="Reply to maya.chen@example.com",
        )
        masked = mask_workflow_request(request, settings)
        assert "[PRIVATE_EMAIL]" in (masked.organisation.existing_surveillance or "")
        assert "[PRIVATE_EMAIL]" in (masked.additional_context or "")
        assert "[PRIVATE_PERSON]" in (masked.risk_assessment.assessor_name or "")
