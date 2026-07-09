# Topology Panel v1 Evaluation Report

Benchmark id: `topology_panel_v1_benchmark_2026-07-08`

This report evaluates the Topology Panel v1 benchmark package according to `docs/topology_graph_eval_protocol_v1.md`.

## Summary

- Prediction mode: external_prediction
- Evaluated rows: 14
- Prediction rows: 14
- Reference graph valid rate: 1.0
- Prediction graph valid rate: 1.0

## Splits

- test: 2
- train: 11
- val: 1

## Phases

- P1: 4
- P3: 9
- P2: 1

## Count Errors

- node_count: MAE=409.285714, MRE=0.773972
- edge_count: MAE=737.357143, MRE=0.870801
- net_count: MAE=16.357143, MRE=14.75

## Diagnostics

- isolated_edge_ratio: min=0.0, max=0.0032, mean=0.000443
- largest_net_edge_ratio: min=0.9964, max=1.0, mean=0.9993

## Invalid Rows

- Reference invalid rows: 0
- Prediction invalid rows: 0
- Missing prediction rows: 0
- Extra prediction panel ids: 0

## Outputs

- summary: `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_summary.json`
- report: `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_report.md`
- details_csv: `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_details.csv`
- errors_csv: `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_errors.csv`
