# Topology Panel v1 Anomaly Report

This report lists quick anomaly buckets from `topology_panel_v1_manifest.csv`.

## Summary

- Panel rows: 2069
- Normal rows: 1348
- Anomaly rows: 721
- Max edge count: 219846
- Max net count: 17100
- Max intersection count: 336142
- Max isolated edge ratio: 1.0

## Severity Counts

- critical: 9
- high: 42
- medium: 600
- low: 70

## Anomaly Type Counts

- truncated_max_segments: 2
- error: 7
- no_edges_or_no_nets: 42
- high_fragmentation: 517
- high_isolated_ratio: 83
- dominant_component: 70

## Status Counts

- ok: 2060
- error: 7
- truncated_max_segments: 2

## Critical and High Samples

- _P2_staging/变电所修#panel_000: type=truncated_max_segments, status=truncated_max_segments, edges=219846, nets=223, flags=none
- _P2_staging/变电所修__479#panel_000: type=truncated_max_segments, status=truncated_max_segments, edges=219846, nets=223, flags=none
- _P2_staging/SGT-变电所设备布置平面图#panel_000: type=error, status=error, edges=0, nets=0, flags=error
- _P2_staging/体育场变电所电气平面图wm666.taobao.com#panel_000: type=error, status=error, edges=0, nets=0, flags=error
- _P2_staging/某降压变电站设计#panel_000: type=error, status=error, edges=0, nets=0, flags=error
- _P2_staging/某降压变电站设计wm666.taobao.com#panel_000: type=error, status=error, edges=0, nets=0, flags=error
- _P3_staging_batch3/泉州涂门街中段保护与改建电气设计#panel_000: type=error, status=error, edges=0, nets=0, flags=error
- _P3_staging_batch3/道窖500KVA变配电工程wm666.taobao.com#panel_000: type=error, status=error, edges=0, nets=0, flags=error
- _P3_staging_batch3/道窖500KVA变配电工程wm666.taobao.com__29#panel_000: type=error, status=error, edges=0, nets=0, flags=error
- _P1_staging/05电气主接线#panel_001: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/35KV变电所设计#panel_001: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所、配电所 (gb4728_11_1.3-1)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所、配电所 (gb4728_11_1.3-2)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所全套图纸wm666.taobao.com#panel_001: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所全套图纸wm666.taobao.com#panel_003: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所全套图纸wm666.taobao.com#panel_004: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所全套图纸wm666.taobao.com#panel_005: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所全套图纸wm666.taobao.com#panel_006: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所全套图纸wm666.taobao.com#panel_008: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所（示出改变电压） (gb4728_11_2.9-1)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/变电所（示出改变电压） (gb4728_11_2.9-2)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/杆上变电站 (gb4728_11_2.11-1)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/杆上变电站 (gb4728_11_2.11-2)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/某厂房变电所平面#panel_001: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/某厂房变电所平面wm666.taobao.com#panel_001: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/电站、变电所电气及设备04#panel_004: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/电站、变电所电气及设备13#panel_001: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/电站、变电所电气及设备13#panel_002: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/电站、变电所电气及设备13#panel_003: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/电站、变电所电气及设备13#panel_004: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/电站、变电所电气及设备13#panel_005: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/电站、变电所电气及设备13#panel_007: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/移动变电所 (gb4728-11_2.12-2)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/移动变电所 (gb4728_11_2.12-1)#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P2_staging/运行的移动变电站#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch1/铁路配电所有载调压保护#panel_002: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch1/铁路配电所有载调压保护#panel_003: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch1/高压异步电机保护二次原理图#panel_004: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch1/高压异步电机保护二次原理图#panel_006: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch2/发-变组保护测量配置图#panel_002: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch2/开关柜底座及基础图#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10KV配网设计块图#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10KV配网设计块图#panel_001: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10KV配网设计块图#panel_002: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10KV配网设计块图#panel_003: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10KV配网设计块图#panel_004: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10KV配网设计块图#panel_005: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10kv系统单线图#panel_004: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/10kv系统单线图#panel_005: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/DXN8B-T接线图#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets
- _P3_staging_batch4/某学校系统图及接线图#panel_000: type=no_edges_or_no_nets, status=ok, edges=0, nets=0, flags=no_edges;no_nets

## Rules

- status=error and status=truncated_max_segments are critical anomalies
- no_edges/no_nets rows require topology-target review or unsupported-geometry inspection
- high_fragmentation, high_isolated_ratio, and dominant_component are risk samples for the next HTML review
