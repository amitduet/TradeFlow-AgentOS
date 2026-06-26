"""Judge-facing TradeFlow AgentOS demo adapter.

This module keeps the demo surface thin: it validates end-user scenario input,
routes the request through the existing constrained planner, and reshapes the
grounded workflow output into a compact response for CLI and local UI demos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.agents.domain_skills import match_skill_for_request
from app.agents.llm_planner import plan_and_execute_user_request
from app.agents.redaction import redact_data


DemoWorkflowType = Literal[
    "sales_order_risk_review",
    "customer_order_risk_assessment",
    "supplier_logistics_payment_term_risk_analysis",
    "approval_required_decision_path",
]
RiskLevel = Literal["low", "medium", "high", "unavailable"]


class TradeFlowDemoInput(BaseModel):
    """Validated end-user scenario payload for the runnable demo."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    user_goal: str = Field(min_length=12)
    workflow_type: DemoWorkflowType = "sales_order_risk_review"
    sales_order_id: str = Field(pattern=r"^SO-\d+$")
    business_context: dict[str, Any] = Field(default_factory=dict)


class DemoRecommendedAction(BaseModel):
    action_type: str
    priority: str
    message: str


class DemoAuditEvent(BaseModel):
    event_type: str
    trace_id: str | None = None
    approval_id: str | None = None
    status: str | None = None
    detail: str
    refs: list[str] = Field(default_factory=list)


class TradeFlowAgentDemoResponse(BaseModel):
    """Compact agent-style response returned by CLI and local UI surfaces."""

    case_id: str
    user_goal: str
    agent_summary: str
    risk_level: RiskLevel
    risk_factors: list[str]
    recommended_action: DemoRecommendedAction | str
    approval_required: bool
    approval_reason: str | None = None
    tools_or_skills_used: list[str]
    audit_events: list[DemoAuditEvent]
    evidence_refs: list[str]
    trace_refs: dict[str, Any]
    success: bool
    error: str | None = None


def load_demo_input(path: str | Path) -> TradeFlowDemoInput:
    """Load and validate a demo scenario JSON file."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return TradeFlowDemoInput.model_validate(payload)


def run_tradeflow_agent_demo(
    demo_input: TradeFlowDemoInput,
    *,
    dataset_path: str | Path | None = None,
    planner_provider_selection: str = "deterministic",
    use_llm: bool = False,
    approval_storage_path: str | Path | None = None,
    audit_log_path: str | Path | None = None,
) -> TradeFlowAgentDemoResponse:
    """Run a validated demo scenario through existing planner/workflow components."""
    user_request = _build_user_request(demo_input)
    planner_result = plan_and_execute_user_request(
        user_request=user_request,
        dataset_path=str(dataset_path) if dataset_path else None,
        use_llm=use_llm or planner_provider_selection == "llm",
        planner_provider_selection=planner_provider_selection,
        approval_storage_path=approval_storage_path,
        audit_log_path=audit_log_path,
    )
    workflow = planner_result.workflow_result
    skill_match = match_skill_for_request(user_request)

    if workflow is None:
        recommended_action: DemoRecommendedAction | str = planner_result.grounded_response.recommendation
        risk_level: RiskLevel = "unavailable"
        risk_factors: list[str] = []
        approval_required = False
        approval_reason = None
    else:
        recommended_action = DemoRecommendedAction(
            action_type=workflow.recommended_action.action_type,
            priority=workflow.recommended_action.priority,
            message=workflow.recommended_action.message,
        )
        risk_level = workflow.risk_level
        risk_factors = workflow.risk_flags
        approval_required = workflow.approval_required
        approval_reason = workflow.approval_request.reason if workflow.approval_required else None

    response = TradeFlowAgentDemoResponse(
        case_id=demo_input.case_id,
        user_goal=demo_input.user_goal,
        agent_summary=planner_result.grounded_response.summary,
        risk_level=risk_level,
        risk_factors=risk_factors,
        recommended_action=recommended_action,
        approval_required=approval_required,
        approval_reason=approval_reason,
        tools_or_skills_used=_tools_or_skills_used(planner_result, skill_match.matched_skill),
        audit_events=_audit_events(planner_result),
        evidence_refs=[
            f"{citation.source_type}:{citation.field_path}"
            for citation in planner_result.grounded_response.cited_evidence
        ],
        trace_refs={
            "trace_id": planner_result.trace.trace_id,
            "planner_version": planner_result.planner_metadata.planner_version,
            "provider_requested": planner_result.trace.provider_requested,
            "provider_used": planner_result.trace.provider_used,
            "fallback_used": planner_result.trace.fallback_used,
            "safety_outcome": planner_result.safety_outcome,
            "reason_codes": planner_result.trace.reason_codes,
        },
        success=planner_result.success,
        error=planner_result.error,
    )
    return TradeFlowAgentDemoResponse.model_validate(redact_data(response.model_dump(mode="json")))


def response_to_json(response: TradeFlowAgentDemoResponse) -> str:
    """Serialize a demo response in stable, readable JSON."""
    return json.dumps(response.model_dump(mode="json", exclude_none=True), indent=2, sort_keys=True) + "\n"


def _build_user_request(demo_input: TradeFlowDemoInput) -> str:
    return (
        "Analyze sales order risk and prepare an action recommendation "
        f"for sales order {demo_input.sales_order_id}."
    )


def _tools_or_skills_used(planner_result: Any, matched_skill: str | None) -> list[str]:
    names = [call.tool_name for call in planner_result.tool_call_trace]
    if matched_skill:
        names.insert(0, f"skill:{matched_skill}")
    if planner_result.planner_decision.selected_workflow:
        names.insert(0, f"workflow:{planner_result.planner_decision.selected_workflow}")
    return list(dict.fromkeys(names))


def _audit_events(planner_result: Any) -> list[DemoAuditEvent]:
    events = [
        DemoAuditEvent(
            event_type="planner_decision",
            trace_id=planner_result.trace.trace_id,
            detail=planner_result.planner_decision.reason,
            refs=planner_result.trace.reason_codes,
        ),
        DemoAuditEvent(
            event_type="planner_audit_recorded",
            trace_id=planner_result.audit_record.planner_decision_id,
            status=planner_result.audit_record.safety_decision,
            detail="Planner audit record created with evidence references.",
            refs=planner_result.audit_record.evidence_references,
        ),
    ]
    if planner_result.approval_request is not None:
        events.append(
            DemoAuditEvent(
                event_type="approval_requested",
                trace_id=planner_result.trace.trace_id,
                approval_id=planner_result.approval_request.approval_id,
                status=planner_result.approval_request.status,
                detail=planner_result.approval_request.reason,
                refs=["approval_gate:approval_id", "approval_gate:status", "approval_gate:reason"],
            )
        )
    return events
