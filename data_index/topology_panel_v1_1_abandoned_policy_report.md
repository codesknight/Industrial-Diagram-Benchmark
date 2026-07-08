# Topology Panel v1.1 Abandoned Policy Report

Policy id: `topology_panel_v1_1_abandoned_policy_2026-07-08`

This report freezes the decision to abandon the v1.1 still-fragmented diagnostic bucket.
The formal Topology Panel v1 baseline is unchanged.

## Summary

- Input improvement rows: 31
- Diagnostic rows: 19
- Abandoned rows: 19
- Active improvement rows: 12

## Decisions

- abandoned: 19
- active_improvement: 12

## Original Improvement Reasons

- still_fragmented: 19
- needs_terminal_anchor: 3
- over_connected: 9

## Abandoned Diagnostic Labels

- no_line_geometry: 1
- non_topology_target: 4
- needs_panel_split_badcase: 7
- terminal_anchor_needed: 2
- true_fragmentation: 5

## Active Next Routes

- terminal_anchor_module: 3
- over_connected_repair: 9

## Rules

- All still_fragmented rows diagnosed in v1.1 are abandoned and kept for badcase/error analysis only.
- Abandoned rows must not be used as v1.1 repair candidates unless a future manual override is created.
- needs_terminal_anchor and over_connected rows remain active improvement targets.
- The formal Topology Panel v1 baseline remains unchanged.

## Outputs

- active_improvement_manifest: `data_index/topology_panel_v1_1_active_improvement_manifest.csv`
- abandoned_manifest: `data_index/topology_panel_v1_1_abandoned_manifest.csv`
- active_terminal_anchor_manifest: `data_index/topology_panel_v1_1_active_terminal_anchor_manifest.csv`
- active_over_connected_manifest: `data_index/topology_panel_v1_1_active_over_connected_manifest.csv`
- summary: `data_index/topology_panel_v1_1_abandoned_policy_summary.json`
- report: `data_index/topology_panel_v1_1_abandoned_policy_report.md`
