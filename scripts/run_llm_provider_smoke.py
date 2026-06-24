"""Manual local smoke test for the real LLM planner provider.

This script is intentionally not part of automated tests. It requires local
environment variables and never executes business actions directly.
"""

from __future__ import annotations

from pathlib import Path
import os
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.llm_planner import plan_and_execute_user_request


REQUIRED_ENV_VARS = ("TRADEFLOW_LLM_PROVIDER", "TRADEFLOW_LLM_MODEL", "TRADEFLOW_LLM_API_KEY")


def main() -> int:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        print("Refusing to run real LLM smoke test; missing environment variables:")
        for name in missing:
            print(f"- {name}")
        return 2

    result = plan_and_execute_user_request(
        "Analyze sales order SO-1005",
        use_llm=True,
        planner_provider_selection="llm",
    )
    print(f"Provider requested: {result.trace.provider_requested}")
    print(f"Provider used: {result.trace.provider_used}")
    print(f"Fallback used: {result.trace.fallback_used}")
    print(f"Fallback reason: {result.trace.fallback_reason or 'none'}")
    print(f"Planner route: {result.trace.selected_route or 'none'}")
    print(f"Risk level: {result.trace.risk_level or 'unavailable'}")
    print(f"Recommended action: {result.trace.recommended_action or 'unavailable'}")
    print(f"Approval state: {result.trace.approval_state or 'unavailable'}")
    print(f"Safety outcome: {result.trace.safety_outcome}")
    print(f"Reason codes: {', '.join(result.trace.reason_codes) if result.trace.reason_codes else 'none'}")
    print(result.grounded_response.summary)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
