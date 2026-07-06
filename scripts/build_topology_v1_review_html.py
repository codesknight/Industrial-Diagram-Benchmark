"""Generate a static HTML review sheet for Topology Graph v1 pilot."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_PILOT_MANIFEST = INDEX_DIR / "topology_v1_pilot_manifest.csv"
DEFAULT_DRAWING_MANIFEST = INDEX_DIR / "final_drawing_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_v1_pilot_review.html"


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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


def as_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def compact_rows(
    pilot_rows: Iterable[Dict[str, str]],
    drawing_rows: Iterable[Dict[str, str]],
    html_path: Path,
) -> List[Dict[str, object]]:
    drawings = {row["drawing_key"]: row for row in drawing_rows}
    compact: List[Dict[str, object]] = []
    for row in pilot_rows:
        drawing = drawings.get(row["drawing_key"], {})
        png_path = drawing.get("png_path", "")
        v0_edges = as_int(row.get("v0_edge_count", ""))
        v1_edges = as_int(row.get("v1_edge_count", ""))
        v0_nets = as_int(row.get("v0_net_count", ""))
        v1_nets = as_int(row.get("v1_net_count", ""))
        v0_iso = as_float(row.get("v0_isolated_edge_ratio", ""))
        v1_iso = as_float(row.get("v1_isolated_edge_ratio", ""))
        compact.append(
            {
                "drawing_key": row["drawing_key"],
                "drawing_id": drawing.get("drawing_id", Path(row["drawing_key"]).name),
                "split": row.get("split", drawing.get("split", "")),
                "phase": row.get("phase", drawing.get("phase", "")),
                "batch": drawing.get("batch", ""),
                "png_path": png_path,
                "image_src": rel_asset_path(png_path, html_path) if png_path else "",
                "topology_v0_json_path": row.get("topology_v0_json_path", ""),
                "topology_v0_json_src": rel_asset_path(row.get("topology_v0_json_path", ""), html_path)
                if row.get("topology_v0_json_path")
                else "",
                "topology_v1_json_path": row.get("topology_v1_json_path", ""),
                "topology_v1_json_src": rel_asset_path(row.get("topology_v1_json_path", ""), html_path)
                if row.get("topology_v1_json_path")
                else "",
                "status": row.get("status", ""),
                "review_label": row.get("review_label", ""),
                "v0_node_count": as_int(row.get("v0_node_count", "")),
                "v0_edge_count": v0_edges,
                "v0_net_count": v0_nets,
                "v0_isolated_edge_ratio": v0_iso,
                "v0_largest_net_edge_ratio": as_float(row.get("v0_largest_net_edge_ratio", "")),
                "v1_node_count": as_int(row.get("v1_node_count", "")),
                "v1_edge_count": v1_edges,
                "v1_net_count": v1_nets,
                "v1_isolated_edge_ratio": v1_iso,
                "v1_largest_net_edge_ratio": as_float(row.get("v1_largest_net_edge_ratio", "")),
                "edge_delta": v1_edges - v0_edges,
                "net_delta": v1_nets - v0_nets,
                "isolated_delta": round(v1_iso - v0_iso, 4),
                "intersection_count": as_int(row.get("intersection_count", "")),
                "split_event_count": as_int(row.get("split_event_count", "")),
                "split_short_segments": as_int(row.get("split_short_segments", "")),
                "effective_endpoint_tolerance": row.get("effective_endpoint_tolerance", ""),
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
      background: rgba(255, 255, 255, 0.96);
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
      grid-template-columns: minmax(420px, 1fr) 480px;
      min-height: 390px;
      overflow: hidden;
    }}
    .image-wrap {{
      min-height: 390px;
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
      max-height: 80vh;
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
      font-size: 12px;
      color: var(--muted);
      background: #fff;
    }}
    .badge.review {{ color: var(--warn); border-color: #fedf89; background: #fffbeb; }}
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
      line-height: 1.15;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .metric span {{
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 11px;
    }}
    .compare {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 8px;
    }}
    .compare .metric strong {{ font-size: 15px; }}
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
      color: var(--ink);
    }}
    .kv {{
      display: grid;
      grid-template-columns: 120px minmax(0, 1fr);
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
    @media (max-width: 1120px) {{
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
      <input id="search" type="search" placeholder="搜索 drawing key" />
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
    const storageKey = "industrial-diagram-topology-v1-pilot-review-v1";
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
        const saved = labelFor(row.drawing_key);
        const label = saved.label || "unlabeled";
        const text = (row.drawing_key + " " + row.drawing_id).toLowerCase();
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
        const label = labelFor(row.drawing_key).label || "unlabeled";
        counts[label] = (counts[label] || 0) + 1;
      }}
      document.getElementById("stats").textContent =
        `显示 ${{filteredRows().length}} / ${{rows.length}} | accept ${{counts.accept_v1}} | over ${{counts.over_connected}} | fragmented ${{counts.still_fragmented}} | terminal ${{counts.needs_terminal_anchor}} | bad ${{counts.bad_geometry}} | 未标注 ${{counts.unlabeled}}`;
    }}
    function imageHtml(row) {{
      if (!row.image_src) return `<div class="missing-image">missing png path</div>`;
      return `<img src="${{row.image_src}}" alt="${{row.drawing_key}}">`;
    }}
    function badgeHtml(row) {{
      return [
        `<span class="badge">${{row.phase || "-"}}</span>`,
        `<span class="badge">${{row.split || "-"}}</span>`,
        `<span class="badge">${{row.status || "-"}}</span>`,
        `<span class="badge review">${{row.review_label || "-"}}</span>`
      ].join("");
    }}
    function render() {{
      const list = document.getElementById("list");
      list.innerHTML = "";
      for (const row of filteredRows()) {{
        const saved = labelFor(row.drawing_key);
        const card = document.createElement("section");
        card.className = "card";
        card.innerHTML = `
          <div class="image-wrap">${{imageHtml(row)}}</div>
          <div class="meta">
            <div class="title"><strong>${{row.drawing_key}}</strong></div>
            <div class="badges">${{badgeHtml(row)}}</div>
            <div class="compare">
              <div class="metric"><strong>${{row.v0_edge_count}} -> ${{row.v1_edge_count}}</strong><span>edges</span></div>
              <div class="metric"><strong>${{row.v0_net_count}} -> ${{row.v1_net_count}}</strong><span>nets</span></div>
              <div class="metric"><strong>${{row.v0_isolated_edge_ratio}} -> ${{row.v1_isolated_edge_ratio}}</strong><span>isolated ratio</span></div>
            </div>
            <div class="metrics">
              <div class="metric"><strong>${{row.edge_delta}}</strong><span>edge delta</span></div>
              <div class="metric"><strong>${{row.net_delta}}</strong><span>net delta</span></div>
              <div class="metric"><strong>${{row.intersection_count}}</strong><span>intersections</span></div>
              <div class="metric"><strong>${{row.split_event_count}}</strong><span>split events</span></div>
              <div class="metric"><strong>${{row.v1_node_count}}</strong><span>v1 nodes</span></div>
              <div class="metric"><strong>${{row.v1_largest_net_edge_ratio}}</strong><span>v1 largest ratio</span></div>
              <div class="metric"><strong>${{row.effective_endpoint_tolerance}}</strong><span>tolerance</span></div>
              <div class="metric"><strong>${{row.split_short_segments}}</strong><span>short splits</span></div>
            </div>
            <div class="choices">
              ${{labelOptions.map(option =>
                `<div class="choice ${{saved.label === option ? "active" : ""}}" data-value="${{option}}">${{option}}</div>`
              ).join("")}}
            </div>
            <textarea placeholder="备注：例如交叉线误连、仍然碎、需要端子锚点、v1可接受..." data-comment>${{saved.comment || ""}}</textarea>
            <div class="kv">
              <span>drawing_id</span><code>${{row.drawing_id || ""}}</code>
              <span>batch</span><code>${{row.batch || ""}}</code>
              <span>png_path</span><code>${{row.png_path || ""}}</code>
              <span>v0_json</span><a href="${{row.topology_v0_json_src || "#"}}" target="_blank">${{row.topology_v0_json_path || ""}}</a>
              <span>v1_json</span><a href="${{row.topology_v1_json_src || "#"}}" target="_blank">${{row.topology_v1_json_path || ""}}</a>
            </div>
          </div>
        `;
        card.querySelectorAll(".choice").forEach(el => {{
          el.addEventListener("click", () => setLabel(row.drawing_key, el.dataset.value));
        }});
        card.querySelector("[data-comment]").addEventListener("input", event => {{
          setComment(row.drawing_key, event.target.value);
        }});
        list.appendChild(card);
      }}
      renderStats();
    }}
    function exportCsv() {{
      const header = [
        "drawing_key", "drawing_id", "split", "phase", "batch", "status", "review_label",
        "v0_edge_count", "v1_edge_count", "edge_delta",
        "v0_net_count", "v1_net_count", "net_delta",
        "v0_isolated_edge_ratio", "v1_isolated_edge_ratio", "isolated_delta",
        "v1_largest_net_edge_ratio", "intersection_count", "split_event_count",
        "topology_v0_json_path", "topology_v1_json_path", "png_path",
        "v1_review_label", "comment"
      ];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const saved = labelFor(row.drawing_key);
        lines.push(header.map(key => {{
          if (key === "v1_review_label") return csvEscape(saved.label || "");
          if (key === "comment") return csvEscape(saved.comment || "");
          return csvEscape(row[key]);
        }}).join(","));
      }}
      const blob = new Blob(["\\ufeff" + lines.join("\\n")], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "topology_v1_pilot_review_labels.csv";
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
    parser.add_argument("--pilot-manifest", type=Path, default=DEFAULT_PILOT_MANIFEST)
    parser.add_argument("--drawing-manifest", type=Path, default=DEFAULT_DRAWING_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--title", default="Industrial Diagram Topology v1 Pilot Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output = args.output.resolve()
    pilot_rows = load_rows(args.pilot_manifest)
    if args.limit:
        pilot_rows = pilot_rows[: args.limit]
    drawing_rows = load_rows(args.drawing_manifest)
    compact = compact_rows(pilot_rows, drawing_rows, args.output)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(compact, args.title), encoding="utf-8")

    print(f"Review rows: {len(compact)}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
