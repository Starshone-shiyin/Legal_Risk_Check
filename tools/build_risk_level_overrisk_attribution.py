"""Build saved-report-only attribution for exact risk-level over-risk failures.

This tool reads an existing RAG eval report. It does not run eval, call
rag_query, contact Qdrant or an LLM, or mutate retrieval, rerank, prompts,
anchors, risk rules, eval cases, or hidden seeds.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.15.23"

DEFAULT_INPUT_PATH = Path("tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/risk_level_overrisk_attribution_v0.4.15.23_report.json")

GUARDRAILS = {
    "saved_reports_only": True,
    "runs_eval": "disallowed",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "runtime_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def expected_risk_level_check(report: dict[str, Any]) -> dict[str, Any]:
    for check in as_list(report.get("checks")):
        if isinstance(check, dict) and check.get("name") == "expected_risk_level":
            return check
    return {}


def risk_level_details(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(expected_risk_level_check(report).get("details"))


def is_over_risk(report: dict[str, Any]) -> bool:
    details = risk_level_details(report)
    return details.get("policy") == "exact" and details.get("mismatch_type") == "over_risk"


def output_contribution_counts(report: dict[str, Any]) -> dict[str, int]:
    summary = as_dict(report.get("contribution_trace_summary"))
    if not summary:
        summary = as_dict(as_dict(report.get("debug_info_summary")).get("output_contribution_counts"))
    return {
        str(key): int(value)
        for key, value in summary.items()
        if isinstance(value, int)
    }


def evidence_refs(report: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for item in as_list(report.get("evidence")):
        if not isinstance(item, dict):
            continue
        refs.append(
            {
                "source": item.get("source") or item.get("law_name"),
                "article_no": item.get("article_no"),
                "section_no": item.get("section_no"),
                "citation": item.get("citation"),
            }
        )
    return refs


def classify_attribution(report: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    counts = output_contribution_counts(report)
    reasons: list[str] = []
    routes: list[str] = []

    if counts.get("risk_supplement_rules", 0) > 0:
        reasons.append("risk_supplement_contributed_to_output")
        routes.append("risk_supplement_rule_review")
    if counts.get("scene_output_rules", 0) > 0:
        reasons.append("scene_output_rule_contributed_to_output")
        routes.append("scene_output_rule_review")
    if counts.get("low_risk_rules", 0) > 0:
        reasons.append("low_risk_rule_present_but_overrisk_remains")
        routes.append("low_risk_rule_coverage_review")

    if not reasons and as_list(report.get("risk_types")):
        reasons.append("risk_types_present_without_recorded_output_rule_contribution")
        routes.append("taxonomy_or_llm_wording_review")
    if not reasons:
        reasons.append("insufficient_saved_report_signal")
        routes.append("manual_expected_level_review")

    if len(as_list(report.get("risk_types"))) >= 4 or len(as_list(report.get("recommended_actions"))) >= 5:
        reasons.append("broad_risk_or_action_output_may_amplify_severity")
        routes.append("answer_wording_overstatement_review")

    unique_routes = sorted(set(routes))
    if "risk_supplement_rule_review" in unique_routes or "scene_output_rule_review" in unique_routes:
        primary = "output_rule_amplification_review"
    elif "taxonomy_or_llm_wording_review" in unique_routes:
        primary = "taxonomy_or_llm_wording_review"
    else:
        primary = "manual_expected_level_review"
    return primary, reasons, unique_routes


def confidence_for_row(primary: str, routes: list[str], reasons: list[str]) -> str:
    if primary == "output_rule_amplification_review" and (
        "risk_supplement_rule_review" in routes or "scene_output_rule_review" in routes
    ):
        return "strong_signal"
    if primary == "taxonomy_or_llm_wording_review" and reasons:
        return "medium_signal"
    return "weak_signal"


def review_reason_for_row(primary: str, routes: list[str], reasons: list[str]) -> str:
    if primary == "output_rule_amplification_review":
        return (
            "The saved report shows exact risk-level over-risk while output contribution counts include "
            "risk supplement or scene output rules. Review those output rules before changing runtime retrieval."
        )
    if primary == "taxonomy_or_llm_wording_review":
        return (
            "The saved report shows exact risk-level over-risk without recorded supplement or scene output contribution. "
            "Review taxonomy mapping and answer wording with a full trace before changing rules."
        )
    if "insufficient_saved_report_signal" in reasons:
        return "The compact saved report lacks enough attribution signal; manual expected-level review is required."
    return "Manual review is required before changing risk-level rules."


def next_step_for_row(primary: str) -> str:
    if primary == "output_rule_amplification_review":
        return "inspect_full_trace_or_rule_contribution_before_risk_rule_change"
    if primary == "taxonomy_or_llm_wording_review":
        return "run_full_trace_or_manual_review_before_taxonomy_or_prompt_change"
    return "manual_expected_level_review"


def build_case_row(report: dict[str, Any]) -> dict[str, Any]:
    details = risk_level_details(report)
    primary, reasons, routes = classify_attribution(report)
    counts = output_contribution_counts(report)
    confidence = confidence_for_row(primary, routes, reasons)
    return {
        "case_id": report.get("id"),
        "id": report.get("id"),
        "category": report.get("category") or "uncategorized",
        "passed": bool(report.get("passed")),
        "retrieval_stage": report.get("retrieval_failure_stage"),
        "retrieval_failure_stage": report.get("retrieval_failure_stage"),
        "actual_level": details.get("actual_level") or report.get("risk_level"),
        "expected_level": details.get("expected_level"),
        "mismatch_type": details.get("mismatch_type"),
        "primary_attribution": primary,
        "suspected_root_causes": routes,
        "confidence": confidence,
        "review_reason": review_reason_for_row(primary, routes, reasons),
        "recommended_next_step": next_step_for_row(primary),
        "review_routes": routes,
        "attribution_reasons": reasons,
        "output_contribution_counts": counts,
        "risk_supplement_count": counts.get("risk_supplement_rules", 0),
        "scene_output_rule_count": counts.get("scene_output_rules", 0),
        "term_preservation_count": counts.get("term_preservation_rules", 0),
        "risk_type_count": len(as_list(report.get("risk_types"))),
        "action_count": len(as_list(report.get("recommended_actions"))),
        "risk_types": as_list(report.get("risk_types")),
        "recommended_actions": as_list(report.get("recommended_actions")),
        "final_evidence_refs": evidence_refs(report),
        "evidence_refs": evidence_refs(report),
    }


def build_report(input_path: Path = DEFAULT_INPUT_PATH) -> dict[str, Any]:
    source = load_json(input_path)
    reports = [item for item in as_list(source.get("reports")) if isinstance(item, dict)]
    rows = [build_case_row(report) for report in reports if is_over_risk(report)]

    attribution_counts = Counter(str(row["primary_attribution"]) for row in rows)
    route_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    for row in rows:
        domain_counts[str(row["category"])] += 1
        confidence_counts[str(row["confidence"])] += 1
        for route in as_list(row.get("review_routes")):
            route_counts[str(route)] += 1

    status = "overrisk_attribution_ready" if rows else "no_overrisk_cases"
    return {
        "version": VERSION,
        "schema_kind": "risk_level_overrisk_attribution",
        "scope": "saved-report-only attribution for exact risk-level over-risk failures",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "source_report": str(input_path),
            "source_report_profile": source.get("report_profile"),
            "source_total": source.get("total"),
            "source_passed": source.get("passed"),
            "source_failed": source.get("failed"),
            "source_retrieval_failure_stage_summary": source.get("retrieval_failure_stage_summary", {}),
            "source_risk_level_mismatch_summary": source.get("risk_level_mismatch_summary", {}),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "overrisk_case_count": len(rows),
            "attribution_counts": dict(attribution_counts),
            "review_route_counts": dict(route_counts),
            "domain_counts": dict(domain_counts),
            "confidence_counts": dict(confidence_counts),
            "high_priority_manual_review_list": [row["case_id"] for row in rows],
            "retrieval_failure_stage_summary": source.get("retrieval_failure_stage_summary", {}),
            "expected_next_step": "risk_level_overrisk_review_before_runtime_or_rule_changes",
        },
        "case_rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build saved-report-only over-risk attribution.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.input)
    write_json(args.output, report)
    print(
        "Risk-level over-risk attribution built: "
        f"status={report['summary']['status']}, "
        f"overrisk_cases={report['summary']['overrisk_case_count']}, "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
