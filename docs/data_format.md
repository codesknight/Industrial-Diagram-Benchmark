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
