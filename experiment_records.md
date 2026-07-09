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

## 2026-07-08 Topology Panel v1.1 Still-Fragmented Diagnostic Review

- Added diagnostic HTML/CSV for the 19 `still_fragmented` v1.1 rows.
- Script: `scripts/build_topology_panel_v1_1_still_fragmented_diagnostic_html.py`.
- Diagnostic CSV: `data_index/topology_panel_v1_1_still_fragmented_diagnostic.csv`.
- Diagnostic HTML: `data_index/topology_panel_v1_1_still_fragmented_diagnostic.html`.
- Diagnostic summary: `data_index/topology_panel_v1_1_still_fragmented_diagnostic_summary.json`.
- Suggested diagnostic label counts:
  - `no_line_geometry`: 1
  - `non_topology_target`: 4
  - `needs_panel_split_badcase`: 7
  - `true_fragmentation`: 5
  - `terminal_anchor_needed`: 2
- HTML supports manual override and exports `topology_panel_v1_1_still_fragmented_diagnostic_labels.csv`.

## 2026-07-08 Topology Panel v1.1 Abandoned Policy

- Applied the decision to abandon all 19 v1.1 `still_fragmented` diagnostic rows.
- Script: `scripts/apply_topology_panel_v1_1_abandoned_policy.py`.
- Abandoned manifest: `data_index/topology_panel_v1_1_abandoned_manifest.csv`.
- Active improvement manifest: `data_index/topology_panel_v1_1_active_improvement_manifest.csv`.
- Summary: `data_index/topology_panel_v1_1_abandoned_policy_summary.json`.
- Report: `data_index/topology_panel_v1_1_abandoned_policy_report.md`.
- Input improvement rows: 31.
- Abandoned rows: 19.
- Active improvement rows: 12.
- Active next routes: terminal anchor 3, over-connected repair 9.
- Formal Topology Panel v1 baseline remains unchanged.

## 2026-07-08 Topology Panel v1.1 Active Improvement Review

- Built the active improvement HTML review entrypoint for the 12 remaining v1.1 candidates.
- Script: `scripts/build_topology_panel_v1_1_active_improvement_review_html.py`.
- Review HTML: `data_index/topology_panel_v1_1_active_improvement_review.html`.
- Review manifest: `data_index/topology_panel_v1_1_active_improvement_review_manifest.csv`.
- Summary: `data_index/topology_panel_v1_1_active_improvement_review_summary.json`.
- Rows: 12.
- Routes: terminal anchor 3, over-connected repair 9.
- Suggested labels: `keep_terminal_anchor` 3, `keep_over_connected` 9.
- HTML exports `topology_panel_v1_1_active_improvement_review_labels.csv`.

## 2026-07-09 Topology Panel v1.1 Active Improvement Labels Applied

- Applied labels exported from `data_index/topology_panel_v1_1_active_improvement_review.html`.
- Labels CSV: `data_index/topology_panel_v1_1_active_improvement_review_labels.csv`.
- Script: `scripts/apply_topology_panel_v1_1_active_improvement_review_labels.py`.
- Reviewed rows: 12.
- Kept rows: 12.
- Keep terminal-anchor rows: 3.
- Keep over-connected rows: 9.
- Abandoned rows: 0.
- Deferred rows: 0.
- Main outputs:
  - `data_index/topology_panel_v1_1_active_improvement_reviewed.csv`
  - `data_index/topology_panel_v1_1_keep_improvement_manifest.csv`
  - `data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv`
  - `data_index/topology_panel_v1_1_keep_over_connected_manifest.csv`
  - `data_index/topology_panel_v1_1_active_improvement_review_result_summary.json`
  - `data_index/topology_panel_v1_1_active_improvement_review_result_report.md`

## 2026-07-09 Topology Panel v1 Release Status Document

- Added Chinese release status document: `docs/topology_panel_v1_release_status.md`.
- Purpose: freeze the current project state before README/HuggingFace release documentation work.
- Formal v1 baseline remains `data_index/topology_panel_v1_final_baseline_manifest.csv`.
- Formal v1 baseline rows: 14.
- Split counts: train 11, val 1, test 2.
- Benchmark JSONL: `data_index/topology_panel_v1_benchmark_manifest.jsonl`.
- Evaluation protocol: `docs/topology_graph_eval_protocol_v1.md`.
- Evaluation script: `benchmark/topology/evaluate_topology_graph_v1.py`.
- v1 excluded badcase rows: 125.
- v1.1 abandoned `still_fragmented` rows: 19.
- v1.1 active kept improvement rows: 12.
- v1.1 active routes: terminal anchor 3, over-connected repair 9.
- Main recommendation: finish README/HuggingFace release documentation before continuing topology algorithm repair.

## 2026-07-09 README Topology Panel v1 Update

- Rewrote `README.md` as the main public entrypoint for the current project state.
- Clarified the official `Topology Panel v1` boundary: 14 clean baseline rows only.
- Added quick benchmark usage for `benchmark/topology/evaluate_topology_graph_v1.py`.
- Added benchmark JSONL, protocol, summary, report, and output paths.
- Added data version boundaries for clean baseline, excluded badcases, improvement targets, and unreviewed rows.
- Clarified that v1.1 kept improvement candidates remain outside the formal v1 baseline.
- Preserved the broader data processing command sequence after the release-facing project summary.

## 2026-07-09 Hugging Face Dataset Card and Release File List

- Updated Hugging Face dataset card draft: `docs/huggingface_dataset_card.md`.
- Added release upload checklist: `data_index/HF_RELEASE_FILES.md`.
- Synchronized the public version boundary from `README.md`:
  - `Topology Panel v1`: 14 clean baseline rows only.
  - `excluded_badcase`: 125 rows.
  - original `improvement_target`: 31 rows.
  - v1.1 kept candidates: 12 rows.
  - abandoned `still_fragmented`: 19 rows.
- Added recommended HF release files for benchmark JSONL, final baseline manifest, summaries/reports, protocol docs, and optional boundary manifests.
- Clarified that review HTML files are optional review artifacts and are not model evaluation inputs.

## 2026-07-09 Hugging Face Release Package Script

- Added release packaging script: `scripts/prepare_hf_release_package.py`.
- Default output directory: `outputs/hf_release_topology_panel_v1/`.
- The script copies the dataset card to package-root `README.md`.
- The script copies required benchmark files, protocol docs, recommended release manifests, and optional boundary manifests.
- Review HTML artifacts are excluded by default and can be included with `--include-review-html`.
- The script writes package metadata inside the output package:
  - `data_index/hf_release_package_manifest.csv`
  - `data_index/hf_release_package_summary.json`
  - `data_index/hf_release_package_report.md`
- Updated `data_index/HF_RELEASE_FILES.md` with the packaging command.

## 2026-07-09 Hugging Face Upload Attempt and Helper Script

- Prepared local package in `outputs/hf_release_topology_panel_v1/`.
- Package check: 23 copied files, 0 missing files.
- Direct upload was blocked because no Hugging Face token or cached login was found on this machine.
- Added upload helper script: `scripts/upload_hf_release_package.py`.
- The script uploads `outputs/hf_release_topology_panel_v1/` to `yanhongliu/Industrial-Diagram-Benchmark`.
- The script supports `.env` token keys such as `HF_TOKEN` and supports cached `hf auth login`.
- Added upload instructions and dry-run command to `data_index/HF_RELEASE_FILES.md`.
