# Order Risk Rules

## Purpose

Define the business rules for evaluating whether a sales order is safe to proceed, needs monitoring, or requires escalation before any downstream action.

## When to Use

Use this runbook when a user asks to analyze a sales order, check order risk, decide whether an order is safe to proceed, or prepare an order-level recommendation.

## Inputs Required

- Valid sales order id, such as `SO-1005`
- Customer profile, including rating and available contact data
- Sales order value, fulfillment type, and line items
- Supplier and purchase order draft context when procurement or drop-shipping is involved
- Logistics events linked to the sales order
- Finance and margin summaries when available

## Risk Indicators

- High-value orders increase risk and may need manager review.
- Missing customer data increases risk, especially missing billing address, shipping address, phone number, or contact person.
- Low customer rating increases risk.
- Delayed logistics events increase risk.
- Supplier lead-time, availability, or missing supplier context increases risk.
- Low margin, overdue payment, or credit exposure increases risk.

## Decision Rules

- Unsupported or unknown sales orders must not be guessed.
- Use only available deterministic evidence from tools or workflow outputs.
- Explain risk with reason codes and evidence, not speculation.
- If required sales order data is missing, ask for clarification or escalate.
- If risk is high, recommend human review before action.
- If drop-shipping lacks a linked purchase order draft, recommend preparing a linked draft after approval.

## Required Evidence

- Sales order id and summary
- Customer rating and relevant missing customer profile fields
- Risk flags and risk level
- Logistics delay or exception evidence when present
- Supplier and purchase order draft linkage when relevant
- Approval request status for proposed actions

## Approval Requirements

- Any recommended business action must preserve the approval gate.
- High-risk actions require human approval.
- Purchase order creation, supplier contact, customer contact, manager escalation, invoice, shipment, or stock-changing actions cannot be executed directly by the planner.

## Refusal and Escalation Conditions

- Refuse requests to invent order facts, use unsupported systems, or bypass approval.
- Escalate when the order id is missing, the order is unknown, required business evidence is unavailable, or the user asks for an unsupported decision.
- Treat incomplete customer, supplier, or logistics context as business risk.

## Examples

- "Analyze sales order SO-1005" -> run approved order-risk analysis and cite risk flags.
- "Is SO-1005 safe to proceed?" -> explain risk level, reason codes, evidence, and approval status.
- "Approve SO-1005 now" -> do not approve directly; explain the approval gate and next safe step.
