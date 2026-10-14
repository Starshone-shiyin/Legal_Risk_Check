"""Build an offline evidence manual-review loop package.

This tool consolidates existing diagnostic reports into a reviewer work package.
It does not write reviewer conclusions, patch eval cases, modify hidden seeds,
or change retrieval, rerank, prompts, anchors, or risk rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_evidence_alignment import normalize_text


VERSION = "0.4.7.4.6"

DEFAULT_MANUAL_REVIEW_DATASET_PATH = Path("tests/evidence_manual_review_dataset.json")
DEFAULT_SCENARIO_CALIBRATION_REPORT_PATH = Path("tests/scenario_registry_calibration_report.json")
DEFAULT_BASE_AUDIT_REPORT_PATH = Path("tests/base_retrieval_quality_audit_report.json")
DEFAULT_ANCHOR_AUDIT_REPORT_PATH = Path("tests/anchor_dependency_audit_report.json")
DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH = Path("tests/final_evidence_selection_audit_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_manual_review_loop_report.json")

QUEUE_HIGH_RISK = "high_risk_grounding_review"
QUEUE_SCENARIO_REGISTRY = "scenario_registry_calibration"
QUEUE_BASE_RETRIEVAL = "base_retrieval_quality_review"
QUEUE_ANCHOR_DEPENDENCY = "anchor_dependency_review"
QUEUE_FINAL_SELECTION = "final_evidence_selection_review"
QUEUE_PRIMARY_EVIDENCE = "primary_evidence_review"

REVIEW_STATUS_PENDING = "pending"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def case_id(item: dict[str, Any]) -> str:
    return normalize_text(item.get("case_id") or item.get("id"))


def case_map(report: dict[str, Any], key: str = "cases") -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in report.get(key) or []
        if isinstance(item, dict) and case_id(item)
    }


def review_item_map(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in dataset.get("review_items") or []
        if isinstance(item, dict) and case_id(item)
    }


def unique_list(values: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for value in values:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def collect_case_ids(*maps: dict[str, dict[str, Any]]) -> list[str]:
    ids = set()
    for mapping in maps:
        ids.update(mapping.keys())
    return sorted(ids)


def queue_tags(
    manual_item: dict[str, Any],
    scenario_case: dict[str, Any],
    base_case: dict[str, Any],
    anchor_case: dict[str, Any],
    final_case: dict[str, Any],
) -> list[str]:
    tags = []
    root_causes = set(manual_item.get("root_causes") or [])
    if manual_item.get("risk_level") == "high" or manual_item.get("priority_score", 0) >= 8:
        tags.append(QUEUE_HIGH_RISK)
    if scenario_case:
        tags.append(QUEUE_SCENARIO_REGISTRY)
    if base_case:
        tags.append(QUEUE_BASE_RETRIEVAL)
    if anchor_case:
        tags.append(QUEUE_ANCHOR_DEPENDENCY)
    if final_case:
        tags.append(QUEUE_FINAL_SELECTION)
    if "final_primary_gap" in root_causes or "primary_evidence_lost" in (final_case.get("detected_issues") or []):
        tags.append(QUEUE_PRIMARY_EVIDENCE)
    return unique_list(tags)


def suggested_review_questions(tags: list[str], issue_types: list[str]) -> list[str]:
    questions = []
    if QUEUE_SCENARIO_REGISTRY in tags:
        questions.append("Should the missing scenario core article remain a required core article for this scenario?")
    if QUEUE_BASE_RETRIEVAL in tags:
        questions.append("Does the base retrieval gap point to metadata, chunking, source coverage, or lexical query mismatch?")
    if QUEUE_ANCHOR_DEPENDENCY in tags:
        questions.append("Is anchor support masking weak base retrieval rather than providing healthy supplemental coverage?")
    if QUEUE_FINAL_SELECTION in tags:
        questions.append("Which evidence present at rerank_input should be preserved in final evidence?")
    if QUEUE_PRIMARY_EVIDENCE in tags:
        questions.append("Does the final answer require the missing primary evidence to be grounded?")
    if "liability_evidence_lost" in issue_types:
        questions.append("Does the report conclusion rely on liability or consequence evidence that was dropped?")
    return unique_list(questions)


def follow_up_candidates(tags: list[str], issue_types: list[str]) -> list[str]:
    actions = []
    if QUEUE_SCENARIO_REGISTRY in tags:
        actions.append("scenario_registry_core_article_review")
    if QUEUE_BASE_RETRIEVAL in tags or "metadata_or_chunking_review_candidate" in issue_types:
        actions.append("metadata_chunking_or_query_coverage_review")
    if QUEUE_ANCHOR_DEPENDENCY in tags:
        actions.append("anchor_dependency_governance_review")
    if QUEUE_FINAL_SELECTION in tags:
        actions.append("final_evidence_selection_policy_review")
    if QUEUE_PRIMARY_EVIDENCE in tags:
        actions.append("primary_evidence_fixture_candidate_review")
    if QUEUE_HIGH_RISK in tags:
        actions.append("high_risk_manual_grounding_review")
    return unique_list(actions)


def build_review_package(
    case_id_value: str,
    manual_item: dict[str, Any],
    scenario_case: dict[str, Any],
    base_case: dict[str, Any],
    anchor_case: dict[str, Any],
    final_case: dict[str, Any],
) -> dict[str, Any]:
    diagnostics = {
        "manual_dataset": {
            "present": bool(manual_item),
            "root_causes": manual_item.get("root_causes") or [],
            "priority_score": manual_item.get("priority_score"),
            "detected_issues": manual_item.get("detected_issues") or [],
            "review_questions": manual_item.get("review_questions") or [],
        },
        "scenario_registry_calibration": {
            "present": bool(scenario_case),
            "detected_issues": scenario_case.get("detected_issues") or [],
            "review_reasons": scenario_case.get("review_reasons") or [],
        },
        "base_retrieval_quality": {
            "present": bool(base_case),
            "detected_issues": base_case.get("detected_issues") or [],
            "review_reasons": base_case.get("review_reasons") or [],
        },
        "anchor_dependency": {
            "present": bool(anchor_case),
            "detected_issues": anchor_case.get("detected_issues") or [],
            "review_reasons": anchor_case.get("review_reasons") or [],
        },
        "final_evidence_selection": {
            "present": bool(final_case),
            "detected_issues": final_case.get("detected_issues") or [],
            "review_reasons": final_case.get("review_reasons") or [],
        },
    }
    issue_types = unique_list(
        diagnostics["manual_dataset"]["detected_issues"]
        + diagnostics["scenario_registry_calibration"]["detected_issues"]
        + diagnostics["base_retrieval_quality"]["detected_issues"]
        + diagnostics["anchor_dependency"]["detected_issues"]
        + diagnostics["final_evidence_selection"]["detected_issues"]
    )
    tags = queue_tags(manual_item, scenario_case, base_case, anchor_case, final_case)
    priority_score = int(manual_item.get("priority_score") or 0)
    priority_score += 3 if QUEUE_HIGH_RISK in tags else 0
    priority_score += 2 if QUEUE_FINAL_SELECTION in tags else 0
    priority_score += 2 if QUEUE_SCENARIO_REGISTRY in tags else 0
    priority_score += 1 if QUEUE_BASE_RETRIEVAL in tags else 0
    priority_score += 1 if QUEUE_ANCHOR_DEPENDENCY in tags else 0

    return {
        "case_id": case_id_value,
        "review_status": REVIEW_STATUS_PENDING,
        "priority_score": priority_score,
        "risk_level": manual_item.get("risk_level") or final_case.get("risk_level") or anchor_case.get("risk_level") or base_case.get("risk_level"),
        "expected_domains": unique_list(
            (manual_item.get("expected_domains") or [])
            + (scenario_case.get("expected_domains") or [])
            + (base_case.get("expected_domains") or [])
            + (anchor_case.get("expected_domains") or [])
            + (final_case.get("expected_domains") or [])
        ),
        "queue_tags": tags,
        "issue_types": issue_types,
        "diagnostics": diagnostics,
        "evidence_context": {
            "missing_final_expected": manual_item.get("missing_final_expected") or final_case.get("missing_final_expected") or [],
            "missing_scenario_core": manual_item.get("missing_scenario_core") or scenario_case.get("missing_scenario_core") or [],
            "lost_evidence": final_case.get("lost_evidence") or [],
            "final_evidence": manual_item.get("final_evidence") or [],
        },
        "suggested_review_questions": unique_list(
            (manual_item.get("review_questions") or [])
            + suggested_review_questions(tags, issue_types)
        ),
        "follow_up_candidates": follow_up_candidates(tags, issue_types),
        "reviewer_fields": {
            "reviewer": "",
            "reviewed_at": "",
            "decision": "",
            "confirmed_root_causes": [],
            "rejected_root_causes": [],
            "confirmed_follow_up_actions": [],
            "fixture_candidate": False,
            "notes": "",
        },
    }


def build_summary(packages: list[dict[str, Any]]) -> dict[str, Any]:
    queue_counts = Counter()
    issue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    follow_up_counts = Counter()
    fixture_candidates = 0

    for package in packages:
        for tag in package.get("queue_tags") or []:
            queue_counts[tag] += 1
        for issue in package.get("issue_types") or []:
            issue_counts[issue] += 1
        for action in package.get("follow_up_candidates") or []:
            follow_up_counts[action] += 1
        for domain in package.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["review_items"] += 1
        if QUEUE_PRIMARY_EVIDENCE in (package.get("queue_tags") or []) or QUEUE_FINAL_SELECTION in (package.get("queue_tags") or []):
            fixture_candidates += 1

    return {
        "total_review_packages": len(packages),
        "pending_review_packages": sum(1 for package in packages if package.get("review_status") == REVIEW_STATUS_PENDING),
        "queue_summary": dict(sorted(queue_counts.items())),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "follow_up_action_summary": dict(sorted(follow_up_counts.items())),
        "fixture_candidate_review_items": fixture_candidates,
    }


def build_report(
    manual_review_dataset_path: Path = DEFAULT_MANUAL_REVIEW_DATASET_PATH,
    scenario_calibration_report_path: Path = DEFAULT_SCENARIO_CALIBRATION_REPORT_PATH,
    base_audit_report_path: Path = DEFAULT_BASE_AUDIT_REPORT_PATH,
    anchor_audit_report_path: Path = DEFAULT_ANCHOR_AUDIT_REPORT_PATH,
    final_selection_audit_report_path: Path = DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH,
) -> dict[str, Any]:
    manual_dataset = load_json(manual_review_dataset_path)
    scenario_report = load_json(scenario_calibration_report_path)
    base_report = load_json(base_audit_report_path)
    anchor_report = load_json(anchor_audit_report_path)
    final_report = load_json(final_selection_audit_report_path)

    manual_by_case = review_item_map(manual_dataset)
    scenario_by_case = case_map(scenario_report)
    base_by_case = case_map(base_report)
    anchor_by_case = case_map(anchor_report)
    final_by_case = case_map(final_report)

    packages = [
        build_review_package(
            case_id_value,
            manual_by_case.get(case_id_value) or {},
            scenario_by_case.get(case_id_value) or {},
            base_by_case.get(case_id_value) or {},
            anchor_by_case.get(case_id_value) or {},
            final_by_case.get(case_id_value) or {},
        )
        for case_id_value in collect_case_ids(manual_by_case, scenario_by_case, base_by_case, anchor_by_case, final_by_case)
    ]
    packages = sorted(packages, key=lambda item: (-int(item.get("priority_score") or 0), item.get("case_id") or ""))

    return {
        "version": VERSION,
        "scope": "offline manual review loop package",
        "inputs": {
            "manual_review_dataset": str(manual_review_dataset_path),
            "manual_review_dataset_version": manual_dataset.get("version"),
            "scenario_calibration_report": str(scenario_calibration_report_path),
            "scenario_calibration_report_version": scenario_report.get("version"),
            "base_retrieval_audit_report": str(base_audit_report_path),
            "base_retrieval_audit_report_version": base_report.get("version"),
            "anchor_dependency_audit_report": str(anchor_audit_report_path),
            "anchor_dependency_audit_report_version": anchor_report.get("version"),
            "final_selection_audit_report": str(final_selection_audit_report_path),
            "final_selection_audit_report_version": final_report.get("version"),
        },
        "summary": build_summary(packages),
        "review_packages": packages,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an offline manual review loop package.")
    parser.add_argument("--manual-review-dataset", type=Path, default=DEFAULT_MANUAL_REVIEW_DATASET_PATH)
    parser.add_argument("--scenario-calibration-report", type=Path, default=DEFAULT_SCENARIO_CALIBRATION_REPORT_PATH)
    parser.add_argument("--base-audit-report", type=Path, default=DEFAULT_BASE_AUDIT_REPORT_PATH)
    parser.add_argument("--anchor-audit-report", type=Path, default=DEFAULT_ANCHOR_AUDIT_REPORT_PATH)
    parser.add_argument("--final-selection-audit-report", type=Path, default=DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        args.manual_review_dataset,
        args.scenario_calibration_report,
        args.base_audit_report,
        args.anchor_audit_report,
        args.final_selection_audit_report,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review loop package built: "
        f"{summary['total_review_packages']} packages, "
        f"{summary['pending_review_packages']} pending"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
