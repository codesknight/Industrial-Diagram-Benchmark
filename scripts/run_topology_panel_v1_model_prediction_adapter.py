"""Run a vision model adapter for Topology Panel v1 predictions.

The adapter asks a vision-capable OpenAI-compatible endpoint for topology graph
counts or an optional full graph, normalizes the response, and writes evaluator-
ready prediction JSONL.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_BENCHMARK = INDEX_DIR / "topology_panel_v1_benchmark_manifest.jsonl"
DEFAULT_IMAGE_CACHE = ROOT / "outputs" / "topology_panel_v1_model_prediction_images"
EXPECTED_SCHEMA = "industrial_diagram.topology_graph.v1_panel"


SYSTEM_PROMPT_V1 = """You are predicting a topology graph summary from an industrial diagram panel image.
Return only strict JSON. Do not include markdown.

The evaluator accepts a topology graph schema with nodes, edges, and nets. For
this first model adapter, you may return either:
1) counts only, or
2) a full topology_graph object.

Prefer conservative counts. If the image is unreadable or not a topology target,
set status to "not_topology_target" or "unreadable" and use zero counts.
"""


SYSTEM_PROMPT_V2 = """You are a careful industrial diagram topology counting assistant.
Return only strict JSON. Do not include markdown, prose, comments, or code fences.

Your task is count-level topology prediction, not visual description. You should
estimate the topology counts visible in the panel even when the drawing is dense.
Use status "ok" whenever the panel contains a readable industrial connection,
terminal, wiring, or control diagram and you can make a reasonable estimate.

Use status "unreadable" only when the image is blank, corrupted, or the linework
is impossible to inspect. Use status "not_topology_target" only when the image is
clearly not a diagram. Use status "uncertain" only when the image is a diagram
but the topology target is genuinely ambiguous.

Do not return zero counts for a readable diagram. If status is "ok", all of
node_count, edge_count, and net_count must be positive integers.
"""


SYSTEM_PROMPT_V3 = """You are a careful industrial diagram topology counting assistant.
Return only strict JSON. Do not include markdown, prose, comments, or code fences.

Your task is count-level topology prediction from an industrial wiring,
terminal, relay, or control diagram panel. Estimate node_count, edge_count, and
net_count from visible topology.

Critical definition:
- net_count means the number of connected components in the topology graph.
- net_count does NOT mean the number of function blocks, terminal rows, cable
  bundles, drawing regions, circuits described by labels, or repeated groups.
- If wires/terminals/line segments are connected through a terminal, junction,
  crossing with a connection mark, continuous line, or bus-like conductor, they
  belong to the same net.
- A dense terminal diagram often has only 1 to 3 large connected nets even when
  it contains many terminals, labels, or repeated rows.

Use status "ok" whenever the panel contains a readable industrial connection,
terminal, wiring, or control diagram and you can make a reasonable estimate.
Use status "unreadable" only when the image is blank, corrupted, or the linework
is impossible to inspect. Use status "not_topology_target" only when the image is
clearly not a diagram. Use status "uncertain" only when the image is a diagram
but the topology target is genuinely ambiguous.

Do not return zero counts for a readable diagram. If status is "ok", all of
node_count, edge_count, and net_count must be positive integers.

When unsure about net_count, prefer the smaller connected-component count. Do not
split one connected drawing into many nets just because it has many labels,
columns, rows, or local wire groups.
"""


def system_prompt(prompt_version: str) -> str:
    if prompt_version == "v3":
        return SYSTEM_PROMPT_V3
    if prompt_version == "v2":
        return SYSTEM_PROMPT_V2
    return SYSTEM_PROMPT_V1


def adapter_id(args: argparse.Namespace) -> str:
    suffix = "" if args.prompt_version == "v1" else f"_{args.prompt_version}"
    return f"topology_panel_v1_{args.provider}_adapter{suffix}_2026-07-09"


def user_prompt(record: Dict[str, object], prompt_version: str) -> str:
    reference = record.get("reference", {})
    if not isinstance(reference, dict):
        reference = {}
    summary = reference.get("topology_summary", {})
    if not isinstance(summary, dict):
        summary = {}
    if prompt_version in {"v2", "v3"}:
        net_rules = ""
        if prompt_version == "v3":
            net_rules = """
