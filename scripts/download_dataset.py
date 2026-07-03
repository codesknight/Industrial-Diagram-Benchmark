"""Download the hosted dataset from Hugging Face.

This keeps the GitHub repository lightweight while allowing a local `datas/`
folder to be restored when needed.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ID = "yanhongliu/Industrial-Diagram-Benchmark"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--local-dir", default=str(ROOT / "datas"))
    parser.add_argument(
        "--allow-pattern",
        action="append",
        default=None,
        help="Optional Hugging Face allow pattern. Can be passed multiple times.",
    )
    parser.add_argument(
        "--ignore-pattern",
        action="append",
        default=None,
        help="Optional Hugging Face ignore pattern. Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: huggingface_hub. Install it with: pip install -r requirements.txt"
        ) from exc

    local_dir = Path(args.local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=args.repo_id,
        repo_type="dataset",
        revision=args.revision,
        local_dir=str(local_dir),
        allow_patterns=args.allow_pattern,
        ignore_patterns=args.ignore_pattern,
    )

    print(f"Downloaded dataset `{args.repo_id}` to {local_dir}")


if __name__ == "__main__":
    main()
