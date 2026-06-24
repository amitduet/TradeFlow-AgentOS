"""Run the unified TradeFlow AgentOS quality gate.

The gate aggregates deterministic tests, planner evals, skill evals, security
evals, and the provider smoke harness into one sanitized JSON report.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import platform
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.redaction import redact_data, redact_text


DEFAULT_REPORT_DIR = REPO_ROOT / "artifacts" / "quality_gate"
DEFAULT_HISTORY_DIR = DEFAULT_REPORT_DIR / "history"
CommandStatus = str


@dataclass(frozen=True)
class GateCommand:
    name: str
    command: list[str]
    required: bool = True
    skipped_stdout_markers: tuple[str, ...] = ()


def git_metadata() -> dict[str, Any]:
    def run_git(args: list[str]) -> str | None:
        completed = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return None
        return completed.stdout.strip() or None

    status = run_git(["status", "--porcelain"])
    return {
        "git_commit": run_git(["rev-parse", "HEAD"]) or "unknown",
        "git_branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        "git_dirty": bool(status),
    }


def default_report_path(now: datetime | None = None) -> Path:
    generated_at = now or datetime.now(UTC)
    stamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_REPORT_DIR / f"quality_gate_{stamp}.json"


def history_report_path(
    *,
    history_dir: Path = DEFAULT_HISTORY_DIR,
    timestamp_utc: datetime | None = None,
    git_commit: str = "unknown",
) -> Path:
    generated_at = timestamp_utc or datetime.now(UTC)
    stamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    short_sha = git_commit[:7] if git_commit and git_commit != "unknown" else "unknown"
    return history_dir / f"quality_gate_{stamp}_{short_sha}.json"


def build_gate_commands(*, require_live_provider: bool = False) -> list[GateCommand]:
    smoke_command = [sys.executable, "scripts/run_llm_provider_smoke.py"]
    if require_live_provider:
        smoke_command.append("--live")

    return [
        GateCommand("pytest", [sys.executable, "-m", "pytest", "-q"]),
        GateCommand("planner_evals", [sys.executable, "scripts/run_planner_evals.py"]),
        GateCommand("skill_evals", [sys.executable, "scripts/run_skill_evals.py"]),
        GateCommand("security_evals", [sys.executable, "scripts/run_security_evals.py", "--quiet"]),
        GateCommand(
            "llm_provider_smoke",
            smoke_command,
            skipped_stdout_markers=("Status: skipped",),
        ),
    ]


def run_quality_gate(
    *,
    json_out: Path | None = None,
    history_dir: Path = DEFAULT_HISTORY_DIR,
    write_history: bool = True,
    max_history: int | None = None,
    require_live_provider: bool = False,
    quiet: bool = False,
    stop_on_failure: bool = False,
    commands: Sequence[GateCommand] | None = None,
) -> tuple[int, dict[str, Any]]:
    started = datetime.now(UTC)
    started_monotonic = time.monotonic()
    gate_commands = list(commands or build_gate_commands(require_live_provider=require_live_provider))
    command_results: list[dict[str, Any]] = []

    for gate_command in gate_commands:
        if not quiet:
            print(f"Running {gate_command.name}...")
        result = run_gate_command(gate_command, require_live_provider=require_live_provider)
        command_results.append(result)

        if not quiet:
            status = result["status"].upper()
            print(f"{status} {gate_command.name} ({result['duration_seconds']:.2f}s)")

        if stop_on_failure and result["status"] == "failed":
            break

    finished = datetime.now(UTC)
    git_info = git_metadata()
    history_path = (
        history_report_path(history_dir=history_dir, timestamp_utc=finished, git_commit=git_info["git_commit"])
        if write_history
        else None
    )
    report_path = json_out or history_path or default_report_path(finished)
    report = build_report(
        started_at=started,
        finished_at=finished,
        duration_seconds=time.monotonic() - started_monotonic,
        command_results=command_results,
        require_live_provider=require_live_provider,
        stop_on_failure=stop_on_failure,
        report_path=report_path,
        git_info=git_info,
        history_path=history_path,
    )
    if json_out:
        write_report(report, json_out)
    if history_path:
        write_report(report, history_path)
        prune_history(history_dir, max_history)

    if not quiet:
        print_summary(report)
    elif report["status"] != "passed":
        print(f"Quality gate {report['status']}: {report['summary']}")

    return (0 if report["status"] == "passed" else 1), report


def run_gate_command(gate_command: GateCommand, *, require_live_provider: bool = False) -> dict[str, Any]:
    started = datetime.now(UTC)
    started_monotonic = time.monotonic()
    completed = subprocess.run(
        gate_command.command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    duration_seconds = time.monotonic() - started_monotonic
    stdout = redact_text(completed.stdout) or ""
    stderr = redact_text(completed.stderr) or ""

    status: CommandStatus = "passed" if completed.returncode == 0 else "failed"
    skip_reason: str | None = None
    if completed.returncode == 0 and any(marker in stdout for marker in gate_command.skipped_stdout_markers):
        status = "skipped"
        skip_reason = _extract_skip_reason(stdout)

    failure_summary: str | None = None
    if status == "skipped" and require_live_provider and gate_command.name == "llm_provider_smoke":
        status = "failed"
        failure_summary = "Live provider smoke was required but did not run."
    elif status == "failed":
        failure_summary = _failure_summary(stdout, stderr, completed.returncode)

    return redact_data(
        {
            "name": gate_command.name,
            "command": gate_command.command,
            "required": gate_command.required,
            "status": status,
            "returncode": completed.returncode,
            "exit_code": completed.returncode,
            "started_at": started.isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "stdout": stdout,
            "stderr": stderr,
            "skip_reason": skip_reason,
            "failure_summary": failure_summary,
            "summary": skip_reason or failure_summary or ("Command passed." if status == "passed" else "Command skipped."),
        }
    )


def build_report(
    *,
    started_at: datetime,
    finished_at: datetime,
    duration_seconds: float,
    command_results: list[dict[str, Any]],
    require_live_provider: bool,
    stop_on_failure: bool,
    report_path: Path | None = None,
    git_info: dict[str, Any] | None = None,
    history_path: Path | None = None,
) -> dict[str, Any]:
    counts = {
        "passed": sum(1 for result in command_results if result["status"] == "passed"),
        "failed": sum(1 for result in command_results if result["status"] == "failed"),
        "skipped": sum(1 for result in command_results if result["status"] == "skipped"),
        "total": len(command_results),
    }
    failures = [
        {
            "name": result["name"],
            "returncode": result["returncode"],
            "summary": result.get("failure_summary") or "Command failed.",
        }
        for result in command_results
        if result["status"] == "failed"
    ]
    status = "failed" if failures else "passed"
    summary = (
        f"{counts['passed']} passed, {counts['failed']} failed, "
        f"{counts['skipped']} skipped out of {counts['total']} gates"
    )
    git_info = git_info or {
        "git_commit": "unknown",
        "git_branch": "unknown",
        "git_dirty": False,
    }
    run_id_commit = git_info["git_commit"][:12] if git_info["git_commit"] != "unknown" else "unknown"
    run_id = f"{finished_at.strftime('%Y%m%dT%H%M%SZ')}-{run_id_commit}"

    return redact_data(
        {
            "schema_version": "2.0",
            "run_id": run_id,
            "timestamp_utc": finished_at.isoformat(),
            "generated_at": finished_at.isoformat(),
            "started_at": started_at.isoformat(),
            "started_at_utc": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "finished_at_utc": finished_at.isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "status": status,
            "overall_status": status,
            "summary": summary,
            "counts": counts,
            "git_commit": git_info["git_commit"],
            "git_branch": git_info["git_branch"],
            "git_dirty": git_info["git_dirty"],
            "python_version": platform.python_version(),
            "platform": f"{platform.system()} {platform.release()} {platform.machine()}".strip(),
            "options": {
                "require_live_provider": require_live_provider,
                "stop_on_failure": stop_on_failure,
            },
            "commands": command_results,
            "gates": command_results,
            "results": command_results,
            "failures": failures,
            "report_path": str(report_path) if report_path else None,
            "history_path": str(history_path) if history_path else None,
            "redaction": {
                "status": "redacted",
                "note": "Report fields are passed through app.agents.redaction before writing.",
            },
        }
    )


def write_report(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_data(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def prune_history(history_dir: Path, max_history: int | None) -> None:
    if max_history is None or max_history < 1 or not history_dir.exists():
        return
    reports = sorted(history_dir.glob("quality_gate_*.json"), key=lambda path: path.name)
    for stale_report in reports[:-max_history]:
        stale_report.unlink(missing_ok=True)


def print_summary(report: dict[str, Any]) -> None:
    print("\nQuality Gate Summary")
    print(f"Status: {report['status']}")
    print(f"Summary: {report['summary']}")
    print(f"Duration: {report['duration_seconds']:.2f}s")
    print(f"Report: {report['report_path']}")
    for failure in report["failures"]:
        print(f"FAIL {failure['name']}: {failure['summary']}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=None, help="Write the JSON report to this path.")
    parser.add_argument(
        "--history-dir",
        type=Path,
        default=DEFAULT_HISTORY_DIR,
        help="Directory for timestamped quality gate history reports.",
    )
    parser.add_argument("--no-history", action="store_true", help="Do not write a timestamped history report.")
    parser.add_argument("--max-history", type=int, default=None, help="Keep only the newest N history reports.")
    parser.add_argument(
        "--require-live-provider",
        action="store_true",
        help="Fail if live provider smoke cannot run because opt-in or credentials are missing.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print minimal output.")
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Stop after the first failed gate instead of aggregating all results.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, _report = run_quality_gate(
        json_out=args.json_out,
        history_dir=args.history_dir,
        write_history=not args.no_history,
        max_history=args.max_history,
        require_live_provider=args.require_live_provider,
        quiet=args.quiet,
        stop_on_failure=args.stop_on_failure,
    )
    return exit_code


def _extract_skip_reason(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("Skip reason:"):
            return line.split(":", 1)[1].strip()
    return None


def _failure_summary(stdout: str, stderr: str, returncode: int) -> str:
    lines = [line.strip() for line in (stderr + "\n" + stdout).splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith(("FAIL", "FAILED", "ERROR", "Overall pass rate")):
            return line
    if lines:
        return lines[-1]
    return f"Command exited with code {returncode}."


if __name__ == "__main__":
    raise SystemExit(main())
