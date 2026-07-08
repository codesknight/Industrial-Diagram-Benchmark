"""Build HTML review sheet for active Topology Panel v1.1 improvement rows."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"

DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_1_active_improvement_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_1_active_improvement_review.html"
DEFAULT_REVIEW_MANIFEST = INDEX_DIR / "topology_panel_v1_1_active_improvement_review_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_1_active_improvement_review_summary.json"

LABELS = [
    "keep_terminal_anchor",
    "keep_over_connected",
    "abandon_badcase",
    "defer_complex",
]


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


def suggested_label(row: Dict[str, str]) -> str:
    route = row.get("topology_panel_v1_1_next_route", "")
    if route == "terminal_anchor_module":
        return "keep_terminal_anchor"
    if route == "over_connected_repair":
        return "keep_over_connected"
    return "defer_complex"


def compact_rows(rows: List[Dict[str, str]], html_path: Path) -> List[Dict[str, object]]:
    compact: List[Dict[str, object]] = []
    for row in rows:
        item: Dict[str, object] = dict(row)
        item["image_src"] = rel_asset_path(row.get("panel_png_path", ""), html_path)
        item["topology_json_src"] = rel_asset_path(row.get("topology_v1_panel_json_path", ""), html_path)
        item["suggested_review_label"] = suggested_label(row)
        compact.append(item)
    return compact


def build_summary(rows: List[Dict[str, str]]) -> Dict[str, object]:
    return {
        "source_manifest": DEFAULT_MANIFEST.relative_to(ROOT).as_posix(),
        "review_html": DEFAULT_OUTPUT.relative_to(ROOT).as_posix(),
        "review_manifest": DEFAULT_REVIEW_MANIFEST.relative_to(ROOT).as_posix(),
        "row_count": len(rows),
        "next_route_counts": dict(Counter(row.get("topology_panel_v1_1_next_route", "") for row in rows)),
        "original_reason_counts": dict(
            Counter(row.get("topology_panel_v1_1_original_improvement_reason", "") for row in rows)
        ),
        "model_label_counts": dict(Counter(row.get("model_review_label", "") for row in rows)),
        "phase_counts": dict(Counter(row.get("phase", "") for row in rows)),
        "split_counts": dict(Counter(row.get("split", "") for row in rows)),
        "suggested_review_label_counts": dict(Counter(suggested_label(row) for row in rows)),
        "labels": LABELS,
    }


def render_html(rows: List[Dict[str, object]], summary: Dict[str, object], title: str) -> str:
    data_json = json.dumps(rows, ensure_ascii=False)
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
      --panel: #ffffff;
      --ink: #101828;
      --muted: #667085;
      --border: #d7dde7;
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
      grid-template-columns: minmax(420px, 1fr) 470px;
      min-height: 360px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
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
    .terminal {{ color: var(--ok); border-color: #b7e4c7; background: #f1fbf5; }}
    .over {{ color: var(--warn); border-color: #ffdca8; background: #fff8eb; }}
    .bad {{ color: var(--bad); border-color: #fecdca; background: #fff3f2; }}
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
      min-height: 72px;
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
      <input id="query" type="search" placeholder="panel / route / reason" />
      <select id="routeFilter">
        <option value="">all routes</option>
        <option value="terminal_anchor_module">terminal_anchor_module</option>
        <option value="over_connected_repair">over_connected_repair</option>
      </select>
      <select id="reviewFilter"><option value="">all review labels</option></select>
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
    const stateKey = "topology_panel_v1_1_active_improvement_review_labels";
    const saved = JSON.parse(localStorage.getItem(stateKey) || "{{}}");
    const cards = document.getElementById("cards");
    const query = document.getElementById("query");
    const routeFilter = document.getElementById("routeFilter");
    const reviewFilter = document.getElementById("reviewFilter");
    const stats = document.getElementById("stats");

    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, ch => ({{
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }}[ch]));
    }}
    function current(id, row) {{
      return saved[id] || {{ review_label: row.suggested_review_label, comment: "" }};
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
    function routeClass(route) {{
      if (route === "terminal_anchor_module") return "terminal";
      if (route === "over_connected_repair") return "over";
      return "bad";
    }}
    function card(row) {{
      const review = current(row.panel_id, row);
      const jsonLink = row.topology_json_src ? `<a href="${{row.topology_json_src}}" target="_blank">topology json</a>` : "";
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
            <span class="badge ${{routeClass(row.topology_panel_v1_1_next_route)}}">${{escapeHtml(row.topology_panel_v1_1_next_route)}}</span>
            <span class="badge">${{escapeHtml(row.model_review_label)}}</span>
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
            ${{metric("entity count", row.panel_entity_count)}}
            ${{metric("quality", row.quality_flags || "none")}}
          </div>
          <div class="sub"><b>policy:</b> ${{escapeHtml(row.topology_panel_v1_1_decision_reason)}}</div>
          <div class="sub"><b>model:</b> ${{escapeHtml(row.model_reason)}}</div>
          <div class="sub">${{jsonLink}}</div>
          <select onchange="save('${{escapeHtml(row.panel_id)}}', {{ review_label: this.value }})">
            ${{labels.map(label => `<option value="${{label}}" ${{review.review_label === label ? "selected" : ""}}>${{label}}</option>`).join("")}}
          </select>
          <textarea placeholder="comment" oninput="save('${{escapeHtml(row.panel_id)}}', {{ comment: this.value }})">${{escapeHtml(review.comment || "")}}</textarea>
        </section>
      </article>`;
    }}
    function populateFilters() {{
      for (const label of labels) {{
        reviewFilter.insertAdjacentHTML("beforeend", `<option value="${{label}}">${{label}}</option>`);
      }}
    }}
    function filteredRows() {{
      const q = query.value.trim().toLowerCase();
      return rows.filter(row => {{
        const review = current(row.panel_id, row);
        if (routeFilter.value && row.topology_panel_v1_1_next_route !== routeFilter.value) return false;
        if (reviewFilter.value && review.review_label !== reviewFilter.value) return false;
        if (!q) return true;
        return [row.panel_id, row.parent_drawing_key, row.topology_panel_v1_1_next_route, row.model_review_label, row.model_reason, row.quality_flags]
          .some(value => String(value || "").toLowerCase().includes(q));
      }});
    }}
    function render() {{
      const visible = filteredRows();
      cards.innerHTML = visible.map(card).join("");
      const counts = rows.reduce((acc, row) => {{
        const label = current(row.panel_id, row).review_label;
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
      const header = ["panel_id", "review_label", "comment", "suggested_review_label", "next_route"];
      const lines = [header.join(",")];
      for (const row of rows) {{
        const review = current(row.panel_id, row);
        lines.push([row.panel_id, review.review_label, review.comment || "", row.suggested_review_label, row.topology_panel_v1_1_next_route].map(csvEscape).join(","));
      }}
      const blob = new Blob(["\\ufeff" + lines.join("\\n") + "\\n"], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "topology_panel_v1_1_active_improvement_review_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    populateFilters();
    for (const input of [query, routeFilter, reviewFilter]) {{
      input.addEventListener("input", render);
      input.addEventListener("change", render);
    }}
    document.getElementById("clearBtn").addEventListener("click", () => {{
      query.value = "";
      routeFilter.value = "";
      reviewFilter.value = "";
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
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--title", default="Topology Panel v1.1 Active Improvement Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    rows = sorted(
        rows,
        key=lambda row: (
            row.get("topology_panel_v1_1_next_route", ""),
            row.get("phase", ""),
            -int_value(row.get("v1_edge_count", 0)),
            row.get("panel_id", ""),
        ),
    )
    fieldnames = list(rows[0].keys()) if rows else []
    write_csv(DEFAULT_REVIEW_MANIFEST, rows, fieldnames)
    summary = build_summary(rows)
    DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compact = compact_rows(rows, args.output)
    args.output.write_text(render_html(compact, summary, args.title), encoding="utf-8")

    print(f"Rows: {len(rows)}")
    print(f"Routes: {summary['next_route_counts']}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_REVIEW_MANIFEST.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {DEFAULT_SUMMARY.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
