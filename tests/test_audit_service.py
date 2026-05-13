"""Tests for the audit logging service."""

from __future__ import annotations

from oh_agent.models.audit import AuditEntry, AuditEventType
from oh_agent.services.audit_service import AuditService


class TestAuditService:
    def test_log_and_read_back(self, audit_service: AuditService) -> None:
        entry = AuditEntry(
            event_type=AuditEventType.WORKFLOW_REQUESTED,
            request_id="test-req-1",
            detail={"organisation": "Test Org"},
        )
        audit_service.log(entry)
        entries = audit_service.read_all()
        assert len(entries) == 1
        assert entries[0].request_id == "test-req-1"

    def test_log_many(self, audit_service: AuditService) -> None:
        entries = [AuditEntry(event_type=AuditEventType.WORKFLOW_REQUESTED, request_id=f"req-{i}") for i in range(5)]
        audit_service.log_many(entries)
        assert audit_service.count() == 5

    def test_count_empty(self, audit_service: AuditService) -> None:
        assert audit_service.count() == 0

    def test_read_all_empty(self, audit_service: AuditService) -> None:
        assert audit_service.read_all() == []

    def test_entries_are_immutable_on_disk(self, audit_service: AuditService) -> None:
        entry = AuditEntry(
            event_type=AuditEventType.GUARDRAIL_TRIGGERED,
            detail={"violations": ["test violation"]},
        )
        audit_service.log(entry)
        original_id = audit_service.read_all()[0].id

        audit_service.log(AuditEntry(event_type=AuditEventType.WORKFLOW_GENERATED))
        entries = audit_service.read_all()
        assert len(entries) == 2
        assert entries[0].id == original_id
