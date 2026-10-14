"""Offline evidence-alignment diagnostics for saved RAG evaluation reports.

This tool reads existing report artifacts only. It does not call rag_query,
does not modify retrieval/rerank/prompt behavior, and does not tune any case.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.legal_functional_typing import (
    classify_evidence_function,
    has_operative_support,
)
from tools._shared.layout import legacy_report_path

DEFAULT_RAG_REPORT_PATH = legacy_report_path("rag_eval_report.json")
DEFAULT_HIDDEN_REPORT_PATH = legacy_report_path("hidden_eval_report.json")
DEFAULT_SCENARIO_REGISTRY_PATH = Path("config/scenario_registry.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_alignment_report.json")

ISSUE_DOMAIN_CONTAMINATION = "domain_contamination"
ISSUE_MISSING_PRIMARY_EVIDENCE = "missing_primary_evidence"
ISSUE_DEFINITION_ONLY = "definition_only"
ISSUE_ANSWER_EVIDENCE_DISCONNECT = "answer_evidence_disconnect"
ISSUE_INSUFFICIENT_EVIDENCE_COVERAGE = "insufficient_evidence_coverage"

STATUS_PASS = "pass"
STATUS_REVIEW = "review"

DOMAIN_SOURCE_HINTS = {
    "数据合规": [
        "个人信息保护法",
        "数据安全法",
        "网络安全法",
        "数据出境安全评估办法",
        "个人信息出境标准合同办法",
        "个人信息安全规范",
    ],
    "市场秩序": ["反不正当竞争法", "反垄断法"],
    "公司治理": ["公司法"],
    "知识产权": ["商标法", "专利法"],
    "财税": ["增值税法"],
    "民商事": ["民法典"],
    "安全合规": ["保守国家秘密法"],
}

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def source_domain(source: str, category: str | None = None) -> str | None:
    if category:
        return category
    for domain, hints in DOMAIN_SOURCE_HINTS.items():
        if any(hint in source for hint in hints):
            return domain
    return None


def article_key(item: dict[str, Any]) -> tuple[str, Any, Any]:
    return (
        normalize_text(item.get("source") or item.get("law_name")),
        item.get("article_no"),
        normalize_text(item.get("section_no")),
    )


def source_matches(source: str, expected_source: str) -> bool:
    if not source or not expected_source:
        return False
    return source == expected_source or source in expected_source or expected_source in source


def evidence_matches_expected(evidence: dict[str, Any], expected: dict[str, Any]) -> bool:
    source = normalize_text(evidence.get("source") or evidence.get("law_name"))
    expected_source = normalize_text(expected.get("source") or expected.get("law_name"))
    if expected_source and not source_matches(source, expected_source):
        return False
    if expected.get("article_no") is not None:
        return evidence.get("article_no") == expected.get("article_no")
    if expected.get("section_no"):
        return normalize_text(evidence.get("section_no")) == normalize_text(expected.get("section_no"))
    return bool(expected_source)


def functional_type_for_evidence(evidence: dict[str, Any]) -> str:
    return classify_evidence_function(evidence).functional_type


def read_reports(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = load_json(path)
    if isinstance(payload, list):
        reports = payload
    elif isinstance(payload, dict):
        reports = payload.get("reports") or []
    else:
        reports = []
    result = []
    for report in reports:
        if isinstance(report, dict):
            item = dict(report)
            item.setdefault("_report_source", label)
            result.append(item)
    return result


def load_scenario_metadata(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = load_json(path)
    scenarios = payload.get("scenarios") if isinstance(payload, dict) else []
    result: dict[str, dict[str, Any]] = {}
    for scenario in scenarios or []:
        if not isinstance(scenario, dict):
            continue
        for case_id in scenario.get("eval_case_ids") or []:
            result[case_id] = scenario
    return result


def expected_evidence_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    final_layer = (
        report.get("retrieval_diagnostics", {})
        .get("layers", {})
        .get("final", {})
    )
    expected = []
    for item in final_layer.get("matched") or []:
        if isinstance(item, dict):
            expected.append(item)
    for item in final_layer.get("missing") or []:
        if isinstance(item, dict):
            expected.append(item)
    return expected


def infer_expected_domains(report: dict[str, Any], scenario: dict[str, Any] | None) -> set[str]:
    domains: set[str] = set()
    if scenario and scenario.get("domain"):
        domains.add(str(scenario["domain"]))
    category = report.get("category") or (report.get("filters") or {}).get("category")
    if category:
        domains.add(str(category))
    for expected in expected_evidence_from_report(report):
        domain = source_domain(normalize_text(expected.get("source") or expected.get("law_name")))
        if domain:
            domains.add(domain)
    return domains


def infer_primary_expected_evidence(
    report: dict[str, Any],
    scenario: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if scenario:
        core_articles = [item for item in scenario.get("core_articles") or [] if isinstance(item, dict)]
        if core_articles:
            return core_articles
    return expected_evidence_from_report(report)


def text_supported_by_evidence(text: str, evidence_items: list[dict[str, Any]]) -> bool:
    text = normalize_text(text)
    if not text:
        return True
    for item in evidence_items:
        content = " ".join(
            normalize_text(item.get(key))
            for key in ("content", "content_preview", "matched_content", "citation", "source", "law_name")
        )
        if text in content or any(token and token in content for token in split_terms(text)):
            return True
    return False


def split_terms(text: str) -> list[str]:
    normalized = normalize_text(text)
    separators = ["、", "，", ",", "/", "／", "和", "及", "与", "或"]
    terms = [normalized]
    for separator in separators:
        next_terms = []
        for term in terms:
            next_terms.extend(part.strip() for part in term.split(separator))
        terms = next_terms
    return [term for term in terms if len(term) >= 4]


def evaluate_case(report: dict[str, Any], scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    case_id = normalize_text(report.get("id") or report.get("case_id") or "unknown_case")
    evidence_items = [item for item in report.get("evidence") or report.get("evidence_chain") or [] if isinstance(item, dict)]
    expected_domains = infer_expected_domains(report, scenario)
    primary_expected = infer_primary_expected_evidence(report, scenario)
    detected_issues: list[str] = []
    review_reasons: list[str] = []

    evidence_domains = []
    domain_contamination = []
    for item in evidence_items:
        domain = source_domain(
            normalize_text(item.get("source") or item.get("law_name")),
            item.get("category"),
        )
        if domain:
            evidence_domains.append(domain)
        if expected_domains and domain and domain not in expected_domains:
            domain_contamination.append({
                "source": item.get("source") or item.get("law_name"),
                "article_no": item.get("article_no"),
                "domain": domain,
            })
    if domain_contamination:
        detected_issues.append(ISSUE_DOMAIN_CONTAMINATION)
        review_reasons.append("Evidence includes sources outside expected legal domains.")

    matched_primary = []
    missing_primary = []
    for expected in primary_expected:
        if any(evidence_matches_expected(item, expected) for item in evidence_items):
            matched_primary.append(expected)
        else:
            missing_primary.append(expected)
    if primary_expected and missing_primary:
        detected_issues.append(ISSUE_MISSING_PRIMARY_EVIDENCE)
        review_reasons.append("One or more primary expected legal issues lack matching evidence.")

    functional_counts = Counter(functional_type_for_evidence(item) for item in evidence_items)
    has_definition = functional_counts.get("definition", 0) > 0
    has_operative = has_operative_support(set(functional_counts))
    if has_definition and not has_operative:
        detected_issues.append(ISSUE_DEFINITION_ONLY)
        review_reasons.append("Evidence contains definition material without operative, procedural, rights, or liability support.")

    unsupported_outputs = []
    for field_name in ("risk_types", "recommended_actions"):
        for value in report.get(field_name) or []:
            if not text_supported_by_evidence(value, evidence_items):
                unsupported_outputs.append({"field": field_name, "value": value})
    if report.get("risk_level") in {"medium", "high"} and not evidence_items:
        unsupported_outputs.append({"field": "risk_level", "value": report.get("risk_level")})
    if unsupported_outputs:
        detected_issues.append(ISSUE_ANSWER_EVIDENCE_DISCONNECT)
        review_reasons.append("Risk outputs include terms or actions not visibly supported by evidence text.")

    if primary_expected:
        coverage_ratio = len(matched_primary) / len(primary_expected)
    else:
        coverage_ratio = 1.0 if evidence_items else 0.0
    if primary_expected and matched_primary and coverage_ratio < 0.5:
        detected_issues.append(ISSUE_INSUFFICIENT_EVIDENCE_COVERAGE)
        review_reasons.append("Evidence covers only a minority of primary expected issues.")

    detected_issues = list(dict.fromkeys(detected_issues))
    review_reasons = list(dict.fromkeys(review_reasons))
    status = STATUS_REVIEW if detected_issues else STATUS_PASS

    return {
        "case_id": case_id,
        "report_source": report.get("_report_source", "unknown"),
        "alignment_status": status,
        "detected_issues": detected_issues,
        "review_reasons": review_reasons,
        "expected_domains": sorted(expected_domains),
        "evidence_domains": sorted(set(evidence_domains)),
        "domain_contamination": domain_contamination,
        "primary_issue_coverage": {
            "matched": len(matched_primary),
            "expected": len(primary_expected),
            "coverage_ratio": round(coverage_ratio, 3),
            "missing": missing_primary,
        },
        "functional_type_counts": dict(sorted(functional_counts.items())),
        "unsupported_outputs": unsupported_outputs,
        "risk_level": report.get("risk_level"),
    }


def build_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    high_risk_manual_review = []
    for result in case_results:
        for issue in result["detected_issues"]:
            issue_counts[issue] += 1
        domains = result.get("expected_domains") or ["unknown"]
        for domain in domains:
            domain_summary[domain]["total"] += 1
            if result["alignment_status"] == STATUS_REVIEW:
                domain_summary[domain]["review"] += 1
        if result.get("risk_level") == "high" and result["alignment_status"] == STATUS_REVIEW:
            high_risk_manual_review.append({
                "case_id": result["case_id"],
                "detected_issues": result["detected_issues"],
                "review_reasons": result["review_reasons"],
            })
    return {
        "total_cases": len(case_results),
        "passed_cases": sum(1 for result in case_results if result["alignment_status"] == STATUS_PASS),
        "review_cases": sum(1 for result in case_results if result["alignment_status"] == STATUS_REVIEW),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "high_risk_manual_review": high_risk_manual_review,
    }


def build_alignment_report(
    rag_report_path: Path = DEFAULT_RAG_REPORT_PATH,
    hidden_report_path: Path = DEFAULT_HIDDEN_REPORT_PATH,
    scenario_registry_path: Path = DEFAULT_SCENARIO_REGISTRY_PATH,
) -> dict[str, Any]:
    scenario_by_case = load_scenario_metadata(scenario_registry_path)
    reports = read_reports(rag_report_path, "rag_eval_report")
    hidden_reports = read_reports(hidden_report_path, "hidden_eval_report")
    skipped_inputs = []
    if not hidden_report_path.exists():
        skipped_inputs.append(str(hidden_report_path))
    reports.extend(hidden_reports)
    case_results = [
        evaluate_case(report, scenario_by_case.get(normalize_text(report.get("id") or report.get("case_id"))))
        for report in reports
    ]
    return {
        "version": "0.4.7.1",
        "scope": "offline evidence alignment diagnostics",
        "inputs": {
            "rag_report": str(rag_report_path),
            "hidden_report": str(hidden_report_path),
            "scenario_registry": str(scenario_registry_path),
            "skipped_inputs": skipped_inputs,
        },
        "summary": build_summary(case_results),
        "cases": case_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check saved RAG reports for evidence alignment diagnostics.")
    parser.add_argument("--rag-report", type=Path, default=DEFAULT_RAG_REPORT_PATH)
    parser.add_argument("--hidden-report", type=Path, default=DEFAULT_HIDDEN_REPORT_PATH)
    parser.add_argument("--scenario-registry", type=Path, default=DEFAULT_SCENARIO_REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_alignment_report(
        rag_report_path=args.rag_report,
        hidden_report_path=args.hidden_report,
        scenario_registry_path=args.scenario_registry,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Evidence alignment check completed: "
        f"{summary['total_cases']} cases, {summary['review_cases']} review, "
        f"{summary['passed_cases']} pass"
    )
    if report["inputs"]["skipped_inputs"]:
        print(f"Skipped optional inputs: {', '.join(report['inputs']['skipped_inputs'])}")
    if args.fail_on_review and summary["review_cases"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
