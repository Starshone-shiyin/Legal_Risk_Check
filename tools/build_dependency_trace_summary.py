"""Build v0.4.15.16 dependency trace summary from a full debug RAG eval report.

This is saved-report-only. It does not run eval, call rag_query, contact Qdrant
or an LLM, or mutate runtime configuration.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.15.16"

DEFAULT_INPUT_PATH = Path("tests/targeted_dependency_trace_v0.4.15.16_report.json")
DEFAULT_TRIAGE_PATH = Path("tests/rag_quality_triage_v0.4.15.15_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/dependency_trace_summary_v0.4.15.16_report.json")

GUARDRAILS = {
    "saved_reports_only": True,
    "runs_eval": "disallowed_by_builder",
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


def load_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def layer(report: dict[str, Any], name: str) -> dict[str, Any]:
    return as_dict(as_dict(as_dict(report.get("retrieval_diagnostics")).get("layers")).get(name))


def layer_satisfied(report: dict[str, Any], name: str) -> bool | None:
    value = layer(report, name).get("satisfied")
    return value if isinstance(value, bool) else None


def count_debug_list(report: dict[str, Any], key: str) -> int:
    return len(as_list(as_dict(report.get("debug_info")).get(key)))


def quality_counts(report: dict[str, Any]) -> dict[str, int]:
    diagnostics = as_dict(report.get("quality_signal_diagnostics"))
    return {key: len(value) for key, value in diagnostics.items() if isinstance(value, list)}


def dependency_reason(report: dict[str, Any]) -> str:
    labels = set(str(label) for label in as_list(report.get("contribution_labels")))
    union = layer_satisfied(report, "union")
    anchor = layer_satisfied(report, "anchor")
    needs_review = bool(report.get("needs_human_review"))
    if needs_review and union is True:
        return "union_satisfied_but_manual_review_or_output_rule_dependency"
    if "ANCHOR_PASS" in labels and union is False and anchor is True:
        return "base_union_gap_anchor_filled"
    if "ANCHOR_PASS" in labels:
        return "anchor_assisted_without_union_gap"
    if "RISK_SUPPLEMENT_PASS" in labels:
        return "risk_supplement_output_dependency"
    return "monitor_only"


def next_inspection(reason: str) -> str:
    if reason == "base_union_gap_anchor_filled":
        return "inspect_query_lexical_coverage_and_base_retrieval_before_any_anchor_change"
    if reason == "union_satisfied_but_manual_review_or_output_rule_dependency":
        return "inspect_answer_policy_and_manual_review_marker_before_runtime_change"
    if reason == "risk_supplement_output_dependency":
        return "inspect_risk_supplement_necessity_with_evidence_chain"
    return "monitor_only"


def case_row(report: dict[str, Any]) -> dict[str, Any]:
    debug_info = as_dict(report.get("debug_info"))
    trace = as_dict(debug_info.get("final_evidence_selection_trace"))
    reason = dependency_reason(report)
    return {
        "id": report.get("id"),
        "category": report.get("category") or "uncategorized",
        "passed": bool(report.get("passed")),
        "retrieval_confidence": report.get("retrieval_confidence"),
        "needs_human_review": bool(report.get("needs_human_review")),
        "contribution_labels": as_list(report.get("contribution_labels")),
        "dependency_reason": reason,
        "next_inspection": next_inspection(reason),
        "retrieval_layers": {
            "dense": layer_satisfied(report, "dense"),
            "sparse": layer_satisfied(report, "sparse"),
            "union": layer_satisfied(report, "union"),
            "anchor": layer_satisfied(report, "anchor"),
            "final": layer_satisfied(report, "final"),
        },
        "matched_counts": {
            name: layer(report, name).get("matched_count")
            for name in ["dense", "sparse", "union", "anchor", "final"]
        },
        "debug_candidate_counts": {
            "dense": count_debug_list(report, "dense_candidates"),
            "sparse": count_debug_list(report, "sparse_candidates"),
            "union": count_debug_list(report, "union_candidates"),
            "anchor": count_debug_list(report, "anchor_candidates"),
            "rerank_input": count_debug_list(report, "rerank_input_candidates"),
            "rerank_full_score_order": count_debug_list(report, "rerank_full_score_order"),
        },
        "final_selection_trace": {
            "full_rerank_count": trace.get("full_rerank_count"),
            "selected_count": trace.get("selected_count"),
            "score_epsilon": trace.get("score_epsilon"),
        },
        "quality_signal_counts": quality_counts(report),
    }


def build_report(
    input_path: Path = DEFAULT_INPUT_PATH,
    triage_path: Path = DEFAULT_TRIAGE_PATH,
) -> dict[str, Any]:
    source = load_json(input_path)
    triage = load_json(triage_path, required=False)
    rows = [case_row(report) for report in as_list(source.get("reports")) if isinstance(report, dict)]
    reason_counts = Counter(str(row.get("dependency_reason")) for row in rows)
    next_counts = Counter(str(row.get("next_inspection")) for row in rows)
    human_review_cases = [str(row.get("id")) for row in rows if row.get("needs_human_review")]
    base_gap_cases = [
        str(row.get("id"))
        for row in rows
        if row.get("dependency_reason") == "base_union_gap_anchor_filled"
    ]
    score_order_observation_cases = [
        str(row.get("id"))
        for row in rows
        if as_dict(row.get("quality_signal_counts")).get("score_order_observations", 0) > 0
    ]

    status = "needs_dependency_reduction_trace_review" if base_gap_cases or human_review_cases else "monitor_only"
    return {
        "version": VERSION,
        "schema_kind": "dependency_trace_summary",
        "scope": "saved full-debug targeted trace summary for dependency-heavy passing cases",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "targeted_trace_report": str(input_path),
            "source_triage_report": str(triage_path),
            "source_triage_status": as_dict(triage.get("summary")).get("status"),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "total_cases": len(rows),
            "passed_cases": sum(1 for row in rows if row.get("passed")),
            "retrieval_failure_stage_summary": as_dict(source.get("retrieval_failure_stage_summary")),
            "dependency_reason_counts": dict(sorted(reason_counts.items())),
            "next_inspection_counts": dict(sorted(next_counts.items())),
            "human_review_cases": human_review_cases,
            "base_union_gap_anchor_filled_cases": base_gap_cases,
            "score_order_observation_cases": score_order_observation_cases,
        },
        "case_rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dependency trace summary from saved full-debug report.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--triage", type=Path, default=DEFAULT_TRIAGE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.input, args.triage)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Dependency trace summary completed: "
        f"{summary['status']}, {summary['passed_cases']}/{summary['total_cases']} passed, "
        f"base_union_gap_anchor_filled={len(summary['base_union_gap_anchor_filled_cases'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
