"""Build diagnostic CSV/HTML for Topology Panel v1.1 still-fragmented rows."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import quote

import build_topology_panel_v1 as panel_v1


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_INPUT = INDEX_DIR / "topology_panel_v1_1_still_fragmented_input.csv"
DEFAULT_BEST = INDEX_DIR / "topology_panel_v1_1_still_fragmented_best_candidates.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_1_still_fragmented_diagnostic.html"
DEFAULT_DIAGNOSTIC = INDEX_DIR / "topology_panel_v1_1_still_fragmented_diagnostic.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_1_still_fragmented_diagnostic_summary.json"

LABELS = [
    "no_line_geometry",
    "crop_or_bbox_issue",
    "non_topology_target",
    "needs_panel_split_badcase",
    "true_fragmentation",
    "terminal_anchor_needed",
]

LINE_TYPES = {"LINE", "LWPOLYLINE"}
NON_WIRE_HINT_TYPES = {"TEXT", "MTEXT", "INSERT", "HATCH", "DIMENSION"}


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


def int_value(value: object) -> int:
    try:
        return int(float(str(value or 0)))
    except ValueError:
        return 0


def float_value(value: object) -> float:
    try:
        return float(str(value or 0))
    except ValueError:
        return 0.0


def load_json(path_value: str) -> Dict[str, object]:
    if not path_value:
        return {}
    path = ROOT / path_value
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def entity_type_counts(row: Dict[str, str]) -> Tuple[Dict[str, int], int, int]:
    payload = load_json(row.get("parent_normalized_json_path", ""))
    bbox = panel_v1.parse_bbox(row.get("panel_bbox_cad", ""))
    if bbox is None:
        return {}, 0, 0
    entities = payload.get("entities", [])
    if not isinstance(entities, list):
        return {}, 0, 0
    inside: List[Dict[str, object]] = [
        entity
        for entity in entities
        if isinstance(entity, dict) and panel_v1.center_in_bbox(entity, bbox)
    ]
    counts = Counter(str(entity.get("type", "")).upper() for entity in inside)
    line_like = sum(counts.get(kind, 0) for kind in LINE_TYPES)
    non_wire_hints = sum(counts.get(kind, 0) for kind in NON_WIRE_HINT_TYPES)
    return dict(counts), line_like, non_wire_hints


def suggest_label(row: Dict[str, object]) -> Tuple[str, str]:
    model_label = str(row.get("model_review_label", ""))
    split_method = str(row.get("split_method", ""))
    line_like = int_value(row.get("panel_line_like_entity_count", 0))
    total_entities = int_value(row.get("panel_total_entity_count", 0))
    non_wire = int_value(row.get("panel_non_wire_hint_entity_count", 0))
    original_edges = int_value(row.get("original_edges", 0))
    new_edges = int_value(row.get("new_edges", 0))
    still_empty = str(row.get("still_empty", "")).lower() == "true"
    isolated = float_value(row.get("original_isolated_edge_ratio", 0))

    if model_label == "not_topology_target":
        return "non_topology_target", "model pre-review marked this row as not a topology target"
    if model_label == "needs_panel_split" or (split_method == "image_components" and total_entities <= 2):
        return "needs_panel_split_badcase", "panel appears to be a residual subfigure/crop rather than a standalone topology target"
    if line_like == 0 and still_empty:
        return "no_line_geometry", "panel bbox contains no LINE/LWPOLYLINE entities and graph stayed empty"
    if total_entities > 0 and line_like == 0 and non_wire > 0:
        return "no_line_geometry", "panel contains non-wire CAD entities but no supported line geometry"
    if original_edges == 0 and new_edges == 0 and line_like > 0:
        return "crop_or_bbox_issue", "line-like entities exist in the panel bbox but graph extraction still produced no edges"
    if original_edges > 0 and isolated >= 0.5:
        return "true_fragmentation", "graph has line edges but remains highly fragmented"
    return "terminal_anchor_needed", "geometry exists but graph repair may require terminal or symbol anchors"


def merge_rows(input_rows: List[Dict[str, str]], best_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    best_by_panel = {row["panel_id"]: row for row in best_rows}
    rows: List[Dict[str, object]] = []
    for source in input_rows:
        best = best_by_panel.get(source["panel_id"], {})
        counts, line_like, non_wire = entity_type_counts(source)
        merged: Dict[str, object] = {
            **source,
            **{f"best_{key}": value for key, value in best.items() if key not in source},
            "best_variant": best.get("variant", ""),
            "original_edges": best.get("original_edges", source.get("v1_edge_count", "")),
            "original_nodes": best.get("original_nodes", source.get("v1_node_count", "")),
            "original_nets": best.get("original_nets", source.get("v1_net_count", "")),
            "original_isolated_edge_ratio": best.get(
                "original_isolated_edge_ratio",
                source.get("v1_isolated_edge_ratio", ""),
            ),
            "original_largest_net_edge_ratio": best.get(
                "original_largest_net_edge_ratio",
                source.get("v1_largest_net_edge_ratio", ""),
            ),
            "new_edges": best.get("new_edges", ""),
            "new_nodes": best.get("new_nodes", ""),
            "new_nets": best.get("new_nets", ""),
            "new_isolated_edge_ratio": best.get("new_isolated_edge_ratio", ""),
            "new_largest_net_edge_ratio": best.get("new_largest_net_edge_ratio", ""),
            "candidate_improved": best.get("candidate_improved", ""),
            "still_empty": best.get("still_empty", ""),
            "overmerge_warning": best.get("overmerge_warning", ""),
            "new_quality_flags": best.get("new_quality_flags", ""),
            "new_topology_v1_1_json_path": best.get("new_topology_v1_1_json_path", ""),
            "panel_entity_type_counts": json.dumps(counts, ensure_ascii=False, sort_keys=True),
            "panel_total_entity_count": sum(counts.values()),
            "panel_line_like_entity_count": line_like,
            "panel_non_wire_hint_entity_count": non_wire,
        }
        label, reason = suggest_label(merged)
        merged["suggested_diagnostic_label"] = label
        merged["suggested_diagnostic_reason"] = reason
        rows.append(merged)
    return rows


def build_summary(rows: List[Dict[str, object]]) -> Dict[str, object]:
    return {
        "source_input": DEFAULT_INPUT.relative_to(ROOT).as_posix(),
        "source_best_candidates": DEFAULT_BEST.relative_to(ROOT).as_posix(),
        "diagnostic_csv": DEFAULT_DIAGNOSTIC.relative_to(ROOT).as_posix(),
        "diagnostic_html": DEFAULT_OUTPUT.relative_to(ROOT).as_posix(),
        "row_count": len(rows),
        "suggested_label_counts": dict(Counter(str(row["suggested_diagnostic_label"]) for row in rows)),
        "model_label_counts": dict(Counter(str(row.get("model_review_label", "")) for row in rows)),
        "quality_flag_counts": dict(Counter(str(row.get("quality_flags", "")) for row in rows)),
        "still_empty_rows": sum(1 for row in rows if str(row.get("still_empty", "")).lower() == "true"),
        "line_like_zero_rows": sum(1 for row in rows if int_value(row.get("panel_line_like_entity_count", 0)) == 0),
        "labels": LABELS,
    }


def render_html(rows: List[Dict[str, object]], summary: Dict[str, object], title: str) -> str:
    compact = []
    for row in rows:
        item = dict(row)
        item["image_src"] = rel_asset_path(str(row.get("panel_png_path", "")), DEFAULT_OUTPUT)
        item["old_graph_src"] = rel_asset_path(str(row.get("topology_v1_panel_json_path", "")), DEFAULT_OUTPUT)
        item["new_graph_src"] = rel_asset_path(str(row.get("new_topology_v1_1_json_path", "")), DEFAULT_OUTPUT)
        compact.append(item)
    data_json = json.dumps(compact, ensure_ascii=False)
    labels_json = json.dumps(LABELS, ensure_ascii=False)
    summary_json = json.dumps(summary, ensure_ascii=False)
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
      --panel: #fff;
      --ink: #101828;
      --muted: #667085;
      --border: #d8dee8;
      --dark: #111827;
      --ok: #0f7b45;
      --warn: #a35b00;
      --bad: #b42318;
      --info: #175cd3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 12px 16px;
      background: rgba(255,255,255,.96);
      border-bottom: 1px solid var(--border);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      font-weight: 680;
      letter-spacing: 0;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    input[type="search"], select {{
      height: 34px;
      min-width: 160px;
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
      font-size: 13px;
      color: var(--muted);
      white-space: nowrap;
    }}
    main {{
      padding: 14px;
      display: grid;
      gap: 14px;
    }}
    .card {{
      display: grid;
      grid-template-columns: minmax(420px, 1fr) 460px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      min-height: 360px;
    }}
    .image-pane {{
      min-height: 360px;
      border-right: 1px solid var(--border);
      background: #fbfcfe;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: auto;
      padding: 10px;
    }}
    .image-pane img {{
      max-width: 100%;
      max-height: 82vh;
      object-fit: contain;
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
    .badge.warn {{ color: var(--warn); border-color: #ffdca8; background: #fff8eb; }}
    .badge.bad {{ color: var(--bad); border-color: #fecdca; background: #fff3f2; }}
    .badge.ok {{ color: var(--ok); border-color: #b7e4c7; background: #f1fbf5; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0,1fr));
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
      font-size: 14px;
      font-weight: 670;
      overflow-wrap: anywhere;
    }}
    textarea {{
      width: 100%;
      min-height: 70px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font: inherit;
      font-size: 13px;
    }}
    a {{ color: var(--info); text-decoration: none; overflow-wrap: anywhere; }}
    @media (max-width: 980px) {{
      .card {{ grid-template-columns: 1fr; }}
      .image-pane {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .stats {{ width: 100%; margin-left: 0; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{escaped_title}</h1>
    <div class="toolbar">
      <input id="query" type="search" placeholder="panel / reason / model" />
      <select id="suggestFilter"><option value="">all suggestions</option></select>
      <select id="reviewFilter"><option value="">all review labels</option></select>
      <select id="emptyFilter">
        <option value="">all graph states</option>
        <option value="true">still empty</option>
        <option value="false">has edges</option>
      </select>
      <button id="clearBtn">Clear</button>
      <button id="exportBtn" class="primary">Export CSV</button>
      <span id="stats" class="stats"></span>
    </div>
  </header>
  <main id="cards"></main>
  <script>
    const rows = {data_json};
    const labels = {labels_json};
    const summary = {summary_json};
    const stateKey = "topology_panel_v1_1_still_fragmented_diagnostic_labels";
    const saved = JSON.parse(localStorage.getItem(stateKey) || "{{}}");
    const cards = document.getElementById("cards");
    const query = document.getElementById("query");
    const suggestFilter = document.getElementById("suggestFilter");
    const reviewFilter = document.getElementById("reviewFilter");
    const emptyFilter = document.getElementById("emptyFilter");
    const stats = document.getElementById("stats");

    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, ch => ({{
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }}[ch]));
    }}
    function current(id, row) {{
      return saved[id] || {{
        diagnostic_label: row.suggested_diagnostic_label,
        comment: ""
      }};
    }}
    function save(id, patch) {{
      const row = rows.find(item => item.panel_id === id);
      saved[id] = {{ ...current(id, row), ...patch }};
      localStorage.setItem(stateKey, JSON.stringify(saved));
      render();
    }}
    function metric(label, value) {{
      return `<div class="metric"><b>${{escapeHtml(label)}}</b><span>${{escapeHtml(value)}}</span></div>`;
    }}
    function badgeClass(row) {{
      if (String(row.still_empty).toLowerCase() === "true") return "bad";
      if (row.suggested_diagnostic_label === "true_fragmentation") return "warn";
      return "ok";
    }}
    function card(row) {{
      const review = current(row.panel_id, row);
      const oldLink = row.old_graph_src ? `<a href="${{row.old_graph_src}}" target="_blank">old graph</a>` : "";
      const newLink = row.new_graph_src ? `<a href="${{row.new_graph_src}}" target="_blank">v1.1 graph</a>` : "";
      return `<article class="card">
        <section class="image-pane">
          <img src="${{row.image_src}}" alt="${{escapeHtml(row.panel_id)}}" loading="lazy" />
        </section>
        <section class="meta">
          <div>
            <div class="title">${{escapeHtml(row.panel_id)}}</div>
            <div class="sub">${{escapeHtml(row.parent_drawing_key)}}</div>
          </div>
          <div class="badges">
            <span class="badge ${{badgeClass(row)}}">${{escapeHtml(row.suggested_diagnostic_label)}}</span>
            <span class="badge">${{escapeHtml(row.model_review_label)}}</span>
            <span class="badge">${{escapeHtml(row.phase)}}</span>
            <span class="badge">${{escapeHtml(row.split_method)}}</span>
          </div>
          <div class="grid">
            ${{metric("old edges", row.original_edges)}}
            ${{metric("new edges", row.new_edges)}}
            ${{metric("old nets", row.original_nets)}}
            ${{metric("new nets", row.new_nets)}}
            ${{metric("line-like entities", row.panel_line_like_entity_count)}}
            ${{metric("total entities", row.panel_total_entity_count)}}
            ${{metric("old isolated", row.original_isolated_edge_ratio)}}
            ${{metric("new isolated", row.new_isolated_edge_ratio)}}
          </div>
          <div class="sub"><b>suggested reason:</b> ${{escapeHtml(row.suggested_diagnostic_reason)}}</div>
          <div class="sub"><b>entity types:</b> ${{escapeHtml(row.panel_entity_type_counts)}}</div>
          <div class="sub"><b>model reason:</b> ${{escapeHtml(row.model_reason)}}</div>
          <div class="sub">${{oldLink}} ${{newLink}}</div>
          <select onchange="save('${{escapeHtml(row.panel_id)}}', {{ diagnostic_label: this.value }})">
            ${{labels.map(label => `<option value="${{label}}" ${{review.diagnostic_label === label ? "selected" : ""}}>${{label}}</option>`).join("")}}
          </select>
          <textarea placeholder="comment" oninput="save('${{escapeHtml(row.panel_id)}}', {{ comment: this.value }})">${{escapeHtml(review.comment || "")}}</textarea>
        </section>
      </article>`;
    }}
    function populateFilters() {{
      for (const label of labels) {{
        suggestFilter.insertAdjacentHTML("beforeend", `<option value="${{label}}">${{label}}</option>`);
        reviewFilter.insertAdjacentHTML("beforeend", `<option value="${{label}}">${{label}}</option>`);
      }}
    }}
    function filteredRows() {{
      const q = query.value.trim().toLowerCase();
      return rows.filter(row => {{
        const review = current(row.panel_id, row);
        if (suggestFilter.value && row.suggested_diagnostic_label !== suggestFilter.value) return false;
        if (reviewFilter.value && review.diagnostic_label !== reviewFilter.value) return false;
        if (emptyFilter.value && String(row.still_empty).toLowerCase() !== emptyFilter.value) return false;
        if (!q) return true;
        return [row.panel_id, row.parent_drawing_key, row.suggested_diagnostic_reason, row.model_review_label, row.model_reason, row.panel_entity_type_counts]
          .some(value => String(value || "").toLowerCase().includes(q));
      }});
    }}
    function render() {{
      const visible = filteredRows();
      cards.innerHTML = visible.map(card).join("");
      const counts = rows.reduce((acc, row) => {{
        const label = current(row.panel_id, row).diagnostic_label;
        acc[label] = (acc[label] || 0) + 1;
        return acc;
      }}, {{}});
      stats.textContent = `${{visible.length}} / ${{rows.length}} visible | ` + labels.map(label => `${{label}} ${{counts[label] || 0}}`).join(" | ");
    }}
    function csvEscape(value) {{
      const text = String(value ?? "");
      return /[",\\n\\r]/.test(text) ? `"${{text.replace(/"/g, '""')}}"` : text;
    }}
    function exportCsv() {{
      const header = ["panel_id", "diagnostic_label", "comment", "suggested_diagnostic_label", "suggested_diagnostic_reason"];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const review = current(row.panel_id, row);
        lines.push([row.panel_id, review.diagnostic_label, review.comment || "", row.suggested_diagnostic_label, row.suggested_diagnostic_reason].map(csvEscape).join(","));
      }}
      const blob = new Blob(["\\ufeff" + lines.join("\\n") + "\\n"], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "topology_panel_v1_1_still_fragmented_diagnostic_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    populateFilters();
    for (const input of [query, suggestFilter, reviewFilter, emptyFilter]) {{
      input.addEventListener("input", render);
      input.addEventListener("change", render);
    }}
    document.getElementById("clearBtn").addEventListener("click", () => {{
      query.value = "";
      suggestFilter.value = "";
      reviewFilter.value = "";
      emptyFilter.value = "";
      render();
    }});
    document.getElementById("exportBtn").addEventListener("click", exportCsv);
    render();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--best", type=Path, default=DEFAULT_BEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--title", default="Topology Panel v1.1 Still-Fragmented Diagnostic")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_rows = load_csv(args.input)
    best_rows = load_csv(args.best)
    rows = merge_rows(input_rows, best_rows)
    fieldnames = list(rows[0].keys()) if rows else []
    write_csv(DEFAULT_DIAGNOSTIC, rows, fieldnames)
    summary = build_summary(rows)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.write_text(render_html(rows, summary, args.title), encoding="utf-8")

    print(f"Rows: {len(rows)}")
    print(f"Suggested labels: {summary['suggested_label_counts']}")
    print(f"Wrote: {DEFAULT_DIAGNOSTIC.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
