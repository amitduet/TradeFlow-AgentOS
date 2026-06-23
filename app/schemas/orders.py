"""Order workflow schemas and guardrail helpers."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, PositiveInt


OrderStatus = Literal[
    "received",
    "feasible",
    "procurement_needed",
    "rejected",
    "fulfilled",
]


class CustomerOrderRequest(BaseModel):
    customer_order_request_id: str
    customer_id: str
    product_id: str
    quantity: PositiveInt
    requested_delivery_date: date | None = None
    status: OrderStatus = "received"


class OrderWorkflowState(BaseModel):
    order: CustomerOrderRequest
    delivery_confirmed: bool = False
    invoice_draft_created: bool = False
    customer_email_draft_created: bool = False
    receivable_follow_up_started: bool = False
    events: list[str] = Field(default_factory=list)


class InvoiceDraftRequest(BaseModel):
    customer_order_request_id: str
    customer_id: str
    product_id: str
    quantity: PositiveInt
    draft_only: bool = True
    requires_human_approval: bool = True


def create_invoice_draft_request(state: OrderWorkflowState) -> InvoiceDraftRequest:
    """Create an invoice draft request only after delivery is confirmed."""
    if not state.delivery_confirmed:
        raise ValueError("Invoice draft cannot be created before delivery confirmation.")

    return InvoiceDraftRequest(
        customer_order_request_id=state.order.customer_order_request_id,
        customer_id=state.order.customer_id,
        product_id=state.order.product_id,
        quantity=state.order.quantity,
    )
