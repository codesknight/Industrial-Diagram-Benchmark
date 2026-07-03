"""Second-round content quality scan for cleaned samples.

This script performs non-destructive content-level checks:
- raw JSON entity statistics
- CAD coordinate extents
- PNG dimensions
- obvious low-information or malformed samples
- heuristic multi-panel / multi-subfigure candidates

It does not crop images or delete samples. Multi-panel samples are flagged for
future panel-level processing.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import struct
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "clean_dataset_manifest.csv"

Point = Tuple[float, float]
BBox = Tuple[float, float, float, float]


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
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


def write_manifest_splits(rows: List[Dict[str, str]], prefix: str, fieldnames: List[str]) -> None:
    for split in ("train", "val", "test"):
        split_rows = [row for row in rows if row.get("split") == split]
        write_csv(INDEX_DIR / f"{prefix}_{split}.csv", split_rows, fieldnames)


def get_png_size(path: Path) -> Tuple[Optional[int], Optional[int], str]:
    try:
        with path.open("rb") as f:
            header = f.read(24)
        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            return None, None, "not_png"
        width, height = struct.unpack(">II", header[16:24])
        return width, height, ""
    except Exception as exc:  # noqa: BLE001
        return None, None, f"png_error:{exc}"


def finite_xy(value: object) -> Optional[Point]:
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


def bbox_from_points(points: Sequence[Point]) -> Optional[BBox]:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def entity_bbox(entity: Dict[str, object]) -> Optional[BBox]:
    kind = str(entity.get("type", "")).upper()
    points: List[Point] = []

    if kind == "LINE":
        for key in ("start", "end"):
            point = finite_xy(entity.get(key))
            if point:
                points.append(point)
    elif kind == "LWPOLYLINE":
        raw_points = entity.get("points", [])
        if isinstance(raw_points, list):
            for raw_point in raw_points:
                point = finite_xy(raw_point)
                if point:
                    points.append(point)
    elif kind in {"TEXT", "MTEXT"}:
        point = finite_xy(entity.get("position"))
        if point:
            height = entity.get("height", 0) or 0
            text = str(entity.get("content", entity.get("text", "")))
            try:
                h = abs(float(height))
            except (TypeError, ValueError):
                h = 0.0
            width = max(h * max(len(text), 1) * 0.65, h)
            points.extend([point, (point[0] + width, point[1] + h)])
    elif kind == "INSERT":
        point = finite_xy(entity.get("position"))
        if point:
            points.append(point)
    elif kind in {"CIRCLE", "ARC"}:
        center = finite_xy(entity.get("center"))
        if center:
            try:
                radius = abs(float(entity.get("radius", 0) or 0))
            except (TypeError, ValueError):
                radius = 0.0
            points.extend(
                [
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius),
                ]
            )
    elif "points" in entity and isinstance(entity.get("points"), list):
        for raw_point in entity["points"]:  # type: ignore[index]
            point = finite_xy(raw_point)
            if point:
                points.append(point)

    return bbox_from_points(points)


def union_bbox(boxes: Sequence[BBox]) -> Optional[BBox]:
    if not boxes:
        return None
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def bbox_area(box: BBox) -> float:
    return max(box[2] - box[0], 0.0) * max(box[3] - box[1], 0.0)


def center_of(box: BBox) -> Point:
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def quantile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    pos = (len(values) - 1) * q
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    if low == high:
        return values[low]
    return values[low] * (high - pos) + values[high] * (pos - low)


def one_dimensional_clusters(
    values: List[float],
    total_range: float,
    min_gap_ratio: float,
    min_cluster_points: int,
) -> Tuple[int, float]:
    if len(values) < min_cluster_points * 2 or total_range <= 0:
        return 1, 0.0
    values = sorted(values)
    gaps = [(values[i + 1] - values[i], i) for i in range(len(values) - 1)]
    if not gaps:
        return 1, 0.0

    split_points = []
    for gap, index in gaps:
        if gap / total_range < min_gap_ratio:
            continue
        left_count = index + 1
        right_count = len(values) - left_count
        if left_count >= min_cluster_points and right_count >= min_cluster_points:
            split_points.append(index)

    if not split_points:
        return 1, max(gap for gap, _ in gaps) / total_range

    # Count clusters from accepted split points. This is intentionally simple
    # because the result is a review candidate, not a final crop.
    return len(split_points) + 1, max(values[i + 1] - values[i] for i in split_points) / total_range


def scan_json(path: Path, args: argparse.Namespace) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    entities = payload.get("entities", [])
    if not isinstance(entities, list):
        entities = []

    type_counts = Counter(str(entity.get("type", "")).upper() for entity in entities if isinstance(entity, dict))
    boxes = [entity_bbox(entity) for entity in entities if isinstance(entity, dict)]
    boxes = [box for box in boxes if box is not None and bbox_area(box) >= 0]  # type: ignore[list-item]
    full_bbox = union_bbox(boxes)  # type: ignore[arg-type]

    if full_bbox:
        cad_width = full_bbox[2] - full_bbox[0]
        cad_height = full_bbox[3] - full_bbox[1]
        cad_area = bbox_area(full_bbox)
        centers = [center_of(box) for box in boxes]  # type: ignore[arg-type]
        x_clusters, max_x_gap_ratio = one_dimensional_clusters(
            [point[0] for point in centers],
            cad_width,
            args.panel_gap_ratio,
            args.min_panel_entities,
        )
        y_clusters, max_y_gap_ratio = one_dimensional_clusters(
            [point[1] for point in centers],
            cad_height,
            args.panel_gap_ratio,
            args.min_panel_entities,
        )
    else:
        cad_width = cad_height = cad_area = 0.0
        x_clusters = y_clusters = 0
        max_x_gap_ratio = max_y_gap_ratio = 0.0

    return {
        "entity_count": len(entities),
        "bbox_entity_count": len(boxes),
        "line_count": type_counts.get("LINE", 0),
        "polyline_count": type_counts.get("LWPOLYLINE", 0),
        "text_count": type_counts.get("TEXT", 0) + type_counts.get("MTEXT", 0),
        "insert_count": type_counts.get("INSERT", 0),
        "circle_count": type_counts.get("CIRCLE", 0),
        "arc_count": type_counts.get("ARC", 0),
        "cad_min_x": full_bbox[0] if full_bbox else "",
        "cad_min_y": full_bbox[1] if full_bbox else "",
        "cad_max_x": full_bbox[2] if full_bbox else "",
        "cad_max_y": full_bbox[3] if full_bbox else "",
        "cad_width": cad_width,
        "cad_height": cad_height,
        "cad_area": cad_area,
        "cad_aspect_ratio": cad_width / cad_height if cad_height else 0.0,
        "x_cluster_count": x_clusters,
        "y_cluster_count": y_clusters,
        "max_x_gap_ratio": max_x_gap_ratio,
        "max_y_gap_ratio": max_y_gap_ratio,
    }


def flag_sample(stats: Dict[str, object], args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    hard_reject: List[str] = []
    review: List[str] = []

    entity_count = int(stats["entity_count"])
    line_like = int(stats["line_count"]) + int(stats["polyline_count"])
    text_count = int(stats["text_count"])
    cad_width = float(stats["cad_width"])
    cad_height = float(stats["cad_height"])
    png_width = int(stats["png_width"] or 0)
    png_height = int(stats["png_height"] or 0)
    x_clusters = int(stats["x_cluster_count"])
    y_clusters = int(stats["y_cluster_count"])
    max_gap = max(float(stats["max_x_gap_ratio"]), float(stats["max_y_gap_ratio"]))

    if stats["png_error"]:
        hard_reject.append("png_unreadable")
    if entity_count == 0:
        hard_reject.append("empty_entities")
    if cad_width <= 0 or cad_height <= 0:
        hard_reject.append("degenerate_cad_bbox")
    if png_width <= 0 or png_height <= 0:
        hard_reject.append("degenerate_png_size")

    if entity_count < args.min_entities:
        review.append("low_entity_count")
    if line_like < args.min_line_like:
        review.append("low_line_geometry")
    if text_count == 0:
        review.append("no_text")
    if entity_count > args.huge_entity_threshold:
        review.append("huge_entity_count")
    if png_width and png_height:
        png_ratio = max(png_width / png_height, png_height / png_width)
        if png_ratio > args.extreme_aspect_ratio:
            review.append("extreme_png_aspect_ratio")

    if (x_clusters >= 2 or y_clusters >= 2) and max_gap >= args.panel_gap_ratio:
        review.append("multi_panel_candidate")

    return hard_reject, review


def scan(args: argparse.Namespace) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    rows = load_rows(args.manifest)
    output_rows: List[Dict[str, object]] = []

    for row in rows:
        json_path = ROOT / row["raw_json_path"]
        png_path = ROOT / row["png_path"]
        png_width, png_height, png_error = get_png_size(png_path)
        stats = scan_json(json_path, args)
        stats.update(
            {
                "drawing_key": row["drawing_key"],
                "drawing_id": row["drawing_id"],
                "phase": row["phase"],
                "batch": row["batch"],
                "split": row["split"],
                "raw_json_path": row["raw_json_path"],
                "png_path": row["png_path"],
                "png_width": png_width or "",
                "png_height": png_height or "",
                "png_error": png_error,
                "png_file_size": png_path.stat().st_size if png_path.exists() else 0,
            }
        )
        hard_reject, review = flag_sample(stats, args)
        stats["hard_reject_reasons"] = ";".join(hard_reject)
        stats["review_flags"] = ";".join(review)
        stats["needs_panel_split"] = "multi_panel_candidate" in review
        stats["round2_keep"] = not hard_reject
        output_rows.append(stats)

    summary = summarize(output_rows, args)
    return output_rows, summary


def summarize(rows: List[Dict[str, object]], args: argparse.Namespace) -> Dict[str, object]:
    entity_counts = [float(row["entity_count"]) for row in rows]
    png_widths = [float(row["png_width"]) for row in rows if row["png_width"]]
    png_heights = [float(row["png_height"]) for row in rows if row["png_height"]]
    review_counter: Counter[str] = Counter()
    hard_counter: Counter[str] = Counter()
    for row in rows:
        for flag in str(row["review_flags"]).split(";"):
            if flag:
                review_counter[flag] += 1
        for reason in str(row["hard_reject_reasons"]).split(";"):
            if reason:
                hard_counter[reason] += 1

    return {
        "source_manifest": str(args.manifest).replace("\\", "/"),
        "total_rows": len(rows),
        "round2_keep_rows": sum(1 for row in rows if row["round2_keep"]),
        "hard_reject_rows": sum(1 for row in rows if row["hard_reject_reasons"]),
        "review_rows": sum(1 for row in rows if row["review_flags"]),
        "multi_panel_candidates": sum(1 for row in rows if row["needs_panel_split"]),
        "review_flags": dict(review_counter),
        "hard_reject_reasons": dict(hard_counter),
        "entity_count": {
            "min": min(entity_counts) if entity_counts else 0,
            "median": median(entity_counts) if entity_counts else 0,
            "p95": quantile(entity_counts, 0.95),
            "p99": quantile(entity_counts, 0.99),
            "max": max(entity_counts) if entity_counts else 0,
        },
        "png_width": {
            "min": min(png_widths) if png_widths else 0,
            "median": median(png_widths) if png_widths else 0,
            "max": max(png_widths) if png_widths else 0,
        },
        "png_height": {
            "min": min(png_heights) if png_heights else 0,
            "median": median(png_heights) if png_heights else 0,
            "max": max(png_heights) if png_heights else 0,
        },
        "thresholds": {
            "min_entities": args.min_entities,
            "min_line_like": args.min_line_like,
            "huge_entity_threshold": args.huge_entity_threshold,
            "extreme_aspect_ratio": args.extreme_aspect_ratio,
            "panel_gap_ratio": args.panel_gap_ratio,
            "min_panel_entities": args.min_panel_entities,
        },
    }


def write_report(summary: Dict[str, object], rows: List[Dict[str, object]]) -> None:
    lines = [
        "# Content Quality Report",
        "",
        "This is the second-round non-destructive content scan.",
        "",
        "## Summary",
        "",
        f"- Total clean rows scanned: {summary['total_rows']}",
        f"- Round-2 keep rows: {summary['round2_keep_rows']}",
        f"- Hard reject rows: {summary['hard_reject_rows']}",
        f"- Review rows: {summary['review_rows']}",
        f"- Multi-panel candidates: {summary['multi_panel_candidates']}",
        "",
        "## Review Flags",
        "",
    ]
    review_flags = summary["review_flags"]
    if review_flags:
        for flag, count in review_flags.items():
            lines.append(f"- {flag}: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Hard Reject Reasons", ""])
    hard_reasons = summary["hard_reject_reasons"]
    if hard_reasons:
        for reason, count in hard_reasons.items():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Multi-Panel Handling Recommendation",
            "",
            "Multi-panel candidates are not bad samples. They should be promoted from drawing-level samples to panel-level samples.",
            "",
            "Recommended next workflow:",
            "",
            "1. Review `data_index/multi_panel_candidates.csv`.",
            "2. Confirm whether detected layout gaps correspond to real subfigures/pages.",
            "3. Generate a `panel_manifest.csv` where each row is one cropped panel with a parent `drawing_key`.",
            "4. Keep original drawing-level rows for CAD reconstruction, but use panel-level rows for VQA and detection tasks.",
            "",
            "## First Multi-Panel Candidates",
            "",
        ]
    )

    candidates = [row for row in rows if row["needs_panel_split"]]
    if not candidates:
        lines.append("No multi-panel candidates.")
    else:
        lines.append("| drawing_key | split | x_clusters | y_clusters | max_x_gap | max_y_gap |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for row in candidates[:50]:
            lines.append(
                f"| `{row['drawing_key']}` | {row['split']} | {row['x_cluster_count']} | "
                f"{row['y_cluster_count']} | {float(row['max_x_gap_ratio']):.3f} | "
                f"{float(row['max_y_gap_ratio']):.3f} |"
            )

    (INDEX_DIR / "content_quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--min-entities", type=int, default=20)
    parser.add_argument("--min-line-like", type=int, default=5)
    parser.add_argument("--huge-entity-threshold", type=int, default=20000)
    parser.add_argument("--extreme-aspect-ratio", type=float, default=8.0)
    parser.add_argument("--panel-gap-ratio", type=float, default=0.18)
    parser.add_argument("--min-panel-entities", type=int, default=80)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.manifest = args.manifest.resolve()
    rows, summary = scan(args)

    write_csv(INDEX_DIR / "content_quality_stats.csv", rows)
    multi_panel_rows = [row for row in rows if row["needs_panel_split"]]
    write_csv(INDEX_DIR / "multi_panel_candidates.csv", multi_panel_rows, list(rows[0].keys()) if rows else [])
    hard_reject_rows = [row for row in rows if row["hard_reject_reasons"]]
    write_csv(INDEX_DIR / "round2_hard_rejects.csv", hard_reject_rows, list(rows[0].keys()) if rows else [])
    round2_rows = [row for row in rows if row["round2_keep"]]
    round2_keys = {str(row["drawing_key"]) for row in round2_rows}
    clean_rows = load_rows(args.manifest)
    round2_manifest = [row for row in clean_rows if row["drawing_key"] in round2_keys]
    write_csv(INDEX_DIR / "round2_clean_manifest.csv", round2_manifest, list(clean_rows[0].keys()) if clean_rows else [])
    write_manifest_splits(round2_manifest, "round2_clean", list(clean_rows[0].keys()) if clean_rows else [])

    (INDEX_DIR / "content_quality_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary, rows)

    print(f"Scanned rows: {summary['total_rows']}")
    print(f"Hard rejects: {summary['hard_reject_rows']}")
    print(f"Multi-panel candidates: {summary['multi_panel_candidates']}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/content_quality_stats.csv")


if __name__ == "__main__":
    main()
