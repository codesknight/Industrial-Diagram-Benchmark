"""Apply manual labels from Topology Panel v1.1 active improvement review."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_1_active_improvement_review_manifest.csv"
DEFAULT_LABELS = INDEX_DIR / "topology_panel_v1_1_active_improvement_review_labels.csv"
DEFAULT_REVIEWED = INDEX_DIR / "topology_panel_v1_1_active_improvement_reviewed.csv"
DEFAULT_KEEP = INDEX_DIR / "topology_panel_v1_1_keep_improvement_manifest.csv"
DEFAULT_TERMINAL = INDEX_DIR / "topology_panel_v1_1_keep_terminal_anchor_manifest.csv"
DEFAULT_OVER_CONNECTED = INDEX_DIR / "topology_panel_v1_1_keep_over_connected_manifest.csv"
DEFAULT_ABANDONED = INDEX_DIR / "topology_panel_v1_1_active_review_abandoned.csv"
DEFAULT_DEFERRED = INDEX_DIR / "topology_panel_v1_1_active_review_deferred.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_1_active_improvement_review_result_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_1_active_improvement_review_result_report.md"

VALID_LABELS = {
    "keep_terminal_anchor",
    "keep_over_connected",
    "abandon_badcase",
    "defer_complex",
}


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
    if label not in VALID_LABELS:
        raise SystemExit(f"Unknown active improvement review label: {label}")
    return label


def load_labels(path: Path) -> Dict[str, Dict[str, str]]:
    labels: Dict[str, Dict[str, str]] = {}
    for row in load_csv(path):
        panel_id = str(row.get("panel_id", "")).strip()
        if not panel_id:
            continue
        labels[panel_id] = {
            "topology_panel_v1_1_active_review_label": normalize_label(row.get("review_label", "")),
            "topology_panel_v1_1_active_review_comment": str(row.get("comment", "") or "").strip(),
            "topology_panel_v1_1_active_review_suggested_label": str(
                row.get("suggested_review_label", "") or ""
            ).strip(),
            "topology_panel_v1_1_active_review_source_next_route": str(row.get("next_route", "") or "").strip(),
        }
    return labels


def decision_from_label(label: str) -> tuple[str, str]:
    if label in {"keep_terminal_anchor", "keep_over_connected"}:
        return "keep_improvement", label
    if label == "abandon_badcase":
        return "abandoned", "manual_active_review_abandon_badcase"
    if label == "defer_complex":
        return "deferred", "manual_active_review_defer_complex"
    return "unknown", label


def apply_labels(rows: List[Dict[str, str]], labels: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    reviewed: List[Dict[str, object]] = []
    for row in rows:
        panel_id = row.get("panel_id", "")
        if panel_id not in labels:
            raise SystemExit(f"Missing active improvement label for panel_id: {panel_id}")
        out: Dict[str, object] = dict(row)
        out.update(labels[panel_id])
        label = str(out["topology_panel_v1_1_active_review_label"])
        decision, route = decision_from_label(label)
        out["topology_panel_v1_1_active_review_decision"] = decision
        out["topology_panel_v1_1_active_review_route"] = route
        out["topology_panel_v1_1_active_review_keep"] = decision == "keep_improvement"
        reviewed.append(out)
    return reviewed


def build_summary(reviewed: List[Dict[str, object]], labels: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    kept = [row for row in reviewed if row.get("topology_panel_v1_1_active_review_decision") == "keep_improvement"]
    terminal = [row for row in kept if row.get("topology_panel_v1_1_active_review_label") == "keep_terminal_anchor"]
    over_connected = [row for row in kept if row.get("topology_panel_v1_1_active_review_label") == "keep_over_connected"]
    abandoned = [row for row in reviewed if row.get("topology_panel_v1_1_active_review_decision") == "abandoned"]
    deferred = [row for row in reviewed if row.get("topology_panel_v1_1_active_review_decision") == "deferred"]
    return {
        "source_manifest": DEFAULT_MANIFEST.relative_to(ROOT).as_posix(),
        "source_labels": DEFAULT_LABELS.relative_to(ROOT).as_posix(),
        "manifest_rows": len(reviewed),
        "label_rows": len(labels),
        "kept_rows": len(kept),
        "keep_terminal_anchor_rows": len(terminal),
        "keep_over_connected_rows": len(over_connected),
        "abandoned_rows": len(abandoned),
        "deferred_rows": len(deferred),
        "label_counts": dict(Counter(str(row.get("topology_panel_v1_1_active_review_label", "")) for row in reviewed)),
        "decision_counts": dict(Counter(str(row.get("topology_panel_v1_1_active_review_decision", "")) for row in reviewed)),
        "next_route_counts": dict(Counter(str(row.get("topology_panel_v1_1_next_route", "")) for row in reviewed)),
        "rules": [
            "Rows labeled keep_terminal_anchor remain candidates for terminal/symbol anchor work.",
            "Rows labeled keep_over_connected remain candidates for crossing-line disambiguation work.",
            "Rows labeled abandon_badcase or defer_complex are excluded from immediate v1.1 repair.",
            "No active improvement row is promoted into the formal v1 baseline by this step.",
        ],
        "outputs": {
            "reviewed": DEFAULT_REVIEWED.relative_to(ROOT).as_posix(),
            "keep_improvement": DEFAULT_KEEP.relative_to(ROOT).as_posix(),
            "keep_terminal_anchor": DEFAULT_TERMINAL.relative_to(ROOT).as_posix(),
            "keep_over_connected": DEFAULT_OVER_CONNECTED.relative_to(ROOT).as_posix(),
            "abandoned": DEFAULT_ABANDONED.relative_to(ROOT).as_posix(),
            "deferred": DEFAULT_DEFERRED.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
        },
    }


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1.1 Active Improvement Review Result Report",
        "",
        "This report applies manual labels exported from `topology_panel_v1_1_active_improvement_review.html`.",
        "The formal Topology Panel v1 baseline is unchanged.",
        "",
        "## Summary",
        "",
        f"- Manifest rows: {summary['manifest_rows']}",
        f"- Label rows: {summary['label_rows']}",
        f"- Kept rows: {summary['kept_rows']}",
        f"- Keep terminal-anchor rows: {summary['keep_terminal_anchor_rows']}",
        f"- Keep over-connected rows: {summary['keep_over_connected_rows']}",
        f"- Abandoned rows: {summary['abandoned_rows']}",
        f"- Deferred rows: {summary['deferred_rows']}",
        "",
        "## Label Counts",
        "",
    ]
    for label, count in summary["label_counts"].items():
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Decision Counts", ""])
    for decision, count in summary["decision_counts"].items():
        lines.append(f"- {decision}: {count}")

    lines.extend(["", "## Next Route Counts", ""])
    for route, count in summary["next_route_counts"].items():
        lines.append(f"- {route}: {count}")

    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    lines.extend(["", "## Outputs", ""])
    for name, path in summary["outputs"].items():
        lines.append(f"- {name}: `{path}`")

    DEFAULT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    labels = load_labels(args.labels)
    reviewed = apply_labels(rows, labels)
    fieldnames = list(reviewed[0].keys()) if reviewed else []

    kept = [row for row in reviewed if row.get("topology_panel_v1_1_active_review_decision") == "keep_improvement"]
    terminal = [row for row in kept if row.get("topology_panel_v1_1_active_review_label") == "keep_terminal_anchor"]
    over_connected = [row for row in kept if row.get("topology_panel_v1_1_active_review_label") == "keep_over_connected"]
    abandoned = [row for row in reviewed if row.get("topology_panel_v1_1_active_review_decision") == "abandoned"]
    deferred = [row for row in reviewed if row.get("topology_panel_v1_1_active_review_decision") == "deferred"]

    write_csv(DEFAULT_REVIEWED, reviewed, fieldnames)
    write_csv(DEFAULT_KEEP, kept, fieldnames)
    write_csv(DEFAULT_TERMINAL, terminal, fieldnames)
    write_csv(DEFAULT_OVER_CONNECTED, over_connected, fieldnames)
    write_csv(DEFAULT_ABANDONED, abandoned, fieldnames)
    write_csv(DEFAULT_DEFERRED, deferred, fieldnames)

    summary = build_summary(reviewed, labels)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary)

    print(f"Manifest rows: {summary['manifest_rows']}")
    print(f"Kept rows: {summary['kept_rows']}")
    print(f"Keep terminal-anchor rows: {summary['keep_terminal_anchor_rows']}")
    print(f"Keep over-connected rows: {summary['keep_over_connected_rows']}")
    print(f"Abandoned rows: {summary['abandoned_rows']}")
    print(f"Deferred rows: {summary['deferred_rows']}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
