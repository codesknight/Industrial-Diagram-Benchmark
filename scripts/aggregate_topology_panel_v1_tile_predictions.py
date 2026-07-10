"""Aggregate tile-level topology count predictions back to panel level."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List

from run_topology_panel_v1_model_prediction_adapter import EXPECTED_SCHEMA, synthetic_graph


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_BENCHMARK = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_TILE_PREDICTIONS = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_tile_predictions.jsonl"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_panel_predictions.jsonl"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_panel_predictions_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_panel_predictions_report.md"


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def source_panel_id(tile_panel_id: str) -> str:
    marker = "#tile_"
    if marker in tile_panel_id:
        return tile_panel_id.split(marker, 1)[0]
    return tile_panel_id


def count_from_tile(row: Dict[str, object], key: str) -> int:
    metadata = row.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get(f"model_{key}") is not None:
        try:
            return max(0, int(metadata.get(f"model_{key}", 0)))
        except (TypeError, ValueError):
            pass
    prediction = row.get("prediction", {})
    if isinstance(prediction, dict):
        stats = prediction.get("stats", {})
        if isinstance(stats, dict):
            try:
                return max(0, int(stats.get(key, 0)))
            except (TypeError, ValueError):
                return 0
    return 0


def aggregate_counts(tile_rows: List[Dict[str, object]], net_strategy: str) -> Dict[str, int]:
    node_counts = [count_from_tile(row, "node_count") for row in tile_rows]
    edge_counts = [count_from_tile(row, "edge_count") for row in tile_rows]
    net_counts = [count_from_tile(row, "net_count") for row in tile_rows]
    if net_strategy == "sum":
        net_count = sum(net_counts)
    elif net_strategy == "mean_round":
        net_count = int(round(mean(net_counts))) if net_counts else 0
    elif net_strategy == "mean_clamped3":
        net_count = min(3, max(1, int(round(mean(net_counts))))) if net_counts else 0
    else:
        net_count = max(net_counts) if net_counts else 0
    return {
        "node_count": sum(node_counts),
        "edge_count": sum(edge_counts),
        "net_count": max(0, net_count),
    }


def aggregate(args: argparse.Namespace) -> List[Dict[str, object]]:
    benchmark_rows = load_jsonl(args.benchmark)
    benchmark_by_panel = {str(row.get("panel_id", "")): row for row in benchmark_rows}
    tile_rows = load_jsonl(args.tile_predictions)
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in tile_rows:
        grouped[source_panel_id(str(row.get("panel_id", "")))].append(row)

    panel_predictions: List[Dict[str, object]] = []
    for panel_id, benchmark_row in benchmark_by_panel.items():
        tiles = grouped.get(panel_id, [])
        counts = aggregate_counts(tiles, args.net_strategy)
        status_counts = Counter(str(row.get("metadata", {}).get("model_status", "")) for row in tiles if isinstance(row.get("metadata"), dict))
        adapter_error_counts = Counter(str(row.get("metadata", {}).get("adapter_error", "")) or "none" for row in tiles if isinstance(row.get("metadata"), dict))
        status = "ok" if tiles and counts["node_count"] > 0 and counts["edge_count"] > 0 else "uncertain"
        reason = f"aggregated {len(tiles)} tile predictions with node/edge=sum and net={args.net_strategy}"
        graph = synthetic_graph(counts["node_count"], counts["edge_count"], counts["net_count"], status, reason)
        panel_predictions.append(
            {
                "adapter_id": "topology_panel_v1_doubao_adapter_v3_tile2x2_2026-07-10",
                "benchmark_id": benchmark_row.get("benchmark_id", ""),
                "task": benchmark_row.get("task", "panel_topology_graph_v1"),
                "panel_id": panel_id,
                "split": benchmark_row.get("split", ""),
                "phase": benchmark_row.get("phase", ""),
                "model": {
                    "provider": args.provider,
                    "name": args.model_name,
                    "adapter_mode": "tile2x2_sum_counts",
                    "dry_run": False,
                },
                "prediction": graph,
                "prediction_schema": EXPECTED_SCHEMA,
                "metadata": {
                    "adapter_mode": "tile2x2_sum_counts",
                    "adapter_error": "" if tiles else "missing_tiles",
                    "tile_count": len(tiles),
                    "tile_panel_ids": [row.get("panel_id", "") for row in tiles],
                    "tile_status_counts": dict(status_counts),
                    "tile_adapter_error_counts": dict(adapter_error_counts),
                    "aggregation": {
                        "node_count": "sum",
                        "edge_count": "sum",
                        "net_count": args.net_strategy,
                    },
                    "model_status": status,
                    "model_node_count": counts["node_count"],
                    "model_edge_count": counts["edge_count"],
                    "model_net_count": counts["net_count"],
                    "model_confidence": 0.0,
                    "model_reason": reason,
                },
            }
        )
    return panel_predictions


def write_summary(args: argparse.Namespace, rows: List[Dict[str, object]]) -> None:
    mode_counts = Counter(str(row.get("model", {}).get("adapter_mode", "")) for row in rows)
    error_counts = Counter(str(row.get("metadata", {}).get("adapter_error", "")) or "none" for row in rows)
    tile_counts = [int(row.get("metadata", {}).get("tile_count", 0)) for row in rows if isinstance(row.get("metadata"), dict)]
    summary = {
        "adapter_id": "topology_panel_v1_doubao_adapter_v3_tile2x2_2026-07-10",
        "provider": args.provider,
        "model": args.model_name,
        "prompt_version": "v3",
        "input_version": "tile2x2_512px_250k",
        "tile_predictions": rel(args.tile_predictions),
        "output_predictions": rel(args.output),
        "prediction_rows": len(rows),
        "adapter_mode_counts": dict(mode_counts),
        "adapter_error_counts": dict(error_counts),
        "tile_count_min": min(tile_counts) if tile_counts else 0,
        "tile_count_max": max(tile_counts) if tile_counts else 0,
        "aggregation": {
            "node_count": "sum",
            "edge_count": "sum",
            "net_count": args.net_strategy,
        },
        "rules": [
            "Tile-level model predictions are aggregated back to panel-level predictions.",
            "This is a count-level image-input experiment, not a full geometry reconstruction.",
        ],
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(args: argparse.Namespace, rows: List[Dict[str, object]]) -> None:
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    lines = [
        "# Topology Panel v1 Tile2x2 Aggregation Report",
        "",
        f"Adapter id: `{summary['adapter_id']}`",
        "",
        "## Summary",
        "",
        f"- Provider: {summary['provider']}",
        f"- Model: {summary['model']}",
        f"- Prompt version: {summary['prompt_version']}",
        f"- Input version: {summary['input_version']}",
        f"- Prediction rows: {summary['prediction_rows']}",
        f"- Tile count per panel: {summary['tile_count_min']} to {summary['tile_count_max']}",
        f"- Aggregation: node=sum, edge=sum, net={summary['aggregation']['net_count']}",
        "",
        "## Outputs",
        "",
        f"- Tile predictions: `{summary['tile_predictions']}`",
        f"- Panel predictions: `{summary['output_predictions']}`",
        f"- Summary: `{rel(args.summary)}`",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--tile-predictions", type=Path, default=DEFAULT_TILE_PREDICTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--provider", default="doubao")
    parser.add_argument("--model-name", default="doubao-seed-2-0-pro-260215")
    parser.add_argument("--net-strategy", choices=["max", "sum", "mean_round", "mean_clamped3"], default="mean_clamped3")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = aggregate(args)
    write_jsonl(args.output, rows)
    write_summary(args, rows)
    write_report(args, rows)
    print(f"Panel predictions: {len(rows)}")
    print(f"Wrote: {rel(args.output)}")
    print(f"Wrote: {rel(args.summary)}")
    print(f"Wrote: {rel(args.report)}")


if __name__ == "__main__":
    main()
