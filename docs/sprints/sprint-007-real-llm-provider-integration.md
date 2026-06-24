# Sprint 007 Real LLM Provider Integration

## Objective

Integrate a real LLM provider behind the constrained planner provider abstraction while preserving deterministic tests, typed contracts, safety checks, traces, audit records, planner evals, skill evals, domain runbooks, and approval gates.

## Provider Selection

Planner provider selection is environment-driven and can be overridden by the planner CLI.

```bash
TRADEFLOW_PLANNER_PROVIDER=deterministic  # deterministic|mock|llm
TRADEFLOW_LLM_PROVIDER=openai             # openai|gemini|custom
TRADEFLOW_LLM_MODEL=
TRADEFLOW_LLM_API_KEY=
TRADEFLOW_LLM_BASE_URL=
TRADEFLOW_LLM_TIMEOUT_SECONDS=30
```

The default is deterministic. Unit tests, CI, planner evals, and skill evals do not require network access or live credentials.

## LLM Provider Adapter

`app/agents/llm_provider.py` adds a minimal provider adapter for OpenAI-compatible APIs, Gemini-style `generateContent`, and custom OpenAI-compatible base URLs. The adapter is only used when `TRADEFLOW_PLANNER_PROVIDER=llm`, `--provider llm`, or the planner is called with an explicit LLM provider selection.

Tests inject mocked response clients, so no real provider is called in automated verification.

## Strict Output Schema

The LLM must return strict JSON containing only planner-compatible fields:

- `resolved_intent`
- `selected_route`
- `recommended_action`
- `risk_level`
- `approval_state`
- `safety_outcome`
- `reason_codes`
- `evidence_references`
- `response_summary`
- `refusal_reason`
- `escalation_reason`
- optional `extracted_sales_order_id`
- optional `confidence`

Validation rejects unknown JSON fields, missing required fields, invalid enum values, unsupported routes, unsafe actions, approval-bypass terms, tool execution claims, and evidence references not present in the prompt context.

## Skills and Runbook Context

The LLM prompt is compact by design. It includes:

- the user request
- the deterministically matched skill, if one matches
- concise snippets from that skill's related runbooks
- approved planner routes
- allowed recommendation labels
- disallowed business actions
- approval-gate constraints
- the required output schema

The planner does not blindly inject every runbook into every prompt.

## Safe Fallback

If the LLM provider fails, times out, returns malformed JSON, returns unsafe content, references ungrounded evidence, or violates planner contracts, the planner falls back to the deterministic provider. Fallback state is exposed in:

- `PlannerRunMetadata`
- `PlannerTrace`
- `PlannerAuditRecord`
- `scripts/run_planner.py` output

Provider metadata fields:

- `provider_requested`
- `provider_used`
- `fallback_used`
- `fallback_reason`
- `llm_response_valid`
- `llm_validation_errors`

## Approval Gate Authority

The LLM may recommend review, escalation, draft preparation, requiring approval, or refusal. It may not approve, execute, bypass approval, modify customer credit, modify supplier terms, execute payments, or update real inventory. Any output implying those actions is rejected and converted to deterministic fallback.

Workflow execution remains limited to the allowlisted deterministic `analyze_sales_order_risk` route, and any recommended business action remains behind a pending human approval request.

## Verification

```bash
.venv/bin/pytest tests/test_sprint_007_llm_provider_integration.py -q
.venv/bin/python scripts/run_planner_evals.py
.venv/bin/python scripts/run_skill_evals.py
.venv/bin/pytest -q
```

Manual smoke test, only with local credentials:

```bash
TRADEFLOW_PLANNER_PROVIDER=llm \
TRADEFLOW_LLM_PROVIDER=<provider> \
TRADEFLOW_LLM_MODEL=<model> \
TRADEFLOW_LLM_API_KEY=<local-secret> \
.venv/bin/python scripts/run_planner.py "Analyze sales order SO-1005" --show-trace
```

Or:

```bash
.venv/bin/python scripts/run_llm_provider_smoke.py
```

## Known Limitations

- The live provider adapter is intentionally minimal and does not stream responses.
- The LLM path only plans routing output; deterministic workflow code still supplies business evidence and approval requests.
- CI does not run live-provider smoke tests.
- Provider-specific behavior should be checked manually with local credentials.
- Prompt context uses deterministic skill matching and compact runbook snippets, not a full retrieval engine.

## Next Sprint Recommendation

Add a secrets-enabled local or staging smoke-eval harness for selected providers, capture provider compatibility snapshots, and expand prompt evaluation without making live providers mandatory for CI.
