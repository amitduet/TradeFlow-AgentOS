import json
import subprocess
import sys
from pathlib import Path

from app.agents.llm_provider import ConfiguredLLMPlannerProvider, LLMProviderConfig, LLMProviderError
from app.agents.llm_provider_smoke import SmokeRunOptions, run_provider_smoke
from app.agents.llm_planner import plan_and_execute_user_request
from app.agents.redaction import redact_data, redact_text


def test_live_smoke_disabled_returns_clean_skip(monkeypatch) -> None:
    monkeypatch.delenv("TRADEFLOW_LLM_SMOKE_ENABLED", raising=False)

    summary = run_provider_smoke(SmokeRunOptions())

    assert summary.status == "skipped"
    assert summary.exit_code == 0
    assert "disabled" in (summary.skip_reason or "")


def test_live_smoke_missing_credentials_returns_clean_skip(monkeypatch) -> None:
    monkeypatch.setenv("TRADEFLOW_LLM_SMOKE_ENABLED", "true")
    monkeypatch.delenv("TRADEFLOW_LLM_MODEL", raising=False)
    monkeypatch.delenv("TRADEFLOW_LLM_API_KEY", raising=False)

    summary = run_provider_smoke(SmokeRunOptions())

    assert summary.status == "skipped"
    assert summary.exit_code == 0
    assert "missing" in (summary.skip_reason or "")


def test_fake_provider_success_smoke_cases_pass() -> None:
    summary = run_provider_smoke(SmokeRunOptions(fake_provider_mode="success"))

    assert summary.status == "passed"
    assert summary.cases_total == 5
    assert summary.cases_passed == 5
    assert all(result["provider_requested"] == "llm" for result in summary.results)


def test_fake_provider_invalid_json_records_fallback() -> None:
    summary = run_provider_smoke(SmokeRunOptions(fake_provider_mode="invalid-json", max_cases=1))

    assert summary.status == "passed"
    result = summary.results[0]
    assert result["provider_used"] == "deterministic"
    assert result["fallback_used"] is True
    assert result["llm_response_valid"] is False
    assert result["llm_validation_errors"]


def test_fake_provider_schema_violation_records_fallback() -> None:
    summary = run_provider_smoke(SmokeRunOptions(fake_provider_mode="schema-violation", max_cases=1))

    assert summary.status == "passed"
    result = summary.results[0]
    assert result["fallback_used"] is True
    assert any("required" in error.lower() for error in result["llm_validation_errors"])


def test_fake_provider_timeout_records_fallback_and_redacts_key() -> None:
    summary = run_provider_smoke(SmokeRunOptions(fake_provider_mode="timeout", max_cases=1))

    assert summary.status == "passed"
    result = summary.results[0]
    assert result["fallback_used"] is True
    assert "fake-smoke-key" not in json.dumps(result)
    assert "[REDACTED]" in json.dumps(result)


def test_fake_provider_unsafe_output_falls_back_safely() -> None:
    summary = run_provider_smoke(SmokeRunOptions(fake_provider_mode="unsafe", max_cases=1))

    assert summary.status == "passed"
    result = summary.results[0]
    assert result["provider_used"] == "deterministic"
    assert result["fallback_used"] is True
    assert result["approval_state"] == "pending"


def test_redaction_prevents_api_key_leakage_in_text_and_data(monkeypatch) -> None:
    monkeypatch.setenv("TRADEFLOW_LLM_API_KEY", "sk-test-secret")

    assert redact_text("Authorization: Bearer sk-test-secret") == "Authorization: Bearer [REDACTED]"
    payload = redact_data(
        {
            "api_key": "sk-test-secret",
            "message": "provider failed with key=sk-test-secret",
            "nested": ["Bearer sk-test-secret"],
        }
    )

    serialized = json.dumps(payload)
    assert "sk-test-secret" not in serialized
    assert serialized.count("[REDACTED]") >= 3


def test_smoke_report_is_sanitized(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TRADEFLOW_LLM_API_KEY", "sk-local-report-secret")
    report_path = tmp_path / "provider_smoke.json"

    summary = run_provider_smoke(
        SmokeRunOptions(fake_provider_mode="timeout", max_cases=1, report_path=report_path)
    )

    assert summary.report_path == str(report_path)
    report = report_path.read_text(encoding="utf-8")
    assert "sk-local-report-secret" not in report
    assert "fake-smoke-key" not in report
    assert "[REDACTED]" in report


def test_planner_trace_and_audit_redact_provider_exception_secret(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TRADEFLOW_LLM_API_KEY", "sk-trace-secret")

    def leaking_client(prompt, config):
        raise LLMProviderError("failed with Authorization: Bearer sk-trace-secret")

    provider = ConfiguredLLMPlannerProvider(
        config=LLMProviderConfig(provider="openai", model="mock", api_key="sk-trace-secret"),
        response_client=leaking_client,
    )
    result = plan_and_execute_user_request(
        "Analyze sales order SO-1001",
        use_llm=True,
        llm_provider=provider,
        planner_provider_selection="llm",
        audit_log_path=tmp_path / "audit.jsonl",
    )

    serialized = result.model_dump_json()
    persisted = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "sk-trace-secret" not in serialized
    assert "sk-trace-secret" not in persisted
    assert "[REDACTED]" in serialized


def test_smoke_cli_skips_without_live_opt_in() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_llm_provider_smoke.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Status: skipped" in result.stdout
    assert "disabled" in result.stdout


def test_smoke_cli_fake_provider_is_deterministic() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_llm_provider_smoke.py",
            "--fake-provider",
            "invalid-json",
            "--max-cases",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Status: passed" in result.stdout
    assert "fallback=True" in result.stdout
