"""Typed contracts for the constrained planner layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.agents.workflow_contracts import ApprovalRequest, OrderRiskWorkflowResult


PlannerMode = Literal["rule_based", "llm_ready"]
PlannerProviderMode = Literal["mocked", "rule_based", "future_llm"]
PlannerSafetyOutcome = Literal["pass", "blocked", "escalated", "refused", "error"]
EvidenceSourceType = Literal["workflow_output", "deterministic_tool_output", "approval_gate"]


class PlannerInput(BaseModel):
    user_request: str
    dataset_path: str | None = None
    use_llm: bool = False


class PlannerDecision(BaseModel):
    intent: str
    selected_workflow: str | None = None
    extracted_sales_order_id: str | None = None
    confidence: float = Field(ge=0, le=1)
    requires_clarification: bool = False
    clarification_question: str | None = None
    reason: str
    reason_codes: list[str] = Field(default_factory=list)


class PlannerRunMetadata(BaseModel):
    planner_version: str
    prompt_template_version: str
    provider_name: str
    provider_mode: PlannerProviderMode
    evaluation_dataset_version: str | None = None


class EvidenceCitation(BaseModel):
    source_type: EvidenceSourceType
    field_path: str
    value: Any
    explanation: str


class GroundedResponse(BaseModel):
    summary: str
    key_findings: list[str]
    recommendation: str
    approval_status: str | None = None
    cited_evidence: list[EvidenceCitation]


class PlannerToolCall(BaseModel):
    tool_name: str
    input: dict[str, Any]
    success: bool
    output_summary: str | None = None
    error: str | None = None


class PlannerSafetyCheck(BaseModel):
    check_name: str
    passed: bool
    reason: str


class PlannerTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    planner_version: str
    prompt_version: str
    provider_type: PlannerProviderMode
    provider_name: str
    user_request: str
    resolved_intent: str
    selected_route: str | None = None
    tool_context_references_used: list[str] = Field(default_factory=list)
    risk_level: str | None = None
    recommended_action: str | None = None
    approval_state: str | None = None
    safety_checks: list[PlannerSafetyCheck]
    safety_outcome: PlannerSafetyOutcome
    reason_codes: list[str] = Field(default_factory=list)
    final_response_summary: str
    errors: list[str] = Field(default_factory=list)
    fallback_behavior: str | None = None


class PlannerAuditRecord(BaseModel):
    planner_decision_id: str
    sales_order_id: str | None = None
    customer_id: str | None = None
    recommended_action: str | None = None
    approval_requirement: bool | None = None
    risk_level: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    safety_decision: PlannerSafetyOutcome
    evidence_references: list[str] = Field(default_factory=list)
    created_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlannerExecutionResult(BaseModel):
    user_request: str
    planner_metadata: PlannerRunMetadata
    planner_decision: PlannerDecision
    workflow_result: OrderRiskWorkflowResult | None = None
    grounded_response: GroundedResponse
    safety_checks: list[PlannerSafetyCheck]
    safety_outcome: PlannerSafetyOutcome
    trace: PlannerTrace
    audit_record: PlannerAuditRecord
    approval_request: ApprovalRequest | None = None
    tool_call_trace: list[PlannerToolCall]
    success: bool
    error: str | None = None
