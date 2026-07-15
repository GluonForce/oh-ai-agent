"""PII masking aligned to OpenAI Privacy Filter placeholder taxonomy.

Default provider uses regex heuristics so production stays lightweight.
Optional ``opf`` provider uses the open-weight OpenAI Privacy Filter when installed.
See https://openai.com/index/introducing-openai-privacy-filter/
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from oh_agent.config import Settings
    from oh_agent.models.hazard import HazardProfile, RiskAssessmentConfirmation
    from oh_agent.models.organisation import OrganisationProfile
    from oh_agent.models.workflow import (
        ComplianceAuditRequest,
        ImprovementPlanRequest,
        TrendAnalysisRequest,
        WorkflowRequest,
    )

logger = logging.getLogger(__name__)

PiiProvider = Literal["regex", "opf"]

# OpenAI Privacy Filter placeholder taxonomy
PLACEHOLDER = {
    "private_person": "[PRIVATE_PERSON]",
    "private_address": "[PRIVATE_ADDRESS]",
    "private_email": "[PRIVATE_EMAIL]",
    "private_phone": "[PRIVATE_PHONE]",
    "private_url": "[PRIVATE_URL]",
    "private_date": "[PRIVATE_DATE]",
    "account_number": "[ACCOUNT_NUMBER]",
    "secret": "[SECRET]",
}

# Order matters: apply secrets/emails before generic digit/person patterns.
_REGEX_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token|bearer)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
        PLACEHOLDER["secret"],
    ),
    (
        re.compile(r"(?i)\bsk-(?:proj-|or-v1-)?[A-Za-z0-9_-]{16,}"),
        PLACEHOLDER["secret"],
    ),
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        PLACEHOLDER["private_email"],
    ),
    (
        re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE),
        PLACEHOLDER["private_url"],
    ),
    (
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        PLACEHOLDER["account_number"],
    ),
    (
        re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b", re.IGNORECASE),
        PLACEHOLDER["account_number"],  # UK NI number-like
    ),
    (
        re.compile(r"\b\d{3}\s?\d{3}\s?\d{4}\b"),  # NHS-like
        PLACEHOLDER["account_number"],
    ),
    (
        re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.-])?(?:\(?0?\d{2,4}\)?[\s.-])?\d{3,4}[\s.-]\d{3,4}(?!\w)"),
        PLACEHOLDER["private_phone"],
    ),
    (
        re.compile(r"(?<!\w)\+44[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?!\w)"),
        PLACEHOLDER["private_phone"],
    ),
    (
        re.compile(r"(?<!\w)07\d{3}[\s.-]?\d{6}(?!\w)"),
        PLACEHOLDER["private_phone"],
    ),
    (
        re.compile(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
            re.IGNORECASE,
        ),
        PLACEHOLDER["private_date"],
    ),
    (
        re.compile(r"(?i)\b(?:my name is|i am|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"),
        PLACEHOLDER["private_person"],
    ),
    (
        re.compile(r"(?i)\b(?:dr\.?|mr\.?|mrs\.?|ms\.?|miss)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"),
        PLACEHOLDER["private_person"],
    ),
]


def mask_text_regex(text: str) -> str:
    """Apply heuristic redaction using Privacy Filter placeholder labels."""
    if not text:
        return text
    result = text
    for pattern, placeholder in _REGEX_RULES:
        if pattern.groups:
            # Keep leading phrase for "My name is …" style matches where useful
            result = pattern.sub(
                lambda m, ph=placeholder: (  # type: ignore[misc]
                    f"{m.group(0)[: m.start(1) - m.start(0)]}{ph}" if m.lastindex else ph
                ),
                result,
            )
        else:
            result = pattern.sub(placeholder, result)
    return result


class PiiMaskingService:
    """Mask PII in free text; default regex, optional OpenAI Privacy Filter (opf)."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        provider: PiiProvider = "regex",
        device: Literal["cpu", "cuda"] = "cpu",
    ) -> None:
        self.enabled = enabled
        self.provider: PiiProvider = provider
        self.device = device
        self._opf: Any | None = None
        self._opf_failed = False

    @classmethod
    def from_settings(cls, settings: Settings) -> PiiMaskingService:
        return cls(
            enabled=settings.pii_masking_enabled,
            provider=settings.pii_provider,  # type: ignore[arg-type]
            device=settings.pii_device,  # type: ignore[arg-type]
        )

    def mask(self, text: str | None) -> str | None:
        if text is None or not self.enabled:
            return text
        if not text.strip():
            return text
        if self.provider == "opf":
            redacted = self._mask_opf(text)
            if redacted is not None:
                return redacted
        return mask_text_regex(text)

    def _mask_opf(self, text: str) -> str | None:
        if self._opf_failed:
            return None
        try:
            if self._opf is None:
                from opf import OPF  # type: ignore[import-not-found]

                self._opf = OPF(device=self.device, output_text_only=True)
            result = self._opf.redact(text)
            return str(result)
        except Exception:
            self._opf_failed = True
            logger.warning(
                "OpenAI Privacy Filter (opf) unavailable; falling back to regex masking.",
                exc_info=True,
            )
            return None

    def mask_organisation(self, org: OrganisationProfile) -> OrganisationProfile:
        data = org.model_dump()
        data["name"] = self.mask(org.name) or org.name
        data["workforce_characteristics"] = self.mask(org.workforce_characteristics)
        data["existing_surveillance"] = self.mask(org.existing_surveillance)
        data["pre_existing_conditions"] = [self.mask(c) or c for c in org.pre_existing_conditions]
        # Sector/tasks are usually catalog values — only mask free-text-looking tasks
        data["tasks"] = [self.mask(t) or t for t in org.tasks]
        return org.__class__.model_validate(data)

    def mask_hazard(self, hazard: HazardProfile) -> HazardProfile:
        data = hazard.model_dump()
        for key in (
            "hazard_phrase",
            "substance_or_agent",
            "workplace_exposure_limit",
            "potential_health_effects",
            "existing_controls",
            "notes",
        ):
            data[key] = self.mask(data.get(key))
        return hazard.__class__.model_validate(data)

    def mask_risk_assessment(self, ra: RiskAssessmentConfirmation) -> RiskAssessmentConfirmation:
        data = ra.model_dump()
        data["assessor_name"] = self.mask(ra.assessor_name)
        data["additional_notes"] = self.mask(ra.additional_notes)
        return ra.__class__.model_validate(data)


