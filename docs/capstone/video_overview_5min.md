# TradeFlow AgentOS Five-Minute Video Overview

## A. Executive Summary

TradeFlow AgentOS demonstrates an agentic order-risk review workflow for a trading business. The problem is cross-functional order judgment: teams need to check customer risk, available inventory, procurement dependencies, logistics status, margin, approval needs, and audit evidence before taking action.

Target users are operations managers, finance or credit reviewers, procurement and logistics coordinators, and Kaggle judges evaluating an Agents for Business capstone.

The business value is faster, safer review of order decisions. The project produces grounded recommendations, visible approval boundaries, audit records, and reproducible evidence without using production data or live services by default.

This is agentic because it uses a constrained planner, approved workflows, domain skills, deterministic tools, specialist agent contracts, guardrails, human approval, and evals. It is not just a basic rules engine: the planner interprets supported business requests, selects an allowlisted workflow, executes tool-grounded steps, cites evidence, records traces, and refuses unsupported or unsafe requests.

## B. Architecture Overview

High-level architecture:

1. Synthetic data and deterministic tools provide local business facts.
2. Domain runbooks and skills describe reusable business capabilities.
3. A constrained planner selects only approved workflows.
4. The order-risk orchestrator executes deterministic tool calls.
5. Guardrails, approval workflow, planner audit, and evidence refs surround the recommendation.
6. CLI and local UI adapters expose the same default deterministic demo path.
7. Evals and the quality gate verify planner behavior, skills, security, approval enforcement, readiness, and submission packaging.

Main components:

- `README.md`: judge quickstart and deterministic review path.
- `examples/demo/`: low, medium, and high risk scenario JSON plus sanitized demo business data.
- `app/agents/demo_agent.py`: thin judge-facing adapter over the existing planner/workflow.
- `app/agents/llm_planner.py`: constrained planner facade with deterministic default and optional LLM path.
- `app/agents/order_risk_orchestrator.py`: deterministic order-risk workflow and tool trace.
- `app/agents/approval_gate.py`: file-backed pending approval requests.
- `app/agents/security_policy.py` and `app/agents/secure_workflow.py`: policy checks and secure workflow enforcement.
- `domain/runbooks/` and `skills/`: business-readable runbooks and skill metadata.
- `evals/`, `tests/`, and `scripts/run_agent_quality_gate.py`: deterministic evaluation and quality evidence.
- `scripts/run_tradeflow_agent_demo.py`: CLI demo.
- `scripts/run_tradeflow_agent_demo_ui.py`: local standard-library UI.
- `.github/workflows/ci.yml`: CI runs tests, readiness, quality gate, release evidence, and AgentOps artifacts.

Data flow:

1. A scenario JSON provides `case_id`, `user_goal`, `workflow_type`, `sales_order_id`, and optional demo context.
2. The demo adapter validates the scenario with Pydantic.
3. The planner converts the request into an approved `analyze_sales_order_risk` route.
4. The orchestrator loads the synthetic dataset, fetches order/customer/logistics/drop-shipping context, calculates margin, and detects risk.
5. The workflow returns risk level, risk flags, recommended action, tool trace, and pending approval request.
6. The response includes summary, evidence refs, audit events, trace refs, deterministic provider metadata, and sanitized demo context.

Technologies used:

- Python application code with Pydantic models.
- Python standard-library local UI server.
- Pytest for tests.
- JSON eval datasets and local artifact reports.
- GitHub Actions for CI.

Optional LLM/API integration is supported behind `--provider llm` and provider smoke checks, but the default demo path uses the deterministic provider and does not require live credentials.

## C. Feature Walkthrough

Major features:

- Deterministic order-risk analysis for supported sales orders.
- Low, medium, and high risk demo scenarios.
- Tool-grounded recommendations with evidence refs.
- Pending human approval request creation for recommended actions.
- Planner traces and audit events.
- Security policy evals for prompt injection, secrets, unsafe tools, data leakage, approval bypasses, destructive operations, and review-worthy requests.
- Local CLI and browser UI demo surfaces.
- Unified quality gate and submission-package checker.

