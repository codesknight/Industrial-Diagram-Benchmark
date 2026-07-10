# Topology Panel v1 Doubao Prompt v3 对比评测报告

日期：2026-07-10

## 1. 实验目标

Prompt v2 已经解决了 Doubao 过度返回 `unreadable/uncertain` 的问题，但明显高估 `net_count`。本轮 prompt v3 专门强化 `net_count = topology graph 连通分量数量`，避免模型把端子排、功能块、线束组、页面区域误当作多个网络。

本实验仍然是 count-level / synthetic graph 评测，不代表完整 topology graph 几何重建能力。

## 2. Prompt v3 改动

Prompt v3 在 v2 基础上增加：

- 明确 `net_count` 是连通分量数量。
- 明确 `net_count` 不等于功能块数量、端子排组数、线束组数、图纸区域数或标签描述的回路数。
- 若线段、端子、母线或连续导体相连，应归入同一个 net。
- 密集端子/接线图通常只有 1 到 3 个大的连通网络，除非视觉上确实存在多个断开的组件。
- 不确定时优先给更小的连通分量估计，而不是把一张连通图拆成很多网络。

运行命令：

```powershell
python scripts/run_topology_panel_v1_model_prediction_adapter.py `
  --provider doubao `
  --prompt-version v3 `
  --progress-every 1 `
  --max-image-side 512 `
  --max-image-pixels 250000 `
  --timeout 45 `
  --retries 1
```

评测命令：

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --predictions data_index/topology_panel_v1_doubao_v3_model_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v3_model_predictions_eval_summary.json `
  --report data_index/topology_panel_v1_doubao_v3_model_predictions_eval_report.md `
  --details-csv data_index/topology_panel_v1_doubao_v3_model_predictions_eval_details.csv `
  --errors-csv data_index/topology_panel_v1_doubao_v3_model_predictions_eval_errors.csv
```

## 3. v1 / v2 / v3 总体对比

| 指标 | Doubao v1 | Doubao prompt v2 | Doubao prompt v3 |
| --- | ---: | ---: | ---: |
| prediction rows | 14 | 14 | 14 |
| adapter errors | 0 | 0 | 0 |
| prediction graph valid rate | 0.357143 | 1.0 | 1.0 |
| invalid prediction rows | 9 | 0 | 0 |
| node_count MAE | 500.857143 | 409.285714 | 394.642857 |
| edge_count MAE | 828.357143 | 737.357143 | 715.642857 |
| net_count MAE | 3.571429 | 16.357143 | 0.857143 |
| node_count MRE | 0.952608 | 0.773972 | 0.743527 |
| edge_count MRE | 0.977183 | 0.870801 | 0.836891 |
| net_count MRE | 3.214286 | 14.75 | 0.773809 |

## 4. 主要发现

Prompt v3 保持了 v2 的可读性收益：14 条全部返回 `status=ok`，prediction graph valid rate 保持 1.0，invalid rows 仍为 0。

Prompt v3 成功修正了 v2 的 `net_count` 过估计问题。net_count MAE 从 v2 的 16.357143 降到 0.857143，相对下降 94.76%；相比 v1 的 3.571429 也下降 76.0%。

Prompt v3 对 node/edge count 也有小幅继续改善。相对 v2，node MAE 从 409.285714 降到 394.642857，edge MAE 从 737.357143 降到 715.642857。说明更严格的连通分量定义没有牺牲节点和边的粗估计表现。

## 5. 结论

Doubao prompt v3 是当前最好的 count-level Doubao baseline：

- valid/status 行为继承 v2 的改进；
- node/edge count 均为当前 Doubao prompt 中最低 MAE；
- net_count 大幅优于 v1/v2；
- 仍然是 count-only synthetic graph，不是完整 topology graph reconstruction。

下一步不建议继续只调 prompt。更有价值的方向是 image input v2：比较 512 与 1024 输入、局部裁剪、分块预测后聚合，判断模型误差主要来自视觉分辨率还是拓扑推理能力。

## 6. 输出文件

- v3 predictions：`data_index/topology_panel_v1_doubao_v3_model_predictions.jsonl`
- v3 adapter summary：`data_index/topology_panel_v1_doubao_v3_model_predictions_summary.json`
- v3 adapter report：`data_index/topology_panel_v1_doubao_v3_model_predictions_report.md`
- v3 eval summary：`data_index/topology_panel_v1_doubao_v3_model_predictions_eval_summary.json`
- v3 eval report：`data_index/topology_panel_v1_doubao_v3_model_predictions_eval_report.md`
- v3 eval details：`data_index/topology_panel_v1_doubao_v3_model_predictions_eval_details.csv`
- v3 eval errors：`data_index/topology_panel_v1_doubao_v3_model_predictions_eval_errors.csv`
- updated leaderboard：`data_index/topology_panel_v1_model_leaderboard.csv`

## 7. 下一步建议

1. 固化 prompt v3 为当前 Doubao count-level baseline。
2. 做 image input v2：同一 prompt v3 下比较 512、1024、局部裁剪/分块输入。
3. 如果 1024 或分块能明显降低 node/edge MAE，再设计 full graph schema 输出实验。
4. 如果 node/edge 仍高误差，则说明需要引入传统图像处理/OCR/符号检测先验，而不是继续要求 VLM 直接读完整图。
