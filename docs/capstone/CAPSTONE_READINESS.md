# TradeFlow AgentOS Capstone Readiness

## Project Title

TradeFlow AgentOS: Agentic Business Workflow Automation for Trading Operations

## One-Line Value Proposition

TradeFlow AgentOS helps a trading business evaluate order risk, coordinate specialist agents, enforce approval controls, and produce deterministic evidence for review.

## Recommended Kaggle Track

Agents for Business

## Target Users

- Operations managers who need fast order feasibility decisions
- Finance and credit reviewers who need approval evidence
- Procurement and logistics coordinators who need safe draft recommendations
- Capstone judges reviewing agentic engineering quality

## Problem Statement

Trading companies often answer order questions under time pressure while balancing customer credit, stock availability, procurement needs, margin, logistics risk, and approval policy. A useful agentic prototype must coordinate those checks without inventing facts, bypassing approvals, leaking secrets, or depending on live services during evaluation.

## Solution Overview

TradeFlow AgentOS models a business control tower with deterministic tools, specialized agent contracts, runbook-backed skills, a constrained planner, security policy checks, human approval workflow, audit trail helpers, and a unified quality gate. It uses synthetic data only and keeps generated evidence under ignored artifact paths.

Sprint 015 added the runnable judge-facing CLI and local stdlib-only UI demo. Sprint 016 freezes the submission path around that demo, the README judge quickstart, final Kaggle docs, media checklist, capstone index, and submission-package checker without adding production integrations or new agent behavior.

## Architecture Summary

The orchestrator classifies supported requests and routes them to approved workflows. Domain agents represent Sales, CRM, Inventory, Finance, Purchase, and Logistics responsibilities. The planner can run in deterministic mode by default and can use an optional provider adapter only when explicitly configured. Security and approval enforcement sit around workflow execution so unsafe requests are blocked or routed to review.

## Agentic Concepts Demonstrated

- Planner contracts with explicit allowed routes and recommendation labels
- Domain skills backed by business-readable runbooks
- Tool-grounded workflow execution over synthetic data
- Deterministic planner, skill, provider-smoke, security, and approval evals
- Human approval requests before sensitive actions
- Redacted audit and evidence artifacts for reviewer inspection

## Verification Evidence

Primary verification command:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py
```

Additional capstone artifacts:

```bash
.venv/bin/python scripts/build_agentops_evidence_index.py
.venv/bin/python scripts/build_agentops_dashboard.py
.venv/bin/python scripts/check_capstone_readiness.py
```

The quality gate aggregates tests, planner evals, skill evals, security evals, approval workflow evals, capstone readiness, and provider smoke. Provider smoke skips cleanly by default unless live credentials and explicit opt-in are provided.

## Security and Guardrails Summary

Security policy evals cover prompt injection, secrets exfiltration, unsafe tool use, approval bypasses, data leakage, destructive operations, and scoped review-worthy requests. The policy is deterministic and explainable, so CI can run without network calls.

## Human Approval and Audit Summary

Approval workflow evals verify that blocked actions do not create approval requests, review-worthy actions create pending requests, and audit events record policy checks, allowed actions, blocked actions, and approvals.

## Setup and Run Instructions

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_agent_quality_gate.py
```

## Demo Path

1. Show the README and capstone docs.
2. Run the high-risk CLI demo: `.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json`.
3. Run the local UI: `.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py`, then open `http://127.0.0.1:8765`.
4. Run the unified quality gate and final submission-package checks.
5. Generate the AgentOps evidence index and dashboard.
6. Open the static dashboard from `artifacts/capstone/agentops_dashboard.html`.

## Known Limitations

- This is a prototype-grade / capstone-grade system, not a production deployment.
- The dataset is synthetic and intentionally small.
- Live provider smoke is optional and skipped by default.
- Approval storage and audit exports are local development constructs.
- The dashboard is a static artifact, not a live operations service.

## Final Submission Checklist

- Quality gate passes locally.
- Capstone readiness checker passes.
- Submission package checker passes.
- CLI high-risk demo and local UI smoke path are documented and runnable.
- AgentOps evidence index and dashboard are generated.
- Kaggle writeup is under 2,500 words.
- Demo script is rehearsed under five minutes.
- Generated artifacts are ignored by Git.
- No secrets or private machine paths are committed.
