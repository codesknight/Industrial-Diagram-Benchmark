# Topology-Ready Manifest Report

This report summarizes the topology-ready subset derived from Topology Graph v0.

## Summary

- Source rows: 2042
- Topology-ready rows: 2031
- Not topology-ready rows: 11
- Ready edge count min: 1
- Ready edge count avg: 2013.51
- Ready edge count max: 70665
- Ready node count avg: 2601.18
- Ready net count avg: 891.59

## Ready Splits

- train: 1630
- val: 195
- test: 206

## Not Ready Splits

- train: 8
- test: 2
- val: 1

## Not Ready Flags

- no_edges: 11
- not_topology_ready: 11

## Rules

- topology_ready is true only when a graph has at least one edge
- not topology-ready rows are excluded from topology training and graph benchmark tasks
- not topology-ready rows may remain useful for symbol, layout, or classification tasks
