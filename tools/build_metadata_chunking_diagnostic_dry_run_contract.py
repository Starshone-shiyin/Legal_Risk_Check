"""Build the v0.4.9.10 metadata/chunking diagnostic dry-run contract.

The contract consumes only the v0.4.9.9 runner design gate and v0.4.9.8
runner design saved reports. It defines a future dry-run runner interface; it
does not implement or execute the diagnostic runner.
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
)


VERSION = "0.4.9.10"

DEFAULT_RUNNER_DESIGN_GATE_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_design_gate_report.json")
DEFAULT_RUNNER_DESIGN_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_dry_run_contract_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md")

CONTRACT_ROW_ORDER = [
    "input_saved_report_contract",
    "cli_argument_contract",
    "diagnostic_output_contract",
    "failure_handling_contract",
    "non_runtime_boundary_contract",
]

DRY_RUN_OUTPUT_FIELDS = [
    "report_version",
    "case_id",
    "source_spec_row_id",
    "check_group",
    "dry_run_status",
    "metadata_completeness_status",
    "chunk_boundary_status",
    "parent_article_link_status",
    "citation_identity_status",
    "article_locator_status",
    "diagnostic_followup",
    "blocking_findings",
    "source_runner_design_status",
    "source_design_gate_status",
]

PROHIBITED_ACTIONS = [
    "execute_diagnostic",
    "read_qdrant",
    "connect_qdrant",
    "scan_knowledge_base_fulltext",
    "run_rag_query",
    "call_llm",
    "merge_or_rewrite_chunks",
    "edit_metadata",
    "change_ingestion_pipeline",
    "tune_retrieval_parameters",
    "add_anchor_rules",
    "modify_eval_cases_or_fixtures",
]

GUARDRAILS = {
    "saved_reports_only": True,
    "contract_only": True,
    "runner_implemented": False,
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


def source_blockers(design_gate: dict[str, Any], design: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(design_gate.get("gate"))
    design_gate_summary = as_dict(design_gate.get("summary"))
    runner_gate = as_dict(design.get("runner_design_gate"))
    if design_gate.get("version") != "0.4.9.9":
        blockers.append("design_gate_version_mismatch")
    if design_gate.get("schema_kind") != "metadata_chunking_diagnostic_runner_design_gate":
        blockers.append("design_gate_schema_mismatch")
    if gate.get("status") != "open_for_metadata_chunking_diagnostic_dry_run_contract":
        blockers.append("design_gate_not_open_for_dry_run_contract")
    if gate.get("allowed_next_step") != "metadata_chunking_diagnostic_dry_run_contract":
        blockers.append("design_gate_next_step_drift")
    if int(design_gate_summary.get("failed_check_count") or 0) != 0:
        blockers.append("design_gate_failed_checks_present")
    if as_list(gate.get("blockers")):
        blockers.append("design_gate_has_blockers")
    if gate.get("implementation_allowed") is not False or gate.get("retrieval_logic_change_allowed") is not False:
        blockers.append("design_gate_runtime_boundary_drift")
    if design.get("version") != "0.4.9.8":
        blockers.append("runner_design_version_mismatch")
    if design.get("schema_kind") != "metadata_chunking_diagnostic_runner_design":
        blockers.append("runner_design_schema_mismatch")
    if runner_gate.get("status") != "ready_for_metadata_chunking_diagnostic_runner_gate":
        blockers.append("runner_design_not_ready")
    if runner_gate.get("allowed_next_step") != "metadata_chunking_diagnostic_runner_design_gate":
        blockers.append("runner_design_next_step_drift")
    if as_dict(design.get("runner_output_contract")).get("required_fields") != OUTPUT_FIELD_CONTRACT:
        blockers.append("runner_design_output_contract_drift")
    if as_dict(design.get("runner_output_contract")).get("failure_buckets") != FAILURE_BUCKETS:
        blockers.append("runner_design_failure_bucket_drift")
    if [text(as_dict(row).get("check_group")) for row in as_list(design.get("design_rows"))] != EXPECTED_DESIGN_ROW_ORDER:
        blockers.append("runner_design_row_order_drift")
    for source_name, payload in {"design_gate": design_gate, "runner_design": design}.items():
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{source_name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def contract_rows(ready: bool) -> list[dict[str, Any]]:
    row_details = {
        "input_saved_report_contract": {
            "required_inputs": [
                "tests/metadata_chunking_diagnostic_runner_design_gate_report.json",
                "tests/metadata_chunking_diagnostic_runner_design_report.json",
                "tests/metadata_chunking_diagnostic_spec_gate_report.json",
                "tests/metadata_chunking_diagnostic_spec_report.json",
            ],
            "optional_inputs": [],
        },
        "cli_argument_contract": {
            "future_entrypoint": "tools/run_metadata_chunking_diagnostic_dry_run.py",
            "required_arguments": ["--runner-design-gate-report", "--runner-design-report", "--output"],
            "optional_arguments": ["--summary", "--fail-on-blocker"],
        },
        "diagnostic_output_contract": {
            "required_fields": DRY_RUN_OUTPUT_FIELDS,
            "inherits_runner_output_fields": OUTPUT_FIELD_CONTRACT,
        },
        "failure_handling_contract": {
            "failure_buckets": FAILURE_BUCKETS,
            "blocking_status": "blocked",
            "missing_input_status": "missing_input",
            "source_drift_status": "source_drift",
        },
        "non_runtime_boundary_contract": {
            "prohibited_actions": PROHIBITED_ACTIONS,
            "diagnostic_run": "not_run",
            "runner_implemented": False,
        },
    }
    rows = []
    for index, group in enumerate(CONTRACT_ROW_ORDER, start=1):
        rows.append({
            "contract_row_id": f"MCD-DRY-RUN-CONTRACT-{index:03d}",
            "contract_group": group,
            "details": row_details[group],
            "status": "ready_for_future_dry_run_runner" if ready else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "diagnostic_run": "not_run",
        })
    return rows


def build_report(
    runner_design_gate_report_path: Path = DEFAULT_RUNNER_DESIGN_GATE_REPORT_PATH,
    runner_design_report_path: Path = DEFAULT_RUNNER_DESIGN_REPORT_PATH,
) -> dict[str, Any]:
    design_gate = load_json(runner_design_gate_report_path)
    design = load_json(runner_design_report_path)
    blockers = source_blockers(design_gate, design)
    ready = not blockers
    rows = contract_rows(ready)
    row_order = [row["contract_group"] for row in rows]
    forbidden = sorted_unique(find_key_paths({"rows": rows}, FORBIDDEN_KEYS))
    readable = readability_paths({"rows": rows})
    failed_assertions = []
    if row_order != CONTRACT_ROW_ORDER:
        failed_assertions.append("contract_row_order_preserved")
    if DRY_RUN_OUTPUT_FIELDS[:4] != ["report_version", "case_id", "source_spec_row_id", "check_group"]:
        failed_assertions.append("dry_run_output_prefix_stable")
    if forbidden:
        failed_assertions.append("forbidden_output_keys_absent")
    if readable:
        failed_assertions.append("text_readability_gate")
    status = "ready_for_v0_4_9_series_closeout" if ready and not failed_assertions else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_dry_run_contract",
        "scope": "saved-report metadata/chunking diagnostic dry-run contract only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "metadata_chunking_diagnostic_runner_design_gate_report": {
                "path": str(runner_design_gate_report_path),
                "present": runner_design_gate_report_path.exists(),
                "version": design_gate.get("version"),
                "schema_kind": design_gate.get("schema_kind"),
            },
            "metadata_chunking_diagnostic_runner_design_report": {
                "path": str(runner_design_report_path),
                "present": runner_design_report_path.exists(),
                "version": design.get("version"),
                "schema_kind": design.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "contract_gate": {
            "status": status,
            "allowed_next_step": "v0_4_9_series_closeout" if status != "blocked" else "blocked",
            "runner_implemented": False,
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": sorted_unique(blockers + failed_assertions),
        },
        "dry_run_cli_contract": {
            "future_entrypoint": "tools/run_metadata_chunking_diagnostic_dry_run.py",
            "entrypoint_created_in_this_version": False,
            "required_arguments": ["--runner-design-gate-report", "--runner-design-report", "--output"],
            "optional_arguments": ["--summary", "--fail-on-blocker"],
            "qdrant_arguments_allowed": False,
            "knowledge_base_scan_arguments_allowed": False,
        },
        "dry_run_output_contract": {
            "required_fields": DRY_RUN_OUTPUT_FIELDS,
            "failure_buckets": FAILURE_BUCKETS,
            "summary_required": True,
            "per_case_grouping_required": True,
        },
        "prohibited_actions": PROHIBITED_ACTIONS,
        "summary": {
            "status": status,
            "contract_row_count": len(rows),
            "contract_row_order": row_order,
            "dry_run_output_field_count": len(DRY_RUN_OUTPUT_FIELDS),
            "failure_bucket_count": len(FAILURE_BUCKETS),
            "runner_implemented": False,
            "diagnostic_run": "not_run",
            "next_version_recommendation": "v0.4.9.11 retrieval input quality series closeout",
        },
        "contract_rows": rows,
        "assertions": [
            {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
            {"name": "five_contract_rows_present", "status": "passed" if len(rows) == 5 else "failed", "row_count": len(rows)},
            {"name": "contract_row_order_preserved", "status": "passed" if row_order == CONTRACT_ROW_ORDER else "failed", "actual": row_order},
            {"name": "dry_run_output_contract_complete", "status": "passed" if all(field in DRY_RUN_OUTPUT_FIELDS for field in OUTPUT_FIELD_CONTRACT) else "failed"},
            {"name": "prohibited_actions_present", "status": "passed" if PROHIBITED_ACTIONS else "failed"},
            {"name": "contract_is_non_runtime", "status": "passed" if all(row.get("implementation_allowed") is False and row.get("retrieval_logic_change_allowed") is False for row in rows) else "failed"},
            {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_paths": forbidden},
            {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
        ],
    }
    failed = [item["name"] for item in report["assertions"] if item["status"] != "passed"]
    if failed:
        report["contract_gate"]["status"] = "blocked"
        report["contract_gate"]["allowed_next_step"] = "blocked"
        report["contract_gate"]["blockers"] = sorted_unique(report["contract_gate"]["blockers"] + failed)
        report["summary"]["status"] = "blocked"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("contract_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.10 Metadata/Chunking Diagnostic Dry-Run Contract",
        "",
        "This contract defines a future dry-run runner interface. It does not implement the runner, run diagnostics, read Qdrant, scan the knowledge base, call RAG, or call an LLM.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Next allowed step: `{gate.get('allowed_next_step')}`",
        f"- Contract rows: {summary.get('contract_row_count')}",
        f"- Dry-run output fields: {summary.get('dry_run_output_field_count')}",
        f"- Runner implemented: {gate.get('runner_implemented')}",
        f"- Diagnostic run: `{gate.get('diagnostic_run')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        "",
        "## Contract Rows",
        "",
        "| Contract row | Group | Status |",
        "|---|---|---|",
    ]
    for row in as_list(report.get("contract_rows")):
        lines.append(f"| `{row.get('contract_row_id')}` | `{row.get('contract_group')}` | `{row.get('status')}` |")
    lines.extend([
        "",
        "## Dry-Run Output Fields",
        "",
    ])
    for field in as_list(as_dict(report.get("dry_run_output_contract")).get("required_fields")):
        lines.append(f"- `{field}`")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is a dry-run contract only.",
        "- It does not create the future runner entrypoint.",
        "- It does not read Qdrant, scan the knowledge base, run RAG, call an LLM, or run full evaluation.",
        "- It does not merge chunks, edit metadata, change ingestion, tune retrieval parameters, add anchors, or modify eval cases/fixtures.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-design-gate-report", type=Path, default=DEFAULT_RUNNER_DESIGN_GATE_REPORT_PATH)
    parser.add_argument("--runner-design-report", type=Path, default=DEFAULT_RUNNER_DESIGN_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.runner_design_gate_report, args.runner_design_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking diagnostic dry-run contract built: "
        f"{summary.get('status')}, {summary.get('contract_row_count')} rows"
    )
    return 0 if report["contract_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
