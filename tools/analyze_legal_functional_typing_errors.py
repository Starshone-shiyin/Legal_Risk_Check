"""Combine functional typing reports into an offline error analysis report.

This tool reads existing diagnostics only. It does not call rag_query, LLM,
Qdrant, rerank, prompt, anchor, risk supplement, or eval execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_FIXTURE_REPORT_PATH = Path("tests/legal_functional_typing_fixture_report.json")
DEFAULT_AUDIT_REPORT_PATH = Path("tests/legal_functional_typing_report.json")
DEFAULT_ALIGNMENT_REPORT_PATH = Path("tests/evidence_alignment_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/legal_functional_typing_error_analysis_report.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ratio(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def analyze_fixture_report(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary") or {}
    failed_cases = [
        {
            "case_id": case.get("id"),
            "expected": case.get("expected_functional_type"),
            "actual": case.get("actual_functional_type"),
            "matched_rule": case.get("matched_rule"),
            "matched_terms": case.get("matched_terms") or [],
        }
        for case in report.get("cases") or []
        if not case.get("passed")
    ]
    return {
        "passed": bool(report.get("passed")),
        "total_cases": int(summary.get("total_cases") or 0),
        "failed_cases": int(summary.get("failed_cases") or 0),
        "failures_by_expected_type": summary.get("failures_by_expected_type") or {},
        "failed_case_details": failed_cases,
    }


def analyze_audit_report(report: dict[str, Any]) -> dict[str, Any]:
    documents = report.get("documents") or []
    high_unclassified_documents = []
    low_operative_documents = []
    definition_only_documents = []
    domain_imbalance = []

    for doc in documents:
        total_chunks = int(doc.get("total_chunks") or 0)
        function_counts = doc.get("functional_type_counts") or {}
        definition_count = int(function_counts.get("definition") or 0)
        operative_support_chunks = int(doc.get("operative_support_chunks") or 0)
        unclassified_ratio = ratio(doc.get("unclassified_ratio"))
        operative_support_ratio = ratio(doc.get("operative_support_ratio"))

        base = {
            "source": doc.get("source"),
            "domain": doc.get("domain"),
            "total_chunks": total_chunks,
            "unclassified_ratio": unclassified_ratio,
            "operative_support_ratio": operative_support_ratio,
            "review_reasons": doc.get("review_reasons") or [],
        }
        if unclassified_ratio > 0.35:
            high_unclassified_documents.append(base)
        if total_chunks >= 10 and operative_support_ratio < 0.25 and doc.get("document_type") != "标准":
            low_operative_documents.append(base)
        if definition_count > 0 and operative_support_chunks == 0:
            definition_only_documents.append(base)

    for domain, stats in (report.get("summary") or {}).get("per_domain_summary", {}).items():
        chunks = int(stats.get("chunks") or 0)
        review_documents = int(stats.get("review_documents") or 0)
        documents_count = int(stats.get("documents") or 0)
        if review_documents:
            domain_imbalance.append({
                "domain": domain,
                "documents": documents_count,
                "chunks": chunks,
                "review_documents": review_documents,
            })

    high_unclassified_documents.sort(key=lambda item: item["unclassified_ratio"], reverse=True)
    low_operative_documents.sort(key=lambda item: item["operative_support_ratio"])
    definition_only_documents.sort(key=lambda item: item["source"] or "")
    domain_imbalance.sort(key=lambda item: item["review_documents"], reverse=True)

    summary = report.get("summary") or {}
    return {
        "total_documents": int(summary.get("total_documents") or 0),
        "review_documents": int(summary.get("review_documents") or 0),
        "total_chunks": int(summary.get("total_chunks") or 0),
        "unclassified_ratio": ratio(summary.get("unclassified_ratio")),
        "operative_support_ratio": ratio(summary.get("operative_support_ratio")),
        "functional_type_summary": summary.get("functional_type_summary") or {},
        "high_unclassified_documents": high_unclassified_documents,
        "low_operative_documents": low_operative_documents,
        "definition_only_documents": definition_only_documents,
        "domain_imbalance": domain_imbalance,
    }


def analyze_alignment_report(report: dict[str, Any]) -> dict[str, Any]:
    cases = report.get("cases") or []
    definition_only_cases = []
    missing_primary_cases = []
    unsupported_output_cases = []
    insufficient_coverage_cases = []

    for case in cases:
        issues = set(case.get("detected_issues") or [])
        base = {
            "case_id": case.get("case_id"),
            "expected_domains": case.get("expected_domains") or [],
            "detected_issues": case.get("detected_issues") or [],
            "review_reasons": case.get("review_reasons") or [],
        }
        if "definition_only" in issues:
            definition_only_cases.append(base)
        if "missing_primary_evidence" in issues:
            missing_primary_cases.append(base)
        if "answer_evidence_disconnect" in issues:
            unsupported_output_cases.append(base)
        if "insufficient_evidence_coverage" in issues:
            insufficient_coverage_cases.append(base)

    summary = report.get("summary") or {}
    return {
        "total_cases": int(summary.get("total_cases") or 0),
        "review_cases": int(summary.get("review_cases") or 0),
        "issue_type_summary": summary.get("issue_type_summary") or {},
        "per_domain_summary": summary.get("per_domain_summary") or {},
        "definition_only_cases": definition_only_cases,
        "missing_primary_cases": missing_primary_cases,
        "unsupported_output_cases": unsupported_output_cases,
        "insufficient_coverage_cases": insufficient_coverage_cases,
        "high_risk_manual_review_count": len(summary.get("high_risk_manual_review") or []),
    }


def prioritize_actions(
    fixture_analysis: dict[str, Any],
    audit_analysis: dict[str, Any],
    alignment_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    actions = []
    if fixture_analysis["failed_cases"]:
        actions.append({
            "priority": "P0",
            "action": "Fix functional typing golden fixture failures before adding new rules.",
            "evidence": {
                "failed_cases": fixture_analysis["failed_cases"],
                "failures_by_expected_type": fixture_analysis["failures_by_expected_type"],
            },
        })
    if audit_analysis["high_unclassified_documents"]:
        actions.append({
            "priority": "P1",
            "action": "Reduce high unclassified document ratios with domain-neutral legal language cues.",
            "evidence": {
                "documents": audit_analysis["high_unclassified_documents"][:5],
            },
        })
    if audit_analysis["definition_only_documents"] or alignment_analysis["definition_only_cases"]:
        actions.append({
            "priority": "P1",
            "action": "Investigate definition-only support and add operative/procedural/liability cues or metadata where appropriate.",
            "evidence": {
                "documents": audit_analysis["definition_only_documents"][:5],
                "cases": alignment_analysis["definition_only_cases"][:10],
            },
        })
    if audit_analysis["low_operative_documents"]:
        actions.append({
            "priority": "P2",
            "action": "Review documents with low operative support coverage.",
            "evidence": {
                "documents": audit_analysis["low_operative_documents"][:5],
            },
        })
    if alignment_analysis["missing_primary_cases"]:
        actions.append({
            "priority": "P2",
            "action": "Use missing-primary evidence cases to guide future coverage diagnostics, not case-specific patches.",
            "evidence": {
                "case_count": len(alignment_analysis["missing_primary_cases"]),
                "sample_cases": alignment_analysis["missing_primary_cases"][:10],
            },
        })
    if alignment_analysis["unsupported_output_cases"]:
        actions.append({
            "priority": "P3",
            "action": "Analyze answer-evidence disconnect separately from functional typing before changing generation rules.",
            "evidence": {
                "case_count": len(alignment_analysis["unsupported_output_cases"]),
            },
        })
    return actions


def build_report(
    fixture_report_path: Path = DEFAULT_FIXTURE_REPORT_PATH,
    audit_report_path: Path = DEFAULT_AUDIT_REPORT_PATH,
    alignment_report_path: Path = DEFAULT_ALIGNMENT_REPORT_PATH,
) -> dict[str, Any]:
    fixture_report = load_json(fixture_report_path)
    audit_report = load_json(audit_report_path)
    alignment_report = load_json(alignment_report_path)

    fixture_analysis = analyze_fixture_report(fixture_report)
    audit_analysis = analyze_audit_report(audit_report)
    alignment_analysis = analyze_alignment_report(alignment_report)
    actions = prioritize_actions(fixture_analysis, audit_analysis, alignment_analysis)
    report_version = (
        audit_report.get("version")
        or fixture_report.get("version")
        or "0.4.7.2.3"
    )
    return {
        "version": report_version,
        "scope": "offline legal functional typing error analysis",
        "inputs": {
            "fixture_report": str(fixture_report_path),
            "functional_typing_audit_report": str(audit_report_path),
            "evidence_alignment_report": str(alignment_report_path),
        },
        "summary": {
            "fixture_failed_cases": fixture_analysis["failed_cases"],
            "high_unclassified_documents": len(audit_analysis["high_unclassified_documents"]),
            "low_operative_documents": len(audit_analysis["low_operative_documents"]),
            "definition_only_documents": len(audit_analysis["definition_only_documents"]),
            "alignment_review_cases": alignment_analysis["review_cases"],
            "alignment_missing_primary_cases": len(alignment_analysis["missing_primary_cases"]),
            "alignment_definition_only_cases": len(alignment_analysis["definition_only_cases"]),
            "alignment_unsupported_output_cases": len(alignment_analysis["unsupported_output_cases"]),
            "prioritized_action_count": len(actions),
        },
        "fixture_analysis": fixture_analysis,
        "functional_typing_audit_analysis": audit_analysis,
        "evidence_alignment_analysis": alignment_analysis,
        "prioritized_actions": actions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build legal functional typing error analysis report.")
    parser.add_argument("--fixture-report", type=Path, default=DEFAULT_FIXTURE_REPORT_PATH)
    parser.add_argument("--audit-report", type=Path, default=DEFAULT_AUDIT_REPORT_PATH)
    parser.add_argument("--alignment-report", type=Path, default=DEFAULT_ALIGNMENT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.fixture_report, args.audit_report, args.alignment_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Legal functional typing error analysis completed: "
        f"{summary['prioritized_action_count']} actions, "
        f"{summary['high_unclassified_documents']} high-unclassified documents, "
        f"{summary['alignment_review_cases']} alignment review cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
