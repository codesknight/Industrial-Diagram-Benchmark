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

## 2026-07-09 Hugging Face Topology Panel v1 Upload Completed

- Detected `HF_TOKEN` in `.env` without printing the token value.
- Regenerated local release package with `python scripts/prepare_hf_release_package.py`.
- Upload dry-run confirmed 26 files in `outputs/hf_release_topology_panel_v1/`.
- Uploaded the package with `python scripts/upload_hf_release_package.py`.
- Target dataset: `yanhongliu/Industrial-Diagram-Benchmark`.
- Upload result: 26 files uploaded.
- Remote verification confirmed these key files:
  - `README.md`
  - `data_index/topology_panel_v1_benchmark_manifest.jsonl`
  - `data_index/hf_release_package_summary.json`
  - `docs/topology_graph_eval_protocol_v1.md`
- Remote dataset file count after upload check: 27.

## 2026-07-09 Topology Panel v1 Release Note

- Added formal release note: `docs/topology_panel_v1_release_note.md`.
- The release note summarizes the v1 clean baseline, data version boundary, benchmark files, evaluation command, Hugging Face upload status, known limitations, and next-step recommendations.
- Official release name: `Topology Panel v1 clean baseline`.
- Official baseline rows: 14.
- Hugging Face dataset: `yanhongliu/Industrial-Diagram-Benchmark`.
- The note records that 26 files were uploaded and key remote files were verified.

## 2026-07-09 Topology Panel v1 Prediction Template

- Added template builder script: `scripts/build_topology_panel_v1_prediction_template.py`.
- Generated prediction template JSONL: `data_index/topology_panel_v1_prediction_template.jsonl`.
- Generated template summary: `data_index/topology_panel_v1_prediction_template_summary.json`.
- Generated template report: `data_index/topology_panel_v1_prediction_template_report.md`.
- Template rows: 14, aligned with `data_index/topology_panel_v1_benchmark_manifest.jsonl`.
- The template fixes `panel_id`, split, phase, image path, reference summary, model metadata fields, and prediction placeholders.
- Accepted prediction modes: inline `prediction`, `prediction_json_path`, or inline `graph` for evaluator compatibility.

## 2026-07-09 Topology Panel v1 Per-Sample Evaluation CSVs

- Extended evaluator: `benchmark/topology/evaluate_topology_graph_v1.py`.
- Added default per-sample details CSV: `data_index/topology_panel_v1_eval_details.csv`.
- Added default error-only CSV: `data_index/topology_panel_v1_eval_errors.csv`.
- Added CLI options:
  - `--details-csv`
  - `--errors-csv`
- Default reference-as-prediction validation:
  - evaluated rows: 14
  - details rows: 14
  - error rows: 0
- External prediction smoke test with the unfilled prediction template:
  - prediction mode: external_prediction
  - details rows: 14
  - error rows: 14
  - prediction graph valid rate: 0.0
- Fixed evaluator output path handling for relative custom output paths such as `outputs/template_eval_summary.json`.

## 2026-07-09 Topology Panel v1 Oracle-Minus Baseline

- Added oracle-minus baseline script: `scripts/build_topology_panel_v1_oracle_minus_baseline.py`.
- Generated predictions: `data_index/topology_panel_v1_oracle_minus_predictions.jsonl`.
- Generated oracle-minus prediction graphs under `outputs/topology_panel_v1_oracle_minus/`.
- The prediction JSONL is self-contained with inline `prediction` graphs and also keeps `prediction_json_path` for local debugging.
- Generated baseline summary/report:
  - `data_index/topology_panel_v1_oracle_minus_summary.json`
  - `data_index/topology_panel_v1_oracle_minus_report.md`
- Ran evaluator on oracle-minus predictions and generated:
  - `data_index/topology_panel_v1_oracle_minus_eval_summary.json`
  - `data_index/topology_panel_v1_oracle_minus_eval_report.md`
  - `data_index/topology_panel_v1_oracle_minus_eval_details.csv`
  - `data_index/topology_panel_v1_oracle_minus_eval_errors.csv`
- Oracle-minus prediction rows: 14.
- Prediction graph valid rate: 1.0.
- Rows with node error: 14.
- Rows with edge error: 14.
- Rows with net error: 5.
- Count error summary: node MAE 7.5, edge MAE 57.857143, net MAE 0.571429.
- Interpretation: the evaluator can detect topology count errors even when predicted graph schemas remain valid.

