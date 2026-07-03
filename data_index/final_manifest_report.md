# Final Manifest Report

This report summarizes the curated dataset entry points after cleaning, manual panel review, and visible watermark filtering.

## Summary

- Drawing source rows: 2054
- Final drawing rows: 2042
- Rejected drawing rows: 12
- Panel source rows: 2196
- Final panel rows: 2069
- Rejected panel rows: 127
- Visible watermark parent rows: 12

## Final Drawing Splits

- train: 1638
- val: 196
- test: 208

## Final Panel Splits

- train: 1665
- val: 196
- test: 208

## Rejected Panel Reasons

- panel_review_reject: 115
- parent_visible_watermark: 12

## Rules

- drawing source: round2 clean manifest
- drop drawing rows with visible watermark candidates
- panel source: panel manifest with manual review labels
- drop panels rejected by manual review
- drop panels whose parent drawing has visible watermark candidate
- source marker filenames are not filtered
