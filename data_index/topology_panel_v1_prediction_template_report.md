# Topology Panel v1 Prediction Template Report

Template id: `topology_panel_v1_prediction_template_2026-07-09`

This template fixes the JSONL format for future model predictions on Topology Panel v1.

## Summary

- Source benchmark: `data_index/topology_panel_v1_benchmark_manifest.jsonl`
- Output JSONL: `data_index/topology_panel_v1_prediction_template.jsonl`
- Records: 14
- Expected prediction schema: `industrial_diagram.topology_graph.v1_panel`
- Required alignment key: `panel_id`

## Splits

- test: 2
- train: 11
- val: 1

## Phases

- P1: 4
- P3: 9
- P2: 1

## Accepted Prediction Modes

- inline `prediction` topology graph object
- `prediction_json_path` repository-relative topology graph JSON path
- inline `graph` topology graph object, accepted by evaluator for compatibility

## Usage

Fill either the inline `prediction` object or `prediction_json_path` for each row.

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py --predictions data_index/topology_panel_v1_prediction_template.jsonl
```

The unfilled template is not a valid model prediction file; it is a format scaffold.
