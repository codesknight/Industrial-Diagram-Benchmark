# Agentic Panel Annotation Report

This run uses multiple vision agents to pre-label Topology Panel v1.5 candidates.

## Summary

- dry run: False
- input rows: 2
- providers: zhipu
- agent output rows: 2
- consensus rows: 2

## Consensus Decisions

- human_review: 2

## Consensus Labels

- accept_clean_topology: 2

## Outputs

- `data_index/topology_panel_v1_5_zhipu_glm46v_smoke_agent_outputs.csv`
- `data_index/topology_panel_v1_5_zhipu_glm46v_smoke_consensus.csv`
- `data_index/topology_panel_v1_5_zhipu_glm46v_smoke_summary.json`

## Policy

- auto_accept requires at least two agents voting accept_clean_topology, average confidence >= 0.80, and no hard-reject vote.
- auto_reject requires at least two agents voting the same hard-reject label with average confidence >= 0.75.
- all other cases go to human_review or auto_defer_improvement.
