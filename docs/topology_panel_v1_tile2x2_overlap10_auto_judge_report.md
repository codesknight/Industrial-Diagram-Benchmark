# Topology Panel v1 Tile2x2 Overlap10 Auto-Judge Report

日期：2026-07-10

## 结论

本轮不再等待人工逐张确认，直接信任自动 Judge 标签。根据 metric delta 与自动标签，`tile2x2 + overlap10` 被固化为下一阶段默认 image-input baseline。

## 全局依据

- 10 of 14 panels have overlap_edge_benefit.
- 10 of 14 panels are better_than_whole_image.
- Only 1 panel has possible_duplicate_edges.
- Overlap10 has best node/edge MAE among current Doubao count-level experiments.

## Decision Counts

- prefer_overlap10: 10
- overlap10_risk_monitor: 2
- prefer_overlap10_with_monitoring: 1
- needs_tile_review_before_scaling: 1

## Next Action Counts

- use_overlap10_for_next_benchmark: 8
- monitor_aggregation_rule: 4
- no_extra_tile_complexity: 1
- inspect_boundary_duplicates: 1

## Policy

- 默认后续 image-input baseline 使用 `doubao_prompt_v3_tile2x2_overlap10`。
- 带 `possible_duplicate_edges` 的样本不阻塞策略，但进入后续边界重复风险观察列表。
- 带 `possible_duplicate_nodes` / `possible_duplicate_nets` 的样本保留在 risk monitor，不单独触发 3x3。
- 下一步优先做 per-sample delta 分析或 hybrid pipeline，而不是直接全量 3x3。

## Outputs

- Auto-judge manifest: `data_index/topology_panel_v1_tile2x2_overlap10_auto_judge_manifest.csv`
- Summary: `data_index/topology_panel_v1_tile2x2_overlap10_auto_judge_summary.json`
- Source review HTML: `data_index/topology_panel_v1_tile2x2_overlap10_review.html`
