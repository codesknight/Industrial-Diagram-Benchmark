"""Insert Topology Panel v1 defense material into the external defense summary."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
DEFENSE_SUMMARY = ROOT.parent / "data" / "答辩汇报总结.md"
EXPERIMENT_RECORDS = ROOT / "experiment_records.md"
DATA_INDEX = ROOT / "data_index"
DOCS = ROOT / "docs"

SECTION_START = "<!-- TOPOLOGY_PANEL_V1_DEFENSE_START -->"
SECTION_END = "<!-- TOPOLOGY_PANEL_V1_DEFENSE_END -->"


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rel_from_defense(path: Path) -> str:
    rel_path = os.path.relpath(path.resolve(), DEFENSE_SUMMARY.parent.resolve())
    return Path(rel_path).as_posix().replace(" ", "%20")


def markdown_table(headers: List[str], rows: List[List[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def build_section() -> str:
    release = read_json(DATA_INDEX / "topology_panel_v1_release_summary.json")
    benchmark = read_json(DATA_INDEX / "topology_panel_v1_benchmark_summary.json")
    best = read_json(DATA_INDEX / "topology_panel_v1_best_model_summary.json")
    delta = read_json(DATA_INDEX / "topology_panel_v1_image_input_delta_analysis_summary.json")
    auto_judge = read_json(DATA_INDEX / "topology_panel_v1_tile2x2_overlap10_auto_judge_summary.json")
    abandoned = read_json(DATA_INDEX / "topology_panel_v1_1_abandoned_policy_summary.json")
    experiment_rows = read_csv(DATA_INDEX / "topology_panel_v1_experiment_table.csv")
    model_rows = [row for row in experiment_rows if row["category"] == "model"]
    count_errors = best["count_errors"]

    mae_chart = rel_from_defense(DOCS / "figures" / "topology_panel_v1_mae_bar_chart.png")
    heatmap = rel_from_defense(DOCS / "figures" / "topology_panel_v1_per_sample_delta_heatmap.png")
    flow = rel_from_defense(DOCS / "figures" / "topology_panel_v1_data_cleaning_flow.png")

    experiment_table = markdown_table(
        ["实验", "输入", "valid", "node MAE", "edge MAE", "net MAE", "结论"],
        [
            [
                row["experiment_id"],
                row["input_version"],
                row["prediction_valid_rate"],
                row["node_mae"],
                row["edge_mae"],
                row["net_mae"],
                "当前最佳" if row["selected_as_current_best"] == "yes" else "对照实验",
            ]
            for row in model_rows
        ],
    )

    partition_table = markdown_table(
        ["分区", "数量", "答辩解释"],
        [
            ["clean_baseline", release["partition_counts"]["clean_baseline"], "正式 v1 benchmark，只用这 14 条计分"],
            ["excluded_badcase", release["partition_counts"]["excluded_badcase"], "多子图、几何异常、非拓扑目标等坏例，不进入正式评测"],
            ["improvement_target", release["partition_counts"]["improvement_target"], "算法改进候选，不和正式 v1 混用"],
            ["unreviewed", release["partition_counts"]["unreviewed"], "未审样本，暂不使用"],
        ],
    )

    graph_stats = benchmark["graph_stats"]
    graph_table = markdown_table(
        ["统计项", "min", "max", "mean"],
        [
            ["node_count", graph_stats["node_count"]["min"], graph_stats["node_count"]["max"], graph_stats["node_count"]["mean"]],
            ["edge_count", graph_stats["edge_count"]["min"], graph_stats["edge_count"]["max"], graph_stats["edge_count"]["mean"]],
            ["net_count", graph_stats["net_count"]["min"], graph_stats["net_count"]["max"], graph_stats["net_count"]["mean"]],
            [
                "intersection_count",
                graph_stats["intersection_count"]["min"],
                graph_stats["intersection_count"]["max"],
                graph_stats["intersection_count"]["mean"],
            ],
        ],
    )

    return f"""{SECTION_START}

---

