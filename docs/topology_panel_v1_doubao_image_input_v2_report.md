# Topology Panel v1 Doubao Image Input v2 评测报告

日期：2026-07-10

## 1. 实验目标

本实验固定 Doubao prompt v3，不再改 prompt，只比较整图输入分辨率是否影响 count-level topology 预测质量。

比较对象：

- v3@512：`--max-image-side 512 --max-image-pixels 250000`
- v3@1024：`--max-image-side 1024 --max-image-pixels 1000000`

两组均使用同一个模型、同一个 prompt v3、同一个 14 条 Topology Panel v1 baseline。

## 2. 运行命令

```powershell
python scripts/run_topology_panel_v1_model_prediction_adapter.py `
  --provider doubao `
  --prompt-version v3 `
  --progress-every 1 `
  --max-image-side 1024 `
  --max-image-pixels 1000000 `
  --timeout 60 `
  --retries 1 `
  --output data_index/topology_panel_v1_doubao_v3_1024_model_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v3_1024_model_predictions_summary.json `
  --report data_index/topology_panel_v1_doubao_v3_1024_model_predictions_report.md
```

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --predictions data_index/topology_panel_v1_doubao_v3_1024_model_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_summary.json `
  --report data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_report.md `
  --details-csv data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_details.csv `
  --errors-csv data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_errors.csv
```

## 3. 结果对比

| 指标 | v3@512 | v3@1024 | 变化 |
| --- | ---: | ---: | ---: |
| prediction rows | 14 | 14 | 0 |
| prediction graph valid rate | 1.0 | 1.0 | 0 |
| invalid prediction rows | 0 | 0 | 0 |
| node_count MAE | 394.642857 | 399.571429 | +4.928572 |
| edge_count MAE | 715.642857 | 724.285714 | +8.642857 |
| net_count MAE | 0.857143 | 0.928571 | +0.071428 |
| node_count MRE | 0.743527 | 0.766494 | +0.022967 |
| edge_count MRE | 0.836891 | 0.859044 | +0.022153 |
| net_count MRE | 0.773809 | 0.833333 | +0.059524 |

## 4. 主要发现

1024 整图输入没有改善 node/edge count。相对 v3@512，node MAE 上升 1.25%，edge MAE 上升 1.21%，net MAE 上升 8.33%。两组 valid rate 都是 1.0，说明更高分辨率没有破坏 schema/status 行为，但也没有提供更好的 topology count。

这说明当前瓶颈不只是整图分辨率不足。对于这批工业图纸，模型可能仍然被整图复杂度、密集端子、文字标签和大量局部线段干扰。单纯把整张图放大，会增加视觉信息量，但不会自动让模型更好地做全局拓扑计数。

## 5. 结论

当前最优设置仍是 Doubao prompt v3 + 512 整图输入。1024 整图输入应作为负结果保留在 leaderboard 中，但不建议作为后续默认配置。

下一步应从“整图放大”转向“信息密度控制”：

- 局部裁剪：按图纸主体区域、端子排区域、连线密集区域裁剪。
- 分块输入：将 panel 切成多个 tiles，分别预测局部 node/edge，再做聚合。
- 结构先验：用传统图像处理先提取线段/端点，再让 VLM 做审核或校正。

## 6. 输出文件

- 1024 predictions：`data_index/topology_panel_v1_doubao_v3_1024_model_predictions.jsonl`
- 1024 adapter summary：`data_index/topology_panel_v1_doubao_v3_1024_model_predictions_summary.json`
- 1024 adapter report：`data_index/topology_panel_v1_doubao_v3_1024_model_predictions_report.md`
- 1024 eval summary：`data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_summary.json`
- 1024 eval report：`data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_report.md`
- 1024 eval details：`data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_details.csv`
- 1024 eval errors：`data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_errors.csv`
- updated leaderboard：`data_index/topology_panel_v1_model_leaderboard.csv`

## 7. 下一步建议

1. 保持 prompt v3 和 512 整图作为当前默认 count-level baseline。
2. 做 image input v3：局部裁剪/分块输入，不再单纯放大整图。
3. 先生成 tiles manifest 和 HTML 快速审核页，确认分块是否覆盖主体图形区域。
4. 再跑 Doubao v3 tile-level prediction，并设计聚合规则。
