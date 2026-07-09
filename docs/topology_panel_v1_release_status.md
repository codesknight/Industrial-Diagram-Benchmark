# Topology Panel v1 发布状态说明

生成日期：2026-07-09

本文档用于说明当前 Topology Panel v1 的正式发布状态、可用于评测的数据范围、已经排除的数据、v1.1 改进候选，以及后续建议。它的定位是项目阶段性断点说明，方便后续更新 README、HuggingFace 数据集卡片、实验交接文档和论文实验记录。

## 一句话结论

当前可以正式发布的是 **Topology Panel v1 clean baseline**，共 **14 条 panel 级样本**。这些样本已经通过人工复核，可以作为第一版拓扑图评测基准。

v1.1 暂时不进入正式 baseline。v1.1 当前只保留 **12 条改进候选**，用于后续算法实验，其中：

- `needs_terminal_anchor`：3 条
- `over_connected`：9 条

此前的 `still_fragmented` 19 条已经正式放弃，不再作为 v1.1 修复目标。

## 正式 v1 Baseline

正式 baseline 文件：

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

样本数量：

```text
total: 14
train: 11
val: 1
test: 2
```

阶段分布：

```text
P1: 4
P2: 1
P3: 9
```

人工复核结论：

```text
confirmed_baseline: 14
needs_recheck: 0
removed: 0
```

这 14 条是当前唯一推荐进入正式 benchmark 的样本。后续算法实验、模型训练或论文表格中，如果使用 “Topology Panel v1 baseline”，应默认只引用这个 manifest。

## Benchmark JSONL Package

已生成 benchmark JSONL：

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
```

对应协议文档：

```text
docs/topology_graph_eval_protocol_v1.md
```

资产检查结果：

```text
missing_image_count: 0
missing_graph_count: 0
```

图统计概览：

```text
node_count mean: 518.5
edge_count mean: 841.6429
net_count mean: 1.2857
intersection_count mean: 440.2857
isolated_edge_ratio mean: 0.0004
largest_net_edge_ratio mean: 0.9993
```

## 评测入口

当前已有第一个 v1 评测脚本：

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py
```

默认模式是 `reference_as_prediction`，用于验证 benchmark 包和评测逻辑本身是否一致。在该模式下：

```text
evaluated_rows: 14
reference graph valid rate: 1.0
prediction graph valid rate: 1.0
node_count MAE/MRE: 0.0 / 0.0
edge_count MAE/MRE: 0.0 / 0.0
net_count MAE/MRE: 0.0 / 0.0
```

评测输出：

```text
data_index/topology_panel_v1_eval_summary.json
data_index/topology_panel_v1_eval_report.md
```

后续如果接入模型预测结果，应把预测 JSONL 作为输入，与 `data_index/topology_panel_v1_benchmark_manifest.jsonl` 中的 reference graph 对齐评测。

## v1 排除数据

v1 发布时，人工复核样本总数为 171 条。最终分区如下：

```text
clean_baseline: 14
excluded_badcase: 125
improvement_target: 31
unreviewed: 1
```

正式排除 badcase：

```text
data_index/topology_panel_v1_release_excluded_manifest.csv
```

排除原因：

```text
multi_subfigure_badcase: 43
bad_geometry: 63
not_topology_target: 19
```

说明：

- `multi_subfigure_badcase`：画面包含多个子图，不再做 panel split v2，直接作为 badcase 排除。
- `bad_geometry`：几何本身异常，拓扑图生成或评测不可靠。
- `not_topology_target`：不适合当前拓扑图任务。

这些样本不进入 v1 baseline，也不建议用于第一版正式评测。

## v1.1 改进候选

原始 v1 improvement target 共 31 条：

```text
data_index/topology_panel_v1_release_improvement_manifest.csv
```

原始问题类型：

```text
still_fragmented: 19
needs_terminal_anchor: 3
over_connected: 9
```

经过 v1.1 第一轮诊断后，`still_fragmented` 19 条已经固化为 abandoned：

```text
data_index/topology_panel_v1_1_abandoned_manifest.csv
```

abandoned 诊断标签：

```text
no_line_geometry: 1
non_topology_target: 4
needs_panel_split_badcase: 7
terminal_anchor_needed: 2
true_fragmentation: 5
```

这些 abandoned 样本只保留作错误分析或未来人工覆盖，不再作为当前 v1.1 修复实验目标。

当前仍保留的 active improvement：

```text
data_index/topology_panel_v1_1_keep_improvement_manifest.csv
```

数量：

```text
total: 12
terminal_anchor_module: 3
over_connected_repair: 9
```

细分文件：

```text
data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv
data_index/topology_panel_v1_1_keep_over_connected_manifest.csv
```

重要边界：

- 这 12 条还没有进入正式 v1 baseline。
- 后续即使算法修复成功，也需要重新生成结果、重新复核，再决定是否进入 v1.1 或 v2。
- 当前论文/报告中的正式 baseline 数字仍然是 14 条。

## 当前已固化的关键文件

正式 baseline：

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
data_index/topology_panel_v1_final_baseline_summary.json
data_index/topology_panel_v1_final_baseline_report.md
```

发布 manifest：

```text
data_index/topology_panel_v1_release_manifest.csv
data_index/topology_panel_v1_release_train.csv
data_index/topology_panel_v1_release_val.csv
data_index/topology_panel_v1_release_test.csv
data_index/topology_panel_v1_release_excluded_manifest.csv
data_index/topology_panel_v1_release_improvement_manifest.csv
data_index/topology_panel_v1_release_summary.json
data_index/topology_panel_v1_release_report.md
```

Benchmark package：

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
data_index/topology_panel_v1_benchmark_summary.json
data_index/topology_panel_v1_benchmark_report.md
```

评测协议和脚本：

```text
docs/topology_graph_eval_protocol_v1.md
benchmark/topology/evaluate_topology_graph_v1.py
```

v1.1 状态：

```text
docs/topology_panel_v1_1_plan.md
data_index/topology_panel_v1_1_abandoned_manifest.csv
data_index/topology_panel_v1_1_keep_improvement_manifest.csv
data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv
data_index/topology_panel_v1_1_keep_over_connected_manifest.csv
```

## 建议的下一步

建议接下来不要马上继续修拓扑算法，而是先完成发布说明层面的整理：

1. 更新 `README.md`，把当前数据状态、任务定义、目录结构、v1 baseline 和评测入口写清楚。
2. 更新 HuggingFace dataset card，说明 v1 baseline、excluded badcase、improvement targets 的边界。
3. 准备一个 `data_index/HF_RELEASE_FILES.md` 或类似清单，列出需要上传到 HuggingFace 的 manifest、JSONL、报告和可选预览文件。
4. 在文档层面固化命名：`Topology Panel v1` 表示 14 条 clean baseline；`Topology Panel v1.1 candidates` 表示 12 条仍待算法实验的改进候选。
5. 等发布说明稳定后，再进入 v1.1 算法实验，优先考虑 `terminal_anchor_module`，因为它只有 3 条，范围小，容易形成可控实验闭环。

## 当前阶段判断

当前项目已经完成了从“清洗和人工复核”到“可评测 benchmark package”的最小闭环：

```text
panel samples -> human review -> clean baseline -> benchmark JSONL -> eval protocol -> eval script
```

这意味着 Topology Panel v1 可以先作为一个小规模但规则清晰的基准发布。后续重点应从继续扩大自动修复，转为先把发布材料、复现实验入口和数据边界写清楚，再逐步扩充 v1.1/v2。
