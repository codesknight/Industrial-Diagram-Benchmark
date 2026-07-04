# Topology Graph v0

`Topology Graph v0` is the first graph layer built from `Normalized Geometry JSON`.
It is designed as a reproducible baseline for topology-aware tasks before adding
heavier CAD-specific graph repair.

Generate it with:

```powershell
python scripts/build_topology_graph.py
```

Default input:

```text
data_index/normalized_geometry_manifest.csv
```

Default outputs:

```text
outputs/topology_graph/
data_index/topology_graph_manifest.csv
data_index/topology_graph_summary.json
data_index/topology_graph_report.md
data_index/topology_quality_review.csv
```

`outputs/topology_graph/` is not committed to Git. Git stores the manifest,
summary, report, and review list.

## Method

Topology v0 extracts wire-like segments from:

- `LINE`
- `LWPOLYLINE`

For each drawing, the builder:

1. Converts lines and polyline spans into graph edges.
2. Clusters endpoints by `endpoint_merge_tolerance`.
3. Builds nodes, edges, and connected components.
4. Writes each connected component as a `net`.
5. Records quality flags for later review.

This version does not split line segments at geometric intersections. That
choice keeps v0 stable and fast across the full dataset. Intersection-aware
splitting should be added in Topology Graph v1.

## Schema

Each local graph JSON uses:

```json
{
  "schema": "industrial_diagram.topology_graph.v0",
  "drawing_key": "...",
  "phase": "...",
  "split": "...",
  "source": {
    "normalized_json_path": "..."
  },
  "params": {
    "endpoint_merge_tolerance": 1.0,
    "min_segment_length": 0.001,
    "precision": 4,
    "max_segments": 300000,
    "intersection_splitting": false
  },
  "status": "ok",
  "stats": {},
  "nodes": [],
  "edges": [],
  "nets": []
}
```

Node fields:

```text
id
point
degree
```

Edge fields:

```text
id
source
target
segment_id
entity_id
entity_type
layer
points
length
```

Net fields:

```text
id
node_count
edge_count
bbox
```

## Quality Flags

`data_index/topology_quality_review.csv` lists drawings that need graph-level
review. Current flags:

- `no_edges`: no usable `LINE` or `LWPOLYLINE` edges.
- `high_isolated_ratio`: many one-edge components.
- `single_large_component`: only one non-empty component in a graph with many edges.
- `dominant_component`: one component contains most graph edges.
- `truncated_max_segments`: graph hit the configured segment cap.

These flags are review signals, not automatic rejection rules.
