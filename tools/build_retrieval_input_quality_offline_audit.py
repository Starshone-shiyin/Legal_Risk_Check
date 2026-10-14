"""Build the v0.4.9.2 retrieval input quality offline audit report.

The runner consumes the v0.4.9.1 audit spec plus existing saved reports. It
summarizes bucket impact and routing signals only; it does not call services,
run evals, or authorize retrieval, rerank, prompt, rule, fixture, or case edits.
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


VERSION = "0.4.9.2"

DEFAULT_AUDIT_SPEC_PATH = legacy_report_path("retrieval_input_quality_audit_spec_report.json")
DEFAULT_INTAKE_REPORT_PATH = legacy_report_path("retrieval_input_quality_intake_report.json")
DEFAULT_BASE_RETRIEVAL_AUDIT_PATH = legacy_report_path("base_retrieval_quality_audit_report.json")
DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH = legacy_report_path("anchor_dependency_audit_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("retrieval_input_quality_offline_audit_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/retrieval_input_quality_offline_audit_v0.4.9.2.md")

EXPECTED_BUCKET_ORDER = [
    "source_article_identity_quality",
    "metadata_chunking_quality",
    "query_lexical_coverage_quality",
    "legal_domain_boundary_quality",
    "anchor_dependency_quality",
]

BUCKET_ROUTES = {
    "source_article_identity_quality": "source_article_identity_diagnostic_report",
    "metadata_chunking_quality": "metadata_chunking_diagnostic_report",
    "query_lexical_coverage_quality": "query_lexical_coverage_diagnostic_report",
    "legal_domain_boundary_quality": "legal_domain_boundary_diagnostic_report",
    "anchor_dependency_quality": "anchor_dependency_reduction_diagnostic_report",
}

BUCKET_SEVERITY = {
    "source_article_identity_quality": "medium",
    "metadata_chunking_quality": "high",
    "query_lexical_coverage_quality": "high",
    "legal_domain_boundary_quality": "medium",
    "anchor_dependency_quality": "high",
}

BUCKET_ISSUE_FILTERS = {
    "source_article_identity_quality": ["index_or_source_coverage_review_candidate"],
    "metadata_chunking_quality": ["metadata_or_chunking_review_candidate"],
    "query_lexical_coverage_quality": [
        "dense_retrieval_gap",
        "sparse_retrieval_gap",
        "union_retrieval_gap",
        "zero_base_recall",
        "no_union_gain",
    ],
    "legal_domain_boundary_quality": [
        "sparse_only_support",
        "dense_only_support",
        "union_retrieval_gap",
    ],
    "anchor_dependency_quality": [
        "anchor_dependency_review_needed",
        "anchor_masking_base_retrieval_gap",
        "anchor_rescue_success",
        "high_anchor_gain",
        "zero_base_to_anchor_recovery",
        "anchor_supported_but_final_lost",
    ],
}

GUARDRAILS = {
    "saved_reports_only": True,
    "offline_audit_only": True,
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


def source_blockers(
    spec: dict[str, Any],
    intake: dict[str, Any],
    base: dict[str, Any],
    anchor: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    spec_gate = as_dict(spec.get("spec_gate"))
    intake_gate = as_dict(intake.get("intake_gate"))
    spec_rows = as_list(spec.get("audit_spec_rows"))
    if spec.get("version") != "0.4.9.1":
        blockers.append("audit_spec_version_mismatch")
    if spec.get("schema_kind") != "retrieval_input_quality_audit_spec":
        blockers.append("audit_spec_schema_mismatch")
    if spec_gate.get("status") != "ready_for_future_offline_audit_design":
        blockers.append("audit_spec_gate_not_ready")
    if spec_gate.get("implementation_allowed") is not False:
        blockers.append("audit_spec_implementation_not_blocked")
    if spec_gate.get("retrieval_logic_change_allowed") is not False:
        blockers.append("audit_spec_retrieval_logic_not_blocked")
    if as_list(spec_gate.get("blockers")):
        blockers.append("audit_spec_has_blockers")
    if [row.get("bucket_id") for row in spec_rows] != EXPECTED_BUCKET_ORDER:
        blockers.append("audit_spec_bucket_order_drift")
    if intake.get("version") != "0.4.9.0":
        blockers.append("intake_version_mismatch")
    if intake.get("schema_kind") != "retrieval_input_quality_intake":
        blockers.append("intake_schema_mismatch")
    if intake_gate.get("status") != "ready_for_retrieval_input_quality_planning":
        blockers.append("intake_gate_not_ready")
    if base.get("version") != "0.4.7.4.3":
        blockers.append("base_retrieval_audit_version_mismatch")
    if anchor.get("version") != "0.4.7.4.4":
        blockers.append("anchor_dependency_audit_version_mismatch")
    for source_name, payload in {
        "audit_spec": spec,
        "intake": intake,
        "base_retrieval_audit": base,
        "anchor_dependency_audit": anchor,
    }.items():
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{source_name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def issue_summary(report: dict[str, Any]) -> dict[str, int]:
    return {
        str(key): int(value)
        for key, value in as_dict(as_dict(report.get("summary")).get("issue_type_summary")).items()
        if isinstance(value, int)
    }


def intake_bucket_map(intake: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("bucket_id")): row
        for row in as_list(intake.get("intake_buckets"))
        if isinstance(row, dict)
    }


def spec_row_map(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("bucket_id")): row
        for row in as_list(spec.get("audit_spec_rows"))
        if isinstance(row, dict)
    }


def case_rows(*reports: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        rows.extend(row for row in as_list(report.get("sample_case_queue")) if isinstance(row, dict))
        summary = as_dict(report.get("summary"))
        rows.extend(row for row in as_list(summary.get("high_risk_manual_review")) if isinstance(row, dict))
    return rows


def sample_case_ids(bucket_id: str, rows: list[dict[str, Any]], limit: int = 8) -> list[str]:
    filters = set(BUCKET_ISSUE_FILTERS[bucket_id])
    selected: list[str] = []
    for row in rows:
        issues = {text(issue) for issue in as_list(row.get("detected_issues"))}
        if issues & filters:
            selected.append(text(row.get("case_id")))
    if not selected and bucket_id == "legal_domain_boundary_quality":
        selected = [text(row.get("case_id")) for row in rows[:limit]]
    return sorted_unique(selected)[:limit]


def source_total(summary: dict[str, Any], key: str) -> int:
    values = as_dict(summary.get(key)).values()
    return sum(value for value in values if isinstance(value, int))


def impacted_case_count(bucket_id: str, intake: dict[str, Any], base: dict[str, Any], anchor: dict[str, Any]) -> int:
    intake_buckets = intake_bucket_map(intake)
    base_summary = as_dict(base.get("summary"))
    anchor_summary = as_dict(anchor.get("summary"))
    base_issues = issue_summary(base)
    anchor_issues = issue_summary(anchor)
    if bucket_id == "source_article_identity_quality":
        return source_total(base_summary, "missing_union_source_summary") or int(as_dict(intake_buckets.get(bucket_id)).get("evidence_count") or 0)
    if bucket_id == "metadata_chunking_quality":
        return base_issues.get("metadata_or_chunking_review_candidate", 0)
    if bucket_id == "query_lexical_coverage_quality":
        return base_issues.get("union_retrieval_gap", 0)
    if bucket_id == "legal_domain_boundary_quality":
        return int(as_dict(intake_buckets.get(bucket_id)).get("evidence_count") or len(as_dict(base_summary.get("per_domain_summary"))))
    if bucket_id == "anchor_dependency_quality":
        return anchor_issues.get("anchor_dependency_review_needed", 0) or int(anchor_summary.get("total_anchor_dependency_cases") or 0)
    return int(as_dict(intake_buckets.get(bucket_id)).get("evidence_count") or 0)


def evidence_signals(bucket_id: str, intake: dict[str, Any], base: dict[str, Any], anchor: dict[str, Any]) -> list[str]:
    intake_buckets = intake_bucket_map(intake)
    base_summary = as_dict(base.get("summary"))
    anchor_summary = as_dict(anchor.get("summary"))
    base_issues = issue_summary(base)
    anchor_issues = issue_summary(anchor)
    bucket = as_dict(intake_buckets.get(bucket_id))
    if bucket_id == "source_article_identity_quality":
        return [
            f"missing_union_source_total={source_total(base_summary, 'missing_union_source_summary')}",
            f"source_groups={len(as_dict(base_summary.get('missing_union_source_summary')))}",
            f"index_or_source_coverage_review_candidate={base_issues.get('index_or_source_coverage_review_candidate', 0)}",
        ]
    if bucket_id == "metadata_chunking_quality":
        return [
            f"metadata_or_chunking_review_candidate={base_issues.get('metadata_or_chunking_review_candidate', 0)}",
            f"anchor_metadata_or_chunking_cases={bucket.get('anchor_metadata_or_chunking_cases')}",
            f"anchor_masking_base_retrieval_gap={anchor_issues.get('anchor_masking_base_retrieval_gap', 0)}",
        ]
    if bucket_id == "query_lexical_coverage_quality":
        return [
            f"dense_retrieval_gap={base_issues.get('dense_retrieval_gap', 0)}",
            f"sparse_retrieval_gap={base_issues.get('sparse_retrieval_gap', 0)}",
            f"union_retrieval_gap={base_issues.get('union_retrieval_gap', 0)}",
            f"zero_base_recall={base_issues.get('zero_base_recall', 0)}",
            f"no_union_gain={base_issues.get('no_union_gain', 0)}",
        ]
    if bucket_id == "legal_domain_boundary_quality":
        return [
            f"domain_count={len(as_dict(base_summary.get('per_domain_summary')))}",
            f"missing_functional_type_count={len(as_dict(base_summary.get('missing_union_functional_type_summary')))}",
            f"sparse_only_support={base_issues.get('sparse_only_support', 0)}",
            f"dense_only_support={base_issues.get('dense_only_support', 0)}",
        ]
    if bucket_id == "anchor_dependency_quality":
        return [
            f"anchor_dependency_review_needed={anchor_issues.get('anchor_dependency_review_needed', 0)}",
            f"anchor_masking_base_retrieval_gap={anchor_issues.get('anchor_masking_base_retrieval_gap', 0)}",
            f"anchor_rescue_success={anchor_issues.get('anchor_rescue_success', 0)}",
            f"zero_base_to_anchor_recovery={anchor_issues.get('zero_base_to_anchor_recovery', 0)}",
            f"anchor_supported_but_final_lost={anchor_issues.get('anchor_supported_but_final_lost', 0)}",
            f"anchor_gain_buckets={len(as_dict(anchor_summary.get('anchor_gain_summary')))}",
        ]
    return [f"source_evidence_count={bucket.get('evidence_count')}"]


def audit_findings(bucket_id: str) -> list[str]:
    return {
        "source_article_identity_quality": [
            "Missing-source signals are concentrated enough to require source/article identity diagnostics before parameter tuning.",
            "The audit treats naming drift and true index absence as separate follow-up questions.",
        ],
        "metadata_chunking_quality": [
            "Metadata/chunking review remains a high-impact route because most anchor-recovered cases are weak at base retrieval.",
            "The next diagnostic should check parent article identity, chunk boundaries, and article-level filterability separately.",
        ],
        "query_lexical_coverage_quality": [
            "Dense, sparse, and union gaps overlap across the base retrieval audit, so lexical bridge review remains necessary.",
            "Zero-base-recall cases should be explained before adding runtime query expansion.",
        ],
        "legal_domain_boundary_quality": [
            "Domain and functional-type signals are present but should be audited as diagnostic evidence, not as routing rules yet.",
            "The next diagnostic should separate valid cross-domain support from irrelevant legal-domain drift.",
        ],
        "anchor_dependency_quality": [
            "Anchor rescue is useful, but the saved reports show it is also masking weak base retrieval in many cases.",
            "The next diagnostic should distinguish healthy supplemental anchors from base-retrieval undercoverage.",
        ],
    }[bucket_id]


def audit_rows(spec: dict[str, Any], intake: dict[str, Any], base: dict[str, Any], anchor: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    specs = spec_row_map(spec)
    cases = case_rows(intake, base, anchor)
    rows = []
    for index, bucket_id in enumerate(EXPECTED_BUCKET_ORDER, start=1):
        spec_row = as_dict(specs.get(bucket_id))
        rows.append({
            "audit_result_id": f"RIQ-OFFLINE-AUDIT-{index:03d}",
            "source_audit_spec_id": spec_row.get("audit_spec_id"),
            "bucket_id": bucket_id,
            "priority": spec_row.get("priority"),
            "audit_status": "completed_saved_report_offline_audit" if ready else "blocked",
            "impacted_case_count": impacted_case_count(bucket_id, intake, base, anchor),
            "sample_case_ids": sample_case_ids(bucket_id, cases),
            "evidence_signals": evidence_signals(bucket_id, intake, base, anchor),
            "severity": BUCKET_SEVERITY[bucket_id],
            "audit_findings": audit_findings(bucket_id),
            "recommended_next_route": BUCKET_ROUTES[bucket_id],
            "runtime_change_allowed": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
        })
    return rows


def build_report(
    audit_spec_path: Path = DEFAULT_AUDIT_SPEC_PATH,
    intake_report_path: Path = DEFAULT_INTAKE_REPORT_PATH,
    base_retrieval_audit_path: Path = DEFAULT_BASE_RETRIEVAL_AUDIT_PATH,
    anchor_dependency_audit_path: Path = DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH,
) -> dict[str, Any]:
    spec = load_json(audit_spec_path)
    intake = load_json(intake_report_path)
    base = load_json(base_retrieval_audit_path)
    anchor = load_json(anchor_dependency_audit_path)
    blockers = source_blockers(spec, intake, base, anchor)
    ready = not blockers
    rows = audit_rows(spec, intake, base, anchor, ready)
    status = "completed_saved_report_offline_audit" if ready else "blocked"
    severity_counts = Counter(row.get("severity") for row in rows)
    route_counts = Counter(row.get("recommended_next_route") for row in rows)
    sample_count = len(sorted_unique([case_id for row in rows for case_id in as_list(row.get("sample_case_ids"))]))
    report = {
        "version": VERSION,
        "schema_kind": "retrieval_input_quality_offline_audit",
        "scope": "saved-report retrieval input quality offline audit only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "retrieval_input_quality_audit_spec": {
                "path": str(audit_spec_path),
                "present": audit_spec_path.exists(),
                "version": spec.get("version"),
                "schema_kind": spec.get("schema_kind"),
            },
            "retrieval_input_quality_intake": {
                "path": str(intake_report_path),
                "present": intake_report_path.exists(),
                "version": intake.get("version"),
                "schema_kind": intake.get("schema_kind"),
            },
            "base_retrieval_quality_audit": {
                "path": str(base_retrieval_audit_path),
                "present": base_retrieval_audit_path.exists(),
                "version": base.get("version"),
                "scope": base.get("scope"),
            },
            "anchor_dependency_audit": {
                "path": str(anchor_dependency_audit_path),
                "present": anchor_dependency_audit_path.exists(),
                "version": anchor.get("version"),
                "scope": anchor.get("scope"),
            },
        },
        "guardrails": GUARDRAILS,
        "audit_gate": {
            "status": status,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "allowed_next_step": "retrieval_input_quality_audit_gate" if ready else "blocked",
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "audit_row_count": len(rows),
            "bucket_ids": [row["bucket_id"] for row in rows],
            "high_severity_count": severity_counts.get("high", 0),
            "severity_summary": counter_dict(severity_counts),
            "total_impacted_signal_count": sum(int(row.get("impacted_case_count") or 0) for row in rows),
            "unique_sample_case_count": sample_count,
            "recommended_route_summary": counter_dict(route_counts),
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.9.3 retrieval input quality audit gate",
        },
        "offline_audit_rows": rows,
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "five_audit_rows_present", "status": "passed" if len(rows) == 5 else "failed", "row_count": len(rows)},
        {"name": "bucket_order_preserved", "status": "passed" if [row["bucket_id"] for row in rows] == EXPECTED_BUCKET_ORDER else "failed"},
        {"name": "each_row_has_impacted_cases", "status": "passed" if all(int(row.get("impacted_case_count") or 0) > 0 for row in rows) else "failed"},
        {"name": "high_priority_rows_have_actionable_severity", "status": "passed" if all(row["severity"] in {"high", "medium"} for row in rows if row.get("priority") == "P0") else "failed"},
        {"name": "audit_is_non_runtime", "status": "passed" if all(row["implementation_allowed"] is False and row["retrieval_logic_change_allowed"] is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["audit_gate"]["status"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["audit_gate"]["blockers"] = sorted_unique(blockers + ["output_audit_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("audit_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.2 Retrieval Input Quality Offline Audit",
        "",
        "This report runs the v0.4.9.1 audit contract against existing saved reports only. It records impact signals and diagnostic routing without changing retrieval behavior.",
        "",
        "## Overview",
        "",
        f"- Audit status: `{gate.get('status')}`",
        f"- Audit rows: {summary.get('audit_row_count')}",
        f"- High severity rows: {summary.get('high_severity_count')}",
        f"- Total impacted signal count: {summary.get('total_impacted_signal_count')}",
        f"- Unique sample cases: {summary.get('unique_sample_case_count')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Audit Results",
        "",
        "| Result | Bucket | Severity | Impacted cases | Next route |",
        "|---|---|---|---:|---|",
    ]
    for row in as_list(report.get("offline_audit_rows")):
        lines.append(
            f"| `{row.get('audit_result_id')}` | `{row.get('bucket_id')}` | `{row.get('severity')}` | {row.get('impacted_case_count')} | `{row.get('recommended_next_route')}` |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is a saved-report offline audit runner only.",
        "- It does not call backend APIs, vector stores, language models, or run full evaluation.",
        "- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.",
        "- The next step may add a lightweight gate for this offline audit report.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-spec", type=Path, default=DEFAULT_AUDIT_SPEC_PATH)
    parser.add_argument("--intake-report", type=Path, default=DEFAULT_INTAKE_REPORT_PATH)
    parser.add_argument("--base-retrieval-audit", type=Path, default=DEFAULT_BASE_RETRIEVAL_AUDIT_PATH)
    parser.add_argument("--anchor-dependency-audit", type=Path, default=DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.audit_spec, args.intake_report, args.base_retrieval_audit, args.anchor_dependency_audit)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Retrieval input quality offline audit built: "
        f"{summary.get('status')}, {summary.get('audit_row_count')} rows"
    )
    return 0 if report["audit_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
