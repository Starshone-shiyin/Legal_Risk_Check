"""Build the v0.4.10.3 metadata/chunking diagnostic runner series closeout.

The closeout records that v0.4.10.x completed the saved-report runner chain.
It does not inspect evidence-level metadata, read Qdrant, scan the knowledge
base, run RAG/LLM, or authorize metadata/chunk/runtime fixes.
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


VERSION = "0.4.10.3"

DEFAULT_MANIFEST_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json")
DEFAULT_RUNNER_PATH = legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_report.json")
DEFAULT_GATE_PATH = legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_series_closeout_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md")

EXPECTED_STEPS = [
    ("0.4.10.0", "runner_manifest", DEFAULT_MANIFEST_PATH, "metadata_chunking_diagnostic_runner_manifest"),
    ("0.4.10.1", "saved_report_runner", DEFAULT_RUNNER_PATH, "metadata_chunking_diagnostic_saved_report_runner"),
    ("0.4.10.2", "saved_report_runner_gate", DEFAULT_GATE_PATH, "metadata_chunking_diagnostic_saved_report_runner_gate"),
]

GUARDRAILS = {
    "saved_reports_only": True,
    "series_closeout_only": True,
    "diagnostic_run": "saved_report_scope_only",
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


def sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


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
    for key in ["manifest_gate", "runner_gate", "gate", "closeout_gate"]:
        status = as_dict(payload.get(key)).get("status")
        if isinstance(status, str):
            return status
    return as_dict(payload.get("summary")).get("status", "")


def build_step_rows(steps: list[tuple[str, str, Path, str]] = EXPECTED_STEPS) -> tuple[list[dict[str, Any]], list[str]]:
    rows = []
    blockers: list[str] = []
    for expected_version, step, path, expected_schema in steps:
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


def build_report(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    runner_path: Path = DEFAULT_RUNNER_PATH,
    gate_path: Path = DEFAULT_GATE_PATH,
) -> dict[str, Any]:
    steps = [
        ("0.4.10.0", "runner_manifest", manifest_path, "metadata_chunking_diagnostic_runner_manifest"),
        ("0.4.10.1", "saved_report_runner", runner_path, "metadata_chunking_diagnostic_saved_report_runner"),
        ("0.4.10.2", "saved_report_runner_gate", gate_path, "metadata_chunking_diagnostic_saved_report_runner_gate"),
    ]
    rows, source_blockers = build_step_rows(steps)
    manifest = load_json(manifest_path)
    runner = load_json(runner_path)
    gate = load_json(gate_path)

    manifest_items = as_list(manifest.get("manifest_items"))
    diagnostic_rows = as_list(runner.get("diagnostic_rows"))
    runner_summary = as_dict(runner.get("summary"))
    gate_summary = as_dict(gate.get("summary"))
    gate_status = as_dict(gate.get("gate"))

    extra_blockers: list[str] = []
    if len(manifest_items) != 40:
        extra_blockers.append("manifest_item_count_not_40")
    if len(diagnostic_rows) != 40 or runner_summary.get("diagnostic_row_count") != 40:
        extra_blockers.append("diagnostic_row_count_not_40")
    if runner_summary.get("blocked_row_count") != 0 or gate_summary.get("source_blocked_row_count") != 0:
        extra_blockers.append("blocked_rows_present")
    if runner_summary.get("evidence_level_metadata_snapshot_read") is not False:
        extra_blockers.append("runner_snapshot_scope_drift")
    if gate_status.get("status") != "open_for_v0_4_10_series_closeout":
        extra_blockers.append("gate_not_open_for_closeout")

    manifest_keys = {(item.get("case_id"), item.get("check_group")) for item in manifest_items}
    runner_keys = {(item.get("case_id"), item.get("check_group")) for item in diagnostic_rows}
    if manifest_keys != runner_keys:
        extra_blockers.append("manifest_runner_matrix_mismatch")

    blockers = sorted_unique(source_blockers + extra_blockers)
    status = "v0_4_10_series_closed_for_saved_report_diagnostic" if not blockers else "blocked"
    completed_versions = [row["version"] for row in rows if row["closeout_status"] == "passed"]

    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_runner_series_closeout",
        "scope": "v0.4.10.x saved-report metadata/chunking diagnostic runner series closeout",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": GUARDRAILS,
        "closeout_gate": {
            "status": status,
            "series": "v0.4.10.x",
            "allowed_next_step": "v0.4.11.x evidence-level metadata snapshot read-only diagnostic design" if status != "blocked" else "blocked",
            "diagnostic_run": "saved_report_scope_only",
            "evidence_level_metadata_snapshot_read": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "completed_step_count": len(completed_versions),
            "expected_step_count": len(steps),
            "completed_versions": completed_versions,
            "expected_versions": [version for version, _, _, _ in steps],
            "manifest_item_count": len(manifest_items),
            "diagnostic_row_count": len(diagnostic_rows),
            "blocked_row_count": runner_summary.get("blocked_row_count"),
            "evidence_level_metadata_snapshot_read": False,
            "recommended_next_series": "v0.4.11.x evidence-level metadata snapshot read-only diagnostic design",
        },
        "series_rows": rows,
        "series_closeout_findings": [
            {
                "finding": "saved_report_runner_chain_completed",
                "status": "closed" if status != "blocked" else "blocked",
                "basis": "v0.4.10.0 manifest, v0.4.10.1 runner, and v0.4.10.2 runner gate are present in order.",
            },
            {
                "finding": "manifest_runner_matrix_aligned",
                "status": "closed" if "manifest_runner_matrix_mismatch" not in blockers else "blocked",
                "basis": "The manifest and runner both cover 8 sample cases x 5 check groups.",
            },
            {
                "finding": "evidence_level_metadata_not_inspected",
                "status": "closed",
                "basis": "The series remained saved-report-only and did not read evidence-level metadata snapshots.",
            },
            {
                "finding": "runtime_not_authorized",
                "status": "closed",
                "basis": "All guardrails keep retrieval, metadata, chunk, ingestion, rule, fixture, and eval mutations disabled.",
            },
        ],
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "series_reports_ready", "status": "passed" if not source_blockers else "failed", "blockers": source_blockers},
        {"name": "manifest_runner_matrix_complete", "status": "passed" if "manifest_runner_matrix_mismatch" not in blockers else "failed"},
        {"name": "forty_rows_no_blocked_rows", "status": "passed" if not {"manifest_item_count_not_40", "diagnostic_row_count_not_40", "blocked_rows_present"} & set(blockers) else "failed"},
        {"name": "evidence_level_snapshot_not_read", "status": "passed" if "runner_snapshot_scope_drift" not in blockers else "failed"},
        {"name": "runtime_changes_blocked", "status": "passed" if report["closeout_gate"]["implementation_allowed"] is False and report["closeout_gate"]["retrieval_logic_change_allowed"] is False else "failed"},
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
        "# v0.4.10.3 Metadata/Chunking Diagnostic Runner Series Closeout",
        "",
        "This closeout marks v0.4.10.x complete as a saved-report metadata/chunking diagnostic runner series. It does not inspect evidence-level metadata and does not authorize runtime changes.",
        "",
        "## Overview",
        "",
        f"- Closeout status: `{gate.get('status')}`",
        f"- Completed steps: {summary.get('completed_step_count')} / {summary.get('expected_step_count')}",
        f"- Manifest items: {summary.get('manifest_item_count')}",
        f"- Diagnostic rows: {summary.get('diagnostic_row_count')}",
        f"- Blocked rows: {summary.get('blocked_row_count')}",
        f"- Evidence-level metadata snapshot read: {summary.get('evidence_level_metadata_snapshot_read')}",
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
        "- v0.4.10.x validates saved-report runner readiness, not real evidence-level metadata quality.",
        "- The series did not read Qdrant, scan the knowledge base, run RAG, call an LLM, or run full evaluation.",
        "- It does not authorize metadata edits, chunk rewrites, ingestion changes, retrieval tuning, anchor additions, or eval case edits.",
        "- Future evidence-level metadata snapshot work needs a separately approved read-only design series.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--runner", type=Path, default=DEFAULT_RUNNER_PATH)
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.manifest, args.runner, args.gate)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking diagnostic runner series closeout built: "
        f"{summary.get('status')}, {summary.get('completed_step_count')} steps"
    )
    return 0 if report["closeout_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
