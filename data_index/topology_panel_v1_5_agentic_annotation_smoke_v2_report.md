# Agentic Panel Annotation Report

This run uses multiple vision agents to pre-label Topology Panel v1.5 candidates.

## Summary

- dry run: False
- input rows: 3
- providers: doubao, deepseek, zhipu
- agent output rows: 9
- consensus rows: 3

## Consensus Decisions

- human_review: 3

## Consensus Labels

- accept_clean_topology: 3

## Outputs

- `data_index/topology_panel_v1_5_agentic_annotation_smoke_v2_agent_outputs.csv`
- `data_index/topology_panel_v1_5_agentic_annotation_smoke_v2_consensus.csv`
- `data_index/topology_panel_v1_5_agentic_annotation_smoke_v2_summary.json`

## Policy

- auto_accept requires at least two agents voting accept_clean_topology, average confidence >= 0.80, and no hard-reject vote.
- auto_reject requires at least two agents voting the same hard-reject label with average confidence >= 0.75.
- all other cases go to human_review or auto_defer_improvement.
