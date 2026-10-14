"""Build a read-only worksheet for ready-action design review.

The worksheet is a human review aid. It reads the saved v0.4.7.9.2 gate report
and v0.4.7.9.1 brief report, turns the five design tracks into a compact review
matrix, and keeps implementation blocked. It does not call RAG, contact a
backend, read Qdrant, use an LLM, or mutate retrieval, prompts, rules, fixtures,
scenario registry entries, eval cases, hidden seeds, anchors, schema/importer
contracts, dry-run contracts, or the main flow.
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


VERSION = "0.4.7.9.3"

DEFAULT_GATE_REPORT_PATH = legacy_report_path("ready_action_design_review_gate_report.json")
DEFAULT_BRIEF_REPORT_PATH = legacy_report_path("ready_action_design_review_brief_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ready_action_design_review_worksheet_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ready_action_design_review_worksheet_v0.4.7.9.3.md")

EXPECTED_GATE_VERSION = "0.4.7.9.2"
EXPECTED_GATE_SCHEMA = "ready_action_design_review_gate"
EXPECTED_BRIEF_VERSION = "0.4.7.9.1"
EXPECTED_BRIEF_SCHEMA = "ready_action_design_review_brief"
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

TRACK_REVIEW_PROFILES = {
    "final_evidence_selection_policy_review": {
        "plain_language_label": "最后到底该留下哪些证据",
        "review_goal": "判断问题是否属于最终证据选择策略，而不是召回、场景范围或提示词问题。",
        "recommended_next_series": "v0.4.8.x",
        "recommended_next_work": "Final evidence selection policy design",
        "implementation_precondition": "先形成经人工确认的策略草案和 simulator 验证计划。",
        "critical_human_question": "这些 case 的关键证据是否已经进入候选池，但没有进入最终 evidence_chain？",
    },
    "primary_evidence_fixture_candidate_review": {
        "plain_language_label": "哪些材料以后可作为测试样例候选",
        "review_goal": "判断候选证据是否真是主争点证据，以及是否适合进入 fixture governance。",
        "recommended_next_series": "fixture governance",
        "recommended_next_work": "Primary evidence fixture candidate review",
        "implementation_precondition": "先有人工确认的候选池规则，不直接写入 eval case 或 golden fixture。",
        "critical_human_question": "这些候选是否能代表通用主证据缺口，而不是单案补丁？",
    },
    "high_risk_manual_grounding_review": {
        "plain_language_label": "高风险结论有没有证据托住",
        "review_goal": "判断风险类型、整改动作或结论是否需要更强的人工 grounding 规则。",
        "recommended_next_series": "manual grounding review",
        "recommended_next_work": "High-risk manual grounding review design",
        "implementation_precondition": "先拆清风险类型、整改动作和法律后果各自的最小证据要求。",
        "critical_human_question": "高风险结论是否能被当前 evidence_chain 直接支撑？",
    },
    "scenario_registry_core_article_review": {
        "plain_language_label": "场景应该绑定哪些核心条文",
        "review_goal": "判断问题是否属于 scenario registry 核心条文范围，而不是最终证据选择问题。",
        "recommended_next_series": "scenario core article review",
        "recommended_next_work": "Scenario registry core article design review",
        "implementation_precondition": "先形成只读条文范围清单，不直接修改 scenario registry。",
        "critical_human_question": "缺失条文是否真是该场景的核心依据？",
    },
    "functional_typing_fixture_review": {
        "plain_language_label": "法律功能类型标签是否可靠",
        "review_goal": "判断候选是否适合沉淀为 legal functional typing fixture，而不是直接改 config。",
        "recommended_next_series": "legal functional typing fixture review",
        "recommended_next_work": "Functional typing fixture design review",
        "implementation_precondition": "先明确条文功能类型和人工标签规范，再考虑 fixture。",
        "critical_human_question": "该条文的定义、义务、责任或程序功能是否足够明确？",
    },
}

WORKSHEET_GUARDRAILS = {
    "worksheet_only": True,
    "source_gate_and_brief_only": True,
    "human_design_review_aid_only": True,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
    "captures_formal_review_outcome": False,
    "pending_records_to_work_items": "disallowed",
    "ai_suggestion_to_authority": "disallowed",
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
    "promotion_candidates_generated",
    "ready_action_candidates_generated",
}

FORBIDDEN_OUTPUT_KEYS = {
    "approved",
    "approved_actions",
    "authorized_actions",
    "ready_to_apply",
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
    "promotion_candidates_generated",
    "ready_action_candidates_generated",
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

ADVISORY_SOURCE_KEYS = {
    "ai_suggestion",
    "safe_ai_suggestion_input",
    "advisory_packet_only",
    "prescreen_advisory",
    "pilot_assist",
    "mobile_aid",
    "human_confirmation_required",
    "contains_completed_manual_decisions",
}


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


def same_path(left: Any, right: Path) -> bool:
    if not left:
        return True
    left_path = Path(str(left))
    return left_path == right or left_path.resolve() == right.resolve()


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


def gate_contract_blockers(gate_report: dict[str, Any]) -> list[str]:
    if not gate_report:
        return ["missing_or_invalid_gate_report"]

    blockers: list[str] = []
    gate = as_dict(gate_report.get("gate"))
    review_scope = as_dict(gate_report.get("review_scope"))
    source_integrity = as_dict(gate_report.get("source_integrity"))
    source_brief = as_dict(gate_report.get("source_brief"))
    gate_inputs = as_dict(gate_report.get("inputs"))
    gate_brief_input = as_dict(gate_inputs.get("ready_action_design_review_brief_report"))
    assertions = as_list(gate_report.get("assertions"))

    if gate_report.get("version") != EXPECTED_GATE_VERSION:
        blockers.append("gate_version_mismatch")
    if gate_report.get("schema_kind") != EXPECTED_GATE_SCHEMA:
        blockers.append("gate_schema_mismatch")
    if source_brief.get("version") != EXPECTED_BRIEF_VERSION:
        blockers.append("gate_source_brief_version_mismatch")
    if source_brief.get("schema_kind") != EXPECTED_BRIEF_SCHEMA:
        blockers.append("gate_source_brief_schema_mismatch")
    if gate_brief_input.get("version") != EXPECTED_BRIEF_VERSION:
        blockers.append("gate_input_brief_version_mismatch")
    if gate_brief_input.get("schema_kind") != EXPECTED_BRIEF_SCHEMA:
        blockers.append("gate_input_brief_schema_mismatch")
    if gate.get("status") != "open_for_human_design_review_only":
        blockers.append("gate_not_open_for_human_design_review")
    if gate.get("human_design_review_allowed") is not True:
        blockers.append("gate_human_design_review_not_allowed")
    if gate.get("implementation_allowed") is not False:
        blockers.append("gate_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("gate_code_patch_not_blocked")
    if gate.get("handoff_to_implementation") != "not_allowed":
        blockers.append("gate_handoff_to_implementation_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("gate_has_blockers")
    if source_integrity.get("status") != "passed":
        blockers.append("gate_source_integrity_not_passed")
    if review_scope.get("design_track_count") != EXPECTED_TRACK_COUNT:
        blockers.append("gate_track_count_drift")
    if review_scope.get("design_action_count") != EXPECTED_READY_ACTION_COUNT:
        blockers.append("gate_action_count_drift")
    if review_scope.get("source_case_count") != EXPECTED_SOURCE_CASE_COUNT:
        blockers.append("gate_source_case_count_drift")
    if review_scope.get("pending_records_excluded") != EXPECTED_PENDING_EXCLUDED:
        blockers.append("gate_pending_excluded_count_drift")
    if as_list(review_scope.get("review_order")) != EXPECTED_REVIEW_ORDER:
        blockers.append("gate_review_order_drift")
    if not assertions:
        blockers.append("gate_assertions_missing")
    elif any(as_dict(item).get("status") != "passed" for item in assertions):
        blockers.append("gate_assertions_not_all_passed")

    forbidden_keys, advisory_keys = key_violations(gate_report)
    for key in forbidden_keys:
        blockers.append(f"gate_forbidden_key_present:{key}")
    for key in advisory_keys:
        blockers.append(f"gate_advisory_signal_present:{key}")
    return blockers


def brief_contract_blockers(brief_report: dict[str, Any], gate_report: dict[str, Any], brief_report_path: Path) -> list[str]:
    if not brief_report:
        return ["missing_or_invalid_brief_report"]

    blockers: list[str] = []
    summary = as_dict(brief_report.get("summary"))
    brief_gate = as_dict(brief_report.get("brief_gate"))
    traceability = as_dict(brief_report.get("traceability"))
    track_briefs = as_list(brief_report.get("track_briefs"))
    gate_scope = as_dict(gate_report.get("review_scope"))
    gate_inputs = as_dict(gate_report.get("inputs"))
    gate_brief_input = as_dict(gate_inputs.get("ready_action_design_review_brief_report"))

    if brief_report.get("version") != EXPECTED_BRIEF_VERSION:
        blockers.append("brief_version_mismatch")
    if brief_report.get("schema_kind") != EXPECTED_BRIEF_SCHEMA:
        blockers.append("brief_schema_mismatch")
    if not same_path(gate_brief_input.get("path"), brief_report_path):
        blockers.append("gate_brief_input_path_mismatch")
    if summary.get("status") != "ready_for_human_design_review":
        blockers.append("brief_summary_not_ready_for_human_design_review")
    if brief_gate.get("status") != "open_for_design_review_brief":
        blockers.append("brief_gate_not_open")
    if brief_gate.get("implementation_allowed") is not False:
        blockers.append("brief_gate_implementation_not_blocked")
    if summary.get("implementation_allowed") is not False:
        blockers.append("brief_summary_implementation_not_blocked")
    if summary.get("code_patch_authorized") is not False:
        blockers.append("brief_summary_code_patch_not_blocked")
    if summary.get("pending_records_are_not_tasks") is not True:
        blockers.append("brief_pending_records_not_background")
    if summary.get("ready_for_design_review_candidates") != EXPECTED_READY_ACTION_COUNT:
        blockers.append("brief_ready_action_count_drift")
    if len(as_list(traceability.get("source_case_ids"))) != EXPECTED_SOURCE_CASE_COUNT:
        blockers.append("brief_source_case_count_drift")
    if len(as_list(traceability.get("design_action_ids"))) != EXPECTED_READY_ACTION_COUNT:
        blockers.append("brief_design_action_id_count_drift")
    if len(track_briefs) != EXPECTED_TRACK_COUNT:
        blockers.append("brief_track_count_drift")
    if as_list(summary.get("review_order")) != EXPECTED_REVIEW_ORDER:
        blockers.append("brief_review_order_drift")
    if gate_scope and summary.get("ready_for_design_review_candidates") != gate_scope.get("design_action_count"):
        blockers.append("brief_gate_action_count_mismatch")
    if gate_scope and summary.get("pending_records_excluded") != gate_scope.get("pending_records_excluded"):
        blockers.append("brief_gate_pending_count_mismatch")

    track_order = [text(as_dict(track).get("action_type")) for track in track_briefs]
    if track_order != EXPECTED_REVIEW_ORDER:
        blockers.append("brief_track_order_drift")
    for index, track_value in enumerate(track_briefs):
        track = as_dict(track_value)
        action_type = text(track.get("action_type")) or str(index)
        if not as_list(track.get("review_questions")):
            blockers.append(f"brief_track_missing_review_questions:{action_type}")
        if not as_list(track.get("decision_points")):
            blockers.append(f"brief_track_missing_decision_points:{action_type}")
        if not as_list(track.get("prohibited_now")):
            blockers.append(f"brief_track_missing_prohibited_now:{action_type}")
        if as_dict(track.get("current_scope")).get("ready_for_design_review_candidates", 0) < 1:
            blockers.append(f"brief_track_empty_scope:{action_type}")

    forbidden_keys, advisory_keys = key_violations(brief_report)
    for key in forbidden_keys:
        blockers.append(f"brief_forbidden_key_present:{key}")
    for key in advisory_keys:
        blockers.append(f"brief_advisory_signal_present:{key}")
    return blockers


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


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


def track_gate_by_action(gate_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {text(as_dict(track).get("action_type")): as_dict(track) for track in as_list(gate_report.get("track_gates"))}


def build_decision_matrix(brief_report: dict[str, Any], gate_report: dict[str, Any], worksheet_ready: bool) -> list[dict[str, Any]]:
    gate_tracks = track_gate_by_action(gate_report)
    rows: list[dict[str, Any]] = []
    for index, track_value in enumerate(as_list(brief_report.get("track_briefs")), start=1):
        track = as_dict(track_value)
        action_type = text(track.get("action_type"))
        profile = TRACK_REVIEW_PROFILES.get(action_type, {})
        scope = as_dict(track.get("current_scope"))
        traceability = as_dict(track.get("traceability"))
        gate_track = gate_tracks.get(action_type, {})
        status = "ready_for_human_design_review" if worksheet_ready and gate_track.get("status") == "open_for_human_design_review_only" else "blocked"
        rows.append({
            "review_order": EXPECTED_REVIEW_ORDER.index(action_type) + 1 if action_type in EXPECTED_REVIEW_ORDER else index,
            "design_track_id": track.get("design_track_id") or action_type,
            "action_type": action_type,
            "display_name": gate_track.get("display_name") or track.get("display_name") or action_type,
            "plain_language_label": profile.get("plain_language_label", action_type),
            "priority_band": track.get("priority_band") or gate_track.get("priority_band") or "",
            "worksheet_status": status,
            "human_review_required": True,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "recommended_next_series": profile.get("recommended_next_series", "future design review"),
            "recommended_next_work": profile.get("recommended_next_work", "human design review"),
            "implementation_precondition": profile.get("implementation_precondition", "future explicit approval required"),
            "critical_human_question": profile.get("critical_human_question", ""),
            "review_goal": profile.get("review_goal", ""),
            "review_prompts": as_list(track.get("review_questions")),
            "design_checkpoints": as_list(track.get("decision_points")),
            "entry_criteria": as_list(track.get("entry_criteria")),
            "exit_criteria": as_list(track.get("exit_criteria")),
            "prohibited_now": as_list(track.get("prohibited_now")),
            "candidate_scope": {
                "ready_for_design_review_candidates": scope.get("ready_for_design_review_candidates", gate_track.get("ready_for_design_review_candidates", 0)),
                "source_case_count": scope.get("source_case_count", gate_track.get("source_case_count", 0)),
                "expected_domains": as_list(scope.get("expected_domains")),
                "risk_level_summary": scope.get("risk_level_summary", {}),
                "confirmed_root_cause_summary": scope.get("confirmed_root_cause_summary", {}),
                "target_area_summary": scope.get("target_area_summary", {}),
            },
            "traceability": {
                "source_case_ids": as_list(traceability.get("source_case_ids")),
                "design_action_ids": as_list(traceability.get("design_action_ids")),
            },
            "route_constraints": [
                "只能进入人工设计评审。",
                "不得把本 worksheet 当作实现授权。",
                "后续实现必须另开版本并重新确认边界。",
            ],
        })
    return sorted(rows, key=lambda row: (int(row.get("review_order") or 999), row.get("action_type") or ""))


def build_summary(gate_report: dict[str, Any], brief_report: dict[str, Any], review_matrix: list[dict[str, Any]], status: str) -> dict[str, Any]:
    gate_scope = as_dict(gate_report.get("review_scope"))
    priority_counts = Counter(text(row.get("priority_band")) for row in review_matrix if text(row.get("priority_band")))
    route_counts = Counter(text(row.get("recommended_next_series")) for row in review_matrix if text(row.get("recommended_next_series")))
    return {
        "status": status,
        "allowed_use": "human_design_review_and_prioritization_only" if status != "blocked" else "blocked",
        "source_gate_status": as_dict(gate_report.get("gate")).get("status"),
        "source_brief_status": as_dict(brief_report.get("summary")).get("status"),
        "review_track_count": len(review_matrix),
        "design_action_count": gate_scope.get("design_action_count", EXPECTED_READY_ACTION_COUNT),
        "source_case_count": gate_scope.get("source_case_count", EXPECTED_SOURCE_CASE_COUNT),
        "pending_records_excluded": gate_scope.get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
        "priority_band_summary": {key: priority_counts[key] for key in sorted(priority_counts)},
        "recommended_next_series_summary": {key: route_counts[key] for key in sorted(route_counts)},
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "captures_formal_review_outcome": False,
        "required_reviewer_action": "review_each_track_and_record_design_direction_outside_this_report",
        "implementation_decision_policy": "must_remain_false_unless_future_explicit_approval_exists",
    }


def build_assertions(
    worksheet_ready: bool,
    gate_blockers: list[str],
    brief_blockers: list[str],
    review_matrix: list[dict[str, Any]],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "source_gate_is_open_for_review_only",
            "status": "passed" if not gate_blockers else "failed",
            "blockers": gate_blockers,
        },
        {
            "name": "source_brief_is_ready_and_traceable",
            "status": "passed" if not brief_blockers else "failed",
            "blockers": brief_blockers,
        },
        {
            "name": "worksheet_has_five_review_rows",
            "status": "passed" if len(review_matrix) == EXPECTED_TRACK_COUNT else "failed",
            "actual": len(review_matrix),
            "expected": EXPECTED_TRACK_COUNT,
        },
        {
            "name": "all_rows_remain_review_only",
            "status": "passed"
            if all(row.get("implementation_allowed") is False and row.get("code_patch_authorized") is False for row in review_matrix)
            else "failed",
        },
        {
            "name": "worksheet_does_not_capture_formal_outcome",
            "status": "passed",
            "captures_formal_review_outcome": False,
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
            "name": "worksheet_ready_only_when_sources_pass",
            "status": "passed" if worksheet_ready == (not gate_blockers and not brief_blockers) else "failed",
            "worksheet_ready": worksheet_ready,
        },
    ]


def build_report(
    gate_report_path: Path = DEFAULT_GATE_REPORT_PATH,
    brief_report_path: Path = DEFAULT_BRIEF_REPORT_PATH,
) -> dict[str, Any]:
    gate_report = load_json(gate_report_path)
    brief_report = load_json(brief_report_path)
    gate_blockers = gate_contract_blockers(gate_report)
    brief_blockers = brief_contract_blockers(brief_report, gate_report, brief_report_path)
    blockers = sorted_unique(gate_blockers + brief_blockers)
    worksheet_ready = not blockers
    decision_matrix = build_decision_matrix(brief_report, gate_report, worksheet_ready)
    status = "ready_for_human_design_review_matrix" if worksheet_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "ready_action_design_review_worksheet_decision_matrix",
        "scope": "offline human design review worksheet only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ready_action_design_review_gate_report": source_meta(gate_report_path, gate_report),
            "ready_action_design_review_brief_report": source_meta(brief_report_path, brief_report),
        },
        "guardrails": WORKSHEET_GUARDRAILS,
        "worksheet_gate": {
            "status": status,
            "human_design_review_allowed": worksheet_ready,
            "allowed_use": "human_design_review_discussion_only" if worksheet_ready else "blocked",
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "captures_formal_review_outcome": False,
            "future_explicit_implementation_approval_required": True,
            "blockers": blockers,
        },
        "summary": build_summary(gate_report, brief_report, decision_matrix, status),
        "decision_matrix": decision_matrix,
        "review_questions": {
            "global_questions": [
                "这条轨道解决的是真实问题，还是单个 case 的偶发现象？",
                "问题发生在召回、排序、最终选择、场景范围，还是人工标注层？",
                "是否需要法律复核人先确认条文范围？",
                "是否存在任何会被误解为实现授权的表述？",
            ],
            "per_track_questions": {
                row["action_type"]: row["review_prompts"] for row in decision_matrix
            },
        },
        "routing_hints": {
            "if_selected_for_next_design_series": {
                "next_status": "ready_for_followup_design_spec_draft",
                "implementation_allowed": False,
                "required_output": "separate_design_spec_draft_not_code",
            },
            "if_needs_legal_review": {
                "next_status": "legal_scope_review_required",
                "block_implementation": True,
            },
            "if_fixture_candidate": {
                "next_status": "fixture_candidate_pool_only",
                "forbid": ["eval_case_write", "golden_fixture_write"],
            },
            "if_not_enough_evidence": {
                "next_status": "defer_or_request_more_cases",
                "reason_required": True,
            },
        },
        "excluded_scope": {
            "pending_records_excluded": as_dict(gate_report.get("review_scope")).get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
            "pending_records_policy": "background_count_only_not_work_items",
            "ai_suggestion_policy": "advisory_only_not_authority",
            "formal_review_outcome_policy": "not_captured_by_this_report",
        },
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_case_ids": as_list(as_dict(gate_report.get("traceability")).get("source_case_ids")),
            "design_action_ids": as_list(as_dict(gate_report.get("traceability")).get("design_action_ids")) if worksheet_ready else [],
            "source_reports": [
                str(gate_report_path),
                str(brief_report_path),
            ],
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        worksheet_ready,
        gate_blockers,
        brief_blockers,
        decision_matrix,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["worksheet_gate"]["status"] = "blocked"
        report["worksheet_gate"]["human_design_review_allowed"] = False
        report["worksheet_gate"]["allowed_use"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra_blockers = []
        if forbidden_output_keys:
            extra_blockers.append("forbidden_output_key_present")
        if readability_errors:
            extra_blockers.append("blocked_for_human_readability")
        report["worksheet_gate"]["blockers"] = sorted_unique(report["worksheet_gate"]["blockers"] + extra_blockers)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    gate = as_dict(report.get("worksheet_gate"))
    lines = [
        "# v0.4.7.9.3 Ready Action Design Review Worksheet",
        "",
        "本文件是人工设计评审用的 worksheet。它把 5 条设计轨道整理成可审阅清单，但不记录正式人工结论，也不批准任何代码、配置、样例或主流程修改。",
        "",
        "## 总览",
        "",
        f"- Worksheet status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Review tracks: {summary.get('review_track_count')}",
        f"- Design actions: {summary.get('design_action_count')}",
        f"- Source cases: {summary.get('source_case_count')}",
        f"- Pending records excluded: {summary.get('pending_records_excluded')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        f"- Captures formal review outcome: {gate.get('captures_formal_review_outcome')}",
        "",
        "## Review Matrix",
        "",
        "| Order | Priority | Track | Plain meaning | Candidates | Next series | Status |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for row in as_list(report.get("decision_matrix")):
        candidates = as_dict(row.get("candidate_scope")).get("ready_for_design_review_candidates")
        lines.append(
            f"| {row.get('review_order')} | {row.get('priority_band')} | {row.get('display_name')} | "
            f"{row.get('plain_language_label')} | {candidates} | {row.get('recommended_next_series')} | `{row.get('worksheet_status')}` |"
        )

    lines.extend([
        "",
        "## Human Review Questions",
        "",
    ])
    for row in as_list(report.get("decision_matrix")):
        lines.append(f"### {row.get('review_order')}. {row.get('display_name')}")
        lines.append("")
        lines.append(f"- 核心问题：{row.get('critical_human_question')}")
        lines.append(f"- 评审目标：{row.get('review_goal')}")
        lines.append(f"- 可能后续：`{row.get('recommended_next_series')}` / {row.get('recommended_next_work')}")
        lines.append(f"- 实现前提：{row.get('implementation_precondition')}")
        lines.append("- 需要讨论：")
        for prompt in as_list(row.get("review_prompts")):
            lines.append(f"  - {prompt}")
        lines.append("- 当前禁止：")
        for item in as_list(row.get("prohibited_now")):
            lines.append(f"  - `{item}`")
        lines.append("")

    lines.extend([
        "## Boundaries",
        "",
        "- 本 worksheet 只帮助人工评审设计方向，不记录正式人工结论。",
        "- `implementation_allowed=false` 和 `code_patch_authorized=false` 必须保持不变。",
        "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约或 RAG 主流程。",
        "- 后续若进入 v0.4.8.x、v0.4.9.x 或 fixture governance，必须另开版本并重新确认边界。",
        "",
        "## Sources",
        "",
        f"- Gate report: `{report['inputs']['ready_action_design_review_gate_report']['path']}`",
        f"- Brief report: `{report['inputs']['ready_action_design_review_brief_report']['path']}`",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a read-only ready-action design review worksheet.")
    parser.add_argument("--gate-report", type=Path, default=DEFAULT_GATE_REPORT_PATH)
    parser.add_argument("--brief-report", type=Path, default=DEFAULT_BRIEF_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.gate_report, args.brief_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Ready action design review worksheet built: "
        f"{summary['status']}, "
        f"{summary['review_track_count']} tracks, "
        f"{summary['design_action_count']} design actions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
