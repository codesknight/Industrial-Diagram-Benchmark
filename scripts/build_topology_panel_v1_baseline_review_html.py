"""Build a compact HTML review page for Topology Panel v1 clean baseline."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_release_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_baseline_review.html"
DEFAULT_REVIEW_MANIFEST = INDEX_DIR / "topology_panel_v1_baseline_review_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_baseline_review_summary.json"


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


def rel_asset_path(path: str, html_path: Path) -> str:
    if not path:
        return ""
    raw = Path(path)
    if raw.is_absolute():
        rel = raw.as_posix()
    else:
        target = (ROOT / raw).resolve()
        try:
            rel = os.path.relpath(target, html_path.parent.resolve())
        except ValueError:
            rel = target.as_posix()
        rel = rel.replace("\\", "/")
    return quote(rel, safe="/:.")


def as_int(row: Dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "") or 0))
    except ValueError:
        return 0


def as_float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except ValueError:
        return 0.0


def point_pair(value: Sequence[object]) -> str:
    if len(value) < 2:
        return ""
    try:
        return f"{float(value[0]):.4f},{float(value[1]):.4f}"
    except (TypeError, ValueError):
        return ""


def load_topology(path_value: str) -> Dict[str, object]:
    path = ROOT / path_value
    if not path.exists():
        return {"missing": True}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"error": f"json_decode_error: {exc}"}


def graph_bbox(topology: Dict[str, object]) -> List[float]:
    stats = topology.get("stats", {})
    bbox = stats.get("graph_bbox") if isinstance(stats, dict) else None
    if isinstance(bbox, list) and len(bbox) == 4:
        try:
            return [float(item) for item in bbox]
        except (TypeError, ValueError):
            pass

    points: List[List[float]] = []
    for edge in topology.get("edges", []) if isinstance(topology.get("edges"), list) else []:
        for point in edge.get("points", []) if isinstance(edge, dict) else []:
            if isinstance(point, list) and len(point) >= 2:
                try:
                    points.append([float(point[0]), float(point[1])])
                except (TypeError, ValueError):
                    continue
    if not points:
        return [0.0, 0.0, 1.0, 1.0]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def render_graph_svg(topology: Dict[str, object], max_edges: int) -> str:
    if topology.get("missing"):
        return '<div class="svg-empty">missing topology json</div>'
    if topology.get("error"):
        return f'<div class="svg-empty">{html.escape(str(topology["error"]))}</div>'

    bbox = graph_bbox(topology)
    min_x, min_y, max_x, max_y = bbox
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    pad = max(width, height) * 0.03
    view_box = f"{min_x - pad:.4f} {min_y - pad:.4f} {width + pad * 2:.4f} {height + pad * 2:.4f}"

    edges = topology.get("edges", [])
    if not isinstance(edges, list):
        edges = []
    visible_edges = edges[:max_edges]
    lines = [
        '<svg class="graph-svg" viewBox="' + view_box + '" xmlns="http://www.w3.org/2000/svg">',
        '<rect class="graph-bg" x="' + f"{min_x - pad:.4f}" + '" y="' + f"{min_y - pad:.4f}" + '" width="' + f"{width + pad * 2:.4f}" + '" height="' + f"{height + pad * 2:.4f}" + '" />',
    ]
    for edge in visible_edges:
        if not isinstance(edge, dict):
            continue
        pairs = [
            point_pair(point)
            for point in edge.get("points", [])
            if isinstance(point, list)
        ]
        pairs = [pair for pair in pairs if pair]
        if len(pairs) < 2:
            continue
        layer = html.escape(str(edge.get("layer", "")))
        lines.append(f'<polyline class="edge" data-layer="{layer}" points="{" ".join(pairs)}" />')

    nodes = topology.get("nodes", [])
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            degree = int(node.get("degree", 0) or 0)
            if degree < 4:
                continue
            point = node.get("point", [])
            if not isinstance(point, list) or len(point) < 2:
                continue
            try:
                x = float(point[0])
                y = float(point[1])
            except (TypeError, ValueError):
                continue
            radius = max(width, height) * (0.0028 if degree < 6 else 0.004)
            lines.append(f'<circle class="node" cx="{x:.4f}" cy="{y:.4f}" r="{radius:.4f}" />')

    if len(edges) > max_edges:
        lines.append(f'<text class="svg-note" x="{min_x:.4f}" y="{min_y:.4f}">showing {max_edges}/{len(edges)} edges</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def topology_summary(topology: Dict[str, object]) -> Dict[str, object]:
    if topology.get("missing") or topology.get("error"):
        return topology
    stats = topology.get("stats", {})
    if not isinstance(stats, dict):
        stats = {}
    edge_type_counts = stats.get("edge_type_counts", {})
    if not isinstance(edge_type_counts, dict):
        edge_type_counts = {}
    nets = topology.get("nets", [])
    if not isinstance(nets, list):
        nets = []
    return {
        "schema": topology.get("schema", ""),
        "status": topology.get("status", ""),
        "node_count": stats.get("node_count", ""),
        "edge_count": stats.get("edge_count", ""),
        "net_count": stats.get("net_count", ""),
        "intersection_count": stats.get("intersection_count", ""),
        "split_event_count": stats.get("split_event_count", ""),
        "largest_net_edges": stats.get("largest_net_edges", ""),
        "isolated_edge_ratio": stats.get("isolated_edge_ratio", ""),
        "largest_net_edge_ratio": stats.get("largest_net_edge_ratio", ""),
        "edge_type_counts": edge_type_counts,
        "net_previews": [
            {
                "id": net.get("id", ""),
                "node_count": net.get("node_count", ""),
                "edge_count": net.get("edge_count", ""),
            }
            for net in nets[:5]
            if isinstance(net, dict)
        ],
    }


def compact_rows(rows: Iterable[Dict[str, str]], html_path: Path, max_edges: int) -> List[Dict[str, object]]:
    compact: List[Dict[str, object]] = []
    for row in rows:
        topology = load_topology(row.get("topology_v1_panel_json_path", ""))
        compact.append(
            {
                "panel_id": row.get("panel_id", ""),
                "parent_drawing_key": row.get("parent_drawing_key", ""),
                "split": row.get("split", ""),
                "phase": row.get("phase", ""),
                "batch": row.get("batch", ""),
                "panel_index": row.get("panel_index", ""),
                "panel_count": row.get("panel_count", ""),
                "split_method": row.get("split_method", ""),
                "panel_png_path": row.get("panel_png_path", ""),
                "image_src": rel_asset_path(row.get("panel_png_path", ""), html_path),
                "topology_v1_panel_json_path": row.get("topology_v1_panel_json_path", ""),
                "topology_v1_panel_json_src": rel_asset_path(row.get("topology_v1_panel_json_path", ""), html_path),
                "panel_bbox_cad": row.get("panel_bbox_cad", ""),
                "panel_entity_count": row.get("panel_entity_count", ""),
                "base_segment_count": row.get("base_segment_count", ""),
                "split_segment_count": row.get("split_segment_count", ""),
                "intersection_count": row.get("intersection_count", ""),
                "split_event_count": row.get("split_event_count", ""),
                "v1_node_count": row.get("v1_node_count", ""),
                "v1_edge_count": row.get("v1_edge_count", ""),
                "v1_net_count": row.get("v1_net_count", ""),
                "v1_isolated_edge_ratio": row.get("v1_isolated_edge_ratio", ""),
                "v1_largest_net_edge_ratio": row.get("v1_largest_net_edge_ratio", ""),
                "effective_endpoint_tolerance": row.get("effective_endpoint_tolerance", ""),
                "quality_flags": row.get("quality_flags", ""),
                "model_review_label": row.get("model_review_label", ""),
                "model_confidence": row.get("model_confidence", ""),
                "model_reason": row.get("model_reason", ""),
                "review_comment": row.get("topology_panel_v1_review_comment", ""),
                "topology_summary": topology_summary(topology),
                "graph_svg": render_graph_svg(topology, max_edges),
            }
        )
    return compact


def render_html(rows: List[Dict[str, object]], title: str) -> str:
    data_json = json.dumps(rows, ensure_ascii=False)
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escaped_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #667085;
      --border: #d7dde7;
      --line: #1f6feb;
      --node: #d12f1f;
      --dark: #111827;
      --ok: #0f7b45;
      --warn: #a35b00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.96);
      border-bottom: 1px solid var(--border);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      line-height: 1.25;
      font-weight: 680;
      letter-spacing: 0;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }}
    input[type="search"], select {{
      height: 34px;
      min-width: 150px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0 10px;
      background: #fff;
      color: var(--ink);
    }}
    button {{
      height: 34px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0 12px;
      background: #fff;
      color: var(--ink);
      cursor: pointer;
      font-weight: 560;
    }}
    button.primary {{
      background: var(--dark);
      border-color: var(--dark);
      color: #fff;
    }}
    .stats {{
      margin-left: auto;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }}
    main {{
      display: grid;
      gap: 14px;
      padding: 14px;
    }}
    .card {{
      display: grid;
      grid-template-columns: minmax(360px, 1.1fr) minmax(360px, 1fr) 380px;
      min-height: 420px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    .image-pane, .graph-pane {{
      min-height: 420px;
      border-right: 1px solid var(--border);
      background: #fbfcfe;
      overflow: auto;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px;
    }}
    .image-pane img {{
      max-width: 100%;
      max-height: 82vh;
      object-fit: contain;
      image-rendering: auto;
    }}
    .graph-pane {{
      background: #ffffff;
    }}
    .graph-svg {{
      width: 100%;
      height: 100%;
      min-height: 380px;
    }}
    .graph-bg {{
      fill: #fff;
      stroke: #d0d5dd;
      stroke-width: 0.35%;
      vector-effect: non-scaling-stroke;
    }}
    .edge {{
      fill: none;
      stroke: var(--line);
      stroke-width: 0.45;
      vector-effect: non-scaling-stroke;
      opacity: 0.78;
    }}
    .node {{
      fill: var(--node);
      opacity: 0.72;
      vector-effect: non-scaling-stroke;
    }}
    .svg-note {{
      fill: var(--warn);
      font-size: 10px;
    }}
    .svg-empty {{
      color: var(--muted);
      font-size: 13px;
    }}
    .meta {{
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      min-width: 0;
    }}
    .title {{
      font-size: 15px;
      font-weight: 680;
      overflow-wrap: anywhere;
    }}
    .sub {{
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    .badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .badge {{
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      background: #fff;
    }}
    .badge.ok {{
      color: var(--ok);
      border-color: #b7e4c7;
      background: #f1fbf5;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
    }}
    .metric {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 7px 8px;
      min-width: 0;
    }}
    .metric b {{
      display: block;
      font-size: 12px;
      color: var(--muted);
      font-weight: 560;
    }}
    .metric span {{
      display: block;
      margin-top: 2px;
      font-size: 15px;
      font-weight: 680;
      overflow-wrap: anywhere;
    }}
    .review {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
      margin-top: auto;
    }}
    textarea {{
      width: 100%;
      min-height: 74px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font: inherit;
      font-size: 13px;
    }}
    a {{
      color: #175cd3;
      text-decoration: none;
      overflow-wrap: anywhere;
    }}
    @media (max-width: 1180px) {{
      .card {{
        grid-template-columns: 1fr;
      }}
      .image-pane, .graph-pane {{
        border-right: 0;
        border-bottom: 1px solid var(--border);
      }}
      .stats {{
        width: 100%;
        margin-left: 0;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{escaped_title}</h1>
    <div class="toolbar">
      <input id="query" type="search" placeholder="panel / drawing / phase" />
      <select id="splitFilter">
        <option value="">all splits</option>
        <option value="train">train</option>
        <option value="val">val</option>
        <option value="test">test</option>
      </select>
      <select id="phaseFilter">
        <option value="">all phases</option>
        <option value="P1">P1</option>
        <option value="P2">P2</option>
        <option value="P3">P3</option>
      </select>
      <select id="labelFilter">
        <option value="">all review labels</option>
        <option value="confirmed_baseline">confirmed_baseline</option>
        <option value="needs_recheck">needs_recheck</option>
        <option value="remove_from_baseline">remove_from_baseline</option>
      </select>
      <button id="clearBtn">Clear</button>
      <button id="exportBtn" class="primary">Export CSV</button>
      <span id="stats" class="stats"></span>
    </div>
  </header>
  <main id="cards"></main>
  <script>
    const rows = {data_json};
    const stateKey = "topology_panel_v1_baseline_review_labels";
    const labels = JSON.parse(localStorage.getItem(stateKey) || "{{}}");

    const cards = document.getElementById("cards");
    const query = document.getElementById("query");
    const splitFilter = document.getElementById("splitFilter");
    const phaseFilter = document.getElementById("phaseFilter");
    const labelFilter = document.getElementById("labelFilter");
    const stats = document.getElementById("stats");

    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, ch => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }}[ch]));
    }}

    function currentReview(id) {{
      return labels[id] || {{ review_label: "confirmed_baseline", comment: "" }};
    }}

    function saveReview(id, patch) {{
      labels[id] = {{ ...currentReview(id), ...patch }};
      localStorage.setItem(stateKey, JSON.stringify(labels));
      render();
    }}

    function metric(label, value) {{
      return `<div class="metric"><b>${{escapeHtml(label)}}</b><span>${{escapeHtml(value)}}</span></div>`;
    }}

    function card(row) {{
      const review = currentReview(row.panel_id);
      const jsonLink = row.topology_v1_panel_json_src
        ? `<a href="${{row.topology_v1_panel_json_src}}" target="_blank">topology json</a>`
        : "";
      return `<article class="card">
        <section class="image-pane">
          <img src="${{row.image_src}}" alt="${{escapeHtml(row.panel_id)}}" loading="lazy" />
        </section>
        <section class="graph-pane">${{row.graph_svg}}</section>
        <section class="meta">
          <div>
            <div class="title">${{escapeHtml(row.panel_id)}}</div>
            <div class="sub">${{escapeHtml(row.parent_drawing_key)}}</div>
          </div>
          <div class="badges">
            <span class="badge ok">clean_baseline</span>
            <span class="badge">${{escapeHtml(row.split)}}</span>
            <span class="badge">${{escapeHtml(row.phase)}}</span>
            <span class="badge">${{escapeHtml(row.split_method)}}</span>
          </div>
          <div class="grid">
            ${{metric("nodes", row.v1_node_count)}}
            ${{metric("edges", row.v1_edge_count)}}
            ${{metric("nets", row.v1_net_count)}}
            ${{metric("intersections", row.intersection_count)}}
            ${{metric("isolated ratio", row.v1_isolated_edge_ratio)}}
            ${{metric("largest net", row.v1_largest_net_edge_ratio)}}
            ${{metric("split events", row.split_event_count)}}
            ${{metric("entity count", row.panel_entity_count)}}
          </div>
          <div class="sub">model: ${{escapeHtml(row.model_review_label)}} / ${{escapeHtml(row.model_confidence)}}</div>
          <div class="sub">${{escapeHtml(row.model_reason)}}</div>
          <div class="sub">${{jsonLink}}</div>
          <div class="review">
            <select onchange="saveReview('${{escapeHtml(row.panel_id)}}', {{ review_label: this.value }})">
              ${{["confirmed_baseline", "needs_recheck", "remove_from_baseline"].map(label =>
                `<option value="${{label}}" ${{review.review_label === label ? "selected" : ""}}>${{label}}</option>`
              ).join("")}}
            </select>
            <textarea placeholder="comment" oninput="saveReview('${{escapeHtml(row.panel_id)}}', {{ comment: this.value }})">${{escapeHtml(review.comment || "")}}</textarea>
          </div>
        </section>
      </article>`;
    }}

    function filteredRows() {{
      const q = query.value.trim().toLowerCase();
      return rows.filter(row => {{
        const review = currentReview(row.panel_id);
        if (splitFilter.value && row.split !== splitFilter.value) return false;
        if (phaseFilter.value && row.phase !== phaseFilter.value) return false;
        if (labelFilter.value && review.review_label !== labelFilter.value) return false;
        if (!q) return true;
        return [row.panel_id, row.parent_drawing_key, row.phase, row.split, row.model_reason]
          .some(value => String(value || "").toLowerCase().includes(q));
      }});
    }}

    function render() {{
      const visible = filteredRows();
      cards.innerHTML = visible.map(card).join("");
      const counts = rows.reduce((acc, row) => {{
        const label = currentReview(row.panel_id).review_label;
        acc[label] = (acc[label] || 0) + 1;
        return acc;
      }}, {{}});
      stats.textContent = `${{visible.length}} / ${{rows.length}} visible | confirmed ${{counts.confirmed_baseline || 0}} | recheck ${{counts.needs_recheck || 0}} | remove ${{counts.remove_from_baseline || 0}}`;
    }}

    function csvEscape(value) {{
      const text = String(value ?? "");
      return /[",\\n\\r]/.test(text) ? `"${{text.replace(/"/g, '""')}}"` : text;
    }}

    function exportCsv() {{
      const header = ["panel_id", "review_label", "comment"];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const review = currentReview(row.panel_id);
        lines.push([row.panel_id, review.review_label, review.comment || ""].map(csvEscape).join(","));
      }}
      const blob = new Blob(["\\ufeff" + lines.join("\\n") + "\\n"], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "topology_panel_v1_baseline_review_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}

    for (const input of [query, splitFilter, phaseFilter, labelFilter]) {{
      input.addEventListener("input", render);
      input.addEventListener("change", render);
    }}
    document.getElementById("clearBtn").addEventListener("click", () => {{
      query.value = "";
      splitFilter.value = "";
      phaseFilter.value = "";
      labelFilter.value = "";
      render();
    }});
    document.getElementById("exportBtn").addEventListener("click", exportCsv);
    render();
  </script>
</body>
</html>
"""


