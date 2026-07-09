"""Build a prediction JSONL template for Topology Panel v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_BENCHMARK = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_prediction_template.jsonl"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_prediction_template_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_prediction_template_report.md"

TEMPLATE_ID = "topology_panel_v1_prediction_template_2026-07-09"
EXPECTED_SCHEMA = "industrial_diagram.topology_graph.v1_panel"


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


def get_nested(record: Dict[str, object], *keys: str) -> object:
    current: object = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def template_record(record: Dict[str, object]) -> Dict[str, object]:
    topology_summary = get_nested(record, "reference", "topology_summary")
    if not isinstance(topology_summary, dict):
        topology_summary = {}

    return {
        "template_id": TEMPLATE_ID,
        "benchmark_id": record.get("benchmark_id", ""),
        "task": record.get("task", "panel_topology_graph_v1"),
        "panel_id": record.get("panel_id", ""),
        "split": record.get("split", ""),
        "phase": record.get("phase", ""),
        "input": {
            "image_path": get_nested(record, "input", "image_path") or "",
            "image_exists": bool(get_nested(record, "input", "image_exists")),
        },
        "reference": {
            "topology_json_path": get_nested(record, "reference", "topology_json_path") or "",
            "topology_summary": {
                "schema": topology_summary.get("schema", EXPECTED_SCHEMA),
                "status": topology_summary.get("status", ""),
                "node_count": topology_summary.get("node_count", 0),
                "edge_count": topology_summary.get("edge_count", 0),
                "net_count": topology_summary.get("net_count", 0),
            },
        },
        "prediction_schema": EXPECTED_SCHEMA,
        "model": {
            "name": "",
            "version": "",
            "provider": "",
            "prompt_id": "",
            "run_id": "",
        },
        "prediction": None,
        "prediction_json_path": "",
        "metadata": {
            "created_at": "",
            "decoder": "",
            "notes": "",
        },
        "template_instructions": [
            "Fill either `prediction` with an inline topology graph object or `prediction_json_path` with a repository-relative JSON path.",
            "If using inline `prediction`, it should contain schema/status/nodes/edges/nets/stats fields.",
            "Set prediction.status to `ok` when the prediction graph is complete.",
            "Keep panel_id unchanged so the evaluator can align predictions with the benchmark manifest.",
            "Run: python benchmark/topology/evaluate_topology_graph_v1.py --predictions data_index/topology_panel_v1_prediction_template.jsonl",
        ],
    }


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build_summary(records: List[Dict[str, object]], templates: List[Dict[str, object]]) -> Dict[str, object]:
    split_counts: Dict[str, int] = {}
    phase_counts: Dict[str, int] = {}
    for row in templates:
        split = str(row.get("split", ""))
        phase = str(row.get("phase", ""))
        split_counts[split] = split_counts.get(split, 0) + 1
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

    return {
        "template_id": TEMPLATE_ID,
        "source_benchmark": DEFAULT_BENCHMARK.relative_to(ROOT).as_posix(),
        "output_jsonl": DEFAULT_OUTPUT.relative_to(ROOT).as_posix(),
        "record_count": len(templates),
        "source_record_count": len(records),
        "expected_prediction_schema": EXPECTED_SCHEMA,
        "split_counts": split_counts,
        "phase_counts": phase_counts,
        "accepted_prediction_modes": [
            "inline `prediction` topology graph object",
            "`prediction_json_path` repository-relative topology graph JSON path",
            "inline `graph` topology graph object, accepted by evaluator for compatibility",
        ],
        "required_alignment_key": "panel_id",
        "outputs": {
            "jsonl": DEFAULT_OUTPUT.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
        },
    }


def write_summary(path: Path, summary: Dict[str, object]) -> None:
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1 Prediction Template Report",
        "",
        f"Template id: `{summary['template_id']}`",
        "",
        "This template fixes the JSONL format for future model predictions on Topology Panel v1.",
        "",
        "## Summary",
        "",
        f"- Source benchmark: `{summary['source_benchmark']}`",
        f"- Output JSONL: `{summary['output_jsonl']}`",
        f"- Records: {summary['record_count']}",
        f"- Expected prediction schema: `{summary['expected_prediction_schema']}`",
        f"- Required alignment key: `{summary['required_alignment_key']}`",
        "",
        "## Splits",
        "",
    ]
    for split, count in summary["split_counts"].items():
        lines.append(f"- {split}: {count}")

    lines.extend(["", "## Phases", ""])
    for phase, count in summary["phase_counts"].items():
        lines.append(f"- {phase}: {count}")

    lines.extend(["", "## Accepted Prediction Modes", ""])
    for mode in summary["accepted_prediction_modes"]:
        lines.append(f"- {mode}")

    lines.extend(
        [
            "",
            "## Usage",
            "",
            "Fill either the inline `prediction` object or `prediction_json_path` for each row.",
            "",
            "```powershell",
            "python benchmark/topology/evaluate_topology_graph_v1.py --predictions data_index/topology_panel_v1_prediction_template.jsonl",
            "```",
            "",
            "The unfilled template is not a valid model prediction file; it is a format scaffold.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl(args.benchmark)
    templates = [template_record(record) for record in records]
    write_jsonl(args.output, templates)

    summary = build_summary(records, templates)
    write_summary(args.summary, summary)
    write_report(args.report, summary)

    print(f"Template records: {summary['record_count']}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.summary.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.report.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
