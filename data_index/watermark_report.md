# Watermark Scan Report

This report scans filenames/paths and Raw JSON text entities for watermark/source keywords.
Filename/path hits are source markers only. Filtering is based on visible text hits.

## Summary

- Total rows scanned: 2054
- Visible watermark rows: 12
- Source marker rows: 585
- Source-marker-only rows: 585

## Recommendation

- Visible watermark: filter from clean training/evaluation or place in a separate watermark split.
- Source marker only: do not filter by default; filename/source marker will be normalized later.
- Do not delete raw files. Keep filtering manifest-based.

## Keyword Counts

- taobao: 6
- 淘宝: 6
- 图库: 7
- 星欣: 7

## First Candidates

| drawing_key | confidence | source_marker_hits | visible_text_hits |
|---|---|---|---|
| `_P1_staging/110kV开关站+ABB避雷针高度计算` | visible |  | taobao;淘宝 |
| `_P1_staging/某医院高低压电气主接线图` | visible |  | taobao;淘宝 |
| `_P2_staging/1B1变电所低压系统` | visible |  | 图库;星欣 |
| `_P2_staging/1B2变电所低压系统` | visible |  | 图库;星欣 |
| `_P2_staging/35kv高压配电室电缆沟平面图` | visible |  | taobao;图库;星欣;淘宝 |
| `_P2_staging/中心变电站` | visible |  | taobao;淘宝 |
| `_P2_staging/体育场变电所电气平面图` | visible |  | taobao;淘宝 |
| `_P2_staging/变电所平面布置图__473` | visible |  | taobao;淘宝 |
| `_P3_staging_batch4/1～3层电照系统及接线图` | visible |  | 图库;星欣 |
| `_P3_staging_batch4/中置柜一二次接线图` | visible |  | 图库;星欣 |
| `_P3_staging_batch4/许继微机保护CAD图` | visible |  | 图库;星欣 |
| `_P3_staging_batch4/铁路局机关10kV配电所电气一次图纸` | visible |  | 图库;星欣 |
