"""Build the v0.4.10.0 metadata/chunking diagnostic runner manifest.

The manifest reads only approved saved reports and expands the v0.4.9.x
metadata/chunking diagnostic contract into sample-case/check-group work items.
It does not execute diagnostics, inspect Qdrant, scan the knowledge base, or
authorize metadata/chunking fixes.
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
from tools.build_metadata_chunking_diagnostic_runner_design import EXPECTED_DESIGN_ROW_ORDER, FAILURE_BUCKETS


VERSION = "0.4.10.0"

DEFAULT_SERIES_CLOSEOUT_REPORT_PATH = legacy_report_path("retrieval_input_quality_series_closeout_report.json")
DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_dry_run_contract_report.json")
DEFAULT_SPEC_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_spec_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_runner_manifest_v0.4.10.0.md")

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
    "manifest_only": True,
    "diagnostic_run": "not_run",
    "diagnostic_runner_implemented": False,
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


def source_blockers(closeout: dict[str, Any], contract: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    closeout_gate = as_dict(closeout.get("closeout_gate"))
    contract_gate = as_dict(contract.get("contract_gate"))
    spec_gate = as_dict(spec.get("spec_gate"))
    if closeout.get("version") != "0.4.9.11":
        blockers.append("series_closeout_version_mismatch")
    if closeout.get("schema_kind") != "retrieval_input_quality_series_closeout":
        blockers.append("series_closeout_schema_mismatch")
    if closeout_gate.get("status") != "v0_4_9_series_closed_for_diagnostic_governance":
        blockers.append("series_closeout_not_ready")
    if contract.get("version") != "0.4.9.10":
        blockers.append("dry_run_contract_version_mismatch")
    if contract.get("schema_kind") != "metadata_chunking_diagnostic_dry_run_contract":
        blockers.append("dry_run_contract_schema_mismatch")
    if contract_gate.get("status") != "ready_for_v0_4_9_series_closeout":
        blockers.append("dry_run_contract_not_ready")
    if as_dict(contract.get("dry_run_output_contract")).get("required_fields") != DRY_RUN_OUTPUT_FIELDS:
        blockers.append("dry_run_output_contract_drift")
    if spec.get("version") != "0.4.9.6":
        blockers.append("spec_version_mismatch")
    if spec.get("schema_kind") != "metadata_chunking_diagnostic_spec":
        blockers.append("spec_schema_mismatch")
    if spec_gate.get("status") != "ready_for_future_metadata_chunking_diagnostic_runner":
        blockers.append("spec_not_ready")
    if [text(as_dict(row).get("check_group")) for row in as_list(spec.get("spec_rows"))] != EXPECTED_DESIGN_ROW_ORDER:
        blockers.append("spec_check_group_order_drift")
    for source_name, payload in {"closeout": closeout, "contract": contract, "spec": spec}.items():
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{source_name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def manifest_items(spec: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    items = []
    for spec_row in as_list(spec.get("spec_rows")):
        row = as_dict(spec_row)
        check_group = text(row.get("check_group"))
        source_spec_row_id = text(row.get("spec_row_id"))
        for case_id in as_list(row.get("sample_case_ids")):
            items.append({
                "manifest_item_id": f"MCD-MANIFEST-{len(items) + 1:03d}",
                "case_id": case_id,
                "source_spec_row_id": source_spec_row_id,
                "check_group": check_group,
                "required_fields": as_list(row.get("required_fields")),
                "failure_signals": as_list(row.get("failure_signals")),
                "failure_buckets": FAILURE_BUCKETS if check_group == "diagnostic_output_contract" else [],
                "diagnostic_input_status": "ready_for_saved_report_runner" if ready else "blocked",
                "diagnostic_run": "not_run",
                "implementation_allowed": False,
                "metadata_mutation": "disallowed",
                "chunk_mutation": "disallowed",
            })
    return items


def build_report(
    series_closeout_report_path: Path = DEFAULT_SERIES_CLOSEOUT_REPORT_PATH,
    dry_run_contract_report_path: Path = DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH,
    spec_report_path: Path = DEFAULT_SPEC_REPORT_PATH,
) -> dict[str, Any]:
    closeout = load_json(series_closeout_report_path)
    contract = load_json(dry_run_contract_report_path)
    spec = load_json(spec_report_path)
    blockers = source_blockers(closeout, contract, spec)
    ready = not blockers
    items = manifest_items(spec, ready)
    case_ids = sorted_unique([text(item.get("case_id")) for item in items])
    check_groups = [text(as_dict(row).get("check_group")) for row in as_list(spec.get("spec_rows"))]
    forbidden = sorted_unique(find_key_paths({"items": items}, FORBIDDEN_KEYS))
    readable = readability_paths({"items": items})
    failed = []
    if len(items) != len(case_ids) * len(EXPECTED_DESIGN_ROW_ORDER):
        failed.append("manifest_matrix_incomplete")
    if check_groups != EXPECTED_DESIGN_ROW_ORDER:
        failed.append("check_group_order_drift")
    if forbidden:
        failed.append("forbidden_output_keys_absent")
    if readable:
        failed.append("text_readability_gate")
    status = "ready_for_saved_report_metadata_chunking_diagnostic_runner" if ready and not failed else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_runner_manifest",
        "scope": "saved-report metadata/chunking diagnostic runner manifest only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "retrieval_input_quality_series_closeout_report": {
                "path": str(series_closeout_report_path),
                "present": series_closeout_report_path.exists(),
                "version": closeout.get("version"),
                "schema_kind": closeout.get("schema_kind"),
            },
            "metadata_chunking_diagnostic_dry_run_contract_report": {
                "path": str(dry_run_contract_report_path),
                "present": dry_run_contract_report_path.exists(),
                "version": contract.get("version"),
                "schema_kind": contract.get("schema_kind"),
            },
            "metadata_chunking_diagnostic_spec_report": {
                "path": str(spec_report_path),
                "present": spec_report_path.exists(),
                "version": spec.get("version"),
                "schema_kind": spec.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "manifest_gate": {
            "status": status,
            "allowed_next_step": "saved_report_metadata_chunking_diagnostic_runner" if status != "blocked" else "blocked",
            "diagnostic_runner_implemented": False,
            "diagnostic_run": "not_run",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": sorted_unique(blockers + failed),
        },
        "runner_input_policy": {
            "sample_source": "metadata_chunking_diagnostic_spec_report",
            "case_ids": case_ids,
            "check_groups": check_groups,
            "saved_reports_only": True,
            "qdrant_access": "disallowed",
            "knowledge_base_fulltext_scan": "disallowed",
        },
        "prohibited_actions": PROHIBITED_ACTIONS,
        "summary": {
            "status": status,
            "case_count": len(case_ids),
            "check_group_count": len(check_groups),
            "manifest_item_count": len(items),
            "diagnostic_runner_implemented": False,
            "diagnostic_run": "not_run",
            "next_version_recommendation": "v0.4.10.1 saved-report metadata/chunking diagnostic runner",
        },
        "manifest_items": items,
        "assertions": [
            {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
            {"name": "manifest_matrix_complete", "status": "passed" if "manifest_matrix_incomplete" not in failed else "failed", "case_count": len(case_ids), "item_count": len(items)},
            {"name": "check_group_order_preserved", "status": "passed" if check_groups == EXPECTED_DESIGN_ROW_ORDER else "failed", "actual": check_groups},
            {"name": "runner_not_implemented", "status": "passed" if GUARDRAILS["diagnostic_runner_implemented"] is False else "failed"},
            {"name": "manifest_is_non_runtime", "status": "passed" if all(item.get("implementation_allowed") is False for item in items) else "failed"},
            {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_paths": forbidden},
            {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
        ],
    }
    if any(item["status"] != "passed" for item in report["assertions"]):
        report["manifest_gate"]["status"] = "blocked"
        report["manifest_gate"]["allowed_next_step"] = "blocked"
        report["summary"]["status"] = "blocked"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("manifest_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.10.0 Metadata/Chunking Diagnostic Runner Manifest",
        "",
        "This manifest expands approved saved-report samples into diagnostic runner inputs. It does not implement or execute the runner.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Next allowed step: `{gate.get('allowed_next_step')}`",
        f"- Cases: {summary.get('case_count')}",
        f"- Check groups: {summary.get('check_group_count')}",
        f"- Manifest items: {summary.get('manifest_item_count')}",
        f"- Diagnostic run: `{gate.get('diagnostic_run')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        "",
        "## Boundaries",
        "",
        "- Saved reports only.",
        "- No diagnostic execution in this version.",
        "- No Qdrant access, knowledge-base fulltext scan, RAG call, LLM call, metadata edit, chunk rewrite, ingestion change, anchor change, or eval-case change.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series-closeout-report", type=Path, default=DEFAULT_SERIES_CLOSEOUT_REPORT_PATH)
    parser.add_argument("--dry-run-contract-report", type=Path, default=DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH)
    parser.add_argument("--spec-report", type=Path, default=DEFAULT_SPEC_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.series_closeout_report, args.dry_run_contract_report, args.spec_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking diagnostic runner manifest built: "
        f"{summary.get('status')}, {summary.get('manifest_item_count')} items"
    )
    return 0 if report["manifest_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
