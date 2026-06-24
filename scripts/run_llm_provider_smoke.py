"""Run opt-in Sprint 008 LLM provider smoke evals.

Default mode performs no live provider call and exits successfully with a skip.
Use --live or TRADEFLOW_LLM_SMOKE_ENABLED=true to call a configured provider.
Use --fake-provider for deterministic local tests without network access.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.llm_provider_smoke import (
    DEFAULT_SMOKE_CASES_PATH,
    SmokeRunOptions,
    run_provider_smoke,
)
from app.agents.redaction import redact_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Run live provider smoke when credentials are configured.")
    parser.add_argument(
        "--fake-provider",
        choices=["success", "invalid-json", "schema-violation", "timeout", "unsafe"],
        default=None,
        help="Run deterministic smoke cases with a fake provider response mode.",
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_SMOKE_CASES_PATH)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--provider", choices=["openai", "gemini", "custom"], default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument("--write-report", action="store_true", help="Write a sanitized local JSON report.")
    parser.add_argument("--report-path", type=Path, default=None)
    args = parser.parse_args()

    summary = run_provider_smoke(
        SmokeRunOptions(
            live=args.live,
            fake_provider_mode=args.fake_provider,  # type: ignore[arg-type]
            cases_path=args.cases,
            report_path=args.report_path,
            write_report=args.write_report,
            max_cases=args.max_cases,
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
        )
    )

    print(f"LLM provider smoke dataset: {summary.dataset_version or 'unknown'}")
    print(f"Mode: {summary.mode}")
    print(f"Status: {summary.status}")
    if summary.skip_reason:
        print(f"Skip reason: {redact_text(summary.skip_reason)}")
    print(
        "Summary: "
        f"{summary.cases_passed}/{summary.cases_total} passed, "
        f"{summary.cases_failed} failed, {summary.cases_skipped} skipped"
    )
    if summary.report_path:
        print(f"Report: {summary.report_path}")

    for result in summary.results:
        if result["status"] == "skipped":
            print(f"SKIPPED {result['case_id']}: {redact_text(result.get('skip_reason'))}")
            continue
        print(
            f"{result['status'].upper()} {result['case_id']}: "
            f"provider_used={result['provider_used']} fallback={result['fallback_used']} "
            f"safety={result['safety_outcome']} route={result['planner_route']}"
        )
        for error in result["errors"]:
            print(f"  - {redact_text(error)}")

    return summary.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
