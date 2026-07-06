# Topology Review Label Report

This report summarizes manual labels exported from `topology_review.html`.

## Summary

- Topology rows: 2042
- Label rows: 52
- Reviewed rows: 52
- Unreviewed rows: 1990
- Reviewed ready rows: 2000
- V1 pilot candidate rows: 7
- Bad geometry rows: 42

## Review Label Counts

- unreviewed: 1990
- accept_v0: 3
- needs_intersection_split: 7
- bad_geometry: 42

## Exclude Reason Counts

- keep: 2000
- bad_geometry: 31
- not_topology_ready: 11

## V1 Candidate Labels

- needs_intersection_split: 7

## Rules

- bad_geometry and not_topology_target are excluded from reviewed topology-ready rows
- not_topology_ready rows remain excluded even without a manual label
- needs_intersection_split and needs_terminal_anchor become v1 pilot candidates
- accept_v0 remains eligible for v0 topology benchmark baselines
