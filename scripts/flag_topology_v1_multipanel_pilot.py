"""Record manual visual finding that v1 pilot drawings are multi-panel pages."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_PILOT = INDEX_DIR / "topology_v1_pilot_manifest.csv"
DEFAULT_PANEL = INDEX_DIR / "final_panel_manifest.csv"


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=Path, default=DEFAULT_PILOT)
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pilot_rows = load_csv(args.pilot)
    panel_rows = load_csv(args.panel)
    panel_by_parent: Dict[str, List[Dict[str, str]]] = {}
    for row in panel_rows:
        panel_by_parent.setdefault(row["parent_drawing_key"], []).append(row)

    finding_rows: List[Dict[str, object]] = []
    for row in pilot_rows:
        panels = panel_by_parent.get(row["drawing_key"], [])
        finding_rows.append(
            {
                "drawing_key": row["drawing_key"],
                "split": row.get("split", ""),
                "phase": row.get("phase", ""),
                "topology_v0_json_path": row.get("topology_v0_json_path", ""),
                "topology_v1_json_path": row.get("topology_v1_json_path", ""),
                "v0_net_count": row.get("v0_net_count", ""),
                "v1_net_count": row.get("v1_net_count", ""),
                "intersection_count": row.get("intersection_count", ""),
                "manual_visual_finding": "multi_panel_page",
                "current_panel_rows": len(panels),
                "current_panel_count_values": ";".join(sorted({p.get("panel_count", "") for p in panels})),
                "current_split_methods": ";".join(sorted({p.get("split_method", "") for p in panels})),
                "recommended_action": "redo_panel_split_before_topology_v1",
                "topology_v1_full_rollout_status": "blocked_by_multi_panel_input",
            }
        )

    fieldnames = [
        "drawing_key",
        "split",
        "phase",
        "topology_v0_json_path",
        "topology_v1_json_path",
        "v0_net_count",
        "v1_net_count",
        "intersection_count",
        "manual_visual_finding",
        "current_panel_rows",
        "current_panel_count_values",
        "current_split_methods",
        "recommended_action",
        "topology_v1_full_rollout_status",
    ]
    write_csv(INDEX_DIR / "topology_v1_pilot_multipanel_findings.csv", finding_rows, fieldnames)

    summary = {
        "pilot_rows": len(pilot_rows),
        "multi_panel_page_rows": len(finding_rows),
        "current_panel_rows_by_count": dict(Counter(str(row["current_panel_rows"]) for row in finding_rows)),
        "current_split_methods": dict(Counter(str(row["current_split_methods"]) for row in finding_rows)),
        "decision": "do not promote drawing-level topology v1 pilot to full rollout until these pages are split to panel-level samples",
        "next_action": "build panel-level topology pilot candidates for these multi-panel pages",
    }
    (INDEX_DIR / "topology_v1_pilot_multipanel_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)

    print(f"Multi-panel v1 pilot findings: {len(finding_rows)}")
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/topology_v1_pilot_multipanel_findings.csv")


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology v1 Pilot Multi-Panel Finding Report",
        "",
        "Manual visual review found that all current v1 pilot drawings are multi-panel pages.",
        "",
        "## Summary",
        "",
        f"- Pilot rows: {summary['pilot_rows']}",
        f"- Multi-panel page rows: {summary['multi_panel_page_rows']}",
        f"- Decision: {summary['decision']}",
        f"- Next action: {summary['next_action']}",
        "",
        "## Current Panel Split State",
        "",
    ]
    for count, rows in summary["current_panel_rows_by_count"].items():
        lines.append(f"- current_panel_rows={count}: {rows}")
    lines.extend(["", "## Current Split Methods", ""])
    for method, rows in summary["current_split_methods"].items():
        lines.append(f"- {method}: {rows}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The drawing-level v1 pilot proves that intersection splitting can reduce fragmentation,",
            "but these pages should not be used to justify full drawing-level rollout.",
            "Topology v1 should be rerun after splitting these pages into single-diagram panels.",
        ]
    )
    (INDEX_DIR / "topology_v1_pilot_multipanel_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
