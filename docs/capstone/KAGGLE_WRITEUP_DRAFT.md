# TradeFlow AgentOS

## Subtitle

An agentic business control tower for safe, explainable trading workflow automation.

## Selected Track: Agents for Business

TradeFlow AgentOS fits the Agents for Business track because it focuses on a realistic business workflow: evaluating customer order feasibility across sales, credit, inventory, procurement, logistics, approval, and audit concerns.

## Problem

Trading companies often need quick answers to questions such as: Can we fulfill this order? Is the customer risky? Do we need procurement? Is margin acceptable? Should finance approve before anyone sends a customer message or creates a purchase order?

Those decisions cross team boundaries. A simple chatbot can summarize a request, but a business-ready agentic system needs stronger structure. It should use approved tools, cite known facts, respect guardrails, preserve auditability, and make it clear when human approval is required.

## Solution

TradeFlow AgentOS is a capstone-grade prototype of a multi-agent trading operations control tower. It uses synthetic data and deterministic tooling to model how specialized agents can coordinate safely:

- Sales frames the order request.
- CRM checks customer profile and payment behavior.
- Inventory checks stock and reservation risk.
- Finance checks margin and credit exposure.
- Purchase prepares procurement recommendations.
- Logistics checks shipment and delivery risk.
- The orchestrator and planner keep the workflow inside approved routes.

The system does not claim production readiness. It is designed to demonstrate agentic engineering practices that can be verified locally and reviewed by judges without live credentials or private data.

## How the Agent Works

The default planner is deterministic. It extracts supported order identifiers, selects an allowlisted workflow, executes deterministic tools, and returns a structured recommendation with evidence references. An optional LLM provider adapter exists behind strict contracts, but normal tests and CI do not require it.

Every sensitive action remains draft-only or pending. The system can recommend escalation, preparation, monitoring, or review, but it cannot approve orders, execute payments, update inventory, or bypass policy.

## Architecture

The architecture has four layers:

1. Synthetic business data and deterministic tools.
2. Domain runbooks and skill definitions.
3. Planner contracts and orchestrated workflows.
4. Security, approval, audit, and evidence generation.

This layered approach keeps business behavior inspectable. Skills define trigger boundaries. Planner evals test route and action selection. Security evals test unsafe prompts. Approval workflow evals test enforcement and audit events. The quality gate ties the checks together.

## Agentic Engineering Practices

TradeFlow AgentOS emphasizes practices that matter for business agents:

- Explicit planner schemas and route allowlists
- Grounded responses with evidence references
- Deterministic fallbacks when provider output is invalid
- Business runbooks separated from code
- Evaluation datasets for planner, skills, provider smoke, security, and approvals
- Redaction of sensitive strings before writing reports
- No-network, no-secrets CI defaults

## Evaluation and Quality Gates

The unified quality gate runs local tests, planner evals, skill evals, security evals, approval workflow evals, capstone readiness checks, and provider smoke. Provider smoke skips cleanly by default because live provider tests require explicit opt-in and credentials.

Sprint 013 adds an AgentOps evidence index and a static dashboard. These artifacts summarize the latest quality gate, security evals, approval workflow evidence, release evidence, verification commands, known skipped checks, and limitations.

## Security, Guardrails, Approval, and Auditability

The security policy handles prompt injection, secrets exfiltration, data leakage, approval bypasses, unsafe tool use, and destructive requests. Some requests are blocked; some are routed to review. Approval workflow evals verify that review-worthy actions create pending approval requests and that audit events are emitted.

This is intentionally deterministic. The goal is not to outsource safety to a model judge, but to show clear, inspectable guardrails that run the same way on every machine.

## User Value

For a business user, TradeFlow AgentOS shows how an agent could reduce coordination effort while preserving control. It can gather relevant facts, classify risk, recommend next steps, and explain what evidence supports the recommendation. For reviewers, it provides reproducible evidence that the system follows its contracts.

## What I Learned

The project reinforced that agentic systems need more than tool calls. The important work is often in boundaries: what the agent may do, what it must refuse, how it cites evidence, how it asks for approval, and how teams can evaluate behavior before trusting it.

## Limitations and Next Steps

TradeFlow AgentOS is prototype-grade / capstone-grade. It uses synthetic data, local artifacts, and deterministic workflows. Next steps would include a richer dataset, a real approval store, production-grade observability, deeper policy coverage, role-based access control, and carefully staged live provider evaluations.
