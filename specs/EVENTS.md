# Event Contracts

TradeFlow AgentOS uses A2A-style event messages to make agent handoffs explicit and testable. Events are synthetic workflow records, not production commands.

## Event Envelope

| Field | Type | Description |
| --- | --- | --- |
| event_id | string | Unique event id. |
| event_type | string | Business event name. |
| source_agent | string | Agent emitting the event. |
| target_agent | string | Agent expected to handle the event. |
| correlation_id | string | Shared workflow id for the order lifecycle. |
| payload | object | Event-specific synthetic data. |
| requires_human_approval | boolean | Whether the next real-world action would require approval. |
| created_at | datetime | Event timestamp. |

## Order Request Created

```json
{
  "event_id": "evt_order_request_001",
  "event_type": "order_request_created",
  "source_agent": "sales",
  "target_agent": "orchestrator",
  "correlation_id": "ord_req_001",
  "payload": {
    "customer_id": "cust_demo_001",
    "product_id": "prod_demo_001",
    "quantity": 25
  },
  "requires_human_approval": false
}
```

## Inventory Shortfall Found

```json
{
  "event_id": "evt_inventory_shortfall_001",
  "event_type": "inventory_shortfall_found",
  "source_agent": "inventory",
  "target_agent": "purchase",
  "correlation_id": "ord_req_002",
  "payload": {
    "product_id": "prod_demo_002",
    "requested_quantity": 80,
    "available_quantity": 30,
    "shortfall_quantity": 50
  },
  "requires_human_approval": false
}
```

## Finance Consent Given

```json
{
  "event_id": "evt_finance_consent_001",
  "event_type": "finance_consent_given",
  "source_agent": "finance",
  "target_agent": "purchase",
  "correlation_id": "ord_req_002",
  "payload": {
    "decision_status": "approved_with_conditions",
    "conditions": ["Collect 40 percent advance payment before supplier PO approval"]
  },
  "requires_human_approval": true
}
```

## Goods Received

```json
{
  "event_id": "evt_goods_received_001",
  "event_type": "goods_received",
  "source_agent": "logistics",
  "target_agent": "inventory",
  "correlation_id": "ord_req_002",
  "payload": {
    "purchase_order_draft_id": "po_draft_001",
    "product_id": "prod_demo_002",
    "received_quantity": 50
  },
  "requires_human_approval": false
}
```

## Delivery Confirmed

```json
{
  "event_id": "evt_delivery_confirmed_001",
  "event_type": "delivery_confirmed",
  "source_agent": "logistics",
  "target_agent": "sales",
  "correlation_id": "ord_req_002",
  "payload": {
    "customer_order_request_id": "ord_req_002",
    "delivered_quantity": 80
  },
  "requires_human_approval": false
}
```
