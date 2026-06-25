# TradeFlow AgentOS

## Subtitle

A capstone-grade business agent prototype for safe, auditable trading operations.

## Track Recommendation: Agents for Business

TradeFlow AgentOS is designed for the Agents for Business track. It focuses on a realistic operating workflow: deciding whether a trading company should proceed with a customer order when credit, inventory, procurement, logistics, margin, approval, and audit concerns all matter at once.

## Problem

Trading teams often need fast answers to questions such as: Can this order be fulfilled? Is the customer risky? Do we need a purchase order? Is margin acceptable? Should finance approve the action before a message, invoice draft, or procurement step is prepared?

Those decisions cross team boundaries. A useful business agent cannot simply chat about the request. It needs to gather facts from approved tools, stay inside known workflows, cite evidence, avoid unsafe actions, and make the human approval boundary explicit.

## Solution

TradeFlow AgentOS is a prototype-grade / capstone-grade multi-agent control tower for order-risk review. It uses synthetic data and deterministic tools to model how specialist agents can coordinate safely:

- Sales frames the order request.
- CRM checks customer and payment context.
- Inventory checks stock and reservation risk.
- Finance checks margin, terms, and credit exposure.
- Purchase prepares supplier and purchase-order recommendations.
- Logistics checks delivery and shipment risk.
- The orchestrator and planner keep execution inside approved routes.

The project does not claim production readiness. It demonstrates an engineering pattern for business agents that can be inspected and reproduced without private data, network calls, or live credentials.

## Agent Architecture

The architecture is intentionally layered:

1. Synthetic business data and deterministic read-only tools.
2. Domain runbooks and skill definitions.
3. Planner contracts and controlled workflows.
4. Security policy, approval workflow, audit helpers, and evidence generation.

The default planner is deterministic. It extracts supported sales order identifiers, selects an allowlisted workflow, executes deterministic tools, and returns a structured recommendation with evidence references. An optional provider adapter exists behind strict validation, but normal review does not require a live model key.

## AgentOps Readiness

The project includes a reviewer-friendly AgentOps layer. The evidence index scans local generated reports for the latest quality gate, security evals, approval or guardrail evals, release evidence, skipped checks, warnings, and verification commands. The static dashboard turns that index into dependency-free local HTML under an ignored artifact path.

This means judges can inspect both the system behavior and the evidence trail without relying on an external monitoring service.

## Safety, Guardrails, Human Approval, and Auditability

The security policy covers prompt injection, secrets exfiltration, approval bypass attempts, unsafe tool use, data leakage, destructive operations, and review-worthy sensitive requests. Some requests are blocked and others are routed to review.

Sensitive business actions remain draft-only or pending. The system can recommend monitoring, escalation, preparation, or review, but it does not execute payments, approve orders, update inventory, or bypass human approval. Approval workflow evals verify that review-worthy actions create pending approval requests and that audit events record policy decisions.

## Evaluation and Quality Gates

The unified quality gate runs:

- Pytest
- Planner evals
- Skill trigger evals
- Security evals
- Approval workflow evals
- Capstone readiness checks
- Submission package checks
- Provider smoke checks

Provider smoke skips cleanly by default because live provider tests require explicit opt-in and local credentials. This keeps the default review path deterministic, offline-safe, and secrets-safe.

The current release candidate also includes release evidence generation and a submission-package checker to validate final docs, writeup length, video script, media checklist, capstone index links, and absence of obvious placeholder markers.

## What Makes It Useful for Business

TradeFlow AgentOS shows how a business agent can reduce coordination effort while preserving control. It gathers relevant facts, classifies order risk, recommends next steps, records approval boundaries, and provides evidence that explains the recommendation.

For a reviewer, the useful part is not only the workflow output. It is the combination of agent contracts, deterministic evals, security checks, auditability, and reproducible evidence.

## Limitations and Future Work

TradeFlow AgentOS uses synthetic data and local artifacts. It is not connected to production ERP, CRM, banking, email, inventory, or logistics systems. The approval store is local, the dashboard is static, and live provider smoke is opt-in.

Future work would include richer data, a durable approval store, role-based access control, production observability, deeper policy coverage, staging integrations, and carefully controlled live-provider evaluation.

## How to Run / Project Link

From a clean clone:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_agent_quality_gate.py
.venv/bin/python scripts/build_agentops_evidence_index.py
.venv/bin/python scripts/build_agentops_dashboard.py
```

Project repository: `amitduet/TradeFlow-AgentOS`.
