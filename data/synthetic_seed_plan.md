# Synthetic Seed Plan

Sprint 1 uses a small, clearly fake dataset to support demo scenarios and tests.

## Principles

- Use demo ids such as `cust_demo_001` and `prod_demo_001`.
- Avoid real customer names, real suppliers, real pricing, real TAM data, and private business details.
- Keep enough rows to test stock fulfillment, procurement, finance rejection, logistics receipt, and invoice draft follow-up.

## Planned Records

- Three customers: one low-risk, one procurement-ready, one over credit exposure.
- Three products: one in stock, one short-stock item, one high-margin item.
- Three inventory records across demo warehouses.
- Three suppliers with synthetic lead times and purchase options.
- Five customer order requests matching golden cases.
- Finance exposure rows for accepted, conditional, and rejected decisions.
- Logistics events for inbound receipt and delivery confirmation.
