"""Compliance guardrails for regulated healthcare environments.

These guardrails enforce the hard boundaries defined in the spec:
- No clinical decisions or diagnosis
- No personalised medical advice
- No removal of professional judgement
- No transfer of accountability from duty holders
- Not a replacement for risk assessment, exposure monitoring, or hierarchy of controls

Every LLM output passes through these checks before being returned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CLINICAL_DECISION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bdiagnos(?:e|is|ed|ing)\b",
        r"\bprescri(?:be|ption|bed|bing)\b",
        r"\btreat(?:ment|ing|ed)?\b.*\brecommend",
        r"\byou (?:have|are suffering|should take)\b",
        r"\bmedical advice\b",
        r"\bclinical decision\b",
        r"\bfit.?note\b",
        r"\bsick.?note\b",
        r"\breturn.to.work.*(?:cleared|approved)\b",
    ]
]

PROHIBITED_PHRASES: list[str] = [
    "I diagnose",
    "my diagnosis",
    "you should take",
    "I recommend treatment",
    "I advise you to",
    "clinical opinion",
    "medical opinion",
    "as your doctor",
    "as your physician",
]

MANDATORY_DISCLAIMERS: list[str] = [
    (
        "This output is generated to support occupational health practitioners and "
        "does not constitute clinical advice, diagnosis, or personalised medical guidance."
    ),
    (
        "Professional judgement by a qualified occupational health practitioner must be "
        "applied to all workflow outputs before implementation."
    ),
    ("Accountability for health and safety compliance remains with the duty holder at all times."),
]


@dataclass
class GuardrailResult:
    """Outcome of a guardrail check."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    sanitised_text: str = ""
    disclaimers_appended: bool = False


def check_output(text: str) -> GuardrailResult:
    """Run all guardrail checks against an LLM output string.

    Returns a *GuardrailResult* indicating whether the text is safe
    to return to the user, along with any violations found.
    """
    violations: list[str] = []

    for pattern in CLINICAL_DECISION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            violations.append(f"Clinical-decision pattern detected: '{pattern.pattern}' matched '{matches[0]}'")

    lower = text.lower()
    for phrase in PROHIBITED_PHRASES:
        if phrase.lower() in lower:
            violations.append(f"Prohibited phrase detected: '{phrase}'")

    passed = len(violations) == 0
    return GuardrailResult(
        passed=passed,
        violations=violations,
        sanitised_text=text if passed else "",
        disclaimers_appended=False,
    )


def append_disclaimers(text: str) -> str:
    """Append mandatory regulatory disclaimers to output text."""
    disclaimer_block = "\n\n---\n**Important Notices:**\n" + "\n".join(f"- {d}" for d in MANDATORY_DISCLAIMERS)
    return text + disclaimer_block


SYSTEM_GUARDRAIL_PROMPT = (
    "You are an occupational health workflow assistant operating "
    "within a highly regulated UK healthcare environment, "
    "structured around the Plan-Do-Check-Act (PDCA) framework.\n\n"
    "HARD CONSTRAINTS — you must NEVER:\n"
    "1. Make clinical diagnoses or decisions.\n"
    "2. Replace professional judgement.\n"
    "3. Conduct risk assessments or exposure monitoring.\n"
    "4. Assume duty holder accountability.\n"
    "5. Operate outside defined regulatory and ethical boundaries.\n\n"
    "Your role is to SUPPORT compliance, not substitute statutory duties.\n\n"
    "You MUST:\n"
    "- Structure outputs within the PDCA framework "
    "(Plan, Do, Check, Act).\n"
    "- Ground every recommendation in authoritative UK sources "
    "(HSE legislation, ACoPs, guidance, peer-reviewed evidence, "
    "established professional standards).\n"
    "- Cite specific sources for every workflow step.\n"
    "- Use conditional language ('this workflow suggests…', "
    "'based on HSE guidance…') rather than directive clinical language.\n"
    "- Clearly distinguish between statutory health surveillance "
    "and general wellbeing checks.\n"
    "- Flag when professional judgement is required.\n"
    "- Support safe delegation by noting supervision requirements.\n"
    "- Include statutory retention periods for health records.\n"
    "- Specify competence requirements for surveillance activities.\n\n"
    "If asked to do anything outside these boundaries, "
    "politely decline and explain why."
)
