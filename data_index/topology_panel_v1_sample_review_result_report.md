# Topology Panel v1 Sample Review Result Report

This report summarizes manual labels exported from `topology_panel_v1_sample_review.html`.

## Summary

- Sample manifest rows: 171
- Label rows: 171
- Reviewed rows: 170
- Unreviewed rows: 1
- Accepted rows: 14
- Needs panel split rows: 43
- Not topology target rows: 19
- Bad geometry rows: 63
- Other not accepted rows: 31

## Review Label Counts

- needs_panel_split: 43
- bad_geometry: 63
- still_fragmented: 19
- not_topology_target: 19
- needs_terminal_anchor: 3
- unreviewed: 1
- over_connected: 9
- accept_v1: 14

## Model Agreement Counts

- agree: 107
- disagree: 63
- unreviewed: 1

## Needs Panel Split by Split Method

- full: 37
- image_components: 6

## Rules

- accept_v1 rows remain eligible for panel-level Topology Graph v1 baseline
- needs_panel_split rows must go to panel split v2 before topology use
- bad_geometry and not_topology_target rows are excluded from topology baseline
- over_connected, still_fragmented, and needs_terminal_anchor remain v1 improvement targets
