"""Model-assisted pre-review for Topology Panel v1 samples.

The script loads API keys from environment variables or `.env`, sends panel
images to a vision-capable Doubao/Ark-compatible endpoint, and writes strict CSV
pre-labels for human review. It does not print secrets.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_INPUT = INDEX_DIR / "topology_panel_v1_sample_review_manifest.csv"
DEFAULT_OUTPUT = INDEX_DIR / "topology_panel_v1_model_review.csv"
DEFAULT_SUMMARY = INDEX_DIR / "topology_panel_v1_model_review_summary.json"

LABELS = {
    "accept_v1",
    "needs_panel_split",
    "over_connected",
    "still_fragmented",
    "needs_terminal_anchor",
    "not_topology_target",
    "bad_geometry",
}


SYSTEM_PROMPT = """You are reviewing industrial/CAD diagram panel crops for a topology graph benchmark.
Return only strict JSON. Do not include markdown.

Choose exactly one review_label:
- accept_v1: one coherent topology target; v1 graph likely usable as a baseline.
- needs_panel_split: the image still contains multiple independent subfigures, multiple drawing panels, separated diagrams, multiple title blocks, or visually independent regions that should be split before topology graph use.
- over_connected: topology graph likely connects visual crossings or unrelated regions.
- still_fragmented: topology graph likely remains too fragmented for one coherent panel.
- needs_terminal_anchor: topology line graph is plausible but needs terminal/symbol/device anchors for semantic correctness.
- not_topology_target: the panel is mainly layout, symbol legend, table, building plan, title, or otherwise not a wiring/topology graph target.
- bad_geometry: image or geometry is visibly corrupted, blank, unreadable, or unusable.

Prioritize needs_panel_split whenever multiple independent diagrams are visible in one image.
"""


def user_prompt(row: Dict[str, str]) -> str:
    return f"""Review this panel image and topology metadata.

panel_id: {row.get("panel_id", "")}
phase: {row.get("phase", "")}
split_method: {row.get("split_method", "")}
severity: {row.get("severity", "")}
anomaly_type: {row.get("anomaly_type", "")}
status: {row.get("status", "")}
quality_flags: {row.get("quality_flags", "")}
panel_entity_count: {row.get("panel_entity_count", "")}
base_segment_count: {row.get("base_segment_count", "")}
v1_node_count: {row.get("v1_node_count", "")}
v1_edge_count: {row.get("v1_edge_count", "")}
v1_net_count: {row.get("v1_net_count", "")}
v1_isolated_edge_ratio: {row.get("v1_isolated_edge_ratio", "")}
v1_largest_net_edge_ratio: {row.get("v1_largest_net_edge_ratio", "")}
intersection_count: {row.get("intersection_count", "")}

