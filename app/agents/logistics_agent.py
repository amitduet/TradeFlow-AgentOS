"""Logistics Agent placeholder."""

from app.schemas.events import AgentEvent
from app.tools.logistics_tools import confirm_customer_delivery, confirm_goods_receipt


def record_goods_receipt(correlation_id: str, product_id: str, received_quantity: int) -> AgentEvent:
    return confirm_goods_receipt(correlation_id, product_id, received_quantity)


def record_customer_delivery(correlation_id: str, order_id: str, delivered_quantity: int) -> AgentEvent:
    return confirm_customer_delivery(correlation_id, order_id, delivered_quantity)
