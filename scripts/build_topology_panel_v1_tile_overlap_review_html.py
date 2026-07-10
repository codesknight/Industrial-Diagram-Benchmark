"""Build an HTML review page for tile2x2 vs overlap10 input experiments."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_BENCHMARK = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_TILE_MANIFEST = INDEX_DIR / "topology_panel_v1_tile2x2_benchmark_manifest.jsonl"
DEFAULT_OVERLAP_MANIFEST = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_benchmark_manifest.jsonl"
DEFAULT_BASE_DETAILS = INDEX_DIR / "topology_panel_v1_doubao_v3_model_predictions_eval_details.csv"
DEFAULT_TILE_DETAILS = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_clamped_panel_predictions_eval_details.csv"
DEFAULT_OVERLAP_DETAILS = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_panel_predictions_eval_details.csv"
DEFAULT_TILE_PREDICTIONS = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_tile_predictions.jsonl"
DEFAULT_OVERLAP_PREDICTIONS = INDEX_DIR / "topology_panel_v1_doubao_v3_tile2x2_overlap10_tile_predictions.jsonl"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_review.html"
DEFAULT_CSV = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_review_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_tile2x2_overlap10_review_summary.json"


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rel_asset_path(path_value: str, html_path: Path) -> str:
    if not path_value:
        return ""
    raw = Path(path_value)
    target = raw if raw.is_absolute() else (ROOT / raw).resolve()
    try:
        rel = os.path.relpath(target, html_path.parent.resolve())
    except ValueError:
        rel = target.as_posix()
    return quote(rel.replace("\\", "/"), safe="/:.")


def as_float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except ValueError:
        return 0.0


def as_int(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def source_panel_id(tile_panel_id: str) -> str:
    return tile_panel_id.split("#tile_", 1)[0] if "#tile_" in tile_panel_id else tile_panel_id


def group_tiles(rows: List[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        input_info = row.get("input", {})
        if not isinstance(input_info, dict):
            input_info = {}
        panel_id = str(input_info.get("source_panel_id") or source_panel_id(str(row.get("panel_id", ""))))
        grouped[panel_id].append(row)
    for tiles in grouped.values():
        tiles.sort(key=lambda item: (as_int(item.get("input", {}).get("tile_row") if isinstance(item.get("input"), dict) else 0), as_int(item.get("input", {}).get("tile_col") if isinstance(item.get("input"), dict) else 0)))
    return grouped


def tile_prediction_counts(rows: List[Dict[str, object]]) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}
    for row in rows:
        metadata = row.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        counts[str(row.get("panel_id", ""))] = {
            "node": as_int(metadata.get("model_node_count", 0)),
            "edge": as_int(metadata.get("model_edge_count", 0)),
            "net": as_int(metadata.get("model_net_count", 0)),
        }
    return counts


def score_delta(before: Dict[str, str], after: Dict[str, str], metric: str) -> float:
    return as_float(after, f"{metric}_count_abs_error") - as_float(before, f"{metric}_count_abs_error")


def classify(base: Dict[str, str], tile: Dict[str, str], overlap: Dict[str, str]) -> Dict[str, object]:
    edge_delta = score_delta(tile, overlap, "edge")
    node_delta = score_delta(tile, overlap, "node")
    net_delta = score_delta(tile, overlap, "net")
    edge_vs_base = score_delta(base, overlap, "edge")
    node_vs_base = score_delta(base, overlap, "node")
    tags: List[str] = []
    if edge_delta <= -10:
        tags.append("overlap_edge_benefit")
    if node_delta <= -10:
        tags.append("overlap_node_benefit")
    if edge_delta >= 10:
        tags.append("possible_duplicate_edges")
    if node_delta >= 10:
        tags.append("possible_duplicate_nodes")
    if net_delta >= 1:
        tags.append("possible_duplicate_nets")
    if edge_vs_base < 0 and node_vs_base < 0:
        tags.append("better_than_whole_image")
    if not tags:
        tags.append("neutral_or_small_delta")
    return {
        "edge_delta_overlap_minus_tile": edge_delta,
        "node_delta_overlap_minus_tile": node_delta,
        "net_delta_overlap_minus_tile": net_delta,
        "edge_delta_overlap_minus_base": edge_vs_base,
        "node_delta_overlap_minus_base": node_vs_base,
        "tags": tags,
    }


def metric_block(label: str, row: Dict[str, str]) -> str:
    return f"""
      <div class="metric-block">
        <div class="metric-title">{html.escape(label)}</div>
        <div>pred n/e/net: <b>{html.escape(row.get('prediction_node_count', ''))}</b> / <b>{html.escape(row.get('prediction_edge_count', ''))}</b> / <b>{html.escape(row.get('prediction_net_count', ''))}</b></div>
        <div>abs err n/e/net: <b>{html.escape(row.get('node_count_abs_error', ''))}</b> / <b>{html.escape(row.get('edge_count_abs_error', ''))}</b> / <b>{html.escape(row.get('net_count_abs_error', ''))}</b></div>
      </div>
    """


def render_tile_grid(tiles: List[Dict[str, object]], counts: Dict[str, Dict[str, int]], html_path: Path) -> str:
    cards: List[str] = []
    for tile in tiles:
        input_info = tile.get("input", {})
        if not isinstance(input_info, dict):
            input_info = {}
        tile_panel_id = str(tile.get("panel_id", ""))
        c = counts.get(tile_panel_id, {"node": 0, "edge": 0, "net": 0})
        image_src = rel_asset_path(str(input_info.get("image_path", "")), html_path)
        tile_id = html.escape(str(input_info.get("tile_id", "")))
        bbox = html.escape(json.dumps(input_info.get("tile_bbox_xyxy", []), ensure_ascii=False))
        cards.append(
            f"""
            <div class="tile-card">
              <div class="tile-head">{tile_id} · n/e/net {c['node']}/{c['edge']}/{c['net']}</div>
              <img src="{image_src}" loading="lazy" />
              <div class="tile-bbox">{bbox}</div>
            </div>
            """
        )
    return '<div class="tile-grid">' + "\n".join(cards) + "</div>"


def build_rows(args: argparse.Namespace) -> List[Dict[str, object]]:
    benchmark = load_jsonl(args.benchmark)
    base_details = {row["panel_id"]: row for row in load_csv(args.base_details)}
    tile_details = {row["panel_id"]: row for row in load_csv(args.tile_details)}
    overlap_details = {row["panel_id"]: row for row in load_csv(args.overlap_details)}
    tile_groups = group_tiles(load_jsonl(args.tile_manifest))
    overlap_groups = group_tiles(load_jsonl(args.overlap_manifest))
    tile_counts = tile_prediction_counts(load_jsonl(args.tile_predictions))
    overlap_counts = tile_prediction_counts(load_jsonl(args.overlap_predictions))

    review_rows: List[Dict[str, object]] = []
    for record in benchmark:
        panel_id = str(record.get("panel_id", ""))
        base = base_details[panel_id]
        tile = tile_details[panel_id]
        overlap = overlap_details[panel_id]
        deltas = classify(base, tile, overlap)
        review_rows.append(
            {
                "panel_id": panel_id,
                "split": record.get("split", ""),
                "phase": record.get("phase", ""),
                "image_path": record.get("input", {}).get("image_path", "") if isinstance(record.get("input"), dict) else "",
                "reference_node_count": base.get("reference_node_count", ""),
                "reference_edge_count": base.get("reference_edge_count", ""),
                "reference_net_count": base.get("reference_net_count", ""),
                "base": base,
                "tile": tile,
                "overlap": overlap,
                "tile_records": tile_groups.get(panel_id, []),
                "overlap_records": overlap_groups.get(panel_id, []),
                "tile_counts": tile_counts,
                "overlap_counts": overlap_counts,
                **deltas,
            }
        )
    review_rows.sort(key=lambda row: (float(row["edge_delta_overlap_minus_tile"]), float(row["node_delta_overlap_minus_tile"])))
    return review_rows


def render_html(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    cards: List[str] = []
    for index, row in enumerate(rows, start=1):
        tags = row["tags"]
        tag_html = "".join(f'<span class="tag {html.escape(tag)}">{html.escape(tag)}</span>' for tag in tags)
        image_src = rel_asset_path(str(row["image_path"]), args.output)
        cards.append(
            f"""
            <section class="panel-card" id="row-{index}">
              <div class="panel-header">
                <div>
                  <h2>{index}. {html.escape(str(row['panel_id']))}</h2>
                  <div class="subtle">{html.escape(str(row['phase']))} · {html.escape(str(row['split']))}</div>
                </div>
                <div class="tags">{tag_html}</div>
              </div>
              <div class="delta-strip">
                <div>overlap - tile edge err: <b>{row['edge_delta_overlap_minus_tile']:+.1f}</b></div>
                <div>overlap - tile node err: <b>{row['node_delta_overlap_minus_tile']:+.1f}</b></div>
                <div>overlap - tile net err: <b>{row['net_delta_overlap_minus_tile']:+.1f}</b></div>
                <div>overlap - whole edge err: <b>{row['edge_delta_overlap_minus_base']:+.1f}</b></div>
              </div>
              <div class="metrics">
                <div class="ref">reference n/e/net: <b>{html.escape(str(row['reference_node_count']))}</b> / <b>{html.escape(str(row['reference_edge_count']))}</b> / <b>{html.escape(str(row['reference_net_count']))}</b></div>
                {metric_block('whole v3@512', row['base'])}
                {metric_block('tile2x2', row['tile'])}
                {metric_block('tile2x2 overlap10', row['overlap'])}
              </div>
              <div class="visual-grid">
                <div class="original">
                  <div class="section-title">Original Panel</div>
                  <img src="{image_src}" loading="lazy" />
                </div>
                <div>
                  <div class="section-title">Tile2x2</div>
                  {render_tile_grid(row['tile_records'], row['tile_counts'], args.output)}
                </div>
                <div>
                  <div class="section-title">Tile2x2 Overlap10</div>
                  {render_tile_grid(row['overlap_records'], row['overlap_counts'], args.output)}
                </div>
              </div>
              <div class="review-controls">
                <label>review_label
                  <select data-field="review_label">
                    <option value=""></option>
                    <option value="overlap_benefit">overlap_benefit</option>
                    <option value="duplicate_counting">duplicate_counting</option>
                    <option value="boundary_cut_issue">boundary_cut_issue</option>
                    <option value="needs_3x3">needs_3x3</option>
                    <option value="needs_adaptive_crop">needs_adaptive_crop</option>
                    <option value="keep_tile2x2">keep_tile2x2</option>
                    <option value="prefer_whole_image">prefer_whole_image</option>
                  </select>
                </label>
                <label>note <input data-field="review_note" placeholder="optional note" /></label>
              </div>
            </section>
            """
        )

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Topology Panel v1 Tile2x2 Overlap Review</title>
  <style>
    body {{ margin: 0; font-family: Arial, "Microsoft YaHei", sans-serif; background: #f5f5f2; color: #202124; }}
    header {{ position: sticky; top: 0; z-index: 10; background: #202124; color: #fff; padding: 12px 18px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }}
    h1 {{ font-size: 18px; margin: 0; }}
    button {{ border: 1px solid #888; background: #fff; color: #111; padding: 7px 10px; cursor: pointer; }}
    main {{ padding: 18px; }}
    .panel-card {{ background: #fff; border: 1px solid #d8d8d8; margin-bottom: 18px; padding: 14px; }}
    .panel-header {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }}
    h2 {{ font-size: 15px; margin: 0 0 4px; word-break: break-all; }}
    .subtle {{ color: #666; font-size: 12px; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }}
    .tag {{ font-size: 12px; border: 1px solid #bbb; padding: 3px 6px; background: #f0f0f0; }}
    .overlap_edge_benefit, .overlap_node_benefit, .better_than_whole_image {{ background: #e6f4ea; border-color: #7dbb86; }}
    .possible_duplicate_edges, .possible_duplicate_nodes, .possible_duplicate_nets {{ background: #fdecea; border-color: #e2847d; }}
    .delta-strip {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 12px 0; font-size: 13px; }}
    .delta-strip div, .metric-block, .ref {{ background: #f7f7f7; border: 1px solid #e1e1e1; padding: 8px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; font-size: 12px; }}
    .metric-title, .section-title {{ font-weight: 700; margin-bottom: 5px; }}
    .visual-grid {{ display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 12px; align-items: start; }}
    img {{ max-width: 100%; display: block; background: #fafafa; border: 1px solid #ddd; }}
    .original img {{ max-height: 620px; object-fit: contain; width: 100%; }}
    .tile-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .tile-card {{ border: 1px solid #ddd; background: #fafafa; padding: 6px; }}
    .tile-head {{ font-size: 12px; font-weight: 700; margin-bottom: 4px; }}
    .tile-bbox {{ font-size: 10px; color: #666; margin-top: 4px; word-break: break-all; }}
    .review-controls {{ display: flex; gap: 12px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e2e2; }}
    .review-controls label {{ font-size: 12px; display: flex; gap: 6px; align-items: center; }}
    .review-controls input {{ min-width: 420px; padding: 6px; }}
    @media (max-width: 1300px) {{
      .visual-grid {{ grid-template-columns: 1fr; }}
      .metrics, .delta-strip {{ grid-template-columns: 1fr 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Topology Panel v1 Tile2x2 / Overlap10 Review · {len(rows)} panels</h1>
    <div>
      <button onclick="exportCsv()">Export Review CSV</button>
      <button onclick="clearLabels()">Clear Labels</button>
    </div>
  </header>
  <main>
    {''.join(cards)}
  </main>
  <script>
    const storageKey = 'topology_panel_v1_tile2x2_overlap10_review';
    const panelIds = {json.dumps([row['panel_id'] for row in rows], ensure_ascii=False)};
    function loadState() {{
      const state = JSON.parse(localStorage.getItem(storageKey) || '{{}}');
      document.querySelectorAll('.panel-card').forEach((card, idx) => {{
        const pid = panelIds[idx];
        const row = state[pid] || {{}};
        card.querySelectorAll('[data-field]').forEach(el => {{
          el.value = row[el.dataset.field] || '';
          el.addEventListener('input', saveState);
          el.addEventListener('change', saveState);
        }});
      }});
    }}
    function saveState() {{
      const state = {{}};
      document.querySelectorAll('.panel-card').forEach((card, idx) => {{
        const pid = panelIds[idx];
        state[pid] = {{}};
        card.querySelectorAll('[data-field]').forEach(el => state[pid][el.dataset.field] = el.value);
      }});
      localStorage.setItem(storageKey, JSON.stringify(state));
    }}
    function exportCsv() {{
      saveState();
      const state = JSON.parse(localStorage.getItem(storageKey) || '{{}}');
      const rows = [['panel_id','review_label','review_note']];
      panelIds.forEach(pid => rows.push([pid, state[pid]?.review_label || '', state[pid]?.review_note || '']));
      const csv = rows.map(r => r.map(v => '"' + String(v).replaceAll('"','""') + '"').join(',')).join('\\n');
      const blob = new Blob([csv], {{type:'text/csv;charset=utf-8;'}});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'topology_panel_v1_tile2x2_overlap10_review_labels.csv';
      a.click();
    }}
    function clearLabels() {{
      if (!confirm('Clear local review labels?')) return;
      localStorage.removeItem(storageKey);
      location.reload();
    }}
    loadState();
  </script>
</body>
</html>
"""
    args.output.write_text(html_text, encoding="utf-8")


