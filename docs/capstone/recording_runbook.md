# TradeFlow AgentOS Recording Runbook

Use this runbook to record the five-minute technical overview in Screen Studio, Loom, or OBS.

## Pre-Record Setup

1. Use a clean terminal at the repository root.
2. Activate the local environment.
3. Clear ignored demo runtime artifacts before running the UI or CLI demo sequentially.
4. Keep the recording to one browser window, one terminal window, and one editor window.

```bash
cd TradeFlow-AgentOS
source .venv/bin/activate
rm -f artifacts/demo_runtime/approval_requests.json artifacts/demo_runtime/planner_audit.jsonl
```

Do not run the low, medium, and high demo commands in parallel against the default runtime approval file. During verification on July 1, 2026, parallel runs corrupted the ignored local `artifacts/demo_runtime/approval_requests.json` file. Sequential runs passed.

## Terminal Window Layout

Use two terminal tabs:

- Tab 1: CLI demos, evals, quality gate.
- Tab 2: UI server.

Set terminal font large enough for screen capture. Resize to show about 100 columns and 30 lines.

## Browser and Editor Layout

Open these before recording:

- `README.md`
- `docs/capstone/README.md`
- `docs/capstone/video_script_5min.md`
- `docs/capstone/kaggle_writeup.md`
- `docs/capstone/CAPSTONE_READINESS.md`
- `app/agents/demo_agent.py`
- `app/agents/llm_planner.py`
- `app/agents/order_risk_orchestrator.py`
- `app/agents/approval_gate.py`
- `evals/`
- `tests/`

Browser:

- `http://127.0.0.1:8765` after starting the UI.
- Optional: generated dashboard at `artifacts/capstone/agentops_dashboard.html` if you choose to show it.

## Exact Recording Sequence

### 0:00-0:25: README Hook

Show `README.md` and the "For Kaggle Judges" section.

Say that TradeFlow AgentOS reviews trading order risk across customer, inventory, procurement, logistics, finance, approvals, and audit evidence.

### 0:25-0:55: Scope

Show `docs/capstone/README.md` and `examples/demo/`.

State that the default path is synthetic, deterministic, local, and does not need live LLM/API credentials. Mention optional LLM mode separately.

### 0:55-1:35: Architecture

Show:

- `app/agents/demo_agent.py`
- `app/agents/llm_planner.py`
- `app/agents/order_risk_orchestrator.py`
- `domain/runbooks/`
- `skills/`
- `specs/AGENT_CONTRACTS.md`

Explain planner, approved workflow, deterministic tools, approval gate, audit, and evals.

### 1:35-2:35: CLI Demo

Run commands sequentially:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/low_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/medium_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
```

Expected outputs:

- Low: `risk_level` is `low`, action is `monitor_only`, risk factors are empty.
- Medium: `risk_level` is `medium`, action is `contact_supplier`, risk factor is `delayed_logistics_event`.
- High: `risk_level` is `high`, action is `create_purchase_order`, risk factor is `missing_linked_po_for_drop_shipping`.
- All current scenario outputs include `approval_required: true` and a pending approval event.
- `trace_refs.provider_used` is `deterministic`.

Only zoom on the relevant JSON fields. Avoid scrolling through the full payload slowly.

### 2:35-3:05: Local UI Demo

In terminal Tab 2:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py
```

Expected output:

```text
TradeFlow AgentOS demo UI: http://127.0.0.1:8765
```

Open `http://127.0.0.1:8765`, choose `high_risk_order.json`, and click `Run Agent Review`.

Expected browser behavior:

- Scenario dropdown lists `high_risk_order.json`, `low_risk_order.json`, and `medium_risk_order.json`.
- Risk shows `high`.
- Approval shows required.
- Action shows `create_purchase_order`.
- JSON output includes audit events, evidence refs, and deterministic trace refs.

Stop the server after the UI section with `Ctrl-C`.

### 3:05-4:10: Evals and Quality Gate

Run or show recent verified output:

```bash
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_guardrail_approval_evals.py
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

Expected outputs verified on July 1, 2026:

- Planner eval summary: `10/10 passed`.
- Skill eval summary: `18/18 passed`.
- Security summary: `21/21 security cases passed`.
- Approval workflow summary: `3/3 approval workflow cases passed`.
- Quality gate summary: `7 passed, 0 failed, 1 skipped out of 8 gates`.
- LLM provider smoke is skipped by default.

### 4:10-4:40: Submission Package

Run:

```bash
.venv/bin/python scripts/check_submission_package.py
```

Expected output:

```text
Submission Package Summary
Status: passed
Summary: 76/76 submission package checks passed
```

Show `docs/capstone/kaggle_writeup.md`, `docs/capstone/CAPSTONE_READINESS.md`, and `docs/capstone/media_gallery_checklist.md`.

### 4:40-5:00: Closing

Return to the README quickstart and quality-gate summary.

Close with the message that TradeFlow AgentOS is deterministic by default, optional-LLM-ready, testable, guardrailed, and prepared for Agents for Business capstone review.

## Optional API/CLI Calls

While the UI server is running:

```bash
curl -s http://127.0.0.1:8765/api/scenarios
curl -s -X POST http://127.0.0.1:8765/api/demo \
  -H 'Content-Type: application/json' \
  --data-binary @examples/demo/high_risk_order.json
```

Expected API result:

- `/api/scenarios` returns the three demo JSON filenames.
- `/api/demo` returns the same high-risk response as the browser UI.

## Recovery Steps

If the demo CLI or UI returns `Extra data` while reading approval requests:

```bash
rm -f artifacts/demo_runtime/approval_requests.json artifacts/demo_runtime/planner_audit.jsonl
```

Then rerun the command sequentially.

If port `8765` is already in use:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py --port 8766
```

Then open `http://127.0.0.1:8766`.

If provider smoke is skipped:

This is expected for the default judge path. Do not try to add credentials during the recording. Say that live provider smoke is optional and opt-in.

If pytest or quality gate fails:

1. Read the failing gate name from the output.
2. If it is the UI endpoint and mentions approval JSON parsing, clean `artifacts/demo_runtime/`.
3. Rerun `scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json`.
4. If the failure persists, do not claim passing results in the recording.

## Final Export Checklist

- Length is under five minutes.
- Screen text is readable.
- Audio is clean and not rushed.
- Commands shown match actual repo commands.
- No local secrets or private data are visible.
- No unsupported production claims are made.
- The final screen shows README quickstart or quality-gate summary.

## YouTube/Kaggle Upload Checklist

- Title: `TradeFlow AgentOS - Kaggle AI Agents Capstone Demo`
- Description includes that the default path is deterministic and local.
- Mention Agents for Business track.
- Include repository link.
- Include commands for CLI demo, UI demo, and quality gate.
- Confirm the uploaded video is public or unlisted according to Kaggle submission requirements.
- Confirm the Kaggle submission links to the repository, writeup, and video.
