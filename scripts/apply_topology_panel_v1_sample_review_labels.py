"""Apply manual labels from the full Topology Panel v1 sample review."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_sample_review_manifest.csv"
DEFAULT_LABELS = INDEX_DIR / "topology_panel_v1_sample_review_labels.csv"

LABELS = {
    "accept_v1",
    "needs_panel_split",
    "over_connected",
    "still_fragmented",
    "needs_terminal_anchor",
    "not_topology_target",
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
            "model_review_label": row.get("model_review_label", ""),
            "model_confidence": row.get("model_confidence", ""),
            "model_needs_human_review": row.get("model_needs_human_review", ""),
            "model_reason": row.get("model_reason", ""),
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
                "model_review_label": row.get("model_review_label", ""),
                "model_confidence": row.get("model_confidence", ""),
                "model_needs_human_review": row.get("model_needs_human_review", ""),
                "model_reason": row.get("model_reason", ""),
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
    needs_panel_split = [row for row in reviewed if row.get("topology_panel_v1_review_label") == "needs_panel_split"]
    not_target = [row for row in reviewed if row.get("topology_panel_v1_review_label") == "not_topology_target"]
    bad_geometry = [row for row in reviewed if row.get("topology_panel_v1_review_label") == "bad_geometry"]
    other_not_accept = [
        row
        for row in reviewed
        if row.get("topology_panel_v1_reviewed") is True
        and row.get("topology_panel_v1_accepted") is not True
        and row.get("topology_panel_v1_review_label") not in {"needs_panel_split", "not_topology_target", "bad_geometry"}
    ]
    unreviewed = [row for row in reviewed if row.get("topology_panel_v1_reviewed") is False]

    write_csv(INDEX_DIR / "topology_panel_v1_sample_reviewed.csv", reviewed, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_sample_accept.csv", accepted, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_needs_panel_split.csv", needs_panel_split, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_not_target.csv", not_target, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_bad_geometry_reviewed.csv", bad_geometry, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_sample_other_not_accept.csv", other_not_accept, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_sample_unreviewed.csv", unreviewed, fieldnames)

    summary = build_summary(
        reviewed,
        label_rows,
        accepted,
        needs_panel_split,
        not_target,
        bad_geometry,
        other_not_accept,
        unreviewed,
    )
    (INDEX_DIR / "topology_panel_v1_sample_review_result_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)

    print(f"Sample manifest rows: {summary['sample_manifest_rows']}")
    print(f"Label rows: {summary['label_rows']}")
    print(f"Reviewed rows: {summary['reviewed_rows']}")
    print(f"Accepted rows: {summary['accepted_rows']}")
    print(f"Needs panel split rows: {summary['needs_panel_split_rows']}")
    print(f"Bad geometry rows: {summary['bad_geometry_rows']}")


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
    needs_panel_split: List[Dict[str, object]],
    not_target: List[Dict[str, object]],
    bad_geometry: List[Dict[str, object]],
    other_not_accept: List[Dict[str, object]],
    unreviewed: List[Dict[str, object]],
) -> Dict[str, object]:
    label_counts = Counter(
        str(row.get("topology_panel_v1_review_label", "")) or "unreviewed"
        for row in reviewed
    )
    model_counts = Counter(
        str(row.get("model_review_label", "")) or "missing"
        for row in reviewed
    )
    agreement_counts = Counter(model_agreement(row) for row in reviewed)
    return {
        "sample_manifest_rows": len(reviewed),
        "label_rows": len(label_rows),
        "reviewed_rows": sum(1 for row in reviewed if row.get("topology_panel_v1_reviewed") is True),
        "unreviewed_rows": len(unreviewed),
        "accepted_rows": len(accepted),
        "needs_panel_split_rows": len(needs_panel_split),
        "not_topology_target_rows": len(not_target),
        "bad_geometry_rows": len(bad_geometry),
        "other_not_accept_rows": len(other_not_accept),
        "review_label_counts": dict(label_counts),
        "model_label_counts": dict(model_counts),
        "model_agreement_counts": dict(agreement_counts),
        "needs_panel_split_by_split_method": dict(
            Counter(str(row.get("split_method", "")) for row in needs_panel_split)
        ),
        "needs_panel_split_by_phase": dict(Counter(str(row.get("phase", "")) for row in needs_panel_split)),
        "rules": [
            "accept_v1 rows remain eligible for panel-level Topology Graph v1 baseline",
            "needs_panel_split rows are multi-subfigure badcases under the current policy and are excluded from topology baseline",
            "bad_geometry and not_topology_target rows are excluded from topology baseline",
            "over_connected, still_fragmented, and needs_terminal_anchor remain v1 improvement targets",
        ],
    }


def model_agreement(row: Dict[str, object]) -> str:
    label = str(row.get("topology_panel_v1_review_label", ""))
    model = str(row.get("model_review_label", ""))
    if not label:
        return "unreviewed"
    if not model:
        return "no_model_label"
    return "agree" if label == model else "disagree"


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1 Sample Review Result Report",
        "",
        "This report summarizes manual labels exported from `topology_panel_v1_sample_review.html`.",
        "",
        "## Summary",
        "",
        f"- Sample manifest rows: {summary['sample_manifest_rows']}",
        f"- Label rows: {summary['label_rows']}",
        f"- Reviewed rows: {summary['reviewed_rows']}",
        f"- Unreviewed rows: {summary['unreviewed_rows']}",
        f"- Accepted rows: {summary['accepted_rows']}",
        f"- Needs panel split rows: {summary['needs_panel_split_rows']}",
        f"- Not topology target rows: {summary['not_topology_target_rows']}",
        f"- Bad geometry rows: {summary['bad_geometry_rows']}",
        f"- Other not accepted rows: {summary['other_not_accept_rows']}",
        "",
        "## Review Label Counts",
        "",
    ]
    for label, count in summary["review_label_counts"].items():
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Model Agreement Counts", ""])
    for status, count in summary["model_agreement_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Needs Panel Split by Split Method", ""])
    for method, count in summary["needs_panel_split_by_split_method"].items():
        lines.append(f"- {method}: {count}")
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    (INDEX_DIR / "topology_panel_v1_sample_review_result_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
