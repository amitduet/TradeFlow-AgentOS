# Capstone Documentation Index

This folder contains the reviewer-facing Kaggle capstone package for TradeFlow AgentOS.

## Final Submission Docs

- [Kaggle writeup](kaggle_writeup.md)
- [Five-minute video script and storyboard](video_script_5min.md)
- [Media gallery checklist](media_gallery_checklist.md)
- [Capstone readiness summary](CAPSTONE_READINESS.md)
- [Public repository checklist](PUBLIC_REPO_CHECKLIST.md)
- [Legacy writeup draft](KAGGLE_WRITEUP_DRAFT.md)
- [Legacy demo video script](DEMO_VIDEO_SCRIPT.md)
- [Legacy media gallery plan](MEDIA_GALLERY_PLAN.md)

## Judge Quickstart

The public judge quickstart lives in the repository [README.md For Kaggle Judges section](../../README.md#for-kaggle-judges).

## Runnable Demo Flow

Sprint 015 adds a runnable end-user demo path for the capstone review:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
```

Flow:

1. User Input: a business scenario JSON under `examples/demo/` provides `case_id`, `user_goal`, `workflow_type`, `sales_order_id`, and optional business context.
2. Agent Planner/Workflow: `scripts/run_tradeflow_agent_demo.py` validates the scenario and routes it to the existing constrained planner in `app/agents/llm_planner.py`.
3. Skills/Tools: the planner selects the approved `analyze_sales_order_risk` workflow, matches the order-risk skill metadata, and executes deterministic read-only tools through `app/agents/order_risk_orchestrator.py`.
4. Guardrails: planner safety checks require an approved workflow, tool-grounded evidence, an unchanged synthetic dataset, and no approval bypass.
5. Approval/Audit: the existing approval gate creates a pending human approval request, and the planner audit record captures trace and evidence references.
6. Final Response: the demo adapter returns a judge-friendly JSON object with summary, risk level, risk factors, recommended action, approval reason, tools or skills used, audit events, evidence refs, and trace refs.

The optional local UI uses the same adapter:

```bash
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py --port 8765
```

## Evidence and Dashboard Generation

Generate the deterministic evidence index:

```bash
.venv/bin/python scripts/build_agentops_evidence_index.py
```

Generate the static local dashboard:

```bash
.venv/bin/python scripts/build_agentops_dashboard.py
```

Run final submission-package checks:

```bash
.venv/bin/python scripts/check_submission_package.py
```

Generated evidence and dashboard files are written under `artifacts/`, which is ignored by Git. This keeps the public repository clean while making all local artifacts reproducible from documented commands.
