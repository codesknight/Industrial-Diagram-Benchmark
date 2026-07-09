# Topology Panel v1 Release Note

发布日期：2026-07-09

发布名称：`Topology Panel v1 clean baseline`

GitHub：

```text
https://github.com/codesknight/Industrial-Diagram-Benchmark
```

Hugging Face Dataset：

```text
https://huggingface.co/datasets/yanhongliu/Industrial-Diagram-Benchmark
```

## 发布摘要

`Topology Panel v1` 是 Industrial Diagram Benchmark 的第一版 panel 级拓扑图评测基准。当前版本采用严格人工复核边界，只发布 **14 条 clean baseline 样本**，用于验证工业图纸 panel 图像到 topology graph 的结构化预测能力。

这次发布完成了一个最小但完整的 benchmark 闭环：

```text
panel samples
  -> human review
  -> clean baseline manifest
  -> benchmark JSONL
  -> evaluation protocol
  -> evaluation script
  -> Hugging Face release package
```

## 版本边界

请注意：`Topology Panel v1` 只表示 14 条 clean baseline，不包含 badcase、未复核样本或 v1.1 改进候选。

当前人工复核样本分区如下：

```text
clean_baseline: 14
excluded_badcase: 125
improvement_target: 31
unreviewed: 1
```

正式 v1 baseline 划分：

```text
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

不进入正式 v1 baseline 的排除样本：

```text
multi_subfigure_badcase: 43
bad_geometry: 63
not_topology_target: 19
```

v1.1 当前保留 12 条改进候选，仅用于后续算法实验：

```text
terminal_anchor_module: 3
over_connected_repair: 9
```

此前的 `still_fragmented` 19 条已经固化为 abandoned，不再作为当前 v1.1 修复目标。

## 核心文件

正式 baseline：

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

Benchmark JSONL：

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
```

评测协议：

```text
docs/topology_graph_eval_protocol_v1.md
```

评测脚本：

```text
benchmark/topology/evaluate_topology_graph_v1.py
```

发布状态说明：

```text
docs/topology_panel_v1_release_status.md
```

Hugging Face 发布文件清单：

```text
data_index/HF_RELEASE_FILES.md
```

## Benchmark 数据概览

资产检查：

```text
missing images: 0
missing topology graphs: 0
```

图结构统计：

```text
node_count mean: 518.5
edge_count mean: 841.6429
net_count mean: 1.2857
intersection_count mean: 440.2857
isolated_edge_ratio mean: 0.0004
largest_net_edge_ratio mean: 0.9993
```

这些统计来自 14 条正式 baseline 样本。

## 快速评测

安装依赖：

```powershell
pip install -r requirements.txt
```

运行默认 sanity check：

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py
```

默认模式为 `reference_as_prediction`，用于验证 benchmark package 与 evaluator 的一致性。

当前默认评测结果：

```text
evaluated_rows: 14
prediction_mode: reference_as_prediction
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

如果要评测模型预测结果：

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --manifest data_index/topology_panel_v1_benchmark_manifest.jsonl `
  --predictions path/to/predictions.jsonl `
  --summary outputs/topology_eval_summary.json `
  --report outputs/topology_eval_report.md
```

预测文件应按 `panel_id` 与 benchmark JSONL 对齐。

## Hugging Face 发布包

本次发布已经上传到 Hugging Face Dataset：

```text
yanhongliu/Industrial-Diagram-Benchmark
```

本地发布包生成命令：

```powershell
python scripts/prepare_hf_release_package.py
```

默认输出目录：

```text
outputs/hf_release_topology_panel_v1/
```

上传命令：

```powershell
python scripts/upload_hf_release_package.py
```

本次上传结果：

```text
uploaded files: 26
remote key files verified: 4
remote dataset file count after check: 27
```

远端已确认存在的关键文件：

```text
README.md
data_index/topology_panel_v1_benchmark_manifest.jsonl
data_index/hf_release_package_summary.json
docs/topology_graph_eval_protocol_v1.md
```

## 使用建议

推荐在论文、报告和实验表格中这样引用当前版本：

```text
Industrial Diagram Benchmark - Topology Panel v1 clean baseline
```

推荐报告的核心信息：

```text
samples: 14
split: train 11 / val 1 / test 2
task: panel image to topology graph
protocol: docs/topology_graph_eval_protocol_v1.md
benchmark jsonl: data_index/topology_panel_v1_benchmark_manifest.jsonl
```

如果使用 v1.1 candidates 做算法实验，必须单独说明，不应把它们合并进正式 v1 分数。

## 已知限制

- 当前 baseline 样本数较小，适合作为第一版可复现评测闭环，不适合作为大规模训练集。
- v1.1 candidates 尚未通过修复后复核，不能进入正式 v1 baseline。
- 多子图样本已经作为 badcase 排除，不再进行 panel split v2。
- 当前评测重点是拓扑图结构质量，尚未覆盖完整语义理解、VQA 或 CAD 重建指标。
- 模型预测 JSONL 的更严格 schema 校验和 per-sample error CSV 仍待后续补强。

## 下一步建议

建议后续按以下顺序推进：

1. 生成 `data_index/topology_panel_v1_prediction_template.jsonl`，固定模型预测输入格式。
2. 扩展 `benchmark/topology/evaluate_topology_graph_v1.py`，输出 per-sample details CSV 和 error CSV。
3. 构建 dummy baseline 或 oracle-minus baseline，验证指标对拓扑错误的敏感性。
4. 启动 v1.1 `terminal_anchor_module` 小规模修复实验。
5. 等 v1.1 修复样本通过重新复核后，再考虑形成 `Topology Panel v1.1` 或 `Topology Panel v2`。

## 发布状态

本版本已经完成：

```text
GitHub README updated
release status document generated
Hugging Face dataset card updated
HF release package generated
HF release package uploaded
remote key files verified
```

当前 release note 可作为 README、Hugging Face dataset card、论文实验说明和项目交接材料的统一参考。
