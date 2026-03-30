from __future__ import annotations
import os
from pathlib import Path

OUTPUT_DIR = Path("docs/figures/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    import svgwrite
except Exception:
    print("Missing svgwrite. Install via: pip install svgwrite")
    raise SystemExit(1)


def draw_box(dwg, insert, size, text, rx=6, ry=6, fill="#f8fbff", stroke="#2B7CD3"):
    x, y = insert
    w, h = size
    rect = dwg.rect(insert=insert, size=size, rx=rx, ry=ry, fill=fill, stroke=stroke, stroke_width=1.5)
    dwg.add(rect)
    if isinstance(text, (list, tuple)):
        lines = list(text)
    else:
        lines = str(text).split('\n')
    line_h = 14
    total_h = line_h * len(lines)
    start_y = y + (h - total_h) / 2 + line_h - 2
    for i, ln in enumerate(lines):
        dwg.add(
            dwg.text(ln, insert=(x + 10, start_y + i * line_h), fill="#111", font_size=12)
        )


def elbow_line(dwg, src_rect, dst_rect, stroke="#333"):
    """Draw an elbow (polyline) from right-middle of src_rect to left-middle of dst_rect.
    src_rect/dst_rect are (x,y,w,h) tuples."""
    sx, sy, sw, sh = src_rect
    dx, dy, dw, dh = dst_rect
    start = (sx + sw, sy + sh / 2)
    end = (dx, dy + dh / 2)
    mid_x = (start[0] + end[0]) / 2
    points = [start, (mid_x, start[1]), (mid_x, end[1]), end]
    dwg.add(dwg.polyline(points=points, fill="none", stroke=stroke, stroke_width=1.2))
    ah = 6
    ex, ey = end
    tri = [(ex, ey), (ex - ah, ey - ah / 2), (ex - ah, ey + ah / 2)]
    dwg.add(dwg.polygon(points=tri, fill=stroke))


def gen_overview(path: Path):
    W, H = 1000, 360
    dwg = svgwrite.Drawing(filename=str(path), size=(W, H))
    dwg.add(dwg.text("系统总览 / System Overview：PromptFuzz-SC", insert=(20, 24), font_size=16, fill="#111"))

    box_x = 20
    box_y = 50
    box_w = 220
    box_h = 60
    gap_y = 8

    items = [
        (("种子提示", "Seeds"), (box_x, box_y)),
        (("变异算子库\n语义 / 字符", "MutationOp Library\nSemantic / Character"), (box_x, box_y + (box_h + gap_y) * 1)),
        (("变异器", "Mutator"), (box_x, box_y + (box_h + gap_y) * 2)),
        (("搜索器", "Searcher\nε-greedy + Hill-Climbing"), (box_x + 280, box_y + (box_h + gap_y) * 1)),
        (("分析器", "Analyzer\nMSR/AQS/Stealth"), (box_x + 560, box_y + (box_h + gap_y) * 1)),
        (("Prometheus 指标", "Prometheus /metrics"), (box_x + 560, box_y + (box_h + gap_y) * 2.2)),
        (("Grafana 仪表盘", "Grafana / Dashboard"), (box_x + 560, box_y + (box_h + gap_y) * 3.4)),
    ]

    rects = {}
    for idx, (text, (x, y)) in enumerate(items):
        draw_box(dwg, (x, y), (box_w, box_h), text)
        rects[idx] = (x, y, box_w, box_h)

    draw_box(dwg, (box_x + 280, box_y - 90), (box_w, box_h), ("远端模型服务", "DeepSeek API\nmodel=deepseek-chat"))
    deep_rect = (box_x + 280, box_y - 90, box_w, box_h)

    elbow_line(dwg, rects[0], rects[2])
    elbow_line(dwg, rects[1], rects[2])
    elbow_line(dwg, rects[2], rects[3])
    elbow_line(dwg, rects[3], deep_rect)
    elbow_line(dwg, deep_rect, rects[3])
    elbow_line(dwg, rects[3], rects[4])
    elbow_line(dwg, rects[4], rects[5])
    elbow_line(dwg, rects[4], rects[6])

    dwg.save()
    print(f"Wrote {path}")


def gen_ops(path: Path):
    W, H = 900, 360
    dwg = svgwrite.Drawing(filename=str(path), size=(W, H))
    dwg.add(dwg.text("变异算子示意 / Ops Taxonomy", insert=(20, 24), font_size=16, fill="#111"))

    draw_box(dwg, (20, 50), (160, 50), ("变异算子库", "MutationOp Library"))
    draw_box(dwg, (220, 30), (200, 40), ("语义算子", "SemanticOps"))
    draw_box(dwg, (220, 160), (200, 40), ("字符算子", "CharacterOps"))

    draw_box(dwg, (460, 20), (140, 30), ("同义替换", "Synonym Replace"))
    draw_box(dwg, (460, 60), (140, 30), ("ICL 污染", "ICL Pollute"))
    draw_box(dwg, (460, 100), (140, 30), ("语义改写", "Semantic Paraphrase"))

    draw_box(dwg, (620, 160), (140, 30), ("零宽字符插入", "Zero-Width Insert"))
    draw_box(dwg, (620, 200), (140, 30), ("随机空格", "Random Space"))
    draw_box(dwg, (620, 240), (140, 30), ("Leet / Base64", "Leet / Base64"))


    elbow_line(dwg, (20, 50, 160, 50), (220, 30, 200, 40))
    elbow_line(dwg, (20, 50, 160, 50), (220, 100, 200, 40))

    elbow_line(dwg, (220, 30, 200, 40), (460, 20, 140, 30))
    elbow_line(dwg, (220, 30, 200, 40), (460, 60, 140, 30))
    elbow_line(dwg, (220, 30, 200, 40), (460, 100, 140, 30))

    elbow_line(dwg, (220, 160, 200, 40), (620, 160, 140, 30))
    elbow_line(dwg, (220, 160, 200, 40), (620, 200, 140, 30))
    elbow_line(dwg, (220, 160, 200, 40), (620, 240, 140, 30))

    dwg.add(dwg.text("示例: 输入: 删除系统权限 => 输出: 删\u200B除系统权限", insert=(20, 320), font_size=12, fill="#111"))

    dwg.save()
    print(f"Wrote {path}")


def gen_search_flow(path: Path):
    W, H = 800, 420
    dwg = svgwrite.Drawing(filename=str(path), size=(W, H))
    dwg.add(dwg.text("搜索流程 / Search Flow", insert=(20, 24), font_size=16, fill="#111"))

    nodes = [
        ("Start", ("开始", "Start"), (40, 60)),
        ("Init", ("初始化: seeds, ε, workers", "Init: seeds, ε, workers"), (40, 120)),
        ("Select", ("ε-greedy 选择 seed / mutation", "ε-greedy select seed/mutation"), (40, 180)),
        ("Mutate", ("应用变异算子", "Apply MutationOps"), (40, 240)),
        ("Eval", ("调用 DeepSeek 并判定 success", "Call DeepSeek & eval success"), (320, 180)),
        ("Record", ("记录成功样本\n更新 MSR/AQS/Stealth", "Record success, update MSR/AQS/Stealth"), (480, 120)),
        ("Hill", ("Hill-Climbing 局部精炼", "Hill-Climbing local refine"), (480, 200)),
        ("Stop", ("终止条件 met?", "Stop condition?"), (320, 300)),
        ("End", ("结束", "End"), (480, 300)),
    ]

    rects = {}
    for idx, (_, txt, (x, y)) in enumerate(nodes):
        draw_box(dwg, (x, y), (200, 40), txt)
        rects[idx] = (x, y, 200, 40)


    elbow_line(dwg, rects[1], rects[2])
    elbow_line(dwg, rects[2], rects[3])

    elbow_line(dwg, rects[3], rects[4])

    elbow_line(dwg, rects[4], rects[5])

    elbow_line(dwg, rects[5], rects[6])
    elbow_line(dwg, rects[6], rects[2])

    elbow_line(dwg, rects[4], rects[2])

    elbow_line(dwg, rects[2], rects[7])

    elbow_line(dwg, rects[7], rects[8])

    dwg.save()
    print(f"Wrote {path}")


if __name__ == "__main__":
    gen_overview(OUTPUT_DIR / "overview.svg")
    gen_ops(OUTPUT_DIR / "ops_taxonomy.svg")
    gen_search_flow(OUTPUT_DIR / "search_flow.svg")
    print("All figures generated under:", OUTPUT_DIR)
