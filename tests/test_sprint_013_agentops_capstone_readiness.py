import json
from pathlib import Path
import subprocess

from scripts import build_release_evidence_pack as release_pack
from scripts.build_agentops_dashboard import build_dashboard, render_dashboard
from scripts.build_agentops_evidence_index import build_evidence_index, render_markdown, write_json, write_markdown
from scripts.check_capstone_readiness import run_readiness_checks
from scripts.run_agent_quality_gate import GateCommand, build_gate_commands, run_quality_gate


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _quality_report() -> dict:
    return {
        "schema_version": "2.0",
        "timestamp_utc": "2026-06-25T00:00:00+00:00",
        "overall_status": "passed",
        "status": "passed",
        "summary": "6 passed, 0 failed, 1 skipped out of 7 gates",
        "counts": {"passed": 6, "failed": 0, "skipped": 1, "total": 7},
        "git_branch": "feature/test",
        "git_commit": "abcdef1234567890",
        "git_dirty": False,
        "gates": [
            {"name": "pytest", "status": "passed", "exit_code": 0, "duration_seconds": 1.0, "summary": "ok"},
            {
                "name": "capstone_readiness",
                "status": "passed",
                "exit_code": 0,
                "duration_seconds": 0.1,
                "summary": "Capstone readiness passed.",
            },
            {
                "name": "llm_provider_smoke",
                "status": "skipped",
                "exit_code": 0,
                "duration_seconds": 0.2,
                "summary": "Live provider smoke is not configured.",
            },
        ],
    }


def test_evidence_index_builder_writes_valid_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    quality_dir = tmp_path / "quality_gate"
    security_dir = tmp_path / "security_evals"
    _write_json(quality_dir / "latest.json", _quality_report())
    _write_json(
        security_dir / "security_eval_20260625T000000Z.json",
        {"status": "passed", "summary": "10/10 security cases passed", "counts": {"passed": 10, "failed": 0, "total": 10}},
    )
    monkeypatch.setitem(
        __import__("scripts.build_agentops_evidence_index", fromlist=["EVIDENCE_SOURCES"]).EVIDENCE_SOURCES,
        "quality_gate",
        {
            "label": "Latest quality gate result",
            "directory": quality_dir,
            "required": True,
            "patterns": ("latest.json", "*.json"),
        },
    )
    monkeypatch.setitem(
        __import__("scripts.build_agentops_evidence_index", fromlist=["EVIDENCE_SOURCES"]).EVIDENCE_SOURCES,
        "security_evals",
        {
            "label": "Latest security eval result",
            "directory": security_dir,
            "required": False,
            "patterns": ("*.json",),
        },
    )

    exit_code, index = build_evidence_index(generated_at="2026-06-25T00:00:00+00:00")
    json_out = tmp_path / "agentops_evidence_index.json"
    md_out = tmp_path / "agentops_evidence_index.md"
    write_json(index, json_out)
    write_markdown(index, md_out)

    assert exit_code == 0
    assert json.loads(json_out.read_text(encoding="utf-8"))["project_name"] == "TradeFlow AgentOS"
    assert "TradeFlow AgentOS AgentOps Evidence Index" in md_out.read_text(encoding="utf-8")
    assert "Latest quality gate result" in render_markdown(index)


def test_missing_optional_artifacts_produce_warnings_not_failure(tmp_path: Path, monkeypatch) -> None:
    module = __import__("scripts.build_agentops_evidence_index", fromlist=["EVIDENCE_SOURCES"])
    monkeypatch.setattr(
        module,
        "EVIDENCE_SOURCES",
        {
            "quality_gate": {
                "label": "Latest quality gate result",
                "directory": tmp_path / "quality_gate",
                "required": True,
                "patterns": ("latest.json",),
            },
            "security_evals": {
                "label": "Latest security eval result",
                "directory": tmp_path / "missing_security",
                "required": False,
                "patterns": ("*.json",),
            },
        },
    )
    _write_json(tmp_path / "quality_gate" / "latest.json", _quality_report())

    exit_code, index = module.build_evidence_index(generated_at="2026-06-25T00:00:00+00:00")

    assert exit_code == 0
    assert index["sources"]["security_evals"]["status"] == "missing"
    assert "Missing optional evidence" in " ".join(index["warnings"])


def test_dashboard_builder_writes_static_html_and_expected_sections(tmp_path: Path) -> None:
    evidence_json = tmp_path / "index.json"
    html_out = tmp_path / "dashboard.html"
    _write_json(
        evidence_json,
        {
            "project_name": "TradeFlow AgentOS",
            "capstone_track_recommendation": "Agents for Business",
            "generated_at_utc": "2026-06-25T00:00:00+00:00",
            "summary": {"overall_status": "passed"},
            "sources": {
                "quality_gate": {"label": "Quality", "status": "passed", "summary": "ok", "source_artifact_filename": "latest.json"},
                "security_evals": {"label": "Security", "status": "passed", "summary": "ok", "source_artifact_filename": "security.json"},
                "approval_workflow_evals": {"label": "Approval", "status": "passed", "summary": "ok", "source_artifact_filename": "approval.json"},
                "release_evidence": {"label": "Release", "status": "present", "summary": "ok", "source_artifact_filename": "release.json"},
            },
            "known_skipped_checks": [{"name": "llm_provider_smoke", "reason": "Skipped by default."}],
            "verification_commands": ["python scripts/run_agent_quality_gate.py"],
            "known_limitations": ["Static local dashboard."],
        },
    )

    build_dashboard(evidence_json=evidence_json, html_out=html_out)
    html = html_out.read_text(encoding="utf-8")

    assert "<script" not in html
    assert "TradeFlow AgentOS" in html
    assert "Quality gate status" in html
    assert "Security guardrail status" in html
    assert "Human approval/audit status" in html
    assert "What Judges Should Notice" in html


