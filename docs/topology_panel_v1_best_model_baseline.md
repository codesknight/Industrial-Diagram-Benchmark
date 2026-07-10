# Topology Panel v1 Best Model Baseline

日期：2026-07-10

## 结论

当前 Topology Panel v1 的最佳真实模型 count-level baseline 固化为：

- Model：Doubao
- Prompt：v3
- Image input：tile2x2 + 10% overlap
- Aggregation：node=sum；edge=sum；net=mean_clamped3
- Scope：count-level synthetic graph baseline，不是完整 topology graph reconstruction

## 指标

- prediction rows：14
- prediction graph valid rate：1.0
- node_count MAE：362.642857
- edge_count MAE：687.857143
- net_count MAE：0.857143

## 统一入口文件

- predictions：`data_index/topology_panel_v1_best_model_predictions.jsonl`
- eval summary：`data_index/topology_panel_v1_best_model_eval_summary.json`
- eval details：`data_index/topology_panel_v1_best_model_eval_details.csv`
- eval errors：`data_index/topology_panel_v1_best_model_eval_errors.csv`
- best manifest：`data_index/topology_panel_v1_best_model_manifest.csv`
- best summary：`data_index/topology_panel_v1_best_model_summary.json`

## 来源实验

该 best baseline 来源于 `doubao_prompt_v3_tile2x2_overlap10`，详见：

- `docs/topology_panel_v1_model_experiment_summary.md`
- `docs/topology_panel_v1_image_input_delta_analysis.md`
- `docs/topology_panel_v1_tile2x2_overlap10_auto_judge_report.md`
- `data_index/topology_panel_v1_model_leaderboard.csv`
