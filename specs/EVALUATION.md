# Evaluation

TradeFlow AgentOS uses deterministic evaluation before agentic evaluation. Sprint 2 focuses on proving that local tools can retrieve and validate synthetic business data without LLM calls, network access, or production systems.

Sprint 3 extends deterministic evaluation to the first agent-facing workflow. The workflow still has no LLM planner: evals verify that the orchestrator calls approved tools, produces typed recommendations, opens approval gates, and leaves the source dataset unchanged.

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
