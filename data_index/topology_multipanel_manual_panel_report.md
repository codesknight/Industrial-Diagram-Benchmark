# Topology Multi-Panel Manual Split Report

This report summarizes manual PNG bbox splits for topology v1 multi-panel pages.

## Summary

- Manual panel rows: 18
- Usable panel rows: 17
- Invalid/review rows: 1
- Parent drawing count: 7
- Usable parent drawing count: 7

## Invalid Quality Flags

- too_small: 1
- low_area_ratio: 1

## Rules

- manual bbox rows with status=accept and no quality flags are usable for panel-level topology pilot
- too_small or low_area_ratio rows are retained for review but excluded from usable panel pilot
- this manifest is scoped to topology v1 multi-panel pages and does not replace final_panel_manifest.csv
