"""Finance Agent placeholder."""

from app.schemas.decisions import FinanceDecision
from app.tools.finance_tools import evaluate_finance_decision, start_receivable_follow_up


def review_order_finance(customer_id: str, order_amount: float) -> FinanceDecision:
    return evaluate_finance_decision(customer_id, order_amount)


def track_receivable(customer_id: str, invoice_draft_id: str) -> dict:
    return start_receivable_follow_up(customer_id, invoice_draft_id)
