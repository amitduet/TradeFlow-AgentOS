import pytest
from pydantic import ValidationError

from app.schemas.decisions import FinanceDecision


@pytest.mark.parametrize(
    "status",
    ["approved", "approved_with_conditions", "rejected", "needs_human_review"],
)
def test_finance_decision_allows_expected_statuses(status: str) -> None:
    decision = FinanceDecision(status=status, rationale="Synthetic test rationale.")

    assert decision.status == status


def test_finance_decision_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        FinanceDecision(status="posted_to_erp", rationale="This must not be allowed.")
