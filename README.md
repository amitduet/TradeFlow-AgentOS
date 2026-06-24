# TradeFlow AgentOS

TradeFlow AgentOS is a Kaggle AI Agents capstone project for the Agents for Business track. It models a multi-agent trading business control tower that evaluates customer order requests and coordinates Sales, CRM, Inventory, Finance, Purchase, and Logistics agents from order feasibility through delivery confirmation, invoice draft, and receivable follow-up.

This Sprint 1 foundation is intentionally minimal. It does not connect to Odoo, production systems, real customer data, real transaction APIs, or real LLM calls. Every business action is synthetic, read-only, or draft-only, with human approval required before any purchase order, invoice, stock update, or customer message could become real.

Sprint 2 adds a deterministic synthetic dataset and read-only tool layer under the same safety model. Sprint 3 adds the first agent-facing workflow orchestrator and approval gate on top of those tools. Sprint 4 adds a constrained planner facade that can interpret supported order-risk requests, select only an approved workflow, execute deterministic tools through the existing orchestrator, and produce cited, tool-grounded responses. Sprint 5 adds planner golden evals, structured traces, version metadata, and audit records for planner decisions. Sprint 6 adds business-readable domain runbooks, reusable skill files, a skill catalog, deterministic skill trigger evals, and loader helpers. Sprint 7 adds an opt-in real LLM provider behind the planner abstraction, with strict JSON validation and deterministic fallback. Sprint 8 adds an opt-in provider smoke-eval harness for local or staging checks. Sprint 9 adds a unified local and CI quality gate for tests, evals, provider-smoke skip tracking, and sanitized JSON reports. Sprint 10 adds timestamped quality gate history, trend summaries, and release evidence packs. Tests and CI still do not require live external LLM credentials.

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

## Quality Gate

Sprint 10 provides one local and CI-ready command for the required agent behavior checks:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py
```

The quality gate runs the pytest suite, planner evals, skill evals, and LLM provider smoke evals. It writes sanitized JSON reports under `artifacts/quality_gate/`, which is ignored by Git. Each normal run also writes timestamped history under `artifacts/quality_gate/history/`. Missing live provider credentials are recorded as a clean provider-smoke skip by default.

Write a report to a stable path:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

Skip the timestamped history write for a one-off run:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json --no-history
```

Summarize recent quality trends:

```bash
.venv/bin/python scripts/summarize_quality_history.py \
  --history-dir artifacts/quality_gate/history \
  --markdown-out artifacts/quality_gate/trend.md
```

Build a release evidence pack for sprint review or capstone submission readiness:

```bash
.venv/bin/python scripts/build_release_evidence_pack.py \
  --quality-report artifacts/quality_gate/latest.json \
  --history-dir artifacts/quality_gate/history \
  --out-dir artifacts/release_evidence/latest \
  --release-name "Sprint 010"
```

Require live provider smoke only in a configured local or staging environment:

```bash
TRADEFLOW_LLM_SMOKE_ENABLED=true \
TRADEFLOW_LLM_PROVIDER=<provider> \
TRADEFLOW_LLM_MODEL=<model> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
.venv/bin/python scripts/run_agent_quality_gate.py --require-live-provider
```

Useful options:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py --quiet
.venv/bin/python scripts/run_agent_quality_gate.py --stop-on-failure
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

## Sprint 7 Real LLM Provider Integration

Sprint 7 keeps the deterministic planner as the default while adding a real provider adapter in `app/agents/llm_provider.py`. Provider selection is environment-driven:

```bash
TRADEFLOW_PLANNER_PROVIDER=deterministic  # deterministic|mock|llm
TRADEFLOW_LLM_PROVIDER=openai             # openai|gemini|custom
TRADEFLOW_LLM_MODEL=
TRADEFLOW_LLM_API_KEY=
TRADEFLOW_LLM_BASE_URL=
TRADEFLOW_LLM_TIMEOUT_SECONDS=30
TRADEFLOW_LLM_SMOKE_ENABLED=false
TRADEFLOW_LLM_SMOKE_MAX_CASES=
```

Run deterministic planner mode:

```bash
python scripts/run_planner.py "Analyze sales order SO-1005" --provider deterministic --show-trace
```

