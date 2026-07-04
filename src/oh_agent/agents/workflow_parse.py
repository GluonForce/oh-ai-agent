"""Normalise and coerce LLM workflow JSON before Pydantic validation."""

from __future__ import annotations

import json
import re
from typing import Any

from oh_agent.models.workflow import ComplianceRating, SurveillanceType, WorkflowComponent

_COMPONENT_ALIASES: dict[str, str] = {
    "spirometry": WorkflowComponent.LUNG_FUNCTION_TEST.value,
    "lung_function": WorkflowComponent.LUNG_FUNCTION_TEST.value,
    "lung_function_test": WorkflowComponent.LUNG_FUNCTION_TEST.value,
    "skin_check": WorkflowComponent.SKIN_ASSESSMENT.value,
    "skin": WorkflowComponent.SKIN_ASSESSMENT.value,
    "questionnaire": WorkflowComponent.HEALTH_QUESTIONNAIRE.value,
    "health_surveillance": WorkflowComponent.HEALTH_QUESTIONNAIRE.value,
    "clinical_exam": WorkflowComponent.CLINICAL_ASSESSMENT.value,
    "examination": WorkflowComponent.CLINICAL_ASSESSMENT.value,
    "fitness": WorkflowComponent.FITNESS_FOR_TASK.value,
    "education": WorkflowComponent.HEALTH_EDUCATION.value,
    "records": WorkflowComponent.RECORD_KEEPING.value,
    "record_keeping": WorkflowComponent.RECORD_KEEPING.value,
}

_SURVEILLANCE_ALIASES: dict[str, str] = {
    "lung_function_test": SurveillanceType.SPIROMETRY.value,
    "lung_function": SurveillanceType.SPIROMETRY.value,
    "skin_assessment": SurveillanceType.SKIN_CHECK.value,
    "skin": SurveillanceType.SKIN_CHECK.value,
    "havs": SurveillanceType.HAVS_QUESTIONNAIRE.value,
    "hand_arm_vibration": SurveillanceType.HAVS_QUESTIONNAIRE.value,
    "noise": SurveillanceType.AUDIOMETRY.value,
    "audiometric": SurveillanceType.AUDIOMETRY.value,
    "clinical_assessment": SurveillanceType.CLINICAL_EXAMINATION.value,
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _coerce_enum(value: Any, allowed: set[str], aliases: dict[str, str], default: str) -> str:
    if value is None:
        return default
    raw = _slug(str(value))
    if raw in allowed:
        return raw
    if raw in aliases:
        return aliases[raw]
    for key, target in aliases.items():
        if key in raw or raw in key:
            return target
    for candidate in allowed:
        if candidate in raw or raw in candidate:
            return candidate
    return default


def _coerce_compliance_status(value: Any) -> str:
    return _coerce_enum(
        value,
        {m.value for m in ComplianceRating},
        {
            "partial": ComplianceRating.PARTIALLY_COMPLIANT.value,
            "non_compliant": ComplianceRating.NON_COMPLIANT.value,
            "noncompliant": ComplianceRating.NON_COMPLIANT.value,
            "compliant": ComplianceRating.COMPLIANT.value,
            "not_assessed": ComplianceRating.NOT_ASSESSED.value,
            "unknown": ComplianceRating.NOT_ASSESSED.value,
        },
        ComplianceRating.NOT_ASSESSED.value,
    )


def extract_json_object(raw: str) -> dict[str, Any]:
    """Extract a JSON object from an LLM response (markdown fences, preamble, etc.)."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found in LLM response", raw, 0)
    return json.loads(cleaned[start : end + 1])  # type: ignore[no-any-return]


def coerce_workflow_payload(parsed: dict[str, Any]) -> dict[str, Any]:
    """Fill defaults and normalise enum-like fields from LLM output."""
    allowed_components = {m.value for m in WorkflowComponent}
    allowed_surveillance = {m.value for m in SurveillanceType}

    provisions: list[dict[str, Any]] = []
    for item in parsed.get("surveillance_provisions") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["surveillance_type"] = _coerce_enum(
            row.get("surveillance_type"),
            allowed_surveillance,
            _SURVEILLANCE_ALIASES,
            SurveillanceType.HEALTH_QUESTIONNAIRE.value,
        )
        row.setdefault("description", "Health surveillance provision")
        row.setdefault("frequency", "As per HSE guidance")
        row.setdefault("competence_required", "Competent occupational health professional")
        row.setdefault("regulatory_basis", "UK health and safety legislation")
        provisions.append(row)

    steps: list[dict[str, Any]] = []
    for idx, item in enumerate(parsed.get("steps") or [], start=1):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["order"] = int(row.get("order") or idx)
        row["component"] = _coerce_enum(
            row.get("component"),
            allowed_components,
            _COMPONENT_ALIASES,
            WorkflowComponent.HEALTH_QUESTIONNAIRE.value,
        )
        row.setdefault("description", "Workflow step")
        row.setdefault("responsible_role", "OHN")
        row.setdefault("frequency", "As per programme")
        row.setdefault("regulatory_basis", "UK health and safety legislation")
        steps.append(row)

    assurance: list[dict[str, Any]] = []
    for item in parsed.get("assurance_checks") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["status"] = _coerce_compliance_status(row.get("status"))
        row.setdefault("area", "Assurance")
        row.setdefault("question", "Compliance check")
        assurance.append(row)

    governance: list[dict[str, Any]] = []
    for item in parsed.get("governance_prompts") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        roles = row.get("applicable_roles")
        if isinstance(roles, str):
            row["applicable_roles"] = [roles]
        elif not roles:
            row["applicable_roles"] = ["OHN", "OHP"]
        row.setdefault("prompt_text", "Apply professional judgement before delegation.")
        row.setdefault("regulatory_reference", "HSG61")
        governance.append(row)

    improvements: list[dict[str, Any]] = []
    for item in parsed.get("improvement_actions") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("area", "Continuous improvement")
        row.setdefault("action", "Review controls")
        row.setdefault("rationale", "Based on surveillance outcomes")
        row.setdefault("priority", "medium")
        improvements.append(row)

    trends: list[dict[str, Any]] = []
    for item in parsed.get("trend_insights") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("area", "Surveillance")
        row.setdefault("observation", "To be reviewed")
        row.setdefault("implication", "Requires professional review")
        trends.append(row)

    parsed["surveillance_provisions"] = provisions
    parsed["steps"] = steps
    parsed["assurance_checks"] = assurance
    parsed["governance_prompts"] = governance
    parsed["improvement_actions"] = improvements
    parsed["trend_insights"] = trends
    return parsed
