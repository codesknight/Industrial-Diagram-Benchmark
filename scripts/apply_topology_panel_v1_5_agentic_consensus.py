"""Materialize Topology Panel v1.5 agentic consensus partitions."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data_index"
DEFAULT_CANDIDATES = DATA_INDEX / "topology_panel_v1_5_candidate_manifest.csv"
DEFAULT_CONSENSUS = DATA_INDEX / "topology_panel_v1_5_agentic_annotation_consensus.csv"
DEFAULT_PREFIX = DATA_INDEX / "topology_panel_v1_5_agentic"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def output_paths(prefix: Path) -> Dict[str, Path]:
    return {
        "auto_accept": prefix.with_name(prefix.name + "_auto_accept_manifest.csv"),
        "auto_reject": prefix.with_name(prefix.name + "_auto_reject_manifest.csv"),
        "defer_improvement": prefix.with_name(prefix.name + "_defer_improvement_manifest.csv"),
        "human_review": prefix.with_name(prefix.name + "_human_review_manifest.csv"),
        "summary": prefix.with_name(prefix.name + "_consensus_partition_summary.json"),
        "report": prefix.with_name(prefix.name + "_consensus_partition_report.md"),
    }


def merge_rows(candidates: List[Dict[str, str]], consensus: List[Dict[str, str]]) -> List[Dict[str, object]]:
    by_id = {row["panel_id"]: row for row in candidates}
    merged: List[Dict[str, object]] = []
    for row in consensus:
        panel_id = row["panel_id"]
        base = dict(by_id.get(panel_id, {}))
        base.update({f"agentic_{key}": value for key, value in row.items() if key != "panel_id"})
        base["panel_id"] = panel_id
        merged.append(base)
    return merged


def write_report(path: Path, summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1.5 Agentic Consensus Partition Report",
        "",
        "This report materializes the multi-agent consensus into release-oriented partitions.",
        "",
        "## Summary",
        "",
        f"- candidate rows: {summary['candidate_rows']}",
        f"- consensus rows: {summary['consensus_rows']}",
        f"- auto accept rows: {summary['partition_counts'].get('auto_accept', 0)}",
        f"- auto reject rows: {summary['partition_counts'].get('auto_reject', 0)}",
        f"- defer improvement rows: {summary['partition_counts'].get('auto_defer_improvement', 0)}",
        f"- human review rows: {summary['partition_counts'].get('human_review', 0)}",
        "",
        "## Label Counts",
        "",
    ]
    for key, value in summary["label_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Outputs", ""])
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- `auto_accept` rows are candidates for Topology Panel v1.5 clean baseline.",
            "- `auto_reject` rows are excluded by agentic consensus.",
            "- `auto_defer_improvement` rows remain algorithm improvement targets.",
            "- `human_review` rows require targeted manual review before use.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--consensus", type=Path, default=DEFAULT_CONSENSUS)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_PREFIX)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = read_csv(args.candidates)
    consensus = read_csv(args.consensus)
    merged = merge_rows(candidates, consensus)
    paths = output_paths(args.output_prefix)

    partitions = {
        "auto_accept": [row for row in merged if row.get("agentic_consensus_decision") == "auto_accept"],
        "auto_reject": [row for row in merged if row.get("agentic_consensus_decision") == "auto_reject"],
        "defer_improvement": [
            row for row in merged if row.get("agentic_consensus_decision") == "auto_defer_improvement"
        ],
        "human_review": [row for row in merged if row.get("agentic_consensus_decision") == "human_review"],
    }
    fieldnames = list(merged[0].keys()) if merged else ["panel_id"]
    for key, rows in partitions.items():
        write_csv(paths[key], rows, fieldnames)

    summary = {
        "candidate_csv": rel(args.candidates),
        "consensus_csv": rel(args.consensus),
        "candidate_rows": len(candidates),
        "consensus_rows": len(consensus),
        "partition_counts": dict(Counter(str(row.get("agentic_consensus_decision", "")) for row in merged)),
        "label_counts": dict(Counter(str(row.get("agentic_consensus_label", "")) for row in merged)),
        "outputs": {key: rel(value) for key, value in paths.items()},
        "rules": [
            "auto_accept rows are not final publication rows until v1.5 release checks pass.",
            "human_review rows are the only rows that should require manual annotation.",
            "auto_reject and defer_improvement rows remain auditable and are not discarded.",
        ],
    }
    write_json(paths["summary"], summary)
    write_report(paths["report"], summary)
    for key, path in paths.items():
        print(f"Wrote: {rel(path)}")


if __name__ == "__main__":
    main()
