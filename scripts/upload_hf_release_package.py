"""Upload the prepared Topology Panel v1 release package to Hugging Face."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, Optional


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_DIR = ROOT / "outputs" / "hf_release_topology_panel_v1"
DEFAULT_REPO_ID = "yanhongliu/Industrial-Diagram-Benchmark"
DEFAULT_COMMIT_MESSAGE = "Add Topology Panel v1 clean baseline benchmark package"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE_DIR)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--commit-message", default=DEFAULT_COMMIT_MESSAGE)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_dotenv_token() -> Optional[str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return None

    token_keys = {
        "HF_TOKEN",
        "HUGGINGFACE_TOKEN",
        "HUGGING_FACE_TOKEN",
        "HUGGINGFACE_HUB_TOKEN",
    }
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key in token_keys and value:
            return value
    return None


def iter_files(package_dir: Path) -> Iterable[Path]:
    for path in sorted(package_dir.rglob("*")):
        if path.is_file():
            yield path


def main() -> None:
    args = parse_args()
    package_dir = args.package_dir.resolve()

    if not package_dir.exists():
        raise SystemExit(
            f"Missing package dir: {package_dir}\n"
            "Run: python scripts/prepare_hf_release_package.py"
        )
    if not (package_dir / "README.md").exists():
        raise SystemExit(f"Package dir does not contain README.md: {package_dir}")

    files = list(iter_files(package_dir))
    if args.dry_run:
        print(f"Repo id: {args.repo_id}")
        print(f"Package dir: {package_dir.relative_to(ROOT).as_posix()}")
        print(f"Files: {len(files)}")
        for path in files:
            print(path.relative_to(package_dir).as_posix())
        return

    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: huggingface_hub. Install it with: pip install -r requirements.txt"
        ) from exc

    token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGINGFACE_TOKEN")
        or os.environ.get("HUGGING_FACE_TOKEN")
        or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        or load_dotenv_token()
    )

    api = HfApi(token=token)
    if token is None:
        try:
            api.whoami()
        except Exception as exc:
            raise SystemExit(
                "No Hugging Face token found. Run `hf auth login` or add `HF_TOKEN=...` "
                "to `.env`, then rerun this script."
            ) from exc

    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="dataset",
        folder_path=str(package_dir),
        path_in_repo=".",
        revision=args.revision,
        commit_message=args.commit_message,
    )

    print(f"Uploaded {len(files)} files to dataset `{args.repo_id}`")


if __name__ == "__main__":
    main()
