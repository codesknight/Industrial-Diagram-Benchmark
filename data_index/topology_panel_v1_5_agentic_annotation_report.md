# Agentic Panel Annotation Report

This run uses multiple vision agents to pre-label Topology Panel v1.5 candidates.

## Summary

- dry run: True
- input rows: 20
- providers: doubao, deepseek, zhipu
- agent output rows: 60
- consensus rows: 20

## Consensus Decisions

- auto_accept: 14
- human_review: 6

## Consensus Labels

- accept_clean_topology: 14
- uncertain: 6

## Outputs

- `data_index/topology_panel_v1_5_agentic_annotation_agent_outputs.csv`
- `data_index/topology_panel_v1_5_agentic_annotation_consensus.csv`
- `data_index/topology_panel_v1_5_agentic_annotation_summary.json`

## Policy

- auto_accept requires at least two agents voting accept_clean_topology, average confidence >= 0.80, and no hard-reject vote.
- auto_reject requires at least two agents voting the same hard-reject label with average confidence >= 0.75.
- all other cases go to human_review or auto_defer_improvement.
