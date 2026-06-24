# Media Gallery Plan

## Cover Image Concept

Create a clean business-control-tower visual: a central TradeFlow AgentOS hub connected to Sales, CRM, Inventory, Finance, Purchase, Logistics, Security, and Approval nodes. Use synthetic or abstract business data only. Do not include real customer names, private dashboards, credentials, or local machine details.

## Suggested Screenshots

- README project overview and track fit
- Agent architecture or agent cards folder
- Planner run showing grounded recommendation
- Quality gate terminal summary
- Security eval summary
- Approval workflow eval summary
- Capstone readiness summary

## Suggested Dashboard Screenshot

Generate the static dashboard:

```bash
.venv/bin/python scripts/build_agentops_evidence_index.py
.venv/bin/python scripts/build_agentops_dashboard.py
```

Capture `artifacts/capstone/agentops_dashboard.html` in a browser. The screenshot should show project name, quality status, security status, approval status, provider smoke skip explanation, and what judges should notice.

## Suggested Terminal Output Screenshot

Capture a clean terminal showing:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py
```

The screenshot should show the final quality gate summary. Avoid showing environment variables.

## Video Upload Reminder

Upload the final demo video to the Kaggle submission area or the required public hosting location. Confirm audio is clear, terminal font is readable, and the run stays under five minutes.

## No Private Data Warning

Use only synthetic project data and generated local artifacts. Do not show API keys, auth headers, private URLs, local environment files, private account names, or machine-specific absolute paths.
