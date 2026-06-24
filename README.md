# TradeFlow AgentOS

TradeFlow AgentOS is a Kaggle AI Agents capstone project for the Agents for Business track. It models a multi-agent trading business control tower that evaluates customer order requests and coordinates Sales, CRM, Inventory, Finance, Purchase, and Logistics agents from order feasibility through delivery confirmation, invoice draft, and receivable follow-up.

This Sprint 1 foundation is intentionally minimal. It does not connect to Odoo, production systems, real customer data, real transaction APIs, or real LLM calls. Every business action is synthetic, read-only, or draft-only, with human approval required before any purchase order, invoice, stock update, or customer message could become real.

Sprint 2 adds a deterministic synthetic dataset and read-only tool layer under the same safety model. Sprint 3 adds the first agent-facing workflow orchestrator and approval gate on top of those tools. It still does not build or call an unconstrained LLM agent. Future agents will call typed, validated Python tools that read local synthetic JSON only.

## Business Problem

Trading companies often need to answer order feasibility questions quickly while balancing customer history, available stock, procurement lead time, margin, credit exposure, logistics risk, and working-capital constraints. TradeFlow AgentOS demonstrates how specialized agents can coordinate those checks using explicit contracts, event messages, guardrails, and evaluation cases.

## Agent Architecture

- Orchestrator Agent classifies the user question and selects the workflow.
- Sales Agent starts the customer order request workflow and coordinates customer-facing drafts.
- CRM Agent checks synthetic customer profile, opportunity, and payment behavior.
- Inventory Agent checks stock availability, reservation risk, and simulated stock status.
- Finance Agent checks margin, payment terms, credit exposure, and finance consent.
- Purchase Agent recommends supplier options and prepares purchase order drafts.
- Logistics Agent tracks inbound shipment, goods receipt, outbound delivery, and notifications.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Sprint 2 Synthetic Data and Tools

The canonical Sprint 2 dataset is stored at `data/synthetic/tradeflow_seed.json`. It contains synthetic customers, suppliers, products, sales orders, purchase order drafts, logistics events, invoice summaries, and payment summaries. The data is generated from a fixed seed and validated before writing, so repeated runs with the same seed produce the same records.

Generate or refresh the dataset:

```bash
python scripts/generate_synthetic_data.py
python scripts/generate_synthetic_data.py --seed 20240623 --output data/synthetic/tradeflow_seed.json
```

Run deterministic tool evals:

```bash
python scripts/run_tool_evals.py
```

Run tests:

```bash
pytest
```

The deterministic tools live in `app/tools/tradeflow_tools.py` and include customer/supplier profile lookup, sales order listing, drop-shipping chain lookup, logistics event listing, margin calculation, and rule-based risk detection. These tools do not call network services, production systems, or LLMs.

## Sprint 3 Workflow Orchestrator and Approval Gates

Sprint 3 introduces `app/agents/order_risk_orchestrator.py`, a controlled execution layer for the "Analyze Sales Order Risk and Prepare Action Recommendation" workflow. The workflow receives a `sales_order_id`, calls only approved deterministic Sprint 2 tools, captures a tool-call trace, produces a typed recommendation, and creates a pending approval request before any business action could happen.

Run the workflow:

```bash
python scripts/run_order_risk_workflow.py --sales-order-id SO-1005
```

Run workflow evals:

```bash
python scripts/run_workflow_evals.py
```

Approval requests are written to `data/runtime/approval_requests.json`, which is local runtime state and ignored by Git. The source synthetic dataset remains read-only. Approval status can change only through explicit `approve_request(...)` or `reject_request(...)` calls in `app/agents/approval_gate.py`.

No LLM is used in Sprint 3. The goal is to prove the safe substrate first: deterministic tools, typed workflow outputs, traceability, approval gates, and repeatable evals. This prepares the future LLM layer to plan over known tools without inventing facts or bypassing human review.

## Demo Scenarios

- Customer order can be fulfilled from available stock.
- Customer order requires procurement and finance consent.
- Finance rejects an order due to credit exposure.
- Logistics confirms goods receipt and notifies Inventory and Sales.
- Delivery confirmation triggers invoice draft and finance receivable follow-up.

## Sprint 1 Status

Sprint 1 establishes the repository structure, source-of-truth specs, agent cards, event contracts, synthetic data model, evaluation plan, placeholder tools, placeholder agents, and basic tests. Sprint 2 can build the first executable workflow on top of these contracts.

## Sprint 2 Status

Sprint 2 establishes the synthetic business-data foundation and deterministic tool layer for future agent workflows. It adds typed Pydantic dataset contracts, a reproducible dataset generator, canonical JSON seed data, deterministic tool eval cases, and pytest coverage for dataset integrity, drop-shipping chains, logistics links, margin calculation, and risk detection.

## Sprint 3 Status

Sprint 3 establishes the first controlled agent workflow without an unconstrained LLM. It adds typed workflow contracts, the order-risk orchestrator, trace capture, deterministic recommendation rules, a file-backed approval gate, workflow eval cases, CLI runners, and pytest coverage.
