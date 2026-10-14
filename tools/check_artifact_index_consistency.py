"""Check that project_artifact_index.md covers root-level test artifacts.

This offline diagnostic scans root-level JSON/CSV/MD artifacts under tests/ and
checks that the artifact index mentions them. It does not run eval, call RAG,
contact Qdrant or an LLM, move files, or migrate reports.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "maintenance-0.1.3"

DEFAULT_TEST_DIR = Path("tests")
DEFAULT_INDEX_PATH = Path("docs/indexes/project_artifact_index.md")
DEFAULT_OUTPUT_PATH = Path("tests/artifact_index_consistency_report.json")

ARTIFACT_SUFFIXES = {".json", ".csv", ".md"}

REQUIRED_ANCHORS = [
    "tests/*.json",
    "tests/*.csv",
    "tests/fixtures/",
    "tests/manual_review_export_pipeline_dry_run_artifacts/",
    "tools/manual_review_visual_workbench/index.html",
    "docs/",
    "reports/eval",
    "reports/audits",
    "reports/manual_review",
    "reports/dry_run",
    "Eval 与回归报告",
    "Evidence 与检索质量诊断",
    "Legal Functional Typing",
    "Manual Review 与治理闭环",
    "Dry-Run 与安全隔离产物",
    "Health Check 与结构维护",
    "工具入口与产物关系",
    "维护规则",
]

SEMANTIC_GUARDRAILS = [
    "不要把 AI suggestion、prescreen、pilot assist、mobile aid 写成 completed manual decision",
    "不要把 `tests/evidence_fixture_candidate_pool.json` 写成已经进入 eval case",
    "不要把 `reports/` scaffold 写成当前权威输出目录",
]


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def root_level_artifacts(test_dir: Path) -> list[Path]:
    if not test_dir.exists():
        return []
    return sorted(
        path
        for path in test_dir.iterdir()
        if path.is_file() and path.suffix.lower() in ARTIFACT_SUFFIXES
    )


def token_set(content: str) -> set[str]:
    tokens = set()
    for token in content.replace("`", " ").split():
        cleaned = token.strip(".,;:()[]{}，。；：（）【】")
        if cleaned.startswith("tests/"):
            tokens.add(cleaned)
    return tokens


def build_report(root: Path, test_dir: Path, index_path: Path) -> dict[str, Any]:
    root = root.resolve()
    test_dir = (root / test_dir).resolve() if not test_dir.is_absolute() else test_dir.resolve()
    index_path = (root / index_path).resolve() if not index_path.is_absolute() else index_path.resolve()

    artifacts = [normalize_rel(path, root) for path in root_level_artifacts(test_dir)]
    content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    tokens = token_set(content)
    missing_artifacts = [path for path in artifacts if path not in tokens]
    missing_anchors = [anchor for anchor in REQUIRED_ANCHORS if anchor not in content]
    missing_guardrails = [guardrail for guardrail in SEMANTIC_GUARDRAILS if guardrail not in content]

    errors = []
    if not index_path.exists():
        errors.append("missing_artifact_index")
    if missing_artifacts:
        errors.append("root_level_artifact_missing_from_index")
    if missing_anchors:
        errors.append("missing_required_anchor")
    if missing_guardrails:
        errors.append("missing_semantic_guardrail")

    return {
        "version": VERSION,
        "scope": "offline artifact index coverage diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "test_dir": normalize_rel(test_dir, root) if test_dir.is_relative_to(root) else str(test_dir),
        "index_path": normalize_rel(index_path, root) if index_path.is_relative_to(root) else str(index_path),
        "guardrails": {
            "scanned_files_are_not_modified": True,
            "writes_report_only": True,
            "report_move_or_migration": "not_performed",
            "default_path_change": "not_performed",
            "full_eval": "not_run",
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
        },
        "summary": {
            "status": "passed" if not errors else "failed",
            "root_level_artifact_count": len(artifacts),
            "indexed_root_level_artifact_count": len(artifacts) - len(missing_artifacts),
            "missing_artifact_count": len(missing_artifacts),
            "missing_required_anchor_count": len(missing_anchors),
            "missing_semantic_guardrail_count": len(missing_guardrails),
            "error_count": len(errors),
        },
        "errors": errors,
        "root_level_artifacts": artifacts,
        "missing_artifacts": missing_artifacts,
        "missing_required_anchors": missing_anchors,
        "missing_semantic_guardrails": missing_guardrails,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check project_artifact_index.md coverage for root-level artifacts.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--test-dir", type=Path, default=DEFAULT_TEST_DIR)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root, args.test_dir, args.index)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Artifact index consistency check completed: "
        f"{summary['status']}, "
        f"{summary['root_level_artifact_count']} root-level artifacts, "
        f"{summary['missing_artifact_count']} missing"
    )
    return 1 if args.fail_on_error and summary["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
