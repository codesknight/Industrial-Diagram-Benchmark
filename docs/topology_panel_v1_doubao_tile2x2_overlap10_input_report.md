# Topology Panel v1 Doubao Tile2x2 Overlap10 输入评测报告

日期：2026-07-10

## 1. 实验目标

上一轮 tile2x2 分块输入已经降低了 node/edge/net MAE，但 edge_count 改善较小，怀疑原因是 tile 边界截断线段。本实验固定 Doubao prompt v3 和 2x2 分块方式，只给每个 tile 增加 10% overlap，验证是否能进一步改善 edge_count。

本实验仍然是 count-level / synthetic graph 评测，不代表完整 topology graph 几何重建能力。

## 2. 方法

### Tile 生成

- Source panels：14
- Grid：2x2
- Overlap：10%
- Tile records：56
- Tile manifest：`data_index/topology_panel_v1_tile2x2_overlap10_benchmark_manifest.jsonl`
- Tile images：`outputs/topology_panel_v1_tiles/tile2x2_overlap10_v1/`

### Tile 预测

```powershell
python scripts/run_topology_panel_v1_model_prediction_adapter.py `
  --provider doubao `
  --prompt-version v3 `
  --benchmark data_index/topology_panel_v1_tile2x2_overlap10_benchmark_manifest.jsonl `
  --progress-every 4 `
  --max-image-side 512 `
  --max-image-pixels 250000 `
  --timeout 60 `
  --retries 1 `
  --output data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_tile_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_tile_predictions_summary.json `
  --report data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_tile_predictions_report.md
```

### Panel 聚合

聚合规则与无 overlap 版本保持一致：

- node_count：tile 求和
- edge_count：tile 求和
- net_count：`mean_clamped3`

## 3. 结果对比

| 指标 | v3@512 整图 | tile2x2 | tile2x2 overlap10 |
| --- | ---: | ---: | ---: |
| prediction rows | 14 | 14 | 14 |
| prediction graph valid rate | 1.0 | 1.0 | 1.0 |
| invalid prediction rows | 0 | 0 | 0 |
| node_count MAE | 394.642857 | 378.285714 | 362.642857 |
| edge_count MAE | 715.642857 | 713.5 | 687.857143 |
| net_count MAE | 0.857143 | 0.714286 | 0.857143 |
| node_count MRE | 0.743527 | 0.716982 | 0.691472 |
| edge_count MRE | 0.836891 | 0.843823 | 0.815865 |
| net_count MRE | 0.773809 | 0.595238 | 0.738095 |

相对无 overlap tile2x2：

- node MAE 下降 15.642857，约 4.14%。
- edge MAE 下降 25.642857，约 3.59%。
- net MAE 上升 0.142857，约 20.0%。

相对 v3@512 整图：

- node MAE 下降 32.0，约 8.11%。
- edge MAE 下降 27.785714，约 3.88%。
- net MAE 持平。

## 4. 主要发现

10% overlap 对 edge_count 有明确帮助。无 overlap 的 tile2x2 只将 edge MAE 从 715.642857 降到 713.5，而 overlap10 进一步降到 687.857143，说明 tile 边界截断确实影响了边数量估计。

overlap10 也继续改善 node_count。node MAE 从无 overlap 的 378.285714 降到 362.642857，是当前所有 Doubao count-level 实验中最低的 node MAE。

net_count 相比无 overlap 略差，但仍与整图 v3 持平。因为 overlap 会让局部 tile 看到更多跨区域连接，也可能让某些 tile 重复估计网络数量；当前 `mean_clamped3` 聚合仍能把 net MAE 控制在可接受范围。

## 5. 结论

当前最优 node/edge count-level baseline 是：

- Prompt：Doubao prompt v3
- Input：tile2x2 + 10% overlap
- Aggregation：node/edge 求和，net 使用 `mean_clamped3`

这个结果支持继续研究 overlap / tile 设计，但下一步应避免只扩大 tile 数量。更建议先生成 tile review HTML，观察哪些 panel 受益、哪些 tile 造成重复计数，再决定是否做 3x3 或自适应裁剪。

## 6. 输出文件

- Overlap tile benchmark：`data_index/topology_panel_v1_tile2x2_overlap10_benchmark_manifest.jsonl`
- Overlap tile predictions：`data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_tile_predictions.jsonl`
- Panel predictions：`data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions.jsonl`
- Eval summary：`data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_summary.json`
- Eval details：`data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_details.csv`
- Eval errors：`data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_errors.csv`
- Updated leaderboard：`data_index/topology_panel_v1_model_leaderboard.csv`

## 7. 下一步建议

1. 生成 tile2x2 / overlap10 HTML 审核表，定位 edge 改善来自哪些 panel。
2. 对比无 overlap 与 overlap tile 的 per-sample error delta。
3. 仅对受益样本尝试 3x3 或主体区域裁剪，避免全量增加 API 成本。
4. 开始设计“传统线段检测 + VLM tile 审核”的 hybrid pipeline。
