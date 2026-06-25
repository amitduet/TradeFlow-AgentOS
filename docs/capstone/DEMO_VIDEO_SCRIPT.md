# Demo Video Script

Target length: five minutes or less.

## 0:00-0:30 - Problem and Project Overview

Narration: "TradeFlow AgentOS is a capstone-grade prototype for the Agents for Business track. It demonstrates how a trading company could use coordinated agents to evaluate order risk while keeping approvals, guardrails, and audit evidence visible."

Screen action: Show the README title, short project description, and capstone docs folder.

Expected output: Viewers understand the business problem and track fit.

## 0:30-1:15 - Architecture and Agent Workflow

Narration: "The system uses synthetic data, deterministic tools, domain runbooks, skills, planner contracts, and specialist business agents. The default planner is deterministic and routes only to approved workflows."

Screen action: Show `app/agents/`, `skills/`, `domain/runbooks/`, and `specs/AGENT_CONTRACTS.md`.

Terminal command:

```bash
.venv/bin/python scripts/run_planner.py --request "Analyze sales order SO-1005"
```

Expected output: A grounded order-risk recommendation with approval state and evidence references.

## 1:15-2:15 - Quality Gate and Evaluation Evidence

Narration: "The project is designed to be reviewed through deterministic checks. The unified quality gate runs tests, planner evals, skill evals, security evals, approval workflow evals, capstone readiness, and provider smoke."

Screen action: Run the quality gate or show a recent completed quality gate report.

Terminal command:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

Expected output: Status is passed, with provider smoke reported as skipped by default when no live provider is configured.

## 2:15-3:15 - Security Guardrails and Approval Workflow

Narration: "Security and approval behavior are tested separately. Prompt injection, secret requests, approval bypass attempts, data leakage, and destructive operations are blocked or routed to review."

Screen action: Show security and approval eval files, then run the eval commands.

Terminal commands:

```bash
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_guardrail_enforcement_evals.py
```

Expected output: Security evals pass. Guardrail and approval workflow evals pass.

## 3:15-4:15 - Release Evidence and AgentOps Dashboard

Narration: "Sprint 013 adds reviewer-friendly AgentOps artifacts: an evidence index and a static local dashboard. These summarize quality, security, approval, release evidence, skipped checks, limitations, and verification commands."

Screen action: Generate the evidence index and dashboard, then open the HTML artifact locally.

Terminal commands:

```bash
.venv/bin/python scripts/build_agentops_evidence_index.py
.venv/bin/python scripts/build_agentops_dashboard.py
```

Expected output: JSON, Markdown, and HTML artifacts are written under `artifacts/capstone/`.

## 4:15-5:00 - Business Value, Limitations, and Next Steps

Narration: "The value is not replacing humans. It is making cross-functional order review faster, safer, and easier to audit. This remains prototype-grade / capstone-grade. Next steps would include production observability, real approval storage, richer data, and staged live-provider validation."

Screen action: Show `docs/capstone/CAPSTONE_READINESS.md`, known limitations, and final checklist.

Closing message: "TradeFlow AgentOS demonstrates a business agent that is structured, testable, guardrailed, and ready for capstone review."
