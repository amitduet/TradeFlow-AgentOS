import hashlib
import json
import subprocess
import sys
from pathlib import Path

from app.agents.approval_gate import approve_request, reject_request
from app.agents.order_risk_orchestrator import REQUIRED_TOOL_CALLS, analyze_sales_order_risk
from app.agents.workflow_contracts import OrderRiskWorkflowResult


DATASET_PATH = Path("data/synthetic/tradeflow_seed.json")


def test_workflow_returns_structured_result(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1001",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert isinstance(result, OrderRiskWorkflowResult)
    assert result.sales_order_id == "SO-1001"
    assert result.customer_summary.id == "CUST-001"
    assert result.order_summary.id == "SO-1001"
    assert result.margin_summary.gross_margin_percent == 33.33
    assert result.drop_shipping_summary.missing_linked_purchase_order is False


def test_workflow_includes_tool_call_trace(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1002",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.tool_call_trace
    assert all(call.success for call in result.tool_call_trace)
    assert all(call.started_at <= call.completed_at for call in result.tool_call_trace)
    assert all(call.latency_ms >= 0 for call in result.tool_call_trace)


def test_workflow_calls_required_tools(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1002",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    actual_calls = [call.tool_name for call in result.tool_call_trace]
    assert actual_calls == REQUIRED_TOOL_CALLS


def test_approval_required_is_true(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1003",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.approval_required is True
    assert result.recommended_action.requires_human_approval is True


def test_approval_request_is_pending_by_default(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1003",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.approval_request.status == "pending"


def test_approve_request_changes_status_to_approved(tmp_path: Path) -> None:
    approval_path = tmp_path / "approval_requests.json"
    result = analyze_sales_order_risk("SO-1001", approval_storage_path=approval_path)

    approved = approve_request(result.approval_request.approval_id, storage_path=approval_path)

    assert approved.status == "approved"


def test_reject_request_changes_status_to_rejected(tmp_path: Path) -> None:
    approval_path = tmp_path / "approval_requests.json"
    result = analyze_sales_order_risk("SO-1001", approval_storage_path=approval_path)

    rejected = reject_request(result.approval_request.approval_id, storage_path=approval_path)

    assert rejected.status == "rejected"


def test_high_risk_low_rated_customer_produces_escalation(tmp_path: Path) -> None:
    dataset_path = _copy_dataset_with_overrides(
        tmp_path,
        [{"collection": "sales_orders", "id": "SO-1008", "updates": {"fulfillment_type": "drop_ship"}}],
    )

    result = analyze_sales_order_risk(
        "SO-1008",
        dataset_path=dataset_path,
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.risk_level == "high"
    assert result.customer_summary.rating == 2
    assert result.recommended_action.action_type == "escalate_to_manager"
    assert result.recommended_action.priority == "high"


def test_missing_po_produces_create_purchase_order(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1005",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.drop_shipping_summary.missing_linked_purchase_order is True
    assert result.recommended_action.action_type == "create_purchase_order"
    assert result.recommended_action.priority == "high"


def test_delayed_logistics_produces_supplier_contact(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1006",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.logistics_summary.delayed_event_ids
    assert result.recommended_action.action_type == "contact_supplier"
    assert result.recommended_action.priority == "medium"


def test_healthy_order_produces_monitor_only(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1001",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.risk_level == "low"
    assert result.risk_flags == []
    assert result.recommended_action.action_type == "monitor_only"
    assert result.recommended_action.priority == "low"


def test_low_margin_order_produces_manager_escalation(tmp_path: Path) -> None:
    result = analyze_sales_order_risk(
        "SO-1004",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert "low_margin" in result.risk_flags
    assert result.margin_summary.below_threshold is True
    assert result.recommended_action.action_type == "escalate_to_manager"
    assert result.recommended_action.priority == "medium"


def test_workflow_does_not_modify_source_synthetic_dataset(tmp_path: Path) -> None:
    before = _sha256(DATASET_PATH)

    analyze_sales_order_risk(
        "SO-1005",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert _sha256(DATASET_PATH) == before


def test_workflow_eval_runner_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_workflow_evals.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "8/8 passed" in result.stdout


def _copy_dataset_with_overrides(tmp_path: Path, overrides: list[dict]) -> Path:
    payload = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    for override in overrides:
        records = payload[override["collection"]]
        record = next(item for item in records if item["id"] == override["id"])
        record.update(override["updates"])
    dataset_path = tmp_path / "tradeflow_seed.json"
    dataset_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dataset_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
