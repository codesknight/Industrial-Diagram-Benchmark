# Topology Panel v1 实验结果总表

日期：2026-07-10

本表汇总 Topology Panel v1 上已经完成的真实模型与 sanity baseline 实验。正式可比较模型结果以 `category=model` 为主；`oracle_minus` 用于验证 evaluator 对拓扑错误是否敏感，不代表模型能力。

## 核心模型对比

| rank | experiment | input | valid | node MAE | edge MAE | net MAE | selected |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | doubao_prompt_v3_tile2x2_overlap10 | tile2x2_overlap10_512px_250k | 1.0 | 362.642857 | 687.857143 | 0.857143 | yes |
| 2 | doubao_prompt_v3_tile2x2 | tile2x2_512px_250k | 1.0 | 378.285714 | 713.5 | 0.714286 | no |
| 3 | doubao_prompt_v3 | image_512px_250k | 1.0 | 394.642857 | 715.642857 | 0.857143 | no |
| 4 | doubao_prompt_v3_image_1024 | image_1024px_1M | 1.0 | 399.571429 | 724.285714 | 0.928571 | no |
| 5 | doubao_prompt_v2 | image_512px_250k | 1.0 | 409.285714 | 737.357143 | 16.357143 | no |
| 6 | doubao_v1 | image_512px_250k | 0.357143 | 500.857143 | 828.357143 | 3.571429 | no |

## Sanity Baseline

| experiment | purpose | node MAE | edge MAE | net MAE |
| --- | --- | --- | --- | --- |
| oracle_minus | Official sanity baseline for evaluator sensitivity; not model performance. | 7.5 | 57.857143 | 0.571429 |

## 结论

- 当前最佳真实模型 count-level baseline：`doubao_prompt_v3_tile2x2_overlap10`。
- 相比整图 `doubao_prompt_v3`，tile2x2 + overlap10 的 node MAE 降低 `32.0`，edge MAE 降低 `27.785714`。
- `net_count` 在 prompt v3 后已显著稳定，后续主要瓶颈转为 node/edge 计数和真实拓扑结构恢复。
- 该实验仍是 count-level synthetic graph baseline，不等同于完整拓扑图重建。

CSV 版本：`data_index/topology_panel_v1_experiment_table.csv`