## 2026-07-09 Oracle-Minus Sanity Baseline Documentation

- Updated evaluation protocol: `docs/topology_graph_eval_protocol_v1.md`.
- Updated release note: `docs/topology_panel_v1_release_note.md`.
- Documented two official sanity baselines:
  - `reference_as_prediction`: package/evaluator consistency check.
  - `oracle_minus`: evaluator sensitivity check with valid but intentionally perturbed prediction graphs.
- Clarified that oracle-minus is not a model-performance baseline.
- Added oracle-minus commands, expected metrics, and output files to the protocol and release note.

## 2026-07-09 Topology Panel v1 Prediction Schema Diagnostics

- Enhanced evaluator schema diagnostics in `benchmark/topology/evaluate_topology_graph_v1.py`.
- Added prediction source diagnostics for inline `prediction`, inline `graph`, `prediction_json_path`, and missing prediction graph cases.
- Added stricter graph schema checks:
  - `schema_missing`, `schema_not_string`, `schema_unexpected_*`
  - `status_missing`, `status_not_string`, `status_*`
  - node id, point, and degree diagnostics
  - edge id, source/target, points, length, and missing reference diagnostics
  - net id, bbox, and count diagnostics
- Added `prediction_error_category_counts` and `prediction_invalid_reason_counts` to evaluation summaries.
- Added per-row CSV columns for `prediction_source`, `load_errors`, `prediction_source_errors`, `schema_errors`, `status_errors`, `nodes_errors`, `edges_errors`, `nets_errors`, and `other_errors`.
- Updated prediction valid-rate denominator so missing prediction rows count against the full evaluated row count.
- Validation:
  - default reference-as-prediction still has 14 details rows and 0 error rows.
  - oracle-minus remains prediction-valid with 14 error rows caused by count differences, not schema errors.
  - unfilled prediction template yields 14 invalid predictions with explicit source/schema/status/node/edge/net error categories.

## 2026-07-09 Topology Panel v1 Model Prediction Adapter

- Added model prediction adapter: `scripts/run_topology_panel_v1_model_prediction_adapter.py`.
- Added dependencies to `requirements.txt`: `openai`, `Pillow`, `python-dotenv`.
- The adapter supports OpenAI-compatible `doubao` and `deepseek` providers.
- The adapter reads `DOUBAO_API_KEY`, `DOUBAO_VISION_MODEL`, `DEEPSEEK_API_KEY`, and `DEEPSEEK_VISION_MODEL` from `.env` without printing secrets.
- The adapter asks a vision model for topology counts or an optional full topology graph.
- If the model returns counts only, the adapter creates a schema-valid synthetic topology graph with stats set to the model counts.
- Doubao smoke test:
  - command: `python scripts/run_topology_panel_v1_model_prediction_adapter.py --provider doubao --limit 1 --keep-raw-response`
  - predictions: `data_index/topology_panel_v1_doubao_model_predictions.jsonl`
  - adapter mode: `synthetic_from_counts`
  - adapter errors: none 1
  - evaluator prediction rows: 1
  - evaluator prediction valid rate: 0.071429
- DeepSeek smoke test:
  - command: `python scripts/run_topology_panel_v1_model_prediction_adapter.py --provider deepseek --limit 1 --keep-raw-response`
  - predictions: `data_index/topology_panel_v1_deepseek_model_predictions.jsonl`
  - adapter mode: `synthetic_from_counts`
  - adapter errors: model_error 1
  - model error indicates the configured DeepSeek endpoint expected text-only messages and rejected `image_url` input.
  - evaluator prediction valid rate: 0.0
- Interpretation: Doubao is currently usable as the first real vision prediction path; DeepSeek requires a vision-capable endpoint or different request format before it can be used for image-based topology prediction.

## 2026-07-09 Doubao Full Topology Panel v1 Baseline Evaluation

