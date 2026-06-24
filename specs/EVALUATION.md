# Evaluation

TradeFlow AgentOS uses deterministic evaluation before agentic evaluation. Sprint 2 focuses on proving that local tools can retrieve and validate synthetic business data without LLM calls, network access, or production systems.

Sprint 3 extends deterministic evaluation to the first agent-facing workflow. The workflow still has no LLM planner: evals verify that the orchestrator calls approved tools, produces typed recommendations, opens approval gates, and leaves the source dataset unchanged.

Sprint 5 adds constrained-planner evaluation before live LLM integration. Planner evals verify route selection, recommended action, approval state, risk level, safety outcome, refusal or escalation behavior, and reason-code coverage against a versioned golden dataset.

Sprint 6 adds deterministic skill trigger evaluation before live LLM integration. Skill evals verify that business-domain skill files trigger on supported requests, avoid wrong-skill matches on negative requests, and route approval-bypass phrasing to approval-gate handling rather than procurement execution.

Sprint 7 adds mocked real-provider integration tests before any live provider is required in CI. These tests verify strict JSON schema validation, rejection of unsafe provider output, deterministic fallback, provider metadata in trace and audit records, and preservation of planner and skill eval pass rates without LLM credentials.

Sprint 8 adds an opt-in provider smoke-eval harness for local or staging use. It validates live-provider behavior against business-domain planner cases only when explicitly enabled, while deterministic tests and CI continue to run without network access or credentials.

Sprint 9 adds a unified local and CI quality gate. It aggregates tests, planner evals, skill evals, and provider smoke into one sanitized JSON report while preserving Sprint 8 skip behavior for missing live provider credentials.

Sprint 10 adds quality gate history, trend reporting, and release evidence packs. This creates an auditable record of recent quality runs, gate-level changes, and reviewer-ready release artifacts without adding network calls or requiring live provider credentials.

Sprint 11 adds deterministic security policy evals. These checks cover prompt injection, secrets exfiltration, unsafe tool requests, unauthorized financial actions, instruction override attempts, data leakage, and destructive operations without LLM calls or network access.

Sprint 12 adds deterministic approval workflow evals. These checks verify that Sprint 11 policy decisions are enforced in workflow outcomes, unsafe actions are blocked, review-worthy actions create pending approval requests, and audit events are emitted without external services.

Sprint 13 adds capstone readiness evaluation and AgentOps evidence artifacts. The capstone readiness gate validates committed capstone docs, writeup length, demo timing blocks, public repo checklist, media plan, README references, ignored generated artifacts, and absence of obvious secrets or local absolute paths. The AgentOps evidence index and static dashboard summarize local quality, security, approval, release, and history evidence for capstone review.

## Why Synthetic Data

The capstone must demonstrate realistic trading-company workflows without storing customer data, supplier terms, production orders, private receivables, or external system credentials. The canonical dataset in `data/synthetic/tradeflow_seed.json` is generated from a fixed seed and contains only fabricated records.

## Deterministic Tool Evals

Sprint 2 eval cases live in `evals/sprint_002_tool_eval_cases.json`. They cover:

- customer profile lookup with rating and contact person
- supplier profile lookup with contact person
- customer-filtered sales order listing
- drop-shipping chain reconstruction
- sales-order-linked logistics events
- margin calculation
- low customer rating risk detection
- missing drop-ship PO risk detection
- delayed logistics risk detection
- exclusion of unrelated customer orders

Run them with:

```bash
python scripts/run_tool_evals.py
```

The runner compares expected key outputs and expected risk flags, prints a pass/fail summary, and exits non-zero on failure.

## Deterministic Workflow Evals

Sprint 3 workflow eval cases live in `evals/sprint_003_workflow_eval_cases.json`. They cover:

- high-risk low-rated customer escalation
- missing drop-shipping purchase order recommendation
- delayed logistics supplier contact recommendation
- low-margin escalation recommendation
- healthy order monitor-only recommendation
- required tool-call trace coverage
- pending approval request creation
- source dataset immutability

Run them with:

```bash
python scripts/run_workflow_evals.py
```

The runner executes the workflow, compares expected key outputs, validates the trace, checks approval status, verifies source dataset hash stability when required, prints pass/fail results, and exits non-zero on failure.

## Test Coverage

Sprint 2 pytest coverage validates:

