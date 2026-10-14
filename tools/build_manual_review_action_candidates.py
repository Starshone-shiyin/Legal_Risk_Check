"""Build offline action candidates from validated manual-review decisions.

The tool separates confirmed action candidates from pending diagnostic
suggestions. Pending records are summarized as blocked candidates, not as
authorized engineering work. It does not modify retrieval, rerank, prompts,
anchors, risk rules, eval cases, or scenario registry content.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_manual_review_decision_schema import (
    ACTION_ADDITIONAL_CAPTURE,
    ACTION_ANCHOR_GOVERNANCE,
    ACTION_FINAL_SELECTION,
    ACTION_FUNCTIONAL_FIXTURE,
    ACTION_HIGH_RISK_GROUNDING,
    ACTION_METADATA_QUERY,
    ACTION_NO_ACTION,
    ACTION_PRIMARY_FIXTURE,
    ACTION_SCENARIO_CORE,
    ACTION_SOURCE_INDEX,
    DECISION_STATUS_COMPLETED,
    ROOT_ADDITIONAL_CAPTURE,
    ROOT_ANCHOR_GOVERNANCE,
    ROOT_FINAL_SELECTION,
    ROOT_FUNCTIONAL_TYPING,
    ROOT_HIGH_RISK_GROUNDING,
    ROOT_METADATA_QUERY,
    ROOT_PRIMARY_EVIDENCE,
    ROOT_SCENARIO_CORE,
    ROOT_SOURCE_INDEX,
)
from tools.check_evidence_alignment import normalize_text
from tools.validate_manual_review_decisions import validate_record


VERSION = "0.4.7.5.2"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_VALIDATION_REPORT_PATH = Path("tests/evidence_manual_review_decision_validation_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_manual_review_action_candidates.json")

READINESS_READY = "ready_from_valid_decision"
READINESS_BLOCKED = "blocked_pending_manual_review"
READINESS_REJECTED = "rejected_no_action"

ACTION_CATEGORIES = {
    ACTION_METADATA_QUERY: "retrieval_input_quality",
    ACTION_SOURCE_INDEX: "knowledge_source_coverage",
    ACTION_ANCHOR_GOVERNANCE: "anchor_governance",
    ACTION_SCENARIO_CORE: "scenario_registry_governance",
    ACTION_FINAL_SELECTION: "final_evidence_policy",
    ACTION_PRIMARY_FIXTURE: "fixture_candidate_governance",
    ACTION_HIGH_RISK_GROUNDING: "manual_grounding_review",
    ACTION_FUNCTIONAL_FIXTURE: "functional_typing_quality",
    ACTION_ADDITIONAL_CAPTURE: "diagnostic_data_capture",
    ACTION_NO_ACTION: "no_action",
}

ACTION_TARGET_AREAS = {
    ACTION_METADATA_QUERY: ["knowledge_manifest_metadata", "chunking_quality", "query_lexical_coverage"],
    ACTION_SOURCE_INDEX: ["knowledge_source_inventory", "index_integrity_diagnostics"],
    ACTION_ANCHOR_GOVERNANCE: ["anchor_dependency_policy_draft"],
    ACTION_SCENARIO_CORE: ["scenario_registry_core_article_review"],
    ACTION_FINAL_SELECTION: ["final_evidence_selection_policy_draft"],
    ACTION_PRIMARY_FIXTURE: ["evidence_fixture_candidate_pool"],
    ACTION_HIGH_RISK_GROUNDING: ["manual_grounding_review_queue"],
    ACTION_FUNCTIONAL_FIXTURE: ["legal_functional_typing_fixture_pool"],
    ACTION_ADDITIONAL_CAPTURE: ["offline_evidence_diagnostics_capture"],
    ACTION_NO_ACTION: [],
}

ROOT_TO_ACTION = {
    ROOT_METADATA_QUERY: ACTION_METADATA_QUERY,
    ROOT_SOURCE_INDEX: ACTION_SOURCE_INDEX,
    ROOT_ANCHOR_GOVERNANCE: ACTION_ANCHOR_GOVERNANCE,
    ROOT_SCENARIO_CORE: ACTION_SCENARIO_CORE,
    ROOT_FINAL_SELECTION: ACTION_FINAL_SELECTION,
    ROOT_PRIMARY_EVIDENCE: ACTION_PRIMARY_FIXTURE,
    ROOT_HIGH_RISK_GROUNDING: ACTION_HIGH_RISK_GROUNDING,
    ROOT_FUNCTIONAL_TYPING: ACTION_FUNCTIONAL_FIXTURE,
    ROOT_ADDITIONAL_CAPTURE: ACTION_ADDITIONAL_CAPTURE,
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def case_id(record: dict[str, Any]) -> str:
    return normalize_text(record.get("case_id"))


def validation_map(validation_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case_id(item): item
        for item in validation_report.get("cases") or []
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


def action_from_root(root_cause: str) -> str | None:
    return ROOT_TO_ACTION.get(root_cause)


def confirmed_actions(record: dict[str, Any]) -> list[str]:
    decision = record.get("reviewer_decision") if isinstance(record.get("reviewer_decision"), dict) else {}
    actions = [normalize_text(item) for item in decision.get("confirmed_follow_up_actions") or [] if normalize_text(item)]
    for root_cause in decision.get("confirmed_root_causes") or []:
        action = action_from_root(normalize_text(root_cause))
        if action:
            actions.append(action)
    return unique_list(actions)


def pending_suggested_actions(record: dict[str, Any]) -> list[str]:
    return [normalize_text(item) for item in record.get("suggested_follow_up_actions") or [] if normalize_text(item)]


def candidate_for_action(record: dict[str, Any], action: str, readiness: str, validation_case: dict[str, Any]) -> dict[str, Any]:
    reviewer_decision = record.get("reviewer_decision") if isinstance(record.get("reviewer_decision"), dict) else {}
    confirmed_root_causes = reviewer_decision.get("confirmed_root_causes") or []
    suggested_root_causes = record.get("suggested_root_causes") or []
    return {
        "case_id": case_id(record),
        "action_type": action,
        "action_category": ACTION_CATEGORIES.get(action, "unknown"),
        "readiness": readiness,
        "priority_score": record.get("priority_score"),
        "risk_level": record.get("risk_level"),
        "expected_domains": record.get("expected_domains") or [],
        "source_decision_status": record.get("decision_status"),
        "validation_status": validation_case.get("validation_status"),
        "confirmed_root_causes": confirmed_root_causes,
        "suggested_root_causes": suggested_root_causes,
        "target_areas": ACTION_TARGET_AREAS.get(action, []),
        "blocked_reason": (
            "Manual decision is still pending; candidate is diagnostic-only."
            if readiness == READINESS_BLOCKED
            else ""
        ),
        "rationale": reviewer_decision.get("rationale") or "",
        "notes": reviewer_decision.get("notes") or "",
    }


def candidates_for_record(record: dict[str, Any], validation_case: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    validation_case = validation_case or validate_record(record)
    status = normalize_text(record.get("decision_status") or "pending")
    validation_status = normalize_text(validation_case.get("validation_status"))
    actions = []
    readiness = READINESS_BLOCKED

    if status == DECISION_STATUS_COMPLETED and validation_status == "valid":
        actions = confirmed_actions(record)
        if actions == [ACTION_NO_ACTION]:
            readiness = READINESS_REJECTED
        else:
            readiness = READINESS_READY
    else:
        actions = pending_suggested_actions(record)
        readiness = READINESS_BLOCKED

    return [
        candidate_for_action(record, action, readiness, validation_case)
        for action in actions
        if action
    ]


def build_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    readiness_counts = Counter()
    action_counts = Counter()
    category_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    ready_cases = set()
    blocked_cases = set()

    for candidate in candidates:
        readiness = candidate.get("readiness")
        readiness_counts[readiness] += 1
        action_counts[candidate.get("action_type")] += 1
        category_counts[candidate.get("action_category")] += 1
        if readiness == READINESS_READY:
            ready_cases.add(candidate.get("case_id"))
        if readiness == READINESS_BLOCKED:
            blocked_cases.add(candidate.get("case_id"))
        for domain in candidate.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["action_candidates"] += 1
            if readiness == READINESS_READY:
                domain_summary[domain]["ready_candidates"] += 1
            if readiness == READINESS_BLOCKED:
                domain_summary[domain]["blocked_candidates"] += 1

    return {
        "total_action_candidates": len(candidates),
        "ready_action_candidates": readiness_counts.get(READINESS_READY, 0),
        "blocked_pending_candidates": readiness_counts.get(READINESS_BLOCKED, 0),
        "rejected_no_action_candidates": readiness_counts.get(READINESS_REJECTED, 0),
        "ready_case_count": len(ready_cases),
        "blocked_case_count": len(blocked_cases),
        "readiness_summary": dict(sorted(readiness_counts.items())),
        "action_type_summary": dict(sorted(action_counts.items())),
        "action_category_summary": dict(sorted(category_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
    }


def build_report(
    decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH,
    validation_report_path: Path = DEFAULT_VALIDATION_REPORT_PATH,
) -> dict[str, Any]:
    decision_schema = load_json(decision_schema_path)
    validation_report = load_json(validation_report_path)
    by_case = validation_map(validation_report)
    candidates = []
    for record in decision_schema.get("decision_records") or []:
        if not isinstance(record, dict):
            continue
        candidates.extend(candidates_for_record(record, by_case.get(case_id(record))))
    candidates = sorted(
        candidates,
        key=lambda item: (
            item.get("readiness") != READINESS_READY,
            -int(item.get("priority_score") or 0),
            item.get("case_id") or "",
            item.get("action_type") or "",
        ),
    )
    return {
        "version": VERSION,
        "scope": "offline manual review action candidates",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "decision_schema_version": decision_schema.get("version"),
            "decision_validation_report": str(validation_report_path),
            "decision_validation_report_version": validation_report.get("version"),
        },
        "readiness_policy": {
            "ready_from_valid_decision": "Only completed, valid reviewer decisions can create ready candidates.",
            "blocked_pending_manual_review": "Pending records are diagnostic-only and require human confirmation.",
            "rejected_no_action": "Reviewer rejected the diagnostic issue or selected no action.",
        },
        "summary": build_summary(candidates),
        "action_candidates": candidates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build offline action candidates from manual-review decisions.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema, args.validation_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review action candidates built: "
        f"{summary['total_action_candidates']} candidates, "
        f"{summary['ready_action_candidates']} ready, "
        f"{summary['blocked_pending_candidates']} blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
