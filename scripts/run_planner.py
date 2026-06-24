"""Run the Sprint 4 constrained planner over the order-risk workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.llm_planner import plan_and_execute_user_request


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_text", nargs="?", help='Business request, such as "Analyze sales order SO-1005"')
    parser.add_argument("--request", help='Business request, such as "Analyze sales order SO-1005"')
    parser.add_argument("--dataset-path", type=Path, default=None)
    parser.add_argument("--approval-storage-path", type=Path, default=None)
    parser.add_argument("--audit-log-path", type=Path, default=None)
    parser.add_argument("--use-llm", action="store_true", help="Use the configured real LLM provider.")
    parser.add_argument(
        "--provider",
        choices=["deterministic", "mock", "llm"],
        default=None,
        help="Override TRADEFLOW_PLANNER_PROVIDER for this run.",
    )
    parser.add_argument("--show-trace", action="store_true", help="Print provider and fallback trace metadata.")
    args = parser.parse_args()
    request_text = args.request or args.request_text
    if not request_text:
        parser.error("a request is required, either as --request or as a positional argument")

    result = plan_and_execute_user_request(
        user_request=request_text,
        dataset_path=str(args.dataset_path) if args.dataset_path else None,
        use_llm=args.use_llm or args.provider == "llm",
        planner_provider_selection=args.provider,
        approval_storage_path=args.approval_storage_path,
        audit_log_path=args.audit_log_path,
    )

    decision = result.planner_decision
    response = result.grounded_response
    metadata = result.planner_metadata
    trace = result.trace
    print(f"Planner version: {metadata.planner_version}")
    print(f"Prompt version: {metadata.prompt_template_version}")
    print(f"Provider: {metadata.provider_name} ({metadata.provider_mode})")
    print(f"Provider requested: {metadata.provider_requested}")
    print(f"Provider used: {metadata.provider_used}")
    print(f"Fallback used: {metadata.fallback_used}")
    if metadata.fallback_reason:
        print(f"Fallback reason: {metadata.fallback_reason}")
    print(f"Trace id: {trace.trace_id}")
    print(f"Planner intent: {decision.intent}")
    print(f"Selected workflow: {decision.selected_workflow or 'none'}")
    print(f"Extracted sales order id: {decision.extracted_sales_order_id or 'none'}")

    if result.workflow_result is not None:
        workflow = result.workflow_result
        print(f"Risk level: {workflow.risk_level}")
        print(f"Risk flags: {', '.join(workflow.risk_flags) if workflow.risk_flags else 'none'}")
        print(
            "Recommended action: "
            f"{workflow.recommended_action.action_type} ({workflow.recommended_action.priority})"
        )
        print(f"Approval request id: {workflow.approval_request.approval_id}")
        print(f"Approval status: {workflow.approval_request.status}")
    else:
        print("Risk level: unavailable")
        print("Recommended action: unavailable")
        print("Approval request id: unavailable")
        print("Approval status: unavailable")
    print(f"Safety outcome: {result.safety_outcome}")
    print(f"Reason codes: {', '.join(trace.reason_codes) if trace.reason_codes else 'none'}")

    if args.show_trace:
        print("\nProvider trace:")
        print(f"- provider_requested: {trace.provider_requested}")
        print(f"- provider_used: {trace.provider_used}")
        print(f"- fallback_used: {trace.fallback_used}")
        print(f"- fallback_reason: {trace.fallback_reason or 'none'}")
        print(f"- llm_response_valid: {trace.llm_response_valid}")
        print(
            "- llm_validation_errors: "
            f"{'; '.join(trace.llm_validation_errors) if trace.llm_validation_errors else 'none'}"
        )

    print("\nGrounded response:")
    print(response.summary)
    print(response.recommendation)

    print("\nCited evidence:")
    if response.cited_evidence:
        for citation in response.cited_evidence:
            print(
                f"- {citation.source_type}:{citation.field_path} = "
                f"{citation.value!r} ({citation.explanation})"
            )
    else:
        print("- none")

    print("\nSafety checks:")
    for check in result.safety_checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"- {status} {check.check_name}: {check.reason}")

    if not result.success and result.error:
        print(f"\nPlanner execution failed: {result.error}", file=sys.stderr)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
