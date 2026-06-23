"""Decision schemas for Finance and approval-gated actions."""

from typing import Literal

from pydantic import BaseModel, Field


FinanceDecisionStatus = Literal[
    "approved",
    "approved_with_conditions",
    "rejected",
    "needs_human_review",
]


class FinanceDecision(BaseModel):
    status: FinanceDecisionStatus
    rationale: str
    conditions: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True


def has_finance_consent(decision: FinanceDecision) -> bool:
    """Return whether a draft PO may be prepared after Finance review."""
    return decision.status in {"approved", "approved_with_conditions"}
