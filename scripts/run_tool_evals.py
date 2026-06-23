"""Run deterministic eval cases against the Sprint 2 tool layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.tools import tradeflow_tools


DEFAULT_CASES_PATH = Path("evals/sprint_002_tool_eval_cases.json")

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "get_customer_profile": tradeflow_tools.get_customer_profile,
    "get_supplier_profile": tradeflow_tools.get_supplier_profile,
    "list_sales_orders": tradeflow_tools.list_sales_orders,
    "get_drop_shipping_chain": tradeflow_tools.get_drop_shipping_chain,
    "list_logistics_events": tradeflow_tools.list_logistics_events,
    "calculate_order_margin": tradeflow_tools.calculate_order_margin,
    "detect_order_risk": tradeflow_tools.detect_order_risk,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    failures = []
    for case in cases:
        tool_name = case["tool_name"]
        tool = TOOL_REGISTRY[tool_name]
        result = tool(**case.get("input", {}))
        errors = _compare_expected_outputs(result, case.get("expected_key_outputs", {}))
        errors.extend(_compare_expected_risk_flags(result, case.get("expected_risk_flags", [])))
        if errors:
            failures.append((case["case_id"], errors))
            print(f"FAIL {case['case_id']}: {case['description']}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {case['case_id']}: {case['description']}")

    passed = len(cases) - len(failures)
    print(f"\nTool eval summary: {passed}/{len(cases)} passed.")
    return 1 if failures else 0


def _compare_expected_outputs(result: Any, expected_outputs: dict[str, Any]) -> list[str]:
    errors = []
    for path, expected_value in expected_outputs.items():
        if path == "$length":
            actual_value = len(result)
        elif path.startswith("$all."):
            field_path = path.removeprefix("$all.")
            actual_value = [_resolve_path(item, field_path) for item in result]
            if any(value != expected_value for value in actual_value):
                errors.append(f"{path}: expected all values to be {expected_value!r}, got {actual_value!r}")
                continue
            continue
        else:
            actual_value = _resolve_path(result, path)
        if actual_value != expected_value:
            errors.append(f"{path}: expected {expected_value!r}, got {actual_value!r}")
    return errors


def _compare_expected_risk_flags(result: Any, expected_flags: list[str]) -> list[str]:
    if not expected_flags:
        return []
    actual_flags = set(result.get("risk_flags", []))
    missing = [flag for flag in expected_flags if flag not in actual_flags]
    if missing:
        return [f"missing expected risk flags {missing!r}; got {sorted(actual_flags)!r}"]
    return []


def _resolve_path(value: Any, path: str) -> Any:
    current = value
    for segment in path.split("."):
        if segment.isdigit():
            current = current[int(segment)]
        else:
            current = current[segment]
    return current


if __name__ == "__main__":
    raise SystemExit(main())
