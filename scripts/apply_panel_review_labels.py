"""Apply exported panel review labels to panel manifest.

The exported CSV comes from data_index/panel_review.html. This script joins the
labels back to panel_manifest.csv and writes review-aware indexes.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "panel_manifest.csv"
DEFAULT_LABELS = INDEX_DIR / "panel_review_labels.csv"


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    panels = load_csv(args.manifest)
    labels = load_csv(args.labels)
    label_by_id = {row["panel_id"]: row for row in labels}

    joined: List[Dict[str, object]] = []
    for row in panels:
        label = label_by_id.get(row["panel_id"], {})
        status = (label.get("status") or "").strip()
        comment = (label.get("comment") or "").strip()
        out = dict(row)
        out["review_status"] = status
        out["review_comment"] = comment
        out["reviewed"] = bool(status)
        out["panel_usable"] = status in {"accept", "adjust"} or (not row.get("needs_review", "").lower() == "true")
        joined.append(out)

    fieldnames = list(joined[0].keys()) if joined else []
    write_csv(INDEX_DIR / "panel_manifest_reviewed.csv", joined, fieldnames)
    usable = [row for row in joined if str(row["panel_usable"]).lower() == "true"]
    write_csv(INDEX_DIR / "panel_manifest_usable.csv", usable, fieldnames)

    summary = {
        "panel_rows": len(panels),
        "label_rows": len(labels),
        "matched_label_rows": sum(1 for row in panels if row["panel_id"] in label_by_id),
        "status_counts": dict(Counter((row.get("status") or "unlabeled").strip() or "unlabeled" for row in labels)),
        "usable_panel_rows": len(usable),
        "rejected_panel_rows": sum(1 for row in joined if row.get("review_status") == "reject"),
        "unlabeled_review_rows": sum(
            1
            for row in joined
            if row.get("needs_review", "").lower() == "true" and not row.get("review_status")
        ),
    }
    (INDEX_DIR / "panel_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Panel rows: {summary['panel_rows']}")
    print(f"Label rows: {summary['label_rows']}")
    print(f"Usable panel rows: {summary['usable_panel_rows']}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/panel_manifest_reviewed.csv")


if __name__ == "__main__":
    main()
