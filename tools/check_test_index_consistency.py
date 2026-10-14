"""Check that project_test_index.md covers root-level test assets.

This is an offline documentation-maintenance diagnostic. It does not run tests,
eval, RAG, Qdrant, or an LLM. The CLI only writes the requested JSON report.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "maintenance-0.1.2"

DEFAULT_TEST_DIR = Path("tests")
DEFAULT_INDEX_PATH = Path("docs/indexes/project_test_index.md")
DEFAULT_OUTPUT_PATH = Path("tests/test_index_consistency_report.json")

REQUIRED_ANCHORS = [
    "## 定位与约定",
    "## 测试套件",
    "## 测试产物",
    "## Legacy 路径与布局契约",
    "## Advisory 与正式人工复核边界",
    "## 已知误读风险",
    "tests/test_*.py",
    "tests/*.json",
    "tests/*.csv",
    "tests/fixtures/",
    "tests/manual_review_export_pipeline_dry_run_artifacts/",
]


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def root_level_test_files(test_dir: Path) -> list[Path]:
    if not test_dir.exists():
        return []
    return sorted(path for path in test_dir.glob("test_*.py") if path.is_file())


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

    tests = [normalize_rel(path, root) for path in root_level_test_files(test_dir)]
    content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    tokens = token_set(content)
    missing_tests = [path for path in tests if path not in tokens]
    missing_anchors = [anchor for anchor in REQUIRED_ANCHORS if anchor not in content]

    errors = []
    if not index_path.exists():
        errors.append("missing_test_index")
    if missing_tests:
        errors.append("root_level_test_missing_from_index")
    if missing_anchors:
        errors.append("missing_required_anchor")

    return {
        "version": VERSION,
        "scope": "offline test index coverage diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "test_dir": normalize_rel(test_dir, root) if test_dir.is_relative_to(root) else str(test_dir),
        "index_path": normalize_rel(index_path, root) if index_path.is_relative_to(root) else str(index_path),
        "guardrails": {
            "scanned_files_are_not_modified": True,
            "writes_report_only": True,
            "test_move_or_rename": "not_performed",
            "default_path_change": "not_performed",
            "tests_executed": "not_run",
            "full_eval": "not_run",
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
        },
        "summary": {
            "status": "passed" if not errors else "failed",
            "root_level_test_count": len(tests),
            "indexed_root_level_test_count": len(tests) - len(missing_tests),
            "missing_test_count": len(missing_tests),
            "missing_required_anchor_count": len(missing_anchors),
            "error_count": len(errors),
        },
        "errors": errors,
        "root_level_tests": tests,
        "missing_tests": missing_tests,
        "missing_required_anchors": missing_anchors,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check project_test_index.md coverage for root-level tests.")
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
        "Test index consistency check completed: "
        f"{summary['status']}, "
        f"{summary['root_level_test_count']} root-level tests, "
        f"{summary['missing_test_count']} missing"
    )
    return 1 if args.fail_on_error and summary["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
