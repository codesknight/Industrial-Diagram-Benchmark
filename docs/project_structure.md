# Project Structure

本项目按“数据层、工具层、评估层、Agent 层”组织。

```text
datas/
  dwg_staging/      原始 DWG
  dxf_staging/      可解析 CAD 中间格式
  raw_json/         Raw Geometry JSON
  qa_and_png/       渲染 PNG，后续可扩展 QA 文件

data_index/
  dataset_manifest.csv   样本总表
  dataset_summary.json   数据统计
  missing_assets.md      缺失文件报告
  png_reuse_report.md    PNG 复用报告
  clean_dataset_manifest.csv  清洗后的样本总表
  clean_summary.json      清洗统计
  clean_report.md         清洗报告
  rejected_samples.csv    剔除样本和原因
  content_quality_stats.csv   第二轮内容质量统计
  content_quality_summary.json 第二轮内容质量摘要
  content_quality_report.md   第二轮内容质量报告
  multi_panel_candidates.csv  多子图候选
  round2_clean_manifest.csv   第二轮清洗样本总表
  round2_clean_train/val/test.csv 第二轮清洗划分
  panel_manifest.csv      panel 级样本总表
  panel_train/val/test.csv panel 级划分
  panel_summary.json      panel 级统计
  panel_report.md         panel 级拆分报告
  panel_review.html       panel 快速审核表
  panel_review_labels.csv panel 人工审核导出结果
  panel_manifest_reviewed.csv 合并审核标签后的 panel 表
  panel_manifest_usable.csv 可用 panel 表
  watermark_*.csv/json/md 水印扫描结果和报告
  watermark_vision_*.csv/json/md Ollama 视觉复查结果
  final_*               最终可用 drawing/panel 清单与报告
  train.csv              训练集样本
  val.csv                验证集样本
  test.csv               测试集样本

scripts/
  build_dataset_manifest.py   生成 manifest、报告和划分
  clean_dataset_manifest.py   生成非破坏式清洗 manifest
  scan_content_quality.py     第二轮内容质量扫描
  build_panel_manifest.py     生成 panel 级 manifest 和本地裁剪图
  build_panel_review_html.py  生成 panel HTML 审核表
  apply_panel_review_labels.py 合并 HTML 导出的人工审核标签
  scan_watermarks.py          扫描水印/来源标记候选
  vision_watermark_review.py  使用 Ollama 视觉模型复查水印候选
  build_final_manifests.py    生成最终可用 drawing/panel 清单
  check_dataset_integrity.py  检查 manifest 完整性

tools/
  后续放 dxf_parser、renderer、graph_builder、validator 等模块。

benchmark/
  后续放 detection、OCR、graph、VQA、CAD reconstruction 评估脚本。

agent/
  后续放工具调用 API、轨迹数据生成和 CAD Agent。
```

## Naming Rule

数据索引使用 `drawing_key` 作为主键，例如：

```text
_P1_staging/example
_P3_staging_batch2/example
```

该主键来自 DWG/DXF/JSON 的相对路径去掉扩展名。PNG 目录按阶段折叠：

- `_P1_staging` -> `P1_oda_output`
- `_P2_staging` -> `P2_oda_output`
- `_P3_staging_batch*` -> `P3_oda_output`

因此 P3 的 PNG 会按文件名回填到对应 batch 样本。
