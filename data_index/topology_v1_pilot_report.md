# Topology Graph v1 Pilot Report

This report compares v0 endpoint topology with v1 pilot intersection splitting.

## Summary

- Pilot rows: 7
- Total intersections: 21087
- Total split events: 31123
- Rows with lower isolated ratio: 7
- Rows with lower net count: 7
- v0 edge total: 7080
- v1 edge total: 37890
- v0 net total: 6164
- v1 net total: 103

## Per Drawing

- _P1_staging/主变压器远方测温及有载调压档位显示接线图(B066-500-1209)wm666.taobao.com: edges 392 -> 1388, nets 350 -> 8, isolated 0.8571 -> 0.0, intersections 834
- _P1_staging/主变及并网线保护屏端子图: edges 919 -> 5977, nets 811 -> 8, isolated 0.8085 -> 0.0, intersections 3400
- _P2_staging/220kV母线保护屏BP-2B端子排(B066-500-0607)wm666.taobao.com: edges 1509 -> 9745, nets 1295 -> 16, isolated 0.8005 -> 0.0, intersections 5479
- _P3_staging_batch3/PLP02-54T线路保护柜端子排接线示意图(B066-500-2704)wm666.taobao.com: edges 715 -> 3573, nets 616 -> 11, isolated 0.8378 -> 0.0, intersections 1980
- _P3_staging_batch3/PLP21-01中断路器保护柜端子排接线示意图(B066-500-2706)wm666.taobao.com: edges 1124 -> 5504, nets 988 -> 17, isolated 0.8514 -> 0.0, intersections 3018
- _P3_staging_batch3/PLP21-01边断路器保护柜端子排接线示意图(B066-500-2705)wm666.taobao.com: edges 1131 -> 5505, nets 986 -> 19, isolated 0.8426 -> 0.0, intersections 3014
- _P3_staging_batch3/攀枝花-青龙山I,II回,攀枝花-施家坪I,II回PLP02-22型保护柜端子排接线示意图(B066-500-2605)wm666.taobao.com: edges 1290 -> 6198, nets 1118 -> 24, isolated 0.8403 -> 0.001, intersections 3362

## Parameters

- endpoint_merge_tolerance: 1.0
- endpoint_tolerance_ratio: 0.0005
- min_segment_length: 0.001
- intersection_epsilon: 1e-09
- max_segments: 300000
