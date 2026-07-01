"""Load sanitized Kaggle demo business data.

The demo data is intentionally small and local. It gives the runnable demo
business context without adding ERP behavior, live services, or dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEMO_DATA_DIR = REPO_ROOT / "examples" / "demo" / "data"

PRODUCTS_FILE = "demo_products.json"
CUSTOMERS_FILE = "demo_customers.json"
INVENTORY_FILE = "demo_inventory.json"
FINANCE_FILE = "demo_finance_opening_balance.json"

PRODUCT_REQUIRED_FIELDS = {
    "product_code",
    "product_name",
    "unit_package_description",
    "base_unit",
    "package_size",
    "demo_category",
}
CUSTOMER_REQUIRED_FIELDS = {
    "customer_id",
    "customer_name",
    "country",
    "customer_type",
    "credit_limit_usd",
    "current_exposure_usd",
    "payment_terms",
    "risk_rating",
    "contact_person",
}
CONTACT_REQUIRED_FIELDS = {"name", "email", "phone", "designation"}
INVENTORY_REQUIRED_FIELDS = {
    "product_code",
    "warehouse",
    "on_hand_quantity",
    "reserved_quantity",
    "available_quantity",
    "unit",
    "package_description",
    "reorder_level",
    "inventory_status",
}
FINANCE_REQUIRED_FIELDS = {
    "currency",
    "opening_cash_balance",
    "opening_receivables",
    "opening_payables",
    "opening_inventory_value",
    "effective_date",
    "note",
}
ALLOWED_INVENTORY_STATUSES = {"healthy", "low_stock", "reserved", "out_of_stock"}


def load_demo_business_data(data_dir: str | Path = DEFAULT_DEMO_DATA_DIR) -> dict[str, Any]:
    """Load and validate all sanitized demo business data files."""
    root = Path(data_dir)
    products = _load_json(root / PRODUCTS_FILE, expected_type=list)
    customers = _load_json(root / CUSTOMERS_FILE, expected_type=list)
    inventory = _load_json(root / INVENTORY_FILE, expected_type=list)
    finance = _load_json(root / FINANCE_FILE, expected_type=dict)

    _validate_records(products, PRODUCT_REQUIRED_FIELDS, PRODUCTS_FILE, key_field="product_code")
    _validate_records(customers, CUSTOMER_REQUIRED_FIELDS, CUSTOMERS_FILE, key_field="customer_id")
    _validate_customer_contacts(customers)
    _validate_records(inventory, INVENTORY_REQUIRED_FIELDS, INVENTORY_FILE, key_field="product_code")
    _validate_finance(finance)

    product_codes = {product["product_code"] for product in products}
    for record in inventory:
        product_code = record["product_code"]
        if product_code not in product_codes:
            raise ValueError(f"{INVENTORY_FILE}: unknown product_code {product_code!r}")
        status = record["inventory_status"]
        if status not in ALLOWED_INVENTORY_STATUSES:
            raise ValueError(f"{INVENTORY_FILE}: invalid inventory_status {status!r} for {product_code}")

    return {
        "products": products,
        "customers": customers,
        "inventory": inventory,
        "finance_opening_balance": finance,
    }


def build_demo_order_context(
    *,
    product_code: str,
    customer_id: str,
    data_dir: str | Path = DEFAULT_DEMO_DATA_DIR,
) -> dict[str, Any]:
    """Return product, customer, inventory, and finance context for a demo order."""
    data = load_demo_business_data(data_dir)
    product = _find_by_key(data["products"], "product_code", product_code, PRODUCTS_FILE)
    customer = _find_by_key(data["customers"], "customer_id", customer_id, CUSTOMERS_FILE)
    inventory = _find_by_key(data["inventory"], "product_code", product_code, INVENTORY_FILE)
    finance = data["finance_opening_balance"]
    return {
        "product": product,
        "customer": customer,
        "inventory": inventory,
        "finance_opening_balance": {
            "currency": finance["currency"],
            "opening_cash_balance": finance["opening_cash_balance"],
            "effective_date": finance["effective_date"],
            "note": finance["note"],
        },
        "demo_context_signals": _demo_context_signals(inventory),
    }


def _load_json(path: Path, *, expected_type: type) -> Any:
    if not path.exists():
        raise ValueError(f"Missing demo data file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in {path}: {exc}") from exc
    if not isinstance(payload, expected_type):
        raise ValueError(f"{path.name}: expected {expected_type.__name__} payload")
    return payload


def _validate_records(records: list[Any], required_fields: set[str], filename: str, *, key_field: str) -> None:
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"{filename}: record {index} must be an object")
        missing = sorted(required_fields - record.keys())
        if missing:
            raise ValueError(f"{filename}: record {index} missing required fields: {', '.join(missing)}")
        key = record[key_field]
        if not isinstance(key, str) or not key:
            raise ValueError(f"{filename}: record {index} has invalid {key_field}")
        if key in seen:
            raise ValueError(f"{filename}: duplicate {key_field} {key!r}")
        seen.add(key)


def _validate_customer_contacts(customers: list[dict[str, Any]]) -> None:
    for customer in customers:
        contact = customer["contact_person"]
        if not isinstance(contact, dict):
            raise ValueError(f"{CUSTOMERS_FILE}: contact_person must be an object for {customer['customer_id']}")
        missing = sorted(CONTACT_REQUIRED_FIELDS - contact.keys())
        if missing:
            raise ValueError(
                f"{CUSTOMERS_FILE}: contact_person for {customer['customer_id']} missing fields: {', '.join(missing)}"
            )


def _validate_finance(finance: dict[str, Any]) -> None:
    missing = sorted(FINANCE_REQUIRED_FIELDS - finance.keys())
    if missing:
        raise ValueError(f"{FINANCE_FILE}: missing required fields: {', '.join(missing)}")
    if finance["currency"] != "USD":
        raise ValueError(f"{FINANCE_FILE}: currency must be USD")


def _find_by_key(records: list[dict[str, Any]], key: str, value: str, filename: str) -> dict[str, Any]:
    for record in records:
        if record[key] == value:
            return record
    raise ValueError(f"{filename}: unknown {key} {value!r}")


def _demo_context_signals(inventory: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    if inventory["inventory_status"] in {"low_stock", "out_of_stock"}:
        signals.append(f"inventory_status:{inventory['inventory_status']}")
    if inventory["available_quantity"] <= inventory["reorder_level"]:
        signals.append("available_inventory_at_or_below_reorder_level")
    return signals
