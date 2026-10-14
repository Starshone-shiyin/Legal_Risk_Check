"""Offline anchor-dependency audit.

This tool reads saved evidence diagnostics only. It separates healthy anchor
support from anchor patterns that mask weak base retrieval. It does not add or
modify anchors, retrieval, rerank, prompts, risk rules, or eval cases.
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


VERSION = "0.4.7.4.4"

DEFAULT_COVERAGE_REPORT_PATH = Path("tests/evidence_coverage_report.json")
DEFAULT_TRIAGE_REPORT_PATH = Path("tests/evidence_coverage_triage_report.json")
DEFAULT_BASE_AUDIT_REPORT_PATH = Path("tests/base_retrieval_quality_audit_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/anchor_dependency_audit_report.json")

ROOT_ANCHOR_DEPENDENCY = "anchor_dependency"
ROOT_BASE_RETRIEVAL_GAP = "base_retrieval_gap"
ISSUE_ANCHOR_DEPENDENT_COVERAGE = "anchor_dependent_coverage"

BASE_THRESHOLD = 0.75
ANCHOR_GAIN_REVIEW_THRESHOLD = 0.5

ISSUE_ANCHOR_DEPENDENCY_REVIEW_NEEDED = "anchor_dependency_review_needed"
ISSUE_HEALTHY_ANCHOR_SUPPORT_CANDIDATE = "healthy_anchor_support_candidate"
ISSUE_ANCHOR_MASKING_BASE_RETRIEVAL_GAP = "anchor_masking_base_retrieval_gap"
ISSUE_ANCHOR_RESCUE_SUCCESS = "anchor_rescue_success"
ISSUE_PARTIAL_ANCHOR_RECOVERY = "partial_anchor_recovery"
ISSUE_ZERO_BASE_TO_ANCHOR_RECOVERY = "zero_base_to_anchor_recovery"
ISSUE_HIGH_ANCHOR_GAIN = "high_anchor_gain"
ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST = "anchor_supported_but_final_lost"
ISSUE_METADATA_OR_CHUNKING_REVIEW = "metadata_or_chunking_review_candidate"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def case_id(item: dict[str, Any]) -> str:
    return normalize_text(item.get("case_id") or item.get("id"))


def case_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in report.get("cases") or []
        if isinstance(item, dict) and case_id(item)
    }


def layer(case: dict[str, Any], layer_name: str) -> dict[str, Any]:
    value = (case.get("layer_coverage") or {}).get(layer_name)
    return value if isinstance(value, dict) else {}


def layer_ratio(case: dict[str, Any], layer_name: str) -> float:
    value = layer(case, layer_name).get("coverage_ratio")
    return float(value) if isinstance(value, (int, float)) else 1.0


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


def anchor_case_ids(coverage_report: dict[str, Any], triage_report: dict[str, Any]) -> list[str]:
    ids = set()
    for item in coverage_report.get("cases") or []:
        if ISSUE_ANCHOR_DEPENDENT_COVERAGE in (item.get("detected_issues") or []):
            ids.add(case_id(item))
        elif layer_ratio(item, "anchor") > layer_ratio(item, "union"):
            ids.add(case_id(item))
    for item in triage_report.get("cases") or []:
        if ROOT_ANCHOR_DEPENDENCY in (item.get("root_causes") or []):
            ids.add(case_id(item))
    return sorted(value for value in ids if value)


def classify_case(
    case_id_value: str,
    coverage_case: dict[str, Any],
    triage_case: dict[str, Any] | None = None,
    base_case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    triage_case = triage_case or {}
    base_case = base_case or {}
    dense = layer_ratio(coverage_case, "dense")
    sparse = layer_ratio(coverage_case, "sparse")
    union = layer_ratio(coverage_case, "union")
    anchor = layer_ratio(coverage_case, "anchor")
    rerank_input = layer_ratio(coverage_case, "rerank_input")
    final = layer_ratio(coverage_case, "final")
    anchor_gain = round(anchor - union, 3)
    final_loss = round(anchor - final, 3)
    root_causes = triage_case.get("root_causes") or []
    base_issues = base_case.get("detected_issues") or []

    issues = [ISSUE_ANCHOR_DEPENDENCY_REVIEW_NEEDED]
    review_reasons = ["Expected evidence coverage improves after anchor layer."]

    if union >= BASE_THRESHOLD and anchor > union:
        issues.append(ISSUE_HEALTHY_ANCHOR_SUPPORT_CANDIDATE)
        review_reasons.append("Base retrieval is already above threshold; anchor appears supplemental.")
    if union < BASE_THRESHOLD:
        issues.append(ISSUE_ANCHOR_MASKING_BASE_RETRIEVAL_GAP)
        review_reasons.append("Anchor improves coverage from a weak base retrieval layer.")
    if union < BASE_THRESHOLD and anchor >= BASE_THRESHOLD:
        issues.append(ISSUE_ANCHOR_RESCUE_SUCCESS)
        review_reasons.append("Anchor raises expected evidence coverage above the review threshold.")
    if union < BASE_THRESHOLD and anchor < BASE_THRESHOLD:
        issues.append(ISSUE_PARTIAL_ANCHOR_RECOVERY)
        review_reasons.append("Anchor improves coverage but remains below the review threshold.")
    if union == 0 and anchor >= BASE_THRESHOLD:
        issues.append(ISSUE_ZERO_BASE_TO_ANCHOR_RECOVERY)
        review_reasons.append("No base expected evidence was covered before anchor, but anchor recovered coverage.")
    if anchor_gain >= ANCHOR_GAIN_REVIEW_THRESHOLD:
        issues.append(ISSUE_HIGH_ANCHOR_GAIN)
        review_reasons.append("Anchor contributes a large coverage increase over union retrieval.")
    if anchor >= BASE_THRESHOLD and final < anchor:
        issues.append(ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST)
        review_reasons.append("Evidence recovered by anchor is not fully preserved in final evidence.")
    if (
        ISSUE_ANCHOR_MASKING_BASE_RETRIEVAL_GAP in issues
        and (
            ROOT_BASE_RETRIEVAL_GAP in root_causes
            or "metadata_or_chunking_review_candidate" in base_issues
            or "anchor_rescue_pattern" in base_issues
        )
    ):
        issues.append(ISSUE_METADATA_OR_CHUNKING_REVIEW)
        review_reasons.append("Base audit points to metadata, chunking, or lexical coverage review before anchor changes.")

    anchor_missing = unique_articles(layer_missing(coverage_case, "anchor"))
    union_missing = unique_articles(layer_missing(coverage_case, "union"))
    missing_domains = sorted({domain for domain in (item_domain(item) for item in union_missing) if domain})
    missing_sources = sorted({
        normalize_text(item.get("source") or item.get("law_name"))
        for item in union_missing
        if normalize_text(item.get("source") or item.get("law_name"))
    })

    priority = "high" if (
        coverage_case.get("risk_level") == "high"
        or ISSUE_ANCHOR_MASKING_BASE_RETRIEVAL_GAP in issues
        or ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST in issues
    ) else "normal"

    return {
        "case_id": case_id_value,
        "audit_status": "review",
        "priority": priority,
        "risk_level": coverage_case.get("risk_level"),
        "expected_domains": coverage_case.get("expected_domains") or [],
        "detected_issues": list(dict.fromkeys(issues)),
        "review_reasons": list(dict.fromkeys(review_reasons)),
        "root_causes": root_causes,
        "anchor_flow": {
            "dense": dense,
            "sparse": sparse,
            "union": union,
            "anchor": anchor,
            "rerank_input": rerank_input,
            "final": final,
            "anchor_gain_over_union": anchor_gain,
            "final_loss_after_anchor": final_loss,
        },
        "union_missing_evidence": union_missing,
        "anchor_missing_evidence": anchor_missing,
        "union_missing_domains": missing_domains,
        "union_missing_sources": missing_sources,
        "reviewer_fields": {
            "anchor_dependency_decision": "",
            "base_retrieval_follow_up": "",
            "anchor_rule_follow_up": "",
            "notes": "",
        },
    }


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    source_summary = Counter()
    high_risk = []
    gain_buckets = Counter()

    for case in cases:
        for issue in case.get("detected_issues") or []:
            issue_counts[issue] += 1
        for domain in case.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["review_cases"] += 1
            if case.get("priority") == "high":
                domain_summary[domain]["high_priority"] += 1
        for source in case.get("union_missing_sources") or []:
            source_summary[source] += 1
        gain = float((case.get("anchor_flow") or {}).get("anchor_gain_over_union") or 0)
        if gain >= 1:
            gain_buckets["gain_1_0"] += 1
        elif gain >= 0.5:
            gain_buckets["gain_0_5_to_0_999"] += 1
        elif gain > 0:
            gain_buckets["gain_0_to_0_499"] += 1
        if case.get("priority") == "high":
            high_risk.append({
                "case_id": case.get("case_id"),
                "risk_level": case.get("risk_level"),
                "detected_issues": case.get("detected_issues") or [],
                "review_reasons": case.get("review_reasons") or [],
            })

    return {
        "total_anchor_dependency_cases": len(cases),
        "high_priority_review_cases": len(high_risk),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "anchor_gain_summary": dict(sorted(gain_buckets.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "union_missing_source_summary": dict(sorted(source_summary.items())),
        "high_risk_manual_review": high_risk,
    }


def build_report(
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    triage_report_path: Path = DEFAULT_TRIAGE_REPORT_PATH,
    base_audit_report_path: Path = DEFAULT_BASE_AUDIT_REPORT_PATH,
) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    triage_report = load_json(triage_report_path)
    base_audit_report = load_json(base_audit_report_path)
    coverage_by_case = case_map(coverage_report)
    triage_by_case = case_map(triage_report)
    base_by_case = case_map(base_audit_report)

    cases = [
        classify_case(
            case_id_value,
            coverage_by_case.get(case_id_value) or {},
            triage_by_case.get(case_id_value),
            base_by_case.get(case_id_value),
        )
        for case_id_value in anchor_case_ids(coverage_report, triage_report)
    ]

    return {
        "version": VERSION,
        "scope": "offline anchor dependency audit",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
            "triage_report": str(triage_report_path),
            "triage_report_version": triage_report.get("version"),
            "base_retrieval_audit_report": str(base_audit_report_path),
            "base_retrieval_audit_report_version": base_audit_report.get("version"),
        },
        "summary": build_summary(cases),
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit saved anchor dependency diagnostics.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--triage-report", type=Path, default=DEFAULT_TRIAGE_REPORT_PATH)
    parser.add_argument("--base-audit-report", type=Path, default=DEFAULT_BASE_AUDIT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.coverage_report, args.triage_report, args.base_audit_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Anchor dependency audit completed: "
        f"{summary['total_anchor_dependency_cases']} anchor-dependency cases, "
        f"{summary['high_priority_review_cases']} high-priority review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
