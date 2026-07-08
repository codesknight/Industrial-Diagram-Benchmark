# Topology Panel v1.1 Still-Fragmented Experiment Report

This report summarizes the first v1.1 repair experiment on rows labeled `still_fragmented`.
The experiment varies endpoint merge tolerance only and does not change the formal v1 baseline.

## Summary

- Experiment id: `topology_panel_v1_1_still_fragmented_2026-07-08`
- Input rows: 19
- Variant count: 4
- Experiment rows: 76
- Best candidate rows: 19
- Best improved rows: 0
- Best still-empty rows: 11
- Best overmerge-warning rows: 0

## Input Quality Flags

- no_edges;no_nets: 11
- high_fragmentation: 2
- high_isolated_ratio: 6

## Variant Results

### baseline_0005_cap1
- rows: 19
- candidate improved rows: 0
- still-empty rows: 11
- overmerge-warning rows: 0
- avg new edges: 3212.4211
- avg isolated edge ratio: 0.276384

### merge_0010_cap2
- rows: 19
- candidate improved rows: 0
- still-empty rows: 11
- overmerge-warning rows: 0
- avg new edges: 3190.2105
- avg isolated edge ratio: 0.276389

### merge_0020_cap5
- rows: 19
- candidate improved rows: 0
- still-empty rows: 11
- overmerge-warning rows: 0
- avg new edges: 2993.9474
- avg isolated edge ratio: 0.276363

### merge_0050_cap10
- rows: 19
- candidate improved rows: 0
- still-empty rows: 11
- overmerge-warning rows: 0
- avg new edges: 2673.1053
- avg isolated edge ratio: 0.297479

## Best Candidates

- _P1_staging/05电气主接线#panel_001: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P2_staging/电站、变电所电气及设备13#panel_002: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P2_staging/电站、变电所电气及设备13#panel_003: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P2_staging/电站、变电所电气及设备13#panel_004: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P2_staging/电站、变电所电气及设备13#panel_005: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P2_staging/电站、变电所电气及设备13#panel_007: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P3_staging_batch1/铁路配电所有载调压保护#panel_002: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P3_staging_batch1/高压异步电机保护二次原理图#panel_004: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P3_staging_batch1/高压异步电机保护二次原理图#panel_006: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P3_staging_batch2/发-变组保护测量配置图#panel_002: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P3_staging_batch4/某学校系统图及接线图#panel_000: variant=baseline_0005_cap1, edges 0 -> 0, nets 0 -> 0, isolated 0.0 -> 0.0, improved=False, still_empty=True, overmerge_warning=False
- _P3_staging_batch2/10kV-中置柜进线电气图纸#panel_000: variant=merge_0010_cap2, edges 34885 -> 34877, nets 2901 -> 2901, isolated 0.0078 -> 0.0078, improved=False, still_empty=False, overmerge_warning=False
- _P2_staging/某煤矿变电所电气系统图wm666.taobao.com#panel_000: variant=merge_0020_cap5, edges 26128 -> 22024, nets 3501 -> 3112, isolated 0.0435 -> 0.0431, improved=False, still_empty=False, overmerge_warning=False
- _P3_staging_batch1/高压异步电机保护二次原理图#panel_007: variant=baseline_0005_cap1, edges 5 -> 5, nets 4 -> 4, isolated 0.6 -> 0.6, improved=False, still_empty=False, overmerge_warning=False
- _P3_staging_batch4/某学校系统图及接线图#panel_004: variant=baseline_0005_cap1, edges 5 -> 5, nets 4 -> 4, isolated 0.6 -> 0.6, improved=False, still_empty=False, overmerge_warning=False
- _P1_staging/某铁路牵引变电所主接线图wm666.taobao.com#panel_000: variant=baseline_0005_cap1, edges 4 -> 4, nets 4 -> 4, isolated 1.0 -> 1.0, improved=False, still_empty=False, overmerge_warning=False
- _P3_staging_batch1/高压异步电机保护二次原理图#panel_005: variant=baseline_0005_cap1, edges 4 -> 4, nets 4 -> 4, isolated 1.0 -> 1.0, improved=False, still_empty=False, overmerge_warning=False
- _P3_staging_batch4/某学校系统图及接线图#panel_002: variant=baseline_0005_cap1, edges 3 -> 3, nets 3 -> 3, isolated 1.0 -> 1.0, improved=False, still_empty=False, overmerge_warning=False
- _P3_staging_batch4/某学校系统图及接线图#panel_003: variant=baseline_0005_cap1, edges 2 -> 2, nets 2 -> 2, isolated 1.0 -> 1.0, improved=False, still_empty=False, overmerge_warning=False

## Rules

- This is an improvement experiment only; no row is promoted into the v1 baseline automatically.
- No-edge rows that remain empty likely need geometry-type support, crop review, or target relabeling rather than endpoint tuning.
- Rows marked overmerge_warning require visual review before any future v1.1 promotion.

## Outputs

- input: `data_index/topology_panel_v1_1_still_fragmented_input.csv`
- experiment_manifest: `data_index/topology_panel_v1_1_still_fragmented_experiment_manifest.csv`
- best_candidates: `data_index/topology_panel_v1_1_still_fragmented_best_candidates.csv`
- summary: `data_index/topology_panel_v1_1_still_fragmented_summary.json`
- report: `data_index/topology_panel_v1_1_still_fragmented_report.md`
- local_graph_dir: `outputs/topology_panel_v1_1_still_fragmented`
