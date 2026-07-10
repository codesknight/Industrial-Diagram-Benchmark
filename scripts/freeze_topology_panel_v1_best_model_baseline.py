"""Freeze the current best Topology Panel v1 model baseline entrypoints."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DOCS_DIR = ROOT / "docs"

BEST_ID = "topology_panel_v1_best_model_baseline_2026-07-10"
BEST_METHOD = "doubao_prompt_v3_tile2x2_overlap10"

SOURCE_FILES = {
    "predictions": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions.jsonl",
    "eval_summary": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_summary.json",
    "eval_report": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_report.md",
    "eval_details": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_details.csv",
    "eval_errors": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_errors.csv",
    "adapter_summary": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_summary.json",
    "adapter_report": INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_report.md",
}

TARGET_FILES = {
    "predictions": INDEX_DIR / "topology_panel_v1_best_model_predictions.jsonl",
    "eval_summary": INDEX_DIR / "topology_panel_v1_best_model_eval_summary.json",
    "eval_report": INDEX_DIR / "topology_panel_v1_best_model_eval_report.md",
    "eval_details": INDEX_DIR / "topology_panel_v1_best_model_eval_details.csv",
    "eval_errors": INDEX_DIR / "topology_panel_v1_best_model_eval_errors.csv",
    "adapter_summary": INDEX_DIR / "topology_panel_v1_best_model_adapter_summary.json",
    "adapter_report": INDEX_DIR / "topology_panel_v1_best_model_adapter_report.md",
    "manifest": INDEX_DIR / "topology_panel_v1_best_model_manifest.csv",
    "summary": INDEX_DIR / "topology_panel_v1_best_model_summary.json",
    "report": DOCS_DIR / "topology_panel_v1_best_model_baseline.md",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def copy_sources() -> None:
    for key, source in SOURCE_FILES.items():
        target = TARGET_FILES[key]
        if not source.exists():
            raise SystemExit(f"Missing source file: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def write_manifest() -> List[Dict[str, object]]:
    eval_summary = load_json(TARGET_FILES["eval_summary"])
    adapter_summary = load_json(TARGET_FILES["adapter_summary"])
    row = {
        "best_id": BEST_ID,
        "method_id": BEST_METHOD,
        "provider": adapter_summary.get("provider", "doubao"),
        "model": adapter_summary.get("model", ""),
        "prompt_version": adapter_summary.get("prompt_version", "v3"),
        "input_version": adapter_summary.get("input_version", "tile2x2_overlap10_512px_250k"),
        "aggregation": "node=sum;edge=sum;net=mean_clamped3",
        "prediction_rows": eval_summary.get("prediction_rows", ""),
        "prediction_valid_rate": eval_summary.get("graph_valid_rate", {}).get("prediction", ""),
        "node_mae": eval_summary.get("count_errors", {}).get("node_count", {}).get("mae", ""),
        "edge_mae": eval_summary.get("count_errors", {}).get("edge_count", {}).get("mae", ""),
        "net_mae": eval_summary.get("count_errors", {}).get("net_count", {}).get("mae", ""),
        "predictions": rel(TARGET_FILES["predictions"]),
        "eval_summary": rel(TARGET_FILES["eval_summary"]),
        "eval_details": rel(TARGET_FILES["eval_details"]),
        "eval_errors": rel(TARGET_FILES["eval_errors"]),
        "report": rel(TARGET_FILES["report"]),
    }
    with TARGET_FILES["manifest"].open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)
    return [row]


def write_summary(manifest_rows: List[Dict[str, object]]) -> None:
    eval_summary = load_json(TARGET_FILES["eval_summary"])
    summary = {
        "best_id": BEST_ID,
        "method_id": BEST_METHOD,
        "status": "current_best_count_level_model_baseline",
        "important_scope_note": "This is a count-level synthetic-graph baseline, not full topology graph reconstruction.",
        "source_files": {key: rel(value) for key, value in SOURCE_FILES.items()},
        "target_files": {key: rel(value) for key, value in TARGET_FILES.items()},
        "prediction_rows": count_jsonl(TARGET_FILES["predictions"]),
        "prediction_valid_rate": eval_summary.get("graph_valid_rate", {}).get("prediction", ""),
        "count_errors": eval_summary.get("count_errors", {}),
        "manifest": manifest_rows,
    }
    TARGET_FILES["summary"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report() -> None:
    summary = load_json(TARGET_FILES["summary"])
    count_errors = summary["count_errors"]
    lines = [
        "# Topology Panel v1 Best Model Baseline",
        "",
        "日期：2026-07-10",
        "",
        "## 结论",
        "",
        "当前 Topology Panel v1 的最佳真实模型 count-level baseline 固化为：",
        "",
        "- Model：Doubao",
        "- Prompt：v3",
        "- Image input：tile2x2 + 10% overlap",
        "- Aggregation：node=sum；edge=sum；net=mean_clamped3",
        "- Scope：count-level synthetic graph baseline，不是完整 topology graph reconstruction",
        "",
        "## 指标",
        "",
        f"- prediction rows：{summary['prediction_rows']}",
        f"- prediction graph valid rate：{summary['prediction_valid_rate']}",
        f"- node_count MAE：{count_errors['node_count']['mae']}",
        f"- edge_count MAE：{count_errors['edge_count']['mae']}",
        f"- net_count MAE：{count_errors['net_count']['mae']}",
        "",
        "## 统一入口文件",
        "",
        f"- predictions：`{rel(TARGET_FILES['predictions'])}`",
        f"- eval summary：`{rel(TARGET_FILES['eval_summary'])}`",
        f"- eval details：`{rel(TARGET_FILES['eval_details'])}`",
        f"- eval errors：`{rel(TARGET_FILES['eval_errors'])}`",
        f"- best manifest：`{rel(TARGET_FILES['manifest'])}`",
        f"- best summary：`{rel(TARGET_FILES['summary'])}`",
        "",
        "## 来源实验",
        "",
        "该 best baseline 来源于 `doubao_prompt_v3_tile2x2_overlap10`，详见：",
        "",
        "- `docs/topology_panel_v1_model_experiment_summary.md`",
        "- `docs/topology_panel_v1_image_input_delta_analysis.md`",
        "- `docs/topology_panel_v1_tile2x2_overlap10_auto_judge_report.md`",
        "- `data_index/topology_panel_v1_model_leaderboard.csv`",
    ]
    TARGET_FILES["report"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    copy_sources()
    manifest_rows = write_manifest()
    write_summary(manifest_rows)
    write_report()
    print(f"Frozen best baseline: {BEST_METHOD}")
    for key in ["predictions", "eval_summary", "eval_details", "eval_errors", "manifest", "summary", "report"]:
        print(f"Wrote: {rel(TARGET_FILES[key])}")


if __name__ == "__main__":
    main()
