"""Planner audit records for business decision evidence."""

from __future__ import annotations

from pathlib import Path

from app.agents.planner_contracts import (
    GroundedResponse,
    PlannerAuditRecord,
    PlannerDecision,
    PlannerSafetyOutcome,
    PlannerTrace,
)
from app.agents.workflow_contracts import OrderRiskWorkflowResult


IN_MEMORY_AUDIT_LOG: list[PlannerAuditRecord] = []


def create_planner_audit_record(
    *,
    decision: PlannerDecision,
    workflow_result: OrderRiskWorkflowResult | None,
    grounded_response: GroundedResponse,
    trace: PlannerTrace,
    safety_outcome: PlannerSafetyOutcome,
) -> PlannerAuditRecord:
    """Create a business-focused audit record without storing model reasoning."""
    evidence_references = [
        f"{citation.source_type}:{citation.field_path}" for citation in grounded_response.cited_evidence
    ]

    return PlannerAuditRecord(
        planner_decision_id=trace.trace_id,
        sales_order_id=decision.extracted_sales_order_id,
        customer_id=workflow_result.customer_summary.id if workflow_result else None,
        recommended_action=workflow_result.recommended_action.action_type if workflow_result else None,
        approval_requirement=workflow_result.approval_required if workflow_result else None,
        risk_level=workflow_result.risk_level if workflow_result else None,
        reason_codes=trace.reason_codes,
        safety_decision=safety_outcome,
        evidence_references=evidence_references,
        provider_requested=trace.provider_requested,
        provider_used=trace.provider_used,
        fallback_used=trace.fallback_used,
        fallback_reason=trace.fallback_reason,
        llm_response_valid=trace.llm_response_valid,
        llm_validation_errors=trace.llm_validation_errors,
    )


def append_planner_audit_record(
    record: PlannerAuditRecord,
    *,
    storage_path: str | Path | None = None,
) -> PlannerAuditRecord:
    """Store an audit record in memory and optionally append it to a JSONL file."""
    IN_MEMORY_AUDIT_LOG.append(record)
    if storage_path is not None:
        path = Path(storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")
    return record
