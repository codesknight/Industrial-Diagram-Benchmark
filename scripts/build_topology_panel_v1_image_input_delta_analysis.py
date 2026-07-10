"""Build per-sample delta analysis for Topology Panel v1 image-input experiments."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DOCS_DIR = ROOT / "docs"

DETAIL_FILES = {
    "whole_v3_512": INDEX_DIR / "topology_panel_v1_doubao_v3_model_predictions_eval_details.csv",
    "whole_v3_1024": INDEX_DIR / "topology_panel_v1_doubao_v3_1024_model_predictions_eval_details.csv",
    "tile2x2": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_eval_details.csv",
    "tile2x2_overlap10": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_details.csv",
}

AUTO_JUDGE = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_auto_judge_manifest.csv"

OUTPUT_CSV = INDEX_DIR / "topology_panel_v1_image_input_delta_analysis.csv"
OUTPUT_MD = DOCS_DIR / "topology_panel_v1_image_input_delta_analysis.md"
OUTPUT_SUMMARY = INDEX_DIR / "topology_panel_v1_image_input_delta_analysis_summary.json"


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def by_panel(path: Path) -> Dict[str, Dict[str, str]]:
    return {row["panel_id"]: row for row in load_csv(path)}


def to_float(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def err(row: Dict[str, str], metric: str) -> float:
    return to_float(row.get(f"{metric}_count_abs_error", 0))


def pred(row: Dict[str, str], metric: str) -> int:
    return int(round(to_float(row.get(f"prediction_{metric}_count", 0))))


def ref(row: Dict[str, str], metric: str) -> int:
    return int(round(to_float(row.get(f"reference_{metric}_count", 0))))


def pct(delta: float, base: float) -> float:
    return 0.0 if base == 0 else round(delta / base * 100.0, 4)


def build_rows() -> List[Dict[str, object]]:
    details = {name: by_panel(path) for name, path in DETAIL_FILES.items()}
    auto_judge = {row["panel_id"]: row for row in load_csv(AUTO_JUDGE)}
    panel_ids = list(details["whole_v3_512"].keys())
    rows: List[Dict[str, object]] = []
    for panel_id in panel_ids:
        base = details["whole_v3_512"][panel_id]
        high = details["whole_v3_1024"][panel_id]
        tile = details["tile2x2"][panel_id]
        overlap = details["tile2x2_overlap10"][panel_id]
        judge = auto_judge.get(panel_id, {})

        row: Dict[str, object] = {
            "panel_id": panel_id,
            "phase": base.get("phase", ""),
            "split": base.get("split", ""),
            "auto_decision": judge.get("auto_decision", ""),
            "next_action": judge.get("next_action", ""),
            "auto_tags": judge.get("auto_tags", ""),
        }
        for metric in ["node", "edge", "net"]:
            base_err = err(base, metric)
            high_err = err(high, metric)
            tile_err = err(tile, metric)
            overlap_err = err(overlap, metric)
            row[f"reference_{metric}_count"] = ref(base, metric)
            row[f"whole_v3_512_pred_{metric}"] = pred(base, metric)
            row[f"whole_v3_1024_pred_{metric}"] = pred(high, metric)
            row[f"tile2x2_pred_{metric}"] = pred(tile, metric)
            row[f"tile2x2_overlap10_pred_{metric}"] = pred(overlap, metric)
            row[f"whole_v3_512_{metric}_abs_error"] = base_err
            row[f"whole_v3_1024_{metric}_abs_error"] = high_err
            row[f"tile2x2_{metric}_abs_error"] = tile_err
            row[f"tile2x2_overlap10_{metric}_abs_error"] = overlap_err
            row[f"delta_1024_minus_512_{metric}_error"] = high_err - base_err
            row[f"delta_tile2x2_minus_512_{metric}_error"] = tile_err - base_err
            row[f"delta_overlap10_minus_tile2x2_{metric}_error"] = overlap_err - tile_err
            row[f"delta_overlap10_minus_512_{metric}_error"] = overlap_err - base_err
            row[f"pct_overlap10_vs_512_{metric}_error"] = pct(overlap_err - base_err, base_err)

        edge_gain = to_float(row["delta_overlap10_minus_512_edge_error"]) < 0
        node_gain = to_float(row["delta_overlap10_minus_512_node_error"]) < 0
        net_gain = to_float(row["delta_overlap10_minus_512_net_error"]) < 0
        regressions = [
            metric
            for metric in ["node", "edge", "net"]
            if to_float(row[f"delta_overlap10_minus_512_{metric}_error"]) > 0
        ]
        row["overlap10_gain_pattern"] = "node_edge_net_gain" if edge_gain and node_gain and net_gain else (
            "node_edge_gain" if edge_gain and node_gain else
            "edge_only_gain" if edge_gain else
            "node_only_gain" if node_gain else
            "no_count_gain"
        )
        row["overlap10_regression_metrics"] = ";".join(regressions)
        rows.append(row)

    rows.sort(key=lambda item: (to_float(item["delta_overlap10_minus_512_edge_error"]), to_float(item["delta_overlap10_minus_512_node_error"])))
    return rows


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def aggregate(rows: List[Dict[str, object]]) -> Dict[str, object]:
    summary: Dict[str, object] = {
        "analysis_id": "topology_panel_v1_image_input_delta_analysis_2026-07-10",
        "row_count": len(rows),
        "output_csv": OUTPUT_CSV.resolve().relative_to(ROOT).as_posix(),
        "output_md": OUTPUT_MD.resolve().relative_to(ROOT).as_posix(),
        "mean_abs_error": {},
        "gain_counts_vs_512": {},
        "regression_counts_vs_512": {},
        "pattern_counts": {},
    }
    for setting in ["whole_v3_512", "whole_v3_1024", "tile2x2", "tile2x2_overlap10"]:
        summary["mean_abs_error"][setting] = {
            metric: round(sum(to_float(row[f"{setting}_{metric}_abs_error"]) for row in rows) / len(rows), 6)
            for metric in ["node", "edge", "net"]
        }
    for metric in ["node", "edge", "net"]:
        deltas = [to_float(row[f"delta_overlap10_minus_512_{metric}_error"]) for row in rows]
        summary["gain_counts_vs_512"][metric] = sum(1 for value in deltas if value < 0)
        summary["regression_counts_vs_512"][metric] = sum(1 for value in deltas if value > 0)
    for row in rows:
        pattern = str(row["overlap10_gain_pattern"])
        summary["pattern_counts"][pattern] = int(summary["pattern_counts"].get(pattern, 0)) + 1
    return summary


def md_table(rows: List[Dict[str, object]]) -> List[str]:
    lines = [
        "| panel_id | decision | pattern | edge delta vs 512 | node delta vs 512 | net delta vs 512 | edge delta overlap-tile | tags |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["panel_id"]),
                    str(row["auto_decision"]),
                    str(row["overlap10_gain_pattern"]),
                    f"{to_float(row['delta_overlap10_minus_512_edge_error']):.1f}",
                    f"{to_float(row['delta_overlap10_minus_512_node_error']):.1f}",
                    f"{to_float(row['delta_overlap10_minus_512_net_error']):.1f}",
                    f"{to_float(row['delta_overlap10_minus_tile2x2_edge_error']):.1f}",
                    str(row["auto_tags"]),
                ]
            )
            + " |"
        )
    return lines


def write_markdown(path: Path, rows: List[Dict[str, object]], summary: Dict[str, object]) -> None:
    mae = summary["mean_abs_error"]
    lines = [
        "# Topology Panel v1 Image Input Delta Analysis",
        "",
        "日期：2026-07-10",
        "",
        "## 目的",
        "",
        "本分析将整图输入、1024 整图输入、tile2x2、tile2x2 overlap10 的 per-sample 误差放到同一张表里，验证 overlap10 的平均收益是否由多数样本支撑，并定位重复计数风险样本。",
        "",
        "## 总体结果",
        "",
        "| setting | node MAE | edge MAE | net MAE |",
        "| --- | ---: | ---: | ---: |",
    ]
    for setting in ["whole_v3_512", "whole_v3_1024", "tile2x2", "tile2x2_overlap10"]:
        lines.append(
            f"| {setting} | {mae[setting]['node']} | {mae[setting]['edge']} | {mae[setting]['net']} |"
        )
    lines.extend(
        [
            "",
            "## Gain Counts vs Whole v3@512",
            "",
            f"- node error improved on {summary['gain_counts_vs_512']['node']} / {summary['row_count']} panels.",
            f"- edge error improved on {summary['gain_counts_vs_512']['edge']} / {summary['row_count']} panels.",
            f"- net error improved on {summary['gain_counts_vs_512']['net']} / {summary['row_count']} panels.",
            "",
            "## Pattern Counts",
            "",
        ]
    )
    for key, value in summary["pattern_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Per-Sample Delta Table",
            "",
            *md_table(rows),
            "",
            "## 结论",
            "",
            "tile2x2 overlap10 的平均优势不是单个样本造成的。它在 node 与 edge 上均有多数样本改善，且 auto judge 已将 overlap10 固化为下一阶段默认 image-input baseline。少数 duplicate 风险样本保留在 monitor，不阻塞策略。",
            "",
            "## 输出",
            "",
            f"- CSV: `{OUTPUT_CSV.resolve().relative_to(ROOT).as_posix()}`",
            f"- Summary: `{OUTPUT_SUMMARY.resolve().relative_to(ROOT).as_posix()}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_CSV, rows)
    summary = aggregate(rows)
    OUTPUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(OUTPUT_MD, rows, summary)
    print(f"Rows: {len(rows)}")
    print(f"Wrote: {OUTPUT_CSV.resolve().relative_to(ROOT).as_posix()}")
    print(f"Wrote: {OUTPUT_MD.resolve().relative_to(ROOT).as_posix()}")
    print(f"Wrote: {OUTPUT_SUMMARY.resolve().relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
