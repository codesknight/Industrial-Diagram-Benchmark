"""Build panel-level Topology Graph v1 pilot from manual multi-panel splits."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from build_topology_v1_pilot import (
    ROOT,
    bbox_from_points,
    detect_split_points,
    effective_endpoint_tolerance,
    graph_from_segments,
    iter_base_segments,
    split_segments,
)


INDEX_DIR = ROOT / "data_index"
DEFAULT_PANEL_MANIFEST = INDEX_DIR / "topology_multipanel_manual_panel_usable.csv"
DEFAULT_TOPOLOGY_MANIFEST = INDEX_DIR / "topology_graph_manifest.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "topology_panel_v1_pilot"

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
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_bbox(value: str) -> Optional[BBox]:
    parts = str(value).split(",")
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


def png_to_cad_bbox(png_bbox: BBox, drawing_bbox: BBox, png_width: int, png_height: int) -> BBox:
    full_width = drawing_bbox[2] - drawing_bbox[0]
    full_height = drawing_bbox[3] - drawing_bbox[1]
    left, top, right, bottom = png_bbox
    cad_min_x = drawing_bbox[0] + (left / png_width) * full_width
    cad_max_x = drawing_bbox[0] + (right / png_width) * full_width
    cad_max_y = drawing_bbox[3] - (top / png_height) * full_height
    cad_min_y = drawing_bbox[3] - (bottom / png_height) * full_height
    return cad_min_x, cad_min_y, cad_max_x, cad_max_y


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
    return output_dir / Path(panel_id.replace("\\", "/") + ".topology.v1_panel_pilot.json")


def process_panel(
    panel: Dict[str, str],
    topology_by_parent: Dict[str, Dict[str, str]],
    args: argparse.Namespace,
) -> Dict[str, object]:
    parent_key = panel["parent_drawing_key"]
    topology_row = topology_by_parent.get(parent_key)
    if not topology_row:
        raise SystemExit(f"Missing topology row for parent drawing: {parent_key}")

    normalized_path = ROOT / topology_row["normalized_json_path"]
    with normalized_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    stats = payload.get("stats", {})
    drawing_bbox = stats.get("drawing_bbox") if isinstance(stats, dict) else None
    if not isinstance(drawing_bbox, list) or len(drawing_bbox) < 4:
        raise SystemExit(f"Missing drawing bbox in normalized JSON: {normalized_path}")
    full_bbox = tuple(float(value) for value in drawing_bbox[:4])  # type: ignore[assignment]
    panel_png_bbox = parse_bbox(panel["panel_bbox_png"])
    if panel_png_bbox is None:
        raise SystemExit(f"Invalid panel bbox: {panel['panel_id']}")
    panel_cad_bbox = png_to_cad_bbox(
        panel_png_bbox,
        full_bbox,  # type: ignore[arg-type]
        int(panel["parent_png_width"]),
        int(panel["parent_png_height"]),
    )

    raw_entities = payload.get("entities", [])
    entities = raw_entities if isinstance(raw_entities, list) else []
    panel_entities = [
        entity for entity in entities
        if isinstance(entity, dict) and center_in_bbox(entity, panel_cad_bbox)
    ]
    panel_payload = {
        **payload,
        "drawing_key": panel["panel_id"],
        "source": {
            **payload.get("source", {}),
            "parent_drawing_key": parent_key,
            "panel_png_path": panel.get("panel_png_path", ""),
        },
        "stats": {
            **stats,
            "entity_count": len(panel_entities),
            "drawing_bbox": list(panel_cad_bbox),
            "parent_drawing_bbox": drawing_bbox,
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

    return {
        "panel_id": panel["panel_id"],
        "parent_drawing_key": parent_key,
        "split": panel.get("split", ""),
        "phase": panel.get("phase", ""),
        "panel_index": panel.get("panel_index", ""),
        "panel_count": panel.get("panel_count", ""),
        "panel_png_path": panel.get("panel_png_path", ""),
        "panel_bbox_png": panel.get("panel_bbox_png", ""),
        "panel_bbox_cad": fmt_bbox(panel_cad_bbox),
        "panel_entity_count": len(panel_entities),
        "base_segment_count": result["base_segment_count"],
        "split_segment_count": result["split_segment_count"],
        "intersection_count": result["intersection_count"],
        "split_event_count": result["split_event_count"],
        "v1_node_count": result["v1_node_count"],
        "v1_edge_count": result["v1_edge_count"],
        "v1_net_count": result["v1_net_count"],
        "v1_isolated_edge_ratio": result["v1_isolated_edge_ratio"],
        "v1_largest_net_edge_ratio": result["v1_largest_net_edge_ratio"],
        "effective_endpoint_tolerance": result["effective_endpoint_tolerance"],
        "topology_v1_panel_json_path": result["topology_v1_json_path"],
        "parent_topology_v0_json_path": topology_row.get("topology_json_path", ""),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-manifest", type=Path, default=DEFAULT_PANEL_MANIFEST)
    parser.add_argument("--topology-manifest", type=Path, default=DEFAULT_TOPOLOGY_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--endpoint-tolerance", type=float, default=1.0)
    parser.add_argument("--endpoint-tolerance-ratio", type=float, default=0.0005)
    parser.add_argument("--min-segment-length", type=float, default=0.001)
    parser.add_argument("--intersection-epsilon", type=float, default=1e-9)
    parser.add_argument("--precision", type=int, default=4)
    parser.add_argument("--max-segments", type=int, default=300000)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    panel_rows = load_csv(args.panel_manifest)
    if args.limit:
        panel_rows = panel_rows[: args.limit]
    topology_rows = load_csv(args.topology_manifest)
    topology_by_parent = {row["drawing_key"]: row for row in topology_rows}

    manifest_rows = [process_panel(row, topology_by_parent, args) for row in panel_rows]
    write_csv(INDEX_DIR / "topology_panel_v1_pilot_manifest.csv", manifest_rows)
    write_summary(manifest_rows, args)

    print(f"Panel v1 pilot rows: {len(manifest_rows)}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/topology_panel_v1_pilot_manifest.csv")
    print(f"Wrote local graph JSON under: {args.output_dir.resolve().relative_to(ROOT).as_posix()}")


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    edge_counts = [int(row["v1_edge_count"]) for row in rows]
    net_counts = [int(row["v1_net_count"]) for row in rows]
    intersection_counts = [int(row["intersection_count"]) for row in rows]
    no_edge_rows = [row for row in rows if int(row["v1_edge_count"]) == 0]
    summary = {
        "panel_rows": len(rows),
        "parent_drawing_count": len({row["parent_drawing_key"] for row in rows}),
        "by_split": dict(Counter(str(row["split"]) for row in rows)),
        "v1_edge_count_min": min(edge_counts) if edge_counts else 0,
        "v1_edge_count_avg": round(sum(edge_counts) / len(edge_counts), 2) if edge_counts else 0,
        "v1_edge_count_max": max(edge_counts) if edge_counts else 0,
        "v1_net_count_min": min(net_counts) if net_counts else 0,
        "v1_net_count_avg": round(sum(net_counts) / len(net_counts), 2) if net_counts else 0,
        "v1_net_count_max": max(net_counts) if net_counts else 0,
        "intersection_count_total": sum(intersection_counts),
        "intersection_count_avg": round(sum(intersection_counts) / len(intersection_counts), 2) if intersection_counts else 0,
        "no_edge_rows": len(no_edge_rows),
        "params": {
            "endpoint_merge_tolerance": args.endpoint_tolerance,
            "endpoint_tolerance_ratio": args.endpoint_tolerance_ratio,
            "min_segment_length": args.min_segment_length,
            "intersection_epsilon": args.intersection_epsilon,
            "max_segments": args.max_segments,
        },
    }
    (INDEX_DIR / "topology_panel_v1_pilot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Topology Panel v1 Pilot Report",
        "",
        "This report summarizes panel-level v1 topology graphs built from manual multi-panel splits.",
        "",
        "## Summary",
        "",
        f"- Panel rows: {summary['panel_rows']}",
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
        "## Split Counts",
        "",
    ]
    for split, count in summary["by_split"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Per Panel", ""])
    for row in rows:
        lines.append(
            "- "
            f"{row['panel_id']}: "
            f"edges={row['v1_edge_count']}, "
            f"nets={row['v1_net_count']}, "
            f"intersections={row['intersection_count']}"
        )
    (INDEX_DIR / "topology_panel_v1_pilot_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
