"""Run first Topology Panel v1.1 experiment on still-fragmented samples."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterable, List

import build_topology_panel_v1 as panel_v1


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_IMPROVEMENT = INDEX_DIR / "topology_panel_v1_release_improvement_manifest.csv"
DEFAULT_TOPOLOGY_MANIFEST = INDEX_DIR / "topology_graph_manifest.csv"
DEFAULT_INPUT = INDEX_DIR / "topology_panel_v1_1_still_fragmented_input.csv"
DEFAULT_EXPERIMENT = INDEX_DIR / "topology_panel_v1_1_still_fragmented_experiment_manifest.csv"
DEFAULT_BEST = INDEX_DIR / "topology_panel_v1_1_still_fragmented_best_candidates.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_1_still_fragmented_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_1_still_fragmented_report.md"
DEFAULT_OUTPUT_ROOT = ROOT / "outputs" / "topology_panel_v1_1_still_fragmented"

VARIANTS = [
    {
        "name": "baseline_0005_cap1",
        "endpoint_tolerance": 1.0,
        "endpoint_tolerance_ratio": 0.0005,
        "min_segment_length": 0.001,
    },
    {
        "name": "merge_0010_cap2",
        "endpoint_tolerance": 2.0,
        "endpoint_tolerance_ratio": 0.001,
        "min_segment_length": 0.001,
    },
    {
        "name": "merge_0020_cap5",
        "endpoint_tolerance": 5.0,
        "endpoint_tolerance_ratio": 0.002,
        "min_segment_length": 0.001,
    },
    {
        "name": "merge_0050_cap10",
        "endpoint_tolerance": 10.0,
        "endpoint_tolerance_ratio": 0.005,
        "min_segment_length": 0.001,
    },
]


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def int_value(value: object) -> int:
    try:
        return int(float(str(value or 0)))
    except ValueError:
        return 0


def float_value(value: object) -> float:
    try:
        return float(str(value or 0))
    except ValueError:
        return 0.0


def select_still_fragmented(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("topology_panel_v1_policy_exclude_reason") == "still_fragmented"
    ]


def variant_args(variant: Dict[str, object]) -> SimpleNamespace:
    name = str(variant["name"])
    return SimpleNamespace(
        output_dir=DEFAULT_OUTPUT_ROOT / name,
        endpoint_tolerance=float(variant["endpoint_tolerance"]),
        endpoint_tolerance_ratio=float(variant["endpoint_tolerance_ratio"]),
        min_segment_length=float(variant["min_segment_length"]),
        intersection_epsilon=1e-9,
        precision=4,
        max_segments=300000,
        limit=None,
        include_filtered=True,
    )


def run_variant(
    rows: List[Dict[str, str]],
    topology_by_parent: Dict[str, Dict[str, str]],
    variant: Dict[str, object],
) -> List[Dict[str, object]]:
    args = variant_args(variant)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_rows = [panel_v1.process_panel(row, topology_by_parent, args) for row in rows]
    for row in output_rows:
        row["variant"] = variant["name"]
        row["variant_endpoint_tolerance"] = variant["endpoint_tolerance"]
        row["variant_endpoint_tolerance_ratio"] = variant["endpoint_tolerance_ratio"]
        row["variant_min_segment_length"] = variant["min_segment_length"]
    return output_rows


def compare_row(source: Dict[str, str], result: Dict[str, object]) -> Dict[str, object]:
    original_edges = int_value(source.get("v1_edge_count", 0))
    original_nodes = int_value(source.get("v1_node_count", 0))
    original_nets = int_value(source.get("v1_net_count", 0))
    original_isolated = float_value(source.get("v1_isolated_edge_ratio", 0))
    original_largest = float_value(source.get("v1_largest_net_edge_ratio", 0))

    new_edges = int_value(result.get("v1_edge_count", 0))
    new_nodes = int_value(result.get("v1_node_count", 0))
    new_nets = int_value(result.get("v1_net_count", 0))
    new_isolated = float_value(result.get("v1_isolated_edge_ratio", 0))
    new_largest = float_value(result.get("v1_largest_net_edge_ratio", 0))

    no_edge_recovered = original_edges == 0 and new_edges > 0 and new_nets > 0
    fragmentation_reduced = original_edges > 0 and new_edges > 0 and new_isolated < max(original_isolated - 0.05, 0)
    dominant_component_improved = original_edges > 0 and new_largest > original_largest + 0.05
    candidate_improved = no_edge_recovered or fragmentation_reduced or dominant_component_improved

    # A very large edge increase is a warning that aggressive merging may be hiding a bad split/crop.
    overmerge_warning = original_edges > 0 and new_edges > original_edges * 2.5
    still_empty = new_edges == 0 or new_nets == 0

    return {
        "panel_id": source.get("panel_id", ""),
        "parent_drawing_key": source.get("parent_drawing_key", ""),
        "split": source.get("split", ""),
        "phase": source.get("phase", ""),
        "split_method": source.get("split_method", ""),
        "model_review_label": source.get("model_review_label", ""),
        "human_review_label": source.get("topology_panel_v1_review_label", ""),
        "original_quality_flags": source.get("quality_flags", ""),
        "variant": result.get("variant", ""),
        "variant_endpoint_tolerance": result.get("variant_endpoint_tolerance", ""),
        "variant_endpoint_tolerance_ratio": result.get("variant_endpoint_tolerance_ratio", ""),
        "status": result.get("status", ""),
        "error": result.get("error", ""),
        "original_nodes": original_nodes,
        "original_edges": original_edges,
        "original_nets": original_nets,
        "original_isolated_edge_ratio": original_isolated,
        "original_largest_net_edge_ratio": original_largest,
        "new_nodes": new_nodes,
        "new_edges": new_edges,
        "new_nets": new_nets,
        "new_isolated_edge_ratio": new_isolated,
        "new_largest_net_edge_ratio": new_largest,
        "edge_delta": new_edges - original_edges,
        "node_delta": new_nodes - original_nodes,
        "net_delta": new_nets - original_nets,
        "no_edge_recovered": no_edge_recovered,
        "fragmentation_reduced": fragmentation_reduced,
        "dominant_component_improved": dominant_component_improved,
        "candidate_improved": candidate_improved,
        "still_empty": still_empty,
        "overmerge_warning": overmerge_warning,
        "new_quality_flags": result.get("quality_flags", ""),
        "new_topology_v1_1_json_path": result.get("topology_v1_panel_json_path", ""),
    }


def best_candidates(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    by_panel: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        by_panel.setdefault(str(row["panel_id"]), []).append(row)

    best: List[Dict[str, object]] = []
    for panel_id, panel_rows in by_panel.items():
        ranked = sorted(
            panel_rows,
            key=lambda row: (
                bool(row.get("candidate_improved")),
                not bool(row.get("overmerge_warning")),
                not bool(row.get("still_empty")),
                -float_value(row.get("new_isolated_edge_ratio", 0)),
                float_value(row.get("new_largest_net_edge_ratio", 0)),
                int_value(row.get("new_edges", 0)),
            ),
            reverse=True,
        )
        candidate = dict(ranked[0])
        candidate["best_for_panel"] = panel_id
        best.append(candidate)
    return best


def build_summary(input_rows: List[Dict[str, str]], experiment_rows: List[Dict[str, object]], best_rows: List[Dict[str, object]]) -> Dict[str, object]:
    by_variant = {}
    for variant in [str(item["name"]) for item in VARIANTS]:
        rows = [row for row in experiment_rows if row.get("variant") == variant]
        by_variant[variant] = {
            "rows": len(rows),
            "status_counts": dict(Counter(str(row.get("status", "")) for row in rows)),
            "candidate_improved_rows": sum(1 for row in rows if row.get("candidate_improved") is True),
            "still_empty_rows": sum(1 for row in rows if row.get("still_empty") is True),
            "overmerge_warning_rows": sum(1 for row in rows if row.get("overmerge_warning") is True),
            "new_edge_count_avg": round(
                sum(int_value(row.get("new_edges", 0)) for row in rows) / len(rows),
                4,
            ) if rows else 0,
            "new_isolated_edge_ratio_avg": round(
                sum(float_value(row.get("new_isolated_edge_ratio", 0)) for row in rows) / len(rows),
                6,
            ) if rows else 0,
        }

    return {
        "experiment_id": "topology_panel_v1_1_still_fragmented_2026-07-08",
        "source_manifest": DEFAULT_IMPROVEMENT.relative_to(ROOT).as_posix(),
        "input_rows": len(input_rows),
        "variant_count": len(VARIANTS),
        "experiment_rows": len(experiment_rows),
        "best_candidate_rows": len(best_rows),
        "input_quality_flag_counts": dict(Counter(str(row.get("quality_flags", "")) for row in input_rows)),
        "input_model_label_counts": dict(Counter(str(row.get("model_review_label", "")) for row in input_rows)),
        "by_variant": by_variant,
        "best_candidate_improved_rows": sum(1 for row in best_rows if row.get("candidate_improved") is True),
        "best_still_empty_rows": sum(1 for row in best_rows if row.get("still_empty") is True),
        "best_overmerge_warning_rows": sum(1 for row in best_rows if row.get("overmerge_warning") is True),
        "rules": [
            "This is an improvement experiment only; no row is promoted into the v1 baseline automatically.",
            "No-edge rows that remain empty likely need geometry-type support, crop review, or target relabeling rather than endpoint tuning.",
            "Rows marked overmerge_warning require visual review before any future v1.1 promotion.",
        ],
        "outputs": {
            "input": DEFAULT_INPUT.relative_to(ROOT).as_posix(),
            "experiment_manifest": DEFAULT_EXPERIMENT.relative_to(ROOT).as_posix(),
            "best_candidates": DEFAULT_BEST.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
            "local_graph_dir": DEFAULT_OUTPUT_ROOT.relative_to(ROOT).as_posix(),
        },
    }


def write_report(summary: Dict[str, object], best_rows: List[Dict[str, object]]) -> None:
    lines = [
        "# Topology Panel v1.1 Still-Fragmented Experiment Report",
        "",
        "This report summarizes the first v1.1 repair experiment on rows labeled `still_fragmented`.",
        "The experiment varies endpoint merge tolerance only and does not change the formal v1 baseline.",
        "",
        "## Summary",
        "",
        f"- Experiment id: `{summary['experiment_id']}`",
        f"- Input rows: {summary['input_rows']}",
        f"- Variant count: {summary['variant_count']}",
        f"- Experiment rows: {summary['experiment_rows']}",
        f"- Best candidate rows: {summary['best_candidate_rows']}",
        f"- Best improved rows: {summary['best_candidate_improved_rows']}",
        f"- Best still-empty rows: {summary['best_still_empty_rows']}",
        f"- Best overmerge-warning rows: {summary['best_overmerge_warning_rows']}",
        "",
        "## Input Quality Flags",
        "",
    ]
    for flag, count in summary["input_quality_flag_counts"].items():
        lines.append(f"- {flag or 'empty'}: {count}")

    lines.extend(["", "## Variant Results", ""])
    for variant, stats in summary["by_variant"].items():
        lines.append(f"### {variant}")
        lines.append(f"- rows: {stats['rows']}")
        lines.append(f"- candidate improved rows: {stats['candidate_improved_rows']}")
        lines.append(f"- still-empty rows: {stats['still_empty_rows']}")
        lines.append(f"- overmerge-warning rows: {stats['overmerge_warning_rows']}")
        lines.append(f"- avg new edges: {stats['new_edge_count_avg']}")
        lines.append(f"- avg isolated edge ratio: {stats['new_isolated_edge_ratio_avg']}")
        lines.append("")

    lines.extend(["## Best Candidates", ""])
    for row in best_rows:
        lines.append(
            "- "
            f"{row['panel_id']}: variant={row['variant']}, "
            f"edges {row['original_edges']} -> {row['new_edges']}, "
            f"nets {row['original_nets']} -> {row['new_nets']}, "
            f"isolated {row['original_isolated_edge_ratio']} -> {row['new_isolated_edge_ratio']}, "
            f"improved={row['candidate_improved']}, "
            f"still_empty={row['still_empty']}, "
            f"overmerge_warning={row['overmerge_warning']}"
        )

    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    lines.extend(["", "## Outputs", ""])
    for name, path in summary["outputs"].items():
        lines.append(f"- {name}: `{path}`")

    DEFAULT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--improvement-manifest", type=Path, default=DEFAULT_IMPROVEMENT)
    parser.add_argument("--topology-manifest", type=Path, default=DEFAULT_TOPOLOGY_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    improvement_rows = load_csv(args.improvement_manifest)
    input_rows = select_still_fragmented(improvement_rows)
    write_csv(DEFAULT_INPUT, input_rows)

    topology_rows = load_csv(args.topology_manifest)
    topology_by_parent = {row["drawing_key"]: row for row in topology_rows}

    source_by_panel = {row["panel_id"]: row for row in input_rows}
    experiment_rows: List[Dict[str, object]] = []
    for variant in VARIANTS:
        result_rows = run_variant(input_rows, topology_by_parent, variant)
        for result in result_rows:
            source = source_by_panel[str(result.get("panel_id", ""))]
            experiment_rows.append(compare_row(source, result))

    fieldnames = list(experiment_rows[0].keys()) if experiment_rows else []
    write_csv(DEFAULT_EXPERIMENT, experiment_rows, fieldnames)
    best_rows = best_candidates(experiment_rows)
    write_csv(DEFAULT_BEST, best_rows, fieldnames + ["best_for_panel"])

    summary = build_summary(input_rows, experiment_rows, best_rows)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary, best_rows)

    print(f"Input still_fragmented rows: {summary['input_rows']}")
    print(f"Experiment rows: {summary['experiment_rows']}")
    print(f"Best improved rows: {summary['best_candidate_improved_rows']}")
    print(f"Best still-empty rows: {summary['best_still_empty_rows']}")
    print(f"Wrote: {DEFAULT_EXPERIMENT.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_REPORT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
