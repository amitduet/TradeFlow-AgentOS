"""Purchase Agent placeholder."""

from app.schemas.decisions import FinanceDecision
from app.tools.purchase_tools import create_purchase_order_draft, recommend_supplier


def prepare_procurement_recommendation(product_id: str, shortfall_quantity: int) -> dict:
    return recommend_supplier(product_id, shortfall_quantity)


def prepare_po_draft(
    customer_order_request_id: str,
    product_id: str,
    quantity: int,
    finance_decision: FinanceDecision,
) -> dict:
    return create_purchase_order_draft(
        customer_order_request_id,
        product_id,
        quantity,
        finance_decision,
    )
