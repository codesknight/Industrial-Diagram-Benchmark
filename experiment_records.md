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
