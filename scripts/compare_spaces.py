import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_stats(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"未找到统计文件: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats-semantic", type=str, required=True, help="语义空间实验的 stats.json 路径")
    parser.add_argument("--stats-char", type=str, required=True, help="字符空间实验的 stats.json 路径")
    parser.add_argument("--stats-both", type=str, required=True, help="双空间实验的 stats.json 路径")
    args = parser.parse_args()

    paths = {
        "语义空间": Path(args.stats_semantic),
        "字符空间": Path(args.stats_char),
        "双空间": Path(args.stats_both),
    }

    stats = {label: load_stats(p) for label, p in paths.items()}

    # 关注的关键指标
    metrics = [
        ("msr", "MSR（成功率）"),
        ("aqs", "AQS（平均成功查询轮数）"),
        ("stealth_mean", "Stealth 平均值"),
    ]

    labels = list(paths.keys())
    x = np.arange(len(labels))
    width = 0.25

    fig, axes = plt.subplots(1, len(metrics), figsize=(5 * len(metrics), 4), constrained_layout=True)
    if len(metrics) == 1:
        axes = [axes]

    for i, (key, title) in enumerate(metrics):
        ax = axes[i]
        vals = [float(stats[label].get(key, float("nan"))) for label in labels]
        ax.bar(x, vals, width, color=["#4C72B0", "#55A868", "#C44E52"])
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15)
        ax.set_title(title)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.suptitle("不同变异空间的指标对比", fontsize=14)

    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "space_comparison.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"对比图已保存：{out_path}")


if __name__ == "__main__":
    main()
