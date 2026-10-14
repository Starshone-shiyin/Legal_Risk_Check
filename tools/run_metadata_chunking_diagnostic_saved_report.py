"""Run the v0.4.10.1 saved-report metadata/chunking diagnostic runner.

This runner executes only the saved-report scope defined by the v0.4.10.0
manifest. It validates diagnostic input readiness and output contract shape; it
does not inspect Qdrant, scan the knowledge base, or repair metadata/chunks.
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
from tools.build_metadata_chunking_diagnostic_runner_design import FAILURE_BUCKETS


VERSION = "0.4.10.1"

DEFAULT_MANIFEST_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json")
DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH = legacy_report_path("metadata_chunking_diagnostic_dry_run_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_diagnostic_saved_report_runner_v0.4.10.1.md")

GUARDRAILS = {
    "saved_reports_only": True,
    "saved_report_diagnostic_runner": True,
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


def source_blockers(manifest: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    manifest_gate = as_dict(manifest.get("manifest_gate"))
    contract_gate = as_dict(contract.get("contract_gate"))
    if manifest.get("version") != "0.4.10.0":
        blockers.append("manifest_version_mismatch")
    if manifest.get("schema_kind") != "metadata_chunking_diagnostic_runner_manifest":
        blockers.append("manifest_schema_mismatch")
    if manifest_gate.get("status") != "ready_for_saved_report_metadata_chunking_diagnostic_runner":
        blockers.append("manifest_not_ready")
    if manifest_gate.get("allowed_next_step") != "saved_report_metadata_chunking_diagnostic_runner":
        blockers.append("manifest_next_step_drift")
    if contract.get("version") != "0.4.9.10":
        blockers.append("dry_run_contract_version_mismatch")
    if contract.get("schema_kind") != "metadata_chunking_diagnostic_dry_run_contract":
        blockers.append("dry_run_contract_schema_mismatch")
    if contract_gate.get("status") != "ready_for_v0_4_9_series_closeout":
        blockers.append("dry_run_contract_not_ready")
    if as_dict(contract.get("dry_run_output_contract")).get("required_fields") != DRY_RUN_OUTPUT_FIELDS:
        blockers.append("dry_run_output_contract_drift")
    for source_name, payload in {"manifest": manifest, "contract": contract}.items():
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{source_name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def status_for_group(check_group: str, target: str) -> str:
    if check_group == target:
        return "contract_ready_saved_report_scope"
    return "not_applicable_saved_report_scope"


def diagnostic_rows(manifest: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    rows = []
    for item in as_list(manifest.get("manifest_items")):
        manifest_item = as_dict(item)
        check_group = text(manifest_item.get("check_group"))
        missing_contract_bits = []
        for field in ["case_id", "source_spec_row_id", "check_group"]:
            if not manifest_item.get(field):
                missing_contract_bits.append(field)
        if not as_list(manifest_item.get("required_fields")):
            missing_contract_bits.append("required_fields")
        blocking_findings = [f"missing_manifest_{field}" for field in missing_contract_bits]
        if not ready:
            blocking_findings.append("source_not_ready")
        rows.append({
            "report_version": VERSION,
            "case_id": manifest_item.get("case_id"),
            "source_spec_row_id": manifest_item.get("source_spec_row_id"),
            "check_group": check_group,
            "dry_run_status": "completed_saved_report_scope" if not blocking_findings else "blocked",
            "metadata_completeness_status": status_for_group(check_group, "metadata_identity_fields"),
            "chunk_boundary_status": status_for_group(check_group, "chunk_boundary_fields"),
            "parent_article_link_status": status_for_group(check_group, "article_locator_fields"),
            "citation_identity_status": status_for_group(check_group, "metadata_identity_fields"),
            "article_locator_status": status_for_group(check_group, "article_locator_fields"),
            "diagnostic_followup": "requires_read_only_metadata_snapshot_for_evidence_level_result",
            "blocking_findings": blocking_findings,
            "source_runner_design_status": "manifest_ready" if ready else "blocked",
            "source_design_gate_status": "contract_ready" if ready else "blocked",
        })
    return rows


def build_report(
    manifest_report_path: Path = DEFAULT_MANIFEST_REPORT_PATH,
    dry_run_contract_report_path: Path = DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH,
) -> dict[str, Any]:
    manifest = load_json(manifest_report_path)
    contract = load_json(dry_run_contract_report_path)
    blockers = source_blockers(manifest, contract)
    ready = not blockers
    rows = diagnostic_rows(manifest, ready)
    forbidden = sorted_unique(find_key_paths({"rows": rows}, FORBIDDEN_KEYS))
    readable = readability_paths({"rows": rows})
    failed = []
    if any(set(DRY_RUN_OUTPUT_FIELDS) - set(row.keys()) for row in rows):
        failed.append("diagnostic_row_output_contract_incomplete")
    if any(row["blocking_findings"] for row in rows):
        failed.append("diagnostic_rows_blocked")
    if forbidden:
        failed.append("forbidden_output_keys_absent")
    if readable:
        failed.append("text_readability_gate")
    status = "completed_saved_report_metadata_chunking_diagnostic" if ready and not failed else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "metadata_chunking_diagnostic_saved_report_runner",
        "scope": "saved-report metadata/chunking diagnostic runner only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "metadata_chunking_diagnostic_runner_manifest_report": {
                "path": str(manifest_report_path),
                "present": manifest_report_path.exists(),
                "version": manifest.get("version"),
                "schema_kind": manifest.get("schema_kind"),
            },
            "metadata_chunking_diagnostic_dry_run_contract_report": {
                "path": str(dry_run_contract_report_path),
                "present": dry_run_contract_report_path.exists(),
                "version": contract.get("version"),
                "schema_kind": contract.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "runner_gate": {
            "status": status,
            "allowed_next_step": "metadata_chunking_diagnostic_saved_report_runner_gate" if status != "blocked" else "blocked",
            "diagnostic_run": "saved_report_scope_only",
            "evidence_level_metadata_snapshot_read": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": sorted_unique(blockers + failed),
        },
        "runner_limitations": {
            "evidence_level_metadata_not_inspected": True,
            "qdrant_not_read": True,
            "knowledge_base_fulltext_not_scanned": True,
            "result_meaning": "contract/readiness diagnostic only; not evidence-level metadata quality verdict",
        },
        "failure_buckets": FAILURE_BUCKETS,
        "summary": {
            "status": status,
            "diagnostic_row_count": len(rows),
            "blocked_row_count": len([row for row in rows if row["blocking_findings"]]),
            "case_count": len(sorted_unique([text(row.get("case_id")) for row in rows])),
            "check_group_count": len(sorted_unique([text(row.get("check_group")) for row in rows])),
            "diagnostic_run": "saved_report_scope_only",
            "evidence_level_metadata_snapshot_read": False,
            "next_version_recommendation": "v0.4.10.2 saved-report diagnostic runner gate",
        },
        "diagnostic_rows": rows,
        "assertions": [
            {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
            {"name": "diagnostic_rows_present", "status": "passed" if len(rows) == 40 else "failed", "row_count": len(rows)},
            {"name": "output_contract_complete", "status": "passed" if "diagnostic_row_output_contract_incomplete" not in failed else "failed"},
            {"name": "no_blocking_findings", "status": "passed" if "diagnostic_rows_blocked" not in failed else "failed"},
            {"name": "saved_report_scope_only", "status": "passed" if GUARDRAILS["evidence_level_metadata_snapshot_read"] is False else "failed"},
            {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_paths": forbidden},
            {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
        ],
    }
    if any(item["status"] != "passed" for item in report["assertions"]):
        report["runner_gate"]["status"] = "blocked"
        report["runner_gate"]["allowed_next_step"] = "blocked"
        report["summary"]["status"] = "blocked"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("runner_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.10.1 Metadata/Chunking Saved-Report Diagnostic Runner",
        "",
        "This runner validates saved-report diagnostic readiness only. It does not inspect evidence-level metadata or repair data.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Next allowed step: `{gate.get('allowed_next_step')}`",
        f"- Diagnostic rows: {summary.get('diagnostic_row_count')}",
        f"- Blocked rows: {summary.get('blocked_row_count')}",
        f"- Diagnostic run: `{gate.get('diagnostic_run')}`",
        f"- Evidence-level metadata snapshot read: {gate.get('evidence_level_metadata_snapshot_read')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        "",
        "## Boundaries",
        "",
        "- Saved-report scope only.",
        "- No Qdrant access, knowledge-base fulltext scan, RAG call, LLM call, metadata edit, chunk rewrite, ingestion change, anchor change, or eval-case change.",
        "- Evidence-level metadata quality still requires a separately approved read-only snapshot step.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-report", type=Path, default=DEFAULT_MANIFEST_REPORT_PATH)
    parser.add_argument("--dry-run-contract-report", type=Path, default=DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.manifest_report, args.dry_run_contract_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Metadata/chunking saved-report diagnostic runner completed: "
        f"{summary.get('status')}, {summary.get('diagnostic_row_count')} rows"
    )
    return 0 if report["runner_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
