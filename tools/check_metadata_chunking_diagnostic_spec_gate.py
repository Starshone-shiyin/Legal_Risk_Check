"""Check the v0.4.9.6 metadata/chunking diagnostic specification gate.

The gate reads only the saved metadata/chunking diagnostic spec report and
verifies structure, field coverage, sample scope, prohibited actions, and
non-runtime boundaries. It does not run diagnostics or authorize code changes.
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


VERSION = "0.4.9.7"

DEFAULT_SPEC_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_spec_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_spec_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md")

EXPECTED_SPEC_ROW_ORDER = [
    "metadata_identity_fields",
    "chunk_boundary_fields",
    "article_locator_fields",
    "sample_case_mapping",
    "diagnostic_output_contract",
]

EXPECTED_REQUIRED_METADATA_FIELDS = [
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

EXPECTED_PROHIBITED_ACTIONS = [
    "merge_or_rewrite_chunks",
    "edit_metadata",
    "change_ingestion_pipeline",
    "tune_retrieval_parameters",
    "add_anchor_rules",
    "modify_eval_cases_or_fixtures",
]

GUARDRAILS = {
    "saved_reports_only": True,
    "gate_only": True,
    "diagnostic_run": "not_run",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "runtime_policy_implementation_allowed": False,
    "rerank_change_allowed": False,
    "prompt_change_allowed": False,
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
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


def spec_checks(spec: dict[str, Any]) -> list[dict[str, Any]]:
    gate = as_dict(spec.get("spec_gate"))
    summary = as_dict(spec.get("summary"))
    sample_scope = as_dict(spec.get("sample_case_scope"))
    required = as_dict(spec.get("required_metadata_field_coverage"))
    source_row = as_dict(spec.get("source_priority_row"))
    rows = as_list(spec.get("spec_rows"))
    row_order = [text(as_dict(row).get("check_group")) for row in rows]
    missing_required = [
        field for field in EXPECTED_REQUIRED_METADATA_FIELDS
        if field not in as_list(required.get("must_cover"))
        or field not in as_list(required.get("covered_by_spec"))
    ]
    row_runtime_violations = [
        text(as_dict(row).get("spec_row_id")) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if as_dict(row).get("diagnostic_only") is not True
        or as_dict(row).get("implementation_allowed") is not False
        or as_dict(row).get("code_patch_authorized") is not False
        or as_dict(row).get("retrieval_logic_change_allowed") is not False
    ]
    row_content_violations = [
        text(as_dict(row).get("spec_row_id")) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if not text(as_dict(row).get("spec_row_id"))
        or not text(as_dict(row).get("check_group"))
        or not as_list(as_dict(row).get("required_fields"))
        or not as_list(as_dict(row).get("failure_signals"))
        or len(as_list(as_dict(row).get("sample_case_ids"))) < 8
        or not as_list(as_dict(row).get("evidence_signals"))
        or text(as_dict(row).get("status")) != "ready_for_future_diagnostic_runner"
    ]
    forbidden_paths = find_key_paths(spec, FORBIDDEN_KEYS)
    readable_paths = readability_paths(spec)
    return [
        {
            "name": "spec_schema",
            "status": "passed" if spec.get("schema_kind") == "metadata_chunking_diagnostic_spec" else "failed",
            "expected": "metadata_chunking_diagnostic_spec",
            "actual": spec.get("schema_kind"),
        },
        {
            "name": "spec_version",
            "status": "passed" if spec.get("version") == "0.4.9.6" else "failed",
            "expected": "0.4.9.6",
            "actual": spec.get("version"),
        },
        {
            "name": "spec_gate_ready",
            "status": "passed" if gate.get("status") == "ready_for_future_metadata_chunking_diagnostic_runner" else "failed",
            "actual": gate.get("status"),
        },
        {
            "name": "spec_gate_has_no_blockers",
            "status": "passed" if as_list(gate.get("blockers")) == [] else "failed",
            "blockers": as_list(gate.get("blockers")),
        },
        {
            "name": "allowed_next_step_is_runner_design",
            "status": "passed" if gate.get("allowed_next_step") == "metadata_chunking_diagnostic_runner_design" else "failed",
            "actual": gate.get("allowed_next_step"),
        },
        {
            "name": "spec_row_count_and_order",
            "status": "passed" if len(rows) == 5 and row_order == EXPECTED_SPEC_ROW_ORDER else "failed",
            "expected": EXPECTED_SPEC_ROW_ORDER,
            "actual": row_order,
            "row_count": len(rows),
        },
        {
            "name": "required_metadata_fields_covered",
            "status": "passed" if not missing_required else "failed",
            "missing_fields": missing_required,
        },
        {
            "name": "sample_scope_stable",
            "status": "passed" if len(as_list(sample_scope.get("case_ids"))) >= 8 and sample_scope.get("scope_limit") == "saved_report_samples_only" else "failed",
            "sample_case_count": len(as_list(sample_scope.get("case_ids"))),
            "scope_limit": sample_scope.get("scope_limit"),
        },
        {
            "name": "source_priority_row_stable",
            "status": "passed" if source_row.get("route_id") == "metadata_chunking_diagnostic_report" and source_row.get("severity") == "high" and int(source_row.get("impacted_case_count") or 0) >= 1 else "failed",
            "route_id": source_row.get("route_id"),
            "severity": source_row.get("severity"),
            "impacted_case_count": source_row.get("impacted_case_count"),
        },
        {
            "name": "prohibited_actions_stable",
            "status": "passed" if spec.get("prohibited_actions") == EXPECTED_PROHIBITED_ACTIONS else "failed",
            "expected": EXPECTED_PROHIBITED_ACTIONS,
            "actual": spec.get("prohibited_actions"),
        },
        {
            "name": "row_content_complete",
            "status": "passed" if not row_content_violations else "failed",
            "violations": row_content_violations,
        },
        {
            "name": "row_runtime_changes_blocked",
            "status": "passed" if not row_runtime_violations else "failed",
            "violations": row_runtime_violations,
        },
        {
            "name": "gate_runtime_changes_blocked",
            "status": "passed" if gate.get("implementation_allowed") is False and gate.get("code_patch_authorized") is False and gate.get("retrieval_logic_change_allowed") is False else "failed",
            "implementation_allowed": gate.get("implementation_allowed"),
            "code_patch_authorized": gate.get("code_patch_authorized"),
            "retrieval_logic_change_allowed": gate.get("retrieval_logic_change_allowed"),
        },
        {
            "name": "diagnostic_not_run",
            "status": "passed" if gate.get("diagnostic_not_run") is True and summary.get("diagnostic_not_run") is True else "failed",
            "gate_diagnostic_not_run": gate.get("diagnostic_not_run"),
            "summary_diagnostic_not_run": summary.get("diagnostic_not_run"),
        },
        {
            "name": "forbidden_keys_absent",
            "status": "passed" if not forbidden_paths else "failed",
            "forbidden_paths": forbidden_paths,
        },
        {
            "name": "text_readability_gate",
            "status": "passed" if not readable_paths else "failed",
            "mojibake_like_paths": readable_paths,
        },
    ]


def build_report(spec_report_path: Path = DEFAULT_SPEC_REPORT_PATH) -> dict[str, Any]:
    spec = load_json(spec_report_path)
    checks = spec_checks(spec)
    failed = [check for check in checks if check["status"] != "passed"]
    status = "open_for_metadata_chunking_diagnostic_runner_design" if not failed else "blocked"
    rows = as_list(spec.get("spec_rows"))
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_spec_gate",
        "scope": "saved-report metadata/chunking diagnostic spec gate only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "metadata_chunking_diagnostic_spec_report": {
                "path": str(spec_report_path),
                "present": spec_report_path.exists(),
                "version": spec.get("version"),
                "schema_kind": spec.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "gate": {
            "status": status,
            "allowed_next_step": "metadata_chunking_diagnostic_runner_design" if not failed else "blocked",
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": [check["name"] for check in failed],
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "spec_row_count": len(rows),
            "spec_row_order": [text(as_dict(row).get("check_group")) for row in rows],
            "source_sample_case_count": len(as_list(as_dict(spec.get("sample_case_scope")).get("case_ids"))),
            "source_required_metadata_fields": as_list(as_dict(spec.get("required_metadata_field_coverage")).get("must_cover")),
            "source_prohibited_actions": as_list(spec.get("prohibited_actions")),
            "implementation_allowed": False,
            "diagnostic_run": "not_run",
            "next_version_recommendation": "v0.4.9.8 metadata chunking diagnostic runner design",
        },
        "checks": checks,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.7 Metadata/Chunking Diagnostic Spec Gate",
        "",
        "This gate checks the v0.4.9.6 metadata/chunking diagnostic specification for structure, field coverage, sample scope, and non-runtime boundaries.",
        "",
        "## Overview",
        "",
        f"- Gate status: `{gate.get('status')}`",
        f"- Checks: {summary.get('check_count')}",
        f"- Failed checks: {summary.get('failed_check_count')}",
        f"- Spec rows: {summary.get('spec_row_count')}",
        f"- Sample cases: {summary.get('source_sample_case_count')}",
        f"- Next allowed step: `{gate.get('allowed_next_step')}`",
        f"- Diagnostic run: `{gate.get('diagnostic_run')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        "",
        "## Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in as_list(report.get("checks")):
        lines.append(f"| `{check.get('name')}` | `{check.get('status')}` |")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- Passing this gate only allows metadata/chunking diagnostic runner design.",
        "- It does not run diagnostics, merge chunks, edit metadata, change ingestion, tune retrieval, add anchors, or modify eval cases.",
        "- It does not call backend/vector/language-model services and does not run full evaluation.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-report", type=Path, default=DEFAULT_SPEC_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.spec_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking diagnostic spec gate checked: "
        f"{summary.get('status')}, {summary.get('failed_check_count')} failed"
    )
    return 0 if report["gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
