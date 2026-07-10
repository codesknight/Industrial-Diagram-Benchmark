"""Run multi-agent vision annotation and consensus for topology panels."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data_index"
OUTPUTS = ROOT / "outputs" / "agentic_annotation"

DEFAULT_INPUT = DATA_INDEX / "topology_panel_v1_5_candidate_manifest.csv"
DEFAULT_PREFIX = DATA_INDEX / "topology_panel_v1_5_agentic_annotation"
DEFAULT_IMAGE_CACHE = OUTPUTS / "image_cache"

ALLOWED_LABELS = {
    "accept_clean_topology",
    "reject_multi_subfigure",
    "reject_visible_watermark",
    "reject_bad_geometry",
    "reject_not_topology",
    "needs_terminal_anchor",
    "needs_graph_repair",
    "uncertain",
}

HARD_REJECT_LABELS = {
    "reject_multi_subfigure",
    "reject_visible_watermark",
    "reject_bad_geometry",
    "reject_not_topology",
}

SYSTEM_PROMPT = """You are one agent in a multi-agent annotation team for an industrial diagram topology benchmark.
Return only strict JSON. Do not include markdown or prose outside JSON.

Goal:
Decide whether this panel image can be used as a clean single-panel topology benchmark sample.

Choose exactly one label:
- accept_clean_topology: one coherent wiring/terminal/control topology diagram; suitable as a clean benchmark candidate.
- reject_multi_subfigure: the image contains multiple independent diagrams/subfigures/panels/title blocks that should not be a single benchmark sample.
- reject_visible_watermark: visible marketplace/library/source watermark or website mark is printed on the image content.
- reject_bad_geometry: blank, corrupted, unreadable, extreme geometry failure, or topology graph is unusable.
- reject_not_topology: mainly layout plan, table, legend, title page, equipment arrangement, building plan, or otherwise not a wiring/topology target.
- needs_terminal_anchor: line topology exists but semantic terminal/symbol/device anchors are needed before it is clean.
- needs_graph_repair: image is a topology target but current graph likely has fragmentation, over-connection, or severe node/edge errors.
- uncertain: insufficient confidence or conflicting cues.

Strict policy:
- If multiple independent subfigures are visible, choose reject_multi_subfigure even if each subfigure is valid.
- If a visible watermark/source mark is on the image, choose reject_visible_watermark.
- Do not accept layout/site/floor/equipment arrangement drawings as topology targets.
- Accept only if the image looks like one coherent topology diagram and has no obvious blocking quality issue.
"""


def user_prompt(row: Dict[str, str]) -> str:
    return f"""Review this candidate panel for Topology Panel v1.5.

Metadata:
panel_id: {row.get("panel_id", "")}
phase: {row.get("phase", "")}
split: {row.get("split", "")}
split_method: {row.get("split_method", "")}
panel_count: {row.get("panel_count", "")}
status: {row.get("status", "")}
quality_flags: {row.get("quality_flags", "")}
candidate_score: {row.get("v1_5_candidate_score", "")}
candidate_bucket: {row.get("v1_5_candidate_bucket", "")}
known_policy_decision: {row.get("topology_panel_v1_policy_decision", "")}
known_review_label: {row.get("topology_panel_v1_review_label", "")}
v1_node_count: {row.get("v1_node_count", "")}
v1_edge_count: {row.get("v1_edge_count", "")}
v1_net_count: {row.get("v1_net_count", "")}
v1_isolated_edge_ratio: {row.get("v1_isolated_edge_ratio", "")}
v1_largest_net_edge_ratio: {row.get("v1_largest_net_edge_ratio", "")}
intersection_count: {row.get("intersection_count", "")}

Return JSON with this exact shape:
{{
  "label": "one allowed label",
  "confidence": 0.0,
  "is_single_panel": true,
  "is_topology_target": true,
  "has_visible_watermark": false,
  "geometry_usable": true,
  "reason": "short concrete reason",
  "visible_cues": ["cue 1", "cue 2"]
}}
"""


def text_only_user_prompt(row: Dict[str, str], vision_error: str) -> str:
    return f"""You are a text-only audit agent in a multi-agent annotation team.

The vision image call failed for this provider, so you must audit only metadata.
Be conservative: choose accept_clean_topology only when the metadata strongly
supports a clean sample, usually an existing accepted baseline anchor. If visual
evidence is required, choose uncertain.

Vision error type:
{vision_error[:500]}

