"""Deterministic, read-only tools for the Sprint 2 synthetic dataset."""

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from app.schemas.tradeflow_dataset import (
    Customer,
    Product,
    SalesOrder,
    Supplier,
    TradeFlowDataset,
)


DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "tradeflow_seed.json"
LOW_MARGIN_THRESHOLD_PERCENT = 10.0


def load_synthetic_dataset(path: str | Path = DEFAULT_DATASET_PATH) -> TradeFlowDataset:
    """Load and validate the synthetic dataset from a local JSON file."""
    return _load_synthetic_dataset_cached(str(Path(path)))


@lru_cache(maxsize=8)
def _load_synthetic_dataset_cached(path: str) -> TradeFlowDataset:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return TradeFlowDataset.model_validate(payload)


def get_customer_profile(customer_id: str, dataset_path: str | Path = DEFAULT_DATASET_PATH) -> dict[str, Any]:
    dataset = load_synthetic_dataset(dataset_path)
    customer = _customer_by_id(dataset, customer_id)
    return customer.model_dump(mode="json")


def get_supplier_profile(supplier_id: str, dataset_path: str | Path = DEFAULT_DATASET_PATH) -> dict[str, Any]:
    dataset = load_synthetic_dataset(dataset_path)
    supplier = _supplier_by_id(dataset, supplier_id)
    return supplier.model_dump(mode="json")


def list_sales_orders(
    customer_id: str | None = None,
    status: str | None = None,
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
) -> list[dict[str, Any]]:
    dataset = load_synthetic_dataset(dataset_path)
    orders = dataset.sales_orders
    if customer_id is not None:
        orders = [order for order in orders if order.customer_id == customer_id]
    if status is not None:
        orders = [order for order in orders if order.status == status]
    return [order.model_dump(mode="json") for order in orders]


def get_sales_order(order_id: str, dataset_path: str | Path = DEFAULT_DATASET_PATH) -> dict[str, Any]:
    dataset = load_synthetic_dataset(dataset_path)
    order = _sales_order_by_id(dataset, order_id)
    customer = _customer_by_id(dataset, order.customer_id)
    result = order.model_dump(mode="json")
    result["customer"] = customer.model_dump(mode="json")
    result["line_items"] = [_line_item_with_product(dataset, line_item) for line_item in order.line_items]
    result["derived_totals"] = calculate_order_margin(order_id, dataset_path)
    return result


def list_purchase_order_drafts(
    related_sales_order_id: str | None = None,
    status: str | None = None,
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
) -> list[dict[str, Any]]:
    dataset = load_synthetic_dataset(dataset_path)
    drafts = dataset.purchase_order_drafts
    if related_sales_order_id is not None:
        drafts = [draft for draft in drafts if draft.related_sales_order_id == related_sales_order_id]
    if status is not None:
        drafts = [draft for draft in drafts if draft.status == status]
    return [draft.model_dump(mode="json") for draft in drafts]


def get_drop_shipping_chain(
    sales_order_id: str,
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
) -> dict[str, Any]:
    dataset = load_synthetic_dataset(dataset_path)
    order = _sales_order_by_id(dataset, sales_order_id)
    customer = _customer_by_id(dataset, order.customer_id)
    po_drafts = [
        draft for draft in dataset.purchase_order_drafts if draft.related_sales_order_id == sales_order_id
    ]
    supplier_ids = sorted({draft.supplier_id for draft in po_drafts})
    suppliers = [_supplier_by_id(dataset, supplier_id) for supplier_id in supplier_ids]
    logistics_events = [
        event for event in dataset.logistics_events if event.related_sales_order_id == sales_order_id
    ]

    return {
        "sales_order": get_sales_order(sales_order_id, dataset_path),
        "customer": customer.model_dump(mode="json"),
        "purchase_order_drafts": [draft.model_dump(mode="json") for draft in po_drafts],
        "suppliers": [supplier.model_dump(mode="json") for supplier in suppliers],
        "logistics_events": [event.model_dump(mode="json") for event in logistics_events],
    }


def list_logistics_events(
    sales_order_id: str,
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
) -> list[dict[str, Any]]:
    dataset = load_synthetic_dataset(dataset_path)
    _sales_order_by_id(dataset, sales_order_id)
    events = [event for event in dataset.logistics_events if event.related_sales_order_id == sales_order_id]
    return [event.model_dump(mode="json") for event in events]


