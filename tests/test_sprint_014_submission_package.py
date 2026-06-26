import json
from pathlib import Path

from scripts import build_release_evidence_pack as release_pack
from scripts.check_submission_package import run_submission_checks
from scripts.run_agent_quality_gate import build_gate_commands


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _quality_report() -> dict:
    return {
        "schema_version": "2.0",
        "timestamp_utc": "2026-06-25T00:00:00+00:00",
        "overall_status": "passed",
        "status": "passed",
        "summary": "7 passed, 0 failed, 1 skipped out of 8 gates",
        "counts": {"passed": 7, "failed": 0, "skipped": 1, "total": 8},
        "git_branch": "feature/test",
        "git_commit": "abcdef1234567890",
        "git_dirty": False,
        "gates": [
            {"name": "pytest", "status": "passed", "exit_code": 0, "duration_seconds": 1.0, "summary": "ok"},
            {
                "name": "submission_package",
                "status": "passed",
                "exit_code": 0,
                "duration_seconds": 0.1,
                "summary": "Submission package passed.",
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


def test_submission_package_checker_passes_for_committed_docs() -> None:
    exit_code, report = run_submission_checks()

    assert exit_code == 0
    assert report["status"] == "passed"


def test_final_kaggle_writeup_is_under_2500_words() -> None:
    text = Path("docs/capstone/kaggle_writeup.md").read_text(encoding="utf-8")

    assert len(text.split()) < 2500


def test_submission_package_checker_detects_placeholder_markers(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "capstone"
    _write(docs_dir / "kaggle_writeup.md", "word " * 20)
    _write(docs_dir / "video_script_5min.md", "0:00 0:30 1:15 2:15 3:15 4:15 5:00")
    _write(docs_dir / "media_gallery_checklist.md", "media checklist")
    _write(
        docs_dir / "README.md",
        "kaggle_writeup.md video_script_5min.md media_gallery_checklist.md For Kaggle Judges README.md",
    )
    _write(docs_dir / "extra.md", "TODO replace this later")
    readme = tmp_path / "README.md"
    _write(
        readme,
        "## For Kaggle Judges\n"
        ".venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json\n",
    )

    exit_code, report = run_submission_checks(docs_dir=docs_dir, readme_path=readme)
    failed_names = [check["name"] for check in report["checks"] if not check["passed"]]

    assert exit_code == 1
    assert "no_placeholder_markers:extra.md" in failed_names


def test_submission_package_checker_detects_missing_index_link(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "capstone"
    _write(docs_dir / "kaggle_writeup.md", "word " * 20)
    _write(docs_dir / "video_script_5min.md", "0:00 0:30 1:15 2:15 3:15 4:15 5:00")
    _write(docs_dir / "media_gallery_checklist.md", "media checklist")
    _write(docs_dir / "README.md", "kaggle_writeup.md video_script_5min.md For Kaggle Judges README.md")
    readme = tmp_path / "README.md"
    _write(
        readme,
        "## For Kaggle Judges\n"
        ".venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json\n",
    )

    exit_code, report = run_submission_checks(docs_dir=docs_dir, readme_path=readme)
    failed_names = [check["name"] for check in report["checks"] if not check["passed"]]

    assert exit_code == 1
    assert "capstone_index_links:media_gallery_checklist.md" in failed_names


def test_quality_gate_includes_submission_package_step() -> None:
    assert "submission_package" in [command.name for command in build_gate_commands()]


def test_release_evidence_pack_includes_submission_package_status(tmp_path: Path) -> None:
    quality_report = tmp_path / "latest.json"
    out_dir = tmp_path / "release"
    _write_json(quality_report, _quality_report())

    evidence = release_pack.build_release_evidence_pack(
        quality_report=quality_report,
        history_dir=tmp_path / "history",
        out_dir=out_dir,
        release_name="Sprint 014",
    )

    assert evidence["submission_package"]["status"] == "passed"
    assert "Submission package" in (out_dir / "release_evidence.md").read_text(encoding="utf-8")
