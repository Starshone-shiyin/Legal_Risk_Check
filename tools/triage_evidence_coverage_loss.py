"""Offline triage for evidence coverage loss diagnostics.

This tool reads the v0.4.7.3 evidence coverage report only. It does not call
rag_query, LLMs, Qdrant, rerank, prompt construction, anchors, or risk rules.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_COVERAGE_REPORT_PATH = Path("tests/evidence_coverage_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_coverage_triage_report.json")

VERSION = "0.4.7.3.2"

TRIAGE_OK = "ok"
TRIAGE_REVIEW = "review"
TRIAGE_HIGH_PRIORITY = "high_priority_review"

ROOT_BASE_RETRIEVAL_GAP = "base_retrieval_gap"
ROOT_ANCHOR_DEPENDENCY = "anchor_dependency"
ROOT_FINAL_SELECTION_LOSS = "final_selection_loss"
ROOT_FINAL_PRIMARY_GAP = "final_primary_gap"
ROOT_SCENARIO_CORE_GAP = "scenario_core_gap"
ROOT_LOW_FINAL_COVERAGE = "low_final_coverage"
ROOT_FUNCTIONAL_METADATA_NOT_EVALUABLE = "functional_metadata_not_evaluable"
ROOT_FUNCTIONAL_SUPPORT_GAP = "functional_support_gap"

ISSUE_FINAL_PRIMARY_GAP = "final_primary_gap"
ISSUE_SCENARIO_CORE_GAP = "scenario_core_gap"
ISSUE_OPERATIVE_SUPPORT_GAP = "operative_support_gap"
ISSUE_FUNCTIONAL_TYPE_GAP = "functional_type_gap"
ISSUE_LOW_FINAL_COVERAGE = "low_final_coverage"

BASE_RETRIEVAL_REVIEW_THRESHOLD = 0.75


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def layer(case: dict[str, Any], layer_name: str) -> dict[str, Any]:
    value = (case.get("layer_coverage") or {}).get(layer_name)
    return value if isinstance(value, dict) else {}


def ratio(case: dict[str, Any], layer_name: str) -> float:
    value = layer(case, layer_name).get("coverage_ratio")
    return float(value) if isinstance(value, (int, float)) else 1.0


def expected_count(case: dict[str, Any], layer_name: str) -> int:
    value = layer(case, layer_name).get("expected_count")
    return int(value) if isinstance(value, int) else 0


def ratio_delta(before: float, after: float) -> float:
    return round(after - before, 3)


def functional_metadata_not_evaluable(case: dict[str, Any]) -> bool:
    coverage = case.get("functional_type_coverage") or {}
    return bool(coverage.get("total_items")) and not bool(coverage.get("evaluable"))


def classify_root_causes(case: dict[str, Any]) -> list[str]:
    issues = set(case.get("detected_issues") or [])
    causes: list[str] = []
    union_ratio = ratio(case, "union")
    anchor_ratio = ratio(case, "anchor")
    rerank_ratio = ratio(case, "rerank_input")
    final_ratio = ratio(case, "final")

    if expected_count(case, "union") and union_ratio < BASE_RETRIEVAL_REVIEW_THRESHOLD:
        causes.append(ROOT_BASE_RETRIEVAL_GAP)
    if anchor_ratio > union_ratio:
        causes.append(ROOT_ANCHOR_DEPENDENCY)
    if rerank_ratio > final_ratio:
        causes.append(ROOT_FINAL_SELECTION_LOSS)
    if ISSUE_FINAL_PRIMARY_GAP in issues:
        causes.append(ROOT_FINAL_PRIMARY_GAP)
    if ISSUE_SCENARIO_CORE_GAP in issues:
        causes.append(ROOT_SCENARIO_CORE_GAP)
    if ISSUE_LOW_FINAL_COVERAGE in issues:
        causes.append(ROOT_LOW_FINAL_COVERAGE)
    if functional_metadata_not_evaluable(case):
        causes.append(ROOT_FUNCTIONAL_METADATA_NOT_EVALUABLE)
    if ISSUE_OPERATIVE_SUPPORT_GAP in issues or ISSUE_FUNCTIONAL_TYPE_GAP in issues:
        causes.append(ROOT_FUNCTIONAL_SUPPORT_GAP)
    return list(dict.fromkeys(causes))


def priority_score(case: dict[str, Any], causes: list[str]) -> int:
    score = 0
    if case.get("coverage_status") == "review":
        score += 1
    if case.get("risk_level") == "high":
        score += 2
    if ROOT_SCENARIO_CORE_GAP in causes:
        score += 3
    if ROOT_FINAL_PRIMARY_GAP in causes:
        score += 3
    if ROOT_FINAL_SELECTION_LOSS in causes:
        score += 2
    if ROOT_LOW_FINAL_COVERAGE in causes:
        score += 2
    if ROOT_ANCHOR_DEPENDENCY in causes:
        score += 1
    return score


def triage_status(score: int, causes: list[str]) -> str:
    actionable_causes = [
        cause for cause in causes if cause != ROOT_FUNCTIONAL_METADATA_NOT_EVALUABLE
    ]
    if not actionable_causes:
        return TRIAGE_OK
    if score >= 5:
        return TRIAGE_HIGH_PRIORITY
    return TRIAGE_REVIEW


def recommended_actions(causes: list[str]) -> list[str]:
    actions = []
    if ROOT_BASE_RETRIEVAL_GAP in causes:
        actions.append("Review base dense/sparse/union retrieval coverage before changing rerank or prompt.")
    if ROOT_ANCHOR_DEPENDENCY in causes:
        actions.append("Audit why expected evidence appears after anchor injection and whether base recall metadata is sufficient.")
    if ROOT_FINAL_SELECTION_LOSS in causes:
        actions.append("Inspect final evidence selection loss from rerank_input to final without changing rerank behavior in this version.")
    if ROOT_FINAL_PRIMARY_GAP in causes:
        actions.append("Manually review missing final expected statutes against the answer evidence chain.")
    if ROOT_SCENARIO_CORE_GAP in causes:
        actions.append("Compare scenario core articles with final evidence and verify whether the registry core set is too broad or evidence is missing.")
    if ROOT_LOW_FINAL_COVERAGE in causes:
        actions.append("Prioritize this case for manual review because final coverage is below the diagnostic threshold.")
    if ROOT_FUNCTIONAL_METADATA_NOT_EVALUABLE in causes:
        actions.append("Consider adding evidence text or functional_type metadata to future offline reports before using functional coverage as a gate.")
    if ROOT_FUNCTIONAL_SUPPORT_GAP in causes:
        actions.append("Review whether final evidence contains operative, procedural, liability, rights, or technical support.")
    return actions


def triage_case(case: dict[str, Any]) -> dict[str, Any]:
    causes = classify_root_causes(case)
    score = priority_score(case, causes)
    return {
        "case_id": case.get("case_id"),
        "report_source": case.get("report_source"),
        "triage_status": triage_status(score, causes),
        "priority_score": score,
        "risk_level": case.get("risk_level"),
        "expected_domains": case.get("expected_domains") or [],
        "coverage_status": case.get("coverage_status"),
        "root_causes": causes,
        "detected_issues": case.get("detected_issues") or [],
        "recommended_actions": recommended_actions(causes),
        "coverage_flow": {
            "dense": ratio(case, "dense"),
            "sparse": ratio(case, "sparse"),
            "union": ratio(case, "union"),
            "anchor": ratio(case, "anchor"),
            "rerank_input": ratio(case, "rerank_input"),
            "final": ratio(case, "final"),
            "union_to_anchor_delta": ratio_delta(ratio(case, "union"), ratio(case, "anchor")),
            "rerank_to_final_delta": ratio_delta(ratio(case, "rerank_input"), ratio(case, "final")),
        },
        "final_evidence_coverage": case.get("final_evidence_coverage") or {},
        "scenario_core_coverage": case.get("scenario_core_coverage") or {},
        "functional_type_coverage": case.get("functional_type_coverage") or {},
    }


def build_summary(triaged_cases: list[dict[str, Any]]) -> dict[str, Any]:
    root_counts = Counter()
    status_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    risk_summary: dict[str, Counter] = defaultdict(Counter)
    flow_totals = Counter()

    for case in triaged_cases:
        status_counts[case["triage_status"]] += 1
        for cause in case["root_causes"]:
            root_counts[cause] += 1
        domains = case.get("expected_domains") or ["unknown"]
        for domain in domains:
            domain_summary[domain]["total"] += 1
            if case["triage_status"] != TRIAGE_OK:
                domain_summary[domain]["review"] += 1
        risk_level = case.get("risk_level") or "unknown"
        risk_summary[risk_level]["total"] += 1
        if case["triage_status"] == TRIAGE_HIGH_PRIORITY:
            risk_summary[risk_level]["high_priority_review"] += 1
        flow = case["coverage_flow"]
        if flow["union_to_anchor_delta"] > 0:
            flow_totals["anchor_improved_cases"] += 1
        if flow["rerank_to_final_delta"] < 0:
            flow_totals["final_selection_loss_cases"] += 1
        if flow["union"] < BASE_RETRIEVAL_REVIEW_THRESHOLD:
            flow_totals["low_union_coverage_cases"] += 1

    high_priority = [
        {
            "case_id": case["case_id"],
            "priority_score": case["priority_score"],
            "risk_level": case.get("risk_level"),
            "root_causes": case["root_causes"],
            "recommended_actions": case["recommended_actions"],
        }
        for case in sorted(
            triaged_cases,
            key=lambda item: (-int(item.get("priority_score") or 0), str(item.get("case_id") or "")),
        )
        if case["triage_status"] == TRIAGE_HIGH_PRIORITY
    ]

    return {
        "total_cases": len(triaged_cases),
        "triage_status_summary": dict(sorted(status_counts.items())),
        "root_cause_summary": dict(sorted(root_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "per_risk_level_summary": {
            risk_level: dict(counts)
            for risk_level, counts in sorted(risk_summary.items())
        },
        "coverage_flow_summary": dict(sorted(flow_totals.items())),
        "high_priority_manual_review": high_priority,
    }


def build_triage_report(coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    cases = [case for case in coverage_report.get("cases") or [] if isinstance(case, dict)]
    triaged_cases = [triage_case(case) for case in cases]
    return {
        "version": VERSION,
        "scope": "offline evidence coverage loss triage",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
        },
        "summary": build_summary(triaged_cases),
        "cases": triaged_cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage saved evidence coverage diagnostics.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-high-priority", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_triage_report(args.coverage_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    high_priority = summary["triage_status_summary"].get(TRIAGE_HIGH_PRIORITY, 0)
    print(
        "Evidence coverage triage completed: "
        f"{summary['total_cases']} cases, {high_priority} high-priority review"
    )
    if args.fail_on_high_priority and high_priority:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
