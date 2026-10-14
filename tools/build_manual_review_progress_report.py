"""Build an offline manual-review progress report.

The progress report measures reviewer completion, validation quality, and
blocked downstream candidates. It does not infer reviewer conclusions or modify
the decision schema, eval cases, hidden seeds, retrieval, rerank, prompts,
anchors, or risk rules.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VERSION = "0.4.7.6.2"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_VALIDATION_REPORT_PATH = Path("tests/evidence_manual_review_decision_validation_report.json")
DEFAULT_WORKBENCH_PATH = Path("tests/evidence_manual_review_workbench.json")
DEFAULT_ACTION_CANDIDATES_PATH = Path("tests/evidence_manual_review_action_candidates.json")
DEFAULT_FIXTURE_POOL_PATH = Path("tests/evidence_fixture_candidate_pool.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_manual_review_progress_report.json")


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def case_id(item: dict[str, Any]) -> str:
    value = item.get("case_id")
    return str(value).strip() if value is not None else ""


def map_by_case(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in items
        if isinstance(item, dict) and case_id(item)
    }


def action_counts_by_case(action_report: dict[str, Any]) -> dict[str, Counter]:
    result: dict[str, Counter] = defaultdict(Counter)
    for item in action_report.get("action_candidates") or []:
        if not isinstance(item, dict) or not case_id(item):
            continue
        result[case_id(item)][item.get("readiness") or "unknown"] += 1
    return result


def fixture_counts_by_case(fixture_pool: dict[str, Any]) -> dict[str, Counter]:
    result: dict[str, Counter] = defaultdict(Counter)
    for item in fixture_pool.get("fixture_candidates") or []:
        if not isinstance(item, dict) or not case_id(item):
            continue
        result[case_id(item)][item.get("fixture_status") or "unknown"] += 1
    return result


def progress_case(
    record: dict[str, Any],
    validation_case: dict[str, Any],
    workbench_item: dict[str, Any],
    action_counts: Counter,
    fixture_counts: Counter,
) -> dict[str, Any]:
    decision_status = record.get("decision_status") or "pending"
    validation_status = validation_case.get("validation_status") or "unknown"
    blockers = []
    if decision_status == "pending":
        blockers.append("awaiting_manual_decision")
    if validation_status == "invalid":
        blockers.append("invalid_manual_decision")
    if action_counts.get("blocked_pending_manual_review", 0):
        blockers.append("blocked_action_candidates")
    if fixture_counts.get("blocked_pending_manual_review", 0):
        blockers.append("blocked_fixture_candidates")
    return {
        "case_id": case_id(record),
        "decision_status": decision_status,
        "validation_status": validation_status,
        "priority_score": record.get("priority_score"),
        "risk_level": record.get("risk_level"),
        "expected_domains": record.get("expected_domains") or [],
        "queue_tags": record.get("queue_tags") or [],
        "workbench_rank": workbench_item.get("rank"),
        "ready_action_candidates": action_counts.get("ready_from_valid_decision", 0),
        "blocked_action_candidates": action_counts.get("blocked_pending_manual_review", 0),
        "ready_fixture_candidates": fixture_counts.get("ready_from_valid_decision", 0),
        "blocked_fixture_candidates": fixture_counts.get("blocked_pending_manual_review", 0),
        "blockers": blockers,
    }


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    decision_status_counts = Counter()
    validation_status_counts = Counter()
    blocker_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    total_ready_actions = 0
    total_blocked_actions = 0
    total_ready_fixtures = 0
    total_blocked_fixtures = 0

    for item in cases:
        decision_status_counts[item.get("decision_status")] += 1
        validation_status_counts[item.get("validation_status")] += 1
        total_ready_actions += int(item.get("ready_action_candidates") or 0)
        total_blocked_actions += int(item.get("blocked_action_candidates") or 0)
        total_ready_fixtures += int(item.get("ready_fixture_candidates") or 0)
        total_blocked_fixtures += int(item.get("blocked_fixture_candidates") or 0)
        for blocker in item.get("blockers") or []:
            blocker_counts[blocker] += 1
        for domain in item.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["review_cases"] += 1
            if item.get("decision_status") == "pending":
                domain_summary[domain]["pending_cases"] += 1
            if item.get("validation_status") == "invalid":
                domain_summary[domain]["invalid_cases"] += 1

    total = len(cases)
    completed = decision_status_counts.get("completed", 0)
    valid = validation_status_counts.get("valid", 0)
    return {
        "total_cases": total,
        "completed_cases": completed,
        "pending_cases": decision_status_counts.get("pending", 0),
        "deferred_cases": decision_status_counts.get("deferred", 0),
        "valid_cases": valid,
        "invalid_cases": validation_status_counts.get("invalid", 0),
        "completion_ratio": round(completed / total, 3) if total else 0.0,
        "valid_completion_ratio": round(valid / total, 3) if total else 0.0,
        "ready_action_candidates": total_ready_actions,
        "blocked_action_candidates": total_blocked_actions,
        "ready_fixture_candidates": total_ready_fixtures,
        "blocked_fixture_candidates": total_blocked_fixtures,
        "decision_status_summary": dict(sorted(decision_status_counts.items())),
        "validation_status_summary": dict(sorted(validation_status_counts.items())),
        "blocker_summary": dict(sorted(blocker_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
    }


def build_report(
    decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH,
    validation_report_path: Path = DEFAULT_VALIDATION_REPORT_PATH,
    workbench_path: Path = DEFAULT_WORKBENCH_PATH,
    action_candidates_path: Path = DEFAULT_ACTION_CANDIDATES_PATH,
    fixture_pool_path: Path = DEFAULT_FIXTURE_POOL_PATH,
) -> dict[str, Any]:
    decision_schema = load_json(decision_schema_path)
    validation_report = load_json(validation_report_path)
    workbench = load_json(workbench_path)
    action_report = load_json(action_candidates_path)
    fixture_pool = load_json(fixture_pool_path)

    validation_by_case = map_by_case(validation_report.get("cases") or [])
    workbench_by_case = map_by_case(workbench.get("workbench_items") or [])
    actions_by_case = action_counts_by_case(action_report)
    fixtures_by_case = fixture_counts_by_case(fixture_pool)

    cases = []
    for record in decision_schema.get("decision_records") or []:
        if not isinstance(record, dict) or not case_id(record):
            continue
        cid = case_id(record)
        cases.append(
            progress_case(
                record,
                validation_by_case.get(cid) or {},
                workbench_by_case.get(cid) or {},
                actions_by_case.get(cid) or Counter(),
                fixtures_by_case.get(cid) or Counter(),
            )
        )
    cases = sorted(cases, key=lambda item: (-int(item.get("priority_score") or 0), item.get("case_id") or ""))
    return {
        "version": VERSION,
        "scope": "offline manual review progress report",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "decision_schema_version": decision_schema.get("version"),
            "decision_validation_report": str(validation_report_path),
            "decision_validation_report_version": validation_report.get("version"),
            "workbench": str(workbench_path),
            "workbench_version": workbench.get("version"),
            "action_candidates": str(action_candidates_path),
            "action_candidates_version": action_report.get("version"),
            "fixture_pool": str(fixture_pool_path),
            "fixture_pool_version": fixture_pool.get("version"),
        },
        "summary": build_summary(cases),
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manual review progress report.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument("--workbench", type=Path, default=DEFAULT_WORKBENCH_PATH)
    parser.add_argument("--action-candidates", type=Path, default=DEFAULT_ACTION_CANDIDATES_PATH)
    parser.add_argument("--fixture-pool", type=Path, default=DEFAULT_FIXTURE_POOL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema, args.validation_report, args.workbench, args.action_candidates, args.fixture_pool)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review progress report built: "
        f"{summary['total_cases']} cases, "
        f"{summary['completed_cases']} completed, "
        f"{summary['pending_cases']} pending"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
