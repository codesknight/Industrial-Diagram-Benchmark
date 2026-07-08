# Topology Panel v1 Release Report

Release id: `topology_panel_v1_2026-07-08`

This release freezes the manually reviewed panel-level Topology Graph v1 baseline.
Multi-subfigure panels are treated as badcases and are not sent to another panel-boxing pass.

## Summary

- Reviewed sample rows: 171
- Clean baseline rows: 14
- Excluded badcase rows: 125
- Improvement target rows: 31
- Unreviewed rows: 1

## Release Partitions

- excluded_badcase: 125
- improvement_target: 31
- unreviewed: 1
- clean_baseline: 14

## Excluded Badcases

- multi_subfigure_badcase: 43
- bad_geometry: 63
- not_topology_target: 19

## Improvement Targets

- still_fragmented: 19
- needs_terminal_anchor: 3
- over_connected: 9

## Clean Baseline Splits

- test: 2
- train: 11
- val: 1

## Clean Baseline Phases

- P1: 4
- P3: 9
- P2: 1

## Asset Checks

- Missing panel PNG rows: 0
- Missing topology v1 JSON rows: 7
- Clean baseline missing panel PNG rows: 0
- Clean baseline missing topology v1 JSON rows: 0

## Clean Baseline Graph Stats

- v1_node_count: min=204, max=731, mean=518.5
- v1_edge_count: min=337, max=1165, mean=841.6429
- v1_net_count: min=1, max=3, mean=1.2857
- intersection_count: min=184, max=628, mean=440.2857

## Rules

- Only clean_baseline rows are eligible for the formal Topology Panel v1 baseline.
- Rows labeled needs_panel_split are multi-subfigure badcases and are excluded from the baseline.
- Rows labeled bad_geometry or not_topology_target are excluded from the baseline.
- Rows labeled over_connected, still_fragmented, or needs_terminal_anchor are retained as improvement targets.

## Outputs

- release_manifest: `data_index/topology_panel_v1_release_manifest.csv`
- release_train_manifest: `data_index/topology_panel_v1_release_train.csv`
- release_val_manifest: `data_index/topology_panel_v1_release_val.csv`
- release_test_manifest: `data_index/topology_panel_v1_release_test.csv`
- all_reviewed_manifest: `data_index/topology_panel_v1_release_all_reviewed_manifest.csv`
- excluded_manifest: `data_index/topology_panel_v1_release_excluded_manifest.csv`
- improvement_manifest: `data_index/topology_panel_v1_release_improvement_manifest.csv`
- unreviewed_manifest: `data_index/topology_panel_v1_release_unreviewed_manifest.csv`
- summary: `data_index/topology_panel_v1_release_summary.json`
- report: `data_index/topology_panel_v1_release_report.md`
