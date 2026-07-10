"""Build tiled image-input benchmark records for Topology Panel v1."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
OUTPUT_ROOT = ROOT / "outputs" / "topology_panel_v1_tiles"

DEFAULT_BENCHMARK = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_tile2x2_benchmark_manifest.jsonl"
DEFAULT_CSV = INDEX_DIR / "topology_panel_v1_tile2x2_benchmark_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_tile2x2_benchmark_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_tile2x2_benchmark_report.md"


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def safe_stem(panel_id: str) -> str:
    cleaned = panel_id.replace("\\", "_").replace("/", "_").replace("#", "__")
    cleaned = "".join(ch if ch.isalnum() or ch in "._-()" else "_" for ch in cleaned)
    return cleaned[:180]


def tile_boxes(width: int, height: int, rows: int, cols: int, overlap: float) -> List[Tuple[int, int, int, int, int, int]]:
    boxes: List[Tuple[int, int, int, int, int, int]] = []
    tile_w = width / cols
    tile_h = height / rows
    pad_x = tile_w * overlap / 2.0
    pad_y = tile_h * overlap / 2.0
    for r in range(rows):
        for c in range(cols):
            left = int(max(0, c * tile_w - pad_x))
            upper = int(max(0, r * tile_h - pad_y))
            right = int(min(width, (c + 1) * tile_w + pad_x))
            lower = int(min(height, (r + 1) * tile_h + pad_y))
            boxes.append((r, c, left, upper, right, lower))
    return boxes


def build_tiles(args: argparse.Namespace) -> List[Dict[str, object]]:
    records = load_jsonl(args.benchmark)
    tile_records: List[Dict[str, object]] = []
    image_output_dir = args.tile_root / args.tile_set_id
    image_output_dir.mkdir(parents=True, exist_ok=True)

    for record in records:
        panel_id = str(record.get("panel_id", ""))
        image_info = record.get("input", {})
        image_path_value = image_info.get("image_path", "") if isinstance(image_info, dict) else ""
        image_path = ROOT / str(image_path_value)
        if not image_path.exists():
            continue
        with Image.open(image_path) as image:
            rgb = image.convert("RGB")
            width, height = rgb.size
            for row, col, left, upper, right, lower in tile_boxes(width, height, args.rows, args.cols, args.overlap):
                tile_id = f"r{row}c{col}"
                tile_path = image_output_dir / f"{safe_stem(panel_id)}__{tile_id}.png"
                if args.force or not tile_path.exists():
                    rgb.crop((left, upper, right, lower)).save(tile_path, format="PNG", optimize=True)

                tile_record = dict(record)
                tile_record["panel_id"] = f"{panel_id}#tile_{tile_id}"
                tile_record["task"] = "panel_topology_graph_v1_tile_input"
                tile_record["input"] = {
                    "image_path": rel(tile_path),
                    "image_exists": True,
                    "source_image_path": str(image_path_value),
                    "source_panel_id": panel_id,
                    "tile_set_id": args.tile_set_id,
                    "tile_id": tile_id,
                    "tile_row": row,
                    "tile_col": col,
                    "tile_rows": args.rows,
                    "tile_cols": args.cols,
                    "tile_bbox_xyxy": [left, upper, right, lower],
                    "source_size": [width, height],
                    "overlap": args.overlap,
                }
                tile_record["evaluation"] = {
                    "use_for_panel_score": False,
                    "aggregation_required": True,
                    "aggregation_key": panel_id,
                }
                tile_records.append(tile_record)
    return tile_records


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    fields = [
        "tile_panel_id",
        "source_panel_id",
        "tile_id",
        "tile_row",
        "tile_col",
        "image_path",
        "source_image_path",
        "tile_bbox_xyxy",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            input_info = row.get("input", {})
            if not isinstance(input_info, dict):
                input_info = {}
            writer.writerow(
                {
                    "tile_panel_id": row.get("panel_id", ""),
                    "source_panel_id": input_info.get("source_panel_id", ""),
                    "tile_id": input_info.get("tile_id", ""),
                    "tile_row": input_info.get("tile_row", ""),
                    "tile_col": input_info.get("tile_col", ""),
                    "image_path": input_info.get("image_path", ""),
                    "source_image_path": input_info.get("source_image_path", ""),
                    "tile_bbox_xyxy": json.dumps(input_info.get("tile_bbox_xyxy", []), ensure_ascii=False),
                }
            )


def write_summary(args: argparse.Namespace, rows: List[Dict[str, object]]) -> None:
    source_panels = sorted({str(row.get("input", {}).get("source_panel_id", "")) for row in rows if isinstance(row.get("input"), dict)})
    summary = {
        "tile_set_id": args.tile_set_id,
        "source_benchmark": rel(args.benchmark),
        "tile_records": len(rows),
        "source_panels": len(source_panels),
        "rows": args.rows,
        "cols": args.cols,
        "overlap": args.overlap,
        "output_jsonl": rel(args.output),
        "output_csv": rel(args.csv),
        "tile_root": rel(args.tile_root / args.tile_set_id),
        "aggregation_note": "Tile predictions are not evaluated directly; aggregate back to panel-level predictions first.",
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(args: argparse.Namespace, rows: List[Dict[str, object]]) -> None:
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    lines = [
        "# Topology Panel v1 Tile2x2 Benchmark Report",
        "",
        f"Tile set id: `{summary['tile_set_id']}`",
        "",
        "## Summary",
        "",
        f"- Source benchmark: `{summary['source_benchmark']}`",
        f"- Source panels: {summary['source_panels']}",
        f"- Tile records: {summary['tile_records']}",
        f"- Grid: {summary['rows']}x{summary['cols']}",
        f"- Overlap: {summary['overlap']}",
        f"- Tile root: `{summary['tile_root']}`",
        "",
        "Tile records are intended for model input only. They should be aggregated back to panel-level predictions before running the official evaluator.",
        "",
        "## Outputs",
        "",
        f"- JSONL: `{summary['output_jsonl']}`",
        f"- CSV: `{summary['output_csv']}`",
        f"- Summary: `{rel(args.summary)}`",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--tile-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--tile-set-id", default="tile2x2_v1")
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--overlap", type=float, default=0.0)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_tiles(args)
    write_jsonl(args.output, rows)
    write_csv(args.csv, rows)
    write_summary(args, rows)
    write_report(args, rows)
    print(f"Tile records: {len(rows)}")
    print(f"Wrote: {rel(args.output)}")
    print(f"Wrote: {rel(args.csv)}")
    print(f"Wrote: {rel(args.summary)}")
    print(f"Wrote: {rel(args.report)}")


if __name__ == "__main__":
    main()
