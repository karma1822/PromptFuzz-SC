from __future__ import annotations

import http.server
import socketserver
import threading
import urllib.parse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8050


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>PromptFuzz-SC 控制面板</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", "SimHei", "SimSun", Arial, sans-serif; margin: 20px; }
    h1 { margin-bottom: 0.2rem; }
    h2 { margin-top: 1.8rem; }
    fieldset { border: 1px solid #ddd; padding: 12px 16px; margin-bottom: 1.2rem; border-radius: 6px; }
    legend { padding: 0 6px; font-weight: bold; }
    label { display: inline-block; min-width: 140px; margin: 4px 0; }
    input[type="text"], input[type="number"] { width: 220px; padding: 2px 4px; }
    select { padding: 2px 4px; }
    .row { margin: 6px 0; }
    button { padding: 6px 12px; margin-top: 8px; cursor: pointer; }
    .msg { margin: 10px 0; color: #006400; }
    .hint { color: #555; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>PromptFuzz-SC 控制面板</h1>
  <p class="hint">通过浏览器选择参数并启动实验；运行日志仍输出在终端。</p>
  __MESSAGE__

  <p class="hint">已完成的鲁棒性 sweep 报告：<a href="/robustness-report" target="_blank">点击这里查看（如已生成）</a></p>

  <form method="post" action="/run-experiment">
    <fieldset>
      <legend>单次实验（ε-greedy + Hill-Climbing）</legend>

      <div class="row">
        <label>查询预算 budget：</label>
        <input type="number" name="budget" value="200" min="1" />
      </div>
      <div class="row">
        <label>并发数 concurrency：</label>
        <input type="number" name="concurrency" value="8" min="1" />
      </div>
      <div class="row">
        <label>ε（探索率 eps）：</label>
        <input type="text" name="eps" value="0.2" />
      </div>
      <div class="row">
        <label>变异空间 mutation-space：</label>
        <select name="mutation_space">
          <option value="semantic">仅语义空间 (semantic)</option>
          <option value="char">仅字符空间 (char)</option>
          <option value="both" selected>双空间 (both)</option>
        </select>
      </div>
      <div class="row">
        <label>种子文件 seed-file：</label>
        <input type="text" name="seed_file" value="data/custom_prompts_template.csv" />
      </div>
      <div class="row">
        <label>插件配置 plugin-config：</label>
        <input type="text" name="plugin_config" value="configs/plugin_concat_for_thesis.json" />
      </div>
      <div class="row">
        <label>DeepSeek temperature：</label>
        <input type="text" name="ds_temperature" value="0.7" />
      </div>
      <div class="row">
        <label>DeepSeek max_length：</label>
        <input type="number" name="ds_max_length" value="512" />
      </div>
      <div class="row">
        <label>Prometheus 端口（可选）：</label>
        <input type="number" name="prometheus_port" value="" placeholder="如 9100" />
      </div>
      <div class="row">
        <label>启动仪表盘：</label>
        <input type="checkbox" name="serve" value="1" checked /> 在 8001 端口打开结果仪表盘
      </div>

      <button type="submit">运行单次实验</button>
      <div class="hint">提示：运行会在终端输出日志，可在浏览器访问 http://127.0.0.1:8001 查看仪表盘。</div>
    </fieldset>
  </form>

  <form method="post" action="/run-sweep">
    <fieldset>
      <legend>批量鲁棒性实验（多预算 / 多温度 / 多长度）</legend>
      <div class="row">
        <label>变异空间 mutation-space：</label>
        <select name="mutation_space">
          <option value="semantic">仅语义空间 (semantic)</option>
          <option value="char">仅字符空间 (char)</option>
          <option value="both" selected>双空间 (both)</option>
        </select>
      </div>
      <div class="row">
        <label>budgets（逗号分隔）：</label>
        <input type="text" name="budgets" value="100,200,400" />
      </div>
      <div class="row">
        <label>temperatures（逗号分隔）：</label>
        <input type="text" name="temperatures" value="0.3,0.7" />
      </div>
      <div class="row">
        <label>max_lengths（逗号分隔）：</label>
        <input type="text" name="max_lengths" value="256,512" />
      </div>
      <div class="row">
        <label>种子文件 seed-file：</label>
        <input type="text" name="seed_file" value="data/custom_prompts_template.csv" />
      </div>
      <div class="row">
        <label>插件配置 plugin-config：</label>
        <input type="text" name="plugin_config" value="configs/plugin_concat_for_thesis.json" />
      </div>
      <div class="row">
        <label>并发数 concurrency：</label>
        <input type="number" name="concurrency" value="8" />
      </div>
      <div class="row">
        <label>ε（探索率 eps）：</label>
        <input type="text" name="eps" value="0.2" />
      </div>
      <button type="submit">运行批量鲁棒性实验</button>
      <div class="hint">提示：脚本会依次调用 run_experiment.py 和 analyze_results.py，并在 results/ 下生成
        robustness_summary.csv、robustness_msr.png、robustness_aqs.png。</div>
    </fieldset>
  </form>
</body>
</html>
"""


class PanelHandler(http.server.SimpleHTTPRequestHandler):
    def _send_html(self, content: str):
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
      path = urllib.parse.urlparse(self.path).path
      if path == "/robustness-report":
        # 展示 sweep 生成的鲁棒性报告页面
        report = ROOT / "results" / "robustness_report.html"
        if report.exists():
          content = report.read_text(encoding="utf-8")
          self._send_html(content)
        else:
          msg = "<p class=\"msg\">当前还没有生成鲁棒性报告，请先运行一次批量鲁棒性实验。</p>"
          page = HTML.replace("__MESSAGE__", msg)
          self._send_html(page)
      else:
        # 主控制面板
        page = HTML.replace("__MESSAGE__", "")
        self._send_html(page)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        params = urllib.parse.parse_qs(body)

        path = urllib.parse.urlparse(self.path).path
        if path == "/run-experiment":
            self._handle_run_experiment(params)
        elif path == "/run-sweep":
            self._handle_run_sweep(params)
        else:
            self.send_error(404, "Unknown path")

    def _handle_run_experiment(self, params):
        def g(name, default=""):
            return params.get(name, [default])[0]

        budget = g("budget", "200")
        concurrency = g("concurrency", "8")
        eps = g("eps", "0.2")
        mutation_space = g("mutation_space", "both")
        seed_file = g("seed_file", "")
        plugin_config = g("plugin_config", "")
        ds_temperature = g("ds_temperature", "")
        ds_max_length = g("ds_max_length", "")
        prometheus_port = g("prometheus_port", "")
        serve = g("serve", "0") == "1"

        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "run_experiment.py"),
            "--budget",
            budget,
            "--concurrency",
            concurrency,
            "--eps",
            eps,
            "--mutation-space",
            mutation_space,
        ]
        if seed_file:
            cmd += ["--seed-file", seed_file]
        if plugin_config:
            cmd += ["--plugin-config", plugin_config]
        if ds_temperature:
            cmd += ["--ds-temperature", ds_temperature]
        if ds_max_length:
            cmd += ["--ds-max-length", ds_max_length]
        if prometheus_port:
            cmd += ["--prometheus-port", prometheus_port]
        if serve:
            cmd += ["--serve"]

        def run():
            print("[web_panel] 运行实验: ", " ".join(cmd))
            subprocess.run(cmd, cwd=ROOT)
            print("[web_panel] 实验完成")

        threading.Thread(target=run, daemon=True).start()

        msg = "<p class=\"msg\">已在后台启动实验，请查看终端输出；若勾选了仪表盘，可在稍后打开 <a href='http://127.0.0.1:8001' target='_blank'>http://127.0.0.1:8001</a> 查看结果。</p>"
        page = HTML.replace("__MESSAGE__", msg)
        self._send_html(page)

    def _handle_run_sweep(self, params):
        def g(name, default=""):
            return params.get(name, [default])[0]

        mutation_space = g("mutation_space", "both")
        budgets = g("budgets", "100,200,400")
        temperatures = g("temperatures", "0.3,0.7")
        max_lengths = g("max_lengths", "256,512")
        seed_file = g("seed_file", "")
        plugin_config = g("plugin_config", "")
        concurrency = g("concurrency", "8")
        eps = g("eps", "0.2")

        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "sweep_robustness.py"),
            "--mutation-space",
            mutation_space,
            "--budgets",
            budgets,
            "--temperatures",
            temperatures,
            "--max-lengths",
            max_lengths,
            "--concurrency",
            concurrency,
            "--eps",
            eps,
        ]
        if seed_file:
            cmd += ["--seed-file", seed_file]
        if plugin_config:
            cmd += ["--plugin-config", plugin_config]

        def run():
            print("[web_panel] 运行 sweep 实验: ", " ".join(cmd))
            subprocess.run(cmd, cwd=ROOT)
            print("[web_panel] sweep 完成")

        threading.Thread(target=run, daemon=True).start()

        msg = "<p class=\"msg\">已在后台启动批量鲁棒性实验，完成后可通过上方链接打开最新的鲁棒性报告页面。</p>"
        page = HTML.replace("__MESSAGE__", msg)
        self._send_html(page)


def main():
    with socketserver.TCPServer(("127.0.0.1", PORT), PanelHandler) as httpd:
        print(f"[web_panel] 控制面板已启动: http://127.0.0.1:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[web_panel] 已停止控制面板。")


if __name__ == "__main__":
    main()
