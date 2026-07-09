# Topology Panel v1 Evaluation Report

Benchmark id: `topology_panel_v1_benchmark_2026-07-08`

This report evaluates the Topology Panel v1 benchmark package according to `docs/topology_graph_eval_protocol_v1.md`.

## Summary

- Prediction mode: external_prediction
- Evaluated rows: 14
- Prediction rows: 14
- Reference graph valid rate: 1.0
- Prediction graph valid rate: 0.357143

## Splits

- test: 2
- train: 11
- val: 1

## Phases

- P1: 4
- P3: 9
- P2: 1

## Count Errors

- node_count: MAE=500.857143, MRE=0.952608
- edge_count: MAE=828.357143, MRE=0.977183
- net_count: MAE=3.571429, MRE=3.214286

## Diagnostics

- isolated_edge_ratio: min=0.0, max=0.0032, mean=0.000443
- largest_net_edge_ratio: min=0.9964, max=1.0, mean=0.9993

## Invalid Rows

- Reference invalid rows: 0
- Prediction invalid rows: 9
- Missing prediction rows: 0
- Extra prediction panel ids: 0

## Prediction Error Categories

- status: 9

## Prediction Invalid Reasons

- status_uncertain: 5
- status_unreadable: 4

### Prediction Invalid Panel Ids

- `_P1_staging/QA-D301-10(110kV南雄线开关机构箱端子排图(3AP1-FG))#panel_000`
- `_P1_staging/QA-D201-16(#1主变110kV侧开关机构箱端子排图(3AP1-FG))#panel_000`
- `_P1_staging/QA-D302-10(110kV澜河线开关机构箱端子排图(3AP1-FG))#panel_000`
- `_P1_staging/主变压器35kV侧断路器在PWFXH-1111上的端子排(B066-500-1215)wm666.taobao.com#panel_002`
- `_P3_staging_batch1/09(通信回路背面接线图)#panel_000`
- `_P3_staging_batch3/#2备用分支在微机保护柜上的端子排(B066-500-0911)wm666.taobao.com#panel_000`
- `_P3_staging_batch4/发电机保护屏端子图#panel_003`
- `_P3_staging_batch1/QA-D601-03(10kV#1(#2)站变柜端子排图)#panel_000`
- `_P2_staging/35kV并联电抗器在监控柜上的端子排(B066-500-1904)wm666.taobao.com#panel_000`

## Outputs

- summary: `data_index/topology_panel_v1_doubao_model_predictions_eval_summary.json`
- report: `data_index/topology_panel_v1_doubao_model_predictions_eval_report.md`
- details_csv: `data_index/topology_panel_v1_doubao_model_predictions_eval_details.csv`
- errors_csv: `data_index/topology_panel_v1_doubao_model_predictions_eval_errors.csv`
