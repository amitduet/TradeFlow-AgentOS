# Evaluation

TradeFlow AgentOS uses deterministic evaluation before agentic evaluation. Sprint 2 focuses on proving that local tools can retrieve and validate synthetic business data without LLM calls, network access, or production systems.

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

Run all tests with:

```bash
pytest
```

## Future Agent Evaluation

Future sprints can add LLM-agent evals on top of this deterministic foundation. Those evals should verify that agents call these tools, cite returned synthetic facts, respect human approval gates, and avoid inventing hidden production state.
