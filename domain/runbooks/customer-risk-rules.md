# Customer Risk Rules

## Purpose

Define customer profile signals that affect sales order and credit risk.

## When to Use

Use this runbook when evaluating customer risk for an order, reviewing customer profile completeness, or explaining how customer evidence affects order risk.

## Inputs Required

- Customer id and customer name
- Customer rating
- Billing address, shipping address, and phone number when available
- Contact person data: name, email, phone, and designation when available
- Payment or credit indicators when available

## Risk Indicators

- Low customer rating increases risk.
- Missing billing address increases risk.
- Missing shipping address increases risk.
- Missing phone number increases risk.
- Missing or incomplete contact person increases risk.
- Incomplete customer profile should be treated as a business risk.

## Decision Rules

- Customer rating affects risk level.
- Do not invent missing customer contact details.
- Explain customer risk with reason codes and available evidence.
- Escalate when customer information is required for a decision but incomplete.

## Required Evidence

- Customer id
- Rating
- Missing customer fields, if any
- Contact person fields available in the dataset
- Related sales order id when customer risk is used in an order decision

## Approval Requirements

- Customer contact, credit changes, or customer-facing communication require human approval before execution.
- The planner may recommend follow-up, but must not send customer messages.

## Refusal and Escalation Conditions

- Refuse requests for confidential or unavailable customer data.
- Escalate when contact details are incomplete and the user asks for an action dependent on those details.

## Examples

- "Check risk for this customer order" -> include rating and missing profile fields in order-risk explanation.
- "Show customer email if not in the tools" -> refuse unavailable data and recommend supported lookup.
