"""Deterministic order-risk workflow orchestrator."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, TypeVar

from app.agents.approval_gate import DEFAULT_APPROVAL_STORE_PATH, create_approval_request
from app.agents.workflow_contracts import (
    CustomerRiskSummary,
    DropShippingSummary,
    LogisticsSummary,
    MarginSummary,
    OrderRiskWorkflowResult,
    OrderSummary,
    RecommendedAction,
    ToolCallTrace,
)
from app.tools import tradeflow_tools
from app.tools.tradeflow_tools import DEFAULT_DATASET_PATH, LOW_MARGIN_THRESHOLD_PERCENT


T = TypeVar("T")


REQUIRED_TOOL_CALLS = [
    "load_synthetic_dataset",
    "get_sales_order",
    "get_customer_profile",
    "get_drop_shipping_chain",
    "list_logistics_events",
    "calculate_order_margin",
    "detect_order_risk",
]


def analyze_sales_order_risk(
    sales_order_id: str,
    dataset_path: str | Path | None = None,
    approval_storage_path: str | Path | None = None,
) -> OrderRiskWorkflowResult:
    """Analyze a sales order with deterministic tools and create an approval gate."""
    resolved_dataset_path = Path(dataset_path) if dataset_path is not None else DEFAULT_DATASET_PATH
    resolved_approval_path = (
        Path(approval_storage_path) if approval_storage_path is not None else DEFAULT_APPROVAL_STORE_PATH
    )
    trace: list[ToolCallTrace] = []

    _call_tool(
        trace,
        "load_synthetic_dataset",
        tradeflow_tools.load_synthetic_dataset,
        {"path": str(resolved_dataset_path)},
        path=resolved_dataset_path,
    )
    sales_order = _call_tool(
        trace,
        "get_sales_order",
        tradeflow_tools.get_sales_order,
        {"order_id": sales_order_id, "dataset_path": str(resolved_dataset_path)},
        order_id=sales_order_id,
        dataset_path=resolved_dataset_path,
    )
    customer = _call_tool(
        trace,
        "get_customer_profile",
        tradeflow_tools.get_customer_profile,
        {"customer_id": sales_order["customer_id"], "dataset_path": str(resolved_dataset_path)},
        customer_id=sales_order["customer_id"],
        dataset_path=resolved_dataset_path,
    )
    drop_shipping_chain = _call_tool(
        trace,
        "get_drop_shipping_chain",
        tradeflow_tools.get_drop_shipping_chain,
        {"sales_order_id": sales_order_id, "dataset_path": str(resolved_dataset_path)},
        sales_order_id=sales_order_id,
        dataset_path=resolved_dataset_path,
    )
    logistics_events = _call_tool(
        trace,
        "list_logistics_events",
        tradeflow_tools.list_logistics_events,
        {"sales_order_id": sales_order_id, "dataset_path": str(resolved_dataset_path)},
        sales_order_id=sales_order_id,
        dataset_path=resolved_dataset_path,
    )
    margin = _call_tool(
        trace,
        "calculate_order_margin",
        tradeflow_tools.calculate_order_margin,
        {"order_id": sales_order_id, "dataset_path": str(resolved_dataset_path)},
        order_id=sales_order_id,
        dataset_path=resolved_dataset_path,
    )
    risk = _call_tool(
        trace,
        "detect_order_risk",
        tradeflow_tools.detect_order_risk,
        {"order_id": sales_order_id, "dataset_path": str(resolved_dataset_path)},
        order_id=sales_order_id,
        dataset_path=resolved_dataset_path,
    )

    recommended_action = _recommend_action(
        risk_level=risk["risk_level"],
        risk_flags=risk["risk_flags"],
        customer_rating=customer["rating"],
    )
    approval_request = create_approval_request(
        sales_order_id=sales_order_id,
        proposed_action=recommended_action,
        reason=_approval_reason(risk["risk_level"], risk["risk_flags"], recommended_action),
        risk_level=risk["risk_level"],
        storage_path=resolved_approval_path,
    )

    return OrderRiskWorkflowResult(
        sales_order_id=sales_order_id,
        customer_summary=_summarize_customer(customer),
        order_summary=_summarize_order(sales_order),
        margin_summary=_summarize_margin(margin),
        logistics_summary=_summarize_logistics(logistics_events),
        drop_shipping_summary=_summarize_drop_shipping(sales_order, drop_shipping_chain),
        risk_level=risk["risk_level"],
        risk_flags=risk["risk_flags"],
        recommended_action=recommended_action,
        approval_required=True,
        approval_request=approval_request,
        tool_call_trace=trace,
    )


def _call_tool(
    trace: list[ToolCallTrace],
    tool_name: str,
    tool: Callable[..., T],
    recorded_input: dict[str, Any],
    **kwargs: Any,
) -> T:
    started_at = datetime.now(UTC)
    started = perf_counter()
    try:
        output = tool(**kwargs)
    except Exception as exc:
        completed_at = datetime.now(UTC)
        trace.append(
            ToolCallTrace(
                tool_name=tool_name,
                input=recorded_input,
                output_summary=None,
                success=False,
                error=str(exc),
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=round((perf_counter() - started) * 1000, 3),
            )
        )
        raise

    completed_at = datetime.now(UTC)
    trace.append(
        ToolCallTrace(
            tool_name=tool_name,
            input=recorded_input,
            output_summary=_summarize_tool_output(output),
            success=True,
            error=None,
            started_at=started_at,
            completed_at=completed_at,
            latency_ms=round((perf_counter() - started) * 1000, 3),
        )
    )
    return output


def _recommend_action(
    *,
    risk_level: str,
    risk_flags: list[str],
    customer_rating: int,
) -> RecommendedAction:
    flags = set(risk_flags)
    if risk_level == "high" and customer_rating <= 2:
        return RecommendedAction(
            action_type="escalate_to_manager",
            priority="high",
            message="Escalate before action because this high-risk order belongs to a low-rated customer.",
        )
    if "missing_linked_po_for_drop_shipping" in flags:
        return RecommendedAction(
            action_type="create_purchase_order",
            priority="high",
            message="Prepare a linked purchase order draft for the drop-shipping order after approval.",
        )
    if "delayed_logistics_event" in flags:
        return RecommendedAction(
            action_type="contact_supplier",
            priority="high" if risk_level == "high" else "medium",
            message="Contact the supplier or logistics owner to confirm delay recovery plan.",
        )
    if "low_margin" in flags:
        return RecommendedAction(
            action_type="escalate_to_manager",
            priority="medium",
            message="Escalate for margin review before committing to the order action.",
        )
    if risk_level == "high":
        return RecommendedAction(
            action_type="escalate_to_manager",
            priority="high",
            message="Escalate high-risk order for human review before any business action.",
        )
    if "low_customer_rating" in flags:
        return RecommendedAction(
            action_type="escalate_to_manager",
            priority="high" if risk_level == "high" else "medium",
            message="Escalate customer-risk review before taking further action.",
        )
    return RecommendedAction(
        action_type="monitor_only",
        priority="low",
        message="Monitor the order; no deterministic major risk requires action.",
    )


def _approval_reason(
    risk_level: str,
    risk_flags: list[str],
    recommended_action: RecommendedAction,
) -> str:
    flag_text = ", ".join(risk_flags) if risk_flags else "no deterministic risk flags"
    return (
        f"Recommended action {recommended_action.action_type} requires human approval; "
        f"risk_level={risk_level}; flags={flag_text}."
    )


def _summarize_customer(customer: dict[str, Any]) -> CustomerRiskSummary:
    return CustomerRiskSummary(
        id=customer["id"],
        name=customer["name"],
        rating=customer["rating"],
        contact_name=customer["contact_person"]["name"],
        contact_email=customer["contact_person"]["email"],
    )


def _summarize_order(order: dict[str, Any]) -> OrderSummary:
    return OrderSummary(
        id=order["id"],
        status=order["status"],
        order_date=order["order_date"],
        expected_delivery_date=order["expected_delivery_date"],
        fulfillment_type=order["fulfillment_type"],
        incoterm=order["incoterm"],
        subtotal=order["subtotal"],
        line_count=len(order["line_items"]),
    )


def _summarize_margin(margin: dict[str, Any]) -> MarginSummary:
    return MarginSummary(
        revenue=margin["revenue"],
        estimated_cost=margin["estimated_cost"],
        gross_margin=margin["gross_margin"],
        gross_margin_percent=margin["gross_margin_percent"],
        low_margin_threshold_percent=LOW_MARGIN_THRESHOLD_PERCENT,
        below_threshold=margin["gross_margin_percent"] < LOW_MARGIN_THRESHOLD_PERCENT,
    )


def _summarize_logistics(events: list[dict[str, Any]]) -> LogisticsSummary:
    latest = sorted(events, key=lambda event: event["event_date"])[-1] if events else None
    return LogisticsSummary(
        event_count=len(events),
        delayed_event_ids=[
            event["id"]
            for event in events
            if event["status"] == "delayed" or event["event_type"] == "delay_reported"
        ],
        latest_event_status=latest["status"] if latest else None,
        latest_event_type=latest["event_type"] if latest else None,
        latest_event_date=latest["event_date"] if latest else None,
    )


def _summarize_drop_shipping(
    sales_order: dict[str, Any],
    chain: dict[str, Any],
) -> DropShippingSummary:
    po_ids = [draft["id"] for draft in chain["purchase_order_drafts"]]
    supplier_ids = [supplier["id"] for supplier in chain["suppliers"]]
    return DropShippingSummary(
        fulfillment_type=sales_order["fulfillment_type"],
        linked_purchase_order_ids=po_ids,
        linked_purchase_order_count=len(po_ids),
        supplier_ids=supplier_ids,
        missing_linked_purchase_order=sales_order["fulfillment_type"] == "drop_ship" and not po_ids,
    )


def _summarize_tool_output(output: Any) -> str:
    if hasattr(output, "model_dump"):
        output = output.model_dump(mode="json")
    summary = json.dumps(output, sort_keys=True, default=str)
    return summary if len(summary) <= 500 else summary[:497] + "..."
