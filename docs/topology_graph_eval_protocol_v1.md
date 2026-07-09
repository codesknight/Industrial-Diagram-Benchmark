# Topology Graph v1 Evaluation Protocol

This document defines the first formal evaluation protocol for panel-level
Topology Graph v1 in Industrial Diagram Benchmark.

The current v1 protocol is intentionally conservative. It evaluates graph
structure on manually confirmed single-diagram panels only. Multi-subfigure
panels are treated as badcases and are excluded from the baseline score.

## Release Scope

Use the final baseline manifest:

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

Current release size:

```text
total: 14
train: 11
val: 1
test: 2
P1: 4
P2: 1
P3: 9
```

Supporting manifests:

```text
data_index/topology_panel_v1_release_excluded_manifest.csv
data_index/topology_panel_v1_release_improvement_manifest.csv
data_index/topology_panel_v1_badcase_manifest.csv
data_index/topology_panel_v1_final_baseline_summary.json
data_index/topology_panel_v1_final_baseline_report.md
```

## Task Definition

The evaluation task is panel-level topology extraction.

Input:

```text
panel PNG image
```

Expected output:

```text
Topology Graph JSON
```

The graph should represent wire-like geometry as nodes, edges, and connected
components. A valid output must be machine-readable JSON and must preserve the
basic graph structure needed for downstream industrial diagram reasoning.

## Reference Graph

The reference graph for the v1 baseline is the local Topology Graph v1 JSON
listed in:

```text
topology_v1_panel_json_path
```

The current reference graph is produced by the repository's intersection-aware
panel topology builder. It is a first engineering baseline, not a full semantic
ground truth. Therefore, metrics in this protocol focus on structural validity
and graph-level consistency rather than exact semantic correctness.

## Expected JSON Schema

Each prediction should follow the same high-level structure as the v1 reference
JSON:

```json
{
  "schema": "industrial_diagram.topology_graph.v1_panel",
  "status": "ok",
  "stats": {},
  "nodes": [],
  "edges": [],
  "nets": []
}
```

Required node fields:

```text
id
point
degree
```

Required edge fields:

```text
id
source
target
points
length
```

Recommended edge fields:

```text
segment_id
entity_id
entity_type
layer
```

Required net fields:

```text
id
node_count
edge_count
bbox
```

## Evaluation Partitions

Only rows with final label `confirmed_baseline` are used for the formal v1
baseline score.

Use:

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

Do not include:

```text
data_index/topology_panel_v1_release_excluded_manifest.csv
```

Do not score these as baseline examples:

- `multi_subfigure_badcase`
- `bad_geometry`
- `not_topology_target`
- `unreviewed`

Use the improvement manifest for algorithm development and error analysis:

```text
data_index/topology_panel_v1_release_improvement_manifest.csv
```

Improvement labels:

- `still_fragmented`
- `needs_terminal_anchor`
- `over_connected`

These rows are not part of the formal v1 score, but they should guide v1.1
repair work.

## Primary Metrics

### 1. Graph Valid Rate

Definition:

```text
valid_graph_count / total_evaluated_count
```

A graph is valid if:

- JSON can be parsed.
- `status` is `ok` or an equivalent success marker.
- `nodes`, `edges`, and `nets` are present.
- Every edge references existing source and target node ids.
- Every net has a non-negative node and edge count.

### 2. Node Count Error

Compare predicted node count against reference node count:

```text
abs(pred_nodes - ref_nodes)
relative_error = abs(pred_nodes - ref_nodes) / max(ref_nodes, 1)
```

Use both mean absolute error and mean relative error.

### 3. Edge Count Error

Compare predicted edge count against reference edge count:

```text
abs(pred_edges - ref_edges)
relative_error = abs(pred_edges - ref_edges) / max(ref_edges, 1)
```

Use both mean absolute error and mean relative error.

### 4. Net Count Error

Compare predicted connected component count against reference net count:

```text
abs(pred_nets - ref_nets)
relative_error = abs(pred_nets - ref_nets) / max(ref_nets, 1)
```

Net count is important because topology extraction should preserve whether the
panel is one connected network or several independent networks.

### 5. Isolated Edge Ratio

Definition:

```text
isolated_edge_count / max(edge_count, 1)
```

High isolated edge ratio usually indicates fragmentation or failed endpoint
merging.

### 6. Largest Net Edge Ratio

Definition:

```text
largest_net_edges / max(edge_count, 1)
```

This value helps detect two opposite failures:

- Too low: graph is fragmented.
- Too high in dense crossing drawings: graph may be over-connected.

### 7. Human Accept Rate

Definition:

```text
human_accepted_count / manually_reviewed_count
```

The current final baseline has already passed human review:

```text
confirmed_baseline: 14
needs_recheck: 0
remove_from_baseline: 0
```

For future model predictions, use the same manual labels:

- `accept`
- `needs_recheck`
- `reject`

## Secondary Diagnostics

Report these fields when available:

- `intersection_count`
- `split_event_count`
- `effective_endpoint_tolerance`
- edge type counts
- node degree histogram
- largest connected component size
- missing asset count
- prediction runtime

These diagnostics are not primary scores, but they are useful for explaining
failure cases.

## Baseline Reporting Format

The evaluation report should include:

