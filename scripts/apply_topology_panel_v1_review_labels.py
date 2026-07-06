"""Apply manual panel-level Topology Graph v1 pilot review labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_pilot_manifest.csv"
DEFAULT_LABELS = INDEX_DIR / "topology_panel_v1_pilot_review_labels.csv"

LABELS = {
    "accept_v1",
    "over_connected",
    "still_fragmented",
    "needs_terminal_anchor",
    "bad_geometry",
}
ACCEPT_LABELS = {"accept_v1"}


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


def normalize_label(value: str) -> str:
    label = str(value or "").strip()
    return label if label in LABELS else ""


def build_label_map(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    labels: Dict[str, Dict[str, str]] = {}
    duplicates: Counter[str] = Counter()
    for row in rows:
        panel_id = row.get("panel_id", "")
        if not panel_id:
            continue
        if panel_id in labels:
            duplicates[panel_id] += 1
        labels[panel_id] = {
            "topology_panel_v1_review_label": normalize_label(row.get("review_label", "")),
            "topology_panel_v1_review_comment": str(row.get("comment", "") or "").strip(),
        }
    if duplicates:
        print(f"Warning: duplicate label rows: {sum(duplicates.values())}")
    return labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_rows = load_csv(args.manifest)
    label_rows = load_csv(args.labels)
    labels = build_label_map(label_rows)

    reviewed: List[Dict[str, object]] = []
    for row in manifest_rows:
        review = labels.get(
            row["panel_id"],
            {
                "topology_panel_v1_review_label": "",
                "topology_panel_v1_review_comment": "",
            },
        )
        label = str(review["topology_panel_v1_review_label"])
        out: Dict[str, object] = dict(row)
        out.update(review)
        out["topology_panel_v1_reviewed"] = bool(label)
        out["topology_panel_v1_accepted"] = label in ACCEPT_LABELS
        out["topology_panel_v1_exclude_reason"] = exclude_reason(label)
        reviewed.append(out)

    fieldnames = list(reviewed[0].keys()) if reviewed else []
    accepted = [row for row in reviewed if row.get("topology_panel_v1_accepted") is True]
    not_accepted = [
        row
        for row in reviewed
        if row.get("topology_panel_v1_reviewed") is True
        and row.get("topology_panel_v1_accepted") is not True
    ]
    unreviewed = [row for row in reviewed if row.get("topology_panel_v1_reviewed") is False]

    write_csv(INDEX_DIR / "topology_panel_v1_pilot_reviewed.csv", reviewed, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_pilot_accept.csv", accepted, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_pilot_not_accept.csv", not_accepted, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_pilot_unreviewed.csv", unreviewed, fieldnames)

    summary = build_summary(reviewed, label_rows, accepted, not_accepted, unreviewed)
    (INDEX_DIR / "topology_panel_v1_pilot_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)

    print(f"Pilot manifest rows: {summary['pilot_manifest_rows']}")
    print(f"Label rows: {summary['label_rows']}")
    print(f"Reviewed rows: {summary['reviewed_rows']}")
    print(f"Accepted rows: {summary['accepted_rows']}")
    print(f"Not accepted rows: {summary['not_accepted_rows']}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/topology_panel_v1_pilot_reviewed.csv")


def exclude_reason(label: str) -> str:
    if not label:
        return "unreviewed"
    if label in ACCEPT_LABELS:
        return ""
    return label


def build_summary(
    reviewed: List[Dict[str, object]],
    label_rows: List[Dict[str, str]],
    accepted: List[Dict[str, object]],
    not_accepted: List[Dict[str, object]],
    unreviewed: List[Dict[str, object]],
) -> Dict[str, object]:
    label_counts = Counter(
        str(row.get("topology_panel_v1_review_label", "")) or "unreviewed"
        for row in reviewed
    )
    exclude_counts = Counter(
        str(row.get("topology_panel_v1_exclude_reason", "")) or "keep"
        for row in reviewed
    )
    return {
        "pilot_manifest_rows": len(reviewed),
        "label_rows": len(label_rows),
        "reviewed_rows": sum(1 for row in reviewed if row.get("topology_panel_v1_reviewed") is True),
        "unreviewed_rows": len(unreviewed),
        "accepted_rows": len(accepted),
        "not_accepted_rows": len(not_accepted),
        "review_label_counts": dict(label_counts),
        "exclude_reason_counts": dict(exclude_counts),
        "accepted_by_phase": dict(Counter(str(row.get("phase", "")) for row in accepted)),
        "accepted_by_split": dict(Counter(str(row.get("split", "")) for row in accepted)),
        "rules": [
            "accept_v1 panels are accepted as panel-level Topology Graph v1 pilot positives",
            "over_connected, still_fragmented, needs_terminal_anchor, and bad_geometry remain reviewed but not accepted",
            "unreviewed rows are retained in the reviewed manifest and excluded from accept output",
        ],
    }


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1 Pilot Review Report",
        "",
        "This report summarizes manual labels exported from `topology_panel_v1_pilot_review.html`.",
        "",
        "## Summary",
        "",
        f"- Pilot manifest rows: {summary['pilot_manifest_rows']}",
        f"- Label rows: {summary['label_rows']}",
        f"- Reviewed rows: {summary['reviewed_rows']}",
        f"- Unreviewed rows: {summary['unreviewed_rows']}",
        f"- Accepted rows: {summary['accepted_rows']}",
        f"- Not accepted rows: {summary['not_accepted_rows']}",
        "",
        "## Review Label Counts",
        "",
    ]
    for label, count in summary["review_label_counts"].items():
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Exclude Reason Counts", ""])
    for reason, count in summary["exclude_reason_counts"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Accepted by Phase", ""])
    for phase, count in summary["accepted_by_phase"].items():
        lines.append(f"- {phase}: {count}")
    lines.extend(["", "## Accepted by Split", ""])
    for split, count in summary["accepted_by_split"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    (INDEX_DIR / "topology_panel_v1_pilot_review_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
