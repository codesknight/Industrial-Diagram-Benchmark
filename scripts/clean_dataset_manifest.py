"""Build a non-destructive cleaned dataset manifest.

Cleaning rules:
1. Keep only samples with DWG, DXF, raw JSON, and PNG.
2. Optionally validate raw JSON files and reject invalid JSON.
3. For rows sharing the same PNG path, keep one deterministic representative.

The script never deletes or moves raw assets. It only writes cleaned indexes.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "dataset_manifest.csv"

BATCH_ORDER = {
    "_P1_staging": 10,
    "_P2_staging": 20,
    "_P3_staging_batch1": 31,
    "_P3_staging_batch2": 32,
    "_P3_staging_batch3": 33,
    "_P3_staging_batch4": 34,
}


def as_bool(value: object) -> bool:
    return str(value).lower() == "true"


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}. Run scripts/build_dataset_manifest.py first.")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_json(row: Dict[str, str]) -> Tuple[bool, str]:
    rel_path = row.get("raw_json_path", "")
    if not rel_path:
        return False, "missing_raw_json_path"
    path = ROOT / rel_path
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict):
            return False, "json_root_not_object"
        if "entities" not in payload:
            return False, "json_missing_entities"
        if not isinstance(payload["entities"], list):
            return False, "json_entities_not_list"
    except Exception as exc:  # noqa: BLE001 - write exact reason to rejected CSV.
        return False, f"json_error:{exc}"
    return True, ""


def representative_key(row: Dict[str, str]) -> tuple[int, str]:
    return (BATCH_ORDER.get(row.get("batch", ""), 999), row.get("drawing_key", ""))


def add_rejected(
    rejected: List[Dict[str, object]],
    row: Dict[str, str],
    reason: str,
    detail: str = "",
) -> None:
    rejected.append(
        {
            "drawing_key": row.get("drawing_key", ""),
            "drawing_id": row.get("drawing_id", ""),
            "phase": row.get("phase", ""),
            "batch": row.get("batch", ""),
            "split": row.get("split", ""),
            "reason": reason,
            "detail": detail,
            "dwg_path": row.get("dwg_path", ""),
            "dxf_path": row.get("dxf_path", ""),
            "raw_json_path": row.get("raw_json_path", ""),
            "png_path": row.get("png_path", ""),
        }
    )


def clean_rows(args: argparse.Namespace, rows: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], List[Dict[str, object]], Dict[str, object]]:
    rejected: List[Dict[str, object]] = []
    candidates: List[Dict[str, str]] = []

    for row in rows:
        if not as_bool(row.get("complete_all")):
            missing = []
            for label, field in (
                ("DWG", "has_dwg"),
                ("DXF", "has_dxf"),
                ("JSON", "has_raw_json"),
                ("PNG", "has_png"),
            ):
                if not as_bool(row.get(field)):
                    missing.append(label)
            add_rejected(rejected, row, "missing_assets", ",".join(missing))
            continue

        if args.validate_json:
            ok, detail = validate_json(row)
            if not ok:
                add_rejected(rejected, row, "invalid_raw_json", detail)
                continue

        candidates.append(row)

    by_png: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in candidates:
        by_png[row["png_path"]].append(row)

    clean: List[Dict[str, str]] = []
    duplicate_groups = 0
    duplicate_rejected = 0

    for png_path, group in sorted(by_png.items()):
        if len(group) == 1:
            clean.append(group[0])
            continue
        duplicate_groups += 1
        chosen = sorted(group, key=representative_key)[0]
        clean.append(chosen)
        for row in sorted(group, key=representative_key)[1:]:
            duplicate_rejected += 1
            add_rejected(
                rejected,
                row,
                "duplicate_png",
                f"kept={chosen['drawing_key']}; png={png_path}",
            )

    clean = sorted(clean, key=lambda row: row["drawing_key"])
    split_counts = Counter(row["split"] for row in clean)
    phase_counts = Counter(row["phase"] for row in clean)
    reject_counts = Counter(row["reason"] for row in rejected)

    summary = {
        "source_manifest": str(args.manifest).replace("\\", "/"),
        "total_rows": len(rows),
        "candidate_rows_after_asset_checks": len(candidates),
        "clean_rows": len(clean),
        "rejected_rows": len(rejected),
        "duplicate_png_groups": duplicate_groups,
        "duplicate_png_rows_rejected": duplicate_rejected,
        "validate_json": args.validate_json,
        "clean_by_split": dict(split_counts),
        "clean_by_phase": dict(phase_counts),
        "rejected_by_reason": dict(reject_counts),
        "rules": [
            "require complete DWG/DXF/raw JSON/PNG",
            "validate raw JSON object with entities list" if args.validate_json else "skip raw JSON validation",
            "deduplicate rows sharing the same PNG path",
            "choose duplicate representative by batch priority then drawing_key",
        ],
    }
    return clean, rejected, summary


def write_split_files(clean: List[Dict[str, str]], fieldnames: List[str]) -> None:
    for split in ("train", "val", "test"):
        rows = [row for row in clean if row.get("split") == split]
        write_csv(INDEX_DIR / f"clean_{split}.csv", rows, fieldnames)


def write_report(summary: Dict[str, object], rejected: List[Dict[str, object]]) -> None:
    lines = [
        "# Clean Dataset Report",
        "",
        "This is a non-destructive cleaning report. Raw files are not deleted or moved.",
        "",
        "## Summary",
        "",
        f"- Total manifest rows: {summary['total_rows']}",
        f"- Candidate rows after asset checks: {summary['candidate_rows_after_asset_checks']}",
        f"- Clean rows: {summary['clean_rows']}",
        f"- Rejected rows: {summary['rejected_rows']}",
        f"- Duplicate PNG groups: {summary['duplicate_png_groups']}",
        f"- Duplicate PNG rows rejected: {summary['duplicate_png_rows_rejected']}",
        f"- Raw JSON validation: {summary['validate_json']}",
        "",
        "## Clean Splits",
        "",
    ]
    for split, count in summary["clean_by_split"].items():
        lines.append(f"- {split}: {count}")

    lines.extend(["", "## Rejected Reasons", ""])
    for reason, count in summary["rejected_by_reason"].items():
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "## First Rejected Samples", ""])
    if not rejected:
        lines.append("No rejected samples.")
    else:
        lines.append("| drawing_key | reason | detail |")
        lines.append("|---|---|---|")
        for row in rejected[:50]:
            detail = str(row.get("detail", "")).replace("|", "\\|")
            lines.append(f"| `{row['drawing_key']}` | {row['reason']} | {detail} |")

    (INDEX_DIR / "clean_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--skip-json-validation", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.manifest = args.manifest.resolve()
    args.validate_json = not args.skip_json_validation

    rows = load_rows(args.manifest)
    clean, rejected, summary = clean_rows(args, rows)
    fieldnames = list(rows[0].keys()) if rows else []
    rejected_fields = [
        "drawing_key",
        "drawing_id",
        "phase",
        "batch",
        "split",
        "reason",
        "detail",
        "dwg_path",
        "dxf_path",
        "raw_json_path",
        "png_path",
    ]

    write_csv(INDEX_DIR / "clean_dataset_manifest.csv", clean, fieldnames)
    write_split_files(clean, fieldnames)
    write_csv(INDEX_DIR / "rejected_samples.csv", rejected, rejected_fields)
    (INDEX_DIR / "clean_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary, rejected)

    print(f"Clean rows: {summary['clean_rows']}")
    print(f"Rejected rows: {summary['rejected_rows']}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/clean_dataset_manifest.csv")


if __name__ == "__main__":
    main()
