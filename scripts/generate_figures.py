from __future__ import annotations
import os
import sys
from pathlib import Path

OUTPUT_DIR = Path("docs/figures/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OVERVIEW_SVG = OUTPUT_DIR / "overview.svg"
OPS_SVG = OUTPUT_DIR / "ops_taxonomy.svg"
SEARCH_SVG = OUTPUT_DIR / "search_flow.svg"

try:
    from graphviz import Digraph
except Exception as e:
    print("Error: Python package 'graphviz' is not available.")
    print("Please run: pip install graphviz")
    raise SystemExit(1)


def gen_overview(path: Path):
    g = Digraph("overview", format="svg")
    g.attr(rankdir="LR", splines="ortho", fontsize="12")

    with g.subgraph(name="cluster_local") as c:
        c.attr(label="本地实验主机", fontsize="12")
        c.node("Seeds", "Seeds\n(种子提示)")
        c.node("Ops", "MutationOp Library\nSemantic / Character")
        c.node("Mutator", "Mutator\n(applies ops)")
        c.node("Search", "Searcher\nε-greedy + Hill-Climbing")
        c.node("Analyzer", "Analyzer\nMSR/AQS/Stealth")
        c.node("Prom", "Prometheus\n/metrics")
        c.node("Dashboard", "Grafana / Dashboard")

    with g.subgraph(name="cluster_remote") as r:
        r.attr(label="远端模型服务", fontsize="12")
        r.node("DeepSeek", "DeepSeek API\nmodel=deepseek-chat")

    g.edge("Seeds", "Mutator")
    g.edge("Ops", "Mutator")
    g.edge("Mutator", "Search")
    g.edge("Search", "DeepSeek", label="requests")
    g.edge("DeepSeek", "Search", label="responses")
    g.edge("Search", "Analyzer")
    g.edge("Analyzer", "Prom")
    g.edge("Prom", "Dashboard")
    g.edge("Analyzer", "Dashboard")

    g.render(filename=str(path), cleanup=True)
    print(f"Wrote {path}")


def gen_ops(path: Path):
    g = Digraph("ops", format="svg")
    g.attr(rankdir="LR", fontsize="12")

    g.node("A", "MutationOp Library")
    g.node("S", "SemanticOps")
    g.node("C", "CharacterOps")
    g.edge("A", "S")
    g.edge("A", "C")

    # semantic
    g.node("S1", "Synonym Replace")
    g.node("S2", "ICL Pollute")
    g.node("S3", "Semantic Paraphrase")

    # char
    g.node("C1", "Zero-Width Insert")
    g.node("C2", "Random Space")
    g.node("C3", "Leet / Base64")

    g.edge("S", "S1")
    g.edge("S", "S2")
    g.edge("S", "S3")

    g.edge("C", "C1")
    g.edge("C", "C2")
    g.edge("C", "C3")

    g.node("ex1", "示例: 输入: 删除系统权限\n=> 输出: 删\u200B除系统权限")
    g.edge("S1", "ex1")
    g.edge("C1", "ex1")

    g.render(filename=str(path), cleanup=True)
    print(f"Wrote {path}")


def gen_search_flow(path: Path):
    g = Digraph("search_flow", format="svg")
    g.attr(rankdir="TB", fontsize="12")

    g.node("Start", "开始", shape="circle")
    g.node("Init", "初始化: seeds, ε, workers")
    g.node("Select", "ε-greedy 选择 seed / mutation")
    g.node("Mutate", "应用变异算子")
    g.node("Eval", "调用 DeepSeek 并判定 success")
    g.node("Success", "成功?", shape="diamond")
    g.node("Record", "记录成功样本\n更新 MSR/AQS/Stealth")
    g.node("Hill", "Hill-Climbing 局部精炼")
    g.node("Stop", "终止条件 met?", shape="diamond")
    g.node("End", "结束", shape="doublecircle")

    g.edge("Start", "Init")
    g.edge("Init", "Select")
    g.edge("Select", "Mutate")
    g.edge("Mutate", "Eval")
    g.edge("Eval", "Success")
    g.edge("Success", "Record", label="Yes")
    g.edge("Record", "Hill")
    g.edge("Hill", "Select")
    g.edge("Success", "Select", label="No")
    g.edge("Select", "Stop")
    g.edge("Stop", "End", label="Yes")
    g.edge("Stop", "Select", label="No")

    g.render(filename=str(path), cleanup=True)
    print(f"Wrote {path}")


if __name__ == "__main__":
    try:
        gen_overview(OVERVIEW_SVG.with_suffix(''))
        gen_ops(OPS_SVG.with_suffix(''))
        gen_search_flow(SEARCH_SVG.with_suffix(''))
        print("All figures generated under:", OUTPUT_DIR)
    except Exception as exc:
        print("Generation failed:", exc)
        print("Possible causes: missing Graphviz system binary (dot) or Python package 'graphviz'.")
        print("On Windows: install Graphviz from https://graphviz.org/download/ and ensure 'dot' is in PATH.")
        print("Then: pip install graphviz")
        raise SystemExit(1)
