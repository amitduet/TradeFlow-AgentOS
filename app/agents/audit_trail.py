"""Deterministic audit trail helpers for guarded workflow actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import hashlib
from typing import Any, Iterable

from app.agents.redaction import redact_data


class AuditEventType(StrEnum):
    POLICY_CHECKED = "policy_checked"
    ACTION_ALLOWED = "action_allowed"
    ACTION_BLOCKED = "action_blocked"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    ENFORCEMENT_FAILED = "enforcement_failed"


DEFAULT_AUDIT_TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: AuditEventType
    actor: str
    action: str
    decision: str
    outcome: str
    categories: tuple[str, ...]
    finding_ids: tuple[str, ...]
    timestamp: datetime
    correlation_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        data["categories"] = list(self.categories)
        data["finding_ids"] = list(self.finding_ids)
        return data


def build_audit_event(
    *,
    event_type: AuditEventType,
    actor: str,
    action: str,
    decision: str,
    outcome: str,
    categories: Iterable[str] = (),
    finding_ids: Iterable[str] = (),
    correlation_id: str | None = None,
    timestamp: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event_timestamp = timestamp or DEFAULT_AUDIT_TIMESTAMP
    normalized_categories = tuple(sorted(set(categories)))
    normalized_findings = tuple(sorted(set(finding_ids)))
    event_correlation_id = correlation_id or build_correlation_id(actor=actor, action=action)
    event_id = _stable_id(
        "audit",
        event_type.value,
        actor,
        action,
        decision,
        outcome,
        event_correlation_id,
        ",".join(normalized_categories),
        ",".join(normalized_findings),
    )
    return AuditEvent(
        event_id=event_id,
        event_type=event_type,
        actor=actor,
        action=action,
        decision=decision,
        outcome=outcome,
        categories=normalized_categories,
        finding_ids=normalized_findings,
        timestamp=event_timestamp,
        correlation_id=event_correlation_id,
        metadata=metadata or {},
    )


def append_audit_event(events: list[AuditEvent], event: AuditEvent) -> list[AuditEvent]:
    events.append(event)
    return events


def export_audit_events(events: Iterable[AuditEvent]) -> list[dict[str, Any]]:
    return [redact_audit_metadata(event.to_dict()) for event in events]


def redact_audit_metadata(value: dict[str, Any]) -> dict[str, Any]:
    return redact_data(value)


def build_correlation_id(*, actor: str, action: str) -> str:
    return _stable_id("correlation", actor, action)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
