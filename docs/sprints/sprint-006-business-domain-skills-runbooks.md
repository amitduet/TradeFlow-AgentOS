# Sprint 006: Business Domain Skills and Runbooks

## Objective

Sprint 006 converts TradeFlow business knowledge into reusable, explainable runbooks and domain skill files before introducing any real LLM provider. The sprint keeps all existing deterministic safety behavior intact: no external APIs, no live LLM calls, no web UI, and no approval-gate bypass.

## What Changed

- Added business-readable runbooks under `domain/runbooks/`.
- Added focused skill definitions under `skills/`.
- Added a skill catalog at `skills/SKILL_CATALOG.md`.
- Added deterministic skill metadata and trigger helpers in `app/agents/domain_skills.py`.
- Added versioned trigger eval cases in `evals/sprint_006_skill_trigger_cases.json`.
- Added `scripts/run_skill_evals.py` and `scripts/list_domain_skills.py`.
- Added pytest coverage in `tests/test_sprint_006_domain_skills_runbooks.py`.

## Runbooks

The runbooks make business policy explicit and reviewable:

- `order-risk-rules.md`
- `purchase-order-recommendation-rules.md`
- `approval-gate-rules.md`
- `customer-risk-rules.md`
- `supplier-risk-rules.md`
- `logistics-risk-rules.md`

Each runbook covers purpose, usage, required inputs, risk indicators, decision rules, required evidence, approval requirements, refusal or escalation conditions, and examples.

## Skills

Sprint 006 skills describe when business knowledge should trigger and what a planner may or may not do:

- `order-risk-analysis`
- `purchase-order-recommendation`
- `approval-gate-handling`

Skills include YAML frontmatter for name, description, version, owner, allowed actions, disallowed actions, related runbooks, trigger phrases, and negative trigger phrases. The body explains process steps, required outputs, safety constraints, and expected behavior.

## How Skills Differ From Planner Code

Planner code executes deterministic routing and approved workflows. Skills are versioned business knowledge artifacts: they define trigger boundaries, required evidence, and safety constraints in a form that future LLM providers can consume or be evaluated against.

Sprint 006 does not add a runtime skill engine. The helper module only loads metadata, validates required fields, lists available skills, and performs simple phrase-based matching for deterministic evals.

## Skill Evals

Run:

```bash
python scripts/run_skill_evals.py
```

The runner reports:

- trigger accuracy for positive cases
- negative trigger accuracy
- per-skill pass rates
- overall pass rate

The dataset includes positive and negative cases for each Sprint 006 skill. Approval-bypass phrasing must route to `approval-gate-handling`, not purchase order execution.

## Explainability and Safety

Runbooks improve explainability by making reason-code policy and required evidence explicit. Skills improve safety by defining negative triggers, disallowed actions, and approval behavior up front. Approval-gate handling remains authoritative and non-optional.

## Known Limitations

- Trigger matching is deterministic phrase matching, not semantic retrieval.
- Skills do not execute workflows or business actions.
- Runbook references are documentation-level links; they are not yet injected into a live provider prompt.
- The system still uses the Sprint 004/005 rule-based planner by default.

## Verification

```bash
python scripts/run_skill_evals.py
pytest tests/test_sprint_006_domain_skills_runbooks.py -q
python scripts/run_planner_evals.py
pytest -q
```

## Recommended Next Sprint

Sprint 007 should integrate a real LLM provider behind the existing provider abstraction while preserving the same constraints: deterministic tool grounding, approval gates, structured traces, JSONL audit logs, planner golden evals, skill trigger evals, and runbook-backed domain rules.
