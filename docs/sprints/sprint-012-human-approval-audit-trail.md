# Sprint 012 - Human Approval Workflow, Guardrail Enforcement, and Audit Trail

## Objective

Sprint 012 makes Sprint 011 security policy decisions operational inside deterministic business workflows. Unsafe actions are blocked, review-level actions create human approval requests, and every path emits JSON-safe audit events.

The sprint remains offline-safe, CI-safe, and secrets-safe. It does not call external APIs, require live model credentials, or write audit events to external systems.

## Implemented Files

- `app/agents/guardrail_enforcement.py` maps policy decisions to `allowed`, `blocked`, or `requires_approval` enforcement outcomes.
- `app/agents/human_approval.py` defines in-memory approval requests, approval decisions, status transitions, and role mapping.
- `app/agents/audit_trail.py` defines deterministic audit events, append/export helpers, correlation ids, and redacted metadata export.
- `app/agents/secure_workflow.py` runs policy, enforcement, approval request creation, and audit event creation end to end.
- `app/agents/secure_workflow.py` also exposes a helper for deterministic approval-approved and approval-rejected audit events.
- `evals/approval_workflow_cases.json` contains the Sprint 012 deterministic approval workflow eval dataset.
- `scripts/run_approval_workflow_evals.py` runs the dataset and writes reports under `artifacts/approval_workflow_evals/`.
- `scripts/build_release_evidence_pack.py` surfaces the approval workflow eval gate in generated release evidence when it appears in the latest quality report.
- `tests/test_sprint_012_human_approval_audit_trail.py` covers enforcement, approval transitions, blocked-action protection, audit events, redaction, eval reporting, and ignored artifact paths.

## Enforcement Model

Policy decisions are enforced as follows:

- `allow` becomes `allowed`.
- `block` becomes `blocked`.
- `review` becomes `requires_approval`.

High-risk categories are handled deterministically:

- `secrets_exfiltration`, `prompt_injection`, and `instruction_override` are blocked.
- `unauthorized_financial_action`, `destructive_operation`, `data_leakage`, and approval-bypass categories require explicit approval unless the policy has already blocked the action.

## Approval Roles

Approval requests remain in memory and are intended for unit tests and deterministic workflow simulations. Role mapping is:

- Unauthorized financial action: `risk_manager`
- Destructive operation: `admin`
- Data leakage or secrets exfiltration: `security_reviewer`
- Prompt injection or instruction override: `security_reviewer`
- Approval bypass: `risk_manager`

Blocked actions cannot be converted into approval requests. Pending requests can be approved or rejected once; repeated decisions raise an error.

## Audit Trail

Audit event types are:

- `policy_checked`
- `action_allowed`
- `action_blocked`
- `approval_requested`
- `approval_approved`
- `approval_rejected`
- `enforcement_failed`

Audit events include stable ids, actor, action, decision/outcome, categories, finding ids, timestamp, correlation id, and metadata. Exported audit dictionaries pass through the shared redaction helper before serialization.

## Quality Gate Integration

The unified quality gate now runs:

- pytest
- planner evals
- skill evals
- security evals
- approval workflow evals
- provider smoke

Approval workflow evals run by default because they are deterministic and offline-safe. Runtime reports remain under ignored `artifacts/` paths.

## Verification Commands

```bash
python scripts/run_approval_workflow_evals.py
python scripts/run_agent_quality_gate.py
pytest -q
```
