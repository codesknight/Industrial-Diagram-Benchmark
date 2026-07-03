# Data Format

## Raw Geometry JSON

当前 `datas/raw_json` 中的文件主要是 DXF 解析后的 Raw Geometry JSON。

典型结构：

```json
{
  "drawing_id": "sample",
  "source_dxf": "path/to/sample.dxf",
  "relative_source": "_P1_staging/sample.dxf",
  "entities": []
}
```

`entities` 常见类型：

- `LINE`: 直线
- `LWPOLYLINE`: 多段线
- `TEXT` / `MTEXT`: 文本
- `INSERT`: 块引用
- `CIRCLE`: 圆
- `ARC`: 圆弧

## Manifest Columns

`data_index/dataset_manifest.csv` 的核心字段：

- `drawing_key`: 样本主键
- `drawing_id`: 文件名去扩展名
- `phase`: P1/P2/P3
- `batch`: 原始 stage 或 batch
- `split`: train/val/test
- `dwg_path`: DWG 相对路径
- `dxf_path`: DXF 相对路径
- `raw_json_path`: Raw JSON 相对路径
- `png_path`: PNG 相对路径
- `has_dwg`, `has_dxf`, `has_raw_json`, `has_png`: 文件是否存在
- `complete_cad_triplet`: DWG/DXF/JSON 是否齐全
- `complete_all`: DWG/DXF/JSON/PNG 是否齐全
- `png_reuse_group_size`: 同一个 PNG 路径被多少个样本行复用

## Next Formats

后续建议逐步补齐：

```text
Raw Geometry JSON
  -> Normalized Geometry JSON
  -> Semantic Diagram JSON
  -> Topology Graph JSON
  -> VQA JSONL
```

## Clean Manifest

`data_index/clean_dataset_manifest.csv` 是非破坏式清洗后的样本清单。

当前清洗规则：

- 剔除缺少 DWG/DXF/Raw JSON/PNG 的样本
- 校验 Raw JSON 必须是对象，且包含 `entities` 列表
- 对共享同一个 PNG 路径的样本只保留一个代表样本
- 重复代表样本按 batch 优先级和 `drawing_key` 稳定选择

被剔除的样本写入：

```text
data_index/rejected_samples.csv
```

## Content Quality Scan

`data_index/content_quality_stats.csv` 是第二轮内容质量统计表。

它包含：

- Raw JSON 图元数量
- 文本、线段、多段线、块引用数量
- CAD 坐标范围
- PNG 宽高和文件大小
- 明显坏样本硬剔除原因
- 需要复核的质量标记
- 多子图候选标记 `needs_panel_split`

多子图候选写入：

```text
data_index/multi_panel_candidates.csv
```

多子图样本不应直接视为坏数据。建议后续生成 panel 级样本：

```text
parent drawing -> panel_001 / panel_002 / ...
```

第二轮硬剔除后的 drawing-level 样本写入：

```text
data_index/round2_clean_manifest.csv
data_index/round2_clean_train.csv
data_index/round2_clean_val.csv
data_index/round2_clean_test.csv
```

## Panel Manifest

`data_index/panel_manifest.csv` 是 panel 级样本入口。

核心字段：

- `panel_id`: panel 主键
- `parent_drawing_key`: 父 drawing 样本
- `parent_png_path`: 原始 PNG
- `panel_index`: panel 序号
- `panel_count`: 父 drawing 下的 panel 数
- `split_method`: `full` / `cad_gap` / `candidate_full_fallback`
- `panel_bbox_cad`: CAD 坐标系裁剪框
- `panel_bbox_png`: PNG 像素坐标裁剪框
- `panel_png_path`: panel 图像路径；多子图拆分样本默认位于 `outputs/panels/`
- `needs_review`: 自动拆分结果是否需要人工复核

## Review Labels

`data_index/panel_review_labels.csv` 是 HTML 审核表导出的人工标注结果。

应用标注结果：

```powershell
python scripts/apply_panel_review_labels.py
```

输出：

```text
data_index/panel_manifest_reviewed.csv
data_index/panel_manifest_usable.csv
data_index/panel_review_summary.json
```

## Watermark Scan

扫描图片内容水印/来源标记：

```powershell
python scripts/scan_watermarks.py
```

输出：

```text
data_index/watermark_scan.csv
data_index/watermark_candidates.csv
data_index/watermark_summary.json
data_index/watermark_report.md
data_index/source_marker_rows.csv
data_index/round2_clean_no_visible_watermark.csv
data_index/round2_clean_no_high_watermark.csv
data_index/round2_clean_no_source_markers.csv
```

当前过滤原则：

- 文件名/路径中出现 `wm666.taobao.com` 等来源标记，不作为过滤依据，后续统一重命名处理。
- Raw JSON 文本图元中出现 `星欣`、`图库`、`淘宝` 等水印关键词，视为可见内容水印候选，建议从 clean 训练/评估集中剔除或单独分组。
- 本脚本暂未做 PNG OCR，因此无法发现纯栅格水印；后续可接 OCR 扩展。

## Vision Watermark Review

使用本地 Ollama 视觉模型复查可见水印候选：

```powershell
python scripts/vision_watermark_review.py
```

如果默认目标模型不可运行，可以显式加入 fallback 模型：

```powershell
python scripts/vision_watermark_review.py --models deepseek-ocr:3b qwen2.5vl:7b qwen2.5vl:3b --max-side 768 --num-ctx 2048
```

输出：

```text
data_index/watermark_vision_model_outputs.csv
data_index/watermark_vision_consensus.csv
data_index/watermark_vision_summary.json
data_index/watermark_vision_report.md
```
