"""Run the judge-facing TradeFlow AgentOS demo from a scenario JSON file."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.demo_agent import load_demo_input, response_to_json, run_tradeflow_agent_demo


DEFAULT_RUNTIME_DIR = REPO_ROOT / "artifacts" / "demo_runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to an examples/demo/*.json scenario.")
    parser.add_argument("--json", action="store_true", help="Emit the full demo response as JSON.")
    parser.add_argument("--dataset-path", type=Path, default=None)
    parser.add_argument("--approval-storage-path", type=Path, default=None)
    parser.add_argument("--audit-log-path", type=Path, default=None)
    parser.add_argument(
        "--provider",
        choices=["deterministic", "llm"],
        default="deterministic",
        help="Use deterministic offline mode by default; choose llm to try the configured provider with fallback.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario = load_demo_input(args.input)
    approval_path = args.approval_storage_path or DEFAULT_RUNTIME_DIR / "approval_requests.json"
    audit_path = args.audit_log_path or DEFAULT_RUNTIME_DIR / "planner_audit.jsonl"
    response = run_tradeflow_agent_demo(
        scenario,
        dataset_path=args.dataset_path,
        planner_provider_selection=args.provider,
        use_llm=args.provider == "llm",
        approval_storage_path=approval_path,
        audit_log_path=audit_path,
    )

    if args.json:
        print(response_to_json(response), end="")
    else:
        _print_human_response(response)
    return 0 if response.success else 1


def _print_human_response(response) -> None:
    print(f"Case: {response.case_id}")
    print(f"Goal: {response.user_goal}")
    print(f"Summary: {response.agent_summary}")
    print(f"Risk level: {response.risk_level}")
    print(f"Risk factors: {', '.join(response.risk_factors) if response.risk_factors else 'none'}")
    if isinstance(response.recommended_action, str):
        print(f"Recommended action: {response.recommended_action}")
    else:
        action = response.recommended_action
        print(f"Recommended action: {action.action_type} ({action.priority})")
        print(f"Action detail: {action.message}")
    print(f"Approval required: {response.approval_required}")
    if response.approval_reason:
        print(f"Approval reason: {response.approval_reason}")
    print(f"Tools/skills used: {', '.join(response.tools_or_skills_used)}")
    print(f"Evidence refs: {', '.join(response.evidence_refs) if response.evidence_refs else 'none'}")
    print(f"Trace id: {response.trace_refs['trace_id']}")
    if not response.success and response.error:
        print(f"Error: {response.error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
