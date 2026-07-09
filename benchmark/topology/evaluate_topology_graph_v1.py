"""Evaluate Topology Panel v1 benchmark graphs.

Default mode evaluates the reference graphs listed in the benchmark JSONL.
An optional predictions JSONL can be supplied later to compare predicted graph
counts against the reference package.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = ROOT / "data_index"

DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_eval_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_eval_report.md"
DEFAULT_DETAILS = INDEX_DIR / "topology_panel_v1_eval_details.csv"
DEFAULT_ERRORS = INDEX_DIR / "topology_panel_v1_eval_errors.csv"


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        raise SystemExit(f"Missing JSONL: {path}")
    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def load_json(path_value: str) -> Dict[str, object]:
    path = ROOT / path_value
    if not path.exists():
        return {"_load_error": "missing_file"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"_load_error": f"json_decode_error: {exc}"}


def as_float(value: object) -> float:
    try:
        return float(str(value or 0))
    except ValueError:
        return 0.0


def as_int(value: object) -> int:
    return int(round(as_float(value)))


def get_nested(record: Dict[str, object], *keys: str) -> object:
    current: object = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def graph_counts_from_record(record: Dict[str, object]) -> Dict[str, int]:
    stats = record.get("graph_stats", {})
    if not isinstance(stats, dict):
        stats = {}
    summary = get_nested(record, "reference", "topology_summary")
    if not isinstance(summary, dict):
        summary = {}
    return {
        "node_count": as_int(stats.get("node_count", summary.get("node_count", 0))),
        "edge_count": as_int(stats.get("edge_count", summary.get("edge_count", 0))),
        "net_count": as_int(stats.get("net_count", summary.get("net_count", 0))),
    }


def graph_counts_from_graph(graph: Dict[str, object]) -> Dict[str, int]:
    stats = graph.get("stats", {})
    if not isinstance(stats, dict):
        stats = {}
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    nets = graph.get("nets", [])
    return {
        "node_count": as_int(stats.get("node_count", len(nodes) if isinstance(nodes, list) else 0)),
        "edge_count": as_int(stats.get("edge_count", len(edges) if isinstance(edges, list) else 0)),
        "net_count": as_int(stats.get("net_count", len(nets) if isinstance(nets, list) else 0)),
    }


def validate_graph(graph: Dict[str, object]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if graph.get("_load_error"):
        return False, [str(graph["_load_error"])]

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    nets = graph.get("nets")
    if not isinstance(nodes, list):
        reasons.append("nodes_missing_or_not_list")
        nodes = []
    if not isinstance(edges, list):
        reasons.append("edges_missing_or_not_list")
        edges = []
    if not isinstance(nets, list):
        reasons.append("nets_missing_or_not_list")
        nets = []

    status = str(graph.get("status", ""))
    if status and status != "ok":
        reasons.append(f"status_{status}")

    node_ids = {
        str(node.get("id", ""))
        for node in nodes
        if isinstance(node, dict) and node.get("id", "") != ""
    }
    if len(node_ids) != len(nodes):
        reasons.append("node_id_missing_or_duplicate")

    missing_edge_refs = 0
    for edge in edges:
        if not isinstance(edge, dict):
            missing_edge_refs += 1
            continue
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source not in node_ids or target not in node_ids:
            missing_edge_refs += 1
    if missing_edge_refs:
        reasons.append(f"missing_edge_refs_{missing_edge_refs}")

    bad_nets = 0
    for net in nets:
        if not isinstance(net, dict):
            bad_nets += 1
            continue
        if as_int(net.get("node_count", 0)) < 0 or as_int(net.get("edge_count", 0)) < 0:
            bad_nets += 1
    if bad_nets:
        reasons.append(f"bad_net_counts_{bad_nets}")

    return not reasons, reasons


def load_predictions(path: Path | None) -> Dict[str, Dict[str, object]]:
    if path is None:
        return {}
    rows = load_jsonl(path)
    predictions: Dict[str, Dict[str, object]] = {}
    for row in rows:
        panel_id = str(row.get("panel_id", ""))
        if panel_id:
            predictions[panel_id] = row
    return predictions


def prediction_graph(row: Dict[str, object]) -> Dict[str, object]:
    graph = row.get("prediction")
    if isinstance(graph, dict):
        return graph
    graph = row.get("graph")
    if isinstance(graph, dict):
        return graph
    path_value = row.get("prediction_json_path") or row.get("topology_json_path")
    if isinstance(path_value, str) and path_value:
        return load_json(path_value)
    return row


def abs_rel_error(pred: int, ref: int) -> Dict[str, float]:
    abs_error = abs(pred - ref)
    return {
        "abs": float(abs_error),
        "rel": round(abs_error / max(ref, 1), 6),
    }


def mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


def numeric_stats(values: Iterable[float]) -> Dict[str, float]:
    values = list(values)
    if not values:
        return {"min": 0.0, "max": 0.0, "mean": 0.0}
    return {"min": min(values), "max": max(values), "mean": mean(values)}


def join_reasons(reasons: object) -> str:
    if isinstance(reasons, list):
        return ";".join(str(reason) for reason in reasons)
    return str(reasons or "")


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def evaluate(records: List[Dict[str, object]], predictions: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    reference_valid = 0
    prediction_valid = 0
    prediction_available = 0

    for record in records:
        panel_id = str(record.get("panel_id", ""))
        reference_path = str(get_nested(record, "reference", "topology_json_path") or "")
        reference_graph = load_json(reference_path)
        ref_valid, ref_reasons = validate_graph(reference_graph)
        reference_valid += int(ref_valid)
        ref_counts = graph_counts_from_record(record)

        pred_row = predictions.get(panel_id)
        pred_counts = ref_counts
        pred_valid = ref_valid
        pred_reasons: List[str] = []
        mode = "reference_as_prediction"
        if pred_row is not None:
            prediction_available += 1
            mode = "external_prediction"
            graph = prediction_graph(pred_row)
            pred_valid, pred_reasons = validate_graph(graph)
            pred_counts = graph_counts_from_graph(graph)
            prediction_valid += int(pred_valid)

        errors = {
            "node_count": abs_rel_error(pred_counts["node_count"], ref_counts["node_count"]),
            "edge_count": abs_rel_error(pred_counts["edge_count"], ref_counts["edge_count"]),
            "net_count": abs_rel_error(pred_counts["net_count"], ref_counts["net_count"]),
        }
        graph_stats = record.get("graph_stats", {})
        if not isinstance(graph_stats, dict):
            graph_stats = {}
        rows.append(
            {
                "panel_id": panel_id,
                "split": record.get("split", ""),
                "phase": record.get("phase", ""),
                "mode": mode,
                "reference_valid": ref_valid,
                "reference_invalid_reasons": ref_reasons,
                "prediction_valid": pred_valid,
                "prediction_invalid_reasons": pred_reasons,
                "reference_counts": ref_counts,
                "prediction_counts": pred_counts,
                "errors": errors,
                "isolated_edge_ratio": as_float(graph_stats.get("isolated_edge_ratio", 0)),
                "largest_net_edge_ratio": as_float(graph_stats.get("largest_net_edge_ratio", 0)),
            }
        )

    total = len(rows)
    available_prediction_denominator = prediction_available if prediction_available else total
    invalid_reference_rows = [row["panel_id"] for row in rows if not row["reference_valid"]]
    invalid_prediction_rows = [row["panel_id"] for row in rows if not row["prediction_valid"]]

    summary = {
        "benchmark_id": records[0].get("benchmark_id", "") if records else "",
        "manifest": DEFAULT_MANIFEST.relative_to(ROOT).as_posix(),
        "prediction_mode": "external_prediction" if predictions else "reference_as_prediction",
        "evaluated_rows": total,
        "prediction_rows": prediction_available,
        "split_counts": dict(Counter(str(row.get("split", "")) for row in rows)),
        "phase_counts": dict(Counter(str(row.get("phase", "")) for row in rows)),
        "graph_valid_rate": {
            "reference": round(reference_valid / max(total, 1), 6),
            "prediction": round(
                (prediction_valid if predictions else reference_valid) / max(available_prediction_denominator, 1),
                6,
            ),
        },
        "count_errors": {
            name: {
                "mae": mean(row["errors"][name]["abs"] for row in rows),
                "mre": mean(row["errors"][name]["rel"] for row in rows),
            }
            for name in ["node_count", "edge_count", "net_count"]
        },
        "diagnostics": {
            "isolated_edge_ratio": numeric_stats(row["isolated_edge_ratio"] for row in rows),
            "largest_net_edge_ratio": numeric_stats(row["largest_net_edge_ratio"] for row in rows),
        },
        "invalid_reference_rows": invalid_reference_rows,
        "invalid_prediction_rows": invalid_prediction_rows,
        "rows": rows,
        "outputs": {
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
            "details_csv": DEFAULT_DETAILS.relative_to(ROOT).as_posix(),
            "errors_csv": DEFAULT_ERRORS.relative_to(ROOT).as_posix(),
        },
    }
    return summary


def write_summary(summary: Dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def flatten_eval_row(row: Dict[str, object]) -> Dict[str, object]:
    ref_counts = row.get("reference_counts", {})
    if not isinstance(ref_counts, dict):
        ref_counts = {}
    pred_counts = row.get("prediction_counts", {})
    if not isinstance(pred_counts, dict):
        pred_counts = {}
    errors = row.get("errors", {})
    if not isinstance(errors, dict):
        errors = {}

    out: Dict[str, object] = {
        "panel_id": row.get("panel_id", ""),
        "split": row.get("split", ""),
        "phase": row.get("phase", ""),
        "mode": row.get("mode", ""),
        "reference_valid": row.get("reference_valid", False),
        "prediction_valid": row.get("prediction_valid", False),
        "reference_invalid_reasons": join_reasons(row.get("reference_invalid_reasons", [])),
        "prediction_invalid_reasons": join_reasons(row.get("prediction_invalid_reasons", [])),
        "reference_node_count": ref_counts.get("node_count", 0),
        "reference_edge_count": ref_counts.get("edge_count", 0),
        "reference_net_count": ref_counts.get("net_count", 0),
        "prediction_node_count": pred_counts.get("node_count", 0),
        "prediction_edge_count": pred_counts.get("edge_count", 0),
        "prediction_net_count": pred_counts.get("net_count", 0),
        "isolated_edge_ratio": row.get("isolated_edge_ratio", 0),
        "largest_net_edge_ratio": row.get("largest_net_edge_ratio", 0),
    }
    for name in ["node_count", "edge_count", "net_count"]:
        metric = errors.get(name, {})
        if not isinstance(metric, dict):
            metric = {}
        out[f"{name}_abs_error"] = metric.get("abs", 0.0)
        out[f"{name}_rel_error"] = metric.get("rel", 0.0)
    return out


def is_error_row(row: Dict[str, object]) -> bool:
    if not row.get("reference_valid", False):
        return True
    if not row.get("prediction_valid", False):
        return True
    errors = row.get("errors", {})
    if not isinstance(errors, dict):
        return True
    for name in ["node_count", "edge_count", "net_count"]:
        metric = errors.get(name, {})
        if isinstance(metric, dict) and as_float(metric.get("abs", 0)) > 0:
            return True
    return False


def write_eval_csv(rows: List[Dict[str, object]], path: Path) -> None:
    fieldnames = [
        "panel_id",
        "split",
        "phase",
        "mode",
        "reference_valid",
        "prediction_valid",
        "reference_invalid_reasons",
        "prediction_invalid_reasons",
        "reference_node_count",
        "reference_edge_count",
        "reference_net_count",
        "prediction_node_count",
        "prediction_edge_count",
        "prediction_net_count",
        "node_count_abs_error",
        "node_count_rel_error",
        "edge_count_abs_error",
        "edge_count_rel_error",
        "net_count_abs_error",
        "net_count_rel_error",
        "isolated_edge_ratio",
        "largest_net_edge_ratio",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(flatten_eval_row(row))


def write_report(summary: Dict[str, object], path: Path) -> None:
    lines = [
        "# Topology Panel v1 Evaluation Report",
        "",
        f"Benchmark id: `{summary['benchmark_id']}`",
        "",
        "This report evaluates the Topology Panel v1 benchmark package according to `docs/topology_graph_eval_protocol_v1.md`.",
        "",
        "## Summary",
        "",
        f"- Prediction mode: {summary['prediction_mode']}",
        f"- Evaluated rows: {summary['evaluated_rows']}",
        f"- Prediction rows: {summary['prediction_rows']}",
        f"- Reference graph valid rate: {summary['graph_valid_rate']['reference']}",
        f"- Prediction graph valid rate: {summary['graph_valid_rate']['prediction']}",
        "",
        "## Splits",
        "",
    ]
    for split, count in summary["split_counts"].items():
        lines.append(f"- {split}: {count}")

    lines.extend(["", "## Phases", ""])
    for phase, count in summary["phase_counts"].items():
        lines.append(f"- {phase}: {count}")

    lines.extend(["", "## Count Errors", ""])
    for name, stats in summary["count_errors"].items():
        lines.append(f"- {name}: MAE={stats['mae']}, MRE={stats['mre']}")

    lines.extend(["", "## Diagnostics", ""])
    for name, stats in summary["diagnostics"].items():
        lines.append(f"- {name}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")

    lines.extend(["", "## Invalid Rows", ""])
    lines.append(f"- Reference invalid rows: {len(summary['invalid_reference_rows'])}")
    lines.append(f"- Prediction invalid rows: {len(summary['invalid_prediction_rows'])}")

    if summary["invalid_reference_rows"]:
        lines.extend(["", "### Reference Invalid Panel Ids", ""])
        for panel_id in summary["invalid_reference_rows"]:
            lines.append(f"- `{panel_id}`")
    if summary["invalid_prediction_rows"]:
        lines.extend(["", "### Prediction Invalid Panel Ids", ""])
        for panel_id in summary["invalid_prediction_rows"]:
            lines.append(f"- `{panel_id}`")

    lines.extend(["", "## Outputs", ""])
    for name, output_path in summary["outputs"].items():
        lines.append(f"- {name}: `{output_path}`")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--predictions", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--details-csv", type=Path, default=DEFAULT_DETAILS)
    parser.add_argument("--errors-csv", type=Path, default=DEFAULT_ERRORS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl(args.manifest)
    predictions = load_predictions(args.predictions)
    summary = evaluate(records, predictions)
    summary["outputs"]["summary"] = display_path(args.summary)
    summary["outputs"]["report"] = display_path(args.report)
    summary["outputs"]["details_csv"] = display_path(args.details_csv)
    summary["outputs"]["errors_csv"] = display_path(args.errors_csv)
    write_summary(summary, args.summary)
    write_report(summary, args.report)
    write_eval_csv(summary["rows"], args.details_csv)
    write_eval_csv([row for row in summary["rows"] if is_error_row(row)], args.errors_csv)

    print(f"Evaluated rows: {summary['evaluated_rows']}")
    print(f"Prediction mode: {summary['prediction_mode']}")
    print(f"Reference graph valid rate: {summary['graph_valid_rate']['reference']}")
    print(f"Prediction graph valid rate: {summary['graph_valid_rate']['prediction']}")
    print(f"Wrote: {display_path(args.summary)}")
    print(f"Wrote: {display_path(args.report)}")
    print(f"Wrote: {display_path(args.details_csv)}")
    print(f"Wrote: {display_path(args.errors_csv)}")


if __name__ == "__main__":
    main()
