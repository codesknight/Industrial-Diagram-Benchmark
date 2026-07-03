"""Use local Ollama vision models to review visible watermark candidates."""

from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / "data_index"
DEFAULT_INPUT = INDEX_DIR / "watermark_candidates.csv"
DEFAULT_MODELS = ["deepseek-ocr:3b", "qwen2.5vl:7b"]

PROMPT = """You are reviewing an industrial CAD drawing image for visible watermarks.

Task:
Decide whether the image visibly contains a watermark, source mark, website, marketplace mark, or library mark that is NOT part of the engineering drawing itself.

Look especially for Chinese or website marks such as:
星欣, 星欣设计图库, 蚂蚁图库, 淘宝, taobao, wm666, 设计库, 图库.

Return only compact JSON with these fields:
{{
  "visible_watermark": true_or_false,
  "evidence": "exact visible words or short reason",
  "confidence": "high|medium|low"
}}
"""


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing input CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def image_to_base64(path: Path, max_side: int) -> str:
    with Image.open(path) as image:
        image = image.convert("RGB")
        width, height = image.size
        scale = min(max_side / max(width, height), 1.0)
        if scale < 1.0:
            image = image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def call_ollama(model: str, image_b64: str, timeout: int, num_ctx: int) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": PROMPT,
                "images": [image_b64],
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_ctx": num_ctx,
            "num_predict": 256,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    message = result.get("message", {})
    return str(message.get("content", result.get("response", ""))).strip()


def parse_visible(response: str) -> tuple[str, str, str]:
    text = response.strip()
    try:
        match = re.search(r"\{.*\}", text, flags=re.S)
        payload = json.loads(match.group(0) if match else text)
        visible = payload.get("visible_watermark")
        evidence = str(payload.get("evidence", "")).strip()
        confidence = str(payload.get("confidence", "")).strip()
        if isinstance(visible, bool):
            return str(visible).lower(), evidence, confidence
    except Exception:
        pass

    folded = text.lower()
    positive_terms = ["true", "yes", "watermark", "taobao", "wm666", "星欣", "图库", "淘宝", "蚂蚁"]
    negative_terms = ["false", "no visible", "no watermark", "not contain", "does not contain"]
    if any(term in folded for term in negative_terms):
        return "false", text[:240], "low"
    if any(term in folded for term in positive_terms):
        return "true", text[:240], "low"
    return "unknown", text[:240], "low"