```text
release id
manifest path
evaluated row count
split-level row counts
phase-level row counts
graph valid rate
node count MAE / MRE
edge count MAE / MRE
net count MAE / MRE
isolated edge ratio mean / max
largest net edge ratio mean / min / max
failed sample ids
```

Recommended output files:

```text
data_index/topology_panel_v1_eval_summary.json
data_index/topology_panel_v1_eval_report.md
data_index/topology_panel_v1_eval_details.csv
data_index/topology_panel_v1_eval_errors.csv
```

## Official Sanity Baselines

The v1 protocol includes two official sanity baselines. These are intended to
validate the benchmark package and evaluator behavior before reporting real
model results.

### Reference-as-Prediction

Command:

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py
```

This mode uses the reference graph as the prediction. It should produce zero
count error and confirms that the benchmark JSONL, reference graph paths, and
evaluation code are internally consistent.

Expected result for the current release:

```text
evaluated_rows: 14
prediction_mode: reference_as_prediction
reference graph valid rate: 1.0
prediction graph valid rate: 1.0
node_count MAE/MRE: 0.0 / 0.0
edge_count MAE/MRE: 0.0 / 0.0
net_count MAE/MRE: 0.0 / 0.0
error rows: 0
```

Primary outputs:

```text
data_index/topology_panel_v1_eval_summary.json
data_index/topology_panel_v1_eval_report.md
data_index/topology_panel_v1_eval_details.csv
data_index/topology_panel_v1_eval_errors.csv
```

### Oracle-Minus

Command:

```powershell
python scripts/build_topology_panel_v1_oracle_minus_baseline.py
python benchmark/topology/evaluate_topology_graph_v1.py `
  --predictions data_index/topology_panel_v1_oracle_minus_predictions.jsonl `
  --summary data_index/topology_panel_v1_oracle_minus_eval_summary.json `
  --report data_index/topology_panel_v1_oracle_minus_eval_report.md `
  --details-csv data_index/topology_panel_v1_oracle_minus_eval_details.csv `
  --errors-csv data_index/topology_panel_v1_oracle_minus_eval_errors.csv
```

The oracle-minus baseline starts from the reference graph and applies
deterministic destructive perturbations: it drops a small fraction of edges,
drops a small fraction of nodes, filters affected edges, and removes nets for
some samples. The resulting prediction graphs remain schema-valid, but their
topology counts are intentionally wrong.

This baseline is **not** a model-performance baseline. It is an evaluator
sensitivity check: it verifies that the evaluator can detect topology errors
even when predicted graph JSON remains valid.

Expected result for the current release:

```text
evaluated_rows: 14
prediction_mode: external_prediction
reference graph valid rate: 1.0
prediction graph valid rate: 1.0
error rows: 14
node_count MAE/MRE: 7.5 / 0.014551
edge_count MAE/MRE: 57.857143 / 0.068867
net_count MAE/MRE: 0.571429 / 0.333333
```

Primary outputs:

```text
data_index/topology_panel_v1_oracle_minus_predictions.jsonl
data_index/topology_panel_v1_oracle_minus_summary.json
data_index/topology_panel_v1_oracle_minus_report.md
data_index/topology_panel_v1_oracle_minus_eval_summary.json
data_index/topology_panel_v1_oracle_minus_eval_report.md
data_index/topology_panel_v1_oracle_minus_eval_details.csv
data_index/topology_panel_v1_oracle_minus_eval_errors.csv
```

The oracle-minus prediction JSONL is self-contained: each row includes an
inline `prediction` graph. The optional `prediction_json_path` field is retained
for local debugging.

## Non-Goals for v1

Topology Graph v1 does not evaluate these tasks:

- Symbol category recognition.
- Terminal semantic anchoring.
- Text recognition or OCR.
- Device naming.
- Wire number extraction.
- Electrical rule verification.
- CAD reconstruction fidelity.
- Multi-subfigure page splitting.

These tasks can become separate benchmark tracks after the graph baseline is
stable.

## Known Limitations

The current reference graph is geometry-derived. It should be treated as a
baseline reference rather than exhaustive ground truth.

Known limitations:

- Crossing visual lines may be incorrectly connected in dense diagrams.
- Symbol terminals are not semantically anchored.
- Text and labels are not part of the graph score.
- Multi-subfigure panels are excluded as badcases.
- Very small or visually ambiguous panels may require manual exclusion.

## v1.1 Improvement Direction

Use the improvement manifest for the next algorithm pass:

```text
data_index/topology_panel_v1_release_improvement_manifest.csv
```

Recommended order:

1. `still_fragmented`: improve endpoint merging and short-segment repair.
2. `needs_terminal_anchor`: add terminal or symbol anchor rules.
3. `over_connected`: add crossing-line disambiguation after the easier repair
   classes are stable.

The v1.1 goal is to move selected improvement-target rows into a new manually
confirmed baseline without weakening the current v1 baseline.

## Reproducibility Checklist

Before reporting a v1 score:

- Confirm the manifest path is `data_index/topology_panel_v1_final_baseline_manifest.csv`.
- Confirm evaluated rows equal 14 for this release.
- Confirm no `excluded_badcase` rows are included.
- Confirm no `improvement_target` rows are included in the formal score.
- Store the prediction JSON path for every evaluated panel.
- Store the evaluation summary and report under `data_index/`.
- Record the run in `experiment_records.md`.
