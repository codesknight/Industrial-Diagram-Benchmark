"""Build normalized geometry JSON files from Raw Geometry JSON.

The output is still geometry-level data, not semantic interpretation. It keeps
CAD primitives in a schema that is easier to validate, index, and feed into
topology/panel/VQA pipelines.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "final_drawing_manifest.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "normalized_geometry"

Point = Tuple[float, float]
BBox = Tuple[float, float, float, float]


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
    rel = Path(drawing_key.replace("\\", "/") + ".normalized.json")
    return output_dir / rel


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


def round_point(point: Point, precision: int) -> List[float]:
    return [round(point[0], precision), round(point[1], precision)]


def round_bbox(box: BBox, precision: int) -> List[float]:
    return [round(value, precision) for value in box]


def bbox_from_points(points: Sequence[Point]) -> Optional[BBox]:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def union_bbox(boxes: Sequence[BBox]) -> Optional[BBox]:
    if not boxes:
        return None
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def parse_float(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def entity_points(entity: Dict[str, object]) -> List[Point]:
    kind = str(entity.get("type", "")).upper()
    points: List[Point] = []

    for key in ("start", "end", "position", "center", "point", "location", "insert"):
        point = finite_xy(entity.get(key))
        if point:
            points.append(point)

    raw_points = entity.get("points")
    if isinstance(raw_points, list):
        for raw_point in raw_points:
            point = finite_xy(raw_point)
            if point:
                points.append(point)

    vertices = entity.get("vertices")
    if isinstance(vertices, list):
        for raw_point in vertices:
            point = finite_xy(raw_point)
            if point:
                points.append(point)

    if kind in {"CIRCLE", "ARC"}:
        center = finite_xy(entity.get("center"))
        radius = abs(parse_float(entity.get("radius")))
        if center and radius:
            points.extend(
                [
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius),
                ]
            )

    if kind in {"TEXT", "MTEXT", "ATTDEF"}:
        point = finite_xy(entity.get("position"))
        if point:
            height = abs(parse_float(entity.get("height")))
            text = str(entity.get("content", entity.get("text", "")))
            width = max(height * max(len(text), 1) * 0.65, height)
            points.append((point[0] + width, point[1] + height))

    return points


def normalize_entity(entity: Dict[str, object], precision: int) -> Dict[str, object]:
    kind = str(entity.get("type", "UNKNOWN")).upper()
    points = entity_points(entity)
    bbox = bbox_from_points(points)
    out: Dict[str, object] = {
        "id": str(entity.get("id", "")),
        "type": kind,
        "layer": str(entity.get("layer", "")),
        "bbox": round_bbox(bbox, precision) if bbox else None,
    }

    if kind == "LINE":
        start = finite_xy(entity.get("start"))
        end = finite_xy(entity.get("end"))
        out["geometry"] = {
            "primitive": "line",
            "start": round_point(start, precision) if start else None,
            "end": round_point(end, precision) if end else None,
        }
    elif kind == "LWPOLYLINE":
        raw_points = entity.get("points", [])
        poly_points = [finite_xy(point) for point in raw_points] if isinstance(raw_points, list) else []
        out["geometry"] = {
            "primitive": "polyline",
            "points": [round_point(point, precision) for point in poly_points if point],
            "closed": bool(entity.get("closed", False)),
        }
    elif kind in {"TEXT", "MTEXT", "ATTDEF"}:
        position = finite_xy(entity.get("position"))
        out["text"] = str(entity.get("content", entity.get("text", "")))
        out["geometry"] = {
            "primitive": "text",
            "position": round_point(position, precision) if position else None,
            "height": round(parse_float(entity.get("height")), precision),
            "rotation": round(parse_float(entity.get("rotation")), precision),
        }
    elif kind == "INSERT":
        position = finite_xy(entity.get("position"))
        out["block_name"] = str(entity.get("block_name", entity.get("name", "")))
        out["geometry"] = {
            "primitive": "insert",
            "position": round_point(position, precision) if position else None,
            "rotation": round(parse_float(entity.get("rotation")), precision),
            "xscale": round(parse_float(entity.get("xscale"), 1.0), precision),
            "yscale": round(parse_float(entity.get("yscale"), 1.0), precision),
        }
    elif kind in {"CIRCLE", "ARC"}:
        center = finite_xy(entity.get("center"))
        geometry = {
            "primitive": kind.lower(),
            "center": round_point(center, precision) if center else None,
            "radius": round(parse_float(entity.get("radius")), precision),
        }
        if kind == "ARC":
            geometry["start_angle"] = round(parse_float(entity.get("start_angle")), precision)
            geometry["end_angle"] = round(parse_float(entity.get("end_angle")), precision)
        out["geometry"] = geometry
    elif kind == "POINT":
        point = finite_xy(entity.get("point", entity.get("position")))
        out["geometry"] = {
            "primitive": "point",
            "point": round_point(point, precision) if point else None,
        }
    else:
        out["geometry"] = {
            "primitive": "raw",
            "point_count": len(points),
        }

    return out


def normalize_file(row: Dict[str, str], output_dir: Path, precision: int) -> Dict[str, object]:
    raw_path = ROOT / row["raw_json_path"]
    with raw_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    raw_entities = payload.get("entities", [])
    if not isinstance(raw_entities, list):
        raw_entities = []
    entities = [
        normalize_entity(entity, precision)
        for entity in raw_entities
        if isinstance(entity, dict)
    ]
    boxes = [
        tuple(entity["bbox"])  # type: ignore[arg-type]
        for entity in entities
        if entity.get("bbox")
    ]
    drawing_bbox = union_bbox(boxes)  # type: ignore[arg-type]
    type_counts = Counter(str(entity["type"]) for entity in entities)
    text_count = sum(1 for entity in entities if entity.get("text"))

    out_payload = {
        "schema": "industrial_diagram.normalized_geometry.v1",
        "drawing_key": row["drawing_key"],
        "drawing_id": row["drawing_id"],
        "phase": row["phase"],
        "split": row["split"],
        "source": {
            "raw_json_path": row["raw_json_path"],
            "dxf_path": row.get("dxf_path", ""),
            "png_path": row.get("png_path", ""),
        },
        "stats": {
            "entity_count": len(entities),
            "bbox_entity_count": len(boxes),
            "text_count": text_count,
            "type_counts": dict(type_counts),
            "drawing_bbox": round_bbox(drawing_bbox, precision) if drawing_bbox else None,
        },
        "entities": entities,
    }

    out_path = safe_output_path(row["drawing_key"], output_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out_payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    return {
        "drawing_key": row["drawing_key"],
        "split": row["split"],
        "phase": row["phase"],
        "raw_json_path": row["raw_json_path"],
        "normalized_json_path": out_path.relative_to(ROOT).as_posix(),
        "entity_count": len(entities),
        "bbox_entity_count": len(boxes),
        "text_count": text_count,
        "type_count_json": json.dumps(dict(type_counts), ensure_ascii=False, sort_keys=True),
        "drawing_bbox": ",".join(str(value) for value in round_bbox(drawing_bbox, precision)) if drawing_bbox else "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--precision", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    if args.limit:
        rows = rows[: args.limit]

    output_dir = args.output_dir.resolve()
    manifest_rows = [normalize_file(row, output_dir, args.precision) for row in rows]

    fieldnames = [
        "drawing_key",
        "split",
        "phase",
        "raw_json_path",
        "normalized_json_path",
        "entity_count",
        "bbox_entity_count",
        "text_count",
        "type_count_json",
        "drawing_bbox",
    ]
    write_csv(INDEX_DIR / "normalized_geometry_manifest.csv", manifest_rows, fieldnames)
    write_summary(manifest_rows)
    print(f"Normalized drawings: {len(manifest_rows)}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/normalized_geometry_manifest.csv")


def write_summary(rows: List[Dict[str, object]]) -> None:
    type_counts: Counter[str] = Counter()
    split_counts = Counter(str(row["split"]) for row in rows)
    phase_counts = Counter(str(row["phase"]) for row in rows)
    for row in rows:
        type_counts.update(json.loads(str(row["type_count_json"])))

    entity_counts = [int(row["entity_count"]) for row in rows]
    summary = {
        "normalized_rows": len(rows),
        "by_split": dict(split_counts),
        "by_phase": dict(phase_counts),
        "entity_count_min": min(entity_counts) if entity_counts else 0,
        "entity_count_max": max(entity_counts) if entity_counts else 0,
        "entity_count_avg": round(sum(entity_counts) / len(entity_counts), 2) if entity_counts else 0,
        "type_counts": dict(type_counts.most_common()),
    }
    (INDEX_DIR / "normalized_geometry_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Normalized Geometry Report",
        "",
        "This report summarizes geometry-level normalization from final drawing samples.",
        "",
        f"- Normalized rows: {summary['normalized_rows']}",
        f"- Entity count min: {summary['entity_count_min']}",
        f"- Entity count avg: {summary['entity_count_avg']}",
        f"- Entity count max: {summary['entity_count_max']}",
        "",
        "## Split Counts",
        "",
    ]
    for split, count in summary["by_split"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Top Entity Types", ""])
    for kind, count in list(summary["type_counts"].items())[:20]:
        lines.append(f"- {kind}: {count}")
    (INDEX_DIR / "normalized_geometry_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
