# PromptFuzz-SC

PromptFuzz-SC: 语义-字符双空间变异的越狱攻击与评估工具（研究版）

项目目标：
- 提供一套可扩展的“语义-字符双空间变异”算子库（MutationOp 插件式设计）。
- 实现 ε-greedy 混合搜索 + Hill-Climbing 局部精修的异步评估框架，支持有限查询预算下高效发现越狱模板。
- 实时计算并导出 MSR、AQS、Stealth 等指标（Prometheus 支持），并提供可视化脚本与 notebook 快速复现实验。
- 提供对 DeepSeek 官方 API 的示例接入（占位），并包含本地模拟器用于无密钥调试。

快速开始（本地调试）:
1. 创建虚拟环境并安装依赖：

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 运行示例实验（使用本地模拟器）：

```powershell
python scripts\run_experiment.py --budget 1000 --concurrency 8
```

### 推荐配置示例

你可以在 `configs/plugin_concat_for_thesis.json` 中配置插件组合。例如：

```json
{
  "plugin_name": "concat_strategy",
  "ops": [
    {"name": "SynonymReplaceOp", "prob": 0.5},
    {"name": "EmojiPadOp", "count": 1},
    {"name": "SegmentShuffleOp", "shuffle_ratio": 0.3}
  ],
  "k": 3,
  "repeat": 2
}
```

运行脚本时指定配置文件：

```powershell
python scripts\run_experiment.py --config configs/plugin_concat_for_thesis.json --budget 1000 --concurrency 8
```

### 种子模板说明（seed file）

- 默认使用：`data/custom_prompts_template.csv`
  - 这个文件是默认的种子 prompt 集合，用于 `scripts/sweep_robustness.py` 和 `scripts/run_experiment.py` 的 `--seed-file` 参数。
- 参考/备选：`data/seeds_template.csv` 或 `data/seeds_template.json`
  - 这两个文件提供一个简化模板，可以作为参考或替换测试集。

推荐运行：

```powershell
python scripts\sweep_robustness.py
```

指定参考种子：

```powershell
python scripts\sweep_robustness.py --seed-file data/seeds_template.csv
```

更多说明请查看 `notebooks/quickstart.ipynb` 与 `src/promptfuzz_sc` 源码。

许可证：MIT（示例）

