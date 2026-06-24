"""End-to-end deterministic secure workflow evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.agents.audit_trail import AuditEvent, AuditEventType, append_audit_event, build_audit_event
from app.agents.guardrail_enforcement import EnforcementOutcome, EnforcementResult, enforce_policy_result
from app.agents.human_approval import ApprovalDecision, ApprovalRequest, ApprovalStatus, create_approval_request
from app.agents.security_policy import PolicyResult, evaluate_security_policy


@dataclass(frozen=True)
class SecureWorkflowResult:
    policy_result: PolicyResult
    enforcement_result: EnforcementResult
    approval_request: ApprovalRequest | None
    audit_events: tuple[AuditEvent, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_result": self.policy_result.to_dict(),
            "enforcement_result": self.enforcement_result.to_dict(),
            "approval_request": self.approval_request.to_dict() if self.approval_request else None,
            "audit_events": [event.to_dict() for event in self.audit_events],
        }


def evaluate_secure_action(
    action_text: str,
    actor: str,
    metadata: dict[str, Any] | None = None,
    *,
    timestamp: datetime | None = None,
) -> SecureWorkflowResult:
    workflow_metadata = metadata or {}
    policy_result = evaluate_security_policy(action_text, metadata=workflow_metadata)
    enforcement_result = enforce_policy_result(
        policy_result,
        action_text=action_text,
        actor=actor,
        metadata=workflow_metadata,
    )
    categories = tuple(finding.category for finding in policy_result.findings)
    finding_ids = tuple(finding.finding_id for finding in policy_result.findings)
    correlation_id = enforcement_result.metadata["correlation_id"]
    audit_events: list[AuditEvent] = []

    append_audit_event(
        audit_events,
        build_audit_event(
            event_type=AuditEventType.POLICY_CHECKED,
            actor=actor,
            action=action_text,
            decision=policy_result.decision.value,
            outcome=enforcement_result.enforcement_outcome.value,
            categories=categories,
            finding_ids=finding_ids,
            correlation_id=correlation_id,
            timestamp=timestamp,
            metadata=workflow_metadata,
        ),
    )

    approval_request = None
    if enforcement_result.enforcement_outcome == EnforcementOutcome.ALLOWED:
        event_type = AuditEventType.ACTION_ALLOWED
    elif enforcement_result.enforcement_outcome == EnforcementOutcome.BLOCKED:
        event_type = AuditEventType.ACTION_BLOCKED
    else:
        approval_request = create_approval_request(
            enforcement_result,
            requested_action=action_text,
            requested_by=actor,
            created_timestamp=timestamp,
            metadata=workflow_metadata,
        )
        event_type = AuditEventType.APPROVAL_REQUESTED

    append_audit_event(
        audit_events,
        build_audit_event(
            event_type=event_type,
            actor=actor,
            action=action_text,
            decision=policy_result.decision.value,
            outcome=enforcement_result.enforcement_outcome.value,
            categories=categories,
            finding_ids=finding_ids,
            correlation_id=correlation_id,
            timestamp=timestamp,
            metadata={
                **workflow_metadata,
                "approval_id": approval_request.approval_id if approval_request else None,
                "enforcement_id": enforcement_result.enforcement_id,
            },
        ),
    )

    return SecureWorkflowResult(
        policy_result=policy_result,
        enforcement_result=enforcement_result,
        approval_request=approval_request,
        audit_events=tuple(audit_events),
    )


def build_approval_decision_audit_event(
    approval_request: ApprovalRequest,
    approval_decision: ApprovalDecision,
    *,
    actor: str | None = None,
    timestamp: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    if approval_decision.status == ApprovalStatus.APPROVED:
        event_type = AuditEventType.APPROVAL_APPROVED
    elif approval_decision.status == ApprovalStatus.REJECTED:
        event_type = AuditEventType.APPROVAL_REJECTED
    else:
        raise ValueError(f"Approval decision status {approval_decision.status.value!r} is not auditable as a decision.")

    return build_audit_event(
        event_type=event_type,
        actor=actor or approval_decision.decided_by,
        action=approval_request.requested_action,
        decision=approval_decision.status.value,
        outcome=approval_decision.status.value,
        categories=approval_request.policy_categories,
        finding_ids=[finding["finding_id"] for finding in approval_request.findings],
        correlation_id=str(approval_request.metadata.get("correlation_id") or approval_request.approval_id),
        timestamp=timestamp or approval_decision.decision_timestamp,
        metadata={
            "approval_id": approval_request.approval_id,
            "decision_reason": approval_decision.reason,
            **(metadata or {}),
        },
    )
