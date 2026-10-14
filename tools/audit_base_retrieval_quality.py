"""Offline base-retrieval quality audit.

This tool reads saved evidence diagnostics only. It audits dense/sparse/union
coverage gaps and does not call rag_query, Qdrant, embeddings, rerank, prompts,
anchors, or risk supplement rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_evidence_alignment import normalize_text, source_domain


VERSION = "0.4.7.4.3"

DEFAULT_COVERAGE_REPORT_PATH = Path("tests/evidence_coverage_report.json")
DEFAULT_TRIAGE_REPORT_PATH = Path("tests/evidence_coverage_triage_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/base_retrieval_quality_audit_report.json")

ROOT_BASE_RETRIEVAL_GAP = "base_retrieval_gap"
BASE_RETRIEVAL_THRESHOLD = 0.75
UNION_GAIN_EPSILON = 0.001

ISSUE_BASE_RETRIEVAL_REVIEW_NEEDED = "base_retrieval_review_needed"
ISSUE_DENSE_RETRIEVAL_GAP = "dense_retrieval_gap"
ISSUE_SPARSE_RETRIEVAL_GAP = "sparse_retrieval_gap"
ISSUE_UNION_RETRIEVAL_GAP = "union_retrieval_gap"
ISSUE_ZERO_BASE_RECALL = "zero_base_recall"
ISSUE_SPARSE_ONLY_SUPPORT = "sparse_only_support"
ISSUE_DENSE_ONLY_SUPPORT = "dense_only_support"
ISSUE_NO_UNION_GAIN = "no_union_gain"
ISSUE_ANCHOR_RESCUE_PATTERN = "anchor_rescue_pattern"
ISSUE_INDEX_OR_SOURCE_REVIEW = "index_or_source_coverage_review_candidate"
ISSUE_METADATA_OR_CHUNKING_REVIEW = "metadata_or_chunking_review_candidate"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def case_id(item: dict[str, Any]) -> str:
    return normalize_text(item.get("case_id") or item.get("id"))


def case_map(report: dict[str, Any], key: str = "cases") -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in report.get(key) or []
        if isinstance(item, dict) and case_id(item)
    }


def layer(case: dict[str, Any], layer_name: str) -> dict[str, Any]:
    value = (case.get("layer_coverage") or {}).get(layer_name)
    return value if isinstance(value, dict) else {}


def layer_ratio(case: dict[str, Any], layer_name: str) -> float:
    value = layer(case, layer_name).get("coverage_ratio")
    return float(value) if isinstance(value, (int, float)) else 1.0


def layer_expected(case: dict[str, Any], layer_name: str) -> int:
    value = layer(case, layer_name).get("expected_count")
    return int(value) if isinstance(value, int) else 0


def layer_missing(case: dict[str, Any], layer_name: str) -> list[dict[str, Any]]:
    return [
        item
        for item in layer(case, layer_name).get("missing") or []
        if isinstance(item, dict)
    ]


def article_key(item: dict[str, Any]) -> tuple[str, Any, str]:
    return (
        normalize_text(item.get("source") or item.get("law_name")),
        item.get("article_no"),
        normalize_text(item.get("section_no")),
    )


def unique_articles(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = article_key(item)
        if key in seen:
            continue
        seen.add(key)
        result.append({
            field: value
            for field, value in item.items()
            if field
            in {
                "source",
                "law_name",
                "article_no",
                "section_no",
                "citation",
                "category",
                "functional_type",
                "functional_type_confidence",
                "functional_type_matched_rule",
                "enrichment_status",
            }
            and value not in (None, "", [])
        })
    return result


def item_domain(item: dict[str, Any]) -> str | None:
    return source_domain(
        normalize_text(item.get("source") or item.get("law_name")),
        item.get("category"),
    )


def base_gap_case_ids(coverage_report: dict[str, Any], triage_report: dict[str, Any]) -> list[str]:
    ids = set()
    for item in triage_report.get("cases") or []:
        if ROOT_BASE_RETRIEVAL_GAP in (item.get("root_causes") or []):
            ids.add(case_id(item))
    for item in coverage_report.get("cases") or []:
        if layer_expected(item, "union") and layer_ratio(item, "union") < BASE_RETRIEVAL_THRESHOLD:
            ids.add(case_id(item))
    return sorted(value for value in ids if value)


def classify_case(
    case_id_value: str,
    coverage_case: dict[str, Any],
    triage_case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    triage_case = triage_case or {}
    dense = layer_ratio(coverage_case, "dense")
    sparse = layer_ratio(coverage_case, "sparse")
    union = layer_ratio(coverage_case, "union")
    anchor = layer_ratio(coverage_case, "anchor")
    final = layer_ratio(coverage_case, "final")
    expected = layer_expected(coverage_case, "union")
    best_base = max(dense, sparse)
    union_missing = unique_articles(layer_missing(coverage_case, "union"))

    issues = [ISSUE_BASE_RETRIEVAL_REVIEW_NEEDED]
    review_reasons = ["Base dense/sparse/union retrieval coverage is below diagnostic threshold."]

    if expected and dense < BASE_RETRIEVAL_THRESHOLD:
        issues.append(ISSUE_DENSE_RETRIEVAL_GAP)
        review_reasons.append("Dense retrieval does not cover enough expected evidence.")
    if expected and sparse < BASE_RETRIEVAL_THRESHOLD:
        issues.append(ISSUE_SPARSE_RETRIEVAL_GAP)
        review_reasons.append("Sparse retrieval does not cover enough expected evidence.")
    if expected and union < BASE_RETRIEVAL_THRESHOLD:
        issues.append(ISSUE_UNION_RETRIEVAL_GAP)
        review_reasons.append("Dense/sparse union still misses expected evidence.")
    if expected and union == 0:
        issues.append(ISSUE_ZERO_BASE_RECALL)
        review_reasons.append("No expected evidence is covered by base retrieval.")
    if dense == 0 and sparse > 0:
        issues.append(ISSUE_SPARSE_ONLY_SUPPORT)
        review_reasons.append("Only sparse retrieval contributes expected evidence before union.")
    if sparse == 0 and dense > 0:
        issues.append(ISSUE_DENSE_ONLY_SUPPORT)
        review_reasons.append("Only dense retrieval contributes expected evidence before union.")
    if expected and union < BASE_RETRIEVAL_THRESHOLD and union <= best_base + UNION_GAIN_EPSILON:
        issues.append(ISSUE_NO_UNION_GAIN)
        review_reasons.append("Union coverage does not materially improve over the best single base retriever.")
    if anchor > union:
        issues.append(ISSUE_ANCHOR_RESCUE_PATTERN)
        review_reasons.append("Expected evidence appears after anchor layer, suggesting base retrieval undercoverage.")
    if union < BASE_RETRIEVAL_THRESHOLD and anchor >= BASE_RETRIEVAL_THRESHOLD:
        issues.append(ISSUE_METADATA_OR_CHUNKING_REVIEW)
        review_reasons.append("Anchor can recover evidence that base retrieval misses; review metadata, chunking, and query lexical coverage.")
    if union < BASE_RETRIEVAL_THRESHOLD and anchor < BASE_RETRIEVAL_THRESHOLD:
        issues.append(ISSUE_INDEX_OR_SOURCE_REVIEW)
        review_reasons.append("Expected evidence remains missing after anchor layer; review source/index coverage before tuning retrieval.")

    missing_domains = sorted({domain for domain in (item_domain(item) for item in union_missing) if domain})
    missing_sources = sorted({
        normalize_text(item.get("source") or item.get("law_name"))
        for item in union_missing
        if normalize_text(item.get("source") or item.get("law_name"))
    })
    missing_functional_types = Counter(
        normalize_text(item.get("functional_type") or "unknown")
        for item in union_missing
    )

    priority = "high" if (
        coverage_case.get("risk_level") == "high"
        or union == 0
        or triage_case.get("triage_status") == "high_priority_review"
    ) else "normal"

    return {
        "case_id": case_id_value,
        "audit_status": "review",
        "priority": priority,
        "risk_level": coverage_case.get("risk_level"),
        "expected_domains": coverage_case.get("expected_domains") or [],
        "detected_issues": list(dict.fromkeys(issues)),
        "review_reasons": list(dict.fromkeys(review_reasons)),
        "root_causes": triage_case.get("root_causes") or [],
        "base_layer_coverage": {
            "dense": dense,
            "sparse": sparse,
            "union": union,
            "anchor": anchor,
            "final": final,
            "expected": expected,
            "union_gain_over_best_single": round(union - best_base, 3),
            "anchor_gain_over_union": round(anchor - union, 3),
        },
        "missing_union_evidence": union_missing,
        "missing_union_domains": missing_domains,
        "missing_union_sources": missing_sources,
        "missing_union_functional_type_counts": dict(sorted(missing_functional_types.items())),
        "reviewer_fields": {
            "retrieval_root_decision": "",
            "metadata_or_chunking_notes": "",
            "source_index_notes": "",
            "follow_up_action": "",
        },
    }


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    layer_gap_summary = Counter()
    source_summary = Counter()
    function_summary = Counter()
    high_risk = []

    for case in cases:
        issues = set(case.get("detected_issues") or [])
        for issue in issues:
            issue_counts[issue] += 1
        for layer_name, issue in (
            ("dense", ISSUE_DENSE_RETRIEVAL_GAP),
            ("sparse", ISSUE_SPARSE_RETRIEVAL_GAP),
            ("union", ISSUE_UNION_RETRIEVAL_GAP),
        ):
            if issue in issues:
                layer_gap_summary[f"{layer_name}_gap_cases"] += 1
        for domain in case.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["review_cases"] += 1
            if case.get("priority") == "high":
                domain_summary[domain]["high_priority"] += 1
        for source in case.get("missing_union_sources") or []:
            source_summary[source] += 1
        for functional_type, count in (case.get("missing_union_functional_type_counts") or {}).items():
            function_summary[functional_type] += int(count)
        if case.get("priority") == "high":
            high_risk.append({
                "case_id": case.get("case_id"),
                "risk_level": case.get("risk_level"),
                "detected_issues": case.get("detected_issues") or [],
                "review_reasons": case.get("review_reasons") or [],
            })

    return {
        "total_base_gap_cases": len(cases),
        "high_priority_review_cases": len(high_risk),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "layer_gap_summary": dict(sorted(layer_gap_summary.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "missing_union_source_summary": dict(sorted(source_summary.items())),
        "missing_union_functional_type_summary": dict(sorted(function_summary.items())),
        "high_risk_manual_review": high_risk,
    }


def build_report(
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    triage_report_path: Path = DEFAULT_TRIAGE_REPORT_PATH,
) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    triage_report = load_json(triage_report_path)
    coverage_by_case = case_map(coverage_report)
    triage_by_case = case_map(triage_report)
    cases = [
        classify_case(case_id_value, coverage_by_case.get(case_id_value) or {}, triage_by_case.get(case_id_value))
        for case_id_value in base_gap_case_ids(coverage_report, triage_report)
    ]
    return {
        "version": VERSION,
        "scope": "offline base retrieval quality audit",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
            "triage_report": str(triage_report_path),
            "triage_report_version": triage_report.get("version"),
            "base_retrieval_threshold": BASE_RETRIEVAL_THRESHOLD,
        },
        "summary": build_summary(cases),
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit saved dense/sparse/union base retrieval quality.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--triage-report", type=Path, default=DEFAULT_TRIAGE_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.coverage_report, args.triage_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Base retrieval quality audit completed: "
        f"{summary['total_base_gap_cases']} base-gap cases, "
        f"{summary['high_priority_review_cases']} high-priority review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
