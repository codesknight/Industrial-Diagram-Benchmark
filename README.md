# Industrial Diagram Benchmark

Industrial Diagram Benchmark 是一个面向工业图纸理解、结构化解析、拓扑图抽取、VQA 与 CAD 重建的 benchmark 工程。

当前仓库主要管理工程代码、数据索引、评测协议、实验报告和发布文档；大体积原始数据托管在 Hugging Face Dataset：

```text
https://huggingface.co/datasets/yanhongliu/Industrial-Diagram-Benchmark
```

当前最稳定、可直接使用的发布单元是 **Topology Panel v1 clean baseline**。它是一个小规模但经过人工复核的 panel 级拓扑图评测基准。

## 当前发布状态

Topology Panel v1 的正式 baseline：

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

规模：

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

当前版本边界：

- `Topology Panel v1`：只表示 14 条已经人工确认的 clean baseline。
- `Topology Panel v1 excluded badcase`：125 条已排除样本，包括多子图、几何异常和非拓扑目标。
- `Topology Panel v1.1 candidates`：12 条仍待算法修复的候选样本，不进入 v1 正式评测。
- `still_fragmented` 19 条已经作为 abandoned 固化，不再作为当前 v1.1 修复目标。

更完整的中文状态说明见：

```text
docs/topology_panel_v1_release_status.md
```

## 快速使用 Benchmark

安装依赖：

```powershell
pip install -r requirements.txt
```

使用默认 reference-as-prediction 模式检查 benchmark 包和评测脚本：

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py
```

默认读取：

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
```

默认输出：

```text
data_index/topology_panel_v1_eval_summary.json
data_index/topology_panel_v1_eval_report.md
```

如需指定 manifest 或模型预测结果：

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --manifest data_index/topology_panel_v1_benchmark_manifest.jsonl `
  --predictions path/to/predictions.jsonl `
  --summary outputs/topology_eval_summary.json `
  --report outputs/topology_eval_report.md
```

预测文件应按 `panel_id` 与 benchmark JSONL 对齐。评测协议见：

```text
docs/topology_graph_eval_protocol_v1.md
```

## Benchmark 数据包

正式 benchmark JSONL：

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
```

来源 manifest：

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

数据包报告：

```text
data_index/topology_panel_v1_benchmark_report.md
data_index/topology_panel_v1_benchmark_summary.json
```

资产检查：

```text
missing images: 0
missing topology graphs: 0
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

## 数据版本边界

当前数据索引分为四类：

```text
clean_baseline: 14
excluded_badcase: 125
improvement_target: 31
unreviewed: 1
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

排除数据不参与正式 v1 评测：

```text
multi_subfigure_badcase: 43
bad_geometry: 63
not_topology_target: 19
```

v1.1 当前保留候选：

```text
data_index/topology_panel_v1_1_keep_improvement_manifest.csv
data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv
data_index/topology_panel_v1_1_keep_over_connected_manifest.csv
```

v1.1 当前保留候选数量：

```text
total: 12
terminal_anchor_module: 3
over_connected_repair: 9
```

这些候选只用于后续算法实验。除非重新生成、重新审核并形成新版本，否则不应混入 `Topology Panel v1` 的正式结果。

## 项目入口

常用入口：

```text
README.md                                      项目首页和快速入口
docs/topology_panel_v1_release_status.md      Topology Panel v1 中文发布状态
docs/topology_graph_eval_protocol_v1.md       Topology Graph v1 评测协议
docs/topology_panel_v1_1_plan.md              v1.1 改进计划
docs/project_structure.md                     更详细的目录说明
experiment_records.md                         实验过程记录
```

核心目录：

```text
configs/       数据集和 benchmark 配置
scripts/       数据索引、清洗、审核表、manifest 构建脚本
tools/         DXF/JSON/Graph/CAD 工具模块
benchmark/     评测脚本入口
agent/         Tool-Augmented VLM / CAD Agent 入口
data_index/    自动生成的数据清单、划分、质量报告和 benchmark 包
outputs/       实验输出、临时产物和评测结果
docs/          项目文档
datas/         原始和中间数据，通常不直接进入 Git
```

## 数据处理流程

整体数据管线：

```text
DWG
  -> DXF
  -> Raw Geometry JSON
  -> PNG
  -> Panel Manifest
  -> Normalized Geometry JSON
  -> Topology Graph
  -> Human Review
  -> Benchmark JSONL
  -> Evaluation
```

基础数据索引：

```powershell
python scripts/download_dataset.py
python scripts/build_dataset_manifest.py
python scripts/check_dataset_integrity.py
```

清洗与 panel 级样本：

```powershell
python scripts/clean_dataset_manifest.py
python scripts/scan_content_quality.py
python scripts/build_panel_manifest.py
python scripts/build_panel_review_html.py
python scripts/apply_panel_review_labels.py
python scripts/scan_watermarks.py
python scripts/build_final_manifests.py
```

Geometry 与 Topology：

```powershell
python scripts/build_normalized_geometry.py
python scripts/build_topology_graph.py
python scripts/build_topology_review_html.py
python scripts/build_topology_ready_manifests.py
python scripts/apply_topology_review_labels.py
```

Topology Panel v1：

```powershell
python scripts/build_topology_panel_v1_pilot.py
python scripts/build_topology_panel_v1_review_html.py
python scripts/build_topology_panel_v1_release.py
python scripts/build_topology_panel_v1_benchmark_package.py
python benchmark/topology/evaluate_topology_graph_v1.py
```

v1.1 诊断和候选管理：

```powershell
python scripts/run_topology_panel_v1_1_still_fragmented_experiment.py
python scripts/build_topology_panel_v1_1_still_fragmented_diagnostic_html.py
python scripts/apply_topology_panel_v1_1_abandoned_policy.py
python scripts/build_topology_panel_v1_1_active_improvement_review_html.py
python scripts/apply_topology_panel_v1_1_active_improvement_review_labels.py
```

## 当前建议

短期优先级：

1. 固化 README、HuggingFace dataset card 和发布文件清单。
2. 保持 `Topology Panel v1` 与 `Topology Panel v1.1 candidates` 的边界清晰。
3. 使用 14 条 clean baseline 先形成可复现评测闭环。
4. 后续再针对 3 条 terminal-anchor 和 9 条 over-connected 候选做 v1.1 算法实验。
