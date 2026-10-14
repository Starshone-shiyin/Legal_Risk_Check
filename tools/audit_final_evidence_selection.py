"""Offline final-evidence selection audit.

This tool reads saved evidence diagnostics only. It audits evidence coverage
loss from rerank_input to final evidence and does not modify rerank, prompts,
final truncation, anchors, risk rules, or eval cases.
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


VERSION = "0.4.7.4.5"

DEFAULT_COVERAGE_REPORT_PATH = Path("tests/evidence_coverage_report.json")
DEFAULT_TRIAGE_REPORT_PATH = Path("tests/evidence_coverage_triage_report.json")
DEFAULT_ANCHOR_AUDIT_REPORT_PATH = Path("tests/anchor_dependency_audit_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/final_evidence_selection_audit_report.json")

ROOT_FINAL_SELECTION_LOSS = "final_selection_loss"
ISSUE_LAYER_COVERAGE_REGRESSION = "layer_coverage_regression"

ISSUE_FINAL_SELECTION_REVIEW_NEEDED = "final_selection_review_needed"
ISSUE_RERANK_INPUT_TO_FINAL_LOSS = "rerank_input_to_final_loss"
ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST = "anchor_supported_but_final_lost"
ISSUE_PRIMARY_EVIDENCE_LOST = "primary_evidence_lost"
ISSUE_SCENARIO_CORE_LOST = "scenario_core_lost"
ISSUE_OPERATIVE_EVIDENCE_LOST = "operative_evidence_lost"
ISSUE_LIABILITY_EVIDENCE_LOST = "liability_evidence_lost"
ISSUE_LOW_FINAL_COVERAGE_AFTER_SELECTION = "low_final_coverage_after_selection"

OPERATIVE_TYPES = {"operative_rule", "procedural", "rights_remedy", "technical_standard"}


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


def function_counts(items: list[dict[str, Any]]) -> Counter:
    return Counter(normalize_text(item.get("functional_type") or "unknown") for item in items)


def selection_loss_case_ids(coverage_report: dict[str, Any], triage_report: dict[str, Any]) -> list[str]:
    ids = set()
    for item in coverage_report.get("cases") or []:
        if ISSUE_LAYER_COVERAGE_REGRESSION in (item.get("detected_issues") or []):
            ids.add(case_id(item))
        elif layer_ratio(item, "rerank_input") > layer_ratio(item, "final"):
            ids.add(case_id(item))
    for item in triage_report.get("cases") or []:
        if ROOT_FINAL_SELECTION_LOSS in (item.get("root_causes") or []):
            ids.add(case_id(item))
    return sorted(value for value in ids if value)


def classify_case(
    case_id_value: str,
    coverage_case: dict[str, Any],
    triage_case: dict[str, Any] | None = None,
    anchor_case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    triage_case = triage_case or {}
    anchor_case = anchor_case or {}
    rerank_input = layer_ratio(coverage_case, "rerank_input")
    final = layer_ratio(coverage_case, "final")
    anchor = layer_ratio(coverage_case, "anchor")
    loss = round(rerank_input - final, 3)
    final_expected_missing = unique_articles((coverage_case.get("final_evidence_coverage") or {}).get("missing") or [])
    scenario_core_missing = unique_articles((coverage_case.get("scenario_core_coverage") or {}).get("missing") or [])
    final_layer_missing = unique_articles(layer_missing(coverage_case, "final"))
    lost_items = final_expected_missing or final_layer_missing
    lost_functions = function_counts(lost_items)

    issues = [ISSUE_FINAL_SELECTION_REVIEW_NEEDED, ISSUE_RERANK_INPUT_TO_FINAL_LOSS]
    review_reasons = ["Expected evidence coverage decreases from rerank_input to final evidence."]

    anchor_issues = set(anchor_case.get("detected_issues") or [])
    if anchor >= rerank_input and (
        "anchor_supported_but_final_lost" in anchor_issues
        or "anchor_rescue_success" in anchor_issues
    ):
        issues.append(ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST)
        review_reasons.append("Evidence recovered before or at anchor/rerank_input is not fully preserved in final evidence.")
    if final_expected_missing:
        issues.append(ISSUE_PRIMARY_EVIDENCE_LOST)
        review_reasons.append("Final evidence misses primary expected evidence present earlier in the pipeline.")
    if scenario_core_missing:
        issues.append(ISSUE_SCENARIO_CORE_LOST)
        review_reasons.append("Final evidence misses scenario core evidence.")
    if set(lost_functions) & OPERATIVE_TYPES:
        issues.append(ISSUE_OPERATIVE_EVIDENCE_LOST)
        review_reasons.append("Lost evidence includes operative, procedural, rights, or technical support.")
    if lost_functions.get("liability"):
        issues.append(ISSUE_LIABILITY_EVIDENCE_LOST)
        review_reasons.append("Lost evidence includes liability or consequence support.")
    if final < 0.75:
        issues.append(ISSUE_LOW_FINAL_COVERAGE_AFTER_SELECTION)
        review_reasons.append("Final evidence coverage falls below the diagnostic threshold after selection.")

    lost_domains = sorted({domain for domain in (item_domain(item) for item in lost_items) if domain})
    lost_sources = sorted({
        normalize_text(item.get("source") or item.get("law_name"))
        for item in lost_items
        if normalize_text(item.get("source") or item.get("law_name"))
    })

    priority = "high" if (
        coverage_case.get("risk_level") == "high"
        or ISSUE_LOW_FINAL_COVERAGE_AFTER_SELECTION in issues
        or ISSUE_LIABILITY_EVIDENCE_LOST in issues
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
        "selection_flow": {
            "anchor": anchor,
            "rerank_input": rerank_input,
            "final": final,
            "rerank_input_to_final_delta": round(final - rerank_input, 3),
            "lost_coverage_ratio": loss,
        },
        "lost_evidence": lost_items,
        "lost_evidence_domains": lost_domains,
        "lost_evidence_sources": lost_sources,
        "lost_functional_type_counts": dict(sorted(lost_functions.items())),
        "missing_final_expected": final_expected_missing,
        "missing_scenario_core": scenario_core_missing,
        "reviewer_fields": {
            "selection_loss_decision": "",
            "final_evidence_policy_notes": "",
            "follow_up_action": "",
            "notes": "",
        },
    }


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    lost_source_summary = Counter()
    lost_function_summary = Counter()
    loss_buckets = Counter()
    high_risk = []

    for case in cases:
        for issue in case.get("detected_issues") or []:
            issue_counts[issue] += 1
        for domain in case.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["review_cases"] += 1
            if case.get("priority") == "high":
                domain_summary[domain]["high_priority"] += 1
        for source in case.get("lost_evidence_sources") or []:
            lost_source_summary[source] += 1
        for functional_type, count in (case.get("lost_functional_type_counts") or {}).items():
            lost_function_summary[functional_type] += int(count)
        loss = float((case.get("selection_flow") or {}).get("lost_coverage_ratio") or 0)
        if loss >= 0.5:
            loss_buckets["loss_0_5_or_more"] += 1
        elif loss >= 0.25:
            loss_buckets["loss_0_25_to_0_499"] += 1
        elif loss > 0:
            loss_buckets["loss_below_0_25"] += 1
        if case.get("priority") == "high":
            high_risk.append({
                "case_id": case.get("case_id"),
                "risk_level": case.get("risk_level"),
                "detected_issues": case.get("detected_issues") or [],
                "review_reasons": case.get("review_reasons") or [],
            })

    return {
        "total_final_selection_loss_cases": len(cases),
        "high_priority_review_cases": len(high_risk),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "selection_loss_summary": dict(sorted(loss_buckets.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "lost_evidence_source_summary": dict(sorted(lost_source_summary.items())),
        "lost_functional_type_summary": dict(sorted(lost_function_summary.items())),
        "high_risk_manual_review": high_risk,
    }


def build_report(
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    triage_report_path: Path = DEFAULT_TRIAGE_REPORT_PATH,
    anchor_audit_report_path: Path = DEFAULT_ANCHOR_AUDIT_REPORT_PATH,
) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    triage_report = load_json(triage_report_path)
    anchor_audit_report = load_json(anchor_audit_report_path)
    coverage_by_case = case_map(coverage_report)
    triage_by_case = case_map(triage_report)
    anchor_by_case = case_map(anchor_audit_report)

    cases = [
        classify_case(
            case_id_value,
            coverage_by_case.get(case_id_value) or {},
            triage_by_case.get(case_id_value),
            anchor_by_case.get(case_id_value),
        )
        for case_id_value in selection_loss_case_ids(coverage_report, triage_report)
    ]

    return {
        "version": VERSION,
        "scope": "offline final evidence selection audit",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
            "triage_report": str(triage_report_path),
            "triage_report_version": triage_report.get("version"),
            "anchor_dependency_audit_report": str(anchor_audit_report_path),
            "anchor_dependency_audit_report_version": anchor_audit_report.get("version"),
        },
        "summary": build_summary(cases),
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit saved final evidence selection loss diagnostics.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--triage-report", type=Path, default=DEFAULT_TRIAGE_REPORT_PATH)
    parser.add_argument("--anchor-audit-report", type=Path, default=DEFAULT_ANCHOR_AUDIT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.coverage_report, args.triage_report, args.anchor_audit_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Final evidence selection audit completed: "
        f"{summary['total_final_selection_loss_cases']} selection-loss cases, "
        f"{summary['high_priority_review_cases']} high-priority review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