def test_dashboard_escapes_dynamic_values_safely() -> None:
    html = render_dashboard(
        {
            "project_name": "<img src=x onerror=alert(1)>",
            "capstone_track_recommendation": "Agents for Business",
            "generated_at_utc": "2026-06-25T00:00:00+00:00",
            "summary": {"overall_status": "passed"},
            "sources": {
                "quality_gate": {
                    "label": "<b>Quality</b>",
                    "status": "passed",
                    "summary": "<script>alert(1)</script>",
                    "source_artifact_filename": "latest.json",
                }
            },
            "known_skipped_checks": [],
            "verification_commands": [],
            "known_limitations": [],
        }
    )

    assert "<img src=x" not in html
    assert "<script>alert" not in html
    assert "&lt;img" in html
    assert "&lt;script&gt;" in html


def test_capstone_readiness_checker_passes_for_committed_docs() -> None:
    exit_code, report = run_readiness_checks()

    assert exit_code == 0
    assert report["status"] == "passed"


def test_kaggle_writeup_draft_is_under_2500_words() -> None:
    text = Path("docs/capstone/KAGGLE_WRITEUP_DRAFT.md").read_text(encoding="utf-8")
    assert len(text.split()) < 2500


def test_readiness_checker_detects_local_absolute_paths_and_secrets(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "capstone"
    docs_dir.mkdir(parents=True)
    for name in [
        "CAPSTONE_READINESS.md",
        "KAGGLE_WRITEUP_DRAFT.md",
        "DEMO_VIDEO_SCRIPT.md",
        "PUBLIC_REPO_CHECKLIST.md",
        "MEDIA_GALLERY_PLAN.md",
    ]:
        docs_dir.joinpath(name).write_text("0:00 to 0:30 safe capstone content\n", encoding="utf-8")
    docs_dir.joinpath("KAGGLE_WRITEUP_DRAFT.md").write_text("word " * 10, encoding="utf-8")
    docs_dir.joinpath("DEMO_VIDEO_SCRIPT.md").write_text("0:00 demo 0:30 next\n", encoding="utf-8")
    docs_dir.joinpath("CAPSTONE_READINESS.md").write_text(
        "Bad path /Users/example/project and api_key=sk-test-secret-value\n",
        encoding="utf-8",
    )

    exit_code, report = run_readiness_checks(docs_dir=docs_dir)
    failed_names = [check["name"] for check in report["checks"] if not check["passed"]]

    assert exit_code == 1
    assert any(name.startswith("no_local_absolute_paths:CAPSTONE_READINESS") for name in failed_names)
    assert any(name.startswith("no_obvious_secrets:CAPSTONE_READINESS") for name in failed_names)


def test_quality_gate_includes_capstone_readiness_as_first_class_step() -> None:
    assert "capstone_readiness" in [command.name for command in build_gate_commands()]


def test_provider_smoke_skip_remains_non_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.run_agent_quality_gate.git_metadata",
        lambda: {"git_commit": "abcdef1234567890", "git_branch": "feature/test", "git_dirty": False},
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=["mock"], returncode=0, stdout="Status: skipped\nSkip reason: not configured\n", stderr="")

    monkeypatch.setattr("scripts.run_agent_quality_gate.subprocess.run", fake_run)

    exit_code, report = run_quality_gate(
        json_out=tmp_path / "latest.json",
        history_dir=tmp_path / "history",
        quiet=True,
        commands=[GateCommand("llm_provider_smoke", ["smoke"], skipped_stdout_markers=("Status: skipped",))],
    )

    assert exit_code == 0
    assert report["overall_status"] == "passed"
    assert report["gates"][0]["status"] == "skipped"


def test_release_evidence_pack_can_include_capstone_artifacts_when_present(tmp_path: Path, monkeypatch) -> None:
    quality_report = tmp_path / "latest.json"
    out_dir = tmp_path / "release"
    capstone_dir = tmp_path / "capstone"
    _write_json(quality_report, _quality_report())
    _write_json(capstone_dir / "agentops_evidence_index.json", {"project_name": "TradeFlow AgentOS"})
    (capstone_dir / "agentops_dashboard.html").write_text("<html>dashboard</html>", encoding="utf-8")
    monkeypatch.setattr(release_pack, "DEFAULT_CAPSTONE_DIR", capstone_dir)

    evidence = release_pack.build_release_evidence_pack(
        quality_report=quality_report,
        history_dir=tmp_path / "history",
        out_dir=out_dir,
        release_name="Sprint 013",
    )

    assert evidence["capstone"]["agentops_evidence_index"].endswith("agentops_evidence_index.json")
    assert evidence["capstone"]["agentops_dashboard"].endswith("agentops_dashboard.html")
    assert evidence["capstone"]["capstone_readiness_status"] == "passed"


def test_generated_capstone_artifacts_remain_under_ignored_paths() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "artifacts/capstone/" in gitignore
