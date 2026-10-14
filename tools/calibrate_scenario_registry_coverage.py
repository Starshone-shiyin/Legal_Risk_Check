"""Offline scenario-registry calibration diagnostics.

This tool reads existing evidence coverage and manual review artifacts only.
It does not edit the scenario registry, eval cases, retrieval, rerank, prompts,
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

from tools.check_evidence_alignment import (
    evidence_matches_expected,
    normalize_text,
    source_domain,
)


VERSION = "0.4.7.4.2"

DEFAULT_COVERAGE_REPORT_PATH = Path("tests/evidence_coverage_report.json")
DEFAULT_MANUAL_REVIEW_DATASET_PATH = Path("tests/evidence_manual_review_dataset.json")
DEFAULT_SCENARIO_REGISTRY_PATH = Path("config/scenario_registry.json")
DEFAULT_OUTPUT_PATH = Path("tests/scenario_registry_calibration_report.json")

ROOT_SCENARIO_CORE_GAP = "scenario_core_gap"
ROOT_FINAL_PRIMARY_GAP = "final_primary_gap"
ROOT_LOW_FINAL_COVERAGE = "low_final_coverage"

ISSUE_REGISTRY_CORE_REVIEW_NEEDED = "registry_core_review_needed"
ISSUE_CORE_MISSING_FROM_FINAL = "core_missing_from_final_evidence"
ISSUE_REGISTRY_SCOPE_REVIEW = "registry_core_scope_review_candidate"
ISSUE_EVIDENCE_CHAIN_GAP = "evidence_chain_gap_candidate"
ISSUE_FINAL_PRIMARY_OVERLAP = "final_primary_gap_overlap"
ISSUE_CROSS_DOMAIN_CORE_GAP = "cross_domain_core_gap"
ISSUE_DEFINITION_CORE_CANDIDATE = "definition_core_candidate"
ISSUE_NON_OPERATIVE_CORE_CANDIDATE = "non_operative_core_candidate"
ISSUE_NO_SCENARIO_MAPPING = "missing_scenario_mapping"

OPERATIVE_TYPES = {
    "operative_rule",
    "procedural",
    "liability",
    "rights_remedy",
    "technical_standard",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def case_id(item: dict[str, Any]) -> str:
    return normalize_text(item.get("case_id") or item.get("id"))


def article_key(item: dict[str, Any]) -> tuple[str, Any, str]:
    return (
        normalize_text(item.get("source") or item.get("law_name")),
        item.get("article_no"),
        normalize_text(item.get("section_no")),
    )


def item_domain(item: dict[str, Any]) -> str | None:
    return source_domain(
        normalize_text(item.get("source") or item.get("law_name")),
        item.get("category"),
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
            key: value
            for key, value in item.items()
            if key
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


def build_case_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in report.get("cases") or []
        if isinstance(item, dict) and case_id(item)
    }


def build_review_map(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in dataset.get("review_items") or []
        if isinstance(item, dict) and case_id(item)
    }


def build_scenario_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for scenario in registry.get("scenarios") or []:
        if not isinstance(scenario, dict):
            continue
        for eval_case_id in scenario.get("eval_case_ids") or []:
            result[normalize_text(eval_case_id)] = scenario
    return result


def scenario_gap_case_ids(
    coverage_report: dict[str, Any],
    manual_review_dataset: dict[str, Any],
) -> list[str]:
    ids = set()
    for item in coverage_report.get("cases") or []:
        if ROOT_SCENARIO_CORE_GAP in (item.get("detected_issues") or []):
            ids.add(case_id(item))
    for item in manual_review_dataset.get("review_items") or []:
        if ROOT_SCENARIO_CORE_GAP in (item.get("root_causes") or []):
            ids.add(case_id(item))
    return sorted(value for value in ids if value)


def missing_core_domains(missing_core: list[dict[str, Any]]) -> list[str]:
    return sorted({domain for domain in (item_domain(item) for item in missing_core) if domain})


def final_domains(final_evidence: list[dict[str, Any]]) -> list[str]:
    return sorted({domain for domain in (item_domain(item) for item in final_evidence) if domain})


def final_core_matches(
    final_evidence: list[dict[str, Any]],
    scenario_core: list[dict[str, Any]],
) -> int:
    return sum(
        1
        for expected in scenario_core
        if any(evidence_matches_expected(evidence, expected) for evidence in final_evidence)
    )


def functional_type_counts(items: list[dict[str, Any]]) -> Counter:
    return Counter(
        normalize_text(item.get("functional_type") or "unknown")
        for item in items
    )


def classify_case(
    case_id_value: str,
    coverage_case: dict[str, Any],
    review_item: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
) -> dict[str, Any]:
    review_item = review_item or {}
    scenario_core_coverage = coverage_case.get("scenario_core_coverage") or {}
    final_evidence_coverage = coverage_case.get("final_evidence_coverage") or {}
    missing_core = (
        review_item.get("missing_scenario_core")
        or scenario_core_coverage.get("missing")
        or []
    )
    final_evidence = review_item.get("final_evidence") or coverage_case.get("final_evidence") or []
    missing_final = (
        review_item.get("missing_final_expected")
        or final_evidence_coverage.get("missing")
        or []
    )
    root_causes = review_item.get("root_causes") or []
    detected_issues = coverage_case.get("detected_issues") or []

    scenario_core = [item for item in (scenario or {}).get("core_articles") or [] if isinstance(item, dict)]
    final_core_match_count = final_core_matches(final_evidence, scenario_core)
    missing_domains = missing_core_domains(missing_core)
    evidence_domains = final_domains(final_evidence)
    missing_types = functional_type_counts(missing_core)

    issues = [ISSUE_REGISTRY_CORE_REVIEW_NEEDED]
    review_reasons = ["Scenario core gap should be manually calibrated before registry edits."]

    if not scenario:
        issues.append(ISSUE_NO_SCENARIO_MAPPING)
        review_reasons.append("Case has scenario_core_gap but no scenario registry mapping was found.")

    if missing_core:
        issues.append(ISSUE_CORE_MISSING_FROM_FINAL)
        review_reasons.append("One or more scenario core articles are absent from final evidence.")

    final_ratio = float(final_evidence_coverage.get("coverage_ratio") or 0)
    scenario_ratio = float(scenario_core_coverage.get("coverage_ratio") or 0)
    if final_ratio >= 1.0 and scenario_ratio < 1.0:
        issues.append(ISSUE_REGISTRY_SCOPE_REVIEW)
        review_reasons.append("Final expected evidence is covered, but scenario core evidence is broader than final evidence.")

    if final_ratio < 1.0 or ROOT_FINAL_PRIMARY_GAP in root_causes or ROOT_FINAL_PRIMARY_GAP in detected_issues:
        issues.append(ISSUE_EVIDENCE_CHAIN_GAP)
        issues.append(ISSUE_FINAL_PRIMARY_OVERLAP)
        review_reasons.append("Scenario core gap overlaps with final primary evidence loss.")

    if missing_domains and evidence_domains and not set(missing_domains).issubset(set(evidence_domains)):
        issues.append(ISSUE_CROSS_DOMAIN_CORE_GAP)
        review_reasons.append("Missing scenario core domains are not represented in final evidence.")

    if missing_core and set(missing_types) == {"definition"}:
        issues.append(ISSUE_DEFINITION_CORE_CANDIDATE)
        review_reasons.append("Missing scenario core articles are definition-only candidates; review whether they belong in core set.")
    elif missing_core and not (set(missing_types) & OPERATIVE_TYPES):
        issues.append(ISSUE_NON_OPERATIVE_CORE_CANDIDATE)
        review_reasons.append("Missing scenario core articles lack operative/procedural/liability support signals.")

    priority = "high" if (
        coverage_case.get("risk_level") == "high"
        or ROOT_LOW_FINAL_COVERAGE in root_causes
        or final_ratio < 0.75
    ) else "normal"

    return {
        "case_id": case_id_value,
        "calibration_status": "review",
        "priority": priority,
        "scenario_id": (scenario or {}).get("scenario_id"),
        "domain": (scenario or {}).get("domain") or (coverage_case.get("expected_domains") or ["unknown"])[0],
        "risk_level": coverage_case.get("risk_level"),
        "detected_issues": list(dict.fromkeys(issues)),
        "review_reasons": list(dict.fromkeys(review_reasons)),
        "root_causes": root_causes,
        "coverage_flow": review_item.get("coverage_flow") or {},
        "scenario_core_coverage": {
            "matched": scenario_core_coverage.get("matched", 0),
            "expected": scenario_core_coverage.get("expected", 0),
            "coverage_ratio": scenario_ratio,
            "final_core_match_count": final_core_match_count,
        },
        "final_evidence_coverage": {
            "matched": final_evidence_coverage.get("matched", 0),
            "expected": final_evidence_coverage.get("expected", 0),
            "coverage_ratio": final_ratio,
        },
        "missing_core_domains": missing_domains,
        "final_evidence_domains": evidence_domains,
        "missing_core_functional_type_counts": dict(sorted(missing_types.items())),
        "missing_scenario_core": unique_articles(missing_core),
        "missing_final_expected": unique_articles(missing_final),
        "final_evidence": unique_articles(final_evidence),
        "reviewer_fields": {
            "registry_decision": "",
            "confirmed_core_articles": [],
            "core_articles_to_review": [],
            "notes": "",
        },
    }


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    scenario_summary: dict[str, Counter] = defaultdict(Counter)
    source_summary = Counter()
    function_summary = Counter()
    high_risk = []

    for case in cases:
        for issue in case.get("detected_issues") or []:
            issue_counts[issue] += 1
        domain = case.get("domain") or "unknown"
        domain_summary[domain]["review_cases"] += 1
        if case.get("priority") == "high":
            domain_summary[domain]["high_priority"] += 1
        scenario_id = case.get("scenario_id") or "unknown"
        scenario_summary[scenario_id]["review_cases"] += 1
        for item in case.get("missing_scenario_core") or []:
            source_summary[normalize_text(item.get("source") or item.get("law_name") or "unknown")] += 1
        for functional_type, count in (case.get("missing_core_functional_type_counts") or {}).items():
            function_summary[functional_type] += int(count)
        if case.get("priority") == "high":
            high_risk.append({
                "case_id": case.get("case_id"),
                "scenario_id": case.get("scenario_id"),
                "domain": domain,
                "detected_issues": case.get("detected_issues") or [],
                "review_reasons": case.get("review_reasons") or [],
            })

    return {
        "total_scenario_gap_cases": len(cases),
        "high_priority_review_cases": len(high_risk),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "per_scenario_summary": {
            scenario_id: dict(counts)
            for scenario_id, counts in sorted(scenario_summary.items())
        },
        "missing_core_source_summary": dict(sorted(source_summary.items())),
        "missing_core_functional_type_summary": dict(sorted(function_summary.items())),
        "high_risk_manual_review": high_risk,
    }


def build_report(
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    manual_review_dataset_path: Path = DEFAULT_MANUAL_REVIEW_DATASET_PATH,
    scenario_registry_path: Path = DEFAULT_SCENARIO_REGISTRY_PATH,
) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    manual_review_dataset = load_json(manual_review_dataset_path)
    scenario_registry = load_json(scenario_registry_path)
    coverage_by_case = build_case_map(coverage_report)
    review_by_case = build_review_map(manual_review_dataset)
    scenario_by_case = build_scenario_map(scenario_registry)

    cases = []
    for case_id_value in scenario_gap_case_ids(coverage_report, manual_review_dataset):
        coverage_case = coverage_by_case.get(case_id_value) or {}
        cases.append(
            classify_case(
                case_id_value,
                coverage_case,
                review_by_case.get(case_id_value),
                scenario_by_case.get(case_id_value),
            )
        )

    return {
        "version": VERSION,
        "scope": "offline scenario registry calibration diagnostics",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
            "manual_review_dataset": str(manual_review_dataset_path),
            "manual_review_dataset_version": manual_review_dataset.get("version"),
            "scenario_registry": str(scenario_registry_path),
            "scenario_registry_version": scenario_registry.get("version"),
        },
        "summary": build_summary(cases),
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate scenario registry core coverage diagnostics.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--manual-review-dataset", type=Path, default=DEFAULT_MANUAL_REVIEW_DATASET_PATH)
    parser.add_argument("--scenario-registry", type=Path, default=DEFAULT_SCENARIO_REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        args.coverage_report,
        args.manual_review_dataset,
        args.scenario_registry,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Scenario registry calibration completed: "
        f"{summary['total_scenario_gap_cases']} scenario-gap cases, "
        f"{summary['high_priority_review_cases']} high-priority review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
