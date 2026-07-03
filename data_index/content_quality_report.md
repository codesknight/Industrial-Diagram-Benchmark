# Content Quality Report

This is the second-round non-destructive content scan.

## Summary

- Total clean rows scanned: 2075
- Round-2 keep rows: 2054
- Hard reject rows: 21
- Review rows: 178
- Multi-panel candidates: 83

## Review Flags

- multi_panel_candidate: 83
- huge_entity_count: 51
- low_entity_count: 41
- low_line_geometry: 39
- no_text: 48

## Hard Reject Reasons

- empty_entities: 21
- degenerate_cad_bbox: 21

## Multi-Panel Handling Recommendation

Multi-panel candidates are not bad samples. They should be promoted from drawing-level samples to panel-level samples.

Recommended next workflow:

1. Review `data_index/multi_panel_candidates.csv`.
2. Confirm whether detected layout gaps correspond to real subfigures/pages.
3. Generate a `panel_manifest.csv` where each row is one cropped panel with a parent `drawing_key`.
4. Keep original drawing-level rows for CAD reconstruction, but use panel-level rows for VQA and detection tasks.

## First Multi-Panel Candidates

| drawing_key | split | x_clusters | y_clusters | max_x_gap | max_y_gap |
|---|---|---:|---:|---:|---:|
| `_P1_staging/001 220kV变电站电气主接线图` | train | 2 | 2 | 0.983 | 0.991 |
| `_P1_staging/02-主接线wm666.taobao.com` | train | 1 | 2 | 0.162 | 0.184 |
| `_P1_staging/05电气主接线` | train | 1 | 2 | 0.053 | 0.371 |
| `_P1_staging/110Kv变电站直流系统接线图` | val | 2 | 1 | 0.419 | 0.061 |
| `_P1_staging/110Kv变电站直流系统接线图wm666.taobao.com` | train | 2 | 1 | 0.419 | 0.061 |
| `_P1_staging/110kV变电站GIS布置平面图` | train | 2 | 1 | 0.768 | 0.032 |
| `_P1_staging/110kV变电站GIS布置平面图wm666.taobao.com` | train | 2 | 1 | 0.768 | 0.032 |
| `_P1_staging/110kV变电站总平面及竖向布置图` | train | 2 | 2 | 0.335 | 0.369 |
| `_P1_staging/110kv安斑东线、西线竣工图设计wm666.taobao.com` | test | 3 | 2 | 0.422 | 0.402 |
| `_P1_staging/主变保护测控屏屏面布置图及元件表` | val | 2 | 1 | 0.185 | 0.076 |
| `_P1_staging/主变压器35kV侧断路器在PWFXH-1111上的端子排(B066-500-1215)wm666.taobao.com` | train | 1 | 2 | 0.067 | 0.196 |
| `_P1_staging/主变进线柜原理图` | train | 2 | 1 | 0.188 | 0.011 |
| `_P1_staging/电气主接线` | train | 2 | 1 | 0.467 | 0.772 |
| `_P2_staging/02052D修-9   35kV进线及母联保护屏1BP接线端子图` | train | 2 | 3 | 0.252 | 0.250 |
| `_P2_staging/057 220KV继电器楼ups配电柜a段馈线接线图` | train | 2 | 2 | 0.983 | 0.991 |
| `_P2_staging/058 220KV继电器楼ups配电柜b段馈线接线图` | train | 2 | 2 | 0.983 | 0.991 |
| `_P2_staging/10KV变电所继电保护二次接线图` | val | 2 | 1 | 0.370 | 0.014 |
| `_P2_staging/220kVI,III分段隔离开关在监控柜上的端子排(B066-500-1721)wm666.taobao.com` | train | 1 | 2 | 0.071 | 0.214 |
| `_P2_staging/220kVI,II母联在监控柜上的端子排(B066-500-1723)wm666.taobao.com` | val | 1 | 2 | 0.066 | 0.211 |
| `_P2_staging/35KV变电所设计` | train | 1 | 2 | 0.331 | 0.180 |
| `_P2_staging/35KV变电所设计(1)` | train | 1 | 2 | 0.331 | 0.180 |
| `_P2_staging/35KV变电所设计(2)` | train | 1 | 2 | 0.331 | 0.180 |
| `_P2_staging/35KV变电所设计(3)` | train | 1 | 2 | 0.331 | 0.180 |
| `_P2_staging/35kV配电一次图` | train | 3 | 2 | 0.458 | 0.672 |
| `_P2_staging/SGT-变电所DLXT` | test | 2 | 1 | 0.209 | 0.450 |
| `_P2_staging/变电所全套图纸wm666.taobao.com` | train | 2 | 2 | 0.224 | 0.395 |
| `_P2_staging/变电站构架支架3d图` | train | 2 | 1 | 0.196 | 0.198 |
| `_P2_staging/某厂房变电所平面` | train | 2 | 1 | 0.313 | 0.434 |
| `_P2_staging/某厂房变电所平面wm666.taobao.com` | train | 2 | 1 | 0.313 | 0.434 |
| `_P2_staging/欧式箱式变电站基础` | train | 1 | 3 | 0.320 | 0.317 |
| `_P2_staging/电站、变电所电气及设备04` | train | 1 | 2 | 0.161 | 0.228 |
| `_P2_staging/电站、变电所电气及设备09` | val | 2 | 1 | 0.482 | 0.050 |
| `_P2_staging/电站、变电所电气及设备13` | train | 2 | 2 | 0.224 | 0.395 |
| `_P3_staging_batch1/10KV开闭所二次原理图` | train | 2 | 2 | 0.301 | 0.242 |
| `_P3_staging_batch1/11(RCS-9661B背面接线图(四))` | val | 1 | 2 | 0.097 | 0.222 |
| `_P3_staging_batch1/7-8(RCS-9000保护测控一体化装置II型安装开孔图)` | train | 2 | 1 | 0.219 | 0.070 |
| `_P3_staging_batch1/毕棚沟3#机保护表计单线图 2` | test | 2 | 1 | 0.318 | 0.252 |
| `_P3_staging_batch1/毕棚沟3#机厂用电接线图 7` | train | 2 | 1 | 0.210 | 0.138 |
| `_P3_staging_batch1/铁路配电所有载调压保护` | train | 3 | 1 | 0.322 | 0.033 |
| `_P3_staging_batch1/高压异步电机保护二次原理图` | train | 1 | 2 | 0.415 | 0.508 |
| `_P3_staging_batch2/发-变组保护测量配置图` | test | 1 | 2 | 0.101 | 0.407 |
| `_P3_staging_batch3/#1所用变压器在微机保护柜上的端子排(B066-500-2115)wm666.taobao.com` | val | 1 | 2 | 0.142 | 0.193 |
| `_P3_staging_batch3/#1所用变有载调压装置接线图(B066-500-2109)wm666.taobao.com` | train | 1 | 2 | 0.105 | 0.200 |
| `_P3_staging_batch3/02-10kV配电装置室平面布置图wm666.taobao.com` | train | 1 | 2 | 0.080 | 0.349 |
| `_P3_staging_batch3/500kV二滩I线路在监控屏上的端子排(B066-500-0415)wm666.taobao.com` | train | 1 | 2 | 0.072 | 0.191 |
| `_P3_staging_batch3/500kV母线侧断路器(13WDL)在监控柜上的端子排(B066-500-1503)wm666.taobao.com` | train | 1 | 2 | 0.054 | 0.256 |
| `_P3_staging_batch3/500kV线路在监控柜上的端子排(B080-500-1406)wm666.taobao.com` | train | 1 | 2 | 0.079 | 0.187 |
| `_P3_staging_batch3/D-05 #1发电机主回路电气接线图wm666.taobao.com` | val | 2 | 2 | 0.920 | 0.189 |
| `_P3_staging_batch3/D-06 #2发电机主回路电气接线图wm666.taobao.com` | train | 2 | 2 | 0.920 | 0.189 |
| `_P3_staging_batch3/D-07 #3发电机主回路电气接线图wm666.taobao.com` | train | 2 | 2 | 0.920 | 0.189 |
