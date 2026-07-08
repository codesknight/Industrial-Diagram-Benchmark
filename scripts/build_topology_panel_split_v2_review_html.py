"""Generate a bbox annotation page for Topology Panel Split v2."""

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
DEFAULT_INPUT = INDEX_DIR / "topology_panel_v1_needs_panel_split.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_split_v2_review.html"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_split_v2_review_summary.json"


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


def compact_rows(rows: Iterable[Dict[str, str]], html_path: Path) -> List[Dict[str, str]]:
    compact: List[Dict[str, str]] = []
    for row in rows:
        png_path = row.get("panel_png_path", "")
        compact.append(
            {
                "parent_panel_id": row.get("panel_id", ""),
                "parent_drawing_key": row.get("parent_drawing_key", ""),
                "split": row.get("split", ""),
                "phase": row.get("phase", ""),
                "batch": row.get("batch", ""),
                "split_method": row.get("split_method", ""),
                "severity": row.get("severity", ""),
                "anomaly_type": row.get("anomaly_type", ""),
                "model_review_label": row.get("model_review_label", ""),
                "model_confidence": row.get("model_confidence", ""),
                "model_reason": row.get("model_reason", ""),
                "review_comment": row.get("topology_panel_v1_review_comment", ""),
                "panel_png_path": png_path,
                "image_src": rel_asset_path(png_path, html_path),
                "panel_bbox_cad": row.get("panel_bbox_cad", ""),
                "panel_entity_count": row.get("panel_entity_count", ""),
                "v1_edge_count": row.get("v1_edge_count", ""),
                "v1_net_count": row.get("v1_net_count", ""),
                "intersection_count": row.get("intersection_count", ""),
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
      background: rgba(255,255,255,0.97);
      border-bottom: 1px solid var(--border);
    }}
    h1 {{ margin: 0 0 10px; font-size: 20px; font-weight: 650; letter-spacing: 0; }}
    .toolbar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }}
    button, select, input[type="search"] {{
      height: 34px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0 10px;
      background: #fff;
      color: var(--ink);
    }}
    button {{ cursor: pointer; font-weight: 550; }}
    button.primary {{ background: var(--dark); color: #fff; border-color: var(--dark); }}
    button.danger {{ color: var(--danger); }}
    .stats {{ margin-left: auto; color: var(--muted); font-size: 13px; white-space: nowrap; }}
    main {{
      padding: 16px;
      display: grid;
      grid-template-columns: 1fr 390px;
      gap: 14px;
      align-items: start;
    }}
    .viewer, .side {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; }}
    .viewer {{ min-height: 540px; overflow: auto; padding: 10px; }}
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
    svg.overlay {{ position: absolute; inset: 0; width: 100%; height: 100%; cursor: crosshair; }}
    .rect {{ fill: rgba(23, 92, 211, 0.10); stroke: var(--accent); stroke-width: 2; }}
    .rect.active {{ stroke: var(--danger); fill: rgba(180, 35, 24, 0.08); }}
    .side {{ padding: 12px; display: grid; gap: 10px; }}
    .title {{ font-size: 13px; line-height: 1.4; word-break: break-all; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 3px 8px;
      color: var(--muted);
      font-size: 12px;
      background: #fff;
    }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }}
    .metric {{ border: 1px solid var(--border); border-radius: 8px; padding: 8px; min-width: 0; }}
    .metric strong {{ display: block; font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .metric span {{ display: block; margin-top: 3px; color: var(--muted); font-size: 11px; }}
    .panel-list {{ display: grid; gap: 6px; max-height: 320px; overflow: auto; }}
    .panel-row {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      cursor: pointer;
      display: grid;
      gap: 4px;
      font-size: 12px;
    }}
    .panel-row.active {{ border-color: var(--danger); background: #fff7f6; }}
    .panel-row code {{ color: var(--muted); word-break: break-all; }}
    textarea {{
      width: 100%;
      min-height: 64px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font-family: inherit;
    }}
    .kv {{ display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 5px 8px; color: var(--muted); font-size: 12px; }}
    .kv code {{ color: var(--ink); word-break: break-all; white-space: pre-wrap; }}
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
      <select id="panelSelect"></select>
      <input id="search" type="search" placeholder="搜索 parent panel / drawing" />
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
      <div class="title"><strong id="parentPanelId"></strong></div>
      <div class="badges" id="badges"></div>
      <div class="metrics">
        <div class="metric"><strong id="edgeCount"></strong><span>edges</span></div>
        <div class="metric"><strong id="netCount"></strong><span>nets</span></div>
        <div class="metric"><strong id="intersections"></strong><span>intersections</span></div>
      </div>
      <div class="panel-list" id="panelList"></div>
      <textarea id="comment" placeholder="备注"></textarea>
      <div class="kv">
        <span>model</span><code id="modelInfo"></code>
        <span>reason</span><code id="modelReason"></code>
        <span>image</span><code id="imageMeta"></code>
        <span>png</span><code id="pngPath"></code>
      </div>
    </aside>
  </main>
  <script>
    const rows = {data_json};
    const storageKey = "industrial-diagram-topology-panel-split-v2-review-v1";
    let state = loadState();
    let currentIndex = 0;
    let selectedBoxIndex = -1;
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
      if (!state[key]) state[key] = {{ boxes: [], comment: "" }};
      return state[key];
    }}
    function currentRow() {{ return rows[currentIndex]; }}
    function currentEntry() {{ return entry(currentRow().parent_panel_id); }}
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
      selectedBoxIndex = -1;
      render();
    }}
    function renderSelect() {{
      const select = document.getElementById("panelSelect");
      select.innerHTML = "";
      rows.forEach((row, index) => {{
        const option = document.createElement("option");
        option.value = String(index);
        option.textContent = `${{index + 1}} / ${{rows.length}}  ${{row.parent_panel_id}}`;
        select.appendChild(option);
      }});
      select.value = String(currentIndex);
    }}
    function renderStats() {{
      const labeled = rows.filter(row => entry(row.parent_panel_id).boxes.length > 0).length;
      const boxCount = rows.reduce((sum, row) => sum + entry(row.parent_panel_id).boxes.length, 0);
      document.getElementById("stats").textContent = `已框 panel ${{labeled}} / ${{rows.length}} | v2 boxes ${{boxCount}}`;
    }}
    function renderOverlay() {{
      const overlay = document.getElementById("overlay");
      const scale = imageScale();
      overlay.setAttribute("viewBox", `0 0 ${{scale.w}} ${{scale.h}}`);
      overlay.innerHTML = "";
      currentEntry().boxes.forEach((box, index) => {{
        const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        r.setAttribute("x", box.x0 * scale.x);
        r.setAttribute("y", box.y0 * scale.y);
        r.setAttribute("width", Math.max(1, (box.x1 - box.x0) * scale.x));
        r.setAttribute("height", Math.max(1, (box.y1 - box.y0) * scale.y));
        r.setAttribute("class", "rect" + (index === selectedBoxIndex ? " active" : ""));
        r.addEventListener("click", event => {{
          event.stopPropagation();
          selectedBoxIndex = index;
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
      document.getElementById("parentPanelId").textContent = row.parent_panel_id;
      document.getElementById("badges").innerHTML = [
        `<span class="badge">${{row.phase}}</span>`,
        `<span class="badge">${{row.split}}</span>`,
        `<span class="badge">${{row.split_method}}</span>`,
        `<span class="badge">${{row.severity}}</span>`
      ].join("");
      document.getElementById("edgeCount").textContent = row.v1_edge_count || "0";
      document.getElementById("netCount").textContent = row.v1_net_count || "0";
      document.getElementById("intersections").textContent = row.intersection_count || "0";
      document.getElementById("comment").value = e.comment || "";
      const img = document.getElementById("image");
      document.getElementById("imageMeta").textContent = `${{img.naturalWidth || 0}} x ${{img.naturalHeight || 0}}`;
      document.getElementById("pngPath").textContent = row.panel_png_path || "";
      document.getElementById("modelInfo").textContent = `${{row.model_review_label || "none"}} ${{row.model_confidence || ""}}`;
      document.getElementById("modelReason").textContent = row.model_reason || "";
      const panelList = document.getElementById("panelList");
      panelList.innerHTML = "";
      e.boxes.forEach((box, index) => {{
        const item = document.createElement("div");
        item.className = "panel-row" + (index === selectedBoxIndex ? " active" : "");
        item.innerHTML = `<strong>v2_${{String(index).padStart(3, "0")}}</strong><code>${{rectToString(box)}}</code>`;
        item.addEventListener("click", () => {{
          selectedBoxIndex = index;
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
      img.alt = row.parent_panel_id;
      img.onload = () => {{
        renderSide();
        renderOverlay();
      }};
      renderSide();
      renderOverlay();
      renderStats();
    }}
    function csvEscape(value) {{
      const s = String(value ?? "");
      return /[",\\n\\r]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s;
    }}
    function exportCsv() {{
      const header = [
        "parent_panel_id", "parent_drawing_key", "split", "phase", "batch",
        "source_split_method", "panel_v2_index", "panel_v2_id", "panel_v2_bbox_png",
        "parent_panel_png_path", "status", "comment"
      ];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const e = entry(row.parent_panel_id);
        e.boxes.forEach((box, index) => {{
          const record = {{
            parent_panel_id: row.parent_panel_id,
            parent_drawing_key: row.parent_drawing_key,
            split: row.split,
            phase: row.phase,
            batch: row.batch,
            source_split_method: row.split_method,
            panel_v2_index: index,
            panel_v2_id: `${{row.parent_panel_id}}#split_v2_${{String(index).padStart(3, "0")}}`,
            panel_v2_bbox_png: rectToString(box),
            parent_panel_png_path: row.panel_png_path,
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
      a.download = "topology_panel_split_v2_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    document.getElementById("panelSelect").addEventListener("change", event => setCurrentIndex(Number(event.target.value)));
    document.getElementById("prevBtn").addEventListener("click", () => setCurrentIndex(currentIndex - 1));
    document.getElementById("nextBtn").addEventListener("click", () => setCurrentIndex(currentIndex + 1));
    document.getElementById("deleteBtn").addEventListener("click", () => {{
      if (selectedBoxIndex >= 0) {{
        currentEntry().boxes.splice(selectedBoxIndex, 1);
        selectedBoxIndex = -1;
        saveState();
        render();
      }}
    }});
    document.getElementById("clearBtn").addEventListener("click", () => {{
      currentEntry().boxes = [];
      selectedBoxIndex = -1;
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
      const index = rows.findIndex(row => (row.parent_panel_id + " " + row.parent_drawing_key).toLowerCase().includes(q));
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
        currentEntry().boxes.push(rect);
        selectedBoxIndex = currentEntry().boxes.length - 1;
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
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--title", default="Industrial Diagram Topology Panel Split v2 Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output = args.output.resolve()
    rows = load_rows(args.input)
    compact = compact_rows(rows, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(compact, args.title), encoding="utf-8")
    summary = {
        "review_rows": len(compact),
        "source_input": args.input.resolve().relative_to(ROOT).as_posix(),
        "review_html": args.output.relative_to(ROOT).as_posix(),
        "by_split_method": {},
        "by_phase": {},
        "export_filename": "topology_panel_split_v2_labels.csv",
    }
    for row in compact:
        summary["by_split_method"][row["split_method"]] = summary["by_split_method"].get(row["split_method"], 0) + 1
        summary["by_phase"][row["phase"]] = summary["by_phase"].get(row["phase"], 0) + 1
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Review rows: {len(compact)}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.summary.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
