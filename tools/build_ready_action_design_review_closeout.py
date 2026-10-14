"""Build a read-only closeout envelope for design review tracks.

The closeout envelope reads the saved v0.4.7.9.3 worksheet and prepares five
review tracks for human closeout discussion. It does not capture formal human
outcomes, authorize implementation, create engineering tasks, call RAG, contact
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


VERSION = "0.4.7.9.4"

DEFAULT_WORKSHEET_REPORT_PATH = legacy_report_path("ready_action_design_review_worksheet_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ready_action_design_review_closeout_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ready_action_design_review_closeout_v0.4.7.9.4.md")

EXPECTED_WORKSHEET_VERSION = "0.4.7.9.3"
EXPECTED_WORKSHEET_SCHEMA = "ready_action_design_review_worksheet_decision_matrix"
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

TRACK_CLOSEOUT_PROFILES = {
    "final_evidence_selection_policy_review": {
        "candidate_route": "v0.4.8.x_final_evidence_selection_policy_design",
        "route_label": "最终证据选择策略设计草案",
        "closeout_question": "是否确认主要问题在最终 evidence_chain 选择，而不是召回、场景范围或提示词？",
        "minimum_human_basis": "至少确认关键证据已进入候选池但未进入最终证据链，并说明后续 simulator 的保护口径。",
        "recommended_closeout_option": "continue_to_design_spec_draft",
    },
    "primary_evidence_fixture_candidate_review": {
        "candidate_route": "fixture_governance_review",
        "route_label": "主证据 fixture 候选治理",
        "closeout_question": "是否确认这些候选可代表通用主证据缺口，而不是单案补丁？",
        "minimum_human_basis": "至少确认候选证据、主争点、来源 case 和不写入 eval case 的边界。",
        "recommended_closeout_option": "needs_legal_or_fixture_scope_review",
    },
    "high_risk_manual_grounding_review": {
        "candidate_route": "manual_grounding_review",
        "route_label": "高风险结论人工 grounding 评审",
        "closeout_question": "是否确认风险类型、整改动作或法律后果需要更强证据支撑规则？",
        "minimum_human_basis": "至少说明哪些高风险结论不能被当前 evidence_chain 直接支撑。",
        "recommended_closeout_option": "continue_to_design_spec_draft",
    },
    "scenario_registry_core_article_review": {
        "candidate_route": "scenario_core_article_review",
        "route_label": "场景核心条文范围复核",
        "closeout_question": "是否确认缺失条文属于该场景的核心法律依据？",
        "minimum_human_basis": "至少由人工确认核心条文清单边界；本报告不修改 scenario registry。",
        "recommended_closeout_option": "needs_legal_or_fixture_scope_review",
    },
    "functional_typing_fixture_review": {
        "candidate_route": "legal_functional_typing_fixture_review",
        "route_label": "法律功能类型 fixture 评审",
        "closeout_question": "是否确认条文功能类型足够明确，适合进入 fixture 候选池？",
        "minimum_human_basis": "至少确认定义、义务、责任或程序功能标签及其人工标注规范。",
        "recommended_closeout_option": "needs_legal_or_fixture_scope_review",
    },
}

CLOSEOUT_OPTIONS = [
    {
        "option": "continue_to_design_spec_draft",
        "meaning": "人工确认方向成立，可进入后续设计草案；仍不允许实现。",
        "implementation_allowed": False,
    },
    {
        "option": "needs_legal_or_fixture_scope_review",
        "meaning": "需要先补法律范围或 fixture 范围复核；仍不允许实现。",
        "implementation_allowed": False,
    },
    {
        "option": "defer_pending_more_cases",
        "meaning": "现有 5 个 pilot case 不足以支撑该方向，等待更多人工复核 case。",
        "implementation_allowed": False,
    },
    {
        "option": "close_without_followup",
        "meaning": "本轮不继续推进该方向；不得生成工程任务。",
        "implementation_allowed": False,
    },
]

CLOSEOUT_GUARDRAILS = {
    "closeout_envelope_only": True,
    "source_worksheet_only": True,
    "human_closeout_discussion_aid_only": True,
    "captures_formal_review_outcome": False,
    "formal_human_outcome_recorded": False,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
    "pending_records_to_work_items": "disallowed",
    "candidate_route_to_work_items": "disallowed",
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
    "human_confirmation_required",
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


def worksheet_contract_blockers(worksheet_report: dict[str, Any]) -> list[str]:
    if not worksheet_report:
        return ["missing_or_invalid_worksheet_report"]

    blockers: list[str] = []
    gate = as_dict(worksheet_report.get("worksheet_gate"))
    summary = as_dict(worksheet_report.get("summary"))
    implementation_gate = as_dict(worksheet_report.get("implementation_gate"))
    matrix = as_list(worksheet_report.get("decision_matrix"))
    assertions = as_list(worksheet_report.get("assertions"))

    if worksheet_report.get("version") != EXPECTED_WORKSHEET_VERSION:
        blockers.append("worksheet_version_mismatch")
    if worksheet_report.get("schema_kind") != EXPECTED_WORKSHEET_SCHEMA:
        blockers.append("worksheet_schema_mismatch")
    if gate.get("status") != "ready_for_human_design_review_matrix":
        blockers.append("worksheet_gate_not_ready")
    if gate.get("human_design_review_allowed") is not True:
        blockers.append("worksheet_human_review_not_allowed")
    if gate.get("implementation_allowed") is not False:
        blockers.append("worksheet_gate_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("worksheet_gate_code_patch_not_blocked")
    if gate.get("handoff_to_implementation") != "not_allowed":
        blockers.append("worksheet_gate_handoff_not_blocked")
    if gate.get("captures_formal_review_outcome") is not False:
        blockers.append("worksheet_captures_formal_outcome")
    if as_list(gate.get("blockers")):
        blockers.append("worksheet_gate_has_blockers")
    if implementation_gate.get("implementation_allowed") is not False:
        blockers.append("worksheet_implementation_gate_not_blocked")
    if implementation_gate.get("code_patch_authorized") is not False:
        blockers.append("worksheet_implementation_code_patch_not_blocked")
    if summary.get("review_track_count") != EXPECTED_TRACK_COUNT:
        blockers.append("worksheet_track_count_drift")
    if summary.get("design_action_count") != EXPECTED_READY_ACTION_COUNT:
        blockers.append("worksheet_action_count_drift")
    if summary.get("source_case_count") != EXPECTED_SOURCE_CASE_COUNT:
        blockers.append("worksheet_source_case_count_drift")
    if summary.get("pending_records_excluded") != EXPECTED_PENDING_EXCLUDED:
        blockers.append("worksheet_pending_excluded_count_drift")
    if summary.get("implementation_allowed") is not False:
        blockers.append("worksheet_summary_implementation_not_blocked")
    if summary.get("code_patch_authorized") is not False:
        blockers.append("worksheet_summary_code_patch_not_blocked")
    if summary.get("captures_formal_review_outcome") is not False:
        blockers.append("worksheet_summary_captures_formal_outcome")
    if len(matrix) != EXPECTED_TRACK_COUNT:
        blockers.append("worksheet_matrix_count_drift")
    track_order = [text(as_dict(row).get("action_type")) for row in matrix]
    if track_order != EXPECTED_REVIEW_ORDER:
        blockers.append("worksheet_matrix_order_drift")
    for index, row_value in enumerate(matrix):
        row = as_dict(row_value)
        action_type = text(row.get("action_type")) or str(index)
        if row.get("worksheet_status") != "ready_for_human_design_review":
            blockers.append(f"worksheet_row_not_ready:{action_type}")
        if row.get("human_review_required") is not True:
            blockers.append(f"worksheet_row_human_review_not_required:{action_type}")
        if row.get("implementation_allowed") is not False:
            blockers.append(f"worksheet_row_implementation_not_blocked:{action_type}")
        if row.get("code_patch_authorized") is not False:
            blockers.append(f"worksheet_row_code_patch_not_blocked:{action_type}")
        if not as_list(as_dict(row.get("traceability")).get("source_case_ids")):
            blockers.append(f"worksheet_row_missing_source_cases:{action_type}")
        if not as_list(as_dict(row.get("traceability")).get("design_action_ids")):
            blockers.append(f"worksheet_row_missing_design_actions:{action_type}")
    if not assertions:
        blockers.append("worksheet_assertions_missing")
    elif any(as_dict(item).get("status") != "passed" for item in assertions):
        blockers.append("worksheet_assertions_not_all_passed")

    forbidden_keys, advisory_keys = key_violations(worksheet_report)
    for key in forbidden_keys:
        blockers.append(f"worksheet_forbidden_key_present:{key}")
    for key in advisory_keys:
        blockers.append(f"worksheet_advisory_signal_present:{key}")
    return sorted_unique(blockers)


def build_closeout_rows(worksheet_report: dict[str, Any], closeout_ready: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row_value in enumerate(as_list(worksheet_report.get("decision_matrix")), start=1):
        row = as_dict(row_value)
        action_type = text(row.get("action_type"))
        profile = TRACK_CLOSEOUT_PROFILES.get(action_type, {})
        candidate_scope = as_dict(row.get("candidate_scope"))
        traceability = as_dict(row.get("traceability"))
        status = "pending_human_closeout" if closeout_ready else "blocked"
        rows.append({
            "review_order": EXPECTED_REVIEW_ORDER.index(action_type) + 1 if action_type in EXPECTED_REVIEW_ORDER else index,
            "design_track_id": row.get("design_track_id") or action_type,
            "action_type": action_type,
            "display_name": row.get("display_name") or action_type,
            "priority_band": row.get("priority_band") or "",
            "closeout_status": status,
            "human_closeout_required": True,
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "candidate_route": profile.get("candidate_route", "defer_pending_human_closeout"),
            "candidate_route_label": profile.get("route_label", "待人工收口后再分流"),
            "candidate_route_authorized": False,
            "recommended_closeout_option": profile.get("recommended_closeout_option", "defer_pending_more_cases"),
            "closeout_question": profile.get("closeout_question", ""),
            "minimum_human_basis": profile.get("minimum_human_basis", ""),
            "source_review_goal": row.get("review_goal", ""),
            "source_critical_question": row.get("critical_human_question", ""),
            "candidate_closeout_options": CLOSEOUT_OPTIONS,
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
            "route_constraints": [
                "本报告只提供人工收口外壳。",
                "候选分流不等于实现授权。",
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


def build_summary(worksheet_report: dict[str, Any], closeout_rows: list[dict[str, Any]], status: str) -> dict[str, Any]:
    worksheet_summary = as_dict(worksheet_report.get("summary"))
    priority_counts = Counter(text(row.get("priority_band")) for row in closeout_rows if text(row.get("priority_band")))
    route_counts = Counter(text(row.get("candidate_route")) for row in closeout_rows if text(row.get("candidate_route")))
    option_counts = Counter(text(row.get("recommended_closeout_option")) for row in closeout_rows if text(row.get("recommended_closeout_option")))
    return {
        "status": status,
        "allowed_use": "human_closeout_discussion_only" if status != "blocked" else "blocked",
        "source_worksheet_status": as_dict(worksheet_report.get("worksheet_gate")).get("status"),
        "closeout_track_count": len(closeout_rows),
        "design_action_count": worksheet_summary.get("design_action_count", EXPECTED_READY_ACTION_COUNT),
        "source_case_count": worksheet_summary.get("source_case_count", EXPECTED_SOURCE_CASE_COUNT),
        "pending_records_excluded": worksheet_summary.get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
        "priority_band_summary": {key: priority_counts[key] for key in sorted(priority_counts)},
        "candidate_route_summary": {key: route_counts[key] for key in sorted(route_counts)},
        "recommended_closeout_option_summary": {key: option_counts[key] for key in sorted(option_counts)},
        "formal_human_outcome_recorded": False,
        "captures_formal_review_outcome": False,
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "next_design_authorized": False,
        "required_reviewer_action": "record_human_closeout_outside_this_report_before_any_followup_design",
        "implementation_decision_policy": "must_remain_false_unless_future_explicit_approval_exists",
    }


def build_assertions(
    closeout_ready: bool,
    worksheet_blockers: list[str],
    closeout_rows: list[dict[str, Any]],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "source_worksheet_is_ready_for_closeout_envelope",
            "status": "passed" if not worksheet_blockers else "failed",
            "blockers": worksheet_blockers,
        },
        {
            "name": "closeout_has_five_review_rows",
            "status": "passed" if len(closeout_rows) == EXPECTED_TRACK_COUNT else "failed",
            "actual": len(closeout_rows),
            "expected": EXPECTED_TRACK_COUNT,
        },
        {
            "name": "all_rows_remain_pending_human_closeout",
            "status": "passed"
            if all(row.get("closeout_status") == ("pending_human_closeout" if closeout_ready else "blocked") for row in closeout_rows)
            else "failed",
        },
        {
            "name": "all_rows_remain_non_implementation",
            "status": "passed"
            if all(row.get("implementation_allowed") is False and row.get("code_patch_authorized") is False for row in closeout_rows)
            else "failed",
        },
        {
            "name": "formal_outcomes_not_captured",
            "status": "passed"
            if all(row.get("formal_human_outcome_recorded") is False for row in closeout_rows)
            else "failed",
        },
        {
            "name": "candidate_routes_not_authorized",
            "status": "passed" if all(row.get("candidate_route_authorized") is False for row in closeout_rows) else "failed",
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
            "name": "closeout_ready_only_when_source_passes",
            "status": "passed" if closeout_ready == (not worksheet_blockers) else "failed",
            "closeout_ready": closeout_ready,
        },
    ]


def build_report(worksheet_report_path: Path = DEFAULT_WORKSHEET_REPORT_PATH) -> dict[str, Any]:
    worksheet_report = load_json(worksheet_report_path)
    worksheet_blockers = worksheet_contract_blockers(worksheet_report)
    closeout_ready = not worksheet_blockers
    closeout_rows = build_closeout_rows(worksheet_report, closeout_ready)
    status = "pending_human_design_closeout" if closeout_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "ready_action_design_review_closeout_envelope",
        "scope": "offline human design review closeout envelope only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ready_action_design_review_worksheet_report": source_meta(worksheet_report_path, worksheet_report),
        },
        "guardrails": CLOSEOUT_GUARDRAILS,
        "closeout_gate": {
            "status": status,
            "human_closeout_allowed": closeout_ready,
            "allowed_use": "human_closeout_discussion_only" if closeout_ready else "blocked",
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "next_design_authorized": False,
            "future_explicit_implementation_approval_required": True,
            "blockers": worksheet_blockers,
        },
        "summary": build_summary(worksheet_report, closeout_rows, status),
        "closeout_matrix": closeout_rows,
        "closeout_options": CLOSEOUT_OPTIONS,
        "route_policy": {
            "candidate_routes_are_not_authorized": True,
            "human_closeout_required_before_followup_design": True,
            "implementation_allowed": False,
            "next_allowed_artifact": "separate_human_closeout_record_or_future_design_spec_draft",
        },
        "excluded_scope": {
            "pending_records_excluded": as_dict(worksheet_report.get("summary")).get("pending_records_excluded", EXPECTED_PENDING_EXCLUDED),
            "pending_records_policy": "background_count_only_not_work_items",
            "formal_outcome_policy": "not_captured_by_this_report",
            "candidate_route_policy": "not_authorized_by_this_report",
        },
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_case_ids": as_list(as_dict(worksheet_report.get("traceability")).get("source_case_ids")),
            "design_action_ids": as_list(as_dict(worksheet_report.get("traceability")).get("design_action_ids")) if closeout_ready else [],
            "source_reports": [str(worksheet_report_path)],
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        closeout_ready,
        worksheet_blockers,
        closeout_rows,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["closeout_gate"]["status"] = "blocked"
        report["closeout_gate"]["human_closeout_allowed"] = False
        report["closeout_gate"]["allowed_use"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra_blockers = []
        if forbidden_output_keys:
            extra_blockers.append("forbidden_output_key_present")
        if readability_errors:
            extra_blockers.append("blocked_for_human_readability")
        report["closeout_gate"]["blockers"] = sorted_unique(report["closeout_gate"]["blockers"] + extra_blockers)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("closeout_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.7.9.4 Ready Action Design Review Closeout Envelope",
        "",
        "本文件是人工设计评审的收口外壳。它列出 5 条设计轨道的候选分流和人工确认问题，但不记录正式人工结论，也不批准任何代码、配置、样例或主流程修改。",
        "",
        "## 总览",
        "",
        f"- Closeout status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Closeout tracks: {summary.get('closeout_track_count')}",
        f"- Design actions: {summary.get('design_action_count')}",
        f"- Source cases: {summary.get('source_case_count')}",
        f"- Pending records excluded: {summary.get('pending_records_excluded')}",
        f"- Formal outcome recorded: {gate.get('formal_human_outcome_recorded')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        f"- Next design authorized: {gate.get('next_design_authorized')}",
        "",
        "## Closeout Matrix",
        "",
        "| Order | Priority | Track | Candidate route | Suggested option | Status |",
        "|---:|---|---|---|---|---|",
    ]
    for row in as_list(report.get("closeout_matrix")):
        lines.append(
            f"| {row.get('review_order')} | {row.get('priority_band')} | {row.get('display_name')} | "
            f"{row.get('candidate_route_label')} | `{row.get('recommended_closeout_option')}` | `{row.get('closeout_status')}` |"
        )

    lines.extend([
        "",
        "## Human Closeout Questions",
        "",
    ])
    for row in as_list(report.get("closeout_matrix")):
        lines.append(f"### {row.get('review_order')}. {row.get('display_name')}")
        lines.append("")
        lines.append(f"- 收口问题：{row.get('closeout_question')}")
        lines.append(f"- 最小人工依据：{row.get('minimum_human_basis')}")
        lines.append(f"- 候选分流：`{row.get('candidate_route')}` / {row.get('candidate_route_label')}")
        lines.append(f"- 当前状态：`{row.get('closeout_status')}`")
        lines.append("- 可选收口口径：")
        for option in as_list(row.get("candidate_closeout_options")):
            item = as_dict(option)
            lines.append(f"  - `{item.get('option')}`：{item.get('meaning')}")
        lines.append("- 当前禁止：")
        for item in as_list(row.get("route_constraints")):
            lines.append(f"  - {item}")
        lines.append("")

    lines.extend([
        "## Boundaries",
        "",
        "- 本 closeout envelope 只帮助人工收口讨论，不记录正式人工结论。",
        "- `formal_human_outcome_recorded=false`、`implementation_allowed=false`、`code_patch_authorized=false` 和 `next_design_authorized=false` 必须保持不变。",
        "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约或 RAG 主流程。",
        "- 后续若进入 v0.4.8.x、v0.4.9.x 或 fixture governance，必须另开版本并重新确认边界。",
        "",
        "## Source",
        "",
        f"- Worksheet report: `{report['inputs']['ready_action_design_review_worksheet_report']['path']}`",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a read-only ready-action design review closeout envelope.")
    parser.add_argument("--worksheet-report", type=Path, default=DEFAULT_WORKSHEET_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.worksheet_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Ready action design review closeout envelope built: "
        f"{summary['status']}, "
        f"{summary['closeout_track_count']} tracks, "
        f"{summary['design_action_count']} design actions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
