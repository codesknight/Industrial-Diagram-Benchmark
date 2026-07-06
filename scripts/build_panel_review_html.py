"""Generate a static HTML panel review sheet.

The HTML file embeds panel metadata and stores annotations in browser
localStorage. Reviewers can export labels as CSV without any server.
"""

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
DEFAULT_MANIFEST = ROOT / "data_index" / "panel_manifest.csv"
DEFAULT_OUTPUT = ROOT / "data_index" / "panel_review.html"


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing manifest: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def as_bool(value: str) -> bool:
    return str(value).lower() == "true"


def rel_image_path(path: str, html_path: Path) -> str:
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


def select_rows(rows: Iterable[Dict[str, str]], mode: str, limit: int | None) -> List[Dict[str, str]]:
    if mode == "review":
        selected = [row for row in rows if as_bool(row.get("needs_review", ""))]
    elif mode == "split":
        selected = [row for row in rows if row.get("split_method") != "full"]
    elif mode == "all":
        selected = list(rows)
    else:
        raise SystemExit(f"Unknown mode: {mode}")
    if limit:
        selected = selected[:limit]
    return selected


def compact_row(row: Dict[str, str], html_path: Path) -> Dict[str, str]:
    return {
        "panel_id": row["panel_id"],
        "parent_drawing_key": row["parent_drawing_key"],
        "panel_index": row["panel_index"],
        "panel_count": row["panel_count"],
        "split": row["split"],
        "phase": row["phase"],
        "batch": row["batch"],
        "split_method": row["split_method"],
        "panel_bbox_png": row["panel_bbox_png"],
        "panel_bbox_cad": row["panel_bbox_cad"],
        "panel_entity_count": row["panel_entity_count"],
        "panel_png_path": row["panel_png_path"],
        "image_src": rel_image_path(row["panel_png_path"], html_path),
        "needs_review": row["needs_review"],
        "notes": row.get("notes", ""),
    }


