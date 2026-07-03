# Clean Dataset Report

This is a non-destructive cleaning report. Raw files are not deleted or moved.

## Summary

- Total manifest rows: 2099
- Candidate rows after asset checks: 2098
- Clean rows: 2075
- Rejected rows: 24
- Duplicate PNG groups: 23
- Duplicate PNG rows rejected: 23
- Raw JSON validation: True

## Clean Splits

- train: 1666
- val: 198
- test: 211

## Rejected Reasons

- missing_assets: 1
- duplicate_png: 23

## First Rejected Samples

| drawing_key | reason | detail |
|---|---|---|
| `_P3_staging_batch2/3XGN2高压开关柜` | missing_assets | DXF,JSON,PNG |
| `_P3_staging_batch4/10KV一次系统图,及全套二次原理图` | duplicate_png | kept=_P3_staging_batch1/10KV一次系统图,及全套二次原理图; png=datas/qa_and_png/P3_oda_output/10KV一次系统图,及全套二次原理图.png |
| `_P3_staging_batch4/10KV开闭所电气图` | duplicate_png | kept=_P3_staging_batch1/10KV开闭所电气图; png=datas/qa_and_png/P3_oda_output/10KV开闭所电气图.png |
| `_P3_staging_batch4/10KV配电系统设计图纸` | duplicate_png | kept=_P3_staging_batch3/10KV配电系统设计图纸; png=datas/qa_and_png/P3_oda_output/10KV配电系统设计图纸.png |
| `_P3_staging_batch4/10kV架空配电线路杆型图` | duplicate_png | kept=_P3_staging_batch1/10kV架空配电线路杆型图; png=datas/qa_and_png/P3_oda_output/10kV架空配电线路杆型图.png |
| `_P3_staging_batch4/EPS-DC系统模块输出灯具接线图17~2(gai)-R14版` | duplicate_png | kept=_P3_staging_batch3/EPS-DC系统模块输出灯具接线图17~2(gai)-R14版; png=datas/qa_and_png/P3_oda_output/EPS-DC系统模块输出灯具接线图17~2(gai)-R14版.png |
| `_P3_staging_batch4/EPS-DC系统模块输出灯具接线图17~20-R14版` | duplicate_png | kept=_P3_staging_batch3/EPS-DC系统模块输出灯具接线图17~20-R14版; png=datas/qa_and_png/P3_oda_output/EPS-DC系统模块输出灯具接线图17~20-R14版.png |
| `_P3_staging_batch4/M保护配置` | duplicate_png | kept=_P3_staging_batch2/M保护配置; png=datas/qa_and_png/P3_oda_output/M保护配置.png |
| `_P3_staging_batch4/WGB-111N 馈线保护二次回路端子排(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-111N 馈线保护二次回路端子排(手车); png=datas/qa_and_png/P3_oda_output/WGB-111N 馈线保护二次回路端子排(手车).png |
| `_P3_staging_batch4/WGB-111N 馈线保护原理图(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-111N 馈线保护原理图(手车); png=datas/qa_and_png/P3_oda_output/WGB-111N 馈线保护原理图(手车).png |
| `_P3_staging_batch4/WGB-112N 馈线保护二次回路端子排(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-112N 馈线保护二次回路端子排(手车); png=datas/qa_and_png/P3_oda_output/WGB-112N 馈线保护二次回路端子排(手车).png |
| `_P3_staging_batch4/WGB-112N 馈线保护原理图(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-112N 馈线保护原理图(手车); png=datas/qa_and_png/P3_oda_output/WGB-112N 馈线保护原理图(手车).png |
| `_P3_staging_batch4/WGB-113N 馈线保护二次回路端子排(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-113N 馈线保护二次回路端子排(手车); png=datas/qa_and_png/P3_oda_output/WGB-113N 馈线保护二次回路端子排(手车).png |
| `_P3_staging_batch4/WGB-113N 馈线保护原理图(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-113N 馈线保护原理图(手车); png=datas/qa_and_png/P3_oda_output/WGB-113N 馈线保护原理图(手车).png |
| `_P3_staging_batch4/WGB-114N 馈线保护二次回路端子排(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-114N 馈线保护二次回路端子排(手车); png=datas/qa_and_png/P3_oda_output/WGB-114N 馈线保护二次回路端子排(手车).png |
| `_P3_staging_batch4/WGB-114N 馈线保护原理图(手车)` | duplicate_png | kept=_P3_staging_batch3/WGB-114N 馈线保护原理图(手车); png=datas/qa_and_png/P3_oda_output/WGB-114N 馈线保护原理图(手车).png |
| `_P3_staging_batch2/保护配置图` | duplicate_png | kept=_P3_staging_batch1/保护配置图; png=datas/qa_and_png/P3_oda_output/保护配置图.png |
| `_P3_staging_batch4/异步电动机原理接线图` | duplicate_png | kept=_P3_staging_batch2/异步电动机原理接线图; png=datas/qa_and_png/P3_oda_output/异步电动机原理接线图.png |
| `_P3_staging_batch4/总图电力接线图` | duplicate_png | kept=_P3_staging_batch3/总图电力接线图; png=datas/qa_and_png/P3_oda_output/总图电力接线图.png |
| `_P3_staging_batch4/接线图` | duplicate_png | kept=_P3_staging_batch2/接线图; png=datas/qa_and_png/P3_oda_output/接线图.png |
| `_P3_staging_batch4/用电原理接线图-6kV配电装置平面布置图8` | duplicate_png | kept=_P3_staging_batch1/用电原理接线图-6kV配电装置平面布置图8; png=datas/qa_and_png/P3_oda_output/用电原理接线图-6kV配电装置平面布置图8.png |
| `_P3_staging_batch4/电容器保护二次原理图` | duplicate_png | kept=_P3_staging_batch2/电容器保护二次原理图; png=datas/qa_and_png/P3_oda_output/电容器保护二次原理图.png |
| `_P3_staging_batch4/电机控制原理及外引端子接线图` | duplicate_png | kept=_P3_staging_batch2/电机控制原理及外引端子接线图; png=datas/qa_and_png/P3_oda_output/电机控制原理及外引端子接线图.png |
| `_P3_staging_batch4/脱硫供配电系统接线图` | duplicate_png | kept=_P3_staging_batch2/脱硫供配电系统接线图; png=datas/qa_and_png/P3_oda_output/脱硫供配电系统接线图.png |
