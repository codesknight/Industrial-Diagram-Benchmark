"""Scan dataset manifests for visible/source watermark signals.

The scanner uses deterministic metadata/text signals:
- filename/path keywords such as wm666.taobao.com
- TEXT/MTEXT contents in Raw Geometry JSON

It does not OCR rendered PNGs yet. Results are candidates for filtering or
manual review, not irreversible deletions.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "round2_clean_manifest.csv"

DEFAULT_KEYWORDS = [
    "wm666",
    "taobao",
    "淘宝",
    "星欣",
    "星欣设计",
    "星欣设计图库",
    "蚂蚁",
    "蚂蚁图库",
    "设计库",
    "图库",
    "素材库",
    "CAD图库",
    "cad图库",
]


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


def normalize(text: str) -> str:
    return text.lower().replace(" ", "")


def keyword_hits(text: str, keywords: List[str]) -> List[str]:
    folded = normalize(text)
    hits = []
    for keyword in keywords:
        if normalize(keyword) in folded:
            hits.append(keyword)
    return sorted(set(hits))


def extract_json_text(path: Path) -> Tuple[str, int, str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        entities = payload.get("entities", [])
        chunks = []
        text_count = 0
        if isinstance(entities, list):
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                if str(entity.get("type", "")).upper() not in {"TEXT", "MTEXT"}:
                    continue
                value = entity.get("content", entity.get("text", ""))
                if value:
                    chunks.append(str(value))
                    text_count += 1
        return "\n".join(chunks), text_count, ""
    except Exception as exc:  # noqa: BLE001
        return "", 0, f"json_error:{exc}"


def scan_row(row: Dict[str, str], keywords: List[str]) -> Dict[str, object]:
    metadata_text = " ".join(
        [
            row.get("drawing_key", ""),
            row.get("drawing_id", ""),
            row.get("dwg_path", ""),
            row.get("dxf_path", ""),
            row.get("raw_json_path", ""),
            row.get("png_path", ""),
        ]
    )
    meta_hits = keyword_hits(metadata_text, keywords)

    json_path = ROOT / row["raw_json_path"]
    text, text_count, error = extract_json_text(json_path)
    json_hits = keyword_hits(text, keywords)

    confidence = "none"
    if json_hits:
        confidence = "high"
    elif meta_hits:
        confidence = "medium"

    return {
        "drawing_key": row["drawing_key"],
        "drawing_id": row["drawing_id"],
        "phase": row["phase"],
        "batch": row["batch"],
        "split": row["split"],
        "watermark_candidate": bool(meta_hits or json_hits),
        "watermark_confidence": confidence,
        "metadata_hits": ";".join(meta_hits),
        "json_text_hits": ";".join(json_hits),
        "text_entity_count": text_count,
        "json_error": error,
        "raw_json_path": row["raw_json_path"],
        "png_path": row["png_path"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    scanned = [scan_row(row, args.keywords) for row in rows]
    candidates = [row for row in scanned if row["watermark_candidate"]]
    scan_by_key = {row["drawing_key"]: row for row in scanned}

    fieldnames = list(scanned[0].keys()) if scanned else []
    write_csv(INDEX_DIR / "watermark_scan.csv", scanned, fieldnames)
    write_csv(INDEX_DIR / "watermark_candidates.csv", candidates, fieldnames)
    write_filtered_manifests(rows, scan_by_key)

    confidence_counts = Counter(str(row["watermark_confidence"]) for row in scanned)
    keyword_counts: Counter[str] = Counter()
    for row in candidates:
        for field in ("metadata_hits", "json_text_hits"):
            for hit in str(row[field]).split(";"):
                if hit:
                    keyword_counts[hit] += 1

    summary = {
        "source_manifest": str(args.manifest).replace("\\", "/"),
        "total_rows": len(rows),
        "watermark_candidate_rows": len(candidates),
        "confidence_counts": dict(confidence_counts),
        "keyword_counts": dict(keyword_counts),
        "high_confidence_rows": sum(1 for row in scanned if row["watermark_confidence"] == "high"),
        "medium_confidence_rows": sum(1 for row in scanned if row["watermark_confidence"] == "medium"),
        "recommendation": {
            "high": "filter from clean training/evaluation or route to separate watermark split",
            "medium": "review; filename/source marker may not imply visible watermark in image",
        },
    }
    (INDEX_DIR / "watermark_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary, candidates)

    print(f"Rows scanned: {len(rows)}")
    print(f"Watermark candidates: {len(candidates)}")
    print(f"High confidence: {summary['high_confidence_rows']}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/watermark_candidates.csv")


def write_report(summary: Dict[str, object], candidates: List[Dict[str, object]]) -> None:
    lines = [
        "# Watermark Scan Report",
        "",
        "This report scans filenames/paths and Raw JSON text entities for watermark/source keywords.",
        "",
        "## Summary",
        "",
        f"- Total rows scanned: {summary['total_rows']}",
        f"- Watermark candidate rows: {summary['watermark_candidate_rows']}",
        f"- High confidence rows: {summary['high_confidence_rows']}",
        f"- Medium confidence rows: {summary['medium_confidence_rows']}",
        "",
        "## Recommendation",
        "",
        "- High confidence: filter from clean training/evaluation or place in a separate watermark split.",
        "- Medium confidence: review before filtering; filename/source marker may not be visibly rendered.",
        "- Do not delete raw files. Keep filtering manifest-based.",
        "",
        "## Keyword Counts",
        "",
    ]
    for keyword, count in summary["keyword_counts"].items():
        lines.append(f"- {keyword}: {count}")

    lines.extend(["", "## First Candidates", ""])
    if not candidates:
        lines.append("No candidates found.")
    else:
        lines.append("| drawing_key | confidence | metadata_hits | json_text_hits |")
        lines.append("|---|---|---|---|")
        for row in candidates[:80]:
            lines.append(
                f"| `{row['drawing_key']}` | {row['watermark_confidence']} | "
                f"{row['metadata_hits']} | {row['json_text_hits']} |"
            )

    (INDEX_DIR / "watermark_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_filtered_manifests(rows: List[Dict[str, str]], scan_by_key: Dict[str, Dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    no_high = [
        row
        for row in rows
        if scan_by_key[row["drawing_key"]]["watermark_confidence"] != "high"
    ]
    no_candidates = [
        row
        for row in rows
        if not scan_by_key[row["drawing_key"]]["watermark_candidate"]
    ]
    write_csv(INDEX_DIR / "round2_clean_no_high_watermark.csv", no_high, fieldnames)
    write_csv(INDEX_DIR / "round2_clean_no_watermark_candidates.csv", no_candidates, fieldnames)


if __name__ == "__main__":
    main()
