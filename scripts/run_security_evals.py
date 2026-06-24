"""Run deterministic Sprint 011 security policy evals."""

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
from app.agents.security_policy import PolicyDecision, evaluate_security_policy


DEFAULT_CASES_PATH = REPO_ROOT / "evals" / "security_policy_cases.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "artifacts" / "security_evals"


def default_report_path(now: datetime | None = None) -> Path:
    generated_at = now or datetime.now(UTC)
    return DEFAULT_REPORT_DIR / f"security_eval_{generated_at.strftime('%Y%m%dT%H%M%SZ')}.json"


def run_security_evals(
    *,
    cases_path: Path = DEFAULT_CASES_PATH,
    json_out: Path | None = None,
    quiet: bool = False,
    fail_on_review: bool = False,
) -> tuple[int, dict[str, Any]]:
    started = datetime.now(UTC)
    started_monotonic = time.monotonic()
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    dataset_version = payload["dataset_version"]
    cases = payload["cases"]
    results = []

    for case in cases:
        result = evaluate_security_policy(
            case["input_text"],
            metadata={"case_id": case["case_id"], "dataset_version": dataset_version},
        )
        actual_categories = sorted({finding.category for finding in result.findings})
        expected_categories = sorted(case.get("expected_categories", []))
        errors = _compare_case(
            expected_decision=case["expected_decision"],
            actual_decision=result.decision.value,
            expected_categories=expected_categories,
            actual_categories=actual_categories,
            fail_on_review=fail_on_review,
        )
        passed = not errors
        results.append(
            {
                "case_id": case["case_id"],
                "passed": passed,
                "expected_decision": case["expected_decision"],
                "actual_decision": result.decision.value,
                "expected_categories": expected_categories,
                "actual_categories": actual_categories,
                "rationale": case["rationale"],
                "tags": case.get("tags", []),
                "errors": errors,
                "findings": [finding.to_dict() for finding in result.findings],
            }
        )
        if not quiet:
            status = "PASS" if passed else "FAIL"
            categories = ", ".join(actual_categories) or "none"
            print(f"{status} {case['case_id']}: {result.decision.value} ({categories})")
            for error in errors:
                print(f"  - {error}")

    finished = datetime.now(UTC)
    failed_results = [result for result in results if not result["passed"]]
    review_results = [result for result in results if result["actual_decision"] == PolicyDecision.REVIEW.value]
    report_path = json_out or default_report_path(finished)
    report = redact_data(
        {
            "schema_version": "1.0",
            "dataset_version": dataset_version,
            "started_at_utc": started.isoformat(),
            "finished_at_utc": finished.isoformat(),
            "duration_seconds": round(time.monotonic() - started_monotonic, 3),
            "status": "failed" if failed_results else "passed",
            "summary": (
                f"{len(results) - len(failed_results)}/{len(results)} security cases passed; "
                f"{len(review_results)} review decisions observed"
            ),
            "options": {"fail_on_review": fail_on_review},
            "counts": {
                "total": len(results),
                "passed": len(results) - len(failed_results),
                "failed": len(failed_results),
                "review": len(review_results),
            },
            "failures": failed_results,
            "cases": results,
            "report_path": str(report_path),
        }
    )
    write_report(report, report_path)

    if not quiet:
        print("\nSecurity Eval Summary")
        print(f"Status: {report['status']}")
        print(f"Summary: {report['summary']}")
        print(f"Report: {report_path}")
    elif report["status"] != "passed":
        print(f"Security evals {report['status']}: {report['summary']}")

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
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Treat review decisions as failures even when the eval case expects review.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, _report = run_security_evals(
        cases_path=args.cases,
        json_out=args.json_out,
        quiet=args.quiet,
        fail_on_review=args.fail_on_review,
    )
    return exit_code


def _compare_case(
    *,
    expected_decision: str,
    actual_decision: str,
    expected_categories: list[str],
    actual_categories: list[str],
    fail_on_review: bool,
) -> list[str]:
    errors = []
    if actual_decision != expected_decision:
        errors.append(f"decision: expected {expected_decision!r}, got {actual_decision!r}")
    if expected_categories:
        missing_categories = sorted(set(expected_categories) - set(actual_categories))
        if missing_categories:
            errors.append(f"categories missing {missing_categories!r}; got {actual_categories!r}")
    elif actual_categories:
        errors.append(f"categories: expected none, got {actual_categories!r}")
    if fail_on_review and actual_decision == PolicyDecision.REVIEW.value:
        errors.append("review decisions are treated as failures because --fail-on-review was set")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
