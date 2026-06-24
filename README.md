# TradeFlow AgentOS

TradeFlow AgentOS is a Kaggle AI Agents capstone project for the Agents for Business track. It models a multi-agent trading business control tower that evaluates customer order requests and coordinates Sales, CRM, Inventory, Finance, Purchase, and Logistics agents from order feasibility through delivery confirmation, invoice draft, and receivable follow-up.

This Sprint 1 foundation is intentionally minimal. It does not connect to Odoo, production systems, real customer data, real transaction APIs, or real LLM calls. Every business action is synthetic, read-only, or draft-only, with human approval required before any purchase order, invoice, stock update, or customer message could become real.

Sprint 2 adds a deterministic synthetic dataset and read-only tool layer under the same safety model. Sprint 3 adds the first agent-facing workflow orchestrator and approval gate on top of those tools. Sprint 4 adds a constrained planner facade that can interpret supported order-risk requests, select only an approved workflow, execute deterministic tools through the existing orchestrator, and produce cited, tool-grounded responses. Sprint 5 adds planner golden evals, structured traces, version metadata, and audit records for planner decisions. Sprint 6 adds business-readable domain runbooks, reusable skill files, a skill catalog, deterministic skill trigger evals, and loader helpers. It still does not require a live external LLM.

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

## Sprint 4 Constrained Planner

Sprint 4 introduces `app/agents/llm_planner.py`, `app/agents/planner_contracts.py`, and `app/agents/planner_safety.py`. The default planner mode is rule-based and makes no external LLM call. It extracts a sales order id, selects only the allowlisted `analyze_sales_order_risk` workflow, executes the Sprint 3 orchestrator, and returns a grounded response with evidence citations from workflow, deterministic tool, and approval outputs.

Run the planner:

```bash
python scripts/run_planner.py --request "Analyze sales order SO-1005"
```

The LLM-ready path is isolated behind a `PlannerProvider` abstraction so tests can supply mocked planner decisions without allowing arbitrary tools or bypassing approval gates. If no provider is configured, the project remains fully usable in rule-based mode.

Planner safety checks verify that a sales order id was recognized, the selected workflow is approved, approval is required, the approval request remains pending, cited evidence resolves to deterministic outputs, and the source dataset hash is unchanged.

## Sprint 5 Planner Evals and Observability

Sprint 5 introduces `evals/sprint_005_planner_golden_cases.json`, `scripts/run_planner_evals.py`, and `app/agents/planner_audit.py`. Planner results now include version metadata, a structured `PlannerTrace`, a safety outcome, reason codes, and a business-focused audit record.

Run planner evals:

```bash
python scripts/run_planner_evals.py
```

The golden dataset covers low-, medium-, and high-risk orders, purchase order recommendation, missing or unknown sales order context, ambiguous requests, unsafe approval-bypass attempts, unavailable-data hallucination traps, and unsupported business actions. See `docs/sprints/sprint-005-planner-evals-observability.md` for the dataset format, pass/fail output, trace fields, audit fields, and CLI examples.

## Sprint 6 Business Runbooks and Domain Skills

Sprint 6 makes TradeFlow business knowledge explicit before any real LLM provider is introduced. Business rules live in `domain/runbooks/`, while reusable skill definitions live in `skills/`. Skills describe trigger behavior, required inputs, allowed and disallowed actions, outputs, and safety constraints; they reference runbooks instead of duplicating long business rules.

Run skill evals:

```bash
python scripts/run_skill_evals.py
```

List available domain skills:

```bash
python scripts/list_domain_skills.py
```

The Sprint 6 trigger dataset covers positive and negative cases for order-risk analysis, purchase-order recommendation, and approval-gate handling. The skill helpers in `app/agents/domain_skills.py` are deterministic metadata and phrase-matching utilities, not a runtime LLM skill engine.

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

## Sprint 4 Status

Sprint 4 establishes the first constrained LLM-facing layer without making a live LLM call mandatory. It adds planner contracts, rule-based routing, an LLM provider abstraction for mocked/future planners, grounded response citations, planner safety checks, a future prompt template, CLI runner, and pytest coverage.

## Sprint 5 Status

Sprint 5 establishes planner regression and observability foundations. It adds a versioned planner golden dataset, eval runner with accuracy metrics, structured traces, planner version/prompt/provider metadata, audit records, refusal/escalation behavior for unsafe or ambiguous requests, documentation, and focused pytest coverage.

## Sprint 6 Status

Sprint 6 establishes versioned business domain knowledge for future planner grounding. It adds readable runbooks for order risk, purchase order recommendation, approval gates, customer risk, supplier risk, and logistics risk; focused skill files and a skill catalog; deterministic trigger evals; loader helpers; CLI discoverability; documentation; and pytest coverage. Approval gates remain authoritative, no external APIs are added, and no real LLM provider is integrated.
