"""Build presentation-ready figures for Topology Panel v1."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data_index"
DOCS = ROOT / "docs"
DOC_FIGURES = DOCS / "figures"
OUTPUT_FIGURES = ROOT / "outputs" / "figures"
FIGURE_INDEX = DOCS / "topology_panel_v1_figures.md"
EXPERIMENT_RECORDS = ROOT / "experiment_records.md"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": False,
        "figure.dpi": 140,
        "savefig.dpi": 220,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    }
)


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ensure_dirs() -> None:
    DOC_FIGURES.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)


def save_figure(fig: plt.Figure, stem: str) -> List[Path]:
    paths = [
        DOC_FIGURES / f"{stem}.png",
        DOC_FIGURES / f"{stem}.svg",
    ]
    for path in paths:
        fig.savefig(path, bbox_inches="tight", facecolor="white")
    for path in paths:
        shutil.copy2(path, OUTPUT_FIGURES / path.name)
    plt.close(fig)
    return paths


def build_mae_bar_chart() -> List[Path]:
    rows = [row for row in read_csv(DATA_INDEX / "topology_panel_v1_experiment_table.csv") if row["category"] == "model"]
    order = [
        "doubao_v1",
        "doubao_prompt_v2",
        "doubao_prompt_v3",
        "doubao_prompt_v3_image_1024",
        "doubao_prompt_v3_tile2x2",
        "doubao_prompt_v3_tile2x2_overlap10",
    ]
    labels = {
        "doubao_v1": "v1\n512",
        "doubao_prompt_v2": "v2\n512",
        "doubao_prompt_v3": "v3\n512",
        "doubao_prompt_v3_image_1024": "v3\n1024",
        "doubao_prompt_v3_tile2x2": "v3\ntile2x2",
        "doubao_prompt_v3_tile2x2_overlap10": "v3\ntile2x2\nov10",
    }
    by_id = {row["experiment_id"]: row for row in rows}
    rows = [by_id[item] for item in order]
    x = list(range(len(rows)))
    colors = ["#7b8da0", "#5d9cec", "#48a868", "#b07cc6", "#f0a43a", "#d9534f"]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), gridspec_kw={"width_ratios": [1.2, 1.2, 0.9]})
    metric_specs = [
        ("node_mae", "Node MAE", axes[0]),
        ("edge_mae", "Edge MAE", axes[1]),
        ("net_mae", "Net MAE", axes[2]),
    ]
    for metric, title, ax in metric_specs:
        values = [float(row[metric]) for row in rows]
        bars = ax.bar(x, values, color=colors, edgecolor="#30343b", linewidth=0.6)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels([labels[row["experiment_id"]] for row in rows], rotation=0)
        ax.set_ylabel("MAE")
        ax.grid(axis="y", alpha=0.25)
        best_idx = values.index(min(values))
        bars[best_idx].set_edgecolor("#111111")
        bars[best_idx].set_linewidth(1.8)
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.1f}" if value >= 10 else f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=7,
                color="#20242b",
            )
    fig.suptitle("Topology Panel v1 Model MAE Comparison", fontsize=14, fontweight="bold")
    fig.text(
        0.5,
        -0.02,
        "Current best for node/edge: Doubao prompt v3 + tile2x2 + 10% overlap. Net count is already stable after prompt v3.",
        ha="center",
        fontsize=9,
        color="#333333",
    )
    return save_figure(fig, "topology_panel_v1_mae_bar_chart")


def build_delta_heatmap() -> Tuple[List[Path], Path]:
    rows = read_csv(DATA_INDEX / "topology_panel_v1_image_input_delta_analysis.csv")
    delta_columns = [
        "delta_overlap10_minus_512_node_error",
        "delta_overlap10_minus_512_edge_error",
        "delta_overlap10_minus_512_net_error",
    ]
    heat = [[float(row[col]) for col in delta_columns] for row in rows]
    labels = [f"{i + 1:02d} {row['phase']}/{row['split']}" for i, row in enumerate(rows)]
    columns = ["node delta", "edge delta", "net delta"]

    fig, ax = plt.subplots(figsize=(7.2, 7.8))
    max_abs = max(abs(value) for row in heat for value in row)
    image = ax.imshow(heat, cmap="RdYlGn_r", vmin=-max_abs, vmax=max_abs, aspect="auto")
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Delta absolute error vs whole-image v3 512")
    ax.set_xticks(list(range(len(columns))))
    ax.set_xticklabels(columns)
    ax.set_yticks(list(range(len(labels))))
    ax.set_yticklabels(labels)
    for y, row in enumerate(heat):
        for x, value in enumerate(row):
            ax.text(x, y, f"{value:.0f}", ha="center", va="center", fontsize=8, color="#111827")
    ax.set_xticks([i - 0.5 for i in range(1, len(columns))], minor=True)
    ax.set_yticks([i - 0.5 for i in range(1, len(labels))], minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_title("Per-Sample Delta: overlap10 vs whole-image v3 512")
    ax.set_xlabel("Metric")
    ax.set_ylabel("Panel sample")
    ax.text(
        0,
        -0.12,
        "Negative values mean overlap10 reduced absolute error; positive values mean regression.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="#333333",
    )
    paths = save_figure(fig, "topology_panel_v1_per_sample_delta_heatmap")

    mapping_path = DOC_FIGURES / "topology_panel_v1_per_sample_delta_heatmap_labels.csv"
    with mapping_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "heatmap_label",
                "panel_id",
                "phase",
                "split",
                "auto_decision",
                "overlap10_gain_pattern",
                "overlap10_regression_metrics",
            ],
        )
        writer.writeheader()
        for label, row in zip(labels, rows):
            writer.writerow(
                {
                    "heatmap_label": label,
                    "panel_id": row["panel_id"],
                    "phase": row["phase"],
                    "split": row["split"],
                    "auto_decision": row["auto_decision"],
                    "overlap10_gain_pattern": row["overlap10_gain_pattern"],
                    "overlap10_regression_metrics": row.get("overlap10_regression_metrics", ""),
                }
            )
    shutil.copy2(mapping_path, OUTPUT_FIGURES / mapping_path.name)
    return paths, mapping_path


def add_box(ax: plt.Axes, x: float, y: float, w: float, h: float, text: str, color: str) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        facecolor=color,
        edgecolor="#27313f",
        linewidth=1.0,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color="#101820")


def add_arrow(ax: plt.Axes, start: Tuple[float, float], end: Tuple[float, float]) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#334155", "shrinkA": 4, "shrinkB": 4},
    )


def build_data_cleaning_flow_chart() -> List[Path]:
    release = read_json(DATA_INDEX / "topology_panel_v1_release_summary.json")
    abandoned = read_json(DATA_INDEX / "topology_panel_v1_1_abandoned_policy_summary.json")
    reviewed = release["reviewed_sample_rows"]
    partitions = release["partition_counts"]
    badcases = release["badcase_reason_counts"]
    active_routes = abandoned["active_next_route_counts"]

    fig, ax = plt.subplots(figsize=(13.2, 6.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    add_box(ax, 0.3, 3.0, 1.7, 1.0, f"Reviewed\nsamples\n{reviewed}", "#dbeafe")
    add_box(ax, 2.6, 4.8, 1.9, 0.9, f"Clean\nbaseline\n{partitions['clean_baseline']}", "#dcfce7")
    add_box(ax, 2.6, 3.0, 1.9, 0.9, f"Excluded\nbadcase\n{partitions['excluded_badcase']}", "#fee2e2")
    add_box(ax, 2.6, 1.2, 1.9, 0.9, f"Improvement\ntarget\n{partitions['improvement_target']}", "#fef3c7")
    add_box(ax, 2.6, 0.1, 1.9, 0.75, f"Unreviewed\n{partitions['unreviewed']}", "#e5e7eb")

    add_box(ax, 5.0, 4.8, 1.9, 0.9, "Benchmark\nJSONL\n14", "#bbf7d0")
    add_box(ax, 7.3, 4.8, 1.9, 0.9, "Evaluator\nProtocol\nv1", "#bfdbfe")
    add_box(ax, 9.6, 4.8, 1.9, 0.9, "Best model\nbaseline\nDoubao v3", "#fecaca")

    add_box(
        ax,
        5.0,
        2.7,
        2.0,
        1.35,
        "Badcase reasons\n"
        f"multi-subfigure {badcases['multi_subfigure_badcase']}\n"
        f"bad geometry {badcases['bad_geometry']}\n"
        f"not topology {badcases['not_topology_target']}",
        "#ffe4e6",
    )
    add_box(ax, 5.0, 1.0, 2.0, 0.9, f"Abandoned\nstill-fragmented\n{abandoned['abandoned_rows']}", "#fed7aa")
    add_box(ax, 7.5, 1.0, 2.1, 0.9, f"Active v1.1\ncandidates\n{abandoned['active_improvement_rows']}", "#fde68a")
    add_box(
        ax,
        9.9,
        1.0,
        1.8,
        0.9,
        f"Next routes\nterminal {active_routes['terminal_anchor_module']}\nover-connected {active_routes['over_connected_repair']}",
        "#fef9c3",
    )

    add_arrow(ax, (2.0, 3.5), (2.6, 5.25))
    add_arrow(ax, (2.0, 3.5), (2.6, 3.45))
    add_arrow(ax, (2.0, 3.5), (2.6, 1.65))
    add_arrow(ax, (2.0, 3.5), (2.6, 0.5))
    add_arrow(ax, (4.5, 5.25), (5.0, 5.25))
    add_arrow(ax, (6.9, 5.25), (7.3, 5.25))
    add_arrow(ax, (9.2, 5.25), (9.6, 5.25))
    add_arrow(ax, (4.5, 3.45), (5.0, 3.35))
    add_arrow(ax, (4.5, 1.65), (5.0, 1.45))
    add_arrow(ax, (7.0, 1.45), (7.5, 1.45))
    add_arrow(ax, (9.6, 1.45), (9.9, 1.45))

    ax.text(
        0.3,
        6.45,
        "Topology Panel v1 Data Cleaning and Release Flow",
        fontsize=16,
        fontweight="bold",
        color="#111827",
    )
    ax.text(
        0.3,
        6.1,
        "Formal v1 score uses only the 14 clean baseline rows; badcases and v1.1 candidates remain outside the formal baseline.",
        fontsize=10,
        color="#374151",
    )
    return save_figure(fig, "topology_panel_v1_data_cleaning_flow")


def write_figure_index(paths: Dict[str, List[Path]], label_mapping: Path) -> None:
    lines = [
        "# Topology Panel v1 图表索引",
        "",
        "日期：2026-07-10",
        "",
        "本页汇总当前答辩和阶段报告可直接使用的图表。图中主要标签使用英文，以保证跨平台字体渲染稳定。",
        "",
        "## 1. MAE 柱状图",
        "",
        "![MAE bar chart](figures/topology_panel_v1_mae_bar_chart.png)",
        "",
        "- 对比 Doubao v1/v2/v3、1024 整图、tile2x2、tile2x2 overlap10。",
        "- 当前最佳 node/edge MAE：`doubao_prompt_v3_tile2x2_overlap10`。",
        "",
        "## 2. Per-Sample Delta 热力图",
        "",
        "![Per-sample delta heatmap](figures/topology_panel_v1_per_sample_delta_heatmap.png)",
        "",
        "- 数值含义：`overlap10 absolute error - whole-image v3 512 absolute error`。",
        "- 负数代表 overlap10 改善，正数代表退化。",
        f"- 样本标签映射：`{label_mapping.relative_to(ROOT).as_posix()}`。",
        "",
        "## 3. 数据清洗流转图",
        "",
        "![Data cleaning flow](figures/topology_panel_v1_data_cleaning_flow.png)",
        "",
        "- 展示 reviewed samples 到 clean baseline、excluded badcase、improvement target、benchmark JSONL 与 best model baseline 的关系。",
        "- 强调正式 v1 score 只使用 14 条 clean baseline。",
        "",
        "## 文件清单",
        "",
    ]
    for figure_paths in paths.values():
        for path in figure_paths:
            lines.append(f"- `{path.relative_to(ROOT).as_posix()}`")
    lines.append(f"- `{label_mapping.relative_to(ROOT).as_posix()}`")
    lines.append("")
    FIGURE_INDEX.write_text("\n".join(lines), encoding="utf-8")


def append_experiment_record() -> None:
    marker = "## 2026-07-10 Topology Panel v1 Figures"
    text = EXPERIMENT_RECORDS.read_text(encoding="utf-8")
    if marker in text:
        return
    section = f"""{marker}

- Generated presentation-ready figures for Topology Panel v1.
- Figure outputs are mirrored to `docs/figures/` and `outputs/figures/`.
- Figures:
  - `docs/figures/topology_panel_v1_mae_bar_chart.png`
  - `docs/figures/topology_panel_v1_per_sample_delta_heatmap.png`
  - `docs/figures/topology_panel_v1_data_cleaning_flow.png`
- Added figure index:
  - `docs/topology_panel_v1_figures.md`
- Design note: figure labels use English to avoid cross-platform Chinese font rendering issues.
"""
    EXPERIMENT_RECORDS.write_text(text.rstrip() + "\n\n" + section, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    paths: Dict[str, List[Path]] = {}
    paths["mae"] = build_mae_bar_chart()
    heatmap_paths, mapping_path = build_delta_heatmap()
    paths["delta_heatmap"] = heatmap_paths
    paths["flow"] = build_data_cleaning_flow_chart()
    write_figure_index(paths, mapping_path)
    append_experiment_record()
    for figure_paths in paths.values():
        for path in figure_paths:
            print(f"Wrote: {path.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {mapping_path.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {FIGURE_INDEX.relative_to(ROOT).as_posix()}")
    print(f"Mirrored to: {OUTPUT_FIGURES.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