def render_html(rows: List[Dict[str, str]], output_path: Path, title: str) -> str:
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
      --border: #d7dde5;
      --ink: #111827;
      --muted: #667085;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --accept: #0f8a4b;
      --adjust: #b76a00;
      --reject: #ba1a1a;
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
      z-index: 3;
      background: rgba(255,255,255,0.96);
      border-bottom: 1px solid var(--border);
      padding: 12px 18px;
    }}
    h1 {{
      margin: 0 0 8px;
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
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0 10px;
      background: #fff;
      min-width: 160px;
    }}
    button {{
      height: 34px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0 12px;
      background: #fff;
      cursor: pointer;
      font-weight: 550;
    }}
    button.primary {{
      background: #111827;
      border-color: #111827;
      color: #fff;
    }}
    .stats {{
      margin-left: auto;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }}
    main {{
      padding: 18px;
      display: grid;
      gap: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      display: grid;
      grid-template-columns: minmax(340px, 1fr) 360px;
      min-height: 280px;
      overflow: hidden;
    }}
    .image-wrap {{
      min-height: 280px;
      background: #fdfdfd;
      display: flex;
      align-items: center;
      justify-content: center;
      border-right: 1px solid var(--border);
      overflow: auto;
      padding: 10px;
    }}
    .image-wrap img {{
      max-width: 100%;
      max-height: 76vh;
      object-fit: contain;
      border: 1px solid #eceff3;
      background: white;
    }}
    .meta {{
      padding: 12px;
      display: grid;
      gap: 10px;
      align-content: start;
    }}
    .id {{
      font-size: 13px;
      line-height: 1.35;
      word-break: break-all;
    }}
    .kv {{
      display: grid;
      grid-template-columns: 96px 1fr;
      gap: 4px 8px;
      font-size: 12px;
      color: var(--muted);
    }}
    .kv code {{
      color: var(--ink);
      white-space: pre-wrap;
      word-break: break-all;
    }}
    .choices {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
    }}
    .choice {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 6px;
      text-align: center;
      cursor: pointer;
      user-select: none;
      font-size: 13px;
      font-weight: 650;
    }}
    .choice[data-value="accept"].active {{ border-color: var(--accept); color: var(--accept); background: #eaf7ef; }}
    .choice[data-value="adjust"].active {{ border-color: var(--adjust); color: var(--adjust); background: #fff3df; }}
    .choice[data-value="reject"].active {{ border-color: var(--reject); color: var(--reject); background: #ffebeb; }}
    textarea {{
      width: 100%;
      min-height: 72px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font-family: inherit;
    }}
    .hidden {{ display: none; }}
    @media (max-width: 980px) {{
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
      <input id="search" type="search" placeholder="搜索 parent / panel id" />
      <select id="statusFilter">
        <option value="all">全部状态</option>
        <option value="unlabeled">未标注</option>
        <option value="accept">accept</option>
        <option value="adjust">adjust</option>
        <option value="reject">reject</option>
      </select>
      <select id="methodFilter">
        <option value="all">全部方法</option>
      </select>
      <button id="clearFilters">清除筛选</button>
      <button id="exportCsv" class="primary">导出 CSV</button>
      <span id="stats" class="stats"></span>
    </div>
  </header>
  <main id="list"></main>
  <script>
    const rows = {data_json};
    const storageKey = "industrial-diagram-panel-review-v1";
    let labels = loadLabels();

    function loadLabels() {{
      try {{ return JSON.parse(localStorage.getItem(storageKey) || "{{}}"); }}
      catch {{ return {{}}; }}
    }}
    function saveLabels() {{
      localStorage.setItem(storageKey, JSON.stringify(labels));
      renderStats();
    }}
    function csvEscape(value) {{
      const s = String(value ?? "");
      return /[",\\n\\r]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s;
    }}
    function labelFor(id) {{
      return labels[id] || {{ status: "", comment: "" }};
    }}
    function setStatus(id, status) {{
      labels[id] = {{ ...labelFor(id), status }};
      saveLabels();
      render();
    }}
    function setComment(id, comment) {{
      labels[id] = {{ ...labelFor(id), comment }};
      saveLabels();
    }}
    function filteredRows() {{
      const q = document.getElementById("search").value.trim().toLowerCase();
      const status = document.getElementById("statusFilter").value;
      const method = document.getElementById("methodFilter").value;
      return rows.filter(row => {{
        const label = labelFor(row.panel_id);
        const rowStatus = label.status || "unlabeled";
        const text = (row.panel_id + " " + row.parent_drawing_key).toLowerCase();
        return (!q || text.includes(q))
          && (status === "all" || status === rowStatus)
          && (method === "all" || method === row.split_method);
      }});
    }}
    function renderMethodFilter() {{
      const select = document.getElementById("methodFilter");
      const methods = [...new Set(rows.map(r => r.split_method))].sort();
      for (const method of methods) {{
        const option = document.createElement("option");
        option.value = method;
        option.textContent = method;
        select.appendChild(option);
      }}
    }}
    function renderStats() {{
      const counts = {{ accept: 0, adjust: 0, reject: 0, unlabeled: 0 }};
      for (const row of rows) {{
        const status = labelFor(row.panel_id).status || "unlabeled";
        counts[status] = (counts[status] || 0) + 1;
      }}
      const visible = filteredRows().length;
      document.getElementById("stats").textContent =
        `显示 ${{visible}} / ${{rows.length}} | accept ${{counts.accept}} | adjust ${{counts.adjust}} | reject ${{counts.reject}} | 未标注 ${{counts.unlabeled}}`;
    }}
    function render() {{
      const list = document.getElementById("list");
      list.innerHTML = "";
      for (const row of filteredRows()) {{
        const label = labelFor(row.panel_id);
        const card = document.createElement("section");
        card.className = "card";
        card.innerHTML = `
          <div class="image-wrap">
            <img src="${{row.image_src}}" alt="${{row.panel_id}}">
          </div>
          <div class="meta">
            <div class="id"><strong>${{row.panel_id}}</strong></div>
            <div class="choices">
              ${{["accept", "adjust", "reject"].map(status =>
                `<div class="choice ${{label.status === status ? "active" : ""}}" data-value="${{status}}">${{status}}</div>`
              ).join("")}}
            </div>
            <textarea placeholder="备注，例如裁剪偏移、漏切、过切、应合并..." data-comment>${{label.comment || ""}}</textarea>
            <div class="kv">
              <span>parent</span><code>${{row.parent_drawing_key}}</code>
              <span>method</span><code>${{row.split_method}}</code>
              <span>split</span><code>${{row.split}}</code>
              <span>panel</span><code>${{row.panel_index}} / ${{row.panel_count}}</code>
              <span>entities</span><code>${{row.panel_entity_count}}</code>
              <span>bbox_png</span><code>${{row.panel_bbox_png}}</code>
              <span>image</span><code>${{row.panel_png_path}}</code>
              <span>notes</span><code>${{row.notes || ""}}</code>
            </div>
          </div>
        `;
        card.querySelectorAll(".choice").forEach(el => {{
          el.addEventListener("click", () => setStatus(row.panel_id, el.dataset.value));
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
        "panel_id", "parent_drawing_key", "panel_index", "panel_count", "split",
        "split_method", "panel_bbox_png", "panel_png_path", "status", "comment"
      ];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const label = labelFor(row.panel_id);
        lines.push(header.map(key => {{
          if (key === "status") return csvEscape(label.status || "");
          if (key === "comment") return csvEscape(label.comment || "");
          return csvEscape(row[key]);
        }}).join(","));
      }}
      const blob = new Blob(["\\ufeff" + lines.join("\\n")], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "panel_review_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}

    document.getElementById("search").addEventListener("input", render);
    document.getElementById("statusFilter").addEventListener("change", render);
    document.getElementById("methodFilter").addEventListener("change", render);
    document.getElementById("clearFilters").addEventListener("click", () => {{
      document.getElementById("search").value = "";
      document.getElementById("statusFilter").value = "all";
      document.getElementById("methodFilter").value = "all";
      render();
    }});
    document.getElementById("exportCsv").addEventListener("click", exportCsv);
    document.addEventListener("keydown", event => {{
      if (event.target.tagName === "TEXTAREA" || event.target.tagName === "INPUT") return;
      const first = filteredRows()[0];
      if (!first) return;
      if (event.key.toLowerCase() === "a") setStatus(first.panel_id, "accept");
      if (event.key.toLowerCase() === "j") setStatus(first.panel_id, "adjust");
      if (event.key.toLowerCase() === "r") setStatus(first.panel_id, "reject");
    }});

    renderMethodFilter();
    render();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=["review", "split", "all"], default="review")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--title", default="Industrial Diagram Panel Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.manifest = args.manifest.resolve()
    args.output = args.output.resolve()

    rows = load_rows(args.manifest)
    selected = select_rows(rows, args.mode, args.limit)
    compact = [compact_row(row, args.output) for row in selected]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(compact, args.output, args.title), encoding="utf-8")

    print(f"Review rows: {len(compact)}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
