# Topology Panel v1 Oracle-Minus Baseline Report

Baseline id: `topology_panel_v1_oracle_minus_2026-07-09`

This baseline copies reference graphs and applies deterministic destructive perturbations.
It is intended to validate metric sensitivity, not to represent model performance.

## Summary

- Prediction rows: 14
- Rows with node error: 14
- Rows with edge error: 14
- Rows with net error: 5
- Mean absolute node error: 7.5
- Mean absolute edge error: 57.857143
- Mean absolute net error: 0.571429

## Outputs

- predictions: `data_index/topology_panel_v1_oracle_minus_predictions.jsonl`
- summary: `data_index/topology_panel_v1_oracle_minus_summary.json`
- report: `data_index/topology_panel_v1_oracle_minus_report.md`
- prediction_graph_dir: `outputs/topology_panel_v1_oracle_minus`

The prediction JSONL is self-contained: each row includes an inline `prediction` graph.
`prediction_json_path` is retained as an optional local debugging path.

## Rows

- `_P1_staging/QA-D301-10(110kV南雄线开关机构箱端子排图(3AP1-FG))#panel_000`: node -10, edge -79, net -1
- `_P1_staging/QA-D201-16(#1主变110kV侧开关机构箱端子排图(3AP1-FG))#panel_000`: node -11, edge -76, net 0
- `_P1_staging/QA-D302-10(110kV澜河线开关机构箱端子排图(3AP1-FG))#panel_000`: node -10, edge -81, net 0
- `_P1_staging/主变压器35kV侧断路器在PWFXH-1111上的端子排(B066-500-1215)wm666.taobao.com#panel_002`: node -7, edge -69, net 0
- `_P3_staging_batch1/QA-D401-06(10kV开关柜柜顶小母线布置图)#panel_000`: node -15, edge -76, net -2
- `_P3_staging_batch1/09(通信回路背面接线图)#panel_000`: node -9, edge -61, net 0
- `_P3_staging_batch3/#2备用分支在微机保护柜上的端子排(B066-500-0911)wm666.taobao.com#panel_000`: node -7, edge -61, net 0
- `_P3_staging_batch1/07(通信回路背面接线图 )#panel_000`: node -5, edge -54, net 0
- `_P3_staging_batch1/07(通信回路背面接线图)#panel_000`: node -5, edge -57, net -1
- `_P3_staging_batch3/1FWK柜左侧端子排电缆接线图(B066-500-2409)wm666.taobao.com#panel_000`: node -6, edge -49, net 0
- `_P3_staging_batch3/2FWK柜左侧端子排电缆接线图(B066-500-2411)wm666.taobao.com#panel_000`: node -5, edge -43, net 0
- `_P3_staging_batch4/发电机保护屏端子图#panel_003`: node -6, edge -43, net -2
- `_P3_staging_batch1/QA-D601-03(10kV#1(#2)站变柜端子排图)#panel_000`: node -4, edge -23, net -2
- `_P2_staging/35kV并联电抗器在监控柜上的端子排(B066-500-1904)wm666.taobao.com#panel_000`: node -5, edge -38, net 0
