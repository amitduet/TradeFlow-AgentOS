import json
import subprocess
from pathlib import Path

from scripts.run_agent_quality_gate import GateCommand, run_quality_gate


def _completed(stdout: str = "ok\n", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["mock"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_quality_gate_successful_aggregate_run_with_mocked_subprocesses(tmp_path: Path, monkeypatch) -> None:
    commands = [
        GateCommand("pytest", ["pytest"]),
        GateCommand("planner_evals", ["planner"]),
        GateCommand("skill_evals", ["skill"]),
        GateCommand("llm_provider_smoke", ["smoke"], skipped_stdout_markers=("Status: skipped",)),
    ]

    def fake_run(*args, **kwargs):
        return _completed("Status: passed\n")

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    exit_code, report = run_quality_gate(json_out=tmp_path / "report.json", quiet=True, commands=commands)

    assert exit_code == 0
    assert report["status"] == "passed"
    assert report["counts"] == {"passed": 4, "failed": 0, "skipped": 0, "total": 4}


def test_quality_gate_failed_command_produces_nonzero_final_result(tmp_path: Path, monkeypatch) -> None:
    commands = [GateCommand("pytest", ["pytest"]), GateCommand("planner_evals", ["planner"])]

    def fake_run(command, **kwargs):
        if command == ["planner"]:
            return _completed("FAIL case-1\n", returncode=1)
        return _completed()

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    exit_code, report = run_quality_gate(json_out=tmp_path / "report.json", quiet=True, commands=commands)

    assert exit_code == 1
    assert report["status"] == "failed"
    assert report["counts"]["failed"] == 1
    assert report["failures"][0]["name"] == "planner_evals"


def test_missing_live_provider_smoke_can_be_recorded_as_skip(tmp_path: Path, monkeypatch) -> None:
    commands = [
        GateCommand("llm_provider_smoke", ["smoke"], skipped_stdout_markers=("Status: skipped",)),
    ]

    def fake_run(*args, **kwargs):
        return _completed("Status: skipped\nSkip reason: Live provider smoke is not configured; missing TRADEFLOW_LLM_API_KEY.\n")

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    exit_code, report = run_quality_gate(json_out=tmp_path / "report.json", quiet=True, commands=commands)

    assert exit_code == 0
    assert report["counts"]["skipped"] == 1
    assert report["commands"][0]["status"] == "skipped"
    assert "missing TRADEFLOW_LLM_API_KEY" in report["commands"][0]["skip_reason"]


def test_require_live_provider_changes_smoke_skip_to_failure(tmp_path: Path, monkeypatch) -> None:
    commands = [
        GateCommand("llm_provider_smoke", ["smoke", "--live"], skipped_stdout_markers=("Status: skipped",)),
    ]

    def fake_run(*args, **kwargs):
        return _completed("Status: skipped\nSkip reason: Live provider smoke is not configured; missing TRADEFLOW_LLM_API_KEY.\n")

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    exit_code, report = run_quality_gate(
        json_out=tmp_path / "report.json",
        quiet=True,
        require_live_provider=True,
        commands=commands,
    )

    assert exit_code == 1
    assert report["commands"][0]["status"] == "failed"
    assert report["failures"][0]["summary"] == "Live provider smoke was required but did not run."


def test_quality_gate_report_redacts_secret_like_values(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TRADEFLOW_LLM_API_KEY", "sk-report-secret")
    commands = [GateCommand("pytest", ["pytest"])]

    def fake_run(*args, **kwargs):
        return _completed(
            stdout="Authorization: Bearer sk-report-secret\n",
            stderr="provider failed with key=sk-report-secret\n",
        )

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    report_path = tmp_path / "report.json"
    exit_code, _report = run_quality_gate(json_out=report_path, quiet=True, commands=commands)
    serialized = report_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "sk-report-secret" not in serialized
    assert "[REDACTED]" in serialized


def test_quality_gate_json_report_schema_contains_expected_fields(tmp_path: Path, monkeypatch) -> None:
    commands = [GateCommand("pytest", ["pytest"])]

    def fake_run(*args, **kwargs):
        return _completed()

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    report_path = tmp_path / "report.json"
    exit_code, report = run_quality_gate(json_out=report_path, quiet=True, commands=commands)
    persisted = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    for field in [
        "schema_version",
        "generated_at",
        "status",
        "summary",
        "counts",
        "commands",
        "failures",
        "duration_seconds",
        "report_path",
    ]:
        assert field in persisted
    assert persisted["commands"][0]["name"] == "pytest"
    assert persisted["report_path"] == str(report_path)
    assert report["report_path"] == str(report_path)
