# Panel Splitting Strategy

部分 PNG 图像中包含多个子图、多个图框或多页图纸拼在同一张渲染图里。这类样本不应简单删除，因为它们对 CAD reconstruction 有价值；但如果直接用于 detection、VQA 或 image-to-JSON，会造成一个问题：一条样本中包含多个相对独立的视觉任务。

## Recommended Policy

保留两种粒度：

- Drawing-level: 保留整张图，用于 CAD reconstruction、全图检索、工程图整体理解。
- Panel-level: 将一张图拆成多个 panel，用于检测、OCR、VQA、拓扑问答。

## Workflow

1. 使用 `scripts/scan_content_quality.py` 生成 `data_index/multi_panel_candidates.csv`。
2. 人工复核候选样本，确认哪些是真正的多子图。
3. 对确认样本生成 `panel_manifest.csv`，每个 panel 一行。
4. 每个 panel 记录父样本和裁剪框。
5. 后续 VQA 和检测任务优先使用 panel-level manifest。

## Suggested Panel Manifest Fields

```text
panel_id
parent_drawing_key
parent_png_path
parent_raw_json_path
panel_index
panel_bbox_png
panel_bbox_cad
split
phase
panel_png_path
status
notes
```

## Detection Ideas

自动检测可以逐步增强：

- CAD 图元中心点投影：寻找横向/纵向大空白间隔。
- 图框检测：寻找大矩形边框、标题栏或重复图签。
- 图像投影：对二值化 PNG 做 connected components 或 whitespace segmentation。
- 人工复核：先把自动检测作为 candidate，不直接裁切覆盖原始数据。

## Current Rule

当前第二轮脚本只做候选标记：

```text
needs_panel_split = true
```

它不会裁切 PNG，也不会从第二轮 clean manifest 中删除多子图样本。