Net-count rules for v3:
- Count connected components, not semantic circuit groups.
- Do not count terminal rows, repeated blocks, wire bundles, columns, or drawing zones as separate nets.
- If most visible wires are connected through terminals, shared buses, or continuous lines, net_count should usually be small.
- For dense terminal/wiring diagrams, prefer net_count in the 1-3 range unless there are clearly disconnected components.
- If uncertain between many small nets and one large connected net, choose the smaller connected-component estimate.
"""
        return f"""Predict topology graph count-level structure for this panel image.

panel_id: {record.get("panel_id", "")}
split: {record.get("split", "")}
phase: {record.get("phase", "")}
task: {record.get("task", "")}

Counting definitions:
- node_count: count junctions, terminal endpoints, wire endpoints, and line split points needed to represent connectivity
- edge_count: count wire-like connected line segments after splitting at junctions/endpoints
- net_count: count connected components / electrical networks

Important counting rules:
- For dense readable diagrams, estimate counts from the visible linework instead of returning zero.
- Prefer a realistic order-of-magnitude estimate over an unreadable/uncertain status.
- If there are many repeated terminal rows or wire runs, count them as topology elements.
- If the exact number is hard, use the best integer estimate and lower confidence.
- Keep status "ok" for readable industrial diagrams even if confidence is not high.
{net_rules}

Return JSON with this exact shape and no extra fields:
{{
  "status": "ok",
  "node_count": 1,
  "edge_count": 1,
  "net_count": 1,
  "confidence": 0.0,
  "reason": "short concrete reason",
  "topology_graph": null
}}

Allowed status values: "ok", "not_topology_target", "unreadable", "uncertain".
For status "ok", node_count, edge_count, and net_count must be positive integers.
"""

    return f"""Predict topology graph structure for this panel image.

panel_id: {record.get("panel_id", "")}
split: {record.get("split", "")}
phase: {record.get("phase", "")}
task: {record.get("task", "")}

Reference counts are not shown to the model in a real benchmark. The fields
below are included only to explain output meaning, not as targets:
- node_count: number of graph nodes / junctions / line endpoints after topology extraction
- edge_count: number of wire-like graph edges / split segments
- net_count: number of connected components

Return JSON with this exact shape:
{{
  "status": "ok | not_topology_target | unreadable | uncertain",
  "node_count": 0,
  "edge_count": 0,
  "net_count": 0,
  "confidence": 0.0,
  "reason": "short concrete reason",
  "topology_graph": null
}}

