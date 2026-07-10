# Topology Panel v1 Image Input Delta Analysis

日期：2026-07-10

## 目的

本分析将整图输入、1024 整图输入、tile2x2、tile2x2 overlap10 的 per-sample 误差放到同一张表里，验证 overlap10 的平均收益是否由多数样本支撑，并定位重复计数风险样本。

## 总体结果

| setting | node MAE | edge MAE | net MAE |
| --- | ---: | ---: | ---: |
| whole_v3_512 | 394.642857 | 715.642857 | 0.857143 |
| whole_v3_1024 | 399.571429 | 724.285714 | 0.928571 |
| tile2x2 | 378.285714 | 713.5 | 0.714286 |
| tile2x2_overlap10 | 362.642857 | 687.857143 | 0.857143 |

## Gain Counts vs Whole v3@512

- node error improved on 10 / 14 panels.
- edge error improved on 10 / 14 panels.
- net error improved on 2 / 14 panels.

## Pattern Counts

- node_edge_gain: 9
- node_edge_net_gain: 1
- no_count_gain: 4

## Per-Sample Delta Table

| panel_id | decision | pattern | edge delta vs 512 | node delta vs 512 | net delta vs 512 | edge delta overlap-tile | tags |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| _P3_staging_batch1/QA-D401-06(10kV开关柜柜顶小母线布置图)#panel_000 | prefer_overlap10 | node_edge_gain | -151.0 | -96.0 | 0.0 | -80.0 | overlap_edge_benefit;overlap_node_benefit;better_than_whole_image |
| _P1_staging/主变压器35kV侧断路器在PWFXH-1111上的端子排(B066-500-1215)wm666.taobao.com#panel_002 | prefer_overlap10 | node_edge_gain | -88.0 | -57.0 | 0.0 | -28.0 | overlap_edge_benefit;possible_duplicate_nets;better_than_whole_image |
| _P1_staging/QA-D302-10(110kV澜河线开关机构箱端子排图(3AP1-FG))#panel_000 | prefer_overlap10 | node_edge_gain | -63.0 | -27.0 | 0.0 | -41.0 | overlap_edge_benefit;overlap_node_benefit;better_than_whole_image |
| _P1_staging/QA-D201-16(#1主变110kV侧开关机构箱端子排图(3AP1-FG))#panel_000 | prefer_overlap10 | node_edge_gain | -50.0 | -47.0 | 0.0 | -30.0 | overlap_edge_benefit;overlap_node_benefit;better_than_whole_image |
| _P3_staging_batch4/发电机保护屏端子图#panel_003 | prefer_overlap10 | node_edge_gain | -47.0 | -83.0 | 0.0 | -12.0 | overlap_edge_benefit;possible_duplicate_nodes;better_than_whole_image |
| _P3_staging_batch1/07(通信回路背面接线图 )#panel_000 | prefer_overlap10 | node_edge_gain | -46.0 | -63.0 | 0.0 | -28.0 | overlap_edge_benefit;overlap_node_benefit;better_than_whole_image |
| _P1_staging/QA-D301-10(110kV南雄线开关机构箱端子排图(3AP1-FG))#panel_000 | prefer_overlap10 | node_edge_net_gain | -38.0 | -65.0 | -1.0 | -53.0 | overlap_edge_benefit;overlap_node_benefit;better_than_whole_image |
| _P3_staging_batch3/2FWK柜左侧端子排电缆接线图(B066-500-2411)wm666.taobao.com#panel_000 | prefer_overlap10 | node_edge_gain | -32.0 | -57.0 | 0.0 | -27.0 | overlap_edge_benefit;overlap_node_benefit;possible_duplicate_nets;better_than_whole_image |
| _P3_staging_batch1/07(通信回路背面接线图)#panel_000 | prefer_overlap10_with_monitoring | node_edge_gain | -22.0 | -24.0 | 0.0 | -1.0 | better_than_whole_image |
| _P3_staging_batch3/#2备用分支在微机保护柜上的端子排(B066-500-0911)wm666.taobao.com#panel_000 | prefer_overlap10 | node_edge_gain | -1.0 | -32.0 | 0.0 | -53.0 | overlap_edge_benefit;overlap_node_benefit;better_than_whole_image |
| _P3_staging_batch1/09(通信回路背面接线图)#panel_000 | needs_tile_review_before_scaling | no_count_gain | 10.0 | 14.0 | -1.0 | 10.0 | possible_duplicate_edges;possible_duplicate_nodes |
| _P3_staging_batch1/QA-D601-03(10kV#1(#2)站变柜端子排图)#panel_000 | overlap10_risk_monitor | no_count_gain | 14.0 | 8.0 | 1.0 | -4.0 | possible_duplicate_nodes |
| _P3_staging_batch3/1FWK柜左侧端子排电缆接线图(B066-500-2409)wm666.taobao.com#panel_000 | overlap10_risk_monitor | no_count_gain | 16.0 | 25.0 | 0.0 | 6.0 | possible_duplicate_nodes |
| _P2_staging/35kV并联电抗器在监控柜上的端子排(B066-500-1904)wm666.taobao.com#panel_000 | prefer_overlap10 | no_count_gain | 109.0 | 56.0 | 1.0 | -18.0 | overlap_edge_benefit;overlap_node_benefit |

## 结论

tile2x2 overlap10 的平均优势不是单个样本造成的。它在 node 与 edge 上均有多数样本改善，且 auto judge 已将 overlap10 固化为下一阶段默认 image-input baseline。少数 duplicate 风险样本保留在 monitor，不阻塞策略。

## 输出

- CSV: `data_index/topology_panel_v1_image_input_delta_analysis.csv`
- Summary: `data_index/topology_panel_v1_image_input_delta_analysis_summary.json`