CLI demo interaction:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/low_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/medium_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
```

Local UI demo interaction:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py
```

Open `http://127.0.0.1:8765`, choose a scenario, and run the agent review. The UI calls `/api/scenarios`, `/api/scenario`, and `/api/demo`.

Scenario behavior verified on July 1, 2026:

- Low risk: `SO-1001`, `risk_level: low`, action `monitor_only`, no risk factors.
- Medium risk: `SO-1006`, `risk_level: medium`, action `contact_supplier`, risk factor `delayed_logistics_event`.
- High risk: `SO-1005`, `risk_level: high`, action `create_purchase_order`, risk factor `missing_linked_po_for_drop_shipping`.

Approval behavior:

All three current scenario outputs create a pending approval request for the recommended action. For the high-risk scenario, the purchase-order action remains a draft-style recommendation until human approval.

## D. Code Highlights

Important design decisions:

- Keep the default judge path deterministic, local, synthetic, and API-key-free.
- Keep the demo adapter thin so it reuses the planner and workflow instead of duplicating business logic.
- Allow only approved workflows from the constrained planner.
- Preserve evidence, trace refs, approval state, and audit events in the response.
- Treat live LLM provider smoke as optional and opt-in.

Folder structure:

- `app/agents/`: planner, orchestrator-facing agents, security, approval, audit, provider integration, demo adapter.
- `app/tools/`: deterministic business tools.
- `app/schemas/`: typed contracts and schemas.
- `agents/agent_cards/`: specialist business role descriptions.
- `domain/runbooks/`: business rules and operating runbooks.
- `skills/`: reusable skill definitions.
- `evals/`: golden cases for planner, skills, security, approval, and provider smoke.
- `tests/`: pytest coverage for workflows, contracts, security, demo, readiness, and submission checks.
- `docs/capstone/`: Kaggle writeup, readiness docs, media planning, and this video package.

Testing and quality strategy:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_guardrail_approval_evals.py
.venv/bin/python scripts/check_submission_package.py
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

Verified status on July 1, 2026:

- Planner evals: 10/10 passed.
- Skill evals: 18/18 passed.
- Security evals: 21/21 passed.
- Approval workflow evals: 3/3 passed.
- Submission package: 76/76 checks passed.
- Unified quality gate: 7 passed, 0 failed, 1 skipped.
- Provider smoke: skipped by default because live credentials are not required for review.

Note: during verification, parallel demo runs corrupted an ignored local runtime file under `artifacts/demo_runtime/`. Removing `artifacts/demo_runtime/approval_requests.json` and rerunning sequentially restored the UI endpoint test and the full quality gate. This is a local artifact hygiene issue, not a checked-in source failure.

## E. Demo Script

Use `docs/capstone/video_script_5min.md` as the final recording script. The narration is designed for five minutes or less and uses only verified commands and repository behavior.

## F. Storyboard

| Time | Screen to show | Narration | Key message |
|---|---|---|---|
| 0:00-0:25 | `README.md` For Kaggle Judges | Introduce TradeFlow AgentOS and the order-risk problem. | Agents for Business fit. |
| 0:25-0:55 | Repo tree, `docs/capstone/README.md`, `agents/agent_cards/` | Show specialist roles, runbooks, skills, specs, and deterministic default path. | Agentic engineering structure. |
| 0:55-1:35 | `app/agents/demo_agent.py`, `app/agents/llm_planner.py`, `app/agents/order_risk_orchestrator.py` | Explain planner, approved workflow, deterministic tools, approval, and audit. | Architecture is inspectable. |
| 1:35-2:35 | Terminal: low, medium, high CLI demos | Show risk levels, actions, evidence refs, and approval state. | Live behavior is grounded and local. |
| 2:35-3:05 | Browser UI at `http://127.0.0.1:8765` | Run high-risk review in the local UI. | Same workflow powers CLI and UI. |
| 3:05-4:10 | Evals and quality gate output | Show planner, skill, security, approval, submission, and gate results. | Reproducible evidence. |
| 4:10-4:40 | `docs/capstone/kaggle_writeup.md`, `CAPSTONE_READINESS.md` | Summarize readiness, limitations, and optional LLM mode. | Clear scope and honesty. |
| 4:40-5:00 | README quickstart | Close for Kaggle judges. | Structured, testable, guardrailed capstone. |

