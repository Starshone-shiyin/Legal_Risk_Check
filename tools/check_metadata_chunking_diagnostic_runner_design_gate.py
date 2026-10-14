"""Check the v0.4.9.8 metadata/chunking diagnostic runner design gate.

The gate reads only the saved runner design report and verifies the design
contract, failure buckets, prohibited actions, and non-runtime boundaries. It
does not run diagnostics, read Qdrant, scan the knowledge base, or authorize
code/data fixes.
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
from tools.build_metadata_chunking_diagnostic_runner_design import (
    EXPECTED_DESIGN_ROW_ORDER,
    FAILURE_BUCKETS,
    OUTPUT_FIELD_CONTRACT,
    PROHIBITED_ACTIONS,
)


VERSION = "0.4.9.9"

DEFAULT_RUNNER_DESIGN_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md")

EXPECTED_SOURCE_REPORTS = [
    "tests/metadata_chunking_diagnostic_spec_gate_report.json",
    "tests/metadata_chunking_diagnostic_spec_report.json",
]

GUARDRAILS = {
    "saved_reports_only": True,
    "gate_only": True,
    "diagnostic_run": "not_run",
    "qdrant_access": "disallowed",
    "knowledge_base_fulltext_scan": "disallowed",
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

SOURCE_DESIGN_GUARDRAILS = {
    key: value for key, value in GUARDRAILS.items()
    if key != "gate_only"
}
SOURCE_DESIGN_GUARDRAILS["runner_design_only"] = True

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


def design_gate_checks(design: dict[str, Any]) -> list[dict[str, Any]]:
    gate = as_dict(design.get("runner_design_gate"))
    summary = as_dict(design.get("summary"))
    guardrails = as_dict(design.get("guardrails"))
    input_contract = as_dict(design.get("runner_input_contract"))
    output_contract = as_dict(design.get("runner_output_contract"))
    rows = as_list(design.get("design_rows"))
    row_order = [text(as_dict(row).get("check_group")) for row in rows]
    row_status_violations = [
        text(as_dict(row).get("runner_design_id")) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if as_dict(row).get("status") != "ready_for_future_read_only_runner"
        or as_dict(row).get("implementation_allowed") is not False
        or as_dict(row).get("code_patch_authorized") is not False
        or as_dict(row).get("retrieval_logic_change_allowed") is not False
        or as_dict(row).get("metadata_mutation") != "disallowed"
        or as_dict(row).get("chunk_mutation") != "disallowed"
    ]
    row_output_violations = [
        text(as_dict(row).get("runner_design_id")) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if as_dict(row).get("output_contract") != OUTPUT_FIELD_CONTRACT
        or not as_list(as_dict(row).get("failure_buckets"))
        or any(bucket not in FAILURE_BUCKETS for bucket in as_list(as_dict(row).get("failure_buckets")))
    ]
    guardrail_errors = [
        name for name, expected in SOURCE_DESIGN_GUARDRAILS.items()
        if guardrails.get(name) != expected
    ]
    forbidden_paths = find_key_paths(design, FORBIDDEN_KEYS)
    readable_paths = readability_paths(design)
    return [
        {
            "name": "runner_design_schema",
            "status": "passed" if design.get("schema_kind") == "metadata_chunking_diagnostic_runner_design" else "failed",
            "expected": "metadata_chunking_diagnostic_runner_design",
            "actual": design.get("schema_kind"),
        },
        {
            "name": "runner_design_version",
            "status": "passed" if design.get("version") == "0.4.9.8" else "failed",
            "expected": "0.4.9.8",
            "actual": design.get("version"),
        },
        {
            "name": "runner_design_ready",
            "status": "passed" if gate.get("status") == "ready_for_metadata_chunking_diagnostic_runner_gate" else "failed",
            "actual": gate.get("status"),
        },
        {
            "name": "runner_design_has_no_blockers",
            "status": "passed" if as_list(gate.get("blockers")) == [] else "failed",
            "blockers": as_list(gate.get("blockers")),
        },
        {
            "name": "allowed_next_step_is_design_gate",
            "status": "passed" if gate.get("allowed_next_step") == "metadata_chunking_diagnostic_runner_design_gate" else "failed",
            "actual": gate.get("allowed_next_step"),
        },
        {
            "name": "source_reports_stable",
            "status": "passed" if input_contract.get("saved_reports") == EXPECTED_SOURCE_REPORTS else "failed",
            "expected": EXPECTED_SOURCE_REPORTS,
            "actual": input_contract.get("saved_reports"),
        },
        {
            "name": "design_row_count_and_order",
            "status": "passed" if len(rows) == 5 and row_order == EXPECTED_DESIGN_ROW_ORDER else "failed",
            "expected": EXPECTED_DESIGN_ROW_ORDER,
            "actual": row_order,
            "row_count": len(rows),
        },
        {
            "name": "output_contract_stable",
            "status": "passed" if output_contract.get("required_fields") == OUTPUT_FIELD_CONTRACT else "failed",
            "expected": OUTPUT_FIELD_CONTRACT,
            "actual": output_contract.get("required_fields"),
        },
        {
            "name": "failure_buckets_stable",
            "status": "passed" if output_contract.get("failure_buckets") == FAILURE_BUCKETS else "failed",
            "expected": FAILURE_BUCKETS,
            "actual": output_contract.get("failure_buckets"),
        },
        {
            "name": "prohibited_actions_stable",
            "status": "passed" if design.get("prohibited_actions") == PROHIBITED_ACTIONS else "failed",
            "expected": PROHIBITED_ACTIONS,
            "actual": design.get("prohibited_actions"),
        },
        {
            "name": "row_boundaries_stable",
            "status": "passed" if not row_status_violations else "failed",
            "violations": row_status_violations,
        },
        {
            "name": "row_output_contracts_stable",
            "status": "passed" if not row_output_violations else "failed",
            "violations": row_output_violations,
        },
        {
            "name": "guardrails_stable",
            "status": "passed" if not guardrail_errors else "failed",
            "mismatches": guardrail_errors,
        },
        {
            "name": "diagnostic_not_run",
            "status": "passed" if gate.get("diagnostic_run") == "not_run" and summary.get("diagnostic_run") == "not_run" else "failed",
            "gate_diagnostic_run": gate.get("diagnostic_run"),
            "summary_diagnostic_run": summary.get("diagnostic_run"),
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


def build_report(runner_design_report_path: Path = DEFAULT_RUNNER_DESIGN_REPORT_PATH) -> dict[str, Any]:
    design = load_json(runner_design_report_path)
    checks = design_gate_checks(design)
    failed = [check for check in checks if check["status"] != "passed"]
    status = "open_for_metadata_chunking_diagnostic_dry_run_contract" if not failed else "blocked"
    rows = as_list(design.get("design_rows"))
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_runner_design_gate",
        "scope": "saved-report metadata/chunking diagnostic runner design gate only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "metadata_chunking_diagnostic_runner_design_report": {
                "path": str(runner_design_report_path),
                "present": runner_design_report_path.exists(),
                "version": design.get("version"),
                "schema_kind": design.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "gate": {
            "status": status,
            "allowed_next_step": "metadata_chunking_diagnostic_dry_run_contract" if not failed else "blocked",
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
            "design_row_count": len(rows),
            "design_row_order": [text(as_dict(row).get("check_group")) for row in rows],
            "output_field_count": len(as_list(as_dict(design.get("runner_output_contract")).get("required_fields"))),
            "failure_bucket_count": len(as_list(as_dict(design.get("runner_output_contract")).get("failure_buckets"))),
            "source_prohibited_actions": as_list(design.get("prohibited_actions")),
            "implementation_allowed": False,
            "diagnostic_run": "not_run",
            "next_version_recommendation": "v0.4.9.10 metadata chunking diagnostic dry-run contract",
        },
        "checks": checks,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.9 Metadata/Chunking Diagnostic Runner Design Gate",
        "",
        "This gate checks the v0.4.9.8 runner design report for contract stability and non-runtime boundaries.",
        "",
        "## Overview",
        "",
        f"- Gate status: `{gate.get('status')}`",
        f"- Checks: {summary.get('check_count')}",
        f"- Failed checks: {summary.get('failed_check_count')}",
        f"- Design rows: {summary.get('design_row_count')}",
        f"- Output fields: {summary.get('output_field_count')}",
        f"- Failure buckets: {summary.get('failure_bucket_count')}",
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
        "- Passing this gate only allows a metadata/chunking diagnostic dry-run contract.",
        "- It does not run diagnostics, read Qdrant, scan the knowledge base, merge chunks, edit metadata, change ingestion, tune retrieval, add anchors, or modify eval cases.",
        "- It does not call backend/vector/language-model services and does not run full evaluation.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-design-report", type=Path, default=DEFAULT_RUNNER_DESIGN_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.runner_design_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking diagnostic runner design gate checked: "
        f"{summary.get('status')}, {summary.get('failed_check_count')} failed"
    )
    return 0 if report["gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
