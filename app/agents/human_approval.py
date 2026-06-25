"""Deterministic in-memory human approval workflow helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
import hashlib
from typing import Any

from app.agents.guardrail_enforcement import EnforcementOutcome, EnforcementResult


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


DEFAULT_APPROVAL_TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    requested_action: str
    requested_by: str
    required_approver_role: str
    status: ApprovalStatus
    policy_categories: tuple[str, ...]
    findings: tuple[dict[str, str], ...]
    created_timestamp: datetime
    decision_timestamp: datetime | None = None
    decision_reason: str | None = None
    decided_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["policy_categories"] = list(self.policy_categories)
        data["findings"] = list(self.findings)
        data["created_timestamp"] = self.created_timestamp.isoformat()
        data["decision_timestamp"] = self.decision_timestamp.isoformat() if self.decision_timestamp else None
        return data


@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    status: ApprovalStatus
    decided_by: str
    decision_timestamp: datetime
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["decision_timestamp"] = self.decision_timestamp.isoformat()
        return data


def create_approval_request(
    enforcement_result: EnforcementResult,
    *,
    requested_action: str,
    requested_by: str,
    created_timestamp: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> ApprovalRequest:
    if enforcement_result.enforcement_outcome == EnforcementOutcome.BLOCKED:
        raise ValueError("Blocked actions cannot be sent for approval.")
    if enforcement_result.enforcement_outcome != EnforcementOutcome.REQUIRES_APPROVAL:
        raise ValueError("Only actions that require approval can create approval requests.")

    categories = tuple(sorted({finding.category for finding in enforcement_result.findings}))
    findings = tuple(finding.to_dict() for finding in enforcement_result.findings)
    approver_role = enforcement_result.required_approval_type or required_role_for_categories(categories)
    approval_id = _stable_id(
        "approval",
        enforcement_result.enforcement_id,
        requested_action,
        requested_by,
        approver_role,
    )
    return ApprovalRequest(
        approval_id=approval_id,
        requested_action=requested_action,
        requested_by=requested_by,
        required_approver_role=approver_role,
        status=ApprovalStatus.PENDING,
        policy_categories=categories,
        findings=findings,
        created_timestamp=created_timestamp or DEFAULT_APPROVAL_TIMESTAMP,
        metadata={
            "enforcement_id": enforcement_result.enforcement_id,
            "correlation_id": enforcement_result.metadata.get("correlation_id"),
            **(metadata or {}),
        },
    )


def approve_pending_request(
    request: ApprovalRequest,
    *,
    decided_by: str,
    reason: str,
    decision_timestamp: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[ApprovalRequest, ApprovalDecision]:
    return _decide_request(
        request,
        status=ApprovalStatus.APPROVED,
        decided_by=decided_by,
        reason=reason,
        decision_timestamp=decision_timestamp,
        metadata=metadata,
    )


def reject_pending_request(
    request: ApprovalRequest,
    *,
    decided_by: str,
    reason: str,
    decision_timestamp: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[ApprovalRequest, ApprovalDecision]:
    return _decide_request(
        request,
        status=ApprovalStatus.REJECTED,
        decided_by=decided_by,
        reason=reason,
        decision_timestamp=decision_timestamp,
        metadata=metadata,
    )


def required_role_for_categories(categories: tuple[str, ...] | list[str] | set[str]) -> str:
    category_set = set(categories)
    if "destructive_operation" in category_set:
        return "admin"
    if category_set & {"data_leakage", "secrets_exfiltration", "prompt_injection", "instruction_override"}:
        return "security_reviewer"
    if "unauthorized_financial_action" in category_set:
        return "risk_manager"
    if "approval_bypass" in category_set:
        return "risk_manager"
    return "risk_manager"


def _decide_request(
    request: ApprovalRequest,
    *,
    status: ApprovalStatus,
    decided_by: str,
    reason: str,
    decision_timestamp: datetime | None,
    metadata: dict[str, Any] | None,
) -> tuple[ApprovalRequest, ApprovalDecision]:
    if request.status != ApprovalStatus.PENDING:
        raise ValueError(f"Approval request is already {request.status.value}.")
    timestamp = decision_timestamp or DEFAULT_APPROVAL_TIMESTAMP
    decision = ApprovalDecision(
        approval_id=request.approval_id,
        status=status,
        decided_by=decided_by,
        decision_timestamp=timestamp,
        reason=reason,
        metadata=metadata or {},
    )
    updated_request = replace(
        request,
        status=status,
        decision_timestamp=timestamp,
        decision_reason=reason,
        decided_by=decided_by,
        metadata={**request.metadata, **(metadata or {})},
    )
    return updated_request, decision


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