def write_manifest(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    fields = [
        "panel_id",
        "phase",
        "split",
        "auto_tags",
        "reference_node_count",
        "reference_edge_count",
        "reference_net_count",
        "base_node_abs_error",
        "base_edge_abs_error",
        "base_net_abs_error",
        "tile_node_abs_error",
        "tile_edge_abs_error",
        "tile_net_abs_error",
        "overlap_node_abs_error",
        "overlap_edge_abs_error",
        "overlap_net_abs_error",
        "edge_delta_overlap_minus_tile",
        "node_delta_overlap_minus_tile",
        "net_delta_overlap_minus_tile",
        "edge_delta_overlap_minus_base",
        "node_delta_overlap_minus_base",
        "image_path",
    ]
    output_rows: List[Dict[str, object]] = []
    for row in rows:
        output_rows.append(
            {
                "panel_id": row["panel_id"],
                "phase": row["phase"],
                "split": row["split"],
                "auto_tags": ";".join(row["tags"]),
                "reference_node_count": row["reference_node_count"],
                "reference_edge_count": row["reference_edge_count"],
                "reference_net_count": row["reference_net_count"],
                "base_node_abs_error": row["base"].get("node_count_abs_error", ""),
                "base_edge_abs_error": row["base"].get("edge_count_abs_error", ""),
                "base_net_abs_error": row["base"].get("net_count_abs_error", ""),
                "tile_node_abs_error": row["tile"].get("node_count_abs_error", ""),
                "tile_edge_abs_error": row["tile"].get("edge_count_abs_error", ""),
                "tile_net_abs_error": row["tile"].get("net_count_abs_error", ""),
                "overlap_node_abs_error": row["overlap"].get("node_count_abs_error", ""),
                "overlap_edge_abs_error": row["overlap"].get("edge_count_abs_error", ""),
                "overlap_net_abs_error": row["overlap"].get("net_count_abs_error", ""),
                "edge_delta_overlap_minus_tile": f"{row['edge_delta_overlap_minus_tile']:.6f}",
                "node_delta_overlap_minus_tile": f"{row['node_delta_overlap_minus_tile']:.6f}",
                "net_delta_overlap_minus_tile": f"{row['net_delta_overlap_minus_tile']:.6f}",
                "edge_delta_overlap_minus_base": f"{row['edge_delta_overlap_minus_base']:.6f}",
                "node_delta_overlap_minus_base": f"{row['node_delta_overlap_minus_base']:.6f}",
                "image_path": row["image_path"],
            }
        )
    write_csv(args.csv, output_rows, fields)


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    tag_counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        for tag in row["tags"]:
            tag_counts[tag] += 1
    summary = {
        "review_id": "topology_panel_v1_tile2x2_overlap10_review_2026-07-10",
        "panel_count": len(rows),
        "output_html": args.output.resolve().relative_to(ROOT).as_posix(),
        "output_manifest": args.csv.resolve().relative_to(ROOT).as_posix(),
        "tag_counts": dict(sorted(tag_counts.items())),
        "sort_order": "most negative edge_delta_overlap_minus_tile first",
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--tile-manifest", type=Path, default=DEFAULT_TILE_MANIFEST)
    parser.add_argument("--overlap-manifest", type=Path, default=DEFAULT_OVERLAP_MANIFEST)
    parser.add_argument("--base-details", type=Path, default=DEFAULT_BASE_DETAILS)
    parser.add_argument("--tile-details", type=Path, default=DEFAULT_TILE_DETAILS)
    parser.add_argument("--overlap-details", type=Path, default=DEFAULT_OVERLAP_DETAILS)
    parser.add_argument("--tile-predictions", type=Path, default=DEFAULT_TILE_PREDICTIONS)
    parser.add_argument("--overlap-predictions", type=Path, default=DEFAULT_OVERLAP_PREDICTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_rows(args)
    render_html(rows, args)
    write_manifest(rows, args)
    write_summary(rows, args)
    print(f"Review panels: {len(rows)}")
    print(f"Wrote: {args.output.resolve().relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.csv.resolve().relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.summary.resolve().relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