- deterministic generation for the same seed
- dataset referential integrity through Pydantic models
- required customer and supplier contact fields
- purchase order draft links to sales orders
- logistics event links to sales orders
- drop-shipping chain shape
- stable order margin outputs
- known risk flags
- eval runner success

Sprint 3 pytest coverage validates:

- structured workflow result model
- tool-call trace capture
- required tool-call sequence
- approval requirement and default pending status
- explicit approve/reject status transitions
- deterministic recommendation rules
- source synthetic dataset immutability
- workflow eval runner success

Run all tests with:

```bash
pytest
```

## Future Agent Evaluation

Future sprints can add LLM-agent evals on top of this deterministic foundation. Those evals should verify that agents call these tools, cite returned synthetic facts, respect human approval gates, and avoid inventing hidden production state.

## Sprint 5 Planner Evals

Sprint 5 planner eval cases live in `evals/sprint_005_planner_golden_cases.json`. They cover:

- low-risk order analysis
- medium-risk supplier-contact recommendation
- high-risk order requiring approval
- missing drop-ship purchase order recommendation
- missing sales order id
- unknown sales order id
- ambiguous order request
- unsafe approval bypass attempt
- unavailable or confidential data request
- unsupported business action

Run them with:

```bash
python scripts/run_planner_evals.py
```

The runner prints per-case pass/fail output, reports route/action/approval/safety/risk/reason-code metrics, and exits non-zero on any failed case or failed pass-rate threshold.

## Sprint 6 Skill Trigger Evals

Sprint 6 skill trigger cases live in `evals/sprint_006_skill_trigger_cases.json`. They cover:

- positive and negative order-risk-analysis triggers
- positive and negative purchase-order-recommendation triggers
- positive and negative approval-gate-handling triggers
- approval-bypass wording that must map to approval-gate handling
- negative cases that must not trigger the wrong skill

Run them with:

```bash
python scripts/run_skill_evals.py
```

The runner loads skill metadata from `skills/*/SKILL.md`, evaluates phrase-based trigger behavior through `app/agents/domain_skills.py`, prints per-case pass/fail output, reports trigger accuracy, negative trigger accuracy, and per-skill pass rates, and exits non-zero on failure.

Sprint 6 skills differ from planner code: skills document business trigger boundaries and safety constraints, while planner code still performs deterministic routing and workflow execution. Future real LLM provider evals should require the provider to use these same runbooks, skill trigger boundaries, traces, audit logs, and approval constraints.

## Sprint 7 LLM Provider Integration Evals

Sprint 7 provider tests live in `tests/test_sprint_007_llm_provider_integration.py`. They cover:

- valid mocked LLM JSON mapping into planner contracts
- malformed JSON fallback
- missing required fields fallback
- invalid enum rejection
- approval-bypass and execution-claim rejection
- unsupported route and action rejection
- hallucinated evidence-reference rejection
- timeout/error fallback
- provider metadata in `PlannerTrace` and audit JSONL records
- CLI provider and fallback reporting
- planner evals and skill evals passing without live credentials

Run the focused provider tests with:

```bash
python -m pytest tests/test_sprint_007_llm_provider_integration.py -q
```

Run the full deterministic verification set with:

```bash
python scripts/run_planner_evals.py
python scripts/run_skill_evals.py
python -m pytest -q
```

Live provider smoke tests are manual only:

```bash
TRADEFLOW_PLANNER_PROVIDER=llm \
TRADEFLOW_LLM_PROVIDER=<provider> \
TRADEFLOW_LLM_MODEL=<model> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
python scripts/run_planner.py "Analyze sales order SO-1005" --show-trace
```

Manual smoke tests must not be required for CI because they depend on local secrets, network availability, and provider behavior outside the deterministic repository contract. They are useful for checking provider configuration and adapter compatibility, not for replacing planner golden evals or skill trigger evals.

## Sprint 8 Provider Smoke Evals

Sprint 8 smoke cases live in `evals/llm_provider_smoke_cases.json`. They cover:

- normal low-risk planning
- high-risk order requiring pending approval
- unavailable evidence that must not be hallucinated
- unsafe approval-bypass or execution request
- ambiguous request requiring clarification or safe fallback

The smoke runner validates structural and policy behavior rather than exact prose:

- planner output parses into existing contracts
- provider metadata is emitted
- fallback metadata is emitted when fallback is used
- cited evidence remains grounded
- unsafe actions are not approved
- approval gates stay pending for workflow recommendations
- missing-evidence and blocked cases do not cite invented workflow evidence

