"""Logistics tool placeholders."""

from app.schemas.events import AgentEvent


def confirm_goods_receipt(correlation_id: str, product_id: str, received_quantity: int) -> AgentEvent:
    return AgentEvent(
        event_id=f"evt_goods_received_{correlation_id}",
        event_type="goods_received",
        source_agent="logistics",
        target_agent="inventory",
        correlation_id=correlation_id,
        payload={"product_id": product_id, "received_quantity": received_quantity},
    )


def confirm_customer_delivery(correlation_id: str, order_id: str, delivered_quantity: int) -> AgentEvent:
    return AgentEvent(
        event_id=f"evt_delivery_confirmed_{correlation_id}",
        event_type="delivery_confirmed",
        source_agent="logistics",
        target_agent="sales",
        correlation_id=correlation_id,
        payload={"customer_order_request_id": order_id, "delivered_quantity": delivered_quantity},
    )
