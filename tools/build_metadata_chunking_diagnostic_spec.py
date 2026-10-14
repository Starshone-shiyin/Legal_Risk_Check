"""Build the v0.4.9.6 metadata/chunking diagnostic specification.

The spec consumes only v0.4.9.5 and v0.4.9.4 saved planning reports. It
defines a future diagnostic contract; it does not run diagnostics or authorize
metadata, chunking, ingestion, retrieval, rerank, prompt, rule, or eval changes.
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


VERSION = "0.4.9.6"

DEFAULT_PRIORITIZATION_GATE_REPORT_PATH = legacy_report_path("retrieval_input_quality_diagnostic_prioritization_gate_report.json")
DEFAULT_PRIORITIZATION_REPORT_PATH = legacy_report_path("retrieval_input_quality_diagnostic_prioritization_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_spec_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_spec_v0.4.9.6.md")

EXPECTED_TOP_ROUTE = "metadata_chunking_diagnostic_report"
EXPECTED_ARTIFACT = "metadata_chunking_diagnostic_spec"
EXPECTED_ALLOWED_NEXT_STEP = "metadata_chunking_diagnostic_spec"

REQUIRED_METADATA_FIELDS = [
    "chunk_id",
    "parent_article_id",
    "article_no",
    "section_no",
    "chunk_index",
    "chunk_count",
    "block_type",
    "citation",
    "law_name",
    "source",
]

PROHIBITED_ACTIONS = [
    "merge_or_rewrite_chunks",
    "edit_metadata",
    "change_ingestion_pipeline",
    "tune_retrieval_parameters",
    "add_anchor_rules",
    "modify_eval_cases_or_fixtures",
]

GUARDRAILS = {
    "saved_reports_only": True,
    "spec_only": True,
    "diagnostic_run": "not_run",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "metadata_mutation": "disallowed",
    "chunk_mutation": "disallowed",
    "ingestion_mutation": "disallowed",
    "runtime_policy_implementation_allowed": False,
    "rerank_change_allowed": False,
    "prompt_change_allowed": False,
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "main_flow_mutation": "disallowed",
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


def text(value: Any) -> str:
    return value if isinstance(value, str) else ""


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


def metadata_priority_row(prioritization_report: dict[str, Any]) -> dict[str, Any]:
    for row in as_list(prioritization_report.get("diagnostic_priority_rows")):
        if as_dict(row).get("route_id") == EXPECTED_TOP_ROUTE:
            return as_dict(row)
    return {}


def source_blockers(gate_report: dict[str, Any], prioritization_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(gate_report.get("gate"))
    gate_summary = as_dict(gate_report.get("summary"))
    prioritization_gate = as_dict(prioritization_report.get("prioritization_gate"))
    prioritization_summary = as_dict(prioritization_report.get("summary"))
    top_row = metadata_priority_row(prioritization_report)
    if gate_report.get("version") != "0.4.9.5":
        blockers.append("prioritization_gate_version_mismatch")
    if gate_report.get("schema_kind") != "retrieval_input_quality_diagnostic_prioritization_gate":
        blockers.append("prioritization_gate_schema_mismatch")
    if gate.get("status") != "open_for_metadata_chunking_diagnostic_spec":
        blockers.append("prioritization_gate_not_open_for_metadata_chunking_spec")
    if gate.get("allowed_next_step") != EXPECTED_ALLOWED_NEXT_STEP:
        blockers.append("prioritization_gate_next_step_drift")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("prioritization_gate_failed_checks_present")
    if as_list(gate.get("blockers")):
        blockers.append("prioritization_gate_has_blockers")
    if gate.get("implementation_allowed") is not False or gate.get("retrieval_logic_change_allowed") is not False:
        blockers.append("prioritization_gate_runtime_boundary_drift")
    if prioritization_report.get("version") != "0.4.9.4":
        blockers.append("prioritization_version_mismatch")
    if prioritization_report.get("schema_kind") != "retrieval_input_quality_diagnostic_prioritization":
        blockers.append("prioritization_schema_mismatch")
    if prioritization_gate.get("status") != "ready_for_diagnostic_spec_design":
        blockers.append("prioritization_not_ready_for_spec_design")
    if prioritization_summary.get("top_route") != EXPECTED_TOP_ROUTE:
        blockers.append("metadata_chunking_not_top_route")
    if not top_row:
        blockers.append("metadata_chunking_priority_row_missing")
    else:
        if top_row.get("recommended_artifact") != EXPECTED_ARTIFACT:
            blockers.append("metadata_chunking_recommended_artifact_drift")
        if top_row.get("severity") != "high":
            blockers.append("metadata_chunking_severity_not_high")
        if int(top_row.get("impacted_case_count") or 0) < 1:
            blockers.append("metadata_chunking_impacted_case_count_empty")
        if not as_list(top_row.get("sample_case_ids")):
            blockers.append("metadata_chunking_sample_cases_missing")
        if top_row.get("implementation_allowed") is not False or top_row.get("retrieval_logic_change_allowed") is not False:
            blockers.append("metadata_chunking_row_runtime_boundary_drift")
    for source_name, payload in {"prioritization_gate": gate_report, "prioritization": prioritization_report}.items():
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{source_name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def spec_rows(top_row: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    sample_cases = as_list(top_row.get("sample_case_ids"))[:8]
    evidence_signals = as_list(top_row.get("evidence_signals"))
    rows = [
        {
            "spec_row_id": "MCD-SPEC-001",
            "check_group": "metadata_identity_fields",
            "required_fields": ["chunk_id", "parent_article_id", "law_name", "source", "article_no_or_section_no", "citation"],
            "success_condition": "Each sampled expected evidence item can be tied to a stable chunk, parent article or section, legal source, and citation identity.",
            "failure_signals": ["missing_chunk_id", "missing_parent_article_id", "law_name_source_mismatch", "citation_identity_missing"],
        },
        {
            "spec_row_id": "MCD-SPEC-002",
            "check_group": "chunk_boundary_fields",
            "required_fields": ["chunk_index", "chunk_count", "block_type", "paragraph_no", "item_no"],
            "success_condition": "Each sampled evidence unit exposes enough boundary fields to review whether it represents a coherent article, section, paragraph, or item.",
            "failure_signals": ["missing_chunk_index", "missing_chunk_count", "ambiguous_block_type", "boundary_locator_missing"],
        },
        {
            "spec_row_id": "MCD-SPEC-003",
            "check_group": "article_locator_fields",
            "required_fields": ["article_no", "section_no", "section_title", "parent_article_id", "citation"],
            "success_condition": "Article and section locators are sufficient for article-level filterability and citation-level review.",
            "failure_signals": ["missing_article_and_section_locator", "parent_article_unlinked", "section_title_missing_when_section_no_present"],
        },
        {
            "spec_row_id": "MCD-SPEC-004",
            "check_group": "sample_case_mapping",
            "required_fields": ["case_id", "expected_evidence_id", "source_audit_result_id", "evidence_signals"],
            "success_condition": "Each sampled case maps back to the v0.4.9.4 metadata/chunking priority row without expanding scope.",
            "failure_signals": ["case_mapping_missing", "expected_evidence_identity_missing", "source_audit_result_unlinked"],
        },
        {
            "spec_row_id": "MCD-SPEC-005",
            "check_group": "diagnostic_output_contract",
            "required_fields": [
                "case_id",
                "metadata_field_status",
                "chunk_boundary_status",
                "parent_article_link_status",
                "citation_identity_status",
                "diagnostic_followup",
            ],
            "success_condition": "Future diagnostic output can separate metadata completeness, chunk boundary, parent linkage, citation identity, and follow-up classification.",
            "failure_signals": ["output_status_missing", "diagnostic_followup_missing", "field_groups_collapsed"],
        },
    ]
    for row in rows:
        row.update({
            "sample_case_ids": sample_cases,
            "evidence_signals": evidence_signals,
            "diagnostic_only": True,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "status": "ready_for_future_diagnostic_runner" if ready else "blocked",
        })
    return rows


def build_report(
    prioritization_gate_report_path: Path = DEFAULT_PRIORITIZATION_GATE_REPORT_PATH,
    prioritization_report_path: Path = DEFAULT_PRIORITIZATION_REPORT_PATH,
) -> dict[str, Any]:
    gate_report = load_json(prioritization_gate_report_path)
    prioritization_report = load_json(prioritization_report_path)
    blockers = source_blockers(gate_report, prioritization_report)
    ready = not blockers
    top_row = metadata_priority_row(prioritization_report)
    rows = spec_rows(top_row, ready)
    sample_cases = as_list(top_row.get("sample_case_ids"))[:8]
    all_required_fields = sorted_unique([
        field
        for row in rows
        for field in as_list(row.get("required_fields"))
    ])
    status = "ready_for_future_metadata_chunking_diagnostic_runner" if ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_spec",
        "scope": "saved-report metadata/chunking diagnostic specification only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "prioritization_gate_report": {
                "path": str(prioritization_gate_report_path),
                "present": prioritization_gate_report_path.exists(),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
            },
            "prioritization_report": {
                "path": str(prioritization_report_path),
                "present": prioritization_report_path.exists(),
                "version": prioritization_report.get("version"),
                "schema_kind": prioritization_report.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "sample_case_scope": {
            "source": "metadata_chunking_priority_row",
            "sample_case_count": len(sample_cases),
            "case_ids": sample_cases,
            "scope_limit": "saved_report_samples_only",
            "expansion_requires_future_approval": True,
        },
        "source_priority_row": {
            "route_id": top_row.get("route_id"),
            "source_audit_result_id": top_row.get("source_audit_result_id"),
            "bucket_id": top_row.get("bucket_id"),
            "severity": top_row.get("severity"),
            "impacted_case_count": top_row.get("impacted_case_count"),
            "diagnostic_focus": top_row.get("diagnostic_focus"),
            "evidence_signals": as_list(top_row.get("evidence_signals")),
        },
        "required_metadata_field_coverage": {
            "must_cover": REQUIRED_METADATA_FIELDS,
            "covered_by_spec": all_required_fields,
        },
        "prohibited_actions": PROHIBITED_ACTIONS,
        "spec_gate": {
            "status": status,
            "allowed_next_step": "metadata_chunking_diagnostic_runner_design" if ready else "blocked",
            "diagnostic_not_run": True,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "check_group_count": len(rows),
            "required_field_count": len(all_required_fields),
            "sample_case_count": len(sample_cases),
            "impacted_case_count": top_row.get("impacted_case_count"),
            "top_route": top_row.get("route_id"),
            "diagnostic_not_run": True,
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.9.7 metadata chunking diagnostic spec gate",
        },
        "spec_rows": rows,
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    missing_required_fields = [field for field in REQUIRED_METADATA_FIELDS if field not in all_required_fields]
    report["assertions"] = [
        {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "five_spec_rows_present", "status": "passed" if len(rows) == 5 else "failed", "row_count": len(rows)},
        {"name": "required_metadata_fields_covered", "status": "passed" if not missing_required_fields else "failed", "missing_fields": missing_required_fields},
        {"name": "sample_scope_present", "status": "passed" if len(sample_cases) >= 8 else "failed", "sample_case_count": len(sample_cases)},
        {"name": "prohibited_actions_present", "status": "passed" if PROHIBITED_ACTIONS == report["prohibited_actions"] else "failed"},
        {"name": "spec_is_non_runtime", "status": "passed" if all(row.get("implementation_allowed") is False and row.get("retrieval_logic_change_allowed") is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_paths": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    assertion_failed = [item["name"] for item in report["assertions"] if item["status"] != "passed"]
    if assertion_failed:
        report["spec_gate"]["status"] = "blocked"
        report["spec_gate"]["allowed_next_step"] = "blocked"
        report["spec_gate"]["blockers"] = sorted_unique(blockers + assertion_failed)
        report["summary"]["status"] = "blocked"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("spec_gate"))
    summary = as_dict(report.get("summary"))
    sample_scope = as_dict(report.get("sample_case_scope"))
    lines = [
        "# v0.4.9.6 Metadata/Chunking Diagnostic Spec",
        "",
        "This specification defines the first metadata/chunking diagnostic contract from saved planning reports only. It does not run a diagnostic or authorize changes.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Next allowed step: `{gate.get('allowed_next_step')}`",
        f"- Check groups: {summary.get('check_group_count')}",
        f"- Required fields: {summary.get('required_field_count')}",
        f"- Sample cases: {sample_scope.get('sample_case_count')}",
        f"- Impacted case signal: {summary.get('impacted_case_count')}",
        f"- Diagnostic not run: {summary.get('diagnostic_not_run')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Check Groups",
        "",
        "| Spec row | Check group | Required fields |",
        "|---|---|---|",
    ]
    for row in as_list(report.get("spec_rows")):
        fields = ", ".join(as_list(row.get("required_fields")))
        lines.append(f"| `{row.get('spec_row_id')}` | `{row.get('check_group')}` | {fields} |")
    lines.extend([
        "",
        "## Sample Case Scope",
        "",
    ])
    for case_id in as_list(sample_scope.get("case_ids")):
        lines.append(f"- `{case_id}`")
    lines.extend([
        "",
        "## Prohibited Actions",
        "",
    ])
    for action in as_list(report.get("prohibited_actions")):
        lines.append(f"- `{action}`")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is a metadata/chunking diagnostic specification only.",
        "- It does not merge chunks, edit metadata, change ingestion, tune retrieval parameters, add anchors, or modify eval cases/fixtures.",
        "- It does not call backend/vector/language-model services and does not run full evaluation.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prioritization-gate-report", type=Path, default=DEFAULT_PRIORITIZATION_GATE_REPORT_PATH)
    parser.add_argument("--prioritization-report", type=Path, default=DEFAULT_PRIORITIZATION_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.prioritization_gate_report, args.prioritization_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking diagnostic spec built: "
        f"{summary.get('status')}, {summary.get('check_group_count')} check groups"
    )
    return 0 if report["spec_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
