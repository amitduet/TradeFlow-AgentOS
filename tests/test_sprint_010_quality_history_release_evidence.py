import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from scripts.build_release_evidence_pack import build_release_evidence_pack, render_evidence_markdown
from scripts.run_agent_quality_gate import (
    GateCommand,
    build_gate_commands,
    history_report_path,
    run_quality_gate,
)
from scripts.summarize_quality_history import build_trend_summary, render_markdown


def _completed(stdout: str = "ok\n", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["mock"], returncode=returncode, stdout=stdout, stderr=stderr)


def _quality_report(
    *,
    status: str = "passed",
    timestamp: str = "2026-06-24T01:00:00+00:00",
    passed: int = 3,
    failed: int = 0,
    skipped: int = 1,
    duration: float = 10.0,
) -> dict:
    return {
        "schema_version": "2.0",
        "run_id": timestamp,
        "timestamp_utc": timestamp,
        "git_commit": "abcdef1234567890",
        "git_branch": "feature/test",
        "git_dirty": False,
        "overall_status": status,
        "status": status,
        "duration_seconds": duration,
        "summary": f"{passed} passed, {failed} failed, {skipped} skipped out of 4 gates",
        "counts": {"passed": passed, "failed": failed, "skipped": skipped, "total": 4},
        "gates": [
            {"name": "pytest", "status": "passed", "exit_code": 0, "duration_seconds": 1.0, "summary": "ok"},
            {"name": "planner_evals", "status": "passed", "exit_code": 0, "duration_seconds": 2.0, "summary": "ok"},
            {"name": "skill_evals", "status": "passed", "exit_code": 0, "duration_seconds": 3.0, "summary": "ok"},
            {
                "name": "llm_provider_smoke",
                "status": "skipped" if skipped else "passed",
                "exit_code": 0,
                "duration_seconds": 4.0,
                "summary": "Live provider smoke is not configured; missing TRADEFLOW_LLM_API_KEY.",
                "skip_reason": "Live provider smoke is not configured; missing TRADEFLOW_LLM_API_KEY.",
            },
        ],
    }


def _write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding="utf-8")


def test_quality_gate_history_report_path_generation() -> None:
    path = history_report_path(
        history_dir=Path("history"),
        timestamp_utc=datetime(2026, 6, 24, 1, 2, 3, tzinfo=UTC),
        git_commit="abcdef1234567890",
    )

    assert path == Path("history") / "quality_gate_20260624T010203Z_abcdef1.json"


