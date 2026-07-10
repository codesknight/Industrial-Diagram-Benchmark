"""Build final project summary and Topology Panel v1 experiment tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data_index"
DOCS = ROOT / "docs"

LEADERBOARD_CSV = DATA_INDEX / "topology_panel_v1_model_leaderboard.csv"
EXPERIMENT_TABLE_CSV = DATA_INDEX / "topology_panel_v1_experiment_table.csv"
EXPERIMENT_TABLE_MD = DOCS / "topology_panel_v1_experiment_table.md"
PROJECT_SUMMARY_MD = DOCS / "project_final_summary.md"
EXPERIMENT_RECORDS = ROOT / "experiment_records.md"


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def as_float(value: object, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    return float(value)


def fmt(value: object) -> str:
    if value in ("", None):
        return ""
    number = float(value)
    if number == int(number):
        return str(int(number))
    return f"{number:.6f}".rstrip("0").rstrip(".")


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: List[str], rows: Iterable[Iterable[object]]) -> List[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def build_experiment_rows() -> List[Dict[str, object]]:
    rows = read_csv(LEADERBOARD_CSV)
    comparable_models = [
        row
        for row in rows
        if row["experiment_id"] not in {"reference_as_prediction", "deepseek_smoke"}
    ]
    best = min(
        [row for row in comparable_models if row["category"] == "model"],
        key=lambda row: (as_float(row["node_mae"]) + as_float(row["edge_mae"])),
    )
    best_node = as_float(best["node_mae"])
    best_edge = as_float(best["edge_mae"])
    best_net = as_float(best["net_mae"])
    v3 = next(row for row in rows if row["experiment_id"] == "doubao_prompt_v3")
    v3_node = as_float(v3["node_mae"])
    v3_edge = as_float(v3["edge_mae"])
    v3_net = as_float(v3["net_mae"])

    out_rows: List[Dict[str, object]] = []
    ranked = sorted(
        comparable_models,
        key=lambda row: (
            0 if row["category"] == "model" else 1,
            as_float(row["node_mae"]) + as_float(row["edge_mae"]),
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        node = as_float(row["node_mae"])
        edge = as_float(row["edge_mae"])
        net = as_float(row["net_mae"])
        out_rows.append(
            {
                "rank_by_node_edge_mae": rank,
                "experiment_id": row["experiment_id"],
                "display_name": row["display_name"],
                "category": row["category"],
                "comparable": row["comparable"],
                "provider": row["provider"],
                "model": row["model"],
                "prompt_version": row["prompt_version"],
                "input_version": row["input_version"],
                "prediction_type": row["prediction_type"],
                "evaluated_rows": row["evaluated_rows"],
                "prediction_valid_rate": row["prediction_valid_rate"],
                "node_mae": row["node_mae"],
                "edge_mae": row["edge_mae"],
                "net_mae": row["net_mae"],
                "node_edge_mae_sum": round(node + edge, 6),
                "node_mae_delta_vs_v3": round(node - v3_node, 6),
                "edge_mae_delta_vs_v3": round(edge - v3_edge, 6),
                "net_mae_delta_vs_v3": round(net - v3_net, 6),
                "node_mae_delta_vs_best": round(node - best_node, 6),
                "edge_mae_delta_vs_best": round(edge - best_edge, 6),
                "net_mae_delta_vs_best": round(net - best_net, 6),
                "selected_as_current_best": "yes" if row["experiment_id"] == best["experiment_id"] else "no",
                "eval_summary": row["eval_summary"],
                "report": row["report"],
                "notes": row["notes"],
            }
        )
    return out_rows


def write_experiment_table_md(rows: List[Dict[str, object]]) -> None:
    selected = [row for row in rows if row["category"] == "model"]
    lines = [
        "# Topology Panel v1 实验结果总表",
        "",
        "日期：2026-07-10",
        "",
        "本表汇总 Topology Panel v1 上已经完成的真实模型与 sanity baseline 实验。正式可比较模型结果以 `category=model` 为主；`oracle_minus` 用于验证 evaluator 对拓扑错误是否敏感，不代表模型能力。",
        "",
        "## 核心模型对比",
        "",
        *markdown_table(
            [
                "rank",
                "experiment",
                "input",
                "valid",
                "node MAE",
                "edge MAE",
                "net MAE",
                "selected",
            ],
            [
                [
                    row["rank_by_node_edge_mae"],
                    row["experiment_id"],
                    row["input_version"],
                    row["prediction_valid_rate"],
                    fmt(row["node_mae"]),
                    fmt(row["edge_mae"]),
                    fmt(row["net_mae"]),
                    row["selected_as_current_best"],
                ]
                for row in selected
            ],
        ),
        "",
        "## Sanity Baseline",
        "",
        *markdown_table(
            ["experiment", "purpose", "node MAE", "edge MAE", "net MAE"],
            [
                [
                    row["experiment_id"],
                    row["notes"],
                    fmt(row["node_mae"]),
                    fmt(row["edge_mae"]),
                    fmt(row["net_mae"]),
                ]
                for row in rows
                if row["category"] == "sanity"
            ],
        ),
        "",
        "## 结论",
        "",
        "- 当前最佳真实模型 count-level baseline：`doubao_prompt_v3_tile2x2_overlap10`。",
        "- 相比整图 `doubao_prompt_v3`，tile2x2 + overlap10 的 node MAE 降低 `32.0`，edge MAE 降低 `27.785714`。",
        "- `net_count` 在 prompt v3 后已显著稳定，后续主要瓶颈转为 node/edge 计数和真实拓扑结构恢复。",
        "- 该实验仍是 count-level synthetic graph baseline，不等同于完整拓扑图重建。",
        "",
        "CSV 版本：`data_index/topology_panel_v1_experiment_table.csv`",
        "",
    ]
    EXPERIMENT_TABLE_MD.write_text("\n".join(lines), encoding="utf-8")


def write_project_summary() -> None:
    release = read_json(DATA_INDEX / "topology_panel_v1_release_summary.json")
    benchmark = read_json(DATA_INDEX / "topology_panel_v1_benchmark_summary.json")
    final_baseline = read_json(DATA_INDEX / "topology_panel_v1_final_baseline_summary.json")
    abandoned = read_json(DATA_INDEX / "topology_panel_v1_1_abandoned_policy_summary.json")
    best = read_json(DATA_INDEX / "topology_panel_v1_best_model_summary.json")
    delta = read_json(DATA_INDEX / "topology_panel_v1_image_input_delta_analysis_summary.json")
    auto_judge = read_json(DATA_INDEX / "topology_panel_v1_tile2x2_overlap10_auto_judge_summary.json")

    count_errors = best["count_errors"]
    graph_stats = benchmark["graph_stats"]
    lines = [
        "# Industrial Diagram Benchmark 项目阶段性总览",
        "",
        "日期：2026-07-10",
        "",
        "## 1. 项目定位",
        "",
        "Industrial Diagram Benchmark 面向工业电气图纸理解，当前阶段重点完成了从原始图纸数据到 panel 级拓扑图评测基准的工程闭环。项目覆盖数据清洗、panel 拆分、拓扑图生成、人工审核、benchmark JSONL、evaluator、模型预测 adapter、leaderboard 与 Hugging Face 发布包。",
        "",
        "当前最稳定的正式发布单元是 `Topology Panel v1 clean baseline`。它规模较小，但数据边界清晰、人工复核严格、评测脚本可复现，适合作为第一版拓扑图理解实验基准。",
        "",
        "## 2. 数据版本边界",
        "",
        *markdown_table(
            ["partition", "rows"],
            [[key, value] for key, value in release["partition_counts"].items()],
        ),
        "",
        "正式 v1 只包含 `clean_baseline` 的 14 条样本。其他分区只用于边界说明、badcase 分析或后续算法实验，不参与正式 v1 score。",
        "",
        "### Badcase 与 v1.1 策略",
        "",
        *markdown_table(
            ["type", "rows"],
            [[key, value] for key, value in release["badcase_reason_counts"].items()],
        ),
        "",
        "v1.1 中原始 improvement target 为 31 条，其中 19 条 `still_fragmented` 已固化为 abandoned，不再作为修复实验目标；剩余 12 条保留为 active improvement candidates。",
        "",
        *markdown_table(
            ["route", "rows"],
            [[key, value] for key, value in abandoned["active_next_route_counts"].items()],
        ),
        "",
        "## 3. Topology Panel v1 Benchmark",
        "",
        f"- Benchmark JSONL：`{benchmark['outputs']['jsonl']}`",
        f"- Evaluation protocol：`{benchmark['protocol']}`",
        f"- Record count：{benchmark['record_count']}",
        f"- Split：train {benchmark['split_counts']['train']} / val {benchmark['split_counts']['val']} / test {benchmark['split_counts']['test']}",
        f"- Asset check：missing image {benchmark['asset_checks']['missing_image_count']}，missing graph {benchmark['asset_checks']['missing_graph_count']}",
        "",
        "### Graph 规模统计",
        "",
        *markdown_table(
            ["metric", "min", "max", "mean"],
            [
                [name, stats["min"], stats["max"], stats["mean"]]
                for name, stats in graph_stats.items()
                if isinstance(stats, dict) and {"min", "max", "mean"}.issubset(stats)
            ],
        ),
        "",
        "## 4. 评测协议与脚本",
        "",
        "Topology Graph v1 的评测协议以 panel 为单位，要求预测结果按 `panel_id` 对齐，并输出 graph validity、node_count、edge_count、net_count 等指标。当前 evaluator 已支持：",
        "",
        "- 默认 `reference_as_prediction` sanity check。",
        "- 模型预测 JSONL schema 校验。",
        "- per-sample `eval_details.csv`。",
        "- 错误定位 `eval_errors.csv`。",
        "- oracle-minus sanity baseline，用于确认指标对删边、扰动节点等真实拓扑错误敏感。",
        "",
        "核心入口：`benchmark/topology/evaluate_topology_graph_v1.py`。",
        "",
        "## 5. 模型实验结果",
        "",
        "真实模型实验目前以 Doubao 为主，目标先限定为 count-level synthetic graph baseline。模型输出 node/edge/net count 后，由 adapter 转成 evaluator 可接受的 synthetic graph，用于统一指标比较。",
        "",
        "当前最佳模型基线：",
        "",
        f"- Method：`{best['method_id']}`",
        "- Model：Doubao",
        "- Prompt：v3",
        "- Image input：tile2x2 + 10% overlap",
        "- Aggregation：node=sum；edge=sum；net=mean_clamped3",
        f"- Rows：{best['prediction_rows']}",
        f"- Prediction valid rate：{best['prediction_valid_rate']}",
        f"- node_count MAE：{count_errors['node_count']['mae']}",
        f"- edge_count MAE：{count_errors['edge_count']['mae']}",
        f"- net_count MAE：{count_errors['net_count']['mae']}",
        "",
        "关键实验结论：",
        "",
        f"- 相比整图 512 输入，tile2x2 + overlap10 在 {delta['gain_counts_vs_512']['node']} / 14 个样本改善 node count，在 {delta['gain_counts_vs_512']['edge']} / 14 个样本改善 edge count。",
        f"- Auto judge 判定：{auto_judge['decision_counts'].get('prefer_overlap10', 0)} 个样本直接 prefer overlap10，{auto_judge['decision_counts'].get('overlap10_risk_monitor', 0)} 个样本需要风险监控。",
        "- 单纯提高整图分辨率到 1024 没有带来收益，说明主要瓶颈不是像素不足，而是整图信息密度过高。",
        "- prompt v3 解决了 v2 的 net_count 过估计问题；后续重点应转向图像输入策略和混合拓扑提取 pipeline。",
        "",
        "实验结果总表：`data_index/topology_panel_v1_experiment_table.csv` 与 `docs/topology_panel_v1_experiment_table.md`。",
        "",
        "## 6. 发布状态",
        "",
        "GitHub 与 Hugging Face Dataset 已同步当前版本边界和 best model baseline：",
        "",
        "- GitHub：`https://github.com/codesknight/Industrial-Diagram-Benchmark`",
        "- Hugging Face Dataset：`yanhongliu/Industrial-Diagram-Benchmark`",
        "- HF release package：`outputs/hf_release_topology_panel_v1/`",
        "- Dataset card：`docs/huggingface_dataset_card.md`",
        "- Release status：`docs/topology_panel_v1_release_status.md`",
        "",
        "## 7. 可答辩表述",
        "",
        "本阶段的核心贡献可以概括为：构建了一个面向工业图纸拓扑理解的 panel 级 benchmark 原型，明确区分 clean baseline、excluded badcase 和 v1.1 improvement candidates；实现了从数据清洗、人工审核到 benchmark JSONL 和 evaluator 的可复现实验闭环；并完成了真实视觉模型 Doubao 在该基准上的多轮 prompt / image-input 对比实验，最终固化了 tile2x2 + overlap10 的当前最佳 count-level baseline。",
        "",
        "## 8. 下一步建议",
        "",
        "1. 生成答辩图表：MAE 柱状图、per-sample delta heatmap、数据流转图。",
        "2. 将 `project_final_summary.md` 的内容整理进 `答辩汇报总结.md`。",
        "3. 建立 hybrid pipeline：传统线段/交点提取 + OCR/符号检测 + VLM tile-level 审核。",
        "4. 在 v1.1 active improvement candidates 上验证 terminal-anchor 和 over-connected repair 模块。",
        "",
        "## 9. 关键文件索引",
        "",
        "- `data_index/topology_panel_v1_final_baseline_manifest.csv`",
        "- `data_index/topology_panel_v1_benchmark_manifest.jsonl`",
        "- `docs/topology_graph_eval_protocol_v1.md`",
        "- `benchmark/topology/evaluate_topology_graph_v1.py`",
        "- `data_index/topology_panel_v1_model_leaderboard.csv`",
        "- `data_index/topology_panel_v1_best_model_summary.json`",
        "- `docs/topology_panel_v1_best_model_baseline.md`",
        "- `docs/topology_panel_v1_release_status.md`",
        "- `docs/huggingface_dataset_card.md`",
        "",
    ]
    PROJECT_SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def append_experiment_record() -> None:
    marker = "## 2026-07-10 Project Final Summary and Experiment Table"
    text = EXPERIMENT_RECORDS.read_text(encoding="utf-8")
    if marker in text:
        return
    section = f"""{marker}

- Generated project-level final summary for the current Industrial Diagram Benchmark stage.
- Generated Topology Panel v1 experiment result table in CSV and Markdown.
- Main outputs:
  - `docs/project_final_summary.md`
  - `data_index/topology_panel_v1_experiment_table.csv`
  - `docs/topology_panel_v1_experiment_table.md`
- Current best model baseline remains:
  - `doubao_prompt_v3_tile2x2_overlap10`
  - node MAE: 362.642857
  - edge MAE: 687.857143
  - net MAE: 0.857143
- The summary keeps the formal v1 boundary unchanged: 14 clean baseline rows only.
"""
    EXPERIMENT_RECORDS.write_text(text.rstrip() + "\n\n" + section, encoding="utf-8")


def main() -> None:
    rows = build_experiment_rows()
    write_csv(EXPERIMENT_TABLE_CSV, rows)
    write_experiment_table_md(rows)
    write_project_summary()
    append_experiment_record()
    print(f"Wrote: {EXPERIMENT_TABLE_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {EXPERIMENT_TABLE_MD.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {PROJECT_SUMMARY_MD.relative_to(ROOT).as_posix()}")
    print(f"Updated: {EXPERIMENT_RECORDS.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
