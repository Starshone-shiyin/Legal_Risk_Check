"""Build the v0.4.9.8 metadata/chunking diagnostic runner design.

The design consumes only the v0.4.9.7 spec gate and v0.4.9.6 spec saved
reports. It defines a future read-only runner contract; it does not read
Qdrant, scan the knowledge base, run diagnostics, or authorize data/code fixes.
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


VERSION = "0.4.9.8"

DEFAULT_SPEC_GATE_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_spec_gate_report.json")
DEFAULT_SPEC_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_spec_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_runner_design_v0.4.9.8.md")

EXPECTED_DESIGN_ROW_ORDER = [
    "metadata_identity_fields",
    "chunk_boundary_fields",
    "article_locator_fields",
    "sample_case_mapping",
    "diagnostic_output_contract",
]

OUTPUT_FIELD_CONTRACT = [
    "case_id",
    "source_spec_row_id",
    "check_group",
    "metadata_completeness_status",
    "chunk_boundary_status",
    "parent_article_link_status",
    "citation_identity_status",
    "article_locator_status",
    "diagnostic_followup",
    "blocking_findings",
]

FAILURE_BUCKETS = [
    "metadata_completeness_gap",
    "chunk_boundary_ambiguity",
    "parent_article_link_gap",
    "citation_identity_gap",
    "article_locator_gap",
    "sample_case_mapping_gap",
]

PROHIBITED_ACTIONS = [
    "run_diagnostic",
    "read_qdrant",
    "scan_knowledge_base_fulltext",
    "merge_or_rewrite_chunks",
    "edit_metadata",
    "change_ingestion_pipeline",
    "tune_retrieval_parameters",
    "add_anchor_rules",
    "modify_eval_cases_or_fixtures",
]

GUARDRAILS = {
    "saved_reports_only": True,
    "runner_design_only": True,
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


def source_blockers(spec_gate: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(spec_gate.get("gate"))
    gate_summary = as_dict(spec_gate.get("summary"))
    spec_gate_block = as_dict(spec.get("spec_gate"))
    if spec_gate.get("version") != "0.4.9.7":
        blockers.append("spec_gate_version_mismatch")
    if spec_gate.get("schema_kind") != "metadata_chunking_diagnostic_spec_gate":
        blockers.append("spec_gate_schema_mismatch")
    if gate.get("status") != "open_for_metadata_chunking_diagnostic_runner_design":
        blockers.append("spec_gate_not_open_for_runner_design")
    if gate.get("allowed_next_step") != "metadata_chunking_diagnostic_runner_design":
        blockers.append("spec_gate_next_step_drift")
    if int(gate_summary.get("failed_check_count") or 0) != 0:
        blockers.append("spec_gate_failed_checks_present")
    if as_list(gate.get("blockers")):
        blockers.append("spec_gate_has_blockers")
    if gate.get("implementation_allowed") is not False or gate.get("retrieval_logic_change_allowed") is not False:
        blockers.append("spec_gate_runtime_boundary_drift")
    if spec.get("version") != "0.4.9.6":
        blockers.append("spec_version_mismatch")
    if spec.get("schema_kind") != "metadata_chunking_diagnostic_spec":
        blockers.append("spec_schema_mismatch")
    if spec_gate_block.get("status") != "ready_for_future_metadata_chunking_diagnostic_runner":
        blockers.append("spec_not_ready_for_runner")
    if spec_gate_block.get("allowed_next_step") != "metadata_chunking_diagnostic_runner_design":
        blockers.append("spec_next_step_drift")
    if spec_gate_block.get("implementation_allowed") is not False or spec_gate_block.get("retrieval_logic_change_allowed") is not False:
        blockers.append("spec_runtime_boundary_drift")
    for source_name, payload in {"spec_gate": spec_gate, "spec": spec}.items():
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{source_name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def design_rows(spec: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    rows = []
    sample_cases = as_list(as_dict(spec.get("sample_case_scope")).get("case_ids"))
    for index, spec_row in enumerate(as_list(spec.get("spec_rows")), start=1):
        row = as_dict(spec_row)
        check_group = text(row.get("check_group"))
        rows.append({
            "runner_design_id": f"MCD-RUNNER-DESIGN-{index:03d}",
            "source_spec_row_id": row.get("spec_row_id"),
            "check_group": check_group,
            "input_contract": {
                "source_saved_reports": [
                    "metadata_chunking_diagnostic_spec_gate_report",
                    "metadata_chunking_diagnostic_spec_report",
                ],
                "future_read_only_snapshot": "metadata_chunking_sample_snapshot",
                "sample_case_ids": sample_cases,
                "required_fields": as_list(row.get("required_fields")),
            },
            "output_contract": OUTPUT_FIELD_CONTRACT,
            "failure_buckets": failure_buckets_for_group(check_group),
            "status": "ready_for_future_read_only_runner" if ready else "blocked",
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "metadata_mutation": "disallowed",
            "chunk_mutation": "disallowed",
        })
    return rows


def failure_buckets_for_group(check_group: str) -> list[str]:
    mapping = {
        "metadata_identity_fields": ["metadata_completeness_gap", "citation_identity_gap"],
        "chunk_boundary_fields": ["chunk_boundary_ambiguity"],
        "article_locator_fields": ["article_locator_gap", "parent_article_link_gap"],
        "sample_case_mapping": ["sample_case_mapping_gap"],
        "diagnostic_output_contract": FAILURE_BUCKETS,
    }
    return mapping.get(check_group, FAILURE_BUCKETS)


def build_report(
    spec_gate_report_path: Path = DEFAULT_SPEC_GATE_REPORT_PATH,
    spec_report_path: Path = DEFAULT_SPEC_REPORT_PATH,
) -> dict[str, Any]:
    spec_gate = load_json(spec_gate_report_path)
    spec = load_json(spec_report_path)
    blockers = source_blockers(spec_gate, spec)
    ready = not blockers
    rows = design_rows(spec, ready)
    row_order = [row["check_group"] for row in rows]
    all_output_fields = sorted_unique([field for row in rows for field in as_list(row.get("output_contract"))])
    forbidden = sorted_unique(find_key_paths({"rows": rows}, FORBIDDEN_KEYS))
    readable = readability_paths({"rows": rows})
    status = "ready_for_metadata_chunking_diagnostic_runner_gate" if ready and not forbidden and not readable else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_runner_design",
        "scope": "saved-report metadata/chunking diagnostic runner design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "metadata_chunking_diagnostic_spec_gate_report": {
                "path": str(spec_gate_report_path),
                "present": spec_gate_report_path.exists(),
                "version": spec_gate.get("version"),
                "schema_kind": spec_gate.get("schema_kind"),
            },
            "metadata_chunking_diagnostic_spec_report": {
                "path": str(spec_report_path),
                "present": spec_report_path.exists(),
                "version": spec.get("version"),
                "schema_kind": spec.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "runner_design_gate": {
            "status": status,
            "allowed_next_step": "metadata_chunking_diagnostic_runner_design_gate" if status != "blocked" else "blocked",
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": sorted_unique(blockers + (["forbidden_output_keys_present"] if forbidden else []) + (["text_readability_issue"] if readable else [])),
        },
        "runner_input_contract": {
            "saved_reports": [
                "tests/metadata_chunking_diagnostic_spec_gate_report.json",
                "tests/metadata_chunking_diagnostic_spec_report.json",
            ],
            "future_read_only_snapshot": "metadata_chunking_sample_snapshot",
            "snapshot_not_read_in_this_version": True,
            "qdrant_access": "disallowed",
            "knowledge_base_fulltext_scan": "disallowed",
        },
        "runner_output_contract": {
            "required_fields": OUTPUT_FIELD_CONTRACT,
            "failure_buckets": FAILURE_BUCKETS,
            "per_case_grouping_required": True,
            "summary_required": True,
        },
        "prohibited_actions": PROHIBITED_ACTIONS,
        "summary": {
            "status": status,
            "design_row_count": len(rows),
            "design_row_order": row_order,
            "output_field_count": len(all_output_fields),
            "sample_case_count": len(as_list(as_dict(spec.get("sample_case_scope")).get("case_ids"))),
            "failure_bucket_count": len(FAILURE_BUCKETS),
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.9.9 metadata chunking diagnostic runner design gate",
        },
        "design_rows": rows,
        "assertions": [
            {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
            {"name": "five_design_rows_present", "status": "passed" if len(rows) == 5 else "failed", "row_count": len(rows)},
            {"name": "design_row_order_preserved", "status": "passed" if row_order == EXPECTED_DESIGN_ROW_ORDER else "failed", "actual": row_order},
            {"name": "output_contract_complete", "status": "passed" if all(field in all_output_fields for field in OUTPUT_FIELD_CONTRACT) else "failed", "output_fields": all_output_fields},
            {"name": "failure_buckets_present", "status": "passed" if all(bucket in FAILURE_BUCKETS for bucket in FAILURE_BUCKETS) else "failed"},
            {"name": "prohibited_actions_present", "status": "passed" if PROHIBITED_ACTIONS else "failed"},
            {"name": "runner_design_is_non_runtime", "status": "passed" if all(row.get("implementation_allowed") is False and row.get("retrieval_logic_change_allowed") is False for row in rows) else "failed"},
            {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_paths": forbidden},
            {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
        ],
    }
    failed_assertions = [item["name"] for item in report["assertions"] if item["status"] != "passed"]
    if failed_assertions:
        report["runner_design_gate"]["status"] = "blocked"
        report["runner_design_gate"]["allowed_next_step"] = "blocked"
        report["runner_design_gate"]["blockers"] = sorted_unique(report["runner_design_gate"]["blockers"] + failed_assertions)
        report["summary"]["status"] = "blocked"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("runner_design_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.8 Metadata/Chunking Diagnostic Runner Design",
        "",
        "This design defines a future read-only diagnostic runner contract. It does not run diagnostics or authorize metadata, chunking, ingestion, retrieval, rerank, prompt, rule, fixture, or eval-case changes.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Next allowed step: `{gate.get('allowed_next_step')}`",
        f"- Design rows: {summary.get('design_row_count')}",
        f"- Output fields: {summary.get('output_field_count')}",
        f"- Sample cases: {summary.get('sample_case_count')}",
        f"- Diagnostic run: `{gate.get('diagnostic_run')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        "",
        "## Design Rows",
        "",
        "| Design row | Check group | Failure buckets |",
        "|---|---|---|",
    ]
    for row in as_list(report.get("design_rows")):
        lines.append(
            f"| `{row.get('runner_design_id')}` | `{row.get('check_group')}` | {', '.join(as_list(row.get('failure_buckets')))} |"
        )
    lines.extend([
        "",
        "## Output Contract",
        "",
    ])
    for field in as_list(as_dict(report.get("runner_output_contract")).get("required_fields")):
        lines.append(f"- `{field}`")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is a runner design only.",
        "- It does not read Qdrant, scan the knowledge base, run RAG, call an LLM, or run full evaluation.",
        "- It does not merge chunks, edit metadata, change ingestion, tune retrieval parameters, add anchors, or modify eval cases/fixtures.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-gate-report", type=Path, default=DEFAULT_SPEC_GATE_REPORT_PATH)
    parser.add_argument("--spec-report", type=Path, default=DEFAULT_SPEC_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.spec_gate_report, args.spec_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking diagnostic runner design built: "
        f"{summary.get('status')}, {summary.get('design_row_count')} rows"
    )
    return 0 if report["runner_design_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