- Ran Doubao on the full 14-row Topology Panel v1 baseline.
- Model: `doubao-seed-2-0-pro-260215`.
- Command used image downscaling controls: `--max-image-side 512 --max-image-pixels 250000 --timeout 45 --retries 1`.
- Prediction rows: 14 / 14.
- Adapter mode counts: `synthetic_from_counts` 14.
- Adapter error counts: `none` 14.
- Evaluator prediction graph valid rate: 0.357143.
- Count error summary: node MAE 500.857143, edge MAE 828.357143, net MAE 3.571429.
- Prediction invalid rows: 9, caused by status diagnostics (`status_uncertain` 5, `status_unreadable` 4).
- Interpretation: Doubao end-to-end model access is now working, but this first run is a count-only synthetic graph baseline rather than a full topology reconstruction baseline.
- Main outputs:
  - `docs/topology_panel_v1_doubao_eval_report.md`
  - `data_index/topology_panel_v1_doubao_model_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_model_predictions_summary.json`
  - `data_index/topology_panel_v1_doubao_model_predictions_report.md`
  - `data_index/topology_panel_v1_doubao_model_predictions_eval_summary.json`
  - `data_index/topology_panel_v1_doubao_model_predictions_eval_report.md`
  - `data_index/topology_panel_v1_doubao_model_predictions_eval_details.csv`
  - `data_index/topology_panel_v1_doubao_model_predictions_eval_errors.csv`

## 2026-07-09 Doubao Prompt v2 Full Baseline Comparison

- Added prompt version support to `scripts/run_topology_panel_v1_model_prediction_adapter.py`.
- Prompt v2 narrows the task to count-level topology prediction and discourages unnecessary `unreadable` / `uncertain` status for readable industrial diagrams.
- Ran Doubao prompt v2 on all 14 Topology Panel v1 baseline rows.
- Command used: `--provider doubao --prompt-version v2 --max-image-side 512 --max-image-pixels 250000 --timeout 45 --retries 1`.
- Prediction rows: 14 / 14.
- Adapter mode counts: `synthetic_from_counts` 14.
- Adapter error counts: `none` 14.
- v2 prediction graph valid rate: 1.0, improved from v1 0.357143.
- v2 invalid prediction rows: 0, improved from v1 9.
- Count error comparison:
  - node MAE: v1 500.857143, v2 409.285714.
  - edge MAE: v1 828.357143, v2 737.357143.
  - net MAE: v1 3.571429, v2 16.357143.
- Interpretation: prompt v2 improves readability/status behavior and node/edge count estimates, but overestimates `net_count`; prompt v3 should focus on stricter network/component definitions.
- Main outputs:
  - `docs/topology_panel_v1_doubao_prompt_v2_comparison_report.md`
  - `data_index/topology_panel_v1_doubao_v2_model_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_v2_model_predictions_summary.json`
  - `data_index/topology_panel_v1_doubao_v2_model_predictions_report.md`
  - `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_summary.json`
  - `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_report.md`
  - `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_details.csv`
  - `data_index/topology_panel_v1_doubao_v2_model_predictions_eval_errors.csv`

## 2026-07-10 Topology Panel v1 Model Leaderboard

- Added a reproducible leaderboard builder: `scripts/build_topology_panel_v1_model_leaderboard.py`.
- Generated the first model experiment leaderboard for Topology Panel v1.
- Leaderboard rows: 5.
- Comparable model rows: 2 (`doubao_v1`, `doubao_prompt_v2`).
- Sanity/smoke rows: `reference_as_prediction`, `oracle_minus`, `deepseek_smoke`.
- Current comparable bests:
  - prediction valid rate: `doubao_prompt_v2` = 1.0.
  - node MAE: `doubao_prompt_v2` = 409.285714.
  - edge MAE: `doubao_prompt_v2` = 737.357143.
  - net MAE: `doubao_v1` = 3.571429.
- Interpretation: Doubao prompt v2 is better for valid/status behavior and node/edge count estimates, while Doubao v1 is still better for net_count. The next prompt iteration should focus on stricter connected-component / network-count definitions.
- Main outputs:
  - `data_index/topology_panel_v1_model_leaderboard.csv`
  - `data_index/topology_panel_v1_model_leaderboard_summary.json`
  - `docs/topology_panel_v1_model_leaderboard.md`

## 2026-07-10 Doubao Prompt v3 Net Count Fix

- Added `--prompt-version v3` to `scripts/run_topology_panel_v1_model_prediction_adapter.py`.
- Prompt v3 keeps the v2 readable-diagram status policy and adds strict `net_count = connected component count` rules.
- Ran Doubao prompt v3 on all 14 Topology Panel v1 baseline rows with the same image settings as v2: `--max-image-side 512 --max-image-pixels 250000 --timeout 45 --retries 1`.
- Prediction rows: 14 / 14.
- Adapter mode counts: `synthetic_from_counts` 14.
- Adapter error counts: `none` 14.
- v3 prediction graph valid rate: 1.0.
- v3 invalid prediction rows: 0.
- Count error comparison:
  - node MAE: v1 500.857143, v2 409.285714, v3 394.642857.
  - edge MAE: v1 828.357143, v2 737.357143, v3 715.642857.
  - net MAE: v1 3.571429, v2 16.357143, v3 0.857143.
