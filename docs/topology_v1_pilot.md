# Topology Graph v1 Pilot

`Topology Graph v1 Pilot` tests line-intersection splitting on manually reviewed
samples labeled `needs_intersection_split`.

Generate it with:

```powershell
python scripts/build_topology_v1_pilot.py
```

Default input:

```text
data_index/topology_v1_pilot_candidates.csv
```

Default outputs:

```text
outputs/topology_graph_v1_pilot/
data_index/topology_v1_pilot_manifest.csv
data_index/topology_v1_pilot_summary.json
data_index/topology_v1_pilot_report.md
```

`outputs/topology_graph_v1_pilot/` is local output and is not committed to Git.

## Method

The pilot keeps the v0 endpoint-clustering rule and adds one operation:

1. Extract wire-like segments from `LINE` and `LWPOLYLINE`.
2. Detect non-parallel line-line intersections.
3. Add each interior intersection as a split point.
4. Split original segments into shorter edges.
5. Rebuild nodes, edges, and connected components.
6. Compare v1 pilot stats against the v0 graph stats.

This version treats geometric line intersections as graph connections. It is a
pilot for drawings where manual review suggests that v0 missed T-junctions or
crossing-line connections.

## Current Pilot Result

The first pilot uses 7 manually reviewed samples.

```text
v0 edge total: 7080
v1 edge total: 37890
v0 net total: 6164
v1 net total: 103
rows with lower isolated ratio: 7
rows with lower net count: 7
```

The result confirms that intersection splitting is valuable for these samples.
Before full rollout, review whether all visual crossings in the target drawing
family should be treated as electrical connections. If not, v1 should add a
connection-marker or layer-aware rule before running full-dataset generation.
