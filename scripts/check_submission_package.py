"""Validate the final Kaggle capstone submission package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Sequence

from app.agents.demo_data import load_demo_business_data


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs" / "capstone"
README = REPO_ROOT / "README.md"
DEMO_RUNNER = REPO_ROOT / "scripts" / "run_tradeflow_agent_demo.py"
DEMO_UI_RUNNER = REPO_ROOT / "scripts" / "run_tradeflow_agent_demo_ui.py"
DEMO_INPUTS_DIR = REPO_ROOT / "examples" / "demo"
DEMO_DATA_DIR = DEMO_INPUTS_DIR / "data"
REQUIRED_DEMO_INPUTS = [
    "low_risk_order.json",
    "medium_risk_order.json",
    "high_risk_order.json",
]
REQUIRED_DEMO_DATA_FILES = [
    "demo_products.json",
    "demo_customers.json",
    "demo_inventory.json",
    "demo_finance_opening_balance.json",
]
DEMO_RUN_COMMAND = ".venv/bin/python scripts/run_tradeflow_agent_demo.py --input examples/demo/high_risk_order.json --json"
DEMO_UI_COMMAND = ".venv/bin/python scripts/run_tradeflow_agent_demo_ui.py"
DEMO_UI_URL = "http://127.0.0.1:8765"
QUALITY_GATE_COMMAND = ".venv/bin/python scripts/run_agent_quality_gate.py"
SETUP_COMMAND = 'pip install -e ".[dev]"'
REQUIRED_DOCS = {
    "kaggle_writeup": "kaggle_writeup.md",
    "video_script": "video_script_5min.md",
    "media_checklist": "media_gallery_checklist.md",
    "capstone_index": "README.md",
}
PLACEHOLDER_PATTERN = re.compile(r"(?i)\b(TODO|FIXME|TBD)\b|<insert[^>]*>")
ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![`A-Za-z0-9_./-])(?:/Users/|/home/|/var/folders/|[A-Za-z]:\\)")
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}|"
    r"sk-[A-Za-z0-9]{12,}|"
    r"ghp_[A-Za-z0-9]{12,}"
)


def run_submission_checks(*, docs_dir: Path = DOCS_DIR, readme_path: Path = README) -> tuple[int, dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    docs = {key: docs_dir / filename for key, filename in REQUIRED_DOCS.items()}

    for key, path in docs.items():
        checks.append(_check(f"doc_exists:{path.name}", path.exists(), _rel(path)))

    writeup = docs["kaggle_writeup"]
    word_count = _word_count(writeup) if writeup.exists() else 0
    checks.append(_check("kaggle_writeup_under_2500_words", 0 < word_count < 2500, f"{word_count} words"))

    video_text = _read(docs["video_script"])
    checks.append(
        _check(
            "video_script_has_required_timing_blocks",
            all(marker in video_text for marker in ["0:00", "0:30", "1:15", "2:15", "3:05", "4:05", "4:40", "5:00"]),
            _rel(docs["video_script"]),
        )
    )
    checks.append(
        _check(
            "video_script_references_cli_demo_command",
            DEMO_RUN_COMMAND in video_text,
            f"{_rel(docs['video_script'])} must include {DEMO_RUN_COMMAND}",
        )
    )
    checks.append(
        _check(
            "video_script_references_ui_demo_command",
            DEMO_UI_COMMAND in video_text and DEMO_UI_URL in video_text,
            f"{_rel(docs['video_script'])} must include {DEMO_UI_COMMAND} and {DEMO_UI_URL}",
        )
    )

    readme_text = _read(readme_path)
    checks.append(
        _check(
            "readme_has_for_kaggle_judges_section",
            "## For Kaggle Judges" in readme_text,
            _rel(readme_path),
        )
    )
    checks.append(
        _check(
            "readme_has_demo_run_command",
            DEMO_RUN_COMMAND in readme_text,
            _rel(readme_path),
        )
    )
    checks.append(_check("readme_has_setup_command", SETUP_COMMAND in readme_text, _rel(readme_path)))
    checks.append(_check("readme_has_quality_gate_command", QUALITY_GATE_COMMAND in readme_text, _rel(readme_path)))
    checks.append(_check("readme_has_ui_demo_command", DEMO_UI_COMMAND in readme_text, _rel(readme_path)))
    checks.append(_check("readme_has_ui_url", DEMO_UI_URL in readme_text, _rel(readme_path)))
    checks.append(
        _check(
            "readme_notes_no_external_services_or_production_data",
            "external services" in readme_text.lower() and "production data" in readme_text.lower(),
            _rel(readme_path),
        )
    )
    checks.append(
        _check(
            "readme_notes_optional_llm_and_deterministic_default",
            "llm planner mode is optional" in readme_text.lower()
            and "deterministic fallback" in readme_text.lower(),
            _rel(readme_path),
        )
    )
    checks.append(
        _check(
            "readme_summarizes_high_risk_behavior",
            all(
                phrase in readme_text.lower()
                for phrase in ["risk classification", "deterministic tool", "approval escalation", "guardrail/audit"]
            ),
            _rel(readme_path),
        )
    )
    checks.append(_check("demo_runner_exists", DEMO_RUNNER.exists(), _rel(DEMO_RUNNER)))
    checks.append(_check("demo_ui_runner_exists", DEMO_UI_RUNNER.exists(), _rel(DEMO_UI_RUNNER)))
    for filename in REQUIRED_DEMO_INPUTS:
        path = DEMO_INPUTS_DIR / filename
        checks.append(_check(f"demo_input_exists:{filename}", path.exists(), _rel(path)))
    for filename in REQUIRED_DEMO_DATA_FILES:
        path = DEMO_DATA_DIR / filename
        checks.append(_check(f"demo_data_exists:{filename}", path.exists(), _rel(path)))
    demo_data = _load_demo_data_for_checks()
    checks.append(
        _check(
            "demo_data_has_10_products",
            demo_data is not None and len(demo_data["products"]) == 10,
            "examples/demo/data/demo_products.json should contain exactly 10 products",
        )
    )
    checks.append(
        _check(
            "demo_data_has_10_customers",
            demo_data is not None and len(demo_data["customers"]) == 10,
            "examples/demo/data/demo_customers.json should contain exactly 10 customers",
        )
    )
    checks.append(
        _check(
            "demo_data_inventory_refs_products",
            demo_data is not None and _inventory_refs_known_products(demo_data),
            "every demo inventory product_code must exist in demo_products.json",
        )
    )
    checks.append(
        _check(
            "demo_data_opening_cash_balance",
            demo_data is not None
            and demo_data["finance_opening_balance"].get("currency") == "USD"
            and demo_data["finance_opening_balance"].get("opening_cash_balance") == 100000,
            "finance opening balance must be exactly 100000 USD",
        )
    )
    checks.append(
        _check(
            "demo_inputs_reference_demo_data",
            demo_data is not None and _demo_inputs_reference_demo_data(demo_data),
            "demo order examples must reference valid demo product_code and customer_id values",
        )
    )
    checks.append(_check("demo_runs_offline", _demo_runs_offline(), "high_risk_order.json deterministic run"))

    index_text = _read(docs["capstone_index"])
    for filename in ["kaggle_writeup.md", "video_script_5min.md", "media_gallery_checklist.md"]:
        checks.append(_check(f"capstone_index_links:{filename}", filename in index_text, _rel(docs["capstone_index"])))
    checks.append(
        _check(
            "capstone_index_links_judge_quickstart",
            "For Kaggle Judges" in index_text and "README.md" in index_text,
            _rel(docs["capstone_index"]),
        )
    )
    checks.append(
        _check(
            "capstone_index_documents_runnable_demo",
            DEMO_RUN_COMMAND in index_text and DEMO_UI_COMMAND in index_text and DEMO_UI_URL in index_text,
            _rel(docs["capstone_index"]),
        )
    )

    writeup_text = _read(writeup)
    checks.append(
        _check(
            "kaggle_writeup_selects_agents_for_business",
            "agents for business" in writeup_text.lower(),
            _rel(writeup),
        )
    )
    checks.append(
        _check(
            "kaggle_writeup_mentions_deterministic_and_optional_llm",
            "deterministic" in writeup_text.lower() and "optional" in writeup_text.lower() and "provider" in writeup_text.lower(),
            _rel(writeup),
        )
    )
    checks.append(
        _check(
            "kaggle_writeup_mentions_evaluation_suite",
            all(
                phrase in writeup_text.lower()
                for phrase in ["planner evals", "skill", "security evals", "approval workflow", "quality gate"]
            ),
            _rel(writeup),
        )
    )

    media_text = _read(docs["media_checklist"])
    for phrase in [
        "README judge quickstart",
        "CLI high-risk JSON output",
        "Local UI home page",
        "Local UI scenario list",
        "Local UI high-risk result",
        "Quality gate terminal result",
        "Capstone readiness",
        "Submission Package",
        "Architecture and Evidence",
    ]:
        checks.append(
            _check(
                f"media_checklist_includes:{_slug(phrase)}",
                phrase.lower() in media_text.lower(),
                f"{_rel(docs['media_checklist'])} should list {phrase}",
            )
        )

    submission_doc_paths = sorted(path for path in docs_dir.glob("*.md")) if docs_dir.exists() else []
    for path in submission_doc_paths:
        text = _read(path)
        checks.append(_check(f"no_placeholder_markers:{path.name}", not PLACEHOLDER_PATTERN.search(text), _rel(path)))
        checks.append(_check(f"no_local_absolute_paths:{path.name}", not ABSOLUTE_PATH_PATTERN.search(text), _rel(path)))
        checks.append(_check(f"no_obvious_secrets:{path.name}", not SECRET_PATTERN.search(text), _rel(path)))

    report = {
        "schema_version": "1.0",
        "status": "failed" if any(not check["passed"] for check in checks) else "passed",
        "summary": f"{sum(1 for check in checks if check['passed'])}/{len(checks)} submission package checks passed",
        "counts": {
            "total": len(checks),
            "passed": sum(1 for check in checks if check["passed"]),
            "failed": sum(1 for check in checks if not check["passed"]),
        },
        "checks": checks,
    }
    return (0 if report["status"] == "passed" else 1), report


def write_json(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, report = run_submission_checks()
    if args.json_out:
        write_json(report, args.json_out)
    if not args.quiet:
        print("Submission Package Summary")
        print(f"Status: {report['status']}")
        print(f"Summary: {report['summary']}")
        for check in report["checks"]:
            if not check["passed"]:
                print(f"FAIL {check['name']}: {check['detail']}")
    elif report["status"] != "passed":
        print(f"Submission package {report['status']}: {report['summary']}")
    return exit_code


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "status": "passed" if passed else "failed", "detail": detail}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _word_count(path: Path) -> int:
    return len(re.findall(r"\b[\w'-]+\b", _read(path)))


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _demo_runs_offline() -> bool:
    if not DEMO_RUNNER.exists() or not (DEMO_INPUTS_DIR / "high_risk_order.json").exists():
        return False
    with tempfile.TemporaryDirectory(prefix="tradeflow-demo-check-") as tmp:
        approval_path = Path(tmp) / "approval_requests.json"
        audit_path = Path(tmp) / "planner_audit.jsonl"
        completed = subprocess.run(
            [
                sys.executable,
                str(DEMO_RUNNER),
                "--input",
                str(DEMO_INPUTS_DIR / "high_risk_order.json"),
                "--json",
                "--approval-storage-path",
                str(approval_path),
                "--audit-log-path",
                str(audit_path),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    if completed.returncode != 0:
        return False
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False
    return (
        payload.get("case_id") == "demo-high-risk-order"
        and payload.get("risk_level") == "high"
        and payload.get("approval_required") is True
    )


def _load_demo_data_for_checks() -> dict[str, Any] | None:
    try:
        return load_demo_business_data(DEMO_DATA_DIR)
    except ValueError:
        return None


def _inventory_refs_known_products(demo_data: dict[str, Any]) -> bool:
    product_codes = {product["product_code"] for product in demo_data["products"]}
    return all(record["product_code"] in product_codes for record in demo_data["inventory"])


def _demo_inputs_reference_demo_data(demo_data: dict[str, Any]) -> bool:
    product_codes = {product["product_code"] for product in demo_data["products"]}
    customer_ids = {customer["customer_id"] for customer in demo_data["customers"]}
    for filename in REQUIRED_DEMO_INPUTS:
        try:
            payload = json.loads((DEMO_INPUTS_DIR / filename).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return False
        context = payload.get("business_context", {})
        if context.get("product_code") not in product_codes or context.get("customer_id") not in customer_ids:
            return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
