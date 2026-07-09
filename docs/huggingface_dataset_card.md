---
license: apache-2.0
task_categories:
  - image-to-text
  - visual-question-answering
  - object-detection
language:
  - zh
  - en
tags:
  - cad
  - dxf
  - dwg
  - industrial-diagram
  - wiring-diagram
  - topology
  - graph
  - benchmark
pretty_name: Industrial Diagram Benchmark
---

# Industrial Diagram Benchmark

Industrial Diagram Benchmark is a dataset project for industrial wiring diagram understanding, structured CAD parsing, topology graph extraction, diagram VQA, and CAD reconstruction.

This dataset is paired with the GitHub engineering repository:

```text
https://github.com/codesknight/Industrial-Diagram-Benchmark
```

The GitHub repository contains code, generated manifests, benchmark scripts, review reports, and documentation. The Hugging Face Dataset hosts large data artifacts such as DWG/DXF/JSON/PNG files and release packages.

## Current Stable Release

The current stable benchmark release is:

```text
Topology Panel v1 clean baseline
```

It contains **14 manually reviewed panel-level topology samples**.

Official v1 baseline manifest:

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
```

Benchmark JSONL:

```text
data_index/topology_panel_v1_benchmark_manifest.jsonl
```

Evaluation protocol:

```text
docs/topology_graph_eval_protocol_v1.md
```

Evaluation script in the companion repository:

```text
benchmark/topology/evaluate_topology_graph_v1.py
```

## Version Boundary

`Topology Panel v1` means **only** the 14 clean baseline samples.

Current reviewed sample partition:

```text
clean_baseline: 14
excluded_badcase: 125
improvement_target: 31
unreviewed: 1
```

Baseline split:

```text
train: 11
val: 1
test: 2
```

Baseline phase distribution:

```text
P1: 4
P2: 1
P3: 9
```

Excluded badcase rows are not part of the formal v1 benchmark:

```text
multi_subfigure_badcase: 43
bad_geometry: 63
not_topology_target: 19
```

`Topology Panel v1.1 candidates` are kept for future algorithm experiments and must not be mixed into the formal v1 score:

```text
total: 12
terminal_anchor_module: 3
over_connected_repair: 9
```

The previous `still_fragmented` bucket contains 19 rows that have been marked as abandoned for the current v1.1 repair cycle. They are preserved for error analysis only.

## How to Evaluate

Install dependencies in the companion repository:

```powershell
pip install -r requirements.txt
```

Run the default sanity-check evaluation:

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py
```

By default, this uses `reference_as_prediction` mode to verify that the benchmark package and evaluator are internally consistent.

To evaluate model predictions:

```powershell
python benchmark/topology/evaluate_topology_graph_v1.py `
  --manifest data_index/topology_panel_v1_benchmark_manifest.jsonl `
  --predictions path/to/predictions.jsonl `
  --summary outputs/topology_eval_summary.json `
  --report outputs/topology_eval_report.md
```

Prediction records should be aligned by `panel_id`.

## Recommended Release Files

The recommended Hugging Face release file list is maintained in:

```text
data_index/HF_RELEASE_FILES.md
```

Core v1 files:

```text
data_index/topology_panel_v1_final_baseline_manifest.csv
data_index/topology_panel_v1_benchmark_manifest.jsonl
data_index/topology_panel_v1_benchmark_summary.json
data_index/topology_panel_v1_benchmark_report.md
data_index/topology_panel_v1_eval_summary.json
data_index/topology_panel_v1_eval_report.md
docs/topology_graph_eval_protocol_v1.md
docs/topology_panel_v1_release_status.md
```

Optional boundary files:

```text
data_index/topology_panel_v1_release_excluded_manifest.csv
data_index/topology_panel_v1_release_improvement_manifest.csv
data_index/topology_panel_v1_1_abandoned_manifest.csv
data_index/topology_panel_v1_1_keep_improvement_manifest.csv
```

## Data Scope

The broader dataset is designed around industrial electrical drawings, including:

- electrical schematic diagrams
- wiring diagrams
- PLC diagrams
- power distribution diagrams
- control cabinet drawings

The raw and intermediate file layout may include:

```text
dwg_staging/      Original DWG files
dxf_staging/      Converted DXF files
raw_json/         Raw Geometry JSON parsed from DXF
qa_and_png/       Rendered PNG files and QA images
```

## Data Representations

The project currently includes or is designed to support:

- Raw Geometry JSON
- Normalized Geometry JSON
- Topology Graph JSON
- panel-level benchmark JSONL
- future Semantic Diagram JSON
- future VQA JSONL
- future CAD reconstruction targets

## Notes

This is an evolving research benchmark. The current stable topology benchmark is intentionally small because it has a strict manual review boundary. Please report numbers separately for:

- `Topology Panel v1 clean baseline`
- `Topology Panel v1 excluded badcase`
- `Topology Panel v1.1 candidates`

Do not merge these partitions when reporting formal v1 benchmark results.

## License

Apache-2.0.
