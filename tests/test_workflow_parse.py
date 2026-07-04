"""Tests for LLM workflow JSON extraction and coercion."""

from __future__ import annotations

import pytest

from oh_agent.agents.workflow_parse import coerce_workflow_payload, extract_json_object


class TestExtractJsonObject:
    def test_markdown_fence(self) -> None:
        raw = '```json\n{"steps": []}\n```'
        assert extract_json_object(raw) == {"steps": []}

    def test_preamble_before_json(self) -> None:
        raw = 'Here is the workflow:\n\n{"steps": [{"order": 1}]}'
        data = extract_json_object(raw)
        assert data["steps"][0]["order"] == 1


class TestCoerceWorkflowPayload:
    def test_normalizes_component_aliases(self) -> None:
        parsed = coerce_workflow_payload(
            {
                "steps": [
                    {
                        "order": 1,
                        "component": "Spirometry",
                        "description": "Lung function test",
                    }
                ]
            }
        )
        assert parsed["steps"][0]["component"] == "lung_function_test"

    def test_normalizes_compliance_status(self) -> None:
        parsed = coerce_workflow_payload(
            {"assurance_checks": [{"area": "A", "question": "Q?", "status": "Partially Compliant"}]}
        )
        assert parsed["assurance_checks"][0]["status"] == "partially_compliant"

    def test_missing_surveillance_fields_get_defaults(self) -> None:
        parsed = coerce_workflow_payload(
            {"surveillance_provisions": [{"surveillance_type": "skin_check", "description": "Skin"}]}
        )
        row = parsed["surveillance_provisions"][0]
        assert row["frequency"]
        assert row["competence_required"]
        assert row["regulatory_basis"]