- Interpretation: prompt v3 fixes the v2 net_count overestimation while preserving valid/status gains and slightly improving node/edge count estimates.
- Main outputs:
  - `docs/topology_panel_v1_doubao_prompt_v3_comparison_report.md`
  - `data_index/topology_panel_v1_doubao_v3_model_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_v3_model_predictions_summary.json`
  - `data_index/topology_panel_v1_doubao_v3_model_predictions_report.md`
  - `data_index/topology_panel_v1_doubao_v3_model_predictions_eval_summary.json`
  - `data_index/topology_panel_v1_doubao_v3_model_predictions_eval_report.md`
  - `data_index/topology_panel_v1_doubao_v3_model_predictions_eval_details.csv`
  - `data_index/topology_panel_v1_doubao_v3_model_predictions_eval_errors.csv`
  - updated `data_index/topology_panel_v1_model_leaderboard.csv`

## 2026-07-10 Doubao Image Input v2 Whole-Image Resolution Test

- Fixed prompt version at `v3` and compared whole-image input resolution.
- Baseline setting: `--max-image-side 512 --max-image-pixels 250000`.
- New setting: `--max-image-side 1024 --max-image-pixels 1000000`.
- Ran Doubao v3@1024 on all 14 Topology Panel v1 baseline rows.
- Prediction rows: 14 / 14.
- Adapter mode counts: `synthetic_from_counts` 14.
- Adapter error counts: `none` 14.
- v3@1024 prediction graph valid rate: 1.0.
- v3@1024 invalid prediction rows: 0.
- Count error comparison:
  - node MAE: v3@512 394.642857, v3@1024 399.571429.
  - edge MAE: v3@512 715.642857, v3@1024 724.285714.
  - net MAE: v3@512 0.857143, v3@1024 0.928571.
- Interpretation: larger whole-image input did not improve node/edge/net MAE. The next image-input experiment should use local cropping or tiled inputs rather than simply increasing full-image resolution.
- Main outputs:
  - `docs/topology_panel_v1_doubao_image_input_v2_report.md`
  - `data_index/topology_panel_v1_doubao_v3_1024_model_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_v3_1024_model_predictions_summary.json`
  - `data_index/topology_panel_v1_doubao_v3_1024_model_predictions_report.md`
  - `data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_summary.json`
  - `data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_report.md`
  - `data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_details.csv`
  - `data_index/topology_panel_v1_doubao_v3_1024_model_predictions_eval_errors.csv`
  - updated `data_index/topology_panel_v1_model_leaderboard.csv`

## 2026-07-10 Doubao Tile2x2 Image Input Experiment

- Added tile benchmark builder: `scripts/build_topology_panel_v1_tile_benchmark.py`.
- Added tile prediction aggregator: `scripts/aggregate_topology_panel_v1_tile_predictions.py`.
- Generated 2x2 tile benchmark from the 14-row Topology Panel v1 baseline.
- Tile records: 56.
- Ran Doubao prompt v3 on all 56 tile images.
- Tile adapter mode counts: `synthetic_from_counts` 56.
- Tile adapter error counts: `none` 56.
- Aggregated tile predictions back to 14 panel-level predictions.
- Aggregation rule: node=sum, edge=sum, net=mean_clamped3.
- Panel-level prediction graph valid rate: 1.0.
- Count error comparison:
  - node MAE: v3@512 394.642857, v3@1024 399.571429, tile2x2 378.285714.
  - edge MAE: v3@512 715.642857, v3@1024 724.285714, tile2x2 713.5.
  - net MAE: v3@512 0.857143, v3@1024 0.928571, tile2x2 0.714286.
- Interpretation: tile2x2 input improves node/edge/net MAE over whole-image v3@512 and v3@1024. The next image-input experiment should test overlap tiles or tile review to reduce edge-boundary truncation.
- Main outputs:
  - `docs/topology_panel_v1_doubao_tile2x2_input_report.md`
  - `data_index/topology_panel_v1_tile2x2_benchmark_manifest.jsonl`
  - `data_index/topology_panel_v1_tile2x2_benchmark_manifest.csv`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_tile_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_eval_summary.json`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_eval_details.csv`
  - updated `data_index/topology_panel_v1_model_leaderboard.csv`

