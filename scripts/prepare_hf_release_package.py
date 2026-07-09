"""Prepare a local Hugging Face release package for Topology Panel v1."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "hf_release_topology_panel_v1"

PACKAGE_ID = "hf_release_topology_panel_v1_2026-07-09"


@dataclass(frozen=True)
class ReleaseFile:
    source: str
    target: str
    category: str
    required: bool
    note: str


CORE_FILES = [
    ReleaseFile(
        "docs/huggingface_dataset_card.md",
        "README.md",
        "dataset_card",
        True,
        "Hugging Face Dataset README.md",
    ),
    ReleaseFile(
        "data_index/HF_RELEASE_FILES.md",
        "data_index/HF_RELEASE_FILES.md",
        "release_checklist",
        True,
        "Release file checklist",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_final_baseline_manifest.csv",
        "data_index/topology_panel_v1_final_baseline_manifest.csv",
        "benchmark_core",
        True,
        "Formal 14-row Topology Panel v1 baseline",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_benchmark_manifest.jsonl",
        "data_index/topology_panel_v1_benchmark_manifest.jsonl",
        "benchmark_core",
        True,
        "Benchmark JSONL entrypoint",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_benchmark_summary.json",
        "data_index/topology_panel_v1_benchmark_summary.json",
        "benchmark_core",
        True,
        "Benchmark package summary",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_benchmark_report.md",
        "data_index/topology_panel_v1_benchmark_report.md",
        "benchmark_core",
        True,
        "Benchmark package report",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_eval_summary.json",
        "data_index/topology_panel_v1_eval_summary.json",
        "benchmark_core",
        True,
        "Default sanity-check evaluation summary",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_eval_report.md",
        "data_index/topology_panel_v1_eval_report.md",
        "benchmark_core",
        True,
        "Default sanity-check evaluation report",
    ),
    ReleaseFile(
        "docs/topology_graph_eval_protocol_v1.md",
        "docs/topology_graph_eval_protocol_v1.md",
        "protocol",
        True,
        "Topology Graph v1 evaluation protocol",
    ),
    ReleaseFile(
        "docs/topology_panel_v1_release_status.md",
        "docs/topology_panel_v1_release_status.md",
        "protocol",
        True,
        "Chinese release status document",
    ),
    ReleaseFile(
        "README.md",
        "docs/github_README.md",
        "protocol",
        True,
        "GitHub project README copied as auxiliary documentation",
    ),
]


RECOMMENDED_FILES = [
    ReleaseFile(
        "data_index/topology_panel_v1_release_manifest.csv",
        "data_index/topology_panel_v1_release_manifest.csv",
        "release_partition",
        False,
        "Release baseline manifest",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_release_train.csv",
        "data_index/topology_panel_v1_release_train.csv",
        "release_partition",
        False,
        "Train split",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_release_val.csv",
        "data_index/topology_panel_v1_release_val.csv",
        "release_partition",
        False,
        "Validation split",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_release_test.csv",
        "data_index/topology_panel_v1_release_test.csv",
        "release_partition",
        False,
        "Test split",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_release_summary.json",
        "data_index/topology_panel_v1_release_summary.json",
        "release_partition",
        False,
        "Release summary",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_release_report.md",
        "data_index/topology_panel_v1_release_report.md",
        "release_partition",
        False,
        "Release report",
    ),
]


BOUNDARY_FILES = [
    ReleaseFile(
        "data_index/topology_panel_v1_release_excluded_manifest.csv",
        "data_index/topology_panel_v1_release_excluded_manifest.csv",
        "boundary",
        False,
        "Excluded badcase manifest",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_release_improvement_manifest.csv",
        "data_index/topology_panel_v1_release_improvement_manifest.csv",
        "boundary",
        False,
        "Original v1 improvement target manifest",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_1_abandoned_manifest.csv",
        "data_index/topology_panel_v1_1_abandoned_manifest.csv",
        "boundary",
        False,
        "Abandoned still-fragmented rows",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_1_keep_improvement_manifest.csv",
        "data_index/topology_panel_v1_1_keep_improvement_manifest.csv",
        "boundary",
        False,
        "Current v1.1 kept improvement candidates",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv",
        "data_index/topology_panel_v1_1_keep_terminal_anchor_manifest.csv",
        "boundary",
        False,
        "Terminal-anchor candidates",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_1_keep_over_connected_manifest.csv",
        "data_index/topology_panel_v1_1_keep_over_connected_manifest.csv",
        "boundary",
        False,
        "Over-connected candidates",
    ),
]


REVIEW_HTML_FILES = [
    ReleaseFile(
        "data_index/topology_panel_v1_baseline_review.html",
        "review_artifacts/topology_panel_v1_baseline_review.html",
        "review_artifact",
        False,
        "Baseline review HTML, optional and large",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_1_active_improvement_review.html",
        "review_artifacts/topology_panel_v1_1_active_improvement_review.html",
        "review_artifact",
        False,
        "Active improvement review HTML, optional and large",
    ),
    ReleaseFile(
        "data_index/topology_panel_v1_1_still_fragmented_diagnostic.html",
        "review_artifacts/topology_panel_v1_1_still_fragmented_diagnostic.html",
        "review_artifact",
        False,
        "Still-fragmented diagnostic HTML, optional and large",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--no-clean", action="store_true", help="Do not remove the output directory before copying.")
    parser.add_argument(
        "--include-review-html",
        action="store_true",
        help="Include large HTML review artifacts in review_artifacts/.",
    )
    return parser.parse_args()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def selected_files(include_review_html: bool) -> List[ReleaseFile]:
    files = [*CORE_FILES, *RECOMMENDED_FILES, *BOUNDARY_FILES]
    if include_review_html:
        files.extend(REVIEW_HTML_FILES)
    return files


def copy_file(item: ReleaseFile, output_dir: Path) -> dict:
    source = ROOT / item.source
    target = output_dir / item.target
    exists = source.exists()
    copied = False
    size_bytes = 0

    if exists:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied = True
        size_bytes = target.stat().st_size
    elif item.required:
        raise SystemExit(f"Missing required release file: {item.source}")

    return {
        "source": item.source,
        "target": target.relative_to(output_dir).as_posix(),
        "category": item.category,
        "required": item.required,
        "exists": exists,
        "copied": copied,
        "size_bytes": size_bytes,
        "note": item.note,
    }


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "target",
        "category",
        "required",
        "exists",
        "copied",
        "size_bytes",
        "note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(output_dir: Path, rows: List[dict], include_review_html: bool) -> dict:
    copied_rows = [row for row in rows if row["copied"]]
    missing_rows = [row for row in rows if not row["exists"]]
    required_missing = [row for row in missing_rows if row["required"]]
    total_size = sum(int(row["size_bytes"]) for row in copied_rows)
    category_counts = {}
    for row in copied_rows:
        category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1

    return {
        "package_id": PACKAGE_ID,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": rel(output_dir),
        "include_review_html": include_review_html,
        "selected_files": len(rows),
        "copied_files": len(copied_rows),
        "missing_files": len(missing_rows),
        "required_missing_files": len(required_missing),
        "total_size_bytes": total_size,
        "category_counts": category_counts,
        "rules": [
            "Package README.md is copied from docs/huggingface_dataset_card.md.",
            "Topology Panel v1 means the 14 clean baseline rows only.",
            "v1.1 candidates are included only as boundary files, not formal v1 scoring rows.",
            "Review HTML artifacts are excluded by default and require --include-review-html.",
        ],
        "outputs": {
            "manifest_csv": "data_index/hf_release_package_manifest.csv",
            "summary_json": "data_index/hf_release_package_summary.json",
            "report_md": "data_index/hf_release_package_report.md",
        },
    }


def write_summary(path: Path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, summary: dict, rows: List[dict]) -> None:
    lines = [
        "# Hugging Face Release Package Report",
        "",
        f"Package id: `{summary['package_id']}`",
        "",
        "## Summary",
        "",
        f"- Output dir: `{summary['output_dir']}`",
        f"- Selected files: {summary['selected_files']}",
        f"- Copied files: {summary['copied_files']}",
        f"- Missing files: {summary['missing_files']}",
        f"- Required missing files: {summary['required_missing_files']}",
        f"- Total size bytes: {summary['total_size_bytes']}",
        f"- Include review HTML: {summary['include_review_html']}",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in sorted(summary["category_counts"].items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Files", ""])
    for row in rows:
        status = "copied" if row["copied"] else "missing"
        lines.append(f"- `{row['target']}` ({row['category']}, {status})")
    lines.extend(
        [
            "",
            "## Upload Note",
            "",
            "Upload the contents of this package directory to the Hugging Face Dataset repository.",
            "The package root `README.md` is the dataset card.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()

    if not output_dir.is_relative_to(ROOT):
        raise SystemExit(f"Output directory must stay inside the repository: {output_dir}")

    if output_dir.exists() and not args.no_clean:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = [copy_file(item, output_dir) for item in selected_files(args.include_review_html)]

    manifest_path = output_dir / "data_index" / "hf_release_package_manifest.csv"
    summary_path = output_dir / "data_index" / "hf_release_package_summary.json"
    report_path = output_dir / "data_index" / "hf_release_package_report.md"

    write_csv(manifest_path, rows)
    summary = build_summary(output_dir, rows, args.include_review_html)
    write_summary(summary_path, summary)
    write_report(report_path, summary, rows)

    print(f"Package id: {PACKAGE_ID}")
    print(f"Output dir: {rel(output_dir)}")
    print(f"Copied files: {summary['copied_files']}")
    print(f"Missing files: {summary['missing_files']}")
    print(f"Wrote: {rel(manifest_path)}")
    print(f"Wrote: {rel(summary_path)}")
    print(f"Wrote: {rel(report_path)}")


if __name__ == "__main__":
    main()