Default smoke behavior skips cleanly and makes no provider call:

```bash
python scripts/run_llm_provider_smoke.py
```

Fake provider modes are deterministic and safe for CI-style local checks:

```bash
python scripts/run_llm_provider_smoke.py --fake-provider success
python scripts/run_llm_provider_smoke.py --fake-provider invalid-json --max-cases 1
python scripts/run_llm_provider_smoke.py --fake-provider schema-violation --max-cases 1
python scripts/run_llm_provider_smoke.py --fake-provider timeout --max-cases 1
python scripts/run_llm_provider_smoke.py --fake-provider unsafe --max-cases 1
```

Live smoke requires explicit opt-in and local or staging credentials:

```bash
TRADEFLOW_LLM_SMOKE_ENABLED=true \
TRADEFLOW_LLM_PROVIDER=<provider> \
TRADEFLOW_LLM_MODEL=<model> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
python scripts/run_llm_provider_smoke.py --live --write-report
```

Non-secret provider values can also be supplied as `--provider`, `--model`, `--base-url`, and `--timeout-seconds`. API keys should stay in environment variables.

Reports are optional sanitized JSON files under `artifacts/provider_smoke/`, which is ignored by Git. Reports include dataset version, mode, pass/fail counts, provider metadata, case outcomes, fallback state, safety outcome, route, risk, approval state, and validation errors. API keys, auth headers, token-like values, and secret-bearing exception text are redacted before output.

Skip behavior exits zero when live smoke is disabled or credentials are missing. A configured live run exits non-zero only if one or more smoke cases fail. This keeps normal deterministic workflows stable while still giving local and staging runs a clear signal.

## Sprint 9 Unified Quality Gate

The unified gate runner is:

```bash
python scripts/run_agent_quality_gate.py
```

It runs the required local verification set:

- `python -m pytest -q`
- `python scripts/run_planner_evals.py`
- `python scripts/run_skill_evals.py`
- `python scripts/run_security_evals.py --quiet`
- `python scripts/run_approval_workflow_evals.py --quiet`
- `python scripts/check_capstone_readiness.py --quiet`
- `python scripts/run_llm_provider_smoke.py`

The default behavior continues after failures so the final report captures every gate outcome. Use `--stop-on-failure` to stop at the first failed gate.

Reports are written under:

```text
artifacts/quality_gate/
```

Use `--json-out PATH` to choose a stable report path, for example:

```bash
python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

The JSON report includes:

- schema version and timestamps
- total duration and per-command duration
- command status, return code, stdout, stderr, and required flag
- aggregate pass/fail/skip counts
- failure summaries
- runner options

All report payloads are passed through `app/agents/redaction.py` before writing, so API keys, auth headers, token-like values, and secret-bearing provider text are removed.

Provider smoke skip semantics are explicit:

- default quality gate: disabled or missing live provider credentials are recorded as `skipped` and the gate can still pass
- `--require-live-provider`: the runner invokes smoke with `--live`; if smoke skips because credentials or configuration are missing, the provider-smoke gate is converted to `failed` and the unified gate exits non-zero
- configured live smoke: exits non-zero only when the smoke harness reports failed cases

CI uses `.github/workflows/ci.yml` to install dependencies, run `python -m pytest -q`, and run `python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json`. Live provider smoke is not required by default. To enable it later, add repository secrets for `TRADEFLOW_LLM_PROVIDER`, `TRADEFLOW_LLM_MODEL`, and `TRADEFLOW_LLM_API_KEY`, set `TRADEFLOW_LLM_SMOKE_ENABLED=true`, and pass `--require-live-provider` in the workflow step.

## Sprint 10 Quality History and Release Evidence

The quality gate now writes timestamped history by default:

```bash
python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json
```

History files are stored under:

```text
artifacts/quality_gate/history/
```

Use `--no-history` for one-off runs that should only write the requested `--json-out` path. Use `--max-history N` to prune older history files after a run.

Trend summaries are generated from existing history reports:

```bash
python scripts/summarize_quality_history.py \
  --history-dir artifacts/quality_gate/history \
  --json-out artifacts/quality_gate/trend.json \
  --markdown-out artifacts/quality_gate/trend.md
```

The trend summary includes total runs considered, latest and previous status, status-change flag, pass/fail/skip deltas, duration delta, latest per-gate status, per-gate changes, passing/failing streaks, and malformed reports that were ignored.

Release evidence packs are generated from the latest quality report and optional history:

```bash
python scripts/build_release_evidence_pack.py \
  --quality-report artifacts/quality_gate/latest.json \
  --history-dir artifacts/quality_gate/history \
  --out-dir artifacts/release_evidence/latest