Metadata:
panel_id: {row.get("panel_id", "")}
phase: {row.get("phase", "")}
split: {row.get("split", "")}
split_method: {row.get("split_method", "")}
panel_count: {row.get("panel_count", "")}
status: {row.get("status", "")}
quality_flags: {row.get("quality_flags", "")}
candidate_score: {row.get("v1_5_candidate_score", "")}
candidate_bucket: {row.get("v1_5_candidate_bucket", "")}
candidate_reasons: {row.get("v1_5_candidate_reasons", "")}
known_policy_decision: {row.get("topology_panel_v1_policy_decision", "")}
known_policy_exclude_reason: {row.get("topology_panel_v1_policy_exclude_reason", "")}
known_review_label: {row.get("topology_panel_v1_review_label", "")}
known_review_comment: {row.get("topology_panel_v1_review_comment", "")}
v1_node_count: {row.get("v1_node_count", "")}
v1_edge_count: {row.get("v1_edge_count", "")}
v1_net_count: {row.get("v1_net_count", "")}
v1_isolated_edge_ratio: {row.get("v1_isolated_edge_ratio", "")}
v1_largest_net_edge_ratio: {row.get("v1_largest_net_edge_ratio", "")}
intersection_count: {row.get("intersection_count", "")}

Return JSON with this exact shape:
{{
  "label": "one allowed label",
  "confidence": 0.0,
  "is_single_panel": true,
  "is_topology_target": true,
  "has_visible_watermark": false,
  "geometry_usable": true,
  "reason": "short concrete reason and mention text-only fallback",
  "visible_cues": ["metadata cue 1", "metadata cue 2"]
}}
"""


@dataclass(frozen=True)
class Provider:
    name: str
    api_key_env: str
    model_env: str
    base_url_env: str
    default_base_url: str
    enabled: bool = True


PROVIDERS = [
    Provider(
        name="doubao",
        api_key_env="DOUBAO_API_KEY",
        model_env="DOUBAO_VISION_MODEL",
        base_url_env="DOUBAO_BASE_URL",
        default_base_url="https://ark.cn-beijing.volces.com/api/v3",
    ),
    Provider(
        name="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_env="DEEPSEEK_VISION_MODEL",
        base_url_env="DEEPSEEK_BASE_URL",
        default_base_url="https://api.deepseek.com",
    ),
    Provider(
        name="zhipu",
        api_key_env="ZHIPU_API_KEY",
        model_env="ZHIPU_VISION_MODEL",
        base_url_env="ZHIPU_BASE_URL",
        default_base_url="https://open.bigmodel.cn/api/paas/v4",
    ),
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def image_data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def resolve_image(row: Dict[str, str]) -> Path:
    path = Path(row.get("panel_png_path", ""))
    if not path.is_absolute():
        path = ROOT / path
    return path


def prepare_image(path: Path, args: argparse.Namespace) -> Path:
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
        rel_name = path.relative_to(ROOT).as_posix().replace("/", "__").replace("\\", "__")
        out_path = args.image_cache / f"{rel_name}.agentic.png"
        if out_path.exists():
            return out_path
        args.image_cache.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").resize(new_size, Image.Resampling.LANCZOS).save(out_path, format="PNG", optimize=True)
        return out_path


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
        raise ValueError("response JSON is not an object")
    return payload


def normalize_payload(payload: Dict[str, object]) -> Dict[str, object]:
    label = str(payload.get("label", "")).strip()
    if label not in ALLOWED_LABELS:
        label = "uncertain"
    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))
    cues = payload.get("visible_cues", [])
    if isinstance(cues, list):
        visible_cues = "; ".join(str(item) for item in cues[:6])
    else:
        visible_cues = str(cues or "")
    return {
        "label": label,
        "confidence": round(confidence, 4),
        "is_single_panel": bool(payload.get("is_single_panel", False)),
        "is_topology_target": bool(payload.get("is_topology_target", False)),
        "has_visible_watermark": bool(payload.get("has_visible_watermark", False)),
        "geometry_usable": bool(payload.get("geometry_usable", False)),
        "reason": str(payload.get("reason", "") or "").strip(),
        "visible_cues": visible_cues,
    }


def provider_from_name(name: str) -> Provider:
    for provider in PROVIDERS:
        if provider.name == name:
            return provider
    raise SystemExit(f"Unknown provider: {name}")


def make_client(provider: Provider) -> Optional[OpenAI]:
    api_key = os.getenv(provider.api_key_env, "")
    model = os.getenv(provider.model_env, "")
    if not api_key or not model:
        return None
    base_url = os.getenv(provider.base_url_env, provider.default_base_url)
    return OpenAI(api_key=api_key, base_url=base_url)


def call_provider(provider: Provider, client: OpenAI, row: Dict[str, str], image_path: Path, args: argparse.Namespace) -> Dict[str, object]:
    model = os.getenv(provider.model_env, "")
    prepared = prepare_image(image_path, args)
    response = client.chat.completions.create(
        model=model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt(row)},
                    {"type": "image_url", "image_url": {"url": image_data_url(prepared)}},
                ],
            },
        ],
    )
    text = response.choices[0].message.content or ""
    result = normalize_payload(extract_json(text))
    result["raw_response"] = text
    result["modality"] = "vision"
    return result


def call_provider_text_only(
    provider: Provider,
    client: OpenAI,
    row: Dict[str, str],
    args: argparse.Namespace,
    vision_error: str,
) -> Dict[str, object]:
    model = os.getenv(provider.model_env, "")
    response = client.chat.completions.create(
        model=model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text_only_user_prompt(row, vision_error)},
        ],
    )
    text = response.choices[0].message.content or ""
    result = normalize_payload(extract_json(text))
    result["raw_response"] = text
    result["modality"] = "text_fallback"
    return result


def dry_run_result(provider: Provider, row: Dict[str, str]) -> Dict[str, object]:
    known = row.get("topology_panel_v1_policy_decision", "")
    review = row.get("topology_panel_v1_review_label", "")
    flags = row.get("quality_flags", "")
    if known == "baseline" or review == "accept_v1":
        label = "accept_clean_topology"
        confidence = 0.92
    elif "needs_panel_split" in {review, row.get("topology_panel_v1_policy_exclude_reason", "")}:
        label = "reject_multi_subfigure"
        confidence = 0.9
    elif review == "bad_geometry" or row.get("status") != "ok":
        label = "reject_bad_geometry"
        confidence = 0.88
    elif review == "not_topology_target":
        label = "reject_not_topology"
        confidence = 0.88
    elif "no_edges" in flags:
        label = "reject_bad_geometry"
        confidence = 0.82
    else:
        label = "uncertain"
        confidence = 0.45
    return {
        "label": label,
        "confidence": confidence,
        "is_single_panel": label != "reject_multi_subfigure",
        "is_topology_target": label not in {"reject_not_topology", "reject_bad_geometry"},
        "has_visible_watermark": False,
        "geometry_usable": label != "reject_bad_geometry",
        "reason": f"dry-run heuristic by {provider.name}",
        "visible_cues": "dry_run",
        "raw_response": "",
        "modality": "dry_run",
    }


def consensus_for_panel(rows: List[Dict[str, object]]) -> Dict[str, object]:
    valid_rows = [
        row
        for row in rows
        if not row.get("error") or row.get("agent_modality") == "text_fallback"
    ]
    labels = [str(row["agent_label"]) for row in valid_rows]
    label_counts = Counter(labels)
    confidence_by_label: Dict[str, List[float]] = defaultdict(list)
    for row in valid_rows:
        confidence_by_label[str(row["agent_label"])].append(float(row.get("agent_confidence", 0.0) or 0.0))

    if not valid_rows:
        return {
            "consensus_label": "uncertain",
            "consensus_decision": "human_review",
            "consensus_confidence": 0.0,
            "agreement_count": 0,
            "agent_count": len(rows),
            "reason": "all agent calls failed",
        }

    winner, agreement = label_counts.most_common(1)[0]
    avg_conf = sum(confidence_by_label[winner]) / len(confidence_by_label[winner])
    has_hard_reject = any(label in HARD_REJECT_LABELS for label in labels)

    if agreement >= 2 and winner == "accept_clean_topology" and avg_conf >= 0.80 and not has_hard_reject:
        decision = "auto_accept"
    elif agreement >= 2 and winner in HARD_REJECT_LABELS and avg_conf >= 0.75:
        decision = "auto_reject"
    elif agreement >= 2 and winner in {"needs_terminal_anchor", "needs_graph_repair"} and avg_conf >= 0.75:
        decision = "auto_defer_improvement"
    else:
        decision = "human_review"

    return {
        "consensus_label": winner,
        "consensus_decision": decision,
        "consensus_confidence": round(avg_conf, 4),
        "agreement_count": agreement,
        "agent_count": len(rows),
        "reason": f"{agreement}/{len(rows)} agents voted {winner}",
    }


def output_paths(prefix: Path) -> Dict[str, Path]:
    return {
        "agent_outputs": prefix.with_name(prefix.name + "_agent_outputs.csv"),
        "consensus": prefix.with_name(prefix.name + "_consensus.csv"),
        "summary": prefix.with_name(prefix.name + "_summary.json"),
        "report": prefix.with_name(prefix.name + "_report.md"),
    }


def run(args: argparse.Namespace) -> tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    input_rows = read_csv(args.input)
    if args.limit:
        input_rows = input_rows[: args.limit]
    providers = [provider_from_name(name) for name in args.providers]
    clients = {provider.name: make_client(provider) for provider in providers}
    if not args.dry_run:
        missing = [provider.name for provider in providers if clients[provider.name] is None]
        if missing:
            raise SystemExit(f"Missing API key or model env for providers: {', '.join(missing)}")

    agent_rows: List[Dict[str, object]] = []
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for index, row in enumerate(input_rows, start=1):
        panel_id = row["panel_id"]
        image_path = resolve_image(row)
        for provider in providers:
            started = time.time()
            error = ""
            if not image_path.exists():
                result = {
                    "label": "reject_bad_geometry",
                    "confidence": 0.0,
                    "is_single_panel": False,
                    "is_topology_target": False,
                    "has_visible_watermark": False,
                    "geometry_usable": False,
                    "reason": f"missing image: {row.get('panel_png_path', '')}",
                    "visible_cues": "",
                    "raw_response": "",
                }
            elif args.dry_run:
                result = dry_run_result(provider, row)
            else:
                for attempt in range(1, args.retries + 1):
                    try:
                        result = call_provider(provider, clients[provider.name], row, image_path, args)  # type: ignore[arg-type]
                        break
                    except Exception as exc:  # noqa: BLE001 - record model/API errors per row.
                        error = str(exc)
                        if args.allow_text_fallback and (
                            "image_url" in error
                            or "messages.content.type" in error
                            or "expected `text`" in error
                            or "expected text" in error
                        ):
                            try:
                                result = call_provider_text_only(
                                    provider,
                                    clients[provider.name],  # type: ignore[arg-type]
                                    row,
                                    args,
                                    error,
                                )
                                error = f"vision_failed_used_text_fallback: {error[:300]}"
                                break
                            except Exception as fallback_exc:  # noqa: BLE001
                                error = f"vision_error: {error[:250]} | text_fallback_error: {fallback_exc}"
                        if attempt < args.retries:
                            time.sleep(args.retry_sleep * attempt)
                else:
                    result = {
                        "label": "uncertain",
                        "confidence": 0.0,
                        "is_single_panel": False,
                        "is_topology_target": False,
                        "has_visible_watermark": False,
                        "geometry_usable": False,
                        "reason": "agent_error",
                        "visible_cues": "",
                        "raw_response": "",
                        "modality": "error",
                    }
            elapsed = round(time.time() - started, 3)
            out = {
                "panel_id": panel_id,
                "agent": provider.name,
                "agent_model": os.getenv(provider.model_env, ""),
                "agent_modality": result.get("modality", "vision"),
                "agent_label": result["label"],
                "agent_confidence": result["confidence"],
                "is_single_panel": result["is_single_panel"],
                "is_topology_target": result["is_topology_target"],
                "has_visible_watermark": result["has_visible_watermark"],
                "geometry_usable": result["geometry_usable"],
                "agent_reason": result["reason"],
                "agent_visible_cues": result["visible_cues"],
                "elapsed_sec": elapsed,
                "error": error,
                "raw_response": result.get("raw_response", ""),
            }
            agent_rows.append(out)
            grouped[panel_id].append(out)
        if index % args.progress_every == 0:
            print(f"Annotated {index}/{len(input_rows)}")

    consensus_rows: List[Dict[str, object]] = []
    input_by_id = {row["panel_id"]: row for row in input_rows}
    for panel_id, panel_agent_rows in grouped.items():
        source = input_by_id[panel_id]
        consensus = consensus_for_panel(panel_agent_rows)
        consensus_rows.append(
            {
                "panel_id": panel_id,
                "phase": source.get("phase", ""),
                "split": source.get("split", ""),
                "panel_png_path": source.get("panel_png_path", ""),
                "topology_v1_panel_json_path": source.get("topology_v1_panel_json_path", ""),
                "v1_5_candidate_score": source.get("v1_5_candidate_score", ""),
                "v1_5_candidate_bucket": source.get("v1_5_candidate_bucket", ""),
                "known_policy_decision": source.get("topology_panel_v1_policy_decision", ""),
                "known_review_label": source.get("topology_panel_v1_review_label", ""),
                **consensus,
            }
        )
    return agent_rows, consensus_rows


def write_report(path: Path, summary: Dict[str, object]) -> None:
    lines = [
        "# Agentic Panel Annotation Report",
        "",
        "This run uses multiple vision agents to pre-label Topology Panel v1.5 candidates.",
        "",
        "## Summary",
        "",
        f"- dry run: {summary['dry_run']}",
        f"- input rows: {summary['input_rows']}",
        f"- providers: {', '.join(summary['providers'])}",
        f"- agent output rows: {summary['agent_output_rows']}",
        f"- consensus rows: {summary['consensus_rows']}",
        "",
        "## Consensus Decisions",
        "",
    ]
    for key, value in summary["consensus_decision_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Consensus Labels", ""])
    for key, value in summary["consensus_label_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `{summary['outputs']['agent_outputs']}`",
            f"- `{summary['outputs']['consensus']}`",
            f"- `{summary['outputs']['summary']}`",
            "",
            "## Policy",
            "",
            "- auto_accept requires at least two agents voting accept_clean_topology, average confidence >= 0.80, and no hard-reject vote.",
            "- auto_reject requires at least two agents voting the same hard-reject label with average confidence >= 0.75.",
            "- all other cases go to human_review or auto_defer_improvement.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(args: argparse.Namespace, agent_rows: List[Dict[str, object]], consensus_rows: List[Dict[str, object]]) -> None:
    paths = output_paths(args.output_prefix)
    agent_fields = [
        "panel_id",
        "agent",
        "agent_model",
        "agent_modality",
        "agent_label",
        "agent_confidence",
        "is_single_panel",
        "is_topology_target",
        "has_visible_watermark",
        "geometry_usable",
        "agent_reason",
        "agent_visible_cues",
        "elapsed_sec",
        "error",
        "raw_response",
    ]
    consensus_fields = [
        "panel_id",
        "phase",
        "split",
        "panel_png_path",
        "topology_v1_panel_json_path",
        "v1_5_candidate_score",
        "v1_5_candidate_bucket",
        "known_policy_decision",
        "known_review_label",
        "consensus_label",
        "consensus_decision",
        "consensus_confidence",
        "agreement_count",
        "agent_count",
        "reason",
    ]
    write_csv(paths["agent_outputs"], agent_rows, agent_fields)
    write_csv(paths["consensus"], consensus_rows, consensus_fields)
    summary = {
        "input_csv": rel(args.input),
        "dry_run": args.dry_run,
        "providers": args.providers,
        "input_rows": len(read_csv(args.input)) if not args.limit else args.limit,
        "agent_output_rows": len(agent_rows),
        "consensus_rows": len(consensus_rows),
        "consensus_decision_counts": dict(Counter(str(row["consensus_decision"]) for row in consensus_rows)),
        "consensus_label_counts": dict(Counter(str(row["consensus_label"]) for row in consensus_rows)),
        "agent_label_counts": {
            agent: dict(Counter(str(row["agent_label"]) for row in agent_rows if row["agent"] == agent))
            for agent in args.providers
        },
        "outputs": {key: rel(value) for key, value in paths.items()},
    }
    write_json(paths["summary"], summary)
    write_report(paths["report"], summary)
    print(f"Consensus rows: {len(consensus_rows)}")
    for key, value in paths.items():
        print(f"Wrote: {rel(value)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_PREFIX)
    parser.add_argument("--providers", nargs="+", default=["doubao", "deepseek", "zhipu"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-text-fallback", action="store_true", default=True)
    parser.add_argument("--no-text-fallback", action="store_false", dest="allow_text_fallback")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--image-cache", type=Path, default=DEFAULT_IMAGE_CACHE)
    parser.add_argument("--max-image-side", type=int, default=3072)
    parser.add_argument("--max-image-pixels", type=int, default=14_000_000)
    args = parser.parse_args()
    args.image_cache = args.image_cache.resolve()
    return args


def main() -> None:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    agent_rows, consensus_rows = run(args)
    write_outputs(args, agent_rows, consensus_rows)


if __name__ == "__main__":
    main()
