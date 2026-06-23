"""Finance tool placeholders."""

from app.schemas.decisions import FinanceDecision


def evaluate_finance_decision(customer_id: str, order_amount: float) -> FinanceDecision:
    if customer_id == "cust_demo_003" or order_amount > 100000:
        return FinanceDecision(
            status="rejected",
            rationale="Synthetic exposure exceeds the demo credit threshold.",
        )
    if order_amount > 50000:
        return FinanceDecision(
            status="approved_with_conditions",
            rationale="Synthetic order is viable with advance payment.",
            conditions=["Collect advance payment before releasing any real purchase order."],
        )
    return FinanceDecision(
        status="approved",
        rationale="Synthetic exposure and margin are within demo thresholds.",
    )


def start_receivable_follow_up(customer_id: str, invoice_draft_id: str) -> dict:
    return {
        "customer_id": customer_id,
        "invoice_draft_id": invoice_draft_id,
        "status": "receivable_follow_up_draft_started",
        "draft_only": True,
    }