## 2026-07-10 Doubao Tile2x2 Overlap10 Image Input Experiment

- Generated a 2x2 tile benchmark with 10% overlap.
- Tile records: 56.
- Ran Doubao prompt v3 on all 56 overlap tile images.
- Tile adapter mode counts: `synthetic_from_counts` 56.
- Tile adapter error counts: `none` 56.
- Aggregated overlap tile predictions back to 14 panel-level predictions.
- Aggregation rule: node=sum, edge=sum, net=mean_clamped3.
- Panel-level prediction graph valid rate: 1.0.
- Count error comparison:
  - node MAE: v3@512 394.642857, tile2x2 378.285714, tile2x2 overlap10 362.642857.
  - edge MAE: v3@512 715.642857, tile2x2 713.5, tile2x2 overlap10 687.857143.
  - net MAE: v3@512 0.857143, tile2x2 0.714286, tile2x2 overlap10 0.857143.
- Interpretation: 10% overlap improves edge_count compared with no-overlap tile2x2, supporting the hypothesis that tile boundary truncation was hurting edge estimates. It also improves node_count, while net_count returns to the whole-image v3 level.
- Main outputs:
  - `docs/topology_panel_v1_doubao_tile2x2_overlap10_input_report.md`
  - `data_index/topology_panel_v1_tile2x2_overlap10_benchmark_manifest.jsonl`
  - `data_index/topology_panel_v1_tile2x2_overlap10_benchmark_manifest.csv`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_tile_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions.jsonl`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_summary.json`
  - `data_index/topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_details.csv`
  - updated `data_index/topology_panel_v1_model_leaderboard.csv`

## 2026-07-10 Tile2x2 / Overlap10 Review HTML

- Added a tile overlap review HTML builder: `scripts/build_topology_panel_v1_tile_overlap_review_html.py`.
- Generated review HTML for comparing whole-image v3@512, tile2x2, and tile2x2 overlap10 predictions.
- Review panels: 14.
- The review page shows the original panel, 2x2 tile images, 2x2 overlap10 tile images, tile-level node/edge/net predictions, panel-level errors, and automatic delta tags.
- Auto tag counts:
  - `overlap_edge_benefit`: 10.
  - `overlap_node_benefit`: 8.
  - `better_than_whole_image`: 10.
  - `possible_duplicate_edges`: 1.
  - `possible_duplicate_nodes`: 4.
  - `possible_duplicate_nets`: 2.
- The page supports browser-local review labels and CSV export for manual decisions about overlap benefit, duplicate counting, boundary cut issues, 3x3, or adaptive crop.
- Main outputs:
  - `data_index/topology_panel_v1_tile2x2_overlap10_review.html`
  - `data_index/topology_panel_v1_tile2x2_overlap10_review_manifest.csv`
  - `data_index/topology_panel_v1_tile2x2_overlap10_review_summary.json`

## 2026-07-10 Tile2x2 Overlap10 Auto Judge Policy

- Applied the user's decision to trust the model/auto Judge instead of waiting for manual per-panel review.
- Added auto-judge policy script: `scripts/apply_topology_panel_v1_tile_overlap_auto_judge.py`.
- Source review manifest: `data_index/topology_panel_v1_tile2x2_overlap10_review_manifest.csv`.
- Auto-judge rows: 14.
- Global decision: use `tile2x2 + overlap10` as the next default image-input baseline.
- Decision counts:
  - `prefer_overlap10`: 10.
  - `overlap10_risk_monitor`: 2.
  - `prefer_overlap10_with_monitoring`: 1.
  - `needs_tile_review_before_scaling`: 1.
- Next action counts:
  - `use_overlap10_for_next_benchmark`: 8.
  - `monitor_aggregation_rule`: 4.
  - `no_extra_tile_complexity`: 1.
  - `inspect_boundary_duplicates`: 1.
- Policy: possible duplicate-edge rows do not block the overlap10 strategy, but remain in a boundary duplicate risk monitor.
- Main outputs:
  - `data_index/topology_panel_v1_tile2x2_overlap10_auto_judge_manifest.csv`
  - `data_index/topology_panel_v1_tile2x2_overlap10_auto_judge_summary.json`
  - `docs/topology_panel_v1_tile2x2_overlap10_auto_judge_report.md`

## 2026-07-10 Model Experiment Summary and Per-Sample Delta Analysis

