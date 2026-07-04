"""Compliance guardrails for regulated healthcare environments.

These guardrails enforce the hard boundaries defined in the new spec
(Section 10 — Regulatory Safeguards and Boundaries):
- No clinical diagnoses or decisions
- No replacement of professional judgement
- No conduct of risk assessments or exposure monitoring
- No assumption of duty holder accountability
- No operation outside defined regulatory and ethical boundaries

Checks target *clinical assertions* (e.g. "I diagnose you"), not legitimate OH
language such as referral pathways, disclaimers, or "diagnostic spirometry".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# First-person / directive clinical assertions — not general OH surveillance language
CLINICAL_ASSERTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bi\s+diagnos(?:e|is|ed|ing)\b",
        r"\bi\s+have\s+diagnosed\b",
        r"\bmy\s+diagnosis\b",
        r"\byou\s+(?:have|are)\s+diagnosed\b",
        r"\bthe\s+diagnosis\s+is\b",
        r"\bi\s+prescri(?:be|ption|bed|bing)\b",
        r"\bi\s+recommend\s+(?:that\s+you\s+)?(?:take|use)\b",
        r"\btreat(?:ment|ing|ed)\b[^.]{0,80}\brecommend(?:ed|ation)?\b",
        r"\byou (?:have|are suffering|should take)\b",
        r"\bthis\s+is\s+medical\s+advice\b",
        r"\bconstitutes\s+medical\s+advice\b",
        r"\bi\s+provide\s+medical\s+advice\b",
        r"\bclinical decision\b",
        r"\bfit.?note\b",
        r"\bsick.?note\b",
        r"\breturn.to.work.*(?:cleared|approved)\b",
    ]
]

# Nearby phrasing that makes an otherwise risky term acceptable in OH workflows
SAFE_CONTEXT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"does\s+not\s+(?:constitute|provide|offer).{0,50}diagnos",
        r"not\s+(?:a\s+)?(?:clinical\s+)?diagnos",
        r"without\s+(?:a\s+)?diagnos",
        r"no\s+clinical\s+diagnos",
        r"refer(?:ral)?\s+(?:to|for|if).{0,60}diagnos",
        r"if\s+.{0,40}diagnosed",
        r"when\s+.{0,40}diagnosed",
        r"undiagnosed",
        r"diagnostic\s+(?:testing|spirometry|assessment|questionnaire|procedure)",
        r"support.{0,30}not.{0,40}diagnos",
        r"does\s+not\s+(?:constitute|provide).{0,50}medical\s+advice",
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
    (
        "This tool does not conduct risk assessments or exposure monitoring, and does not "
        "operate outside defined regulatory and ethical boundaries."
    ),
]

_GUARD_RETRY_HINT = (
    "Your previous response was blocked by compliance guardrails. "
    "Regenerate valid JSON only. Do NOT make clinical diagnoses or prescribe treatment. "
    "Use OH surveillance language only: screening, referral, assessment, monitoring. "
    "Avoid first-person clinical phrasing (e.g. 'I diagnose', 'you are diagnosed'). "
    "You may refer workers for clinical assessment when findings are abnormal."
)


@dataclass
class GuardrailResult:
    """Outcome of a guardrail check."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    sanitised_text: str = ""
    disclaimers_appended: bool = False


class GuardrailViolation(Exception):
    """Raised when LLM output fails compliance checks after retry."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__("; ".join(violations))


def _window(text: str, start: int, end: int, *, radius: int = 100) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)]


def _has_safe_context(text: str, start: int, end: int) -> bool:
    window = _window(text, start, end)
    return any(p.search(window) for p in SAFE_CONTEXT_PATTERNS)


def check_output(text: str) -> GuardrailResult:
    """Run compliance checks on narrative text (not raw JSON structure)."""
    violations: list[str] = []

    for pattern in CLINICAL_ASSERTION_PATTERNS:
        for match in pattern.finditer(text):
            if _has_safe_context(text, match.start(), match.end()):
                continue
            violations.append(
                f"Clinical-assertion pattern detected: '{pattern.pattern}' matched '{match.group(0)}'"
            )
            break  # one violation per pattern is enough

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


def collect_string_values(obj: Any) -> list[str]:
    """Recursively collect string leaf values from parsed LLM JSON."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        parts: list[str] = []
        for value in obj.values():
            parts.extend(collect_string_values(value))
        return parts
    if isinstance(obj, list):
        parts = []
        for item in obj:
            parts.extend(collect_string_values(item))
        return parts
    return []


def check_parsed_content(parsed: dict[str, Any]) -> GuardrailResult:
    """Check guardrails on workflow JSON content fields only."""
    fields = collect_string_values(parsed)
    combined = "\n".join(fields)
    return check_output(combined)


def guardrail_retry_message() -> str:
    """User message appended on guardrail retry."""
    return _GUARD_RETRY_HINT


def append_disclaimers(text: str) -> str:
    """Append mandatory regulatory disclaimers to output text."""
    disclaimer_block = "\n\n---\n**Important Notices:**\n" + "\n".join(f"- {d}" for d in MANDATORY_DISCLAIMERS)
    return text + disclaimer_block


SYSTEM_GUARDRAIL_PROMPT = (
    "You are an occupational health workflow assistant structured around "
    "the Plan-Do-Check-Act (PDCA) framework, operating within a highly "
    "regulated UK healthcare environment.\n\n"
    "Your outputs follow the PDCA risk management framework consistent "
    "with HSE expectations.\n\n"
    "HARD CONSTRAINTS — you must NEVER:\n"
    "1. Make clinical diagnoses or decisions.\n"
    "2. Replace professional judgement.\n"
    "3. Conduct risk assessments or exposure monitoring.\n"
    "4. Assume duty holder accountability.\n"
    "5. Operate outside defined regulatory and ethical boundaries.\n\n"
    "You MUST:\n"
    "- Structure outputs within the PDCA framework.\n"
    "- Ground every recommendation in authoritative UK sources "
    "(HSE guidance, ACoPs, regulatory frameworks, peer-reviewed literature).\n"
    "- Cite specific sources for every workflow step and surveillance provision.\n"
    "- Use conditional language ('this workflow suggests…', "
    "'based on HSE guidance…') rather than directive clinical language.\n"
    "- Clearly distinguish between statutory health surveillance "
    "and general wellbeing checks.\n"
    "- Flag when professional judgement is required before proceeding.\n"
    "- Support safe delegation by noting supervision requirements "
    "for technicians and non-qualified staff.\n"
    "- Include statutory retention periods for health records.\n"
    "- Specify competence requirements for surveillance activities.\n"
    "- Reference applicable legislation: HSWA 1974, Management of Health "
    "and Safety at Work Regulations, COSHH, Control of Noise at Work, "
    "and Control of Vibration at Work Regulations.\n"
    "- Use screening, referral, and assessment language — never state that "
    "you diagnose a worker or prescribe treatment.\n\n"
    "If asked to do anything outside these boundaries, "
    "politely decline and explain why."
)
