# Synthetic Data Model

All tables are synthetic and local-demo only. They must not contain real customers, real TAM data, private supplier terms, or production transaction details.

Sprint 2 adds a deterministic JSON dataset at `data/synthetic/tradeflow_seed.json`. It supports multi-line-ready sales orders and purchase order drafts through `line_items`, although the canonical records currently use one line per order for readability.

## customers

- customer_id: string primary key
- customer_name: string
- rating: integer from 1 to 5, used by deterministic risk tools
- segment: string
- payment_terms: string
- credit_limit: decimal
- credit_rating: string
- risk_rating: low, medium, high, blocked
- status: active, watchlist, blocked
- billing_address: synthetic text
- shipping_address: synthetic text
- phone_number: synthetic phone string
- primary_contact_name: synthetic contact name
- primary_contact_email: synthetic email
- primary_contact_phone: synthetic phone string
- primary_contact_designation: string

Sprint 2 JSON fields:

- id: string primary key
- name: synthetic customer name
- rating: integer from 1 to 5
- billing_address: synthetic billing address
- shipping_address: synthetic shipping address
- phone_number: synthetic phone string
- contact_person: object with name, email, phone, and designation

## crm_opportunities

- opportunity_id: string primary key
- customer_id: string
- stage: string
- expected_value: decimal
- probability: decimal
- notes: synthetic text

## products

- product_id: string primary key
- sku: string
- product_name: string
- unit_price: decimal
- unit_cost: decimal

Sprint 2 JSON fields:

- id: string primary key
- sku: synthetic SKU
- name: product name
- category: product category
- unit: selling unit
- supplier_id: supplier reference
- standard_cost: decimal
- sale_price: decimal

## inventory

- inventory_id: string primary key
- product_id: string
- warehouse_id: string
- warehouse: string
- available_qty: integer
- reserved_qty: integer
- incoming_qty: integer
- reorder_level: integer

## suppliers

- supplier_id: string primary key
- supplier_name: string
- rating: integer
- lead_time_days: integer
- reliability_score: decimal
- default_currency: string
- default_incoterm: string
- payment_terms: string
- phone_number: synthetic phone string
- primary_contact_name: synthetic contact name
- primary_contact_email: synthetic email
- primary_contact_phone: synthetic phone string
- primary_contact_designation: string
- approved: boolean

Sprint 2 JSON fields:

- id: string primary key
- name: synthetic supplier name
- country: supplier country
- phone_number: synthetic phone string
- contact_person: object with name, email, phone, and designation

## purchase_options

- purchase_option_id: string primary key
- supplier_id: string
- product_id: string
- unit_cost: decimal
- minimum_order_quantity: integer
- lead_time_days: integer

## customer_order_requests

- customer_order_request_id: string primary key
- customer_id: string
- product_id: string
- quantity: integer
- requested_delivery_date: date
- sales_type: stock_sale, procurement_sale, drop_ship, intercompany
- order_status: under_review, finance_review, procurement_required, approved_with_conditions, rejected, ready_for_delivery, delivered, invoice_drafted
- procurement_required: boolean
- finance_consent_status: pending, approved, approved_with_conditions, rejected, needs_human_review
- human_approval_required: boolean

## sales_orders

Lightweight simulated sales order record created from an approved customer order request. This is not a real ERP sales order.

- sales_order_id: string primary key
- customer_order_request_id: string
- customer_id: string
- order_date: date
- order_status: draft, pending_human_approval, approved_simulated, fulfilled, canceled
- delivery_status: pending, ready_for_delivery, dispatched, delivered, delayed
- invoice_status: not_ready, draft_ready, invoice_drafted, pending_human_approval
- created_from_request: boolean

Sprint 2 JSON fields:

- id: string primary key
- customer_id: customer reference
- order_date: date
- expected_delivery_date: date
- status: draft, confirmed, in_transit, delivered, delayed, cancelled
- incoterm: synthetic trade term
- fulfillment_type: warehouse_stock, procurement, drop_ship
- line_items: list of product_id, quantity, and unit_price
- subtotal: decimal
- risk_flags: list of pre-existing synthetic review hints
- notes: synthetic text

