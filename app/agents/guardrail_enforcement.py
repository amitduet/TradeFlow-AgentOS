"""Apply security policy decisions to deterministic workflow outcomes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
from typing import Any

from app.agents.audit_trail import build_correlation_id
from app.agents.security_policy import PolicyCategory, PolicyDecision, PolicyFinding, PolicyResult


class EnforcementOutcome(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    REQUIRES_APPROVAL = "requires_approval"


HIGH_RISK_BLOCK_CATEGORIES: frozenset[str] = frozenset(
    {
        PolicyCategory.SECRETS_EXFILTRATION.value,
        PolicyCategory.PROMPT_INJECTION.value,
        PolicyCategory.INSTRUCTION_OVERRIDE.value,
    }
)
HIGH_RISK_APPROVAL_CATEGORIES: frozenset[str] = frozenset(
    {
        PolicyCategory.UNAUTHORIZED_FINANCIAL_ACTION.value,
        PolicyCategory.DESTRUCTIVE_OPERATION.value,
        PolicyCategory.DATA_LEAKAGE.value,
        "approval_bypass",
    }
)
HIGH_RISK_CATEGORIES: frozenset[str] = HIGH_RISK_BLOCK_CATEGORIES | HIGH_RISK_APPROVAL_CATEGORIES


@dataclass(frozen=True)
class EnforcementResult:
    enforcement_id: str
    original_policy_decision: PolicyDecision
    enforcement_outcome: EnforcementOutcome
    reason: str
    findings: tuple[PolicyFinding, ...]
    required_approval_type: str | None
    audit_event_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["original_policy_decision"] = self.original_policy_decision.value
        data["enforcement_outcome"] = self.enforcement_outcome.value
        data["findings"] = [finding.to_dict() for finding in self.findings]
        return data


def enforce_policy_result(
    policy_result: PolicyResult,
    *,
    action_text: str,
    actor: str = "system",
    metadata: dict[str, Any] | None = None,
) -> EnforcementResult:
    categories = {finding.category for finding in policy_result.findings}
    outcome = _resolve_enforcement_outcome(policy_result.decision, categories)
    required_approval_type = _required_approval_type(categories) if outcome == EnforcementOutcome.REQUIRES_APPROVAL else None
    reason = _reason(policy_result.decision, outcome, categories)
    correlation_id = build_correlation_id(actor=actor, action=action_text)
    audit_event_id = _stable_id("audit", "enforcement", correlation_id, outcome.value)
    enforcement_id = _stable_id(
        "enforcement",
        policy_result.decision.value,
        outcome.value,
        action_text,
        actor,
        ",".join(sorted(categories)),
    )
    return EnforcementResult(
        enforcement_id=enforcement_id,
        original_policy_decision=policy_result.decision,
        enforcement_outcome=outcome,
        reason=reason,
        findings=policy_result.findings,
        required_approval_type=required_approval_type,
        audit_event_id=audit_event_id,
        metadata={
            "correlation_id": correlation_id,
            "high_risk_categories": sorted(categories & HIGH_RISK_CATEGORIES),
            **(metadata or {}),
        },
    )


def _resolve_enforcement_outcome(decision: PolicyDecision, categories: set[str]) -> EnforcementOutcome:
    if categories & HIGH_RISK_BLOCK_CATEGORIES:
        return EnforcementOutcome.BLOCKED
    if decision == PolicyDecision.BLOCK:
        return EnforcementOutcome.BLOCKED
    if decision == PolicyDecision.REVIEW or categories & HIGH_RISK_APPROVAL_CATEGORIES:
        return EnforcementOutcome.REQUIRES_APPROVAL
    return EnforcementOutcome.ALLOWED


def _required_approval_type(categories: set[str]) -> str | None:
    if PolicyCategory.DESTRUCTIVE_OPERATION.value in categories:
        return "admin"
    if categories & {PolicyCategory.DATA_LEAKAGE.value, PolicyCategory.SECRETS_EXFILTRATION.value}:
        return "security_reviewer"
    if categories & {PolicyCategory.PROMPT_INJECTION.value, PolicyCategory.INSTRUCTION_OVERRIDE.value}:
        return "security_reviewer"
    if categories & {PolicyCategory.UNAUTHORIZED_FINANCIAL_ACTION.value, "approval_bypass"}:
        return "risk_manager"
    return "risk_manager"


def _reason(decision: PolicyDecision, outcome: EnforcementOutcome, categories: set[str]) -> str:
    category_text = ", ".join(sorted(categories)) or "no policy findings"
    if outcome == EnforcementOutcome.ALLOWED:
        return "Policy allowed the action with no guardrail findings."
    if outcome == EnforcementOutcome.BLOCKED:
        return f"Policy decision {decision.value!r} produced blocked enforcement for: {category_text}."
    return f"Policy decision {decision.value!r} requires human approval for: {category_text}."


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
