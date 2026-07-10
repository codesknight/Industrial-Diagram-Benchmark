# Industrial Diagram Benchmark 项目阶段性总览

日期：2026-07-10

## 1. 项目定位

Industrial Diagram Benchmark 面向工业电气图纸理解，当前阶段重点完成了从原始图纸数据到 panel 级拓扑图评测基准的工程闭环。项目覆盖数据清洗、panel 拆分、拓扑图生成、人工审核、benchmark JSONL、evaluator、模型预测 adapter、leaderboard 与 Hugging Face 发布包。

当前最稳定的正式发布单元是 `Topology Panel v1 clean baseline`。它规模较小，但数据边界清晰、人工复核严格、评测脚本可复现，适合作为第一版拓扑图理解实验基准。

## 2. 数据版本边界

| partition | rows |
| --- | --- |
| excluded_badcase | 125 |
| improvement_target | 31 |
| unreviewed | 1 |
| clean_baseline | 14 |

正式 v1 只包含 `clean_baseline` 的 14 条样本。其他分区只用于边界说明、badcase 分析或后续算法实验，不参与正式 v1 score。

### Badcase 与 v1.1 策略

| type | rows |
| --- | --- |
| multi_subfigure_badcase | 43 |
| bad_geometry | 63 |
| not_topology_target | 19 |

v1.1 中原始 improvement target 为 31 条，其中 19 条 `still_fragmented` 已固化为 abandoned，不再作为修复实验目标；剩余 12 条保留为 active improvement candidates。

| route | rows |
| --- | --- |
| terminal_anchor_module | 3 |
| over_connected_repair | 9 |

## 3. Topology Panel v1 Benchmark

- Benchmark JSONL：`data_index/topology_panel_v1_benchmark_manifest.jsonl`
- Evaluation protocol：`docs/topology_graph_eval_protocol_v1.md`
- Record count：14
- Split：train 11 / val 1 / test 2
- Asset check：missing image 0，missing graph 0

### Graph 规模统计

| metric | min | max | mean |
| --- | --- | --- | --- |
| node_count | 204.0 | 731.0 | 518.5 |
| edge_count | 337.0 | 1165.0 | 841.6429 |
| net_count | 1.0 | 3.0 | 1.2857 |
| intersection_count | 184.0 | 628.0 | 440.2857 |
| isolated_edge_ratio | 0.0 | 0.0032 | 0.0004 |
| largest_net_edge_ratio | 0.9964 | 1.0 | 0.9993 |

## 4. 评测协议与脚本

Topology Graph v1 的评测协议以 panel 为单位，要求预测结果按 `panel_id` 对齐，并输出 graph validity、node_count、edge_count、net_count 等指标。当前 evaluator 已支持：

- 默认 `reference_as_prediction` sanity check。
- 模型预测 JSONL schema 校验。
- per-sample `eval_details.csv`。
- 错误定位 `eval_errors.csv`。
- oracle-minus sanity baseline，用于确认指标对删边、扰动节点等真实拓扑错误敏感。

核心入口：`benchmark/topology/evaluate_topology_graph_v1.py`。

## 5. 模型实验结果

真实模型实验目前以 Doubao 为主，目标先限定为 count-level synthetic graph baseline。模型输出 node/edge/net count 后，由 adapter 转成 evaluator 可接受的 synthetic graph，用于统一指标比较。

当前最佳模型基线：

- Method：`doubao_prompt_v3_tile2x2_overlap10`
- Model：Doubao
- Prompt：v3
- Image input：tile2x2 + 10% overlap
- Aggregation：node=sum；edge=sum；net=mean_clamped3
- Rows：14
- Prediction valid rate：1.0
- node_count MAE：362.642857
- edge_count MAE：687.857143
- net_count MAE：0.857143

关键实验结论：

- 相比整图 512 输入，tile2x2 + overlap10 在 10 / 14 个样本改善 node count，在 10 / 14 个样本改善 edge count。
- Auto judge 判定：10 个样本直接 prefer overlap10，2 个样本需要风险监控。
- 单纯提高整图分辨率到 1024 没有带来收益，说明主要瓶颈不是像素不足，而是整图信息密度过高。
- prompt v3 解决了 v2 的 net_count 过估计问题；后续重点应转向图像输入策略和混合拓扑提取 pipeline。

实验结果总表：`data_index/topology_panel_v1_experiment_table.csv` 与 `docs/topology_panel_v1_experiment_table.md`。

## 6. 发布状态

GitHub 与 Hugging Face Dataset 已同步当前版本边界和 best model baseline：

- GitHub：`https://github.com/codesknight/Industrial-Diagram-Benchmark`
- Hugging Face Dataset：`yanhongliu/Industrial-Diagram-Benchmark`
- HF release package：`outputs/hf_release_topology_panel_v1/`
- Dataset card：`docs/huggingface_dataset_card.md`
- Release status：`docs/topology_panel_v1_release_status.md`

## 7. 可答辩表述

本阶段的核心贡献可以概括为：构建了一个面向工业图纸拓扑理解的 panel 级 benchmark 原型，明确区分 clean baseline、excluded badcase 和 v1.1 improvement candidates；实现了从数据清洗、人工审核到 benchmark JSONL 和 evaluator 的可复现实验闭环；并完成了真实视觉模型 Doubao 在该基准上的多轮 prompt / image-input 对比实验，最终固化了 tile2x2 + overlap10 的当前最佳 count-level baseline。

## 8. 下一步建议

1. 生成答辩图表：MAE 柱状图、per-sample delta heatmap、数据流转图。
2. 将 `project_final_summary.md` 的内容整理进 `答辩汇报总结.md`。
3. 建立 hybrid pipeline：传统线段/交点提取 + OCR/符号检测 + VLM tile-level 审核。
4. 在 v1.1 active improvement candidates 上验证 terminal-anchor 和 over-connected repair 模块。

## 9. 关键文件索引

- `data_index/topology_panel_v1_final_baseline_manifest.csv`
- `data_index/topology_panel_v1_benchmark_manifest.jsonl`
- `docs/topology_graph_eval_protocol_v1.md`
- `benchmark/topology/evaluate_topology_graph_v1.py`
- `data_index/topology_panel_v1_model_leaderboard.csv`
- `data_index/topology_panel_v1_best_model_summary.json`
- `docs/topology_panel_v1_best_model_baseline.md`
- `docs/topology_panel_v1_release_status.md`
- `docs/huggingface_dataset_card.md`
