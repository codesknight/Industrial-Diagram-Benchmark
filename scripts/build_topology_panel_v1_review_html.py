"""Generate a static HTML review sheet for panel-level Topology Graph v1 pilot."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_pilot_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_pilot_review.html"


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rel_asset_path(path: str, html_path: Path) -> str:
    raw = Path(path)
    if raw.is_absolute():
        return raw.as_posix()
    target = ROOT / raw
    try:
        return target.relative_to(html_path.parent).as_posix()
    except ValueError:
        return target.as_posix()


def compact_rows(rows: Iterable[Dict[str, str]], html_path: Path) -> List[Dict[str, object]]:
    compact: List[Dict[str, object]] = []
    for row in rows:
        compact.append(
            {
                "panel_id": row["panel_id"],
                "parent_drawing_key": row["parent_drawing_key"],
                "split": row.get("split", ""),
                "phase": row.get("phase", ""),
                "panel_index": row.get("panel_index", ""),
                "panel_count": row.get("panel_count", ""),
                "panel_png_path": row.get("panel_png_path", ""),
                "image_src": rel_asset_path(row.get("panel_png_path", ""), html_path),
                "panel_bbox_png": row.get("panel_bbox_png", ""),
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
                "topology_v1_panel_json_path": row.get("topology_v1_panel_json_path", ""),
                "topology_v1_panel_json_src": rel_asset_path(row.get("topology_v1_panel_json_path", ""), html_path),
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
      --bg: #f5f7fa;
      --panel: #ffffff;
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
      color: var(--ink);
      background: var(--bg);
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 5;
      padding: 12px 18px;
      background: rgba(255,255,255,0.96);
      border-bottom: 1px solid var(--border);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      font-weight: 650;
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
      min-width: 170px;
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
      font-weight: 550;
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
      padding: 16px;
      display: grid;
      gap: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      display: grid;
      grid-template-columns: minmax(420px, 1fr) 450px;
      min-height: 360px;
      overflow: hidden;
    }}
    .image-wrap {{
      min-height: 360px;
      border-right: 1px solid var(--border);
      background: #fcfcfd;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: auto;
      padding: 10px;
    }}
    .image-wrap img {{
      max-width: 100%;
      max-height: 78vh;
      object-fit: contain;
      border: 1px solid #edf0f5;
      background: #fff;
    }}
    .meta {{
      padding: 12px;
      display: grid;
      gap: 10px;
      align-content: start;
    }}
    .title {{
      font-size: 13px;
      line-height: 1.4;
      word-break: break-all;
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
      color: var(--muted);
      font-size: 12px;
      background: #fff;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }}
    .metric {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px;
      min-width: 0;
    }}
    .metric strong {{
      display: block;
      font-size: 16px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      margin-top: 3px;
    }}
    .choices {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
    }}
    .choice {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 6px;
      text-align: center;
      cursor: pointer;
      user-select: none;
      font-size: 12px;
      font-weight: 650;
      min-height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .choice.active[data-value="accept_v1"] {{ border-color: var(--ok); color: var(--ok); background: #ecfdf3; }}
    .choice.active[data-value="over_connected"] {{ border-color: var(--bad); color: var(--bad); background: #fff1f0; }}
    .choice.active[data-value="still_fragmented"] {{ border-color: var(--warn); color: var(--warn); background: #fff7e8; }}
    .choice.active[data-value="needs_terminal_anchor"] {{ border-color: var(--info); color: var(--info); background: #eff6ff; }}
    .choice.active[data-value="bad_geometry"] {{ border-color: #7a271a; color: #7a271a; background: #fff1f0; }}
    textarea {{
      width: 100%;
      min-height: 70px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font-family: inherit;
    }}
    .kv {{
      display: grid;
      grid-template-columns: 116px minmax(0, 1fr);
      gap: 5px 8px;
      font-size: 12px;
      color: var(--muted);
    }}
    .kv code, .kv a {{
      color: var(--ink);
      word-break: break-all;
      white-space: pre-wrap;
    }}
    .kv a {{ text-decoration: none; }}
    .kv a:hover {{ text-decoration: underline; }}
    @media (max-width: 1080px) {{
      .card {{ grid-template-columns: 1fr; }}
      .image-wrap {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .stats {{ width: 100%; margin-left: 0; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{escaped_title}</h1>
    <div class="toolbar">
      <input id="search" type="search" placeholder="搜索 panel / parent" />
      <select id="labelFilter">
        <option value="all">全部标注</option>
        <option value="unlabeled">未标注</option>
        <option value="accept_v1">accept_v1</option>
        <option value="over_connected">over_connected</option>
        <option value="still_fragmented">still_fragmented</option>
        <option value="needs_terminal_anchor">needs_terminal_anchor</option>
        <option value="bad_geometry">bad_geometry</option>
      </select>
      <select id="phaseFilter">
        <option value="all">全部 phase</option>
      </select>
      <button id="clearFilters">清除筛选</button>
      <button id="exportCsv" class="primary">导出 CSV</button>
      <span id="stats" class="stats"></span>
    </div>
  </header>
  <main id="list"></main>
  <script>
    const rows = {data_json};
    const storageKey = "industrial-diagram-topology-panel-v1-pilot-review-v1";
    const labelOptions = ["accept_v1", "over_connected", "still_fragmented", "needs_terminal_anchor", "bad_geometry"];
    let labels = loadLabels();

    function loadLabels() {{
      try {{ return JSON.parse(localStorage.getItem(storageKey) || "{{}}"); }}
      catch {{ return {{}}; }}
    }}
    function saveLabels() {{
      localStorage.setItem(storageKey, JSON.stringify(labels));
      renderStats();
    }}
    function labelFor(id) {{
      return labels[id] || {{ label: "", comment: "" }};
    }}
    function setLabel(id, label) {{
      labels[id] = {{ ...labelFor(id), label }};
      saveLabels();
      render();
    }}
    function setComment(id, comment) {{
      labels[id] = {{ ...labelFor(id), comment }};
      saveLabels();
    }}
    function csvEscape(value) {{
      const s = String(value ?? "");
      return /[",\\n\\r]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s;
    }}
    function filteredRows() {{
      const q = document.getElementById("search").value.trim().toLowerCase();
      const labelFilter = document.getElementById("labelFilter").value;
      const phaseFilter = document.getElementById("phaseFilter").value;
      return rows.filter(row => {{
        const saved = labelFor(row.panel_id);
        const label = saved.label || "unlabeled";
        const text = (row.panel_id + " " + row.parent_drawing_key).toLowerCase();
        return (!q || text.includes(q))
          && (labelFilter === "all" || labelFilter === label)
          && (phaseFilter === "all" || row.phase === phaseFilter);
      }});
    }}
    function renderFilters() {{
      const phaseSelect = document.getElementById("phaseFilter");
      const phases = [...new Set(rows.map(row => row.phase).filter(Boolean))].sort();
      for (const phase of phases) {{
        const option = document.createElement("option");
        option.value = phase;
        option.textContent = phase;
        phaseSelect.appendChild(option);
      }}
    }}
    function renderStats() {{
      const counts = {{ unlabeled: 0 }};
      for (const option of labelOptions) counts[option] = 0;
      for (const row of rows) {{
        const label = labelFor(row.panel_id).label || "unlabeled";
        counts[label] = (counts[label] || 0) + 1;
      }}
      document.getElementById("stats").textContent =
        `显示 ${{filteredRows().length}} / ${{rows.length}} | accept ${{counts.accept_v1}} | over ${{counts.over_connected}} | fragmented ${{counts.still_fragmented}} | terminal ${{counts.needs_terminal_anchor}} | bad ${{counts.bad_geometry}} | 未标注 ${{counts.unlabeled}}`;
    }}
    function render() {{
      const list = document.getElementById("list");
      list.innerHTML = "";
      for (const row of filteredRows()) {{
        const saved = labelFor(row.panel_id);
        const card = document.createElement("section");
        card.className = "card";
        card.innerHTML = `
          <div class="image-wrap"><img src="${{row.image_src}}" alt="${{row.panel_id}}"></div>
          <div class="meta">
            <div class="title"><strong>${{row.panel_id}}</strong></div>
            <div class="badges">
              <span class="badge">${{row.phase}}</span>
              <span class="badge">${{row.split}}</span>
              <span class="badge">panel ${{row.panel_index}} / ${{row.panel_count}}</span>
            </div>
            <div class="metrics">
              <div class="metric"><strong>${{row.v1_edge_count}}</strong><span>edges</span></div>
              <div class="metric"><strong>${{row.v1_node_count}}</strong><span>nodes</span></div>
              <div class="metric"><strong>${{row.v1_net_count}}</strong><span>nets</span></div>
              <div class="metric"><strong>${{row.v1_isolated_edge_ratio}}</strong><span>isolated</span></div>
              <div class="metric"><strong>${{row.intersection_count}}</strong><span>intersections</span></div>
              <div class="metric"><strong>${{row.split_segment_count}}</strong><span>split segments</span></div>
              <div class="metric"><strong>${{row.panel_entity_count}}</strong><span>entities</span></div>
              <div class="metric"><strong>${{row.v1_largest_net_edge_ratio}}</strong><span>largest ratio</span></div>
            </div>
            <div class="choices">
              ${{labelOptions.map(option =>
                `<div class="choice ${{saved.label === option ? "active" : ""}}" data-value="${{option}}">${{option}}</div>`
              ).join("")}}
            </div>
            <textarea placeholder="备注：例如 v1合理、交叉误连、仍然碎、需要端子锚点..." data-comment>${{saved.comment || ""}}</textarea>
            <div class="kv">
              <span>parent</span><code>${{row.parent_drawing_key}}</code>
              <span>bbox_png</span><code>${{row.panel_bbox_png}}</code>
              <span>bbox_cad</span><code>${{row.panel_bbox_cad}}</code>
              <span>image</span><code>${{row.panel_png_path}}</code>
              <span>v1_json</span><a href="${{row.topology_v1_panel_json_src}}" target="_blank">${{row.topology_v1_panel_json_path}}</a>
            </div>
          </div>
        `;
        card.querySelectorAll(".choice").forEach(el => {{
          el.addEventListener("click", () => setLabel(row.panel_id, el.dataset.value));
        }});
        card.querySelector("[data-comment]").addEventListener("input", event => {{
          setComment(row.panel_id, event.target.value);
        }});
        list.appendChild(card);
      }}
      renderStats();
    }}
    function exportCsv() {{
      const header = [
        "panel_id", "parent_drawing_key", "split", "phase", "panel_index", "panel_count",
        "v1_edge_count", "v1_node_count", "v1_net_count", "v1_isolated_edge_ratio",
        "v1_largest_net_edge_ratio", "intersection_count", "split_event_count",
        "panel_png_path", "topology_v1_panel_json_path", "review_label", "comment"
      ];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const saved = labelFor(row.panel_id);
        lines.push(header.map(key => {{
          if (key === "review_label") return csvEscape(saved.label || "");
          if (key === "comment") return csvEscape(saved.comment || "");
          return csvEscape(row[key]);
        }}).join(","));
      }}
      const blob = new Blob(["\\ufeff" + lines.join("\\n")], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "topology_panel_v1_pilot_review_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    document.getElementById("search").addEventListener("input", render);
    document.getElementById("labelFilter").addEventListener("change", render);
    document.getElementById("phaseFilter").addEventListener("change", render);
    document.getElementById("clearFilters").addEventListener("click", () => {{
      document.getElementById("search").value = "";
      document.getElementById("labelFilter").value = "all";
      document.getElementById("phaseFilter").value = "all";
      render();
    }});
    document.getElementById("exportCsv").addEventListener("click", exportCsv);
    renderFilters();
    render();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--title", default="Industrial Diagram Topology Panel v1 Pilot Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output = args.output.resolve()
    rows = load_rows(args.manifest)
    if args.limit:
        rows = rows[: args.limit]
    compact = compact_rows(rows, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(compact, args.title), encoding="utf-8")
    print(f"Review rows: {len(compact)}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
