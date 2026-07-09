# Hugging Face Release Files

生成日期：2026-07-09

本文档列出当前建议同步到 Hugging Face Dataset 的文件，以及每类文件在发布页中的用途。当前发布重点是 `Topology Panel v1 clean baseline`。

## 发布原则

- Hugging Face Dataset 托管大体积数据、benchmark JSONL、manifest、summary/report 和数据集卡片。
- GitHub 托管代码、脚本、协议、文档和实验记录。
- `Topology Panel v1` 只表示 14 条 clean baseline，不包含 v1.1 candidates。
- v1.1 candidates、abandoned、excluded badcase 可以作为边界说明文件上传，但不能并入正式 v1 baseline。

## Dataset Card

建议将下面文件内容复制为 Hugging Face Dataset 首页 `README.md`：

```text
docs/huggingface_dataset_card.md
```

该 card 已同步 GitHub README 中的版本边界：

```text
clean_baseline: 14
excluded_badcase: 125
improvement_target: 31
unreviewed: 1
```

## 必选：Topology Panel v1 Benchmark

这些文件构成当前正式 v1 benchmark 的最小可发布包。

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
data_index/topology_panel_v1_benchmark_manifest.jsonl
data_index/topology_panel_v1_benchmark_summary.json
data_index/topology_panel_v1_benchmark_report.md
data_index/topology_panel_v1_eval_summary.json
data_index/topology_panel_v1_eval_report.md
```

用途说明：

```text
topology_panel_v1_final_baseline_manifest.csv   正式 v1 baseline CSV，14 条
topology_panel_v1_benchmark_manifest.jsonl      模型评测入口 JSONL
topology_panel_v1_benchmark_summary.json        benchmark 包统计
topology_panel_v1_benchmark_report.md           benchmark 包人类可读报告
topology_panel_v1_eval_summary.json             默认评测 sanity check 结果
topology_panel_v1_eval_report.md                默认评测 sanity check 报告
```

## 必选：协议与状态说明

建议同步这些文档，方便使用者理解数据边界和评测方式。

```text
docs/topology_graph_eval_protocol_v1.md
docs/topology_panel_v1_release_status.md
README.md
```

说明：

```text
topology_graph_eval_protocol_v1.md      Topology Graph v1 评测协议
topology_panel_v1_release_status.md     中文发布状态说明
README.md                               GitHub 项目入口，可作为辅助说明
```

## 推荐：发布分区 Manifest

这些文件用于说明 v1 数据是如何从人工复核样本中筛选出来的。

```text
data_index/topology_panel_v1_release_manifest.csv
data_index/topology_panel_v1_release_train.csv
data_index/topology_panel_v1_release_val.csv
data_index/topology_panel_v1_release_test.csv
data_index/topology_panel_v1_release_summary.json
data_index/topology_panel_v1_release_report.md
```

用途说明：

```text
topology_panel_v1_release_manifest.csv     v1 release baseline 候选清单
topology_panel_v1_release_train.csv        train split，11 条
topology_panel_v1_release_val.csv          val split，1 条
topology_panel_v1_release_test.csv         test split，2 条
topology_panel_v1_release_summary.json     release 构建统计
topology_panel_v1_release_report.md        release 构建报告
```

## 可选：边界与排除文件

这些文件建议上传，但需要在数据集卡片里明确说明它们不属于正式 v1 baseline。

```text
data_index/topology_panel_v1_release_excluded_manifest.csv
data_index/topology_panel_v1_release_improvement_manifest.csv
data_index/topology_panel_v1_1_abandoned_manifest.csv
data_index/topology_panel_v1_1_keep_improvement_manifest.csv
data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv
data_index/topology_panel_v1_1_keep_over_connected_manifest.csv
```

用途说明：

```text
topology_panel_v1_release_excluded_manifest.csv       125 条排除 badcase
topology_panel_v1_release_improvement_manifest.csv    原始 31 条 improvement target
topology_panel_v1_1_abandoned_manifest.csv            19 条已放弃 still_fragmented
topology_panel_v1_1_keep_improvement_manifest.csv     当前保留 12 条 v1.1 改进候选
topology_panel_v1_1_keep_terminal_anchor_manifest.csv 3 条 terminal-anchor 候选
topology_panel_v1_1_keep_over_connected_manifest.csv  9 条 over-connected 候选
```

## 可选：审核 HTML

审核 HTML 文件体积较大，适合 GitHub 或本地使用。若上传 Hugging Face，建议放入单独目录并标注为 review artifact。

```text
data_index/topology_panel_v1_baseline_review.html
data_index/topology_panel_v1_1_active_improvement_review.html
data_index/topology_panel_v1_1_still_fragmented_diagnostic.html
```

这些 HTML 不属于模型评测输入。

## 暂不建议上传

以下文件更适合留在 GitHub 或本地工作区：

```text
experiment_records.md
scripts/
tools/
benchmark/
outputs/
```

如果需要让 Hugging Face 用户直接复现实验，应在 dataset card 中链接 GitHub，而不是复制整套工程脚本。

## 建议 Hugging Face 目录结构

建议在 Hugging Face Dataset 中采用下面的轻量结构：

```text
README.md
data_index/
  HF_RELEASE_FILES.md
  topology_panel_v1_final_baseline_manifest.csv
  topology_panel_v1_benchmark_manifest.jsonl
  topology_panel_v1_benchmark_summary.json
  topology_panel_v1_benchmark_report.md
  topology_panel_v1_eval_summary.json
  topology_panel_v1_eval_report.md
  topology_panel_v1_release_*.csv/json/md
  topology_panel_v1_1_*.csv/json/md
