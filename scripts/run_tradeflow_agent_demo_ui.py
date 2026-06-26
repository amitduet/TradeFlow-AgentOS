"""Serve a tiny local TradeFlow AgentOS demo UI using only the Python standard library."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agents.demo_agent import TradeFlowDemoInput, response_to_json, run_tradeflow_agent_demo


EXAMPLES_DIR = REPO_ROOT / "examples" / "demo"
DEFAULT_RUNTIME_DIR = REPO_ROOT / "artifacts" / "demo_runtime"


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TradeFlow AgentOS Demo</title>
  <style>
    :root { color-scheme: light; --ink:#17212b; --muted:#5a6572; --line:#d8dee6; --panel:#f7f9fb; --accent:#0f766e; --warn:#b45309; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #ffffff; }
    header { border-bottom: 1px solid var(--line); padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
    h1 { margin: 0; font-size: 22px; line-height: 1.2; }
    main { display: grid; grid-template-columns: minmax(320px, 460px) 1fr; min-height: calc(100vh - 70px); }
    section { padding: 22px 24px; }
    .input { border-right: 1px solid var(--line); background: var(--panel); }
    label { display: block; font-weight: 700; font-size: 13px; margin-bottom: 8px; }
    select, textarea, button { font: inherit; }
    select, textarea { width: 100%; border: 1px solid var(--line); border-radius: 6px; background: white; color: var(--ink); }
    select { padding: 10px 12px; margin-bottom: 16px; }
    textarea { min-height: 420px; resize: vertical; padding: 12px; line-height: 1.45; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }
    button { margin-top: 14px; border: 0; border-radius: 6px; background: var(--accent); color: white; font-weight: 700; padding: 11px 16px; cursor: pointer; }
    button:disabled { opacity: .6; cursor: wait; }
    .status { color: var(--muted); font-size: 13px; margin-left: 12px; }
    .summary { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; margin-bottom: 18px; }
    .metric { border: 1px solid var(--line); border-radius: 6px; padding: 12px; background: white; }
    .metric span { display: block; color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .metric strong { display: block; margin-top: 6px; font-size: 18px; }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; border: 1px solid var(--line); border-radius: 6px; padding: 14px; background: #0f1720; color: #f8fafc; min-height: 420px; }
    .high { color: #b91c1c; }
    .medium { color: var(--warn); }
    .low { color: #15803d; }
    @media (max-width: 860px) {
      main { grid-template-columns: 1fr; }
      .input { border-right: 0; border-bottom: 1px solid var(--line); }
      .summary { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <h1>TradeFlow AgentOS Demo</h1>
    <div class="status" id="status">Offline deterministic mode</div>
  </header>
  <main>
    <section class="input">
      <label for="scenario">Scenario</label>
      <select id="scenario"></select>
      <label for="payload">Business case JSON</label>
      <textarea id="payload" spellcheck="false"></textarea>
      <button id="run">Run Agent Review</button><span class="status" id="runStatus"></span>
    </section>
    <section>
      <div class="summary">
        <div class="metric"><span>Risk</span><strong id="risk">-</strong></div>
        <div class="metric"><span>Approval</span><strong id="approval">-</strong></div>
        <div class="metric"><span>Action</span><strong id="action">-</strong></div>
        <div class="metric"><span>Trace</span><strong id="trace">-</strong></div>
      </div>
      <pre id="output">{}</pre>
    </section>
  </main>
  <script>
    const scenario = document.getElementById("scenario");
    const payload = document.getElementById("payload");
    const output = document.getElementById("output");
    const run = document.getElementById("run");
    const runStatus = document.getElementById("runStatus");
    const risk = document.getElementById("risk");
    const approval = document.getElementById("approval");
    const action = document.getElementById("action");
    const trace = document.getElementById("trace");

    async function loadScenarios() {
      const res = await fetch("/api/scenarios");
      const data = await res.json();
      scenario.innerHTML = data.scenarios.map(name => `<option value="${name}">${name}</option>`).join("");
      scenario.value = "high_risk_order.json";
      await loadScenario();
    }

    async function loadScenario() {
      const res = await fetch(`/api/scenario?name=${encodeURIComponent(scenario.value)}`);
      payload.value = JSON.stringify(await res.json(), null, 2);
    }

    async function runDemo() {
      run.disabled = true;
      runStatus.textContent = "Running...";
      try {
        const res = await fetch("/api/demo", { method: "POST", headers: {"Content-Type":"application/json"}, body: payload.value });
        const data = await res.json();
        output.textContent = JSON.stringify(data, null, 2);
        risk.textContent = data.risk_level || "-";
        risk.className = data.risk_level || "";
        approval.textContent = data.approval_required ? "Required" : "Not required";
        action.textContent = typeof data.recommended_action === "string" ? data.recommended_action : data.recommended_action.action_type;
        trace.textContent = data.trace_refs ? data.trace_refs.trace_id.slice(0, 8) : "-";
        runStatus.textContent = res.ok ? "Complete" : "Needs review";
      } catch (error) {
        output.textContent = JSON.stringify({error: String(error)}, null, 2);
        runStatus.textContent = "Failed";
      } finally {
        run.disabled = false;
      }
    }

    scenario.addEventListener("change", loadScenario);
    run.addEventListener("click", runDemo);
    loadScenarios().then(runDemo);
  </script>
</body>
</html>
"""


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(HTTPStatus.OK, HTML, content_type="text/html; charset=utf-8")
            return
        if parsed.path == "/api/scenarios":
            scenarios = sorted(path.name for path in EXAMPLES_DIR.glob("*.json"))
            self._send_json(HTTPStatus.OK, {"scenarios": scenarios})
            return
        if parsed.path == "/api/scenario":
            name = parse_qs(parsed.query).get("name", [""])[0]
            path = EXAMPLES_DIR / Path(name).name
            if not path.exists():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "scenario not found"})
                return
            self._send(HTTPStatus.OK, path.read_text(encoding="utf-8"), content_type="application/json")
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/demo":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            scenario = TradeFlowDemoInput.model_validate(payload)
            response = run_tradeflow_agent_demo(
                scenario,
                approval_storage_path=DEFAULT_RUNTIME_DIR / "approval_requests.json",
                audit_log_path=DEFAULT_RUNTIME_DIR / "planner_audit.jsonl",
            )
            status = HTTPStatus.OK if response.success else HTTPStatus.BAD_REQUEST
            self._send(status, response_to_json(response), content_type="application/json")
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        self._send(status, json.dumps(payload, indent=2, sort_keys=True) + "\n", content_type="application/json")

    def _send(self, status: HTTPStatus, body: str, *, content_type: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    print(f"TradeFlow AgentOS demo UI: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped TradeFlow AgentOS demo UI.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
