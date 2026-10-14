"""Build the v0.4.9.0 retrieval input quality intake report.

The intake reads existing saved reports and turns retrieval-quality symptoms
into governance buckets for future source, metadata, chunking, lexical, and
domain-boundary review. It does not call RAG/Qdrant/LLM, run eval, or modify
retrieval, rerank, rules, prompts, fixtures, or eval cases.
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


VERSION = "0.4.9.0"

DEFAULT_BASE_RETRIEVAL_AUDIT_PATH = legacy_report_path("base_retrieval_quality_audit_report.json")
DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH = legacy_report_path("anchor_dependency_audit_report.json")
DEFAULT_ROOT_CAUSE_ACTION_PLAN_PATH = legacy_report_path("evidence_root_cause_action_plan.json")
DEFAULT_SERIES_CLOSEOUT_PATH = legacy_report_path("final_evidence_selection_policy_series_closeout_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("retrieval_input_quality_intake_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/retrieval_input_quality_intake_v0.4.9.0.md")

EXPECTED_BASE_VERSION = "0.4.7.4.3"
EXPECTED_ANCHOR_VERSION = "0.4.7.4.4"
EXPECTED_ROOT_ACTION_VERSION = "0.4.7.3.5"
EXPECTED_CLOSEOUT_VERSION = "0.4.8.15"

INTAKE_BUCKETS = [
    {
        "bucket_id": "source_article_identity_quality",
        "title": "Source and article identity quality",
        "input_signals": [
            "index_or_source_coverage_review_candidate",
            "missing_union_source_summary",
        ],
        "future_review_focus": [
            "source name normalization",
            "law name and article number consistency",
            "expected evidence source availability",
        ],
    },
    {
        "bucket_id": "metadata_chunking_quality",
        "title": "Metadata and chunking quality",
        "input_signals": [
            "metadata_or_chunking_review_candidate",
            "anchor_masking_base_retrieval_gap",
        ],
        "future_review_focus": [
            "chunk granularity",
            "parent article identifiers",
            "metadata completeness and filterability",
        ],
    },
    {
        "bucket_id": "query_lexical_coverage_quality",
        "title": "Query lexical coverage quality",
        "input_signals": [
            "dense_retrieval_gap",
            "sparse_retrieval_gap",
            "union_retrieval_gap",
            "zero_base_recall",
            "no_union_gain",
        ],
        "future_review_focus": [
            "issue term expansion",
            "legal synonym coverage",
            "scenario-to-article lexical bridge",
        ],
    },
    {
        "bucket_id": "legal_domain_boundary_quality",
        "title": "Legal domain boundary quality",
        "input_signals": [
            "per_domain_summary",
            "missing_union_functional_type_summary",
        ],
        "future_review_focus": [
            "domain routing signals",
            "cross-domain pollution review",
            "functional type coverage by domain",
        ],
    },
    {
        "bucket_id": "anchor_dependency_quality",
        "title": "Anchor dependency quality",
        "input_signals": [
            "anchor_dependency_review_needed",
            "anchor_rescue_success",
            "high_anchor_gain",
            "zero_base_to_anchor_recovery",
        ],
        "future_review_focus": [
            "healthy supplemental anchor versus masking",
            "base retrieval undercoverage before adding anchors",
            "anchor-supported evidence preservation",
        ],
    },
]

GUARDRAILS = {
    "saved_reports_only": True,
    "intake_only": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_policy_implementation_allowed": False,
    "retrieval_logic_change_allowed": False,
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
    base: dict[str, Any],
    anchor: dict[str, Any],
    action_plan: dict[str, Any],
    closeout: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if base.get("version") != EXPECTED_BASE_VERSION:
        blockers.append("base_retrieval_audit_version_mismatch")
    if as_dict(base.get("summary")).get("total_base_gap_cases", 0) <= 0:
        blockers.append("base_retrieval_audit_has_no_gap_cases")
    if anchor.get("version") != EXPECTED_ANCHOR_VERSION:
        blockers.append("anchor_dependency_audit_version_mismatch")
    if as_dict(anchor.get("summary")).get("total_anchor_dependency_cases", 0) <= 0:
        blockers.append("anchor_dependency_audit_has_no_cases")
    if action_plan.get("version") != EXPECTED_ROOT_ACTION_VERSION:
        blockers.append("root_cause_action_plan_version_mismatch")
    if as_dict(action_plan.get("summary")).get("total_actions", 0) <= 0:
        blockers.append("root_cause_action_plan_has_no_actions")
    if closeout.get("version") != EXPECTED_CLOSEOUT_VERSION:
        blockers.append("series_closeout_version_mismatch")
    if as_dict(closeout.get("closeout_gate")).get("status") != "v0_4_8_series_closed_for_offline_design":
        blockers.append("v0_4_8_series_not_closed")
    for name, payload in [
        ("base", base),
        ("anchor", anchor),
        ("action_plan", action_plan),
        ("closeout", closeout),
    ]:
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{name}_forbidden_key_present:{path.split('.')[-1]}")
    return sorted_unique(blockers)


def issue_count(summary: dict[str, Any], issue: str) -> int:
    return int(as_dict(summary.get("issue_type_summary")).get(issue, 0) or 0)


def high_priority_cases(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in as_list(as_dict(report.get("summary")).get("high_risk_manual_review")) if isinstance(item, dict)]


def bucket_rows(base: dict[str, Any], anchor: dict[str, Any]) -> list[dict[str, Any]]:
    base_summary = as_dict(base.get("summary"))
    anchor_summary = as_dict(anchor.get("summary"))
    rows = []
    for bucket in INTAKE_BUCKETS:
        bucket_id = bucket["bucket_id"]
        if bucket_id == "source_article_identity_quality":
            evidence_count = issue_count(base_summary, "index_or_source_coverage_review_candidate")
            extra = {
                "missing_union_source_summary": as_dict(base_summary.get("missing_union_source_summary")),
            }
        elif bucket_id == "metadata_chunking_quality":
            evidence_count = max(
                issue_count(base_summary, "metadata_or_chunking_review_candidate"),
                issue_count(anchor_summary, "metadata_or_chunking_review_candidate"),
            )
            extra = {
                "base_metadata_or_chunking_cases": issue_count(base_summary, "metadata_or_chunking_review_candidate"),
                "anchor_metadata_or_chunking_cases": issue_count(anchor_summary, "metadata_or_chunking_review_candidate"),
            }
        elif bucket_id == "query_lexical_coverage_quality":
            evidence_count = max(
                issue_count(base_summary, "dense_retrieval_gap"),
                issue_count(base_summary, "sparse_retrieval_gap"),
                issue_count(base_summary, "union_retrieval_gap"),
            )
            extra = {
                "zero_base_recall_cases": issue_count(base_summary, "zero_base_recall"),
                "no_union_gain_cases": issue_count(base_summary, "no_union_gain"),
            }
        elif bucket_id == "legal_domain_boundary_quality":
            domain_summary = as_dict(base_summary.get("per_domain_summary"))
            function_summary = as_dict(base_summary.get("missing_union_functional_type_summary"))
            evidence_count = len(domain_summary)
            extra = {
                "domain_count": len(domain_summary),
                "per_domain_summary": domain_summary,
                "missing_union_functional_type_summary": function_summary,
            }
        else:
            evidence_count = issue_count(anchor_summary, "anchor_dependency_review_needed")
            extra = {
                "anchor_rescue_success_cases": issue_count(anchor_summary, "anchor_rescue_success"),
                "zero_base_to_anchor_recovery_cases": issue_count(anchor_summary, "zero_base_to_anchor_recovery"),
                "anchor_supported_but_final_lost_cases": issue_count(anchor_summary, "anchor_supported_but_final_lost"),
            }
        rows.append({
            "bucket_id": bucket_id,
            "title": bucket["title"],
            "status": "ready_for_future_quality_audit" if evidence_count > 0 else "watch_only",
            "evidence_count": evidence_count,
            "input_signals": bucket["input_signals"],
            "future_review_focus": bucket["future_review_focus"],
            "implementation_allowed": False,
            "code_patch_authorized": False,
            **extra,
        })
    return rows


def sample_cases(base: dict[str, Any], anchor: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    by_case: dict[str, dict[str, Any]] = {}
    for source_name, report in [("base_retrieval_quality_audit", base), ("anchor_dependency_audit", anchor)]:
        for item in high_priority_cases(report):
            case_id = text(item.get("case_id"))
            if not case_id:
                continue
            target = by_case.setdefault(case_id, {
                "case_id": case_id,
                "risk_level": item.get("risk_level"),
                "sources": [],
                "detected_issues": [],
                "review_reasons": [],
            })
            target["sources"].append(source_name)
            target["detected_issues"].extend(as_list(item.get("detected_issues")))
            target["review_reasons"].extend(as_list(item.get("review_reasons")))
    rows = []
    for case_id in sorted(by_case):
        row = by_case[case_id]
        row["sources"] = sorted_unique([text(value) for value in row["sources"]])
        row["detected_issues"] = sorted_unique([text(value) for value in row["detected_issues"]])
        row["review_reasons"] = sorted_unique([text(value) for value in row["review_reasons"]])
        row["suggested_intake_use"] = "future_retrieval_input_quality_manual_review_sample"
        rows.append(row)
    return rows[:limit]


def build_report(
    base_retrieval_audit_path: Path = DEFAULT_BASE_RETRIEVAL_AUDIT_PATH,
    anchor_dependency_audit_path: Path = DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH,
    root_cause_action_plan_path: Path = DEFAULT_ROOT_CAUSE_ACTION_PLAN_PATH,
    series_closeout_path: Path = DEFAULT_SERIES_CLOSEOUT_PATH,
) -> dict[str, Any]:
    base = load_json(base_retrieval_audit_path)
    anchor = load_json(anchor_dependency_audit_path)
    action_plan = load_json(root_cause_action_plan_path)
    closeout = load_json(series_closeout_path)
    blockers = source_blockers(base, anchor, action_plan, closeout)
    rows = bucket_rows(base, anchor)
    cases = sample_cases(base, anchor)
    base_summary = as_dict(base.get("summary"))
    anchor_summary = as_dict(anchor.get("summary"))
    status = "ready_for_retrieval_input_quality_planning" if not blockers else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "retrieval_input_quality_intake",
        "scope": "saved-report retrieval input quality intake only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "base_retrieval_audit": {
                "path": str(base_retrieval_audit_path),
                "present": base_retrieval_audit_path.exists(),
                "version": base.get("version"),
            },
            "anchor_dependency_audit": {
                "path": str(anchor_dependency_audit_path),
                "present": anchor_dependency_audit_path.exists(),
                "version": anchor.get("version"),
            },
            "root_cause_action_plan": {
                "path": str(root_cause_action_plan_path),
                "present": root_cause_action_plan_path.exists(),
                "version": action_plan.get("version"),
            },
            "final_evidence_policy_series_closeout": {
                "path": str(series_closeout_path),
                "present": series_closeout_path.exists(),
                "version": closeout.get("version"),
            },
        },
        "guardrails": GUARDRAILS,
        "intake_gate": {
            "status": status,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "allowed_next_step": "retrieval_input_quality_audit_spec" if not blockers else "blocked",
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "bucket_count": len(rows),
            "ready_bucket_count": len([row for row in rows if row["status"] == "ready_for_future_quality_audit"]),
            "sample_case_count": len(cases),
            "total_base_gap_cases": base_summary.get("total_base_gap_cases"),
            "total_anchor_dependency_cases": anchor_summary.get("total_anchor_dependency_cases"),
            "metadata_or_chunking_review_candidates": issue_count(base_summary, "metadata_or_chunking_review_candidate"),
            "zero_base_recall_cases": issue_count(base_summary, "zero_base_recall"),
            "anchor_masking_base_retrieval_gap_cases": issue_count(anchor_summary, "anchor_masking_base_retrieval_gap"),
            "issue_summary": counter_dict(Counter({
                "dense_retrieval_gap": issue_count(base_summary, "dense_retrieval_gap"),
                "sparse_retrieval_gap": issue_count(base_summary, "sparse_retrieval_gap"),
                "union_retrieval_gap": issue_count(base_summary, "union_retrieval_gap"),
                "metadata_or_chunking_review_candidate": issue_count(base_summary, "metadata_or_chunking_review_candidate"),
                "anchor_masking_base_retrieval_gap": issue_count(anchor_summary, "anchor_masking_base_retrieval_gap"),
            })),
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.9.1 retrieval input quality audit spec",
        },
        "intake_buckets": rows,
        "sample_case_queue": cases,
        "source_action_plan_alignment": {
            "root_cause_actions": [
                {
                    "action_id": action.get("action_id"),
                    "root_cause": action.get("root_cause"),
                    "priority": action.get("priority"),
                    "observed_cases": action.get("observed_cases"),
                    "status": action.get("status"),
                }
                for action in as_list(action_plan.get("actions"))
                if action.get("root_cause") in {"base_retrieval_gap", "anchor_dependency", "final_selection_loss"}
            ],
            "v0_4_8_closeout_next_track": as_dict(closeout.get("summary")).get("next_recommended_series"),
        },
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "five_intake_buckets_present", "status": "passed" if len(rows) == 5 else "failed", "bucket_count": len(rows)},
        {"name": "base_gap_signal_present", "status": "passed" if base_summary.get("total_base_gap_cases", 0) > 0 else "failed"},
        {"name": "anchor_dependency_signal_present", "status": "passed" if anchor_summary.get("total_anchor_dependency_cases", 0) > 0 else "failed"},
        {"name": "intake_is_non_runtime", "status": "passed" if all(row["implementation_allowed"] is False and row["code_patch_authorized"] is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["intake_gate"]["status"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["intake_gate"]["blockers"] = sorted_unique(blockers + ["output_intake_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("intake_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.9.0 Retrieval Input Quality Intake",
        "",
        "This intake converts existing retrieval and evidence diagnostics into governance buckets for future input-quality work. It does not change retrieval behavior.",
        "",
        "## Overview",
        "",
        f"- Intake status: `{gate.get('status')}`",
        f"- Buckets: {summary.get('bucket_count')}",
        f"- Ready buckets: {summary.get('ready_bucket_count')}",
        f"- Sample cases: {summary.get('sample_case_count')}",
        f"- Base gap cases: {summary.get('total_base_gap_cases')}",
        f"- Anchor dependency cases: {summary.get('total_anchor_dependency_cases')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Buckets",
        "",
        "| Bucket | Status | Evidence count |",
        "|---|---|---|",
    ]
    for row in as_list(report.get("intake_buckets")):
        lines.append(f"| `{row.get('bucket_id')}` | `{row.get('status')}` | {row.get('evidence_count')} |")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is saved-report intake only.",
        "- It does not call backend APIs, RAG, Qdrant, or LLM services.",
        "- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.",
        "- The next step should specify audit contracts before any implementation work.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-retrieval-audit", type=Path, default=DEFAULT_BASE_RETRIEVAL_AUDIT_PATH)
    parser.add_argument("--anchor-dependency-audit", type=Path, default=DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH)
    parser.add_argument("--root-cause-action-plan", type=Path, default=DEFAULT_ROOT_CAUSE_ACTION_PLAN_PATH)
    parser.add_argument("--series-closeout", type=Path, default=DEFAULT_SERIES_CLOSEOUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(
        args.base_retrieval_audit,
        args.anchor_dependency_audit,
        args.root_cause_action_plan,
        args.series_closeout,
    )
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Retrieval input quality intake built: "
        f"{summary.get('status')}, {summary.get('bucket_count')} buckets, "
        f"{summary.get('sample_case_count')} sample cases"
    )
    return 0 if report["intake_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
