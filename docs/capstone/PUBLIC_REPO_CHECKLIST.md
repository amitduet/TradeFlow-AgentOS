# Public Repository Readiness Checklist

## README Quality

- README explains the business problem and Agents for Business track fit.
- README includes setup commands, full quality gate, CLI demo command, local UI command, and local UI URL.
- README states that the default judge path uses no external services, no production data, and deterministic fallback by default.
- README points reviewers to capstone docs and generated AgentOps artifacts.

## Setup Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_agent_quality_gate.py
.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json
.venv/bin/python scripts/run_tradeflow_agent_demo_ui.py
```

## No Secrets

- Do not commit API keys, tokens, passwords, credentials, private URLs, or environment dumps.
- Keep live provider credentials in local environment variables only.
- Provider smoke remains skipped by default in public and CI runs.

## Generated Artifacts Ignored

- `artifacts/quality_gate/`
- `artifacts/release_evidence/`
- `artifacts/capstone/`
- `artifacts/security_evals/`
- `artifacts/approval_workflow_evals/`
- `artifacts/audit_trail/`

## Clear Eval Commands

- Planner evals: `.venv/bin/python scripts/run_planner_evals.py`
- Skill evals: `.venv/bin/python scripts/run_skill_evals.py`
- Security evals: `.venv/bin/python scripts/run_security_evals.py`
- Guardrail approval evals: `.venv/bin/python scripts/run_guardrail_approval_evals.py`
- Capstone readiness: `.venv/bin/python scripts/check_capstone_readiness.py`
- Submission package: `.venv/bin/python scripts/check_submission_package.py`
- Unified gate: `.venv/bin/python scripts/run_agent_quality_gate.py`

## Screenshots and Video Plan

- Capture README judge quickstart.
- Capture CLI high-risk JSON output.
- Capture local UI home page, scenario list, and high-risk result.
- Capture quality gate terminal summary.
- Capture capstone readiness and submission-package check output.
- Capture security and approval eval summaries.
- Capture generated AgentOps dashboard.
- Keep demo under five minutes.

## Public Project Link Readiness

- Repository is public or shareable before final submission.
- Default branch contains capstone docs.
- Generated artifacts are reproducible from committed scripts.
- No local-only files are required to understand the project.

## License and Status Note

- Add or confirm a license if public reuse is intended.
- State clearly that the system is prototype-grade / capstone-grade.

## Final Pre-Submit Verification

- `.venv/bin/python -m pytest -q`
- `.venv/bin/python scripts/run_agent_quality_gate.py`
- `.venv/bin/python scripts/check_capstone_readiness.py`
- `.venv/bin/python scripts/check_submission_package.py`
- `.venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json`
- `.venv/bin/python scripts/build_agentops_evidence_index.py`
- `.venv/bin/python scripts/build_agentops_dashboard.py`
- `git diff --check`
