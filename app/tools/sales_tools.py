"""Sales tool placeholders."""

from app.schemas.orders import InvoiceDraftRequest, OrderWorkflowState, create_invoice_draft_request


def capture_order_request(customer_id: str, product_id: str, quantity: int) -> dict:
    return {
        "customer_id": customer_id,
        "product_id": product_id,
        "quantity": quantity,
        "status": "received",
        "draft_only": True,
    }


def prepare_invoice_draft(state: OrderWorkflowState) -> InvoiceDraftRequest:
    return create_invoice_draft_request(state)


def prepare_customer_email_draft(customer_id: str, message_summary: str) -> dict:
    return {
        "customer_id": customer_id,
        "message_summary": message_summary,
        "draft_only": True,
        "requires_human_approval": True,
    }
