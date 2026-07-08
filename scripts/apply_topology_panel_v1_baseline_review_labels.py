"""Apply final clean-baseline review labels for Topology Panel v1."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_baseline_review_manifest.csv"
DEFAULT_LABELS = INDEX_DIR / "topology_panel_v1_baseline_review_labels.csv"
DEFAULT_REVIEWED = INDEX_DIR / "topology_panel_v1_baseline_reviewed.csv"
DEFAULT_FINAL = INDEX_DIR / "topology_panel_v1_final_baseline_manifest.csv"
DEFAULT_RECHECK = INDEX_DIR / "topology_panel_v1_baseline_needs_recheck.csv"
DEFAULT_REMOVED = INDEX_DIR / "topology_panel_v1_baseline_removed.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_final_baseline_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_final_baseline_report.md"

VALID_LABELS = {"confirmed_baseline", "needs_recheck", "remove_from_baseline"}


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
    if not label:
        return "confirmed_baseline"
    if label not in VALID_LABELS:
        raise SystemExit(f"Unknown baseline review label: {label}")
    return label


def load_labels(path: Path, default_confirmed: bool) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        if default_confirmed:
            return {}
        raise SystemExit(f"Missing labels CSV: {path}")
    labels: Dict[str, Dict[str, str]] = {}
    for row in load_csv(path):
        panel_id = str(row.get("panel_id", "")).strip()
        if not panel_id:
            continue
        labels[panel_id] = {
            "topology_panel_v1_final_review_label": normalize_label(row.get("review_label", "")),
            "topology_panel_v1_final_review_comment": str(row.get("comment", "") or "").strip(),
        }
    return labels


def apply_labels(rows: List[Dict[str, str]], labels: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    reviewed: List[Dict[str, object]] = []
    for row in rows:
        panel_id = row.get("panel_id", "")
        label = labels.get(
            panel_id,
            {
                "topology_panel_v1_final_review_label": "confirmed_baseline",
                "topology_panel_v1_final_review_comment": "default confirmed after manual baseline review",
            },
        )
        out: Dict[str, object] = dict(row)
        out.update(label)
        review_label = str(out["topology_panel_v1_final_review_label"])
        out["topology_panel_v1_final_is_baseline"] = review_label == "confirmed_baseline"
        out["topology_panel_v1_final_exclude_reason"] = "" if review_label == "confirmed_baseline" else review_label
        reviewed.append(out)
    return reviewed


def build_summary(reviewed: List[Dict[str, object]], labels_path: Path, used_default_confirmed: bool) -> Dict[str, object]:
    final_rows = [row for row in reviewed if row.get("topology_panel_v1_final_is_baseline") is True]
    recheck_rows = [row for row in reviewed if row.get("topology_panel_v1_final_review_label") == "needs_recheck"]
    removed_rows = [row for row in reviewed if row.get("topology_panel_v1_final_review_label") == "remove_from_baseline"]
    return {
        "source_manifest": DEFAULT_MANIFEST.relative_to(ROOT).as_posix(),
        "labels_csv": labels_path.relative_to(ROOT).as_posix() if labels_path.is_relative_to(ROOT) else labels_path.as_posix(),
        "used_default_confirmed": used_default_confirmed,
        "reviewed_rows": len(reviewed),
        "final_baseline_rows": len(final_rows),
        "needs_recheck_rows": len(recheck_rows),
        "removed_rows": len(removed_rows),
        "label_counts": dict(Counter(str(row.get("topology_panel_v1_final_review_label", "")) for row in reviewed)),
        "split_counts": dict(Counter(str(row.get("split", "")) for row in final_rows)),
        "phase_counts": dict(Counter(str(row.get("phase", "")) for row in final_rows)),
        "outputs": {
            "reviewed": DEFAULT_REVIEWED.relative_to(ROOT).as_posix(),
            "final_baseline": DEFAULT_FINAL.relative_to(ROOT).as_posix(),
            "needs_recheck": DEFAULT_RECHECK.relative_to(ROOT).as_posix(),
            "removed": DEFAULT_REMOVED.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
        },
    }


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1 Final Baseline Report",
        "",
        "This report freezes the final clean-baseline subset after visual review.",
        "",
        "## Summary",
        "",
        f"- Reviewed rows: {summary['reviewed_rows']}",
        f"- Final baseline rows: {summary['final_baseline_rows']}",
        f"- Needs recheck rows: {summary['needs_recheck_rows']}",
        f"- Removed rows: {summary['removed_rows']}",
        f"- Used default confirmed labels: {summary['used_default_confirmed']}",
        "",
        "## Label Counts",
        "",
    ]
    for label, count in summary["label_counts"].items():
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Final Baseline Splits", ""])
    for split, count in summary["split_counts"].items():
        lines.append(f"- {split}: {count}")

    lines.extend(["", "## Final Baseline Phases", ""])
    for phase, count in summary["phase_counts"].items():
        lines.append(f"- {phase}: {count}")

    lines.extend(["", "## Outputs", ""])
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: `{value}`")

    DEFAULT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--default-confirmed", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    labels = load_labels(args.labels, args.default_confirmed)
    used_default_confirmed = not args.labels.exists()
    reviewed = apply_labels(rows, labels)
    fieldnames = list(reviewed[0].keys()) if reviewed else []

    final_rows = [row for row in reviewed if row.get("topology_panel_v1_final_is_baseline") is True]
    recheck_rows = [row for row in reviewed if row.get("topology_panel_v1_final_review_label") == "needs_recheck"]
    removed_rows = [row for row in reviewed if row.get("topology_panel_v1_final_review_label") == "remove_from_baseline"]

    write_csv(DEFAULT_REVIEWED, reviewed, fieldnames)
    write_csv(DEFAULT_FINAL, final_rows, fieldnames)
    write_csv(DEFAULT_RECHECK, recheck_rows, fieldnames)
    write_csv(DEFAULT_REMOVED, removed_rows, fieldnames)

    summary = build_summary(reviewed, args.labels, used_default_confirmed)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary)

    print(f"Reviewed rows: {summary['reviewed_rows']}")
    print(f"Final baseline rows: {summary['final_baseline_rows']}")
    print(f"Needs recheck rows: {summary['needs_recheck_rows']}")
    print(f"Removed rows: {summary['removed_rows']}")
    print(f"Used default confirmed labels: {summary['used_default_confirmed']}")
    print(f"Wrote: {DEFAULT_FINAL.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
