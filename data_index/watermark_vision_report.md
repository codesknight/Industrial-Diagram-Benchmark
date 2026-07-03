# Watermark Vision Review Report

This report uses local Ollama vision models to review visible watermark candidates.

## Summary

- Input rows: 12
- Models: deepseek-ocr:3b, qwen2.5vl:7b, qwen2.5vl:3b
- Max side: 768
- Context: 2048

## Consensus Counts

- likely_visible_watermark: 10
- single_model_not_visible: 2

## Model Status Counts

- deepseek-ocr:3b: {'error': 12}
- qwen2.5vl:7b: {'error': 12}
- qwen2.5vl:3b: {'false': 2, 'true': 10}

## Rows

| drawing_key | consensus | positive_models | negative_models | json_text_hits |
|---|---|---|---|---|
| `_P1_staging/110kV开关站+ABB避雷针高度计算` | likely_visible_watermark | qwen2.5vl:3b |  | taobao;淘宝 |
| `_P1_staging/某医院高低压电气主接线图` | likely_visible_watermark | qwen2.5vl:3b |  | taobao;淘宝 |
| `_P2_staging/1B1变电所低压系统` | likely_visible_watermark | qwen2.5vl:3b |  | 图库;星欣 |
| `_P2_staging/1B2变电所低压系统` | likely_visible_watermark | qwen2.5vl:3b |  | 图库;星欣 |
| `_P2_staging/35kv高压配电室电缆沟平面图` | likely_visible_watermark | qwen2.5vl:3b |  | taobao;图库;星欣;淘宝 |
| `_P2_staging/中心变电站` | likely_visible_watermark | qwen2.5vl:3b |  | taobao;淘宝 |
| `_P2_staging/体育场变电所电气平面图` | single_model_not_visible |  | qwen2.5vl:3b | taobao;淘宝 |
| `_P2_staging/变电所平面布置图__473` | likely_visible_watermark | qwen2.5vl:3b |  | taobao;淘宝 |
| `_P3_staging_batch4/1～3层电照系统及接线图` | single_model_not_visible |  | qwen2.5vl:3b | 图库;星欣 |
| `_P3_staging_batch4/中置柜一二次接线图` | likely_visible_watermark | qwen2.5vl:3b |  | 图库;星欣 |
| `_P3_staging_batch4/许继微机保护CAD图` | likely_visible_watermark | qwen2.5vl:3b |  | 图库;星欣 |
| `_P3_staging_batch4/铁路局机关10kV配电所电气一次图纸` | likely_visible_watermark | qwen2.5vl:3b |  | 图库;星欣 |
