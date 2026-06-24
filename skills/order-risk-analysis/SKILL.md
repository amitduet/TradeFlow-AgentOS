---
name: order-risk-analysis
description: Analyze sales order risk with deterministic TradeFlow evidence and approval-gated recommendations.
version: sprint-006-v1
owner: TradeFlow AgentOS
allowed_actions:
  - analyze_sales_order_risk
  - explain_reason_codes
  - recommend_next_safe_step
disallowed_actions:
  - approve_order
  - bypass_approval
  - execute_purchase_order
  - invent_missing_order_data
related_runbooks:
  - ../../domain/runbooks/order-risk-rules.md
  - ../../domain/runbooks/customer-risk-rules.md
  - ../../domain/runbooks/logistics-risk-rules.md
  - ../../domain/runbooks/supplier-risk-rules.md
trigger_phrases:
  - analyze sales order
  - check risk
  - safe to proceed
  - order risk
  - customer order
non_trigger_phrases:
  - create a supplier contact record
  - show system health
  - write a marketing email
---

# Order Risk Analysis

## What This Skill Does

Analyzes sales order risk using TradeFlow deterministic workflow outputs, reason codes, and approval gate status.

## When It Should Trigger

- The user asks to analyze a sales order.
- The user asks whether an order is safe to proceed.
- The user asks for risk on a customer order.

## When It Must Not Trigger

- The user asks to create supplier records.
- The user asks for system health or unrelated platform status.
- The user asks for marketing copy or non-operational writing.
- The user asks to bypass approval; route that to approval-gate handling.

## Required Inputs

- Sales order id when available.
- Customer, supplier, logistics, margin, and order evidence returned by approved tools.
- Approval request status for any recommended action.

## Business Process Steps

1. Confirm the request is about sales order risk or safety.
2. Extract a sales order id when present.
3. Use only approved deterministic workflow evidence.
4. Summarize risk level, reason codes, and cited evidence.
5. Preserve approval gate requirements for any recommended action.

## Relevant Runbooks

- `domain/runbooks/order-risk-rules.md`
- `domain/runbooks/customer-risk-rules.md`
- `domain/runbooks/logistics-risk-rules.md`
- `domain/runbooks/supplier-risk-rules.md`

## Required Outputs

- Selected skill name.
- Sales order id when recognized.
- Risk level when workflow evidence exists.
- Reason codes and evidence summary.
- Approval status and next safe step.

## Safety Constraints

- Do not guess unsupported or unknown sales orders.
- Do not execute downstream actions.
- Do not bypass approval.
- Refuse unavailable or confidential data requests.

## Example User Requests

- "Analyze sales order SO-1005"
- "Check risk for this customer order"
- "Is SO-1005 safe to proceed?"

## Example Expected Behavior

Route to the order-risk workflow, cite deterministic risk evidence, explain reason codes, and leave required approval pending.
