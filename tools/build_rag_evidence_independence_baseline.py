"""Build a saved-report-only RAG evidence independence baseline.

This tool reads an existing RAG eval report and summarizes how much the passing
set depends on anchors, risk supplements, term preservation, and pure LLM output
behavior. It does not run eval, call rag_query, contact Qdrant or an LLM, or
mutate runtime configuration.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.17.1"

DEFAULT_INPUT_PATH = Path("tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/rag_evidence_independence_baseline_v0.4.17.1_report.json")

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
    "taxonomy_mutation": "disallowed",
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def contribution_labels(report: dict[str, Any]) -> set[str]:
    return {str(label) for label in as_list(report.get("contribution_labels"))}


def layer(report: dict[str, Any], name: str) -> dict[str, Any]:
    return as_dict(as_dict(as_dict(report.get("retrieval_diagnostics")).get("layers")).get(name))


def layer_satisfied(report: dict[str, Any], name: str) -> bool | None:
    value = layer(report, name).get("satisfied")
    return value if isinstance(value, bool) else None


def matched_count(report: dict[str, Any], name: str) -> int | None:
    value = layer(report, name).get("matched_count")
    return int(value) if isinstance(value, int) else None


def quality_signal_counts(report: dict[str, Any]) -> dict[str, int]:
    diagnostics = as_dict(report.get("quality_signal_diagnostics"))
    return {key: len(value) for key, value in diagnostics.items() if isinstance(value, list)}


def risk_level_mismatch_type(report_id: str, source: dict[str, Any]) -> str | None:
    summary = as_dict(source.get("risk_level_mismatch_summary"))
    for item in as_list(summary.get("mismatch_cases")):
        if str(as_dict(item).get("id")) == report_id:
            return str(as_dict(item).get("mismatch_type") or "")
    return None


def dependency_bucket(labels: set[str]) -> str:
    has_anchor = "ANCHOR_PASS" in labels
    has_risk = "RISK_SUPPLEMENT_PASS" in labels
    has_term = "TERM_PRESERVATION_PASS" in labels
    has_pure = "PURE_LLM_PASS" in labels
    if has_anchor and has_risk:
        return "anchor_and_risk_supplement"
    if has_anchor:
        return "anchor_only_or_anchor_primary"
    if has_risk:
        return "risk_supplement_primary"
    if has_term:
        return "term_preservation_primary"
    if has_pure:
        return "pure_llm_or_low_rule_dependency"
    return "unlabeled_or_other"


def independence_score(report: dict[str, Any]) -> int:
    labels = contribution_labels(report)
    score = 100
    if "ANCHOR_PASS" in labels:
        score -= 35
    if "RISK_SUPPLEMENT_PASS" in labels:
        score -= 30
    if "TERM_PRESERVATION_PASS" in labels:
        score -= 15
    if "PURE_LLM_PASS" in labels:
        score += 5
    if layer_satisfied(report, "union") is False and layer_satisfied(report, "anchor") is True:
        score -= 15
    if bool(report.get("needs_human_review")):
        score -= 20
    if not report.get("passed"):
        score -= 30
    return max(0, min(100, score))


def next_action(report: dict[str, Any]) -> str:
    labels = contribution_labels(report)
    union = layer_satisfied(report, "union")
    anchor = layer_satisfied(report, "anchor")
    if not report.get("passed"):
        return "failed_case_fact_or_expected_level_review"
    if "ANCHOR_PASS" in labels and union is False and anchor is True:
        return "inspect_base_retrieval_query_lexical_coverage"
    if {"ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"}.issubset(labels):
        return "targeted_rerun_before_runtime_change"
    if "RISK_SUPPLEMENT_PASS" in labels:
        return "inspect_output_rule_dependency"
    if "TERM_PRESERVATION_PASS" in labels:
        return "preserve_term_behavior_with_regression_watch"
    if "PURE_LLM_PASS" in labels:
        return "candidate_stable_baseline"
    return "monitor_only"


def case_row(report: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    labels = sorted(contribution_labels(report))
    report_id = str(report.get("id") or "")
    return {
        "id": report_id,
        "category": report.get("category") or "uncategorized",
        "passed": bool(report.get("passed")),
        "retrieval_failure_stage": report.get("retrieval_failure_stage"),
        "risk_level_mismatch_type": risk_level_mismatch_type(report_id, source),
        "needs_human_review": bool(report.get("needs_human_review")),
        "contribution_labels": labels,
        "dependency_bucket": dependency_bucket(set(labels)),
        "independence_score": independence_score(report),
        "next_action": next_action(report),
        "retrieval_layers": {
            name: {
                "satisfied": layer_satisfied(report, name),
                "matched_count": matched_count(report, name),
            }
            for name in ["dense", "sparse", "union", "anchor", "final"]
        },
        "quality_signal_counts": quality_signal_counts(report),
    }


def bucket_domain_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        domain = str(row.get("category") or "uncategorized")
        summary[domain][str(row.get("dependency_bucket"))] += 1
    return {domain: dict(sorted(counter.items())) for domain, counter in sorted(summary.items())}


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            int(row.get("passed") is True),
            -int(row.get("independence_score") or 0),
            str(row.get("id") or ""),
        ),
    )


def build_report(input_path: Path = DEFAULT_INPUT_PATH) -> dict[str, Any]:
    source = load_json(input_path)
    reports = [item for item in as_list(source.get("reports")) if isinstance(item, dict)]
    rows = [case_row(report, source) for report in reports]

    label_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    next_action_counts: Counter[str] = Counter()
    layer_gap_counts: Counter[str] = Counter()
    quality_signal_summary: Counter[str] = Counter()

    for row in rows:
        bucket_counts[str(row.get("dependency_bucket"))] += 1
        next_action_counts[str(row.get("next_action"))] += 1
        for label in as_list(row.get("contribution_labels")):
            label_counts[str(label)] += 1
        for name, layer_payload in as_dict(row.get("retrieval_layers")).items():
            if as_dict(layer_payload).get("satisfied") is False:
                layer_gap_counts[name] += 1
        for key, count in as_dict(row.get("quality_signal_counts")).items():
            quality_signal_summary[key] += int(count)

    total = len(rows)
    passed = sum(1 for row in rows if row.get("passed"))
    high_dependency_rows = [
        row
        for row in rows
        if row.get("dependency_bucket")
        in {"anchor_and_risk_supplement", "anchor_only_or_anchor_primary", "risk_supplement_primary"}
    ]
    ranked_dependency_rows = rank_rows(high_dependency_rows)
    failed_rows = [row for row in rows if not row.get("passed")]

    high_dependency_ratio = round(len(high_dependency_rows) / total, 4) if total else 0
    pure_ratio = round(label_counts.get("PURE_LLM_PASS", 0) / total, 4) if total else 0
    status = "needs_dependency_reduction_baseline" if high_dependency_rows else "low_dependency_baseline"
    if failed_rows:
        status = "has_failed_cases_and_dependency_hotspots"

    return {
        "version": VERSION,
        "schema_kind": "rag_evidence_independence_baseline",
        "scope": "saved-report-only baseline for RAG evidence independence and dependency hotspots",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "eval_report": str(input_path),
            "report_profile": source.get("report_profile", "full_or_unspecified"),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
            "retrieval_failure_stage_summary": as_dict(source.get("retrieval_failure_stage_summary")),
            "risk_level_mismatch_summary": as_dict(source.get("risk_level_mismatch_summary")),
            "label_counts": dict(sorted(label_counts.items())),
            "dependency_bucket_counts": dict(sorted(bucket_counts.items())),
            "next_action_counts": dict(sorted(next_action_counts.items())),
            "retrieval_layer_gap_counts": dict(sorted(layer_gap_counts.items())),
            "quality_signal_summary": dict(sorted(quality_signal_summary.items())),
            "high_dependency_case_count": len(high_dependency_rows),
            "high_dependency_ratio": high_dependency_ratio,
            "pure_llm_pass_ratio": pure_ratio,
        },
        "priority_lists": {
            "dependency_hotspots": [row["id"] for row in ranked_dependency_rows[:15]],
            "base_retrieval_query_lexical_triage": [
                row["id"]
                for row in rows
                if row.get("next_action") == "inspect_base_retrieval_query_lexical_coverage"
            ][:15],
            "targeted_rerun_before_runtime_change": [
                row["id"]
                for row in rows
                if row.get("next_action") == "targeted_rerun_before_runtime_change"
            ][:15],
            "output_rule_dependency_review": [
                row["id"]
                for row in rows
                if row.get("next_action") == "inspect_output_rule_dependency"
            ][:15],
            "failed_or_expected_level_review": [row["id"] for row in failed_rows],
        },
        "per_domain_summary": bucket_domain_summary(rows),
        "case_rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved-report-only RAG evidence independence baseline.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.input)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "RAG evidence independence baseline completed: "
        f"{summary['status']}, {summary['passed_cases']}/{summary['total_cases']} passed, "
        f"high_dependency_ratio={summary['high_dependency_ratio']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
