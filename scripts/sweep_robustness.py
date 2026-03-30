import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import base64


ROOT = Path(__file__).resolve().parents[1]

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def parse_float_list(s: str):
    return [float(x) for x in s.split(",") if x.strip()]


def parse_int_list(s: str):
    return [int(x) for x in s.split(",") if x.strip()]


def run_once(
    budget: int,
    temperature: float,
    max_length: int,
    mutation_space: str,
    seed_file: str | None,
    plugin_config: str | None,
    concurrency: int,
    eps: float,
):

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_experiment.py"),
        "--budget",
        str(budget),
        "--concurrency",
        str(concurrency),
        "--eps",
        str(eps),
        "--mutation-space",
        mutation_space,
        "--ds-temperature",
        str(temperature),
        "--ds-max-length",
        str(max_length),
    ]
    if seed_file:
        cmd += ["--seed-file", seed_file]
    if plugin_config:
        cmd += ["--plugin-config", plugin_config]

    print("运行实验: ", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)

    # 运行分析脚本
    analyze_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "analyze_results.py"),
    ]
    print("生成统计: ", " ".join(analyze_cmd))
    subprocess.run(analyze_cmd, check=True, cwd=ROOT)

    stats_path = ROOT / "results" / "stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutation-space", type=str, default="both", choices=["semantic", "char", "both"], help="实验使用的变异空间")
    parser.add_argument("--budgets", type=str, default="100,200,400", help="逗号分隔的查询预算列表，例如 100,200,400")
    parser.add_argument("--temperatures", type=str, default="0.3,0.7", help="逗号分隔的 temperature 列表，例如 0.3,0.7")
    parser.add_argument("--max-lengths", type=str, default="256,512", help="逗号分隔的 max_length 列表，例如 256,512")
    parser.add_argument("--seed-file", type=str, default="data/custom_prompts_template.csv")
    parser.add_argument("--plugin-config", type=str, default="configs/plugin_concat_for_thesis.json")
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--eps", type=float, default=0.2)

    args = parser.parse_args()

    budgets = parse_int_list(args.budgets)
    temps = parse_float_list(args.temperatures)
    maxlens = parse_int_list(args.max_lengths)

    rows = []
    for b, t, L in itertools.product(budgets, temps, maxlens):
        stats = run_once(
            budget=b,
            temperature=t,
            max_length=L,
            mutation_space=args.mutation_space,
            seed_file=args.seed_file,
            plugin_config=args.plugin_config,
            concurrency=args.concurrency,
            eps=args.eps,
        )
        row = {
            "budget": b,
            "ds_temperature": t,
            "ds_max_length": L,
            "mutation_space": args.mutation_space,
            "msr": stats.get("msr"),
            "aqs": stats.get("aqs"),
            "stealth_mean": stats.get("stealth_mean"),
        }
        rows.append(row)

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    df = pd.DataFrame(rows)
    csv_path = out_dir / "robustness_summary.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"已写入汇总表: {csv_path}")

    # 画 MSR / AQS 曲线
    combos = sorted({(r["ds_temperature"], r["ds_max_length"]) for r in rows})
    budgets_sorted = sorted(set(r["budget"] for r in rows))

    def plot_metric(metric: str, title: str, filename: str):
        plt.figure(figsize=(7, 5))
        for t, L in combos:
            sub = sorted(
                [r for r in rows if r["ds_temperature"] == t and r["ds_max_length"] == L],
                key=lambda r: r["budget"],
            )
            xs = [r["budget"] for r in sub]
            ys = [r.get(metric) for r in sub]
            label = f"T={t}, L={L}"
            plt.plot(xs, ys, marker="o", label=label)
        plt.xlabel("查询预算")
        plt.ylabel(metric)
        plt.title(title + f"（空间: {args.mutation_space}）")
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.legend()
        out_path = out_dir / filename
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"已保存图像: {out_path}")
        plt.close()

    plot_metric("msr", "MSR（成功率）随预算变化", "robustness_msr.png")
    plot_metric("aqs", "AQS（平均成功查询轮数）随预算变化", "robustness_aqs.png")

    # 生成汇总可视化 HTML 页面（便于论文中直接查看图表和摘要表）
    html_path = out_dir / "robustness_report.html"

    def _img_to_data_uri(path: Path) -> str:
        if not path.exists():
            return ""
        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{b64}"

    msr_uri = _img_to_data_uri(out_dir / "robustness_msr.png")
    aqs_uri = _img_to_data_uri(out_dir / "robustness_aqs.png")

    # 结果表转成 HTML 表格
    table_html = df.to_html(index=False, justify="center", border=0)

    html = f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"utf-8\" />
    <title>鲁棒性实验汇总报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", \"Microsoft YaHei\", Arial, sans-serif; margin: 20px; }}
        h1 {{ margin-bottom: 0.5rem; }}
        h2 {{ margin-top: 1.8rem; }}
        .row {{ display: flex; flex-wrap: wrap; gap: 20px; }}
        .card {{ flex: 1 1 360px; border: 1px solid #ddd; border-radius: 6px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        img {{ max-width: 100%; height: auto; }}
        table {{ border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ccc; padding: 4px 8px; text-align: center; }}
    </style>
</head>
<body>
    <h1>鲁棒性实验汇总报告</h1>
    <p>变异空间：{args.mutation_space}；组合数量：{len(rows)}；数据文件：robustness_summary.csv</p>

    <div class=\"row\">
        <div class=\"card\">
            <h2>MSR（成功率）随预算变化</h2>
            {f'<img src="{msr_uri}" alt="MSR 曲线" />' if msr_uri else '<p>未找到 robustness_msr.png</p>'}
        </div>
        <div class=\"card\">
            <h2>AQS（平均成功查询轮数）随预算变化</h2>
            {f'<img src="{aqs_uri}" alt="AQS 曲线" />' if aqs_uri else '<p>未找到 robustness_aqs.png</p>'}
        </div>
    </div>

    <h2>数值结果一览（robustness_summary.csv）</h2>
    {table_html}

</body>
</html>
"""

    html_path.write_text(html, encoding="utf-8")
    print(f"已生成图表页面: {html_path}")


if __name__ == "__main__":
    main()
