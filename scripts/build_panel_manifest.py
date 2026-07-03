"""Build a panel-level manifest from round-2 cleaned drawings.

For normal drawings, the panel manifest contains one full-image panel.
For multi-panel candidates, it splits CAD entities using large gaps in entity
center distributions and optionally writes cropped PNG panels under outputs/.

Raw assets are never modified.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from scan_content_quality import bbox_area, center_of, entity_bbox, get_png_size, union_bbox


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "round2_clean_manifest.csv"
DEFAULT_QUALITY_STATS = INDEX_DIR / "content_quality_stats.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "panels"

BBox = Tuple[float, float, float, float]


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
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


def safe_slug(value: str, max_len: int = 96) -> str:
    value = value.replace("\\", "/").replace("/", "__")
    value = re.sub(r'[<>:"|?*\x00-\x1f]', "_", value)
    value = re.sub(r"\s+", "_", value).strip("._ ")
    return value[:max_len] or "panel"


def load_entity_boxes(path: Path) -> List[Tuple[Dict[str, object], BBox]]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    entities = payload.get("entities", [])
    results: List[Tuple[Dict[str, object], BBox]] = []
    if not isinstance(entities, list):
        return results
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        box = entity_bbox(entity)
        if box is None:
            continue
        if bbox_area(box) < 0:
            continue
        results.append((entity, box))
    return results


def accepted_split_indices(
    values: List[float],
    total_range: float,
    gap_ratio: float,
    min_points: int,
    max_splits: int,
) -> List[int]:
    if len(values) < min_points * 2 or total_range <= 0:
        return []
    values = sorted(values)
    gaps = []
    for index in range(len(values) - 1):
        gap = values[index + 1] - values[index]
        left = index + 1
        right = len(values) - left
        if gap / total_range >= gap_ratio and left >= min_points and right >= min_points:
            gaps.append((gap, index))
    gaps = sorted(gaps, reverse=True)[:max_splits]
    return sorted(index for _, index in gaps)


def assign_cluster(value: float, boundaries: List[float]) -> int:
    for index, boundary in enumerate(boundaries):
        if value <= boundary:
            return index
    return len(boundaries)


def cluster_boundaries(values: List[float], split_indices: List[int]) -> List[float]:
    values = sorted(values)
    boundaries = []
    for index in split_indices:
        boundaries.append((values[index] + values[index + 1]) / 2.0)
    return boundaries


def padded_bbox(box: BBox, full: BBox, padding_ratio: float) -> BBox:
    width = box[2] - box[0]
    height = box[3] - box[1]
    pad_x = max(width * padding_ratio, (full[2] - full[0]) * 0.005)
    pad_y = max(height * padding_ratio, (full[3] - full[1]) * 0.005)
    return (
        max(full[0], box[0] - pad_x),
        max(full[1], box[1] - pad_y),
        min(full[2], box[2] + pad_x),
        min(full[3], box[3] + pad_y),
    )


def cad_to_png_bbox(panel: BBox, full: BBox, png_width: int, png_height: int) -> Tuple[int, int, int, int]:
    full_width = full[2] - full[0]
    full_height = full[3] - full[1]
    if full_width <= 0 or full_height <= 0:
        return (0, 0, png_width, png_height)

    left = int(round((panel[0] - full[0]) / full_width * png_width))
    right = int(round((panel[2] - full[0]) / full_width * png_width))
    top = int(round((full[3] - panel[3]) / full_height * png_height))
    bottom = int(round((full[3] - panel[1]) / full_height * png_height))

    left = max(0, min(left, png_width - 1))
    right = max(left + 1, min(right, png_width))
    top = max(0, min(top, png_height - 1))
    bottom = max(top + 1, min(bottom, png_height))
    return left, top, right, bottom


def cad_point_to_png(point: Tuple[float, float], full: BBox, png_width: int, png_height: int) -> Tuple[float, float]:
    full_width = full[2] - full[0]
    full_height = full[3] - full[1]
    if full_width <= 0 or full_height <= 0:
        return 0.0, 0.0
    x = (point[0] - full[0]) / full_width * png_width
    y = (full[3] - point[1]) / full_height * png_height
    return x, y


def png_to_cad_bbox(png_bbox: Tuple[int, int, int, int], full: BBox, png_width: int, png_height: int) -> BBox:
    full_width = full[2] - full[0]
    full_height = full[3] - full[1]
    left, top, right, bottom = png_bbox
    cad_min_x = full[0] + (left / png_width) * full_width
    cad_max_x = full[0] + (right / png_width) * full_width
    cad_max_y = full[3] - (top / png_height) * full_height
    cad_min_y = full[3] - (bottom / png_height) * full_height
    return cad_min_x, cad_min_y, cad_max_x, cad_max_y


def read_gray_image(path: Path):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    except Exception:  # noqa: BLE001
        return None


def image_component_bboxes(png_path: Path, args: argparse.Namespace) -> List[Tuple[int, int, int, int]]:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return []

    image = read_gray_image(png_path)
    if image is None:
        return []

    height, width = image.shape[:2]
    mask = (image < args.image_threshold).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (args.image_dilate_kernel, args.image_dilate_kernel),
    )
    dilated = cv2.dilate(mask, kernel, iterations=1)
    count, _, stats, _ = cv2.connectedComponentsWithStats(dilated, 8)

    boxes: List[Tuple[int, int, int, int]] = []
    min_area = width * height * args.min_image_panel_png_area_ratio
    for index in range(1, count):
        x, y, w, h, area = stats[index]
        if area < min_area:
            continue
        if min(w, h) < args.min_panel_png_side:
            continue
        pad_x = max(int(round(w * args.image_padding_ratio)), 16)
        pad_y = max(int(round(h * args.image_padding_ratio)), 16)
        left = max(0, int(x) - pad_x)
        top = max(0, int(y) - pad_y)
        right = min(width, int(x + w) + pad_x)
        bottom = min(height, int(y + h) + pad_y)
        boxes.append((left, top, right, bottom))

    return sorted(boxes, key=lambda box: (box[1], box[0]))


def count_entities_in_png_bbox(
    png_bbox: Tuple[int, int, int, int],
    boxes: List[BBox],
    full_bbox: BBox,
    png_width: int,
    png_height: int,
) -> int:
    left, top, right, bottom = png_bbox
    count = 0
    for box in boxes:
        x, y = cad_point_to_png(center_of(box), full_bbox, png_width, png_height)
        if left <= x <= right and top <= y <= bottom:
            count += 1
    return count


def build_panels_for_row(row: Dict[str, str], is_candidate: bool, args: argparse.Namespace) -> List[Dict[str, object]]:
    json_path = ROOT / row["raw_json_path"]
    png_path = ROOT / row["png_path"]
    png_width, png_height, png_error = get_png_size(png_path)
    entity_boxes = load_entity_boxes(json_path)
    boxes = [box for _, box in entity_boxes]
    full_bbox = union_bbox(boxes)

    if not png_width or not png_height or png_error or not full_bbox:
        return []

    if not is_candidate:
        return [
            make_panel_row(
                row,
                panel_index=0,
                panel_count=1,
                split_method="full",
                cad_bbox=full_bbox,
                full_cad_bbox=full_bbox,
                png_bbox=(0, 0, png_width, png_height),
                entity_count=len(entity_boxes),
                png_width=png_width,
                png_height=png_height,
                panel_png_path=row["png_path"],
            )
        ]

    image_boxes = image_component_bboxes(png_path, args)
    if len(image_boxes) > 1:
        panel_rows = []
        panel_count = len(image_boxes)
        for panel_index, png_bbox in enumerate(image_boxes):
            cad_bbox = png_to_cad_bbox(png_bbox, full_bbox, png_width, png_height)
            panel_png_path = ""
            if args.write_crops:
                panel_png_path = crop_panel(row, png_path, png_bbox, panel_index, args.output_dir)
            panel_rows.append(
                make_panel_row(
                    row,
                    panel_index=panel_index,
                    panel_count=panel_count,
                    split_method="image_components",
                    cad_bbox=cad_bbox,
                    full_cad_bbox=full_bbox,
                    png_bbox=png_bbox,
                    entity_count=count_entities_in_png_bbox(png_bbox, boxes, full_bbox, png_width, png_height),
                    png_width=png_width,
                    png_height=png_height,
                    panel_png_path=panel_png_path or row["png_path"],
                    notes="",
                )
            )
        return panel_rows

    centers = [center_of(box) for box in boxes]
    cad_width = full_bbox[2] - full_bbox[0]
    cad_height = full_bbox[3] - full_bbox[1]
    x_values = [point[0] for point in centers]
    y_values = [point[1] for point in centers]
    x_splits = accepted_split_indices(
        x_values,
        cad_width,
        args.gap_ratio,
        args.min_panel_entities,
        args.max_splits_per_axis,
    )
    y_splits = accepted_split_indices(
        y_values,
        cad_height,
        args.gap_ratio,
        args.min_panel_entities,
        args.max_splits_per_axis,
    )
    x_boundaries = cluster_boundaries(x_values, x_splits)
    y_boundaries = cluster_boundaries(y_values, y_splits)

    groups: Dict[Tuple[int, int], List[BBox]] = {}
    for _, box in entity_boxes:
        cx, cy = center_of(box)
        key = (assign_cluster(cx, x_boundaries), assign_cluster(cy, y_boundaries))
        groups.setdefault(key, []).append(box)

    panel_specs = []
    discarded_tiny_panels = 0
    for key, group_boxes in sorted(groups.items()):
        if len(group_boxes) < args.min_panel_entities:
            continue
        panel_bbox = union_bbox(group_boxes)
        if panel_bbox is None:
            continue
        if bbox_area(panel_bbox) <= 0:
            continue
        panel_bbox = padded_bbox(panel_bbox, full_bbox, args.padding_ratio)
        png_bbox = cad_to_png_bbox(panel_bbox, full_bbox, png_width, png_height)
        png_box_width = png_bbox[2] - png_bbox[0]
        png_box_height = png_bbox[3] - png_bbox[1]
        png_area_ratio = (png_box_width * png_box_height) / float(png_width * png_height)
        if png_area_ratio < args.min_panel_png_area_ratio or min(png_box_width, png_box_height) < args.min_panel_png_side:
            discarded_tiny_panels += 1
            continue
        panel_specs.append((key, panel_bbox, len(group_boxes)))

    if len(panel_specs) <= 1:
        # Candidate was too ambiguous after stricter grouping. Keep full image,
        # but preserve the status so humans can review it later.
        return [
            make_panel_row(
                row,
                panel_index=0,
                panel_count=1,
                split_method="candidate_full_fallback",
                cad_bbox=full_bbox,
                full_cad_bbox=full_bbox,
                png_bbox=(0, 0, png_width, png_height),
                entity_count=len(entity_boxes),
                png_width=png_width,
                png_height=png_height,
                panel_png_path=row["png_path"],
                notes=f"discarded_tiny_panels={discarded_tiny_panels}",
            )
        ]

    panel_rows = []
    panel_count = len(panel_specs)
    for panel_index, (_, cad_bbox, count) in enumerate(panel_specs):
        png_bbox = cad_to_png_bbox(cad_bbox, full_bbox, png_width, png_height)
        panel_png_path = ""
        if args.write_crops:
            panel_png_path = crop_panel(row, png_path, png_bbox, panel_index, args.output_dir)
        panel_rows.append(
            make_panel_row(
                row,
                panel_index=panel_index,
                panel_count=panel_count,
                split_method="cad_gap",
                cad_bbox=cad_bbox,
                full_cad_bbox=full_bbox,
                png_bbox=png_bbox,
                entity_count=count,
                png_width=png_width,
                png_height=png_height,
                panel_png_path=panel_png_path or row["png_path"],
                notes="",
            )
        )
    return panel_rows


def fmt_bbox(box: Sequence[float | int]) -> str:
    return ",".join(str(round(float(value), 4)) for value in box)


def make_panel_row(
    row: Dict[str, str],
    panel_index: int,
    panel_count: int,
    split_method: str,
    cad_bbox: BBox,
    full_cad_bbox: BBox,
    png_bbox: Tuple[int, int, int, int],
    entity_count: int,
    png_width: int,
    png_height: int,
    panel_png_path: str,
    notes: str = "",
) -> Dict[str, object]:
    panel_id = f"{row['drawing_key']}#panel_{panel_index:03d}"
    return {
        "panel_id": panel_id,
        "parent_drawing_key": row["drawing_key"],
        "parent_drawing_id": row["drawing_id"],
        "parent_png_path": row["png_path"],
        "parent_raw_json_path": row["raw_json_path"],
        "panel_index": panel_index,
        "panel_count": panel_count,
        "split": row["split"],
        "phase": row["phase"],
        "batch": row["batch"],
        "split_method": split_method,
        "panel_bbox_cad": fmt_bbox(cad_bbox),
        "parent_bbox_cad": fmt_bbox(full_cad_bbox),
        "panel_bbox_png": fmt_bbox(png_bbox),
        "parent_png_width": png_width,
        "parent_png_height": png_height,
        "panel_entity_count": entity_count,
        "panel_png_path": panel_png_path,
        "needs_review": split_method in {"image_components", "cad_gap", "candidate_full_fallback"},
        "notes": notes,
    }


def crop_panel(
    row: Dict[str, str],
    png_path: Path,
    png_bbox: Tuple[int, int, int, int],
    panel_index: int,
    output_dir: Path,
) -> str:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required for crop output. Install pillow or pass --no-crops.") from exc

    phase_dir = output_dir / row["phase"]
    phase_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{safe_slug(row['drawing_key'])}__panel_{panel_index:03d}.png"
    out_path = phase_dir / filename
    with Image.open(png_path) as image:
        image.crop(png_bbox).save(out_path)
    return out_path.relative_to(ROOT).as_posix()


def write_split_files(panel_rows: List[Dict[str, object]]) -> None:
    fieldnames = list(panel_rows[0].keys()) if panel_rows else []
    for split in ("train", "val", "test"):
        rows = [row for row in panel_rows if row["split"] == split]
        write_csv(INDEX_DIR / f"panel_{split}.csv", rows, fieldnames)


def write_summary(panel_rows: List[Dict[str, object]], drawing_count: int, candidate_count: int) -> Dict[str, object]:
    by_method = Counter(str(row["split_method"]) for row in panel_rows)
    by_split = Counter(str(row["split"]) for row in panel_rows)
    multi_panel_parents = {
        str(row["parent_drawing_key"])
        for row in panel_rows
        if int(row["panel_count"]) > 1
    }
    review_rows = sum(1 for row in panel_rows if str(row["needs_review"]).lower() == "true")
    summary = {
        "source_manifest": str(DEFAULT_MANIFEST).replace("\\", "/"),
        "source_multi_panel_candidates": candidate_count,
        "source_drawing_rows": drawing_count,
        "panel_rows": len(panel_rows),
        "multi_panel_parent_count": len(multi_panel_parents),
        "review_panel_rows": review_rows,
        "by_split": dict(by_split),
        "by_split_method": dict(by_method),
    }
    (INDEX_DIR / "panel_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def write_report(summary: Dict[str, object], panel_rows: List[Dict[str, object]]) -> None:
    lines = [
        "# Panel Manifest Report",
        "",
        "This report describes the drawing-level to panel-level expansion.",
        "",
        "## Summary",
        "",
        f"- Source drawing rows: {summary['source_drawing_rows']}",
        f"- Source multi-panel candidates: {summary['source_multi_panel_candidates']}",
        f"- Panel rows: {summary['panel_rows']}",
        f"- Multi-panel parent drawings: {summary['multi_panel_parent_count']}",
        f"- Review panel rows: {summary['review_panel_rows']}",
        "",
        "## Split Counts",
        "",
    ]
    for split, count in summary["by_split"].items():
        lines.append(f"- {split}: {count}")

    lines.extend(["", "## Split Methods", ""])
    for method, count in summary["by_split_method"].items():
        lines.append(f"- {method}: {count}")

    lines.extend(["", "## First Split Panels", ""])
    split_rows = [row for row in panel_rows if row["split_method"] in {"image_components", "cad_gap"}]
    if not split_rows:
        lines.append("No split panels generated.")
    else:
        lines.append("| parent | panel | panel_count | bbox_png | panel_png |")
        lines.append("|---|---:|---:|---|---|")
        for row in split_rows[:50]:
            lines.append(
                f"| `{row['parent_drawing_key']}` | {row['panel_index']} | {row['panel_count']} | "
                f"`{row['panel_bbox_png']}` | `{row['panel_png_path']}` |"
            )

    (INDEX_DIR / "panel_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--quality-stats", type=Path, default=DEFAULT_QUALITY_STATS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--gap-ratio", type=float, default=0.18)
    parser.add_argument("--min-panel-entities", type=int, default=80)
    parser.add_argument("--max-splits-per-axis", type=int, default=3)
    parser.add_argument("--padding-ratio", type=float, default=0.02)
    parser.add_argument("--min-panel-png-area-ratio", type=float, default=0.03)
    parser.add_argument("--min-image-panel-png-area-ratio", type=float, default=0.01)
    parser.add_argument("--min-panel-png-side", type=int, default=512)
    parser.add_argument("--image-threshold", type=int, default=245)
    parser.add_argument("--image-dilate-kernel", type=int, default=45)
    parser.add_argument("--image-padding-ratio", type=float, default=0.015)
    parser.add_argument("--no-crops", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.manifest = args.manifest.resolve()
    args.quality_stats = args.quality_stats.resolve()
    args.output_dir = args.output_dir.resolve()
    args.write_crops = not args.no_crops

    drawing_rows = load_csv(args.manifest)
    quality_rows = load_csv(args.quality_stats)
    candidate_keys = {
        row["drawing_key"]
        for row in quality_rows
        if str(row.get("needs_panel_split", "")).lower() == "true"
    }

    panel_rows: List[Dict[str, object]] = []
    for row in drawing_rows:
        panel_rows.extend(build_panels_for_row(row, row["drawing_key"] in candidate_keys, args))

    fieldnames = list(panel_rows[0].keys()) if panel_rows else []
    write_csv(INDEX_DIR / "panel_manifest.csv", panel_rows, fieldnames)
    write_split_files(panel_rows)
    summary = write_summary(panel_rows, len(drawing_rows), len(candidate_keys))
    write_report(summary, panel_rows)

    print(f"Source drawings: {summary['source_drawing_rows']}")
    print(f"Panel rows: {summary['panel_rows']}")
    print(f"Multi-panel parents: {summary['multi_panel_parent_count']}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/panel_manifest.csv")


if __name__ == "__main__":
    main()
