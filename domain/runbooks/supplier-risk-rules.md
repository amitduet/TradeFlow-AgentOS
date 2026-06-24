# Supplier Risk Rules

## Purpose

Define supplier signals that affect procurement confidence and purchase order recommendations.

## When to Use

Use this runbook when a request involves supplier readiness, purchase order recommendation, drop-shipping, supplier contact, lead-time, or supplier availability.

## Inputs Required

- Supplier id and supplier name when available
- Supplier contact person data: name, email, phone, and designation when available
- Product and SKU relationship
- Lead-time and availability context when available
- Related sales order and purchase order draft links

## Risk Indicators

- Missing supplier contact person increases risk.
- Incomplete supplier contact person data increases risk.
- Supplier lead-time uncertainty increases risk.
- Supplier availability uncertainty increases risk.
- Missing product-to-supplier mapping should trigger escalation for procurement requests.

## Decision Rules

- Supplier uncertainty should affect purchase-order recommendation confidence.
- Supplier-related missing data should trigger escalation when procurement action is requested.
- Do not fabricate supplier availability, terms, or contacts.
- Preserve sales order to purchase order draft linkage for drop-shipping.

## Required Evidence

- Supplier id and linked product or order context
- Supplier contact fields available in the dataset
- Lead-time or availability signals when available
- Related purchase order draft ids
- Reason codes for missing supplier context

## Approval Requirements

- Supplier contact and purchase order actions require human approval before execution.
- The planner may recommend contacting a supplier, but must not send messages or create procurement commitments.

## Refusal and Escalation Conditions

- Escalate missing supplier or product information for procurement requests.
- Refuse unsupported supplier record creation or data invention.
- Refuse approval-bypass procurement wording.

## Examples

- "Prepare PO recommendation for this order" -> check supplier evidence and approval requirement.
- "Create a supplier contact record" -> not a Sprint 006 skill trigger; refuse or route outside supported workflow.
