"""Deterministic security policy checks for agent-facing requests."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import re
from typing import Any, Iterable


class PolicyDecision(StrEnum):
    """Allowed policy outcomes ordered from least to most restrictive."""

    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class PolicyCategory(StrEnum):
    PROMPT_INJECTION = "prompt_injection"
    SECRETS_EXFILTRATION = "secrets_exfiltration"
    UNSAFE_TOOL_REQUEST = "unsafe_tool_request"
    UNAUTHORIZED_FINANCIAL_ACTION = "unauthorized_financial_action"
    INSTRUCTION_OVERRIDE = "instruction_override"
    DATA_LEAKAGE = "data_leakage"
    DESTRUCTIVE_OPERATION = "destructive_operation"


@dataclass(frozen=True)
class PolicyFinding:
    finding_id: str
    severity: str
    category: str
    message: str
    matched_evidence: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyResult:
    decision: PolicyDecision
    findings: tuple[PolicyFinding, ...]
    normalized_input: str
    checked_categories: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "findings": [finding.to_dict() for finding in self.findings],
            "normalized_input": self.normalized_input,
            "checked_categories": list(self.checked_categories),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class _PolicyRule:
    finding_id: str
    severity: str
    category: PolicyCategory
    decision: PolicyDecision
    message: str
    patterns: tuple[str, ...]


CHECKED_CATEGORIES: tuple[str, ...] = tuple(category.value for category in PolicyCategory)


_RULES: tuple[_PolicyRule, ...] = (
    _PolicyRule(
        finding_id="SEC-PROMPT-INJECTION-001",
        severity="high",
        category=PolicyCategory.PROMPT_INJECTION,
        decision=PolicyDecision.BLOCK,
        message="Request attempts to override prior or higher-priority instructions.",
        patterns=(
            r"\bignore (all )?(previous|prior|earlier|above) (instructions|rules|policies)\b",
            r"\bforget (all )?(previous|prior|earlier|above) (instructions|rules|policies)\b",
            r"\bdisregard (all )?(previous|prior|earlier|above) (instructions|rules|policies)\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-INSTRUCTION-OVERRIDE-001",
        severity="high",
        category=PolicyCategory.INSTRUCTION_OVERRIDE,
        decision=PolicyDecision.BLOCK,
        message="Request asks for hidden, system, or developer instructions.",
        patterns=(
            r"\breveal (the )?(system prompt|hidden instructions|developer instructions)\b",
            r"\bprint (your )?(system prompt|hidden instructions|developer instructions)\b",
            r"\bshow (your )?(system prompt|hidden instructions|developer instructions)\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-SECRETS-001",
        severity="critical",
        category=PolicyCategory.SECRETS_EXFILTRATION,
        decision=PolicyDecision.BLOCK,
        message="Request attempts to expose credentials, API keys, tokens, or passwords.",
        patterns=(
            r"\b(show|print|reveal|send|export|dump) (the |all )?(api key|api keys|secret|secrets|token|tokens|password|passwords|credentials)\b",
            r"\bsend supplier credentials\b",
            r"\bshow api key\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-DATA-LEAKAGE-001",
        severity="critical",
        category=PolicyCategory.DATA_LEAKAGE,
        decision=PolicyDecision.BLOCK,
        message="Request attempts broad customer, supplier, payment, or private-data exfiltration.",
        patterns=(
            r"\bexport all (customer|supplier|payment|invoice|order) data\b",
            r"\bdump all (customer|supplier|payment|invoice|order) (data|records)\b",
            r"\bdownload all (customer|supplier|payment|invoice|order) (data|records)\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-DATA-LEAKAGE-REVIEW-001",
        severity="medium",
        category=PolicyCategory.DATA_LEAKAGE,
        decision=PolicyDecision.REVIEW,
        message="Request asks to export sensitive business records and needs data-access review.",
        patterns=(
            r"\bexport (customer|supplier|payment|invoice|order|receivable|receivables) (history|records|data)\b",
            r"\bexport customer payment history\b",
            r"\bshare (customer|supplier) (history|records|data)\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-DESTRUCTIVE-001",
        severity="critical",
        category=PolicyCategory.DESTRUCTIVE_OPERATION,
        decision=PolicyDecision.BLOCK,
        message="Request asks for destructive or audit-disabling operations.",
        patterns=(
            r"\bdelete all (records|orders|customers|suppliers|data)\b",
            r"\berase all (records|orders|customers|suppliers|data)\b",
            r"\bwipe (the )?(database|records|orders|customers|suppliers|data)\b",
            r"\bdisable audit logging\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-FINANCE-ACTION-001",
        severity="high",
        category=PolicyCategory.UNAUTHORIZED_FINANCIAL_ACTION,
        decision=PolicyDecision.BLOCK,
        message="Request attempts to bypass approval or risk checks for a financial/business action.",
        patterns=(
            r"\bapprove (the )?.*without (checking|review|risk|approval)\b",
            r"\bapprove .*without .*risk\b",
            r"\bbypass approval\b",
            r"\bskip (the )?(approval|risk check|risk review)\b",
            r"\bapprove this high-risk order\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-UNSAFE-TOOL-001",
        severity="high",
        category=PolicyCategory.UNSAFE_TOOL_REQUEST,
        decision=PolicyDecision.BLOCK,
        message="Request asks the agent to use tools in a way that bypasses controls or accesses local internals.",
        patterns=(
            r"\buse (a )?tool to bypass\b",
            r"\brun shell\b.*\b(api key|secret|token|password)\b",
            r"\bcall .*external api\b.*\bwithout approval\b",
            r"\bdisable (the )?(guardrail|guardrails|policy checks)\b",
        ),
    ),
    _PolicyRule(
        finding_id="SEC-UNSAFE-TOOL-REVIEW-001",
        severity="medium",
        category=PolicyCategory.UNSAFE_TOOL_REQUEST,
        decision=PolicyDecision.REVIEW,
        message="Request asks for bulk tool execution or external transfer and needs review.",
        patterns=(
            r"\bbulk export\b",
            r"\bsend .* to external\b",
            r"\btransfer .* to .*outside\b",
        ),
    ),
)


def normalize_policy_input(text: str) -> str:
    """Normalize text for stable, explainable matching."""

    return re.sub(r"\s+", " ", text.strip().lower())


def evaluate_security_policy(text: str, *, metadata: dict[str, Any] | None = None) -> PolicyResult:
    normalized = normalize_policy_input(text)
    findings = tuple(_find_policy_matches(normalized))
    decision = _resolve_decision(findings)
    return PolicyResult(
        decision=decision,
        findings=findings,
        normalized_input=normalized,
        checked_categories=CHECKED_CATEGORIES,
        metadata={
            "policy_version": "sprint-011-v1",
            "rule_count": len(_RULES),
            **(metadata or {}),
        },
    )


def _find_policy_matches(normalized: str) -> Iterable[PolicyFinding]:
    for rule in _RULES:
        for pattern in rule.patterns:
            match = re.search(pattern, normalized)
            if not match:
                continue
            yield PolicyFinding(
                finding_id=rule.finding_id,
                severity=rule.severity,
                category=rule.category.value,
                message=rule.message,
                matched_evidence=match.group(0),
            )
            break


def _resolve_decision(findings: tuple[PolicyFinding, ...]) -> PolicyDecision:
    finding_decisions = {
        rule.finding_id: rule.decision
        for rule in _RULES
    }
    if any(finding_decisions[finding.finding_id] == PolicyDecision.BLOCK for finding in findings):
        return PolicyDecision.BLOCK
    if any(finding_decisions[finding.finding_id] == PolicyDecision.REVIEW for finding in findings):
        return PolicyDecision.REVIEW
    return PolicyDecision.ALLOW
