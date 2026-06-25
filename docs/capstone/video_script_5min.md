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

Narration: "The default planner is deterministic. It extracts a supported sales order, selects an approved workflow, runs local tools, and returns a grounded recommendation with evidence references and approval state."

Screen recording: Run:

```bash
.venv/bin/python scripts/run_planner.py --request "Analyze sales order SO-1005"
```

Suggested close-up: Show the recommended action, risk level, approval state, reason codes, and evidence references.

On-screen outcome: Viewers see the agent workflow produce a business recommendation without live services.

## 2:15-3:15 AgentOps, Evaluation, and Guardrails

Narration: "The project is built for reproducible review. Planner evals check route and action selection. Skill evals check trigger behavior. Security evals check prompt injection, secret requests, unsafe tool use, approval bypasses, data leakage, and destructive requests."

Screen recording: Run:

```bash
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_guardrail_enforcement_evals.py
```

Suggested close-up: Show all eval summaries passing.

On-screen outcome: Viewers see deterministic evidence for planner behavior, skills, security, and approval enforcement.

## 3:15-4:15 Evidence Dashboard and Quality Gate

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

## 4:15-5:00 Business Value and Closing

Narration: "The value is not replacing human reviewers. It is making cross-functional order review faster to inspect, safer to run, and easier to audit. TradeFlow AgentOS demonstrates an agentic business workflow with clear boundaries, deterministic evidence, and capstone-ready documentation."

Screen recording: Show `docs/capstone/kaggle_writeup.md`, `docs/capstone/media_gallery_checklist.md`, and the final README quickstart.

Closing message: "TradeFlow AgentOS is structured, testable, guardrailed, and ready for Kaggle capstone review."