## G. Recording Checklist

Open before recording:

- `README.md`
- `docs/capstone/README.md`
- `docs/capstone/kaggle_writeup.md`
- `docs/capstone/CAPSTONE_READINESS.md`
- `docs/capstone/video_script_5min.md`
- `app/agents/demo_agent.py`
- `app/agents/llm_planner.py`
- `app/agents/order_risk_orchestrator.py`
- `app/agents/approval_gate.py`
- `evals/`
- `tests/`

Prepare terminal:

```bash
source .venv/bin/activate
rm -f artifacts/demo_runtime/approval_requests.json artifacts/demo_runtime/planner_audit.jsonl
```

Demo commands:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/low_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/medium_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
.venv/bin/python scripts/check_submission_package.py
```

Optional API calls while UI server is running:

```bash
curl -s http://127.0.0.1:8765/api/scenarios
curl -s -X POST http://127.0.0.1:8765/api/demo \
  -H 'Content-Type: application/json' \
  --data-binary @examples/demo/high_risk_order.json
```

Data to prepare:

- `examples/demo/low_risk_order.json`
- `examples/demo/medium_risk_order.json`
- `examples/demo/high_risk_order.json`
- `examples/demo/data/demo_customers.json`
- `examples/demo/data/demo_products.json`
- `examples/demo/data/demo_inventory.json`
- `examples/demo/data/demo_finance_opening_balance.json`

Browser pages:

- `http://127.0.0.1:8765`
- Optional generated dashboard after building artifacts: `artifacts/capstone/agentops_dashboard.html`

Common recording mistakes to avoid:

- Do not use `--scenario`; the actual CLI requires `--input`.
- Do not claim the default path requires live LLM credentials.
- Do not claim the system writes to production ERP, CRM, banking, email, inventory, or logistics systems.
- Do not claim low-risk orders skip approval; current outputs still create pending approval requests.
- Do not run low, medium, and high demo commands in parallel against the same default runtime approval file.
- Do not spend more than 20 seconds scrolling raw JSON.

## H. FAQs

**Is this using AI APIs?**

The default demo does not use live AI APIs. The planner default is deterministic. Optional LLM/provider integration exists behind explicit configuration and provider smoke checks.

**Does it work without live LLM credentials?**

Yes. The judge path, CLI demo, local UI demo, tests, evals, and quality gate run without live provider credentials. Provider smoke skips cleanly by default.

**What makes it agentic?**

It combines planner routing, approved workflows, specialist agent contracts, skills, tool execution, guardrails, approvals, audit traces, and evals around a business decision workflow.

**How are unsafe actions controlled?**

Security policy and secure workflow code evaluate prompt injection, secrets, destructive actions, unsafe tool requests, approval bypasses, and data leakage. Sensitive actions remain blocked or routed to review.

**How are evals and quality gates used?**

Planner, skill, security, approval, readiness, submission, and pytest checks run individually or through `scripts/run_agent_quality_gate.py`.

**What is deterministic vs LLM-assisted?**

Deterministic is the default provider and uses local tools and runbooks. LLM-assisted mode is optional, opt-in, validated, and separate from the normal judge path.

**What is production-ready vs demo-only?**

The architecture, contracts, eval discipline, and safety boundaries are the main production-style patterns. The current system is capstone-grade: synthetic data, local approval storage, static dashboard artifacts, and no production integrations.

**What would be next for real deployment?**

Durable approval storage, role-based access control, production observability, ERP/CRM/logistics integration, richer data quality controls, staged provider validation, and live incident-ready monitoring.

**How does this demonstrate Kaggle course concepts?**

It demonstrates agent planning, tool use, grounding, guardrails, human-in-the-loop approval, evals, auditability, and an Agents for Business workflow that can be reproduced locally.