- Generated final method summary document for Topology Panel v1 model experiments.
- Generated per-sample image-input delta analysis across:
  - whole-image Doubao prompt v3 at 512.
  - whole-image Doubao prompt v3 at 1024.
  - Doubao prompt v3 tile2x2.
  - Doubao prompt v3 tile2x2 overlap10.
- Delta analysis rows: 14.
- Mean absolute errors:
  - whole_v3_512: node 394.642857, edge 715.642857, net 0.857143.
  - whole_v3_1024: node 399.571429, edge 724.285714, net 0.928571.
  - tile2x2: node 378.285714, edge 713.5, net 0.714286.
  - tile2x2_overlap10: node 362.642857, edge 687.857143, net 0.857143.
- Gain counts versus whole_v3_512:
  - node improved on 10 / 14 panels.
  - edge improved on 10 / 14 panels.
  - net improved on 2 / 14 panels.
- Pattern counts:
  - `node_edge_gain`: 9.
  - `node_edge_net_gain`: 1.
  - `no_count_gain`: 4.
- Interpretation: tile2x2 overlap10 is supported by per-sample evidence, not just aggregate averages; duplicate-risk samples remain monitored but do not block the default baseline policy.
- Main outputs:
  - `docs/topology_panel_v1_model_experiment_summary.md`
  - `scripts/build_topology_panel_v1_image_input_delta_analysis.py`
  - `data_index/topology_panel_v1_image_input_delta_analysis.csv`
  - `data_index/topology_panel_v1_image_input_delta_analysis_summary.json`
  - `docs/topology_panel_v1_image_input_delta_analysis.md`

## 2026-07-10 Frozen Current Best Model Baseline

- Frozen current best real-model count-level baseline for Topology Panel v1.
- Method: `doubao_prompt_v3_tile2x2_overlap10`.
- Input: Doubao prompt v3 with tile2x2 + 10% overlap.
- Aggregation: node=sum; edge=sum; net=mean_clamped3.
- Scope: count-level synthetic graph baseline, not full topology graph reconstruction.
- Rows: 14.
- Prediction graph valid rate: 1.0.
- MAE:
  - node_count: 362.642857.
  - edge_count: 687.857143.
  - net_count: 0.857143.
- Main outputs:
  - `data_index/topology_panel_v1_best_model_predictions.jsonl`
  - `data_index/topology_panel_v1_best_model_eval_summary.json`
  - `data_index/topology_panel_v1_best_model_eval_details.csv`
  - `data_index/topology_panel_v1_best_model_eval_errors.csv`
  - `data_index/topology_panel_v1_best_model_manifest.csv`
  - `data_index/topology_panel_v1_best_model_summary.json`
  - `docs/topology_panel_v1_best_model_baseline.md`

## 2026-07-10 Hugging Face Release Package Sync for Best Baseline

- Synced the frozen current best model baseline into the Hugging Face release package and dataset card.
- Updated dataset card section: `Current Best Model Baseline`.
- Updated release file checklist with the 2026-07-10 best baseline addendum.
- Updated `scripts/prepare_hf_release_package.py`:
  - package id: `hf_release_topology_panel_v1_2026-07-10`.
  - added `model_baseline` release category.
  - included 10 best baseline files.
- Rebuilt local package:
  - output directory: `outputs/hf_release_topology_panel_v1/`.
  - copied files: 33 source files plus 3 generated package metadata files.
  - missing files: 0.
  - package file count uploaded: 36.
- Uploaded package to Hugging Face Dataset:
  - repo: `yanhongliu/Industrial-Diagram-Benchmark`.
- Important boundary:
  - best model baseline files are reproducible model-result artifacts.
  - they are not ground truth and do not change the 14-row Topology Panel v1 clean baseline boundary.

## 2026-07-10 Project Final Summary and Experiment Table

- Generated project-level final summary for the current Industrial Diagram Benchmark stage.
- Generated Topology Panel v1 experiment result table in CSV and Markdown.
- Main outputs:
  - `docs/project_final_summary.md`
  - `data_index/topology_panel_v1_experiment_table.csv`
  - `docs/topology_panel_v1_experiment_table.md`
- Current best model baseline remains:
  - `doubao_prompt_v3_tile2x2_overlap10`
  - node MAE: 362.642857
  - edge MAE: 687.857143
  - net MAE: 0.857143
- The summary keeps the formal v1 boundary unchanged: 14 clean baseline rows only.
