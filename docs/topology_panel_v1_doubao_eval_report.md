# Topology Panel v1 Doubao 模型评测报告

日期：2026-07-09

## 1. 评测对象

- 数据集版本：Topology Panel v1 baseline
- Benchmark manifest：`data_index/topology_panel_v1_benchmark_manifest.jsonl`
- 样本数：14
- 划分：train 11，val 1，test 2
- 阶段分布：P1 4，P2 1，P3 9
- 预测模型：`doubao-seed-2-0-pro-260215`
- 适配器：`scripts/run_topology_panel_v1_model_prediction_adapter.py`
- 预测输出：`data_index/topology_panel_v1_doubao_model_predictions.jsonl`

## 2. 执行命令

```powershell
python scripts/run_topology_panel_v1_model_prediction_adapter.py `
  --provider doubao `
  --progress-every 1 `
  --max-image-side 512 `
  --max-image-pixels 250000 `
  --timeout 45 `
  --retries 1
```

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --predictions data_index/topology_panel_v1_doubao_model_predictions.jsonl `
  --summary data_index/topology_panel_v1_doubao_model_predictions_eval_summary.json `
  --report data_index/topology_panel_v1_doubao_model_predictions_eval_report.md `
  --details-csv data_index/topology_panel_v1_doubao_model_predictions_eval_details.csv `
  --errors-csv data_index/topology_panel_v1_doubao_model_predictions_eval_errors.csv
```

## 3. Adapter 运行结果

- 预测行数：14 / 14
- API/解析错误：0
- adapter mode：`synthetic_from_counts` 14 条
- 说明：Doubao 本轮输出主要是节点、边、网络数量估计，未输出可直接用于几何拓扑匹配的完整 graph。因此 adapter 将计数结果转换为 schema-valid 的 synthetic graph，以便 evaluator 先做 count-level sanity evaluation。

## 4. Evaluator 结果

- 参考图有效率：1.0
- 预测图有效率：0.357143
- 缺失预测行：0
- 额外预测 panel_id：0
- 预测 invalid rows：9
- invalid reason：
  - `status_uncertain`：5
  - `status_unreadable`：4
- prediction error category：
  - `status`：9

### Count Error

| metric | MAE | MRE |
| --- | ---: | ---: |
| node_count | 500.857143 | 0.952608 |
| edge_count | 828.357143 | 0.977183 |
| net_count | 3.571429 | 3.214286 |

### 结构诊断

| diagnostic | min | max | mean |
| --- | ---: | ---: | ---: |
| isolated_edge_ratio | 0.0 | 0.0032 | 0.000443 |
| largest_net_edge_ratio | 0.9964 | 1.0 | 0.9993 |

## 5. 结论

Doubao 已经可以跑通完整 14 条 v1 baseline，说明当前真实模型接入链路是可用的：图片读取、API 调用、JSON 解析、schema 转换、evaluator 评测、CSV 错误定位都能闭环。

但从评测指标看，本轮 Doubao 结果还不能作为有效的 Topology Graph 预测 baseline。主要原因是模型没有稳定输出完整拓扑图，只给出非常粗的计数估计，且对复杂工业图纸经常判断为 `uncertain` 或 `unreadable`。因此当前结果应定位为：

- 正式记录的真实模型首轮接入结果；
- count-only / synthetic graph baseline；
- 后续 prompt、裁剪、局部图块输入、OCR/符号先验增强实验的对照基线；
- 不作为 topology graph v1 的有效性能上限。

## 6. 输出文件

- Adapter summary：`data_index/topology_panel_v1_doubao_model_predictions_summary.json`
- Adapter report：`data_index/topology_panel_v1_doubao_model_predictions_report.md`
- Prediction JSONL：`data_index/topology_panel_v1_doubao_model_predictions.jsonl`
- Eval summary：`data_index/topology_panel_v1_doubao_model_predictions_eval_summary.json`
- Eval report：`data_index/topology_panel_v1_doubao_model_predictions_eval_report.md`
- Eval details：`data_index/topology_panel_v1_doubao_model_predictions_eval_details.csv`
- Eval errors：`data_index/topology_panel_v1_doubao_model_predictions_eval_errors.csv`

## 7. 下一步建议

1. 固定本报告为 Doubao v1 baseline 的正式记录。
2. 做 prompt v2：强制模型只输出 JSON，并把 `status=ok/uncertain/unreadable` 与 count 字段分离。
3. 做 image input v2：优先尝试 panel 局部裁剪、放大线段区域、降低整图信息密度。
4. 做 task split：先让模型判断可读性与图纸类型，再对可读样本做 topology count 或局部连接预测。
5. 后续若要真正进入 graph-level 评测，需要模型输出节点、边、端点、连通网络，而不仅是数量。
