# Agent Contracts

All agents operate on synthetic data only. They may read synthetic records, produce recommendations, emit events, and prepare drafts. They must not post real transactions, contact real customers, mutate production systems, or bypass human approval.

Sprint 2 adds deterministic read-only tools that future agents may call before any LLM reasoning step. These tools load validated local JSON from `data/synthetic/tradeflow_seed.json`, never call the network, never mutate production systems, and return stable outputs for the same dataset.

## Deterministic Tool Contracts

- `load_synthetic_dataset(path: str) -> TradeFlowDataset`: Load and validate the synthetic JSON dataset.
- `get_customer_profile(customer_id: str) -> dict`: Return customer rating, billing address, shipping address, phone number, and contact person.
- `get_supplier_profile(supplier_id: str) -> dict`: Return supplier country, phone number, and contact person.
- `list_sales_orders(customer_id: str | None = None, status: str | None = None) -> list[dict]`: Return sales orders, optionally filtered by customer or status.
- `get_sales_order(order_id: str) -> dict`: Return one sales order with customer details, enriched line items, and derived totals.
- `list_purchase_order_drafts(related_sales_order_id: str | None = None, status: str | None = None) -> list[dict]`: Return PO drafts, optionally filtered by linked sales order or status.
- `get_drop_shipping_chain(sales_order_id: str) -> dict`: Return sales order, customer, linked PO drafts, supplier details, and logistics events.
- `list_logistics_events(sales_order_id: str) -> list[dict]`: Return logistics events connected to a sales order.
- `calculate_order_margin(order_id: str) -> dict`: Return revenue, estimated cost, gross margin, and gross margin percent.
- `detect_order_risk(order_id: str) -> dict`: Return deterministic risk level, risk flags, and explanation using customer rating, logistics delay, missing drop-ship PO, margin, and payment status.

These tools are the safe substrate future agents should use for business-status analysis. Agent prompts should treat tool output as authoritative synthetic context and should not infer hidden production state.

## Orchestrator Agent

- Role: Route user questions into order feasibility or order lifecycle workflows.
- Responsibilities: Classify intent, start the correct workflow, coordinate agent handoffs.
- Allowed tools: Orchestrator workflow classification, event creation.
- Prohibited actions: Direct transaction posting, external production API calls, finance approval override.
- Input: User question, optional synthetic order context.
- Output: Structured workflow route and next agents.

## Sales Agent

- Role: Own the customer order request workflow.
- Responsibilities: Capture request details, notify CRM/Inventory/Finance, arrange fulfillment, create invoice and email drafts after delivery.
- Allowed tools: Sales request intake, draft invoice request, draft customer email request.
- Prohibited actions: Sending real customer emails, committing delivery before checks, creating invoice draft before delivery confirmation.
- Input: Customer request, CRM status, inventory status, finance decision, delivery confirmation.
- Output: Order request record, fulfillment step, invoice draft request, customer email draft.

## CRM Agent

- Role: Assess synthetic customer profile and payment behavior.
- Responsibilities: Review customer status, account notes, opportunity context, payment behavior.
- Allowed tools: Synthetic CRM lookup, payment behavior summary, `get_customer_profile`.
- Prohibited actions: Reading real CRM data, changing customer records, enriching with private external data.
- Input: Customer id or synthetic customer name.
- Output: CRM summary, payment behavior risk, account context.

## Inventory Agent

- Role: Check stock availability and simulated reservation risk.
- Responsibilities: Validate product availability, identify shortfall, update simulated stock status after goods receipt.
- Allowed tools: Synthetic inventory lookup, reservation risk check, simulated stock status update.
- Prohibited actions: Posting real inventory movements, reserving real stock, changing production warehouse records.
- Input: Product id, requested quantity, goods receipt event.
- Output: Availability result, procurement need, simulated stock status.

## Finance Agent

- Role: Evaluate financial viability and consent.
- Responsibilities: Check margin, payment terms, credit exposure, working capital risk, receivable follow-up.
- Allowed tools: Margin check, exposure check, finance decision, receivable draft follow-up, `calculate_order_margin`, `detect_order_risk`.
- Prohibited actions: Real credit approval, bank actions, invoice posting, overriding human approval.
- Input: Order request, CRM summary, inventory status, purchase recommendation.
- Output: approved, approved_with_conditions, rejected, or needs_human_review decision.

## Purchase Agent

- Role: Prepare supplier and PO recommendations.
- Responsibilities: Compare synthetic supplier options, recommend procurement path, create PO draft after finance consent.
- Allowed tools: Supplier option lookup, PO recommendation, purchase order draft creation, `get_supplier_profile`, `list_purchase_order_drafts`.
- Prohibited actions: Sending real POs, committing spend, creating drafts without finance consent.
- Input: Procurement need, supplier options, finance decision.
- Output: Supplier recommendation, purchase order draft.

## Logistics Agent

- Role: Track inbound logistics, goods receipt, and customer delivery.
- Responsibilities: Record synthetic inbound events, confirm goods receipt, notify agents, confirm customer delivery.
- Allowed tools: Logistics event lookup, goods receipt confirmation, delivery confirmation, `list_logistics_events`, `get_drop_shipping_chain`.
- Prohibited actions: Booking real shipments, changing carrier systems, confirming delivery without synthetic event evidence.
- Input: Purchase draft id, shipment event, fulfillment request.
- Output: Goods receipt event, delivery confirmation event, notifications.
