"""Build an HTML review table for agentic annotation conflicts."""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data_index"
DEFAULT_CONSENSUS = DATA_INDEX / "topology_panel_v1_5_agentic_annotation_consensus.csv"
DEFAULT_AGENT_OUTPUTS = DATA_INDEX / "topology_panel_v1_5_agentic_annotation_agent_outputs.csv"
DEFAULT_OUTPUT = DATA_INDEX / "topology_panel_v1_5_agentic_annotation_review.html"
DEFAULT_SUMMARY = DATA_INDEX / "topology_panel_v1_5_agentic_annotation_review_summary.json"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def image_src(path_value: str) -> str:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    try:
        return path.resolve().relative_to(DEFAULT_OUTPUT.parent.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_uri()


def agent_block(rows: List[Dict[str, str]]) -> str:
    parts = []
    for row in rows:
        label = html.escape(row.get("agent_label", ""))
        conf = html.escape(row.get("agent_confidence", ""))
        agent = html.escape(row.get("agent", ""))
        reason = html.escape(row.get("agent_reason", ""))
        cues = html.escape(row.get("agent_visible_cues", ""))
        error = html.escape(row.get("error", ""))
        err = f"<div class='error'>{error}</div>" if error else ""
        parts.append(
            f"<div class='agent'><b>{agent}</b> <span class='label'>{label}</span> "
            f"<span class='conf'>{conf}</span><div>{reason}</div><small>{cues}</small>{err}</div>"
        )
    return "\n".join(parts)


def build_html(consensus_rows: List[Dict[str, str]], agent_rows: List[Dict[str, str]], args: argparse.Namespace) -> str:
    by_panel: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in agent_rows:
        by_panel[row["panel_id"]].append(row)

    if args.only_review:
        rows = [row for row in consensus_rows if row.get("consensus_decision") == "human_review"]
    else:
        rows = consensus_rows
    if args.limit:
        rows = rows[: args.limit]

    cards = []
    for index, row in enumerate(rows, start=1):
        panel_id = html.escape(row["panel_id"])
        src = html.escape(image_src(row.get("panel_png_path", "")))
        consensus = html.escape(row.get("consensus_label", ""))
        decision = html.escape(row.get("consensus_decision", ""))
        reason = html.escape(row.get("reason", ""))
        bucket = html.escape(row.get("v1_5_candidate_bucket", ""))
        score = html.escape(row.get("v1_5_candidate_score", ""))
        known = html.escape(row.get("known_policy_decision", ""))
        cards.append(
            f"""
<article class="card">
  <header>
    <div><b>#{index}</b> <code>{panel_id}</code></div>
    <div class="pill {decision}">{decision}</div>
  </header>
  <section class="grid">
    <div class="image-wrap"><img src="{src}" loading="lazy" /></div>
    <div>
      <dl>
        <dt>consensus</dt><dd>{consensus}</dd>
        <dt>reason</dt><dd>{reason}</dd>
        <dt>bucket / score</dt><dd>{bucket} / {score}</dd>
        <dt>known policy</dt><dd>{known}</dd>
      </dl>
      <h4>Agent votes</h4>
      {agent_block(by_panel[row["panel_id"]])}
      <h4>Human label</h4>
      <div class="buttons">
        <button data-label="accept_clean_topology">accept</button>
        <button data-label="reject_multi_subfigure">multi</button>
        <button data-label="reject_visible_watermark">watermark</button>
        <button data-label="reject_bad_geometry">bad geometry</button>
        <button data-label="reject_not_topology">not topology</button>
        <button data-label="needs_graph_repair">repair</button>
        <button data-label="uncertain">uncertain</button>
      </div>
      <textarea placeholder="review comment"></textarea>
    </div>
  </section>
</article>
"""
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Agentic Annotation Review</title>
  <style>
    body {{ margin: 0; font-family: Arial, "Microsoft YaHei", sans-serif; background: #f6f7f9; color: #1f2937; }}
    .toolbar {{ position: sticky; top: 0; z-index: 2; background: #111827; color: white; padding: 12px 18px; display: flex; gap: 12px; align-items: center; }}
    .toolbar button {{ padding: 7px 10px; border: 0; border-radius: 4px; cursor: pointer; }}
    main {{ max-width: 1280px; margin: 18px auto; padding: 0 14px; }}
    .card {{ background: white; border: 1px solid #d6dbe3; border-radius: 8px; margin-bottom: 16px; overflow: hidden; }}
    header {{ display: flex; justify-content: space-between; gap: 10px; padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }}
    code {{ white-space: normal; overflow-wrap: anywhere; }}
    .grid {{ display: grid; grid-template-columns: minmax(360px, 58%) 1fr; gap: 14px; padding: 12px; }}
    .image-wrap {{ background: #eef2f7; border: 1px solid #d1d5db; max-height: 760px; overflow: auto; }}
    img {{ max-width: 100%; display: block; }}
    dl {{ display: grid; grid-template-columns: 110px 1fr; gap: 6px 10px; margin: 0; }}
    dt {{ font-weight: 700; color: #4b5563; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    .pill {{ padding: 4px 8px; border-radius: 999px; font-size: 12px; background: #e5e7eb; }}
    .human_review {{ background: #fde68a; }}
    .auto_accept {{ background: #bbf7d0; }}
    .auto_reject {{ background: #fecaca; }}
    .auto_defer_improvement {{ background: #bfdbfe; }}
    .agent {{ border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; margin: 8px 0; }}
    .label {{ color: #0f766e; margin-left: 6px; }}
    .conf {{ float: right; color: #6b7280; }}
    .error {{ color: #b91c1c; font-size: 12px; margin-top: 4px; }}
    .buttons {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }}
    .buttons button {{ padding: 6px 8px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; cursor: pointer; }}
    .buttons button.selected {{ background: #2563eb; color: white; border-color: #2563eb; }}
    textarea {{ width: 100%; min-height: 52px; box-sizing: border-box; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="toolbar">
    <b>Agentic Annotation Review</b>
    <span>{len(rows)} rows</span>
    <button onclick="exportCsv()">Export CSV</button>
  </div>
  <main>
    {''.join(cards)}
  </main>
  <script>
    const labels = new Map();
    document.querySelectorAll('.card').forEach(card => {{
      const panel = card.querySelector('code').innerText;
      card.querySelectorAll('button[data-label]').forEach(btn => {{
        btn.addEventListener('click', () => {{
          card.querySelectorAll('button[data-label]').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
          labels.set(panel, btn.dataset.label);
        }});
      }});
    }});
    function csvEscape(value) {{
      const text = String(value ?? '');
      return '"' + text.replaceAll('"', '""') + '"';
    }}
    function exportCsv() {{
      const rows = [['panel_id','human_label','human_comment']];
      document.querySelectorAll('.card').forEach(card => {{
        const panel = card.querySelector('code').innerText;
        const comment = card.querySelector('textarea').value;
        rows.push([panel, labels.get(panel) || '', comment]);
      }});
      const csv = rows.map(row => row.map(csvEscape).join(',')).join('\\n');
      const blob = new Blob([csv], {{type: 'text/csv;charset=utf-8'}});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'topology_panel_v1_5_agentic_human_review_labels.csv';
      a.click();
      URL.revokeObjectURL(a.href);
    }}
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--consensus", type=Path, default=DEFAULT_CONSENSUS)
    parser.add_argument("--agent-outputs", type=Path, default=DEFAULT_AGENT_OUTPUTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--only-review", action="store_true", default=True)
    parser.add_argument("--include-all", action="store_false", dest="only_review")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    consensus_rows = read_csv(args.consensus)
    agent_rows = read_csv(args.agent_outputs)
    html_text = build_html(consensus_rows, agent_rows, args)
    args.output.write_text(html_text, encoding="utf-8")
    selected_rows = [row for row in consensus_rows if row.get("consensus_decision") == "human_review"] if args.only_review else consensus_rows
    if args.limit:
        selected_rows = selected_rows[: args.limit]
    summary = {
        "consensus_csv": rel(args.consensus),
        "agent_outputs_csv": rel(args.agent_outputs),
        "output_html": rel(args.output),
        "selected_rows": len(selected_rows),
        "only_review": args.only_review,
        "decision_counts": dict(Counter(row.get("consensus_decision", "") for row in consensus_rows)),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote: {rel(args.output)}")
    print(f"Wrote: {rel(args.summary)}")


if __name__ == "__main__":
    main()
