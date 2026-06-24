"""Summarize TradeFlow AgentOS quality gate history reports."""

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


DEFAULT_HISTORY_DIR = REPO_ROOT / "artifacts" / "quality_gate" / "history"


def load_history_reports(history_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    reports: list[dict[str, Any]] = []
    malformed: list[dict[str, str]] = []
    if not history_dir.exists():
        return reports, malformed

    for path in sorted(history_dir.glob("*.json")):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            malformed.append({"path": str(path), "error": str(exc)})
            continue
        if not isinstance(report, dict):
            malformed.append({"path": str(path), "error": "Report root is not an object."})
            continue
        report["_source_path"] = str(path)
        reports.append(report)

    return sorted(reports, key=_report_sort_key), malformed


def build_trend_summary(history_dir: Path = DEFAULT_HISTORY_DIR, *, limit: int | None = None) -> dict[str, Any]:
    reports, malformed = load_history_reports(history_dir)
    if limit is not None and limit > 0:
        reports = reports[-limit:]

    latest = reports[-1] if reports else None
    previous = reports[-2] if len(reports) > 1 else None
    latest_counts = _counts(latest)
    previous_counts = _counts(previous)

    summary = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "history_dir": str(history_dir),
        "total_runs_considered": len(reports),
        "malformed_reports": malformed,
        "latest_run_status": _status(latest),
        "latest_git_commit": latest.get("git_commit", "unknown") if latest else None,
        "previous_run_status": _status(previous),
        "status_changed": _status(latest) != _status(previous) if latest and previous else False,
        "counts_delta": _delta_counts(latest_counts, previous_counts) if latest and previous else None,
        "duration_delta_seconds": _duration_delta(latest, previous) if latest and previous else None,
        "per_gate_latest_status": _gate_statuses(latest),
        "per_gate_changes": _gate_changes(latest, previous) if latest and previous else {},
        "consecutive_passing_runs": _streak(reports, "passed"),
        "consecutive_failing_runs": _streak(reports, "failed"),
        "notes": _notes(reports, malformed),
    }
    return redact_data(summary)


def write_json(summary: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_data(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_markdown(summary: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(summary), encoding="utf-8")
    return path


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Quality Gate Trend Summary",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Runs considered: {summary['total_runs_considered']}",
        f"Latest status: {summary['latest_run_status'] or 'n/a'}",
        f"Previous status: {summary['previous_run_status'] or 'n/a'}",
        f"Status changed: {summary['status_changed']}",
        f"Latest commit: {summary['latest_git_commit'] or 'n/a'}",
        "",
        "## Count Deltas",
        "",
    ]
    counts_delta = summary.get("counts_delta")
    if counts_delta is None:
        lines.append("No previous run is available for count deltas.")
    else:
        lines.extend(
            [
                "| Count | Delta |",
                "| --- | ---: |",
                *[f"| {name} | {value:+d} |" for name, value in counts_delta.items()],
            ]
        )

    lines.extend(["", "## Latest Gate Status", "", "| Gate | Status |", "| --- | --- |"])
    for name, status in summary.get("per_gate_latest_status", {}).items():
        lines.append(f"| {name} | {status} |")
    if not summary.get("per_gate_latest_status"):
        lines.append("| n/a | n/a |")

    lines.extend(["", "## Notes", ""])
    for note in summary.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history-dir", type=Path, default=DEFAULT_HISTORY_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_trend_summary(args.history_dir, limit=args.limit)
    if args.json_out:
        write_json(summary, args.json_out)
    if args.markdown_out:
        write_markdown(summary, args.markdown_out)
    if not args.quiet:
        print(render_markdown(summary))
    return 0


def _report_sort_key(report: dict[str, Any]) -> str:
    return str(report.get("timestamp_utc") or report.get("generated_at") or report.get("_source_path") or "")


def _status(report: dict[str, Any] | None) -> str | None:
    if not report:
        return None
    return str(report.get("overall_status") or report.get("status") or "unknown")


def _counts(report: dict[str, Any] | None) -> dict[str, int]:
    counts = report.get("counts", {}) if report else {}
    return {name: int(counts.get(name, 0)) for name in ("passed", "failed", "skipped", "total")}


def _delta_counts(latest: dict[str, int], previous: dict[str, int]) -> dict[str, int]:
    return {name: latest[name] - previous[name] for name in ("passed", "failed", "skipped", "total")}


def _duration_delta(latest: dict[str, Any] | None, previous: dict[str, Any] | None) -> float | None:
    try:
        return round(float(latest.get("duration_seconds", 0)) - float(previous.get("duration_seconds", 0)), 3)
    except (AttributeError, TypeError, ValueError):
        return None


def _gate_statuses(report: dict[str, Any] | None) -> dict[str, str]:
    if not report:
        return {}
    gates = report.get("gates") or report.get("commands") or report.get("results") or []
    statuses: dict[str, str] = {}
    for gate in gates:
        if isinstance(gate, dict) and gate.get("name"):
            statuses[str(gate["name"])] = str(gate.get("status", "unknown"))
    return dict(sorted(statuses.items()))


def _gate_changes(latest: dict[str, Any] | None, previous: dict[str, Any] | None) -> dict[str, dict[str, str | bool]]:
    latest_statuses = _gate_statuses(latest)
    previous_statuses = _gate_statuses(previous)
    changes: dict[str, dict[str, str | bool]] = {}
    for name in sorted(set(latest_statuses) | set(previous_statuses)):
        latest_status = latest_statuses.get(name, "missing")
        previous_status = previous_statuses.get(name, "missing")
        changes[name] = {
            "previous": previous_status,
            "latest": latest_status,
            "changed": latest_status != previous_status,
        }
    return changes


def _streak(reports: list[dict[str, Any]], status: str) -> int:
    count = 0
    for report in reversed(reports):
        if _status(report) != status:
            break
        count += 1
    return count


def _notes(reports: list[dict[str, Any]], malformed: list[dict[str, str]]) -> list[str]:
    notes: list[str] = []
    if not reports:
        notes.append("No valid quality gate history reports were found.")
    elif len(reports) == 1:
        notes.append("Only one valid run is available; trend deltas need at least two runs.")
    if malformed:
        notes.append(f"Ignored {len(malformed)} malformed history report(s).")
    return notes


if __name__ == "__main__":
    raise SystemExit(main())