Return JSON with this exact shape:
{{
  "review_label": "one of the allowed labels",
  "confidence": 0.0,
  "needs_human_review": true,
  "reason": "short concrete reason",
  "visible_cues": ["short cue 1", "short cue 2"]
}}
"""


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


def image_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def resolve_image_path(row: Dict[str, str]) -> Path:
    raw = Path(row.get("panel_png_path", ""))
    return raw if raw.is_absolute() else ROOT / raw


def first_env(names: List[str]) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""


def make_client(args: argparse.Namespace) -> OpenAI:
    api_key = args.api_key or first_env([
        "DOUBAO_API_KEY",
        "DOUBE_API_KEY",
        "ARK_API_KEY",
        "VOLCENGINE_API_KEY",
    ])
    if not api_key:
        raise SystemExit(
            "Missing API key. Set DOUBAO_API_KEY, DOUBE_API_KEY, ARK_API_KEY, "
            "or VOLCENGINE_API_KEY in .env/environment."
        )
    return OpenAI(api_key=api_key, base_url=args.base_url)


def extract_json(text: str) -> Dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("model response is not a JSON object")
    return payload


def normalize_response(payload: Dict[str, object]) -> Dict[str, object]:
    label = str(payload.get("review_label", "")).strip()
    if label not in LABELS:
        label = "bad_geometry"
    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))
    visible_cues = payload.get("visible_cues", [])
    if isinstance(visible_cues, list):
        cues = "; ".join(str(item) for item in visible_cues[:5])
    else:
        cues = str(visible_cues or "")
    needs_human_review = bool(payload.get("needs_human_review", confidence < 0.85))
    if confidence < 0.85 or label in {"needs_panel_split", "bad_geometry", "not_topology_target"}:
        needs_human_review = True
    return {
        "model_review_label": label,
        "model_confidence": round(confidence, 4),
        "model_needs_human_review": needs_human_review,
        "model_reason": str(payload.get("reason", "") or "").strip(),
        "model_visible_cues": cues,
    }


def call_vision_model(client: OpenAI, row: Dict[str, str], image_path: Path, args: argparse.Namespace) -> Dict[str, object]:
    response = client.chat.completions.create(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt(row)},
                    {"type": "image_url", "image_url": {"url": image_data_url(image_path)}},
                ],
            },
        ],
    )
    text = response.choices[0].message.content or ""
    return normalize_response(extract_json(text))


def existing_rows(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    rows = load_csv(path)
    return {row["panel_id"]: row for row in rows if row.get("panel_id")}


def build_dry_run_label(row: Dict[str, str], image_path: Path) -> Dict[str, object]:
    flags = row.get("quality_flags", "")
    anomaly = row.get("anomaly_type", "")
    if anomaly == "no_edges_or_no_nets" or "no_edges" in flags:
        label = "not_topology_target"
    elif row.get("split_method") == "full" and row.get("severity") in {"critical", "medium", "normal"}:
        label = "needs_panel_split"
    else:
        label = "accept_v1"
    return {
        "model_review_label": label,
        "model_confidence": 0.0,
        "model_needs_human_review": True,
        "model_reason": f"dry-run heuristic for {image_path.name}",
        "model_visible_cues": "dry_run",
    }


def review_rows(args: argparse.Namespace) -> List[Dict[str, object]]:
    rows = load_csv(args.input)
    if args.limit:
        rows = rows[: args.limit]
    done = existing_rows(args.output) if args.resume else {}
    client = None if args.dry_run else make_client(args)
    out_rows: List[Dict[str, object]] = [dict(row) for row in done.values()]

    for index, row in enumerate(rows, start=1):
        panel_id = row["panel_id"]
        if panel_id in done:
            continue
        image_path = resolve_image_path(row)
        result: Dict[str, object]
        if not image_path.exists():
            result = {
                "model_review_label": "bad_geometry",
                "model_confidence": 0.0,
                "model_needs_human_review": True,
                "model_reason": f"missing image: {row.get('panel_png_path', '')}",
                "model_visible_cues": "",
            }
        elif args.dry_run:
            result = build_dry_run_label(row, image_path)
        else:
            last_error = ""
            for attempt in range(1, args.retries + 1):
                try:
                    result = call_vision_model(client, row, image_path, args)  # type: ignore[arg-type]
                    break
                except Exception as exc:  # noqa: BLE001 - preserve batch progress and record failure.
                    last_error = str(exc)
                    if attempt < args.retries:
                        time.sleep(args.retry_sleep * attempt)
            else:
                result = {
                    "model_review_label": "bad_geometry",
                    "model_confidence": 0.0,
                    "model_needs_human_review": True,
                    "model_reason": f"model_error: {last_error[:300]}",
                    "model_visible_cues": "",
                }
        out = compact_output_row(row, result)
        out_rows.append(out)
        write_csv(args.output, out_rows, OUTPUT_FIELDNAMES)
        if args.sleep > 0 and not args.dry_run:
            time.sleep(args.sleep)
        if index % args.progress_every == 0:
            print(f"Reviewed {index}/{len(rows)}")
    return out_rows


def compact_output_row(row: Dict[str, str], result: Dict[str, object]) -> Dict[str, object]:
    out: Dict[str, object] = {
        "panel_id": row.get("panel_id", ""),
        "parent_drawing_key": row.get("parent_drawing_key", ""),
        "split": row.get("split", ""),
        "phase": row.get("phase", ""),
        "severity": row.get("severity", ""),
        "anomaly_type": row.get("anomaly_type", ""),
        "split_method": row.get("split_method", ""),
        "status": row.get("status", ""),
        "quality_flags": row.get("quality_flags", ""),
        "v1_edge_count": row.get("v1_edge_count", ""),
        "v1_node_count": row.get("v1_node_count", ""),
        "v1_net_count": row.get("v1_net_count", ""),
        "v1_isolated_edge_ratio": row.get("v1_isolated_edge_ratio", ""),
        "v1_largest_net_edge_ratio": row.get("v1_largest_net_edge_ratio", ""),
        "intersection_count": row.get("intersection_count", ""),
        "panel_png_path": row.get("panel_png_path", ""),
        "topology_v1_panel_json_path": row.get("topology_v1_panel_json_path", ""),
    }
    out.update(result)
    return out


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    summary = {
        "model_review_rows": len(rows),
        "input_manifest": args.input.resolve().relative_to(ROOT).as_posix(),
        "output_csv": args.output.resolve().relative_to(ROOT).as_posix(),
        "dry_run": args.dry_run,
        "model": args.model,
        "label_counts": dict(Counter(str(row.get("model_review_label", "")) for row in rows)),
        "human_review_counts": dict(Counter(str(row.get("model_needs_human_review", "")) for row in rows)),
        "severity_counts": dict(Counter(str(row.get("severity", "")) for row in rows)),
        "rules": [
            "Model labels are pre-annotations only; final labels require human confirmation.",
            "needs_panel_split means a displayed panel still contains multiple independent subfigures.",
            "Rows with confidence below 0.85 are forced into human review.",
        ],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--base-url", default=os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"))
    parser.add_argument(
        "--model",
        default=(
            os.getenv("DOUBAO_VISION_MODEL")
            or os.getenv("DOUBAO_MODEL")
            or os.getenv("DOUBE_VISION_MODEL")
            or os.getenv("DOUBE_MODEL")
            or os.getenv("ARK_MODEL")
            or os.getenv("ARK_ENDPOINT_ID")
            or ""
        ),
    )
    parser.add_argument("--api-key", default="")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=500)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.model:
        raise SystemExit(
            "Missing model. Set DOUBAO_VISION_MODEL, DOUBAO_MODEL, DOUBE_VISION_MODEL, "
            "DOUBE_MODEL, ARK_MODEL, or ARK_ENDPOINT_ID; or pass --model."
        )
    return args


OUTPUT_FIELDNAMES = [
    "panel_id",
    "parent_drawing_key",
    "split",
    "phase",
    "severity",
    "anomaly_type",
    "split_method",
    "status",
    "quality_flags",
    "v1_edge_count",
    "v1_node_count",
    "v1_net_count",
    "v1_isolated_edge_ratio",
    "v1_largest_net_edge_ratio",
    "intersection_count",
    "panel_png_path",
    "topology_v1_panel_json_path",
    "model_review_label",
    "model_confidence",
    "model_needs_human_review",
    "model_reason",
    "model_visible_cues",
]


def main() -> None:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    rows = review_rows(args)
    write_summary(rows, args)
    print(f"Model review rows: {len(rows)}")
    print(f"Wrote: {args.output.resolve().relative_to(ROOT).as_posix()}")
    print(f"Wrote: {args.summary.resolve().relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