def build_summary(rows: List[Dict[str, str]]) -> Dict[str, object]:
    split_counts: Dict[str, int] = {}
    phase_counts: Dict[str, int] = {}
    for row in rows:
        split_counts[row.get("split", "") or "empty"] = split_counts.get(row.get("split", "") or "empty", 0) + 1
        phase_counts[row.get("phase", "") or "empty"] = phase_counts.get(row.get("phase", "") or "empty", 0) + 1
    return {
        "source_manifest": DEFAULT_MANIFEST.relative_to(ROOT).as_posix(),
        "review_html": DEFAULT_OUTPUT.relative_to(ROOT).as_posix(),
        "review_manifest": DEFAULT_REVIEW_MANIFEST.relative_to(ROOT).as_posix(),
        "row_count": len(rows),
        "split_counts": split_counts,
        "phase_counts": phase_counts,
        "min_nodes": min((as_int(row, "v1_node_count") for row in rows), default=0),
        "max_nodes": max((as_int(row, "v1_node_count") for row in rows), default=0),
        "min_edges": min((as_int(row, "v1_edge_count") for row in rows), default=0),
        "max_edges": max((as_int(row, "v1_edge_count") for row in rows), default=0),
        "min_nets": min((as_int(row, "v1_net_count") for row in rows), default=0),
        "max_nets": max((as_int(row, "v1_net_count") for row in rows), default=0),
        "mean_isolated_edge_ratio": round(
            sum(as_float(row, "v1_isolated_edge_ratio") for row in rows) / len(rows),
            4,
        ) if rows else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-edges", type=int, default=2500)
    parser.add_argument("--title", default="Topology Panel v1 Clean Baseline Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    rows = sorted(
        rows,
        key=lambda row: (
            row.get("split", ""),
            row.get("phase", ""),
            -as_int(row, "v1_edge_count"),
            row.get("panel_id", ""),
        ),
    )
    fieldnames = list(rows[0].keys()) if rows else []
    write_csv(DEFAULT_REVIEW_MANIFEST, rows, fieldnames)

    compact = compact_rows(rows, args.output, args.max_edges)
    args.output.write_text(render_html(compact, args.title), encoding="utf-8")

    summary = build_summary(rows)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Rows: {len(rows)}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_REVIEW_MANIFEST.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
