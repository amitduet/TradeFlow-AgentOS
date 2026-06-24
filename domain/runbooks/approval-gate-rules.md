# Approval Gate Rules

## Purpose

Define how the human approval gate controls restricted business actions in TradeFlow AgentOS.

## When to Use

Use this runbook when a request asks about approval requirements, approving high-risk work, bypassing approval, or executing an action that requires human review.

## Inputs Required

- Proposed action and related sales order id when available
- Risk level and reason codes
- Approval request id and current approval status when available
- Evidence behind the recommendation

## Risk Indicators

- High-risk actions require explicit human approval.
- Requests to skip, bypass, override, auto-approve, or proceed without approval are safety risks.
- Missing approval status is a control risk.
- Any direct execution request for procurement, invoice, shipment, stock, or customer/supplier messages is restricted.

## Decision Rules

- Approval gate is authoritative.
- Planner must not bypass approval.
- User requests to skip or override approval must be refused.
- The planner may recommend next safe steps, but not execute restricted actions.
- Approval status must remain pending unless changed through the explicit approval gate API.

## Required Evidence

- Approval request id when one exists
- Approval status
- Proposed action
- Risk level
- Reason codes explaining why approval is required

## Approval Requirements

- High-risk actions require human approval.
- Purchase order creation, invoice creation, stock movement, shipment changes, and customer or supplier outbound messages require approval before execution.
- Approval must be handled through `approve_request` or `reject_request`, not planner text.

## Refusal and Escalation Conditions

- Refuse bypass wording such as "bypass approval", "skip approval", "auto approve", or "without approval".
- Escalate if the approval request id or sales order context is missing.
- Refuse execution when the approval gate is not satisfied.

## Examples

- "Can we approve this high-risk order?" -> explain required approval state and next safe step.
- "Bypass approval for SO-1005" -> refuse and cite the authoritative approval gate.
- "What approval is required before PO creation?" -> explain required human approval and evidence.
