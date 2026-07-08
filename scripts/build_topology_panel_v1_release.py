"""Build formal release manifests for Topology Panel v1.

The release is derived from manually reviewed panel-level samples after the
final badcase policy has been applied. Multi-subfigure panels are excluded as
badcases instead of being sent to another split pass.
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

DEFAULT_POLICY = INDEX_DIR / "topology_panel_v1_sample_policy_reviewed.csv"
DEFAULT_RELEASE = INDEX_DIR / "topology_panel_v1_release_manifest.csv"
DEFAULT_ALL = INDEX_DIR / "topology_panel_v1_release_all_reviewed_manifest.csv"
DEFAULT_EXCLUDED = INDEX_DIR / "topology_panel_v1_release_excluded_manifest.csv"
DEFAULT_IMPROVEMENT = INDEX_DIR / "topology_panel_v1_release_improvement_manifest.csv"
DEFAULT_UNREVIEWED = INDEX_DIR / "topology_panel_v1_release_unreviewed_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_release_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_release_report.md"

RELEASE_ID = "topology_panel_v1_2026-07-08"


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


def rel_exists(path_value: str) -> bool:
    if not path_value:
        return False
    return (ROOT / path_value).exists()


def release_partition(row: Dict[str, str]) -> str:
    decision = row.get("topology_panel_v1_policy_decision", "")
    if decision == "baseline_accept":
        return "clean_baseline"
    if decision == "badcase":
        return "excluded_badcase"
    if decision == "improvement_target":
        return "improvement_target"
    if decision == "unreviewed":
        return "unreviewed"
    return "unknown"


def release_use(partition: str) -> str:
    return {
        "clean_baseline": "topology_graph_v1_baseline",
        "excluded_badcase": "excluded_from_topology_baseline",
        "improvement_target": "topology_algorithm_improvement",
        "unreviewed": "pending_manual_review",
    }.get(partition, "unknown")


def normalize_row(row: Dict[str, str]) -> Dict[str, object]:
    out: Dict[str, object] = dict(row)
    partition = release_partition(row)
    exclude_reason = row.get("topology_panel_v1_policy_exclude_reason", "")
    review_label = row.get("topology_panel_v1_review_label", "")

    out["topology_panel_v1_release_id"] = RELEASE_ID
    out["topology_panel_v1_release_partition"] = partition
    out["topology_panel_v1_release_use"] = release_use(partition)
    out["topology_panel_v1_release_exclude_reason"] = exclude_reason
    out["topology_panel_v1_release_is_baseline"] = partition == "clean_baseline"
    out["topology_panel_v1_release_is_badcase"] = partition == "excluded_badcase"
    out["topology_panel_v1_release_is_improvement_target"] = partition == "improvement_target"
    out["topology_panel_v1_release_is_reviewed"] = bool(review_label)
    out["panel_png_exists"] = rel_exists(row.get("panel_png_path", ""))
    out["topology_v1_panel_json_exists"] = rel_exists(row.get("topology_v1_panel_json_path", ""))
    return out


def int_value(row: Dict[str, object], key: str) -> int:
    try:
        return int(float(str(row.get(key, "") or 0)))
    except ValueError:
        return 0


def numeric_stats(rows: List[Dict[str, object]], key: str) -> Dict[str, float]:
    values = [int_value(row, key) for row in rows]
    if not values:
        return {"min": 0, "max": 0, "mean": 0.0}
    return {
        "min": min(values),
        "max": max(values),
        "mean": round(sum(values) / len(values), 4),
    }


def counter(rows: List[Dict[str, object]], key: str) -> Dict[str, int]:
    return dict(Counter(str(row.get(key, "")) or "empty" for row in rows))


def summarize(rows: List[Dict[str, object]]) -> Dict[str, object]:
    baseline = [row for row in rows if row["topology_panel_v1_release_partition"] == "clean_baseline"]
    excluded = [row for row in rows if row["topology_panel_v1_release_partition"] == "excluded_badcase"]
    improvement = [row for row in rows if row["topology_panel_v1_release_partition"] == "improvement_target"]
    unreviewed = [row for row in rows if row["topology_panel_v1_release_partition"] == "unreviewed"]

    return {
        "release_id": RELEASE_ID,
        "source_manifest": DEFAULT_POLICY.relative_to(ROOT).as_posix(),
        "reviewed_sample_rows": len(rows),
        "release_baseline_rows": len(baseline),
        "excluded_badcase_rows": len(excluded),
        "improvement_target_rows": len(improvement),
        "unreviewed_rows": len(unreviewed),
        "partition_counts": counter(rows, "topology_panel_v1_release_partition"),
        "review_label_counts": counter(rows, "topology_panel_v1_review_label"),
        "exclude_reason_counts": counter(rows, "topology_panel_v1_release_exclude_reason"),
        "baseline_split_counts": counter(baseline, "split"),
        "baseline_phase_counts": counter(baseline, "phase"),
        "badcase_reason_counts": counter(excluded, "topology_panel_v1_release_exclude_reason"),
        "improvement_reason_counts": counter(improvement, "topology_panel_v1_release_exclude_reason"),
        "asset_checks": {
            "missing_panel_png_rows": sum(1 for row in rows if not row["panel_png_exists"]),
            "missing_topology_v1_json_rows": sum(1 for row in rows if not row["topology_v1_panel_json_exists"]),
            "baseline_missing_panel_png_rows": sum(1 for row in baseline if not row["panel_png_exists"]),
            "baseline_missing_topology_v1_json_rows": sum(
                1 for row in baseline if not row["topology_v1_panel_json_exists"]
            ),
        },
        "baseline_graph_stats": {
            "v1_node_count": numeric_stats(baseline, "v1_node_count"),
            "v1_edge_count": numeric_stats(baseline, "v1_edge_count"),
            "v1_net_count": numeric_stats(baseline, "v1_net_count"),
            "intersection_count": numeric_stats(baseline, "intersection_count"),
        },
        "rules": [
            "Only clean_baseline rows are eligible for the formal Topology Panel v1 baseline.",
            "Rows labeled needs_panel_split are multi-subfigure badcases and are excluded from the baseline.",
            "Rows labeled bad_geometry or not_topology_target are excluded from the baseline.",
            "Rows labeled over_connected, still_fragmented, or needs_terminal_anchor are retained as improvement targets.",
        ],
        "outputs": {
            "release_manifest": DEFAULT_RELEASE.relative_to(ROOT).as_posix(),
            "release_train_manifest": (INDEX_DIR / "topology_panel_v1_release_train.csv").relative_to(ROOT).as_posix(),
            "release_val_manifest": (INDEX_DIR / "topology_panel_v1_release_val.csv").relative_to(ROOT).as_posix(),
            "release_test_manifest": (INDEX_DIR / "topology_panel_v1_release_test.csv").relative_to(ROOT).as_posix(),
            "all_reviewed_manifest": DEFAULT_ALL.relative_to(ROOT).as_posix(),
            "excluded_manifest": DEFAULT_EXCLUDED.relative_to(ROOT).as_posix(),
            "improvement_manifest": DEFAULT_IMPROVEMENT.relative_to(ROOT).as_posix(),
            "unreviewed_manifest": DEFAULT_UNREVIEWED.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
        },
    }


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1 Release Report",
        "",
        f"Release id: `{summary['release_id']}`",
        "",
        "This release freezes the manually reviewed panel-level Topology Graph v1 baseline.",
        "Multi-subfigure panels are treated as badcases and are not sent to another panel-boxing pass.",
        "",
        "## Summary",
        "",
        f"- Reviewed sample rows: {summary['reviewed_sample_rows']}",
        f"- Clean baseline rows: {summary['release_baseline_rows']}",
        f"- Excluded badcase rows: {summary['excluded_badcase_rows']}",
        f"- Improvement target rows: {summary['improvement_target_rows']}",
        f"- Unreviewed rows: {summary['unreviewed_rows']}",
        "",
        "## Release Partitions",
        "",
    ]
    for key, value in summary["partition_counts"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Excluded Badcases", ""])
    for key, value in summary["badcase_reason_counts"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Improvement Targets", ""])
    for key, value in summary["improvement_reason_counts"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Clean Baseline Splits", ""])
    for key, value in summary["baseline_split_counts"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Clean Baseline Phases", ""])
    for key, value in summary["baseline_phase_counts"].items():
        lines.append(f"- {key}: {value}")

    asset = summary["asset_checks"]
    lines.extend([
        "",
        "## Asset Checks",
        "",
        f"- Missing panel PNG rows: {asset['missing_panel_png_rows']}",
        f"- Missing topology v1 JSON rows: {asset['missing_topology_v1_json_rows']}",
        f"- Clean baseline missing panel PNG rows: {asset['baseline_missing_panel_png_rows']}",
        f"- Clean baseline missing topology v1 JSON rows: {asset['baseline_missing_topology_v1_json_rows']}",
        "",
        "## Clean Baseline Graph Stats",
        "",
    ])
    graph_stats = summary["baseline_graph_stats"]
    for key, stats in graph_stats.items():
        lines.append(f"- {key}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")

    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    lines.extend(["", "## Outputs", ""])
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: `{value}`")

    DEFAULT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_split_manifests(baseline: List[Dict[str, object]], fieldnames: List[str]) -> None:
    for split_name in ["train", "val", "test"]:
        rows = [row for row in baseline if row.get("split") == split_name]
        write_csv(INDEX_DIR / f"topology_panel_v1_release_{split_name}.csv", rows, fieldnames)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = [normalize_row(row) for row in load_csv(args.policy)]
    fieldnames = list(rows[0].keys()) if rows else []

    baseline = [row for row in rows if row["topology_panel_v1_release_partition"] == "clean_baseline"]
    excluded = [row for row in rows if row["topology_panel_v1_release_partition"] == "excluded_badcase"]
    improvement = [row for row in rows if row["topology_panel_v1_release_partition"] == "improvement_target"]
    unreviewed = [row for row in rows if row["topology_panel_v1_release_partition"] == "unreviewed"]

    write_csv(DEFAULT_ALL, rows, fieldnames)
    write_csv(DEFAULT_RELEASE, baseline, fieldnames)
    write_csv(DEFAULT_EXCLUDED, excluded, fieldnames)
    write_csv(DEFAULT_IMPROVEMENT, improvement, fieldnames)
    write_csv(DEFAULT_UNREVIEWED, unreviewed, fieldnames)
    write_split_manifests(baseline, fieldnames)

    summary = summarize(rows)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary)

    print(f"Release id: {summary['release_id']}")
    print(f"Reviewed sample rows: {summary['reviewed_sample_rows']}")
    print(f"Clean baseline rows: {summary['release_baseline_rows']}")
    print(f"Excluded badcase rows: {summary['excluded_badcase_rows']}")
    print(f"Improvement target rows: {summary['improvement_target_rows']}")
    print(f"Unreviewed rows: {summary['unreviewed_rows']}")
    print(f"Wrote: {DEFAULT_RELEASE.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_REPORT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
