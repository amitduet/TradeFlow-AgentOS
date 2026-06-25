"""Validate the final Kaggle capstone submission package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs" / "capstone"
README = REPO_ROOT / "README.md"
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
            all(marker in video_text for marker in ["0:00", "0:30", "1:15", "2:15", "3:15", "4:15", "5:00"]),
            _rel(docs["video_script"]),
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


if __name__ == "__main__":
    raise SystemExit(main())
