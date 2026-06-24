# Sprint 013 - AgentOps Dashboard and Capstone Readiness

## Sprint Objective

Prepare TradeFlow AgentOS for Kaggle capstone review by making the project easier to understand, verify, and demonstrate through deterministic evidence, static dashboard output, capstone docs, and readiness checks.

## Implemented Files

- `scripts/build_agentops_evidence_index.py`
- `scripts/build_agentops_dashboard.py`
- `scripts/check_capstone_readiness.py`
- `docs/capstone/CAPSTONE_READINESS.md`
- `docs/capstone/KAGGLE_WRITEUP_DRAFT.md`
- `docs/capstone/DEMO_VIDEO_SCRIPT.md`
- `docs/capstone/PUBLIC_REPO_CHECKLIST.md`
- `docs/capstone/MEDIA_GALLERY_PLAN.md`
- `tests/test_sprint_013_agentops_capstone_readiness.py`

## Evidence Index Model

The AgentOps evidence index scans local generated artifacts for the latest quality gate, security eval, guardrail or approval workflow eval, release evidence pack, and optional quality history summary. It writes deterministic JSON and Markdown under `artifacts/capstone/`, includes verification commands, records known skipped checks, and emits warnings when optional artifacts are absent.

## Dashboard Model

The dashboard builder reads the evidence index JSON and writes a dependency-free static HTML file under `artifacts/capstone/agentops_dashboard.html`. It uses inline CSS only, escapes dynamic values, and highlights quality gate, test/eval, security guardrail, human approval/audit, release evidence, provider smoke skip, verification commands, limitations, and what judges should notice.

## Capstone Docs

The committed capstone docs provide a readiness summary, Kaggle writeup draft, five-minute demo script, public repository checklist, and media gallery plan. They avoid secrets, private URLs, and local absolute paths.

## Quality Gate Integration

`scripts/run_agent_quality_gate.py` now includes `capstone_readiness` as a first-class deterministic gate. Provider smoke remains a separate gate and continues to skip cleanly by default when live provider credentials are not configured.

## Release Evidence Integration

`scripts/build_release_evidence_pack.py` now includes a capstone evidence section when AgentOps artifacts are present. Missing capstone artifacts are reported as not generated rather than failing the release pack.

## Limitations

- Generated AgentOps artifacts depend on prior local evidence generation.
- The dashboard is static and local; it is not a production monitoring UI.
- Live provider smoke remains opt-in and is not required for default CI.
- The project remains prototype-grade / capstone-grade.

## Verification Commands

```bash
.venv/bin/python -m pytest tests/test_sprint_013_agentops_capstone_readiness.py -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/python scripts/run_llm_provider_smoke.py
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_guardrail_enforcement_evals.py
.venv/bin/python scripts/check_capstone_readiness.py
.venv/bin/python scripts/run_agent_quality_gate.py
.venv/bin/python scripts/summarize_quality_history.py
.venv/bin/python scripts/build_release_evidence_pack.py
.venv/bin/python scripts/build_agentops_evidence_index.py
.venv/bin/python scripts/build_agentops_dashboard.py
git diff --check
```