## purchase_order_drafts

- purchase_order_draft_id: string primary key
- customer_order_request_id: string
- sales_order_id: string
- supplier_id: string
- product_id: string
- quantity: integer
- procurement_route: warehouse_stock, drop_shipping, direct_shipment, intercompany
- finance_consent_status: pending, approved, approved_with_conditions, rejected, needs_human_review
- finance_conditions: synthetic text or string list
- human_approval_required: boolean
- draft_status: prepared, pending_human_approval, approved_by_human, canceled

Sprint 2 JSON fields:

- id: string primary key
- supplier_id: supplier reference
- related_sales_order_id: nullable sales order reference
- purpose: stock_replenishment, drop_shipping, customer_procurement
- status: draft, pending_approval, approved_by_human, cancelled
- line_items: list of product_id, quantity, and unit_price
- subtotal: decimal
- created_from_sales_order: boolean
- notes: synthetic text

Rule: drop-shipping purchase order drafts must have `related_sales_order_id` populated so the drop-shipping chain can be reconstructed deterministically.

## logistics_events

- logistics_event_id: string primary key
- related_record_id: string
- customer_order_request_id: string
- sales_order_id: string
- purchase_order_draft_id: string
- event_type: inbound_shipment, goods_received, outbound_delivery, customer_delivery_confirmed, delay_reported
- event_timestamp: datetime
- carrier: synthetic carrier name
- tracking_reference: synthetic tracking string
- expected_date: date
- actual_date: date
- from_location: synthetic location
- to_location: synthetic location
- notes: synthetic text

Sprint 2 JSON fields:

- id: string primary key
- related_sales_order_id: required sales order reference
- event_type: booking_created, picked_up, customs_clearance, in_transit, delay_reported, out_for_delivery, delivered
- event_date: date
- location: synthetic location
- status: planned, completed, delayed, exception
- notes: synthetic text

Rule: every logistics event must reference a valid sales order through `related_sales_order_id`.

## invoice_summaries

- id: string primary key
- sales_order_id: sales order reference
- customer_id: customer reference
- invoice_date: date
- due_date: date
- amount: decimal
- status: draft, issued, paid, overdue, cancelled

## payment_summaries

- id: string primary key
- invoice_id: invoice reference
- sales_order_id: sales order reference
- customer_id: customer reference
- amount_due: decimal
- amount_paid: decimal
- due_date: date
- status: not_due, partial, paid, overdue

## Referential Integrity

The Sprint 2 `TradeFlowDataset` Pydantic model validates that:

- sales orders reference existing customers
- products and purchase order drafts reference existing suppliers
- line items reference existing products
- purchase order draft `related_sales_order_id` values exist when provided
- logistics events reference existing sales orders
- invoice and payment summaries reference existing customers, orders, and invoices

## invoice_drafts

- invoice_draft_id: string primary key
- customer_order_request_id: string
- customer_id: string
- amount: decimal
- draft_status: prepared, pending_human_approval, approved_by_human, canceled

## finance_exposure

- finance_exposure_id: string primary key
- customer_id: string
- customer_order_request_id: string
- order_value: decimal
- gross_margin_percent: decimal
- open_receivables: decimal
- pending_order_exposure: decimal
- credit_limit: decimal
- available_credit: decimal
- working_capital_impact: decimal
- finance_risk_level: low, medium, high, blocked
- finance_consent_status: pending, approved, approved_with_conditions, rejected, needs_human_review
- finance_conditions: synthetic text or string list
- risk_status: acceptable, watchlist, exceeded

## agent_logs

- agent_log_id: string primary key
- correlation_id: string
- workflow_case_id: string
- agent_name: string
- event_name: string
- action_type: string
- tool_called: string
- decision: synthetic text
- confidence_score: decimal
- summary: synthetic text
- created_at: datetime
