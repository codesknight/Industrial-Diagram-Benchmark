# Topology Panel v1 Pilot Review Report

This report summarizes manual labels exported from `topology_panel_v1_pilot_review.html`.

## Summary

- Pilot manifest rows: 17
- Label rows: 17
- Reviewed rows: 17
- Unreviewed rows: 0
- Accepted rows: 17
- Not accepted rows: 0

## Review Label Counts

- accept_v1: 17

## Exclude Reason Counts

- keep: 17

## Accepted by Phase

- P1: 4
- P2: 2
- P3: 11

## Accepted by Split

- val: 7
- train: 10

## Rules

- accept_v1 panels are accepted as panel-level Topology Graph v1 pilot positives
- over_connected, still_fragmented, needs_terminal_anchor, and bad_geometry remain reviewed but not accepted
- unreviewed rows are retained in the reviewed manifest and excluded from accept output
