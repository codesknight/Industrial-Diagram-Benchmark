# Topology Panel v1 Doubao Tile2x2 输入评测报告

日期：2026-07-10

## 1. 实验目标

整图 1024 输入没有降低 node/edge MAE，因此本轮改为降低每次给模型看的信息密度：将每个 panel 切成 2x2 四个 tile，固定 Doubao prompt v3，对每个 tile 单独预测 topology count，再聚合回 panel 级。

本实验仍然是 count-level / synthetic graph 评测，不代表完整 topology graph 几何重建能力。

## 2. 方法

### Tile 生成

- Source benchmark：`data_index/topology_panel_v1_benchmark_manifest.jsonl`
- Source panels：14
- Grid：2x2
- Tile records：56
- Tile manifest：`data_index/topology_panel_v1_tile2x2_benchmark_manifest.jsonl`
- Tile images：`outputs/topology_panel_v1_tiles/tile2x2_v1/`

### Tile 预测

```powershell
python scripts/run_topology_panel_v1_model_prediction_adapter.py `
  --provider doubao `
  --prompt-version v3 `
  --benchmark data_index/topology_panel_v1_tile2x2_benchmark_manifest.jsonl `
  --progress-every 4 `
  --max-image-side 512 `
  --max-image-pixels 250000 `
  --timeout 60 `
  --retries 1 `
  --output data_index/topology_panel_v1_doubao_v3_tile2x2_tile_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v3_tile2x2_tile_predictions_summary.json `
  --report data_index/topology_panel_v1_doubao_v3_tile2x2_tile_predictions_report.md
```

### Panel 聚合

聚合规则：

- node_count：四个 tile 求和
- edge_count：四个 tile 求和
- net_count：四个 tile 平均后四舍五入，并限制在 1 到 3 之间，即 `mean_clamped3`

```powershell
python scripts/aggregate_topology_panel_v1_tile_predictions.py `
  --net-strategy mean_clamped3 `
  --output data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_summary.json `
  --report data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_report.md
```

## 3. 结果对比

| 指标 | v3@512 整图 | v3@1024 整图 | v3 tile2x2 |
| --- | ---: | ---: | ---: |
| prediction rows | 14 | 14 | 14 |
| prediction graph valid rate | 1.0 | 1.0 | 1.0 |
| invalid prediction rows | 0 | 0 | 0 |
| node_count MAE | 394.642857 | 399.571429 | 378.285714 |
| edge_count MAE | 715.642857 | 724.285714 | 713.5 |
| net_count MAE | 0.857143 | 0.928571 | 0.714286 |
| node_count MRE | 0.743527 | 0.766494 | 0.716982 |
| edge_count MRE | 0.836891 | 0.859044 | 0.843823 |
| net_count MRE | 0.773809 | 0.833333 | 0.595238 |

相对 v3@512：

- node MAE 下降 16.357143，约 4.14%。
- edge MAE 下降 2.142857，约 0.30%。
- net MAE 下降 0.142857，约 16.67%。

## 4. 主要发现

2x2 分块输入是有效方向。相比直接放大整图到 1024，tile2x2 更符合当前瓶颈：模型不是缺少更多像素，而是被整图的密集信息干扰。分块后，模型对局部节点数量的估计更充分，panel 聚合后的 node_count MAE 明显下降。

edge_count 改善较小，说明边数量仍然是当前 count-level 预测的主要难点。原因可能是 tile 边界截断线段、跨 tile 连线无法被模型作为整体理解，或者模型对密集线段仍然严重低估。

net_count 需要稳健聚合。直接取 tile net 最大值会被局部异常值拖坏；`mean_clamped3` 更符合 prompt v3 对密集接线图的先验，也得到了更好的 panel 级 net_count MAE。

## 5. 结论

当前最优 count-level Doubao baseline 是：

- Prompt：v3
- Input：tile2x2，每 tile 512 输入
- Aggregation：node/edge 求和，net 使用 `mean_clamped3`

这个结果支持继续推进分块输入，但下一步不应盲目增加 tile 数量。更合理的是先做 tile 审核页，观察哪些 tile 带来改进、哪些 tile 造成重复/截断，再设计 overlap 或主体区域裁剪。

## 6. 输出文件

- Tile benchmark：`data_index/topology_panel_v1_tile2x2_benchmark_manifest.jsonl`
- Tile benchmark CSV：`data_index/topology_panel_v1_tile2x2_benchmark_manifest.csv`
- Tile prediction JSONL：`data_index/topology_panel_v1_doubao_v3_tile2x2_tile_predictions.jsonl`
- Panel prediction JSONL：`data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions.jsonl`
- Eval summary：`data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_eval_summary.json`
- Eval details：`data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_eval_details.csv`
- Eval errors：`data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_eval_errors.csv`
- Updated leaderboard：`data_index/topology_panel_v1_model_leaderboard.csv`

## 7. 下一步建议

1. 生成 tile2x2 HTML 审核表，查看 tile 边界是否切断关键拓扑。
2. 做 overlap tile 实验，例如 2x2 + 10% overlap，比较是否改善 edge_count。
3. 如果 overlap 有效，再考虑 3x3 或主体区域自适应裁剪。
4. 长期方向是将传统线段检测/OCR 与 VLM tile 审核结合，而不是只让 VLM 从图像直接猜完整拓扑。
