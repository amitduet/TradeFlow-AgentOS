"""Constrained planner facade for LLM-ready, tool-grounded order-risk workflows."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.agents.llm_provider import ConfiguredLLMPlannerProvider, LLMProviderError, PROHIBITED_ACTION_TERMS
from app.agents.order_risk_orchestrator import analyze_sales_order_risk
from app.agents.planner_contracts import (
    EvidenceCitation,
    GroundedResponse,
    PlannerDecision,
    PlannerExecutionResult,
    PlannerInput,
    PlannerRunMetadata,
    PlannerSafetyOutcome,
    PlannerTrace,
    PlannerToolCall,
)
from app.agents.planner_audit import append_planner_audit_record, create_planner_audit_record
from app.agents.planner_safety import (
    APPROVED_WORKFLOWS,
    run_planner_safety_checks,
    safety_checks_passed,
)
from app.tools.tradeflow_tools import DEFAULT_DATASET_PATH


ORDER_ID_PATTERN = re.compile(r"\bSO-\d+\b", re.IGNORECASE)
SUPPORTED_REQUEST_TERMS = {
    "analyze",
    "analysis",
    "check",
    "risk",
    "proceed",
    "issue",
    "drop-shipping",
    "drop shipping",
    "recommendation",
    "recommend",
    "sales order",
    "business recommendation",
}
PLANNER_VERSION = "sprint-005-constrained-planner-v1"
PROMPT_TEMPLATE_VERSION = "order-risk-planner-prompt-v1"
PROVIDER_NAME = "tradeflow-rule-planner"
DETERMINISTIC_PROVIDER_SELECTIONS = {"deterministic", "rule_based", "rule-based"}
SUPPORTED_PROVIDER_SELECTIONS = {*DETERMINISTIC_PROVIDER_SELECTIONS, "mock", "llm"}


class PlannerProvider(Protocol):
    """Provider abstraction for future LLM planners and test doubles."""

    def decide(self, planner_input: PlannerInput) -> PlannerDecision:
        """Return a constrained planner decision without executing tools."""


@dataclass(frozen=True)
class PlannerProviderExecution:
    requested: str
    used: str
    provider_mode: str
    provider_name: str
    fallback_used: bool = False
    fallback_reason: str | None = None
    llm_response_valid: bool | None = None
    llm_validation_errors: list[str] | None = None


def plan_and_execute_user_request(
    user_request: str,
    dataset_path: str | None = None,
    use_llm: bool = False,
    *,
    llm_provider: PlannerProvider | None = None,
    planner_provider_selection: str | None = None,
    approval_storage_path: str | Path | None = None,
    audit_log_path: str | Path | None = None,
    evaluation_dataset_version: str | None = None,
) -> PlannerExecutionResult:
    """Plan a business request, execute the allowlisted workflow, and ground the answer."""
    planner_input = PlannerInput(
        user_request=user_request,
        dataset_path=dataset_path,
        use_llm=use_llm,
    )
    resolved_dataset_path = str(Path(dataset_path)) if dataset_path is not None else str(DEFAULT_DATASET_PATH)
    dataset_hash_before = _sha256_if_exists(resolved_dataset_path)

    decision, provider_execution = _make_planner_decision(
        planner_input,
        llm_provider,
        planner_provider_selection=planner_provider_selection,
    )
    metadata = _build_metadata(
        provider_execution=provider_execution,
        evaluation_dataset_version=evaluation_dataset_version,
    )
    workflow_result = None
    tool_call_trace: list[PlannerToolCall] = []
    error: str | None = None

    if _decision_can_execute(decision):
        try:
            workflow_result = analyze_sales_order_risk(
                sales_order_id=decision.extracted_sales_order_id or "",
                dataset_path=resolved_dataset_path,
                approval_storage_path=approval_storage_path,
            )
            tool_call_trace = [
                PlannerToolCall(
                    tool_name=call.tool_name,
                    input=call.input,
                    success=call.success,
                    output_summary=call.output_summary,
                    error=call.error,
                )
                for call in workflow_result.tool_call_trace
            ]
        except Exception as exc:
            error = f"Workflow execution failed: {exc}"
    elif decision.requires_clarification:
        error = decision.clarification_question
    else:
        error = decision.reason

    grounded_response = (
        _build_grounded_response(workflow_result)
        if workflow_result is not None
        else _build_blocked_response(decision, error)
    )
    dataset_hash_after = _sha256_if_exists(resolved_dataset_path)
    safety_checks = run_planner_safety_checks(
        decision=decision,
        workflow_result=workflow_result,
        grounded_response=grounded_response,
        dataset_path=resolved_dataset_path,
        dataset_hash_before=dataset_hash_before,
        dataset_hash_after=dataset_hash_after,
    )
    success = workflow_result is not None and error is None and safety_checks_passed(safety_checks)
    reason_codes = _collect_reason_codes(decision, workflow_result, safety_checks, error)
    safety_outcome = _determine_safety_outcome(
        decision=decision,
        workflow_result=workflow_result,
        success=success,
        error=error,
    )
    trace = PlannerTrace(
        planner_version=metadata.planner_version,
        prompt_version=metadata.prompt_template_version,
        provider_type=metadata.provider_mode,
        provider_name=metadata.provider_name,
        user_request=user_request,
        resolved_intent=decision.intent,
        selected_route=decision.selected_workflow,
        tool_context_references_used=[call.tool_name for call in tool_call_trace],
        risk_level=workflow_result.risk_level if workflow_result else None,
        recommended_action=workflow_result.recommended_action.action_type if workflow_result else None,
        approval_state=workflow_result.approval_request.status if workflow_result else None,
        safety_checks=safety_checks,
        safety_outcome=safety_outcome,
        reason_codes=reason_codes,
        final_response_summary=grounded_response.summary,
        errors=[] if success else [error or _safety_error(safety_checks) or "Planner execution did not succeed."],
        fallback_behavior=_fallback_behavior(decision, error, safety_outcome),
        provider_requested=provider_execution.requested,
        provider_used=provider_execution.used,
        fallback_used=provider_execution.fallback_used,
        fallback_reason=provider_execution.fallback_reason,
        llm_response_valid=provider_execution.llm_response_valid,
        llm_validation_errors=provider_execution.llm_validation_errors or [],
    )
    audit_record = create_planner_audit_record(
        decision=decision,
        workflow_result=workflow_result,
        grounded_response=grounded_response,
        trace=trace,
        safety_outcome=safety_outcome,
    )
    append_planner_audit_record(audit_record, storage_path=audit_log_path)

    return PlannerExecutionResult(
        user_request=user_request,
        planner_metadata=metadata,
        planner_decision=decision,
        workflow_result=workflow_result,
        grounded_response=grounded_response,
        safety_checks=safety_checks,
        safety_outcome=safety_outcome,
        trace=trace,
        audit_record=audit_record,
        approval_request=workflow_result.approval_request if workflow_result else None,
        tool_call_trace=tool_call_trace,
        success=success,
        error=None if success else error or _safety_error(safety_checks),
    )


def _build_metadata(
    *,
    provider_execution: PlannerProviderExecution,
    evaluation_dataset_version: str | None,
) -> PlannerRunMetadata:
    return PlannerRunMetadata(
        planner_version=PLANNER_VERSION,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        provider_name=provider_execution.provider_name,
        provider_mode=provider_execution.provider_mode,  # type: ignore[arg-type]
        evaluation_dataset_version=evaluation_dataset_version,
        provider_requested=provider_execution.requested,
        provider_used=provider_execution.used,
        fallback_used=provider_execution.fallback_used,
        fallback_reason=provider_execution.fallback_reason,
        llm_response_valid=provider_execution.llm_response_valid,
        llm_validation_errors=provider_execution.llm_validation_errors or [],
    )


def _make_planner_decision(
    planner_input: PlannerInput,
    llm_provider: PlannerProvider | None,
    *,
    planner_provider_selection: str | None,
) -> tuple[PlannerDecision, PlannerProviderExecution]:
    requested = _resolve_provider_selection(
        use_llm=planner_input.use_llm,
        llm_provider=llm_provider,
        planner_provider_selection=planner_provider_selection,
    )
    if requested not in SUPPORTED_PROVIDER_SELECTIONS:
        fallback_reason = f"Unsupported planner provider {requested!r}; using deterministic provider."
        return _fallback_decision(
            planner_input,
            requested=requested,
            fallback_reason=fallback_reason,
            validation_errors=[fallback_reason],
        )

    if requested in DETERMINISTIC_PROVIDER_SELECTIONS:
        return (
            _rule_based_decision(planner_input.user_request),
            PlannerProviderExecution(
                requested="deterministic",
                used="deterministic",
                provider_mode="rule_based",
                provider_name=PROVIDER_NAME,
            ),
        )

    provider = llm_provider
    if requested == "llm" and provider is None:
        provider = ConfiguredLLMPlannerProvider()
    if requested == "mock" and provider is None:
        fallback_reason = "Mock planner provider was requested but no mock provider was supplied."
        return _fallback_decision(
            planner_input,
            requested=requested,
            fallback_reason=fallback_reason,
            validation_errors=[fallback_reason],
        )

    assert provider is not None
    try:
        decision = _normalize_provider_decision(provider.decide(planner_input), planner_input.user_request)
        validation_errors = _provider_decision_errors(decision)
        if validation_errors:
            return _fallback_decision(
                planner_input,
                requested=requested,
                fallback_reason="Planner provider decision violated planner constraints.",
                validation_errors=validation_errors,
            )
    except LLMProviderError as exc:
        return _fallback_decision(
            planner_input,
            requested=requested,
            fallback_reason=str(exc),
            validation_errors=exc.validation_errors,
        )
    except Exception as exc:
        return _fallback_decision(
            planner_input,
            requested=requested,
            fallback_reason=f"Planner provider failed safely: {exc}",
            validation_errors=[str(exc)],
        )

    return (
        decision,
        PlannerProviderExecution(
            requested=requested,
            used=requested,
            provider_mode="llm" if requested == "llm" else "mocked",
            provider_name=type(provider).__name__,
            llm_response_valid=True if requested == "llm" else None,
            llm_validation_errors=[],
        ),
    )


def _resolve_provider_selection(
    *,
    use_llm: bool,
    llm_provider: PlannerProvider | None,
    planner_provider_selection: str | None,
) -> str:
    if planner_provider_selection:
        return planner_provider_selection.strip().lower()
    env_selection = os.getenv("TRADEFLOW_PLANNER_PROVIDER", "").strip().lower()
    if env_selection:
        return env_selection
    if use_llm and llm_provider is not None:
        return "mock"
    if use_llm:
        return "llm"
    return "deterministic"


def _fallback_decision(
    planner_input: PlannerInput,
    *,
    requested: str,
    fallback_reason: str,
    validation_errors: list[str],
) -> tuple[PlannerDecision, PlannerProviderExecution]:
    decision = _rule_based_decision(planner_input.user_request)
    return (
        decision.model_copy(
            update={"reason_codes": list(dict.fromkeys([*decision.reason_codes, "provider_fallback_used"]))}
        ),
        PlannerProviderExecution(
            requested=requested,
            used="deterministic",
            provider_mode="rule_based",
            provider_name=PROVIDER_NAME,
            fallback_used=True,
            fallback_reason=fallback_reason,
            llm_response_valid=False if requested == "llm" else None,
            llm_validation_errors=validation_errors,
        ),
    )


def _normalize_provider_decision(decision: PlannerDecision, user_request: str) -> PlannerDecision:
    sales_order_id = decision.extracted_sales_order_id or _extract_sales_order_id(user_request)
    return decision.model_copy(update={"extracted_sales_order_id": sales_order_id})


def _provider_decision_errors(decision: PlannerDecision) -> list[str]:
    errors: list[str] = []
    if decision.selected_workflow is not None and decision.selected_workflow not in APPROVED_WORKFLOWS:
        errors.append(f"selected_workflow {decision.selected_workflow!r} is not approved.")
    lowered_text = "\n".join(
        [
            decision.intent,
            decision.selected_workflow or "",
            decision.reason,
            decision.clarification_question or "",
            *decision.reason_codes,
        ]
    ).lower()
    for term in PROHIBITED_ACTION_TERMS:
        if term in lowered_text:
            errors.append(f"prohibited action term {term!r} appeared in provider decision.")
    return errors


def _rule_based_decision(user_request: str) -> PlannerDecision:
    sales_order_id = _extract_sales_order_id(user_request)
    unsafe_reason = _unsafe_request_reason(user_request)
    if unsafe_reason is not None:
        return PlannerDecision(
            intent="unsafe_request_refused",
            selected_workflow=None,
            extracted_sales_order_id=sales_order_id,
            confidence=1.0,
            requires_clarification=False,
            clarification_question=None,
            reason=unsafe_reason,
            reason_codes=["unsafe_approval_bypass", "approval_gate_authoritative"],
        )

    if sales_order_id is None:
        if _asks_for_purchase_order_creation(user_request):
            return PlannerDecision(
                intent="missing_order_context",
                selected_workflow=None,
                extracted_sales_order_id=None,
                confidence=1.0,
                requires_clarification=True,
                clarification_question=(
                    "I need a sales order id before recommending any purchase order action. "
                    "Provide an id like SO-1005."
                ),
                reason="Purchase order creation requires a concrete sales order context.",
                reason_codes=["missing_required_order_context", "approval_gate_authoritative"],
            )
        return PlannerDecision(
            intent="clarify_sales_order_id",
            selected_workflow=None,
            extracted_sales_order_id=None,
            confidence=1.0,
            requires_clarification=True,
            clarification_question="Which sales order id should I analyze? Use an id like SO-1005.",
            reason="The request does not contain a recognizable sales order id.",
            reason_codes=["missing_sales_order_id"],
        )

    unavailable_reason = _unavailable_data_reason(user_request)
    if unavailable_reason is not None:
        return PlannerDecision(
            intent="unavailable_data_refused",
            selected_workflow=None,
            extracted_sales_order_id=sales_order_id,
            confidence=0.9,
            requires_clarification=False,
            clarification_question=None,
            reason=unavailable_reason,
            reason_codes=["unavailable_or_confidential_data", "tool_grounding_required"],
        )

    unsupported_action_reason = _unsupported_business_action_reason(user_request)
    if unsupported_action_reason is not None:
        return PlannerDecision(
            intent="unsupported_request",
            selected_workflow=None,
            extracted_sales_order_id=sales_order_id,
            confidence=0.9,
            requires_clarification=False,
            clarification_question=None,
            reason=unsupported_action_reason,
            reason_codes=["unsupported_business_action", "approved_workflow_required"],
        )

    if not _is_supported_order_risk_request(user_request):
        if _is_ambiguous_order_request(user_request):
            return PlannerDecision(
                intent="ambiguous_request_escalated",
                selected_workflow=None,
                extracted_sales_order_id=sales_order_id,
                confidence=0.65,
                requires_clarification=True,
                clarification_question=(
                    "What business decision should I help with for this sales order: "
                    "risk analysis, action recommendation, or approval review?"
                ),
                reason="The request names a sales order but does not specify a supported business decision.",
                reason_codes=["ambiguous_request", "human_clarification_required"],
            )
        return PlannerDecision(
            intent="unsupported_request",
            selected_workflow=None,
            extracted_sales_order_id=sales_order_id,
            confidence=0.75,
            requires_clarification=False,
            clarification_question=None,
            reason=(
                "Sprint 4 supports only sales-order risk analysis and action recommendations "
                "through analyze_sales_order_risk."
            ),
            reason_codes=["unsupported_business_action", "approved_workflow_required"],
        )

    return PlannerDecision(
        intent="analyze_sales_order_risk",
        selected_workflow="analyze_sales_order_risk",
        extracted_sales_order_id=sales_order_id,
        confidence=0.95,
        requires_clarification=False,
        clarification_question=None,
        reason="Detected a sales-order risk or recommendation request and routed it to the approved workflow.",
        reason_codes=["approved_workflow_selected", "tool_grounding_required"],
    )


def _decision_can_execute(decision: PlannerDecision) -> bool:
    return (
        decision.extracted_sales_order_id is not None
        and decision.selected_workflow in APPROVED_WORKFLOWS
        and not decision.requires_clarification
    )


def _extract_sales_order_id(user_request: str) -> str | None:
    match = ORDER_ID_PATTERN.search(user_request)
    return match.group(0).upper() if match else None


def _is_supported_order_risk_request(user_request: str) -> bool:
    lowered = user_request.lower()
    return any(term in lowered for term in SUPPORTED_REQUEST_TERMS)


def _unsafe_request_reason(user_request: str) -> str | None:
    lowered = user_request.lower()
    bypass_terms = ("bypass approval", "skip approval", "without approval", "auto approve", "auto-approve")
    if any(term in lowered for term in bypass_terms):
        return (
            "I cannot bypass or weaken the approval gate. The next safe step is to run the approved "
            "risk workflow and leave any required approval in pending human review."
        )
    return None


def _asks_for_purchase_order_creation(user_request: str) -> bool:
    lowered = user_request.lower()
    return "purchase order" in lowered or "po" in lowered


def _unavailable_data_reason(user_request: str) -> str | None:
    lowered = user_request.lower()
    unavailable_terms = ("customer email", "confidential", "private", "secret", "contract terms")
    if any(term in lowered for term in unavailable_terms):
        return (
            "I cannot provide confidential or unavailable data that was not returned by the approved "
            "workflow context. The next safe step is to request a supported sales-order risk analysis."
        )
    return None


def _is_ambiguous_order_request(user_request: str) -> bool:
    lowered = user_request.lower()
    ambiguous_terms = ("help", "what should", "handle", "deal with", "do something")
    unsupported_action_terms = ("cancel", "refund", "ship", "invoice", "change price", "discount")
    return any(term in lowered for term in ambiguous_terms) and not any(
        _contains_business_action(lowered, term) for term in unsupported_action_terms
    )


def _unsupported_business_action_reason(user_request: str) -> str | None:
    lowered = user_request.lower()
    unsupported_action_terms = ("cancel", "refund", "ship", "invoice", "change price", "discount")
    if any(_contains_business_action(lowered, term) for term in unsupported_action_terms):
        return (
            "That business action is outside the approved Sprint 5 planner workflow. "
            "The next safe step is to request sales-order risk analysis or an action recommendation."
        )
    return None


def _contains_business_action(lowered_request: str, term: str) -> bool:
    if " " in term:
        return term in lowered_request
    return re.search(rf"\b{re.escape(term)}\b", lowered_request) is not None


def _build_grounded_response(workflow_result) -> GroundedResponse:
    action = workflow_result.recommended_action
    approval = workflow_result.approval_request
    flags = workflow_result.risk_flags
    flag_text = ", ".join(flags) if flags else "none"
    citations = [
        EvidenceCitation(
            source_type="workflow_output",
            field_path="sales_order_id",
            value=workflow_result.sales_order_id,
            explanation="Identifies the analyzed sales order.",
        ),
        EvidenceCitation(
            source_type="deterministic_tool_output",
            field_path="risk_level",
            value=workflow_result.risk_level,
            explanation="Risk level returned by the deterministic risk workflow.",
        ),
        EvidenceCitation(
            source_type="deterministic_tool_output",
            field_path="risk_flags",
            value=flags,
            explanation="Risk flags returned by deterministic tools and summarized by the workflow.",
        ),
        EvidenceCitation(
            source_type="workflow_output",
            field_path="recommended_action.action_type",
            value=action.action_type,
            explanation="Workflow-selected recommended action.",
        ),
        EvidenceCitation(
            source_type="workflow_output",
            field_path="recommended_action.priority",
            value=action.priority,
            explanation="Workflow-selected action priority.",
        ),
        EvidenceCitation(
            source_type="workflow_output",
            field_path="recommended_action.message",
            value=action.message,
            explanation="Workflow-grounded action explanation.",
        ),
        EvidenceCitation(
            source_type="approval_gate",
            field_path="status",
            value=approval.status,
            explanation="Approval gate status created for the proposed action.",
        ),
        EvidenceCitation(
            source_type="approval_gate",
            field_path="approval_id",
            value=approval.approval_id,
            explanation="Approval request id for human review.",
        ),
        EvidenceCitation(
            source_type="approval_gate",
            field_path="reason",
            value=approval.reason,
            explanation="Approval gate reason generated from workflow outputs.",
        ),
    ]
    return GroundedResponse(
        summary=(
            f"Sales order {workflow_result.sales_order_id} is {workflow_result.risk_level} risk. "
            f"The workflow recommends {action.action_type} and created a pending approval request."
        ),
        key_findings=[
            f"Order id: {workflow_result.sales_order_id}",
            f"Risk level: {workflow_result.risk_level}",
            f"Risk flags: {flag_text}",
            f"Approval request status: {approval.status}",
            f"Why: {approval.reason}",
        ],
        recommendation=f"{action.action_type} ({action.priority}): {action.message}",
        approval_status=approval.status,
        cited_evidence=citations,
    )


def _build_blocked_response(decision: PlannerDecision, error: str | None) -> GroundedResponse:
    message = error or decision.clarification_question or decision.reason
    return GroundedResponse(
        summary=message,
        key_findings=[],
        recommendation="No workflow was executed.",
        approval_status=None,
        cited_evidence=[],
    )


def _collect_reason_codes(
    decision: PlannerDecision,
    workflow_result,
    safety_checks,
    error: str | None,
) -> list[str]:
    codes = list(dict.fromkeys(decision.reason_codes))
    if workflow_result is not None:
        codes.extend(flag for flag in workflow_result.risk_flags if flag not in codes)
        codes.append(f"risk_{workflow_result.risk_level}")
        codes.append(f"action_{workflow_result.recommended_action.action_type}")
        if workflow_result.approval_required:
            codes.append("approval_required")
    if error and error.startswith("Workflow execution failed"):
        codes.append("workflow_execution_failed")
    for check in safety_checks:
        if not check.passed:
            codes.append(f"safety_failed_{check.check_name}")
    return list(dict.fromkeys(codes))


def _determine_safety_outcome(
    *,
    decision: PlannerDecision,
    workflow_result,
    success: bool,
    error: str | None,
) -> PlannerSafetyOutcome:
    if success:
        return "pass"
    if error and error.startswith("Workflow execution failed"):
        return "error"
    if decision.requires_clarification:
        return "escalated"
    if decision.intent in {"unsafe_request_refused", "unavailable_data_refused", "unsupported_request"}:
        return "refused"
    if workflow_result is None:
        return "blocked"
    return "error"


def _fallback_behavior(
    decision: PlannerDecision,
    error: str | None,
    safety_outcome: PlannerSafetyOutcome,
) -> str | None:
    if safety_outcome == "pass":
        return None
    if decision.requires_clarification:
        return decision.clarification_question
    if safety_outcome == "refused":
        return decision.reason
    return error


def _safety_error(safety_checks) -> str | None:
    failed = [check for check in safety_checks if not check.passed]
    if not failed:
        return None
    return "Safety checks failed: " + "; ".join(f"{check.check_name}: {check.reason}" for check in failed)


def _sha256_if_exists(path: str | Path) -> str | None:
    resolved = Path(path)
    if not resolved.exists() or not resolved.is_file():
        return None
    return hashlib.sha256(resolved.read_bytes()).hexdigest()
