# Industrial Diagram Benchmark

面向工业接线图理解、结构化解析、拓扑问答与 CAD 重建的数据集工程。

当前项目已有一批工业图纸数据，主要包含：

- `datas/dwg_staging/`: 原始 DWG 图纸
- `datas/dxf_staging/`: DWG 转换后的 DXF
- `datas/raw_json/`: DXF 解析得到的 Raw Geometry JSON
- `datas/qa_and_png/`: ODA 渲染得到的 PNG
- `docs/Industrial_Diagram_Benchmark_Roadmap.md`: 研究路线说明

数据托管在 Hugging Face Dataset：

```text
https://huggingface.co/datasets/yanhongliu/Industrial-Diagram-Benchmark
```

GitHub 仓库只管理工程代码、配置、文档和数据索引；大体积原始数据不直接进入 Git。

## Current Stage

当前阶段重点是把现有数据整理成可复现、可检查、可训练的数据集工程：

1. 统一生成数据清单 `data_index/dataset_manifest.csv`
2. 检查 DWG/DXF/JSON/PNG 是否一一对应
3. 输出缺失文件报告 `data_index/missing_assets.md`
4. 生成 `train/val/test` 划分
5. 为后续 Geometry JSON、Topology Graph、VQA、Benchmark 评估留出工程入口

## Project Layout

```text
configs/       数据集和 Benchmark 配置
scripts/       数据索引、校验、构建脚本
tools/         DXF/JSON/Graph/CAD 工具模块
benchmark/     评估脚本入口
agent/         Tool-Augmented VLM / CAD Agent 入口
data_index/    自动生成的数据清单、划分和质量报告
outputs/       实验输出、临时产物和评估结果
docs/          项目文档
datas/         原始和中间数据
```

## Quick Start

下载 Hugging Face Dataset 到本地 `datas/`：

```powershell
pip install -r requirements.txt
python scripts/download_dataset.py
```

生成数据清单、缺失报告和数据划分：

```powershell
python scripts/build_dataset_manifest.py
```

检查数据完整性：

```powershell
python scripts/check_dataset_integrity.py
```

如需抽取 JSON 图元统计，可额外开启：

```powershell
python scripts/build_dataset_manifest.py --inspect-json
```

生成非破坏式清洗后的样本清单：

```powershell
python scripts/clean_dataset_manifest.py
```

进行第二轮内容质量扫描，并标记多子图候选：

```powershell
python scripts/scan_content_quality.py
```

生成 panel 级样本清单，并对多子图候选生成本地裁剪图：

```powershell
python scripts/build_panel_manifest.py
```

生成可快速标注并导出 CSV 的 HTML 审核表：

```powershell
python scripts/build_panel_review_html.py
```

应用人工审核结果，并扫描图片内容水印/来源标记：

```powershell
python scripts/apply_panel_review_labels.py
python scripts/scan_watermarks.py
```

使用本地 Ollama 视觉模型复查水印候选：

```powershell
python scripts/vision_watermark_review.py --models deepseek-ocr:3b qwen2.5vl:7b qwen2.5vl:3b --max-side 768 --num-ctx 2048
```

生成最终可用的 drawing/panel 清单：

```powershell
python scripts/build_final_manifests.py
```

构建 Geometry 标准化中间表示：

```powershell
python scripts/build_normalized_geometry.py
```

构建 Topology Graph v0：

```powershell
python scripts/build_topology_graph.py
```

生成 Topology Graph HTML 审核表：

```powershell
python scripts/build_topology_review_html.py
```

生成 Topology-ready 训练/评估入口清单：

```powershell
python scripts/build_topology_ready_manifests.py
```

## Data Pipeline

```text
DWG
  -> DXF
  -> Raw Geometry JSON
  -> PNG
  -> Normalized Geometry JSON
  -> Topology Graph v0
  -> Semantic JSON
  -> VQA
  -> Benchmark
```

目前仓库中的 `raw_json` 主要是 Raw Geometry JSON；已补充 Geometry 标准化和 Topology Graph v0，后续会继续推进语义归一化、VQA 生成和 Benchmark 评估脚本。
