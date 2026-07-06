"""Build Topology Graph v1 pilot with line-intersection splitting.

This pilot targets manually reviewed `needs_intersection_split` samples. It
keeps v0 endpoint clustering, then adds interior line-line intersections as
split points before graph construction.
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
DEFAULT_MANIFEST = INDEX_DIR / "topology_v1_pilot_candidates.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "topology_graph_v1_pilot"

Point = Tuple[float, float]
BBox = Tuple[float, float, float, float]


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
    return output_dir / Path(drawing_key.replace("\\", "/") + ".topology.v1_pilot.json")


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


def quantize(point: Point, tolerance: float) -> Tuple[int, int]:
    return (math.floor(point[0] / tolerance + 0.5), math.floor(point[1] / tolerance + 0.5))


def iter_base_segments(entities: List[Dict[str, object]], min_length: float) -> Iterator[Dict[str, object]]:
    segment_index = 0
    for entity in entities:
        kind = str(entity.get("type", "")).upper()
        geometry = entity.get("geometry", {})
        if not isinstance(geometry, dict):
            continue

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
            raw_segments.extend(zip(clean_points, clean_points[1:]))
            if geometry.get("closed") and len(clean_points) > 2:
                raw_segments.append((clean_points[-1], clean_points[0]))

        for start, end in raw_segments:
            length = segment_length(start, end)
            if length < min_length:
                continue
            yield {
                "base_segment_id": f"bs{segment_index}",
                "entity_id": str(entity.get("id", "")),
                "entity_type": kind,
                "layer": str(entity.get("layer", "")),
                "start": start,
                "end": end,
                "length": length,
            }
            segment_index += 1


def parameter_on_segment(point: Point, start: Point, end: Point) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    denom = dx * dx + dy * dy
    if denom <= 0:
        return 0.0
    return ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / denom


def interpolate(start: Point, end: Point, t: float) -> Point:
    return (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)


def bbox_of_segment(segment: Dict[str, object]) -> BBox:
    start = segment["start"]  # type: ignore[assignment]
    end = segment["end"]  # type: ignore[assignment]
    return (
        min(start[0], end[0]),  # type: ignore[index]
        min(start[1], end[1]),  # type: ignore[index]
        max(start[0], end[0]),  # type: ignore[index]
        max(start[1], end[1]),  # type: ignore[index]
    )


def bbox_overlap(left: BBox, right: BBox, eps: float) -> bool:
    return not (
        left[2] < right[0] - eps
        or right[2] < left[0] - eps
        or left[3] < right[1] - eps
        or right[3] < left[1] - eps
    )


def cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


def segment_intersection(
    a0: Point,
    a1: Point,
    b0: Point,
    b1: Point,
    eps: float,
) -> Optional[Tuple[Point, float, float]]:
    rx = a1[0] - a0[0]
    ry = a1[1] - a0[1]
    sx = b1[0] - b0[0]
    sy = b1[1] - b0[1]
    qp_x = b0[0] - a0[0]
    qp_y = b0[1] - a0[1]
    denom = cross(rx, ry, sx, sy)

    if abs(denom) <= eps:
        return None

    t = cross(qp_x, qp_y, sx, sy) / denom
    u = cross(qp_x, qp_y, rx, ry) / denom
    if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
        t = min(max(t, 0.0), 1.0)
        u = min(max(u, 0.0), 1.0)
        return interpolate(a0, a1, t), t, u
    return None


def build_spatial_index(
    segments: List[Dict[str, object]],
    cell_size: float,
) -> Dict[Tuple[int, int], List[int]]:
    cells: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for index, segment in enumerate(segments):
        box = bbox_of_segment(segment)
        min_x = math.floor(box[0] / cell_size)
        max_x = math.floor(box[2] / cell_size)
        min_y = math.floor(box[1] / cell_size)
        max_y = math.floor(box[3] / cell_size)
        for gx in range(min_x, max_x + 1):
            for gy in range(min_y, max_y + 1):
                cells[(gx, gy)].append(index)
    return cells


def detect_split_points(
    segments: List[Dict[str, object]],
    tolerance: float,
    intersection_epsilon: float,
) -> Tuple[Dict[int, List[float]], int, int]:
    split_params: Dict[int, List[float]] = {index: [0.0, 1.0] for index in range(len(segments))}
    cell_size = max(tolerance * 10, 1.0)
    cells = build_spatial_index(segments, cell_size)
    checked: set[Tuple[int, int]] = set()
    intersection_count = 0
    split_event_count = 0
    boxes = [bbox_of_segment(segment) for segment in segments]

    for indexes in cells.values():
        if len(indexes) < 2:
            continue
        for local_i, left_index in enumerate(indexes):
            for right_index in indexes[local_i + 1:]:
                pair = (left_index, right_index) if left_index < right_index else (right_index, left_index)
                if pair in checked:
                    continue
                checked.add(pair)
                if not bbox_overlap(boxes[left_index], boxes[right_index], tolerance):
                    continue

                left = segments[left_index]
                right = segments[right_index]
                hit = segment_intersection(
                    left["start"],  # type: ignore[arg-type]
                    left["end"],  # type: ignore[arg-type]
                    right["start"],  # type: ignore[arg-type]
                    right["end"],  # type: ignore[arg-type]
                    intersection_epsilon,
                )
                if not hit:
                    continue
                _, left_t, right_t = hit
                added = False
                if tolerance_param(left_t):
                    split_params[left_index].append(left_t)
                    split_event_count += 1
                    added = True
                if tolerance_param(right_t):
                    split_params[right_index].append(right_t)
                    split_event_count += 1
                    added = True
                if added:
                    intersection_count += 1

    return split_params, intersection_count, split_event_count


def tolerance_param(value: float) -> bool:
    return 1e-7 < value < 1 - 1e-7


def unique_sorted_params(values: List[float], tolerance: float) -> List[float]:
    values = sorted(min(max(value, 0.0), 1.0) for value in values)
    out: List[float] = []
    for value in values:
        if not out or abs(value - out[-1]) > tolerance:
            out.append(value)
    if out[0] != 0.0:
        out.insert(0, 0.0)
    if out[-1] != 1.0:
        out.append(1.0)
    return out


def split_segments(
    segments: List[Dict[str, object]],
    split_params: Dict[int, List[float]],
    min_segment_length: float,
) -> Tuple[List[Dict[str, object]], int]:
    out: List[Dict[str, object]] = []
    skipped_short = 0
    for index, segment in enumerate(segments):
        params = unique_sorted_params(split_params[index], 1e-7)
        start = segment["start"]  # type: ignore[assignment]
        end = segment["end"]  # type: ignore[assignment]
        for left_t, right_t in zip(params, params[1:]):
            left = interpolate(start, end, left_t)  # type: ignore[arg-type]
            right = interpolate(start, end, right_t)  # type: ignore[arg-type]
            length = segment_length(left, right)
            if length < min_segment_length:
                skipped_short += 1
                continue
            out.append(
                {
                    "segment_id": f"s{len(out)}",
                    "base_segment_id": segment["base_segment_id"],
                    "entity_id": segment["entity_id"],
                    "entity_type": segment["entity_type"],
                    "layer": segment["layer"],
                    "start": left,
                    "end": right,
                    "length": length,
                    "split_from_t": round(left_t, 8),
                    "split_to_t": round(right_t, 8),
                }
            )
    return out, skipped_short


def graph_from_segments(
    row: Dict[str, str],
    payload: Dict[str, object],
    base_segments: List[Dict[str, object]],
    segments: List[Dict[str, object]],
    output_path: Path,
    tolerance: float,
    tolerance_ratio: float,
    min_segment_length: float,
    precision: int,
    max_segments: int,
    intersection_count: int,
    split_event_count: int,
    split_short_segments: int,
) -> Dict[str, object]:
    node_lookup: Dict[Tuple[int, int], int] = {}
    node_sums: List[List[float]] = []
    degrees: List[int] = []
    edges: List[Dict[str, object]] = []
    layer_counts: Counter[str] = Counter()
    entity_type_counts: Counter[str] = Counter()
    segment_points: List[Point] = []
    active_tolerance = effective_endpoint_tolerance(payload, tolerance, tolerance_ratio, min_segment_length)
    skipped_same_node_segments = 0

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

    for segment in segments[:max_segments]:
        start = segment["start"]  # type: ignore[assignment]
        end = segment["end"]  # type: ignore[assignment]
        if quantize(start, active_tolerance) == quantize(end, active_tolerance):  # type: ignore[arg-type]
            skipped_same_node_segments += 1
            continue
        source = add_node(start)  # type: ignore[arg-type]
        target = add_node(end)  # type: ignore[arg-type]
        degrees[source] += 1
        degrees[target] += 1
        layer = str(segment["layer"])
        entity_type = str(segment["entity_type"])
        layer_counts[layer] += 1
        entity_type_counts[entity_type] += 1
        segment_points.extend([start, end])  # type: ignore[arg-type]
        edges.append(
            {
                "id": f"e{len(edges)}",
                "source": f"n{source}",
                "target": f"n{target}",
                "source_index": source,
                "target_index": target,
                "segment_id": segment["segment_id"],
                "base_segment_id": segment["base_segment_id"],
                "entity_id": segment["entity_id"],
                "entity_type": entity_type,
                "layer": layer,
                "points": [round_point(start, precision), round_point(end, precision)],  # type: ignore[arg-type]
                "length": round(float(segment["length"]), precision),
            }
        )

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
        node_payload.append({"id": f"n{node_index}", "point": round_point(point, precision), "degree": degrees[node_index]})

    nets = []
    for net_index, root in enumerate(sorted(component_nodes)):
        net_nodes = component_nodes[root]
        net_edges = component_edges.get(root, [])
        bbox = bbox_from_points([node_points[index] for index in net_nodes])
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

    nonempty_nets = [int(net["edge_count"]) for net in nets if int(net["edge_count"]) > 0]
    isolated_edge_count = sum(1 for count in nonempty_nets if count == 1)
    largest_net_edges = max(nonempty_nets) if nonempty_nets else 0
    isolated_ratio = round(isolated_edge_count / len(edges), 4) if edges else 0.0
    largest_ratio = round(largest_net_edges / len(edges), 4) if edges else 0.0
    graph_bbox = bbox_from_points(segment_points)
    status = "ok" if len(segments) <= max_segments else "truncated_max_segments"

    stats = {
        "base_segment_count": len(base_segments),
        "split_segment_count": len(segments),
        "intersection_count": intersection_count,
        "split_event_count": split_event_count,
        "split_short_segments": split_short_segments,
        "node_count": len(node_payload),
        "edge_count": len(edges),
        "net_count": len(nonempty_nets),
        "largest_net_edges": largest_net_edges,
        "isolated_edge_count": isolated_edge_count,
        "isolated_edge_ratio": isolated_ratio,
        "largest_net_edge_ratio": largest_ratio,
        "skipped_same_node_segments": skipped_same_node_segments,
        "graph_bbox": [round(value, precision) for value in graph_bbox] if graph_bbox else None,
        "edge_type_counts": dict(entity_type_counts),
        "top_layers": dict(layer_counts.most_common(20)),
        "effective_endpoint_tolerance": round(active_tolerance, precision),
    }
    graph_payload = {
        "schema": "industrial_diagram.topology_graph.v1_pilot",
        "drawing_key": row["drawing_key"],
        "phase": row.get("phase", ""),
        "split": row.get("split", ""),
        "source": {
            "normalized_json_path": row["normalized_json_path"],
            "topology_v0_json_path": row.get("topology_json_path", ""),
        },
        "params": {
            "endpoint_merge_tolerance": tolerance,
            "endpoint_tolerance_ratio": tolerance_ratio,
            "min_segment_length": min_segment_length,
            "precision": precision,
            "max_segments": max_segments,
            "intersection_splitting": True,
        },
        "status": status,
        "stats": stats,
        "nodes": node_payload,
        "edges": edges,
        "nets": nets,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph_payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    return {
        "drawing_key": row["drawing_key"],
        "split": row.get("split", ""),
        "phase": row.get("phase", ""),
        "normalized_json_path": row["normalized_json_path"],
        "topology_v0_json_path": row.get("topology_json_path", ""),
        "topology_v1_json_path": output_path.relative_to(ROOT).as_posix(),
        "status": status,
        "v0_node_count": row.get("node_count", ""),
        "v0_edge_count": row.get("edge_count", ""),
        "v0_net_count": row.get("net_count", ""),
        "v0_isolated_edge_ratio": row.get("isolated_edge_ratio", ""),
        "v0_largest_net_edge_ratio": row.get("largest_net_edge_ratio", ""),
        "v1_node_count": len(node_payload),
        "v1_edge_count": len(edges),
        "v1_net_count": len(nonempty_nets),
        "v1_isolated_edge_ratio": isolated_ratio,
        "v1_largest_net_edge_ratio": largest_ratio,
        "base_segment_count": len(base_segments),
        "split_segment_count": len(segments),
        "intersection_count": intersection_count,
        "split_event_count": split_event_count,
        "split_short_segments": split_short_segments,
        "effective_endpoint_tolerance": round(active_tolerance, precision),
        "review_label": row.get("topology_review_label", ""),
    }


def process_row(row: Dict[str, str], args: argparse.Namespace) -> Dict[str, object]:
    normalized_path = ROOT / row["normalized_json_path"]
    with normalized_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    entities = payload.get("entities", [])
    if not isinstance(entities, list):
        entities = []

    active_tolerance = effective_endpoint_tolerance(
        payload,
        args.endpoint_tolerance,
        args.endpoint_tolerance_ratio,
        args.min_segment_length,
    )
    base_segments = list(iter_base_segments(entities, args.min_segment_length))
    split_params, intersection_count, split_event_count = detect_split_points(
        base_segments,
        tolerance=active_tolerance,
        intersection_epsilon=args.intersection_epsilon,
    )
    split, split_short_segments = split_segments(base_segments, split_params, args.min_segment_length)
    output_path = safe_output_path(row["drawing_key"], args.output_dir.resolve())
    return graph_from_segments(
        row=row,
        payload=payload,
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


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    improved_isolated = 0
    improved_nets = 0
    total_intersections = 0
    total_split_events = 0
    for row in rows:
        total_intersections += int(row["intersection_count"])
        total_split_events += int(row["split_event_count"])
        try:
            if float(row["v1_isolated_edge_ratio"]) < float(row["v0_isolated_edge_ratio"]):
                improved_isolated += 1
            if int(row["v1_net_count"]) < int(row["v0_net_count"]):
                improved_nets += 1
        except (TypeError, ValueError):
            pass

    summary = {
        "pilot_rows": len(rows),
        "total_intersections": total_intersections,
        "total_split_events": total_split_events,
        "improved_isolated_ratio_rows": improved_isolated,
        "reduced_net_count_rows": improved_nets,
        "v0_edge_total": sum(int(row["v0_edge_count"]) for row in rows),
        "v1_edge_total": sum(int(row["v1_edge_count"]) for row in rows),
        "v0_net_total": sum(int(row["v0_net_count"]) for row in rows),
        "v1_net_total": sum(int(row["v1_net_count"]) for row in rows),
        "params": {
            "endpoint_merge_tolerance": args.endpoint_tolerance,
            "endpoint_tolerance_ratio": args.endpoint_tolerance_ratio,
            "min_segment_length": args.min_segment_length,
            "intersection_epsilon": args.intersection_epsilon,
            "max_segments": args.max_segments,
        },
    }
    (INDEX_DIR / "topology_v1_pilot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary, rows)


def write_report(summary: Dict[str, object], rows: List[Dict[str, object]]) -> None:
    lines = [
        "# Topology Graph v1 Pilot Report",
        "",
        "This report compares v0 endpoint topology with v1 pilot intersection splitting.",
        "",
        "## Summary",
        "",
        f"- Pilot rows: {summary['pilot_rows']}",
        f"- Total intersections: {summary['total_intersections']}",
        f"- Total split events: {summary['total_split_events']}",
        f"- Rows with lower isolated ratio: {summary['improved_isolated_ratio_rows']}",
        f"- Rows with lower net count: {summary['reduced_net_count_rows']}",
        f"- v0 edge total: {summary['v0_edge_total']}",
        f"- v1 edge total: {summary['v1_edge_total']}",
        f"- v0 net total: {summary['v0_net_total']}",
        f"- v1 net total: {summary['v1_net_total']}",
        "",
        "## Per Drawing",
        "",
    ]
    for row in rows:
        lines.append(
            "- "
            f"{row['drawing_key']}: "
            f"edges {row['v0_edge_count']} -> {row['v1_edge_count']}, "
            f"nets {row['v0_net_count']} -> {row['v1_net_count']}, "
            f"isolated {row['v0_isolated_edge_ratio']} -> {row['v1_isolated_edge_ratio']}, "
            f"intersections {row['intersection_count']}"
        )
    lines.extend(["", "## Parameters", ""])
    for key, value in summary["params"].items():
        lines.append(f"- {key}: {value}")
    (INDEX_DIR / "topology_v1_pilot_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
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
    rows = load_csv(args.manifest)
    if args.limit:
        rows = rows[: args.limit]
    manifest_rows = [process_row(row, args) for row in rows]

    fieldnames = [
        "drawing_key",
        "split",
        "phase",
        "normalized_json_path",
        "topology_v0_json_path",
        "topology_v1_json_path",
        "status",
        "v0_node_count",
        "v0_edge_count",
        "v0_net_count",
        "v0_isolated_edge_ratio",
        "v0_largest_net_edge_ratio",
        "v1_node_count",
        "v1_edge_count",
        "v1_net_count",
        "v1_isolated_edge_ratio",
        "v1_largest_net_edge_ratio",
        "base_segment_count",
        "split_segment_count",
        "intersection_count",
        "split_event_count",
        "split_short_segments",
        "effective_endpoint_tolerance",
        "review_label",
    ]
    write_csv(INDEX_DIR / "topology_v1_pilot_manifest.csv", manifest_rows, fieldnames)
    write_summary(manifest_rows, args)

    print(f"Topology v1 pilot rows: {len(manifest_rows)}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/topology_v1_pilot_manifest.csv")
    print(f"Wrote local graph JSON under: {args.output_dir.resolve().relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
