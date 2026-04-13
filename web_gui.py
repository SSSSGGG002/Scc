from __future__ import annotations

import argparse
import json
import tempfile
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from snlc.compiler import compile_source
from snlc.errors import CompileError
from snlc.runtime import resolve_mars_jar, run_mips


ROOT = Path(__file__).resolve().parent
EXAMPLES_DIR = ROOT / "examples"


HTML_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SNL Compiler Demo</title>
  <style>
    :root {
      --bg: #f2ede3;
      --panel: #fcfaf5;
      --ink: #2a2118;
      --muted: #6e5f4c;
      --line: #d8ccb9;
      --accent: #8b5e34;
      --accent-2: #b98953;
      --shadow: 0 18px 40px rgba(86, 63, 38, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "SF Pro Text", "PingFang SC", "Helvetica Neue", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(185, 137, 83, 0.18), transparent 28%),
        linear-gradient(160deg, #f5f0e7 0%, #efe5d6 52%, #f7f2ea 100%);
      min-height: 100vh;
    }
    .shell {
      width: min(1500px, calc(100vw - 32px));
      margin: 16px auto;
      display: grid;
      gap: 16px;
    }
    .hero, .panel {
      background: rgba(252, 250, 245, 0.92);
      border: 1px solid rgba(216, 204, 185, 0.9);
      border-radius: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }
    .hero {
      padding: 18px 22px;
      display: grid;
      gap: 14px;
    }
    .title {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: end;
      flex-wrap: wrap;
    }
    h1 {
      margin: 0;
      font-size: clamp(28px, 4vw, 42px);
      line-height: 1;
      letter-spacing: -0.04em;
    }
    .subtitle {
      color: var(--muted);
      max-width: 720px;
      font-size: 15px;
    }
    .toolbar {
      display: grid;
      grid-template-columns: 220px 1fr 220px auto auto;
      gap: 12px;
      align-items: end;
    }
    .field {
      display: grid;
      gap: 6px;
      min-width: 0;
    }
    .field label {
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    input, select, textarea, button {
      font: inherit;
    }
    input, select {
      width: 100%;
      border: 1px solid var(--line);
      background: #fffdf8;
      color: var(--ink);
      border-radius: 14px;
      padding: 12px 14px;
    }
    button {
      border: 0;
      border-radius: 14px;
      padding: 13px 18px;
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease, opacity 120ms ease;
      white-space: nowrap;
    }
    button:hover { transform: translateY(-1px); }
    .primary {
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
      color: white;
    }
    .secondary {
      background: #e7ddce;
      color: var(--ink);
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(360px, 1fr) minmax(420px, 1.25fr);
      gap: 16px;
    }
    .panel {
      padding: 14px;
      min-height: 72vh;
      display: grid;
      gap: 12px;
    }
    .panel-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .panel-head h2 {
      margin: 0;
      font-size: 16px;
      letter-spacing: 0.02em;
    }
    .status {
      color: var(--muted);
      font-size: 13px;
    }
    textarea.source {
      width: 100%;
      min-height: calc(72vh - 48px);
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: #fffdf8;
      color: var(--ink);
      font-family: Menlo, Monaco, "Cascadia Mono", monospace;
      font-size: 14px;
      line-height: 1.5;
    }
    .tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .tab {
      padding: 9px 12px;
      border-radius: 999px;
      background: #ece2d3;
      color: var(--ink);
      font-size: 13px;
    }
    .tab.active {
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
      color: white;
    }
    pre.output {
      margin: 0;
      min-height: calc(72vh - 102px);
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: #fffdf8;
      color: var(--ink);
      font-family: Menlo, Monaco, "Cascadia Mono", monospace;
      font-size: 13px;
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .footer {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      font-size: 13px;
      color: var(--muted);
    }
    @media (max-width: 1100px) {
      .toolbar { grid-template-columns: 1fr 1fr; }
      .layout { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="title">
        <div>
          <h1>SNL Compiler Demo</h1>
          <div class="subtitle">本地浏览器版展示界面。可以直接编辑源码、查看 Token 序列与层次语法树、观察四元式和 MIPS，并调用 MARS 运行。</div>
        </div>
        <div class="status" id="hero-status">Ready</div>
      </div>
      <div class="toolbar">
        <div class="field">
          <label for="example-select">Example</label>
          <select id="example-select"></select>
        </div>
        <div class="field">
          <label for="mars-jar">MARS Jar</label>
          <input id="mars-jar" type="text" value="Mars for Compile 2022.jar">
        </div>
        <div class="field">
          <label for="run-input">Run Input</label>
          <input id="run-input" type="text" placeholder='例如 5\\n'>
        </div>
        <button class="secondary" id="load-example">Load Example</button>
        <div style="display:flex; gap:10px;">
          <button class="secondary" id="compile-btn">Compile</button>
          <button class="primary" id="run-btn">Run</button>
        </div>
      </div>
    </section>

    <section class="layout">
      <div class="panel">
        <div class="panel-head">
          <h2>Source</h2>
          <div class="status" id="source-status">examples</div>
        </div>
        <textarea class="source" id="source"></textarea>
      </div>

      <div class="panel">
        <div class="panel-head">
          <h2>Artifacts</h2>
          <div class="status" id="artifact-status">Tokens / AST / IR / MIPS / Output</div>
        </div>
        <div class="tabs" id="tabs"></div>
        <pre class="output" id="output"></pre>
        <div class="footer">
          <div id="footer-message">启动后会自动加载一个示例。</div>
          <div>Server runs locally on 127.0.0.1</div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const views = {
      tokens: "",
      ast: "",
      ir: "",
      mips: "",
      output: "",
      messages: ""
    };
    let activeTab = "ast";

    const outputEl = document.getElementById("output");
    const tabsEl = document.getElementById("tabs");
    const statusEl = document.getElementById("hero-status");
    const footerEl = document.getElementById("footer-message");
    const sourceEl = document.getElementById("source");
    const exampleEl = document.getElementById("example-select");
    const sourceStatusEl = document.getElementById("source-status");

    function renderTabs() {
      tabsEl.innerHTML = "";
      [["tokens", "Tokens"], ["ast", "AST"], ["ir", "IR"], ["mips", "MIPS"], ["output", "Program Output"], ["messages", "Messages"]]
        .forEach(([key, label]) => {
          const button = document.createElement("button");
          button.className = "tab" + (key === activeTab ? " active" : "");
          button.textContent = label;
          button.onclick = () => {
            activeTab = key;
            renderTabs();
            renderOutput();
          };
          tabsEl.appendChild(button);
        });
    }

    function renderOutput() {
      outputEl.textContent = views[activeTab] || "(empty)";
    }

    function setStatus(message) {
      statusEl.textContent = message;
      footerEl.textContent = message;
    }

    async function loadExamples() {
      const response = await fetch("/api/examples");
      const data = await response.json();
      exampleEl.innerHTML = "";
      data.examples.forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        exampleEl.appendChild(option);
      });
      if (data.examples.length) {
        exampleEl.value = data.selected;
        await loadExample();
      }
    }

    async function loadExample() {
      const response = await fetch("/api/example?name=" + encodeURIComponent(exampleEl.value));
      const data = await response.json();
      sourceEl.value = data.source;
      sourceStatusEl.textContent = "Loaded " + data.name;
      setStatus("Loaded example " + data.name);
    }

    async function postJSON(url, payload) {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      return response.json();
    }

    function applyCompileData(data) {
      views.tokens = data.tokens;
      views.ast = data.ast;
      views.ir = data.ir;
      views.mips = data.mips;
      views.messages = data.message || "";
      if (data.output !== undefined) {
        views.output = data.output;
      }
      activeTab = data.active_tab || activeTab;
      renderTabs();
      renderOutput();
      setStatus(data.status);
    }

    async function compileSource() {
      setStatus("Compiling...");
      const data = await postJSON("/api/compile", {
        source: sourceEl.value
      });
      applyCompileData(data);
    }

    async function runSource() {
      setStatus("Running...");
      const data = await postJSON("/api/run", {
        source: sourceEl.value,
        run_input: document.getElementById("run-input").value,
        mars_jar: document.getElementById("mars-jar").value
      });
      applyCompileData(data);
    }

    document.getElementById("load-example").onclick = loadExample;
    document.getElementById("compile-btn").onclick = compileSource;
    document.getElementById("run-btn").onclick = runSource;

    renderTabs();
    renderOutput();
    loadExamples().catch((error) => {
      views.messages = String(error);
      activeTab = "messages";
      renderTabs();
      renderOutput();
      setStatus("Failed to load examples");
    });
  </script>
</body>
</html>
"""


class AppServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int]) -> None:
        super().__init__(server_address, AppHandler)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="snlc_web_gui_")
        self.example_names = sorted(path.name for path in EXAMPLES_DIR.glob("*.snl"))
        if "procedures.snl" in self.example_names:
            self.default_example = "procedures.snl"
        elif self.example_names:
            self.default_example = self.example_names[0]
        else:
            self.default_example = ""

    def server_close(self) -> None:
        self.temp_dir.cleanup()
        super().server_close()


class AppHandler(BaseHTTPRequestHandler):
    server: AppServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTML_PAGE)
            return
        if parsed.path == "/api/examples":
            self._send_json(
                {
                    "examples": self.server.example_names,
                    "selected": self.server.default_example,
                }
            )
            return
        if parsed.path == "/api/example":
            params = parse_qs(parsed.query)
            name = params.get("name", [self.server.default_example])[0]
            if not name:
                self._send_json({"error": "No examples available"}, status=HTTPStatus.NOT_FOUND)
                return
            path = EXAMPLES_DIR / name
            if not path.exists():
                self._send_json({"error": f"Example not found: {name}"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json({"name": name, "source": path.read_text(encoding="utf-8")})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json()
        if payload is None:
            return
        if parsed.path == "/api/compile":
            self._send_json(self._compile(payload.get("source", "")))
            return
        if parsed.path == "/api/run":
            self._send_json(self._run(payload))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _compile(self, source: str) -> dict[str, str]:
        try:
            result = compile_source(source)
        except CompileError as exc:
            return self._error_response(str(exc))
        except Exception as exc:
            return self._error_response(f"Unexpected error: {exc}")
        return {
            "status": "Compile succeeded",
            "message": "Compilation succeeded.",
            "tokens": result.format_tokens(),
            "ast": result.format_ast(),
            "ir": result.format_quads(),
            "mips": result.mips,
            "output": "",
            "active_tab": "ast",
        }

    def _run(self, payload: dict[str, str]) -> dict[str, str]:
        compile_data = self._compile(payload.get("source", ""))
        if compile_data["status"] != "Compile succeeded":
            return compile_data

        try:
            jar_path = resolve_mars_jar(payload.get("mars_jar") or None)
        except FileNotFoundError as exc:
            error_data = self._error_response(str(exc))
            error_data.update(
                {
                    "tokens": compile_data["tokens"],
                    "ast": compile_data["ast"],
                    "ir": compile_data["ir"],
                    "mips": compile_data["mips"],
                }
            )
            return error_data

        asm_path = Path(self.server.temp_dir.name) / "web_gui_output.asm"
        asm_path.write_text(compile_data["mips"], encoding="utf-8")
        runtime = run_mips(
            asm_path,
            mars_jar=jar_path,
            stdin_data=self._decode_run_input(payload.get("run_input", "")),
        )

        output_parts: list[str] = []
        if runtime.stdout:
            output_parts.append(runtime.stdout.rstrip("\n"))
        if runtime.stderr:
            output_parts.append("[stderr]")
            output_parts.append(runtime.stderr.rstrip("\n"))
        if not output_parts:
            output_parts.append("(no output)")

        compile_data.update(
            {
                "status": "Run succeeded" if runtime.exit_code == 0 else f"Run failed with exit code {runtime.exit_code}",
                "message": f"Executed with {jar_path.name}",
                "output": "\n".join(output_parts),
                "active_tab": "output" if runtime.exit_code == 0 else "messages",
            }
        )
        if runtime.exit_code != 0:
            compile_data["message"] = runtime.stderr or f"Process exited with code {runtime.exit_code}"
        return compile_data

    def _error_response(self, message: str) -> dict[str, str]:
        return {
            "status": "Failed",
            "message": message,
            "tokens": "",
            "ast": "",
            "ir": "",
            "mips": "",
            "output": "",
            "active_tab": "messages",
        }

    def _read_json(self) -> dict[str, str] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            self._send_json({"error": "Invalid JSON payload"}, status=HTTPStatus.BAD_REQUEST)
            return None

    def _send_html(self, html: str) -> None:
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _decode_run_input(self, value: str) -> str | None:
        if not value:
            return None
        return bytes(value, "utf-8").decode("unicode_escape")


def launch_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local browser GUI for the SNL compiler.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the browser")
    args = parser.parse_args()

    server = AppServer((args.host, args.port))
    url = f"http://{args.host}:{args.port}/"
    print(f"Web GUI listening on {url}")
    print("Press Ctrl+C to stop.")

    if not args.no_browser:
        threading.Timer(0.4, launch_browser, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