## 补充专题：Industrial Diagram Benchmark 与 Topology Panel v1

> 本节整理自 `docs/project_final_summary.md`、`docs/topology_panel_v1_experiment_table.md` 和 `docs/topology_panel_v1_figures.md`，用于答辩中补充说明“工业图纸拓扑理解 benchmark 构建与真实模型评测”这一阶段性成果。

### 1. 为什么要增加这个专题

原有工作主要围绕电力工程接线图 VQA 微调与 LLM-judge 评测展开。为了进一步把“看懂图纸”从自然语言问答推进到结构化理解，本阶段补充构建了 **Industrial Diagram Benchmark / Topology Panel v1**：

- 面向工业电气图纸的 panel 级拓扑理解任务。
- 从图纸图片和几何结构中抽取 topology graph。
- 通过人工审核明确 clean baseline、badcase 和 improvement candidates 的边界。
- 建立 benchmark JSONL、评测协议、evaluator、模型预测 adapter 和 leaderboard。
- 将 GitHub 与 Hugging Face Dataset 的发布口径统一。

答辩时可以这样概括：

> 除了问答式理解，我进一步探索了工业图纸的结构化拓扑理解，将图纸拆成 panel 级样本，构建了一个小规模但人工复核严格的 Topology Panel v1 benchmark，并完成了真实视觉模型在该基准上的首轮可复现实验。

### 2. 数据清洗与版本边界

Topology Panel v1 的关键原则是：**宁可小规模，也要边界清楚、质量可解释**。正式 v1 只使用人工确认的 clean baseline，其余样本不混入正式分数。

{partition_table}

v1.1 的处理策略：

- 原始 improvement target：{release["partition_counts"]["improvement_target"]} 条。
- 其中 still_fragmented 诊断后放弃：{abandoned["abandoned_rows"]} 条。
- 当前保留 active improvement candidates：{abandoned["active_improvement_rows"]} 条。
- 后续路线：terminal-anchor {abandoned["active_next_route_counts"]["terminal_anchor_module"]} 条，over-connected repair {abandoned["active_next_route_counts"]["over_connected_repair"]} 条。

![Topology Panel v1 data cleaning flow]({flow})

图表讲解建议：

- 左侧是人工审核后的 171 个样本。
- 正式 benchmark 只走上方 clean baseline 分支，共 14 条。
- 中间 excluded badcase 记录数据质量问题，但不进入计分。
- 下方 improvement target 是未来算法修复对象，不和 v1 正式结果混用。
- 右上角形成 benchmark JSONL、评测协议和当前 best model baseline。

### 3. Topology Panel v1 benchmark 定义

