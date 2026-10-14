"""Build the v0.4.9.4 retrieval input quality diagnostic prioritization.

The planner consumes only the v0.4.9.3 gate and v0.4.9.2 offline audit reports.
It ranks diagnostic routes and records entry conditions; it does not authorize
retrieval, rerank, prompt, rule, fixture, eval-case, or scenario changes.
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


VERSION = "0.4.9.4"

DEFAULT_GATE_REPORT_PATH = legacy_report_path("retrieval_input_quality_offline_audit_gate_report.json")
DEFAULT_OFFLINE_AUDIT_REPORT_PATH = legacy_report_path("retrieval_input_quality_offline_audit_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("retrieval_input_quality_diagnostic_prioritization_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md")

EXPECTED_BUCKET_ORDER = [
    "source_article_identity_quality",
    "metadata_chunking_quality",
    "query_lexical_coverage_quality",
    "legal_domain_boundary_quality",
    "anchor_dependency_quality",
]

EXPECTED_PRIORITY_ROUTE_ORDER = [
    "metadata_chunking_diagnostic_report",
    "anchor_dependency_reduction_diagnostic_report",
    "query_lexical_coverage_diagnostic_report",
    "source_article_identity_diagnostic_report",
    "legal_domain_boundary_diagnostic_report",
]

ROUTE_PRIORITY_MODEL = {
    "metadata_chunking_diagnostic_report": {
        "priority_rank": 1,
        "diagnostic_focus": "parent article identity, chunk boundaries, metadata completeness, and article-level filterability",
        "entry_conditions": [
            "Confirm expected evidence can be represented as coherent article or section units.",
            "Review parent identifiers, chunk identifiers, chunk counts, and citation metadata before tuning retrieval.",
            "Use saved-report samples only unless a later version explicitly approves a new diagnostic run.",
        ],
        "prohibited_actions": [
            "Do not tune retrieval parameters from this planning report.",
            "Do not merge or rewrite chunks from this planning report.",
            "Do not add anchors to compensate for metadata gaps.",
        ],
        "recommended_artifact": "metadata_chunking_diagnostic_spec",
    },
    "anchor_dependency_reduction_diagnostic_report": {
        "priority_rank": 2,
        "diagnostic_focus": "healthy supplemental anchors versus anchors masking weak base retrieval",
        "entry_conditions": [
            "Classify anchor rescue cases after metadata/chunking signals are reviewed.",
            "Separate anchor-supported-final-lost cases from zero-base-to-anchor recovery cases.",
            "Treat anchor dependency as a symptom until base retrieval undercoverage is explained.",
        ],
        "prohibited_actions": [
            "Do not delete or add anchor rules from this planning report.",
            "Do not treat anchor rescue as proof that base retrieval is healthy.",
            "Do not change final evidence selection policy from this planning report.",
        ],
        "recommended_artifact": "anchor_dependency_reduction_diagnostic_spec",
    },
    "query_lexical_coverage_diagnostic_report": {
        "priority_rank": 3,
        "diagnostic_focus": "scenario-to-article legal term bridges for dense and sparse recall",
        "entry_conditions": [
            "Review dense, sparse, union, zero-base-recall, and no-union-gain signals separately.",
            "Identify legal terms missing from queries without injecting terms into runtime prompts.",
            "Use lexical findings as review signals until a later version approves implementation design.",
        ],
        "prohibited_actions": [
            "Do not implement runtime query expansion from this planning report.",
            "Do not alter prompts or eval cases to hide lexical gaps.",
            "Do not collapse dense and sparse failures into a single explanation.",
        ],
        "recommended_artifact": "query_lexical_coverage_diagnostic_spec",
    },
    "source_article_identity_diagnostic_report": {
        "priority_rank": 4,
        "diagnostic_focus": "source naming, article identity, citation identity, and true index absence",
        "entry_conditions": [
            "Review the source identity case as a narrow P0 diagnostic before broader source work.",
            "Separate source naming drift from missing source/index coverage.",
            "Preserve legal authority boundaries when comparing aliases.",
        ],
        "prohibited_actions": [
            "Do not normalize source names in data from this planning report.",
            "Do not merge legal authorities based on textual similarity.",
            "Do not patch citations without a later source identity diagnostic.",
        ],
        "recommended_artifact": "source_article_identity_diagnostic_spec",
    },
    "legal_domain_boundary_diagnostic_report": {
        "priority_rank": 5,
        "diagnostic_focus": "domain drift and functional-type mismatch as diagnostic evidence",
        "entry_conditions": [
            "Review domain and functional-type drift after metadata, anchor, and lexical causes are separated.",
            "Distinguish valid cross-domain support from irrelevant domain pollution.",
            "Keep domain routing out of runtime until a later design is explicitly approved.",
        ],
        "prohibited_actions": [
            "Do not implement domain routing from this planning report.",
            "Do not filter candidate laws by domain from this planning report.",
            "Do not demote definition or liability provisions without a functional-type diagnostic.",
        ],
        "recommended_artifact": "legal_domain_boundary_diagnostic_spec",
    },
}

GUARDRAILS = {
    "saved_reports_only": True,
    "diagnostic_prioritization_only": True,
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


def source_blockers(gate_report: dict[str, Any], audit_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(gate_report.get("gate"))
    gate_summary = as_dict(gate_report.get("summary"))
    audit_gate = as_dict(audit_report.get("audit_gate"))
    audit_rows = as_list(audit_report.get("offline_audit_rows"))
    if gate_report.get("version") != "0.4.9.3":
        blockers.append("gate_version_mismatch")
    if gate_report.get("schema_kind") != "retrieval_input_quality_offline_audit_gate":
        blockers.append("gate_schema_mismatch")
    if gate.get("status") != "open_for_retrieval_input_quality_diagnostic_planning":
        blockers.append("gate_not_open_for_diagnostic_planning")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("gate_failed_checks_present")
    if gate.get("implementation_allowed") is not False:
        blockers.append("gate_implementation_not_blocked")
    if gate.get("retrieval_logic_change_allowed") is not False:
        blockers.append("gate_retrieval_logic_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("gate_has_blockers")
    if audit_report.get("version") != "0.4.9.2":
        blockers.append("offline_audit_version_mismatch")
    if audit_report.get("schema_kind") != "retrieval_input_quality_offline_audit":
        blockers.append("offline_audit_schema_mismatch")
    if audit_gate.get("status") != "completed_saved_report_offline_audit":
        blockers.append("offline_audit_not_completed")
    if [row.get("bucket_id") for row in audit_rows] != EXPECTED_BUCKET_ORDER:
        blockers.append("offline_audit_bucket_order_drift")
    routes = sorted_unique([text(row.get("recommended_next_route")) for row in audit_rows])
    if routes != sorted(EXPECTED_PRIORITY_ROUTE_ORDER):
        blockers.append("offline_audit_route_set_drift")
    for source_name, payload in {"gate": gate_report, "offline_audit": audit_report}.items():
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{source_name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def row_by_route(audit_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        text(row.get("recommended_next_route")): row
        for row in as_list(audit_report.get("offline_audit_rows"))
        if isinstance(row, dict)
    }


def diagnostic_priority_rows(audit_report: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    rows_by_route = row_by_route(audit_report)
    priority_rows = []
    for route_id in EXPECTED_PRIORITY_ROUTE_ORDER:
        source = as_dict(rows_by_route.get(route_id))
        model = ROUTE_PRIORITY_MODEL[route_id]
        priority_rows.append({
            "priority_rank": model["priority_rank"],
            "route_id": route_id,
            "source_audit_result_id": source.get("audit_result_id"),
            "bucket_id": source.get("bucket_id"),
            "source_priority": source.get("priority"),
            "severity": source.get("severity"),
            "impacted_case_count": source.get("impacted_case_count"),
            "sample_case_ids": as_list(source.get("sample_case_ids"))[:8],
            "evidence_signals": as_list(source.get("evidence_signals")),
            "diagnostic_focus": model["diagnostic_focus"],
            "entry_conditions": model["entry_conditions"],
            "prohibited_actions": model["prohibited_actions"],
            "recommended_artifact": model["recommended_artifact"],
            "planning_status": "ready_for_future_diagnostic_spec" if ready else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
        })
    return priority_rows


def build_report(
    gate_report_path: Path = DEFAULT_GATE_REPORT_PATH,
    offline_audit_report_path: Path = DEFAULT_OFFLINE_AUDIT_REPORT_PATH,
) -> dict[str, Any]:
    gate_report = load_json(gate_report_path)
    audit_report = load_json(offline_audit_report_path)
    blockers = source_blockers(gate_report, audit_report)
    ready = not blockers
    rows = diagnostic_priority_rows(audit_report, ready)
    status = "ready_for_diagnostic_spec_design" if ready else "blocked"
    severity_summary = Counter(text(row.get("severity")) for row in rows)
    route_order = [text(row.get("route_id")) for row in rows]
    sample_count = len(sorted_unique([case_id for row in rows for case_id in as_list(row.get("sample_case_ids"))]))
    report = {
        "version": VERSION,
        "schema_kind": "retrieval_input_quality_diagnostic_prioritization",
        "scope": "saved-report retrieval input quality diagnostic prioritization only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "offline_audit_gate_report": {
                "path": str(gate_report_path),
                "present": gate_report_path.exists(),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
            },
            "offline_audit_report": {
                "path": str(offline_audit_report_path),
                "present": offline_audit_report_path.exists(),
                "version": audit_report.get("version"),
                "schema_kind": audit_report.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "prioritization_gate": {
            "status": status,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "allowed_next_step": "retrieval_input_quality_diagnostic_spec_design" if ready else "blocked",
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "priority_row_count": len(rows),
            "route_order": route_order,
            "top_route": route_order[0] if route_order else None,
            "severity_summary": counter_dict(severity_summary),
            "total_impacted_signal_count": sum(int(row.get("impacted_case_count") or 0) for row in rows),
            "unique_sample_case_count": sample_count,
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.9.5 retrieval input quality diagnostic prioritization gate",
        },
        "diagnostic_priority_rows": rows,
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "five_priority_rows_present", "status": "passed" if len(rows) == 5 else "failed", "row_count": len(rows)},
        {"name": "priority_order_expected", "status": "passed" if route_order == EXPECTED_PRIORITY_ROUTE_ORDER else "failed", "route_order": route_order},
        {"name": "top_route_is_metadata_chunking", "status": "passed" if route_order[:1] == ["metadata_chunking_diagnostic_report"] else "failed"},
        {"name": "each_row_has_entry_conditions", "status": "passed" if all(as_list(row.get("entry_conditions")) for row in rows) else "failed"},
        {"name": "each_row_has_prohibited_actions", "status": "passed" if all(as_list(row.get("prohibited_actions")) for row in rows) else "failed"},
        {"name": "planning_is_non_runtime", "status": "passed" if all(row["implementation_allowed"] is False and row["retrieval_logic_change_allowed"] is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["prioritization_gate"]["status"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["prioritization_gate"]["blockers"] = sorted_unique(blockers + ["output_prioritization_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("prioritization_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.4 Retrieval Input Quality Diagnostic Prioritization",
        "",
        "This report ranks diagnostic routes from the passed offline audit gate. It is planning only and does not authorize runtime changes.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Priority rows: {summary.get('priority_row_count')}",
        f"- Top route: `{summary.get('top_route')}`",
        f"- Severity summary: {summary.get('severity_summary')}",
        f"- Total impacted signal count: {summary.get('total_impacted_signal_count')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Priority Matrix",
        "",
        "| Rank | Route | Bucket | Severity | Impacted cases |",
        "|---:|---|---|---|---:|",
    ]
    for row in as_list(report.get("diagnostic_priority_rows")):
        lines.append(
            f"| {row.get('priority_rank')} | `{row.get('route_id')}` | `{row.get('bucket_id')}` | `{row.get('severity')}` | {row.get('impacted_case_count')} |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is diagnostic prioritization only.",
        "- It does not run evaluation, call backend/vector/language-model services, or change runtime behavior.",
        "- It does not authorize retrieval, rerank, prompt, anchor, risk rule, fixture, scenario registry, or eval-case changes.",
        "- The next step may gate this prioritization before any diagnostic spec work.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-report", type=Path, default=DEFAULT_GATE_REPORT_PATH)
    parser.add_argument("--offline-audit-report", type=Path, default=DEFAULT_OFFLINE_AUDIT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.gate_report, args.offline_audit_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Retrieval input quality diagnostic prioritization built: "
        f"{summary.get('status')}, {summary.get('priority_row_count')} rows"
    )
    return 0 if report["prioritization_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
