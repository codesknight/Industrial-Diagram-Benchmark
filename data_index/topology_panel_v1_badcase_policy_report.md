# Topology Panel v1 Badcase Policy Report

This report applies the final policy that multi-subfigure panels are badcases, not split-v2 candidates.

## Summary

- Sample rows: 171
- Baseline accept rows: 14
- Badcase rows: 125
- Multi-subfigure badcase rows: 43
- Improvement target rows: 31
- Unreviewed rows: 1

## Policy Exclude Reason Counts

- multi_subfigure_badcase: 43
- bad_geometry: 63
- still_fragmented: 19
- not_topology_target: 19
- needs_terminal_anchor: 3
- unreviewed: 1
- over_connected: 9
- keep: 14

## Multi-Subfigure by Split Method

- full: 37
- image_components: 6

## Rules

- needs_panel_split is treated as multi_subfigure_badcase and excluded from topology baseline
- bad_geometry and not_topology_target are excluded from topology baseline
- accept_v1 remains eligible for the clean panel-level v1 baseline
- over_connected, still_fragmented, and needs_terminal_anchor are retained as algorithm improvement targets
