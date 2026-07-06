"""Generate a static bbox annotation page for topology v1 multi-panel pages."""

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
DEFAULT_FINDINGS = INDEX_DIR / "topology_v1_pilot_multipanel_findings.csv"
DEFAULT_DRAWING_MANIFEST = INDEX_DIR / "final_drawing_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_multipanel_split_review.html"


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


def compact_rows(
    finding_rows: Iterable[Dict[str, str]],
    drawing_rows: Iterable[Dict[str, str]],
    html_path: Path,
) -> List[Dict[str, str]]:
    drawings = {row["drawing_key"]: row for row in drawing_rows}
    compact: List[Dict[str, str]] = []
    for row in finding_rows:
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
                "v0_net_count": row.get("v0_net_count", ""),
                "v1_net_count": row.get("v1_net_count", ""),
                "intersection_count": row.get("intersection_count", ""),
                "manual_visual_finding": row.get("manual_visual_finding", ""),
                "recommended_action": row.get("recommended_action", ""),
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
      --accent: #175cd3;
      --danger: #b42318;
      --ok: #0f7b45;
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
      align-items: center;
      gap: 8px;
    }}
    button, select, input[type="search"] {{
      height: 34px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0 10px;
      background: #fff;
      color: var(--ink);
    }}
    button {{
      cursor: pointer;
      font-weight: 550;
    }}
    button.primary {{
      background: var(--dark);
      color: #fff;
      border-color: var(--dark);
    }}
    button.danger {{
      color: var(--danger);
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
      grid-template-columns: 1fr 360px;
      gap: 14px;
      align-items: start;
    }}
    .viewer, .side {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    .viewer {{
      min-height: 520px;
      overflow: auto;
      padding: 10px;
    }}
    .canvas-wrap {{
      position: relative;
      display: inline-block;
      min-width: 320px;
      min-height: 240px;
      background: #fff;
      border: 1px solid #edf0f5;
    }}
    .canvas-wrap img {{
      display: block;
      max-width: min(100%, 1400px);
      max-height: 82vh;
      object-fit: contain;
    }}
    svg.overlay {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      cursor: crosshair;
    }}
    .rect {{
      fill: rgba(23, 92, 211, 0.10);
      stroke: var(--accent);
      stroke-width: 2;
    }}
    .rect.active {{
      stroke: var(--danger);
      fill: rgba(180, 35, 24, 0.08);
    }}
    .side {{
      padding: 12px;
      display: grid;
      gap: 10px;
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
      font-size: 16px;
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
    .panel-list {{
      display: grid;
      gap: 6px;
      max-height: 320px;
      overflow: auto;
    }}
    .panel-row {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      cursor: pointer;
      display: grid;
      gap: 4px;
      font-size: 12px;
    }}
    .panel-row.active {{
      border-color: var(--danger);
      background: #fff7f6;
    }}
    .panel-row code {{
      color: var(--muted);
      word-break: break-all;
    }}
    textarea {{
      width: 100%;
      min-height: 64px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font-family: inherit;
    }}
    .kv {{
      display: grid;
      grid-template-columns: 84px minmax(0, 1fr);
      gap: 5px 8px;
      color: var(--muted);
      font-size: 12px;
    }}
    .kv code {{
      color: var(--ink);
      word-break: break-all;
      white-space: pre-wrap;
    }}
    @media (max-width: 1040px) {{
      main {{ grid-template-columns: 1fr; }}
      .stats {{ width: 100%; margin-left: 0; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{escaped_title}</h1>
    <div class="toolbar">
      <select id="drawingSelect"></select>
      <input id="search" type="search" placeholder="搜索 drawing key" />
      <button id="prevBtn">上一张</button>
      <button id="nextBtn">下一张</button>
      <button id="deleteBtn" class="danger">删除选中框</button>
      <button id="clearBtn" class="danger">清空本图</button>
      <button id="exportCsv" class="primary">导出 CSV</button>
      <span id="stats" class="stats"></span>
    </div>
  </header>
  <main>
    <section class="viewer">
      <div class="canvas-wrap" id="canvasWrap">
        <img id="image" alt="">
        <svg id="overlay" class="overlay"></svg>
      </div>
    </section>
    <aside class="side">
      <div class="title"><strong id="drawingKey"></strong></div>
      <div class="badges" id="badges"></div>
      <div class="metrics">
        <div class="metric"><strong id="v0Nets"></strong><span>v0 nets</span></div>
        <div class="metric"><strong id="v1Nets"></strong><span>v1 nets</span></div>
        <div class="metric"><strong id="intersections"></strong><span>intersections</span></div>
      </div>
      <div class="panel-list" id="panelList"></div>
      <textarea id="comment" placeholder="备注"></textarea>
      <div class="kv">
        <span>image</span><code id="imageMeta"></code>
        <span>png</span><code id="pngPath"></code>
      </div>
    </aside>
  </main>
  <script>
    const rows = {data_json};
    const storageKey = "industrial-diagram-topology-multipanel-split-v1";
    let state = loadState();
    let currentIndex = 0;
    let selectedPanelIndex = -1;
    let dragStart = null;
    let draftRect = null;

    function loadState() {{
      try {{ return JSON.parse(localStorage.getItem(storageKey) || "{{}}"); }}
      catch {{ return {{}}; }}
    }}
    function saveState() {{
      localStorage.setItem(storageKey, JSON.stringify(state));
      renderStats();
    }}
    function entry(key) {{
      if (!state[key]) state[key] = {{ panels: [], comment: "" }};
      return state[key];
    }}
    function currentRow() {{ return rows[currentIndex]; }}
    function currentEntry() {{ return entry(currentRow().drawing_key); }}
    function imageScale() {{
      const img = document.getElementById("image");
      const rect = img.getBoundingClientRect();
      return {{
        x: img.naturalWidth ? rect.width / img.naturalWidth : 1,
        y: img.naturalHeight ? rect.height / img.naturalHeight : 1,
        w: rect.width,
        h: rect.height,
        naturalW: img.naturalWidth,
        naturalH: img.naturalHeight
      }};
    }}
    function clientToImage(event) {{
      const img = document.getElementById("image");
      const rect = img.getBoundingClientRect();
      const scale = imageScale();
      const x = Math.max(0, Math.min(scale.naturalW, (event.clientX - rect.left) / scale.x));
      const y = Math.max(0, Math.min(scale.naturalH, (event.clientY - rect.top) / scale.y));
      return {{ x, y }};
    }}
    function normalizedRect(a, b) {{
      const x0 = Math.min(a.x, b.x);
      const y0 = Math.min(a.y, b.y);
      const x1 = Math.max(a.x, b.x);
      const y1 = Math.max(a.y, b.y);
      return {{ x0, y0, x1, y1 }};
    }}
    function rectToString(rect) {{
      return [rect.x0, rect.y0, rect.x1, rect.y1].map(v => Number(v).toFixed(1)).join(",");
    }}
    function setCurrentIndex(index) {{
      currentIndex = Math.max(0, Math.min(rows.length - 1, index));
      selectedPanelIndex = -1;
      render();
    }}
    function renderSelect() {{
      const select = document.getElementById("drawingSelect");
      select.innerHTML = "";
      rows.forEach((row, index) => {{
        const option = document.createElement("option");
        option.value = String(index);
        option.textContent = `${{index + 1}} / ${{rows.length}}  ${{row.drawing_id || row.drawing_key}}`;
        select.appendChild(option);
      }});
      select.value = String(currentIndex);
    }}
    function renderStats() {{
      const labeled = rows.filter(row => entry(row.drawing_key).panels.length > 0).length;
      const panelCount = rows.reduce((sum, row) => sum + entry(row.drawing_key).panels.length, 0);
      document.getElementById("stats").textContent = `已框图纸 ${{labeled}} / ${{rows.length}} | panels ${{panelCount}}`;
    }}
    function renderOverlay() {{
      const overlay = document.getElementById("overlay");
      const scale = imageScale();
      overlay.setAttribute("viewBox", `0 0 ${{scale.w}} ${{scale.h}}`);
      overlay.innerHTML = "";
      currentEntry().panels.forEach((panel, index) => {{
        const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        r.setAttribute("x", panel.x0 * scale.x);
        r.setAttribute("y", panel.y0 * scale.y);
        r.setAttribute("width", Math.max(1, (panel.x1 - panel.x0) * scale.x));
        r.setAttribute("height", Math.max(1, (panel.y1 - panel.y0) * scale.y));
        r.setAttribute("class", "rect" + (index === selectedPanelIndex ? " active" : ""));
        r.addEventListener("click", event => {{
          event.stopPropagation();
          selectedPanelIndex = index;
          renderSide();
          renderOverlay();
        }});
        overlay.appendChild(r);
      }});
      if (draftRect) {{
        const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        r.setAttribute("x", draftRect.x0 * scale.x);
        r.setAttribute("y", draftRect.y0 * scale.y);
        r.setAttribute("width", Math.max(1, (draftRect.x1 - draftRect.x0) * scale.x));
        r.setAttribute("height", Math.max(1, (draftRect.y1 - draftRect.y0) * scale.y));
        r.setAttribute("class", "rect active");
        overlay.appendChild(r);
      }}
    }}
    function renderSide() {{
      const row = currentRow();
      const e = currentEntry();
      document.getElementById("drawingKey").textContent = row.drawing_key;
      document.getElementById("badges").innerHTML = [
        `<span class="badge">${{row.phase}}</span>`,
        `<span class="badge">${{row.split}}</span>`,
        `<span class="badge">${{row.manual_visual_finding}}</span>`
      ].join("");
      document.getElementById("v0Nets").textContent = row.v0_net_count || "0";
      document.getElementById("v1Nets").textContent = row.v1_net_count || "0";
      document.getElementById("intersections").textContent = row.intersection_count || "0";
      document.getElementById("comment").value = e.comment || "";
      const img = document.getElementById("image");
      document.getElementById("imageMeta").textContent = `${{img.naturalWidth || 0}} x ${{img.naturalHeight || 0}}`;
      document.getElementById("pngPath").textContent = row.png_path || "";
      const panelList = document.getElementById("panelList");
      panelList.innerHTML = "";
      e.panels.forEach((panel, index) => {{
        const item = document.createElement("div");
        item.className = "panel-row" + (index === selectedPanelIndex ? " active" : "");
        item.innerHTML = `<strong>panel_${{String(index).padStart(3, "0")}}</strong><code>${{rectToString(panel)}}</code>`;
        item.addEventListener("click", () => {{
          selectedPanelIndex = index;
          renderSide();
          renderOverlay();
        }});
        panelList.appendChild(item);
      }});
    }}
    function render() {{
      const row = currentRow();
      renderSelect();
      const img = document.getElementById("image");
      img.src = row.image_src;
      img.alt = row.drawing_key;
      img.onload = () => {{
        renderSide();
        renderOverlay();
      }};
      renderSide();
      renderOverlay();
      renderStats();
    }}
    function exportCsv() {{
      const header = ["parent_drawing_key", "drawing_id", "split", "phase", "batch", "panel_index", "panel_id", "panel_bbox_png", "png_path", "status", "comment"];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const e = entry(row.drawing_key);
        e.panels.forEach((panel, index) => {{
          const panelId = `${{row.drawing_key}}#manual_panel_${{String(index).padStart(3, "0")}}`;
          const record = {{
            parent_drawing_key: row.drawing_key,
            drawing_id: row.drawing_id,
            split: row.split,
            phase: row.phase,
            batch: row.batch,
            panel_index: index,
            panel_id: panelId,
            panel_bbox_png: rectToString(panel),
            png_path: row.png_path,
            status: "accept",
            comment: e.comment || ""
          }};
          lines.push(header.map(key => csvEscape(record[key])).join(","));
        }});
      }}
      const blob = new Blob(["\\ufeff" + lines.join("\\n")], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "topology_multipanel_split_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    function csvEscape(value) {{
      const s = String(value ?? "");
      return /[",\\n\\r]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s;
    }}
    document.getElementById("drawingSelect").addEventListener("change", event => setCurrentIndex(Number(event.target.value)));
    document.getElementById("prevBtn").addEventListener("click", () => setCurrentIndex(currentIndex - 1));
    document.getElementById("nextBtn").addEventListener("click", () => setCurrentIndex(currentIndex + 1));
    document.getElementById("deleteBtn").addEventListener("click", () => {{
      if (selectedPanelIndex >= 0) {{
        currentEntry().panels.splice(selectedPanelIndex, 1);
        selectedPanelIndex = -1;
        saveState();
        render();
      }}
    }});
    document.getElementById("clearBtn").addEventListener("click", () => {{
      currentEntry().panels = [];
      selectedPanelIndex = -1;
      saveState();
      render();
    }});
    document.getElementById("comment").addEventListener("input", event => {{
      currentEntry().comment = event.target.value;
      saveState();
    }});
    document.getElementById("exportCsv").addEventListener("click", exportCsv);
    document.getElementById("search").addEventListener("input", event => {{
      const q = event.target.value.trim().toLowerCase();
      const index = rows.findIndex(row => (row.drawing_key + " " + row.drawing_id).toLowerCase().includes(q));
      if (index >= 0) setCurrentIndex(index);
    }});
    const overlay = document.getElementById("overlay");
    overlay.addEventListener("pointerdown", event => {{
      dragStart = clientToImage(event);
      draftRect = null;
      overlay.setPointerCapture(event.pointerId);
    }});
    overlay.addEventListener("pointermove", event => {{
      if (!dragStart) return;
      draftRect = normalizedRect(dragStart, clientToImage(event));
      renderOverlay();
    }});
    overlay.addEventListener("pointerup", event => {{
      if (!dragStart) return;
      const rect = normalizedRect(dragStart, clientToImage(event));
      dragStart = null;
      draftRect = null;
      if ((rect.x1 - rect.x0) >= 8 && (rect.y1 - rect.y0) >= 8) {{
        currentEntry().panels.push(rect);
        selectedPanelIndex = currentEntry().panels.length - 1;
        saveState();
      }}
      render();
    }});
    window.addEventListener("resize", renderOverlay);
    render();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings", type=Path, default=DEFAULT_FINDINGS)
    parser.add_argument("--drawing-manifest", type=Path, default=DEFAULT_DRAWING_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--title", default="Topology v1 Multi-Panel Split Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output = args.output.resolve()
    finding_rows = load_rows(args.findings)
    drawing_rows = load_rows(args.drawing_manifest)
    compact = compact_rows(finding_rows, drawing_rows, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(compact, args.title), encoding="utf-8")
    print(f"Split review rows: {len(compact)}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
