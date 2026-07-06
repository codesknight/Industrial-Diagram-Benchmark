"""Build topology-ready manifests from Topology Graph v0 outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_SOURCE = INDEX_DIR / "topology_graph_manifest.csv"


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


def write_splits(prefix: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    for split in ("train", "val", "test"):
        split_rows = [row for row in rows if row.get("split") == split]
        write_csv(INDEX_DIR / f"{prefix}_{split}.csv", split_rows, fieldnames)


def flag_counts(rows: Iterable[Dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(flag for flag in row.get("quality_flags", "").split(";") if flag)
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.source)
    if not rows:
        raise SystemExit("Source manifest is empty.")

    ready_rows = [row for row in rows if as_bool(row.get("topology_ready", ""))]
    not_ready_rows = [row for row in rows if not as_bool(row.get("topology_ready", ""))]
    fieldnames = list(rows[0].keys())

    write_csv(INDEX_DIR / "topology_ready_manifest.csv", ready_rows, fieldnames)
    write_csv(INDEX_DIR / "topology_not_ready_manifest.csv", not_ready_rows, fieldnames)
    write_splits("topology_ready", ready_rows, fieldnames)

    edge_counts = [int(row["edge_count"]) for row in ready_rows]
    node_counts = [int(row["node_count"]) for row in ready_rows]
    net_counts = [int(row["net_count"]) for row in ready_rows]
    summary = {
        "source_rows": len(rows),
        "topology_ready_rows": len(ready_rows),
        "topology_not_ready_rows": len(not_ready_rows),
        "ready_by_split": dict(Counter(row["split"] for row in ready_rows)),
        "not_ready_by_split": dict(Counter(row["split"] for row in not_ready_rows)),
        "ready_by_phase": dict(Counter(row["phase"] for row in ready_rows)),
        "not_ready_by_phase": dict(Counter(row["phase"] for row in not_ready_rows)),
        "not_ready_quality_flags": dict(flag_counts(not_ready_rows)),
        "ready_edge_count_min": min(edge_counts) if edge_counts else 0,
        "ready_edge_count_avg": round(sum(edge_counts) / len(edge_counts), 2) if edge_counts else 0,
        "ready_edge_count_max": max(edge_counts) if edge_counts else 0,
        "ready_node_count_avg": round(sum(node_counts) / len(node_counts), 2) if node_counts else 0,
        "ready_net_count_avg": round(sum(net_counts) / len(net_counts), 2) if net_counts else 0,
        "rules": [
            "topology_ready is true only when a graph has at least one edge",
            "not topology-ready rows are excluded from topology training and graph benchmark tasks",
            "not topology-ready rows may remain useful for symbol, layout, or classification tasks",
        ],
    }
    (INDEX_DIR / "topology_ready_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)

    print(f"Topology-ready rows: {len(ready_rows)}")
    print(f"Not topology-ready rows: {len(not_ready_rows)}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/topology_ready_manifest.csv")


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology-Ready Manifest Report",
        "",
        "This report summarizes the topology-ready subset derived from Topology Graph v0.",
        "",
        "## Summary",
        "",
        f"- Source rows: {summary['source_rows']}",
        f"- Topology-ready rows: {summary['topology_ready_rows']}",
        f"- Not topology-ready rows: {summary['topology_not_ready_rows']}",
        f"- Ready edge count min: {summary['ready_edge_count_min']}",
        f"- Ready edge count avg: {summary['ready_edge_count_avg']}",
        f"- Ready edge count max: {summary['ready_edge_count_max']}",
        f"- Ready node count avg: {summary['ready_node_count_avg']}",
        f"- Ready net count avg: {summary['ready_net_count_avg']}",
        "",
        "## Ready Splits",
        "",
    ]
    for split, count in summary["ready_by_split"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Not Ready Splits", ""])
    for split, count in summary["not_ready_by_split"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Not Ready Flags", ""])
    for flag, count in summary["not_ready_quality_flags"].items():
        lines.append(f"- {flag}: {count}")
    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    (INDEX_DIR / "topology_ready_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
