"""Validate offline manual-review decisions.

This tool validates reviewer-filled decision records against the schema built
in v0.4.7.5.0. It does not infer missing reviewer conclusions, mutate action
plans, patch eval cases, or change retrieval, rerank, prompts, anchors, or risk
rules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_manual_review_decision_schema import (
    ACTION_NO_ACTION,
    ALLOWED_DECISIONS,
    ALLOWED_FOLLOW_UP_ACTIONS,
    ALLOWED_ROOT_CAUSES,
    DECISION_CONFIRM_ISSUE,
    DECISION_CONFIRM_SCOPE,
    DECISION_DEFER,
    DECISION_INSUFFICIENT_INFO,
    DECISION_REJECT_ISSUE,
    DECISION_STATUS_COMPLETED,
    DECISION_STATUS_DEFERRED,
    DECISION_STATUS_PENDING,
    PROHIBITED_CHANGE_TARGETS,
    ROOT_CAUSE_TO_FOLLOW_UP_ACTIONS,
)
from tools.check_evidence_alignment import normalize_text


VERSION = "0.4.7.5.1"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_manual_review_decision_validation_report.json")

ERROR_MISSING_CASE_ID = "missing_case_id"
ERROR_INVALID_STATUS = "invalid_decision_status"
ERROR_INVALID_DECISION = "invalid_decision_value"
ERROR_MISSING_REVIEWER = "missing_reviewer_for_completed_decision"
ERROR_MISSING_REVIEWED_AT = "missing_reviewed_at_for_completed_decision"
ERROR_MISSING_RATIONALE = "missing_rationale_for_completed_decision"
ERROR_INVALID_REVIEWED_AT = "invalid_reviewed_at_format"
ERROR_INVALID_ROOT_CAUSE = "invalid_confirmed_root_cause"
ERROR_INVALID_REJECTED_ROOT_CAUSE = "invalid_rejected_root_cause"
ERROR_INVALID_ACTION = "invalid_confirmed_follow_up_action"
ERROR_ACTION_WITHOUT_ROOT_CAUSE = "follow_up_action_without_matching_root_cause"
ERROR_PROHIBITED_CHANGE_TARGET = "prohibited_change_target"
ERROR_NO_ACTION_WITH_OTHER_ACTIONS = "no_action_mixed_with_other_actions"
ERROR_REJECTION_WITH_CONFIRMED_ACTIONS = "rejection_decision_has_confirmed_actions"
ERROR_COMPLETED_DECISION_EMPTY = "completed_decision_without_outcome"

WARNING_PENDING_WITH_REVIEWER_CONTENT = "pending_decision_has_reviewer_content"
WARNING_DEFER_WITH_CONFIRMED_ACTIONS = "deferred_decision_has_confirmed_actions"
WARNING_FIXTURE_WITHOUT_PRIMARY_CAUSE = "fixture_candidate_without_primary_or_functional_cause"

REVIEWED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ][0-2]\d:[0-5]\d(?::[0-5]\d)?)?$")


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def has_reviewer_content(decision: dict[str, Any]) -> bool:
    for key, value in decision.items():
        if isinstance(value, bool):
            if value:
                return True
        elif isinstance(value, list):
            if value:
                return True
        elif normalize_text(value):
            return True
    return False


def matching_actions_for_root_causes(root_causes: list[str]) -> set[str]:
    actions: set[str] = set()
    for root_cause in root_causes:
        actions.update(ROOT_CAUSE_TO_FOLLOW_UP_ACTIONS.get(root_cause, []))
    return actions


def target_is_prohibited(target: Any) -> bool:
    text = normalize_text(target).lower()
    if not text:
        return False
    return any(prohibited.lower() in text for prohibited in PROHIBITED_CHANGE_TARGETS)


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    case_id = normalize_text(record.get("case_id"))
    if not case_id:
        errors.append(ERROR_MISSING_CASE_ID)

    status = normalize_text(record.get("decision_status") or DECISION_STATUS_PENDING)
    if status not in {DECISION_STATUS_PENDING, DECISION_STATUS_COMPLETED, DECISION_STATUS_DEFERRED}:
        errors.append(ERROR_INVALID_STATUS)

    reviewer_decision = record.get("reviewer_decision") if isinstance(record.get("reviewer_decision"), dict) else {}
    decision_value = normalize_text(reviewer_decision.get("decision"))
    confirmed_root_causes = [normalize_text(item) for item in as_list(reviewer_decision.get("confirmed_root_causes")) if normalize_text(item)]
    rejected_root_causes = [normalize_text(item) for item in as_list(reviewer_decision.get("rejected_root_causes")) if normalize_text(item)]
    confirmed_actions = [normalize_text(item) for item in as_list(reviewer_decision.get("confirmed_follow_up_actions")) if normalize_text(item)]
    proposed_targets = [normalize_text(item) for item in as_list(reviewer_decision.get("proposed_change_targets")) if normalize_text(item)]

    if status == DECISION_STATUS_PENDING and has_reviewer_content(reviewer_decision):
        warnings.append(WARNING_PENDING_WITH_REVIEWER_CONTENT)

    if status == DECISION_STATUS_COMPLETED:
        if decision_value not in ALLOWED_DECISIONS:
            errors.append(ERROR_INVALID_DECISION)
        if not normalize_text(reviewer_decision.get("reviewer")):
            errors.append(ERROR_MISSING_REVIEWER)
        reviewed_at = normalize_text(reviewer_decision.get("reviewed_at"))
        if not reviewed_at:
            errors.append(ERROR_MISSING_REVIEWED_AT)
        elif not REVIEWED_AT_RE.match(reviewed_at):
            errors.append(ERROR_INVALID_REVIEWED_AT)
        if not normalize_text(reviewer_decision.get("rationale")):
            errors.append(ERROR_MISSING_RATIONALE)
        if (
            decision_value in {DECISION_CONFIRM_ISSUE, DECISION_CONFIRM_SCOPE}
            and not confirmed_root_causes
            and not confirmed_actions
        ):
            errors.append(ERROR_COMPLETED_DECISION_EMPTY)

    if status == DECISION_STATUS_DEFERRED:
        if decision_value not in {"", DECISION_DEFER, DECISION_INSUFFICIENT_INFO}:
            errors.append(ERROR_INVALID_DECISION)
        if confirmed_actions:
            warnings.append(WARNING_DEFER_WITH_CONFIRMED_ACTIONS)

    for root_cause in confirmed_root_causes:
        if root_cause not in ALLOWED_ROOT_CAUSES:
            errors.append(ERROR_INVALID_ROOT_CAUSE)
    for root_cause in rejected_root_causes:
        if root_cause not in ALLOWED_ROOT_CAUSES:
            errors.append(ERROR_INVALID_REJECTED_ROOT_CAUSE)
    for action in confirmed_actions:
        if action not in ALLOWED_FOLLOW_UP_ACTIONS:
            errors.append(ERROR_INVALID_ACTION)

    if ACTION_NO_ACTION in confirmed_actions and len(confirmed_actions) > 1:
        errors.append(ERROR_NO_ACTION_WITH_OTHER_ACTIONS)
    if decision_value == DECISION_REJECT_ISSUE and [action for action in confirmed_actions if action != ACTION_NO_ACTION]:
        errors.append(ERROR_REJECTION_WITH_CONFIRMED_ACTIONS)

    allowed_actions = matching_actions_for_root_causes(confirmed_root_causes)
    for action in confirmed_actions:
        if action == ACTION_NO_ACTION:
            continue
        if action not in allowed_actions:
            errors.append(ERROR_ACTION_WITHOUT_ROOT_CAUSE)
            break

    for target in proposed_targets:
        if target_is_prohibited(target):
            errors.append(ERROR_PROHIBITED_CHANGE_TARGET)
            break

    if reviewer_decision.get("fixture_candidate") and not (
        {"primary_evidence_gap", "functional_typing_metadata"} & set(confirmed_root_causes)
    ):
        warnings.append(WARNING_FIXTURE_WITHOUT_PRIMARY_CAUSE)

    validation_status = "valid" if not errors else "invalid"
    if status == DECISION_STATUS_PENDING and not errors:
        validation_status = "pending"

    return {
        "case_id": case_id,
        "decision_status": status or DECISION_STATUS_PENDING,
        "validation_status": validation_status,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "confirmed_root_causes": confirmed_root_causes,
        "confirmed_follow_up_actions": confirmed_actions,
        "proposed_change_targets": proposed_targets,
    }


def build_summary(validation_cases: list[dict[str, Any]]) -> dict[str, Any]:
    error_counts = Counter()
    warning_counts = Counter()
    status_counts = Counter()
    root_cause_counts = Counter()
    action_counts = Counter()
    invalid_cases = []

    for case in validation_cases:
        status_counts[case.get("validation_status")] += 1
        for error in case.get("errors") or []:
            error_counts[error] += 1
        for warning in case.get("warnings") or []:
            warning_counts[warning] += 1
        for root_cause in case.get("confirmed_root_causes") or []:
            root_cause_counts[root_cause] += 1
        for action in case.get("confirmed_follow_up_actions") or []:
            action_counts[action] += 1
        if case.get("validation_status") == "invalid":
            invalid_cases.append({
                "case_id": case.get("case_id"),
                "errors": case.get("errors") or [],
            })

    return {
        "total_records": len(validation_cases),
        "valid_records": status_counts.get("valid", 0),
        "pending_records": status_counts.get("pending", 0),
        "invalid_records": status_counts.get("invalid", 0),
        "error_summary": dict(sorted(error_counts.items())),
        "warning_summary": dict(sorted(warning_counts.items())),
        "confirmed_root_cause_summary": dict(sorted(root_cause_counts.items())),
        "confirmed_follow_up_action_summary": dict(sorted(action_counts.items())),
        "invalid_manual_review_list": invalid_cases,
    }


def build_report(decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH) -> dict[str, Any]:
    decision_schema = load_json(decision_schema_path)
    validation_cases = [
        validate_record(record)
        for record in decision_schema.get("decision_records") or []
        if isinstance(record, dict)
    ]
    return {
        "version": VERSION,
        "scope": "offline manual review decision validation",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "decision_schema_version": decision_schema.get("version"),
        },
        "summary": build_summary(validation_cases),
        "cases": validation_cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate offline manual-review decisions.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--fail-on-invalid",
        action="store_true",
        help="Return non-zero if any completed decision is invalid.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review decision validation completed: "
        f"{summary['total_records']} records, "
        f"{summary['invalid_records']} invalid, "
        f"{summary['pending_records']} pending"
    )
    if args.fail_on_invalid and summary["invalid_records"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
