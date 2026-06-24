# Sprint 010: Quality Gate History, Trends, and Release Evidence

Sprint 010 turns the Sprint 009 quality gate from a single-run check into an auditable AgentOps record. The system now stores timestamped quality gate history, summarizes trends across prior runs, and builds a reviewer-ready release evidence pack for sprint review, capstone demos, and submission readiness.

## What Changed

- `scripts/run_agent_quality_gate.py` still runs pytest, planner evals, skill evals, and provider smoke, but now writes a timestamped history report by default.
- `scripts/summarize_quality_history.py` reads prior reports and produces JSON or Markdown trend summaries.
- `scripts/build_release_evidence_pack.py` packages the latest report, trend summary, reproduction commands, known limitations, and artifact inventory.
- CI writes `artifacts/quality_gate/latest.json`, builds release evidence, and uploads ignored artifacts.

All generated reports remain under `artifacts/` and are ignored by Git. Reports are passed through the shared redaction helper before writing so API keys, auth headers, token-like values, and configured provider secrets are not persisted.

## Run the Quality Gate

```bash
python scripts/run_agent_quality_gate.py
```

By default this writes a timestamped history file under:

```text
artifacts/quality_gate/history/
```

Write a stable report path as well:

```bash
python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

Skip timestamped history for a one-off run:

```bash
python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json --no-history
```

Keep only the newest N history reports:

```bash
python scripts/run_agent_quality_gate.py --max-history 20
```

Provider smoke still skips cleanly by default when live credentials are absent. To require a live provider in a configured local or staging environment:

```bash
TRADEFLOW_LLM_SMOKE_ENABLED=true \
TRADEFLOW_LLM_PROVIDER=<provider> \
TRADEFLOW_LLM_MODEL=<model> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
python scripts/run_agent_quality_gate.py --require-live-provider
```

## Inspect History and Trends

Generate a Markdown trend summary:

```bash
python scripts/summarize_quality_history.py \
  --history-dir artifacts/quality_gate/history \
  --markdown-out artifacts/quality_gate/trend.md
```

Generate a machine-readable trend summary:

```bash
python scripts/summarize_quality_history.py \
  --history-dir artifacts/quality_gate/history \
  --json-out artifacts/quality_gate/trend.json \
  --quiet
```

The summary reports latest and previous status, pass/fail/skip deltas, duration delta, per-gate status changes, passing or failing streaks, and malformed files that were ignored.

## Generate Release Evidence

```bash
python scripts/build_release_evidence_pack.py \
  --quality-report artifacts/quality_gate/latest.json \
  --history-dir artifacts/quality_gate/history \
  --out-dir artifacts/release_evidence/latest \
  --release-name "Sprint 010"
```

The evidence pack includes:

- `release_evidence.json`
- `release_evidence.md`
- `quality_gate_report.json`
- `quality_trend_summary.json`
- `quality_trend_summary.md`

The Markdown pack is intended for reviewers. It includes the release name, generated timestamp, git branch and commit, dirty status, overall quality status, gate summary table, provider-smoke skip explanation, local reproduction commands, artifact inventory, limitations, and next recommended action.

## CI Behavior

CI remains deterministic and credential-free by default. It runs tests, runs the unified quality gate, generates `artifacts/quality_gate/latest.json`, builds the release evidence pack, and uploads quality/evidence artifacts. A failed quality gate still fails CI; provider smoke does not fail normal CI when live provider credentials are absent.

## Why This Matters

Production-grade AgentOps needs more than a green terminal line. Sprint 010 creates durable release evidence that shows what was checked, when it ran, which git revision produced it, whether the working tree was dirty, how each gate behaved, and whether quality is improving or regressing over time. That audit trail supports capstone submission readiness while preserving the project safety model: no production data, no network calls by default, no required live LLM credentials, and no committed generated reports.
