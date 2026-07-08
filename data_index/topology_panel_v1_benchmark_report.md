# Topology Panel v1 Benchmark Package Report

Benchmark id: `topology_panel_v1_benchmark_2026-07-08`

This package converts the final 14-row Topology Panel v1 baseline into a JSONL benchmark manifest.

## Summary

- Records: 14
- Source manifest: `data_index/topology_panel_v1_final_baseline_manifest.csv`
- Output JSONL: `data_index/topology_panel_v1_benchmark_manifest.jsonl`
- Protocol: `docs/topology_graph_eval_protocol_v1.md`

## Splits

- test: 2
- train: 11
- val: 1

## Phases

- P1: 4
- P3: 9
- P2: 1

## Asset Checks

- Missing images: 0
- Missing topology graphs: 0

## Graph Stats

- node_count: min=204.0, max=731.0, mean=518.5
- edge_count: min=337.0, max=1165.0, mean=841.6429
- net_count: min=1.0, max=3.0, mean=1.2857
- intersection_count: min=184.0, max=628.0, mean=440.2857
- isolated_edge_ratio: min=0.0, max=0.0032, mean=0.0004
- largest_net_edge_ratio: min=0.9964, max=1.0, mean=0.9993

## Quality Labels

- confirmed_baseline: 14

## Outputs

- jsonl: `data_index/topology_panel_v1_benchmark_manifest.jsonl`
- summary: `data_index/topology_panel_v1_benchmark_summary.json`
- report: `data_index/topology_panel_v1_benchmark_report.md`
