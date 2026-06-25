# Media Gallery Checklist

Use this checklist for Kaggle submission media. Do not include private data, real credentials, private URLs, or customer information. The project uses synthetic records only.

## Cover Image

Recommended filename: `tradeflow-agentos-cover.png`

Caption: "TradeFlow AgentOS: an agentic business control tower for order-risk review."

Suggested content: Project name, Agents for Business track, and a simple visual showing Sales, CRM, Inventory, Finance, Purchase, Logistics, Guardrails, Approval, and Evidence.

## Repository Screenshot

Recommended filename: `01-repository-quickstart.png`

Caption: "Public judge quickstart and capstone documentation entry point."

Capture: README title, "For Kaggle Judges" section, and setup commands.

## Architecture Diagram Screenshot

Recommended filename: `02-agent-architecture.png`

Caption: "Specialist agents, deterministic tools, planner contracts, guardrails, approval, and evidence."

Capture: A diagram made from `specs/AGENT_CONTRACTS.md`, the agent cards, or a clean slide-style diagram created for the demo.

## Agent Workflow Screenshot

Recommended filename: `03-agent-workflow-demo.png`

Caption: "Order-risk analysis produces a grounded recommendation with approval state and evidence."

Capture: Terminal output from:

```bash
.venv/bin/python scripts/run_planner.py --request "Analyze sales order SO-1005"
```

## Quality Gate Screenshot

Recommended filename: `04-quality-gate.png`

Caption: "Unified quality gate passes deterministic tests and evals; provider smoke skips by default."

Capture: Terminal output from:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py
```

## AgentOps Dashboard Screenshot

Recommended filename: `05-agentops-dashboard.png`

Caption: "Static AgentOps dashboard summarizing quality, security, approval, release evidence, limitations, and skipped checks."

Capture: Browser view of:

```text
artifacts/capstone/agentops_dashboard.html
```

## Evidence Index Screenshot

Recommended filename: `06-evidence-index.png`

Caption: "Deterministic evidence index for capstone review."

Capture: `artifacts/capstone/agentops_evidence_index.md` or the JSON summary opened in an editor.

## Demo Video

Recommended filename: `tradeflow-agentos-demo-5min.mp4`

Caption: "Five-minute TradeFlow AgentOS capstone demo."

Checklist:

- Video is five minutes or less.
- Narration follows `docs/capstone/video_script_5min.md`.
- Terminal commands are readable.
- No private desktop notifications, keys, private URLs, or personal files are visible.
- Dashboard and quality-gate outputs are generated from repository commands.
