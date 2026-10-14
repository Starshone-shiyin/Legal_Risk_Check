"""Build the v0.4.9.11 retrieval input quality series closeout report.

The closeout records that v0.4.9.x completed the offline retrieval input
quality governance chain through metadata/chunking dry-run contract. It does
not implement the diagnostic runner or authorize runtime changes.
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


VERSION = "0.4.9.11"

SERIES_REPORTS = [
    ("0.4.9.0", "intake", legacy_report_path("retrieval_input_quality_intake_report.json"), "retrieval_input_quality_intake"),
    ("0.4.9.1", "audit_spec", legacy_report_path("retrieval_input_quality_audit_spec_report.json"), "retrieval_input_quality_audit_spec"),
    ("0.4.9.2", "offline_audit", legacy_report_path("retrieval_input_quality_offline_audit_report.json"), "retrieval_input_quality_offline_audit"),
    ("0.4.9.3", "offline_audit_gate", legacy_report_path("retrieval_input_quality_offline_audit_gate_report.json"), "retrieval_input_quality_offline_audit_gate"),
    ("0.4.9.4", "diagnostic_prioritization", legacy_report_path("retrieval_input_quality_diagnostic_prioritization_report.json"), "retrieval_input_quality_diagnostic_prioritization"),
    ("0.4.9.5", "diagnostic_prioritization_gate", legacy_report_path("retrieval_input_quality_diagnostic_prioritization_gate_report.json"), "retrieval_input_quality_diagnostic_prioritization_gate"),
    ("0.4.9.6", "metadata_chunking_diagnostic_spec", legacy_report_path("metadata_chunking_diagnostic_spec_report.json"), "metadata_chunking_diagnostic_spec"),
    ("0.4.9.7", "metadata_chunking_diagnostic_spec_gate", legacy_report_path("metadata_chunking_diagnostic_spec_gate_report.json"), "metadata_chunking_diagnostic_spec_gate"),
    ("0.4.9.8", "metadata_chunking_diagnostic_runner_design", legacy_report_path("metadata_chunking_diagnostic_runner_design_report.json"), "metadata_chunking_diagnostic_runner_design"),
    ("0.4.9.9", "metadata_chunking_diagnostic_runner_design_gate", legacy_report_path("metadata_chunking_diagnostic_runner_design_gate_report.json"), "metadata_chunking_diagnostic_runner_design_gate"),
    ("0.4.9.10", "metadata_chunking_diagnostic_dry_run_contract", legacy_report_path("metadata_chunking_diagnostic_dry_run_contract_report.json"), "metadata_chunking_diagnostic_dry_run_contract"),
]

DEFAULT_OUTPUT_PATH = legacy_report_path("retrieval_input_quality_series_closeout_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/retrieval_input_quality_series_closeout_v0.4.9.11.md")

GUARDRAILS = {
    "saved_reports_only": True,
    "series_closeout_only": True,
    "diagnostic_runner_implemented": False,
    "diagnostic_run": "not_run",
    "qdrant_access": "disallowed",
    "knowledge_base_fulltext_scan": "disallowed",
    "rag_query_integration": "disallowed",
    "llm_access": "disallowed",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "runtime_policy_implementation_allowed": False,
    "rerank_change_allowed": False,
    "prompt_change_allowed": False,
    "full_eval": "not_run",
    "main_flow_mutation": "disallowed",
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

MOJIBAKE_MARKERS = ["\u951b", "\u7ecb", "\u9428", "\u93c2", "\u6d93", "\u4e63", "\ufffd"]
FORBIDDEN_KEYS = {
    "implementation_plan",
    "patch_plan",
    "files_to_change",
    "commands",
    "work_items",
    "engineering_tasks",
    "pending_tasks",
    "implementation_queue",
    "reviewer_decision",
    "human_outcome_record",
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


def sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def find_key_paths(value: Any, blocked: set[str], prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if key in blocked:
                paths.append(child_path)
            paths.extend(find_key_paths(child, blocked, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(find_key_paths(child, blocked, f"{prefix}[{index}]"))
    return paths


def readability_paths(value: Any, prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, str) and any(marker in value for marker in MOJIBAKE_MARKERS):
        paths.append(prefix)
    elif isinstance(value, dict):
        for key, child in value.items():
            paths.extend(readability_paths(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(readability_paths(child, f"{prefix}[{index}]"))
    return paths


def report_status(payload: dict[str, Any]) -> str:
    for key in [
        "contract_gate",
        "gate",
        "runner_design_gate",
        "spec_gate",
        "prioritization_gate",
        "audit_gate",
        "intake_gate",
    ]:
        status = as_dict(payload.get(key)).get("status")
        if isinstance(status, str):
            return status
    return as_dict(payload.get("summary")).get("status", "")


def build_series_rows() -> tuple[list[dict[str, Any]], list[str]]:
    rows = []
    blockers: list[str] = []
    for expected_version, step, path, expected_schema in SERIES_REPORTS:
        payload = load_json(path)
        row_blockers = []
        if not path.exists():
            row_blockers.append("missing_report")
        if payload.get("version") != expected_version:
            row_blockers.append("version_mismatch")
        if payload.get("schema_kind") != expected_schema:
            row_blockers.append("schema_mismatch")
        if find_key_paths(payload, FORBIDDEN_KEYS):
            row_blockers.append("forbidden_key_present")
        if readability_paths(payload):
            row_blockers.append("text_readability_issue")
        if row_blockers:
            blockers.extend([f"{step}:{blocker}" for blocker in row_blockers])
        rows.append({
            "version": expected_version,
            "step": step,
            "path": str(path),
            "schema_kind": payload.get("schema_kind"),
            "status_signal": report_status(payload),
            "present": path.exists(),
            "closeout_status": "passed" if not row_blockers else "failed",
            "blockers": row_blockers,
        })
    return rows, sorted_unique(blockers)


def build_report() -> dict[str, Any]:
    rows, source_blockers = build_series_rows()
    completed_versions = [row["version"] for row in rows if row["closeout_status"] == "passed"]
    expected_versions = [version for version, _, _, _ in SERIES_REPORTS]
    sequence_ok = completed_versions == expected_versions
    status = "v0_4_9_series_closed_for_diagnostic_governance" if not source_blockers and sequence_ok else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "retrieval_input_quality_series_closeout",
        "scope": "v0.4.9.x retrieval input quality governance series closeout",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": GUARDRAILS,
        "closeout_gate": {
            "status": status,
            "series": "v0.4.9.x",
            "allowed_next_step": "v0.4.10.x read-only metadata/chunking diagnostic runner series" if status != "blocked" else "blocked",
            "diagnostic_runner_implemented": False,
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": source_blockers + ([] if sequence_ok else ["series_sequence_incomplete"]),
        },
        "summary": {
            "status": status,
            "completed_step_count": len(completed_versions),
            "expected_step_count": len(SERIES_REPORTS),
            "completed_versions": completed_versions,
            "expected_versions": expected_versions,
            "diagnostic_runner_implemented": False,
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "recommended_next_series": "v0.4.10.x read-only metadata/chunking diagnostic runner series",
        },
        "series_rows": rows,
        "series_closeout_findings": [
            {
                "finding": "retrieval_input_quality_chain_completed",
                "status": "closed" if status != "blocked" else "blocked",
                "basis": "v0.4.9.0-v0.4.9.10 reports are present in order.",
            },
            {
                "finding": "metadata_chunking_path_reaches_dry_run_contract",
                "status": "closed" if status != "blocked" else "blocked",
                "basis": "spec, spec gate, runner design, runner design gate, and dry-run contract are present.",
            },
            {
                "finding": "runtime_not_authorized",
                "status": "closed",
                "basis": "No diagnostic runner was implemented and all closeout guardrails keep runtime changes disabled.",
            },
        ],
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "series_reports_ready", "status": "passed" if not source_blockers else "failed", "blockers": source_blockers},
        {"name": "series_sequence_complete", "status": "passed" if sequence_ok else "failed", "completed_versions": completed_versions},
        {"name": "diagnostic_runner_not_implemented", "status": "passed" if report["closeout_gate"]["diagnostic_runner_implemented"] is False else "failed"},
        {"name": "series_is_non_runtime", "status": "passed" if report["closeout_gate"]["implementation_allowed"] is False and report["closeout_gate"]["retrieval_logic_change_allowed"] is False else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    failed = [item["name"] for item in report["assertions"] if item["status"] != "passed"]
    if failed:
        report["closeout_gate"]["status"] = "blocked"
        report["closeout_gate"]["allowed_next_step"] = "blocked"
        report["closeout_gate"]["blockers"] = sorted_unique(report["closeout_gate"]["blockers"] + failed)
        report["summary"]["status"] = "blocked"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("closeout_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.11 Retrieval Input Quality Series Closeout",
        "",
        "This closeout marks v0.4.9.x complete as an offline retrieval input quality governance series. It does not implement a diagnostic runner and does not authorize runtime changes.",
        "",
        "## Overview",
        "",
        f"- Closeout status: `{gate.get('status')}`",
        f"- Completed steps: {summary.get('completed_step_count')} / {summary.get('expected_step_count')}",
        f"- Diagnostic runner implemented: {summary.get('diagnostic_runner_implemented')}",
        f"- Diagnostic run: `{summary.get('diagnostic_run')}`",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        f"- Recommended next series: `{summary.get('recommended_next_series')}`",
        "",
        "## Completed Steps",
        "",
        "| Version | Step | Status |",
        "|---|---|---|",
    ]
    for row in as_list(report.get("series_rows")):
        lines.append(f"| `{row.get('version')}` | `{row.get('step')}` | `{row.get('closeout_status')}` |")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- v0.4.9.x is closed for offline governance, not runtime implementation.",
        "- The series did not create or execute a diagnostic runner.",
        "- It does not read Qdrant, scan the knowledge base, run RAG, call an LLM, or run full evaluation.",
        "- Future diagnostic runner work needs a separately approved series.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report()
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Retrieval input quality series closeout built: "
        f"{summary.get('status')}, {summary.get('completed_step_count')} steps"
    )
    return 0 if report["closeout_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
