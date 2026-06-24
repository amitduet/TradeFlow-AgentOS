"""Typed contracts for deterministic agent-facing workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ApprovalStatus = Literal["pending", "approved", "rejected"]
RecommendedActionType = Literal[
    "contact_customer",
    "contact_supplier",
    "create_purchase_order",
    "escalate_to_manager",
    "monitor_only",
]
RecommendedActionPriority = Literal["low", "medium", "high"]


class ToolCallTrace(BaseModel):
    tool_name: str
    input: dict[str, Any]
    output_summary: str | None = None
    success: bool
    error: str | None = None
    started_at: datetime
    completed_at: datetime
    latency_ms: float = Field(ge=0)


class OrderRiskWorkflowInput(BaseModel):
    sales_order_id: str
    dataset_path: str | None = None


class OrderSummary(BaseModel):
    id: str
    status: str
    order_date: str
    expected_delivery_date: str
    fulfillment_type: str
    incoterm: str
    subtotal: float
    line_count: int


class CustomerRiskSummary(BaseModel):
    id: str
    name: str
    rating: int
    contact_name: str
    contact_email: str


class MarginSummary(BaseModel):
    revenue: float
    estimated_cost: float
    gross_margin: float
    gross_margin_percent: float
    low_margin_threshold_percent: float
    below_threshold: bool


class LogisticsSummary(BaseModel):
    event_count: int
    delayed_event_ids: list[str]
    latest_event_status: str | None = None
    latest_event_type: str | None = None
    latest_event_date: str | None = None


class DropShippingSummary(BaseModel):
    fulfillment_type: str
    linked_purchase_order_ids: list[str]
    linked_purchase_order_count: int
    supplier_ids: list[str]
    missing_linked_purchase_order: bool


class RecommendedAction(BaseModel):
    action_type: RecommendedActionType
    priority: RecommendedActionPriority
    message: str
    requires_human_approval: bool = True


class ApprovalRequest(BaseModel):
    approval_id: str
    sales_order_id: str
    proposed_action: RecommendedAction
    reason: str
    risk_level: Literal["low", "medium", "high"]
    status: ApprovalStatus = "pending"
    created_at: datetime


class OrderRiskWorkflowResult(BaseModel):
    sales_order_id: str
    customer_summary: CustomerRiskSummary
    order_summary: OrderSummary
    margin_summary: MarginSummary
    logistics_summary: LogisticsSummary
    drop_shipping_summary: DropShippingSummary
    risk_level: Literal["low", "medium", "high"]
    risk_flags: list[str]
    recommended_action: RecommendedAction
    approval_required: bool = True
    approval_request: ApprovalRequest
    tool_call_trace: list[ToolCallTrace]
