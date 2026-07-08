# Experiment Records

## 2026-07-08 Topology Panel v1 Release Manifest

- Built formal Topology Panel v1 release manifests from `data_index/topology_panel_v1_sample_policy_reviewed.csv`.
- Applied the current policy that multi-subfigure panels are badcases, not split-v2 candidates.
- Release id: `topology_panel_v1_2026-07-08`.
- Clean baseline rows: 14.
- Excluded badcase rows: 125.
- Improvement target rows: 31.
- Unreviewed rows: 1.
- Clean baseline asset check: 0 missing panel PNG rows, 0 missing topology v1 JSON rows.
- Main outputs:
  - `data_index/topology_panel_v1_release_manifest.csv`
  - `data_index/topology_panel_v1_release_train.csv`
  - `data_index/topology_panel_v1_release_val.csv`
  - `data_index/topology_panel_v1_release_test.csv`
  - `data_index/topology_panel_v1_release_excluded_manifest.csv`
  - `data_index/topology_panel_v1_release_improvement_manifest.csv`
  - `data_index/topology_panel_v1_release_summary.json`
  - `data_index/topology_panel_v1_release_report.md`

## 2026-07-08 Topology Panel v1 Clean Baseline Review HTML

- Built a compact HTML visual review sheet for the 14-row clean baseline release.
- Source manifest: `data_index/topology_panel_v1_release_manifest.csv`.
- Review HTML: `data_index/topology_panel_v1_baseline_review.html`.
- Review manifest: `data_index/topology_panel_v1_baseline_review_manifest.csv`.
- Summary: `data_index/topology_panel_v1_baseline_review_summary.json`.
- The page shows the panel PNG, a lightweight topology SVG preview generated from the v1 graph JSON, key graph metrics, model review notes, and a CSV export for final baseline confirmation labels.
- Baseline review split counts: train 11, val 1, test 2.
- Baseline review phase counts: P1 4, P2 1, P3 9.

## 2026-07-08 Topology Panel v1 Final Baseline

- Applied final clean-baseline review confirmation after manual visual check.
- No exported `topology_panel_v1_baseline_review_labels.csv` was found in `data_index`, so the run used the user's confirmation that all reviewed baseline samples were valid.
- Final baseline rows: 14.
- Needs recheck rows: 0.
- Removed rows: 0.
- Final baseline split counts: train 11, val 1, test 2.
- Final baseline phase counts: P1 4, P2 1, P3 9.
- Main outputs:
  - `data_index/topology_panel_v1_final_baseline_manifest.csv`
  - `data_index/topology_panel_v1_baseline_reviewed.csv`
  - `data_index/topology_panel_v1_final_baseline_summary.json`
  - `data_index/topology_panel_v1_final_baseline_report.md`

## 2026-07-08 Topology Graph v1 Evaluation Protocol

- Added the first formal evaluation protocol for panel-level Topology Graph v1.
- Protocol document: `docs/topology_graph_eval_protocol_v1.md`.
- Formal score manifest: `data_index/topology_panel_v1_final_baseline_manifest.csv`.
- Baseline size fixed for this release: 14 rows.
- The protocol excludes multi-subfigure badcases, bad geometry, not-topology targets, unreviewed rows, and v1.1 improvement targets from the formal v1 score.
- Primary metrics defined: graph valid rate, node count error, edge count error, net count error, isolated edge ratio, largest net edge ratio, and human accept rate.
- The document also records v1 non-goals and the recommended v1.1 improvement order.

## 2026-07-08 Topology Panel v1 Benchmark JSONL Package

- Built the first machine-readable JSONL package for the final Topology Panel v1 baseline.
- Source manifest: `data_index/topology_panel_v1_final_baseline_manifest.csv`.
- Output JSONL: `data_index/topology_panel_v1_benchmark_manifest.jsonl`.
- Summary: `data_index/topology_panel_v1_benchmark_summary.json`.
- Report: `data_index/topology_panel_v1_benchmark_report.md`.
- Benchmark id: `topology_panel_v1_benchmark_2026-07-08`.
- Records: 14.
- Missing images: 0.
- Missing topology graphs: 0.
- Split counts: train 11, val 1, test 2.
- Phase counts: P1 4, P2 1, P3 9.

## 2026-07-08 Topology Panel v1 Evaluation Script

- Added the first benchmark evaluation script for Topology Panel v1.
- Script: `benchmark/topology/evaluate_topology_graph_v1.py`.
- Input manifest: `data_index/topology_panel_v1_benchmark_manifest.jsonl`.
- Output summary: `data_index/topology_panel_v1_eval_summary.json`.
- Output report: `data_index/topology_panel_v1_eval_report.md`.
- Default mode: `reference_as_prediction`, used to validate the evaluation pipeline and reference graph structure.
- Evaluated rows: 14.
- Reference graph valid rate: 1.0.
- Prediction graph valid rate in default mode: 1.0.
- Node, edge, and net count MAE/MRE are all 0.0 in default mode.

## 2026-07-08 Topology Panel v1.1 Still-Fragmented Experiment

- Added v1.1 planning document: `docs/topology_panel_v1_1_plan.md`.
- Added first still-fragmented experiment script: `scripts/run_topology_panel_v1_1_still_fragmented_experiment.py`.
- Input rows: 19 from `data_index/topology_panel_v1_release_improvement_manifest.csv`.
- Variants tested: `baseline_0005_cap1`, `merge_0010_cap2`, `merge_0020_cap5`, `merge_0050_cap10`.
- Experiment rows: 76.
- Best improved rows: 0.
- Best still-empty rows: 11.
- Best overmerge-warning rows: 0.
- Main interpretation: endpoint tolerance tuning alone does not repair this bucket; next v1.1 step should diagnose no-line geometry, crop/bbox issues, non-topology targets, panel-split remnants, true fragmentation, and terminal-anchor cases.
- Main outputs:
  - `data_index/topology_panel_v1_1_still_fragmented_input.csv`
  - `data_index/topology_panel_v1_1_still_fragmented_experiment_manifest.csv`
  - `data_index/topology_panel_v1_1_still_fragmented_best_candidates.csv`
  - `data_index/topology_panel_v1_1_still_fragmented_summary.json`
  - `data_index/topology_panel_v1_1_still_fragmented_report.md`
