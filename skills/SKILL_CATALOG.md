# Skill Catalog

Sprint 006 exposes TradeFlow business knowledge as focused, versioned skills. Skills describe when business knowledge should be used; runbooks hold the reusable business rules.

| Skill name | Purpose | Trigger examples | Non-trigger examples | Related runbooks | Risk level | Current status |
| --- | --- | --- | --- | --- | --- | --- |
| `order-risk-analysis` | Analyze sales order risk and explain reason codes from deterministic evidence. | "Analyze sales order SO-1005"; "Check risk for this customer order"; "Is SO-1005 safe to proceed?" | "Create a supplier contact record"; "Show system health"; "Write a marketing email" | `order-risk-rules.md`, `customer-risk-rules.md`, `logistics-risk-rules.md`, `supplier-risk-rules.md` | Medium to high | Active in Sprint 006 evals |
| `purchase-order-recommendation` | Recommend whether a valid sales order needs a linked purchase order draft without executing procurement. | "Should we create a purchase order for SO-1005?"; "Prepare PO recommendation for this order"; "Does this drop-shipping order need a PO draft?" | "Analyze customer rating only"; "Approve the order directly"; "Summarize logistics events" | `purchase-order-recommendation-rules.md`, `supplier-risk-rules.md`, `approval-gate-rules.md` | High | Active in Sprint 006 evals |
| `approval-gate-handling` | Explain approval requirements and refuse bypass attempts for restricted actions. | "Can we approve this high-risk order?"; "Bypass approval for SO-1005"; "What approval is required before PO creation?" | "List supplier phone numbers"; "Calculate order margin"; "Show customer billing address" | `approval-gate-rules.md`, `order-risk-rules.md`, `purchase-order-recommendation-rules.md` | High | Active in Sprint 006 evals |

## Notes

- Skills are not a real LLM provider and do not execute business actions.
- Skills keep trigger behavior testable before live provider integration.
- Approval-gate behavior remains authoritative and non-optional.