docs/
  topology_graph_eval_protocol_v1.md
  topology_panel_v1_release_status.md
```

如果同步原始数据，则继续沿用：

```text
datas/
  dwg_staging/
  dxf_staging/
  raw_json/
  qa_and_png/
```

## 上传前检查

上传前建议确认：

```powershell
git status --short
python benchmark/topology/evaluate_topology_graph_v1.py
python scripts/prepare_hf_release_package.py
```

评测 sanity check 应保持：

```text
evaluated_rows: 14
reference graph valid rate: 1.0
prediction graph valid rate: 1.0
node_count MAE/MRE: 0.0 / 0.0
edge_count MAE/MRE: 0.0 / 0.0
net_count MAE/MRE: 0.0 / 0.0
```

## 推荐发布说明

可在 Hugging Face commit message 或 release note 中使用：

```text
Add Topology Panel v1 clean baseline benchmark package.

This release includes 14 manually reviewed panel-level topology samples,
the benchmark JSONL manifest, evaluation protocol, sanity-check evaluation
outputs, and boundary manifests for excluded badcases and v1.1 candidates.
The formal Topology Panel v1 score should only use the 14 clean baseline rows.
```

## 自动打包脚本

可以使用下面命令自动生成本地上传包：

```powershell
python scripts/prepare_hf_release_package.py
```

默认输出：

```text
outputs/hf_release_topology_panel_v1/
```

默认不包含大型 HTML 审核表。如需一起复制审核 HTML：

```powershell
python scripts/prepare_hf_release_package.py --include-review-html
```

输出包内会自动生成：

```text
data_index/hf_release_package_manifest.csv
data_index/hf_release_package_summary.json
data_index/hf_release_package_report.md
```

生成本地包后，可以上传到 Hugging Face Dataset：

```powershell
python scripts/upload_hf_release_package.py
```

上传脚本默认使用：

```text
repo_id: yanhongliu/Industrial-Diagram-Benchmark
package_dir: outputs/hf_release_topology_panel_v1/
```

上传前可先预览文件列表：

```powershell
python scripts/upload_hf_release_package.py --dry-run
```

上传需要 Hugging Face 登录状态，任选一种：

```powershell
hf auth login
```

或在 `.env` 中设置：

```text
HF_TOKEN=...
```
