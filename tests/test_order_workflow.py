import pytest

from app.schemas.orders import (
    CustomerOrderRequest,
    OrderWorkflowState,
    create_invoice_draft_request,
)


def test_order_workflow_blocks_invoice_draft_before_delivery_confirmation() -> None:
    order = CustomerOrderRequest(
        customer_order_request_id="ord_req_001",
        customer_id="cust_demo_001",
        product_id="prod_demo_001",
        quantity=25,
    )
    state = OrderWorkflowState(order=order, delivery_confirmed=False)

    with pytest.raises(ValueError, match="delivery confirmation"):
        create_invoice_draft_request(state)


def test_order_workflow_allows_invoice_draft_after_delivery_confirmation() -> None:
    order = CustomerOrderRequest(
        customer_order_request_id="ord_req_001",
        customer_id="cust_demo_001",
        product_id="prod_demo_001",
        quantity=25,
    )
    state = OrderWorkflowState(order=order, delivery_confirmed=True)

    draft = create_invoice_draft_request(state)

    assert draft.customer_order_request_id == "ord_req_001"
    assert draft.draft_only is True
    assert draft.requires_human_approval is True
