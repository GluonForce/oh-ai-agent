"""Tests for compliance guardrails."""

from __future__ import annotations

from oh_agent.agents.guardrails import (
    MANDATORY_DISCLAIMERS,
    SYSTEM_GUARDRAIL_PROMPT,
    append_disclaimers,
    check_output,
    check_parsed_content,
)
from oh_agent.agents.workflow_agent import WORKFLOW_CONSISTENCY_RULES


class TestCheckOutput:
    def test_clean_text_passes(self) -> None:
        result = check_output(
            "Based on HSE guidance HSG61, this workflow suggests implementing "
            "baseline skin assessments for all workers exposed to wet work."
        )
        assert result.passed is True
        assert result.violations == []
        assert result.sanitised_text != ""

    def test_diagnosis_detected(self) -> None:
        result = check_output("Based on the symptoms, I diagnose contact dermatitis.")
        assert result.passed is False
        assert any("diagnos" in v.lower() for v in result.violations)

    def test_prescription_detected(self) -> None:
        result = check_output("I prescribe a course of steroids for the rash.")
        assert result.passed is False
        assert any("prescri" in v.lower() for v in result.violations)

    def test_prohibited_phrase_detected(self) -> None:
        result = check_output("As your doctor, I advise you to stop working immediately.")
        assert result.passed is False
        assert any("as your doctor" in v.lower() for v in result.violations)

    def test_medical_advice_detected(self) -> None:
        result = check_output("This constitutes medical advice for your condition.")
        assert result.passed is False
        assert any("medical advice" in v.lower() for v in result.violations)

    def test_clinical_decision_detected(self) -> None:
        result = check_output("This is a clinical decision that requires immediate action.")
        assert result.passed is False

    def test_diagnostic_spirometry_allowed(self) -> None:
        result = check_output(
            "The workflow components include a diagnostic spirometry step "
            "to be performed by a qualified OHN as part of surveillance."
        )
        assert result.passed is True

    def test_referral_when_diagnosed_allowed(self) -> None:
        result = check_output(
            "Refer to the occupational health physician if dermatitis is diagnosed "
            "following skin surveillance."
        )
        assert result.passed is True

    def test_disclaimer_with_diagnosis_allowed(self) -> None:
        result = check_parsed_content(
            {
                "steps": [
                    {
                        "description": (
                            "This does not constitute clinical advice or diagnosis; "
                            "refer for clinical assessment if indicated."
                        )
                    }
                ]
            }
        )
        assert result.passed is True

    def test_multiple_violations(self) -> None:
        result = check_output("I diagnose asthma. I prescribe an inhaler. As your doctor, take this.")
        assert result.passed is False
        assert len(result.violations) >= 3


class TestDisclaimers:
    def test_disclaimers_appended(self) -> None:
        text = "Workflow step 1: Conduct baseline health questionnaire."
        result = append_disclaimers(text)
        assert "Important Notices" in result
        for disclaimer in MANDATORY_DISCLAIMERS:
            assert disclaimer in result

    def test_disclaimers_not_duplicated(self) -> None:
        text = "Some output."
        result = append_disclaimers(text)
        for disclaimer in MANDATORY_DISCLAIMERS:
            assert result.count(disclaimer) == 1

    def test_fourth_disclaimer_present(self) -> None:
        assert len(MANDATORY_DISCLAIMERS) >= 4
        assert "risk assessments" in MANDATORY_DISCLAIMERS[3].lower()


class TestSystemPrompt:
    def test_guardrail_prompt_contains_hard_constraints(self) -> None:
        lower = SYSTEM_GUARDRAIL_PROMPT.lower()
        assert "clinical diagnos" in lower
        assert "professional judgement" in lower
        assert "duty holder" in lower

    def test_guardrail_prompt_requires_sources(self) -> None:
        assert "HSE" in SYSTEM_GUARDRAIL_PROMPT
        assert "cite" in SYSTEM_GUARDRAIL_PROMPT.lower()

    def test_guardrail_prompt_pdca_reference(self) -> None:
        assert "Plan-Do-Check-Act" in SYSTEM_GUARDRAIL_PROMPT

    def test_guardrail_prompt_new_boundaries(self) -> None:
        lower = SYSTEM_GUARDRAIL_PROMPT.lower()
        assert "risk assessments" in lower
        assert "exposure monitoring" in lower
        assert "ethical boundaries" in lower
        assert "hswa 1974" in lower

    def test_guardrail_prompt_requires_consistent_roles_and_terminology(self) -> None:
        lower = SYSTEM_GUARDRAIL_PROMPT.lower()
        assert "consistent role assignments across surveillance provisions and workflow steps" in lower
        assert "interpretation requires an oh professional" in lower
        assert "audiometry, not colloquial 'hearing test'" in lower


class TestWorkflowConsistencyRules:
    def test_rules_cover_roles_terminology_and_section_purpose(self) -> None:
        lower = " ".join(WORKFLOW_CONSISTENCY_RULES.lower().split())
        assert "audiometry" in lower
        assert "competence_required and responsible_role" in lower
        assert "interpretation requires an oh professional" in lower
        assert "statutory checks and competence requirements" in lower
        assert "operational sequence" in lower
        assert "hierarchy of controls" in lower
        assert "seqohs" in lower
        assert "20 hand washes" in lower
        assert "unilateral hearing loss" in lower