```

The pack writes machine-readable JSON and reviewer-readable Markdown. It records release name, generated timestamp, git branch and commit, dirty status, overall quality status, gate summary, counts, provider-smoke skip explanation, local reproduction commands, artifact inventory, known limitations, and next recommended action.

Generated artifacts stay ignored by Git:

```text
artifacts/quality_gate/
artifacts/release_evidence/
artifacts/capstone/
artifacts/security_evals/
artifacts/approval_workflow_evals/
artifacts/audit_trail/
```

CI writes `artifacts/quality_gate/latest.json`, builds the release evidence pack, and uploads quality/evidence artifacts. A failed gate still fails CI. Live provider smoke remains skipped by default unless credentials and `--require-live-provider` are explicitly configured.

## Sprint 11 Security Policy Evals

Sprint 11 security cases live in `evals/security_policy_cases.json`. They cover:

- allowed order-risk, finance, logistics, and approval-status requests
- prompt injection such as "ignore previous instructions"
- hidden-instruction requests such as "reveal system prompt"
- secrets exfiltration such as API keys, tokens, passwords, or supplier credentials
- broad data exfiltration such as exporting all customer data
- review-worthy scoped exports such as customer payment history
- destructive actions such as deleting records or disabling audit logging
- approval bypasses such as approving orders without risk review
- unsafe tool-use requests such as bypassing policy checks

Run them with:

```bash
python scripts/run_security_evals.py
```

Write a stable JSON report with:

```bash
python scripts/run_security_evals.py --json-out artifacts/security_evals/latest.json
```

Security evals are included in the unified quality gate because they are deterministic, offline-safe, and secrets-safe. Reports are written under `artifacts/security_evals/`, which is ignored by Git.

The Sprint 11 security model intentionally uses explicit rules rather than LLM-as-judge scoring. That keeps CI repeatable and makes each finding explainable through a finding id, severity, category, message, and matched evidence. Out of scope for this sprint: advanced semantic jailbreak detection, production policy servers, real data-loss-prevention integrations, live red-team automation, and any network-backed security service.

## Sprint 12 Approval Workflow Evals

Sprint 12 approval workflow cases live in `evals/approval_workflow_cases.json`. They cover:

- allowed business actions that should proceed without approval
- blocked prompt-injection and unsafe requests that must not create approval requests
- review-level sensitive exports that must create pending approval requests
- deterministic audit event sequences for policy checks, allowed actions, blocked actions, and approval requests

Run them with:

```bash
python scripts/run_approval_workflow_evals.py
```

Write a stable JSON report with:

```bash
python scripts/run_approval_workflow_evals.py --json-out artifacts/approval_workflow_evals/latest.json
```

Approval workflow evals are included in the unified quality gate because they are deterministic, offline-safe, and secrets-safe. Reports are written under `artifacts/approval_workflow_evals/`, which is ignored by Git.

The Sprint 12 workflow is an enforcement harness, not a production approval database. Approval requests and audit events are in-memory structures suitable for unit tests and local evidence generation. Runtime audit files, if later generated, must stay under ignored `artifacts/audit_trail/`.

## Sprint 13 Capstone Readiness and AgentOps Evidence

The capstone readiness checker is deterministic and offline-safe:

```bash
python scripts/check_capstone_readiness.py
```

It verifies that required docs exist under `docs/capstone/`, the Kaggle writeup draft is under 2,500 words, the demo script includes timing blocks, README mentions capstone and evaluation context, generated capstone artifacts are ignored, and committed capstone docs do not contain obvious secrets or local absolute paths.

AgentOps evidence artifacts are generated locally:

```bash
python scripts/build_agentops_evidence_index.py
python scripts/build_agentops_dashboard.py
```

The evidence index scans generated artifact folders for the latest quality gate result, security eval result, guardrail or approval workflow eval result, release evidence pack, and optional quality history summary. Missing optional evidence produces warnings rather than failures. The static dashboard reads that JSON and writes dependency-free HTML under `artifacts/capstone/`.

This fits with Sprint 10 quality history and release evidence by adding a reviewer-facing index over the same ignored artifact ecosystem. The release evidence pack now includes capstone evidence paths when the AgentOps index or dashboard has already been generated.
