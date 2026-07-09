# Topology Panel v1.1 Active Improvement Review Result Report

This report applies manual labels exported from `topology_panel_v1_1_active_improvement_review.html`.
The formal Topology Panel v1 baseline is unchanged.

## Summary

- Manifest rows: 12
- Label rows: 12
- Kept rows: 12
- Keep terminal-anchor rows: 3
- Keep over-connected rows: 9
- Abandoned rows: 0
- Deferred rows: 0

## Label Counts

- keep_over_connected: 9
- keep_terminal_anchor: 3

## Decision Counts

- keep_improvement: 12

## Next Route Counts

- over_connected_repair: 9
- terminal_anchor_module: 3

## Rules

- Rows labeled keep_terminal_anchor remain candidates for terminal/symbol anchor work.
- Rows labeled keep_over_connected remain candidates for crossing-line disambiguation work.
- Rows labeled abandon_badcase or defer_complex are excluded from immediate v1.1 repair.
- No active improvement row is promoted into the formal v1 baseline by this step.

## Outputs

- reviewed: `data_index/topology_panel_v1_1_active_improvement_reviewed.csv`
- keep_improvement: `data_index/topology_panel_v1_1_keep_improvement_manifest.csv`
- keep_terminal_anchor: `data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv`
- keep_over_connected: `data_index/topology_panel_v1_1_keep_over_connected_manifest.csv`
- abandoned: `data_index/topology_panel_v1_1_active_review_abandoned.csv`
- deferred: `data_index/topology_panel_v1_1_active_review_deferred.csv`
- summary: `data_index/topology_panel_v1_1_active_improvement_review_result_summary.json`
- report: `data_index/topology_panel_v1_1_active_improvement_review_result_report.md`
