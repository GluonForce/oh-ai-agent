"""Tests for benchmark and compliance audit agent prompts."""

from __future__ import annotations

from oh_agent.agents.benchmark_agent import _COMPLIANCE_AUDIT_PROMPT


def test_compliance_audit_prompt_requests_new_assessment_flags() -> None:
    assert "methodology_assessed" in _COMPLIANCE_AUDIT_PROMPT
    assert "escalation_process_assessed" in _COMPLIANCE_AUDIT_PROMPT
