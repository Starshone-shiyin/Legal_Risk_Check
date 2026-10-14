"""Report whether the project is ready for a future layout migration.

This maintenance diagnostic is deliberately conservative. It does not move
files, change default paths, run eval, call RAG, contact Qdrant, or use an LLM.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "maintenance-0.1.7"

DEFAULT_OUTPUT_PATH = Path("tests/layout_migration_readiness_report.json")

SCAFFOLD_DIRS = [
    Path("reports/eval"),
    Path("reports/audits"),
    Path("reports/manual_review"),
    Path("reports/dry_run"),
    Path("tools/eval"),
    Path("tools/evidence_diagnostics"),
    Path("tools/manual_review"),
    Path("tools/ops"),
    Path("tools/ingestion"),
]

REQUIRED_INDEXES = [
    Path("docs/indexes/project_structure_index.md"),
    Path("docs/indexes/project_artifact_index.md"),
    Path("docs/indexes/project_tool_index.md"),
    Path("docs/indexes/project_test_index.md"),
    Path("docs/indexes/project_maintenance_index.md"),
]

REQUIRED_REPORTS = [
    Path("tests/encoding_hygiene_report.json"),
    Path("tests/tool_index_consistency_report.json"),
    Path("tests/test_index_consistency_report.json"),
    Path("tests/artifact_index_consistency_report.json"),
]


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def scaffold_status(root: Path) -> list[dict[str, Any]]:
    rows = []
    for rel_path in SCAFFOLD_DIRS:
        path = root / rel_path
        non_placeholder_files = []
        if path.exists():
            for child in path.rglob("*"):
                if child.is_file() and child.name not in {".gitkeep", "README.md"}:
                    non_placeholder_files.append(child.relative_to(root).as_posix())
        rows.append({
            "path": rel_path.as_posix(),
            "present": path.is_dir(),
            "non_placeholder_files": non_placeholder_files,
        })
    return rows


def report_status(root: Path) -> list[dict[str, Any]]:
    rows = []
    for rel_path in REQUIRED_REPORTS:
        data = read_json(root / rel_path)
        summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
        rows.append({
            "path": rel_path.as_posix(),
            "present": (root / rel_path).exists(),
            "status": summary.get("status"),
            "failed_checks": summary.get("failed_checks"),
            "error_count": summary.get("error_count"),
        })
    return rows


def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    scaffolds = scaffold_status(root)
    reports = report_status(root)
    missing_indexes = [path.as_posix() for path in REQUIRED_INDEXES if not (root / path).exists()]
    missing_scaffolds = [row["path"] for row in scaffolds if not row["present"]]
    populated_scaffolds = [
        {"path": row["path"], "non_placeholder_files": row["non_placeholder_files"]}
        for row in scaffolds
        if row["non_placeholder_files"]
    ]
    failing_reports = [
        row
        for row in reports
        if not row["present"] or row.get("status") not in {None, "passed"}
    ]
    blockers = []
    if missing_indexes:
        blockers.append("missing_required_indexes")
    if missing_scaffolds:
        blockers.append("missing_scaffold_directories")
    if populated_scaffolds:
        blockers.append("scaffold_contains_migrated_files")
    if failing_reports:
        blockers.append("required_maintenance_report_not_passed")

    return {
        "version": VERSION,
        "scope": "offline layout migration readiness diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "guardrails": {
            "scanned_files_are_not_modified": True,
            "writes_report_only": True,
            "file_move_or_migration": "not_performed",
            "default_path_change": "not_performed",
            "full_eval": "not_run",
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
        },
        "summary": {
            "status": "ready_for_planning" if not blockers else "blocked",
            "ready_for_automatic_migration": False,
            "missing_index_count": len(missing_indexes),
            "missing_scaffold_count": len(missing_scaffolds),
            "populated_scaffold_count": len(populated_scaffolds),
            "failing_report_count": len(failing_reports),
            "blocker_count": len(blockers),
        },
        "blockers": blockers,
        "missing_indexes": missing_indexes,
        "missing_scaffolds": missing_scaffolds,
        "populated_scaffolds": populated_scaffolds,
        "required_reports": reports,
        "recommendation": (
            "可以规划目录迁移方案，但仍不应自动迁移。需要先设计兼容读取、双输出、回滚策略和版本计划。"
            if not blockers
            else "暂不适合规划迁移；先处理 blockers。"
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check readiness for future layout migration planning.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-blocker", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Layout migration readiness check completed: "
        f"{summary['status']}, "
        f"{summary['blocker_count']} blockers"
    )
    return 1 if args.fail_on_blocker and summary["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