If you provide topology_graph, it should follow:
{{
  "schema": "{EXPECTED_SCHEMA}",
  "status": "ok",
  "stats": {{"node_count": 0, "edge_count": 0, "net_count": 0}},
  "nodes": [],
  "edges": [],
  "nets": []
}}
"""


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        raise SystemExit(f"Missing JSONL: {path}")
    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def image_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def prepare_image_for_model(path: Path, args: argparse.Namespace) -> Path:
    with Image.open(path) as image:
        width, height = image.size
        pixels = width * height
        scale = min(
            1.0,
            args.max_image_side / max(width, height),
            (args.max_image_pixels / pixels) ** 0.5 if pixels > 0 else 1.0,
        )
        if scale >= 1.0:
            return path
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        cache_root = args.image_cache.resolve()
        rel_name = path.relative_to(ROOT).as_posix().replace("/", "__").replace("\\", "__")
        size_tag = f"s{args.max_image_side}_p{args.max_image_pixels}"
        out_path = cache_root / f"{rel_name}.{size_tag}.prediction.png"
        if out_path.exists():
            return out_path
        cache_root.mkdir(parents=True, exist_ok=True)
        resized = image.convert("RGB").resize(new_size, Image.Resampling.LANCZOS)
        resized.save(out_path, format="PNG", optimize=True)
        return out_path


def first_env(names: List[str]) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""


def provider_defaults(provider: str) -> Tuple[str, str, List[str], List[str]]:
    if provider == "deepseek":
        return (
            "https://api.deepseek.com",
            first_env(["DEEPSEEK_VISION_MODEL", "DEEPSEEK_MODEL"]),
            ["DEEPSEEK_API_KEY"],
            ["DEEPSEEK_BASE_URL"],
        )
    return (
        "https://ark.cn-beijing.volces.com/api/v3",
        first_env(["DOUBAO_VISION_MODEL", "DOUBAO_MODEL", "ARK_MODEL", "ARK_ENDPOINT_ID"]),
        ["DOUBAO_API_KEY", "ARK_API_KEY", "VOLCENGINE_API_KEY"],
        ["DOUBAO_BASE_URL", "ARK_BASE_URL", "VOLCENGINE_BASE_URL"],
    )


def make_client(args: argparse.Namespace) -> OpenAI:
    default_base_url, default_model, api_key_names, base_url_names = provider_defaults(args.provider)
    args.model = args.model or default_model
    base_url = args.base_url or first_env(base_url_names) or default_base_url
    api_key = args.api_key or first_env(api_key_names)
    if not api_key:
        raise SystemExit(f"Missing API key for {args.provider}. Checked: {', '.join(api_key_names)}")
    if not args.model:
        raise SystemExit(f"Missing model for {args.provider}. Pass --model or set the provider model env var.")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=args.timeout)


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


def as_int(value: object, default: int = 0) -> int:
    try:
        return max(0, int(round(float(str(value)))))
    except (TypeError, ValueError):
        return default


def as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def synthetic_graph(node_count: int, edge_count: int, net_count: int, status: str, reason: str) -> Dict[str, object]:
    support_nodes = node_count
    if edge_count > 0:
        support_nodes = max(support_nodes, 2)
    nodes = [
        {"id": f"n{i}", "point": [float(i), 0.0], "degree": 0}
        for i in range(support_nodes)
    ]
    edges = []
    for i in range(edge_count):
        source = f"n{i % max(support_nodes, 1)}"
        target = f"n{(i + 1) % max(support_nodes, 1)}"
        if source == target and support_nodes > 1:
            target = f"n{(i + 2) % support_nodes}"
        edges.append(
            {
                "id": f"e{i}",
                "source": source,
                "target": target,
                "points": [[0.0, float(i)], [1.0, float(i)]],
                "length": 1.0,
                "entity_type": "MODEL_SYNTHETIC",
                "layer": "model_prediction",
            }
        )
    nets = [
        {
            "id": f"net{i}",
            "node_count": support_nodes if i == 0 else 0,
            "edge_count": edge_count if i == 0 else 0,
            "bbox": [0.0, 0.0, float(max(support_nodes, 1)), float(max(edge_count, 1))],
        }
        for i in range(net_count)
    ]
    return {
        "schema": EXPECTED_SCHEMA,
        "status": "ok" if status == "ok" else status,
        "stats": {
            "node_count": node_count,
            "edge_count": edge_count,
            "net_count": net_count,
            "largest_net_edges": edge_count if nets else 0,
            "isolated_edge_count": 0,
            "isolated_edge_ratio": 0.0,
            "largest_net_edge_ratio": 1.0 if edge_count and nets else 0.0,
        },
        "nodes": nodes,
        "edges": edges,
        "nets": nets,
        "model_adapter": {
            "source": "synthetic_from_model_counts",
            "reason": reason,
            "support_node_count": support_nodes,
        },
    }


def normalize_model_payload(payload: Dict[str, object]) -> Tuple[Dict[str, object], Dict[str, object]]:
    graph = payload.get("topology_graph")
    if isinstance(graph, dict):
        if "schema" not in graph:
            graph["schema"] = EXPECTED_SCHEMA
        return graph, {"adapter_mode": "topology_graph"}

    status = str(payload.get("status", "ok") or "ok")
    node_count = as_int(payload.get("node_count", 0))
    edge_count = as_int(payload.get("edge_count", 0))
    net_count = as_int(payload.get("net_count", 0))
    reason = str(payload.get("reason", "") or "")
    graph = synthetic_graph(node_count, edge_count, net_count, status, reason)
    return graph, {
        "adapter_mode": "synthetic_from_counts",
        "model_status": status,
        "model_node_count": node_count,
        "model_edge_count": edge_count,
        "model_net_count": net_count,
        "model_confidence": round(max(0.0, min(1.0, as_float(payload.get("confidence", 0.0)))), 4),
        "model_reason": reason,
    }


def dry_run_payload(record: Dict[str, object]) -> Dict[str, object]:
    summary = record.get("reference", {})
    if isinstance(summary, dict):
        summary = summary.get("topology_summary", {})
    if not isinstance(summary, dict):
        summary = {}
    return {
        "status": "ok",
        "node_count": as_int(summary.get("node_count", 0)),
        "edge_count": as_int(summary.get("edge_count", 0)),
        "net_count": as_int(summary.get("net_count", 0)),
        "confidence": 0.0,
        "reason": "dry_run_reference_counts",
        "topology_graph": None,
    }


def call_model(client: OpenAI, record: Dict[str, object], image_path: Path, args: argparse.Namespace) -> Dict[str, object]:
    model_image_path = prepare_image_for_model(image_path, args)
    response = client.chat.completions.create(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        messages=[
            {"role": "system", "content": system_prompt(args.prompt_version)},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt(record, args.prompt_version)},
                    {"type": "image_url", "image_url": {"url": image_data_url(model_image_path)}},
                ],
            },
        ],
    )
    text = response.choices[0].message.content or ""
    return extract_json(text)


def run_predictions(args: argparse.Namespace) -> List[Dict[str, object]]:
    records = load_jsonl(args.benchmark)
    if args.limit:
        records = records[: args.limit]
    client = None if args.dry_run else make_client(args)
    prediction_rows: List[Dict[str, object]] = []

    for index, record in enumerate(records, start=1):
        panel_id = str(record.get("panel_id", ""))
        image_path_value = record.get("input", {})
        if isinstance(image_path_value, dict):
            image_path_value = image_path_value.get("image_path", "")
        image_path = ROOT / str(image_path_value)
        error = ""
        payload: Dict[str, object]

        if args.dry_run:
            payload = dry_run_payload(record)
        elif not image_path.exists():
            payload = {
                "status": "unreadable",
                "node_count": 0,
                "edge_count": 0,
                "net_count": 0,
                "confidence": 0.0,
                "reason": f"missing image: {image_path_value}",
                "topology_graph": None,
            }
            error = "missing_image"
        else:
            last_error = ""
            for attempt in range(1, args.retries + 1):
                try:
                    payload = call_model(client, record, image_path, args)  # type: ignore[arg-type]
                    break
                except Exception as exc:  # noqa: BLE001 - preserve batch progress and record failure.
                    last_error = str(exc)
                    if attempt < args.retries:
                        time.sleep(args.retry_sleep * attempt)
            else:
                payload = {
                    "status": "model_error",
                    "node_count": 0,
                    "edge_count": 0,
                    "net_count": 0,
                    "confidence": 0.0,
                    "reason": last_error[:500],
                    "topology_graph": None,
                }
                error = "model_error"

        graph, meta = normalize_model_payload(payload)
        prediction_rows.append(
            {
                "adapter_id": adapter_id(args),
                "benchmark_id": record.get("benchmark_id", ""),
                "task": record.get("task", "panel_topology_graph_v1"),
                "panel_id": panel_id,
                "split": record.get("split", ""),
                "phase": record.get("phase", ""),
                "model": {
                    "provider": args.provider,
                    "name": args.model or ("dry_run" if args.dry_run else ""),
                    "adapter_mode": meta.get("adapter_mode", ""),
                    "dry_run": args.dry_run,
                },
                "prediction": graph,
                "prediction_schema": EXPECTED_SCHEMA,
                "metadata": {
                    **meta,
                    "adapter_error": error,
                    "raw_model_payload": payload if args.keep_raw_response else {},
                },
            }
        )
        write_jsonl(args.output, prediction_rows)
        if index % args.progress_every == 0:
            print(f"Predicted {index}/{len(records)}")
        if args.sleep > 0 and not args.dry_run:
            time.sleep(args.sleep)
    return prediction_rows


def write_summary(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    mode_counts = Counter(str(row.get("model", {}).get("adapter_mode", "")) for row in rows)
    error_counts = Counter(str(row.get("metadata", {}).get("adapter_error", "")) or "none" for row in rows)
    summary = {
        "adapter_id": adapter_id(args),
        "provider": args.provider,
        "model": args.model or ("dry_run" if args.dry_run else ""),
        "prompt_version": args.prompt_version,
        "image_max_side": args.max_image_side,
        "image_max_pixels": args.max_image_pixels,
        "dry_run": args.dry_run,
        "benchmark": rel(args.benchmark),
        "output_predictions": rel(args.output),
        "prediction_rows": len(rows),
        "adapter_mode_counts": dict(mode_counts),
        "adapter_error_counts": dict(error_counts),
        "rules": [
            "Model predictions are converted into evaluator-ready topology graph JSONL.",
            "If the model returns only counts, the adapter creates a synthetic schema-valid graph with stats equal to model counts.",
            "This adapter is a first-pass bridge; count-only predictions are not full geometric topology reconstructions.",
        ],
    }
    write_json(args.summary, summary)


def write_report(rows: List[Dict[str, object]], args: argparse.Namespace) -> None:
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    lines = [
        "# Topology Panel v1 Model Prediction Adapter Report",
        "",
        f"Adapter id: `{summary['adapter_id']}`",
        "",
        "## Summary",
        "",
        f"- Provider: {summary['provider']}",
        f"- Model: {summary['model']}",
        f"- Prompt version: {summary.get('prompt_version', 'v1')}",
        f"- Image max side: {summary.get('image_max_side', '')}",
        f"- Image max pixels: {summary.get('image_max_pixels', '')}",
        f"- Dry run: {summary['dry_run']}",
        f"- Prediction rows: {summary['prediction_rows']}",
        f"- Output predictions: `{summary['output_predictions']}`",
        "",
        "## Adapter Modes",
        "",
    ]
    for mode, count in summary["adapter_mode_counts"].items():
        lines.append(f"- {mode}: {count}")
    lines.extend(["", "## Adapter Errors", ""])
    for error, count in summary["adapter_error_counts"].items():
        lines.append(f"- {error}: {count}")
    lines.extend(["", "## Evaluator Command", "", "```powershell"])
    stem = args.output.stem
    lines.extend(
        [
            "python benchmark/topology/evaluate_topology_graph_v1.py `",
            f"  --predictions {rel(args.output)} `",
            f"  --summary data_index/{stem}_eval_summary.json `",
            f"  --report data_index/{stem}_eval_report.md `",
            f"  --details-csv data_index/{stem}_eval_details.csv `",
            f"  --errors-csv data_index/{stem}_eval_errors.csv",
            "```",
            "",
            "Count-only predictions are converted to synthetic graph objects so evaluator count metrics can run.",
            "",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["doubao", "deepseek"], default="doubao")
    parser.add_argument("--prompt-version", choices=["v1", "v2", "v3"], default="v1")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=900)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--progress-every", type=int, default=1)
    parser.add_argument("--image-cache", type=Path, default=DEFAULT_IMAGE_CACHE)
    parser.add_argument("--max-image-side", type=int, default=2048)
    parser.add_argument("--max-image-pixels", type=int, default=4_000_000)
    parser.add_argument("--keep-raw-response", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompt_suffix = "" if args.prompt_version == "v1" else f"_{args.prompt_version}"
    default_prefix = INDEX_DIR / f"topology_panel_v1_{args.provider}{prompt_suffix}_model_predictions"
    if args.dry_run:
        default_prefix = INDEX_DIR / f"topology_panel_v1_{args.provider}_model_predictions_dry_run"
    args.output = args.output or default_prefix.with_suffix(".jsonl")
    args.summary = args.summary or INDEX_DIR / f"{default_prefix.name}_summary.json"
    args.report = args.report or INDEX_DIR / f"{default_prefix.name}_report.md"
    return args


def main() -> None:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    rows = run_predictions(args)
    write_summary(rows, args)
    write_report(rows, args)
    print(f"Prediction rows: {len(rows)}")
    print(f"Wrote: {rel(args.output)}")
    print(f"Wrote: {rel(args.summary)}")
    print(f"Wrote: {rel(args.report)}")


if __name__ == "__main__":
    main()
