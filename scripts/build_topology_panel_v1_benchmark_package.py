"""Build JSONL benchmark package for Topology Panel v1 final baseline."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_final_baseline_manifest.csv"
DEFAULT_JSONL = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_benchmark_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_benchmark_report.md"

BENCHMARK_ID = "topology_panel_v1_benchmark_2026-07-08"


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path_value: str) -> Dict[str, object]:
    path = ROOT / path_value
    if not path.exists():
        return {"status": "missing"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "json_decode_error", "error": str(exc)}


def rel_exists(path_value: str) -> bool:
    if not path_value:
        return False
    return (ROOT / path_value).exists()


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


def graph_stats(row: Dict[str, str], graph: Dict[str, object]) -> Dict[str, object]:
    stats = graph.get("stats", {})
    if not isinstance(stats, dict):
        stats = {}
    return {
        "node_count": int_value(stats.get("node_count", row.get("v1_node_count", ""))),
        "edge_count": int_value(stats.get("edge_count", row.get("v1_edge_count", ""))),
        "net_count": int_value(stats.get("net_count", row.get("v1_net_count", ""))),
        "base_segment_count": int_value(stats.get("base_segment_count", row.get("base_segment_count", ""))),
        "split_segment_count": int_value(stats.get("split_segment_count", row.get("split_segment_count", ""))),
        "intersection_count": int_value(stats.get("intersection_count", row.get("intersection_count", ""))),
        "split_event_count": int_value(stats.get("split_event_count", row.get("split_event_count", ""))),
        "split_short_segments": int_value(stats.get("split_short_segments", row.get("split_short_segments", ""))),
        "isolated_edge_ratio": float_value(stats.get("isolated_edge_ratio", row.get("v1_isolated_edge_ratio", ""))),
        "largest_net_edge_ratio": float_value(
            stats.get("largest_net_edge_ratio", row.get("v1_largest_net_edge_ratio", ""))
        ),
        "effective_endpoint_tolerance": float_value(
            stats.get("effective_endpoint_tolerance", row.get("effective_endpoint_tolerance", ""))
        ),
        "edge_type_counts": stats.get("edge_type_counts", {}),
        "top_layers": stats.get("top_layers", {}),
        "graph_bbox": stats.get("graph_bbox", []),
    }


def target_summary(graph: Dict[str, object]) -> Dict[str, object]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    nets = graph.get("nets", [])
    return {
        "schema": graph.get("schema", ""),
        "status": graph.get("status", ""),
        "node_count": len(nodes) if isinstance(nodes, list) else 0,
        "edge_count": len(edges) if isinstance(edges, list) else 0,
        "net_count": len(nets) if isinstance(nets, list) else 0,
    }


def build_record(row: Dict[str, str]) -> Dict[str, object]:
    graph = load_json(row.get("topology_v1_panel_json_path", ""))
    return {
        "benchmark_id": BENCHMARK_ID,
        "task": "panel_topology_graph_v1",
        "panel_id": row.get("panel_id", ""),
        "parent_drawing_key": row.get("parent_drawing_key", ""),
        "split": row.get("split", ""),
        "phase": row.get("phase", ""),
        "batch": row.get("batch", ""),
        "panel": {
            "index": int_value(row.get("panel_index", "")),
            "count": int_value(row.get("panel_count", "")),
            "split_method": row.get("split_method", ""),
            "bbox_cad": row.get("panel_bbox_cad", ""),
        },
        "input": {
            "image_path": row.get("panel_png_path", ""),
            "image_exists": rel_exists(row.get("panel_png_path", "")),
        },
        "reference": {
            "topology_json_path": row.get("topology_v1_panel_json_path", ""),
            "topology_json_exists": rel_exists(row.get("topology_v1_panel_json_path", "")),
            "topology_summary": target_summary(graph),
        },
        "source": {
            "parent_normalized_json_path": row.get("parent_normalized_json_path", ""),
            "parent_topology_v0_json_path": row.get("parent_topology_v0_json_path", ""),
        },
        "graph_stats": graph_stats(row, graph),
        "quality": {
            "final_label": row.get("topology_panel_v1_final_review_label", ""),
            "release_partition": row.get("topology_panel_v1_release_partition", ""),
            "release_use": row.get("topology_panel_v1_release_use", ""),
            "human_review_comment": row.get("topology_panel_v1_final_review_comment", ""),
            "model_review_label": row.get("model_review_label", ""),
            "model_confidence": row.get("model_confidence", ""),
            "model_reason": row.get("model_reason", ""),
            "quality_flags": row.get("quality_flags", ""),
        },
        "evaluation": {
            "include_in_v1_score": row.get("topology_panel_v1_final_is_baseline", "") == "True",
            "expected_prediction_schema": "industrial_diagram.topology_graph.v1_panel",
            "protocol": "docs/topology_graph_eval_protocol_v1.md",
        },
    }


def write_jsonl(path: Path, records: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def numeric_stats(records: List[Dict[str, object]], key: str) -> Dict[str, float]:
    values = [float_value(record["graph_stats"].get(key, 0)) for record in records]
    if not values:
        return {"min": 0, "max": 0, "mean": 0.0}
    return {
        "min": min(values),
        "max": max(values),
        "mean": round(sum(values) / len(values), 4),
    }


def build_summary(records: List[Dict[str, object]]) -> Dict[str, object]:
    split_counts = Counter(str(record.get("split", "")) for record in records)
    phase_counts = Counter(str(record.get("phase", "")) for record in records)
    missing_images = [
        record["panel_id"]
        for record in records
        if not record["input"]["image_exists"]
    ]
    missing_graphs = [
        record["panel_id"]
        for record in records
        if not record["reference"]["topology_json_exists"]
    ]
    return {
        "benchmark_id": BENCHMARK_ID,
        "source_manifest": DEFAULT_MANIFEST.relative_to(ROOT).as_posix(),
        "output_jsonl": DEFAULT_JSONL.relative_to(ROOT).as_posix(),
        "protocol": "docs/topology_graph_eval_protocol_v1.md",
        "record_count": len(records),
        "split_counts": dict(split_counts),
        "phase_counts": dict(phase_counts),
        "asset_checks": {
            "missing_image_count": len(missing_images),
            "missing_graph_count": len(missing_graphs),
            "missing_image_panel_ids": missing_images,
            "missing_graph_panel_ids": missing_graphs,
        },
        "graph_stats": {
            "node_count": numeric_stats(records, "node_count"),
            "edge_count": numeric_stats(records, "edge_count"),
            "net_count": numeric_stats(records, "net_count"),
            "intersection_count": numeric_stats(records, "intersection_count"),
            "isolated_edge_ratio": numeric_stats(records, "isolated_edge_ratio"),
            "largest_net_edge_ratio": numeric_stats(records, "largest_net_edge_ratio"),
        },
        "quality_label_counts": dict(
            Counter(str(record["quality"].get("final_label", "")) for record in records)
        ),
        "outputs": {
            "jsonl": DEFAULT_JSONL.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
        },
    }


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1 Benchmark Package Report",
        "",
        f"Benchmark id: `{summary['benchmark_id']}`",
        "",
        "This package converts the final 14-row Topology Panel v1 baseline into a JSONL benchmark manifest.",
        "",
        "## Summary",
        "",
        f"- Records: {summary['record_count']}",
        f"- Source manifest: `{summary['source_manifest']}`",
        f"- Output JSONL: `{summary['output_jsonl']}`",
        f"- Protocol: `{summary['protocol']}`",
        "",
        "## Splits",
        "",
    ]
    for split, count in summary["split_counts"].items():
        lines.append(f"- {split}: {count}")

    lines.extend(["", "## Phases", ""])
    for phase, count in summary["phase_counts"].items():
        lines.append(f"- {phase}: {count}")

    assets = summary["asset_checks"]
    lines.extend([
        "",
        "## Asset Checks",
        "",
        f"- Missing images: {assets['missing_image_count']}",
        f"- Missing topology graphs: {assets['missing_graph_count']}",
        "",
        "## Graph Stats",
        "",
    ])
    for name, stats in summary["graph_stats"].items():
        lines.append(f"- {name}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")

    lines.extend(["", "## Quality Labels", ""])
    for label, count in summary["quality_label_counts"].items():
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Outputs", ""])
    for name, path in summary["outputs"].items():
        lines.append(f"- {name}: `{path}`")

    DEFAULT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    records = [build_record(row) for row in rows]
    write_jsonl(args.jsonl, records)
    summary = build_summary(records)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary)

    print(f"Benchmark id: {summary['benchmark_id']}")
    print(f"Records: {summary['record_count']}")
    print(f"Missing images: {summary['asset_checks']['missing_image_count']}")
    print(f"Missing topology graphs: {summary['asset_checks']['missing_graph_count']}")
    print(f"Wrote: {args.jsonl.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_REPORT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