def consensus(model_rows: List[Dict[str, object]]) -> str:
    positives = sum(1 for row in model_rows if row["model_visible_watermark"] == "true")
    negatives = sum(1 for row in model_rows if row["model_visible_watermark"] == "false")
    if positives >= 2:
        return "visible_watermark"
    if positives == 1 and negatives == 0:
        return "likely_visible_watermark"
    if negatives >= 2:
        return "not_visible_watermark"
    if positives == 0 and negatives == 1:
        return "single_model_not_visible"
    if positives == 1:
        return "single_model_visible_watermark"
    if all(row["model_visible_watermark"] == "error" for row in model_rows):
        return "model_errors"
    return "needs_manual_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--max-side", type=int, default=2200)
    parser.add_argument("--num-ctx", type=int, default=4096)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input)
    if args.limit:
        rows = rows[: args.limit]

    model_outputs: List[Dict[str, object]] = []
    consensus_rows: List[Dict[str, object]] = []

    for index, row in enumerate(rows, start=1):
        image_path = ROOT / row["png_path"]
        image_b64 = image_to_base64(image_path, args.max_side)
        current_model_rows: List[Dict[str, object]] = []
        for model in args.models:
            started = time.time()
            error = ""
            response = ""
            try:
                response = call_ollama(model, image_b64, args.timeout, args.num_ctx)
                visible, evidence, confidence = parse_visible(response)
            except urllib.error.HTTPError as exc:
                visible, evidence, confidence = "error", "", ""
                body = exc.read().decode("utf-8", errors="ignore")
                error = f"{exc}; {body}"
            except Exception as exc:  # noqa: BLE001
                visible, evidence, confidence = "error", "", ""
                error = str(exc)
            elapsed = round(time.time() - started, 2)
            out = {
                "drawing_key": row["drawing_key"],
                "png_path": row["png_path"],
                "json_text_hits": row.get("json_text_hits", ""),
                "model": model,
                "model_visible_watermark": visible,
                "model_evidence": evidence,
                "model_confidence": confidence,
                "elapsed_sec": elapsed,
                "error": error,
                "raw_response": response,
            }
            model_outputs.append(out)
            current_model_rows.append(out)
            print(f"[{index}/{len(rows)}] {model}: {visible} {evidence[:60]}")

        consensus_rows.append(
            {
                "drawing_key": row["drawing_key"],
                "png_path": row["png_path"],
                "json_text_hits": row.get("json_text_hits", ""),
                "vision_consensus": consensus(current_model_rows),
                "positive_models": ";".join(
                    str(item["model"]) for item in current_model_rows if item["model_visible_watermark"] == "true"
                ),
                "negative_models": ";".join(
                    str(item["model"]) for item in current_model_rows if item["model_visible_watermark"] == "false"
                ),
                "model_count": len(current_model_rows),
            }
        )

    model_fields = [
        "drawing_key",
        "png_path",
        "json_text_hits",
        "model",
        "model_visible_watermark",
        "model_evidence",
        "model_confidence",
        "elapsed_sec",
        "error",
        "raw_response",
    ]
    consensus_fields = [
        "drawing_key",
        "png_path",
        "json_text_hits",
        "vision_consensus",
        "positive_models",
        "negative_models",
        "model_count",
    ]
    write_csv(INDEX_DIR / "watermark_vision_model_outputs.csv", model_outputs, model_fields)
    write_csv(INDEX_DIR / "watermark_vision_consensus.csv", consensus_rows, consensus_fields)

    summary = {
        "input_rows": len(rows),
        "models": args.models,
        "max_side": args.max_side,
        "num_ctx": args.num_ctx,
        "consensus_counts": {
            label: sum(1 for row in consensus_rows if row["vision_consensus"] == label)
            for label in sorted(set(str(row["vision_consensus"]) for row in consensus_rows))
        },
        "model_status_counts": {
            model: {
                label: sum(
                    1
                    for row in model_outputs
                    if row["model"] == model and row["model_visible_watermark"] == label
                )
                for label in sorted(
                    set(
                        str(row["model_visible_watermark"])
                        for row in model_outputs
                        if row["model"] == model
                    )
                )
            }
            for model in args.models
        },
    }
    (INDEX_DIR / "watermark_vision_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary, consensus_rows)
    print(f"Wrote: {INDEX_DIR.relative_to(ROOT).as_posix()}/watermark_vision_consensus.csv")


def write_report(summary: Dict[str, object], rows: List[Dict[str, object]]) -> None:
    lines = [
        "# Watermark Vision Review Report",
        "",
        "This report uses local Ollama vision models to review visible watermark candidates.",
        "",
        "## Summary",
        "",
        f"- Input rows: {summary['input_rows']}",
        f"- Models: {', '.join(summary['models'])}",
        f"- Max side: {summary['max_side']}",
        f"- Context: {summary['num_ctx']}",
        "",
        "## Consensus Counts",
        "",
    ]
    for label, count in summary["consensus_counts"].items():
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Model Status Counts", ""])
    for model, counts in summary["model_status_counts"].items():
        lines.append(f"- {model}: {counts}")
    lines.extend(["", "## Rows", "", "| drawing_key | consensus | positive_models | negative_models | json_text_hits |", "|---|---|---|---|---|"])
    for row in rows:
        lines.append(
            f"| `{row['drawing_key']}` | {row['vision_consensus']} | "
            f"{row['positive_models']} | {row['negative_models']} | {row['json_text_hits']} |"
        )
    (INDEX_DIR / "watermark_vision_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
