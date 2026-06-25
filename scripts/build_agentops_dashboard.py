"""Build a dependency-free static AgentOps dashboard from evidence JSON."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import html
import json
from pathlib import Path
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_JSON = REPO_ROOT / "artifacts" / "capstone" / "agentops_evidence_index.json"
DEFAULT_HTML_OUT = REPO_ROOT / "artifacts" / "capstone" / "agentops_dashboard.html"


def build_dashboard(*, evidence_json: Path = DEFAULT_EVIDENCE_JSON, html_out: Path = DEFAULT_HTML_OUT) -> dict[str, Any]:
    evidence = _load_json(evidence_json)
    html_text = render_dashboard(evidence)
    html_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(html_text, encoding="utf-8")
    return {"html_out": str(html_out), "project_name": evidence.get("project_name", "TradeFlow AgentOS")}


def render_dashboard(evidence: dict[str, Any]) -> str:
    sources = evidence.get("sources", {})
    summary = evidence.get("summary", {})
    generated_at = evidence.get("generated_at_utc") or datetime.now(UTC).isoformat()
    quality = sources.get("quality_gate", {})
    security = sources.get("security_evals", {})
    approval = sources.get("approval_workflow_evals") or sources.get("guardrail_enforcement", {})
    release = sources.get("release_evidence", {})
    commands = evidence.get("verification_commands", [])
    limitations = evidence.get("known_limitations", [])
    skipped = evidence.get("known_skipped_checks", [])

    source_rows = "\n".join(
        "<tr>"
        f"<td>{_e(source.get('label', name))}</td>"
        f"<td><span class=\"status status-{_status_class(source.get('status'))}\">{_e(source.get('status', 'unknown'))}</span></td>"
        f"<td>{_e(source.get('summary', ''))}</td>"
        f"<td><code>{_e(source.get('source_artifact_filename') or 'n/a')}</code></td>"
        "</tr>"
        for name, source in sorted(sources.items())
    )
    command_items = "\n".join(f"<li><code>{_e(command)}</code></li>" for command in commands)
    limitation_items = "\n".join(f"<li>{_e(item)}</li>" for item in limitations)
    skipped_items = "\n".join(f"<li><strong>{_e(item.get('name', 'check'))}</strong>: {_e(item.get('reason', ''))}</li>" for item in skipped)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TradeFlow AgentOS AgentOps Dashboard</title>
  <style>
    :root {{ color-scheme: light; --ink:#1f2933; --muted:#5f6b7a; --line:#d7dde5; --panel:#f7f9fb; --good:#176b3a; --bad:#a12622; --skip:#7a5a00; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: var(--ink); background: #ffffff; }}
    header {{ padding: 32px 40px 24px; border-bottom: 1px solid var(--line); background: var(--panel); }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px 24px 48px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; line-height: 1.15; }}
    h2 {{ margin: 28px 0 12px; font-size: 20px; }}
    p {{ line-height: 1.55; }}
    .meta {{ color: var(--muted); margin: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
    .panel {{ border: 1px solid var(--line); border-radius: 6px; padding: 16px; background: #fff; }}
    .label {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }}
    .value {{ font-size: 22px; font-weight: 700; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 10px 8px; vertical-align: top; }}
    th {{ font-size: 13px; color: var(--muted); }}
    code {{ background: #eef2f6; padding: 2px 5px; border-radius: 4px; overflow-wrap: anywhere; }}
    .status {{ font-weight: 700; }}
    .status-passed, .status-present {{ color: var(--good); }}
    .status-failed {{ color: var(--bad); }}
    .status-skipped, .status-missing {{ color: var(--skip); }}
    ul {{ padding-left: 22px; }}
  </style>
</head>
<body>
  <header>
    <h1>{_e(evidence.get('project_name', 'TradeFlow AgentOS'))}</h1>
    <p class="meta">Capstone track recommendation: {_e(evidence.get('capstone_track_recommendation', 'Agents for Business'))}</p>
    <p class="meta">Generated: {_e(generated_at)}</p>
  </header>
  <main>
    <section class="grid" aria-label="AgentOps status summary">
      <div class="panel"><div class="label">Quality gate status</div><div class="value">{_e(quality.get('status', 'missing'))}</div></div>
      <div class="panel"><div class="label">Test/eval status</div><div class="value">{_e(summary.get('overall_status', 'unknown'))}</div></div>
      <div class="panel"><div class="label">Security guardrail status</div><div class="value">{_e(security.get('status', 'missing'))}</div></div>
      <div class="panel"><div class="label">Human approval/audit status</div><div class="value">{_e(approval.get('status', 'missing'))}</div></div>
      <div class="panel"><div class="label">Release evidence status</div><div class="value">{_e(release.get('status', 'missing'))}</div></div>
    </section>

    <h2>Evidence Index</h2>
    <table>
      <thead><tr><th>Evidence</th><th>Status</th><th>Summary</th><th>Source</th></tr></thead>
      <tbody>{source_rows}</tbody>
    </table>

    <h2>Provider Smoke Skip Explanation</h2>
    <ul>{skipped_items}</ul>

    <h2>Verification Commands</h2>
    <ul>{command_items}</ul>

    <h2>Known Limitations</h2>
    <ul>{limitation_items}</ul>

    <h2>What Judges Should Notice</h2>
    <p>TradeFlow AgentOS demonstrates an agentic business workflow with explicit planner contracts, deterministic evals, security policy checks, approval enforcement, audit evidence, and reviewer-friendly generated artifacts. The capstone assets are local, repeatable, no-network, and secrets-safe by default.</p>
  </main>
</body>
</html>
"""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-json", type=Path, default=DEFAULT_EVIDENCE_JSON)
    parser.add_argument("--html-out", type=Path, default=DEFAULT_HTML_OUT)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = build_dashboard(evidence_json=args.evidence_json, html_out=args.html_out)
    if not args.quiet:
        print(f"Wrote AgentOps dashboard to {result['html_out']}")
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Evidence JSON not found: {path}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"Evidence JSON root must be an object: {path}")
    return payload


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _status_class(value: Any) -> str:
    status = str(value or "unknown")
    return status if status in {"passed", "failed", "skipped", "missing", "present"} else "present"


if __name__ == "__main__":
    raise SystemExit(main())
