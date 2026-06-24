"""Run deterministic eval cases against the Sprint 3 workflow layer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.order_risk_orchestrator import analyze_sales_order_risk
from app.tools.tradeflow_tools import DEFAULT_DATASET_PATH


DEFAULT_CASES_PATH = Path("evals/sprint_003_workflow_eval_cases.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    failures = []
    source_dataset_hash = _sha256(DEFAULT_DATASET_PATH)

    with tempfile.TemporaryDirectory(prefix="tradeflow-workflow-evals-") as tmp:
        tmp_path = Path(tmp)
        for case in cases:
            dataset_path = _prepare_dataset(case, tmp_path)
            approval_path = tmp_path / f"{case['case_id']}_approval_requests.json"
            try:
                result = analyze_sales_order_risk(
                    case["sales_order_id"],
                    dataset_path=dataset_path,
                    approval_storage_path=approval_path,
                )
                errors = _compare_expected(result.model_dump(mode="json"), case.get("expected", {}))
                if case.get("expected", {}).get("source_dataset_unchanged") is True:
                    after_hash = _sha256(DEFAULT_DATASET_PATH)
                    if after_hash != source_dataset_hash:
                        errors.append("source dataset hash changed during workflow execution")
            except Exception as exc:
                errors = [f"workflow raised {type(exc).__name__}: {exc}"]

            if errors:
                failures.append((case["case_id"], errors))
                print(f"FAIL {case['case_id']}: {case['description']}")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"PASS {case['case_id']}: {case['description']}")

    passed = len(cases) - len(failures)
    print(f"\nWorkflow eval summary: {passed}/{len(cases)} passed.")
    return 1 if failures else 0


def _prepare_dataset(case: dict[str, Any], tmp_path: Path) -> Path:
    overrides = case.get("dataset_overrides", [])
    if not overrides:
        return DEFAULT_DATASET_PATH

    payload = json.loads(DEFAULT_DATASET_PATH.read_text(encoding="utf-8"))
    for override in overrides:
        records = payload[override["collection"]]
        record = next(item for item in records if item["id"] == override["id"])
        record.update(override["updates"])
    dataset_path = tmp_path / f"{case['case_id']}_tradeflow_seed.json"
    dataset_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dataset_path


def _compare_expected(result: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors = []
    if "risk_level" in expected and result["risk_level"] != expected["risk_level"]:
        errors.append(f"risk_level: expected {expected['risk_level']!r}, got {result['risk_level']!r}")
    if "risk_flags_exact" in expected and result["risk_flags"] != expected["risk_flags_exact"]:
        errors.append(f"risk_flags: expected {expected['risk_flags_exact']!r}, got {result['risk_flags']!r}")
    for flag in expected.get("risk_flags_contains", []):
        if flag not in result["risk_flags"]:
            errors.append(f"risk_flags missing {flag!r}; got {result['risk_flags']!r}")
    if (
        "recommended_action_type" in expected
        and result["recommended_action"]["action_type"] != expected["recommended_action_type"]
    ):
        errors.append(
            "recommended_action.action_type: "
            f"expected {expected['recommended_action_type']!r}, "
            f"got {result['recommended_action']['action_type']!r}"
        )
    if (
        "recommended_priority" in expected
        and result["recommended_action"]["priority"] != expected["recommended_priority"]
    ):
        errors.append(
            "recommended_action.priority: "
            f"expected {expected['recommended_priority']!r}, "
            f"got {result['recommended_action']['priority']!r}"
        )
    if "approval_status" in expected and result["approval_request"]["status"] != expected["approval_status"]:
        errors.append(
            f"approval_request.status: expected {expected['approval_status']!r}, "
            f"got {result['approval_request']['status']!r}"
        )
    if "approval_required" in expected and result["approval_required"] != expected["approval_required"]:
        errors.append(
            f"approval_required: expected {expected['approval_required']!r}, got {result['approval_required']!r}"
        )
    if "required_tool_calls" in expected:
        actual_calls = [call["tool_name"] for call in result["tool_call_trace"]]
        missing = [tool_name for tool_name in expected["required_tool_calls"] if tool_name not in actual_calls]
        if missing:
            errors.append(f"tool_call_trace missing {missing!r}; got {actual_calls!r}")
        failed_calls = [call["tool_name"] for call in result["tool_call_trace"] if not call["success"]]
        if failed_calls:
            errors.append(f"tool_call_trace contains failed calls {failed_calls!r}")
    return errors


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
