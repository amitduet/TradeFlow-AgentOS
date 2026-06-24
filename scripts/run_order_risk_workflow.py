"""Run the deterministic Sprint 3 order-risk workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.order_risk_orchestrator import analyze_sales_order_risk


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sales-order-id", required=True)
    parser.add_argument("--dataset-path", type=Path, default=None)
    args = parser.parse_args()

    try:
        result = analyze_sales_order_risk(
            sales_order_id=args.sales_order_id,
            dataset_path=args.dataset_path,
        )
    except Exception as exc:
        print(f"Workflow execution failed: {exc}", file=sys.stderr)
        return 1

    print(f"Sales order: {result.sales_order_id}")
    print(f"Risk level: {result.risk_level}")
    print(f"Risk flags: {', '.join(result.risk_flags) if result.risk_flags else 'none'}")
    print(
        "Recommended action: "
        f"{result.recommended_action.action_type} "
        f"({result.recommended_action.priority})"
    )
    print(f"Approval request: {result.approval_request.approval_id} ({result.approval_request.status})")
    print("Tool-call trace:")
    for call in result.tool_call_trace:
        status = "ok" if call.success else "error"
        print(f"- {call.tool_name}: {status}, {call.latency_ms:.3f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
