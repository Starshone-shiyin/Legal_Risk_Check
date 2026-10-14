"""Build an offline manual review dataset from evidence coverage diagnostics.

The dataset is intentionally a review worklist. It does not patch cases, update
eval expectations, call rag_query, or change retrieval/rerank/prompt behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.3.3"

DEFAULT_COVERAGE_REPORT_PATH = legacy_report_path("evidence_coverage_report.json")
DEFAULT_TRIAGE_REPORT_PATH = legacy_report_path("evidence_coverage_triage_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_manual_review_dataset.json")

REVIEW_PENDING = "pending"
TRIAGE_HIGH_PRIORITY = "high_priority_review"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def case_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("case_id")): case
        for case in report.get("cases") or []
        if isinstance(case, dict) and case.get("case_id")
    }


def review_questions(root_causes: list[str]) -> list[str]:
    questions = []
    if "base_retrieval_gap" in root_causes:
        questions.append("Did dense/sparse/union retrieval miss expected evidence before anchor injection?")
    if "anchor_dependency" in root_causes:
        questions.append("Is anchor dependency acceptable, or does it indicate weak base retrieval metadata?")
    if "final_selection_loss" in root_causes:
        questions.append("Which expected article was present in rerank_input but absent from final evidence?")
    if "final_primary_gap" in root_causes:
        questions.append("Does the answer rely on a primary statute that is missing from final evidence?")
    if "scenario_core_gap" in root_causes:
        questions.append("Is the scenario core article truly required, or is the registry core set too broad?")
    if "low_final_coverage" in root_causes:
        questions.append("Does low final coverage make the answer unsuitable without manual review?")
    return questions


def build_review_item(
    triage_case: dict[str, Any],
    coverage_case: dict[str, Any] | None,
) -> dict[str, Any]:
    coverage_case = coverage_case or {}
    root_causes = triage_case.get("root_causes") or []
    return {
        "case_id": triage_case.get("case_id"),
        "review_status": REVIEW_PENDING,
        "priority_score": triage_case.get("priority_score"),
        "risk_level": triage_case.get("risk_level"),
        "expected_domains": triage_case.get("expected_domains") or coverage_case.get("expected_domains") or [],
        "root_causes": root_causes,
        "detected_issues": triage_case.get("detected_issues") or coverage_case.get("detected_issues") or [],
        "recommended_actions": triage_case.get("recommended_actions") or [],
        "review_questions": review_questions(root_causes),
        "coverage_flow": triage_case.get("coverage_flow") or {},
        "final_evidence_coverage": coverage_case.get("final_evidence_coverage") or {},
        "scenario_core_coverage": coverage_case.get("scenario_core_coverage") or {},
        "functional_type_coverage": coverage_case.get("functional_type_coverage") or {},
        "missing_final_expected": (coverage_case.get("final_evidence_coverage") or {}).get("missing") or [],
        "missing_scenario_core": (coverage_case.get("scenario_core_coverage") or {}).get("missing") or [],
        "final_evidence": coverage_case.get("final_evidence") or [],
        "reviewer_fields": {
            "reviewer": "",
            "reviewed_at": "",
            "decision": "",
            "confirmed_root_causes": [],
            "rejected_root_causes": [],
            "notes": "",
            "follow_up_action": "",
        },
    }


def build_summary(review_items: list[dict[str, Any]], triage_report: dict[str, Any]) -> dict[str, Any]:
    root_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    risk_summary: dict[str, Counter] = defaultdict(Counter)

    for item in review_items:
        for cause in item.get("root_causes") or []:
            root_counts[cause] += 1
        for domain in item.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["review_items"] += 1
        risk_summary[item.get("risk_level") or "unknown"]["review_items"] += 1

    scores = [int(item.get("priority_score") or 0) for item in review_items]
    return {
        "total_review_items": len(review_items),
        "pending_review_items": sum(1 for item in review_items if item.get("review_status") == REVIEW_PENDING),
        "root_cause_summary": dict(sorted(root_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "per_risk_level_summary": {
            level: dict(counts)
            for level, counts in sorted(risk_summary.items())
        },
        "priority_score": {
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0,
        },
        "source_triage_status_summary": (triage_report.get("summary") or {}).get("triage_status_summary") or {},
    }


def build_dataset(
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    triage_report_path: Path = DEFAULT_TRIAGE_REPORT_PATH,
) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    triage_report = load_json(triage_report_path)
    coverage_by_case = case_map(coverage_report)
    triage_cases = [
        case
        for case in triage_report.get("cases") or []
        if isinstance(case, dict) and case.get("triage_status") == TRIAGE_HIGH_PRIORITY
    ]
    triage_cases = sorted(
        triage_cases,
        key=lambda case: (-int(case.get("priority_score") or 0), str(case.get("case_id") or "")),
    )
    review_items = [
        build_review_item(case, coverage_by_case.get(str(case.get("case_id"))))
        for case in triage_cases
    ]
    return {
        "version": VERSION,
        "scope": "offline evidence manual review dataset",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
            "triage_report": str(triage_report_path),
            "triage_report_version": triage_report.get("version"),
        },
        "summary": build_summary(review_items, triage_report),
        "review_items": review_items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an evidence manual review dataset.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--triage-report", type=Path, default=DEFAULT_TRIAGE_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_dataset(args.coverage_report, args.triage_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Evidence manual review dataset built: "
        f"{report['summary']['total_review_items']} pending review items"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
