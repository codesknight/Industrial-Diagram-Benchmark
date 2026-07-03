---
license: apache-2.0
task_categories:
  - image-to-text
  - visual-question-answering
  - object-detection
language:
  - zh
tags:
  - cad
  - dxf
  - dwg
  - industrial-diagram
  - wiring-diagram
  - topology
  - vqa
pretty_name: Industrial Diagram Benchmark
---

# Industrial Diagram Benchmark

Industrial Diagram Benchmark is a dataset project for industrial wiring diagram understanding, structured CAD parsing, topology extraction, diagram VQA, and CAD reconstruction.

## Data Scope

The dataset is designed around industrial electrical drawings, including:

- Electrical schematic diagrams
- Wiring diagrams
- PLC diagrams
- Power distribution diagrams
- Control cabinet drawings

## Expected File Layout

```text
dwg_staging/      Original DWG files
dxf_staging/      Converted DXF files
raw_json/         Raw Geometry JSON parsed from DXF
qa_and_png/       Rendered PNG files and future QA artifacts
```

## Companion Code

The code, configuration, generated manifest, and benchmark scripts are maintained on GitHub:

```text
https://github.com/codesknight/Industrial-Diagram-Benchmark
```

## Current Representation

The current JSON files are Raw Geometry JSON. They mainly contain CAD primitives such as:

- `LINE`
- `LWPOLYLINE`
- `TEXT` / `MTEXT`
- `INSERT`
- `CIRCLE`
- `ARC`

Future releases may add:

- Normalized Geometry JSON
- Semantic Diagram JSON
- Topology Graph JSON
- VQA JSONL
- CAD reconstruction targets

## Known Data Notes

The companion GitHub manifest currently records:

- 2099 indexed drawing rows
- 2098 complete DWG/DXF/JSON/PNG logical samples
- 1 sample missing DXF/JSON/PNG
- 23 PNG reuse groups caused mainly by P3 batches sharing one rendered PNG folder

See the GitHub `data_index/` directory for the latest generated reports.

## License

Apache-2.0.
