# Topology Panel v1 Doubao Prompt v2 对比评测报告

日期：2026-07-09

## 1. 实验目标

本实验在已跑通的 Doubao v1 baseline 基础上，改进 prompt 并重新跑完整 14 条 Topology Panel v1 baseline。目标是验证 prompt v2 是否能减少 `unreadable/uncertain`，并改善 count-level topology 估计。

本实验仍然是 count-level / synthetic graph 评测，不代表完整 topology graph 几何重建能力。

## 2. Prompt v2 改动

Prompt v2 的核心变化：

- 将任务明确收窄为 count-level topology prediction。
- 要求可读工业图纸优先返回 `status=ok`，不要轻易返回 `unreadable` 或 `uncertain`。
- 规定 `status=ok` 时 `node_count`、`edge_count`、`net_count` 必须是正整数。
- 强调对密集端子排、接线图、控制图也要给出数量级估计。
- 保持输出为严格 JSON，继续兼容现有 evaluator schema adapter。

运行命令：

```powershell
python scripts/run_topology_panel_v1_model_prediction_adapter.py `
  --provider doubao `
  --prompt-version v2 `
  --progress-every 1 `
  --max-image-side 512 `
  --max-image-pixels 250000 `
  --timeout 45 `
  --retries 1
```

评测命令：

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --predictions data_index/topology_panel_v1_doubao_v2_model_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_v2_model_predictions_eval_summary.json `
  --report data_index/topology_panel_v1_doubao_v2_model_predictions_eval_report.md `
  --details-csv data_index/topology_panel_v1_doubao_v2_model_predictions_eval_details.csv `
  --errors-csv data_index/topology_panel_v1_doubao_v2_model_predictions_eval_errors.csv
```

## 3. 总体对比

| 指标 | Doubao v1 | Doubao prompt v2 | 变化 |
| --- | ---: | ---: | ---: |
| prediction rows | 14 | 14 | 0 |
| adapter errors | 0 | 0 | 0 |
| prediction graph valid rate | 0.357143 | 1.0 | +0.642857 |
| invalid prediction rows | 9 | 0 | -9 |
| node_count MAE | 500.857143 | 409.285714 | -91.571429 |
| edge_count MAE | 828.357143 | 737.357143 | -91.0 |
| net_count MAE | 3.571429 | 16.357143 | +12.785714 |
| node_count MRE | 0.952608 | 0.773972 | -0.178636 |
| edge_count MRE | 0.977183 | 0.870801 | -0.106382 |
| net_count MRE | 3.214286 | 14.75 | +11.535714 |

## 4. 主要发现

Prompt v2 明显改善了模型的可读性判断。v1 中 9 条预测图因为 `status_uncertain` 或 `status_unreadable` 被 evaluator 判为 invalid；v2 中 14 条全部返回 `status=ok`，prediction graph valid rate 从 0.357143 提升到 1.0。

Prompt v2 对节点和边数量估计有一定改善。node_count MAE 从 500.857143 降到 409.285714，edge_count MAE 从 828.357143 降到 737.357143，说明“不要轻易放弃可读图纸”的 prompt 对 count-level 粗估计有正向作用。

但 prompt v2 显著恶化了 net_count。net_count MAE 从 3.571429 上升到 16.357143，说明模型倾向于把局部线束、端子列或图块区域误认为多个独立网络。后续 prompt 需要把 `net_count` 定义得更严格：它不是图纸区域数、回路块数量或线束组数量，而是图结构连通分量数量。

## 5. 结论

Prompt v2 是一次有效的第一轮 prompt 改进：它解决了模型过度返回 `unreadable/uncertain` 的问题，并让 node/edge count 误差下降。但它没有解决完整拓扑预测问题，也暴露出 `net_count` 定义需要单独强化。

当前推荐定位：

- Doubao v1：真实模型首轮接入 baseline。
- Doubao prompt v2：count-level prompt 改进 baseline。
- 下一轮 v3：重点约束 `net_count`，同时尝试局部裁剪或分块输入，降低整图复杂度。

## 6. 输出文件

- v2 predictions：`data_index/topology_panel_v1_doubao_v2_model_predictions.jsonl`
- v2 adapter summary：`data_index/topology_panel_v1_doubao_v2_model_predictions_summary.json`
- v2 adapter report：`data_index/topology_panel_v1_doubao_v2_model_predictions_report.md`
- v2 eval summary：`data_index/topology_panel_v1_doubao_v2_model_predictions_eval_summary.json`
- v2 eval report：`data_index/topology_panel_v1_doubao_v2_model_predictions_eval_report.md`
- v2 eval details：`data_index/topology_panel_v1_doubao_v2_model_predictions_eval_details.csv`
- v2 eval errors：`data_index/topology_panel_v1_doubao_v2_model_predictions_eval_errors.csv`

## 7. 下一步建议

1. 做 prompt v3：专门重写 `net_count` 定义和反例。
2. 做 image input v2：同一 prompt 下比较 512、1024、局部裁剪/分块输入。
3. 建立 `topology_panel_v1_model_leaderboard.csv`，把 oracle-minus、Doubao v1、Doubao v2、后续 v3 统一登记。
4. 在模型能稳定输出 count 后，再尝试 full graph schema，而不是直接要求模型生成完整节点边列表。
