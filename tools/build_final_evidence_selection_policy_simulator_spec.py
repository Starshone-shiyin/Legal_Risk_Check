"""Build the v0.4.8.1 final-evidence selection policy simulator spec.

This is a saved-report-only contract builder. It defines how a future offline
policy simulator should read existing governance reports and emit grounding
quality signals, but it does not implement a runtime policy, change rerank,
alter prompts, mutate eval cases, call RAG, contact a backend, contact Qdrant
or call an LLM.
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


VERSION = "0.4.8.1"

DEFAULT_INTAKE_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_intake_report.json")
DEFAULT_AUDIT_REPORT_PATH = legacy_report_path("final_evidence_selection_audit_report.json")
DEFAULT_CONFIRMATION_REPORT_PATH = legacy_report_path("ready_action_human_closeout_confirmation_record_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_simulator_spec_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_simulator_spec_v0.4.8.1.md")

EXPECTED_INTAKE_VERSION = "0.4.8.0"
EXPECTED_INTAKE_SCHEMA = "final_evidence_selection_policy_design_intake"
EXPECTED_AUDIT_VERSION = "0.4.7.4.5"
EXPECTED_AUDIT_SCOPE = "offline final evidence selection audit"
EXPECTED_CONFIRMATION_VERSION = "0.4.7.9.6"
EXPECTED_CONFIRMATION_SCHEMA = "ready_action_human_closeout_confirmation_record"
EXPECTED_CONFIRMATION_STATUS = "confirmed_for_future_design_planning"
EXPECTED_TRACK_ACTION = "final_evidence_selection_policy_review"
EXPECTED_CASE_COUNT = 5
EXPECTED_PRESERVATION_ITEM_COUNT = 6
EXPECTED_POLICY_QUESTION_COUNT = 6

SPEC_GUARDRAILS = {
    "spec_only": True,
    "saved_reports_only": True,
    "not_simulator_implementation": True,
    "not_policy_implementation": True,
    "not_runtime_selection_patch": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_policy_implementation_allowed": False,
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
    "不实现 final evidence selection runtime policy。",
    "不修改 rerank、prompt、anchor、hidden seed、risk supplement 或 term preservation 规则。",
    "不修改 scenario registry、fixture、eval case、schema、importer 或 dry-run 契约。",
    "不接入 RAG 主流程，不访问后端、Qdrant 或 LLM，不运行 full eval。",
    "不把 spec row 转成工程修复任务、backlog 或 patch plan。",
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

POLICY_CANDIDATE_CATEGORIES = [
    {
        "category_id": "primary",
        "display_name": "主证据保留",
        "purpose": "核心法条已经进入候选层时，模拟器必须检查它是否进入 final evidence_chain，或是否存在可解释替代。",
        "source_signals": ["primary_evidence_lost", "rerank_input_to_final_loss"],
        "required_output_signal": "primary_evidence_should_be_preserved",
        "allowed_stage": "offline_spec_only",
    },
    {
        "category_id": "operative",
        "display_name": "义务或行为规范保留",
        "purpose": "义务、禁止、许可、合法性基础等规范性条款不能被背景性材料替代。",
        "source_signals": ["operative_evidence_lost", "operative_rule"],
        "required_output_signal": "operative_rule_should_be_preserved",
        "allowed_stage": "offline_spec_only",
    },
    {
        "category_id": "procedural",
        "display_name": "程序性证据保留",
        "purpose": "告知、评估、申报、同意、程序步骤等证据必须被单独识别，不能被结论性回答概括掉。",
        "source_signals": ["procedural"],
        "required_output_signal": "procedural_evidence_should_be_preserved",
        "allowed_stage": "offline_spec_only",
    },
    {
        "category_id": "liability",
        "display_name": "责任或后果证据保留",
        "purpose": "答案涉及处罚、赔偿、整改责任或高风险结论时，必须检查责任/后果条款是否被保留。",
        "source_signals": ["liability_evidence_lost", "liability"],
        "required_output_signal": "liability_evidence_should_be_preserved",
        "allowed_stage": "offline_spec_only",
    },
    {
        "category_id": "scenario_core",
        "display_name": "场景核心条文保留或解释",
        "purpose": "场景核心条文丢失时，模拟器必须输出保留要求或解释性人工复核信号。",
        "source_signals": ["scenario_core_lost"],
        "required_output_signal": "scenario_core_should_be_preserved_or_explained",
        "allowed_stage": "offline_spec_only",
    },
    {
        "category_id": "definition_only",
        "display_name": "定义条款替代防线",
        "purpose": "定义条款只能辅助解释，不能替代义务、责任、程序或后果条款支撑最终结论。",
        "source_signals": ["definition"],
        "required_output_signal": "definition_only_must_not_substitute_normative_evidence",
        "allowed_stage": "offline_spec_only",
    },
]

FAILURE_SIGNAL_CATALOG = [
    {
        "signal_id": "primary_evidence_should_be_preserved",
        "severity": "P0",
        "trigger": "primary evidence is present before final selection but missing from final evidence.",
        "review_reason": "主证据已进入前序候选层但没有进入最终证据链，可能导致核心法律依据缺失。",
    },
    {
        "signal_id": "operative_rule_should_be_preserved",
        "severity": "P0",
        "trigger": "lost evidence includes operative_rule or operative evidence loss.",
        "review_reason": "义务、禁止、合法性基础等规范性条款丢失，答案可能只剩结论而缺少规则支撑。",
    },
    {
        "signal_id": "procedural_evidence_should_be_preserved",
        "severity": "P0",
        "trigger": "lost evidence includes procedural functional type.",
        "review_reason": "程序性要求丢失，可能影响整改动作、合规步骤和审查路径。",
    },
    {
        "signal_id": "liability_evidence_should_be_preserved",
        "severity": "P0",
        "trigger": "lost evidence includes liability or consequence support.",
        "review_reason": "责任或后果条款丢失，高风险结论可能缺少直接法律后果支撑。",
    },
    {
        "signal_id": "scenario_core_should_be_preserved_or_explained",
        "severity": "P1",
        "trigger": "scenario core evidence is missing from final evidence.",
        "review_reason": "场景核心条文未进入最终证据链，需要确认是选择策略流失还是场景范围需要复核。",
    },
    {
        "signal_id": "definition_only_must_not_substitute_normative_evidence",
        "severity": "P1",
        "trigger": "definition-only evidence appears where normative support is still missing.",
        "review_reason": "定义条款不能替代义务、程序、责任或后果条款，需要人工确认最终证据是否支撑结论。",
    },
    {
        "signal_id": "final_coverage_floor_review_needed",
        "severity": "P1",
        "trigger": "final evidence coverage falls below the saved audit threshold.",
        "review_reason": "最终证据覆盖率过低，需要进入人工复核或阻断后续策略草案。",
    },
    {
        "signal_id": "manual_review_required_for_high_risk_gap",
        "severity": "P0",
        "trigger": "high-risk case has any preservation or coverage failure signal.",
        "review_reason": "高风险结论下存在证据保留缺口，策略草案前必须人工复核。",
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


def audit_case_map(audit_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in as_list(audit_report.get("cases")):
        row = as_dict(item)
        case_id = text(row.get("case_id"))
        if case_id:
            result[case_id] = row
    return result


def source_contract_blockers(
    intake: dict[str, Any],
    audit_report: dict[str, Any],
    confirmation: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    intake_gate = as_dict(intake.get("intake_gate"))
    intake_summary = as_dict(intake.get("summary"))
    simulator_plan = as_dict(intake.get("policy_simulator_plan"))
    audit_summary = as_dict(audit_report.get("summary"))
    confirmation_gate = as_dict(confirmation.get("confirmation_gate"))
    confirmation_row = confirmation_final_row(confirmation)

    if intake.get("version") != EXPECTED_INTAKE_VERSION:
        blockers.append("intake_version_mismatch")
    if intake.get("schema_kind") != EXPECTED_INTAKE_SCHEMA:
        blockers.append("intake_schema_mismatch")
    if intake_gate.get("status") != "ready_for_policy_design_intake":
        blockers.append("intake_gate_not_ready")
    if as_list(intake_gate.get("blockers")):
        blockers.append("intake_gate_has_blockers")
    if intake_summary.get("confirmed_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("intake_confirmed_case_count_drift")
    if intake_summary.get("preservation_item_count") != EXPECTED_PRESERVATION_ITEM_COUNT:
        blockers.append("intake_preservation_item_count_drift")
    if intake_summary.get("policy_question_count") != EXPECTED_POLICY_QUESTION_COUNT:
        blockers.append("intake_policy_question_count_drift")
    if simulator_plan.get("recommended_next_version") != "v0.4.8.1":
        blockers.append("intake_next_version_not_simulator_spec")
    if simulator_plan.get("input_policy") != "saved_reports_only":
        blockers.append("intake_simulator_plan_not_saved_reports_only")
    if simulator_plan.get("runtime_integration_allowed") is not False:
        blockers.append("intake_runtime_integration_not_blocked")
    if simulator_plan.get("rerank_change_allowed") is not False:
        blockers.append("intake_rerank_change_not_blocked")
    for key in [
        "implementation_allowed",
        "code_patch_authorized",
        "runtime_selection_policy_patch_allowed",
        "rerank_change_allowed",
    ]:
        if intake_gate.get(key) is not False:
            blockers.append(f"intake_{key}_not_false")

    if audit_report.get("version") != EXPECTED_AUDIT_VERSION:
        blockers.append("audit_version_mismatch")
    if audit_report.get("scope") != EXPECTED_AUDIT_SCOPE:
        blockers.append("audit_scope_mismatch")
    if audit_summary.get("high_priority_review_cases") != EXPECTED_CASE_COUNT:
        blockers.append("audit_high_priority_count_drift")
    if audit_summary.get("total_final_selection_loss_cases", 0) < EXPECTED_CASE_COUNT:
        blockers.append("audit_selection_loss_case_count_insufficient")

    if confirmation.get("version") != EXPECTED_CONFIRMATION_VERSION:
        blockers.append("confirmation_version_mismatch")
    if confirmation.get("schema_kind") != EXPECTED_CONFIRMATION_SCHEMA:
        blockers.append("confirmation_schema_mismatch")
    if confirmation_gate.get("status") != EXPECTED_CONFIRMATION_STATUS:
        blockers.append("confirmation_gate_status_mismatch")
    if confirmation_gate.get("future_design_planning_allowed") is not True:
        blockers.append("confirmation_future_design_not_allowed")
    if confirmation_gate.get("implementation_allowed") is not False:
        blockers.append("confirmation_implementation_not_blocked")
    if not confirmation_row:
        blockers.append("confirmation_final_selection_row_missing")
    else:
        if confirmation_row.get("confirmed_next_series") != "v0.4.8.x":
            blockers.append("confirmation_next_series_mismatch")
        if confirmation_row.get("implementation_allowed") is not False:
            blockers.append("confirmation_row_implementation_not_blocked")
        if confirmation_row.get("code_patch_authorized") is not False:
            blockers.append("confirmation_row_code_patch_not_blocked")

    intake_case_ids = sorted_unique([text(row.get("case_id")) for row in as_list(intake.get("case_intake_matrix"))])
    audit_case_ids = sorted_unique([text(row.get("case_id")) for row in as_list(audit_report.get("cases"))])
    confirmation_case_ids = sorted_unique([
        text(case_id)
        for case_id in as_list(as_dict(confirmation_row.get("traceability")).get("source_case_ids"))
    ])
    if len(intake_case_ids) != EXPECTED_CASE_COUNT:
        blockers.append("intake_case_matrix_count_drift")
    if not set(intake_case_ids).issubset(set(audit_case_ids)):
        blockers.append("intake_cases_missing_from_audit")
    if sorted(intake_case_ids) != sorted(confirmation_case_ids):
        blockers.append("intake_confirmation_case_ids_mismatch")

    for label, report in [
        ("intake", intake),
        ("audit", audit_report),
        ("confirmation", confirmation),
    ]:
        forbidden, advisory = key_violations(report)
        for key in forbidden:
            blockers.append(f"{label}_forbidden_key_present:{key}")
        for key in advisory:
            blockers.append(f"{label}_advisory_signal_present:{key}")

    return sorted_unique(blockers)


def functional_types_from_summary(summary: dict[str, Any]) -> list[str]:
    return sorted_unique([text(key) for key in as_dict(summary.get("functional_type_summary")).keys()])


def build_expected_signals(row: dict[str, Any], audit_case: dict[str, Any]) -> list[dict[str, Any]]:
    issues = set(as_list(row.get("detected_issues")) or as_list(audit_case.get("detected_issues")))
    lost_summary = as_dict(row.get("lost_evidence_summary"))
    missing_final_summary = as_dict(row.get("missing_final_expected_summary"))
    missing_core_summary = as_dict(row.get("missing_scenario_core_summary"))
    functional_types = set(functional_types_from_summary(lost_summary))
    functional_types.update(functional_types_from_summary(missing_final_summary))
    functional_types.update(functional_types_from_summary(missing_core_summary))
    risk_level = text(row.get("risk_level") or audit_case.get("risk_level"))

    signals: list[dict[str, Any]] = []

    def add(signal_id: str, basis: list[str]) -> None:
        signals.append({
            "signal_id": signal_id,
            "basis": sorted_unique(basis),
            "spec_action": "future_simulator_must_emit_quality_signal",
        })

    if "primary_evidence_lost" in issues or "rerank_input_to_final_loss" in issues:
        add("primary_evidence_should_be_preserved", ["primary_evidence_lost", "rerank_input_to_final_loss"])
    if "operative_evidence_lost" in issues or "operative_rule" in functional_types:
        add("operative_rule_should_be_preserved", ["operative_evidence_lost", "operative_rule"])
    if "procedural" in functional_types:
        add("procedural_evidence_should_be_preserved", ["lost_functional_type:procedural"])
    if "liability_evidence_lost" in issues or "liability" in functional_types:
        add("liability_evidence_should_be_preserved", ["liability_evidence_lost", "lost_functional_type:liability"])
    if "scenario_core_lost" in issues or int(missing_core_summary.get("count") or 0) > 0:
        add("scenario_core_should_be_preserved_or_explained", ["scenario_core_lost", "missing_scenario_core"])
    if "definition" in functional_types:
        add("definition_only_must_not_substitute_normative_evidence", ["lost_functional_type:definition"])
    if "low_final_coverage_after_selection" in issues:
        add("final_coverage_floor_review_needed", ["low_final_coverage_after_selection"])
    if risk_level == "high" and signals:
        add("manual_review_required_for_high_risk_gap", ["risk_level:high", "preservation_gap_signal"])

    return signals


def build_case_simulation_spec_matrix(
    intake: dict[str, Any],
    audit_report: dict[str, Any],
    spec_ready: bool,
) -> list[dict[str, Any]]:
    audit_cases = audit_case_map(audit_report)
    rows = []
    for item in as_list(intake.get("case_intake_matrix")):
        row = as_dict(item)
        case_id = text(row.get("case_id"))
        audit_case = audit_cases.get(case_id, {})
        expected_signals = build_expected_signals(row, audit_case)
        signal_ids = [signal["signal_id"] for signal in expected_signals]
        rows.append({
            "case_id": case_id,
            "spec_status": "ready_for_saved_report_simulation_spec" if spec_ready and audit_case else "blocked",
            "risk_level": row.get("risk_level") or audit_case.get("risk_level") or "",
            "expected_domains": as_list(row.get("expected_domains")) or as_list(audit_case.get("expected_domains")),
            "detected_issues": as_list(row.get("detected_issues")) or as_list(audit_case.get("detected_issues")),
            "review_reasons": as_list(row.get("review_reasons")) or as_list(audit_case.get("review_reasons")),
            "selection_flow": as_dict(row.get("selection_flow")) or as_dict(audit_case.get("selection_flow")),
            "lost_evidence_summary": as_dict(row.get("lost_evidence_summary")),
            "missing_final_expected_summary": as_dict(row.get("missing_final_expected_summary")),
            "missing_scenario_core_summary": as_dict(row.get("missing_scenario_core_summary")),
            "required_quality_signals": expected_signals,
            "manual_review_required": "manual_review_required_for_high_risk_gap" in signal_ids,
            "simulator_expected_status": (
                "manual_review_required_before_runtime_policy"
                if "manual_review_required_for_high_risk_gap" in signal_ids
                else "ready_for_policy_draft_candidate"
            ),
            "traceability": {
                "intake_row_present": bool(row),
                "audit_case_present": bool(audit_case),
                "design_action_id": as_dict(row.get("design_action")).get("design_action_id"),
            },
        })
    return rows


def build_input_contract() -> dict[str, Any]:
    return {
        "contract_type": "saved_report_only_input_contract",
        "required_reports": [
            {
                "role": "policy_intake",
                "path": str(DEFAULT_INTAKE_REPORT_PATH),
                "expected_version": EXPECTED_INTAKE_VERSION,
                "expected_schema_kind": EXPECTED_INTAKE_SCHEMA,
                "required_sections": [
                    "intake_gate",
                    "summary",
                    "policy_questions",
                    "preservation_rule_discussion_items",
                    "case_intake_matrix",
                    "policy_simulator_plan",
                    "traceability",
                ],
            },
            {
                "role": "final_selection_audit",
                "path": str(DEFAULT_AUDIT_REPORT_PATH),
                "expected_version": EXPECTED_AUDIT_VERSION,
                "expected_scope": EXPECTED_AUDIT_SCOPE,
                "required_sections": ["summary", "cases"],
            },
            {
                "role": "human_closeout_confirmation",
                "path": str(DEFAULT_CONFIRMATION_REPORT_PATH),
                "expected_version": EXPECTED_CONFIRMATION_VERSION,
                "expected_schema_kind": EXPECTED_CONFIRMATION_SCHEMA,
                "required_sections": ["confirmation_gate", "confirmation_matrix", "traceability"],
            },
        ],
        "forbidden_inputs": [
            "live RAG output",
            "backend response",
            "Qdrant query result",
            "LLM-generated new answer",
            "modified eval case",
            "modified scenario registry",
        ],
    }


def build_simulation_output_contract() -> dict[str, Any]:
    return {
        "contract_type": "future_offline_simulator_output_contract",
        "report_schema_kind": "final_evidence_selection_policy_simulation_report",
        "allowed_status_values": [
            "blocked_by_input_contract",
            "manual_review_required_before_runtime_policy",
            "ready_for_policy_draft_candidate",
        ],
        "required_top_level_fields": [
            "version",
            "schema_kind",
            "scope",
            "inputs",
            "simulation_gate",
            "summary",
            "case_results",
            "issue_type_summary",
            "manual_review_list",
            "traceability",
            "assertions",
        ],
        "required_case_fields": [
            "case_id",
            "input_trace",
            "policy_candidate_categories_checked",
            "required_quality_signals",
            "preservation_outcome",
            "coverage_floor_signal",
            "definition_only_substitution_signal",
            "manual_review_required",
            "review_reasons",
        ],
        "must_not_emit": [
            "runtime policy patch",
            "rerank change",
            "prompt change",
            "eval case mutation",
            "fixture write",
            "main-flow integration",
        ],
    }


def build_manual_review_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manual_review_rows = []
    for row in rows:
        if not row.get("manual_review_required"):
            continue
        manual_review_rows.append({
            "case_id": row.get("case_id"),
            "risk_level": row.get("risk_level"),
            "required_quality_signals": [
                signal.get("signal_id")
                for signal in as_list(row.get("required_quality_signals"))
            ],
            "review_reasons": row.get("review_reasons"),
        })
    return {
        "status": "manual_review_required_before_runtime_policy" if manual_review_rows else "no_manual_review_signal",
        "manual_review_required_count": len(manual_review_rows),
        "manual_review_list": manual_review_rows,
        "design_policy_table_draft_allowed": True,
        "runtime_policy_adoption_allowed_without_review": False if manual_review_rows else True,
    }


def build_summary(status: str, rows: list[dict[str, Any]], intake: dict[str, Any], audit_report: dict[str, Any]) -> dict[str, Any]:
    domains = Counter()
    risks = Counter()
    issues = Counter()
    signals = Counter()
    for row in rows:
        risks[text(row.get("risk_level")) or "unknown"] += 1
        for domain in as_list(row.get("expected_domains")):
            domains[text(domain) or "unknown"] += 1
        issues.update(as_list(row.get("detected_issues")))
        signals.update(signal.get("signal_id") for signal in as_list(row.get("required_quality_signals")))
    intake_summary = as_dict(intake.get("summary"))
    audit_summary = as_dict(audit_report.get("summary"))
    return {
        "status": status,
        "allowed_use": "offline_policy_simulator_spec_only" if status != "blocked" else "blocked",
        "confirmed_case_count": len(rows),
        "source_intake_case_count": intake_summary.get("confirmed_case_count", 0),
        "audit_high_priority_review_cases": audit_summary.get("high_priority_review_cases", 0),
        "policy_candidate_category_count": len(POLICY_CANDIDATE_CATEGORIES),
        "failure_signal_count": len(FAILURE_SIGNAL_CATALOG),
        "case_risk_level_summary": counter_dict(risks),
        "case_domain_occurrence_summary": counter_dict(domains),
        "case_issue_type_summary": counter_dict(issues),
        "required_quality_signal_summary": counter_dict(signals),
        "manual_review_required_case_count": signals.get("manual_review_required_for_high_risk_gap", 0),
        "next_version_recommendation": "v0.4.8.2 policy table draft",
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
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
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "source_reports_are_ready_for_simulator_spec",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "confirmed_cases_have_case_level_spec_rows",
            "status": "passed"
            if len(rows) == EXPECTED_CASE_COUNT and all(row.get("spec_status") == "ready_for_saved_report_simulation_spec" for row in rows)
            else "failed",
            "case_count": len(rows),
            "expected": EXPECTED_CASE_COUNT,
        },
        {
            "name": "policy_candidates_are_spec_only",
            "status": "passed"
            if all(item.get("allowed_stage") == "offline_spec_only" for item in POLICY_CANDIDATE_CATEGORIES)
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
            "status": "passed" if not readability_errors else "failed",
            "mojibake_like_paths": readability_errors,
        },
    ]


def build_report(
    intake_report_path: Path = DEFAULT_INTAKE_REPORT_PATH,
    audit_report_path: Path = DEFAULT_AUDIT_REPORT_PATH,
    confirmation_report_path: Path = DEFAULT_CONFIRMATION_REPORT_PATH,
) -> dict[str, Any]:
    intake = load_json(intake_report_path)
    audit_report = load_json(audit_report_path)
    confirmation = load_json(confirmation_report_path)
    source_blockers = source_contract_blockers(intake, audit_report, confirmation)
    spec_ready = not source_blockers
    rows = build_case_simulation_spec_matrix(intake, audit_report, spec_ready)
    status = "ready_for_offline_policy_simulator_spec" if spec_ready else "blocked"
    manual_review_gate = build_manual_review_gate(rows)
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_simulator_spec",
        "scope": "offline final evidence selection policy simulator spec only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_intake": source_meta(intake_report_path, intake),
            "final_selection_audit": source_meta(audit_report_path, audit_report),
            "human_closeout_confirmation": source_meta(confirmation_report_path, confirmation),
        },
        "guardrails": SPEC_GUARDRAILS,
        "non_goals": NON_GOALS,
        "simulator_spec_gate": {
            "status": status,
            "allowed_use": "offline_policy_simulator_spec_only" if spec_ready else "blocked",
            "saved_report_only": True,
            "simulator_spec_allowed": spec_ready,
            "simulator_implementation_allowed": False,
            "policy_implementation_allowed": False,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "rag_query_integration": "disallowed",
            "blockers": source_blockers,
        },
        "summary": build_summary(status, rows, intake, audit_report),
        "input_contract": build_input_contract(),
        "policy_candidate_categories": POLICY_CANDIDATE_CATEGORIES,
        "simulation_output_contract": build_simulation_output_contract(),
        "case_simulation_spec_matrix": rows,
        "failure_signal_catalog": FAILURE_SIGNAL_CATALOG,
        "manual_review_gate": manual_review_gate,
        "next_version_handoff": {
            "recommended_next_version": "v0.4.8.2",
            "recommended_artifact": "final evidence selection policy table draft",
            "handoff_status": "design_contract_ready" if spec_ready else "blocked",
            "allowed_next_step": "draft_policy_table_from_saved_report_spec_only" if spec_ready else "resolve_source_contract_blockers",
            "runtime_implementation_allowed": False,
            "requires_explicit_future_implementation_approval": True,
        },
        "excluded_scope": {
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
            "source_case_ids": [row.get("case_id") for row in rows],
            "source_reports": [
                str(intake_report_path),
                str(audit_report_path),
                str(confirmation_report_path),
            ],
            "source_intake_version": intake.get("version"),
            "source_audit_version": audit_report.get("version"),
            "source_confirmation_version": confirmation.get("version"),
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        rows,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["simulator_spec_gate"]["status"] = "blocked"
        report["simulator_spec_gate"]["allowed_use"] = "blocked"
        report["simulator_spec_gate"]["simulator_spec_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["simulator_spec_gate"]["blockers"] = sorted_unique(report["simulator_spec_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("simulator_spec_gate"))
    summary = as_dict(report.get("summary"))
    manual_review = as_dict(report.get("manual_review_gate"))
    lines = [
        "# v0.4.8.1 Final Evidence Selection Policy Simulator Spec",
        "",
        "本文档是最终证据选择策略模拟器的离线契约。它只定义未来 saved-report simulator 应如何读取既有报告、输出质量信号和触发人工复核；它不是 runtime policy 实现，也不是 rerank、prompt、eval case 或 RAG 主流程修复。",
        "",
        "## Overview",
        "",
        f"- Spec status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Confirmed cases: {summary.get('confirmed_case_count')}",
        f"- Policy candidate categories: {summary.get('policy_candidate_category_count')}",
        f"- Failure signals: {summary.get('failure_signal_count')}",
        f"- Manual-review cases: {manual_review.get('manual_review_required_count')}",
        f"- Next version recommendation: `{summary.get('next_version_recommendation')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Runtime policy implementation allowed: {gate.get('runtime_policy_implementation_allowed')}",
        f"- Rerank change allowed: {gate.get('rerank_change_allowed')}",
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
        "## Policy Candidate Categories",
        "",
        "| Category | Signal | Purpose |",
        "|---|---|---|",
    ])
    for item in as_list(report.get("policy_candidate_categories")):
        lines.append(
            f"| `{item.get('category_id')}` | `{item.get('required_output_signal')}` | {item.get('purpose')} |"
        )

    lines.extend([
        "",
        "## Case Spec Matrix",
        "",
        "| Case | Risk | Domains | Required signals | Simulator status |",
        "|---|---|---|---|---|",
    ])
    for row in as_list(report.get("case_simulation_spec_matrix")):
        signals = [
            signal.get("signal_id")
            for signal in as_list(row.get("required_quality_signals"))
        ]
        lines.append(
            f"| `{row.get('case_id')}` | {row.get('risk_level')} | "
            f"{', '.join(as_list(row.get('expected_domains')))} | "
            f"{', '.join(signals)} | `{row.get('simulator_expected_status')}` |"
        )

    lines.extend([
        "",
        "## Failure Signals",
        "",
        "| Signal | Severity | Review reason |",
        "|---|---|---|",
    ])
    for item in as_list(report.get("failure_signal_catalog")):
        lines.append(f"| `{item.get('signal_id')}` | {item.get('severity')} | {item.get('review_reason')} |")

    lines.extend([
        "",
        "## Manual Review Gate",
        "",
        f"- Status: `{manual_review.get('status')}`",
        f"- Manual-review required count: {manual_review.get('manual_review_required_count')}",
        f"- Design policy table draft allowed: {manual_review.get('design_policy_table_draft_allowed')}",
        f"- Runtime policy adoption allowed without review: {manual_review.get('runtime_policy_adoption_allowed_without_review')}",
        "",
        "## Boundaries",
        "",
        "- 本版本是 RAG grounding quality governance 的 saved-report simulator spec，不是样本修补工具。",
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
    parser = argparse.ArgumentParser(description="Build final evidence selection policy simulator spec.")
    parser.add_argument("--intake-report", type=Path, default=DEFAULT_INTAKE_REPORT_PATH)
    parser.add_argument("--audit-report", type=Path, default=DEFAULT_AUDIT_REPORT_PATH)
    parser.add_argument("--confirmation-report", type=Path, default=DEFAULT_CONFIRMATION_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.intake_report, args.audit_report, args.confirmation_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy simulator spec built: "
        f"{summary['status']}, "
        f"{summary['confirmed_case_count']} cases, "
        f"{summary['policy_candidate_category_count']} categories"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
