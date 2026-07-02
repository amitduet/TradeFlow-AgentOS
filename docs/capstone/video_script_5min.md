# TradeFlow AgentOS Five-Minute Video Script

Target: five minutes or less for Kaggle judges and a technical audience.

## 0:00-0:30 Opening Hook

Screen direction: Show `README.md`, the project title, and the "For Kaggle Judges" section.

Narration: "Trading teams rarely make order decisions from one screen. They check customer risk, inventory, procurement dependencies, logistics, margin, and approvals. TradeFlow AgentOS is my Agents for Business capstone: a local, deterministic business-agent workflow that reviews order risk while keeping evidence, guardrails, approvals, and audit traces visible."

## 0:30-1:15 Scope and Architecture

Screen direction: Show `docs/capstone/README.md`, `examples/demo/`, `app/agents/demo_agent.py`, `app/agents/llm_planner.py`, `app/agents/order_risk_orchestrator.py`, `domain/runbooks/`, `skills/`, and `specs/AGENT_CONTRACTS.md`.

Narration: "This is a capstone-grade prototype, not a production ERP integration. The judge path uses synthetic data, deterministic tools, and local artifacts. A thin demo adapter validates scenario JSON, a constrained planner selects approved workflows, and the order-risk orchestrator runs deterministic tools for sales order, customer, drop-shipping, logistics, margin, and risk detection. Optional LLM provider mode exists separately, but it is not required for this demo."

## 1:15-2:15 CLI Demo: Low, Medium, High Risk

Screen direction: Run each command and zoom only on `risk_level`, `recommended_action`, `approval_required`, `risk_factors`, `evidence_refs`, and `trace_refs`.

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/low_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/medium_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
```

Narration: "Here are the three committed demo cases. The low-risk order returns `monitor_only` with no risk factors. The medium-risk order flags a delayed logistics event and recommends `contact_supplier`. The high-risk order flags a missing linked purchase order for drop-shipping and recommends `create_purchase_order`. In the current workflow, every recommended action stays behind a pending human approval request, and the response includes evidence references, audit events, reason codes, and deterministic provider metadata."

## 2:15-3:05 Local UI Demo

Screen direction: Start the UI, open the browser, select the high-risk scenario, and run the review.

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py
```

Open `http://127.0.0.1:8765`.

Narration: "The same adapter powers this local UI, built with the Python standard library. It lists the committed scenarios, posts the selected JSON to `/api/demo`, and displays the risk, approval state, recommended action, trace, and full JSON output. This is still local, synthetic, and deterministic."

## 3:05-4:05 Evals, Guardrails, and Quality Gate

Screen direction: Show the eval folders, then run the commands or show verified recent output.

```bash
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_guardrail_approval_evals.py
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

Narration: "The project is built for reproducible review. Planner evals check routing, action selection, approval decisions, refusals, risk level, and reason codes. Skill evals check trigger behavior. Security evals cover prompt injection, secrets, unsafe tools, approval bypasses, data leakage, and destructive operations. Approval workflow evals verify allowed, blocked, and review-required paths. The unified quality gate runs tests, evals, readiness checks, submission checks, and provider smoke."

## 4:05-4:40 Submission Readiness

Screen direction: Show `docs/capstone/kaggle_writeup.md`, `docs/capstone/CAPSTONE_READINESS.md`, `docs/capstone/media_gallery_checklist.md`, and `scripts/check_submission_package.py`.

Narration: "The capstone package includes a Kaggle writeup, readiness summary, media checklist, public repository checklist, demo scripts, and a submission-package checker. The current verified quality gate is seven passed, zero failed, and one skipped provider-smoke check. Provider smoke skips by default unless live credentials are explicitly configured."

## 4:40-5:00 Closing

Screen direction: Return to the README quickstart and keep the final quality-gate summary visible.

Narration: "The goal is not to replace human reviewers. It is to make cross-functional order review faster to inspect, safer to run, and easier to audit. TradeFlow AgentOS is deterministic by default, optional-LLM-ready, and prepared for Agents for Business capstone review."

## Storyboard

| Time | Screen | Narration focus | Key message |
|---|---|---|---|
| 0:00-0:30 | README judge section | Hook and business problem | Agents for Business fit |
| 0:30-1:15 | Capstone docs, planner, orchestrator, runbooks, skills | Scope and architecture | No live credentials required |
| 1:15-2:15 | CLI demos | Low, medium, high scenarios | Grounded recommendations and approval state |
| 2:15-3:05 | Local UI | Same workflow in browser | Runnable judge demo |
| 3:05-4:05 | Eval commands and quality gate | Tests, evals, guardrails | Reproducible evidence |
| 4:05-4:40 | Capstone docs and checker | Submission readiness | Complete review package |
| 4:40-5:00 | README and gate summary | Closing value | Structured, testable, guardrailed |
