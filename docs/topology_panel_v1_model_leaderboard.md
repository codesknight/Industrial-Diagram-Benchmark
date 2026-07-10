# Topology Panel v1 模型实验 Leaderboard

日期：2026-07-10

本文件汇总 Topology Panel v1 的模型与 sanity baseline 评测结果。`comparable=yes` 的行可以作为真实模型实验横向比较；`comparable=no` 的行只用于链路校验、评测器敏感性验证或 smoke test。

## 总览

| experiment | comparable | provider | prompt | valid rate | invalid | node MAE | edge MAE | net MAE | notes |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| reference_as_prediction | no | reference | none | 1 | 0 | 0 | 0 | 0 | Evaluator/package consistency check; not a model baseline. |
| oracle_minus | no | oracle | none | 1 | 0 | 7.5 | 57.857143 | 0.571429 | Official sanity baseline for evaluator sensitivity; not model performance. |
| doubao_v1 | yes | doubao | v1 | 0.357143 | 9 | 500.857143 | 828.357143 | 3.571429 | First full real-model baseline; many rows were uncertain/unreadable. |
| doubao_prompt_v2 | yes | doubao | v2 | 1 | 0 | 409.285714 | 737.357143 | 16.357143 | Improves valid/status behavior and node/edge counts; overestimates net_count. |
| deepseek_smoke | no | deepseek | v1 | 0 | 14 | 518.5 | 841.642857 | 1.285714 | Smoke run only; configured endpoint rejected image input, so it is not comparable. |

## 当前可比较模型结论

- 最高 prediction valid rate：`doubao_prompt_v2` = 1
- 最低 node_count MAE：`doubao_prompt_v2` = 409.285714
- 最低 edge_count MAE：`doubao_prompt_v2` = 737.357143
- 最低 net_count MAE：`doubao_v1` = 3.571429

Doubao prompt v2 相比 Doubao v1，显著改善了 status/valid 行为，并降低 node/edge MAE；但 net_count MAE 明显变差。因此下一步 prompt v3 应优先约束 `net_count = 连通分量数量`，避免把端子组、功能区域或线束组误计为多个网络。

## 文件入口

- CSV：`data_index/topology_panel_v1_model_leaderboard.csv`
- Summary：`data_index/topology_panel_v1_model_leaderboard_summary.json`
- Doubao v1 report：`docs/topology_panel_v1_doubao_eval_report.md`
- Doubao prompt v2 report：`docs/topology_panel_v1_doubao_prompt_v2_comparison_report.md`
- Evaluation protocol：`docs/topology_graph_eval_protocol_v1.md`

## 更新规则

新增模型或 prompt/input 实验后，先生成 prediction JSONL 并运行 evaluator，再将对应 adapter summary 与 eval summary 加入 `scripts/build_topology_panel_v1_model_leaderboard.py` 的 `EXPERIMENTS` 列表，最后重新运行脚本。
