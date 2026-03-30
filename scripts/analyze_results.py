import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import hashlib


def redact_prompt(p: str) -> str:
    def repl(token: str) -> str:
        h = hashlib.sha1(token.encode()).hexdigest()
        return f"<R-{h[:8]}>"

    import re
    parts = re.split(r"(\w+)", p)
    parts = [repl(t) if t and t.isalnum() and len(t) > 2 else t for t in parts]
    return "".join(parts)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def main(path: str = "results/results.json"):
    p = Path(path)
    if not p.exists():
        print("未找到 results.json，请先运行 experiments 并生成结果。")
        return

    data = json.loads(p.read_text(encoding="utf-8"))
    history = data.get("history", [])
    best = data.get("best", [])
    total_queries = int(data.get("queries", len(history)))

    if (not history) and best and total_queries > 0:
        history = [{"prompt": "", "success": False, "resp": ""} for _ in range(total_queries)]
        provided = []
        missing = []
        for b in best:
            q = b.get("queries_used")
            if isinstance(q, int):
                provided.append((q, b))
            else:
                missing.append(b)

        # 填入已知的成功位置（转换为 0-based 索引，确保在范围内）
        for q, b in provided:
            idx = max(0, min(total_queries - 1, int(q) - 1))
            history[idx] = {"prompt": b.get("prompt", ""), "success": True, "resp": b.get("resp", "")}

        # 为缺失的成功项在末尾附近分配空位
        assign_positions = []
        candidate_idxs = list(range(max(0, total_queries - 20), total_queries))
        for i in candidate_idxs:
            if not history[i].get("success"):
                assign_positions.append(i)
        for i, b in enumerate(missing):
            if i < len(assign_positions):
                idx = assign_positions[i]
            else:
                idx = next((j for j in range(total_queries) if not history[j].get("success")), total_queries - 1)
            history[idx] = {"prompt": b.get("prompt", ""), "success": True, "resp": b.get("resp", "")}


    # MSR: 成功次数 / 查询数
    successes = [h for h in history if h.get("success")]
    msr = len(successes) / total_queries if total_queries > 0 else 0.0

    # AQS: 平均到达成功所用查询（使用 history 的索引 +1 作为查询编号）
    q_to_succ = [i + 1 for i, h in enumerate(history) if h.get("success")]
    aqs = float(np.mean(q_to_succ)) if q_to_succ else float('nan')

    # Stealth：使用 best 列表中提供的 stealth 字段
    stealths = [b.get("stealth") for b in best if b.get("stealth") is not None]

    results_dir = p.parent
    results_dir.mkdir(exist_ok=True)

    stats = {
        "total_queries": total_queries,
        "success_count": len(successes),
        "msr": msr,
        "aqs": aqs,
        "stealth_count": len(stealths),
        "stealth_mean": float(np.mean(stealths)) if stealths else float('nan'),
        "stealth_median": float(np.median(stealths)) if stealths else float('nan'),
    }

    # 将运行配置中的关键信息也写入 stats，便于 sweep/画图
    cfg = data.get("config", {}) or {}
    for key in [
        "budget",
        "concurrency",
        "eps",
        "seed_file",
        "plugin_config",
        "mutation_space",
        "ds_temperature",
        "ds_max_length",
    ]:
        if key in cfg:
            stats[key] = cfg.get(key)
    (results_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"统计已写入：{results_dir / 'stats.json'}")

    # 保存脱敏模板
    redacted = []
    for b in best:
        redacted.append({
            "prompt_redacted": redact_prompt(b.get("prompt", "")),
            "success_rate": b.get("success_rate"),
            "queries_used": b.get("queries_used"),
            "stealth": b.get("stealth"),
        })
    df_red = pd.DataFrame(redacted)
    df_red.to_csv(results_dir / "redacted_templates.csv", index=False, encoding="utf-8-sig")
    print(f"脱敏模板已写入：{results_dir / 'redacted_templates.csv'}")

    # 画箱线图与 CDF
    plt.figure(figsize=(8, 5))
    if stealths:
        sns.boxplot(data=stealths)
        plt.title("Stealth 分数箱线图")
        plt.xlabel("Stealth 分数")
        plt.savefig(results_dir / "stealth_boxplot.png", bbox_inches='tight')
        plt.close()
        print(f"箱线图已保存：{results_dir / 'stealth_boxplot.png'}")

        arr = np.array(stealths)
        arr_sorted = np.sort(arr)
        cdf = np.arange(1, len(arr_sorted) + 1) / len(arr_sorted)
        plt.figure(figsize=(8, 5))
        plt.plot(arr_sorted, cdf, marker='.')
        plt.grid(True)
        plt.xlabel('Stealth 分数')
        plt.ylabel('累计分布（CDF）')
        plt.title('Stealth 分数累积分布（CDF）')
        plt.savefig(results_dir / "stealth_cdf.png", bbox_inches='tight')
        plt.close()
        print(f"CDF 图已保存：{results_dir / 'stealth_cdf.png'}")
    else:
        print("无 stealth 数据，跳过绘图。")

    # 保存历史中的成功分布
    if q_to_succ:
        plt.figure(figsize=(8, 5))
        sns.histplot(q_to_succ, bins=30, kde=False)
        plt.xlabel('成功前所需查询轮数')
        plt.ylabel('样本数量')
        plt.title('成功前查询轮数分布')
        plt.savefig(results_dir / "queries_to_success_hist.png", bbox_inches='tight')
        plt.close()
        print(f"Queries-to-success 直方图已保存：{results_dir / 'queries_to_success_hist.png'}")


if __name__ == '__main__':
    main()
