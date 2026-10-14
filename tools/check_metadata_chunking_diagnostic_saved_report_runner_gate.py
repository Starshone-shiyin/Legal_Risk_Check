"""Check the v0.4.10.1 saved-report metadata/chunking runner gate.

The gate reads only the saved runner report and verifies row count, output
contract, zero blocked rows, and non-runtime boundaries. It does not inspect
Qdrant, scan the knowledge base, or authorize fixes.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_diagnostic_dry_run_contract import DRY_RUN_OUTPUT_FIELDS


VERSION = "0.4.10.2"

DEFAULT_RUNNER_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_saved_report_runner_gate_v0.4.10.2.md")

GUARDRAILS = {
    "saved_reports_only": True,
    "gate_only": True,
    "diagnostic_run": "not_run_by_gate",
    "evidence_level_metadata_snapshot_read": False,
    "qdrant_access": "disallowed",
    "knowledge_base_fulltext_scan": "disallowed",
    "rag_query_integration": "disallowed",
    "llm_access": "disallowed",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "metadata_mutation": "disallowed",
    "chunk_mutation": "disallowed",
    "ingestion_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def runner_checks(runner: dict[str, Any]) -> list[dict[str, Any]]:
    gate = as_dict(runner.get("runner_gate"))
    summary = as_dict(runner.get("summary"))
    rows = as_list(runner.get("diagnostic_rows"))
    missing_fields = [
        {"row": index, "missing": sorted(set(DRY_RUN_OUTPUT_FIELDS) - set(as_dict(row).keys()))}
        for index, row in enumerate(rows, start=1)
        if set(DRY_RUN_OUTPUT_FIELDS) - set(as_dict(row).keys())
    ]
    blocked_rows = [
        index for index, row in enumerate(rows, start=1)
        if as_list(as_dict(row).get("blocking_findings"))
        or as_dict(row).get("dry_run_status") != "completed_saved_report_scope"
    ]
    return [
        {"name": "runner_schema", "status": "passed" if runner.get("schema_kind") == "metadata_chunking_diagnostic_saved_report_runner" else "failed"},
        {"name": "runner_version", "status": "passed" if runner.get("version") == "0.4.10.1" else "failed"},
        {"name": "runner_completed", "status": "passed" if gate.get("status") == "completed_saved_report_metadata_chunking_diagnostic" else "failed", "actual": gate.get("status")},
        {"name": "runner_next_step", "status": "passed" if gate.get("allowed_next_step") == "metadata_chunking_diagnostic_saved_report_runner_gate" else "failed"},
        {"name": "row_count", "status": "passed" if len(rows) == 40 and summary.get("diagnostic_row_count") == 40 else "failed", "row_count": len(rows)},
        {"name": "zero_blocked_rows", "status": "passed" if not blocked_rows and summary.get("blocked_row_count") == 0 else "failed", "blocked_rows": blocked_rows},
        {"name": "output_contract_complete", "status": "passed" if not missing_fields else "failed", "missing_fields": missing_fields},
        {"name": "saved_report_scope_only", "status": "passed" if gate.get("diagnostic_run") == "saved_report_scope_only" and gate.get("evidence_level_metadata_snapshot_read") is False else "failed"},
        {"name": "runtime_changes_blocked", "status": "passed" if gate.get("implementation_allowed") is False and gate.get("retrieval_logic_change_allowed") is False else "failed"},
    ]


def build_report(runner_report_path: Path = DEFAULT_RUNNER_REPORT_PATH) -> dict[str, Any]:
    runner = load_json(runner_report_path)
    checks = runner_checks(runner)
    failed = [check for check in checks if check["status"] != "passed"]
    status = "open_for_v0_4_10_series_closeout" if not failed else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_saved_report_runner_gate",
        "scope": "saved-report metadata/chunking diagnostic runner gate only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "metadata_chunking_diagnostic_saved_report_runner_report": {
                "path": str(runner_report_path),
                "present": runner_report_path.exists(),
                "version": runner.get("version"),
                "schema_kind": runner.get("schema_kind"),
            }
        },
        "guardrails": GUARDRAILS,
        "gate": {
            "status": status,
            "allowed_next_step": "v0_4_10_series_closeout" if not failed else "blocked",
            "diagnostic_run": "not_run_by_gate",
            "evidence_level_metadata_snapshot_read": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": [check["name"] for check in failed],
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "source_diagnostic_row_count": as_dict(runner.get("summary")).get("diagnostic_row_count"),
            "source_blocked_row_count": as_dict(runner.get("summary")).get("blocked_row_count"),
            "next_version_recommendation": "v0.4.10.3 metadata/chunking diagnostic runner series closeout",
        },
        "checks": checks,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.10.2 Metadata/Chunking Saved-Report Runner Gate",
        "",
        "This gate checks the saved-report runner output. It does not run diagnostics or inspect evidence-level metadata.",
        "",
        f"- Gate status: `{gate.get('status')}`",
        f"- Checks: {summary.get('check_count')}",
        f"- Failed checks: {summary.get('failed_check_count')}",
        f"- Source diagnostic rows: {summary.get('source_diagnostic_row_count')}",
        f"- Source blocked rows: {summary.get('source_blocked_row_count')}",
        f"- Next allowed step: `{gate.get('allowed_next_step')}`",
        "",
        "## Boundaries",
        "",
        "- Gate only; no diagnostic execution in this version.",
        "- No evidence-level metadata snapshot, Qdrant, knowledge-base fulltext scan, RAG, LLM, metadata edit, chunk rewrite, or eval-case change.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-report", type=Path, default=DEFAULT_RUNNER_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.runner_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking saved-report runner gate checked: "
        f"{summary.get('status')}, {summary.get('failed_check_count')} failed"
    )
    return 0 if report["gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