正式 benchmark 文件：

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
docs/topology_graph_eval_protocol_v1.md
benchmark/topology/evaluate_topology_graph_v1.py
```

基本统计：

- 样本数：{benchmark["record_count"]}。
- 划分：train {benchmark["split_counts"]["train"]} / val {benchmark["split_counts"]["val"]} / test {benchmark["split_counts"]["test"]}。
- 缺失图片：{benchmark["asset_checks"]["missing_image_count"]}。
- 缺失拓扑图：{benchmark["asset_checks"]["missing_graph_count"]}。

{graph_table}

评测协议重点：

- 按 `panel_id` 对齐 reference 与 prediction。
- 输出 graph validity、node_count、edge_count、net_count。
- 输出 per-sample `eval_details.csv` 和 `eval_errors.csv`，便于定位错误。
- 使用 `reference_as_prediction` 做一致性 sanity check。
- 使用 `oracle_minus` 做指标敏感性 sanity baseline。

答辩讲法：

> 这个 benchmark 不是简单图片分类，而是要求模型或算法恢复图纸中的拓扑结构。现阶段先用 node、edge、net 三类 count-level 指标建立可复现实验闭环，后续再逐步推进到完整图结构匹配。

### 4. 真实模型实验设计

真实模型实验以 Doubao 为主，先限定为 **count-level synthetic graph baseline**：

1. 模型读取 panel 图片。
2. 输出 node_count、edge_count、net_count。
3. Adapter 将 count 结果转成 evaluator 可接收的 synthetic graph。
4. 使用同一套 evaluator 输出 MAE 与错误明细。

实验演进路线：

- Doubao v1：首次接入真实模型，但 valid rate 低。
- Prompt v2：提升输出格式稳定性，但 net_count 严重过估计。
- Prompt v3：明确 net_count 是连通分量数，修复 net_count 过估计。
- 1024 整图：验证单纯提高分辨率没有收益。
- tile2x2：降低单次输入的信息密度。
- tile2x2 + overlap10：缓解 tile 边界截断，成为当前最佳 node/edge 方案。

{experiment_table}

### 5. 当前最佳 baseline

当前固化的 best model baseline：

```text
method: doubao_prompt_v3_tile2x2_overlap10
model: Doubao
prompt: v3
image_input: tile2x2 + 10% overlap
aggregation: node=sum; edge=sum; net=mean_clamped3
rows: {best["prediction_rows"]}
prediction_valid_rate: {best["prediction_valid_rate"]}
node_count_mae: {count_errors["node_count"]["mae"]}
edge_count_mae: {count_errors["edge_count"]["mae"]}
net_count_mae: {count_errors["net_count"]["mae"]}
```

![Topology Panel v1 MAE bar chart]({mae_chart})

图表讲解建议：

- v1 到 v3 主要是 prompt 和输出定义优化。
- v3 后 net_count 已经稳定，主要瓶颈转为 node/edge。
- 1024 整图没有提升，说明瓶颈不是单纯分辨率不足。
- tile2x2 + overlap10 在 node/edge MAE 上最低，因此固化为 current best baseline。

### 6. Per-sample delta 分析

为了避免只看平均值，本阶段做了 per-sample delta analysis，比较 `tile2x2 + overlap10` 相对 `whole-image v3 512` 的逐样本误差变化。

![Topology Panel v1 per-sample delta heatmap]({heatmap})

热力图读法：

- 负数：overlap10 降低了绝对误差，是收益。
- 正数：overlap10 误差变大，是退化。
- node count 改善样本数：{delta["gain_counts_vs_512"]["node"]} / 14。
- edge count 改善样本数：{delta["gain_counts_vs_512"]["edge"]} / 14。
- net count 改善样本数：{delta["gain_counts_vs_512"]["net"]} / 14。

Auto judge 的全局判断：

- prefer overlap10：{auto_judge["decision_counts"]["prefer_overlap10"]}。
- overlap10 risk monitor：{auto_judge["decision_counts"]["overlap10_risk_monitor"]}。
- prefer overlap10 with monitoring：{auto_judge["decision_counts"]["prefer_overlap10_with_monitoring"]}。
- needs tile review before scaling：{auto_judge["decision_counts"]["needs_tile_review_before_scaling"]}。

答辩讲法：

> overlap10 的优势不是只体现在平均值上。逐样本分析显示，它在 10/14 个样本上改善了 node 和 edge 误差，说明 tile 边界截断确实是影响拓扑计数的重要因素。但仍有少数样本出现重复计数风险，因此后续不直接盲目扩展到 3x3，而是进入更精细的 hybrid pipeline。

### 7. 阶段性贡献总结

本阶段可以作为答辩中的一个独立贡献点：

1. 构建了面向工业图纸拓扑理解的 panel 级 benchmark 原型。
2. 明确区分 clean baseline、excluded badcase、v1.1 improvement candidates，避免数据边界混淆。
3. 建立了 benchmark JSONL、评测协议、evaluator、prediction schema 和 per-sample 错误定位机制。
4. 完成了 Doubao 在 Topology Panel v1 上的多轮 prompt / image-input 对比实验。
5. 通过图表证明 tile2x2 + overlap10 是当前最优 count-level baseline。
6. 将 GitHub 与 Hugging Face Dataset 的发布口径同步，便于复现和后续扩展。

### 8. 局限性与后续工作

当前 Topology Panel v1 仍有明确边界：

- 正式 clean baseline 只有 14 条，规模较小。
- 当前 best baseline 是 count-level synthetic graph，不是完整 topology graph reconstruction。
- 模型仍明显低估 node/edge 数量。
- 多子图、复杂端子锚点、over-connected 等问题仍需专门算法模块处理。

后续方向：

1. 生成答辩 PPT，将数据流转图、MAE 柱状图和 delta 热力图放入方法与实验部分。
2. 建立 hybrid pipeline：传统线段/交点检测 + OCR/符号检测 + VLM tile-level 审核。
3. 在 12 条 active v1.1 candidates 上验证 terminal-anchor 与 over-connected repair。
4. 扩充 clean baseline 样本，形成 Topology Panel v2。

### 9. 可直接放入答辩的口播稿

> 在问答任务之外，我还进一步构建了一个工业图纸拓扑理解基准 Topology Panel v1。这个基准从 171 个经过审核的 panel 样本中筛选出 14 条 clean baseline，并明确排除了多子图、几何异常和非拓扑目标等 badcase。为了保证实验可复现，我建立了 benchmark JSONL、评测协议、evaluator、prediction schema 和 per-sample 错误分析文件。
>
> 在模型实验方面，我以 Doubao 为真实视觉模型基线，逐步比较了 prompt v1、v2、v3、1024 整图、tile2x2 以及 tile2x2 overlap10。实验发现，单纯提高整图分辨率没有收益，而把图像切成 2x2 并加入 10% overlap 可以降低每次输入的信息密度，同时缓解 tile 边界截断问题。最终 `doubao_prompt_v3_tile2x2_overlap10` 在 node 和 edge MAE 上达到当前最好结果，因此被固化为 current best count-level baseline。
>
> 这个阶段的意义在于，它把“模型能不能看懂图纸”从自然语言问答进一步推进到结构化拓扑理解，并形成了可以发布、可以复现、可以逐步扩展的 benchmark 工程闭环。

{SECTION_END}
"""


def insert_or_replace_section(text: str, section: str) -> str:
    if SECTION_START in text and SECTION_END in text:
        start = text.index(SECTION_START)
        end = text.index(SECTION_END) + len(SECTION_END)
        return text[:start].rstrip() + "\n\n" + section.strip() + "\n\n" + text[end:].lstrip()

    first_rule = text.find("\n---")
    if first_rule != -1:
        insert_at = text.find("\n", first_rule + 1) + 1
        return text[:insert_at].rstrip() + "\n\n" + section.strip() + "\n\n" + text[insert_at:].lstrip()

    return text.rstrip() + "\n\n" + section.strip() + "\n"


def update_experiment_records() -> None:
    marker = "## 2026-07-10 Defense Summary Topology Panel v1 Integration"
    text = EXPERIMENT_RECORDS.read_text(encoding="utf-8")
    if marker in text:
        return
    section = f"""{marker}

- Integrated project final summary, experiment table, and figures into the external defense summary.
- External file:
  - `D:/LiuYanhong/Projects/BISHE/data/答辩汇报总结.md`
- Inserted section marker:
  - `{SECTION_START}`
- Included:
  - data boundary and cleaning flow explanation.
  - Topology Panel v1 benchmark definition.
  - Doubao model experiment table.
  - current best baseline metrics.
  - MAE bar chart, per-sample delta heatmap, and data cleaning flow chart.
  - ready-to-speak defense script.
"""
    EXPERIMENT_RECORDS.write_text(text.rstrip() + "\n\n" + section, encoding="utf-8")


def main() -> None:
    if not DEFENSE_SUMMARY.exists():
        raise SystemExit(f"Missing defense summary: {DEFENSE_SUMMARY}")
    text = DEFENSE_SUMMARY.read_text(encoding="utf-8")
    section = build_section()
    DEFENSE_SUMMARY.write_text(insert_or_replace_section(text, section), encoding="utf-8")
    update_experiment_records()
    print(f"Updated: {DEFENSE_SUMMARY}")
    print(f"Updated: {EXPERIMENT_RECORDS.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
