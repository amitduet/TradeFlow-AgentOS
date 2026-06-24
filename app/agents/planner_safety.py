"""Safety checks for constrained planner execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agents.planner_contracts import (
    EvidenceCitation,
    GroundedResponse,
    PlannerDecision,
    PlannerSafetyCheck,
)
from app.agents.workflow_contracts import OrderRiskWorkflowResult


APPROVED_WORKFLOWS = {"analyze_sales_order_risk"}
DETERMINISTIC_TOOL_FIELD_PREFIXES = (
    "risk_level",
    "risk_flags",
    "margin_summary",
    "logistics_summary",
    "drop_shipping_summary",
    "customer_summary",
    "order_summary",
)


def run_planner_safety_checks(
    *,
    decision: PlannerDecision,
    workflow_result: OrderRiskWorkflowResult | None,
    grounded_response: GroundedResponse,
    dataset_path: str | Path | None,
    dataset_hash_before: str | None,
    dataset_hash_after: str | None,
) -> list[PlannerSafetyCheck]:
    """Validate planner output against the Sprint 4 safety contract."""
    return [
        _check_sales_order_id(decision),
        _check_workflow_allowlist(decision),
        _check_approval_required(workflow_result),
        _check_approval_pending(workflow_result),
        _check_grounding(workflow_result, grounded_response),
        _check_dataset_not_mutated(dataset_path, dataset_hash_before, dataset_hash_after),
    ]


def safety_checks_passed(checks: list[PlannerSafetyCheck]) -> bool:
    return all(check.passed for check in checks)


def _check_sales_order_id(decision: PlannerDecision) -> PlannerSafetyCheck:
    passed = bool(decision.extracted_sales_order_id)
    return PlannerSafetyCheck(
        check_name="recognizable_sales_order_id",
        passed=passed,
        reason=(
            f"Extracted {decision.extracted_sales_order_id}."
            if passed
            else "No recognizable sales order id was extracted."
        ),
    )


def _check_workflow_allowlist(decision: PlannerDecision) -> PlannerSafetyCheck:
    passed = decision.selected_workflow in APPROVED_WORKFLOWS
    return PlannerSafetyCheck(
        check_name="approved_workflow_selected",
        passed=passed,
        reason=(
            f"Selected workflow {decision.selected_workflow} is approved."
            if passed
            else f"Selected workflow {decision.selected_workflow!r} is not in the approved allowlist."
        ),
    )


def _check_approval_required(workflow_result: OrderRiskWorkflowResult | None) -> PlannerSafetyCheck:
    passed = bool(workflow_result and workflow_result.approval_required is True)
    return PlannerSafetyCheck(
        check_name="workflow_requires_approval",
        passed=passed,
        reason=(
            "Workflow result requires approval."
            if passed
            else "Workflow result is missing or does not require approval."
        ),
    )


def _check_approval_pending(workflow_result: OrderRiskWorkflowResult | None) -> PlannerSafetyCheck:
    status = workflow_result.approval_request.status if workflow_result else None
    passed = status == "pending"
    return PlannerSafetyCheck(
        check_name="approval_request_pending",
        passed=passed,
        reason=(
            "Approval request status is pending."
            if passed
            else f"Approval request status is {status!r}, expected 'pending'."
        ),
    )


def _check_grounding(
    workflow_result: OrderRiskWorkflowResult | None,
    grounded_response: GroundedResponse,
) -> PlannerSafetyCheck:
    if workflow_result is None:
        passed = not grounded_response.cited_evidence
        return PlannerSafetyCheck(
            check_name="grounded_response_supported",
            passed=passed,
            reason=(
                "No workflow result was produced and the response cites no unsupported evidence."
                if passed
                else "Response cites evidence despite no workflow result."
            ),
        )

    errors = [
        error
        for citation in grounded_response.cited_evidence
        if (error := _citation_error(workflow_result, citation)) is not None
    ]
    return PlannerSafetyCheck(
        check_name="grounded_response_supported",
        passed=not errors,
        reason="All cited evidence resolves to workflow, deterministic tool, or approval outputs."
        if not errors
        else "; ".join(errors),
    )


def _check_dataset_not_mutated(
    dataset_path: str | Path | None,
    dataset_hash_before: str | None,
    dataset_hash_after: str | None,
) -> PlannerSafetyCheck:
    if dataset_hash_before is None or dataset_hash_after is None:
        return PlannerSafetyCheck(
            check_name="source_dataset_not_mutated",
            passed=True,
            reason=f"No source dataset hash was available for {dataset_path!r}; mutation check skipped.",
        )
    passed = dataset_hash_before == dataset_hash_after
    return PlannerSafetyCheck(
        check_name="source_dataset_not_mutated",
        passed=passed,
        reason="Source dataset hash is unchanged."
        if passed
        else "Source dataset hash changed during planner execution.",
    )


def _citation_error(
    workflow_result: OrderRiskWorkflowResult,
    citation: EvidenceCitation,
) -> str | None:
    if citation.source_type == "approval_gate":
        source: Any = workflow_result.approval_request
    elif citation.source_type == "workflow_output":
        source = workflow_result
    elif citation.source_type == "deterministic_tool_output":
        if not citation.field_path.startswith(DETERMINISTIC_TOOL_FIELD_PREFIXES):
            return f"{citation.field_path!r} is not an allowed deterministic tool-derived field"
        source = workflow_result
    else:
        return f"{citation.source_type!r} is not an allowed evidence source"

    try:
        actual = _resolve_field_path(source, citation.field_path)
    except (AttributeError, KeyError, IndexError, ValueError, TypeError) as exc:
        return f"{citation.field_path!r} could not be resolved: {exc}"
    if actual != citation.value:
        return f"{citation.field_path!r} value {citation.value!r} does not match source value {actual!r}"
    return None


def _resolve_field_path(source: Any, field_path: str) -> Any:
    current = source
    for part in field_path.split("."):
        if not part:
            raise ValueError("empty field path segment")
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            current = getattr(current, part)
    return current
