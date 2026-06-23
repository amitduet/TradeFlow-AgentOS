"""Typed contracts for the Sprint 2 synthetic TradeFlow dataset."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, PositiveInt, model_validator


class ContactPerson(BaseModel):
    name: str
    email: str
    phone: str
    designation: str


class Customer(BaseModel):
    id: str
    name: str
    rating: int = Field(ge=1, le=5)
    billing_address: str
    shipping_address: str
    phone_number: str
    contact_person: ContactPerson


class Supplier(BaseModel):
    id: str
    name: str
    country: str
    phone_number: str
    contact_person: ContactPerson


class Product(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    unit: str
    supplier_id: str
    standard_cost: float = Field(gt=0)
    sale_price: float = Field(gt=0)


class OrderLineItem(BaseModel):
    product_id: str
    quantity: PositiveInt
    unit_price: float = Field(gt=0)


class SalesOrder(BaseModel):
    id: str
    customer_id: str
    order_date: date
    expected_delivery_date: date
    status: Literal["draft", "confirmed", "in_transit", "delivered", "delayed", "cancelled"]
    incoterm: str
    fulfillment_type: Literal["warehouse_stock", "procurement", "drop_ship"]
    line_items: list[OrderLineItem]
    subtotal: float = Field(ge=0)
    risk_flags: list[str] = Field(default_factory=list)
    notes: str


class PurchaseOrderDraft(BaseModel):
    id: str
    supplier_id: str
    related_sales_order_id: str | None = None
    purpose: Literal["stock_replenishment", "drop_shipping", "customer_procurement"]
    status: Literal["draft", "pending_approval", "approved_by_human", "cancelled"]
    line_items: list[OrderLineItem]
    subtotal: float = Field(ge=0)
    created_from_sales_order: bool
    notes: str


class LogisticsEvent(BaseModel):
    id: str
    related_sales_order_id: str
    event_type: Literal[
        "booking_created",
        "picked_up",
        "customs_clearance",
        "in_transit",
        "delay_reported",
        "out_for_delivery",
        "delivered",
    ]
    event_date: date
    location: str
    status: Literal["planned", "completed", "delayed", "exception"]
    notes: str


class InvoiceSummary(BaseModel):
    id: str
    sales_order_id: str
    customer_id: str
    invoice_date: date
    due_date: date
    amount: float = Field(ge=0)
    status: Literal["draft", "issued", "paid", "overdue", "cancelled"]


class PaymentSummary(BaseModel):
    id: str
    invoice_id: str
    sales_order_id: str
    customer_id: str
    amount_due: float = Field(ge=0)
    amount_paid: float = Field(ge=0)
    due_date: date
    status: Literal["not_due", "partial", "paid", "overdue"]


class TradeFlowDataset(BaseModel):
    customers: list[Customer]
    suppliers: list[Supplier]
    products: list[Product]
    sales_orders: list[SalesOrder]
    purchase_order_drafts: list[PurchaseOrderDraft]
    logistics_events: list[LogisticsEvent]
    invoice_summaries: list[InvoiceSummary] = Field(default_factory=list)
    payment_summaries: list[PaymentSummary] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "TradeFlowDataset":
        customer_ids = {customer.id for customer in self.customers}
        supplier_ids = {supplier.id for supplier in self.suppliers}
        product_ids = {product.id for product in self.products}
        sales_order_ids = {order.id for order in self.sales_orders}
        invoice_ids = {invoice.id for invoice in self.invoice_summaries}

        for product in self.products:
            if product.supplier_id not in supplier_ids:
                raise ValueError(f"Product {product.id} references unknown supplier {product.supplier_id}.")

        for order in self.sales_orders:
            if order.customer_id not in customer_ids:
                raise ValueError(f"Sales order {order.id} references unknown customer {order.customer_id}.")
            for line_item in order.line_items:
                if line_item.product_id not in product_ids:
                    raise ValueError(
                        f"Sales order {order.id} references unknown product {line_item.product_id}."
                    )

        for draft in self.purchase_order_drafts:
            if draft.supplier_id not in supplier_ids:
                raise ValueError(f"PO draft {draft.id} references unknown supplier {draft.supplier_id}.")
            if draft.related_sales_order_id and draft.related_sales_order_id not in sales_order_ids:
                raise ValueError(
                    f"PO draft {draft.id} references unknown sales order {draft.related_sales_order_id}."
                )
            for line_item in draft.line_items:
                if line_item.product_id not in product_ids:
                    raise ValueError(f"PO draft {draft.id} references unknown product {line_item.product_id}.")

        for event in self.logistics_events:
            if event.related_sales_order_id not in sales_order_ids:
                raise ValueError(
                    f"Logistics event {event.id} references unknown sales order {event.related_sales_order_id}."
                )

        for invoice in self.invoice_summaries:
            if invoice.sales_order_id not in sales_order_ids:
                raise ValueError(f"Invoice {invoice.id} references unknown sales order {invoice.sales_order_id}.")
            if invoice.customer_id not in customer_ids:
                raise ValueError(f"Invoice {invoice.id} references unknown customer {invoice.customer_id}.")

        for payment in self.payment_summaries:
            if payment.invoice_id not in invoice_ids:
                raise ValueError(f"Payment {payment.id} references unknown invoice {payment.invoice_id}.")
            if payment.sales_order_id not in sales_order_ids:
                raise ValueError(f"Payment {payment.id} references unknown sales order {payment.sales_order_id}.")
            if payment.customer_id not in customer_ids:
                raise ValueError(f"Payment {payment.id} references unknown customer {payment.customer_id}.")

        return self
