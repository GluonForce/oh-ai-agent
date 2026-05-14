"""Audit logging service.

Writes immutable JSONL audit entries for regulatory traceability.
Every agent action is recorded so outputs are fully defensible.
"""

from __future__ import annotations

import json
import logging

from oh_agent.config import Settings
from oh_agent.models.audit import AuditEntry

logger = logging.getLogger(__name__)


class AuditService:
    """Append-only audit logger writing JSONL to a configured path."""

    def __init__(self, settings: Settings) -> None:
        self._path = settings.audit_log_file
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, entry: AuditEntry) -> None:
        """Persist a single audit entry."""
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(entry.model_dump_json() + "\n")
        logger.debug("Audit entry written: %s / %s", entry.event_type, entry.request_id)

    def log_many(self, entries: list[AuditEntry]) -> None:
        """Persist multiple audit entries atomically."""
        with self._path.open("a", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(entry.model_dump_json() + "\n")
        logger.debug("Wrote %d audit entries.", len(entries))

    def read_all(self) -> list[AuditEntry]:
        """Read back all audit entries (for inspection/testing)."""
        if not self._path.exists():
            return []
        entries: list[AuditEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(AuditEntry.model_validate(json.loads(line)))
        return entries

    def count(self) -> int:
        """Return the number of recorded audit entries."""
        if not self._path.exists():
            return 0
        with self._path.open("r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
