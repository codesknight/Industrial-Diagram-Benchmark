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
