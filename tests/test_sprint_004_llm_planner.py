import hashlib
import subprocess
import sys
from pathlib import Path

from app.agents.llm_planner import plan_and_execute_user_request
from app.agents.planner_contracts import PlannerDecision, PlannerInput


DATASET_PATH = Path("data/synthetic/tradeflow_seed.json")


def test_rule_based_planner_executes_allowed_workflow(tmp_path: Path) -> None:
    result = plan_and_execute_user_request(
        "Prepare a business recommendation for SO-1005",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.planner_decision.selected_workflow == "analyze_sales_order_risk"
    assert result.planner_decision.extracted_sales_order_id == "SO-1005"
    assert result.workflow_result is not None
    assert result.workflow_result.risk_level == "high"
    assert result.workflow_result.recommended_action.action_type == "create_purchase_order"
    assert result.approval_request is not None
    assert result.approval_request.status == "pending"
    assert all(check.passed for check in result.safety_checks)


def test_grounded_response_cites_workflow_and_approval_outputs(tmp_path: Path) -> None:
    result = plan_and_execute_user_request(
        "Analyze sales order SO-1001",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    citations = {(citation.source_type, citation.field_path) for citation in result.grounded_response.cited_evidence}
    assert ("workflow_output", "sales_order_id") in citations
    assert ("deterministic_tool_output", "risk_level") in citations
    assert ("deterministic_tool_output", "risk_flags") in citations
    assert ("workflow_output", "recommended_action.action_type") in citations
    assert ("approval_gate", "status") in citations
    assert "SO-1001" in result.grounded_response.summary


def test_missing_sales_order_id_returns_clarification_without_workflow() -> None:
    result = plan_and_execute_user_request("Should we proceed with this sales order?")

    assert result.success is False
    assert result.workflow_result is None
    assert result.planner_decision.requires_clarification is True
    assert result.planner_decision.clarification_question is not None
    assert not result.tool_call_trace


def test_unsupported_question_does_not_guess_or_execute_workflow() -> None:
    result = plan_and_execute_user_request("What is the customer's email for SO-1001?")

    assert result.success is False
    assert result.workflow_result is None
    assert result.planner_decision.intent == "unsupported_request"
    assert result.planner_decision.selected_workflow is None
    assert result.grounded_response.cited_evidence == []


def test_mocked_llm_provider_can_supply_planner_decision(tmp_path: Path) -> None:
    class MockProvider:
        def decide(self, planner_input: PlannerInput) -> PlannerDecision:
            return PlannerDecision(
                intent="analyze_sales_order_risk",
                selected_workflow="analyze_sales_order_risk",
                extracted_sales_order_id=None,
                confidence=0.9,
                requires_clarification=False,
                clarification_question=None,
                reason=f"Mocked provider selected workflow for {planner_input.user_request}.",
            )

    result = plan_and_execute_user_request(
        "Check risk for SO-1006",
        use_llm=True,
        llm_provider=MockProvider(),
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.planner_decision.extracted_sales_order_id == "SO-1006"
    assert result.workflow_result is not None
    assert result.workflow_result.recommended_action.action_type == "contact_supplier"


def test_planner_does_not_modify_source_dataset(tmp_path: Path) -> None:
    before = _sha256(DATASET_PATH)

    result = plan_and_execute_user_request(
        "Find the issue with this drop-shipping order SO-1005",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert _sha256(DATASET_PATH) == before
    assert _check(result, "source_dataset_not_mutated").passed is True


def test_planner_cli_passes_for_supported_request(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_planner.py",
            "--request",
            "Analyze sales order SO-1005",
            "--approval-storage-path",
            str(tmp_path / "approval_requests.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Planner intent: analyze_sales_order_risk" in result.stdout
    assert "Risk level: high" in result.stdout
    assert "Approval status: pending" in result.stdout


def test_planner_cli_fails_when_order_id_missing() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_planner.py", "--request", "Analyze this sales order"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Extracted sales order id: none" in result.stdout


def _check(result, check_name: str):
    return next(check for check in result.safety_checks if check.check_name == check_name)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
