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
  train.csv              训练集样本
  val.csv                验证集样本
  test.csv               测试集样本

scripts/
  build_dataset_manifest.py   生成 manifest、报告和划分
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
