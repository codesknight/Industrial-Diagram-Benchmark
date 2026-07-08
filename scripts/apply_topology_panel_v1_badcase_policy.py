"""Apply final badcase policy to panel-level Topology Graph v1 sample labels.

After manual inspection, panels labeled `needs_panel_split` are treated as
multi-subfigure badcases rather than candidates for another split pass.
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
DEFAULT_REVIEWED = INDEX_DIR / "topology_panel_v1_sample_reviewed.csv"

BADCASE_LABELS = {"needs_panel_split", "bad_geometry", "not_topology_target"}
IMPROVEMENT_LABELS = {"over_connected", "still_fragmented", "needs_terminal_anchor"}


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


def apply_policy(row: Dict[str, str]) -> Dict[str, object]:
    out: Dict[str, object] = dict(row)
    label = row.get("topology_panel_v1_review_label", "")
    if label == "accept_v1":
        decision = "baseline_accept"
        exclude_reason = ""
    elif label == "needs_panel_split":
        decision = "badcase"
        exclude_reason = "multi_subfigure_badcase"
    elif label == "bad_geometry":
        decision = "badcase"
        exclude_reason = "bad_geometry"
    elif label == "not_topology_target":
        decision = "badcase"
        exclude_reason = "not_topology_target"
    elif label in IMPROVEMENT_LABELS:
        decision = "improvement_target"
        exclude_reason = label
    elif not label:
        decision = "unreviewed"
        exclude_reason = "unreviewed"
    else:
        decision = "unknown"
        exclude_reason = label or "unknown"
    out["topology_panel_v1_policy_decision"] = decision
    out["topology_panel_v1_policy_exclude_reason"] = exclude_reason
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewed", type=Path, default=DEFAULT_REVIEWED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = [apply_policy(row) for row in load_csv(args.reviewed)]
    fieldnames = list(rows[0].keys()) if rows else []

    baseline = [row for row in rows if row.get("topology_panel_v1_policy_decision") == "baseline_accept"]
    badcases = [row for row in rows if row.get("topology_panel_v1_policy_decision") == "badcase"]
    multi_subfigure = [
        row for row in rows
        if row.get("topology_panel_v1_policy_exclude_reason") == "multi_subfigure_badcase"
    ]
    improvement = [row for row in rows if row.get("topology_panel_v1_policy_decision") == "improvement_target"]
    unreviewed = [row for row in rows if row.get("topology_panel_v1_policy_decision") == "unreviewed"]

    write_csv(INDEX_DIR / "topology_panel_v1_sample_policy_reviewed.csv", rows, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_clean_baseline_candidates.csv", baseline, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_badcase_manifest.csv", badcases, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_multi_subfigure_badcase.csv", multi_subfigure, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_improvement_targets.csv", improvement, fieldnames)
    write_csv(INDEX_DIR / "topology_panel_v1_policy_unreviewed.csv", unreviewed, fieldnames)

    summary = {
        "sample_rows": len(rows),
        "baseline_accept_rows": len(baseline),
        "badcase_rows": len(badcases),
        "multi_subfigure_badcase_rows": len(multi_subfigure),
        "improvement_target_rows": len(improvement),
        "unreviewed_rows": len(unreviewed),
        "review_label_counts": dict(Counter(str(row.get("topology_panel_v1_review_label", "")) or "unreviewed" for row in rows)),
        "policy_decision_counts": dict(Counter(str(row.get("topology_panel_v1_policy_decision", "")) for row in rows)),
        "policy_exclude_reason_counts": dict(Counter(str(row.get("topology_panel_v1_policy_exclude_reason", "")) or "keep" for row in rows)),
        "multi_subfigure_by_split_method": dict(Counter(str(row.get("split_method", "")) for row in multi_subfigure)),
        "multi_subfigure_by_phase": dict(Counter(str(row.get("phase", "")) for row in multi_subfigure)),
        "rules": [
            "needs_panel_split is treated as multi_subfigure_badcase and excluded from topology baseline",
            "bad_geometry and not_topology_target are excluded from topology baseline",
            "accept_v1 remains eligible for the clean panel-level v1 baseline",
            "over_connected, still_fragmented, and needs_terminal_anchor are retained as algorithm improvement targets",
        ],
    }
    (INDEX_DIR / "topology_panel_v1_badcase_policy_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)

    print(f"Sample rows: {summary['sample_rows']}")
    print(f"Baseline accept rows: {summary['baseline_accept_rows']}")
    print(f"Badcase rows: {summary['badcase_rows']}")
    print(f"Multi-subfigure badcase rows: {summary['multi_subfigure_badcase_rows']}")
    print(f"Improvement target rows: {summary['improvement_target_rows']}")


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1 Badcase Policy Report",
        "",
        "This report applies the final policy that multi-subfigure panels are badcases, not split-v2 candidates.",
        "",
        "## Summary",
        "",
        f"- Sample rows: {summary['sample_rows']}",
        f"- Baseline accept rows: {summary['baseline_accept_rows']}",
        f"- Badcase rows: {summary['badcase_rows']}",
        f"- Multi-subfigure badcase rows: {summary['multi_subfigure_badcase_rows']}",
        f"- Improvement target rows: {summary['improvement_target_rows']}",
        f"- Unreviewed rows: {summary['unreviewed_rows']}",
        "",
        "## Policy Exclude Reason Counts",
        "",
    ]
    for reason, count in summary["policy_exclude_reason_counts"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Multi-Subfigure by Split Method", ""])
    for method, count in summary["multi_subfigure_by_split_method"].items():
        lines.append(f"- {method}: {count}")
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    (INDEX_DIR / "topology_panel_v1_badcase_policy_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
