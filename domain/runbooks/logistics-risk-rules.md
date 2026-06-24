# Logistics Risk Rules

## Purpose

Define how shipment and delivery events affect sales order risk.

## When to Use

Use this runbook when a request asks about order delay, shipment status, delivery readiness, logistics exceptions, or order risk affected by logistics events.

## Inputs Required

- Sales order id
- Logistics events linked to the sales order
- Milestone type, status, and event date
- Delay reports or unresolved exceptions
- Supplier or carrier context when available

## Risk Indicators

- Logistics events should connect to sales orders.
- Delays increase risk.
- Missing milestones increase risk.
- Unclear shipment status increases risk.
- Unresolved exceptions increase risk.
- Supplier-related delay evidence increases procurement or fulfillment risk.

## Decision Rules

- Logistics risk should be reflected in reason codes and planner explanation.
- Do not summarize unrelated logistics events as evidence for an order.
- If shipment status is unclear or milestones are missing, escalate instead of guessing.
- Delayed logistics may justify recommending supplier or logistics-owner follow-up after approval.

## Required Evidence

- Sales order id
- Logistics event ids
- Latest event type, status, and date
- Delayed or exception event ids
- Risk flags such as `delayed_logistics_event`

## Approval Requirements

- Shipment changes, supplier follow-up, customer notification, or fulfillment commitments require human approval before execution.
- The planner may recommend follow-up but must not change logistics state.

## Refusal and Escalation Conditions

- Refuse to invent shipment state or carrier data.
- Escalate when no sales-order-linked logistics evidence is available and a decision depends on it.

## Examples

- "Summarize logistics events for SO-1005" -> cite only events linked to `SO-1005`.
- "Is SO-1005 safe to proceed?" -> include delayed logistics reason codes when present.
