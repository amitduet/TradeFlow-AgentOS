"""Build a deterministic AgentOps evidence index for capstone review."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.redaction import redact_data


DEFAULT_JSON_OUT = REPO_ROOT / "artifacts" / "capstone" / "agentops_evidence_index.json"
DEFAULT_MD_OUT = REPO_ROOT / "artifacts" / "capstone" / "agentops_evidence_index.md"
DEFAULT_GENERATED_AT = "1970-01-01T00:00:00+00:00"

EVIDENCE_SOURCES = {
    "quality_gate": {
        "label": "Latest quality gate result",
        "directory": REPO_ROOT / "artifacts" / "quality_gate",
        "required": True,
        "patterns": ("latest.json", "quality_gate_*.json", "*.json"),
    },
    "security_evals": {
        "label": "Latest security eval result",
        "directory": REPO_ROOT / "artifacts" / "security_evals",
        "required": False,
        "patterns": ("latest.json", "security_eval_*.json", "*.json"),
    },
    "guardrail_enforcement": {
        "label": "Latest guardrail enforcement eval result",
        "directory": REPO_ROOT / "artifacts" / "guardrail_enforcement",
        "required": False,
        "patterns": ("latest.json", "guardrail*.json", "*.json"),
    },
    "approval_workflow_evals": {
        "label": "Latest approval workflow eval result",
        "directory": REPO_ROOT / "artifacts" / "approval_workflow_evals",
        "required": False,
        "patterns": ("latest.json", "approval_workflow_eval_*.json", "*.json"),
    },
    "release_evidence": {
        "label": "Latest release evidence pack",
        "directory": REPO_ROOT / "artifacts" / "release_evidence",
        "required": False,
        "patterns": ("latest/release_evidence.json", "*/release_evidence.json", "*.json"),
    },
    "quality_history": {
        "label": "Latest quality history summary",
        "directory": REPO_ROOT / "artifacts" / "quality_history",
        "required": False,
        "patterns": ("latest.json", "quality_trend_summary.json", "*.json"),
    },
}

VERIFICATION_COMMANDS = [
    ".venv/bin/python -m pytest -q",
    ".venv/bin/python scripts/run_planner_evals.py",
    ".venv/bin/python scripts/run_skill_evals.py",
    ".venv/bin/python scripts/run_llm_provider_smoke.py",
    ".venv/bin/python scripts/run_security_evals.py",
    ".venv/bin/python scripts/run_guardrail_enforcement_evals.py",
    ".venv/bin/python scripts/check_capstone_readiness.py",
    ".venv/bin/python scripts/run_agent_quality_gate.py",
    ".venv/bin/python scripts/summarize_quality_history.py",
    ".venv/bin/python scripts/build_release_evidence_pack.py",
    ".venv/bin/python scripts/build_agentops_evidence_index.py",
    ".venv/bin/python scripts/build_agentops_dashboard.py",
]

KNOWN_SKIPPED_CHECKS = [
    {
        "name": "llm_provider_smoke",
        "status": "skipped_by_default",
        "reason": "Live provider smoke requires explicit opt-in and local credentials; default runs make no network calls.",
    }
]


def build_evidence_index(*, generated_at: str | None = None, strict: bool = False) -> tuple[int, dict[str, Any]]:
    timestamp = generated_at or datetime.now(UTC).isoformat()
    evidence: dict[str, Any] = {}
    warnings: list[str] = []

    for key, spec in EVIDENCE_SOURCES.items():
        entry = _build_source_entry(key, spec)
        evidence[key] = entry
        if entry["status"] == "missing":
            severity = "required" if spec["required"] else "optional"
            warnings.append(f"Missing {severity} evidence: {spec['label']} ({_repo_path(spec['directory'])})")

    summary = _rollup(evidence)
    index = redact_data(
        {
            "schema_version": "1.0",
            "project_name": "TradeFlow AgentOS",
            "capstone_track_recommendation": "Agents for Business",
            "generated_at_utc": timestamp,
            "sources": evidence,
            "source_artifact_filenames": {
                name: entry.get("source_artifact_filename") for name, entry in evidence.items() if entry.get("source_artifact_filename")
            },
            "summary": summary,
            "warnings": warnings,
            "known_skipped_checks": KNOWN_SKIPPED_CHECKS,
            "verification_commands": VERIFICATION_COMMANDS,
            "known_limitations": [
                "Evidence is generated from local deterministic artifacts and may be incomplete until the full quality gate has run.",
                "Live provider smoke is skipped by default to keep CI no-network and secrets-safe.",
                "The dashboard is a static local artifact, not a production monitoring service.",
            ],
        }
    )

    has_missing_required = any(entry["status"] == "missing" and EVIDENCE_SOURCES[name]["required"] for name, entry in evidence.items())
    return (1 if strict and has_missing_required else 0), index


def write_json(index: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_data(index), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_markdown(index: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(index), encoding="utf-8")
    return path


def render_markdown(index: dict[str, Any]) -> str:
    summary = index["summary"]
    lines = [
        "# TradeFlow AgentOS AgentOps Evidence Index",
        "",
        f"Generated: {index['generated_at_utc']}",
        f"Capstone track recommendation: {index['capstone_track_recommendation']}",
        f"Overall status: {summary['overall_status']}",
        f"Pass/fail/skip/missing: {summary['passed']}/{summary['failed']}/{summary['skipped']}/{summary['missing']}",
        "",
        "## Evidence Sources",
        "",
        "| Evidence | Status | Source | Summary |",
        "| --- | --- | --- | --- |",
    ]
    for name, source in index["sources"].items():
        lines.append(
            f"| {source['label']} | {source['status']} | `{source.get('source_artifact_filename') or 'n/a'}` | "
            f"{_md_cell(source.get('summary') or '')} |"
        )

    lines.extend(["", "## Warnings", ""])
    if index.get("warnings"):
        lines.extend(f"- {warning}" for warning in index["warnings"])
    else:
        lines.append("- None.")

    lines.extend(["", "## Known Skipped Checks", ""])
    for skipped in index["known_skipped_checks"]:
        lines.append(f"- `{skipped['name']}`: {skipped['reason']}")

    lines.extend(["", "## Verification Commands", ""])
    lines.extend(f"- `{command}`" for command in index["verification_commands"])

    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in index["known_limitations"])
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--generated-at", default=None, help="Deterministic timestamp override for tests.")
    parser.add_argument("--strict", action="store_true", help="Fail when required evidence is missing.")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, index = build_evidence_index(generated_at=args.generated_at, strict=args.strict)
    write_json(index, args.json_out)
    write_markdown(index, args.md_out)
    if not args.quiet:
        print(f"Wrote AgentOps evidence index JSON to {args.json_out}")
        print(f"Wrote AgentOps evidence index Markdown to {args.md_out}")
        for warning in index["warnings"]:
            print(f"WARNING: {warning}")
    return exit_code


def _build_source_entry(key: str, spec: dict[str, Any]) -> dict[str, Any]:
    path = _latest_json(spec["directory"], spec["patterns"])
    if path is None:
        return {
            "key": key,
            "label": spec["label"],
            "status": "missing",
            "required": spec["required"],
            "source_artifact_filename": None,
            "summary": "Evidence artifact not found.",
            "counts": {},
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "key": key,
            "label": spec["label"],
            "status": "failed",
            "required": spec["required"],
            "source_artifact_filename": _repo_path(path),
            "summary": f"Could not parse evidence artifact: {exc}",
            "counts": {},
        }
    if not isinstance(payload, dict):
        status = "failed"
        summary = "Evidence artifact root is not an object."
        counts: dict[str, Any] = {}
    else:
        status = _status_from_payload(payload)
        summary = str(payload.get("summary") or payload.get("latest_run_status") or payload.get("release_name") or status)
        counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}

    return redact_data(
        {
            "key": key,
            "label": spec["label"],
            "status": status,
            "required": spec["required"],
            "source_artifact_filename": _repo_path(path),
            "summary": summary,
            "counts": counts,
        }
    )


def _latest_json(directory: Path, patterns: Sequence[str]) -> Path | None:
    if not directory.exists():
        return None
    candidates: dict[Path, None] = {}
    for pattern in patterns:
        for path in directory.glob(pattern):
            if path.is_file() and path.suffix == ".json":
                candidates[path] = None
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (_payload_sort_key(path), path.name))[-1]


def _payload_sort_key(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return path.name
    if not isinstance(payload, dict):
        return path.name
    return str(
        payload.get("finished_at_utc")
        or payload.get("timestamp_utc")
        or payload.get("generated_at_utc")
        or payload.get("generated_at")
        or path.name
    )


def _status_from_payload(payload: dict[str, Any]) -> str:
    status = str(payload.get("overall_status") or payload.get("status") or payload.get("latest_run_status") or "present")
    if status == "passed":
        return "passed"
    if status == "failed":
        return "failed"
    if status == "skipped":
        return "skipped"
    return "present"


def _rollup(evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "passed": sum(1 for source in evidence.values() if source["status"] == "passed"),
        "failed": sum(1 for source in evidence.values() if source["status"] == "failed"),
        "skipped": sum(1 for source in evidence.values() if source["status"] == "skipped"),
        "missing": sum(1 for source in evidence.values() if source["status"] == "missing"),
        "present": sum(1 for source in evidence.values() if source["status"] == "present"),
        "total": len(evidence),
    }
    required_missing = [name for name, source in evidence.items() if source["status"] == "missing" and source["required"]]
    overall = "failed" if counts["failed"] or required_missing else "passed"
    return {**counts, "overall_status": overall, "required_missing": required_missing}


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
