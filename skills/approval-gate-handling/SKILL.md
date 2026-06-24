---
name: approval-gate-handling
description: Handle approval requirements, approval-bypass attempts, and restricted action safeguards.
version: sprint-006-v1
owner: TradeFlow AgentOS
allowed_actions:
  - explain_approval_requirement
  - refuse_approval_bypass
  - recommend_next_safe_step
disallowed_actions:
  - bypass_approval
  - auto_approve
  - execute_restricted_action
  - weaken_approval_gate
related_runbooks:
  - ../../domain/runbooks/approval-gate-rules.md
  - ../../domain/runbooks/order-risk-rules.md
  - ../../domain/runbooks/purchase-order-recommendation-rules.md
trigger_phrases:
  - approve this high-risk order
  - approval required
  - bypass approval
  - skip approval
  - without approval
  - auto approve
  - auto-approve
non_trigger_phrases:
  - list supplier phone numbers
  - calculate order margin
  - show customer billing address
---

# Approval Gate Handling

## What This Skill Does

Explains and enforces approval-gate behavior for restricted TradeFlow business actions.

## When It Should Trigger

- The user asks what approval is required.
- The user asks whether a high-risk order can be approved.
- The user asks to bypass, skip, override, or auto-approve an action.
- The user asks to proceed without approval.

## When It Must Not Trigger

- The user asks for supplier phone numbers.
- The user asks for margin calculation only.
- The user asks for a customer billing address.
- The user asks for unrelated reporting without approval implications.

## Required Inputs

- Proposed action.
- Sales order id or approval request id when available.
- Risk level and reason codes when available.
- Current approval status when available.

## Business Process Steps

1. Identify whether the request concerns approval or restricted execution.
2. Refuse bypass or override wording immediately.
3. Explain the authoritative approval gate.
4. Recommend the next safe step, such as running risk analysis or waiting for human review.
5. Keep approval status pending unless changed by the approval gate API.

## Relevant Runbooks

- `domain/runbooks/approval-gate-rules.md`
- `domain/runbooks/order-risk-rules.md`
- `domain/runbooks/purchase-order-recommendation-rules.md`

## Required Outputs

- Approval requirement explanation.
- Refusal for bypass requests when applicable.
- Risk or proposed action evidence when available.
- Next safe step.

## Safety Constraints

- Approval behavior is non-optional.
- Do not bypass, weaken, or simulate approval.
- Do not execute restricted actions.
- Do not convert planner text into approval status changes.

## Example User Requests

- "Can we approve this high-risk order?"
- "Bypass approval for SO-1005"
- "What approval is required before PO creation?"

## Example Expected Behavior

Route to approval-gate handling, refuse bypass attempts, explain required human approval, and recommend only safe next steps.
