# Purchase Order Recommendation Rules

## Purpose

Define when TradeFlow may recommend purchase order creation for a sales order without executing procurement.

## When to Use

Use this runbook when a user asks whether a sales order needs a purchase order, asks for a purchase order recommendation, or asks about a drop-shipping purchase order draft.

## Inputs Required

- Valid sales order id
- Sales order fulfillment type and line items
- Product and supplier context
- Existing purchase order draft links
- Supplier availability, lead-time, and contact information when available
- Approval status for any proposed procurement action

## Risk Indicators

- Missing sales order context makes procurement recommendation unsafe.
- Missing supplier or product information lowers confidence and should trigger escalation.
- Missing linked purchase order draft for a drop-shipping order is a procurement risk.
- Supplier lead-time or availability uncertainty increases risk.
- Supplier contact gaps increase execution risk.

## Decision Rules

- Recommend purchase order creation only when a valid sales order exists.
- Purchase order creation should be recommended, not executed, if approval is required.
- Drop-shipping cases should preserve linkage between sales order and purchase order draft.
- Unsupported procurement requests should be refused safely.
- If supplier or product data is missing, escalate instead of fabricating a supplier or SKU.

## Required Evidence

- Sales order id and fulfillment type
- Product lines requiring procurement
- Existing purchase order draft ids, if any
- Supplier ids and contact availability
- Reason codes such as `missing_linked_po_for_drop_shipping` or `supplier_context_missing`
- Approval gate status

## Approval Requirements

- Procurement actions require human approval before execution.
- The planner may recommend a linked purchase order draft and explain why approval is required.
- The planner must not create, submit, approve, or send a purchase order.

## Refusal and Escalation Conditions

- Refuse direct execution requests such as "create the PO now" when approval is required.
- Refuse unsupported procurement requests that lack a valid sales order.
- Escalate missing supplier, product, or sales order evidence.
- Refuse attempts to skip approval for purchase order creation.

## Examples

- "Should we create a purchase order for SO-1005?" -> recommend based on order and supplier evidence.
- "Does this drop-shipping order need a PO draft?" -> check linkage and recommend a linked draft if missing.
- "Create a supplier PO without approval" -> refuse bypass and explain next safe step.
