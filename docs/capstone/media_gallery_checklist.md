# Media Gallery Checklist

Use this checklist for Kaggle submission media. Do not include private data, real credentials, private URLs, or customer information. The project uses synthetic records only.

## Cover Image

Recommended filename: `tradeflow-agentos-cover.png`

Caption: "TradeFlow AgentOS: an agentic business control tower for order-risk review."

Suggested content: Project name, Agents for Business track, and a simple visual showing Sales, CRM, Inventory, Finance, Purchase, Logistics, Guardrails, Approval, and Evidence.

## Repository Screenshot

Recommended filename: `01-repository-quickstart.png`

Caption: "README judge quickstart with setup, quality gate, CLI demo, UI demo, and local URL."

Capture: README title, "For Kaggle Judges" section, and setup commands.

## CLI High-Risk JSON Output

Recommended filename: `02-cli-high-risk-json-output.png`

Caption: "CLI high-risk JSON output showing risk classification, approval escalation, guardrail/audit explanation, and evidence."

Capture: Terminal output from:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
```

## Local UI Home Page

Recommended filename: `03-local-ui-home.png`

Caption: "Local stdlib-only UI home page running on 127.0.0.1:8765."

Capture: Browser view after running:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py
```

Then opening:

```text
http://127.0.0.1:8765
```

## Local UI Scenario List

Recommended filename: `04-local-ui-scenarios.png`

Caption: "Local UI scenario dropdown with low, medium, and high-risk demo inputs."

Capture: UI scenario selector plus the loaded high-risk JSON input.

## Local UI High-Risk Result

Recommended filename: `05-local-ui-high-risk-result.png`

Caption: "High-risk UI result with approval required, recommended action, trace, and JSON evidence."

Capture: UI result panel after running the high-risk scenario.

## Quality Gate Terminal Result

Recommended filename: `06-quality-gate-terminal-result.png`

Caption: "Unified quality gate passes deterministic tests and evals; provider smoke skips by default."

Capture: Terminal output from:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py
```

## Capstone Readiness and Submission Package Checks

Recommended filename: `07-capstone-submission-checks.png`

Caption: "Capstone readiness and final submission-package checks pass."

Capture: Terminal output from:

```bash
.venv/bin/python scripts/check_capstone_readiness.py
.venv/bin/python scripts/check_submission_package.py
```

## Architecture and Evidence Screenshot

Recommended filename: `08-architecture-evidence.png`

Caption: "Specialist agents, deterministic tools, planner contracts, guardrails, approval, and evidence."

Capture: A diagram made from `specs/AGENT_CONTRACTS.md`, the agent cards, or a clean slide-style diagram created for the demo. If the local evidence dashboard has already been generated, capture it too:

```bash
.venv/bin/python scripts/build_agentops_evidence_index.py
.venv/bin/python scripts/build_agentops_dashboard.py
```

Open:

```text
artifacts/capstone/agentops_dashboard.html
```

## AgentOps Dashboard Screenshot

Recommended filename: `09-agentops-dashboard.png`

Caption: "Static AgentOps dashboard summarizing quality, security, approval, release evidence, limitations, and skipped checks."

Capture: Browser view of:

```text
artifacts/capstone/agentops_dashboard.html
```

## Evidence Index Screenshot

Recommended filename: `10-evidence-index.png`

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
