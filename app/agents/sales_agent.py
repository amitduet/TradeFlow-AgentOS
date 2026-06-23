"""Sales Agent placeholder."""

from app.schemas.orders import OrderWorkflowState
from app.tools.sales_tools import (
    capture_order_request,
    prepare_customer_email_draft,
    prepare_invoice_draft,
)


def start_order_request(customer_id: str, product_id: str, quantity: int) -> dict:
    return capture_order_request(customer_id, product_id, quantity)


def prepare_post_delivery_drafts(state: OrderWorkflowState) -> dict:
    invoice_draft = prepare_invoice_draft(state)
    email_draft = prepare_customer_email_draft(
        invoice_draft.customer_id,
        "Delivery confirmed; invoice draft is ready for human review.",
    )
    return {"invoice_draft": invoice_draft, "customer_email_draft": email_draft}
