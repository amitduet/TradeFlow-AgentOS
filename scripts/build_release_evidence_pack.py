"""Build a reviewer-ready release evidence pack from quality gate artifacts."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.redaction import redact_data
from scripts.summarize_quality_history import build_trend_summary, render_markdown


DEFAULT_QUALITY_REPORT = REPO_ROOT / "artifacts" / "quality_gate" / "latest.json"
DEFAULT_HISTORY_DIR = REPO_ROOT / "artifacts" / "quality_gate" / "history"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "release_evidence" / "latest"


def build_release_evidence_pack(
    *,
    quality_report: Path = DEFAULT_QUALITY_REPORT,
    history_dir: Path = DEFAULT_HISTORY_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
    release_name: str | None = None,
) -> dict[str, Any]:
    report = _load_json(quality_report)
    trend = build_trend_summary(history_dir)
    generated_at = datetime.now(UTC).isoformat()
    release = release_name or f"TradeFlow AgentOS {report.get('git_commit', 'unknown')[:7]}"
    inventory = {
        "release_evidence_json": str(out_dir / "release_evidence.json"),
        "release_evidence_markdown": str(out_dir / "release_evidence.md"),
        "quality_gate_report": str(out_dir / "quality_gate_report.json"),
        "quality_trend_summary_json": str(out_dir / "quality_trend_summary.json"),
        "quality_trend_summary_markdown": str(out_dir / "quality_trend_summary.md"),
    }

    evidence = redact_data(
        {
            "schema_version": "1.0",
            "release_name": release,
            "generated_at_utc": generated_at,
            "git": {
                "branch": report.get("git_branch", "unknown"),
                "commit": report.get("git_commit", "unknown"),
                "dirty": report.get("git_dirty", "unknown"),
            },
            "quality_gate": {
                "overall_status": report.get("overall_status") or report.get("status"),
                "counts": report.get("counts", {}),
                "summary": report.get("summary"),
                "gates": _normalized_gates(report),
                "approval_workflow_eval_explanation": _approval_workflow_eval_explanation(report),
                "provider_smoke_skip_explanation": _provider_skip_explanation(report),
            },
            "trend_summary": trend,
            "reproduce_commands": [
                "python scripts/run_agent_quality_gate.py --json-out artifacts/quality_gate/latest.json",
                "python scripts/summarize_quality_history.py --markdown-out artifacts/quality_gate/trend.md",
                "python scripts/build_release_evidence_pack.py --quality-report artifacts/quality_gate/latest.json",
            ],
            "artifact_inventory": inventory,
            "known_limitations": [
                "Live LLM provider smoke is skipped by default unless credentials and explicit opt-in are provided.",
                "Reports are generated from local deterministic artifacts and do not call production systems.",
            ],
            "next_recommended_action": _next_action(report),
        }
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "release_evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "release_evidence.md").write_text(render_evidence_markdown(evidence), encoding="utf-8")
    (out_dir / "quality_gate_report.json").write_text(
        json.dumps(redact_data(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "quality_trend_summary.json").write_text(
        json.dumps(redact_data(trend), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "quality_trend_summary.md").write_text(render_markdown(trend), encoding="utf-8")
    return evidence


def render_evidence_markdown(evidence: dict[str, Any]) -> str:
    quality = evidence["quality_gate"]
    git = evidence["git"]
    lines = [
        f"# {evidence['release_name']} Release Evidence",
        "",
        f"Generated: {evidence['generated_at_utc']}",
        f"Git branch: {git['branch']}",
        f"Git commit: {git['commit']}",
        f"Git dirty: {git['dirty']}",
        f"Overall quality gate status: {quality['overall_status']}",
        "",
        "## Gate Summary",
        "",
        "| Gate | Status | Exit Code | Duration | Summary |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for gate in quality["gates"]:
        lines.append(
            f"| {gate['name']} | {gate['status']} | {gate['exit_code']} | "
            f"{gate['duration_seconds']}s | {gate['summary']} |"
        )
    counts = quality["counts"]
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"Passed: {counts.get('passed', 0)}",
            f"Failed: {counts.get('failed', 0)}",
            f"Skipped: {counts.get('skipped', 0)}",
            f"Total: {counts.get('total', 0)}",
            "",
            "## Provider Smoke",
            "",
            quality.get("provider_smoke_skip_explanation") or "Provider smoke was not skipped in the latest report.",
            "",
            "## Approval Workflow Evals",
            "",
            quality.get("approval_workflow_eval_explanation")
            or "Approval workflow evals were not present in the latest quality report.",
            "",
            "## Reproduce Locally",
            "",
        ]
    )
    for command in evidence["reproduce_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Artifact Inventory", ""])
    for name, path in evidence["artifact_inventory"].items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(["", "## Known Limitations", ""])
    for limitation in evidence["known_limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(["", "## Next Recommended Action", "", evidence["next_recommended_action"]])
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality-report", type=Path, default=DEFAULT_QUALITY_REPORT)
    parser.add_argument("--history-dir", type=Path, default=DEFAULT_HISTORY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--release-name", default=None)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    evidence = build_release_evidence_pack(
        quality_report=args.quality_report,
        history_dir=args.history_dir,
        out_dir=args.out_dir,
        release_name=args.release_name,
    )
    if not args.quiet:
        print(f"Wrote release evidence pack for {evidence['release_name']} to {args.out_dir}")
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Quality report not found: {path}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Quality report root must be an object: {path}")
    return redact_data(data)


def _normalized_gates(report: dict[str, Any]) -> list[dict[str, Any]]:
    gates = report.get("gates") or report.get("commands") or report.get("results") or []
    normalized = []
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        normalized.append(
            {
                "name": gate.get("name", "unknown"),
                "status": gate.get("status", "unknown"),
                "exit_code": gate.get("exit_code", gate.get("returncode")),
                "duration_seconds": gate.get("duration_seconds", 0),
                "summary": gate.get("summary") or gate.get("skip_reason") or gate.get("failure_summary") or "",
            }
        )
    return normalized


def _provider_skip_explanation(report: dict[str, Any]) -> str | None:
    for gate in _normalized_gates(report):
        if gate["name"] == "llm_provider_smoke" and gate["status"] == "skipped":
            return gate["summary"] or "Live provider smoke was skipped because it is not configured by default."
    return None


def _approval_workflow_eval_explanation(report: dict[str, Any]) -> str | None:
    for gate in _normalized_gates(report):
        if gate["name"] == "approval_workflow_evals":
            return (
                "Approval workflow evals were included in the quality gate with "
                f"status {gate['status']!r}: {gate['summary'] or 'no summary'}"
            )
    return None


def _next_action(report: dict[str, Any]) -> str:
    if (report.get("overall_status") or report.get("status")) == "passed":
        return "Use this evidence pack for sprint review or capstone submission readiness checks."
    return "Resolve failed quality gates, rerun the gate, and regenerate the evidence pack."


if __name__ == "__main__":
    raise SystemExit(main())
