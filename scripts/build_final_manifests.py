"""Build final curated manifests from cleaning, review, and watermark outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"


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


def write_splits(prefix: str, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    for split in ("train", "val", "test"):
        split_rows = [row for row in rows if row.get("split") == split]
        write_csv(INDEX_DIR / f"{prefix}_{split}.csv", split_rows, fieldnames)


def add_final_columns(row: Dict[str, str], reason: str = "") -> Dict[str, object]:
    out: Dict[str, object] = dict(row)
    out["final_keep"] = not reason
    out["final_filter_reason"] = reason
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drawing-source", type=Path, default=INDEX_DIR / "round2_clean_manifest.csv")
    parser.add_argument("--panel-source", type=Path, default=INDEX_DIR / "panel_manifest_reviewed.csv")
    parser.add_argument("--watermark-candidates", type=Path, default=INDEX_DIR / "watermark_candidates.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    drawing_rows = load_csv(args.drawing_source)
    panel_rows = load_csv(args.panel_source)
    watermark_rows = load_csv(args.watermark_candidates)
    visible_watermark_keys = {row["drawing_key"] for row in watermark_rows}

    final_drawings = [
        add_final_columns(row)
        for row in drawing_rows
        if row["drawing_key"] not in visible_watermark_keys
    ]
    rejected_drawings = [
        add_final_columns(row, "visible_watermark")
        for row in drawing_rows
        if row["drawing_key"] in visible_watermark_keys
    ]

    final_panels: List[Dict[str, object]] = []
    rejected_panels: List[Dict[str, object]] = []
    for row in panel_rows:
        reason = ""
        if str(row.get("panel_usable", "")).lower() != "true":
            reason = "panel_review_reject"
        elif row["parent_drawing_key"] in visible_watermark_keys:
            reason = "parent_visible_watermark"

        out = add_final_columns(row, reason)
        if reason:
            rejected_panels.append(out)
        else:
            final_panels.append(out)

    drawing_fields = list(final_drawings[0].keys()) if final_drawings else list(drawing_rows[0].keys())
    panel_fields = list(final_panels[0].keys()) if final_panels else list(panel_rows[0].keys())
    rejected_drawing_fields = list(rejected_drawings[0].keys()) if rejected_drawings else drawing_fields
    rejected_panel_fields = list(rejected_panels[0].keys()) if rejected_panels else panel_fields

    write_csv(INDEX_DIR / "final_drawing_manifest.csv", final_drawings, drawing_fields)
    write_csv(INDEX_DIR / "final_rejected_drawings.csv", rejected_drawings, rejected_drawing_fields)
    write_splits("final_drawing", final_drawings, drawing_fields)

    write_csv(INDEX_DIR / "final_panel_manifest.csv", final_panels, panel_fields)
    write_csv(INDEX_DIR / "final_rejected_panels.csv", rejected_panels, rejected_panel_fields)
    write_splits("final_panel", final_panels, panel_fields)

    summary = {
        "drawing_source_rows": len(drawing_rows),
        "final_drawing_rows": len(final_drawings),
        "rejected_drawing_rows": len(rejected_drawings),
        "panel_source_rows": len(panel_rows),
        "final_panel_rows": len(final_panels),
        "rejected_panel_rows": len(rejected_panels),
        "visible_watermark_parent_rows": len(visible_watermark_keys),
        "final_drawing_by_split": dict(Counter(row["split"] for row in final_drawings)),
        "final_panel_by_split": dict(Counter(row["split"] for row in final_panels)),
        "rejected_panel_by_reason": dict(Counter(str(row["final_filter_reason"]) for row in rejected_panels)),
        "rules": [
            "drawing source: round2 clean manifest",
            "drop drawing rows with visible watermark candidates",
            "panel source: panel manifest with manual review labels",
            "drop panels rejected by manual review",
            "drop panels whose parent drawing has visible watermark candidate",
            "source marker filenames are not filtered",
        ],
    }
    (INDEX_DIR / "final_manifest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)

    print(f"Final drawings: {summary['final_drawing_rows']}")
    print(f"Final panels: {summary['final_panel_rows']}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/final_drawing_manifest.csv")


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Final Manifest Report",
        "",
        "This report summarizes the curated dataset entry points after cleaning, manual panel review, and visible watermark filtering.",
        "",
        "## Summary",
        "",
        f"- Drawing source rows: {summary['drawing_source_rows']}",
        f"- Final drawing rows: {summary['final_drawing_rows']}",
        f"- Rejected drawing rows: {summary['rejected_drawing_rows']}",
        f"- Panel source rows: {summary['panel_source_rows']}",
        f"- Final panel rows: {summary['final_panel_rows']}",
        f"- Rejected panel rows: {summary['rejected_panel_rows']}",
        f"- Visible watermark parent rows: {summary['visible_watermark_parent_rows']}",
        "",
        "## Final Drawing Splits",
        "",
    ]
    for split, count in summary["final_drawing_by_split"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Final Panel Splits", ""])
    for split, count in summary["final_panel_by_split"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Rejected Panel Reasons", ""])
    for reason, count in summary["rejected_panel_by_reason"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    (INDEX_DIR / "final_manifest_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