def calculate_order_margin(order_id: str, dataset_path: str | Path = DEFAULT_DATASET_PATH) -> dict[str, Any]:
    dataset = load_synthetic_dataset(dataset_path)
    order = _sales_order_by_id(dataset, order_id)
    products_by_id = {product.id: product for product in dataset.products}

    revenue = 0.0
    estimated_cost = 0.0
    for line_item in order.line_items:
        product = products_by_id[line_item.product_id]
        revenue += line_item.quantity * line_item.unit_price
        estimated_cost += line_item.quantity * product.standard_cost

    gross_margin = revenue - estimated_cost
    gross_margin_percent = (gross_margin / revenue * 100) if revenue else 0.0
    return {
        "order_id": order_id,
        "revenue": round(revenue, 2),
        "estimated_cost": round(estimated_cost, 2),
        "gross_margin": round(gross_margin, 2),
        "gross_margin_percent": round(gross_margin_percent, 2),
    }


def detect_order_risk(order_id: str, dataset_path: str | Path = DEFAULT_DATASET_PATH) -> dict[str, Any]:
    dataset = load_synthetic_dataset(dataset_path)
    order = _sales_order_by_id(dataset, order_id)
    customer = _customer_by_id(dataset, order.customer_id)
    margin = calculate_order_margin(order_id, dataset_path)
    linked_po_drafts = [
        draft for draft in dataset.purchase_order_drafts if draft.related_sales_order_id == order_id
    ]
    logistics_events = [
        event for event in dataset.logistics_events if event.related_sales_order_id == order_id
    ]
    payment_summaries = [
        payment for payment in dataset.payment_summaries if payment.sales_order_id == order_id
    ]

    risk_flags: list[str] = []
    if customer.rating <= 2:
        risk_flags.append("low_customer_rating")
    if any(event.status == "delayed" or event.event_type == "delay_reported" for event in logistics_events):
        risk_flags.append("delayed_logistics_event")
    if order.fulfillment_type == "drop_ship" and not linked_po_drafts:
        risk_flags.append("missing_linked_po_for_drop_shipping")
    if margin["gross_margin_percent"] < LOW_MARGIN_THRESHOLD_PERCENT:
        risk_flags.append("low_margin")
    if any(payment.status == "overdue" for payment in payment_summaries):
        risk_flags.append("overdue_payment")

    if {"missing_linked_po_for_drop_shipping", "overdue_payment"} & set(risk_flags):
        risk_level = "high"
    elif len(risk_flags) >= 2 or "delayed_logistics_event" in risk_flags or "low_customer_rating" in risk_flags:
        risk_level = "medium"
    else:
        risk_level = "low"

    explanation = "No deterministic risk rules were triggered."
    if risk_flags:
        explanation = "Triggered deterministic risk rules: " + ", ".join(risk_flags) + "."

    return {
        "order_id": order_id,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "explanation": explanation,
    }


def _customer_by_id(dataset: TradeFlowDataset, customer_id: str) -> Customer:
    for customer in dataset.customers:
        if customer.id == customer_id:
            return customer
    raise KeyError(f"Unknown customer_id: {customer_id}")


def _supplier_by_id(dataset: TradeFlowDataset, supplier_id: str) -> Supplier:
    for supplier in dataset.suppliers:
        if supplier.id == supplier_id:
            return supplier
    raise KeyError(f"Unknown supplier_id: {supplier_id}")


def _sales_order_by_id(dataset: TradeFlowDataset, order_id: str) -> SalesOrder:
    for order in dataset.sales_orders:
        if order.id == order_id:
            return order
    raise KeyError(f"Unknown sales_order_id: {order_id}")


def _product_by_id(dataset: TradeFlowDataset, product_id: str) -> Product:
    for product in dataset.products:
        if product.id == product_id:
            return product
    raise KeyError(f"Unknown product_id: {product_id}")


def _line_item_with_product(dataset: TradeFlowDataset, line_item: Any) -> dict[str, Any]:
    product = _product_by_id(dataset, line_item.product_id)
    result = line_item.model_dump(mode="json")
    result["product"] = product.model_dump(mode="json")
    result["line_total"] = round(line_item.quantity * line_item.unit_price, 2)
    return result
