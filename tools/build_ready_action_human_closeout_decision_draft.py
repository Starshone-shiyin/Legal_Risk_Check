"""Build a human-confirmation draft for design review closeout decisions.

The draft reads the saved v0.4.7.9.4 closeout envelope and prepares five
suggested closeout directions for user confirmation. It is not a formal human
decision record. It does not authorize implementation, create engineering
tasks, call RAG, contact Qdrant or an LLM, or mutate retrieval, prompts, rules,
fixtures, scenario registry entries, eval cases, hidden seeds, anchors,
schema/importer contracts, dry-run contracts, or the main flow.
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


VERSION = "0.4.7.9.5"

DEFAULT_CLOSEOUT_REPORT_PATH = legacy_report_path("ready_action_design_review_closeout_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ready_action_human_closeout_decision_draft_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ready_action_human_closeout_decision_draft_v0.4.7.9.5.md")

EXPECTED_CLOSEOUT_VERSION = "0.4.7.9.4"
EXPECTED_CLOSEOUT_SCHEMA = "ready_action_design_review_closeout_envelope"
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

DRAFT_PROFILES = {
    "final_evidence_selection_policy_review": {
        "draft_closeout_direction": "建议继续进入 v0.4.8.x 最终证据选择策略设计草案。",
        "draft_confirmation_status": "user_confirmation_required",
        "draft_option": "continue_to_design_spec_draft",
        "draft_next_series": "v0.4.8.x",
        "draft_next_artifact": "final_evidence_selection_policy_design_spec_draft",
        "draft_rationale": "5 个 pilot case 均显示关键证据可能已进入候选池但未进入最终 evidence_chain，是当前最明确的 Harvey-style grounding 质量瓶颈。",
        "draft_required_confirmation": "确认问题主要发生在最终证据选择，而不是召回、场景范围或提示词。",
    },
    "primary_evidence_fixture_candidate_review": {
        "draft_closeout_direction": "建议先进入 fixture governance 范围复核，不直接写入 eval case 或 golden fixture。",
        "draft_confirmation_status": "user_confirmation_required",
        "draft_option": "needs_legal_or_fixture_scope_review",
        "draft_next_series": "fixture governance",
        "draft_next_artifact": "primary_evidence_fixture_candidate_scope_review",
        "draft_rationale": "主证据候选对后续评测很重要，但当前只能作为候选池材料，必须先确认通用性和非单案补丁属性。",
        "draft_required_confirmation": "确认候选证据是否能代表通用主争点证据缺口。",
    },
    "high_risk_manual_grounding_review": {
        "draft_closeout_direction": "建议继续形成高风险结论 grounding 设计草案，但仍不改 prompt 或 risk rule。",
        "draft_confirmation_status": "user_confirmation_required",
        "draft_option": "continue_to_design_spec_draft",
        "draft_next_series": "manual grounding review",
        "draft_next_artifact": "high_risk_grounding_design_spec_draft",
        "draft_rationale": "高风险结论、整改动作和法律后果需要可追溯证据支撑，否则企业风控报告会出现结论强、证据弱的问题。",
        "draft_required_confirmation": "确认哪些高风险结论不能被当前 evidence_chain 直接支撑。",
    },
    "scenario_registry_core_article_review": {
        "draft_closeout_direction": "建议先做场景核心条文范围复核，不直接修改 scenario registry。",
        "draft_confirmation_status": "user_confirmation_required",
        "draft_option": "needs_legal_or_fixture_scope_review",
        "draft_next_series": "scenario core article review",
        "draft_next_artifact": "scenario_core_article_scope_review",
        "draft_rationale": "部分缺失证据可能来自场景法律范围边界，而不是最终选择策略；需要人工确认核心条文清单。",
        "draft_required_confirmation": "确认缺失条文是否属于该场景的核心法律依据。",
    },
    "functional_typing_fixture_review": {
        "draft_closeout_direction": "建议先做 legal functional typing fixture 范围复核，不直接改 config。",
        "draft_confirmation_status": "user_confirmation_required",
        "draft_option": "needs_legal_or_fixture_scope_review",
        "draft_next_series": "legal functional typing fixture review",
        "draft_next_artifact": "legal_functional_typing_fixture_scope_review",
        "draft_rationale": "功能类型标签是长期 RAG grounding 基建，当前只能沉淀候选和标注规范，不能直接修改配置。",
        "draft_required_confirmation": "确认条文功能类型是否足够明确，适合进入 fixture 候选池。",
    },
}

DRAFT_GUARDRAILS = {
    "draft_only": True,
    "source_closeout_only": True,
    "requires_user_confirmation": True,
    "formal_human_outcome_recorded": False,
    "captures_formal_review_outcome": False,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "next_design_authorized": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
    "pending_records_to_work_items": "disallowed",
    "draft_route_to_work_items": "disallowed",
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


def closeout_contract_blockers(closeout_report: dict[str, Any]) -> list[str]:
    if not closeout_report:
        return ["missing_or_invalid_closeout_report"]

    blockers: list[str] = []
    gate = as_dict(closeout_report.get("closeout_gate"))
    summary = as_dict(closeout_report.get("summary"))
    implementation_gate = as_dict(closeout_report.get("implementation_gate"))
    matrix = as_list(closeout_report.get("closeout_matrix"))
    assertions = as_list(closeout_report.get("assertions"))

    if closeout_report.get("version") != EXPECTED_CLOSEOUT_VERSION:
        blockers.append("closeout_version_mismatch")
    if closeout_report.get("schema_kind") != EXPECTED_CLOSEOUT_SCHEMA:
        blockers.append("closeout_schema_mismatch")
    if gate.get("status") != "pending_human_design_closeout":
        blockers.append("closeout_gate_not_pending")
    if gate.get("human_closeout_allowed") is not True:
        blockers.append("closeout_human_review_not_allowed")
    if gate.get("formal_human_outcome_recorded") is not False:
        blockers.append("closeout_records_formal_outcome")
    if gate.get("captures_formal_review_outcome") is not False:
        blockers.append("closeout_captures_formal_outcome")
    if gate.get("implementation_allowed") is not False:
        blockers.append("closeout_gate_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("closeout_gate_code_patch_not_blocked")
    if gate.get("next_design_authorized") is not False:
        blockers.append("closeout_next_design_not_blocked")
    if gate.get("handoff_to_implementation") != "not_allowed":
        blockers.append("closeout_gate_handoff_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("closeout_gate_has_blockers")
    if implementation_gate.get("implementation_allowed") is not False:
        blockers.append("closeout_implementation_gate_not_blocked")
    if implementation_gate.get("code_patch_authorized") is not False:
        blockers.append("closeout_implementation_code_patch_not_blocked")
    if summary.get("closeout_track_count") != EXPECTED_TRACK_COUNT:
        blockers.append("closeout_track_count_drift")
    if summary.get("design_action_count") != EXPECTED_READY_ACTION_COUNT:
        blockers.append("closeout_action_count_drift")
    if summary.get("source_case_count") != EXPECTED_SOURCE_CASE_COUNT:
        blockers.append("closeout_source_case_count_drift")
    if summary.get("pending_records_excluded") != EXPECTED_PENDING_EXCLUDED:
        blockers.append("closeout_pending_excluded_count_drift")
    if summary.get("formal_human_outcome_recorded") is not False:
        blockers.append("closeout_summary_records_formal_outcome")
    if summary.get("captures_formal_review_outcome") is not False:
        blockers.append("closeout_summary_captures_formal_outcome")
    if summary.get("implementation_allowed") is not False:
        blockers.append("closeout_summary_implementation_not_blocked")
    if summary.get("code_patch_authorized") is not False:
        blockers.append("closeout_summary_code_patch_not_blocked")
    if summary.get("next_design_authorized") is not False:
        blockers.append("closeout_summary_next_design_not_blocked")
    if len(matrix) != EXPECTED_TRACK_COUNT:
        blockers.append("closeout_matrix_count_drift")
    track_order = [text(as_dict(row).get("action_type")) for row in matrix]
    if track_order != EXPECTED_REVIEW_ORDER:
        blockers.append("closeout_matrix_order_drift")
    for index, row_value in enumerate(matrix):
        row = as_dict(row_value)
        action_type = text(row.get("action_type")) or str(index)
        if row.get("closeout_status") != "pending_human_closeout":
            blockers.append(f"closeout_row_not_pending:{action_type}")
        if row.get("human_closeout_required") is not True:
            blockers.append(f"closeout_row_human_review_not_required:{action_type}")
        if row.get("formal_human_outcome_recorded") is not False:
            blockers.append(f"closeout_row_records_formal_outcome:{action_type}")
        if row.get("implementation_allowed") is not False:
            blockers.append(f"closeout_row_implementation_not_blocked:{action_type}")
        if row.get("code_patch_authorized") is not False:
            blockers.append(f"closeout_row_code_patch_not_blocked:{action_type}")
        if row.get("candidate_route_authorized") is not False:
            blockers.append(f"closeout_row_candidate_route_authorized:{action_type}")
        if not as_list(as_dict(row.get("traceability")).get("source_case_ids")):
            blockers.append(f"closeout_row_missing_source_cases:{action_type}")
        if not as_list(as_dict(row.get("traceability")).get("design_action_ids")):
            blockers.append(f"closeout_row_missing_design_actions:{action_type}")
    if not assertions:
        blockers.append("closeout_assertions_missing")
    elif any(as_dict(item).get("status") != "passed" for item in assertions):
        blockers.append("closeout_assertions_not_all_passed")

    forbidden_keys, advisory_keys = key_violations(closeout_report)
    for key in forbidden_keys:
        blockers.append(f"closeout_forbidden_key_present:{key}")
    for key in advisory_keys:
        blockers.append(f"closeout_advisory_signal_present:{key}")
    return sorted_unique(blockers)


def build_draft_rows(closeout_report: dict[str, Any], draft_ready: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row_value in enumerate(as_list(closeout_report.get("closeout_matrix")), start=1):
        row = as_dict(row_value)
        action_type = text(row.get("action_type"))
        profile = DRAFT_PROFILES.get(action_type, {})
        candidate_scope = as_dict(row.get("candidate_scope"))
        traceability = as_dict(row.get("traceability"))
        status = "draft_pending_user_confirmation" if draft_ready else "blocked"
        rows.append({
            "review_order": EXPECTED_REVIEW_ORDER.index(action_type) + 1 if action_type in EXPECTED_REVIEW_ORDER else index,
            "design_track_id": row.get("design_track_id") or action_type,
            "action_type": action_type,
            "display_name": row.get("display_name") or action_type,
            "priority_band": row.get("priority_band") or "",
            "draft_status": status,
            "requires_user_confirmation": True,
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "draft_is_importable_decision": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "next_design_authorized": False,
            "draft_option": profile.get("draft_option", row.get("recommended_closeout_option") or "defer_pending_more_cases"),
            "draft_closeout_direction": profile.get("draft_closeout_direction", "建议等待人工确认后再分流。"),
            "draft_next_series": profile.get("draft_next_series", row.get("candidate_route") or "defer"),
            "draft_next_artifact": profile.get("draft_next_artifact", "human_confirmed_closeout_record_required"),
            "draft_rationale": profile.get("draft_rationale", row.get("minimum_human_basis") or ""),
            "draft_required_confirmation": profile.get("draft_required_confirmation", row.get("closeout_question") or ""),
            "source_closeout_question": row.get("closeout_question", ""),
            "source_minimum_human_basis": row.get("minimum_human_basis", ""),
            "source_candidate_route": row.get("candidate_route", ""),
            "source_candidate_route_label": row.get("candidate_route_label", ""),
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
            "draft_constraints": [
                "这是待用户确认草案，不是正式人工结论。",
                "不能导入 importer，也不能作为 completed manual decision。",
                "任何后续设计或实现必须另开版本并重新确认边界。",
            ],
        })
    return sorted(rows, key=lambda item: (int(item.get("review_order") or 999), item.get("action_type") or ""))


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


def build_summary(closeout_report: dict[str, Any], draft_rows: list[dict[str, Any]], status: str) -> dict[str, Any]:
    closeout_summary = as_dict(closeout_report.get("summary"))
    priority_counts = Counter(text(row.get("priority_band")) for row in draft_rows if text(row.get("priority_band")))
    option_counts = Counter(text(row.get("draft_option")) for row in draft_rows if text(row.get("draft_option")))
    series_counts = Counter(text(row.get("draft_next_series")) for row in draft_rows if text(row.get("draft_next_series")))
    return {
        "status": status,
        "allowed_use": "user_confirmation_draft_only" if status != "blocked" else "blocked",
        "source_closeout_status": as_dict(closeout_report.get("closeout_gate")).get("status"),
        "draft_track_count": len(draft_rows),
        "design_action_count": closeout_summary.get("design_action_count", EXPECTED_READY_ACTION_COUNT),
        "source_case_count": closeout_summary.get("source_case_count", EXPECTED_SOURCE_CASE_COUNT),
        "pending_records_excluded": closeout_summary.get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
        "priority_band_summary": {key: priority_counts[key] for key in sorted(priority_counts)},
        "draft_option_summary": {key: option_counts[key] for key in sorted(option_counts)},
        "draft_next_series_summary": {key: series_counts[key] for key in sorted(series_counts)},
        "requires_user_confirmation": True,
        "formal_human_outcome_recorded": False,
        "captures_formal_review_outcome": False,
        "draft_is_importable_decision": False,
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "next_design_authorized": False,
        "required_user_action": "confirm_or_revise_draft_outside_this_report_before_any_followup_design",
        "implementation_decision_policy": "must_remain_false_unless_future_explicit_approval_exists",
    }


def build_assertions(
    draft_ready: bool,
    closeout_blockers: list[str],
    draft_rows: list[dict[str, Any]],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "source_closeout_is_ready_for_draft",
            "status": "passed" if not closeout_blockers else "failed",
            "blockers": closeout_blockers,
        },
        {
            "name": "draft_has_five_review_rows",
            "status": "passed" if len(draft_rows) == EXPECTED_TRACK_COUNT else "failed",
            "actual": len(draft_rows),
            "expected": EXPECTED_TRACK_COUNT,
        },
        {
            "name": "all_rows_require_user_confirmation",
            "status": "passed" if all(row.get("requires_user_confirmation") is True for row in draft_rows) else "failed",
        },
        {
            "name": "all_rows_remain_non_importable_drafts",
            "status": "passed"
            if all(row.get("draft_is_importable_decision") is False and row.get("formal_human_outcome_recorded") is False for row in draft_rows)
            else "failed",
        },
        {
            "name": "all_rows_remain_non_implementation",
            "status": "passed"
            if all(
                row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("next_design_authorized") is False
                for row in draft_rows
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
            "name": "draft_ready_only_when_source_passes",
            "status": "passed" if draft_ready == (not closeout_blockers) else "failed",
            "draft_ready": draft_ready,
        },
    ]


def build_report(closeout_report_path: Path = DEFAULT_CLOSEOUT_REPORT_PATH) -> dict[str, Any]:
    closeout_report = load_json(closeout_report_path)
    closeout_blockers = closeout_contract_blockers(closeout_report)
    draft_ready = not closeout_blockers
    draft_rows = build_draft_rows(closeout_report, draft_ready)
    status = "draft_pending_user_confirmation" if draft_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "ready_action_human_closeout_decision_draft",
        "scope": "offline user-confirmation draft only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ready_action_design_review_closeout_report": source_meta(closeout_report_path, closeout_report),
        },
        "guardrails": DRAFT_GUARDRAILS,
        "draft_gate": {
            "status": status,
            "allowed_use": "user_confirmation_draft_only" if draft_ready else "blocked",
            "requires_user_confirmation": True,
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "draft_is_importable_decision": False,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "next_design_authorized": False,
            "future_explicit_implementation_approval_required": True,
            "blockers": closeout_blockers,
        },
        "summary": build_summary(closeout_report, draft_rows, status),
        "draft_matrix": draft_rows,
        "confirmation_policy": {
            "user_must_confirm_or_revise": True,
            "formal_outcome_not_recorded_here": True,
            "importer_compatible_decision": False,
            "candidate_routes_are_not_authorized": True,
            "implementation_allowed": False,
        },
        "excluded_scope": {
            "pending_records_excluded": as_dict(closeout_report.get("summary")).get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
            "pending_records_policy": "background_count_only_not_work_items",
            "formal_outcome_policy": "not_captured_by_this_report",
            "draft_route_policy": "not_authorized_by_this_report",
        },
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_case_ids": as_list(as_dict(closeout_report.get("traceability")).get("source_case_ids")),
            "design_action_ids": as_list(as_dict(closeout_report.get("traceability")).get("design_action_ids")) if draft_ready else [],
            "source_reports": [str(closeout_report_path)],
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        draft_ready,
        closeout_blockers,
        draft_rows,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["draft_gate"]["status"] = "blocked"
        report["draft_gate"]["allowed_use"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra_blockers = []
        if forbidden_output_keys:
            extra_blockers.append("forbidden_output_key_present")
        if readability_errors:
            extra_blockers.append("blocked_for_human_readability")
        report["draft_gate"]["blockers"] = sorted_unique(report["draft_gate"]["blockers"] + extra_blockers)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("draft_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.7.9.5 Ready Action Human Closeout Decision Draft",
        "",
        "本文件是待用户确认的人工收口草案。它给出 5 条设计轨道的建议方向，但不记录正式人工结论，也不批准任何代码、配置、样例或主流程修改。",
        "",
        "## 总览",
        "",
        f"- Draft status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Draft tracks: {summary.get('draft_track_count')}",
        f"- Design actions: {summary.get('design_action_count')}",
        f"- Source cases: {summary.get('source_case_count')}",
        f"- Pending records excluded: {summary.get('pending_records_excluded')}",
        f"- Requires user confirmation: {gate.get('requires_user_confirmation')}",
        f"- Formal outcome recorded: {gate.get('formal_human_outcome_recorded')}",
        f"- Importable decision: {gate.get('draft_is_importable_decision')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        f"- Next design authorized: {gate.get('next_design_authorized')}",
        "",
        "## Draft Matrix",
        "",
        "| Order | Priority | Track | Draft option | Suggested next | Status |",
        "|---:|---|---|---|---|---|",
    ]
    for row in as_list(report.get("draft_matrix")):
        lines.append(
            f"| {row.get('review_order')} | {row.get('priority_band')} | {row.get('display_name')} | "
            f"`{row.get('draft_option')}` | {row.get('draft_next_series')} | `{row.get('draft_status')}` |"
        )

    lines.extend([
        "",
        "## Draft Directions",
        "",
    ])
    for row in as_list(report.get("draft_matrix")):
        lines.append(f"### {row.get('review_order')}. {row.get('display_name')}")
        lines.append("")
        lines.append(f"- 草案方向：{row.get('draft_closeout_direction')}")
        lines.append(f"- 草案理由：{row.get('draft_rationale')}")
        lines.append(f"- 需要你确认：{row.get('draft_required_confirmation')}")
        lines.append(f"- 候选后续：`{row.get('draft_next_series')}` / {row.get('draft_next_artifact')}")
        lines.append(f"- 当前状态：`{row.get('draft_status')}`")
        lines.append("- 草案限制：")
        for item in as_list(row.get("draft_constraints")):
            lines.append(f"  - {item}")
        lines.append("")

    lines.extend([
        "## Boundaries",
        "",
        "- 本 draft 只帮助用户确认或修改收口方向，不记录正式人工结论。",
        "- `requires_user_confirmation=true`、`formal_human_outcome_recorded=false`、`draft_is_importable_decision=false` 必须保持不变。",
        "- `implementation_allowed=false`、`code_patch_authorized=false` 和 `next_design_authorized=false` 必须保持不变。",
        "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约或 RAG 主流程。",
        "- 后续若进入 v0.4.8.x、v0.4.9.x 或 fixture governance，必须另开版本并重新确认边界。",
        "",
        "## Source",
        "",
        f"- Closeout report: `{report['inputs']['ready_action_design_review_closeout_report']['path']}`",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a read-only human closeout decision draft.")
    parser.add_argument("--closeout-report", type=Path, default=DEFAULT_CLOSEOUT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.closeout_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Ready action human closeout decision draft built: "
        f"{summary['status']}, "
        f"{summary['draft_track_count']} tracks, "
        f"{summary['design_action_count']} design actions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
