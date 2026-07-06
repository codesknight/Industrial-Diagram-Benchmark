"""Generate a static HTML review sheet for Topology Graph v0.

The review page joins topology rows with drawing-level PNG paths, stores labels
in browser localStorage, and exports reviewer decisions as CSV.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_TOPOLOGY_MANIFEST = INDEX_DIR / "topology_graph_manifest.csv"
DEFAULT_QUALITY_REVIEW = INDEX_DIR / "topology_quality_review.csv"
DEFAULT_DRAWING_MANIFEST = INDEX_DIR / "final_drawing_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_review.html"


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


def select_topology_rows(args: argparse.Namespace) -> List[Dict[str, str]]:
    if args.mode == "review":
        rows = load_rows(args.quality_review)
    elif args.mode == "all":
        rows = load_rows(args.topology_manifest)
    else:
        raise SystemExit(f"Unknown mode: {args.mode}")
    if args.limit:
        rows = rows[: args.limit]
    return rows


def compact_rows(
    topology_rows: Iterable[Dict[str, str]],
    drawing_rows: Iterable[Dict[str, str]],
    html_path: Path,
) -> List[Dict[str, str]]:
    drawings = {row["drawing_key"]: row for row in drawing_rows}
    compact: List[Dict[str, str]] = []

    for row in topology_rows:
        drawing = drawings.get(row["drawing_key"], {})
        png_path = drawing.get("png_path", "")
        compact.append(
            {
                "drawing_key": row["drawing_key"],
                "drawing_id": drawing.get("drawing_id", Path(row["drawing_key"]).name),
                "split": row.get("split", drawing.get("split", "")),
                "phase": row.get("phase", drawing.get("phase", "")),
                "batch": drawing.get("batch", ""),
                "png_path": png_path,
                "image_src": rel_asset_path(png_path, html_path) if png_path else "",
                "topology_json_path": row.get("topology_json_path", ""),
                "topology_json_src": rel_asset_path(row.get("topology_json_path", ""), html_path)
                if row.get("topology_json_path")
                else "",
                "status": row.get("status", ""),
                "topology_ready": row.get("topology_ready", ""),
                "edge_count": row.get("edge_count", ""),
                "node_count": row.get("node_count", ""),
                "net_count": row.get("net_count", ""),
                "largest_net_edge_ratio": row.get("largest_net_edge_ratio", ""),
                "isolated_edge_ratio": row.get("isolated_edge_ratio", ""),
                "quality_flags": row.get("quality_flags", ""),
                "largest_net_edges": row.get("largest_net_edges", ""),
                "isolated_edge_count": row.get("isolated_edge_count", ""),
                "graph_bbox": row.get("graph_bbox", ""),
            }
        )
    return compact


def render_html(rows: List[Dict[str, str]], title: str) -> str:
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
      line-height: 1.2;
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
      grid-template-columns: minmax(420px, 1fr) 430px;
      overflow: hidden;
      min-height: 360px;
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
    .missing-image {{
      color: var(--muted);
      font-size: 13px;
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
    .badge.flag {{ color: var(--bad); border-color: #f4b8b1; background: #fff4f2; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
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
      font-size: 18px;
      line-height: 1.15;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .metric span {{
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 12px;
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
    .choice.active[data-value="accept_v0"] {{ border-color: var(--ok); color: var(--ok); background: #ecfdf3; }}
    .choice.active[data-value="needs_intersection_split"] {{ border-color: var(--warn); color: var(--warn); background: #fff7e8; }}
    .choice.active[data-value="needs_terminal_anchor"] {{ border-color: var(--info); color: var(--info); background: #eff6ff; }}
    .choice.active[data-value="not_topology_target"] {{ border-color: #7a5af8; color: #5925dc; background: #f4f3ff; }}
    .choice.active[data-value="bad_geometry"] {{ border-color: var(--bad); color: var(--bad); background: #fff1f0; }}
    textarea {{
      width: 100%;
      min-height: 72px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font-family: inherit;
      color: var(--ink);
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
      <input id="search" type="search" placeholder="搜索 drawing key" />
      <select id="labelFilter">
        <option value="all">全部标注</option>
        <option value="unlabeled">未标注</option>
        <option value="accept_v0">accept_v0</option>
        <option value="needs_intersection_split">needs_intersection_split</option>
        <option value="needs_terminal_anchor">needs_terminal_anchor</option>
        <option value="not_topology_target">not_topology_target</option>
        <option value="bad_geometry">bad_geometry</option>
      </select>
      <select id="flagFilter">
        <option value="all">全部 flag</option>
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
    const storageKey = "industrial-diagram-topology-review-v1";
    const labelOptions = [
      "accept_v0",
      "needs_intersection_split",
      "needs_terminal_anchor",
      "not_topology_target",
      "bad_geometry"
    ];
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
    function rowFlags(row) {{
      return String(row.quality_flags || "").split(";").filter(Boolean);
    }}
    function filteredRows() {{
      const q = document.getElementById("search").value.trim().toLowerCase();
      const labelFilter = document.getElementById("labelFilter").value;
      const flagFilter = document.getElementById("flagFilter").value;
      const phaseFilter = document.getElementById("phaseFilter").value;
      return rows.filter(row => {{
        const saved = labelFor(row.drawing_key);
        const label = saved.label || "unlabeled";
        const text = (row.drawing_key + " " + row.drawing_id).toLowerCase();
        const flags = rowFlags(row);
        return (!q || text.includes(q))
          && (labelFilter === "all" || labelFilter === label)
          && (flagFilter === "all" || flags.includes(flagFilter))
          && (phaseFilter === "all" || row.phase === phaseFilter);
      }});
    }}
    function renderFilters() {{
      const flagSelect = document.getElementById("flagFilter");
      const flags = [...new Set(rows.flatMap(rowFlags))].sort();
      for (const flag of flags) {{
        const option = document.createElement("option");
        option.value = flag;
        option.textContent = flag;
        flagSelect.appendChild(option);
      }}
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
        `显示 ${{filteredRows().length}} / ${{rows.length}} | accept ${{counts.accept_v0}} | intersection ${{counts.needs_intersection_split}} | terminal ${{counts.needs_terminal_anchor}} | other ${{counts.not_topology_target + counts.bad_geometry}} | 未标注 ${{counts.unlabeled}}`;
    }}
    function badgeHtml(row) {{
      const flags = rowFlags(row);
      const basics = [
        `<span class="badge">${{row.phase || "-"}}</span>`,
        `<span class="badge">${{row.split || "-"}}</span>`,
        `<span class="badge">${{row.status || "-"}}</span>`,
        `<span class="badge">${{row.topology_ready === "True" ? "topology_ready" : "not_topology_ready"}}</span>`
      ];
      const flagBadges = flags.length
        ? flags.map(flag => `<span class="badge flag">${{flag}}</span>`)
        : [`<span class="badge">no flag</span>`];
      return basics.concat(flagBadges).join("");
    }}
    function imageHtml(row) {{
      if (!row.image_src) return `<div class="missing-image">missing png path</div>`;
      return `<img src="${{row.image_src}}" alt="${{row.drawing_key}}">`;
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
            <div class="metrics">
              <div class="metric"><strong>${{row.edge_count || 0}}</strong><span>edges</span></div>
              <div class="metric"><strong>${{row.node_count || 0}}</strong><span>nodes</span></div>
              <div class="metric"><strong>${{row.net_count || 0}}</strong><span>nets</span></div>
              <div class="metric"><strong>${{row.isolated_edge_ratio || 0}}</strong><span>isolated ratio</span></div>
              <div class="metric"><strong>${{row.largest_net_edge_ratio || 0}}</strong><span>largest ratio</span></div>
              <div class="metric"><strong>${{row.largest_net_edges || 0}}</strong><span>largest net</span></div>
            </div>
            <div class="choices">
              ${{labelOptions.map(option =>
                `<div class="choice ${{saved.label === option ? "active" : ""}}" data-value="${{option}}">${{option}}</div>`
              ).join("")}}
            </div>
            <textarea placeholder="备注：例如需要交点拆分、端子锚点、图纸不适合拓扑任务、几何异常..." data-comment>${{saved.comment || ""}}</textarea>
            <div class="kv">
              <span>drawing_id</span><code>${{row.drawing_id || ""}}</code>
              <span>batch</span><code>${{row.batch || ""}}</code>
              <span>graph_bbox</span><code>${{row.graph_bbox || ""}}</code>
              <span>png_path</span><code>${{row.png_path || ""}}</code>
              <span>topology_json</span><a href="${{row.topology_json_src || "#"}}" target="_blank">${{row.topology_json_path || ""}}</a>
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
        "drawing_key", "drawing_id", "split", "phase", "batch", "status", "topology_ready",
        "edge_count", "node_count", "net_count", "largest_net_edge_ratio",
        "isolated_edge_ratio", "quality_flags", "topology_json_path",
        "png_path", "review_label", "comment"
      ];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const saved = labelFor(row.drawing_key);
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
      a.download = "topology_review_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}

    document.getElementById("search").addEventListener("input", render);
    document.getElementById("labelFilter").addEventListener("change", render);
    document.getElementById("flagFilter").addEventListener("change", render);
    document.getElementById("phaseFilter").addEventListener("change", render);
    document.getElementById("clearFilters").addEventListener("click", () => {{
      document.getElementById("search").value = "";
      document.getElementById("labelFilter").value = "all";
      document.getElementById("flagFilter").value = "all";
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
    parser.add_argument("--topology-manifest", type=Path, default=DEFAULT_TOPOLOGY_MANIFEST)
    parser.add_argument("--quality-review", type=Path, default=DEFAULT_QUALITY_REVIEW)
    parser.add_argument("--drawing-manifest", type=Path, default=DEFAULT_DRAWING_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=["review", "all"], default="review")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--title", default="Industrial Diagram Topology Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output = args.output.resolve()

    topology_rows = select_topology_rows(args)
    drawing_rows = load_rows(args.drawing_manifest)
    compact = compact_rows(topology_rows, drawing_rows, args.output)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(compact, args.title), encoding="utf-8")

    print(f"Review rows: {len(compact)}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
