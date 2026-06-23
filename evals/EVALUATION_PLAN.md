# Evaluation Plan

## Golden Dataset Tests

- Validate that five canonical synthetic cases map to the expected workflow.
- Confirm expected Finance decisions for approved, approved_with_conditions, rejected, and needs_human_review cases.
- Confirm procurement cases include Purchase Agent handoff.

## Workflow Tests

- Stock fulfillment starts Sales, CRM, Inventory, and Finance checks without procurement.
- Procurement workflow starts Purchase only after shortfall is identified.
- Goods receipt notifies Purchase, Inventory, and Sales.
- Delivery confirmation enables invoice draft and receivable follow-up.

## Tool-Call Tests

- CRM tools must return synthetic customer summaries only.
- Inventory tools must return availability and simulated status only.
- Finance tools must return one of the allowed decision statuses.
- Purchase tools must create drafts only after Finance consent.
- Logistics tools must create synthetic logistics events only.

## Guardrail Tests

- No real external production API calls are allowed.
- No secrets, real customer data, real TAM data, or private business details are stored.
- Invoice draft creation is blocked before delivery confirmation.
- PO draft creation is blocked before approved or approved_with_conditions Finance consent.
- Customer email output remains draft-only.
