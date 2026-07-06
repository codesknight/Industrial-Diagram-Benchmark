"""Generate a sampled HTML review sheet for full panel-level Topology Graph v1."""

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


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_MANIFEST = INDEX_DIR / "topology_panel_v1_manifest.csv"
DEFAULT_ANOMALIES = INDEX_DIR / "topology_panel_v1_anomaly_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_sample_review.html"
DEFAULT_SAMPLE_MANIFEST = INDEX_DIR / "topology_panel_v1_sample_review_manifest.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_sample_review_summary.json"

LABEL_OPTIONS = [
    "accept_v1",
    "over_connected",
    "still_fragmented",
    "needs_terminal_anchor",
    "not_topology_target",
    "bad_geometry",
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


def risk_key(row: Dict[str, str]) -> Tuple[float, int, int, str]:
    anomaly_type = row.get("anomaly_type", "")
    if anomaly_type == "high_isolated_ratio":
        primary = as_float(row, "v1_isolated_edge_ratio")
    elif anomaly_type == "dominant_component":
        primary = as_float(row, "v1_largest_net_edge_ratio")
    else:
        primary = float(as_int(row, "v1_net_count"))
    return (
        primary,
        as_int(row, "v1_edge_count"),
        as_int(row, "intersection_count"),
        row.get("panel_id", ""),
    )


def select_by_type(rows: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
    if limit <= 0:
        return []
    by_type: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        by_type.setdefault(row.get("anomaly_type", ""), []).append(row)
    selected: List[Dict[str, str]] = []
    type_names = sorted(by_type)
    base = max(limit // max(len(type_names), 1), 1)
    for anomaly_type in type_names:
        ranked = sorted(by_type[anomaly_type], key=risk_key, reverse=True)
        selected.extend(ranked[:base])
    if len(selected) < limit:
        seen = {row["panel_id"] for row in selected}
        remaining = [
            row for row in sorted(rows, key=risk_key, reverse=True)
            if row["panel_id"] not in seen
        ]
        selected.extend(remaining[: limit - len(selected)])
    return selected[:limit]


def build_sample(
    full_rows: List[Dict[str, str]],
    anomaly_rows: List[Dict[str, str]],
    medium_limit: int,
    low_limit: int,
    normal_limit: int,
) -> List[Dict[str, object]]:
    full_by_panel = {row["panel_id"]: row for row in full_rows}
    selected: List[Dict[str, str]] = []
    selected.extend(row for row in anomaly_rows if row.get("severity") in {"critical", "high"})
    selected.extend(select_by_type([row for row in anomaly_rows if row.get("severity") == "medium"], medium_limit))
    selected.extend(select_by_type([row for row in anomaly_rows if row.get("severity") == "low"], low_limit))

    selected_ids = {row["panel_id"] for row in selected}
    if normal_limit > 0:
        normal_rows = [
            row for row in full_rows
            if row["panel_id"] not in selected_ids
            and row.get("status") == "ok"
            and not row.get("quality_flags", "")
        ]
        normal_rows = sorted(
            normal_rows,
            key=lambda row: (
                as_int(row, "intersection_count"),
                as_int(row, "v1_edge_count"),
                row.get("panel_id", ""),
            ),
            reverse=True,
        )
        for row in normal_rows[:normal_limit]:
            selected.append(
                {
                    "severity": "normal",
                    "anomaly_type": "normal_high_intersection",
                    "suggested_action": "Spot-check accepted-looking high-intersection samples.",
                    **row,
                }
            )

    deduped: Dict[str, Dict[str, str]] = {}
    for row in selected:
        deduped[row["panel_id"]] = row

    sample: List[Dict[str, object]] = []
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "normal": 4}
    for row in sorted(
        deduped.values(),
        key=lambda item: (
            severity_order.get(item.get("severity", ""), 99),
            item.get("anomaly_type", ""),
            -as_int(item, "v1_edge_count"),
            item.get("panel_id", ""),
        ),
    ):
        full = full_by_panel.get(row["panel_id"], row)
        out = dict(full)
        out["severity"] = row.get("severity", "")
        out["anomaly_type"] = row.get("anomaly_type", "")
        out["suggested_action"] = row.get("suggested_action", "")
        sample.append(out)
    return sample


def compact_rows(rows: Iterable[Dict[str, object]], html_path: Path) -> List[Dict[str, object]]:
    compact: List[Dict[str, object]] = []
    for row in rows:
        item = dict(row)
        item["image_src"] = rel_asset_path(str(row.get("panel_png_path", "")), html_path)
        item["topology_v1_panel_json_src"] = rel_asset_path(
            str(row.get("topology_v1_panel_json_path", "")),
            html_path,
        )
        compact.append(item)
    return compact


def render_html(rows: List[Dict[str, object]], title: str) -> str:
    data_json = json.dumps(rows, ensure_ascii=False)
    labels_json = json.dumps(LABEL_OPTIONS, ensure_ascii=False)
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
      background: rgba(255,255,255,0.97);
      border-bottom: 1px solid var(--border);
    }}
    h1 {{ margin: 0 0 10px; font-size: 20px; font-weight: 650; letter-spacing: 0; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
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
    button.primary {{ background: var(--dark); border-color: var(--dark); color: #fff; }}
    .stats {{ margin-left: auto; color: var(--muted); font-size: 13px; white-space: nowrap; }}
    main {{ padding: 16px; display: grid; gap: 14px; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      display: grid;
      grid-template-columns: minmax(420px, 1fr) 470px;
      min-height: 370px;
      overflow: hidden;
    }}
    .image-wrap {{
      min-height: 370px;
      border-right: 1px solid var(--border);
      background: #fcfcfd;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: auto;
      padding: 10px;
    }}
    .image-wrap img {{ max-width: 100%; max-height: 78vh; object-fit: contain; border: 1px solid #edf0f5; background: #fff; }}
    .meta {{ padding: 12px; display: grid; gap: 10px; align-content: start; }}
    .title {{ font-size: 13px; line-height: 1.4; word-break: break-all; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{ border: 1px solid var(--border); border-radius: 999px; padding: 3px 8px; color: var(--muted); font-size: 12px; background: #fff; }}
    .badge.critical {{ border-color: var(--bad); color: var(--bad); background: #fff1f0; }}
    .badge.high {{ border-color: #c4320a; color: #c4320a; background: #fff4ed; }}
    .badge.medium {{ border-color: var(--warn); color: var(--warn); background: #fff7e8; }}
    .badge.low {{ border-color: var(--info); color: var(--info); background: #eff6ff; }}
    .badge.normal {{ border-color: var(--ok); color: var(--ok); background: #ecfdf3; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }}
    .metric {{ border: 1px solid var(--border); border-radius: 8px; padding: 8px; min-width: 0; }}
    .metric strong {{ display: block; font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .metric span {{ display: block; color: var(--muted); font-size: 11px; margin-top: 3px; }}
    .choices {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }}
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
    .choice.active[data-value="not_topology_target"] {{ border-color: #475467; color: #475467; background: #f2f4f7; }}
    .choice.active[data-value="bad_geometry"] {{ border-color: #7a271a; color: #7a271a; background: #fff1f0; }}
    textarea {{
      width: 100%;
      min-height: 72px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font-family: inherit;
    }}
    .kv {{ display: grid; grid-template-columns: 122px minmax(0, 1fr); gap: 5px 8px; font-size: 12px; color: var(--muted); }}
    .kv code, .kv a {{ color: var(--ink); word-break: break-all; white-space: pre-wrap; }}
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
      <select id="severityFilter"><option value="all">全部 severity</option></select>
      <select id="typeFilter"><option value="all">全部 anomaly</option></select>
      <select id="labelFilter">
        <option value="all">全部标注</option>
        <option value="unlabeled">未标注</option>
      </select>
      <button id="clearFilters">清除筛选</button>
      <button id="exportCsv" class="primary">导出 CSV</button>
      <span id="stats" class="stats"></span>
    </div>
  </header>
  <main id="list"></main>
  <script>
    const rows = {data_json};
    const labelOptions = {labels_json};
    const storageKey = "industrial-diagram-topology-panel-v1-sample-review-v1";
    let labels = loadLabels();

    function loadLabels() {{
      try {{ return JSON.parse(localStorage.getItem(storageKey) || "{{}}"); }}
      catch {{ return {{}}; }}
    }}
    function saveLabels() {{
      localStorage.setItem(storageKey, JSON.stringify(labels));
      renderStats();
    }}
    function labelFor(id) {{ return labels[id] || {{ label: "", comment: "" }}; }}
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
      const severity = document.getElementById("severityFilter").value;
      const type = document.getElementById("typeFilter").value;
      const labelFilter = document.getElementById("labelFilter").value;
      return rows.filter(row => {{
        const saved = labelFor(row.panel_id);
        const label = saved.label || "unlabeled";
        const text = `${{row.panel_id}} ${{row.parent_drawing_key}} ${{row.anomaly_type}} ${{row.quality_flags}}`.toLowerCase();
        return (!q || text.includes(q))
          && (severity === "all" || row.severity === severity)
          && (type === "all" || row.anomaly_type === type)
          && (labelFilter === "all" || labelFilter === label);
      }});
    }}
    function renderFilters() {{
      const severitySelect = document.getElementById("severityFilter");
      const typeSelect = document.getElementById("typeFilter");
      const labelSelect = document.getElementById("labelFilter");
      for (const value of [...new Set(rows.map(row => row.severity).filter(Boolean))]) {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        severitySelect.appendChild(option);
      }}
      for (const value of [...new Set(rows.map(row => row.anomaly_type).filter(Boolean))].sort()) {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        typeSelect.appendChild(option);
      }}
      for (const value of labelOptions) {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        labelSelect.appendChild(option);
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
        `显示 ${{filteredRows().length}} / ${{rows.length}} | accept ${{counts.accept_v1}} | over ${{counts.over_connected}} | fragmented ${{counts.still_fragmented}} | terminal ${{counts.needs_terminal_anchor}} | not target ${{counts.not_topology_target}} | bad ${{counts.bad_geometry}} | 未标注 ${{counts.unlabeled}}`;
    }}
    function render() {{
      const list = document.getElementById("list");
      list.innerHTML = "";
      for (const row of filteredRows()) {{
        const saved = labelFor(row.panel_id);
        const card = document.createElement("section");
        card.className = "card";
        const imageHtml = row.image_src
          ? `<img src="${{row.image_src}}" alt="${{row.panel_id}}">`
          : `<div>missing image</div>`;
        card.innerHTML = `
          <div class="image-wrap">${{imageHtml}}</div>
          <div class="meta">
            <div class="title"><strong>${{row.panel_id}}</strong></div>
            <div class="badges">
              <span class="badge ${{row.severity}}">${{row.severity}}</span>
              <span class="badge">${{row.anomaly_type}}</span>
              <span class="badge">${{row.phase}}</span>
              <span class="badge">${{row.split}}</span>
              <span class="badge">${{row.status}}</span>
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
            <textarea placeholder="备注：说明过连、碎裂、端子锚点需求、非拓扑目标或几何异常..." data-comment>${{saved.comment || ""}}</textarea>
            <div class="kv">
              <span>suggested</span><code>${{row.suggested_action || ""}}</code>
              <span>parent</span><code>${{row.parent_drawing_key}}</code>
              <span>flags</span><code>${{row.quality_flags || "none"}}</code>
              <span>error</span><code>${{row.error || ""}}</code>
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
        "panel_id", "parent_drawing_key", "split", "phase", "severity", "anomaly_type",
        "status", "quality_flags", "v1_edge_count", "v1_node_count", "v1_net_count",
        "v1_isolated_edge_ratio", "v1_largest_net_edge_ratio", "intersection_count",
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
      a.download = "topology_panel_v1_sample_review_labels.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    document.getElementById("search").addEventListener("input", render);
    document.getElementById("severityFilter").addEventListener("change", render);
    document.getElementById("typeFilter").addEventListener("change", render);
    document.getElementById("labelFilter").addEventListener("change", render);
    document.getElementById("clearFilters").addEventListener("click", () => {{
      document.getElementById("search").value = "";
      document.getElementById("severityFilter").value = "all";
      document.getElementById("typeFilter").value = "all";
      document.getElementById("labelFilter").value = "all";
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
    parser.add_argument("--anomalies", type=Path, default=DEFAULT_ANOMALIES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sample-manifest", type=Path, default=DEFAULT_SAMPLE_MANIFEST)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--medium-limit", type=int, default=80)
    parser.add_argument("--low-limit", type=int, default=30)
    parser.add_argument("--normal-limit", type=int, default=10)
    parser.add_argument("--title", default="Industrial Diagram Topology Panel v1 Sample Review")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output = args.output.resolve()
    full_rows = load_csv(args.manifest)
    anomaly_rows = load_csv(args.anomalies)
    sample_rows = build_sample(
        full_rows,
        anomaly_rows,
        medium_limit=args.medium_limit,
        low_limit=args.low_limit,
        normal_limit=args.normal_limit,
    )
    fieldnames = list(sample_rows[0].keys()) if sample_rows else []
    write_csv(args.sample_manifest, sample_rows, fieldnames)
    compact = compact_rows(sample_rows, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(compact, args.title), encoding="utf-8")
    summary = {
        "sample_rows": len(sample_rows),
        "source_manifest": args.manifest.resolve().relative_to(ROOT).as_posix(),
        "source_anomalies": args.anomalies.resolve().relative_to(ROOT).as_posix(),
        "sample_manifest": args.sample_manifest.resolve().relative_to(ROOT).as_posix(),
        "review_html": args.output.relative_to(ROOT).as_posix(),
        "severity_counts": dict(Counter(str(row.get("severity", "")) for row in sample_rows)),
        "anomaly_type_counts": dict(Counter(str(row.get("anomaly_type", "")) for row in sample_rows)),
        "rules": [
            "All critical and high anomalies are included.",
            f"Medium anomalies are risk-sorted and capped at {args.medium_limit}.",
            f"Low anomalies are risk-sorted and capped at {args.low_limit}.",
            f"Normal high-intersection spot checks are capped at {args.normal_limit}.",
        ],
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sample review rows: {len(sample_rows)}")
    print(f"Severity counts: {summary['severity_counts']}")
    print(f"Wrote: {args.output.relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.sample_manifest.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
