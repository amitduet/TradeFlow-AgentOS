"""Inventory tool placeholders."""

from app.data.db import SYNTHETIC_INVENTORY


def check_stock_availability(product_id: str, requested_quantity: int) -> dict:
    available_quantity = SYNTHETIC_INVENTORY.get(product_id, {}).get("available_quantity", 0)
    shortfall_quantity = max(requested_quantity - available_quantity, 0)
    return {
        "product_id": product_id,
        "requested_quantity": requested_quantity,
        "available_quantity": available_quantity,
        "shortfall_quantity": shortfall_quantity,
        "procurement_needed": shortfall_quantity > 0,
        "synthetic": True,
    }


def update_simulated_stock_status(product_id: str, received_quantity: int) -> dict:
    return {
        "product_id": product_id,
        "received_quantity": received_quantity,
        "status": "simulated_stock_updated",
        "draft_only": True,
        "requires_human_approval": True,
    }
