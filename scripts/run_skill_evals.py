"""Run Sprint 006 deterministic domain-skill trigger evals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.domain_skills import SkillTriggerCase, evaluate_trigger_case, list_available_skills


DEFAULT_CASES_PATH = Path("evals/sprint_006_skill_trigger_cases.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--min-overall-pass-rate", type=float, default=1.0)
    args = parser.parse_args()

    payload = json.loads(args.cases.read_text(encoding="utf-8"))
    dataset_version = payload["dataset_version"]
    cases = [
        SkillTriggerCase(
            case_id=case["case_id"],
            user_request=case["user_request"],
            expected_skill=case.get("expected_skill"),
            focus_skill=case.get("focus_skill"),
        )
        for case in payload["cases"]
    ]
    catalog = list_available_skills()
    failures = []
    positive_total = 0
    positive_passed = 0
    negative_total = 0
    negative_passed = 0
    per_skill_totals = {skill.name: 0 for skill in catalog.skills}
    per_skill_passed = {skill.name: 0 for skill in catalog.skills}

    for raw_case, case in zip(payload["cases"], cases, strict=True):
        result = evaluate_trigger_case(case, catalog)
        skill_name = raw_case["skill"]
        polarity = raw_case["polarity"]
        per_skill_totals[skill_name] += 1
        per_skill_passed[skill_name] += int(result.passed)
        if polarity == "positive":
            positive_total += 1
            positive_passed += int(result.passed)
        else:
            negative_total += 1
            negative_passed += int(result.passed)

        if result.passed:
            print(f"PASS {case.case_id}: matched {result.matched_skill or 'none'}")
        else:
            failures.append(result)
            print(
                f"FAIL {case.case_id}: expected {case.expected_skill or 'not ' + (case.focus_skill or 'any skill')}, "
                f"got {result.matched_skill or 'none'}"
            )
            print(f"  scores: {result.score_by_skill}")

    passed_cases = len(cases) - len(failures)
    overall_pass_rate = passed_cases / len(cases) if cases else 0.0
    trigger_accuracy = positive_passed / positive_total if positive_total else 0.0
    negative_accuracy = negative_passed / negative_total if negative_total else 0.0

    print(f"\nSkill eval dataset: {dataset_version}")
    print(f"Skill eval summary: {passed_cases}/{len(cases)} passed ({overall_pass_rate:.1%}).")
    print("Metrics:")
    print(f"- trigger_accuracy: {positive_passed}/{positive_total} ({trigger_accuracy:.1%})")
    print(f"- negative_trigger_accuracy: {negative_passed}/{negative_total} ({negative_accuracy:.1%})")
    for skill_name in sorted(per_skill_totals):
        total = per_skill_totals[skill_name]
        passed = per_skill_passed[skill_name]
        print(f"- {skill_name}_pass_rate: {passed}/{total} ({passed / total:.1%})")

    threshold_failed = overall_pass_rate < args.min_overall_pass_rate
    if threshold_failed:
        print(
            f"\nOverall pass rate {overall_pass_rate:.1%} is below required "
            f"{args.min_overall_pass_rate:.1%}.",
            file=sys.stderr,
        )
    return 1 if failures or threshold_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
