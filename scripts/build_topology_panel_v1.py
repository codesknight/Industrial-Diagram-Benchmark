"""Build panel-level Topology Graph v1 for usable/final panels.

This is the full-data successor of `build_topology_panel_v1_pilot.py`. It
filters normalized drawing entities into panel CAD bboxes, splits wire-like
segments at geometric intersections, then writes one v1 topology graph JSON per
panel plus a manifest and summary report.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from build_topology_v1_pilot import (
    ROOT,
    detect_split_points,
    effective_endpoint_tolerance,
    graph_from_segments,
    iter_base_segments,
    split_segments,
)


INDEX_DIR = ROOT / "data_index"
DEFAULT_PANEL_MANIFEST = INDEX_DIR / "final_panel_manifest.csv"
DEFAULT_TOPOLOGY_MANIFEST = INDEX_DIR / "topology_graph_manifest.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "topology_panel_v1"
DEFAULT_OUTPUT_MANIFEST = INDEX_DIR / "topology_panel_v1_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_report.md"

BBox = Tuple[float, float, float, float]


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Optional[List[str]] = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else DEFAULT_FIELDNAMES
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_bbox(value: str) -> Optional[BBox]:
    parts = str(value or "").split(",")
    if len(parts) != 4:
        return None
    try:
        x0, y0, x1, y1 = [float(part) for part in parts]
    except ValueError:
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def fmt_bbox(box: Sequence[float]) -> str:
    return ",".join(str(round(float(value), 4)) for value in box)


def as_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def center_in_bbox(entity: Dict[str, object], panel_bbox: BBox) -> bool:
    raw_bbox = entity.get("bbox")
    if not isinstance(raw_bbox, list) or len(raw_bbox) < 4:
        return False
    try:
        x0, y0, x1, y1 = [float(value) for value in raw_bbox[:4]]
    except (TypeError, ValueError):
        return False
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    return panel_bbox[0] <= cx <= panel_bbox[2] and panel_bbox[1] <= cy <= panel_bbox[3]


def safe_output_path(panel_id: str, output_dir: Path) -> Path:
    return output_dir / Path(panel_id.replace("\\", "/") + ".topology.v1.json")


def make_error_row(panel: Dict[str, str], message: str) -> Dict[str, object]:
    return {
        "panel_id": panel.get("panel_id", ""),
        "parent_drawing_key": panel.get("parent_drawing_key", ""),
        "split": panel.get("split", ""),
        "phase": panel.get("phase", ""),
        "batch": panel.get("batch", ""),
        "panel_index": panel.get("panel_index", ""),
        "panel_count": panel.get("panel_count", ""),
        "split_method": panel.get("split_method", ""),
        "panel_png_path": panel.get("panel_png_path", ""),
        "panel_bbox_cad": panel.get("panel_bbox_cad", ""),
        "parent_normalized_json_path": "",
        "parent_topology_v0_json_path": "",
        "topology_v1_panel_json_path": "",
        "status": "error",
        "error": message,
        "panel_entity_count": 0,
        "base_segment_count": 0,
        "split_segment_count": 0,
        "intersection_count": 0,
        "split_event_count": 0,
        "split_short_segments": 0,
        "v1_node_count": 0,
        "v1_edge_count": 0,
        "v1_net_count": 0,
        "v1_isolated_edge_ratio": 0.0,
        "v1_largest_net_edge_ratio": 0.0,
        "effective_endpoint_tolerance": "",
        "quality_flags": "error",
    }


def process_panel(
    panel: Dict[str, str],
    topology_by_parent: Dict[str, Dict[str, str]],
    args: argparse.Namespace,
) -> Dict[str, object]:
    try:
        return process_panel_or_raise(panel, topology_by_parent, args)
    except Exception as exc:  # noqa: BLE001 - keep full batches moving and record the row error.
        return make_error_row(panel, str(exc))


def process_panel_or_raise(
    panel: Dict[str, str],
    topology_by_parent: Dict[str, Dict[str, str]],
    args: argparse.Namespace,
) -> Dict[str, object]:
    parent_key = panel["parent_drawing_key"]
    topology_row = topology_by_parent.get(parent_key)
    if not topology_row:
        raise ValueError(f"missing parent topology row: {parent_key}")

    normalized_path = ROOT / topology_row["normalized_json_path"]
    with normalized_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    panel_cad_bbox = parse_bbox(panel.get("panel_bbox_cad", ""))
    if panel_cad_bbox is None:
        raise ValueError(f"invalid panel_bbox_cad: {panel.get('panel_bbox_cad', '')}")

    raw_entities = payload.get("entities", [])
    entities = raw_entities if isinstance(raw_entities, list) else []
    panel_entities = [
        entity
        for entity in entities
        if isinstance(entity, dict) and center_in_bbox(entity, panel_cad_bbox)
    ]
    stats = payload.get("stats", {})
    stats = stats if isinstance(stats, dict) else {}
    parent_drawing_bbox = stats.get("drawing_bbox")
    panel_payload = {
        **payload,
        "drawing_key": panel["panel_id"],
        "source": {
            **(payload.get("source", {}) if isinstance(payload.get("source", {}), dict) else {}),
            "parent_drawing_key": parent_key,
            "panel_png_path": panel.get("panel_png_path", ""),
            "split_method": panel.get("split_method", ""),
        },
        "stats": {
            **stats,
            "entity_count": len(panel_entities),
            "drawing_bbox": list(panel_cad_bbox),
            "parent_drawing_bbox": parent_drawing_bbox,
        },
        "entities": panel_entities,
    }

    active_tolerance = effective_endpoint_tolerance(
        panel_payload,
        args.endpoint_tolerance,
        args.endpoint_tolerance_ratio,
        args.min_segment_length,
    )
    base_segments = list(iter_base_segments(panel_entities, args.min_segment_length))
    split_params, intersection_count, split_event_count = detect_split_points(
        base_segments,
        tolerance=active_tolerance,
        intersection_epsilon=args.intersection_epsilon,
    )
    split, split_short_segments = split_segments(base_segments, split_params, args.min_segment_length)
    output_path = safe_output_path(panel["panel_id"], args.output_dir.resolve())
    graph_row = {
        "drawing_key": panel["panel_id"],
        "split": panel.get("split", ""),
        "phase": panel.get("phase", ""),
        "normalized_json_path": topology_row["normalized_json_path"],
        "topology_json_path": topology_row.get("topology_json_path", ""),
    }
    result = graph_from_segments(
        row=graph_row,
        payload=panel_payload,
        base_segments=base_segments,
        segments=split,
        output_path=output_path,
        tolerance=args.endpoint_tolerance,
        tolerance_ratio=args.endpoint_tolerance_ratio,
        min_segment_length=args.min_segment_length,
        precision=args.precision,
        max_segments=args.max_segments,
        intersection_count=intersection_count,
        split_event_count=split_event_count,
        split_short_segments=split_short_segments,
    )
    rewrite_graph_metadata(output_path, panel, topology_row)

    quality_flags = quality_flags_for(result)
    return {
        "panel_id": panel["panel_id"],
        "parent_drawing_key": parent_key,
        "split": panel.get("split", ""),
        "phase": panel.get("phase", ""),
        "batch": panel.get("batch", ""),
        "panel_index": panel.get("panel_index", ""),
        "panel_count": panel.get("panel_count", ""),
        "split_method": panel.get("split_method", ""),
        "panel_png_path": panel.get("panel_png_path", ""),
        "panel_bbox_cad": fmt_bbox(panel_cad_bbox),
        "parent_normalized_json_path": topology_row.get("normalized_json_path", ""),
        "parent_topology_v0_json_path": topology_row.get("topology_json_path", ""),
        "topology_v1_panel_json_path": result["topology_v1_json_path"],
        "status": result["status"],
        "error": "",
        "panel_entity_count": len(panel_entities),
        "base_segment_count": result["base_segment_count"],
        "split_segment_count": result["split_segment_count"],
        "intersection_count": result["intersection_count"],
        "split_event_count": result["split_event_count"],
        "split_short_segments": result["split_short_segments"],
        "v1_node_count": result["v1_node_count"],
        "v1_edge_count": result["v1_edge_count"],
        "v1_net_count": result["v1_net_count"],
        "v1_isolated_edge_ratio": result["v1_isolated_edge_ratio"],
        "v1_largest_net_edge_ratio": result["v1_largest_net_edge_ratio"],
        "effective_endpoint_tolerance": result["effective_endpoint_tolerance"],
        "quality_flags": ";".join(quality_flags),
    }


def quality_flags_for(result: Dict[str, object]) -> List[str]:
    flags: List[str] = []
    edge_count = int(result.get("v1_edge_count", 0) or 0)
    net_count = int(result.get("v1_net_count", 0) or 0)
    isolated_ratio = float(result.get("v1_isolated_edge_ratio", 0) or 0)
    largest_ratio = float(result.get("v1_largest_net_edge_ratio", 0) or 0)
    if edge_count == 0:
        flags.append("no_edges")
    if net_count == 0:
        flags.append("no_nets")
    if isolated_ratio > 0.2:
        flags.append("high_isolated_ratio")
    if edge_count > 0 and largest_ratio > 0.95:
        flags.append("dominant_component")
    if edge_count > 0 and largest_ratio < 0.15:
        flags.append("high_fragmentation")
    return flags


def rewrite_graph_metadata(
    output_path: Path,
    panel: Dict[str, str],
    topology_row: Dict[str, str],
) -> None:
    with output_path.open("r", encoding="utf-8") as f:
        graph_payload = json.load(f)
    graph_payload["schema"] = "industrial_diagram.topology_graph.v1_panel"
    graph_payload["panel_id"] = panel.get("panel_id", "")
    graph_payload["parent_drawing_key"] = panel.get("parent_drawing_key", "")
    graph_payload["panel_index"] = panel.get("panel_index", "")
    graph_payload["panel_count"] = panel.get("panel_count", "")
    graph_payload["split_method"] = panel.get("split_method", "")
    source = graph_payload.get("source", {})
    if not isinstance(source, dict):
        source = {}
    source.update(
        {
            "parent_normalized_json_path": topology_row.get("normalized_json_path", ""),
            "parent_topology_v0_json_path": topology_row.get("topology_json_path", ""),
            "panel_png_path": panel.get("panel_png_path", ""),
            "panel_bbox_cad": panel.get("panel_bbox_cad", ""),
        }
    )
    graph_payload["source"] = source
    output_path.write_text(
        json.dumps(graph_payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-manifest", type=Path, default=DEFAULT_PANEL_MANIFEST)
    parser.add_argument("--topology-manifest", type=Path, default=DEFAULT_TOPOLOGY_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--endpoint-tolerance", type=float, default=1.0)
    parser.add_argument("--endpoint-tolerance-ratio", type=float, default=0.0005)
    parser.add_argument("--min-segment-length", type=float, default=0.001)
    parser.add_argument("--intersection-epsilon", type=float, default=1e-9)
    parser.add_argument("--precision", type=int, default=4)
    parser.add_argument("--max-segments", type=int, default=300000)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--include-filtered", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    panel_rows = load_csv(args.panel_manifest)
    if not args.include_filtered and panel_rows and "final_keep" in panel_rows[0]:
        panel_rows = [row for row in panel_rows if as_bool(row.get("final_keep", ""))]
    if args.limit:
        panel_rows = panel_rows[: args.limit]

    topology_rows = load_csv(args.topology_manifest)
    topology_by_parent = {row["drawing_key"]: row for row in topology_rows}
    manifest_rows = [process_panel(row, topology_by_parent, args) for row in panel_rows]

    write_csv(args.output_manifest, manifest_rows, DEFAULT_FIELDNAMES)
    write_summary(manifest_rows, args)

    print(f"Panel rows: {len(manifest_rows)}")
    print(f"Status counts: {dict(Counter(str(row['status']) for row in manifest_rows))}")
    print(f"Wrote: {args.output_manifest.resolve().relative_to(ROOT).as_posix()}")
    print(f"Wrote local graph JSON under: {args.output_dir.resolve().relative_to(ROOT).as_posix()}")


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    ok_rows = [row for row in rows if row.get("status") in {"ok", "truncated_max_segments"}]
    error_rows = [row for row in rows if row.get("status") == "error"]
    edge_counts = [int(row["v1_edge_count"]) for row in ok_rows]
    net_counts = [int(row["v1_net_count"]) for row in ok_rows]
    intersection_counts = [int(row["intersection_count"]) for row in ok_rows]
    no_edge_rows = [row for row in ok_rows if int(row["v1_edge_count"]) == 0]
    summary = {
        "panel_rows": len(rows),
        "ok_rows": len(ok_rows),
        "error_rows": len(error_rows),
        "parent_drawing_count": len({row["parent_drawing_key"] for row in rows if row.get("parent_drawing_key")}),
        "by_split": dict(Counter(str(row["split"]) for row in rows)),
        "by_phase": dict(Counter(str(row["phase"]) for row in rows)),
        "status_counts": dict(Counter(str(row["status"]) for row in rows)),
        "quality_flag_counts": quality_flag_counts(rows),
        "v1_edge_count_min": min(edge_counts) if edge_counts else 0,
        "v1_edge_count_avg": round(sum(edge_counts) / len(edge_counts), 2) if edge_counts else 0,
        "v1_edge_count_max": max(edge_counts) if edge_counts else 0,
        "v1_net_count_min": min(net_counts) if net_counts else 0,
        "v1_net_count_avg": round(sum(net_counts) / len(net_counts), 2) if net_counts else 0,
        "v1_net_count_max": max(net_counts) if net_counts else 0,
        "intersection_count_total": sum(intersection_counts),
        "intersection_count_avg": round(sum(intersection_counts) / len(intersection_counts), 2) if intersection_counts else 0,
        "no_edge_rows": len(no_edge_rows),
        "output_manifest": args.output_manifest.resolve().relative_to(ROOT).as_posix(),
        "output_dir": args.output_dir.resolve().relative_to(ROOT).as_posix(),
        "params": {
            "endpoint_merge_tolerance": args.endpoint_tolerance,
            "endpoint_tolerance_ratio": args.endpoint_tolerance_ratio,
            "min_segment_length": args.min_segment_length,
            "intersection_epsilon": args.intersection_epsilon,
            "max_segments": args.max_segments,
            "limit": args.limit,
        },
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary, rows, args.report)


def quality_flag_counts(rows: List[Dict[str, object]]) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        flags = str(row.get("quality_flags", ""))
        if not flags:
            counts["none"] += 1
            continue
        for flag in flags.split(";"):
            if flag:
                counts[flag] += 1
    return dict(counts)


def write_report(summary: Dict[str, object], rows: List[Dict[str, object]], report_path: Path) -> None:
    lines = [
        "# Topology Panel v1 Report",
        "",
        "This report summarizes panel-level v1 topology graphs built with line-intersection splitting.",
        "",
        "## Summary",
        "",
        f"- Panel rows: {summary['panel_rows']}",
        f"- OK rows: {summary['ok_rows']}",
        f"- Error rows: {summary['error_rows']}",
        f"- Parent drawing count: {summary['parent_drawing_count']}",
        f"- v1 edge count min: {summary['v1_edge_count_min']}",
        f"- v1 edge count avg: {summary['v1_edge_count_avg']}",
        f"- v1 edge count max: {summary['v1_edge_count_max']}",
        f"- v1 net count min: {summary['v1_net_count_min']}",
        f"- v1 net count avg: {summary['v1_net_count_avg']}",
        f"- v1 net count max: {summary['v1_net_count_max']}",
        f"- Total intersections: {summary['intersection_count_total']}",
        f"- No-edge rows: {summary['no_edge_rows']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in summary["status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Quality Flag Counts", ""])
    for flag, count in summary["quality_flag_counts"].items():
        lines.append(f"- {flag}: {count}")
    lines.extend(["", "## Phase Counts", ""])
    for phase, count in summary["by_phase"].items():
        lines.append(f"- {phase}: {count}")
    lines.extend(["", "## Highest Intersection Panels", ""])
    top_intersections = sorted(
        [row for row in rows if row.get("status") != "error"],
        key=lambda row: int(row.get("intersection_count", 0) or 0),
        reverse=True,
    )[:20]
    for row in top_intersections:
        lines.append(
            "- "
            f"{row['panel_id']}: "
            f"edges={row['v1_edge_count']}, "
            f"nets={row['v1_net_count']}, "
            f"intersections={row['intersection_count']}, "
            f"flags={row['quality_flags'] or 'none'}"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


DEFAULT_FIELDNAMES = [
    "panel_id",
    "parent_drawing_key",
    "split",
    "phase",
    "batch",
    "panel_index",
    "panel_count",
    "split_method",
    "panel_png_path",
    "panel_bbox_cad",
    "parent_normalized_json_path",
    "parent_topology_v0_json_path",
    "topology_v1_panel_json_path",
    "status",
    "error",
    "panel_entity_count",
    "base_segment_count",
    "split_segment_count",
    "intersection_count",
    "split_event_count",
    "split_short_segments",
    "v1_node_count",
    "v1_edge_count",
    "v1_net_count",
    "v1_isolated_edge_ratio",
    "v1_largest_net_edge_ratio",
    "effective_endpoint_tolerance",
    "quality_flags",
]


if __name__ == "__main__":
    main()
