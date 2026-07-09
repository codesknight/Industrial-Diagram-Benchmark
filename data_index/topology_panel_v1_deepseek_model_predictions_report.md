# Topology Panel v1 Model Prediction Adapter Report

Adapter id: `topology_panel_v1_deepseek_adapter_2026-07-09`

## Summary

- Provider: deepseek
- Model: deepseek-v4-pro
- Dry run: False
- Prediction rows: 1
- Output predictions: `data_index/topology_panel_v1_deepseek_model_predictions.jsonl`

## Adapter Modes

- synthetic_from_counts: 1

## Adapter Errors

- model_error: 1

## Evaluator Command

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --predictions data_index/topology_panel_v1_deepseek_model_predictions.jsonl `
  --summary data_index/topology_panel_v1_deepseek_model_predictions_eval_summary.json `
  --report data_index/topology_panel_v1_deepseek_model_predictions_eval_report.md `
  --details-csv data_index/topology_panel_v1_deepseek_model_predictions_eval_details.csv `
  --errors-csv data_index/topology_panel_v1_deepseek_model_predictions_eval_errors.csv
```

Count-only predictions are converted to synthetic graph objects so evaluator count metrics can run.
