"""Build an offline manual-review decision schema.

This tool turns pending manual review packages into structured reviewer
decision records. It does not write reviewer conclusions, modify eval cases,
patch hidden seeds, or change retrieval, rerank, prompts, anchors, or risk
rules.
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


VERSION = "0.4.7.5.0"

DEFAULT_MANUAL_REVIEW_LOOP_PATH = Path("tests/evidence_manual_review_loop_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_manual_review_decision_schema.json")

DECISION_STATUS_PENDING = "pending"
DECISION_STATUS_COMPLETED = "completed"
DECISION_STATUS_DEFERRED = "deferred"

DECISION_CONFIRM_ISSUE = "confirm_diagnostic_issue"
DECISION_CONFIRM_SCOPE = "confirm_scope_adjustment_needed"
DECISION_REJECT_ISSUE = "reject_diagnostic_issue"
DECISION_INSUFFICIENT_INFO = "insufficient_information"
DECISION_DEFER = "defer"

ROOT_METADATA_QUERY = "metadata_chunking_or_query_coverage"
ROOT_SOURCE_INDEX = "source_or_index_coverage"
ROOT_ANCHOR_GOVERNANCE = "anchor_dependency_governance"
ROOT_SCENARIO_CORE = "scenario_core_scope"
ROOT_FINAL_SELECTION = "final_evidence_selection_policy"
ROOT_PRIMARY_EVIDENCE = "primary_evidence_gap"
ROOT_HIGH_RISK_GROUNDING = "high_risk_grounding_gap"
ROOT_FUNCTIONAL_TYPING = "functional_typing_metadata"
ROOT_ADDITIONAL_CAPTURE = "insufficient_saved_evidence"

ACTION_METADATA_QUERY = "metadata_chunking_or_query_coverage_review"
ACTION_SOURCE_INDEX = "source_index_coverage_review"
ACTION_ANCHOR_GOVERNANCE = "anchor_dependency_governance_review"
ACTION_SCENARIO_CORE = "scenario_registry_core_article_review"
ACTION_FINAL_SELECTION = "final_evidence_selection_policy_review"
ACTION_PRIMARY_FIXTURE = "primary_evidence_fixture_candidate_review"
ACTION_HIGH_RISK_GROUNDING = "high_risk_manual_grounding_review"
ACTION_FUNCTIONAL_FIXTURE = "functional_typing_fixture_review"
ACTION_ADDITIONAL_CAPTURE = "needs_additional_evidence_capture"
ACTION_NO_ACTION = "no_action"

ALLOWED_DECISIONS = [
    DECISION_CONFIRM_ISSUE,
    DECISION_CONFIRM_SCOPE,
    DECISION_REJECT_ISSUE,
    DECISION_INSUFFICIENT_INFO,
    DECISION_DEFER,
]

ALLOWED_ROOT_CAUSES = [
    ROOT_METADATA_QUERY,
    ROOT_SOURCE_INDEX,
    ROOT_ANCHOR_GOVERNANCE,
    ROOT_SCENARIO_CORE,
    ROOT_FINAL_SELECTION,
    ROOT_PRIMARY_EVIDENCE,
    ROOT_HIGH_RISK_GROUNDING,
    ROOT_FUNCTIONAL_TYPING,
    ROOT_ADDITIONAL_CAPTURE,
]

ALLOWED_FOLLOW_UP_ACTIONS = [
    ACTION_METADATA_QUERY,
    ACTION_SOURCE_INDEX,
    ACTION_ANCHOR_GOVERNANCE,
    ACTION_SCENARIO_CORE,
    ACTION_FINAL_SELECTION,
    ACTION_PRIMARY_FIXTURE,
    ACTION_HIGH_RISK_GROUNDING,
    ACTION_FUNCTIONAL_FIXTURE,
    ACTION_ADDITIONAL_CAPTURE,
    ACTION_NO_ACTION,
]

ROOT_CAUSE_TO_FOLLOW_UP_ACTIONS = {
    ROOT_METADATA_QUERY: [ACTION_METADATA_QUERY],
    ROOT_SOURCE_INDEX: [ACTION_SOURCE_INDEX],
    ROOT_ANCHOR_GOVERNANCE: [ACTION_ANCHOR_GOVERNANCE],
    ROOT_SCENARIO_CORE: [ACTION_SCENARIO_CORE],
    ROOT_FINAL_SELECTION: [ACTION_FINAL_SELECTION],
    ROOT_PRIMARY_EVIDENCE: [ACTION_PRIMARY_FIXTURE],
    ROOT_HIGH_RISK_GROUNDING: [ACTION_HIGH_RISK_GROUNDING],
    ROOT_FUNCTIONAL_TYPING: [ACTION_FUNCTIONAL_FIXTURE],
    ROOT_ADDITIONAL_CAPTURE: [ACTION_ADDITIONAL_CAPTURE],
}

PROHIBITED_CHANGE_TARGETS = [
    "hidden_seed",
    "hidden_eval",
    "rag_anchor_rules",
    "anchor_rule",
    "rerank",
    "reranker",
    "prompt",
    "risk_payload_supplement",
    "term_preservation",
    "rag_eval_cases",
    "eval_case",
    "rag_query_main_flow",
]

GLOBAL_GUARDRAILS = [
    "Do not fix hidden seed.",
    "Do not add or modify anchors.",
    "Do not modify rerank.",
    "Do not modify prompt.",
    "Do not modify risk supplement or term preservation rules.",
    "Do not modify eval cases.",
    "Do not connect diagnostics to rag_query main flow.",
    "Do not treat diagnostics as automatic repair instructions.",
]


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def suggest_root_causes(package: dict[str, Any]) -> list[str]:
    queue_tags = set(package.get("queue_tags") or [])
    issue_types = set(package.get("issue_types") or [])
    follow_ups = set(package.get("follow_up_candidates") or [])
    suggestions = []

    if "base_retrieval_quality_review" in queue_tags or "metadata_or_chunking_review_candidate" in issue_types:
        suggestions.append(ROOT_METADATA_QUERY)
    if "index_or_source_coverage_review_candidate" in issue_types:
        suggestions.append(ROOT_SOURCE_INDEX)
    if "anchor_dependency_review" in queue_tags or "anchor_masking_base_retrieval_gap" in issue_types:
        suggestions.append(ROOT_ANCHOR_GOVERNANCE)
    if "scenario_registry_calibration" in queue_tags or "registry_core_review_needed" in issue_types:
        suggestions.append(ROOT_SCENARIO_CORE)
    if "final_evidence_selection_review" in queue_tags or "rerank_input_to_final_loss" in issue_types:
        suggestions.append(ROOT_FINAL_SELECTION)
    if "primary_evidence_review" in queue_tags or "final_primary_gap" in issue_types or "primary_evidence_lost" in issue_types:
        suggestions.append(ROOT_PRIMARY_EVIDENCE)
    if "high_risk_grounding_review" in queue_tags or "high_risk_manual_grounding_review" in follow_ups:
        suggestions.append(ROOT_HIGH_RISK_GROUNDING)
    if "definition_core_candidate" in issue_types or "operative_evidence_lost" in issue_types:
        suggestions.append(ROOT_FUNCTIONAL_TYPING)
    return unique_list(suggestions)


def suggest_follow_up_actions(package: dict[str, Any], root_causes: list[str]) -> list[str]:
    actions = list(package.get("follow_up_candidates") or [])
    for root_cause in root_causes:
        actions.extend(ROOT_CAUSE_TO_FOLLOW_UP_ACTIONS.get(root_cause, []))
    return [action for action in unique_list(actions) if action in ALLOWED_FOLLOW_UP_ACTIONS]


def compact_diagnostics(package: dict[str, Any]) -> dict[str, Any]:
    diagnostics = package.get("diagnostics") or {}
    compact: dict[str, Any] = {}
    for name, value in diagnostics.items():
        if not isinstance(value, dict) or not value.get("present"):
            continue
        compact[name] = {
            "detected_issues": value.get("detected_issues") or [],
            "review_reasons": value.get("review_reasons") or [],
            "root_causes": value.get("root_causes") or [],
        }
    return compact


def decision_record(package: dict[str, Any]) -> dict[str, Any]:
    case_id = normalize_text(package.get("case_id"))
    root_causes = suggest_root_causes(package)
    actions = suggest_follow_up_actions(package, root_causes)
    return {
        "case_id": case_id,
        "decision_status": DECISION_STATUS_PENDING,
        "source_review_status": package.get("review_status"),
        "priority_score": package.get("priority_score"),
        "risk_level": package.get("risk_level"),
        "expected_domains": package.get("expected_domains") or [],
        "queue_tags": package.get("queue_tags") or [],
        "issue_types": package.get("issue_types") or [],
        "diagnostic_summary": compact_diagnostics(package),
        "evidence_context": package.get("evidence_context") or {},
        "suggested_review_questions": package.get("suggested_review_questions") or [],
        "suggested_root_causes": root_causes,
        "suggested_follow_up_actions": actions,
        "reviewer_decision": {
            "reviewer": "",
            "reviewed_at": "",
            "decision": "",
            "confirmed_root_causes": [],
            "rejected_root_causes": [],
            "confirmed_follow_up_actions": [],
            "proposed_change_targets": [],
            "fixture_candidate": False,
            "rationale": "",
            "notes": "",
        },
    }


def schema_definition() -> dict[str, Any]:
    return {
        "decision_status_values": [
            DECISION_STATUS_PENDING,
            DECISION_STATUS_COMPLETED,
            DECISION_STATUS_DEFERRED,
        ],
        "allowed_decisions": ALLOWED_DECISIONS,
        "allowed_root_causes": ALLOWED_ROOT_CAUSES,
        "allowed_follow_up_actions": ALLOWED_FOLLOW_UP_ACTIONS,
        "root_cause_to_follow_up_actions": ROOT_CAUSE_TO_FOLLOW_UP_ACTIONS,
        "required_reviewer_fields": [
            "reviewer",
            "reviewed_at",
            "decision",
            "confirmed_root_causes",
            "rejected_root_causes",
            "confirmed_follow_up_actions",
            "proposed_change_targets",
            "fixture_candidate",
            "rationale",
            "notes",
        ],
        "prohibited_change_targets": PROHIBITED_CHANGE_TARGETS,
        "global_guardrails": GLOBAL_GUARDRAILS,
        "interpretation": (
            "This schema captures manual grounding-quality decisions only. "
            "It is not a patching mechanism and does not authorize main-flow changes."
        ),
    }


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts = Counter()
    root_cause_counts = Counter()
    action_counts = Counter()
    queue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    high_priority = []

    for record in records:
        for issue in record.get("issue_types") or []:
            issue_counts[issue] += 1
        for root_cause in record.get("suggested_root_causes") or []:
            root_cause_counts[root_cause] += 1
        for action in record.get("suggested_follow_up_actions") or []:
            action_counts[action] += 1
        for tag in record.get("queue_tags") or []:
            queue_counts[tag] += 1
        for domain in record.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["decision_records"] += 1
        if record.get("risk_level") == "high" or int(record.get("priority_score") or 0) >= 10:
            high_priority.append(record.get("case_id"))

    return {
        "total_decision_records": len(records),
        "pending_decisions": sum(1 for record in records if record.get("decision_status") == DECISION_STATUS_PENDING),
        "completed_decisions": sum(1 for record in records if record.get("decision_status") == DECISION_STATUS_COMPLETED),
        "deferred_decisions": sum(1 for record in records if record.get("decision_status") == DECISION_STATUS_DEFERRED),
        "queue_summary": dict(sorted(queue_counts.items())),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "suggested_root_cause_summary": dict(sorted(root_cause_counts.items())),
        "suggested_follow_up_action_summary": dict(sorted(action_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "high_priority_manual_decision_list": high_priority,
    }


def build_report(manual_review_loop_path: Path = DEFAULT_MANUAL_REVIEW_LOOP_PATH) -> dict[str, Any]:
    manual_review_loop = load_json(manual_review_loop_path)
    records = [
        decision_record(package)
        for package in manual_review_loop.get("review_packages") or []
        if isinstance(package, dict) and normalize_text(package.get("case_id"))
    ]
    records = sorted(records, key=lambda item: (-int(item.get("priority_score") or 0), item.get("case_id") or ""))

    return {
        "version": VERSION,
        "scope": "offline manual review decision schema",
        "inputs": {
            "manual_review_loop_report": str(manual_review_loop_path),
            "manual_review_loop_report_version": manual_review_loop.get("version"),
        },
        "schema": schema_definition(),
        "summary": build_summary(records),
        "decision_records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an offline manual-review decision schema.")
    parser.add_argument("--manual-review-loop", type=Path, default=DEFAULT_MANUAL_REVIEW_LOOP_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.manual_review_loop)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review decision schema built: "
        f"{summary['total_decision_records']} records, "
        f"{summary['pending_decisions']} pending"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