Run real LLM mode only with local credentials:

```bash
TRADEFLOW_PLANNER_PROVIDER=llm \
TRADEFLOW_LLM_PROVIDER=openai \
TRADEFLOW_LLM_MODEL=<model-name> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
python scripts/run_planner.py "Analyze sales order SO-1005" --show-trace
```

The LLM receives the user request, allowed planner routes, allowed recommendation labels, approval constraints, strict output schema, and only the deterministically matched skill plus compact related runbook snippets. It must return strict JSON. Unknown fields, invalid enum values, unsupported routes, approval-bypass terms, tool execution claims, and evidence references outside the prompt context are rejected.

If the LLM fails, times out, returns malformed JSON, or violates planner contracts, the planner falls back to the deterministic provider. `PlannerTrace`, `PlannerRunMetadata`, CLI output, and audit records expose `provider_requested`, `provider_used`, `fallback_used`, `fallback_reason`, `llm_response_valid`, and `llm_validation_errors`.

Provider smoke evals skip by default and make no live provider call:

```bash
python scripts/run_llm_provider_smoke.py
```

Run deterministic fake-provider smoke for local harness validation:

```bash
python scripts/run_llm_provider_smoke.py --fake-provider success
python scripts/run_llm_provider_smoke.py --fake-provider invalid-json --max-cases 1
```

Run live provider smoke only with local or staging credentials and explicit opt-in:

```bash
TRADEFLOW_LLM_SMOKE_ENABLED=true \
TRADEFLOW_LLM_PROVIDER=openai \
TRADEFLOW_LLM_MODEL=<model-name> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
python scripts/run_llm_provider_smoke.py --live --write-report
```

You can also pass non-secret provider settings with `--provider`, `--model`, `--base-url`, and `--timeout-seconds`; keep API keys in environment variables, not CLI history.

Smoke reports are written under `artifacts/provider_smoke/` when requested. That path is ignored by Git, and reports redact API keys, auth headers, token-like values, and provider exception text before writing. A skipped smoke run exits zero; a configured live run exits non-zero only if a smoke case fails.

The smoke script runs business-domain planner cases and never executes business actions directly. Approval gates remain authoritative; the LLM can recommend review, escalation, draft preparation, or requiring approval, but cannot approve, execute, bypass, modify credit or supplier terms, execute payment, or update inventory.

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

## Sprint 7 Status

Sprint 7 integrates a real LLM provider behind the constrained planner abstraction without changing the default test path. It adds provider selection, an OpenAI-compatible/Gemini/custom HTTP adapter, strict planner-output schema validation, deterministic fallback, provider metadata in traces and audits, CLI provider reporting, mocked provider tests, a manual smoke script, and setup documentation. Known limitations: the live provider path is intentionally minimal, does not stream responses, and only supports planner routing output; workflow execution and all business evidence remain deterministic and approval-gated. A recommended next sprint is to add provider-specific live smoke evals in a secrets-enabled local or staging environment while keeping CI deterministic.

## Sprint 8 Status

Sprint 8 adds a secrets-aware provider smoke-eval harness without changing deterministic defaults. It adds versioned smoke cases, opt-in live execution, deterministic fake-provider modes, sanitized JSON reports under ignored local artifacts, redaction helpers, and pytest coverage for skip behavior, fallback reporting, timeout/schema/unsafe responses, and secret leakage prevention. Live smoke remains manual or staging-only and is not required for CI.

## Sprint 9 Status

Sprint 9 adds a unified quality gate runner and CI workflow. The gate aggregates pytest, planner evals, skill evals, and provider smoke into one pass/fail/skip report under `artifacts/quality_gate/`, redacts secret-like values with the shared redaction helper, treats missing live provider credentials as a clean skip by default, and can fail on skipped live smoke with `--require-live-provider`.

## Sprint 10 Status

Sprint 10 turns the quality gate into an auditable release-quality system. It adds timestamped history reports with git/runtime metadata, trend summaries across previous runs, release evidence JSON and Markdown packs, CI artifact upload, and focused tests for history, trends, redaction, provider-smoke skip semantics, and evidence generation. Generated quality and release artifacts remain ignored under `artifacts/`.
