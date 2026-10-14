"""Build the v0.4.8.3 final-evidence policy human-review worksheet.

This tool reads only the saved v0.4.8.2 policy table draft report and turns its
eight draft policy rows into a human-review worksheet. It does not implement a
runtime policy, change rerank, alter prompts, mutate eval cases, call RAG,
contact a backend, contact Qdrant, or call an LLM.
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


VERSION = "0.4.8.3"

DEFAULT_TABLE_DRAFT_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_table_draft_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_human_review_worksheet_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md")

EXPECTED_TABLE_DRAFT_VERSION = "0.4.8.2"
EXPECTED_TABLE_DRAFT_SCHEMA = "final_evidence_selection_policy_table_draft"
EXPECTED_TABLE_DRAFT_SCOPE = "offline final evidence selection policy table draft only"
EXPECTED_TABLE_DRAFT_STATUS = "ready_for_manual_review_policy_table_draft"
EXPECTED_TABLE_ROW_COUNT = 8
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

WORKSHEET_GUARDRAILS = {
    "worksheet_only": True,
    "saved_report_only": True,
    "human_review_aid_only": True,
    "not_formal_review_outcome": True,
    "not_policy_implementation": True,
    "not_runtime_selection_patch": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_policy_implementation_allowed": False,
    "runtime_selection_policy_patch_allowed": False,
    "captures_formal_review_outcome": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
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

CATEGORY_REVIEW_PROFILES = {
    "primary": {
        "review_goal": "确认主证据保留规则是否足以防止核心法律依据在 final evidence 阶段流失。",
        "review_questions": [
            "该 policy 是否准确覆盖 primary evidence lost 的真实问题？",
            "可接受替代依据是否必须同时满足同法域、同争点和同等规范功能？",
            "主证据缺失时是否必须触发人工复核，而不是自动通过？",
        ],
        "acceptance_checks": [
            "触发条件能被 saved report 中的 case signal 复核。",
            "替代条件不会放宽到普通背景材料。",
            "高风险结论时仍保留人工复核入口。",
        ],
    },
    "operative": {
        "review_goal": "确认义务、禁止、许可、合法性基础等规范条款不会被定义或背景条款替代。",
        "review_questions": [
            "该 policy 是否能区分 operative rule 与说明性材料？",
            "当答案输出风险结论或整改动作时，是否要求 final evidence 保留对应规范条款？",
            "缺少 operative rule 时是否应该阻断 runtime adoption？",
        ],
        "acceptance_checks": [
            "至少能解释为什么义务或行为规范应被保留。",
            "不会把定义条款当作充分规范依据。",
            "manual review trigger 与高风险输出一致。",
        ],
    },
    "procedural": {
        "review_goal": "确认告知、评估、申报、同意、申诉等程序性证据被单独审议。",
        "review_questions": [
            "该 policy 是否把程序性要求作为独立证据类型？",
            "答案提出流程整改时，是否有对应程序依据？",
            "程序条款缺失是否会被实体条款覆盖率掩盖？",
        ],
        "acceptance_checks": [
            "程序证据不会被实体规则自动替代。",
            "审议项能覆盖告知、评估、申报、同意或申诉类问题。",
            "缺失时保留人工复核信号。",
        ],
    },
    "liability": {
        "review_goal": "确认高风险、责任、处罚、赔偿或整改后果类结论有直接后果依据。",
        "review_questions": [
            "该 policy 是否应在高风险结论中强制检查 liability evidence？",
            "责任条款缺失时，答案置信度或人工复核是否应受影响？",
            "义务条款能否替代责任后果条款，边界是什么？",
        ],
        "acceptance_checks": [
            "责任或后果判断不能仅由义务条款支撑。",
            "高风险输出必须进入人工复核清单。",
            "可接受替代必须覆盖同类责任、后果或救济路径。",
        ],
    },
    "scenario_core": {
        "review_goal": "确认场景核心条文缺失时，不会被相邻场景或背景证据误判为充分覆盖。",
        "review_questions": [
            "该 policy 是否能说明 scenario core evidence 的保留边界？",
            "场景核心条文缺失时，是否允许同场景同争点替代？",
            "是否需要把该问题留给后续 scenario core article review？",
        ],
        "acceptance_checks": [
            "不会把相邻背景条款当作场景核心条款。",
            "缺失解释必须能从 saved report 复核。",
            "不直接修改 scenario registry。",
        ],
    },
    "definition_only": {
        "review_goal": "确认定义条款只能辅助解释概念，不能替代义务、程序、责任或后果依据。",
        "review_questions": [
            "该 policy 是否清楚阻断 definition-only substitution？",
            "定义条款何时可以作为补充证据，而不是主证据？",
            "复杂自动化决策或数据出境场景是否需要特别关注定义条款替代问题？",
        ],
        "acceptance_checks": [
            "定义条款不得单独支撑风险结论。",
            "规范性条款缺失时必须保留人工复核信号。",
            "不会把定义条款提升为 runtime policy。",
        ],
    },
    "coverage_floor": {
        "review_goal": "确认 final evidence coverage 下降时，需要人工解释而不是自动通过。",
        "review_questions": [
            "coverage floor 是否应该作为阻断信号，而不是普通提示？",
            "覆盖率下降是否能区分主争点和次争点？",
            "哪些 case 可以证明 coverage floor 不应单独决定通过？",
        ],
        "acceptance_checks": [
            "低覆盖率触发人工审议。",
            "覆盖率解释必须结合主争点、场景核心和功能类型。",
            "不直接改 rerank 或 final selection runtime。",
        ],
    },
    "high_risk_manual_review": {
        "review_goal": "确认高风险缺口必须先人工复核，不能被离线 policy 草案直接转成实现任务。",
        "review_questions": [
            "该 policy 是否足以阻断高风险证据缺口的自动采纳？",
            "人工复核需要看到哪些最小依据？",
            "后续版本是否应先做 closeout，而不是直接实现？",
        ],
        "acceptance_checks": [
            "高风险缺口必须保留 manual review required。",
            "worksheet 不产生 completed manual decision。",
            "后续实现仍需要单独版本与明确授权。",
        ],
    },
}


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
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def source_contract_blockers(table_draft: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(table_draft.get("policy_table_gate"))
    summary = as_dict(table_draft.get("summary"))
    manual_gate = as_dict(table_draft.get("manual_review_gate"))
    rows = as_list(table_draft.get("policy_table_rows"))

    if table_draft.get("version") != EXPECTED_TABLE_DRAFT_VERSION:
        blockers.append("table_draft_version_mismatch")
    if table_draft.get("schema_kind") != EXPECTED_TABLE_DRAFT_SCHEMA:
        blockers.append("table_draft_schema_mismatch")
    if table_draft.get("scope") != EXPECTED_TABLE_DRAFT_SCOPE:
        blockers.append("table_draft_scope_mismatch")
    if gate.get("status") != EXPECTED_TABLE_DRAFT_STATUS:
        blockers.append("table_draft_gate_not_ready")
    if gate.get("policy_table_draft_allowed") is not True:
        blockers.append("table_draft_not_allowed")
    if gate.get("implementation_allowed") is not False:
        blockers.append("table_draft_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("table_draft_code_patch_not_blocked")
    if gate.get("runtime_policy_implementation_allowed") is not False:
        blockers.append("table_draft_runtime_policy_not_blocked")
    if gate.get("runtime_selection_policy_patch_allowed") is not False:
        blockers.append("table_draft_runtime_selection_not_blocked")
    if gate.get("rerank_change_allowed") is not False:
        blockers.append("table_draft_rerank_not_blocked")
    if gate.get("rag_query_integration") != "disallowed":
        blockers.append("table_draft_rag_query_integration_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("table_draft_has_blockers")
    if summary.get("next_version_recommendation") != "v0.4.8.3 policy table human review worksheet":
        blockers.append("table_draft_next_version_mismatch")
    if summary.get("confirmed_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("confirmed_case_count_drift")
    if len(rows) != EXPECTED_TABLE_ROW_COUNT:
        blockers.append("policy_table_row_count_drift")
    if [row.get("policy_category") for row in rows] != EXPECTED_POLICY_CATEGORIES:
        blockers.append("policy_category_order_drift")
    if any(row.get("policy_status") != "draft_for_manual_review" for row in rows):
        blockers.append("policy_row_status_not_draft")
    if any(row.get("runtime_adoption_status") != "not_allowed" for row in rows):
        blockers.append("policy_row_runtime_adoption_not_blocked")
    if any(row.get("implementation_allowed") is not False for row in rows):
        blockers.append("policy_row_implementation_not_blocked")
    if manual_gate.get("status") != "manual_review_required_before_runtime_policy":
        blockers.append("manual_review_gate_not_preserved")
    if manual_gate.get("runtime_policy_adoption_allowed_without_review") is not False:
        blockers.append("manual_review_gate_runtime_adoption_not_blocked")

    for path in find_key_paths(table_draft, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"table_draft_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(table_draft, ADVISORY_SOURCE_KEYS):
        blockers.append(f"table_draft_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(table_draft):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def build_input_contract() -> dict[str, Any]:
    return {
        "contract_type": "saved_report_only_policy_human_review_worksheet_input_contract",
        "required_reports": [
            {
                "role": "policy_table_draft",
                "path": str(DEFAULT_TABLE_DRAFT_REPORT_PATH),
                "expected_version": EXPECTED_TABLE_DRAFT_VERSION,
                "expected_schema_kind": EXPECTED_TABLE_DRAFT_SCHEMA,
                "expected_scope": EXPECTED_TABLE_DRAFT_SCOPE,
                "required_sections": [
                    "policy_table_gate",
                    "summary",
                    "policy_table_rows",
                    "manual_review_gate",
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
        ],
    }


def build_review_rows(table_draft: dict[str, Any], worksheet_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(as_list(table_draft.get("policy_table_rows")), start=1):
        category = text(source_row.get("policy_category"))
        profile = CATEGORY_REVIEW_PROFILES.get(category, {})
        applicable_case_ids = as_list(source_row.get("applicable_case_ids"))
        rows.append({
            "review_row_id": f"FES-WORKSHEET-REVIEW-{index:03d}",
            "source_policy_id": source_row.get("policy_id"),
            "policy_category": category,
            "priority": source_row.get("priority"),
            "worksheet_status": "ready_for_human_review" if worksheet_ready else "blocked",
            "human_review_required": True,
            "captures_formal_review_outcome": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "required_quality_signal": source_row.get("required_quality_signal"),
            "source_signals": as_list(source_row.get("source_signals")),
            "case_count": len(applicable_case_ids),
            "applicable_case_ids": applicable_case_ids,
            "review_goal": profile.get("review_goal", "确认该 policy row 是否可以继续进入人工策略审议。"),
            "review_questions": profile.get("review_questions", []),
            "acceptance_checks": profile.get("acceptance_checks", []),
            "source_policy_summary": {
                "trigger_condition": source_row.get("trigger_condition"),
                "preservation_requirement": source_row.get("preservation_requirement"),
                "acceptable_substitution_condition": source_row.get("acceptable_substitution_condition"),
                "must_emit_manual_review_when": source_row.get("must_emit_manual_review_when"),
                "coverage_floor_rule": source_row.get("coverage_floor_rule"),
                "definition_only_guard": source_row.get("definition_only_guard"),
            },
            "discussion_options": [
                "accept_for_future_offline_simulation_design",
                "revise_policy_language_before_closeout",
                "split_or_merge_policy_row_after_manual_review",
                "defer_until_more_manual_cases_exist",
            ],
            "prohibited_now": [
                "不得把 worksheet 当作 runtime policy。",
                "不得据此修改 rerank、prompt、anchor、risk supplement、scenario registry 或 eval case。",
                "不得记录正式人工结论或导入 manual review importer。",
                "不得生成实现任务、补丁清单或工程 backlog。",
            ],
            "traceability": {
                "source_policy_id": source_row.get("policy_id"),
                "source_report": str(DEFAULT_TABLE_DRAFT_REPORT_PATH),
                "source_case_ids": applicable_case_ids,
            },
        })
    return rows


def build_summary(status: str, review_rows: list[dict[str, Any]], table_draft: dict[str, Any]) -> dict[str, Any]:
    priority_counter = Counter(text(row.get("priority")) or "unknown" for row in review_rows)
    category_counter = Counter(text(row.get("policy_category")) or "unknown" for row in review_rows)
    signal_counter = Counter(text(row.get("required_quality_signal")) or "unknown" for row in review_rows)
    unique_case_ids = {
        text(case_id)
        for row in review_rows
        for case_id in as_list(row.get("applicable_case_ids"))
    }
    return {
        "status": status,
        "allowed_use": "human_policy_review_discussion_only" if status != "blocked" else "blocked",
        "source_table_draft_status": as_dict(table_draft.get("policy_table_gate")).get("status"),
        "policy_review_row_count": len(review_rows),
        "source_policy_table_row_count": len(as_list(table_draft.get("policy_table_rows"))),
        "unique_case_count": len(unique_case_ids),
        "priority_summary": counter_dict(priority_counter),
        "policy_category_summary": counter_dict(category_counter),
        "required_quality_signal_summary": counter_dict(signal_counter),
        "review_rows_requiring_human_review_count": sum(
            1 for row in review_rows if row.get("human_review_required") is True
        ),
        "next_version_recommendation": "v0.4.8.4 policy table human review closeout",
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "captures_formal_review_outcome": False,
        "rag_query_integration": "disallowed",
    }


def build_human_review_packet(review_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "policy_table_human_review_discussion_packet",
        "formal_review_outcome_captured": False,
        "importer_compatible": False,
        "recommended_review_order": [row.get("source_policy_id") for row in review_rows],
        "reviewer_instructions": [
            "逐条确认 policy row 是否表达了正确的证据保留要求。",
            "只记录讨论结论到后续 closeout 版本，不在本报告中写正式结论。",
            "如需实现，必须另开版本并获得明确授权。",
        ],
        "minimum_materials_to_review": [
            str(DEFAULT_TABLE_DRAFT_REPORT_PATH),
            "tests/final_evidence_selection_policy_simulator_spec_report.json",
            "tests/final_evidence_selection_audit_report.json",
        ],
    }


def build_assertions(
    source_blockers: list[str],
    review_rows: list[dict[str, Any]],
    table_draft: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_policy_ids = {
        text(row.get("policy_id"))
        for row in as_list(table_draft.get("policy_table_rows"))
    }
    worksheet_policy_ids = {
        text(row.get("source_policy_id"))
        for row in review_rows
    }
    unique_case_ids = {
        text(case_id)
        for row in review_rows
        for case_id in as_list(row.get("applicable_case_ids"))
    }
    readability_blockers = [
        blocker for blocker in source_blockers if blocker == "blocked_for_human_readability"
    ]
    return [
        {
            "name": "source_table_draft_is_ready_for_human_review_worksheet",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "worksheet_covers_all_policy_rows",
            "status": "passed"
            if source_policy_ids and source_policy_ids == worksheet_policy_ids
            else "failed",
            "source_policy_count": len(source_policy_ids),
            "worksheet_policy_count": len(worksheet_policy_ids),
            "missing_policy_ids": sorted(source_policy_ids - worksheet_policy_ids),
        },
        {
            "name": "worksheet_has_eight_review_rows",
            "status": "passed" if len(review_rows) == EXPECTED_TABLE_ROW_COUNT else "failed",
            "review_row_count": len(review_rows),
            "expected": EXPECTED_TABLE_ROW_COUNT,
        },
        {
            "name": "worksheet_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) == EXPECTED_CASE_COUNT else "failed",
            "unique_case_count": len(unique_case_ids),
            "expected": EXPECTED_CASE_COUNT,
        },
        {
            "name": "worksheet_is_review_only",
            "status": "passed"
            if all(
                row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("captures_formal_review_outcome") is False
                and row.get("runtime_adoption_status") == "not_allowed"
                for row in review_rows
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


def output_key_violations(report: dict[str, Any]) -> list[str]:
    violations = []
    for node in walk_dicts(report):
        for key in FORBIDDEN_OUTPUT_KEYS & set(node.keys()):
            violations.append(key)
    return sorted_unique(violations)


def readability_violations(report: dict[str, Any]) -> list[str]:
    return sorted_unique(find_string_paths_with_markers(report))


def build_report(
    table_draft_report_path: Path = DEFAULT_TABLE_DRAFT_REPORT_PATH,
) -> dict[str, Any]:
    table_draft = load_json(table_draft_report_path)
    source_blockers = source_contract_blockers(table_draft)
    worksheet_ready = not source_blockers
    review_rows = build_review_rows(table_draft, worksheet_ready)
    status = "ready_for_policy_table_human_review_worksheet" if worksheet_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_human_review_worksheet",
        "scope": "offline final evidence selection policy human review worksheet only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_table_draft": source_meta(table_draft_report_path, table_draft),
        },
        "guardrails": WORKSHEET_GUARDRAILS,
        "non_goals": NON_GOALS,
        "worksheet_gate": {
            "status": status,
            "allowed_use": "human_policy_review_discussion_only" if worksheet_ready else "blocked",
            "saved_report_only": True,
            "human_review_worksheet_allowed": worksheet_ready,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "captures_formal_review_outcome": False,
            "rag_query_integration": "disallowed",
            "blockers": source_blockers,
        },
        "summary": build_summary(status, review_rows, table_draft),
        "input_contract": build_input_contract(),
        "review_worksheet_rows": review_rows,
        "human_review_packet": build_human_review_packet(review_rows),
        "next_version_handoff": {
            "recommended_next_version": "v0.4.8.4",
            "recommended_artifact": "policy table human review closeout",
            "handoff_status": "worksheet_ready_for_human_review" if worksheet_ready else "blocked",
            "allowed_next_step": "record_human_review_closeout_after_user_review" if worksheet_ready else "resolve_source_contract_blockers",
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
            "source_report": str(table_draft_report_path),
            "source_table_draft_version": table_draft.get("version"),
            "source_policy_ids": [row.get("policy_id") for row in as_list(table_draft.get("policy_table_rows"))],
            "worksheet_review_row_ids": [row.get("review_row_id") for row in review_rows],
            "source_case_ids": sorted_unique([
                text(case_id)
                for row in review_rows
                for case_id in as_list(row.get("applicable_case_ids"))
            ]),
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        review_rows,
        table_draft,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["worksheet_gate"]["status"] = "blocked"
        report["worksheet_gate"]["allowed_use"] = "blocked"
        report["worksheet_gate"]["human_review_worksheet_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["worksheet_gate"]["blockers"] = sorted_unique(report["worksheet_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("worksheet_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.3 Final Evidence Selection Policy Human Review Worksheet",
        "",
        "本文件是最终证据选择 policy table 的人工复核 worksheet。它只把 v0.4.8.2 的 8 条 policy row 转成审议问题、验收检查点和边界提示；它不记录正式人工结论，也不批准 runtime policy、rerank、prompt、eval case 或 RAG 主流程修改。",
        "",
        "## Overview",
        "",
        f"- Worksheet status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Review rows: {summary.get('policy_review_row_count')}",
        f"- Unique cases: {summary.get('unique_case_count')}",
        f"- Next version recommendation: `{summary.get('next_version_recommendation')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Runtime policy implementation allowed: {gate.get('runtime_policy_implementation_allowed')}",
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
        "## Review Worksheet Rows",
        "",
        "| Row | Policy | Category | Priority | Cases | Review goal |",
        "|---|---|---|---|---:|---|",
    ])
    for row in as_list(report.get("review_worksheet_rows")):
        lines.append(
            f"| `{row.get('review_row_id')}` | `{row.get('source_policy_id')}` | "
            f"`{row.get('policy_category')}` | {row.get('priority')} | "
            f"{row.get('case_count')} | {row.get('review_goal')} |"
        )

    lines.extend([
        "",
        "## Review Questions",
        "",
    ])
    for row in as_list(report.get("review_worksheet_rows")):
        lines.append(f"### {row.get('source_policy_id')} - {row.get('policy_category')}")
        for question in as_list(row.get("review_questions")):
            lines.append(f"- {question}")
        lines.append("")

    lines.extend([
        "## Acceptance Checks",
        "",
    ])
    for row in as_list(report.get("review_worksheet_rows")):
        checks = "; ".join(as_list(row.get("acceptance_checks")))
        lines.append(f"- `{row.get('source_policy_id')}`: {checks}")

    lines.extend([
        "",
        "## Boundaries",
        "",
        "- 本 worksheet 只帮助人工审议 policy table，不记录 formal review outcome。",
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
    parser = argparse.ArgumentParser(description="Build final evidence selection policy human review worksheet.")
    parser.add_argument("--table-draft-report", type=Path, default=DEFAULT_TABLE_DRAFT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.table_draft_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy human review worksheet built: "
        f"{summary['status']}, "
        f"{summary['policy_review_row_count']} rows, "
        f"{summary['unique_case_count']} cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
