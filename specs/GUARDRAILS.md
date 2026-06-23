# Guardrails

## Read-Only and Draft-Only Behavior

- Agents may read synthetic data and create synthetic recommendations.
- Purchase orders must remain purchase order drafts.
- Invoices must remain invoice drafts.
- Inventory updates must be simulated status updates.
- Customer communications must remain message drafts.

## Human Approval Checkpoints

Human approval is required before any real-world equivalent of:

- Purchase order release.
- Supplier commitment.
- Inventory stock posting.
- Customer delivery commitment.
- Invoice posting.
- Customer email sending.
- Credit exception approval.

## Data Safety

- Do not use real customer data.
- Do not use real TAM data or private market sizing data.
- Do not store private business details in prompt files, fixtures, docs, or synthetic data.
- Synthetic examples must use clearly fake ids and demo names.

## External System Safety

- Do not call production APIs.
- Do not connect to real Odoo, ERP, CRM, banking, carrier, email, or accounting systems.
- Do not store API keys or secrets in the repository.
- `.env.example` may document variable names only.

## Agent Behavior

- Agents must explain decisions with evidence from synthetic records.
- Agents must surface uncertainty and use needs_human_review when required.
- Agents must not override Finance decisions.
- Agents must not create invoice drafts before delivery confirmation.
- Agents must not create PO drafts before Finance consent.
