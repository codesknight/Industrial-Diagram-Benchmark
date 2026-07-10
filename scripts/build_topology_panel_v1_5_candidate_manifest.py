"""Build a candidate pool for Topology Panel v1.5 agentic annotation."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data_index"
DEFAULT_INPUT = DATA_INDEX / "topology_panel_v1_sample_policy_reviewed.csv"
DEFAULT_OUTPUT = DATA_INDEX / "topology_panel_v1_5_candidate_manifest.csv"
DEFAULT_SUMMARY = DATA_INDEX / "topology_panel_v1_5_candidate_summary.json"
DEFAULT_REPORT = DATA_INDEX / "topology_panel_v1_5_candidate_report.md"


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


def as_float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except ValueError:
        return 0.0


def exists_rel(path_value: str) -> bool:
    if not path_value:
        return False
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path.exists()


def candidate_score(row: Dict[str, str]) -> tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []

    if row.get("status") == "ok":
        score += 20
        reasons.append("status_ok")
    if row.get("split_method") == "full":
        score += 10
        reasons.append("single_full_panel")
    if row.get("panel_count") == "1":
        score += 10
        reasons.append("one_panel")
    if exists_rel(row.get("panel_png_path", "")):
        score += 10
        reasons.append("image_exists")
    if exists_rel(row.get("topology_v1_panel_json_path", "")):
        score += 10
        reasons.append("graph_exists")

    node_count = as_float(row, "v1_node_count")
    edge_count = as_float(row, "v1_edge_count")
    net_count = as_float(row, "v1_net_count")
    isolated_ratio = as_float(row, "v1_isolated_edge_ratio")
    largest_ratio = as_float(row, "v1_largest_net_edge_ratio")

    if node_count > 0 and edge_count > 0 and net_count > 0:
        score += 20
        reasons.append("positive_graph_counts")
    if 50 <= node_count <= 1200 and 80 <= edge_count <= 2200:
        score += 10
        reasons.append("moderate_graph_scale")
    if net_count <= 20:
        score += 6
        reasons.append("small_net_count")
    if isolated_ratio <= 0.02:
        score += 6
        reasons.append("low_isolated_edge_ratio")
    if largest_ratio >= 0.65:
        score += 4
        reasons.append("dominant_connected_component")

    quality_flags = row.get("quality_flags", "")
    if quality_flags:
        score -= 12
        reasons.append(f"quality_flags:{quality_flags}")
    if row.get("topology_panel_v1_policy_decision") in {"baseline", "baseline_accept"}:
        score += 8
        reasons.append("known_v1_baseline_anchor")
    if row.get("topology_panel_v1_policy_decision") == "badcase":
        score -= 40
        reasons.append("known_badcase")
    if row.get("topology_panel_v1_policy_decision") == "improvement_target":
        score -= 12
        reasons.append("known_improvement_target")

    return score, reasons


def priority_bucket(row: Dict[str, str], score: int) -> str:
    if row.get("topology_panel_v1_policy_decision") in {"baseline", "baseline_accept"}:
        return "anchor_existing_v1"
    if row.get("topology_panel_v1_policy_decision") == "badcase":
        return "negative_control_badcase"
    if score >= 80:
        return "high_priority"
    if score >= 60:
        return "medium_priority"
    return "low_priority"


def build_rows(args: argparse.Namespace) -> List[Dict[str, object]]:
    rows = read_csv(args.input)
    out_rows: List[Dict[str, object]] = []
    for row in rows:
        score, reasons = candidate_score(row)
        bucket = priority_bucket(row, score)
        if not args.include_negative_controls and bucket == "negative_control_badcase":
            continue
        if score < args.min_score and bucket not in {"anchor_existing_v1", "negative_control_badcase"}:
            continue
        out = dict(row)
        out.update(
            {
                "v1_5_candidate_score": score,
                "v1_5_candidate_bucket": bucket,
                "v1_5_candidate_reasons": ";".join(reasons),
                "v1_5_target_task": "clean_single_panel_topology",
                "agentic_annotation_status": "pending",
            }
        )
        out_rows.append(out)

    bucket_order = {
        "anchor_existing_v1": 0,
        "high_priority": 1,
        "medium_priority": 2,
        "low_priority": 3,
        "negative_control_badcase": 4,
    }
    out_rows.sort(
        key=lambda row: (
            bucket_order.get(str(row["v1_5_candidate_bucket"]), 9),
            -int(row["v1_5_candidate_score"]),
            str(row.get("panel_id", "")),
        )
    )
    if args.limit:
        out_rows = out_rows[: args.limit]
    return out_rows


def write_report(path: Path, summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1.5 Candidate Manifest Report",
        "",
        "This candidate pool is the input for agentic multi-model annotation.",
        "",
        "## Summary",
        "",
        f"- input rows: {summary['input_rows']}",
        f"- candidate rows: {summary['candidate_rows']}",
        f"- min score: {summary['min_score']}",
        f"- include negative controls: {summary['include_negative_controls']}",
        "",
        "## Bucket Counts",
        "",
    ]
    for key, value in summary["bucket_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Output",
            "",
            f"- `{summary['output_csv']}`",
            f"- `{summary['summary_json']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-score", type=int, default=45)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--include-negative-controls", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_rows = read_csv(args.input)
    rows = build_rows(args)
    if not rows:
        raise SystemExit("No candidate rows selected.")
    fieldnames = list(rows[0].keys())
    write_csv(args.output, rows, fieldnames)
    summary = {
        "input_csv": rel(args.input),
        "output_csv": rel(args.output),
        "summary_json": rel(args.summary),
        "report_md": rel(args.report),
        "input_rows": len(input_rows),
        "candidate_rows": len(rows),
        "min_score": args.min_score,
        "limit": args.limit,
        "include_negative_controls": args.include_negative_controls,
        "bucket_counts": dict(Counter(str(row["v1_5_candidate_bucket"]) for row in rows)),
        "phase_counts": dict(Counter(str(row.get("phase", "")) for row in rows)),
        "policy_decision_counts": dict(Counter(str(row.get("topology_panel_v1_policy_decision", "")) for row in rows)),
        "rules": [
            "This is not a final benchmark manifest.",
            "Rows must pass agentic annotation consensus before entering v1.5.",
            "Existing v1 baseline rows are kept as anchors for calibration.",
            "Known badcases are excluded unless --include-negative-controls is used.",
        ],
    }
    write_json(args.summary, summary)
    write_report(args.report, summary)
    print(f"Candidate rows: {len(rows)}")
    print(f"Wrote: {rel(args.output)}")
    print(f"Wrote: {rel(args.summary)}")
    print(f"Wrote: {rel(args.report)}")


if __name__ == "__main__":
    main()
