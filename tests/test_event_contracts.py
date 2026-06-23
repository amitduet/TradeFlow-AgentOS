from app.schemas.events import AgentEvent


def test_event_schema_accepts_valid_event() -> None:
    event = AgentEvent(
        event_id="evt_demo_001",
        event_type="order_request_created",
        source_agent="sales",
        target_agent="orchestrator",
        correlation_id="ord_req_001",
        payload={
            "customer_id": "cust_demo_001",
            "product_id": "prod_demo_001",
            "quantity": 25,
        },
    )

    assert event.event_type == "order_request_created"
    assert event.payload["quantity"] == 25
    assert event.requires_human_approval is False