def test_no_history_disables_timestamped_history_write(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.run_agent_quality_gate.git_metadata", lambda: _git_info())
    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", lambda *args, **kwargs: _completed())

    exit_code, report = run_quality_gate(
        json_out=tmp_path / "latest.json",
        history_dir=tmp_path / "history",
        write_history=False,
        quiet=True,
        commands=[GateCommand("pytest", ["pytest"])],
    )

    assert exit_code == 0
    assert report["history_path"] is None
    assert not (tmp_path / "history").exists()


def test_json_out_still_writes_requested_path_and_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.run_agent_quality_gate.git_metadata", lambda: _git_info())
    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", lambda *args, **kwargs: _completed())

    json_out = tmp_path / "stable" / "latest.json"
    exit_code, report = run_quality_gate(
        json_out=json_out,
        history_dir=tmp_path / "history",
        quiet=True,
        commands=[GateCommand("pytest", ["pytest"])],
    )

    assert exit_code == 0
    assert json_out.exists()
    assert Path(report["history_path"]).exists()
    assert json.loads(json_out.read_text(encoding="utf-8"))["report_path"] == str(json_out)


def test_history_report_redacts_obvious_secret_token_and_api_key_values(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TRADEFLOW_LLM_API_KEY", "sk-history-secret")
    monkeypatch.setattr("scripts.run_agent_quality_gate.git_metadata", lambda: _git_info())

    def fake_run(*args, **kwargs):
        return _completed(
            stdout="Authorization: Bearer sk-history-secret\n",
            stderr="api_key=sk-history-secret token=plain-token\n",
        )

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    _exit_code, report = run_quality_gate(
        json_out=tmp_path / "latest.json",
        history_dir=tmp_path / "history",
        quiet=True,
        commands=[GateCommand("pytest", ["pytest"])],
    )
    serialized = Path(report["history_path"]).read_text(encoding="utf-8")

    assert "sk-history-secret" not in serialized
    assert "Bearer [REDACTED]" in serialized
    assert "[REDACTED]" in serialized


def test_trend_summary_with_zero_reports(tmp_path: Path) -> None:
    summary = build_trend_summary(tmp_path / "missing")

    assert summary["total_runs_considered"] == 0
    assert summary["latest_run_status"] is None
    assert "No valid quality gate history reports were found." in summary["notes"]


def test_trend_summary_with_one_report(tmp_path: Path) -> None:
    _write_report(tmp_path / "quality_gate_1.json", _quality_report())

    summary = build_trend_summary(tmp_path)

    assert summary["total_runs_considered"] == 1
    assert summary["latest_run_status"] == "passed"
    assert summary["previous_run_status"] is None
    assert summary["counts_delta"] is None
    assert "trend deltas need at least two runs" in " ".join(summary["notes"])


def test_trend_summary_with_two_reports_has_deltas_and_gate_changes(tmp_path: Path) -> None:
    _write_report(
        tmp_path / "quality_gate_1.json",
        _quality_report(status="failed", timestamp="2026-06-24T01:00:00+00:00", passed=2, failed=1, duration=8.0),
    )
    latest = _quality_report(status="passed", timestamp="2026-06-24T02:00:00+00:00", passed=3, failed=0, duration=11.5)
    latest["gates"][0]["status"] = "passed"
    _write_report(tmp_path / "quality_gate_2.json", latest)

    summary = build_trend_summary(tmp_path)

    assert summary["latest_run_status"] == "passed"
    assert summary["previous_run_status"] == "failed"
    assert summary["status_changed"] is True
    assert summary["counts_delta"]["passed"] == 1
    assert summary["counts_delta"]["failed"] == -1
    assert summary["duration_delta_seconds"] == 3.5
    assert summary["consecutive_passing_runs"] == 1


def test_trend_summary_ignores_malformed_reports(tmp_path: Path) -> None:
    _write_report(tmp_path / "quality_gate_good.json", _quality_report())
    (tmp_path / "quality_gate_bad.json").write_text("{not-json", encoding="utf-8")

    summary = build_trend_summary(tmp_path)

    assert summary["total_runs_considered"] == 1
    assert len(summary["malformed_reports"]) == 1
    assert "Ignored 1 malformed" in " ".join(summary["notes"])


def test_release_evidence_json_and_markdown_generation(tmp_path: Path) -> None:
    quality_report = tmp_path / "latest.json"
    history_dir = tmp_path / "history"
    out_dir = tmp_path / "release"
    _write_report(quality_report, _quality_report())
    _write_report(history_dir / "quality_gate_1.json", _quality_report())

    evidence = build_release_evidence_pack(
        quality_report=quality_report,
        history_dir=history_dir,
        out_dir=out_dir,
        release_name="Sprint 010",
    )
    markdown = (out_dir / "release_evidence.md").read_text(encoding="utf-8")

    assert evidence["release_name"] == "Sprint 010"
    assert (out_dir / "release_evidence.json").exists()
    assert (out_dir / "quality_gate_report.json").exists()
    assert (out_dir / "quality_trend_summary.json").exists()
    assert "# Sprint 010 Release Evidence" in markdown
    assert "| pytest | passed | 0 | 1.0s | ok |" in markdown


def test_skipped_provider_smoke_is_represented_as_skipped_not_failed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.run_agent_quality_gate.git_metadata", lambda: _git_info())
    command = GateCommand("llm_provider_smoke", ["smoke"], skipped_stdout_markers=("Status: skipped",))

    def fake_run(*args, **kwargs):
        return _completed("Status: skipped\nSkip reason: Live provider smoke is not configured.\n")

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    exit_code, report = run_quality_gate(
        json_out=tmp_path / "latest.json",
        history_dir=tmp_path / "history",
        quiet=True,
        commands=[command],
    )

    assert exit_code == 0
    assert report["gates"][0]["status"] == "skipped"
    assert report["overall_status"] == "passed"


def test_deterministic_ordering_of_default_gates() -> None:
    assert [command.name for command in build_gate_commands()] == [
        "pytest",
        "planner_evals",
        "skill_evals",
        "security_evals",
        "approval_workflow_evals",
        "llm_provider_smoke",
    ]


def test_markdown_renderers_are_stable_for_empty_inputs(tmp_path: Path) -> None:
    trend = build_trend_summary(tmp_path / "missing")
    evidence = {
        "release_name": "Release",
        "generated_at_utc": "2026-06-24T00:00:00+00:00",
        "git": {"branch": "main", "commit": "unknown", "dirty": False},
        "quality_gate": {"overall_status": "passed", "counts": {}, "gates": [], "provider_smoke_skip_explanation": None},
        "reproduce_commands": [],
        "artifact_inventory": {},
        "known_limitations": [],
        "next_recommended_action": "Done.",
    }

    assert "Runs considered: 0" in render_markdown(trend)
    assert "Overall quality gate status: passed" in render_evidence_markdown(evidence)


def _git_info() -> dict:
    return {"git_commit": "abcdef1234567890", "git_branch": "feature/test", "git_dirty": False}
