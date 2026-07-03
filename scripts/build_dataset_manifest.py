"""Build dataset manifest, split files, and integrity reports.

The script is intentionally dependency-free so it can run on a fresh machine.
It aligns DWG, DXF, raw JSON, and rendered PNG files by staged drawing keys.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
DWG_ROOT = ROOT / "datas" / "dwg_staging"
DXF_ROOT = ROOT / "datas" / "dxf_staging"
JSON_ROOT = ROOT / "datas" / "raw_json"
PNG_ROOT = ROOT / "datas" / "qa_and_png"
OUT_DIR = ROOT / "data_index"

SOURCE_TO_PNG_PHASE = {
    "_P1_staging": "P1_oda_output",
    "_P2_staging": "P2_oda_output",
    "_P3_staging_batch1": "P3_oda_output",
    "_P3_staging_batch2": "P3_oda_output",
    "_P3_staging_batch3": "P3_oda_output",
    "_P3_staging_batch4": "P3_oda_output",
}


def norm_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def key_without_ext(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return rel.with_suffix("").as_posix()


def collect_by_key(root: Path, suffix: str) -> Dict[str, Path]:
    items: Dict[str, Path] = {}
    if not root.exists():
        return items
    for path in root.rglob(f"*{suffix}"):
        if path.is_file():
            items[key_without_ext(path, root)] = path
    return items


def phase_from_key(key: str) -> str:
    first = key.split("/", 1)[0]
    if first == "_P1_staging":
        return "P1"
    if first == "_P2_staging":
        return "P2"
    if first.startswith("_P3_staging"):
        return "P3"
    return "unknown"


def batch_from_key(key: str) -> str:
    return key.split("/", 1)[0]


def drawing_id_from_key(key: str) -> str:
    return key.rsplit("/", 1)[-1]


def build_png_index() -> Dict[str, List[Path]]:
    """Index PNG files by (png phase dir, filename stem)."""
    index: Dict[str, List[Path]] = defaultdict(list)
    if not PNG_ROOT.exists():
        return index
    for path in PNG_ROOT.rglob("*.png"):
        if not path.is_file():
            continue
        rel = path.relative_to(PNG_ROOT)
        phase_dir = rel.parts[0] if len(rel.parts) > 1 else ""
        index[f"{phase_dir}/{path.stem}"].append(path)
    return index


def match_png(key: str, png_index: Dict[str, List[Path]]) -> tuple[Optional[Path], int]:
    stage = batch_from_key(key)
    png_phase = SOURCE_TO_PNG_PHASE.get(stage)
    if not png_phase:
        return None, 0
    lookup = f"{png_phase}/{drawing_id_from_key(key)}"
    matches = png_index.get(lookup, [])
    if len(matches) == 1:
        return matches[0], 1
    if len(matches) > 1:
        return matches[0], len(matches)
    return None, 0


def stable_bucket(key: str, seed: int) -> float:
    digest = hashlib.sha1(f"{seed}:{key}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(0xFFFFFFFFFFFF)


def choose_split(key: str, seed: int, train: float, val: float) -> str:
    bucket = stable_bucket(key, seed)
    if bucket < train:
        return "train"
    if bucket < train + val:
        return "val"
    return "test"


def inspect_json(path: Optional[Path]) -> Dict[str, object]:
    if not path:
        return {
            "entity_count": "",
            "text_count": "",
            "line_count": "",
            "insert_count": "",
            "json_valid": "",
        }
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        entities = payload.get("entities", [])
        counts = Counter(entity.get("type", "") for entity in entities if isinstance(entity, dict))
        return {
            "entity_count": len(entities),
            "text_count": counts.get("TEXT", 0) + counts.get("MTEXT", 0),
            "line_count": counts.get("LINE", 0) + counts.get("LWPOLYLINE", 0),
            "insert_count": counts.get("INSERT", 0),
            "json_valid": True,
        }
    except Exception as exc:  # noqa: BLE001 - report exact parse failure.
        return {
            "entity_count": "",
            "text_count": "",
            "line_count": "",
            "insert_count": "",
            "json_valid": False,
            "json_error": str(exc),
        }


def rel_or_empty(path: Optional[Path]) -> str:
    if not path:
        return ""
    return path.relative_to(ROOT).as_posix()


def build_rows(args: argparse.Namespace) -> List[Dict[str, object]]:
    dwgs = collect_by_key(DWG_ROOT, ".dwg")
    dxfs = collect_by_key(DXF_ROOT, ".dxf")
    jsons = collect_by_key(JSON_ROOT, ".json")
    png_index = build_png_index()

    keys = sorted(set(dwgs) | set(dxfs) | set(jsons))
    rows: List[Dict[str, object]] = []

    for key in keys:
        dwg_path = dwgs.get(key)
        dxf_path = dxfs.get(key)
        json_path = jsons.get(key)
        png_path, png_match_count = match_png(key, png_index)
        split = choose_split(key, args.seed, args.train, args.val)
        row: Dict[str, object] = {
            "drawing_key": key,
            "drawing_id": drawing_id_from_key(key),
            "phase": phase_from_key(key),
            "batch": batch_from_key(key),
            "split": split,
            "dwg_path": rel_or_empty(dwg_path),
            "dxf_path": rel_or_empty(dxf_path),
            "raw_json_path": rel_or_empty(json_path),
            "png_path": rel_or_empty(png_path),
            "has_dwg": bool(dwg_path),
            "has_dxf": bool(dxf_path),
            "has_raw_json": bool(json_path),
            "has_png": bool(png_path),
            "png_match_count": png_match_count,
            "png_reuse_group_size": 0,
            "complete_cad_triplet": bool(dwg_path and dxf_path and json_path),
            "complete_all": bool(dwg_path and dxf_path and json_path and png_path),
        }
        if args.inspect_json:
            row.update(inspect_json(json_path))
        rows.append(row)

    png_usage = Counter(row["png_path"] for row in rows if row["png_path"])
    for row in rows:
        if row["png_path"]:
            row["png_reuse_group_size"] = png_usage[row["png_path"]]
    return rows


def write_csv(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_splits(rows: List[Dict[str, object]]) -> None:
    for split in ("train", "val", "test"):
        split_rows = [row for row in rows if row["split"] == split and row["complete_all"]]
        write_csv(OUT_DIR / f"{split}.csv", split_rows)


def summarize(rows: List[Dict[str, object]]) -> Dict[str, object]:
    physical_counts = {
        "dwg": len(list(DWG_ROOT.rglob("*.dwg"))) if DWG_ROOT.exists() else 0,
        "dxf": len(list(DXF_ROOT.rglob("*.dxf"))) if DXF_ROOT.exists() else 0,
        "raw_json": len(list(JSON_ROOT.rglob("*.json"))) if JSON_ROOT.exists() else 0,
        "png": len(list(PNG_ROOT.rglob("*.png"))) if PNG_ROOT.exists() else 0,
    }
    used_pngs = [row["png_path"] for row in rows if row["png_path"]]
    png_usage = Counter(used_pngs)
    summary = {
        "total_rows": len(rows),
        "physical_file_counts": physical_counts,
        "complete_all": sum(1 for row in rows if row["complete_all"]),
        "complete_cad_triplet": sum(1 for row in rows if row["complete_cad_triplet"]),
        "missing_dwg": sum(1 for row in rows if not row["has_dwg"]),
        "missing_dxf": sum(1 for row in rows if not row["has_dxf"]),
        "missing_raw_json": sum(1 for row in rows if not row["has_raw_json"]),
        "missing_png": sum(1 for row in rows if not row["has_png"]),
        "unique_png_used": len(png_usage),
        "unused_physical_png": physical_counts["png"] - len(png_usage),
        "rows_with_reused_png": sum(1 for row in rows if row["png_reuse_group_size"] > 1),
        "png_reuse_groups": sum(1 for count in png_usage.values() if count > 1),
        "by_phase": Counter(row["phase"] for row in rows),
        "complete_by_phase": Counter(row["phase"] for row in rows if row["complete_all"]),
        "by_split_complete_all": Counter(row["split"] for row in rows if row["complete_all"]),
    }
    return json.loads(json.dumps(summary, ensure_ascii=False))


def write_missing_report(rows: List[Dict[str, object]], summary: Dict[str, object]) -> None:
    lines = [
        "# Dataset Missing Assets Report",
        "",
        "## Summary",
        "",
        f"- Total indexed drawings: {summary['total_rows']}",
        f"- Complete DWG/DXF/JSON/PNG samples: {summary['complete_all']}",
        f"- Physical PNG files: {summary['physical_file_counts']['png']}",
        f"- Unique PNG files used by manifest: {summary['unique_png_used']}",
        f"- Rows using a reused PNG path: {summary['rows_with_reused_png']}",
        f"- PNG reuse groups: {summary['png_reuse_groups']}",
        f"- Missing DWG: {summary['missing_dwg']}",
        f"- Missing DXF: {summary['missing_dxf']}",
        f"- Missing Raw JSON: {summary['missing_raw_json']}",
        f"- Missing PNG: {summary['missing_png']}",
        "",
        "## Missing Items",
        "",
    ]

    missing_rows = [
        row
        for row in rows
        if not (row["has_dwg"] and row["has_dxf"] and row["has_raw_json"] and row["has_png"])
    ]
    if not missing_rows:
        lines.append("No missing assets found.")
    else:
        lines.append("| drawing_key | missing |")
        lines.append("|---|---|")
        for row in missing_rows:
            missing = []
            for label, field in (
                ("DWG", "has_dwg"),
                ("DXF", "has_dxf"),
                ("JSON", "has_raw_json"),
                ("PNG", "has_png"),
            ):
                if not row[field]:
                    missing.append(label)
            lines.append(f"| `{row['drawing_key']}` | {', '.join(missing)} |")

    (OUT_DIR / "missing_assets.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_png_reuse_report(rows: List[Dict[str, object]]) -> None:
    groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["png_path"]:
            groups[str(row["png_path"])].append(row)

    reused = {path: group for path, group in groups.items() if len(group) > 1}
    lines = [
        "# PNG Reuse Report",
        "",
        "This report lists PNG files matched to more than one manifest row.",
        "Most cases come from P3 batch directories being rendered into a single `P3_oda_output` folder.",
        "",
        f"- Reused PNG groups: {len(reused)}",
        f"- Rows involved: {sum(len(group) for group in reused.values())}",
        "",
    ]

    if not reused:
        lines.append("No reused PNG paths found.")
    else:
        for png_path, group in sorted(reused.items()):
            lines.append(f"## `{png_path}`")
            lines.append("")
            for row in sorted(group, key=lambda item: str(item["drawing_key"])):
                lines.append(f"- `{row['drawing_key']}`")
            lines.append("")

    (OUT_DIR / "png_reuse_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-json", action="store_true", help="Parse every raw JSON and add entity counts.")
    parser.add_argument("--seed", type=int, default=20260703)
    parser.add_argument("--train", type=float, default=0.8)
    parser.add_argument("--val", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.train <= 0 or args.val < 0 or args.train + args.val >= 1:
        raise SystemExit("--train and --val must leave a positive test split.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows(args)
    write_csv(OUT_DIR / "dataset_manifest.csv", rows)
    write_splits(rows)
    summary = summarize(rows)
    (OUT_DIR / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_missing_report(rows, summary)
    write_png_reuse_report(rows)

    print(f"Indexed drawings: {summary['total_rows']}")
    print(f"Complete samples: {summary['complete_all']}")
    print(f"Missing PNG: {summary['missing_png']}")
    print(f"Wrote: {OUT_DIR.relative_to(ROOT).as_posix()}/dataset_manifest.csv")


if __name__ == "__main__":
    main()
