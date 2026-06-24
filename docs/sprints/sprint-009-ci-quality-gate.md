# Sprint 009 CI Quality Gate

## Purpose

Sprint 009 adds a unified quality gate for TradeFlow AgentOS agent behavior. It gives local development and CI one command that runs the required deterministic checks, records provider-smoke skip behavior, and writes a sanitized machine-readable report.

## Implementation

The new runner is:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py
```

It runs:

- pytest test suite
- Sprint 005 planner evals
- Sprint 006 skill evals
- Sprint 008 LLM provider smoke evals

Reports are written under:

```text
artifacts/quality_gate/
```

The report directory is ignored by Git. Reports include timestamps, command results, pass/fail/skip counts, durations, failure summaries, captured output, and CLI options. Report payloads are passed through the shared redaction helper in `app/agents/redaction.py`.

## CLI Options

```bash
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
.venv/bin/python scripts/run_agent_quality_gate.py --quiet
.venv/bin/python scripts/run_agent_quality_gate.py --stop-on-failure
.venv/bin/python scripts/run_agent_quality_gate.py --require-live-provider
```

By default, the runner continues after failures so the JSON report contains all gate outcomes. `--stop-on-failure` opts into early exit after the first failed command.

## Skip And Fail Semantics

The provider smoke gate does not require live credentials by default. If live smoke is disabled or credentials are missing, `scripts/run_llm_provider_smoke.py` reports `Status: skipped` and exits zero. The unified gate records that as a skip, not a failure.

When `--require-live-provider` is passed, the quality gate invokes smoke with `--live`. If smoke still skips because credentials or opt-in are missing, the unified gate records the provider smoke gate as failed and exits non-zero.

## CI

The workflow in `.github/workflows/ci.yml` installs dependencies, runs `python -m pytest -q`, and then runs:

```bash
python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/ci.json
```

CI intentionally does not require live provider credentials. To enable live provider smoke later, configure repository secrets for `TRADEFLOW_LLM_PROVIDER`, `TRADEFLOW_LLM_MODEL`, and `TRADEFLOW_LLM_API_KEY`, set `TRADEFLOW_LLM_SMOKE_ENABLED=true`, and pass `--require-live-provider`.

## Acceptance Criteria

- all existing tests pass
- planner evals pass
- skill evals pass
- provider smoke passes or cleanly skips without credentials
- unified quality gate passes locally without provider credentials
- `--json-out artifacts/quality_gate/latest.json` writes a valid redacted report
- CI workflow uses the unified quality gate
- generated reports are ignored by Git

## Verification Results

Sprint 009 was verified with:

```bash
.venv/bin/pytest -q
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/python scripts/run_llm_provider_smoke.py
.venv/bin/python scripts/run_agent_quality_gate.py
.venv/bin/python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```
