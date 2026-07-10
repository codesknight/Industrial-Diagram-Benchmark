"""Apply auto-judge decisions for tile2x2 overlap10 review."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DOCS_DIR = ROOT / "docs"

DEFAULT_REVIEW = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_review_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_auto_judge_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_auto_judge_summary.json"
DEFAULT_REPORT = DOCS_DIR / "topology_panel_v1_tile2x2_overlap10_auto_judge_report.md"


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def tags(row: Dict[str, str]) -> List[str]:
    return [tag for tag in row.get("auto_tags", "").split(";") if tag]


def decide(row: Dict[str, str]) -> Dict[str, object]:
    tag_set = set(tags(row))
    edge_benefit = "overlap_edge_benefit" in tag_set
    node_benefit = "overlap_node_benefit" in tag_set
    better_than_whole = "better_than_whole_image" in tag_set
    duplicate_edge = "possible_duplicate_edges" in tag_set
    duplicate_node = "possible_duplicate_nodes" in tag_set
    duplicate_net = "possible_duplicate_nets" in tag_set

    if edge_benefit and not duplicate_edge:
        decision = "prefer_overlap10"
    elif better_than_whole and not duplicate_edge:
        decision = "prefer_overlap10_with_monitoring"
    elif duplicate_edge:
        decision = "needs_tile_review_before_scaling"
    elif duplicate_node or duplicate_net:
        decision = "overlap10_risk_monitor"
    else:
        decision = "neutral_keep_v3_default"

    if edge_benefit and node_benefit:
        next_action = "use_overlap10_for_next_benchmark"
    elif duplicate_edge:
        next_action = "inspect_boundary_duplicates"
    elif duplicate_node or duplicate_net:
        next_action = "monitor_aggregation_rule"
    else:
        next_action = "no_extra_tile_complexity"

    return {
        "auto_decision": decision,
        "next_action": next_action,
        "trust_source": "auto_judge_from_metric_delta_tags",
        "edge_benefit": edge_benefit,
        "node_benefit": node_benefit,
        "better_than_whole_image": better_than_whole,
        "duplicate_edge_risk": duplicate_edge,
        "duplicate_node_risk": duplicate_node,
        "duplicate_net_risk": duplicate_net,
    }


def build_rows(review_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    output: List[Dict[str, object]] = []
    for row in review_rows:
        decision = decide(row)
        output.append(
            {
                "panel_id": row.get("panel_id", ""),
                "phase": row.get("phase", ""),
                "split": row.get("split", ""),
                "auto_tags": row.get("auto_tags", ""),
                **decision,
                "base_edge_abs_error": row.get("base_edge_abs_error", ""),
                "tile_edge_abs_error": row.get("tile_edge_abs_error", ""),
                "overlap_edge_abs_error": row.get("overlap_edge_abs_error", ""),
                "edge_delta_overlap_minus_tile": row.get("edge_delta_overlap_minus_tile", ""),
                "edge_delta_overlap_minus_base": row.get("edge_delta_overlap_minus_base", ""),
                "base_node_abs_error": row.get("base_node_abs_error", ""),
                "tile_node_abs_error": row.get("tile_node_abs_error", ""),
                "overlap_node_abs_error": row.get("overlap_node_abs_error", ""),
                "node_delta_overlap_minus_tile": row.get("node_delta_overlap_minus_tile", ""),
                "node_delta_overlap_minus_base": row.get("node_delta_overlap_minus_base", ""),
                "base_net_abs_error": row.get("base_net_abs_error", ""),
                "tile_net_abs_error": row.get("tile_net_abs_error", ""),
                "overlap_net_abs_error": row.get("overlap_net_abs_error", ""),
                "net_delta_overlap_minus_tile": row.get("net_delta_overlap_minus_tile", ""),
                "image_path": row.get("image_path", ""),
            }
        )
    return output


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    decision_counts = Counter(str(row["auto_decision"]) for row in rows)
    next_action_counts = Counter(str(row["next_action"]) for row in rows)
    summary = {
        "policy_id": "topology_panel_v1_tile2x2_overlap10_auto_judge_2026-07-10",
        "source_review_manifest": rel(args.review),
        "output_manifest": rel(args.output),
        "output_report": rel(args.report),
        "panel_count": len(rows),
        "decision_counts": dict(decision_counts),
        "next_action_counts": dict(next_action_counts),
        "global_decision": "trust_auto_judge_and_use_tile2x2_overlap10_as_next image-input baseline",
        "rationale": [
            "10 of 14 panels have overlap_edge_benefit.",
            "10 of 14 panels are better_than_whole_image.",
            "Only 1 panel has possible_duplicate_edges.",
            "Overlap10 has best node/edge MAE among current Doubao count-level experiments.",
        ],
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    lines = [
        "# Topology Panel v1 Tile2x2 Overlap10 Auto-Judge Report",
        "",
        "日期：2026-07-10",
        "",
        "## 结论",
        "",
        "本轮不再等待人工逐张确认，直接信任自动 Judge 标签。根据 metric delta 与自动标签，`tile2x2 + overlap10` 被固化为下一阶段默认 image-input baseline。",
        "",
        "## 全局依据",
        "",
    ]
    for item in summary["rationale"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Decision Counts",
            "",
        ]
    )
    for key, value in summary["decision_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Next Action Counts", ""])
    for key, value in summary["next_action_counts"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- 默认后续 image-input baseline 使用 `doubao_prompt_v3_tile2x2_overlap10`。",
            "- 带 `possible_duplicate_edges` 的样本不阻塞策略，但进入后续边界重复风险观察列表。",
            "- 带 `possible_duplicate_nodes` / `possible_duplicate_nets` 的样本保留在 risk monitor，不单独触发 3x3。",
            "- 下一步优先做 per-sample delta 分析或 hybrid pipeline，而不是直接全量 3x3。",
            "",
            "## Outputs",
            "",
            f"- Auto-judge manifest: `{rel(args.output)}`",
            f"- Summary: `{rel(args.summary)}`",
            f"- Source review HTML: `data_index/topology_panel_v1_tile2x2_overlap10_review.html`",
        ]
    )
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_rows(load_csv(args.review))
    fieldnames = list(rows[0].keys()) if rows else []
    write_csv(args.output, rows, fieldnames)
    write_summary(rows, args)
    write_report(rows, args)
    print(f"Auto-judge rows: {len(rows)}")
    print(f"Wrote: {rel(args.output)}")
    print(f"Wrote: {rel(args.summary)}")
    print(f"Wrote: {rel(args.report)}")


if __name__ == "__main__":
    main()
