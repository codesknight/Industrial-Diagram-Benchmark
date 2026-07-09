"""Build an oracle-minus prediction baseline for Topology Panel v1.

The baseline starts from each reference graph and applies deterministic
destructive perturbations. It is not a model baseline; it is a sensitivity check
for the evaluator.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Dict, Iterable, List, Set


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
OUTPUT_DIR = ROOT / "outputs" / "topology_panel_v1_oracle_minus"

DEFAULT_BENCHMARK = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_PREDICTIONS = INDEX_DIR / "topology_panel_v1_oracle_minus_predictions.jsonl"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_oracle_minus_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_oracle_minus_report.md"

BASELINE_ID = "topology_panel_v1_oracle_minus_2026-07-09"
PREDICTION_SCHEMA = "industrial_diagram.topology_graph.v1_panel"


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
        raise SystemExit(f"Missing reference graph: {path_value}")
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(value: str) -> str:
    keep = []
    for char in value:
        if char.isalnum() or char in "-_#":
            keep.append(char)
        else:
            keep.append("_")
    return "".join(keep).strip("_")[:180]


def select_indices(total: int, count: int, offset: int) -> Set[int]:
    if total <= 0 or count <= 0:
        return set()
    if count >= total:
        return set(range(total))
    step = total / count
    selected: Set[int] = set()
    for i in range(count):
        selected.add(int((i * step + offset) % total))
    while len(selected) < count:
        selected.add((len(selected) * 7919 + offset) % total)
    return selected


def edge_node_ids(edges: Iterable[Dict[str, object]]) -> Set[str]:
    node_ids: Set[str] = set()
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source:
            node_ids.add(source)
        if target:
            node_ids.add(target)
    return node_ids


def perturb_graph(
    graph: Dict[str, object],
    sample_index: int,
    edge_drop_rate: float,
    node_drop_rate: float,
    drop_net_every: int,
) -> Dict[str, object]:
    out = copy.deepcopy(graph)
    nodes = [node for node in out.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in out.get("edges", []) if isinstance(edge, dict)]
    nets = [net for net in out.get("nets", []) if isinstance(net, dict)]

    original_counts = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "net_count": len(nets),
    }

    edge_drop_count = max(1, int(round(len(edges) * edge_drop_rate))) if edges else 0
    edge_drop_indices = select_indices(len(edges), edge_drop_count, sample_index)
    edges = [edge for i, edge in enumerate(edges) if i not in edge_drop_indices]

    node_drop_count = max(1, int(round(len(nodes) * node_drop_rate))) if nodes else 0
    node_drop_indices = select_indices(len(nodes), node_drop_count, sample_index * 3 + 1)
    dropped_node_ids = {
        str(node.get("id", ""))
        for i, node in enumerate(nodes)
        if i in node_drop_indices and str(node.get("id", ""))
    }
    nodes = [node for node in nodes if str(node.get("id", "")) not in dropped_node_ids]
    edges = [
        edge
        for edge in edges
        if str(edge.get("source", "")) not in dropped_node_ids
        and str(edge.get("target", "")) not in dropped_node_ids
    ]

    referenced_node_ids = edge_node_ids(edges)
    nodes = [node for node in nodes if str(node.get("id", "")) in referenced_node_ids]

    if drop_net_every > 0 and sample_index % drop_net_every == 0:
        nets = []
    elif nets:
        nets = [copy.deepcopy(nets[0])]
        nets[0]["node_count"] = len(nodes)
        nets[0]["edge_count"] = len(edges)

    stats = out.get("stats", {})
    if not isinstance(stats, dict):
        stats = {}
    stats["node_count"] = len(nodes)
    stats["edge_count"] = len(edges)
    stats["net_count"] = len(nets)
    stats["largest_net_edges"] = len(edges) if nets else 0
    stats["isolated_edge_count"] = 0
    stats["isolated_edge_ratio"] = 0.0
    stats["largest_net_edge_ratio"] = 1.0 if edges and nets else 0.0

    out["schema"] = out.get("schema") or PREDICTION_SCHEMA
    out["status"] = "ok"
    out["stats"] = stats
    out["nodes"] = nodes
    out["edges"] = edges
    out["nets"] = nets
    out["oracle_minus"] = {
        "baseline_id": BASELINE_ID,
        "edge_drop_rate": edge_drop_rate,
        "node_drop_rate": node_drop_rate,
        "drop_net_every": drop_net_every,
        "original_counts": original_counts,
        "prediction_counts": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "net_count": len(nets),
        },
        "count_deltas": {
            "node_count": len(nodes) - original_counts["node_count"],
            "edge_count": len(edges) - original_counts["edge_count"],
            "net_count": len(nets) - original_counts["net_count"],
        },
    }
    return out


def write_json(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build_summary(rows: List[Dict[str, object]]) -> Dict[str, object]:
    node_abs_errors = [abs(int(row["count_deltas"]["node_count"])) for row in rows]
    edge_abs_errors = [abs(int(row["count_deltas"]["edge_count"])) for row in rows]
    net_abs_errors = [abs(int(row["count_deltas"]["net_count"])) for row in rows]
    return {
        "baseline_id": BASELINE_ID,
        "prediction_rows": len(rows),
        "rows_with_node_error": sum(1 for value in node_abs_errors if value > 0),
        "rows_with_edge_error": sum(1 for value in edge_abs_errors if value > 0),
        "rows_with_net_error": sum(1 for value in net_abs_errors if value > 0),
        "mean_abs_node_error": round(sum(node_abs_errors) / max(len(rows), 1), 6),
        "mean_abs_edge_error": round(sum(edge_abs_errors) / max(len(rows), 1), 6),
        "mean_abs_net_error": round(sum(net_abs_errors) / max(len(rows), 1), 6),
        "outputs": {
            "predictions": DEFAULT_PREDICTIONS.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
            "prediction_graph_dir": OUTPUT_DIR.relative_to(ROOT).as_posix(),
        },
    }


def write_report(path: Path, summary: Dict[str, object], rows: List[Dict[str, object]]) -> None:
    lines = [
        "# Topology Panel v1 Oracle-Minus Baseline Report",
        "",
        f"Baseline id: `{summary['baseline_id']}`",
        "",
        "This baseline copies reference graphs and applies deterministic destructive perturbations.",
        "It is intended to validate metric sensitivity, not to represent model performance.",
        "",
        "## Summary",
        "",
        f"- Prediction rows: {summary['prediction_rows']}",
        f"- Rows with node error: {summary['rows_with_node_error']}",
        f"- Rows with edge error: {summary['rows_with_edge_error']}",
        f"- Rows with net error: {summary['rows_with_net_error']}",
        f"- Mean absolute node error: {summary['mean_abs_node_error']}",
        f"- Mean absolute edge error: {summary['mean_abs_edge_error']}",
        f"- Mean absolute net error: {summary['mean_abs_net_error']}",
        "",
        "## Outputs",
        "",
    ]
    for name, output_path in summary["outputs"].items():
        lines.append(f"- {name}: `{output_path}`")
    lines.extend(
        [
            "",
            "The prediction JSONL is self-contained: each row includes an inline `prediction` graph.",
            "`prediction_json_path` is retained as an optional local debugging path.",
        ]
    )
    lines.extend(["", "## Rows", ""])
    for row in rows:
        deltas = row["count_deltas"]
        lines.append(
            f"- `{row['panel_id']}`: "
            f"node {deltas['node_count']}, edge {deltas['edge_count']}, net {deltas['net_count']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--prediction-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--edge-drop-rate", type=float, default=0.05)
    parser.add_argument("--node-drop-rate", type=float, default=0.01)
    parser.add_argument("--drop-net-every", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl(args.benchmark)
    prediction_rows: List[Dict[str, object]] = []
    report_rows: List[Dict[str, object]] = []

    for sample_index, record in enumerate(records):
        panel_id = str(record.get("panel_id", ""))
        reference_path = str(record.get("reference", {}).get("topology_json_path", ""))
        reference_graph = load_json(reference_path)
        prediction_graph = perturb_graph(
            reference_graph,
            sample_index=sample_index,
            edge_drop_rate=args.edge_drop_rate,
            node_drop_rate=args.node_drop_rate,
            drop_net_every=args.drop_net_every,
        )
        graph_path = args.prediction_dir / f"{safe_name(panel_id)}.oracle_minus.topology.v1.json"
        write_json(graph_path, prediction_graph)
        graph_rel = graph_path.resolve().relative_to(ROOT).as_posix()

        prediction_rows.append(
            {
                "baseline_id": BASELINE_ID,
                "benchmark_id": record.get("benchmark_id", ""),
                "task": record.get("task", "panel_topology_graph_v1"),
                "panel_id": panel_id,
                "split": record.get("split", ""),
                "phase": record.get("phase", ""),
                "model": {
                    "name": "oracle_minus",
                    "version": "2026-07-09",
                    "provider": "local_script",
                },
                "prediction_json_path": graph_rel,
                "prediction": prediction_graph,
                "prediction_schema": PREDICTION_SCHEMA,
            }
        )
        report_rows.append(
            {
                "panel_id": panel_id,
                "count_deltas": prediction_graph["oracle_minus"]["count_deltas"],
            }
        )

    write_jsonl(args.predictions, prediction_rows)
    summary = build_summary(report_rows)
    write_json(args.summary, summary)
    write_report(args.report, summary, report_rows)

    print(f"Oracle-minus predictions: {len(prediction_rows)}")
    print(f"Wrote: {args.predictions.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.summary.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.report.relative_to(ROOT).as_posix()}")
    print(f"Wrote graphs under: {args.prediction_dir.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
