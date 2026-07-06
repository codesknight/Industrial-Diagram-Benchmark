# Topology Panel v1 Pilot

`Topology Panel v1 Pilot` reruns intersection-splitting topology on manually
split single-diagram panels from the 7 multi-panel v1 pilot pages.

Generate it with:

```powershell
python scripts/build_topology_panel_v1_pilot.py
```

Default input:

```text
data_index/topology_multipanel_manual_panel_usable.csv
```

Default outputs:

```text
outputs/topology_panel_v1_pilot/
data_index/topology_panel_v1_pilot_manifest.csv
data_index/topology_panel_v1_pilot_summary.json
data_index/topology_panel_v1_pilot_report.md
```

## Result

```text
panel rows: 17
parent drawings: 7
no-edge rows: 0
v1 edge count avg: 1710.41
v1 net count avg: 6.35
total intersections: 15925
```

This panel-level pilot is more reliable than the earlier drawing-level v1 pilot
because it avoids connecting separate subfigures on the same PNG page.
