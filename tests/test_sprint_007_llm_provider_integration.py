import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.agents.llm_planner import plan_and_execute_user_request
from app.agents.llm_provider import ConfiguredLLMPlannerProvider, LLMProviderConfig, LLMProviderError


def test_valid_llm_json_response_maps_to_planner_contracts(tmp_path: Path) -> None:
    provider = _provider_with_response(_valid_llm_response())

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1005",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.planner_decision.intent == "analyze_sales_order_risk"
    assert result.planner_decision.selected_workflow == "analyze_sales_order_risk"
    assert result.planner_decision.extracted_sales_order_id == "SO-1005"
    assert "llm_provider_validated" in result.planner_decision.reason_codes
    assert result.trace.provider_requested == "llm"
    assert result.trace.provider_used == "llm"
    assert result.trace.fallback_used is False
    assert result.trace.llm_response_valid is True


def test_invalid_json_falls_back_safely(tmp_path: Path) -> None:
    provider = _provider_with_response("not json")

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1005",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.provider_used == "deterministic"
    assert result.trace.fallback_used is True
    assert result.trace.llm_response_valid is False
    assert result.trace.llm_validation_errors
    assert "provider_fallback_used" in result.trace.reason_codes


def test_missing_required_llm_fields_fall_back_safely(tmp_path: Path) -> None:
    response = _valid_llm_response()
    del response["response_summary"]
    provider = _provider_with_response(response)

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1001",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.fallback_used is True
    assert any("response_summary" in error for error in result.trace.llm_validation_errors)


def test_invalid_llm_enum_values_are_rejected(tmp_path: Path) -> None:
    response = _valid_llm_response()
    response["risk_level"] = "critical"
    provider = _provider_with_response(response)

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1001",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.fallback_used is True
    assert any("risk_level" in error for error in result.trace.llm_validation_errors)


def test_llm_approval_bypass_is_rejected(tmp_path: Path) -> None:
    response = _valid_llm_response()
    response["response_summary"] = "I approved the order and bypass_approval for speed."
    provider = _provider_with_response(response)

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1005",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.fallback_used is True
    assert any("bypass_approval" in error or "i approved" in error for error in result.trace.llm_validation_errors)
    assert result.approval_request is not None
    assert result.approval_request.status == "pending"


def test_llm_unsupported_route_is_rejected(tmp_path: Path) -> None:
    response = _valid_llm_response()
    response["selected_route"] = "execute_purchase_order"
    provider = _provider_with_response(response)

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1005",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.fallback_used is True
    assert any("selected_route" in error for error in result.trace.llm_validation_errors)


def test_llm_invalid_recommended_action_is_rejected(tmp_path: Path) -> None:
    response = _valid_llm_response()
    response["recommended_action"] = "execute_purchase_order"
    provider = _provider_with_response(response)

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1005",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.fallback_used is True
    assert any("recommended_action" in error for error in result.trace.llm_validation_errors)


def test_llm_hallucinated_evidence_is_rejected(tmp_path: Path) -> None:
    response = _valid_llm_response()
    response["evidence_references"] = ["user_request", "workflow_output:risk_level"]
    provider = _provider_with_response(response)

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1001",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.fallback_used is True
    assert any("workflow_output:risk_level" in error for error in result.trace.llm_validation_errors)


def test_llm_timeout_or_error_triggers_fallback(tmp_path: Path) -> None:
    def failing_client(prompt: dict[str, Any], config: LLMProviderConfig) -> str:
        raise LLMProviderError("LLM provider request timed out.")

    provider = ConfiguredLLMPlannerProvider(config=_dummy_config(), response_client=failing_client)

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1001",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
    )

    assert result.success is True
    assert result.trace.provider_used == "deterministic"
    assert result.trace.fallback_used is True
    assert "timed out" in (result.trace.fallback_reason or "")


def test_trace_and_audit_records_include_provider_metadata(tmp_path: Path) -> None:
    audit_path = tmp_path / "planner_audit.jsonl"
    provider = _provider_with_response("not json")

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1007",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        approval_storage_path=tmp_path / "approval_requests.json",
        audit_log_path=audit_path,
    )

    assert result.success is True
    assert result.trace.provider_requested == "llm"
    assert result.trace.provider_used == "deterministic"
    assert result.audit_record.provider_requested == "llm"
    assert result.audit_record.provider_used == "deterministic"
    assert result.audit_record.fallback_used is True

    persisted = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[0])
    assert persisted["provider_requested"] == "llm"
    assert persisted["provider_used"] == "deterministic"
    assert persisted["fallback_used"] is True


def test_planner_cli_reports_provider_and_fallback_status(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_planner.py",
            "Analyze sales order SO-1005",
            "--provider",
            "deterministic",
            "--approval-storage-path",
            str(tmp_path / "approval_requests.json"),
            "--show-trace",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Provider requested: deterministic" in result.stdout
    assert "Provider used: deterministic" in result.stdout
    assert "Fallback used: False" in result.stdout
    assert "Safety outcome: pass" in result.stdout


def test_planner_evals_still_pass_without_live_llm_credentials() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_planner_evals.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Planner eval summary: 10/10 passed" in result.stdout


def test_skill_evals_still_pass_without_live_llm_credentials() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_skill_evals.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Skill eval summary: 18/18 passed" in result.stdout


def _provider_with_response(response: str | dict[str, Any]) -> ConfiguredLLMPlannerProvider:
    text = json.dumps(response) if isinstance(response, dict) else response

    def response_client(prompt: dict[str, Any], config: LLMProviderConfig) -> str:
        return text

    return ConfiguredLLMPlannerProvider(config=_dummy_config(), response_client=response_client)


def _dummy_config() -> LLMProviderConfig:
    return LLMProviderConfig(provider="openai", model="mock-model", api_key="mock-key", timeout_seconds=1)


def _valid_llm_response() -> dict[str, Any]:
    return {
        "resolved_intent": "analyze_sales_order_risk",
        "selected_route": "analyze_sales_order_risk",
        "recommended_action": "review",
        "risk_level": "unknown",
        "approval_state": "requires_approval",
        "safety_outcome": "pass",
        "reason_codes": ["approved_workflow_selected", "approval_gate_authoritative"],
        "evidence_references": ["user_request", "skill:order-risk-analysis", "runbook:order-risk-rules.md"],
        "response_summary": "Route the request to the approved order risk workflow and preserve approval gates.",
        "refusal_reason": None,
        "escalation_reason": None,
        "extracted_sales_order_id": None,
        "confidence": 0.91,
    }
