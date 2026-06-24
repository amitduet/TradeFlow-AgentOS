# Sprint 008 Provider Smoke Evals

## Objective

Add a safe local/staging smoke-evaluation workflow for real LLM planner providers while preserving deterministic CI, Sprint 007 fallback behavior, typed planner contracts, traces, audit records, skill evals, planner evals, and approval gates.

## Deterministic Default

The default smoke command makes no live provider call:

```bash
.venv/bin/python scripts/run_llm_provider_smoke.py
```

It exits zero with `Status: skipped` unless live smoke is explicitly enabled through `--live` or `TRADEFLOW_LLM_SMOKE_ENABLED=true`.

Normal verification remains deterministic:

```bash
.venv/bin/pytest -q
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
```

## Configuration

Live smoke uses the same provider settings as Sprint 007 plus explicit smoke controls:

```bash
TRADEFLOW_LLM_PROVIDER=openai
TRADEFLOW_LLM_MODEL=<model-name>
TRADEFLOW_LLM_BASE_URL=
TRADEFLOW_LLM_API_KEY=<local-secret>
TRADEFLOW_LLM_TIMEOUT_SECONDS=30
TRADEFLOW_LLM_SMOKE_ENABLED=true
TRADEFLOW_LLM_SMOKE_MAX_CASES=
```

Never commit `.env` files or real provider credentials.

## Smoke Cases

The versioned smoke dataset is `evals/llm_provider_smoke_cases.json`. It covers:

- low-risk sales order planning
- high-risk order requiring approval
- missing evidence that must not be hallucinated
- unsafe approval-bypass or execution request
- ambiguous request that should clarify or fall back safely

Assertions are structural and policy-based, not exact text matching.

## Fake Provider Modes

Fake modes exercise the smoke harness and Sprint 007 fallback paths without network access:

```bash
.venv/bin/python scripts/run_llm_provider_smoke.py --fake-provider success
.venv/bin/python scripts/run_llm_provider_smoke.py --fake-provider invalid-json --max-cases 1
.venv/bin/python scripts/run_llm_provider_smoke.py --fake-provider schema-violation --max-cases 1
.venv/bin/python scripts/run_llm_provider_smoke.py --fake-provider timeout --max-cases 1
.venv/bin/python scripts/run_llm_provider_smoke.py --fake-provider unsafe --max-cases 1
```

These modes are deterministic and do not use live credentials.

## Live Smoke

Run live smoke only from a local or staging environment with explicit opt-in:

```bash
TRADEFLOW_LLM_SMOKE_ENABLED=true \
TRADEFLOW_LLM_PROVIDER=<provider> \
TRADEFLOW_LLM_MODEL=<model> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
.venv/bin/python scripts/run_llm_provider_smoke.py --live --write-report
```

Provider, model, base URL, and timeout can also be supplied with non-secret CLI flags. Keep API keys in environment variables rather than command history.

Missing opt-in or missing credentials produce a clean skip. A configured live run exits non-zero only when one or more smoke cases fail.

## Reports

Use `--write-report` or `--report-path` to write sanitized JSON reports. The default report directory is:

```text
artifacts/provider_smoke/
```

That path is ignored by Git. Reports include dataset version, mode, pass/fail counts, provider metadata, provider/fallback state, safety outcome, route, risk, approval state, reason codes, and validation errors.

Reports and CLI output redact API keys, auth headers, token-like values, and secret-bearing exception text.

## Safety Rules

The smoke harness does not weaken Sprint 007 behavior:

- deterministic planner remains the default
- no live provider is called during tests or normal evals
- invalid JSON, schema violations, unsafe output, hallucinated evidence, timeouts, and provider errors still fall back deterministically
- approval gates remain pending and authoritative
- no purchase order, payment, inventory, credit, or supplier-term action is executed

## Known Limitations

- Live smoke is manual/staging only and depends on network and provider behavior.
- The live adapter remains minimal and does not stream responses.
- Smoke cases validate provider compatibility and safety behavior, not full business accuracy.
- Reports should be attached to PRs only after confirming they are sanitized.

## Next Sprint Recommendation

Add provider compatibility snapshots and optional staging automation that archives sanitized smoke reports while keeping deterministic CI as the required gate.
