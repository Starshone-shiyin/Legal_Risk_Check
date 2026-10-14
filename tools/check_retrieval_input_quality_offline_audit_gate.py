"""Check the v0.4.9.2 retrieval input quality offline audit gate.

The gate reads only the saved offline audit report, verifies structure and
non-runtime boundaries, and emits a release-quality gate report. It does not
run evals or authorize retrieval, rerank, prompt, rule, fixture, or case edits.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.9.3"

DEFAULT_OFFLINE_AUDIT_REPORT_PATH = legacy_report_path("retrieval_input_quality_offline_audit_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("retrieval_input_quality_offline_audit_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/retrieval_input_quality_offline_audit_gate_v0.4.9.3.md")

EXPECTED_BUCKET_ORDER = [
    "source_article_identity_quality",
    "metadata_chunking_quality",
    "query_lexical_coverage_quality",
    "legal_domain_boundary_quality",
    "anchor_dependency_quality",
]

EXPECTED_ROUTES = [
    "anchor_dependency_reduction_diagnostic_report",
    "legal_domain_boundary_diagnostic_report",
    "metadata_chunking_diagnostic_report",
    "query_lexical_coverage_diagnostic_report",
    "source_article_identity_diagnostic_report",
]

REQUIRED_ROW_FIELDS = [
    "audit_result_id",
    "source_audit_spec_id",
    "bucket_id",
    "priority",
    "audit_status",
    "impacted_case_count",
    "sample_case_ids",
    "evidence_signals",
    "severity",
    "audit_findings",
    "recommended_next_route",
    "runtime_change_allowed",
    "implementation_allowed",
    "code_patch_authorized",
    "retrieval_logic_change_allowed",
]

GUARDRAILS = {
    "saved_reports_only": True,
    "gate_only": True,
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


def counter_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: str(item[0])))


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


def audit_checks(audit: dict[str, Any]) -> list[dict[str, Any]]:
    gate = as_dict(audit.get("audit_gate"))
    summary = as_dict(audit.get("summary"))
    rows = as_list(audit.get("offline_audit_rows"))
    bucket_ids = [row.get("bucket_id") for row in rows]
    route_ids = sorted_unique([text(row.get("recommended_next_route")) for row in rows])
    severity_counts = Counter(text(row.get("severity")) for row in rows)
    missing_row_fields = {
        text(row.get("audit_result_id")) or f"row_{index}": [
            field for field in REQUIRED_ROW_FIELDS if field not in row
        ]
        for index, row in enumerate(rows, start=1)
    }
    missing_row_fields = {key: value for key, value in missing_row_fields.items() if value}
    row_runtime_violations = [
        text(row.get("audit_result_id")) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if row.get("runtime_change_allowed") is not False
        or row.get("implementation_allowed") is not False
        or row.get("code_patch_authorized") is not False
        or row.get("retrieval_logic_change_allowed") is not False
    ]
    row_content_violations = [
        text(row.get("audit_result_id")) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if int(row.get("impacted_case_count") or 0) <= 0
        or not as_list(row.get("sample_case_ids"))
        or not as_list(row.get("evidence_signals"))
        or not as_list(row.get("audit_findings"))
        or text(row.get("severity")) not in {"high", "medium"}
        or not text(row.get("recommended_next_route"))
    ]
    forbidden_paths = find_key_paths(audit, FORBIDDEN_KEYS)
    readable_paths = readability_paths(audit)
    return [
        {
            "name": "offline_audit_schema",
            "status": "passed" if audit.get("schema_kind") == "retrieval_input_quality_offline_audit" else "failed",
            "expected": "retrieval_input_quality_offline_audit",
            "actual": audit.get("schema_kind"),
        },
        {
            "name": "offline_audit_version",
            "status": "passed" if audit.get("version") == "0.4.9.2" else "failed",
            "expected": "0.4.9.2",
            "actual": audit.get("version"),
        },
        {
            "name": "offline_audit_completed",
            "status": "passed" if gate.get("status") == "completed_saved_report_offline_audit" else "failed",
            "actual": gate.get("status"),
        },
        {
            "name": "offline_audit_has_no_blockers",
            "status": "passed" if as_list(gate.get("blockers")) == [] else "failed",
            "blockers": as_list(gate.get("blockers")),
        },
        {
            "name": "audit_row_count",
            "status": "passed" if len(rows) == 5 and summary.get("audit_row_count") == 5 else "failed",
            "row_count": len(rows),
            "summary_row_count": summary.get("audit_row_count"),
        },
        {
            "name": "bucket_order",
            "status": "passed" if bucket_ids == EXPECTED_BUCKET_ORDER and summary.get("bucket_ids") == EXPECTED_BUCKET_ORDER else "failed",
            "expected": EXPECTED_BUCKET_ORDER,
            "actual": bucket_ids,
            "summary_bucket_ids": summary.get("bucket_ids"),
        },
        {
            "name": "required_row_fields",
            "status": "passed" if not missing_row_fields else "failed",
            "missing_row_fields": missing_row_fields,
        },
        {
            "name": "row_content_complete",
            "status": "passed" if not row_content_violations else "failed",
            "violations": row_content_violations,
        },
        {
            "name": "severity_summary_expected",
            "status": "passed" if severity_counts == Counter({"high": 3, "medium": 2}) and summary.get("high_severity_count") == 3 else "failed",
            "expected": {"high": 3, "medium": 2},
            "actual": counter_dict(severity_counts),
            "summary_high_severity_count": summary.get("high_severity_count"),
        },
        {
            "name": "recommended_routes_complete",
            "status": "passed" if route_ids == EXPECTED_ROUTES else "failed",
            "expected": EXPECTED_ROUTES,
            "actual": route_ids,
        },
        {
            "name": "summary_case_signal_floor",
            "status": "passed" if int(summary.get("total_impacted_signal_count") or 0) >= 100 and int(summary.get("unique_sample_case_count") or 0) >= 8 else "failed",
            "total_impacted_signal_count": summary.get("total_impacted_signal_count"),
            "unique_sample_case_count": summary.get("unique_sample_case_count"),
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


def build_report(offline_audit_report_path: Path = DEFAULT_OFFLINE_AUDIT_REPORT_PATH) -> dict[str, Any]:
    audit = load_json(offline_audit_report_path)
    checks = audit_checks(audit)
    failed = [check for check in checks if check["status"] != "passed"]
    status = "open_for_retrieval_input_quality_diagnostic_planning" if not failed else "blocked"
    rows = as_list(audit.get("offline_audit_rows"))
    bucket_ids = [text(row.get("bucket_id")) for row in rows]
    severity_summary = Counter(text(row.get("severity")) for row in rows)
    route_summary = Counter(text(row.get("recommended_next_route")) for row in rows)
    report = {
        "version": VERSION,
        "schema_kind": "retrieval_input_quality_offline_audit_gate",
        "scope": "saved-report retrieval input quality offline audit gate only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "offline_audit_report": {
                "path": str(offline_audit_report_path),
                "present": offline_audit_report_path.exists(),
                "version": audit.get("version"),
                "schema_kind": audit.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "gate": {
            "status": status,
            "allowed_next_step": "retrieval_input_quality_diagnostic_planning" if not failed else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": [check["name"] for check in failed],
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "audit_row_count": len(rows),
            "bucket_ids": bucket_ids,
            "severity_summary": counter_dict(severity_summary),
            "recommended_route_summary": counter_dict(route_summary),
            "source_total_impacted_signal_count": as_dict(audit.get("summary")).get("total_impacted_signal_count"),
            "source_unique_sample_case_count": as_dict(audit.get("summary")).get("unique_sample_case_count"),
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.9.4 retrieval input quality diagnostic prioritization",
        },
        "checks": checks,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.3 Retrieval Input Quality Offline Audit Gate",
        "",
        "This gate checks the v0.4.9.2 offline audit report for release-quality structure and non-runtime boundaries.",
        "",
        "## Overview",
        "",
        f"- Gate status: `{gate.get('status')}`",
        f"- Checks: {summary.get('check_count')}",
        f"- Failed checks: {summary.get('failed_check_count')}",
        f"- Audit rows: {summary.get('audit_row_count')}",
        f"- Severity summary: {summary.get('severity_summary')}",
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
        "- Passing this gate only allows retrieval input quality diagnostic planning.",
        "- It does not authorize retrieval, rerank, prompt, anchor, risk rule, fixture, scenario registry, or eval-case changes.",
        "- It does not run full evaluation or call backend/vector/language-model services.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-audit-report", type=Path, default=DEFAULT_OFFLINE_AUDIT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.offline_audit_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Retrieval input quality offline audit gate checked: "
        f"{summary.get('status')}, {summary.get('failed_check_count')} failed"
    )
    return 0 if report["gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
