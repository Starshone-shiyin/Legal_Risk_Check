"""Build a user-confirmed closeout record for ready-action design tracks.

The confirmation record reads the saved v0.4.7.9.5 draft and records the user's
confirmation of the five draft directions. This record may route tracks to
future design planning, but it does not authorize implementation, create
engineering tasks, become a manual-review importer decision, call RAG, contact
Qdrant or an LLM, or mutate retrieval, prompts, rules, fixtures, scenario
registry entries, eval cases, hidden seeds, anchors, schema/importer contracts,
dry-run contracts, or the main flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.9.6"

DEFAULT_DRAFT_REPORT_PATH = legacy_report_path("ready_action_human_closeout_decision_draft_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ready_action_human_closeout_confirmation_record_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md")

EXPECTED_DRAFT_VERSION = "0.4.7.9.5"
EXPECTED_DRAFT_SCHEMA = "ready_action_human_closeout_decision_draft"
EXPECTED_READY_ACTION_COUNT = 18
EXPECTED_SOURCE_CASE_COUNT = 5
EXPECTED_TRACK_COUNT = 5
EXPECTED_PENDING_EXCLUDED = 31

EXPECTED_REVIEW_ORDER = [
    "final_evidence_selection_policy_review",
    "primary_evidence_fixture_candidate_review",
    "high_risk_manual_grounding_review",
    "scenario_registry_core_article_review",
    "functional_typing_fixture_review",
]

USER_CONFIRMATION_CONTEXT = {
    "source": "chat_user_confirmation",
    "confirmation_text": "用户确认 v0.4.7.9.5 的 5 条草案方向。",
    "confirmed_at_version": VERSION,
    "confirmed_scope": "design_closeout_direction_only",
    "manual_review_importable": False,
    "implementation_allowed": False,
}

CONFIRMATION_GUARDRAILS = {
    "confirmation_record_only": True,
    "source_draft_only": True,
    "user_confirmation_recorded": True,
    "formal_design_closeout_recorded": True,
    "manual_review_importable": False,
    "not_completed_manual_review_decision": True,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "next_design_authorized": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
    "pending_records_to_work_items": "disallowed",
    "confirmed_route_to_work_items": "disallowed",
    "fixture_write_to_eval": "disallowed",
    "schema_mutation": "disallowed",
    "manual_review_schema_mutation": "disallowed",
    "manual_review_importer_mutation": "disallowed",
    "manual_review_dry_run_contract_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "rag_query_integration": "disallowed",
    "main_flow_mutation": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
}

DESIGN_TRACK_AUTHORITY = {
    "future_design_planning_allowed": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "requires_new_version_for_design_spec": True,
    "requires_new_user_approval_for_implementation": True,
}

FORBIDDEN_SOURCE_KEYS = {
    "approved",
    "approved_actions",
    "authorized_actions",
    "ready_to_apply",
    "ready_to_implement",
    "implementation_plan",
    "patch_plan",
    "files_to_change",
    "commands",
    "migration_steps",
    "reviewer_decision",
    "reviewer_input_template",
    "decision_status",
    "decision",
    "reviewer",
    "reviewed_at",
    "confirmed_root_causes",
    "confirmed_follow_up_actions",
    "proposed_change_targets",
    "fixture_candidate",
    "workbench_items",
    "work_items",
    "engineering_tasks",
    "pending_tasks",
    "implementation_queue",
    "pending_candidates",
    "pending_backlog",
    "completed_decisions",
    "completed_outcomes",
    "formal_review_outcomes",
    "human_outcome_record",
    "promotion_candidates_generated",
    "ready_action_candidates_generated",
}

FORBIDDEN_OUTPUT_KEYS = set(FORBIDDEN_SOURCE_KEYS)

ADVISORY_SOURCE_KEYS = {
    "ai_suggestion",
    "safe_ai_suggestion_input",
    "advisory_packet_only",
    "prescreen_advisory",
    "pilot_assist",
    "mobile_aid",
    "contains_completed_manual_decisions",
}

MOJIBAKE_MARKERS = [
    "\u951b",
    "\u7ecb",
    "\u9428",
    "\u93c2",
    "\u6d93",
    "\u4e63",
    "\ufffd",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return str(value or "").strip()


def sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "scope": data.get("scope"),
        "schema_kind": data.get("schema_kind"),
    }


def key_violations(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    forbidden: list[str] = []
    advisory: list[str] = []
    for node in walk_dicts(data):
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            if key in FORBIDDEN_SOURCE_KEYS:
                forbidden.append(key)
            if key in ADVISORY_SOURCE_KEYS and value:
                advisory.append(key)
            if key.startswith("advisory_") and value:
                advisory.append(key)
            if key.startswith("prescreen_") and value:
                advisory.append(key)
    return sorted_unique(forbidden), sorted_unique(advisory)


def readability_violations(value: Any) -> list[str]:
    matches: list[str] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                visit(child, f"{path}.{key}" if path else str(key))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{path}[{index}]")
        elif isinstance(node, str) and any(marker in node for marker in MOJIBAKE_MARKERS):
            matches.append(path or "<root>")

    visit(value, "")
    return sorted_unique(matches)


def draft_contract_blockers(draft_report: dict[str, Any]) -> list[str]:
    if not draft_report:
        return ["missing_or_invalid_draft_report"]

    blockers: list[str] = []
    gate = as_dict(draft_report.get("draft_gate"))
    summary = as_dict(draft_report.get("summary"))
    implementation_gate = as_dict(draft_report.get("implementation_gate"))
    matrix = as_list(draft_report.get("draft_matrix"))
    assertions = as_list(draft_report.get("assertions"))

    if draft_report.get("version") != EXPECTED_DRAFT_VERSION:
        blockers.append("draft_version_mismatch")
    if draft_report.get("schema_kind") != EXPECTED_DRAFT_SCHEMA:
        blockers.append("draft_schema_mismatch")
    if gate.get("status") != "draft_pending_user_confirmation":
        blockers.append("draft_gate_not_pending_confirmation")
    if gate.get("requires_user_confirmation") is not True:
        blockers.append("draft_user_confirmation_not_required")
    if gate.get("formal_human_outcome_recorded") is not False:
        blockers.append("draft_records_formal_outcome")
    if gate.get("draft_is_importable_decision") is not False:
        blockers.append("draft_importable_decision_not_blocked")
    if gate.get("implementation_allowed") is not False:
        blockers.append("draft_gate_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("draft_gate_code_patch_not_blocked")
    if gate.get("next_design_authorized") is not False:
        blockers.append("draft_gate_next_design_not_blocked")
    if gate.get("handoff_to_implementation") != "not_allowed":
        blockers.append("draft_gate_handoff_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("draft_gate_has_blockers")
    if implementation_gate.get("implementation_allowed") is not False:
        blockers.append("draft_implementation_gate_not_blocked")
    if implementation_gate.get("code_patch_authorized") is not False:
        blockers.append("draft_implementation_code_patch_not_blocked")
    if summary.get("draft_track_count") != EXPECTED_TRACK_COUNT:
        blockers.append("draft_track_count_drift")
    if summary.get("design_action_count") != EXPECTED_READY_ACTION_COUNT:
        blockers.append("draft_action_count_drift")
    if summary.get("source_case_count") != EXPECTED_SOURCE_CASE_COUNT:
        blockers.append("draft_source_case_count_drift")
    if summary.get("pending_records_excluded") != EXPECTED_PENDING_EXCLUDED:
        blockers.append("draft_pending_excluded_count_drift")
    if summary.get("requires_user_confirmation") is not True:
        blockers.append("draft_summary_user_confirmation_not_required")
    if summary.get("formal_human_outcome_recorded") is not False:
        blockers.append("draft_summary_records_formal_outcome")
    if summary.get("draft_is_importable_decision") is not False:
        blockers.append("draft_summary_importable_decision_not_blocked")
    if summary.get("implementation_allowed") is not False:
        blockers.append("draft_summary_implementation_not_blocked")
    if summary.get("code_patch_authorized") is not False:
        blockers.append("draft_summary_code_patch_not_blocked")
    if summary.get("next_design_authorized") is not False:
        blockers.append("draft_summary_next_design_not_blocked")
    if len(matrix) != EXPECTED_TRACK_COUNT:
        blockers.append("draft_matrix_count_drift")
    track_order = [text(as_dict(row).get("action_type")) for row in matrix]
    if track_order != EXPECTED_REVIEW_ORDER:
        blockers.append("draft_matrix_order_drift")
    for index, row_value in enumerate(matrix):
        row = as_dict(row_value)
        action_type = text(row.get("action_type")) or str(index)
        if row.get("draft_status") != "draft_pending_user_confirmation":
            blockers.append(f"draft_row_not_pending:{action_type}")
        if row.get("requires_user_confirmation") is not True:
            blockers.append(f"draft_row_confirmation_not_required:{action_type}")
        if row.get("formal_human_outcome_recorded") is not False:
            blockers.append(f"draft_row_records_formal_outcome:{action_type}")
        if row.get("draft_is_importable_decision") is not False:
            blockers.append(f"draft_row_importable_decision_not_blocked:{action_type}")
        if row.get("implementation_allowed") is not False:
            blockers.append(f"draft_row_implementation_not_blocked:{action_type}")
        if row.get("code_patch_authorized") is not False:
            blockers.append(f"draft_row_code_patch_not_blocked:{action_type}")
        if row.get("next_design_authorized") is not False:
            blockers.append(f"draft_row_next_design_not_blocked:{action_type}")
        if not text(row.get("draft_option")):
            blockers.append(f"draft_row_missing_option:{action_type}")
        if not text(row.get("draft_next_series")):
            blockers.append(f"draft_row_missing_next_series:{action_type}")
        if not as_list(as_dict(row.get("traceability")).get("source_case_ids")):
            blockers.append(f"draft_row_missing_source_cases:{action_type}")
        if not as_list(as_dict(row.get("traceability")).get("design_action_ids")):
            blockers.append(f"draft_row_missing_design_actions:{action_type}")
    if not assertions:
        blockers.append("draft_assertions_missing")
    elif any(as_dict(item).get("status") != "passed" for item in assertions):
        blockers.append("draft_assertions_not_all_passed")

    forbidden_keys, advisory_keys = key_violations(draft_report)
    for key in forbidden_keys:
        blockers.append(f"draft_forbidden_key_present:{key}")
    for key in advisory_keys:
        blockers.append(f"draft_advisory_signal_present:{key}")
    return sorted_unique(blockers)


def build_confirmation_rows(draft_report: dict[str, Any], confirmation_ready: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row_value in enumerate(as_list(draft_report.get("draft_matrix")), start=1):
        row = as_dict(row_value)
        action_type = text(row.get("action_type"))
        candidate_scope = as_dict(row.get("candidate_scope"))
        traceability = as_dict(row.get("traceability"))
        status = "confirmed_for_future_design_planning" if confirmation_ready else "blocked"
        rows.append({
            "review_order": EXPECTED_REVIEW_ORDER.index(action_type) + 1 if action_type in EXPECTED_REVIEW_ORDER else index,
            "design_track_id": row.get("design_track_id") or action_type,
            "action_type": action_type,
            "display_name": row.get("display_name") or action_type,
            "priority_band": row.get("priority_band") or "",
            "confirmation_status": status,
            "user_confirmation_recorded": confirmation_ready,
            "confirmed_closeout_option": row.get("draft_option"),
            "confirmed_direction": row.get("draft_closeout_direction"),
            "confirmed_next_series": row.get("draft_next_series"),
            "confirmed_next_artifact": row.get("draft_next_artifact"),
            "confirmation_basis": row.get("draft_rationale"),
            "confirmation_note": row.get("draft_required_confirmation"),
            "manual_review_importable": False,
            "not_completed_manual_review_decision": True,
            "future_design_planning_allowed": confirmation_ready,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "next_design_authorized": False,
            "source_draft_status": row.get("draft_status"),
            "source_requires_user_confirmation": row.get("requires_user_confirmation"),
            "candidate_scope": {
                "ready_for_design_review_candidates": candidate_scope.get("ready_for_design_review_candidates", 0),
                "source_case_count": candidate_scope.get("source_case_count", 0),
                "expected_domains": as_list(candidate_scope.get("expected_domains")),
                "risk_level_summary": candidate_scope.get("risk_level_summary", {}),
                "confirmed_root_cause_summary": candidate_scope.get("confirmed_root_cause_summary", {}),
                "target_area_summary": candidate_scope.get("target_area_summary", {}),
            },
            "traceability": {
                "source_case_ids": as_list(traceability.get("source_case_ids")),
                "design_action_ids": as_list(traceability.get("design_action_ids")),
            },
            "confirmation_constraints": [
                "本记录只确认设计收口方向。",
                "本记录不是 manual review importer 的 completed decision。",
                "任何后续实现必须另开版本并重新确认边界。",
            ],
        })
    return sorted(rows, key=lambda item: (int(item.get("review_order") or 999), item.get("action_type") or ""))


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


def build_summary(draft_report: dict[str, Any], rows: list[dict[str, Any]], status: str) -> dict[str, Any]:
    draft_summary = as_dict(draft_report.get("summary"))
    priority_counts = Counter(text(row.get("priority_band")) for row in rows if text(row.get("priority_band")))
    option_counts = Counter(text(row.get("confirmed_closeout_option")) for row in rows if text(row.get("confirmed_closeout_option")))
    series_counts = Counter(text(row.get("confirmed_next_series")) for row in rows if text(row.get("confirmed_next_series")))
    return {
        "status": status,
        "allowed_use": "future_design_planning_input_only" if status != "blocked" else "blocked",
        "source_draft_status": as_dict(draft_report.get("draft_gate")).get("status"),
        "confirmation_track_count": len(rows),
        "design_action_count": draft_summary.get("design_action_count", EXPECTED_READY_ACTION_COUNT),
        "source_case_count": draft_summary.get("source_case_count", EXPECTED_SOURCE_CASE_COUNT),
        "pending_records_excluded": draft_summary.get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
        "priority_band_summary": {key: priority_counts[key] for key in sorted(priority_counts)},
        "confirmed_option_summary": {key: option_counts[key] for key in sorted(option_counts)},
        "confirmed_next_series_summary": {key: series_counts[key] for key in sorted(series_counts)},
        "user_confirmation_recorded": status != "blocked",
        "formal_design_closeout_recorded": status != "blocked",
        "manual_review_importable": False,
        "not_completed_manual_review_decision": True,
        "future_design_planning_allowed": status != "blocked",
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "next_design_authorized": False,
        "required_next_action": "open_separate_design_version_before_any_followup_design_or_implementation",
        "implementation_decision_policy": "must_remain_false_unless_future_explicit_approval_exists",
    }


def build_assertions(
    confirmation_ready: bool,
    draft_blockers: list[str],
    rows: list[dict[str, Any]],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "source_draft_is_ready_for_confirmation_record",
            "status": "passed" if not draft_blockers else "failed",
            "blockers": draft_blockers,
        },
        {
            "name": "confirmation_has_five_review_rows",
            "status": "passed" if len(rows) == EXPECTED_TRACK_COUNT else "failed",
            "actual": len(rows),
            "expected": EXPECTED_TRACK_COUNT,
        },
        {
            "name": "all_rows_confirm_only_future_design_planning",
            "status": "passed"
            if all(
                row.get("future_design_planning_allowed") == confirmation_ready
                and row.get("manual_review_importable") is False
                for row in rows
            )
            else "failed",
        },
        {
            "name": "all_rows_remain_non_implementation",
            "status": "passed"
            if all(
                row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("next_design_authorized") is False
                for row in rows
            )
            else "failed",
        },
        {
            "name": "forbidden_output_keys_absent",
            "status": "passed" if not output_forbidden_keys else "failed",
            "forbidden_keys": output_forbidden_keys,
        },
        {
            "name": "text_readability_gate",
            "status": "passed" if not readability_errors else "failed",
            "mojibake_like_paths": readability_errors,
        },
        {
            "name": "confirmation_ready_only_when_source_passes",
            "status": "passed" if confirmation_ready == (not draft_blockers) else "failed",
            "confirmation_ready": confirmation_ready,
        },
    ]


def build_report(draft_report_path: Path = DEFAULT_DRAFT_REPORT_PATH) -> dict[str, Any]:
    draft_report = load_json(draft_report_path)
    draft_blockers = draft_contract_blockers(draft_report)
    confirmation_ready = not draft_blockers
    rows = build_confirmation_rows(draft_report, confirmation_ready)
    status = "confirmed_for_future_design_planning" if confirmation_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "ready_action_human_closeout_confirmation_record",
        "scope": "offline human closeout confirmation record for future design planning only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ready_action_human_closeout_decision_draft_report": source_meta(draft_report_path, draft_report),
        },
        "confirmation_context": USER_CONFIRMATION_CONTEXT,
        "guardrails": CONFIRMATION_GUARDRAILS,
        "confirmation_gate": {
            "status": status,
            "allowed_use": "future_design_planning_input_only" if confirmation_ready else "blocked",
            "user_confirmation_recorded": confirmation_ready,
            "formal_design_closeout_recorded": confirmation_ready,
            "manual_review_importable": False,
            "not_completed_manual_review_decision": True,
            "future_design_planning_allowed": confirmation_ready,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "next_design_authorized": False,
            "future_explicit_implementation_approval_required": True,
            "blockers": draft_blockers,
        },
        "design_track_authority": DESIGN_TRACK_AUTHORITY,
        "summary": build_summary(draft_report, rows, status),
        "confirmation_matrix": rows,
        "excluded_scope": {
            "pending_records_excluded": as_dict(draft_report.get("summary")).get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
            "pending_records_policy": "background_count_only_not_work_items",
            "manual_review_import_policy": "not_importable",
            "implementation_policy": "not_authorized_by_this_report",
        },
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_case_ids": as_list(as_dict(draft_report.get("traceability")).get("source_case_ids")),
            "design_action_ids": as_list(as_dict(draft_report.get("traceability")).get("design_action_ids")) if confirmation_ready else [],
            "source_reports": [str(draft_report_path)],
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        confirmation_ready,
        draft_blockers,
        rows,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["confirmation_gate"]["status"] = "blocked"
        report["confirmation_gate"]["allowed_use"] = "blocked"
        report["confirmation_gate"]["user_confirmation_recorded"] = False
        report["confirmation_gate"]["formal_design_closeout_recorded"] = False
        report["confirmation_gate"]["future_design_planning_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        report["summary"]["user_confirmation_recorded"] = False
        report["summary"]["formal_design_closeout_recorded"] = False
        report["summary"]["future_design_planning_allowed"] = False
        extra_blockers = []
        if forbidden_output_keys:
            extra_blockers.append("forbidden_output_key_present")
        if readability_errors:
            extra_blockers.append("blocked_for_human_readability")
        report["confirmation_gate"]["blockers"] = sorted_unique(report["confirmation_gate"]["blockers"] + extra_blockers)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("confirmation_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.7.9.6 Ready Action Human Closeout Confirmation Record",
        "",
        "本文件记录用户已确认 5 条设计收口方向。它只能作为后续设计规划输入，不是 manual review importer 的 completed decision，也不批准任何代码、配置、样例或主流程修改。",
        "",
        "## 总览",
        "",
        f"- Confirmation status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Confirmation tracks: {summary.get('confirmation_track_count')}",
        f"- Design actions: {summary.get('design_action_count')}",
        f"- Source cases: {summary.get('source_case_count')}",
        f"- Pending records excluded: {summary.get('pending_records_excluded')}",
        f"- User confirmation recorded: {gate.get('user_confirmation_recorded')}",
        f"- Manual review importable: {gate.get('manual_review_importable')}",
        f"- Future design planning allowed: {gate.get('future_design_planning_allowed')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        f"- Next design authorized: {gate.get('next_design_authorized')}",
        "",
        "## Confirmation Matrix",
        "",
        "| Order | Priority | Track | Confirmed option | Confirmed next | Status |",
        "|---:|---|---|---|---|---|",
    ]
    for row in as_list(report.get("confirmation_matrix")):
        lines.append(
            f"| {row.get('review_order')} | {row.get('priority_band')} | {row.get('display_name')} | "
            f"`{row.get('confirmed_closeout_option')}` | {row.get('confirmed_next_series')} | `{row.get('confirmation_status')}` |"
        )

    lines.extend([
        "",
        "## Confirmed Directions",
        "",
    ])
    for row in as_list(report.get("confirmation_matrix")):
        lines.append(f"### {row.get('review_order')}. {row.get('display_name')}")
        lines.append("")
        lines.append(f"- 确认方向：{row.get('confirmed_direction')}")
        lines.append(f"- 确认依据：{row.get('confirmation_basis')}")
        lines.append(f"- 确认备注：{row.get('confirmation_note')}")
        lines.append(f"- 后续系列：`{row.get('confirmed_next_series')}` / {row.get('confirmed_next_artifact')}")
        lines.append(f"- 当前状态：`{row.get('confirmation_status')}`")
        lines.append("- 限制：")
        for item in as_list(row.get("confirmation_constraints")):
            lines.append(f"  - {item}")
        lines.append("")

    lines.extend([
        "## Boundaries",
        "",
        "- 本 record 只确认设计收口方向，可作为后续设计规划输入。",
        "- `manual_review_importable=false`，本 record 不是 completed manual review decision。",
        "- `implementation_allowed=false`、`code_patch_authorized=false` 和 `next_design_authorized=false` 必须保持不变。",
        "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约或 RAG 主流程。",
        "- 后续若进入 v0.4.8.x、v0.4.9.x 或 fixture governance，必须另开版本并重新确认边界。",
        "",
        "## Source",
        "",
        f"- Draft report: `{report['inputs']['ready_action_human_closeout_decision_draft_report']['path']}`",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a read-only human closeout confirmation record.")
    parser.add_argument("--draft-report", type=Path, default=DEFAULT_DRAFT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.draft_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Ready action human closeout confirmation record built: "
        f"{summary['status']}, "
        f"{summary['confirmation_track_count']} tracks, "
        f"{summary['design_action_count']} design actions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
