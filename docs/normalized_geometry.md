# Normalized Geometry

`Normalized Geometry JSON` 是 Raw Geometry JSON 和后续 Semantic/Topology 表示之间的中间层。

目标：

- 统一图元类型字段
- 补充 bbox
- 保留文本、块引用和基础几何
- 输出稳定 schema，方便后续 Validator、Graph Builder、VQA 生成

生成命令：

```powershell
python scripts/build_normalized_geometry.py
```

默认输入：

```text
data_index/final_drawing_manifest.csv
```

默认输出：

```text
outputs/normalized_geometry/
data_index/normalized_geometry_manifest.csv
data_index/normalized_geometry_summary.json
data_index/normalized_geometry_report.md
data_index/low_geometry_review.csv
```

`outputs/normalized_geometry/` 不进入 Git；Git 只保存索引和统计。

## Schema

```json
{
  "schema": "industrial_diagram.normalized_geometry.v1",
  "drawing_key": "...",
  "source": {
    "raw_json_path": "...",
    "dxf_path": "...",
    "png_path": "..."
  },
  "stats": {
    "entity_count": 0,
    "bbox_entity_count": 0,
    "text_count": 0,
    "type_counts": {},
    "drawing_bbox": [0, 0, 0, 0]
  },
  "entities": []
}
```

## Entity Fields

每个 entity 至少包含：

```text
id
type
layer
bbox
geometry
```

常见类型：

- `LINE`
- `LWPOLYLINE`
- `TEXT` / `MTEXT`
- `INSERT`
- `CIRCLE`
- `ARC`
- `POINT`

未知或暂未深度解析的类型保留为 `geometry.primitive = raw`，避免丢失原始图元索引。

## Low Geometry Review

`low_geometry_review.csv` 记录标准化后图元数低于 20 的样本。

这类样本暂不自动剔除，因为它们可能是极简图纸、图签、局部符号或转换残留。建议在进入拓扑构建前人工复核。
