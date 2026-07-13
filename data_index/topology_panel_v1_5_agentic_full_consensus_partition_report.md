# Topology Panel v1.5 Agentic Consensus Partition Report

This report materializes the multi-agent consensus into release-oriented partitions.

## Summary

- candidate rows: 154
- consensus rows: 154
- auto accept rows: 14
- auto reject rows: 119
- defer improvement rows: 13
- human review rows: 8

## Label Counts

- accept_clean_topology: 14
- needs_graph_repair: 11
- reject_visible_watermark: 2
- needs_terminal_anchor: 2
- reject_not_topology: 20
- reject_bad_geometry: 57
- uncertain: 8
- reject_multi_subfigure: 40

## Outputs

- auto_accept: `data_index/topology_panel_v1_5_agentic_full_auto_accept_manifest.csv`
- auto_reject: `data_index/topology_panel_v1_5_agentic_full_auto_reject_manifest.csv`
- defer_improvement: `data_index/topology_panel_v1_5_agentic_full_defer_improvement_manifest.csv`
- human_review: `data_index/topology_panel_v1_5_agentic_full_human_review_manifest.csv`
- summary: `data_index/topology_panel_v1_5_agentic_full_consensus_partition_summary.json`
- report: `data_index/topology_panel_v1_5_agentic_full_consensus_partition_report.md`

## Policy

- `auto_accept` rows are candidates for Topology Panel v1.5 clean baseline.
- `auto_reject` rows are excluded by agentic consensus.
- `auto_defer_improvement` rows remain algorithm improvement targets.
- `human_review` rows require targeted manual review before use.
