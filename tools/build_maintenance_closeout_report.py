"""Build a closeout report for the maintenance-0.1.x series.

The report summarizes existing maintenance diagnostics. It does not run eval,
call RAG, contact Qdrant or an LLM, move files, or change default paths.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "maintenance-0.1.8"

DEFAULT_OUTPUT_PATH = Path("tests/maintenance_closeout_report.json")

MAINTENANCE_REPORTS = [
    Path("tests/encoding_hygiene_report.json"),
    Path("tests/tool_index_consistency_report.json"),
    Path("tests/test_index_consistency_report.json"),
    Path("tests/artifact_index_consistency_report.json"),
    Path("tests/layout_migration_readiness_report.json"),
]

INDEX_DOCS = [
    Path("docs/indexes/project_structure_index.md"),
    Path("docs/indexes/project_artifact_index.md"),
    Path("docs/indexes/project_tool_index.md"),
    Path("docs/indexes/project_test_index.md"),
    Path("docs/indexes/project_maintenance_index.md"),
    Path("docs/maintenance_terms_guide.md"),
]


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def report_rows(root: Path) -> list[dict[str, Any]]:
    rows = []
    for rel_path in MAINTENANCE_REPORTS:
        path = root / rel_path
        data = read_json(path)
        summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
        rows.append({
            "path": rel_path.as_posix(),
            "present": path.exists(),
            "status": summary.get("status"),
            "summary": summary,
        })
    return rows


def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    reports = report_rows(root)
    missing_docs = [path.as_posix() for path in INDEX_DOCS if not (root / path).exists()]
    failed_reports = [
        row for row in reports if not row["present"] or row.get("status") in {"failed", "blocked"}
    ]
    warnings = []
    readiness = read_json(root / "tests/layout_migration_readiness_report.json")
    readiness_summary = readiness.get("summary") if isinstance(readiness, dict) else {}
    if readiness_summary.get("ready_for_automatic_migration") is not False:
        warnings.append("layout_readiness_does_not_explicitly_block_automatic_migration")

    status = "passed" if not missing_docs and not failed_reports and not warnings else "attention_required"
    return {
        "version": VERSION,
        "scope": "maintenance-0.1.x closeout report",
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
            "status": status,
            "maintenance_series": "maintenance-0.1.x",
            "report_count": len(reports),
            "failed_report_count": len(failed_reports),
            "missing_doc_count": len(missing_docs),
            "warning_count": len(warnings),
            "manual_review_gate": "still_blocked_until_real_completed_decisions",
            "layout_migration": "not_performed",
            "rag_main_flow_change": "not_performed",
        },
        "reports": reports,
        "missing_docs": missing_docs,
        "failed_reports": failed_reports,
        "warnings": warnings,
        "closeout_notes": [
            "维护系列增强了索引、可发现性、一致性检查和收尾报告。",
            "project health check 是 closeout 之后的总门禁，避免 closeout 与 health check 互相依赖。",
            "维护完成不代表人工复核完成；当前仍需要真实人工 completed manual decision。",
            "维护完成不代表目录迁移完成；reports/ 和 tool 子目录仍是脚手架。",
            "进入 v0.4.8.x 前，应继续保持不补 hidden seed、不新增 anchor、不绕过人工复核门禁。",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build maintenance closeout report.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-attention", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Maintenance closeout report completed: "
        f"{summary['status']}, "
        f"{summary['report_count']} reports, "
        f"{summary['failed_report_count']} failed"
    )
    return 1 if args.fail_on_attention and summary["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
