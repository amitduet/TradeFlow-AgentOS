"""Check committed capstone assets for Kaggle submission readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs" / "capstone"
REQUIRED_DOCS = [
    "CAPSTONE_READINESS.md",
    "KAGGLE_WRITEUP_DRAFT.md",
    "DEMO_VIDEO_SCRIPT.md",
    "PUBLIC_REPO_CHECKLIST.md",
    "MEDIA_GALLERY_PLAN.md",
]
ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![`A-Za-z0-9_./-])(?:/Users/|/home/|/var/folders/|[A-Za-z]:\\)")
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}|"
    r"sk-[A-Za-z0-9]{12,}|"
    r"ghp_[A-Za-z0-9]{12,}"
)


def run_readiness_checks(*, docs_dir: Path = DOCS_DIR) -> tuple[int, dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    docs = {name: docs_dir / name for name in REQUIRED_DOCS}

    for name, path in docs.items():
        checks.append(_check(name=f"doc_exists:{name}", passed=path.exists(), detail=_rel(path)))

    writeup = docs["KAGGLE_WRITEUP_DRAFT.md"]
    word_count = _word_count(writeup) if writeup.exists() else 0
    checks.append(_check("kaggle_writeup_under_2500_words", word_count > 0 and word_count < 2500, f"{word_count} words"))

    demo = docs["DEMO_VIDEO_SCRIPT.md"]
    demo_text = _read(demo)
    checks.append(_check("demo_script_has_timing_blocks", bool(re.search(r"\b0:00\b.*\b0:30\b", demo_text, re.S)), _rel(demo)))

    readme = _read(REPO_ROOT / "README.md")
    checks.append(
        _check(
            "readme_mentions_capstone_and_evaluation",
            "capstone" in readme.lower() and "evaluation" in readme.lower(),
            "README.md",
        )
    )

    gitignore = _read(REPO_ROOT / ".gitignore")
    checks.append(_check("gitignore_ignores_capstone_artifacts", "artifacts/capstone/" in gitignore, ".gitignore"))

    for path in sorted(docs_dir.glob("*.md")) if docs_dir.exists() else []:
        text = _read(path)
        checks.append(_check(f"no_local_absolute_paths:{path.name}", not ABSOLUTE_PATH_PATTERN.search(text), _rel(path)))
        checks.append(_check(f"no_obvious_secrets:{path.name}", not SECRET_PATTERN.search(text), _rel(path)))

    report = {
        "schema_version": "1.0",
        "status": "failed" if any(not check["passed"] for check in checks) else "passed",
        "summary": f"{sum(1 for check in checks if check['passed'])}/{len(checks)} capstone readiness checks passed",
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
    exit_code, report = run_readiness_checks()
    if args.json_out:
        write_json(report, args.json_out)
    if not args.quiet:
        print("Capstone Readiness Summary")
        print(f"Status: {report['status']}")
        print(f"Summary: {report['summary']}")
        for check in report["checks"]:
            if not check["passed"]:
                print(f"FAIL {check['name']}: {check['detail']}")
    elif report["status"] != "passed":
        print(f"Capstone readiness {report['status']}: {report['summary']}")
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


if __name__ == "__main__":
    raise SystemExit(main())
