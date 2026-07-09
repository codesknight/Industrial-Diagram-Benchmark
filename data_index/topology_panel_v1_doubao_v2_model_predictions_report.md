# Topology Panel v1 Model Prediction Adapter Report

Adapter id: `topology_panel_v1_doubao_adapter_v2_2026-07-09`

## Summary

- Provider: doubao
- Model: doubao-seed-2-0-pro-260215
- Prompt version: v2
- Image max side: 512
- Image max pixels: 250000
- Dry run: False
- Prediction rows: 14
- Output predictions: `data_index/topology_panel_v1_doubao_v2_model_predictions.jsonl`

## Adapter Modes

- synthetic_from_counts: 14

## Adapter Errors

- none: 14

## Evaluator Command

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --predictions data_index/topology_panel_v1_doubao_v2_model_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v2_model_predictions_eval_summary.json `
  --report data_index/topology_panel_v1_doubao_v2_model_predictions_eval_report.md `
  --details-csv data_index/topology_panel_v1_doubao_v2_model_predictions_eval_details.csv `
  --errors-csv data_index/topology_panel_v1_doubao_v2_model_predictions_eval_errors.csv
```

Count-only predictions are converted to synthetic graph objects so evaluator count metrics can run.
