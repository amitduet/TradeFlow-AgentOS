# Evaluation

TradeFlow AgentOS uses deterministic evaluation before agentic evaluation. Sprint 2 focuses on proving that local tools can retrieve and validate synthetic business data without LLM calls, network access, or production systems.

Sprint 3 extends deterministic evaluation to the first agent-facing workflow. The workflow still has no LLM planner: evals verify that the orchestrator calls approved tools, produces typed recommendations, opens approval gates, and leaves the source dataset unchanged.

Sprint 5 adds constrained-planner evaluation before live LLM integration. Planner evals verify route selection, recommended action, approval state, risk level, safety outcome, refusal or escalation behavior, and reason-code coverage against a versioned golden dataset.

Sprint 6 adds deterministic skill trigger evaluation before live LLM integration. Skill evals verify that business-domain skill files trigger on supported requests, avoid wrong-skill matches on negative requests, and route approval-bypass phrasing to approval-gate handling rather than procurement execution.

Sprint 7 adds mocked real-provider integration tests before any live provider is required in CI. These tests verify strict JSON schema validation, rejection of unsafe provider output, deterministic fallback, provider metadata in trace and audit records, and preservation of planner and skill eval pass rates without LLM credentials.

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
