"""Build Topology Graph v0 from normalized geometry JSON files.

Topology v0 is intentionally conservative: it builds a graph from explicit
wire-like endpoints only. It does not split lines at geometric intersections.
That keeps the first graph layer reproducible and cheap enough for the full
dataset while leaving room for a stricter v1 graph builder later.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "normalized_geometry_manifest.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "topology_graph"

Point = Tuple[float, float]
BBox = Tuple[float, float, float, float]
Segment = Dict[str, object]


class UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, value: int) -> int:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_output_path(drawing_key: str, output_dir: Path) -> Path:
    rel = Path(drawing_key.replace("\\", "/") + ".topology.v0.json")
    return output_dir / rel


def finite_point(value: object) -> Optional[Point]:
    if not isinstance(value, Sequence) or len(value) < 2:
        return None
    try:
        x = float(value[0])
        y = float(value[1])
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return x, y


def round_point(point: Point, precision: int) -> List[float]:
    return [round(point[0], precision), round(point[1], precision)]


def segment_length(start: Point, end: Point) -> float:
    return math.hypot(end[0] - start[0], end[1] - start[1])


def bbox_from_points(points: Sequence[Point]) -> Optional[BBox]:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def bbox_diagonal(box: object) -> Optional[float]:
    if not isinstance(box, Sequence) or len(box) < 4:
        return None
    try:
        x0, y0, x1, y1 = [float(value) for value in box[:4]]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (x0, y0, x1, y1)):
        return None
    return math.hypot(x1 - x0, y1 - y0)


def effective_endpoint_tolerance(
    payload: Dict[str, object],
    max_tolerance: float,
    tolerance_ratio: float,
    min_segment_length: float,
) -> float:
    stats = payload.get("stats", {})
    drawing_bbox = stats.get("drawing_bbox") if isinstance(stats, dict) else None
    diagonal = bbox_diagonal(drawing_bbox)
    if not diagonal or diagonal <= 0:
        return max_tolerance
    scaled = max(diagonal * tolerance_ratio, min_segment_length * 2)
    return max(min(scaled, max_tolerance), min_segment_length)


def round_bbox(box: Optional[BBox], precision: int) -> str:
    if not box:
        return ""
    return ",".join(str(round(value, precision)) for value in box)


def iter_segments(entities: List[Dict[str, object]], min_length: float) -> Iterator[Segment]:
    skipped_short = 0
    segment_index = 0

    for entity in entities:
        kind = str(entity.get("type", "")).upper()
        geometry = entity.get("geometry", {})
        if not isinstance(geometry, dict):
            continue

        entity_id = str(entity.get("id", ""))
        layer = str(entity.get("layer", ""))
        raw_segments: List[Tuple[Point, Point]] = []

        if kind == "LINE":
            start = finite_point(geometry.get("start"))
            end = finite_point(geometry.get("end"))
            if start and end:
                raw_segments.append((start, end))
        elif kind == "LWPOLYLINE":
            raw_points = geometry.get("points", [])
            points = [finite_point(point) for point in raw_points] if isinstance(raw_points, list) else []
            clean_points = [point for point in points if point]
            for left, right in zip(clean_points, clean_points[1:]):
                raw_segments.append((left, right))
            if geometry.get("closed") and len(clean_points) > 2:
                raw_segments.append((clean_points[-1], clean_points[0]))

        for start, end in raw_segments:
            length = segment_length(start, end)
            if length < min_length:
                skipped_short += 1
                continue
            yield {
                "segment_id": f"s{segment_index}",
                "entity_id": entity_id,
                "entity_type": kind,
                "layer": layer,
                "start": start,
                "end": end,
                "length": length,
            }
            segment_index += 1

    if skipped_short:
        yield {"_skipped_short_segments": skipped_short}


def quantize(point: Point, tolerance: float) -> Tuple[int, int]:
    return (math.floor(point[0] / tolerance + 0.5), math.floor(point[1] / tolerance + 0.5))


def build_graph(
    payload: Dict[str, object],
    row: Dict[str, str],
    output_path: Path,
    tolerance: float,
    tolerance_ratio: float,
    min_segment_length: float,
    precision: int,
    max_segments: int,
) -> Dict[str, object]:
    raw_entities = payload.get("entities", [])
    entities = raw_entities if isinstance(raw_entities, list) else []

    node_lookup: Dict[Tuple[int, int], int] = {}
    node_sums: List[List[float]] = []
    degrees: List[int] = []
    edges: List[Dict[str, object]] = []
    skipped_short_segments = 0
    skipped_same_node_segments = 0
    layer_counts: Counter[str] = Counter()
    entity_type_counts: Counter[str] = Counter()
    segment_points: List[Point] = []
    active_tolerance = effective_endpoint_tolerance(
        payload=payload,
        max_tolerance=tolerance,
        tolerance_ratio=tolerance_ratio,
        min_segment_length=min_segment_length,
    )

    def add_node(point: Point) -> int:
        key = quantize(point, active_tolerance)
        node_index = node_lookup.get(key)
        if node_index is None:
            node_index = len(node_sums)
            node_lookup[key] = node_index
            node_sums.append([point[0], point[1], 1.0])
            degrees.append(0)
        else:
            node_sums[node_index][0] += point[0]
            node_sums[node_index][1] += point[1]
            node_sums[node_index][2] += 1.0
        return node_index

    for segment in iter_segments(entities, min_segment_length):
        if "_skipped_short_segments" in segment:
            skipped_short_segments += int(segment["_skipped_short_segments"])
            continue
        if len(edges) >= max_segments:
            break

        start = segment["start"]  # type: ignore[assignment]
        end = segment["end"]  # type: ignore[assignment]
        if quantize(start, active_tolerance) == quantize(end, active_tolerance):  # type: ignore[arg-type]
            skipped_same_node_segments += 1
            continue
        source = add_node(start)  # type: ignore[arg-type]
        target = add_node(end)  # type: ignore[arg-type]

        edge_id = f"e{len(edges)}"
        degrees[source] += 1
        degrees[target] += 1
        layer = str(segment["layer"])
        entity_type = str(segment["entity_type"])
        layer_counts[layer] += 1
        entity_type_counts[entity_type] += 1
        segment_points.extend([start, end])  # type: ignore[arg-type]
        edges.append(
            {
                "id": edge_id,
                "source": f"n{source}",
                "target": f"n{target}",
                "source_index": source,
                "target_index": target,
                "segment_id": segment["segment_id"],
                "entity_id": segment["entity_id"],
                "entity_type": entity_type,
                "layer": layer,
                "points": [round_point(start, precision), round_point(end, precision)],  # type: ignore[arg-type]
                "length": round(float(segment["length"]), precision),
            }
        )

    status = "ok"
    total_candidate_segments = len(edges) + skipped_same_node_segments + skipped_short_segments
    if len(edges) >= max_segments:
        status = "truncated_max_segments"

    uf = UnionFind(len(node_sums))
    for edge in edges:
        uf.union(int(edge["source_index"]), int(edge["target_index"]))

    component_nodes: Dict[int, List[int]] = defaultdict(list)
    component_edges: Dict[int, List[int]] = defaultdict(list)
    for node_index in range(len(node_sums)):
        component_nodes[uf.find(node_index)].append(node_index)
    for edge_index, edge in enumerate(edges):
        component_edges[uf.find(int(edge["source_index"]))].append(edge_index)

    node_payload = []
    node_points: List[Point] = []
    for node_index, sums in enumerate(node_sums):
        count = max(sums[2], 1.0)
        point = (sums[0] / count, sums[1] / count)
        node_points.append(point)
        node_payload.append(
            {
                "id": f"n{node_index}",
                "point": round_point(point, precision),
                "degree": degrees[node_index],
            }
        )

    nets = []
    for net_index, root in enumerate(sorted(component_nodes)):
        net_nodes = component_nodes[root]
        net_edges = component_edges.get(root, [])
        net_points = [node_points[index] for index in net_nodes]
        bbox = bbox_from_points(net_points)
        nets.append(
            {
                "id": f"net{net_index}",
                "node_count": len(net_nodes),
                "edge_count": len(net_edges),
                "bbox": [round(value, precision) for value in bbox] if bbox else None,
            }
        )

    for edge in edges:
        edge.pop("source_index", None)
        edge.pop("target_index", None)

    edge_counts = [int(net["edge_count"]) for net in nets]
    nonempty_nets = [count for count in edge_counts if count > 0]
    isolated_edge_count = sum(1 for count in nonempty_nets if count == 1)
    largest_net_edges = max(nonempty_nets) if nonempty_nets else 0
    graph_bbox = bbox_from_points(segment_points)
    isolated_ratio = round(isolated_edge_count / len(edges), 4) if edges else 0.0
    largest_net_ratio = round(largest_net_edges / len(edges), 4) if edges else 0.0

    flags = quality_flags(
        status=status,
        edge_count=len(edges),
        net_count=len(nonempty_nets),
        isolated_ratio=isolated_ratio,
        largest_net_ratio=largest_net_ratio,
    )

    stats = {
        "node_count": len(node_payload),
        "edge_count": len(edges),
        "candidate_segment_count": total_candidate_segments,
        "net_count": len(nonempty_nets),
        "topology_ready": bool(edges),
        "largest_net_edges": largest_net_edges,
        "isolated_edge_count": isolated_edge_count,
        "isolated_edge_ratio": isolated_ratio,
        "largest_net_edge_ratio": largest_net_ratio,
        "skipped_short_segments": skipped_short_segments,
        "skipped_same_node_segments": skipped_same_node_segments,
        "graph_bbox": [round(value, precision) for value in graph_bbox] if graph_bbox else None,
        "edge_type_counts": dict(entity_type_counts),
        "top_layers": dict(layer_counts.most_common(20)),
        "quality_flags": flags,
        "effective_endpoint_tolerance": round(active_tolerance, precision),
    }

    graph_payload = {
        "schema": "industrial_diagram.topology_graph.v0",
        "drawing_key": row["drawing_key"],
        "phase": row.get("phase", ""),
        "split": row.get("split", ""),
        "source": {
            "normalized_json_path": row["normalized_json_path"],
            "raw_json_path": row.get("raw_json_path", ""),
        },
        "params": {
            "endpoint_merge_tolerance": tolerance,
            "endpoint_tolerance_ratio": tolerance_ratio,
            "effective_endpoint_tolerance": round(active_tolerance, precision),
            "min_segment_length": min_segment_length,
            "precision": precision,
            "max_segments": max_segments,
            "intersection_splitting": False,
        },
        "status": status,
        "stats": stats,
        "nodes": node_payload,
        "edges": edges,
        "nets": nets,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(graph_payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    return {
        "drawing_key": row["drawing_key"],
        "split": row.get("split", ""),
        "phase": row.get("phase", ""),
        "normalized_json_path": row["normalized_json_path"],
        "topology_json_path": output_path.relative_to(ROOT).as_posix(),
        "status": status,
        "node_count": len(node_payload),
        "edge_count": len(edges),
        "candidate_segment_count": total_candidate_segments,
        "net_count": len(nonempty_nets),
        "topology_ready": bool(edges),
        "largest_net_edges": largest_net_edges,
        "isolated_edge_count": isolated_edge_count,
        "isolated_edge_ratio": isolated_ratio,
        "largest_net_edge_ratio": largest_net_ratio,
        "skipped_short_segments": skipped_short_segments,
        "skipped_same_node_segments": skipped_same_node_segments,
        "graph_bbox": round_bbox(graph_bbox, precision),
        "edge_type_count_json": json.dumps(dict(entity_type_counts), ensure_ascii=False, sort_keys=True),
        "effective_endpoint_tolerance": round(active_tolerance, precision),
        "quality_flags": ";".join(flags),
    }


def quality_flags(
    status: str,
    edge_count: int,
    net_count: int,
    isolated_ratio: float,
    largest_net_ratio: float,
) -> List[str]:
    flags = []
    if status != "ok":
        flags.append(status)
    if edge_count == 0:
        flags.append("no_edges")
        flags.append("not_topology_ready")
    if edge_count > 100 and isolated_ratio > 0.8:
        flags.append("high_isolated_ratio")
    if edge_count > 50 and net_count <= 1:
        flags.append("single_large_component")
    if edge_count > 100 and largest_net_ratio > 0.85:
        flags.append("dominant_component")
    return flags


def process_row(
    row: Dict[str, str],
    output_dir: Path,
    tolerance: float,
    tolerance_ratio: float,
    min_segment_length: float,
    precision: int,
    max_segments: int,
) -> Dict[str, object]:
    normalized_path = ROOT / row["normalized_json_path"]
    with normalized_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    output_path = safe_output_path(row["drawing_key"], output_dir)
    return build_graph(
        payload=payload,
        row=row,
        output_path=output_path,
        tolerance=tolerance,
        tolerance_ratio=tolerance_ratio,
        min_segment_length=min_segment_length,
        precision=precision,
        max_segments=max_segments,
    )


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    split_counts = Counter(str(row["split"]) for row in rows)
    phase_counts = Counter(str(row["phase"]) for row in rows)
    status_counts = Counter(str(row["status"]) for row in rows)
    flag_counts: Counter[str] = Counter()
    edge_type_counts: Counter[str] = Counter()
    for row in rows:
        flags = [flag for flag in str(row["quality_flags"]).split(";") if flag]
        flag_counts.update(flags)
        edge_type_counts.update(json.loads(str(row["edge_type_count_json"])))

    edge_counts = [int(row["edge_count"]) for row in rows]
    node_counts = [int(row["node_count"]) for row in rows]
    net_counts = [int(row["net_count"]) for row in rows]
    review_rows = [row for row in rows if str(row["quality_flags"])]
    topology_ready_rows = [row for row in rows if str(row.get("topology_ready", "")).lower() == "true"]

    summary = {
        "topology_rows": len(rows),
        "topology_ready_rows": len(topology_ready_rows),
        "not_topology_ready_rows": len(rows) - len(topology_ready_rows),
        "by_split": dict(split_counts),
        "by_phase": dict(phase_counts),
        "by_status": dict(status_counts),
        "quality_flag_counts": dict(flag_counts),
        "edge_count_min": min(edge_counts) if edge_counts else 0,
        "edge_count_avg": round(sum(edge_counts) / len(edge_counts), 2) if edge_counts else 0,
        "edge_count_max": max(edge_counts) if edge_counts else 0,
        "node_count_min": min(node_counts) if node_counts else 0,
        "node_count_avg": round(sum(node_counts) / len(node_counts), 2) if node_counts else 0,
        "node_count_max": max(node_counts) if node_counts else 0,
        "net_count_min": min(net_counts) if net_counts else 0,
        "net_count_avg": round(sum(net_counts) / len(net_counts), 2) if net_counts else 0,
        "net_count_max": max(net_counts) if net_counts else 0,
        "review_rows": len(review_rows),
        "edge_type_counts": dict(edge_type_counts.most_common()),
        "params": {
            "endpoint_merge_tolerance": args.endpoint_tolerance,
            "endpoint_tolerance_ratio": args.endpoint_tolerance_ratio,
            "min_segment_length": args.min_segment_length,
            "precision": args.precision,
            "max_segments": args.max_segments,
            "intersection_splitting": False,
        },
    }
    (INDEX_DIR / "topology_graph_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    quality_fields = [
        "drawing_key",
        "split",
        "phase",
        "status",
        "edge_count",
        "node_count",
        "net_count",
        "topology_ready",
        "largest_net_edge_ratio",
        "isolated_edge_ratio",
        "quality_flags",
        "topology_json_path",
    ]
    quality_rows = [
        {field: row.get(field, "") for field in quality_fields}
        for row in review_rows
    ]
    write_csv(INDEX_DIR / "topology_quality_review.csv", quality_rows, quality_fields)
    write_report(summary)


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Graph v0 Report",
        "",
        "This report summarizes endpoint-cluster topology graphs built from Normalized Geometry JSON.",
        "",
        "## Summary",
        "",
        f"- Topology rows: {summary['topology_rows']}",
        f"- Topology-ready rows: {summary['topology_ready_rows']}",
        f"- Not topology-ready rows: {summary['not_topology_ready_rows']}",
        f"- Review rows: {summary['review_rows']}",
        f"- Edge count min: {summary['edge_count_min']}",
        f"- Edge count avg: {summary['edge_count_avg']}",
        f"- Edge count max: {summary['edge_count_max']}",
        f"- Node count avg: {summary['node_count_avg']}",
        f"- Net count avg: {summary['net_count_avg']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in summary["by_status"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Quality Flags", ""])
    if summary["quality_flag_counts"]:
        for flag, count in summary["quality_flag_counts"].items():
            lines.append(f"- {flag}: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Top Edge Entity Types", ""])
    for kind, count in list(summary["edge_type_counts"].items())[:10]:
        lines.append(f"- {kind}: {count}")
    lines.extend(["", "## Parameters", ""])
    params = summary["params"]
    for key, value in params.items():
        lines.append(f"- {key}: {value}")

    (INDEX_DIR / "topology_graph_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--endpoint-tolerance", type=float, default=1.0)
    parser.add_argument("--endpoint-tolerance-ratio", type=float, default=0.0005)
    parser.add_argument("--min-segment-length", type=float, default=0.001)
    parser.add_argument("--precision", type=int, default=4)
    parser.add_argument("--max-segments", type=int, default=300000)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    if args.limit:
        rows = rows[: args.limit]

    output_dir = args.output_dir.resolve()
    manifest_rows = [
        process_row(
            row=row,
            output_dir=output_dir,
            tolerance=args.endpoint_tolerance,
            tolerance_ratio=args.endpoint_tolerance_ratio,
            min_segment_length=args.min_segment_length,
            precision=args.precision,
            max_segments=args.max_segments,
        )
        for row in rows
    ]

    fieldnames = [
        "drawing_key",
        "split",
        "phase",
        "normalized_json_path",
        "topology_json_path",
        "status",
        "node_count",
        "edge_count",
        "candidate_segment_count",
        "net_count",
        "topology_ready",
        "largest_net_edges",
        "isolated_edge_count",
        "isolated_edge_ratio",
        "largest_net_edge_ratio",
        "skipped_short_segments",
        "skipped_same_node_segments",
        "graph_bbox",
        "edge_type_count_json",
        "effective_endpoint_tolerance",
        "quality_flags",
    ]
    write_csv(INDEX_DIR / "topology_graph_manifest.csv", manifest_rows, fieldnames)
    write_summary(manifest_rows, args)

    print(f"Topology graphs: {len(manifest_rows)}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/topology_graph_manifest.csv")
    print(f"Wrote local graph JSON under: {output_dir.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