def mask_text(text: str | None, settings: Settings | None = None) -> str | None:
    """Convenience wrapper using settings or regex defaults."""
    if settings is None:
        return mask_text_regex(text) if text is not None else None
    return PiiMaskingService.from_settings(settings).mask(text)


def mask_workflow_request(request: WorkflowRequest, settings: Settings) -> WorkflowRequest:
    """Return a request with free-text PII masked."""
    svc = PiiMaskingService.from_settings(settings)
    if not svc.enabled:
        return request
    return request.__class__(
        organisation=svc.mask_organisation(request.organisation),
        hazards=[svc.mask_hazard(h) for h in request.hazards],
        risk_assessment=svc.mask_risk_assessment(request.risk_assessment),
        additional_context=svc.mask(request.additional_context),
    )


def mask_org_hazards(
    organisation: OrganisationProfile,
    hazards: list[HazardProfile],
    settings: Settings,
) -> tuple[OrganisationProfile, list[HazardProfile]]:
    svc = PiiMaskingService.from_settings(settings)
    if not svc.enabled:
        return organisation, hazards
    return svc.mask_organisation(organisation), [svc.mask_hazard(h) for h in hazards]


def mask_trend_request(request: TrendAnalysisRequest, settings: Settings) -> TrendAnalysisRequest:
    svc = PiiMaskingService.from_settings(settings)
    if not svc.enabled:
        return request
    org, hazards = mask_org_hazards(request.organisation, request.hazards, settings)
    return request.__class__(
        organisation=org,
        hazards=hazards,
        surveillance_summary=svc.mask(request.surveillance_summary) or request.surveillance_summary,
    )


def mask_improvement_request(request: ImprovementPlanRequest, settings: Settings) -> ImprovementPlanRequest:
    svc = PiiMaskingService.from_settings(settings)
    if not svc.enabled:
        return request
    org, hazards = mask_org_hazards(request.organisation, request.hazards, settings)
    return request.__class__(
        organisation=org,
        hazards=hazards,
        surveillance_findings=svc.mask(request.surveillance_findings) or request.surveillance_findings,
    )


def mask_compliance_request(request: ComplianceAuditRequest, settings: Settings) -> ComplianceAuditRequest:
    svc = PiiMaskingService.from_settings(settings)
    if not svc.enabled:
        return request
    org, hazards = mask_org_hazards(request.organisation, request.hazards, settings)
    return request.__class__(organisation=org, hazards=hazards)
