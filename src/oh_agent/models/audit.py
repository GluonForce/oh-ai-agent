"""Audit trail models for regulatory compliance.

Every agent action is recorded with full provenance so that
outputs are traceable and defensible in a regulated environment.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from uuid_extensions import uuid7


class AuditEventType(StrEnum):
    """Categories of auditable events, aligned to PDCA phases."""

    # PLAN
    RISK_ASSESSMENT_CONFIRMED = "risk_assessment_confirmed"
    WORKFLOW_REQUESTED = "workflow_requested"
    # DO
    WORKFLOW_GENERATED = "workflow_generated"
    # CHECK
    COMPLIANCE_AUDIT_REQUESTED = "compliance_audit_requested"
    COMPLIANCE_AUDIT_GENERATED = "compliance_audit_generated"
    # REVIEW
    TREND_ANALYSIS_REQUESTED = "trend_analysis_requested"
    TREND_ANALYSIS_GENERATED = "trend_analysis_generated"
    # ACT
    IMPROVEMENT_PLAN_REQUESTED = "improvement_plan_requested"
    IMPROVEMENT_PLAN_GENERATED = "improvement_plan_generated"
    # Knowledge & system
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    DOCUMENT_INGESTED = "document_ingested"
    GUARDRAIL_TRIGGERED = "guardrail_triggered"
    ERROR = "error"


class AuditEntry(BaseModel):
    """Immutable audit log entry."""

    id: str = Field(default_factory=lambda: str(uuid7()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: AuditEventType
    request_id: str | None = None
    actor: str = "system"
    detail: dict[str, Any] = Field(default_factory=dict)
    sources_used: list[str] = Field(default_factory=list)
    model_used: str | None = None
    guardrails_applied: list[str] = Field(default_factory=list)
