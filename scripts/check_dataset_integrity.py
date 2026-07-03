"""Check generated dataset manifest integrity."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data_index" / "dataset_manifest.csv"
SUMMARY = ROOT / "data_index" / "dataset_summary.json"


def load_rows() -> list[dict[str, str]]:
    if not MANIFEST.exists():
        raise SystemExit("Manifest not found. Run: python scripts/build_dataset_manifest.py")
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def as_bool(value: str) -> bool:
    return value.lower() == "true"


def main() -> None:
    rows = load_rows()
    total = len(rows)
    complete = sum(1 for row in rows if as_bool(row["complete_all"]))
    missing_png = [row for row in rows if not as_bool(row["has_png"])]
    missing_dxf = [row for row in rows if not as_bool(row["has_dxf"])]
    missing_json = [row for row in rows if not as_bool(row["has_raw_json"])]

    print(f"Rows: {total}")
    print(f"Complete DWG/DXF/JSON/PNG: {complete}")
    print(f"Missing DXF: {len(missing_dxf)}")
    print(f"Missing Raw JSON: {len(missing_json)}")
    print(f"Missing PNG: {len(missing_png)}")

    if SUMMARY.exists():
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        physical = summary.get("physical_file_counts", {})
        if physical:
            print("Physical file counts:")
            for label, count in physical.items():
                print(f"  {label}: {count}")
        print(f"Unique PNG used: {summary.get('unique_png_used', 'n/a')}")
        print(f"Rows using reused PNG paths: {summary.get('rows_with_reused_png', 'n/a')}")
        print("Split counts for complete samples:")
        for split, count in summary.get("by_split_complete_all", {}).items():
            print(f"  {split}: {count}")

    if missing_dxf or missing_json:
        raise SystemExit(2)
    if missing_png:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
