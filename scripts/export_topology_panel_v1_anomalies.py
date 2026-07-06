"""Export quick anomaly lists for full panel-level Topology Graph v1."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_anomaly_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_anomaly_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_anomaly_report.md"


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


def as_int(row: Dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "") or 0))
    except ValueError:
        return 0


def as_float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except ValueError:
        return 0.0


def classify(row: Dict[str, str]) -> Tuple[str, str, str]:
    status = row.get("status", "")
    flags = set(filter(None, row.get("quality_flags", "").split(";")))
    if status == "error":
        return "critical", "error", "Inspect parent normalized/topology paths or geometry payload, then rerun this row."
    if status == "truncated_max_segments":
        return "critical", "truncated_max_segments", "Review extremely dense graph; raise max_segments only if visually valid."
    if "no_edges" in flags or "no_nets" in flags:
        return "high", "no_edges_or_no_nets", "Check whether this panel is not a topology target or uses unsupported geometry types."
    if "high_isolated_ratio" in flags:
        return "medium", "high_isolated_ratio", "Review endpoint merge tolerance or geometry fragmentation."
    if "high_fragmentation" in flags:
        return "medium", "high_fragmentation", "Review as a candidate for terminal anchors or line-merge improvements."
    if "dominant_component" in flags:
        return "low", "dominant_component", "Spot-check whether the graph is over-connected."
    return "", "", ""


def build_anomalies(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    anomalies: List[Dict[str, object]] = []
    for row in rows:
        severity, anomaly_type, action = classify(row)
        if not severity:
            continue
        out: Dict[str, object] = {
            "severity": severity,
            "anomaly_type": anomaly_type,
            "suggested_action": action,
            "panel_id": row.get("panel_id", ""),
            "parent_drawing_key": row.get("parent_drawing_key", ""),
            "split": row.get("split", ""),
            "phase": row.get("phase", ""),
            "status": row.get("status", ""),
            "error": row.get("error", ""),
            "quality_flags": row.get("quality_flags", ""),
            "panel_entity_count": row.get("panel_entity_count", ""),
            "base_segment_count": row.get("base_segment_count", ""),
            "split_segment_count": row.get("split_segment_count", ""),
            "intersection_count": row.get("intersection_count", ""),
            "v1_node_count": row.get("v1_node_count", ""),
            "v1_edge_count": row.get("v1_edge_count", ""),
            "v1_net_count": row.get("v1_net_count", ""),
            "v1_isolated_edge_ratio": row.get("v1_isolated_edge_ratio", ""),
            "v1_largest_net_edge_ratio": row.get("v1_largest_net_edge_ratio", ""),
            "panel_png_path": row.get("panel_png_path", ""),
            "topology_v1_panel_json_path": row.get("topology_v1_panel_json_path", ""),
        }
        anomalies.append(out)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    anomalies.sort(
        key=lambda row: (
            severity_order.get(str(row["severity"]), 99),
            -int(float(row.get("v1_edge_count", 0) or 0)),
            str(row["panel_id"]),
        )
    )
    return anomalies


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    anomalies = build_anomalies(rows)
    fieldnames = list(anomalies[0].keys()) if anomalies else ANOMALY_FIELDNAMES
    write_csv(args.output, anomalies, fieldnames)
    summary = build_summary(rows, anomalies, args)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary, anomalies, args.report)
    print(f"Panel rows: {summary['panel_rows']}")
    print(f"Anomaly rows: {summary['anomaly_rows']}")
    print(f"Wrote: {args.output.resolve().relative_to(ROOT).as_posix()}")


def build_summary(
    rows: List[Dict[str, str]],
    anomalies: List[Dict[str, object]],
    args: argparse.Namespace,
) -> Dict[str, object]:
    return {
        "panel_rows": len(rows),
        "anomaly_rows": len(anomalies),
        "normal_rows": len(rows) - len(anomalies),
        "severity_counts": dict(Counter(str(row["severity"]) for row in anomalies)),
        "anomaly_type_counts": dict(Counter(str(row["anomaly_type"]) for row in anomalies)),
        "status_counts": dict(Counter(row.get("status", "") for row in rows)),
        "phase_counts": dict(Counter(str(row.get("phase", "")) for row in anomalies)),
        "split_counts": dict(Counter(str(row.get("split", "")) for row in anomalies)),
        "max_edge_count": max((as_int(row, "v1_edge_count") for row in rows), default=0),
        "max_net_count": max((as_int(row, "v1_net_count") for row in rows), default=0),
        "max_intersection_count": max((as_int(row, "intersection_count") for row in rows), default=0),
        "max_isolated_edge_ratio": max((as_float(row, "v1_isolated_edge_ratio") for row in rows), default=0.0),
        "source_manifest": args.manifest.resolve().relative_to(ROOT).as_posix(),
        "output_manifest": args.output.resolve().relative_to(ROOT).as_posix(),
        "rules": [
            "status=error and status=truncated_max_segments are critical anomalies",
            "no_edges/no_nets rows require topology-target review or unsupported-geometry inspection",
            "high_fragmentation, high_isolated_ratio, and dominant_component are risk samples for the next HTML review",
        ],
    }


def write_report(summary: Dict[str, object], anomalies: List[Dict[str, object]], report_path: Path) -> None:
    lines = [
        "# Topology Panel v1 Anomaly Report",
        "",
        "This report lists quick anomaly buckets from `topology_panel_v1_manifest.csv`.",
        "",
        "## Summary",
        "",
        f"- Panel rows: {summary['panel_rows']}",
        f"- Normal rows: {summary['normal_rows']}",
        f"- Anomaly rows: {summary['anomaly_rows']}",
        f"- Max edge count: {summary['max_edge_count']}",
        f"- Max net count: {summary['max_net_count']}",
        f"- Max intersection count: {summary['max_intersection_count']}",
        f"- Max isolated edge ratio: {summary['max_isolated_edge_ratio']}",
        "",
        "## Severity Counts",
        "",
    ]
    for severity, count in summary["severity_counts"].items():
        lines.append(f"- {severity}: {count}")
    lines.extend(["", "## Anomaly Type Counts", ""])
    for anomaly_type, count in summary["anomaly_type_counts"].items():
        lines.append(f"- {anomaly_type}: {count}")
    lines.extend(["", "## Status Counts", ""])
    for status, count in summary["status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Critical and High Samples", ""])
    for row in anomalies:
        if row["severity"] not in {"critical", "high"}:
            continue
        lines.append(
            "- "
            f"{row['panel_id']}: "
            f"type={row['anomaly_type']}, "
            f"status={row['status']}, "
            f"edges={row['v1_edge_count']}, "
            f"nets={row['v1_net_count']}, "
            f"flags={row['quality_flags'] or 'none'}"
        )
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


ANOMALY_FIELDNAMES = [
    "severity",
    "anomaly_type",
    "suggested_action",
    "panel_id",
    "parent_drawing_key",
    "split",
    "phase",
    "status",
    "error",
    "quality_flags",
    "panel_entity_count",
    "base_segment_count",
    "split_segment_count",
    "intersection_count",
    "v1_node_count",
    "v1_edge_count",
    "v1_net_count",
    "v1_isolated_edge_ratio",
    "v1_largest_net_edge_ratio",
    "panel_png_path",
    "topology_v1_panel_json_path",
]


if __name__ == "__main__":
    main()
