"""Update docs with the frozen Topology Panel v1 best model baseline."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BEST_SECTION_TITLE = "## Current Best Model Baseline"
BEST_SECTION = """## Current Best Model Baseline

As of 2026-07-10, the current best real-model count-level baseline for Topology Panel v1 is:

- Method: `doubao_prompt_v3_tile2x2_overlap10`
- Model/input: Doubao, prompt v3, `tile2x2 + 10% overlap`
- Aggregation: `node=sum; edge=sum; net=mean_clamped3`
- Scope: count-level synthetic graph baseline, not full topology graph reconstruction
- Rows: 14
- Prediction graph valid rate: 1.0
- MAE: node `362.642857`, edge `687.857143`, net `0.857143`

Stable entry files:

```text
data_index/topology_panel_v1_best_model_predictions.jsonl
data_index/topology_panel_v1_best_model_eval_summary.json
data_index/topology_panel_v1_best_model_eval_details.csv
data_index/topology_panel_v1_best_model_eval_errors.csv
data_index/topology_panel_v1_best_model_manifest.csv
data_index/topology_panel_v1_best_model_summary.json
docs/topology_panel_v1_best_model_baseline.md
```

Related experiment analysis:

```text
docs/topology_panel_v1_model_experiment_summary.md
docs/topology_panel_v1_image_input_delta_analysis.md
docs/topology_panel_v1_tile2x2_overlap10_auto_judge_report.md
data_index/topology_panel_v1_model_leaderboard.csv
```
"""

RELEASE_SECTION_TITLE = "## 当前最佳模型基线 / Current Best Model Baseline"
RELEASE_SECTION = """## 当前最佳模型基线 / Current Best Model Baseline

截至 2026-07-10，Topology Panel v1 当前最佳真实模型 count-level baseline 已固化为：

- 方法：`doubao_prompt_v3_tile2x2_overlap10`
- 模型与输入：Doubao，prompt v3，`tile2x2 + 10% overlap`
- 聚合规则：`node=sum; edge=sum; net=mean_clamped3`
- 适用范围：count-level synthetic graph baseline，不代表完整 topology graph reconstruction
- 样本数：14
- prediction graph valid rate：1.0
- MAE：node `362.642857`，edge `687.857143`，net `0.857143`

正式入口文件：

```text
data_index/topology_panel_v1_best_model_predictions.jsonl
data_index/topology_panel_v1_best_model_eval_summary.json
data_index/topology_panel_v1_best_model_eval_details.csv
data_index/topology_panel_v1_best_model_eval_errors.csv
data_index/topology_panel_v1_best_model_manifest.csv
data_index/topology_panel_v1_best_model_summary.json
docs/topology_panel_v1_best_model_baseline.md
```

这个 best baseline 只用于模型实验结果的统一引用；数据集边界仍然以 14 条 `Topology Panel v1 clean baseline` 为准。
"""

EXPERIMENT_RECORD = """## 2026-07-10 Frozen Current Best Model Baseline

- Frozen current best real-model count-level baseline for Topology Panel v1.
- Method: `doubao_prompt_v3_tile2x2_overlap10`.
- Input: Doubao prompt v3 with tile2x2 + 10% overlap.
- Aggregation: node=sum; edge=sum; net=mean_clamped3.
- Scope: count-level synthetic graph baseline, not full topology graph reconstruction.
- Rows: 14.
- Prediction graph valid rate: 1.0.
- MAE:
  - node_count: 362.642857.
  - edge_count: 687.857143.
  - net_count: 0.857143.
- Main outputs:
  - `data_index/topology_panel_v1_best_model_predictions.jsonl`
  - `data_index/topology_panel_v1_best_model_eval_summary.json`
  - `data_index/topology_panel_v1_best_model_eval_details.csv`
  - `data_index/topology_panel_v1_best_model_eval_errors.csv`
  - `data_index/topology_panel_v1_best_model_manifest.csv`
  - `data_index/topology_panel_v1_best_model_summary.json`
  - `docs/topology_panel_v1_best_model_baseline.md`
"""


def replace_or_append(path: Path, title: str, section: str) -> None:
    text = path.read_text(encoding="utf-8")
    if title in text:
        start = text.index(title)
        next_header = text.find("\n## ", start + 1)
        if next_header == -1:
            text = text[:start].rstrip() + "\n\n" + section.rstrip() + "\n"
        else:
            text = text[:start].rstrip() + "\n\n" + section.rstrip() + "\n\n" + text[next_header + 1 :].lstrip()
    else:
        text = text.rstrip() + "\n\n" + section.rstrip() + "\n"
    path.write_text(text, encoding="utf-8")


def append_once(path: Path, marker: str, section: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        path.write_text(text.rstrip() + "\n\n" + section.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    replace_or_append(ROOT / "README.md", BEST_SECTION_TITLE, BEST_SECTION)
    replace_or_append(ROOT / "docs" / "topology_panel_v1_release_status.md", RELEASE_SECTION_TITLE, RELEASE_SECTION)
    append_once(ROOT / "experiment_records.md", "## 2026-07-10 Frozen Current Best Model Baseline", EXPERIMENT_RECORD)
    print("Updated README, release status, and experiment records.")


if __name__ == "__main__":
    main()
