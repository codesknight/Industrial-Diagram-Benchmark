# Topology Panel v1.1 Plan

This document records the v1.1 improvement direction after the Topology Panel
v1 baseline was frozen.

The v1 baseline remains unchanged. v1.1 experiments operate only on improvement
targets and must not promote rows into the formal baseline without a new manual
review pass.

## Current v1 Baseline

Formal baseline:

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

Current size:

```text
total: 14
train: 11
val: 1
test: 2
```

Benchmark package:

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
```

Evaluation entrypoint:

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py
```

## v1.1 Target Pool

Improvement manifest:

```text
data_index/topology_panel_v1_release_improvement_manifest.csv
```

Current improvement labels:

```text
still_fragmented: 19
needs_terminal_anchor: 3
over_connected: 9
```

Recommended priority:

1. `still_fragmented`
2. `needs_terminal_anchor`
3. `over_connected`

## First Still-Fragmented Experiment

Script:

```powershell
python scripts/run_topology_panel_v1_1_still_fragmented_experiment.py
```

Inputs:

```text
data_index/topology_panel_v1_release_improvement_manifest.csv
data_index/topology_graph_manifest.csv
```

Outputs:

```text
data_index/topology_panel_v1_1_still_fragmented_input.csv
data_index/topology_panel_v1_1_still_fragmented_experiment_manifest.csv
data_index/topology_panel_v1_1_still_fragmented_best_candidates.csv
data_index/topology_panel_v1_1_still_fragmented_summary.json
data_index/topology_panel_v1_1_still_fragmented_report.md
outputs/topology_panel_v1_1_still_fragmented/
```

The first experiment tested endpoint merge tolerance variants only:

```text
baseline_0005_cap1
merge_0010_cap2
merge_0020_cap5
merge_0050_cap10
```

## First Experiment Result

Summary:

```text
input rows: 19
variant count: 4
experiment rows: 76
best improved rows: 0
best still-empty rows: 11
best overmerge-warning rows: 0
```

Input quality flags:

```text
no_edges;no_nets: 11
high_fragmentation: 2
high_isolated_ratio: 6
```

Input model labels:

```text
still_fragmented: 14
not_topology_target: 4
needs_panel_split: 1
```

Interpretation:

- Endpoint tolerance tuning alone did not repair any `still_fragmented` row.
- The 11 no-edge rows stayed empty across all variants.
- Some rows in the `still_fragmented` bucket are probably misclassified for v1.1
  repair: they may be non-topology targets, multi-subfigure remnants, or panels
  whose usable geometry is not represented by `LINE`/`LWPOLYLINE`.
- The next useful step is diagnostic classification, not wider tolerance search.

## Next v1.1 Step

Run a still-fragmented diagnostic pass that separates rows into:

```text
no_line_geometry
crop_or_bbox_issue
non_topology_target
needs_panel_split_badcase
true_fragmentation
terminal_anchor_needed
```

For each row, inspect:

- entity type counts inside the panel bbox
- whether line-like entities exist but are outside the bbox
- whether the panel image is a real topology target
- whether the graph has many tiny disconnected components
- whether geometry is present only as text, hatch, block inserts, or dimensions

Only `true_fragmentation` should receive algorithmic endpoint/short-segment
repair. Other classes should be routed to filtering, relabeling, or symbol
anchor work.

## Abandoned Policy

After reviewing the first still-fragmented experiment and diagnostic buckets,
the current decision is to abandon all 19 `still_fragmented` rows for v1.1
repair. They are kept only for badcase and error analysis.

Apply the policy with:

```powershell
python scripts/apply_topology_panel_v1_1_abandoned_policy.py
```

Outputs:

```text
data_index/topology_panel_v1_1_abandoned_manifest.csv
data_index/topology_panel_v1_1_active_improvement_manifest.csv
data_index/topology_panel_v1_1_active_terminal_anchor_manifest.csv
data_index/topology_panel_v1_1_active_over_connected_manifest.csv
data_index/topology_panel_v1_1_abandoned_policy_summary.json
data_index/topology_panel_v1_1_abandoned_policy_report.md
```

Current policy result:

```text
input improvement rows: 31
abandoned rows: 19
active improvement rows: 12
active terminal-anchor rows: 3
active over-connected rows: 9
```

Abandoned diagnostic label counts:

```text
no_line_geometry: 1
non_topology_target: 4
needs_panel_split_badcase: 7
true_fragmentation: 5
terminal_anchor_needed: 2
```

The abandoned rows must not be used as v1.1 repair candidates unless a future
manual override creates a new candidate manifest.

## Active Improvement Review

The remaining 12 active improvement rows were reviewed through:

```text
data_index/topology_panel_v1_1_active_improvement_review.html
```

Apply exported labels with:

```powershell
python scripts/apply_topology_panel_v1_1_active_improvement_review_labels.py
```

Current review result:

```text
manifest rows: 12
kept rows: 12
keep terminal-anchor rows: 3
keep over-connected rows: 9
abandoned rows: 0
deferred rows: 0
```

Next active manifests:

```text
data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv
data_index/topology_panel_v1_1_keep_over_connected_manifest.csv
```

Recommended order:

1. Explore the 3 terminal-anchor rows first if v1.1 expansion is still desired.
2. Keep the 9 over-connected rows for later crossing-line disambiguation work.
3. Do not promote either group into the benchmark baseline without another
   candidate-generation and manual-review cycle.

## Promotion Rule

No v1.1 output should enter the benchmark baseline automatically.

Promotion requires:

1. Produce a candidate manifest.
2. Generate an HTML review sheet.
3. Manually confirm the candidate.
4. Create a new release manifest and summary.
5. Run the evaluation script against the updated benchmark package.
