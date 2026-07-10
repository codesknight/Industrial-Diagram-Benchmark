"""Build the Topology Panel v1 model experiment leaderboard."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DOCS_DIR = ROOT / "docs"

OUTPUT_CSV = INDEX_DIR / "topology_panel_v1_model_leaderboard.csv"
OUTPUT_MD = DOCS_DIR / "topology_panel_v1_model_leaderboard.md"
OUTPUT_SUMMARY = INDEX_DIR / "topology_panel_v1_model_leaderboard_summary.json"


EXPERIMENTS = [
    {
        "experiment_id": "reference_as_prediction",
        "display_name": "Reference as Prediction",
        "category": "sanity",
        "comparable": "no",
        "provider": "reference",
        "model": "reference_graph",
        "prompt_version": "none",
        "input_version": "none",
        "prediction_type": "reference_as_prediction",
        "adapter_summary": None,
        "eval_summary": INDEX_DIR / "topology_panel_v1_eval_summary.json",
        "report": INDEX_DIR / "topology_panel_v1_eval_report.md",
        "notes": "Evaluator/package consistency check; not a model baseline.",
    },
    {
        "experiment_id": "oracle_minus",
        "display_name": "Oracle-minus",
        "category": "sanity",
        "comparable": "no",
        "provider": "oracle",
        "model": "oracle_minus",
        "prompt_version": "none",
        "input_version": "none",
        "prediction_type": "valid_perturbed_graph",
        "adapter_summary": INDEX_DIR / "topology_panel_v1_oracle_minus_summary.json",
        "eval_summary": INDEX_DIR / "topology_panel_v1_oracle_minus_eval_summary.json",
        "report": INDEX_DIR / "topology_panel_v1_oracle_minus_eval_report.md",
        "notes": "Official sanity baseline for evaluator sensitivity; not model performance.",
    },
    {
        "experiment_id": "doubao_v1",
        "display_name": "Doubao v1",
        "category": "model",
        "comparable": "yes",
        "provider": "doubao",
        "model": "",
        "prompt_version": "v1",
        "input_version": "image_512px_250k",
        "prediction_type": "count_only_synthetic_graph",
        "adapter_summary": INDEX_DIR / "topology_panel_v1_doubao_model_predictions_summary.json",
        "eval_summary": INDEX_DIR / "topology_panel_v1_doubao_model_predictions_eval_summary.json",
        "report": DOCS_DIR / "topology_panel_v1_doubao_eval_report.md",
        "notes": "First full real-model baseline; many rows were uncertain/unreadable.",
    },
    {
        "experiment_id": "doubao_prompt_v2",
        "display_name": "Doubao prompt v2",
        "category": "model",
        "comparable": "yes",
        "provider": "doubao",
        "model": "",
        "prompt_version": "v2",
        "input_version": "image_512px_250k",
        "prediction_type": "count_only_synthetic_graph",
        "adapter_summary": INDEX_DIR / "topology_panel_v1_doubao_v2_model_predictions_summary.json",
        "eval_summary": INDEX_DIR / "topology_panel_v1_doubao_v2_model_predictions_eval_summary.json",
        "report": DOCS_DIR / "topology_panel_v1_doubao_prompt_v2_comparison_report.md",
        "notes": "Improves valid/status behavior and node/edge counts; overestimates net_count.",
    },
    {
        "experiment_id": "doubao_prompt_v3",
        "display_name": "Doubao prompt v3",
        "category": "model",
        "comparable": "yes",
        "provider": "doubao",
        "model": "",
        "prompt_version": "v3",
        "input_version": "image_512px_250k",
        "prediction_type": "count_only_synthetic_graph",
        "adapter_summary": INDEX_DIR / "topology_panel_v1_doubao_v3_model_predictions_summary.json",
        "eval_summary": INDEX_DIR / "topology_panel_v1_doubao_v3_model_predictions_eval_summary.json",
        "report": DOCS_DIR / "topology_panel_v1_doubao_prompt_v3_comparison_report.md",
        "notes": "Keeps valid/status gains and fixes net_count overestimation with stricter connected-component rules.",
    },
    {
        "experiment_id": "deepseek_smoke",
        "display_name": "DeepSeek smoke",
        "category": "smoke",
        "comparable": "no",
        "provider": "deepseek",
        "model": "",
        "prompt_version": "v1",
        "input_version": "image_512px_250k",
        "prediction_type": "adapter_smoke",
        "adapter_summary": INDEX_DIR / "topology_panel_v1_deepseek_model_predictions_summary.json",
        "eval_summary": INDEX_DIR / "topology_panel_v1_deepseek_model_predictions_eval_summary.json",
        "report": INDEX_DIR / "topology_panel_v1_deepseek_model_predictions_eval_report.md",
        "notes": "Smoke run only; configured endpoint rejected image input, so it is not comparable.",
    },
]


def load_json(path: Optional[Path]) -> Dict[str, object]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Optional[Path]) -> str:
    if not path:
        return ""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def metric(summary: Dict[str, object], metric_name: str, stat: str) -> object:
    count_errors = summary.get("count_errors", {})
    if not isinstance(count_errors, dict):
        return ""
    metric_values = count_errors.get(metric_name, {})
    if not isinstance(metric_values, dict):
        return ""
    return metric_values.get(stat, "")


def build_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for spec in EXPERIMENTS:
        adapter = load_json(spec["adapter_summary"])
        evaluation = load_json(spec["eval_summary"])
        graph_valid_rate = evaluation.get("graph_valid_rate", {})
        if not isinstance(graph_valid_rate, dict):
            graph_valid_rate = {}
        invalid_prediction_rows = evaluation.get("invalid_prediction_rows", [])
        if not isinstance(invalid_prediction_rows, list):
            invalid_prediction_rows = []
        missing_prediction_rows = evaluation.get("missing_prediction_rows", [])
        if not isinstance(missing_prediction_rows, list):
            missing_prediction_rows = []
        extra_prediction_panel_ids = evaluation.get("extra_prediction_panel_ids", [])
        if not isinstance(extra_prediction_panel_ids, list):
            extra_prediction_panel_ids = []

        row = {
            "experiment_id": spec["experiment_id"],
            "display_name": spec["display_name"],
            "category": spec["category"],
            "comparable": spec["comparable"],
            "provider": adapter.get("provider") or spec["provider"],
            "model": adapter.get("model") or spec["model"],
            "prompt_version": adapter.get("prompt_version") or spec["prompt_version"],
            "input_version": spec["input_version"],
            "prediction_type": spec["prediction_type"],
            "prediction_rows": evaluation.get("prediction_rows", adapter.get("prediction_rows", "")),
            "evaluated_rows": evaluation.get("evaluated_rows", ""),
            "adapter_mode_counts": json.dumps(adapter.get("adapter_mode_counts", {}), ensure_ascii=False, sort_keys=True),
            "adapter_error_counts": json.dumps(adapter.get("adapter_error_counts", {}), ensure_ascii=False, sort_keys=True),
            "prediction_valid_rate": graph_valid_rate.get("prediction", ""),
            "reference_valid_rate": graph_valid_rate.get("reference", ""),
            "invalid_prediction_rows": len(invalid_prediction_rows),
            "missing_prediction_rows": len(missing_prediction_rows),
            "extra_prediction_panel_ids": len(extra_prediction_panel_ids),
            "node_mae": metric(evaluation, "node_count", "mae"),
            "node_mre": metric(evaluation, "node_count", "mre"),
            "edge_mae": metric(evaluation, "edge_count", "mae"),
            "edge_mre": metric(evaluation, "edge_count", "mre"),
            "net_mae": metric(evaluation, "net_count", "mae"),
            "net_mre": metric(evaluation, "net_count", "mre"),
            "eval_summary": rel(spec["eval_summary"]),
            "adapter_summary": rel(spec["adapter_summary"]),
            "report": rel(spec["report"]),
            "notes": spec["notes"],
        }
        rows.append(row)
    return rows


def write_csv(rows: List[Dict[str, object]]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object) -> str:
    if value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def md_table(rows: List[Dict[str, object]]) -> List[str]:
    headers = [
        "experiment_id",
        "comparable",
        "provider",
        "prompt",
        "valid_rate",
        "invalid",
        "node_mae",
        "edge_mae",
        "net_mae",
        "notes",
    ]
    lines = [
        "| experiment | comparable | provider | prompt | valid rate | invalid | node MAE | edge MAE | net MAE | notes |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        values = {
            "experiment_id": row["experiment_id"],
            "comparable": row["comparable"],
            "provider": row["provider"],
            "prompt": row["prompt_version"],
            "valid_rate": row["prediction_valid_rate"],
            "invalid": row["invalid_prediction_rows"],
            "node_mae": row["node_mae"],
            "edge_mae": row["edge_mae"],
            "net_mae": row["net_mae"],
            "notes": row["notes"],
        }
        lines.append("| " + " | ".join(fmt(values[key]) for key in headers) + " |")
    return lines


def best_ids(rows: List[Dict[str, object]], key: str, prefer: str) -> str:
    if not rows:
        return ""
    values = [float(row[key] or 0) for row in rows]
    best_value = max(values) if prefer == "max" else min(values)
    ids = [str(row["experiment_id"]) for row in rows if float(row[key] or 0) == best_value]
    return ", ".join(ids)


def write_markdown(rows: List[Dict[str, object]]) -> None:
    comparable_rows = [row for row in rows if row["comparable"] == "yes"]
    lines = [
        "# Topology Panel v1 模型实验 Leaderboard",
        "",
        "日期：2026-07-10",
        "",
        "本文件汇总 Topology Panel v1 的模型与 sanity baseline 评测结果。`comparable=yes` 的行可以作为真实模型实验横向比较；`comparable=no` 的行只用于链路校验、评测器敏感性验证或 smoke test。",
        "",
        "## 总览",
        "",
        *md_table(rows),
        "",
        "## 当前可比较模型结论",
        "",
    ]
    if comparable_rows:
        best_valid = max(comparable_rows, key=lambda row: float(row["prediction_valid_rate"] or 0))
        best_node = min(comparable_rows, key=lambda row: float(row["node_mae"] or 999999))
        best_edge = min(comparable_rows, key=lambda row: float(row["edge_mae"] or 999999))
        best_net = min(comparable_rows, key=lambda row: float(row["net_mae"] or 999999))
        lines.extend(
            [
                f"- 最高 prediction valid rate：`{best_ids(comparable_rows, 'prediction_valid_rate', 'max')}` = {fmt(best_valid['prediction_valid_rate'])}",
                f"- 最低 node_count MAE：`{best_ids(comparable_rows, 'node_mae', 'min')}` = {fmt(best_node['node_mae'])}",
                f"- 最低 edge_count MAE：`{best_ids(comparable_rows, 'edge_mae', 'min')}` = {fmt(best_edge['edge_mae'])}",
                f"- 最低 net_count MAE：`{best_ids(comparable_rows, 'net_mae', 'min')}` = {fmt(best_net['net_mae'])}",
                "",
                "Doubao prompt v3 相比 v2 保持了 status/valid 改善，同时显著修正 net_count 过估计，并继续小幅降低 node/edge MAE。当前下一步应转向 image input v2 或局部裁剪/分块输入实验。",
            ]
        )
    lines.extend(
        [
            "",
            "## 文件入口",
            "",
            f"- CSV：`{rel(OUTPUT_CSV)}`",
            f"- Summary：`{rel(OUTPUT_SUMMARY)}`",
            "- Doubao v1 report：`docs/topology_panel_v1_doubao_eval_report.md`",
            "- Doubao prompt v2 report：`docs/topology_panel_v1_doubao_prompt_v2_comparison_report.md`",
            "- Doubao prompt v3 report：`docs/topology_panel_v1_doubao_prompt_v3_comparison_report.md`",
            "- Evaluation protocol：`docs/topology_graph_eval_protocol_v1.md`",
            "",
            "## 更新规则",
            "",
            "新增模型或 prompt/input 实验后，先生成 prediction JSONL 并运行 evaluator，再将对应 adapter summary 与 eval summary 加入 `scripts/build_topology_panel_v1_model_leaderboard.py` 的 `EXPERIMENTS` 列表，最后重新运行脚本。",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(rows: List[Dict[str, object]]) -> None:
    comparable_rows = [row for row in rows if row["comparable"] == "yes"]
    summary = {
        "leaderboard_id": "topology_panel_v1_model_leaderboard_2026-07-10",
        "row_count": len(rows),
        "comparable_row_count": len(comparable_rows),
        "output_csv": rel(OUTPUT_CSV),
        "output_md": rel(OUTPUT_MD),
        "experiments": [row["experiment_id"] for row in rows],
        "best_comparable": {
            "prediction_valid_rate": best_ids(comparable_rows, "prediction_valid_rate", "max") if comparable_rows else "",
            "node_mae": best_ids(comparable_rows, "node_mae", "min") if comparable_rows else "",
            "edge_mae": best_ids(comparable_rows, "edge_mae", "min") if comparable_rows else "",
            "net_mae": best_ids(comparable_rows, "net_mae", "min") if comparable_rows else "",
        },
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    write_summary(rows)
    print(f"Wrote: {rel(OUTPUT_CSV)}")
    print(f"Wrote: {rel(OUTPUT_MD)}")
    print(f"Wrote: {rel(OUTPUT_SUMMARY)}")


if __name__ == "__main__":
    main()
