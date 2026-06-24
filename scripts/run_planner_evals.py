"""Run Sprint 5 constrained-planner evals against golden cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.llm_planner import plan_and_execute_user_request


DEFAULT_CASES_PATH = Path("evals/sprint_005_planner_golden_cases.json")
METRIC_NAMES = [
    "route_accuracy",
    "action_accuracy",
    "approval_decision_accuracy",
    "safety_pass_accuracy",
    "refusal_escalation_accuracy",
    "risk_level_accuracy",
    "reason_code_coverage",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--min-overall-pass-rate", type=float, default=1.0)
    args = parser.parse_args()

    payload = json.loads(args.cases.read_text(encoding="utf-8"))
    dataset_version = payload["dataset_version"]
    cases = payload["cases"]
    failures: list[tuple[str, list[str]]] = []
    metric_totals = {name: 0 for name in METRIC_NAMES}

    with tempfile.TemporaryDirectory(prefix="tradeflow-planner-evals-") as tmp:
        tmp_path = Path(tmp)
        for case in cases:
            result = plan_and_execute_user_request(
                case["user_request"],
                approval_storage_path=tmp_path / f"{case['case_id']}_approvals.json",
                audit_log_path=tmp_path / "planner_audit.jsonl",
                evaluation_dataset_version=dataset_version,
            )
            actual = _actual_outputs(result)
            errors, metrics = _compare_expected(actual, case.get("expected", {}))
            for name, passed in metrics.items():
                metric_totals[name] += int(passed)

            if errors:
                failures.append((case["case_id"], errors))
                print(f"FAIL {case['case_id']}: {case['description']}")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"PASS {case['case_id']}: {case['description']}")

    passed_cases = len(cases) - len(failures)
    overall_pass_rate = passed_cases / len(cases) if cases else 0.0

    print(f"\nPlanner eval dataset: {dataset_version}")
    print(f"Planner eval summary: {passed_cases}/{len(cases)} passed ({overall_pass_rate:.1%}).")
    print("Metrics:")
    for name in METRIC_NAMES:
        print(f"- {name}: {metric_totals[name]}/{len(cases)} ({metric_totals[name] / len(cases):.1%})")

    threshold_failed = overall_pass_rate < args.min_overall_pass_rate
    if threshold_failed:
        print(
            f"\nOverall pass rate {overall_pass_rate:.1%} is below required "
            f"{args.min_overall_pass_rate:.1%}.",
            file=sys.stderr,
        )
    return 1 if failures or threshold_failed else 0


def _actual_outputs(result) -> dict[str, Any]:
    workflow = result.workflow_result
    return {
        "route": result.planner_decision.selected_workflow or "none",
        "recommended_action": workflow.recommended_action.action_type if workflow else "none",
        "approval_state": workflow.approval_request.status if workflow else "none",
        "risk_level": workflow.risk_level if workflow else "unavailable",
        "reason_codes": result.trace.reason_codes,
        "safety_outcome": result.safety_outcome,
        "refusal_or_escalation_behavior": _behavior(result.safety_outcome),
    }


def _compare_expected(actual: dict[str, Any], expected: dict[str, Any]) -> tuple[list[str], dict[str, bool]]:
    errors: list[str] = []
    metrics = {
        "route_accuracy": _compare_field(errors, actual, expected, "route"),
        "action_accuracy": _compare_field(errors, actual, expected, "recommended_action"),
        "approval_decision_accuracy": _compare_field(errors, actual, expected, "approval_state"),
        "safety_pass_accuracy": _compare_field(errors, actual, expected, "safety_outcome"),
        "refusal_escalation_accuracy": _compare_field(errors, actual, expected, "refusal_or_escalation_behavior"),
        "risk_level_accuracy": _compare_field(errors, actual, expected, "risk_level"),
        "reason_code_coverage": _compare_reason_codes(errors, actual, expected),
    }
    return errors, metrics


def _compare_field(
    errors: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
    field: str,
) -> bool:
    if field not in expected:
        return True
    if actual[field] == expected[field]:
        return True
    errors.append(f"{field}: expected {expected[field]!r}, got {actual[field]!r}")
    return False


def _compare_reason_codes(
    errors: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    required = expected.get("reason_codes_contains", [])
    missing = [code for code in required if code not in actual["reason_codes"]]
    if not missing:
        return True
    errors.append(f"reason_codes missing {missing!r}; got {actual['reason_codes']!r}")
    return False


def _behavior(safety_outcome: str) -> str:
    if safety_outcome == "pass":
        return "none"
    if safety_outcome in {"refused", "escalated", "error"}:
        return safety_outcome
    return "blocked"


if __name__ == "__main__":
    raise SystemExit(main())
