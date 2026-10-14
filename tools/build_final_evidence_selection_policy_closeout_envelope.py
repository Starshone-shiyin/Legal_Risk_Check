"""Build the v0.4.8.4 final-evidence policy closeout envelope.

The closeout envelope reads the saved v0.4.8.3 human-review worksheet and
prepares eight policy rows for human closeout discussion. It does not capture
formal human outcomes, authorize implementation, create engineering tasks, call
RAG, contact Qdrant or an LLM, or mutate retrieval, prompts, rules, fixtures,
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


VERSION = "0.4.8.4"

DEFAULT_WORKSHEET_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_human_review_worksheet_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_closeout_envelope_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md")

EXPECTED_WORKSHEET_VERSION = "0.4.8.3"
EXPECTED_WORKSHEET_SCHEMA = "final_evidence_selection_policy_human_review_worksheet"
EXPECTED_WORKSHEET_SCOPE = "offline final evidence selection policy human review worksheet only"
EXPECTED_WORKSHEET_STATUS = "ready_for_policy_table_human_review_worksheet"
EXPECTED_REVIEW_ROW_COUNT = 8
EXPECTED_CASE_COUNT = 5
EXPECTED_POLICY_CATEGORIES = [
    "primary",
    "operative",
    "procedural",
    "liability",
    "scenario_core",
    "definition_only",
    "coverage_floor",
    "high_risk_manual_review",
]
EXPECTED_SOURCE_POLICY_IDS = [f"FES-POLICY-DRAFT-{index:03d}" for index in range(1, 9)]

CLOSEOUT_OPTIONS = [
    {
        "option": "accept_for_future_offline_simulation_design",
        "meaning": "人工确认该 policy 方向可进入后续离线模拟设计；仍不允许实现。",
        "implementation_allowed": False,
    },
    {
        "option": "revise_policy_language_before_closeout",
        "meaning": "先调整 policy 文本或验收口径，再进入下一轮 closeout。",
        "implementation_allowed": False,
    },
    {
        "option": "split_or_merge_policy_row_after_manual_review",
        "meaning": "人工认为该 policy 需要拆分、合并或重排后再继续。",
        "implementation_allowed": False,
    },
    {
        "option": "defer_until_more_manual_cases_exist",
        "meaning": "当前 5 个 source case 不足以支持收口，等待更多人工复核材料。",
        "implementation_allowed": False,
    },
    {
        "option": "close_without_followup",
        "meaning": "本轮关闭该 policy 方向，不生成工程任务。",
        "implementation_allowed": False,
    },
]

CATEGORY_CLOSEOUT_PROFILES = {
    "primary": {
        "candidate_route": "future_offline_policy_simulation_primary_evidence_preservation",
        "closeout_question": "是否确认主证据保留规则可以进入后续离线模拟设计？",
        "minimum_human_basis": "至少确认主证据已在候选层出现但未进入 final evidence，并确认替代依据边界不会过宽。",
        "recommended_closeout_option": "accept_for_future_offline_simulation_design",
    },
    "operative": {
        "candidate_route": "future_offline_policy_simulation_operative_rule_preservation",
        "closeout_question": "是否确认义务、禁止、许可或合法性基础类规范条款必须被 final evidence 优先保留？",
        "minimum_human_basis": "至少确认定义或背景条款不能替代 operative rule，并确认高风险输出需要规范条款支撑。",
        "recommended_closeout_option": "accept_for_future_offline_simulation_design",
    },
    "procedural": {
        "candidate_route": "future_offline_policy_simulation_procedural_evidence_preservation",
        "closeout_question": "是否确认程序性证据应作为独立证据类别进入后续模拟？",
        "minimum_human_basis": "至少确认告知、评估、申报、同意或申诉类依据不能被实体条款覆盖率自动替代。",
        "recommended_closeout_option": "accept_for_future_offline_simulation_design",
    },
    "liability": {
        "candidate_route": "future_offline_policy_simulation_liability_evidence_preservation",
        "closeout_question": "是否确认责任、后果、处罚、赔偿或救济依据缺失时必须进入人工复核？",
        "minimum_human_basis": "至少确认高风险或责任判断需要直接后果依据，不能仅由义务条款支撑。",
        "recommended_closeout_option": "revise_policy_language_before_closeout",
    },
    "scenario_core": {
        "candidate_route": "scenario_core_article_review_before_runtime_policy",
        "closeout_question": "是否确认该 policy 需要先与 scenario core article review 保持边界一致？",
        "minimum_human_basis": "至少确认场景核心条文缺失不能被相邻背景条款替代，且本版本不修改 scenario registry。",
        "recommended_closeout_option": "revise_policy_language_before_closeout",
    },
    "definition_only": {
        "candidate_route": "definition_only_substitution_guard_design",
        "closeout_question": "是否确认 definition-only substitution guard 是独立策略防线？",
        "minimum_human_basis": "至少确认定义条款只能辅助解释概念，不能单独支撑风险、整改、责任或后果结论。",
        "recommended_closeout_option": "accept_for_future_offline_simulation_design",
    },
    "coverage_floor": {
        "candidate_route": "final_coverage_floor_review_design",
        "closeout_question": "是否确认 coverage floor 应作为人工阻断信号，而不是自动通过条件？",
        "minimum_human_basis": "至少确认覆盖率下降需要结合主争点、场景核心和规范功能解释。",
        "recommended_closeout_option": "revise_policy_language_before_closeout",
    },
    "high_risk_manual_review": {
        "candidate_route": "high_risk_gap_manual_review_gate_design",
        "closeout_question": "是否确认高风险证据缺口必须先人工复核，不能直接 runtime adoption？",
        "minimum_human_basis": "至少确认 high-risk gap 与任一 required quality signal 同时出现时必须保留人工入口。",
        "recommended_closeout_option": "accept_for_future_offline_simulation_design",
    },
}

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
    "runtime_policy_implementation_allowed": False,
    "runtime_selection_policy_patch_allowed": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
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

NON_GOALS = [
    "不实现 final evidence selection runtime policy。",
    "不记录正式人工复核结论，不替代 manual review importer。",
    "不把 candidate route 转成工程任务、backlog、patch plan 或实现队列。",
    "不修改 rerank、prompt、anchor、hidden seed、risk supplement 或 term preservation 规则。",
    "不修改 scenario registry、fixture、eval case、schema、importer 或 dry-run 契约。",
    "不接入 RAG 主流程，不访问后端、Qdrant 或 LLM，不运行 full eval。",
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
    "reviewer_decision",
    "completed_decisions",
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


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def counter_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: item[0]))


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


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def source_meta(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": payload.get("version"),
        "scope": payload.get("scope"),
        "schema_kind": payload.get("schema_kind"),
    }


def find_key_paths(value: Any, blocked_keys: set[str], prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if key in blocked_keys:
                paths.append(child_path)
            paths.extend(find_key_paths(child, blocked_keys, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(find_key_paths(child, blocked_keys, f"{prefix}[{index}]"))
    return paths


def find_string_paths_with_markers(value: Any, prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, str):
        if any(marker in value for marker in MOJIBAKE_MARKERS):
            paths.append(prefix)
    elif isinstance(value, dict):
        for key, child in value.items():
            paths.extend(find_string_paths_with_markers(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(find_string_paths_with_markers(child, f"{prefix}[{index}]"))
    return paths


def worksheet_rows(worksheet: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(worksheet.get("review_worksheet_rows"))


def source_contract_blockers(worksheet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(worksheet.get("worksheet_gate"))
    summary = as_dict(worksheet.get("summary"))
    rows = worksheet_rows(worksheet)

    if worksheet.get("version") != EXPECTED_WORKSHEET_VERSION:
        blockers.append("worksheet_version_mismatch")
    if worksheet.get("schema_kind") != EXPECTED_WORKSHEET_SCHEMA:
        blockers.append("worksheet_schema_mismatch")
    if worksheet.get("scope") != EXPECTED_WORKSHEET_SCOPE:
        blockers.append("worksheet_scope_mismatch")
    if gate.get("status") != EXPECTED_WORKSHEET_STATUS:
        blockers.append("worksheet_gate_not_ready")
    if gate.get("human_review_worksheet_allowed") is not True:
        blockers.append("worksheet_not_allowed")
    if gate.get("implementation_allowed") is not False:
        blockers.append("worksheet_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("worksheet_code_patch_not_blocked")
    if gate.get("runtime_policy_implementation_allowed") is not False:
        blockers.append("worksheet_runtime_policy_not_blocked")
    if gate.get("runtime_selection_policy_patch_allowed") is not False:
        blockers.append("worksheet_runtime_selection_not_blocked")
    if gate.get("rerank_change_allowed") is not False:
        blockers.append("worksheet_rerank_not_blocked")
    if gate.get("captures_formal_review_outcome") is not False:
        blockers.append("worksheet_formal_outcome_not_blocked")
    if gate.get("rag_query_integration") != "disallowed":
        blockers.append("worksheet_rag_query_integration_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("worksheet_has_blockers")
    if summary.get("next_version_recommendation") != "v0.4.8.4 policy table human review closeout":
        blockers.append("worksheet_next_version_mismatch")
    if summary.get("policy_review_row_count") != EXPECTED_REVIEW_ROW_COUNT:
        blockers.append("worksheet_review_row_count_summary_drift")
    if summary.get("unique_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("worksheet_case_count_drift")
    if len(rows) != EXPECTED_REVIEW_ROW_COUNT:
        blockers.append("worksheet_review_row_count_drift")
    if [row.get("policy_category") for row in rows] != EXPECTED_POLICY_CATEGORIES:
        blockers.append("worksheet_policy_category_order_drift")
    if [row.get("source_policy_id") for row in rows] != EXPECTED_SOURCE_POLICY_IDS:
        blockers.append("worksheet_policy_id_order_drift")
    if any(row.get("worksheet_status") != "ready_for_human_review" for row in rows):
        blockers.append("worksheet_row_status_not_ready")
    if any(row.get("implementation_allowed") is not False for row in rows):
        blockers.append("worksheet_row_implementation_not_blocked")
    if any(row.get("code_patch_authorized") is not False for row in rows):
        blockers.append("worksheet_row_code_patch_not_blocked")
    if any(row.get("captures_formal_review_outcome") is not False for row in rows):
        blockers.append("worksheet_row_formal_outcome_not_blocked")

    for path in find_key_paths(worksheet, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"worksheet_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(worksheet, ADVISORY_SOURCE_KEYS):
        blockers.append(f"worksheet_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(worksheet):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def build_input_contract() -> dict[str, Any]:
    return {
        "contract_type": "saved_report_only_policy_closeout_envelope_input_contract",
        "required_reports": [
            {
                "role": "policy_human_review_worksheet",
                "path": str(DEFAULT_WORKSHEET_REPORT_PATH),
                "expected_version": EXPECTED_WORKSHEET_VERSION,
                "expected_schema_kind": EXPECTED_WORKSHEET_SCHEMA,
                "expected_scope": EXPECTED_WORKSHEET_SCOPE,
                "required_sections": [
                    "worksheet_gate",
                    "summary",
                    "review_worksheet_rows",
                    "human_review_packet",
                    "assertions",
                ],
            }
        ],
        "forbidden_inputs": [
            "live RAG output",
            "backend response",
            "Qdrant query result",
            "LLM-generated answer",
            "modified eval case",
            "modified scenario registry",
            "runtime policy state",
            "formal manual review outcome",
            "implementation authorization",
        ],
    }


def build_closeout_rows(worksheet: dict[str, Any], closeout_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(worksheet_rows(worksheet), start=1):
        category = text(source_row.get("policy_category"))
        profile = CATEGORY_CLOSEOUT_PROFILES.get(category, {})
        rows.append({
            "closeout_row_id": f"FES-CLOSEOUT-{index:03d}",
            "source_review_row_id": source_row.get("review_row_id"),
            "source_policy_id": source_row.get("source_policy_id"),
            "policy_category": category,
            "priority": source_row.get("priority"),
            "closeout_status": "pending_human_closeout" if closeout_ready else "blocked",
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "candidate_route_authorized": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "candidate_route": profile.get("candidate_route", "manual_policy_review_needed"),
            "closeout_question": profile.get("closeout_question", "是否继续推进该 policy row 的后续设计？"),
            "minimum_human_basis": profile.get("minimum_human_basis", "至少需要人工确认该 policy row 的适用边界。"),
            "recommended_closeout_option": profile.get("recommended_closeout_option", "revise_policy_language_before_closeout"),
            "available_closeout_options": [item["option"] for item in CLOSEOUT_OPTIONS],
            "source_review_questions": as_list(source_row.get("review_questions")),
            "source_acceptance_checks": as_list(source_row.get("acceptance_checks")),
            "source_discussion_options": as_list(source_row.get("discussion_options")),
            "case_count": int(source_row.get("case_count", 0)),
            "source_case_ids": as_list(source_row.get("applicable_case_ids")),
            "prohibited_now": [
                "不得把 closeout envelope 当作人工已完成结论。",
                "不得据此修改 rerank、prompt、anchor、risk supplement、scenario registry 或 eval case。",
                "不得生成实现任务、补丁清单或工程 backlog。",
                "不得接入 RAG 主流程或 runtime policy。",
            ],
            "traceability": {
                "source_review_row_id": source_row.get("review_row_id"),
                "source_policy_id": source_row.get("source_policy_id"),
                "source_report": str(DEFAULT_WORKSHEET_REPORT_PATH),
                "source_case_ids": as_list(source_row.get("applicable_case_ids")),
            },
        })
    return rows


def build_summary(status: str, closeout_rows: list[dict[str, Any]], worksheet: dict[str, Any]) -> dict[str, Any]:
    priority_counter = Counter(text(row.get("priority")) or "unknown" for row in closeout_rows)
    route_counter = Counter(text(row.get("recommended_closeout_option")) or "unknown" for row in closeout_rows)
    unique_case_ids = {
        text(case_id)
        for row in closeout_rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    return {
        "status": status,
        "allowed_use": "human_closeout_discussion_only" if status != "blocked" else "blocked",
        "source_worksheet_status": as_dict(worksheet.get("worksheet_gate")).get("status"),
        "closeout_row_count": len(closeout_rows),
        "source_review_row_count": len(worksheet_rows(worksheet)),
        "unique_case_count": len(unique_case_ids),
        "priority_summary": counter_dict(priority_counter),
        "recommended_closeout_option_summary": counter_dict(route_counter),
        "pending_human_closeout_count": sum(
            1 for row in closeout_rows if row.get("closeout_status") == "pending_human_closeout"
        ),
        "formal_human_outcome_recorded": False,
        "captures_formal_review_outcome": False,
        "next_version_recommendation": "v0.4.8.5 policy table human closeout decision draft",
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "rag_query_integration": "disallowed",
    }


def build_closeout_packet(closeout_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "policy_table_human_closeout_discussion_packet",
        "formal_review_outcome_captured": False,
        "importer_compatible": False,
        "recommended_closeout_order": [row.get("closeout_row_id") for row in closeout_rows],
        "closeout_options": CLOSEOUT_OPTIONS,
        "reviewer_instructions": [
            "逐条选择或修改 closeout option，但正式结果应写入后续 decision draft / confirmation 版本。",
            "不要在本报告中写 reviewer 结论、批准实现或工程任务。",
            "如需实现 final evidence selection policy，必须另开版本并获得明确授权。",
        ],
        "minimum_materials_to_review": [
            str(DEFAULT_WORKSHEET_REPORT_PATH),
            "tests/final_evidence_selection_policy_table_draft_report.json",
            "tests/final_evidence_selection_policy_simulator_spec_report.json",
            "tests/final_evidence_selection_audit_report.json",
        ],
    }


def output_key_violations(report: dict[str, Any]) -> list[str]:
    violations = []
    for node in walk_dicts(report):
        for key in FORBIDDEN_OUTPUT_KEYS & set(node.keys()):
            violations.append(key)
    return sorted_unique(violations)


def readability_violations(report: dict[str, Any]) -> list[str]:
    return sorted_unique(find_string_paths_with_markers(report))


def build_assertions(
    source_blockers: list[str],
    closeout_rows: list[dict[str, Any]],
    worksheet: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_review_ids = {text(row.get("review_row_id")) for row in worksheet_rows(worksheet)}
    closeout_review_ids = {text(row.get("source_review_row_id")) for row in closeout_rows}
    source_policy_ids = {text(row.get("source_policy_id")) for row in worksheet_rows(worksheet)}
    closeout_policy_ids = {text(row.get("source_policy_id")) for row in closeout_rows}
    unique_case_ids = {
        text(case_id)
        for row in closeout_rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    readability_blockers = [
        blocker for blocker in source_blockers if blocker == "blocked_for_human_readability"
    ]
    return [
        {
            "name": "source_worksheet_is_ready_for_closeout_envelope",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "closeout_covers_all_review_rows",
            "status": "passed"
            if source_review_ids and source_review_ids == closeout_review_ids
            else "failed",
            "source_review_row_count": len(source_review_ids),
            "closeout_review_row_count": len(closeout_review_ids),
            "missing_review_row_ids": sorted(source_review_ids - closeout_review_ids),
        },
        {
            "name": "closeout_preserves_policy_traceability",
            "status": "passed"
            if source_policy_ids and source_policy_ids == closeout_policy_ids
            else "failed",
            "source_policy_count": len(source_policy_ids),
            "closeout_policy_count": len(closeout_policy_ids),
            "missing_policy_ids": sorted(source_policy_ids - closeout_policy_ids),
        },
        {
            "name": "closeout_has_eight_rows",
            "status": "passed" if len(closeout_rows) == EXPECTED_REVIEW_ROW_COUNT else "failed",
            "closeout_row_count": len(closeout_rows),
            "expected": EXPECTED_REVIEW_ROW_COUNT,
        },
        {
            "name": "closeout_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) == EXPECTED_CASE_COUNT else "failed",
            "unique_case_count": len(unique_case_ids),
            "expected": EXPECTED_CASE_COUNT,
        },
        {
            "name": "closeout_is_not_formal_outcome_or_implementation",
            "status": "passed"
            if all(
                row.get("formal_human_outcome_recorded") is False
                and row.get("candidate_route_authorized") is False
                and row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("captures_formal_review_outcome") is False
                for row in closeout_rows
            )
            else "failed",
        },
        {
            "name": "implementation_is_not_authorized",
            "status": "passed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
        },
        {
            "name": "forbidden_output_keys_absent",
            "status": "passed" if not output_forbidden_keys else "failed",
            "forbidden_keys": output_forbidden_keys,
        },
        {
            "name": "text_readability_gate",
            "status": "passed" if not readability_errors and not readability_blockers else "failed",
            "source_readability_blockers": readability_blockers,
            "mojibake_like_paths": readability_errors,
        },
    ]


def build_report(
    worksheet_report_path: Path = DEFAULT_WORKSHEET_REPORT_PATH,
) -> dict[str, Any]:
    worksheet = load_json(worksheet_report_path)
    source_blockers = source_contract_blockers(worksheet)
    closeout_ready = not source_blockers
    closeout_rows = build_closeout_rows(worksheet, closeout_ready)
    status = "pending_policy_table_human_closeout" if closeout_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_closeout_envelope",
        "scope": "offline final evidence selection policy closeout envelope only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_human_review_worksheet": source_meta(worksheet_report_path, worksheet),
        },
        "guardrails": CLOSEOUT_GUARDRAILS,
        "non_goals": NON_GOALS,
        "closeout_gate": {
            "status": status,
            "allowed_use": "human_closeout_discussion_only" if closeout_ready else "blocked",
            "saved_report_only": True,
            "closeout_envelope_allowed": closeout_ready,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "captures_formal_review_outcome": False,
            "formal_human_outcome_recorded": False,
            "rag_query_integration": "disallowed",
            "blockers": source_blockers,
        },
        "summary": build_summary(status, closeout_rows, worksheet),
        "input_contract": build_input_contract(),
        "closeout_rows": closeout_rows,
        "closeout_packet": build_closeout_packet(closeout_rows),
        "next_version_handoff": {
            "recommended_next_version": "v0.4.8.5",
            "recommended_artifact": "policy table human closeout decision draft",
            "handoff_status": "closeout_envelope_ready_for_human_discussion" if closeout_ready else "blocked",
            "allowed_next_step": "draft_human_closeout_decision_after_user_review" if closeout_ready else "resolve_source_contract_blockers",
            "runtime_implementation_allowed": False,
            "requires_explicit_future_implementation_approval": True,
        },
        "excluded_scope": {
            "formal_manual_review_outcome": "not_captured",
            "runtime_policy_patch": "disallowed",
            "rerank_or_prompt_change": "disallowed",
            "hidden_seed_anchor_eval_fixture_mutation": "disallowed",
            "backend_qdrant_llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_report": str(worksheet_report_path),
            "source_worksheet_version": worksheet.get("version"),
            "source_review_row_ids": [row.get("review_row_id") for row in worksheet_rows(worksheet)],
            "closeout_row_ids": [row.get("closeout_row_id") for row in closeout_rows],
            "source_policy_ids": [row.get("source_policy_id") for row in closeout_rows],
            "source_case_ids": sorted_unique([
                text(case_id)
                for row in closeout_rows
                for case_id in as_list(row.get("source_case_ids"))
            ]),
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        closeout_rows,
        worksheet,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["closeout_gate"]["status"] = "blocked"
        report["closeout_gate"]["allowed_use"] = "blocked"
        report["closeout_gate"]["closeout_envelope_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["closeout_gate"]["blockers"] = sorted_unique(report["closeout_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("closeout_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.4 Final Evidence Selection Policy Closeout Envelope",
        "",
        "本文件是最终证据选择 policy table 的人工收口外壳。它只把 v0.4.8.3 worksheet 转成待人工讨论的 closeout rows、候选收口路径和最低人工依据；它不记录正式人工结论，也不批准 runtime policy、rerank、prompt、eval case 或 RAG 主流程修改。",
        "",
        "## Overview",
        "",
        f"- Closeout status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Closeout rows: {summary.get('closeout_row_count')}",
        f"- Unique cases: {summary.get('unique_case_count')}",
        f"- Pending closeout rows: {summary.get('pending_human_closeout_count')}",
        f"- Next version recommendation: `{summary.get('next_version_recommendation')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Formal human outcome recorded: {gate.get('formal_human_outcome_recorded')}",
        f"- Captures formal review outcome: {gate.get('captures_formal_review_outcome')}",
        "",
        "## Input Contract",
        "",
    ]
    for item in as_list(as_dict(report.get("input_contract")).get("required_reports")):
        lines.append(
            f"- `{item.get('role')}`: `{item.get('path')}` "
            f"(version `{item.get('expected_version')}`)"
        )

    lines.extend([
        "",
        "## Closeout Rows",
        "",
        "| Row | Policy | Category | Status | Candidate route | Recommended option |",
        "|---|---|---|---|---|---|",
    ])
    for row in as_list(report.get("closeout_rows")):
        lines.append(
            f"| `{row.get('closeout_row_id')}` | `{row.get('source_policy_id')}` | "
            f"`{row.get('policy_category')}` | `{row.get('closeout_status')}` | "
            f"`{row.get('candidate_route')}` | `{row.get('recommended_closeout_option')}` |"
        )

    lines.extend([
        "",
        "## Closeout Questions",
        "",
    ])
    for row in as_list(report.get("closeout_rows")):
        lines.append(f"### {row.get('source_policy_id')} - {row.get('policy_category')}")
        lines.append(f"- Closeout question: {row.get('closeout_question')}")
        lines.append(f"- Minimum human basis: {row.get('minimum_human_basis')}")
        lines.append("")

    lines.extend([
        "## Closeout Options",
        "",
    ])
    for option in as_list(as_dict(report.get("closeout_packet")).get("closeout_options")):
        lines.append(f"- `{option.get('option')}`: {option.get('meaning')}")

    lines.extend([
        "",
        "## Boundaries",
        "",
        "- 本 closeout envelope 只帮助人工收口讨论，不记录 formal review outcome。",
        "- `implementation_allowed=false` 和 `code_patch_authorized=false` 必须保持不变。",
        "- 不实现 runtime policy，不修改 final evidence selection runtime，不修改 rerank，不修改 prompt，不改 eval case。",
        "- 不新增 anchor，不修 hidden seed，不改 risk supplement / term preservation / scenario registry / fixture / schema / importer / dry-run 契约。",
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
    parser = argparse.ArgumentParser(description="Build final evidence selection policy closeout envelope.")
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
        "Final evidence selection policy closeout envelope built: "
        f"{summary['status']}, "
        f"{summary['closeout_row_count']} rows, "
        f"{summary['unique_case_count']} cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
