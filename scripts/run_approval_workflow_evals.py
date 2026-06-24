"""Run deterministic Sprint 012 approval workflow evals."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import time
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.redaction import redact_data
from app.agents.secure_workflow import evaluate_secure_action


DEFAULT_CASES_PATH = REPO_ROOT / "evals" / "approval_workflow_cases.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "artifacts" / "approval_workflow_evals"


def default_report_path(now: datetime | None = None) -> Path:
    generated_at = now or datetime.now(UTC)
    return DEFAULT_REPORT_DIR / f"approval_workflow_eval_{generated_at.strftime('%Y%m%dT%H%M%SZ')}.json"


def run_approval_workflow_evals(
    *,
    cases_path: Path = DEFAULT_CASES_PATH,
    json_out: Path | None = None,
    quiet: bool = False,
) -> tuple[int, dict[str, Any]]:
    started = datetime.now(UTC)
    started_monotonic = time.monotonic()
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    dataset_version = payload["dataset_version"]
    results = []

    for case in payload["cases"]:
        workflow_result = evaluate_secure_action(
            case["input_text"],
            actor=case["actor"],
            metadata={"case_id": case["case_id"], "dataset_version": dataset_version},
        )
        actual_event_types = [event.event_type.value for event in workflow_result.audit_events]
        approval = workflow_result.approval_request
        errors = _compare_case(
            case=case,
            actual_policy_decision=workflow_result.policy_result.decision.value,
            actual_enforcement_outcome=workflow_result.enforcement_result.enforcement_outcome.value,
            actual_approval_status=approval.status.value if approval else None,
            actual_required_approver_role=approval.required_approver_role if approval else None,
            actual_audit_event_types=actual_event_types,
        )
        passed = not errors
        results.append(
            {
                "case_id": case["case_id"],
                "passed": passed,
                "expected_policy_decision": case["expected_policy_decision"],
                "actual_policy_decision": workflow_result.policy_result.decision.value,
                "expected_enforcement_outcome": case["expected_enforcement_outcome"],
                "actual_enforcement_outcome": workflow_result.enforcement_result.enforcement_outcome.value,
                "expected_approval_status": case.get("expected_approval_status"),
                "actual_approval_status": approval.status.value if approval else None,
                "expected_audit_event_types": case["expected_audit_event_types"],
                "actual_audit_event_types": actual_event_types,
                "rationale": case["rationale"],
                "errors": errors,
            }
        )
        if not quiet:
            status = "PASS" if passed else "FAIL"
            print(f"{status} {case['case_id']}: {workflow_result.enforcement_result.enforcement_outcome.value}")
            for error in errors:
                print(f"  - {error}")

    finished = datetime.now(UTC)
    failures = [result for result in results if not result["passed"]]
    report_path = json_out or default_report_path(finished)
    report = redact_data(
        {
            "schema_version": "1.0",
            "dataset_version": dataset_version,
            "started_at_utc": started.isoformat(),
            "finished_at_utc": finished.isoformat(),
            "duration_seconds": round(time.monotonic() - started_monotonic, 3),
            "status": "failed" if failures else "passed",
            "summary": f"{len(results) - len(failures)}/{len(results)} approval workflow cases passed",
            "counts": {
                "total": len(results),
                "passed": len(results) - len(failures),
                "failed": len(failures),
            },
            "failures": failures,
            "cases": results,
            "report_path": str(report_path),
        }
    )
    write_report(report, report_path)

    if not quiet:
        print("\nApproval Workflow Eval Summary")
        print(f"Status: {report['status']}")
        print(f"Summary: {report['summary']}")
        print(f"Report: {report_path}")
    elif report["status"] != "passed":
        print(f"Approval workflow evals {report['status']}: {report['summary']}")

    return (0 if report["status"] == "passed" else 1), report


def write_report(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_data(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--json-out", type=Path, default=None, help="Write the JSON report to this path.")
    parser.add_argument("--quiet", action="store_true", help="Print minimal output.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, _report = run_approval_workflow_evals(cases_path=args.cases, json_out=args.json_out, quiet=args.quiet)
    return exit_code


def _compare_case(
    *,
    case: dict[str, Any],
    actual_policy_decision: str,
    actual_enforcement_outcome: str,
    actual_approval_status: str | None,
    actual_required_approver_role: str | None,
    actual_audit_event_types: list[str],
) -> list[str]:
    errors = []
    if actual_policy_decision != case["expected_policy_decision"]:
        errors.append(f"policy decision: expected {case['expected_policy_decision']!r}, got {actual_policy_decision!r}")
    if actual_enforcement_outcome != case["expected_enforcement_outcome"]:
        errors.append(
            f"enforcement outcome: expected {case['expected_enforcement_outcome']!r}, got {actual_enforcement_outcome!r}"
        )
    if actual_approval_status != case.get("expected_approval_status"):
        errors.append(f"approval status: expected {case.get('expected_approval_status')!r}, got {actual_approval_status!r}")
    expected_role = case.get("expected_required_approver_role")
    if expected_role and actual_required_approver_role != expected_role:
        errors.append(f"approver role: expected {expected_role!r}, got {actual_required_approver_role!r}")
    if actual_audit_event_types != case["expected_audit_event_types"]:
        errors.append(f"audit event types: expected {case['expected_audit_event_types']!r}, got {actual_audit_event_types!r}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
