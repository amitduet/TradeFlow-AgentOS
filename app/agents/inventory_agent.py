"""Inventory Agent placeholder."""

from app.tools.inventory_tools import check_stock_availability, update_simulated_stock_status


def review_inventory(product_id: str, requested_quantity: int) -> dict:
    return check_stock_availability(product_id, requested_quantity)


def handle_goods_receipt(product_id: str, received_quantity: int) -> dict:
    return update_simulated_stock_status(product_id, received_quantity)
