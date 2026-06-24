# Sprint 011 - Agent Security Guardrails

## Objective

Sprint 011 adds a deterministic security assurance layer for TradeFlow AgentOS. The layer checks agent-facing requests for prompt injection, unsafe tool use, secrets exfiltration, approval bypasses, broad data leakage, and destructive operations before future live-provider behavior can depend on more advanced security evaluation.

The sprint remains offline-safe, CI-safe, and secrets-safe. It does not call external APIs, require live model credentials, or introduce production data-loss-prevention integrations.

## Implemented Files

- `app/agents/security_policy.py` defines the policy decision model, finding/result structures, checked categories, and deterministic rule matching.
- `evals/security_policy_cases.json` contains the versioned Sprint 011 security eval dataset.
- `scripts/run_security_evals.py` runs the dataset, prints a concise summary, exits non-zero on failures, and writes JSON reports under `artifacts/security_evals/`.
- `scripts/run_agent_quality_gate.py` now includes `security_evals` as a first-class deterministic gate.
- `tests/test_sprint_011_agent_security_guardrails.py` covers policy behavior, eval reporting, quality gate integration, provider-smoke skip behavior, and artifact ignore paths.

## Security Categories

The policy checks these categories:

- `prompt_injection`
- `secrets_exfiltration`
- `unsafe_tool_request`
- `unauthorized_financial_action`
- `instruction_override`
- `data_leakage`
- `destructive_operation`

Rules are intentionally small, explicit, and explainable. Each finding records a stable finding id, severity, category, message, and matched evidence.

## Decision Model

Policy decisions are:

- `allow`: no policy findings were matched.
- `review`: one or more review-worthy findings were matched, but no blocking finding was matched.
- `block`: one or more blocking findings were matched.

Blocking findings take priority over review findings. For example, a request that both asks for a payment-history export and says "ignore previous instructions" is blocked.

## Eval Dataset Design

The dataset includes allowed business workflows, clear blocked cases, and review cases. Coverage includes prompt-injection attempts, tool misuse, financial approval bypasses, data exfiltration, destructive operations, and normal order-risk requests that should pass.

Run the security evals with:

```bash
.venv/bin/python scripts/run_security_evals.py
```

Useful options:

```bash
.venv/bin/python scripts/run_security_evals.py --json-out artifacts/security_evals/latest.json
.venv/bin/python scripts/run_security_evals.py --quiet
.venv/bin/python scripts/run_security_evals.py --fail-on-review
```

The default behavior allows expected `review` cases to pass. Use `--fail-on-review` when a release process wants any review decision to require manual follow-up.

## Quality Gate Integration

The unified quality gate now runs:

- pytest
- planner evals
- skill evals
- security evals
- provider smoke

Security evals run by default because they are deterministic and offline-safe. Provider smoke remains opt-in for live providers and still skips cleanly by default when credentials are not configured.

Run the full gate with:

```bash
.venv/bin/python scripts/run_agent_quality_gate.py
```

## Limitations

This sprint is a deterministic guardrail layer, not a complete production security system. It intentionally does not implement:

- advanced LLM-as-judge security evaluation
- production policy servers
- real data-loss-prevention integrations
- live red-team automation
- semantic jailbreak detection beyond explicit rule patterns
- network or live-provider security checks by default

Future work can add deeper classifiers or policy services, but those should remain opt-in until they are deterministic enough for CI or clearly separated from CI-only checks.

## Verification Commands

```bash
.venv/bin/python scripts/run_security_evals.py
.venv/bin/python scripts/run_agent_quality_gate.py
.venv/bin/pytest -q
```
