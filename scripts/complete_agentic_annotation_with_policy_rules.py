"""Complete missing agentic annotation rows with deterministic policy rules."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data_index"
DEFAULT_CANDIDATES = DATA_INDEX / "topology_panel_v1_5_candidate_manifest.csv"
DEFAULT_PREFIX = DATA_INDEX / "topology_panel_v1_5_agentic_annotation_full"


AGENT_FIELDS = [
    "panel_id",
    "agent",
    "agent_model",
    "agent_modality",
    "agent_label",
    "agent_confidence",
    "is_single_panel",
    "is_topology_target",
    "has_visible_watermark",
    "geometry_usable",
    "agent_reason",
    "agent_visible_cues",
    "elapsed_sec",
    "error",
    "raw_response",
]

CONSENSUS_FIELDS = [
    "panel_id",
    "phase",
    "split",
    "panel_png_path",
    "topology_v1_panel_json_path",
    "v1_5_candidate_score",
    "v1_5_candidate_bucket",
    "known_policy_decision",
    "known_review_label",
    "consensus_label",
    "consensus_decision",
    "consensus_confidence",
    "agreement_count",
    "agent_count",
    "reason",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def output_paths(prefix: Path) -> Dict[str, Path]:
    return {
        "agent_outputs": prefix.with_name(prefix.name + "_agent_outputs.csv"),
        "consensus": prefix.with_name(prefix.name + "_consensus.csv"),
        "summary": prefix.with_name(prefix.name + "_summary.json"),
        "report": prefix.with_name(prefix.name + "_report.md"),
    }


def policy_label(row: Dict[str, str]) -> tuple[str, str, float, bool, bool, bool, bool]:
    review = row.get("topology_panel_v1_review_label", "")
    exclude_reason = row.get("topology_panel_v1_policy_exclude_reason", "")
    release_reason = row.get("topology_panel_v1_release_exclude_reason", "")
    combined = ";".join([review, exclude_reason, release_reason])
    if "needs_panel_split" in combined or "multi_subfigure" in combined:
        return "reject_multi_subfigure", "known policy badcase: multi-subfigure", 0.98, False, True, False, True
    if "bad_geometry" in combined or row.get("status") != "ok":
        return "reject_bad_geometry", "known policy badcase: bad geometry", 0.98, False, False, False, False
    if "not_topology_target" in combined:
        return "reject_not_topology", "known policy badcase: not topology target", 0.98, True, False, False, True
    if row.get("v1_5_candidate_bucket") == "negative_control_badcase":
        return "reject_bad_geometry", "known negative-control badcase", 0.9, False, False, False, False
    return "uncertain", "no deterministic policy rule", 0.0, False, False, False, False


def consensus_decision(label: str, confidence: float) -> str:
    if label.startswith("reject_") and confidence >= 0.75:
        return "auto_reject"
    if label == "accept_clean_topology" and confidence >= 0.9:
        return "auto_accept"
    if label in {"needs_terminal_anchor", "needs_graph_repair"} and confidence >= 0.75:
        return "auto_defer_improvement"
    return "human_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_PREFIX)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = output_paths(args.output_prefix)
    candidates = read_csv(args.candidates)
    agent_rows = read_csv(paths["agent_outputs"])
    consensus_rows = read_csv(paths["consensus"])
    existing = {row["panel_id"] for row in consensus_rows}

    added = 0
    for row in candidates:
        panel_id = row["panel_id"]
        if panel_id in existing:
            continue
        label, reason, confidence, is_single, is_topology, watermark, geometry = policy_label(row)
        agent_rows.append(
            {
                "panel_id": panel_id,
                "agent": "policy_rule",
                "agent_model": "deterministic_policy",
                "agent_modality": "metadata_rule",
                "agent_label": label,
                "agent_confidence": confidence,
                "is_single_panel": is_single,
                "is_topology_target": is_topology,
                "has_visible_watermark": watermark,
                "geometry_usable": geometry,
                "agent_reason": reason,
                "agent_visible_cues": row.get("topology_panel_v1_policy_exclude_reason", ""),
                "elapsed_sec": 0,
                "error": "",
                "raw_response": "",
            }
        )
        consensus_rows.append(
            {
                "panel_id": panel_id,
                "phase": row.get("phase", ""),
                "split": row.get("split", ""),
                "panel_png_path": row.get("panel_png_path", ""),
                "topology_v1_panel_json_path": row.get("topology_v1_panel_json_path", ""),
                "v1_5_candidate_score": row.get("v1_5_candidate_score", ""),
                "v1_5_candidate_bucket": row.get("v1_5_candidate_bucket", ""),
                "known_policy_decision": row.get("topology_panel_v1_policy_decision", ""),
                "known_review_label": row.get("topology_panel_v1_review_label", ""),
                "consensus_label": label,
                "consensus_decision": consensus_decision(label, confidence),
                "consensus_confidence": confidence,
                "agreement_count": 1,
                "agent_count": 1,
                "reason": f"policy_rule completed missing row: {reason}",
            }
        )
        added += 1

    write_csv(paths["agent_outputs"], agent_rows, AGENT_FIELDS)
    write_csv(paths["consensus"], consensus_rows, CONSENSUS_FIELDS)
    summary = {
        "candidate_csv": rel(args.candidates),
        "agent_outputs": rel(paths["agent_outputs"]),
        "consensus": rel(paths["consensus"]),
        "candidate_rows": len(candidates),
        "final_agent_rows": len(agent_rows),
        "final_consensus_rows": len(consensus_rows),
        "policy_completed_rows": added,
        "decision_counts": dict(Counter(row["consensus_decision"] for row in consensus_rows)),
        "label_counts": dict(Counter(row["consensus_label"] for row in consensus_rows)),
        "agent_counts": dict(Counter(row["agent"] for row in agent_rows)),
    }
    write_json(paths["summary"], summary)
    report_lines = [
        "# Agentic Annotation Policy Completion Report",
        "",
        f"- candidate rows: {len(candidates)}",
        f"- final consensus rows: {len(consensus_rows)}",
        f"- policy completed rows: {added}",
        "",
        "## Decision Counts",
        "",
    ]
    for key, value in summary["decision_counts"].items():
        report_lines.append(f"- {key}: {value}")
    report_lines.extend(["", "## Agent Counts", ""])
    for key, value in summary["agent_counts"].items():
        report_lines.append(f"- {key}: {value}")
    paths["report"].write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Policy completed rows: {added}")
    print(f"Final consensus rows: {len(consensus_rows)}")
    print(f"Wrote: {rel(paths['summary'])}")
    print(f"Wrote: {rel(paths['report'])}")


if __name__ == "__main__":
    main()
