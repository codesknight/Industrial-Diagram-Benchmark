"""Apply v1.1 abandoned policy after still-fragmented diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_IMPROVEMENT = INDEX_DIR / "topology_panel_v1_release_improvement_manifest.csv"
DEFAULT_DIAGNOSTIC = INDEX_DIR / "topology_panel_v1_1_still_fragmented_diagnostic.csv"
DEFAULT_ACTIVE = INDEX_DIR / "topology_panel_v1_1_active_improvement_manifest.csv"
DEFAULT_ABANDONED = INDEX_DIR / "topology_panel_v1_1_abandoned_manifest.csv"
DEFAULT_TERMINAL = INDEX_DIR / "topology_panel_v1_1_active_terminal_anchor_manifest.csv"
DEFAULT_OVER_CONNECTED = INDEX_DIR / "topology_panel_v1_1_active_over_connected_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_1_abandoned_policy_summary.json"
DEFAULT_REPORT = INDEX_DIR / "topology_panel_v1_1_abandoned_policy_report.md"

ABANDONED_POLICY_ID = "topology_panel_v1_1_abandoned_policy_2026-07-08"


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


def diagnostic_by_panel(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {row["panel_id"]: row for row in rows if row.get("panel_id")}


def apply_policy(row: Dict[str, str], diagnostic: Dict[str, str] | None) -> Dict[str, object]:
    out: Dict[str, object] = dict(row)
    original_reason = row.get("topology_panel_v1_policy_exclude_reason", "")
    out["topology_panel_v1_1_policy_id"] = ABANDONED_POLICY_ID
    out["topology_panel_v1_1_original_improvement_reason"] = original_reason

    if diagnostic is not None:
        out["topology_panel_v1_1_diagnostic_label"] = diagnostic.get("suggested_diagnostic_label", "")
        out["topology_panel_v1_1_diagnostic_reason"] = diagnostic.get("suggested_diagnostic_reason", "")
        out["topology_panel_v1_1_panel_line_like_entity_count"] = diagnostic.get("panel_line_like_entity_count", "")
        out["topology_panel_v1_1_panel_total_entity_count"] = diagnostic.get("panel_total_entity_count", "")
        out["topology_panel_v1_1_still_empty"] = diagnostic.get("still_empty", "")
        out["topology_panel_v1_1_candidate_improved"] = diagnostic.get("candidate_improved", "")
        out["topology_panel_v1_1_abandoned"] = True
        out["topology_panel_v1_1_decision"] = "abandoned"
        out["topology_panel_v1_1_decision_reason"] = (
            "still_fragmented bucket abandoned after v1.1 tolerance experiment produced no improved candidates"
        )
        out["topology_panel_v1_1_next_route"] = "badcase_error_analysis_only"
    elif original_reason == "needs_terminal_anchor":
        out["topology_panel_v1_1_diagnostic_label"] = ""
        out["topology_panel_v1_1_diagnostic_reason"] = ""
        out["topology_panel_v1_1_panel_line_like_entity_count"] = ""
        out["topology_panel_v1_1_panel_total_entity_count"] = ""
        out["topology_panel_v1_1_still_empty"] = ""
        out["topology_panel_v1_1_candidate_improved"] = ""
        out["topology_panel_v1_1_abandoned"] = False
        out["topology_panel_v1_1_decision"] = "active_improvement"
        out["topology_panel_v1_1_decision_reason"] = "reserved for terminal or symbol anchor work"
        out["topology_panel_v1_1_next_route"] = "terminal_anchor_module"
    elif original_reason == "over_connected":
        out["topology_panel_v1_1_diagnostic_label"] = ""
        out["topology_panel_v1_1_diagnostic_reason"] = ""
        out["topology_panel_v1_1_panel_line_like_entity_count"] = ""
        out["topology_panel_v1_1_panel_total_entity_count"] = ""
        out["topology_panel_v1_1_still_empty"] = ""
        out["topology_panel_v1_1_candidate_improved"] = ""
        out["topology_panel_v1_1_abandoned"] = False
        out["topology_panel_v1_1_decision"] = "active_improvement"
        out["topology_panel_v1_1_decision_reason"] = "reserved for crossing-line disambiguation work"
        out["topology_panel_v1_1_next_route"] = "over_connected_repair"
    else:
        out["topology_panel_v1_1_diagnostic_label"] = ""
        out["topology_panel_v1_1_diagnostic_reason"] = ""
        out["topology_panel_v1_1_panel_line_like_entity_count"] = ""
        out["topology_panel_v1_1_panel_total_entity_count"] = ""
        out["topology_panel_v1_1_still_empty"] = ""
        out["topology_panel_v1_1_candidate_improved"] = ""
        out["topology_panel_v1_1_abandoned"] = False
        out["topology_panel_v1_1_decision"] = "active_improvement"
        out["topology_panel_v1_1_decision_reason"] = "kept for future review"
        out["topology_panel_v1_1_next_route"] = "future_review"
    return out


def build_summary(rows: List[Dict[str, object]], diagnostic_rows: List[Dict[str, str]]) -> Dict[str, object]:
    abandoned = [row for row in rows if row.get("topology_panel_v1_1_decision") == "abandoned"]
    active = [row for row in rows if row.get("topology_panel_v1_1_decision") == "active_improvement"]
    return {
        "policy_id": ABANDONED_POLICY_ID,
        "source_improvement_manifest": DEFAULT_IMPROVEMENT.relative_to(ROOT).as_posix(),
        "source_diagnostic_csv": DEFAULT_DIAGNOSTIC.relative_to(ROOT).as_posix(),
        "input_improvement_rows": len(rows),
        "diagnostic_rows": len(diagnostic_rows),
        "abandoned_rows": len(abandoned),
        "active_improvement_rows": len(active),
        "decision_counts": dict(Counter(str(row.get("topology_panel_v1_1_decision", "")) for row in rows)),
        "original_reason_counts": dict(
            Counter(str(row.get("topology_panel_v1_1_original_improvement_reason", "")) for row in rows)
        ),
        "abandoned_diagnostic_label_counts": dict(
            Counter(str(row.get("topology_panel_v1_1_diagnostic_label", "")) for row in abandoned)
        ),
        "active_next_route_counts": dict(
            Counter(str(row.get("topology_panel_v1_1_next_route", "")) for row in active)
        ),
        "rules": [
            "All still_fragmented rows diagnosed in v1.1 are abandoned and kept for badcase/error analysis only.",
            "Abandoned rows must not be used as v1.1 repair candidates unless a future manual override is created.",
            "needs_terminal_anchor and over_connected rows remain active improvement targets.",
            "The formal Topology Panel v1 baseline remains unchanged.",
        ],
        "outputs": {
            "active_improvement_manifest": DEFAULT_ACTIVE.relative_to(ROOT).as_posix(),
            "abandoned_manifest": DEFAULT_ABANDONED.relative_to(ROOT).as_posix(),
            "active_terminal_anchor_manifest": DEFAULT_TERMINAL.relative_to(ROOT).as_posix(),
            "active_over_connected_manifest": DEFAULT_OVER_CONNECTED.relative_to(ROOT).as_posix(),
            "summary": DEFAULT_SUMMARY.relative_to(ROOT).as_posix(),
            "report": DEFAULT_REPORT.relative_to(ROOT).as_posix(),
        },
    }


def write_report(summary: Dict[str, object]) -> None:
    lines = [
        "# Topology Panel v1.1 Abandoned Policy Report",
        "",
        f"Policy id: `{summary['policy_id']}`",
        "",
        "This report freezes the decision to abandon the v1.1 still-fragmented diagnostic bucket.",
        "The formal Topology Panel v1 baseline is unchanged.",
        "",
        "## Summary",
        "",
        f"- Input improvement rows: {summary['input_improvement_rows']}",
        f"- Diagnostic rows: {summary['diagnostic_rows']}",
        f"- Abandoned rows: {summary['abandoned_rows']}",
        f"- Active improvement rows: {summary['active_improvement_rows']}",
        "",
        "## Decisions",
        "",
    ]
    for decision, count in summary["decision_counts"].items():
        lines.append(f"- {decision}: {count}")

    lines.extend(["", "## Original Improvement Reasons", ""])
    for reason, count in summary["original_reason_counts"].items():
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "## Abandoned Diagnostic Labels", ""])
    for label, count in summary["abandoned_diagnostic_label_counts"].items():
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Active Next Routes", ""])
    for route, count in summary["active_next_route_counts"].items():
        lines.append(f"- {route}: {count}")

    lines.extend(["", "## Rules", ""])
    for rule in summary["rules"]:
        lines.append(f"- {rule}")

    lines.extend(["", "## Outputs", ""])
    for name, path in summary["outputs"].items():
        lines.append(f"- {name}: `{path}`")

    DEFAULT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--improvement", type=Path, default=DEFAULT_IMPROVEMENT)
    parser.add_argument("--diagnostic", type=Path, default=DEFAULT_DIAGNOSTIC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    improvement_rows = load_csv(args.improvement)
    diagnostic_rows = load_csv(args.diagnostic)
    diagnostics = diagnostic_by_panel(diagnostic_rows)
    rows = [apply_policy(row, diagnostics.get(row.get("panel_id", ""))) for row in improvement_rows]
    fieldnames = list(rows[0].keys()) if rows else []

    active = [row for row in rows if row.get("topology_panel_v1_1_decision") == "active_improvement"]
    abandoned = [row for row in rows if row.get("topology_panel_v1_1_decision") == "abandoned"]
    terminal = [
        row for row in active
        if row.get("topology_panel_v1_1_next_route") == "terminal_anchor_module"
    ]
    over_connected = [
        row for row in active
        if row.get("topology_panel_v1_1_next_route") == "over_connected_repair"
    ]

    write_csv(DEFAULT_ACTIVE, active, fieldnames)
    write_csv(DEFAULT_ABANDONED, abandoned, fieldnames)
    write_csv(DEFAULT_TERMINAL, terminal, fieldnames)
    write_csv(DEFAULT_OVER_CONNECTED, over_connected, fieldnames)

    summary = build_summary(rows, diagnostic_rows)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary)

    print(f"Input improvement rows: {summary['input_improvement_rows']}")
    print(f"Abandoned rows: {summary['abandoned_rows']}")
    print(f"Active improvement rows: {summary['active_improvement_rows']}")
    print(f"Wrote: {DEFAULT_ABANDONED.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_ACTIVE.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
