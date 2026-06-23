"""Purchase tool placeholders."""

from app.schemas.decisions import FinanceDecision, has_finance_consent


def recommend_supplier(product_id: str, shortfall_quantity: int) -> dict:
    return {
        "product_id": product_id,
        "recommended_supplier_id": "supp_demo_001",
        "quantity": shortfall_quantity,
        "synthetic": True,
    }


def create_purchase_order_draft(
    customer_order_request_id: str,
    product_id: str,
    quantity: int,
    finance_decision: FinanceDecision,
) -> dict:
    if not has_finance_consent(finance_decision):
        raise ValueError("Purchase order draft requires approved Finance consent.")
    return {
        "purchase_order_draft_id": f"po_draft_{customer_order_request_id}",
        "customer_order_request_id": customer_order_request_id,
        "product_id": product_id,
        "quantity": quantity,
        "draft_only": True,
        "requires_human_approval": True,
    }
