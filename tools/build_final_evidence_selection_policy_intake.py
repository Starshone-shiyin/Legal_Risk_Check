"""Build the v0.4.8.0 final-evidence selection policy intake.

The intake is a read-only design artifact. It consolidates confirmed
final-evidence selection loss signals into policy-design inputs, but it does
not implement a policy, change rerank, alter prompts, mutate eval cases, call
RAG, contact Qdrant or an LLM, or connect anything to the main flow.
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


VERSION = "0.4.8.0"

DEFAULT_CONFIRMATION_REPORT_PATH = legacy_report_path("ready_action_human_closeout_confirmation_record_report.json")
DEFAULT_DECISION_DRAFT_REPORT_PATH = legacy_report_path("ready_action_human_closeout_decision_draft_report.json")
DEFAULT_CLOSEOUT_REPORT_PATH = legacy_report_path("ready_action_design_review_closeout_report.json")
DEFAULT_WORKSHEET_REPORT_PATH = legacy_report_path("ready_action_design_review_worksheet_report.json")
DEFAULT_DESIGN_PACK_REPORT_PATH = legacy_report_path("ready_action_design_pack_report.json")
DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH = legacy_report_path("final_evidence_selection_audit_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_intake_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_intake_v0.4.8.0.md")

EXPECTED_CONFIRMATION_VERSION = "0.4.7.9.6"
EXPECTED_CONFIRMATION_SCHEMA = "ready_action_human_closeout_confirmation_record"
EXPECTED_DRAFT_VERSION = "0.4.7.9.5"
EXPECTED_DRAFT_SCHEMA = "ready_action_human_closeout_decision_draft"
EXPECTED_CLOSEOUT_VERSION = "0.4.7.9.4"
EXPECTED_CLOSEOUT_SCHEMA = "ready_action_design_review_closeout_envelope"
EXPECTED_WORKSHEET_VERSION = "0.4.7.9.3"
EXPECTED_WORKSHEET_SCHEMA = "ready_action_design_review_worksheet_decision_matrix"
EXPECTED_DESIGN_PACK_VERSION = "0.4.7.9.0"
EXPECTED_DESIGN_PACK_SCHEMA = "governed_ready_action_design_pack"
EXPECTED_AUDIT_VERSION = "0.4.7.4.5"
EXPECTED_TRACK_ACTION = "final_evidence_selection_policy_review"
EXPECTED_NEXT_SERIES = "v0.4.8.x"
EXPECTED_CONFIRMED_CASE_COUNT = 5
EXPECTED_FINAL_SELECTION_ACTION_COUNT = 5
EXPECTED_PENDING_EXCLUDED = 31

INTAKE_GUARDRAILS = {
    "design_intake_only": True,
    "source_reports_only": True,
    "not_policy_implementation": True,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_selection_policy_patch_allowed": False,
    "rerank_change_allowed": False,
    "prompt_change_allowed": False,
    "final_evidence_selection_runtime_change": "disallowed",
    "policy_simulator_runtime_integration": "disallowed",
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

NON_GOALS = [
    "不修改 rerank 或 final evidence selection runtime 逻辑。",
    "不新增 anchor，不修改 hidden seed，不修改 prompt。",
    "不修改 risk supplement、term preservation、scenario registry、eval case 或 fixture。",
    "不接入 RAG 主流程，不调用后端、Qdrant 或 LLM。",
    "不把 intake row 转成工程任务、backlog 或 patch plan。",
]

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
    "work_items",
    "engineering_tasks",
    "pending_tasks",
    "implementation_queue",
    "completed_outcomes",
    "formal_review_outcomes",
}

FORBIDDEN_OUTPUT_KEYS = set(FORBIDDEN_SOURCE_KEYS)

ADVISORY_SOURCE_KEYS = {
    "ai_suggestion",
    "safe_ai_suggestion_input",
    "advisory_packet_only",
    "prescreen_advisory",
    "pilot_assist",
    "mobile_aid",
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

POLICY_QUESTIONS = [
    {
        "question_id": "primary_evidence_preservation",
        "priority": "P0",
        "plain_question": "已经进入候选池的主证据，什么情况下必须进入 final evidence_chain？",
        "design_reason": "人工确认的 5 个 pilot case 均涉及 final evidence selection policy，audit 中 primary_evidence_lost 为主要信号。",
    },
    {
        "question_id": "operative_and_procedural_preservation",
        "priority": "P0",
        "plain_question": "义务、程序、权利或技术支撑类条文是否需要比背景性条文更高的保留优先级？",
        "design_reason": "audit 的 lost functional types 包含 operative_rule 与 procedural，且多例出现 operative_evidence_lost。",
    },
    {
        "question_id": "liability_and_consequence_preservation",
        "priority": "P0",
        "plain_question": "答案涉及处罚、赔偿、责任后果或高风险结论时，是否必须保留责任/后果支撑条款？",
        "design_reason": "risk_employee_data_export_001 出现 liability evidence loss，且高风险结论需要更强 grounding。",
    },
    {
        "question_id": "scenario_core_preservation",
        "priority": "P1",
        "plain_question": "场景核心条文已进入前序候选层时，final evidence 是否必须保留或给出可解释替代？",
        "design_reason": "audit 中 scenario_core_lost 出现在多个高优先级 case。",
    },
    {
        "question_id": "definition_clause_substitution_guard",
        "priority": "P1",
        "plain_question": "定义条款是否只能补充解释，不能替代义务、程序、责任或后果条款？",
        "design_reason": "Harvey-style grounding 需要区分定义性依据和可直接支撑结论的规范性依据。",
    },
    {
        "question_id": "final_coverage_floor",
        "priority": "P1",
        "plain_question": "final evidence coverage 低于什么诊断阈值时，必须进入人工复核或 simulator 失败状态？",
        "design_reason": "audit 中存在 low_final_coverage_after_selection 信号。",
    },
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


def counter_dict(counter: Counter) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


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


def confirmation_final_row(confirmation: dict[str, Any]) -> dict[str, Any]:
    for row in as_list(confirmation.get("confirmation_matrix")):
        item = as_dict(row)
        if item.get("action_type") == EXPECTED_TRACK_ACTION:
            return item
    return {}


def design_pack_final_group(design_pack: dict[str, Any]) -> dict[str, Any]:
    return as_dict(as_dict(design_pack.get("action_groups")).get(EXPECTED_TRACK_ACTION))


def audit_case_map(audit_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in as_list(audit_report.get("cases")):
        row = as_dict(item)
        case_id = text(row.get("case_id"))
        if case_id:
            result[case_id] = row
    return result


def source_contract_blockers(
    confirmation: dict[str, Any],
    draft: dict[str, Any],
    closeout: dict[str, Any],
    worksheet: dict[str, Any],
    design_pack: dict[str, Any],
    audit_report: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    confirmation_gate = as_dict(confirmation.get("confirmation_gate"))
    confirmation_summary = as_dict(confirmation.get("summary"))
    confirmation_row = confirmation_final_row(confirmation)
    design_group = design_pack_final_group(design_pack)
    audit_summary = as_dict(audit_report.get("summary"))

    if confirmation.get("version") != EXPECTED_CONFIRMATION_VERSION:
        blockers.append("confirmation_version_mismatch")
    if confirmation.get("schema_kind") != EXPECTED_CONFIRMATION_SCHEMA:
        blockers.append("confirmation_schema_mismatch")
    if confirmation_gate.get("status") != "confirmed_for_future_design_planning":
        blockers.append("confirmation_gate_not_confirmed")
    if as_list(confirmation_gate.get("blockers")):
        blockers.append("confirmation_gate_has_blockers")
    if confirmation_gate.get("future_design_planning_allowed") is not True:
        blockers.append("confirmation_future_design_not_allowed")
    if confirmation_gate.get("manual_review_importable") is not False:
        blockers.append("confirmation_importable_decision_not_blocked")
    if confirmation_gate.get("implementation_allowed") is not False:
        blockers.append("confirmation_implementation_not_blocked")
    if confirmation_gate.get("code_patch_authorized") is not False:
        blockers.append("confirmation_code_patch_not_blocked")
    if confirmation_gate.get("next_design_authorized") is not False:
        blockers.append("confirmation_next_design_not_blocked")
    if confirmation_summary.get("pending_records_excluded") != EXPECTED_PENDING_EXCLUDED:
        blockers.append("confirmation_pending_excluded_count_drift")
    if not confirmation_row:
        blockers.append("final_selection_confirmation_row_missing")
    else:
        if confirmation_row.get("confirmed_next_series") != EXPECTED_NEXT_SERIES:
            blockers.append("final_selection_next_series_mismatch")
        if confirmation_row.get("future_design_planning_allowed") is not True:
            blockers.append("final_selection_row_not_design_planning_ready")
        if confirmation_row.get("implementation_allowed") is not False:
            blockers.append("final_selection_row_implementation_not_blocked")
        if confirmation_row.get("code_patch_authorized") is not False:
            blockers.append("final_selection_row_code_patch_not_blocked")
        if len(as_list(as_dict(confirmation_row.get("traceability")).get("source_case_ids"))) != EXPECTED_CONFIRMED_CASE_COUNT:
            blockers.append("final_selection_source_case_count_drift")
        if len(as_list(as_dict(confirmation_row.get("traceability")).get("design_action_ids"))) != EXPECTED_FINAL_SELECTION_ACTION_COUNT:
            blockers.append("final_selection_design_action_count_drift")

    source_specs = [
        ("draft", draft, EXPECTED_DRAFT_VERSION, EXPECTED_DRAFT_SCHEMA, "draft_gate", "draft_pending_user_confirmation"),
        ("closeout", closeout, EXPECTED_CLOSEOUT_VERSION, EXPECTED_CLOSEOUT_SCHEMA, "closeout_gate", "pending_human_design_closeout"),
        ("worksheet", worksheet, EXPECTED_WORKSHEET_VERSION, EXPECTED_WORKSHEET_SCHEMA, "worksheet_gate", "ready_for_human_design_review_matrix"),
    ]
    for label, report, expected_version, expected_schema, gate_key, expected_status in source_specs:
        if report.get("version") != expected_version:
            blockers.append(f"{label}_version_mismatch")
        if report.get("schema_kind") != expected_schema:
            blockers.append(f"{label}_schema_mismatch")
        if as_dict(report.get(gate_key)).get("status") != expected_status:
            blockers.append(f"{label}_gate_status_mismatch")
        if as_dict(report.get("summary")).get("implementation_allowed") is not False:
            blockers.append(f"{label}_summary_implementation_not_blocked")

    if design_pack.get("version") != EXPECTED_DESIGN_PACK_VERSION:
        blockers.append("design_pack_version_mismatch")
    if design_pack.get("schema_kind") != EXPECTED_DESIGN_PACK_SCHEMA:
        blockers.append("design_pack_schema_mismatch")
    if as_dict(design_pack.get("planning_gate")).get("status") != "open_for_design_review":
        blockers.append("design_pack_gate_not_open")
    if not design_group:
        blockers.append("design_pack_final_selection_group_missing")
    elif design_group.get("ready_action_count") != EXPECTED_FINAL_SELECTION_ACTION_COUNT:
        blockers.append("design_pack_final_selection_action_count_drift")

    if audit_report.get("version") != EXPECTED_AUDIT_VERSION:
        blockers.append("final_selection_audit_version_mismatch")
    if audit_report.get("scope") != "offline final evidence selection audit":
        blockers.append("final_selection_audit_scope_mismatch")
    if audit_summary.get("high_priority_review_cases") != EXPECTED_CONFIRMED_CASE_COUNT:
        blockers.append("audit_high_priority_count_drift")
    if audit_summary.get("total_final_selection_loss_cases", 0) < EXPECTED_CONFIRMED_CASE_COUNT:
        blockers.append("audit_selection_loss_cases_insufficient")

    for label, report in [
        ("confirmation", confirmation),
        ("draft", draft),
        ("closeout", closeout),
        ("worksheet", worksheet),
        ("design_pack", design_pack),
        ("final_selection_audit", audit_report),
    ]:
        forbidden, advisory = key_violations(report)
        for key in forbidden:
            blockers.append(f"{label}_forbidden_key_present:{key}")
        for key in advisory:
            blockers.append(f"{label}_advisory_signal_present:{key}")

    return sorted_unique(blockers)


def evidence_summary(items: list[Any]) -> dict[str, Any]:
    sources = Counter()
    functional_types = Counter()
    citations = []
    for value in items:
        item = as_dict(value)
        if text(item.get("source")):
            sources[text(item.get("source"))] += 1
        if text(item.get("functional_type")):
            functional_types[text(item.get("functional_type"))] += 1
        if text(item.get("citation")):
            citations.append(text(item.get("citation")))
    return {
        "count": len(items),
        "source_summary": counter_dict(sources),
        "functional_type_summary": counter_dict(functional_types),
        "citations": sorted_unique(citations),
    }


def build_case_intake_rows(
    confirmation_row: dict[str, Any],
    design_group: dict[str, Any],
    audit_report: dict[str, Any],
    intake_ready: bool,
) -> list[dict[str, Any]]:
    case_ids = as_list(as_dict(confirmation_row.get("traceability")).get("source_case_ids"))
    audit_cases = audit_case_map(audit_report)
    design_actions = {
        text(action.get("case_id")): as_dict(action)
        for action in as_list(design_group.get("candidate_actions"))
        if text(as_dict(action).get("case_id"))
    }
    rows = []
    for case_id in sorted_unique([text(case_id) for case_id in case_ids]):
        audit_case = audit_cases.get(case_id, {})
        design_action = design_actions.get(case_id, {})
        rows.append({
            "case_id": case_id,
            "intake_status": "policy_design_input_ready" if intake_ready and audit_case and design_action else "blocked",
            "audit_priority": audit_case.get("priority") or "",
            "risk_level": audit_case.get("risk_level") or design_action.get("risk_level") or "",
            "expected_domains": as_list(audit_case.get("expected_domains")) or as_list(design_action.get("expected_domains")),
            "detected_issues": as_list(audit_case.get("detected_issues")),
            "review_reasons": as_list(audit_case.get("review_reasons")),
            "selection_flow": as_dict(audit_case.get("selection_flow")),
            "lost_evidence_summary": evidence_summary(as_list(audit_case.get("lost_evidence"))),
            "missing_final_expected_summary": evidence_summary(as_list(audit_case.get("missing_final_expected"))),
            "missing_scenario_core_summary": evidence_summary(as_list(audit_case.get("missing_scenario_core"))),
            "design_action": {
                "design_action_id": design_action.get("design_action_id") or f"{case_id}::{EXPECTED_TRACK_ACTION}",
                "priority_score": design_action.get("priority_score"),
                "confirmed_root_causes": as_list(design_action.get("confirmed_root_causes")),
                "target_areas": as_list(design_action.get("target_areas")),
                "source_review_outcome": design_action.get("source_review_outcome") or "",
            },
            "policy_intake_notes": [
                "只作为 policy design 输入。",
                "不得直接改 rerank 或 final evidence runtime。",
                "后续 simulator 必须仍读取 saved report，不接入主流程。",
            ],
        })
    return rows


def build_preservation_items(audit_report: dict[str, Any]) -> list[dict[str, Any]]:
    summary = as_dict(audit_report.get("summary"))
    issue_counts = Counter(as_dict(summary.get("issue_type_summary")))
    functional_counts = Counter(as_dict(summary.get("lost_functional_type_summary")))
    return [
        {
            "item_id": "preserve_primary_evidence",
            "priority": "P0",
            "trigger_signals": ["primary_evidence_lost", "rerank_input_to_final_loss"],
            "source_counts": {
                "primary_evidence_lost": issue_counts.get("primary_evidence_lost", 0),
                "rerank_input_to_final_loss": issue_counts.get("rerank_input_to_final_loss", 0),
            },
            "design_input": "主证据如果已在 rerank_input 出现，policy 草案需定义保留或替代解释条件。",
            "allowed_stage": "design_discussion_only",
        },
        {
            "item_id": "preserve_operative_rule_evidence",
            "priority": "P0",
            "trigger_signals": ["operative_evidence_lost", "operative_rule"],
            "source_counts": {
                "operative_evidence_lost": issue_counts.get("operative_evidence_lost", 0),
                "lost_functional_type_operative_rule": functional_counts.get("operative_rule", 0),
            },
            "design_input": "义务、行为规则或合法性基础类证据需要进入 preservation rule 讨论。",
            "allowed_stage": "design_discussion_only",
        },
        {
            "item_id": "preserve_procedural_evidence",
            "priority": "P0",
            "trigger_signals": ["procedural"],
            "source_counts": {
                "lost_functional_type_procedural": functional_counts.get("procedural", 0),
            },
            "design_input": "程序、告知、评估、申报等条款不能被泛化结论替代。",
            "allowed_stage": "design_discussion_only",
        },
        {
            "item_id": "preserve_liability_evidence",
            "priority": "P0",
            "trigger_signals": ["liability_evidence_lost", "liability"],
            "source_counts": {
                "liability_evidence_lost": issue_counts.get("liability_evidence_lost", 0),
                "lost_functional_type_liability": functional_counts.get("liability", 0),
            },
            "design_input": "答案涉及责任、处罚、赔偿或后果时，需要讨论责任条款的保留底线。",
            "allowed_stage": "design_discussion_only",
        },
        {
            "item_id": "preserve_scenario_core_evidence",
            "priority": "P1",
            "trigger_signals": ["scenario_core_lost"],
            "source_counts": {
                "scenario_core_lost": issue_counts.get("scenario_core_lost", 0),
            },
            "design_input": "场景核心证据丢失需要和 scenario core review 分界，但 policy intake 必须记录该风险。",
            "allowed_stage": "design_discussion_only",
        },
        {
            "item_id": "final_coverage_safety_floor",
            "priority": "P1",
            "trigger_signals": ["low_final_coverage_after_selection"],
            "source_counts": {
                "low_final_coverage_after_selection": issue_counts.get("low_final_coverage_after_selection", 0),
            },
            "design_input": "final evidence coverage 过低时，后续 simulator 应输出失败或人工复核信号。",
            "allowed_stage": "simulator_design_input_only",
        },
    ]


def build_simulator_plan() -> dict[str, Any]:
    return {
        "recommended_next_version": "v0.4.8.1",
        "plan_status": "design_plan_only",
        "runtime_integration_allowed": False,
        "rerank_change_allowed": False,
        "input_policy": "saved_reports_only",
        "required_inputs": [
            "tests/final_evidence_selection_policy_intake_report.json",
            "tests/final_evidence_selection_audit_report.json",
            "tests/ready_action_human_closeout_confirmation_record_report.json",
        ],
        "phases": [
            "draft_policy_table_from_intake",
            "replay_saved_audit_cases_without_runtime_changes",
            "compare_policy_expected_preservation_against_saved_final_chain",
            "produce_manual_review_gate_before_any_implementation",
        ],
        "must_not_do": [
            "do_not_call_rag_or_qdrant",
            "do_not_modify_rerank",
            "do_not_modify_prompt",
            "do_not_modify_eval_cases",
            "do_not_patch_final_selection_runtime",
        ],
    }


def build_summary(
    status: str,
    confirmation_row: dict[str, Any],
    design_group: dict[str, Any],
    audit_report: dict[str, Any],
    rows: list[dict[str, Any]],
    preservation_items: list[dict[str, Any]],
) -> dict[str, Any]:
    audit_summary = as_dict(audit_report.get("summary"))
    domains = Counter()
    risks = Counter()
    issues = Counter()
    for row in rows:
        risks[text(row.get("risk_level")) or "unknown"] += 1
        for domain in as_list(row.get("expected_domains")):
            domains[text(domain) or "unknown"] += 1
        issues.update(as_list(row.get("detected_issues")))
    return {
        "status": status,
        "allowed_use": "final_evidence_selection_policy_design_input_only" if status != "blocked" else "blocked",
        "confirmed_next_series": confirmation_row.get("confirmed_next_series"),
        "confirmed_case_count": len(rows),
        "design_action_count": design_group.get("ready_action_count", 0),
        "pending_records_excluded": EXPECTED_PENDING_EXCLUDED,
        "audit_total_final_selection_loss_cases": audit_summary.get("total_final_selection_loss_cases", 0),
        "audit_high_priority_review_cases": audit_summary.get("high_priority_review_cases", 0),
        "matched_high_priority_case_count": len([row for row in rows if row.get("audit_priority") == "high"]),
        "policy_question_count": len(POLICY_QUESTIONS),
        "preservation_item_count": len(preservation_items),
        "case_risk_level_summary": counter_dict(risks),
        "case_domain_occurrence_summary": counter_dict(domains),
        "case_domain_counting_note": "A case may contribute to multiple domains; this is an occurrence count, not a distinct case count.",
        "case_issue_type_summary": counter_dict(issues),
        "source_audit_issue_type_summary": dict(sorted(as_dict(audit_summary.get("issue_type_summary")).items())),
        "source_lost_functional_type_summary": dict(sorted(as_dict(audit_summary.get("lost_functional_type_summary")).items())),
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "rerank_change_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rag_query_integration": "disallowed",
    }


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


def build_assertions(
    source_blockers: list[str],
    rows: list[dict[str, Any]],
    preservation_items: list[dict[str, Any]],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "source_reports_are_ready_for_intake",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "confirmed_final_selection_cases_are_matched",
            "status": "passed"
            if len(rows) == EXPECTED_CONFIRMED_CASE_COUNT and all(row.get("intake_status") == "policy_design_input_ready" for row in rows)
            else "failed",
            "case_count": len(rows),
            "expected": EXPECTED_CONFIRMED_CASE_COUNT,
        },
        {
            "name": "preservation_items_are_design_only",
            "status": "passed"
            if preservation_items and all(item.get("allowed_stage") in {"design_discussion_only", "simulator_design_input_only"} for item in preservation_items)
            else "failed",
        },
        {
            "name": "implementation_is_not_authorized",
            "status": "passed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "rerank_change_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
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
    ]


def build_report(
    confirmation_report_path: Path = DEFAULT_CONFIRMATION_REPORT_PATH,
    decision_draft_report_path: Path = DEFAULT_DECISION_DRAFT_REPORT_PATH,
    closeout_report_path: Path = DEFAULT_CLOSEOUT_REPORT_PATH,
    worksheet_report_path: Path = DEFAULT_WORKSHEET_REPORT_PATH,
    design_pack_report_path: Path = DEFAULT_DESIGN_PACK_REPORT_PATH,
    final_selection_audit_report_path: Path = DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH,
) -> dict[str, Any]:
    confirmation = load_json(confirmation_report_path)
    draft = load_json(decision_draft_report_path)
    closeout = load_json(closeout_report_path)
    worksheet = load_json(worksheet_report_path)
    design_pack = load_json(design_pack_report_path)
    audit_report = load_json(final_selection_audit_report_path)
    source_blockers = source_contract_blockers(confirmation, draft, closeout, worksheet, design_pack, audit_report)
    intake_ready = not source_blockers
    confirmation_row = confirmation_final_row(confirmation)
    design_group = design_pack_final_group(design_pack)
    case_rows = build_case_intake_rows(confirmation_row, design_group, audit_report, intake_ready)
    preservation_items = build_preservation_items(audit_report)
    status = "ready_for_policy_design_intake" if intake_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_design_intake",
        "scope": "offline final evidence selection policy design intake only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "confirmation_record": source_meta(confirmation_report_path, confirmation),
            "decision_draft": source_meta(decision_draft_report_path, draft),
            "closeout_envelope": source_meta(closeout_report_path, closeout),
            "worksheet": source_meta(worksheet_report_path, worksheet),
            "design_pack": source_meta(design_pack_report_path, design_pack),
            "final_selection_audit": source_meta(final_selection_audit_report_path, audit_report),
        },
        "guardrails": INTAKE_GUARDRAILS,
        "non_goals": NON_GOALS,
        "intake_gate": {
            "status": status,
            "allowed_use": "final_evidence_selection_policy_design_input_only" if intake_ready else "blocked",
            "design_intake_allowed": intake_ready,
            "policy_implementation_allowed": False,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "rag_query_integration": "disallowed",
            "blockers": source_blockers,
        },
        "summary": build_summary(status, confirmation_row, design_group, audit_report, case_rows, preservation_items),
        "source_track_context": {
            "action_type": EXPECTED_TRACK_ACTION,
            "display_name": confirmation_row.get("display_name") or "最终证据选择策略评审",
            "confirmed_direction": confirmation_row.get("confirmed_direction"),
            "confirmation_basis": confirmation_row.get("confirmation_basis"),
            "confirmation_note": confirmation_row.get("confirmation_note"),
            "confirmed_next_series": confirmation_row.get("confirmed_next_series"),
            "candidate_scope": as_dict(confirmation_row.get("candidate_scope")),
        },
        "policy_questions": POLICY_QUESTIONS,
        "preservation_rule_discussion_items": preservation_items,
        "case_intake_matrix": case_rows,
        "policy_simulator_plan": build_simulator_plan(),
        "excluded_scope": {
            "pending_records_excluded": EXPECTED_PENDING_EXCLUDED,
            "pending_records_policy": "background_count_only_not_design_inputs",
            "implementation_policy": "not_authorized_by_this_intake",
            "runtime_policy_patch": "disallowed",
        },
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_case_ids": [row["case_id"] for row in case_rows],
            "design_action_ids": [as_dict(row.get("design_action")).get("design_action_id") for row in case_rows],
            "source_reports": [
                str(confirmation_report_path),
                str(decision_draft_report_path),
                str(closeout_report_path),
                str(worksheet_report_path),
                str(design_pack_report_path),
                str(final_selection_audit_report_path),
            ],
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        case_rows,
        preservation_items,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["intake_gate"]["status"] = "blocked"
        report["intake_gate"]["allowed_use"] = "blocked"
        report["intake_gate"]["design_intake_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["intake_gate"]["blockers"] = sorted_unique(report["intake_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("intake_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.0 Final Evidence Selection Policy Design Intake",
        "",
        "本文件是 v0.4.8.x 最终证据选择策略设计系列的入口材料。它只整理已确认的 final evidence selection loss 和既有审计信号，不实现策略、不修改 rerank、不接入主流程。",
        "",
        "## Overview",
        "",
        f"- Intake status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Confirmed next series: `{summary.get('confirmed_next_series')}`",
        f"- Confirmed cases: {summary.get('confirmed_case_count')}",
        f"- Design actions: {summary.get('design_action_count')}",
        f"- Audit high-priority cases: {summary.get('audit_high_priority_review_cases')}",
        f"- Preservation discussion items: {summary.get('preservation_item_count')}",
        f"- Policy questions: {summary.get('policy_question_count')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Rerank change allowed: {gate.get('rerank_change_allowed')}",
        f"- Runtime selection policy patch allowed: {gate.get('runtime_selection_policy_patch_allowed')}",
        "",
        "## Policy Questions",
        "",
    ]
    for item in as_list(report.get("policy_questions")):
        lines.append(f"- `{item.get('question_id')}` ({item.get('priority')}): {item.get('plain_question')}")

    lines.extend([
        "",
        "## Preservation Discussion Items",
        "",
        "| Item | Priority | Signals | Design Input |",
        "|---|---|---|---|",
    ])
    for item in as_list(report.get("preservation_rule_discussion_items")):
        lines.append(
            f"| `{item.get('item_id')}` | {item.get('priority')} | "
            f"{', '.join(as_list(item.get('trigger_signals')))} | {item.get('design_input')} |"
        )

    lines.extend([
        "",
        "## Case Intake Matrix",
        "",
        "| Case | Priority | Risk | Issues | Lost Evidence | Status |",
        "|---|---|---|---|---:|---|",
    ])
    for row in as_list(report.get("case_intake_matrix")):
        lines.append(
            f"| `{row.get('case_id')}` | {row.get('audit_priority')} | {row.get('risk_level')} | "
            f"{', '.join(as_list(row.get('detected_issues')))} | "
            f"{as_dict(row.get('lost_evidence_summary')).get('count', 0)} | `{row.get('intake_status')}` |"
        )

    simulator = as_dict(report.get("policy_simulator_plan"))
    lines.extend([
        "",
        "## Simulator Plan",
        "",
        f"- Recommended next version: `{simulator.get('recommended_next_version')}`",
        f"- Plan status: `{simulator.get('plan_status')}`",
        f"- Runtime integration allowed: {simulator.get('runtime_integration_allowed')}",
        f"- Input policy: `{simulator.get('input_policy')}`",
        "",
        "## Boundaries",
        "",
        "- 本 intake 不是策略实现、rerank 修复、selection policy patch 或主流程接入。",
        "- `implementation_allowed=false`、`code_patch_authorized=false`、`rerank_change_allowed=false` 必须保持不变。",
        "- 不修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer 或 dry-run 契约。",
        "- 不调用后端、Qdrant、LLM，不运行 full eval，不接入 RAG 主流程。",
        "",
        "## Sources",
        "",
    ])
    for label, meta in as_dict(report.get("inputs")).items():
        lines.append(f"- {label}: `{as_dict(meta).get('path')}`")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build final evidence selection policy design intake.")
    parser.add_argument("--confirmation-report", type=Path, default=DEFAULT_CONFIRMATION_REPORT_PATH)
    parser.add_argument("--decision-draft-report", type=Path, default=DEFAULT_DECISION_DRAFT_REPORT_PATH)
    parser.add_argument("--closeout-report", type=Path, default=DEFAULT_CLOSEOUT_REPORT_PATH)
    parser.add_argument("--worksheet-report", type=Path, default=DEFAULT_WORKSHEET_REPORT_PATH)
    parser.add_argument("--design-pack-report", type=Path, default=DEFAULT_DESIGN_PACK_REPORT_PATH)
    parser.add_argument("--final-selection-audit-report", type=Path, default=DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        args.confirmation_report,
        args.decision_draft_report,
        args.closeout_report,
        args.worksheet_report,
        args.design_pack_report,
        args.final_selection_audit_report,
    )
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy intake built: "
        f"{summary['status']}, "
        f"{summary['confirmed_case_count']} cases, "
        f"{summary['preservation_item_count']} preservation items"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
