"""Build the v0.4.9.1 retrieval input quality audit specification.

The spec consumes the v0.4.9.0 intake report and turns each governance bucket
into an offline audit contract. It does not run the audits, call services, or
authorize retrieval, rerank, prompt, rule, fixture, or eval-case changes.
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


VERSION = "0.4.9.1"

DEFAULT_INTAKE_REPORT_PATH = legacy_report_path("retrieval_input_quality_intake_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("retrieval_input_quality_audit_spec_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/retrieval_input_quality_audit_spec_v0.4.9.1.md")

EXPECTED_BUCKET_ORDER = [
    "source_article_identity_quality",
    "metadata_chunking_quality",
    "query_lexical_coverage_quality",
    "legal_domain_boundary_quality",
    "anchor_dependency_quality",
]

AUDIT_SPECS = {
    "source_article_identity_quality": {
        "priority": "P0",
        "audit_scope": "Check whether expected legal sources and article identifiers are consistently represented before retrieval tuning.",
        "required_inputs": [
            "missing_union_source_summary",
            "sample_case_queue",
            "law_name",
            "source",
            "article_no_or_section_no",
            "parent_article_id",
            "citation",
        ],
        "required_output_fields": [
            "case_id",
            "expected_source",
            "observed_source_aliases",
            "article_identity_status",
            "source_available_in_index",
            "recommended_followup",
        ],
        "gate_checks": [
            "each sampled missing source has an identity status",
            "source aliases are grouped without merging legal authorities",
            "missing index coverage is separated from naming drift",
        ],
        "success_condition": "The audit can distinguish source/index absence from source/article naming drift.",
    },
    "metadata_chunking_quality": {
        "priority": "P0",
        "audit_scope": "Check whether metadata and chunk boundaries preserve the article-level evidence needed by dense and sparse retrieval.",
        "required_inputs": [
            "metadata_or_chunking_review_candidate",
            "parent_article_id",
            "chunk_id",
            "chunk_index",
            "chunk_count",
            "article_no_or_section_no",
            "block_type",
        ],
        "required_output_fields": [
            "case_id",
            "evidence_id",
            "metadata_completeness_status",
            "chunk_boundary_status",
            "parent_article_link_status",
            "recommended_followup",
        ],
        "gate_checks": [
            "metadata completeness is checked separately from chunk boundary quality",
            "parent article links are present for sampled expected evidence",
            "chunking issues are reported before retrieval parameter changes",
        ],
        "success_condition": "The audit can identify whether expected evidence is retrievable as a coherent article or section unit.",
    },
    "query_lexical_coverage_quality": {
        "priority": "P1",
        "audit_scope": "Check whether scenario language contains enough legal lexical bridges for sparse and dense recall.",
        "required_inputs": [
            "dense_retrieval_gap",
            "sparse_retrieval_gap",
            "union_retrieval_gap",
            "zero_base_recall",
            "query_terms",
            "expected_article_terms",
            "scenario_terms",
        ],
        "required_output_fields": [
            "case_id",
            "missing_legal_terms",
            "query_to_article_bridge_status",
            "dense_gap_reason",
            "sparse_gap_reason",
            "recommended_followup",
        ],
        "gate_checks": [
            "dense and sparse lexical gaps are not collapsed into one label",
            "zero-base-recall cases receive explicit term-bridge review",
            "suggested terms remain review signals and are not injected into runtime prompts",
        ],
        "success_condition": "The audit can explain whether query wording lacks legal terms needed to reach expected evidence.",
    },
    "legal_domain_boundary_quality": {
        "priority": "P1",
        "audit_scope": "Check whether retrieval candidates drift across legal domains or functional types in ways that can pollute evidence.",
        "required_inputs": [
            "per_domain_summary",
            "missing_union_functional_type_summary",
            "sample_case_queue",
            "category",
            "law_level",
            "functional_type",
        ],
        "required_output_fields": [
            "case_id",
            "expected_domain",
            "observed_candidate_domains",
            "domain_boundary_status",
            "functional_type_gap_status",
            "recommended_followup",
        ],
        "gate_checks": [
            "domain drift is separated from relevant cross-domain support",
            "definition, procedural, liability, and operative gaps are reported separately",
            "no domain routing rule is implemented by this audit spec",
        ],
        "success_condition": "The audit can identify domain-boundary and functional-type mismatch without changing retrieval scope.",
    },
    "anchor_dependency_quality": {
        "priority": "P0",
        "audit_scope": "Check whether anchors are supplementing retrieval or masking base retrieval undercoverage.",
        "required_inputs": [
            "anchor_dependency_review_needed",
            "anchor_masking_base_retrieval_gap",
            "anchor_rescue_success",
            "zero_base_to_anchor_recovery",
            "anchor_supported_but_final_lost",
        ],
        "required_output_fields": [
            "case_id",
            "base_coverage_status",
            "anchor_gain_status",
            "anchor_masking_status",
            "final_preservation_status",
            "recommended_followup",
        ],
        "gate_checks": [
            "anchor rescue is not treated as healthy base retrieval",
            "zero-base-to-anchor recovery is marked high priority",
            "anchor-supported-but-final-lost cases are routed to final evidence selection review",
        ],
        "success_condition": "The audit can separate healthy anchor support from anchor masking weak base retrieval.",
    },
}

GUARDRAILS = {
    "saved_reports_only": True,
    "audit_spec_only": True,
    "audits_not_run": True,
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


def source_blockers(intake: dict[str, Any]) -> list[str]:
    gate = as_dict(intake.get("intake_gate"))
    buckets = as_list(intake.get("intake_buckets"))
    bucket_ids = [row.get("bucket_id") for row in buckets]
    blockers: list[str] = []
    if intake.get("version") != "0.4.9.0":
        blockers.append("intake_version_mismatch")
    if intake.get("schema_kind") != "retrieval_input_quality_intake":
        blockers.append("intake_schema_mismatch")
    if gate.get("status") != "ready_for_retrieval_input_quality_planning":
        blockers.append("intake_gate_not_ready")
    if gate.get("implementation_allowed") is not False:
        blockers.append("intake_implementation_not_blocked")
    if gate.get("retrieval_logic_change_allowed") is not False:
        blockers.append("intake_retrieval_logic_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("intake_has_blockers")
    if bucket_ids != EXPECTED_BUCKET_ORDER:
        blockers.append("intake_bucket_order_drift")
    if len(buckets) != 5:
        blockers.append("intake_bucket_count_drift")
    for path in find_key_paths(intake, FORBIDDEN_KEYS):
        blockers.append(f"intake_forbidden_key_present:{path.split('.')[-1]}")
    if readability_paths(intake):
        blockers.append("intake_blocked_for_human_readability")
    return sorted_unique(blockers)


def spec_rows(intake: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    intake_by_bucket = {
        row.get("bucket_id"): row
        for row in as_list(intake.get("intake_buckets"))
        if isinstance(row, dict)
    }
    rows = []
    for index, bucket_id in enumerate(EXPECTED_BUCKET_ORDER, start=1):
        source = as_dict(intake_by_bucket.get(bucket_id))
        spec = AUDIT_SPECS[bucket_id]
        rows.append({
            "audit_spec_id": f"RIQ-AUDIT-SPEC-{index:03d}",
            "bucket_id": bucket_id,
            "priority": spec["priority"],
            "source_intake_status": source.get("status"),
            "source_evidence_count": source.get("evidence_count"),
            "audit_spec_status": "ready_for_future_offline_audit" if ready else "blocked",
            "audit_scope": spec["audit_scope"],
            "required_inputs": spec["required_inputs"],
            "required_output_fields": spec["required_output_fields"],
            "gate_checks": spec["gate_checks"],
            "success_condition": spec["success_condition"],
            "allowed_next_step": "future_offline_audit_runner_design",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "runtime_adoption_status": "not_allowed",
        })
    return rows


def build_report(intake_report_path: Path = DEFAULT_INTAKE_REPORT_PATH) -> dict[str, Any]:
    intake = load_json(intake_report_path)
    blockers = source_blockers(intake)
    ready = not blockers
    rows = spec_rows(intake, ready)
    status = "ready_for_future_offline_audit_design" if ready else "blocked"
    priorities = Counter(row.get("priority") for row in rows)
    report = {
        "version": VERSION,
        "schema_kind": "retrieval_input_quality_audit_spec",
        "scope": "saved-report retrieval input quality audit specification only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "retrieval_input_quality_intake": {
                "path": str(intake_report_path),
                "present": intake_report_path.exists(),
                "version": intake.get("version"),
                "schema_kind": intake.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "spec_gate": {
            "status": status,
            "audits_not_run": True,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "allowed_next_step": "retrieval_input_quality_offline_audit_runner" if ready else "blocked",
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "audit_spec_count": len(rows),
            "bucket_ids": [row["bucket_id"] for row in rows],
            "priority_summary": counter_dict(priorities),
            "required_output_field_count": sum(len(row["required_output_fields"]) for row in rows),
            "gate_check_count": sum(len(row["gate_checks"]) for row in rows),
            "audits_not_run": True,
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.9.2 retrieval input quality offline audit runner",
        },
        "audit_spec_rows": rows,
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "intake_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "five_audit_specs_present", "status": "passed" if len(rows) == 5 else "failed", "spec_count": len(rows)},
        {"name": "bucket_order_preserved", "status": "passed" if [row["bucket_id"] for row in rows] == EXPECTED_BUCKET_ORDER else "failed"},
        {"name": "each_spec_has_required_contract_fields", "status": "passed" if all(row["required_inputs"] and row["required_output_fields"] and row["gate_checks"] for row in rows) else "failed"},
        {"name": "spec_is_non_runtime", "status": "passed" if all(row["implementation_allowed"] is False and row["retrieval_logic_change_allowed"] is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["spec_gate"]["status"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["spec_gate"]["blockers"] = sorted_unique(blockers + ["output_spec_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("spec_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.1 Retrieval Input Quality Audit Spec",
        "",
        "This specification turns the v0.4.9.0 intake buckets into offline audit contracts. It does not run audits or change retrieval behavior.",
        "",
        "## Overview",
        "",
        f"- Spec status: `{gate.get('status')}`",
        f"- Audit specs: {summary.get('audit_spec_count')}",
        f"- Priority summary: {summary.get('priority_summary')}",
        f"- Required output fields: {summary.get('required_output_field_count')}",
        f"- Gate checks: {summary.get('gate_check_count')}",
        f"- Audits not run: {summary.get('audits_not_run')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Audit Specs",
        "",
        "| Spec | Bucket | Priority | Status |",
        "|---|---|---|---|",
    ]
    for row in as_list(report.get("audit_spec_rows")):
        lines.append(
            f"| `{row.get('audit_spec_id')}` | `{row.get('bucket_id')}` | `{row.get('priority')}` | `{row.get('audit_spec_status')}` |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is an audit specification only.",
        "- It does not execute audits, call backend APIs, RAG, Qdrant, or LLM services.",
        "- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.",
        "- The next step may build an offline audit runner against this contract.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake-report", type=Path, default=DEFAULT_INTAKE_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.intake_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Retrieval input quality audit spec built: "
        f"{summary.get('status')}, {summary.get('audit_spec_count')} specs"
    )
    return 0 if report["spec_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
