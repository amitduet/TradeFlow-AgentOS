import json
from pathlib import Path
import subprocess
import sys
import threading
from urllib.request import Request, urlopen

from app.agents.demo_agent import TradeFlowDemoInput, load_demo_input, run_tradeflow_agent_demo
from scripts.check_submission_package import run_submission_checks
from scripts.run_tradeflow_agent_demo_ui import DemoHandler, ThreadingHTTPServer


EXAMPLES_DIR = Path("examples/demo")


def test_demo_input_scenarios_validate_against_schema() -> None:
    for filename in ["low_risk_order.json", "medium_risk_order.json", "high_risk_order.json"]:
        scenario = load_demo_input(EXAMPLES_DIR / filename)

        assert isinstance(scenario, TradeFlowDemoInput)
        assert scenario.case_id.startswith("demo-")
        assert scenario.sales_order_id.startswith("SO-")


def test_demo_scenarios_produce_expected_risk_levels(tmp_path: Path) -> None:
    cases = {
        "low_risk_order.json": "low",
        "medium_risk_order.json": "medium",
        "high_risk_order.json": "high",
    }

    for filename, expected_risk in cases.items():
        scenario = load_demo_input(EXAMPLES_DIR / filename)
        response = run_tradeflow_agent_demo(
            scenario,
            approval_storage_path=tmp_path / f"{scenario.case_id}_approvals.json",
            audit_log_path=tmp_path / f"{scenario.case_id}_audit.jsonl",
        )

        assert response.success is True
        assert response.risk_level == expected_risk
        assert response.evidence_refs
        assert "workflow:analyze_sales_order_risk" in response.tools_or_skills_used


def test_high_risk_demo_requires_approval_with_reason(tmp_path: Path) -> None:
    scenario = load_demo_input(EXAMPLES_DIR / "high_risk_order.json")

    response = run_tradeflow_agent_demo(
        scenario,
        approval_storage_path=tmp_path / "approval_requests.json",
        audit_log_path=tmp_path / "planner_audit.jsonl",
    )

    assert response.risk_level == "high"
    assert response.approval_required is True
    assert response.approval_reason is not None
    assert "missing_linked_po_for_drop_shipping" in response.approval_reason
    assert any(event.event_type == "approval_requested" for event in response.audit_events)


def test_low_risk_demo_does_not_escalate(tmp_path: Path) -> None:
    scenario = load_demo_input(EXAMPLES_DIR / "low_risk_order.json")

    response = run_tradeflow_agent_demo(
        scenario,
        approval_storage_path=tmp_path / "approval_requests.json",
        audit_log_path=tmp_path / "planner_audit.jsonl",
    )

    assert response.risk_level == "low"
    assert response.risk_factors == []
    assert not isinstance(response.recommended_action, str)
    assert response.recommended_action.action_type == "monitor_only"
    assert response.recommended_action.priority == "low"


def test_demo_cli_returns_valid_json_for_all_scenarios(tmp_path: Path) -> None:
    cases = {
        "low_risk_order.json": ("demo-low-risk-order", "low", True),
        "medium_risk_order.json": ("demo-medium-risk-order", "medium", True),
        "high_risk_order.json": ("demo-high-risk-order", "high", True),
    }

    for filename, (expected_case_id, expected_risk, expected_approval) in cases.items():
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_tradeflow_agent_demo.py",
                "--input",
                f"examples/demo/{filename}",
                "--json",
                "--approval-storage-path",
                str(tmp_path / f"{filename}_approval_requests.json"),
                "--audit-log-path",
                str(tmp_path / f"{filename}_planner_audit.jsonl"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(result.stdout)
        assert payload["case_id"] == expected_case_id
        assert payload["user_goal"]
        assert payload["agent_summary"]
        assert payload["risk_level"] == expected_risk
        assert payload["approval_required"] is expected_approval
        assert payload["tools_or_skills_used"]
        assert payload["audit_events"]
        assert payload["evidence_refs"]
        assert payload["trace_refs"]["provider_used"] == "deterministic"


def test_demo_cli_high_risk_json_shape(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_tradeflow_agent_demo.py",
            "--input",
            "examples/demo/high_risk_order.json",
            "--json",
            "--approval-storage-path",
            str(tmp_path / "approval_requests.json"),
            "--audit-log-path",
            str(tmp_path / "planner_audit.jsonl"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["case_id"] == "demo-high-risk-order"
    assert payload["user_goal"]
    assert payload["agent_summary"]
    assert payload["risk_level"] == "high"
    assert payload["approval_required"] is True
    assert payload["tools_or_skills_used"]
    assert payload["audit_events"]
    assert payload["evidence_refs"]
    assert payload["trace_refs"]["provider_used"] == "deterministic"


def test_demo_default_path_requires_no_secrets_or_api_keys(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("TRADEFLOW_LLM_API_KEY", raising=False)
    monkeypatch.delenv("TRADEFLOW_PLANNER_PROVIDER", raising=False)
    scenario = load_demo_input(EXAMPLES_DIR / "medium_risk_order.json")

    response = run_tradeflow_agent_demo(
        scenario,
        approval_storage_path=tmp_path / "approval_requests.json",
        audit_log_path=tmp_path / "planner_audit.jsonl",
    )

    assert response.success is True
    assert response.trace_refs["provider_used"] == "deterministic"
    assert response.trace_refs["fallback_used"] is False


def test_readme_references_runnable_demo_command() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert ".venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json" in readme
    assert ".venv/bin/python scripts/run_tradeflow_agent_demo_ui.py" in readme
    assert "http://127.0.0.1:8765" in readme


def test_submission_checker_includes_demo_readiness_checks() -> None:
    exit_code, report = run_submission_checks()
    check_names = {check["name"] for check in report["checks"]}

    assert exit_code == 0
    assert "demo_runner_exists" in check_names
    assert "demo_input_exists:low_risk_order.json" in check_names
    assert "demo_input_exists:medium_risk_order.json" in check_names
    assert "demo_input_exists:high_risk_order.json" in check_names
    assert "readme_has_demo_run_command" in check_names
    assert "demo_runs_offline" in check_names
    assert "demo_ui_runner_exists" in check_names
    assert "readme_has_ui_demo_command" in check_names
    assert "readme_has_ui_url" in check_names


def test_demo_ui_endpoints_return_expected_content() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{base_url}/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert "TradeFlow AgentOS Demo" in html

        with urlopen(f"{base_url}/api/scenarios", timeout=5) as response:
            scenarios = json.loads(response.read().decode("utf-8"))["scenarios"]
        assert {"low_risk_order.json", "medium_risk_order.json", "high_risk_order.json"}.issubset(set(scenarios))

        high_risk_payload = (EXAMPLES_DIR / "high_risk_order.json").read_text(encoding="utf-8")
        request = Request(
            f"{base_url}/api/demo",
            data=high_risk_payload.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["case_id"] == "demo-high-risk-order"
        assert payload["risk_level"] == "high"
        assert payload["approval_required"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
