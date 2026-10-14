"""Build saved-report-only RAG quality triage from an eval report.

This tool does not run eval, call rag_query, contact Qdrant or an LLM, or
mutate retrieval, rerank, prompts, anchors, risk rules, eval cases, or hidden
seeds. It reads an existing RAG eval report and writes a compact triage report
about pass quality, contribution dependency, review flags, and quality signals.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.15.15"

DEFAULT_INPUT_PATH = Path("tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/rag_quality_triage_v0.4.15.15_report.json")

DEPENDENCY_LABELS = {
    "ANCHOR_PASS",
    "RISK_SUPPLEMENT_PASS",
    "TERM_PRESERVATION_PASS",
}

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


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def case_id(report: dict[str, Any]) -> str:
    return str(report.get("id") or "")


def contribution_labels(report: dict[str, Any]) -> set[str]:
    return {str(label) for label in as_list(report.get("contribution_labels"))}


def layer_satisfied(report: dict[str, Any], layer_name: str) -> bool | None:
    layers = as_dict(as_dict(report.get("retrieval_diagnostics")).get("layers"))
    layer = as_dict(layers.get(layer_name))
    value = layer.get("satisfied")
    return value if isinstance(value, bool) else None


def final_ref_count(report: dict[str, Any]) -> int:
    diagnostics = as_dict(report.get("quality_signal_diagnostics"))
    refs = diagnostics.get("final_refs")
    if isinstance(refs, list):
        return len(refs)
    return len(as_list(report.get("evidence")))


def retrieval_confidence(report: dict[str, Any]) -> float | None:
    value = report.get("retrieval_confidence")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def quality_signal_counts(report: dict[str, Any]) -> dict[str, int]:
    diagnostics = as_dict(report.get("quality_signal_diagnostics"))
    counts = {}
    for key, value in diagnostics.items():
        if isinstance(value, list):
            counts[key] = len(value)
    return counts


def dependency_classification(report: dict[str, Any]) -> str:
    labels = contribution_labels(report)
    if "PURE_LLM_PASS" in labels and labels.isdisjoint(DEPENDENCY_LABELS):
        return "pure_llm_pass"
    if {"ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"}.issubset(labels):
        return "anchor_and_risk_supplement_assisted"
    if "ANCHOR_PASS" in labels:
        return "anchor_assisted"
    if "RISK_SUPPLEMENT_PASS" in labels:
        return "risk_supplement_assisted"
    if "TERM_PRESERVATION_PASS" in labels:
        return "term_preservation_assisted"
    return "other_or_unlabeled_pass"


def recommendation_for_case(report: dict[str, Any]) -> str:
    labels = contribution_labels(report)
    needs_review = bool(report.get("needs_human_review"))
    union_satisfied = layer_satisfied(report, "union")
    anchor_satisfied = layer_satisfied(report, "anchor")
    signal_counts = quality_signal_counts(report)

    if needs_review:
        return "manual_review_marker_present"
    if signal_counts.get("score_order_risks", 0):
        return "inspect_score_order_risk_before_runtime_change"
    if "ANCHOR_PASS" in labels and union_satisfied is False and anchor_satisfied is True:
        return "candidate_for_base_retrieval_or_query_lexical_triage"
    if {"ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"}.issubset(labels):
        return "candidate_for_dependency_reduction_targeted_smoke"
    if "RISK_SUPPLEMENT_PASS" in labels:
        return "candidate_for_output_rule_dependency_review"
    if "PURE_LLM_PASS" in labels:
        return "stable_baseline_candidate"
    return "monitor_only"


def triage_priority_score(report: dict[str, Any]) -> int:
    labels = contribution_labels(report)
    signal_counts = quality_signal_counts(report)
    confidence = retrieval_confidence(report)
    score = 0
    if report.get("needs_human_review"):
        score += 100
    if {"ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"}.issubset(labels):
        score += 30
    elif "ANCHOR_PASS" in labels or "RISK_SUPPLEMENT_PASS" in labels:
        score += 15
    score += min(signal_counts.get("score_order_observations", 0), 20)
    if confidence is not None and confidence < 0.8:
        score += 20
    elif confidence is not None and confidence < 0.82:
        score += 10
    return score


def build_case_row(report: dict[str, Any]) -> dict[str, Any]:
    signal_counts = quality_signal_counts(report)
    return {
        "id": case_id(report),
        "category": report.get("category") or "uncategorized",
        "passed": bool(report.get("passed")),
        "retrieval_failure_stage": report.get("retrieval_failure_stage"),
        "retrieval_confidence": retrieval_confidence(report),
        "needs_human_review": bool(report.get("needs_human_review")),
        "contribution_labels": sorted(contribution_labels(report)),
        "dependency_classification": dependency_classification(report),
        "recommendation": recommendation_for_case(report),
        "triage_priority_score": triage_priority_score(report),
        "retrieval_layer_satisfied": {
            "dense": layer_satisfied(report, "dense"),
            "sparse": layer_satisfied(report, "sparse"),
            "union": layer_satisfied(report, "union"),
            "anchor": layer_satisfied(report, "anchor"),
            "final": layer_satisfied(report, "final"),
        },
        "quality_signal_counts": signal_counts,
        "final_ref_count": final_ref_count(report),
    }


def top_case_ids(rows: list[dict[str, Any]], recommendation: str, limit: int = 12) -> list[str]:
    selected = [row for row in rows if row.get("recommendation") == recommendation]
    selected.sort(
        key=lambda row: (
            int(row.get("triage_priority_score") or 0),
            int(as_dict(row.get("quality_signal_counts")).get("score_order_observations", 0)),
            -(row.get("retrieval_confidence") or 1.0),
            str(row.get("id") or ""),
        ),
        reverse=True,
    )
    return [row["id"] for row in selected[:limit]]


def build_report(input_path: Path = DEFAULT_INPUT_PATH) -> dict[str, Any]:
    source = load_json(input_path)
    reports = [item for item in as_list(source.get("reports")) if isinstance(item, dict)]
    rows = [build_case_row(report) for report in reports]

    label_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()
    recommendation_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    quality_signal_summary: Counter[str] = Counter()
    review_cases = []

    for row in rows:
        domain_counts[str(row["category"])] += 1
        dependency_counts[str(row["dependency_classification"])] += 1
        recommendation_counts[str(row["recommendation"])] += 1
        for label in row["contribution_labels"]:
            label_counts[label] += 1
        for key, count in as_dict(row.get("quality_signal_counts")).items():
            quality_signal_summary[key] += int(count)
        if row.get("needs_human_review"):
            review_cases.append(row["id"])

    total = len(rows)
    passed = sum(1 for row in rows if row.get("passed"))
    anchor_count = label_counts.get("ANCHOR_PASS", 0)
    risk_supplement_count = label_counts.get("RISK_SUPPLEMENT_PASS", 0)
    pure_count = label_counts.get("PURE_LLM_PASS", 0)
    both_anchor_risk = dependency_counts.get("anchor_and_risk_supplement_assisted", 0)
    score_order_risks = quality_signal_summary.get("score_order_risks", 0)
    ranked_rows = sorted(
        rows,
        key=lambda row: (
            int(row.get("triage_priority_score") or 0),
            int(as_dict(row.get("quality_signal_counts")).get("score_order_observations", 0)),
            -(row.get("retrieval_confidence") or 1.0),
            str(row.get("id") or ""),
        ),
        reverse=True,
    )

    if passed != total:
        status = "has_eval_failures"
        next_action = "triage_failed_cases_before_any_quality-optimization work"
    elif score_order_risks:
        status = "passed_with_quality_risks"
        next_action = "inspect_quality_signal_risks_before_runtime_change"
    elif anchor_count >= total / 2 or risk_supplement_count >= total / 2:
        status = "passed_with_high_dependency"
        next_action = "prioritize_dependency_reduction_triage_over_runtime_fix"
    else:
        status = "passed_with_low_dependency"
        next_action = "use_as_stable_baseline_for_targeted_smoke_or_law_expansion"

    return {
        "version": VERSION,
        "schema_kind": "rag_quality_triage",
        "scope": "saved-report quality triage for pass quality and dependency signals",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "eval_report": str(input_path),
            "report_profile": source.get("report_profile", "full_or_unspecified"),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "next_action": next_action,
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
            "retrieval_failure_stage_summary": as_dict(source.get("retrieval_failure_stage_summary")),
            "label_counts": dict(sorted(label_counts.items())),
            "dependency_classification_counts": dict(sorted(dependency_counts.items())),
            "recommendation_counts": dict(sorted(recommendation_counts.items())),
            "domain_counts": dict(sorted(domain_counts.items())),
            "quality_signal_summary": dict(sorted(quality_signal_summary.items())),
            "needs_human_review_cases": review_cases,
            "anchor_assisted_ratio": round(anchor_count / total, 4) if total else 0,
            "risk_supplement_assisted_ratio": round(risk_supplement_count / total, 4) if total else 0,
            "pure_llm_pass_ratio": round(pure_count / total, 4) if total else 0,
            "anchor_and_risk_supplement_ratio": round(both_anchor_risk / total, 4) if total else 0,
        },
        "priority_lists": {
            "top_dependency_triage_candidates": [row["id"] for row in ranked_rows[:12]],
            "manual_review_marker_present": top_case_ids(rows, "manual_review_marker_present"),
            "base_retrieval_or_query_lexical_triage": top_case_ids(
                rows,
                "candidate_for_base_retrieval_or_query_lexical_triage",
            ),
            "dependency_reduction_targeted_smoke": top_case_ids(
                rows,
                "candidate_for_dependency_reduction_targeted_smoke",
            ),
            "output_rule_dependency_review": top_case_ids(
                rows,
                "candidate_for_output_rule_dependency_review",
            ),
            "stable_baseline_candidates": top_case_ids(rows, "stable_baseline_candidate"),
        },
        "case_rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved-report-only RAG quality triage.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.input)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "RAG quality triage completed: "
        f"{summary['status']}, {summary['passed_cases']}/{summary['total_cases']} passed, "
        f"anchor_ratio={summary['anchor_assisted_ratio']}, "
        f"risk_supplement_ratio={summary['risk_supplement_assisted_ratio']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
