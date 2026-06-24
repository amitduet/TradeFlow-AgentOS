---
name: purchase-order-recommendation
description: Recommend whether a sales order needs a linked purchase order draft without executing procurement.
version: sprint-006-v1
owner: TradeFlow AgentOS
allowed_actions:
  - recommend_purchase_order_draft
  - explain_procurement_evidence
  - recommend_next_safe_step
disallowed_actions:
  - create_purchase_order_without_approval
  - submit_purchase_order
  - approve_purchase_order
  - invent_supplier_or_product_data
related_runbooks:
  - ../../domain/runbooks/purchase-order-recommendation-rules.md
  - ../../domain/runbooks/supplier-risk-rules.md
  - ../../domain/runbooks/approval-gate-rules.md
trigger_phrases:
  - create a purchase order
  - purchase order
  - po recommendation
  - po draft
  - drop-shipping order
  - drop shipping order
non_trigger_phrases:
  - analyze customer rating only
  - approve the order directly
  - summarize logistics events
---

# Purchase Order Recommendation

## What This Skill Does

Recommends whether a valid sales order should have a linked purchase order draft, especially for drop-shipping or supplier-dependent fulfillment.

## When It Should Trigger

- The user asks whether to create a purchase order for a sales order.
- The user asks for a PO recommendation.
- The user asks whether a drop-shipping order needs a PO draft.

## When It Must Not Trigger

- The user asks only about customer rating.
- The user asks to approve an order directly.
- The user asks only to summarize logistics events.
- The user requests unsupported procurement without a sales order.

## Required Inputs

- Valid sales order id.
- Fulfillment type and line items.
- Supplier and product context when available.
- Linked purchase order draft evidence.
- Approval gate status.

## Business Process Steps

1. Confirm the request is a recommendation, not execution.
2. Require a valid sales order context.
3. Check drop-shipping and linked purchase order draft evidence.
4. Identify missing supplier or product information.
5. Recommend next safe procurement step and preserve approval.

## Relevant Runbooks

- `domain/runbooks/purchase-order-recommendation-rules.md`
- `domain/runbooks/supplier-risk-rules.md`
- `domain/runbooks/approval-gate-rules.md`

## Required Outputs

- Recommendation to prepare, not execute, a purchase order draft when justified.
- Sales order to purchase order linkage requirement.
- Missing supplier or product evidence, if any.
- Approval requirement and next safe step.

## Safety Constraints

- Do not create, submit, approve, or send purchase orders.
- Do not fabricate suppliers, products, availability, or lead time.
- Escalate missing procurement evidence.
- Refuse approval bypass.

## Example User Requests

- "Should we create a purchase order for SO-1005?"
- "Prepare PO recommendation for this order"
- "Does this drop-shipping order need a PO draft?"

## Example Expected Behavior

Recommend whether a linked purchase order draft is needed, cite sales order and supplier evidence, and keep procurement action behind human approval.
