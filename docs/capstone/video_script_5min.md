# Five-Minute Demo Video Script and Storyboard

Target: a YouTube demo of five minutes or less.

## 0:00-0:30 Problem and Hook

Narration: "Trading teams make order decisions across sales, finance, inventory, procurement, and logistics. TradeFlow AgentOS shows how a business agent can coordinate that review while keeping evidence, approvals, and guardrails visible."

Screen recording: Show the repository README, the project title, and the "For Kaggle Judges" section.

On-screen outcome: Viewers understand the business problem and the Agents for Business track fit.

## 0:30-1:15 Product Overview

Narration: "This is a capstone-grade prototype, not a production deployment. It uses synthetic data, deterministic tools, domain runbooks, planner contracts, and specialist agent responsibilities to review order risk safely."

Screen recording: Open `docs/capstone/README.md`, then briefly show `agents/agent_cards/`, `skills/`, `domain/runbooks/`, and `specs/AGENT_CONTRACTS.md`.

On-screen outcome: Viewers see the system is structured around business roles and explicit contracts.

## 1:15-2:15 Agent Workflow Demo

Narration: "The default judge demo is deterministic. It loads a committed high-risk business scenario, routes it through the approved order-risk workflow, runs local tools, and returns a grounded JSON recommendation with risk classification, approval state, audit events, and evidence references."

Screen recording: Run:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
```

Suggested close-up: Show `risk_level: "high"`, `approval_required: true`, the recommended action, approval reason, reason codes, audit events, and evidence references.

On-screen outcome: Viewers see the final judge-facing agent demo produce a business recommendation without live services.

## 2:15-3:05 Local UI Demo

Narration: "The same demo adapter also powers a tiny local UI built with only the Python standard library. It is still local, synthetic, deterministic, and safe for judge review."

Screen recording: Run:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py
```

Then open:

```text
http://127.0.0.1:8765
```

Suggested close-up: Show the home page, scenario dropdown, high-risk JSON input, risk summary, approval status, action, and JSON output.

On-screen outcome: Viewers see a runnable local UI over the same deterministic scenario path.

## 3:05-4:05 AgentOps, Evaluation, and Guardrails

Narration: "The project is built for reproducible review. Planner evals check route and action selection. Skill evals check trigger behavior. Security evals check prompt injection, secret requests, unsafe tool use, approval bypasses, data leakage, and destructive requests."

Screen recording: Run:

```bash
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_guardrail_approval_evals.py
```

Suggested close-up: Show all eval summaries passing.

On-screen outcome: Viewers see deterministic evidence for planner behavior, skills, security, and approval enforcement.

## 4:05-4:40 Evidence Dashboard and Quality Gate

Narration: "The unified quality gate brings the checks together. Provider smoke is included, but it skips by default unless a live provider is explicitly configured. The AgentOps evidence index and static dashboard summarize the local evidence for judges."

Screen recording: Run:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
.venv/bin/python scripts/build_release_evidence_pack.py --quality-report artifacts/quality_gate/latest.json
.venv/bin/python scripts/build_agentops_evidence_index.py
.venv/bin/python scripts/build_agentops_dashboard.py
```

Suggested close-up: Open `artifacts/capstone/agentops_dashboard.html` in a browser and show quality, security, approval, release evidence, skipped provider smoke, and limitations.

On-screen outcome: Viewers see a reviewer-ready evidence path.

## 4:40-5:00 Business Value and Closing

Narration: "The value is not replacing human reviewers. It is making cross-functional order review faster to inspect, safer to run, and easier to audit. TradeFlow AgentOS demonstrates an agentic business workflow with clear boundaries, deterministic evidence, and capstone-ready documentation."

Screen recording: Show `docs/capstone/kaggle_writeup.md`, `docs/capstone/media_gallery_checklist.md`, and the final README quickstart.

Closing message: "TradeFlow AgentOS is structured, testable, guardrailed, and ready for Kaggle capstone review."
