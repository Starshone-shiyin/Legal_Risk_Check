"""Build v0.4.15.17 base retrieval / query lexical inspection.

This tool reads saved full-debug eval traces only. It does not run eval, call
rag_query, contact Qdrant or an LLM, or mutate runtime/config/test data.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.15.17"

DEFAULT_TRACE_PATH = Path("tests/targeted_dependency_trace_v0.4.15.16_report.json")
DEFAULT_SUMMARY_PATH = Path("tests/dependency_trace_summary_v0.4.15.16_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/base_retrieval_query_inspection_v0.4.15.17_report.json")

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


def load_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ref_key(item: dict[str, Any]) -> str:
    source = str(item.get("source") or item.get("law_name") or "")
    article = item.get("article_no")
    section = str(item.get("section_no") or "")
    return f"{source}::{article}::{section}"


def ref_label(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": item.get("source") or item.get("law_name"),
        "article_no": item.get("article_no"),
        "section_no": item.get("section_no") or "",
        "citation": item.get("citation"),
    }


def layers(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(as_dict(report.get("retrieval_diagnostics")).get("layers"))


def layer(report: dict[str, Any], name: str) -> dict[str, Any]:
    return as_dict(layers(report).get(name))


def layer_satisfied(report: dict[str, Any], name: str) -> bool | None:
    value = layer(report, name).get("satisfied")
    return value if isinstance(value, bool) else None


def debug(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(report.get("debug_info"))


def candidate_refs(report: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [item for item in as_list(debug(report).get(key)) if isinstance(item, dict)]


def final_refs(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in as_list(report.get("evidence")) if isinstance(item, dict)]


def candidate_keys(report: dict[str, Any], key: str) -> set[str]:
    return {ref_key(item) for item in candidate_refs(report, key)}


def final_keys(report: dict[str, Any]) -> set[str]:
    return {ref_key(item) for item in final_refs(report)}


def anchor_filled_refs(report: dict[str, Any]) -> list[dict[str, Any]]:
    union_keys = candidate_keys(report, "union_candidates")
    anchor_keys = candidate_keys(report, "anchor_candidates")
    filled = []
    for item in final_refs(report):
        key = ref_key(item)
        if key in anchor_keys and key not in union_keys:
            filled.append(ref_label(item))
    return filled


def union_top_refs(report: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    return [ref_label(item) for item in candidate_refs(report, "union_candidates")[:limit]]


def query_features(report: dict[str, Any]) -> dict[str, Any]:
    used_query = str(debug(report).get("used_query") or "")
    used_rerank_query = str(debug(report).get("used_rerank_query") or "")
    return {
        "used_query_length": len(used_query),
        "used_rerank_query_length": len(used_rerank_query),
        "has_related_concepts": "相关检索概念" in used_rerank_query,
        "has_scenario_anchor_statutes": "场景锚点法条" in used_rerank_query,
        "used_query_excerpt": used_query[:180],
        "used_rerank_query_excerpt": used_rerank_query[:260],
    }


def inspect_case(report: dict[str, Any]) -> dict[str, Any]:
    filled = anchor_filled_refs(report)
    union_satisfied = layer_satisfied(report, "union")
    anchor_satisfied = layer_satisfied(report, "anchor")
    features = query_features(report)
    final = final_refs(report)
    union_top = union_top_refs(report)
    final_key_set = {ref_key(item) for item in final}
    union_key_set = candidate_keys(report, "union_candidates")
    final_in_union_count = len(final_key_set & union_key_set)

    if union_satisfied is False and anchor_satisfied is True and filled:
        classification = "base_union_gap_with_anchor_filled_final_refs"
        next_step = "inspect_query_terms_and_base_candidate_sources_before_anchor_change"
    elif union_satisfied is True and report.get("needs_human_review"):
        classification = "union_satisfied_manual_review_or_output_dependency"
        next_step = "inspect_manual_review_marker_and_output_contribution_rules"
    elif union_satisfied is False and anchor_satisfied is True:
        classification = "base_union_gap_anchor_helped_but_final_overlap_unclear"
        next_step = "inspect_full_candidate_overlap"
    else:
        classification = "monitor_only"
        next_step = "no_immediate_action"

    return {
        "id": report.get("id"),
        "passed": bool(report.get("passed")),
        "retrieval_confidence": report.get("retrieval_confidence"),
        "needs_human_review": bool(report.get("needs_human_review")),
        "contribution_labels": as_list(report.get("contribution_labels")),
        "classification": classification,
        "next_step": next_step,
        "query_features": features,
        "retrieval_layers": {
            "dense": layer_satisfied(report, "dense"),
            "sparse": layer_satisfied(report, "sparse"),
            "union": union_satisfied,
            "anchor": anchor_satisfied,
            "final": layer_satisfied(report, "final"),
        },
        "matched_counts": {
            name: layer(report, name).get("matched_count")
            for name in ["dense", "sparse", "union", "anchor", "final"]
        },
        "final_refs": [ref_label(item) for item in final],
        "union_top_refs": union_top,
        "anchor_filled_final_refs": filled,
        "final_refs_in_union_count": final_in_union_count,
        "final_ref_count": len(final),
        "union_candidate_count": len(candidate_refs(report, "union_candidates")),
        "anchor_candidate_count": len(candidate_refs(report, "anchor_candidates")),
    }


def build_report(
    trace_path: Path = DEFAULT_TRACE_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> dict[str, Any]:
    trace = load_json(trace_path)
    dependency_summary = load_json(summary_path, required=False)
    rows = [inspect_case(report) for report in as_list(trace.get("reports")) if isinstance(report, dict)]
    classification_counts = Counter(str(row.get("classification")) for row in rows)
    next_step_counts = Counter(str(row.get("next_step")) for row in rows)
    anchor_filled_cases = [
        str(row.get("id"))
        for row in rows
        if row.get("classification") == "base_union_gap_with_anchor_filled_final_refs"
    ]
    query_anchor_hint_cases = [
        str(row.get("id"))
        for row in rows
        if as_dict(row.get("query_features")).get("has_scenario_anchor_statutes")
    ]

    status = "base_retrieval_query_inspection_needed" if anchor_filled_cases else "monitor_only"
    return {
        "version": VERSION,
        "schema_kind": "base_retrieval_query_inspection",
        "scope": "saved-report inspection for base retrieval, query lexical coverage, and anchor-filled final refs",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "targeted_trace_report": str(trace_path),
            "dependency_trace_summary": str(summary_path),
            "dependency_trace_status": as_dict(dependency_summary.get("summary")).get("status"),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "total_cases": len(rows),
            "classification_counts": dict(sorted(classification_counts.items())),
            "next_step_counts": dict(sorted(next_step_counts.items())),
            "anchor_filled_final_ref_cases": anchor_filled_cases,
            "query_contains_scenario_anchor_statutes_cases": query_anchor_hint_cases,
            "interpretation": (
                "Most inspected dependency-heavy passes already include scenario anchor statute hints in the rerank query, "
                "but base union retrieval still misses final refs later supplied by anchors."
            ),
        },
        "case_rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved-report base retrieval/query inspection.")
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.trace, args.summary)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Base retrieval/query inspection completed: "
        f"{summary['status']}, total={summary['total_cases']}, "
        f"anchor_filled_final_ref_cases={len(summary['anchor_filled_final_ref_cases'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
