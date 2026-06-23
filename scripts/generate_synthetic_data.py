"""Generate the deterministic Sprint 2 TradeFlow synthetic dataset."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
import random
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas.tradeflow_dataset import (
    ContactPerson,
    Customer,
    InvoiceSummary,
    LogisticsEvent,
    OrderLineItem,
    PaymentSummary,
    Product,
    PurchaseOrderDraft,
    SalesOrder,
    Supplier,
    TradeFlowDataset,
)


DEFAULT_SEED = 20240623
DEFAULT_OUTPUT = Path("data/synthetic/tradeflow_seed.json")


CUSTOMER_NAMES = [
    "Aster Retail Group",
    "Blue Harbor Traders",
    "Cedar Lane Wholesale",
    "Delta Mart Supplies",
    "Eastern Bazaar Co",
    "Futura Home Goods",
    "Greenline Distribution",
    "Harborview Medical",
    "Indigo Office Mart",
    "Jasmine Food Service",
    "Kite Electronics",
    "Lotus Metro Stores",
]

SUPPLIER_DATA = [
    ("SUP-001", "Ningbo Atlas Manufacturing", "China"),
    ("SUP-002", "Ho Chi Minh Allied Goods", "Vietnam"),
    ("SUP-003", "Izmir Packaging Works", "Turkey"),
    ("SUP-004", "Jakarta Prime Components", "Indonesia"),
    ("SUP-005", "Chittagong Textile Source", "Bangladesh"),
    ("SUP-006", "Penang Industrial Supply", "Malaysia"),
    ("SUP-007", "Dubai General Trading", "UAE"),
    ("SUP-008", "Mumbai Metro Exports", "India"),
]

PRODUCT_BLUEPRINTS = [
    ("Portable Blender", "Home Appliances", "pcs", 48.0, 72.0),
    ("Thermal Label Printer", "Office Equipment", "pcs", 115.0, 168.0),
    ("Cotton Shop Towel", "Textiles", "carton", 18.0, 27.0),
    ("LED Desk Lamp", "Electronics", "pcs", 22.0, 36.0),
    ("Food Storage Container", "Housewares", "carton", 14.0, 24.0),
    ("Stainless Flask", "Housewares", "pcs", 9.5, 16.0),
    ("Barcode Scanner", "Office Equipment", "pcs", 88.0, 132.0),
    ("Disposable Apron", "Food Service", "case", 12.0, 19.0),
    ("USB-C Dock", "Electronics", "pcs", 42.0, 68.0),
    ("Microfiber Mop Kit", "Cleaning", "carton", 31.0, 48.0),
    ("Nitrile Gloves", "Medical Supplies", "case", 28.0, 44.0),
    ("Retail Shelf Basket", "Store Fixtures", "pcs", 17.0, 29.0),
    ("Rice Cooker", "Home Appliances", "pcs", 38.0, 58.0),
    ("Shipping Carton XL", "Packaging", "bundle", 20.0, 33.0),
    ("Thermal Receipt Roll", "Office Supplies", "case", 15.0, 25.0),
    ("Cotton Tote Bag", "Textiles", "carton", 24.0, 39.0),
    ("Handheld Fan", "Electronics", "pcs", 11.0, 19.0),
    ("Chef Knife Set", "Food Service", "set", 33.0, 54.0),
    ("Bluetooth Speaker", "Electronics", "pcs", 29.0, 49.0),
    ("Warehouse Safety Vest", "Industrial", "carton", 26.0, 41.0),
    ("Ceramic Dinner Set", "Housewares", "set", 52.0, 84.0),
    ("POS Cash Drawer", "Store Fixtures", "pcs", 64.0, 97.0),
    ("Air Purifier Filter", "Home Appliances", "pcs", 21.0, 34.0),
    ("Invoice File Box", "Office Supplies", "carton", 13.0, 22.0),
    ("Poly Mailer Pack", "Packaging", "bundle", 10.0, 18.0),
]


def generate_synthetic_dataset(seed: int = DEFAULT_SEED) -> TradeFlowDataset:
    rng = random.Random(seed)
    customers = _build_customers(rng)
    suppliers = _build_suppliers()
    products = _build_products(rng)
    sales_orders = _build_sales_orders()
    purchase_order_drafts = _build_purchase_order_drafts(products)
    logistics_events = _build_logistics_events()
    invoice_summaries, payment_summaries = _build_invoice_and_payment_summaries(sales_orders)

    return TradeFlowDataset(
        customers=customers,
        suppliers=suppliers,
        products=products,
        sales_orders=sales_orders,
        purchase_order_drafts=purchase_order_drafts,
        logistics_events=logistics_events,
        invoice_summaries=invoice_summaries,
        payment_summaries=payment_summaries,
    )


def write_dataset(dataset: TradeFlowDataset, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dataset.model_dump(mode="json")
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    dataset = generate_synthetic_dataset(args.seed)
    write_dataset(dataset, args.output)
    print(f"Wrote deterministic synthetic dataset to {args.output} with seed {args.seed}.")
    return 0


def _build_customers(rng: random.Random) -> list[Customer]:
    ratings = [5, 4, 2, 3, 5, 4, 3, 2, 4, 5, 3, 4]
    customers = []
    for index, name in enumerate(CUSTOMER_NAMES, start=1):
        city_code = 100 + index
        customers.append(
            Customer(
                id=f"CUST-{index:03d}",
                name=name,
                rating=ratings[index - 1],
                billing_address=f"{city_code} Finance Avenue, Dhaka Demo Zone",
                shipping_address=f"Warehouse Gate {index}, TradeFlow Industrial Park",
                phone_number=f"+880-1700-{rng.randint(100000, 999999)}",
                contact_person=ContactPerson(
                    name=f"{name.split()[0]} Rahman",
                    email=f"contact{index}@example-tradeflow.test",
                    phone=f"+880-1800-{rng.randint(100000, 999999)}",
                    designation="Procurement Manager",
                ),
            )
        )
    return customers


def _build_suppliers() -> list[Supplier]:
    suppliers = []
    for index, (supplier_id, name, country) in enumerate(SUPPLIER_DATA, start=1):
        suppliers.append(
            Supplier(
                id=supplier_id,
                name=name,
                country=country,
                phone_number=f"+99-55-{index:04d}-2200",
                contact_person=ContactPerson(
                    name=f"Supplier Contact {index}",
                    email=f"supplier{index}@example-tradeflow.test",
                    phone=f"+99-55-{index:04d}-3300",
                    designation="Export Sales Lead",
                ),
            )
        )
    return suppliers


def _build_products(rng: random.Random) -> list[Product]:
    products = []
    for index, (name, category, unit, standard_cost, sale_price) in enumerate(PRODUCT_BLUEPRINTS, start=1):
        supplier_index = ((index - 1) % len(SUPPLIER_DATA)) + 1
        products.append(
            Product(
                id=f"PROD-{index:03d}",
                sku=f"TF-{category[:3].upper()}-{1000 + index}",
                name=name,
                category=category,
                unit=unit,
                supplier_id=f"SUP-{supplier_index:03d}",
                standard_cost=round(standard_cost * rng.uniform(0.98, 1.02), 2),
                sale_price=sale_price,
            )
        )
    products[0].standard_cost = 48.0
    products[1].standard_cost = 115.0
    products[2].standard_cost = 18.0
    return products


def _build_sales_orders() -> list[SalesOrder]:
    base_date = date(2026, 1, 5)
    specs = [
        ("SO-1001", "CUST-001", 0, 14, "confirmed", "CFR", "warehouse_stock", [("PROD-001", 40, 72.0)], []),
        ("SO-1002", "CUST-002", 1, 18, "in_transit", "DAP", "drop_ship", [("PROD-002", 12, 168.0)], []),
        ("SO-1003", "CUST-003", 2, 12, "confirmed", "FOB", "procurement", [("PROD-003", 150, 27.0)], []),
        ("SO-1004", "CUST-004", 3, 11, "confirmed", "CIF", "warehouse_stock", [("PROD-004", 80, 23.0)], ["thin_margin_review"]),
        ("SO-1005", "CUST-005", 4, 19, "draft", "DAP", "drop_ship", [("PROD-005", 110, 24.0)], []),
        ("SO-1006", "CUST-006", 5, 16, "delayed", "CFR", "procurement", [("PROD-006", 200, 16.0)], []),
        ("SO-1007", "CUST-007", 6, 15, "delivered", "DAP", "warehouse_stock", [("PROD-007", 18, 132.0)], []),
        ("SO-1008", "CUST-008", 7, 14, "confirmed", "FOB", "procurement", [("PROD-008", 260, 19.0)], []),
        ("SO-1009", "CUST-009", 8, 20, "in_transit", "DAP", "drop_ship", [("PROD-009", 70, 68.0)], []),
        ("SO-1010", "CUST-010", 9, 12, "delivered", "CFR", "warehouse_stock", [("PROD-010", 45, 48.0)], []),
        ("SO-1011", "CUST-011", 10, 21, "confirmed", "CIF", "procurement", [("PROD-011", 95, 44.0)], []),
        ("SO-1012", "CUST-012", 11, 13, "confirmed", "FOB", "warehouse_stock", [("PROD-012", 60, 29.0)], []),
        ("SO-1013", "CUST-002", 12, 17, "in_transit", "DAP", "drop_ship", [("PROD-013", 20, 58.0)], []),
        ("SO-1014", "CUST-004", 13, 16, "delivered", "CFR", "warehouse_stock", [("PROD-014", 75, 33.0)], []),
        ("SO-1015", "CUST-006", 14, 18, "confirmed", "CIF", "procurement", [("PROD-015", 120, 25.0)], []),
        ("SO-1016", "CUST-007", 15, 12, "confirmed", "FOB", "warehouse_stock", [("PROD-016", 90, 39.0)], []),
        ("SO-1017", "CUST-009", 16, 22, "in_transit", "DAP", "drop_ship", [("PROD-017", 160, 19.0)], []),
        ("SO-1018", "CUST-010", 17, 15, "confirmed", "CFR", "procurement", [("PROD-018", 55, 54.0)], []),
        ("SO-1019", "CUST-001", 18, 10, "delivered", "DAP", "warehouse_stock", [("PROD-019", 44, 49.0)], []),
        ("SO-1020", "CUST-012", 19, 24, "confirmed", "CIF", "procurement", [("PROD-020", 130, 41.0)], []),
    ]
    orders = []
    for order_id, customer_id, day_offset, delivery_offset, status, incoterm, fulfillment_type, items, flags in specs:
        line_items = [OrderLineItem(product_id=pid, quantity=qty, unit_price=price) for pid, qty, price in items]
        subtotal = round(sum(item.quantity * item.unit_price for item in line_items), 2)
        orders.append(
            SalesOrder(
                id=order_id,
                customer_id=customer_id,
                order_date=base_date + timedelta(days=day_offset),
                expected_delivery_date=base_date + timedelta(days=delivery_offset),
                status=status,
                incoterm=incoterm,
                fulfillment_type=fulfillment_type,
                line_items=line_items,
                subtotal=subtotal,
                risk_flags=flags,
                notes=f"Synthetic {fulfillment_type} order for deterministic Sprint 2 tooling.",
            )
        )
    return orders


def _build_purchase_order_drafts(products: list[Product]) -> list[PurchaseOrderDraft]:
    product_supplier = {product.id: product.supplier_id for product in products}
    specs = [
        ("POD-2001", "SO-1002", "drop_shipping", "pending_approval", [("PROD-002", 12, 115.0)], True),
        ("POD-2002", "SO-1003", "customer_procurement", "draft", [("PROD-003", 150, 18.0)], True),
        ("POD-2003", "SO-1006", "customer_procurement", "pending_approval", [("PROD-006", 200, 9.5)], True),
        ("POD-2004", "SO-1009", "drop_shipping", "approved_by_human", [("PROD-009", 70, 42.0)], True),
        ("POD-2005", "SO-1011", "customer_procurement", "draft", [("PROD-011", 95, 28.0)], True),
        ("POD-2006", "SO-1013", "drop_shipping", "pending_approval", [("PROD-013", 20, 38.0)], True),
        ("POD-2007", "SO-1015", "customer_procurement", "draft", [("PROD-015", 120, 15.0)], True),
        ("POD-2008", "SO-1017", "drop_shipping", "pending_approval", [("PROD-017", 160, 11.0)], True),
        ("POD-2009", "SO-1018", "customer_procurement", "draft", [("PROD-018", 55, 33.0)], True),
        ("POD-2010", "SO-1020", "customer_procurement", "pending_approval", [("PROD-020", 130, 26.0)], True),
        ("POD-2011", None, "stock_replenishment", "draft", [("PROD-021", 40, 52.0)], False),
        ("POD-2012", None, "stock_replenishment", "draft", [("PROD-022", 30, 64.0)], False),
    ]
    drafts = []
    for draft_id, order_id, purpose, status, items, created_from_order in specs:
        line_items = [OrderLineItem(product_id=pid, quantity=qty, unit_price=price) for pid, qty, price in items]
        supplier_id = product_supplier[line_items[0].product_id]
        drafts.append(
            PurchaseOrderDraft(
                id=draft_id,
                supplier_id=supplier_id,
                related_sales_order_id=order_id,
                purpose=purpose,
                status=status,
                line_items=line_items,
                subtotal=round(sum(item.quantity * item.unit_price for item in line_items), 2),
                created_from_sales_order=created_from_order,
                notes=f"Synthetic {purpose.replace('_', ' ')} draft; human approval still required.",
            )
        )
    return drafts


def _build_logistics_events() -> list[LogisticsEvent]:
    base_date = date(2026, 1, 6)
    order_ids = [f"SO-{1000 + index}" for index in range(1, 11)]
    events = []
    event_counter = 1
    for order_index, order_id in enumerate(order_ids):
        event_templates = [
            ("booking_created", "Dhaka Control Tower", "planned", "Shipment booking created."),
            ("picked_up", "Origin Hub", "completed", "Cargo picked up from origin."),
            ("delivered", "Customer Dock", "completed", "Delivery completed in synthetic record."),
        ]
        if order_id == "SO-1006":
            event_templates[2] = (
                "delay_reported",
                "Chittagong Port",
                "delayed",
                "Carrier reported customs delay against expected delivery.",
            )
        for event_type, location, status, notes in event_templates:
            events.append(
                LogisticsEvent(
                    id=f"LOG-{event_counter:04d}",
                    related_sales_order_id=order_id,
                    event_type=event_type,
                    event_date=base_date + timedelta(days=order_index + event_counter % 3),
                    location=location,
                    status=status,
                    notes=notes,
                )
            )
            event_counter += 1
    return events


def _build_invoice_and_payment_summaries(
    sales_orders: list[SalesOrder],
) -> tuple[list[InvoiceSummary], list[PaymentSummary]]:
    invoice_summaries = []
    payment_summaries = []
    for index, order in enumerate(sales_orders[:15], start=1):
        invoice_date = order.order_date + timedelta(days=3)
        due_date = invoice_date + timedelta(days=30)
        status = "paid" if index in {1, 2, 5, 10, 14} else "issued"
        payment_status = "paid" if status == "paid" else "not_due"
        amount_paid = order.subtotal if status == "paid" else 0.0
        if order.id == "SO-1007":
            status = "overdue"
            payment_status = "overdue"
            amount_paid = 0.0

        invoice = InvoiceSummary(
            id=f"INV-{3000 + index}",
            sales_order_id=order.id,
            customer_id=order.customer_id,
            invoice_date=invoice_date,
            due_date=due_date,
            amount=order.subtotal,
            status=status,
        )
        invoice_summaries.append(invoice)
        payment_summaries.append(
            PaymentSummary(
                id=f"PAY-{4000 + index}",
                invoice_id=invoice.id,
                sales_order_id=order.id,
                customer_id=order.customer_id,
                amount_due=round(order.subtotal - amount_paid, 2),
                amount_paid=amount_paid,
                due_date=due_date,
                status=payment_status,
            )
        )
    return invoice_summaries, payment_summaries


if __name__ == "__main__":
    raise SystemExit(main())
