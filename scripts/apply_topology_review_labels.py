"""Apply manual topology review labels to topology manifests."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_TOPOLOGY = INDEX_DIR / "topology_graph_manifest.csv"
DEFAULT_LABELS = INDEX_DIR / "topology_review_labels.csv"

LABELS = {
    "accept_v0",
    "needs_intersection_split",
    "needs_terminal_anchor",
    "not_topology_target",
    "bad_geometry",
}
V1_LABELS = {"needs_intersection_split", "needs_terminal_anchor"}


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


def as_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def normalize_label(value: str) -> str:
    label = str(value).strip()
    return label if label in LABELS else ""


def label_map(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    labels: Dict[str, Dict[str, str]] = {}
    duplicates: Counter[str] = Counter()
    for row in rows:
        key = row.get("drawing_key", "")
        if not key:
            continue
        if key in labels:
            duplicates[key] += 1
        labels[key] = {
            "topology_review_label": normalize_label(row.get("review_label", "")),
            "topology_review_comment": row.get("comment", ""),
        }
    if duplicates:
        print(f"Warning: duplicate label rows: {sum(duplicates.values())}")
    return labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topology", type=Path, default=DEFAULT_TOPOLOGY)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    topology_rows = load_csv(args.topology)
    label_rows = load_csv(args.labels)
    labels = label_map(label_rows)

    reviewed: List[Dict[str, object]] = []
    for row in topology_rows:
        review = labels.get(
            row["drawing_key"],
            {"topology_review_label": "", "topology_review_comment": ""},
        )
        label = str(review["topology_review_label"])
        topology_ready = as_bool(row.get("topology_ready", ""))
        row_out: Dict[str, object] = dict(row)
        row_out.update(review)
        row_out["topology_reviewed"] = bool(label)
        row_out["topology_v0_accepted"] = label == "accept_v0"
        row_out["topology_v1_candidate"] = label in V1_LABELS
        row_out["topology_exclude_reason"] = exclude_reason(label, topology_ready)
        reviewed.append(row_out)

    fieldnames = list(reviewed[0].keys()) if reviewed else []
    write_csv(INDEX_DIR / "topology_manifest_reviewed.csv", reviewed, fieldnames)

    reviewed_ready = [
        row for row in reviewed
        if as_bool(str(row.get("topology_ready", "")))
        and row.get("topology_exclude_reason") == ""
    ]
    v1_candidates = [row for row in reviewed if row.get("topology_v1_candidate") is True]
    bad_geometry = [row for row in reviewed if row.get("topology_review_label") == "bad_geometry"]
    not_target = [row for row in reviewed if row.get("topology_review_label") == "not_topology_target"]
    accepted_v0 = [row for row in reviewed if row.get("topology_review_label") == "accept_v0"]

    write_csv(INDEX_DIR / "topology_ready_reviewed.csv", reviewed_ready, fieldnames)
    write_csv(INDEX_DIR / "topology_v1_pilot_candidates.csv", v1_candidates, fieldnames)
    write_csv(INDEX_DIR / "topology_bad_geometry_reviewed.csv", bad_geometry, fieldnames)
    write_csv(INDEX_DIR / "topology_not_target_reviewed.csv", not_target, fieldnames)
    write_csv(INDEX_DIR / "topology_v0_accept_reviewed.csv", accepted_v0, fieldnames)

    write_splits("topology_ready_reviewed", reviewed_ready, fieldnames)
    write_summary(reviewed, label_rows, reviewed_ready, v1_candidates, bad_geometry)

    print(f"Label rows: {len(label_rows)}")
    print(f"Reviewed topology rows: {len(reviewed)}")
    print(f"Reviewed ready rows: {len(reviewed_ready)}")
    print(f"V1 pilot candidates: {len(v1_candidates)}")
    print(f"Bad geometry rows: {len(bad_geometry)}")


def exclude_reason(label: str, topology_ready: bool) -> str:
    if not topology_ready:
        return "not_topology_ready"
    if label == "bad_geometry":
        return "bad_geometry"
    if label == "not_topology_target":
        return "not_topology_target"
    return ""


def write_splits(prefix: str, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    for split in ("train", "val", "test"):
        split_rows = [row for row in rows if row.get("split") == split]
        write_csv(INDEX_DIR / f"{prefix}_{split}.csv", split_rows, fieldnames)


def write_summary(
    reviewed: List[Dict[str, object]],
    label_rows: List[Dict[str, str]],
    reviewed_ready: List[Dict[str, object]],
    v1_candidates: List[Dict[str, object]],
    bad_geometry: List[Dict[str, object]],
) -> None:
    label_counts = Counter(str(row.get("topology_review_label", "")) or "unreviewed" for row in reviewed)
    exclude_counts = Counter(
        str(row.get("topology_exclude_reason", "")) or "keep"
        for row in reviewed
    )
    summary = {
        "topology_rows": len(reviewed),
        "label_rows": len(label_rows),
        "reviewed_rows": sum(1 for row in reviewed if row.get("topology_reviewed") is True),
        "unreviewed_rows": sum(1 for row in reviewed if row.get("topology_reviewed") is False),
        "review_label_counts": dict(label_counts),
        "exclude_reason_counts": dict(exclude_counts),
        "reviewed_ready_rows": len(reviewed_ready),
        "v1_pilot_candidate_rows": len(v1_candidates),
        "bad_geometry_rows": len(bad_geometry),
        "reviewed_ready_by_split": dict(Counter(str(row.get("split", "")) for row in reviewed_ready)),
        "v1_candidate_by_label": dict(Counter(str(row.get("topology_review_label", "")) for row in v1_candidates)),
        "rules": [
            "bad_geometry and not_topology_target are excluded from reviewed topology-ready rows",
            "not_topology_ready rows remain excluded even without a manual label",
            "needs_intersection_split and needs_terminal_anchor become v1 pilot candidates",
            "accept_v0 remains eligible for v0 topology benchmark baselines",
        ],
    }
    (INDEX_DIR / "topology_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Review Label Report",
        "",
        "This report summarizes manual labels exported from `topology_review.html`.",
        "",
        "## Summary",
        "",
        f"- Topology rows: {summary['topology_rows']}",
        f"- Label rows: {summary['label_rows']}",
        f"- Reviewed rows: {summary['reviewed_rows']}",
        f"- Unreviewed rows: {summary['unreviewed_rows']}",
        f"- Reviewed ready rows: {summary['reviewed_ready_rows']}",
        f"- V1 pilot candidate rows: {summary['v1_pilot_candidate_rows']}",
        f"- Bad geometry rows: {summary['bad_geometry_rows']}",
        "",
        "## Review Label Counts",
        "",
    ]
    for label, count in summary["review_label_counts"].items():
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Exclude Reason Counts", ""])
    for reason, count in summary["exclude_reason_counts"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## V1 Candidate Labels", ""])
    for label, count in summary["v1_candidate_by_label"].items():
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    (INDEX_DIR / "topology_review_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
