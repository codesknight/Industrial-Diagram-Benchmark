"""Apply manual multi-panel split labels for topology v1 pilot pages.

The exported labels contain PNG-space bounding boxes. This script writes local
panel crops and a panel-level manifest for the next topology pilot step without
modifying the full dataset panel manifests.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_LABELS = INDEX_DIR / "topology_multipanel_split_labels.csv"
DEFAULT_DRAWINGS = INDEX_DIR / "final_drawing_manifest.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "topology_multipanel_panels"

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


def safe_slug(value: str, max_len: int = 120) -> str:
    value = value.replace("\\", "/").replace("/", "__")
    value = re.sub(r'[<>:"|?*\x00-\x1f]', "_", value)
    value = re.sub(r"\s+", "_", value).strip("._ ")
    return value[:max_len] or "panel"


def parse_bbox(value: str) -> Optional[BBox]:
    parts = str(value).split(",")
    if len(parts) != 4:
        return None
    try:
        box = tuple(float(part) for part in parts)
    except ValueError:
        return None
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def fmt_bbox(box: Sequence[float | int]) -> str:
    return ",".join(str(round(float(value), 4)) for value in box)


def clamp_bbox(box: BBox, width: int, height: int) -> Tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    left = max(0, min(int(round(x0)), width - 1))
    top = max(0, min(int(round(y0)), height - 1))
    right = max(left + 1, min(int(round(x1)), width))
    bottom = max(top + 1, min(int(round(y1)), height))
    return left, top, right, bottom


def crop_panel(png_path: Path, out_path: Path, bbox: Tuple[int, int, int, int]) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to crop panels.") from exc

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(png_path) as image:
        image.crop(bbox).save(out_path)


def image_size(path: Path) -> Tuple[int, int]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to read PNG sizes.") from exc

    with Image.open(path) as image:
        return image.size


def quality_flags(
    bbox: Tuple[int, int, int, int],
    image_width: int,
    image_height: int,
    min_side: int,
    min_area_ratio: float,
) -> List[str]:
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    area_ratio = (width * height) / float(image_width * image_height) if image_width and image_height else 0
    flags = []
    if min(width, height) < min_side:
        flags.append("too_small")
    if area_ratio < min_area_ratio:
        flags.append("low_area_ratio")
    return flags


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--drawing-manifest", type=Path, default=DEFAULT_DRAWINGS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-panel-side", type=int, default=512)
    parser.add_argument("--min-area-ratio", type=float, default=0.01)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    label_rows = load_csv(args.labels)
    drawing_rows = load_csv(args.drawing_manifest)
    drawings = {row["drawing_key"]: row for row in drawing_rows}

    manifest_rows: List[Dict[str, object]] = []
    invalid_rows: List[Dict[str, object]] = []
    image_cache: Dict[str, Tuple[int, int]] = {}

    for row in label_rows:
        parent_key = row["parent_drawing_key"]
        drawing = drawings.get(parent_key, {})
        png_path = ROOT / row["png_path"]
        if not png_path.exists():
            out = dict(row)
            out["quality_flags"] = "missing_png"
            invalid_rows.append(out)
            continue
        if row["png_path"] not in image_cache:
            image_cache[row["png_path"]] = image_size(png_path)
        image_width, image_height = image_cache[row["png_path"]]
        raw_bbox = parse_bbox(row.get("panel_bbox_png", ""))
        if raw_bbox is None:
            out = dict(row)
            out["quality_flags"] = "invalid_bbox"
            invalid_rows.append(out)
            continue

        bbox = clamp_bbox(raw_bbox, image_width, image_height)
        flags = quality_flags(bbox, image_width, image_height, args.min_panel_side, args.min_area_ratio)
        panel_png_path = ""
        if not flags:
            rel_dir = Path(row.get("phase", drawing.get("phase", "unknown")))
            filename = f"{safe_slug(row['panel_id'])}.png"
            out_path = args.output_dir.resolve() / rel_dir / filename
            crop_panel(png_path, out_path, bbox)
            panel_png_path = out_path.relative_to(ROOT).as_posix()

        out_row: Dict[str, object] = {
            "panel_id": row["panel_id"],
            "parent_drawing_key": parent_key,
            "parent_drawing_id": row.get("drawing_id", drawing.get("drawing_id", "")),
            "parent_png_path": row["png_path"],
            "parent_raw_json_path": drawing.get("raw_json_path", ""),
            "panel_index": row.get("panel_index", ""),
            "panel_count": "",
            "split": row.get("split", drawing.get("split", "")),
            "phase": row.get("phase", drawing.get("phase", "")),
            "batch": row.get("batch", drawing.get("batch", "")),
            "split_method": "manual_topology_multipanel",
            "panel_bbox_png": fmt_bbox(bbox),
            "parent_png_width": image_width,
            "parent_png_height": image_height,
            "panel_png_width": bbox[2] - bbox[0],
            "panel_png_height": bbox[3] - bbox[1],
            "panel_area_ratio": round(((bbox[2] - bbox[0]) * (bbox[3] - bbox[1])) / float(image_width * image_height), 6),
            "panel_png_path": panel_png_path,
            "status": row.get("status", ""),
            "quality_flags": ";".join(flags),
            "usable_for_topology_panel_pilot": not flags and row.get("status", "") == "accept",
            "comment": row.get("comment", ""),
        }
        if flags:
            invalid_rows.append(out_row)
        manifest_rows.append(out_row)

    counts_by_parent = Counter(str(row["parent_drawing_key"]) for row in manifest_rows)
    for row in manifest_rows:
        row["panel_count"] = counts_by_parent[str(row["parent_drawing_key"])]

    fieldnames = list(manifest_rows[0].keys()) if manifest_rows else []
    usable_rows = [row for row in manifest_rows if row["usable_for_topology_panel_pilot"] is True]
    write_csv(INDEX_DIR / "topology_multipanel_manual_panel_manifest.csv", manifest_rows, fieldnames)
    write_csv(INDEX_DIR / "topology_multipanel_manual_panel_usable.csv", usable_rows, fieldnames)
    write_csv(INDEX_DIR / "topology_multipanel_manual_panel_invalid.csv", invalid_rows)
    write_summary(manifest_rows, usable_rows, invalid_rows)

    print(f"Manual panel rows: {len(manifest_rows)}")
    print(f"Usable panel rows: {len(usable_rows)}")
    print(f"Invalid/review rows: {len(invalid_rows)}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/topology_multipanel_manual_panel_manifest.csv")


def write_summary(
    manifest_rows: List[Dict[str, object]],
    usable_rows: List[Dict[str, object]],
    invalid_rows: List[Dict[str, object]],
) -> None:
    flag_counts: Counter[str] = Counter()
    for row in invalid_rows:
        flags = [flag for flag in str(row.get("quality_flags", "")).split(";") if flag]
        flag_counts.update(flags)
    summary = {
        "manual_panel_rows": len(manifest_rows),
        "usable_panel_rows": len(usable_rows),
        "invalid_or_review_rows": len(invalid_rows),
        "parent_drawing_count": len({row["parent_drawing_key"] for row in manifest_rows}),
        "usable_parent_drawing_count": len({row["parent_drawing_key"] for row in usable_rows}),
        "panel_rows_by_split": dict(Counter(str(row["split"]) for row in manifest_rows)),
        "usable_rows_by_split": dict(Counter(str(row["split"]) for row in usable_rows)),
        "invalid_quality_flags": dict(flag_counts),
        "rules": [
            "manual bbox rows with status=accept and no quality flags are usable for panel-level topology pilot",
            "too_small or low_area_ratio rows are retained for review but excluded from usable panel pilot",
            "this manifest is scoped to topology v1 multi-panel pages and does not replace final_panel_manifest.csv",
        ],
    }
    (INDEX_DIR / "topology_multipanel_manual_panel_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Topology Multi-Panel Manual Split Report",
        "",
        "This report summarizes manual PNG bbox splits for topology v1 multi-panel pages.",
        "",
        "## Summary",
        "",
        f"- Manual panel rows: {summary['manual_panel_rows']}",
        f"- Usable panel rows: {summary['usable_panel_rows']}",
        f"- Invalid/review rows: {summary['invalid_or_review_rows']}",
        f"- Parent drawing count: {summary['parent_drawing_count']}",
        f"- Usable parent drawing count: {summary['usable_parent_drawing_count']}",
        "",
        "## Invalid Quality Flags",
        "",
    ]
    if flag_counts:
        for flag, count in flag_counts.items():
            lines.append(f"- {flag}: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")
    (INDEX_DIR / "topology_multipanel_manual_panel_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
