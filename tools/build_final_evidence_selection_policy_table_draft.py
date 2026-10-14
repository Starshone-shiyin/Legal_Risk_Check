"""Build the v0.4.8.2 final-evidence selection policy table draft.

This tool reads saved governance reports and converts the v0.4.8.1 simulator
spec into a human-reviewable policy table. It is a design-layer artifact only:
it does not implement runtime policy, change rerank, alter prompts, mutate eval
cases, call RAG, contact a backend, contact Qdrant, or call an LLM.
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


VERSION = "0.4.8.2"

DEFAULT_SIMULATOR_SPEC_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_simulator_spec_report.json")
DEFAULT_INTAKE_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_intake_report.json")
DEFAULT_AUDIT_REPORT_PATH = legacy_report_path("final_evidence_selection_audit_report.json")
DEFAULT_CONFIRMATION_REPORT_PATH = legacy_report_path("ready_action_human_closeout_confirmation_record_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_table_draft_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_table_draft_v0.4.8.2.md")

EXPECTED_SPEC_VERSION = "0.4.8.1"
EXPECTED_SPEC_SCHEMA = "final_evidence_selection_policy_simulator_spec"
EXPECTED_SPEC_STATUS = "ready_for_offline_policy_simulator_spec"
EXPECTED_INTAKE_VERSION = "0.4.8.0"
EXPECTED_INTAKE_SCHEMA = "final_evidence_selection_policy_design_intake"
EXPECTED_AUDIT_VERSION = "0.4.7.4.5"
EXPECTED_AUDIT_SCOPE = "offline final evidence selection audit"
EXPECTED_CONFIRMATION_VERSION = "0.4.7.9.6"
EXPECTED_CONFIRMATION_SCHEMA = "ready_action_human_closeout_confirmation_record"
EXPECTED_CASE_COUNT = 5
EXPECTED_POLICY_CATEGORY_COUNT = 6
EXPECTED_FAILURE_SIGNAL_COUNT = 8
EXPECTED_TABLE_ROW_COUNT = 8

POLICY_TABLE_GUARDRAILS = {
    "table_draft_only": True,
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
    "不把 policy table row 转成工程修复任务、backlog 或补丁清单。",
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

POLICY_ROW_BLUEPRINTS = [
    {
        "policy_id": "FES-POLICY-DRAFT-001",
        "policy_category": "primary",
        "priority": "P0",
        "required_quality_signal": "primary_evidence_should_be_preserved",
        "source_signals": ["primary_evidence_lost", "rerank_input_to_final_loss"],
        "trigger_condition": "核心或主要法律依据在前序候选层存在，但没有进入 final evidence_chain。",
        "preservation_requirement": "最终证据选择草案必须把主证据保留为优先检查对象；如未保留，必须说明可复核的替代依据。",
        "acceptable_substitution_condition": "只有同一法域、同一核心争点、同等或更强规范功能的证据可以作为替代候选。",
        "must_emit_manual_review_when": "主证据未进入 final evidence_chain，或替代依据的法域、争点、规范功能无法从保存报告中确认。",
        "coverage_floor_rule": "主证据缺失时不得仅凭次要争点覆盖率判断为足够。",
        "definition_only_guard": "定义条款不得替代主证据中的义务、程序、责任或后果规则。",
    },
    {
        "policy_id": "FES-POLICY-DRAFT-002",
        "policy_category": "operative",
        "priority": "P0",
        "required_quality_signal": "operative_rule_should_be_preserved",
        "source_signals": ["operative_evidence_lost", "operative_rule"],
        "trigger_condition": "丢失证据包含义务、禁止、许可、合法性基础等行为规范。",
        "preservation_requirement": "最终证据选择草案必须保留能直接支撑结论的义务或行为规范条款。",
        "acceptable_substitution_condition": "替代证据必须同样表达可执行的义务、禁止、许可或合法性基础，不能只是背景说明。",
        "must_emit_manual_review_when": "答案存在风险结论或整改动作，但 final evidence_chain 缺少对应规范性条款。",
        "coverage_floor_rule": "背景材料覆盖不能抵消操作性规范缺失。",
        "definition_only_guard": "定义条款只能解释概念，不能替代行为规范。",
    },
    {
        "policy_id": "FES-POLICY-DRAFT-003",
        "policy_category": "procedural",
        "priority": "P0",
        "required_quality_signal": "procedural_evidence_should_be_preserved",
        "source_signals": ["procedural"],
        "trigger_condition": "丢失证据包含告知、评估、申报、同意、程序步骤等程序性要求。",
        "preservation_requirement": "最终证据选择草案必须把程序性要求作为独立证据类型保留或解释。",
        "acceptable_substitution_condition": "替代证据必须覆盖相同程序环节，且能支撑整改步骤或合规流程。",
        "must_emit_manual_review_when": "答案提出整改流程、合规步骤或审查路径，但证据链缺少程序性依据。",
        "coverage_floor_rule": "实体规则覆盖不能替代程序要求覆盖。",
        "definition_only_guard": "定义条款不得替代程序步骤或申报/告知义务。",
    },
    {
        "policy_id": "FES-POLICY-DRAFT-004",
        "policy_category": "liability",
        "priority": "P0",
        "required_quality_signal": "liability_evidence_should_be_preserved",
        "source_signals": ["liability_evidence_lost", "liability"],
        "trigger_condition": "丢失证据包含处罚、赔偿、整改责任、法律后果或高风险结论支撑。",
        "preservation_requirement": "最终证据选择草案必须保留责任或后果条款，尤其是答案给出高风险结论时。",
        "acceptable_substitution_condition": "替代证据必须直接覆盖同类责任、后果或救济路径。",
        "must_emit_manual_review_when": "答案存在高风险或责任判断，但 final evidence_chain 缺少直接责任/后果依据。",
        "coverage_floor_rule": "义务条款覆盖不能自动替代责任后果覆盖。",
        "definition_only_guard": "定义条款不得替代责任条款或处罚后果条款。",
    },
    {
        "policy_id": "FES-POLICY-DRAFT-005",
        "policy_category": "scenario_core",
        "priority": "P1",
        "required_quality_signal": "scenario_core_should_be_preserved_or_explained",
        "source_signals": ["scenario_core_lost"],
        "trigger_condition": "scenario registry 或既有审计标记的场景核心条文没有进入 final evidence_chain。",
        "preservation_requirement": "最终证据选择草案必须保留场景核心条文，或输出可人工复核的缺失解释。",
        "acceptable_substitution_condition": "替代证据必须覆盖同一场景核心争点，不能只覆盖相邻背景问题。",
        "must_emit_manual_review_when": "场景核心条文缺失且无法从 saved report 中确认合理替代。",
        "coverage_floor_rule": "次要争点覆盖不能替代场景核心条文覆盖。",
        "definition_only_guard": "若场景核心只剩定义条款，应触发定义替代防线复核。",
    },
    {
        "policy_id": "FES-POLICY-DRAFT-006",
        "policy_category": "definition_only",
        "priority": "P1",
        "required_quality_signal": "definition_only_must_not_substitute_normative_evidence",
        "source_signals": ["definition"],
        "trigger_condition": "最终证据或缺失核心证据只剩定义条款，而规范性支撑仍不足。",
        "preservation_requirement": "最终证据选择草案必须区分定义条款与义务、程序、责任、后果条款。",
        "acceptable_substitution_condition": "定义条款只能辅助解释；只有同时存在规范性条款时才可作为补充证据。",
        "must_emit_manual_review_when": "答案结论依赖风险、整改、责任或合规动作，但证据链只有定义性支撑。",
        "coverage_floor_rule": "定义条款覆盖不计为规范性争点的充分覆盖。",
        "definition_only_guard": "定义条款替代规范条款时必须进入人工复核。",
    },
    {
        "policy_id": "FES-POLICY-DRAFT-007",
        "policy_category": "coverage_floor",
        "priority": "P1",
        "required_quality_signal": "final_coverage_floor_review_needed",
        "source_signals": ["low_final_coverage_after_selection"],
        "trigger_condition": "final evidence 覆盖率低于既有审计阈值，或 rerank_input 到 final 出现明显覆盖下降。",
        "preservation_requirement": "最终证据选择草案必须把覆盖率下降作为阻断人工复核信号，而不是自动通过。",
        "acceptable_substitution_condition": "只有主要争点、场景核心和规范功能均可从保存报告中确认时，才可解释覆盖下降。",
        "must_emit_manual_review_when": "final evidence 只覆盖次要争点，或主要争点覆盖不足。",
        "coverage_floor_rule": "主要争点覆盖优先于单纯数量覆盖；低覆盖必须触发复核。",
        "definition_only_guard": "定义条款覆盖不得抬高规范性覆盖判断。",
    },
    {
        "policy_id": "FES-POLICY-DRAFT-008",
        "policy_category": "high_risk_manual_review",
        "priority": "P0",
        "required_quality_signal": "manual_review_required_for_high_risk_gap",
        "source_signals": ["preservation_gap_signal", "risk_level:high"],
        "trigger_condition": "高风险 case 存在任一证据保留、覆盖或定义替代缺口。",
        "preservation_requirement": "最终证据选择草案必须把高风险缺口列入人工复核清单。",
        "acceptable_substitution_condition": "高风险缺口不得仅由自动策略解释；必须保留人工复核入口。",
        "must_emit_manual_review_when": "高风险结论与任何 required quality signal 同时出现。",
        "coverage_floor_rule": "高风险 case 不允许以低覆盖或次要争点覆盖直接进入运行时采用。",
        "definition_only_guard": "高风险 case 中定义条款替代规范条款时必须人工复核。",
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


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


def signal_ids_for_case(row: dict[str, Any]) -> list[str]:
    return sorted_unique([
        text(signal.get("signal_id"))
        for signal in as_list(row.get("required_quality_signals"))
        if isinstance(signal, dict)
    ])


def source_contract_blockers(
    simulator_spec: dict[str, Any],
    intake: dict[str, Any],
    audit_report: dict[str, Any],
    confirmation: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    spec_gate = as_dict(simulator_spec.get("simulator_spec_gate"))
    spec_summary = as_dict(simulator_spec.get("summary"))
    manual_review_gate = as_dict(simulator_spec.get("manual_review_gate"))

    if simulator_spec.get("version") != EXPECTED_SPEC_VERSION:
        blockers.append("simulator_spec_version_mismatch")
    if simulator_spec.get("schema_kind") != EXPECTED_SPEC_SCHEMA:
        blockers.append("simulator_spec_schema_mismatch")
    if spec_gate.get("status") != EXPECTED_SPEC_STATUS:
        blockers.append("simulator_spec_gate_not_ready")
    if spec_gate.get("saved_report_only") is not True:
        blockers.append("simulator_spec_not_saved_report_only")
    if as_list(spec_gate.get("blockers")):
        blockers.append("simulator_spec_gate_has_blockers")
    if spec_summary.get("confirmed_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("simulator_spec_case_count_drift")
    if spec_summary.get("policy_candidate_category_count") != EXPECTED_POLICY_CATEGORY_COUNT:
        blockers.append("simulator_spec_policy_category_count_drift")
    if spec_summary.get("failure_signal_count") != EXPECTED_FAILURE_SIGNAL_COUNT:
        blockers.append("simulator_spec_failure_signal_count_drift")
    if spec_summary.get("manual_review_required_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("simulator_spec_manual_review_count_drift")
    if spec_summary.get("next_version_recommendation") != "v0.4.8.2 policy table draft":
        blockers.append("simulator_spec_next_version_mismatch")
    if manual_review_gate.get("design_policy_table_draft_allowed") is not True:
        blockers.append("simulator_spec_table_draft_not_allowed")
    if manual_review_gate.get("runtime_policy_adoption_allowed_without_review") is not False:
        blockers.append("simulator_spec_runtime_adoption_not_blocked")

    for key in [
        "implementation_allowed",
        "code_patch_authorized",
        "runtime_policy_implementation_allowed",
        "runtime_selection_policy_patch_allowed",
        "rerank_change_allowed",
    ]:
        if spec_gate.get(key) is not False:
            blockers.append(f"simulator_spec_{key}_not_false")
        if spec_summary.get(key) is not False:
            blockers.append(f"simulator_spec_summary_{key}_not_false")

    rows = [as_dict(row) for row in as_list(simulator_spec.get("case_simulation_spec_matrix"))]
    if len(rows) != EXPECTED_CASE_COUNT:
        blockers.append("simulator_spec_case_matrix_count_drift")
    if not all(row.get("spec_status") == "ready_for_saved_report_simulation_spec" for row in rows):
        blockers.append("simulator_spec_case_rows_not_ready")
    if not all(row.get("manual_review_required") is True for row in rows):
        blockers.append("simulator_spec_manual_review_not_preserved")

    signal_catalog = as_list(simulator_spec.get("failure_signal_catalog"))
    if len(signal_catalog) != EXPECTED_FAILURE_SIGNAL_COUNT:
        blockers.append("simulator_spec_signal_catalog_count_drift")
    if len(as_list(simulator_spec.get("policy_candidate_categories"))) != EXPECTED_POLICY_CATEGORY_COUNT:
        blockers.append("simulator_spec_policy_candidate_catalog_count_drift")

    if intake.get("version") != EXPECTED_INTAKE_VERSION:
        blockers.append("intake_version_mismatch")
    if intake.get("schema_kind") != EXPECTED_INTAKE_SCHEMA:
        blockers.append("intake_schema_mismatch")
    if audit_report.get("version") != EXPECTED_AUDIT_VERSION:
        blockers.append("audit_version_mismatch")
    if audit_report.get("scope") != EXPECTED_AUDIT_SCOPE:
        blockers.append("audit_scope_mismatch")
    if confirmation.get("version") != EXPECTED_CONFIRMATION_VERSION:
        blockers.append("confirmation_version_mismatch")
    if confirmation.get("schema_kind") != EXPECTED_CONFIRMATION_SCHEMA:
        blockers.append("confirmation_schema_mismatch")

    for label, report in [
        ("simulator_spec", simulator_spec),
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


def signal_catalog_map(simulator_spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in as_list(simulator_spec.get("failure_signal_catalog")):
        row = as_dict(item)
        signal_id = text(row.get("signal_id"))
        if signal_id:
            result[signal_id] = row
    return result


def case_rows(simulator_spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [as_dict(row) for row in as_list(simulator_spec.get("case_simulation_spec_matrix"))]


def evidence_summary_for_signal(row: dict[str, Any], signal_id: str) -> dict[str, Any]:
    if signal_id == "scenario_core_should_be_preserved_or_explained":
        summary = as_dict(row.get("missing_scenario_core_summary"))
    elif signal_id == "definition_only_must_not_substitute_normative_evidence":
        summary = as_dict(row.get("missing_scenario_core_summary")) or as_dict(row.get("lost_evidence_summary"))
    elif signal_id == "final_coverage_floor_review_needed":
        flow = as_dict(row.get("selection_flow"))
        return {
            "summary_kind": "selection_flow",
            "anchor": flow.get("anchor"),
            "rerank_input": flow.get("rerank_input"),
            "final": flow.get("final"),
            "rerank_input_to_final_delta": flow.get("rerank_input_to_final_delta"),
            "lost_coverage_ratio": flow.get("lost_coverage_ratio"),
        }
    elif signal_id == "manual_review_required_for_high_risk_gap":
        return {
            "summary_kind": "manual_review_gap",
            "risk_level": row.get("risk_level"),
            "required_quality_signals": signal_ids_for_case(row),
            "review_reason_count": len(as_list(row.get("review_reasons"))),
        }
    else:
        summary = as_dict(row.get("missing_final_expected_summary")) or as_dict(row.get("lost_evidence_summary"))

    return {
        "summary_kind": "evidence_gap",
        "count": summary.get("count", 0),
        "source_summary": as_dict(summary.get("source_summary")),
        "functional_type_summary": as_dict(summary.get("functional_type_summary")),
        "citations": as_list(summary.get("citations"))[:3],
    }


def build_policy_table_rows(simulator_spec: dict[str, Any], table_ready: bool) -> list[dict[str, Any]]:
    catalog = signal_catalog_map(simulator_spec)
    rows = case_rows(simulator_spec)
    table_rows: list[dict[str, Any]] = []

    for blueprint in POLICY_ROW_BLUEPRINTS:
        signal_id = blueprint["required_quality_signal"]
        applicable_cases = [
            row
            for row in rows
            if signal_id in signal_ids_for_case(row)
        ]
        applicable_case_ids = [text(row.get("case_id")) for row in applicable_cases]
        reasons = sorted_unique([
            text(reason)
            for row in applicable_cases
            for reason in as_list(row.get("review_reasons"))
        ])
        examples = [
            {
                "case_id": row.get("case_id"),
                "expected_domains": as_list(row.get("expected_domains")),
                "evidence_summary": evidence_summary_for_signal(row, signal_id),
            }
            for row in applicable_cases[:3]
        ]
        signal_meta = catalog.get(signal_id, {})
        table_rows.append({
            "policy_id": blueprint["policy_id"],
            "policy_category": blueprint["policy_category"],
            "priority": blueprint["priority"],
            "policy_status": "draft_for_manual_review" if table_ready else "blocked_by_source_contract",
            "source_signals": blueprint["source_signals"],
            "required_quality_signal": signal_id,
            "signal_severity": signal_meta.get("severity"),
            "signal_trigger": signal_meta.get("trigger"),
            "trigger_condition": blueprint["trigger_condition"],
            "preservation_requirement": blueprint["preservation_requirement"],
            "acceptable_substitution_condition": blueprint["acceptable_substitution_condition"],
            "must_emit_manual_review_when": blueprint["must_emit_manual_review_when"],
            "coverage_floor_rule": blueprint["coverage_floor_rule"],
            "definition_only_guard": blueprint["definition_only_guard"],
            "applicable_case_ids": applicable_case_ids,
            "case_count": len(applicable_case_ids),
            "example_evidence_summaries": examples,
            "review_reasons": reasons,
            "runtime_adoption_status": "not_allowed",
            "implementation_allowed": False,
            "traceability": {
                "source_report": str(DEFAULT_SIMULATOR_SPEC_REPORT_PATH),
                "source_matrix": "case_simulation_spec_matrix",
                "source_signal_catalog": "failure_signal_catalog",
            },
        })
    return table_rows


def build_input_contract() -> dict[str, Any]:
    return {
        "contract_type": "saved_report_only_policy_table_draft_input_contract",
        "required_reports": [
            {
                "role": "policy_simulator_spec",
                "path": str(DEFAULT_SIMULATOR_SPEC_REPORT_PATH),
                "expected_version": EXPECTED_SPEC_VERSION,
                "expected_schema_kind": EXPECTED_SPEC_SCHEMA,
                "required_sections": [
                    "simulator_spec_gate",
                    "summary",
                    "policy_candidate_categories",
                    "case_simulation_spec_matrix",
                    "failure_signal_catalog",
                    "manual_review_gate",
                    "assertions",
                ],
            },
            {
                "role": "policy_intake",
                "path": str(DEFAULT_INTAKE_REPORT_PATH),
                "expected_version": EXPECTED_INTAKE_VERSION,
                "expected_schema_kind": EXPECTED_INTAKE_SCHEMA,
                "required_sections": ["intake_gate", "summary", "case_intake_matrix"],
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
                "required_sections": ["confirmation_gate", "confirmation_matrix"],
            },
        ],
        "forbidden_inputs": [
            "live RAG output",
            "backend response",
            "Qdrant query result",
            "LLM-generated new answer",
            "modified eval case",
            "modified scenario registry",
            "runtime policy state",
        ],
    }


def build_policy_table_contract() -> dict[str, Any]:
    return {
        "contract_type": "human_reviewable_policy_table_draft_contract",
        "report_schema_kind": "final_evidence_selection_policy_table_draft",
        "allowed_status_values": [
            "blocked_by_source_contract",
            "draft_for_manual_review",
        ],
        "required_top_level_fields": [
            "version",
            "schema_kind",
            "scope",
            "inputs",
            "policy_table_gate",
            "summary",
            "policy_table_rows",
            "manual_review_gate",
            "traceability",
            "assertions",
        ],
        "required_row_fields": [
            "policy_id",
            "policy_category",
            "priority",
            "policy_status",
            "source_signals",
            "required_quality_signal",
            "trigger_condition",
            "preservation_requirement",
            "acceptable_substitution_condition",
            "must_emit_manual_review_when",
            "coverage_floor_rule",
            "definition_only_guard",
            "applicable_case_ids",
            "case_count",
            "review_reasons",
            "runtime_adoption_status",
            "implementation_allowed",
            "traceability",
        ],
        "must_not_emit": [
            "runtime policy patch",
            "rerank change",
            "prompt change",
            "eval case mutation",
            "fixture write",
            "main-flow integration",
            "backend call",
            "Qdrant query",
            "LLM call",
        ],
    }


def build_manual_review_gate(policy_rows: list[dict[str, Any]], simulator_spec: dict[str, Any]) -> dict[str, Any]:
    source_gate = as_dict(simulator_spec.get("manual_review_gate"))
    high_risk_list = as_list(source_gate.get("manual_review_list"))
    rows_requiring_review = [
        {
            "policy_id": row.get("policy_id"),
            "policy_category": row.get("policy_category"),
            "priority": row.get("priority"),
            "required_quality_signal": row.get("required_quality_signal"),
            "case_count": row.get("case_count"),
            "review_reason_count": len(as_list(row.get("review_reasons"))),
        }
        for row in policy_rows
        if row.get("case_count", 0) > 0
    ]
    return {
        "status": "manual_review_required_before_runtime_policy" if high_risk_list else "no_manual_review_signal",
        "source_manual_review_gate_status": source_gate.get("status"),
        "policy_rows_requiring_review_count": len(rows_requiring_review),
        "policy_rows_requiring_review": rows_requiring_review,
        "high_risk_manual_review_case_count": len(high_risk_list),
        "high_risk_manual_review_list": high_risk_list,
        "policy_table_draft_allowed": True,
        "runtime_policy_adoption_allowed_without_review": False if high_risk_list else True,
        "requires_manual_review_before_runtime_adoption": True if high_risk_list else False,
    }


def build_summary(status: str, policy_rows: list[dict[str, Any]], simulator_spec: dict[str, Any]) -> dict[str, Any]:
    spec_summary = as_dict(simulator_spec.get("summary"))
    case_rows_data = case_rows(simulator_spec)
    priority_counter = Counter()
    signal_counter = Counter()
    domain_counter = Counter()
    issue_counter = Counter()
    category_case_counts: dict[str, int] = {}
    for row in policy_rows:
        priority_counter[text(row.get("priority")) or "unknown"] += 1
        signal_counter[text(row.get("required_quality_signal")) or "unknown"] += int(row.get("case_count", 0))
        category_case_counts[text(row.get("policy_category"))] = int(row.get("case_count", 0))
    for row in case_rows_data:
        for domain in as_list(row.get("expected_domains")):
            domain_counter[text(domain) or "unknown"] += 1
        issue_counter.update(as_list(row.get("detected_issues")))
    return {
        "status": status,
        "allowed_use": "offline_policy_table_draft_only" if status != "blocked" else "blocked",
        "source_spec_status": spec_summary.get("status"),
        "confirmed_case_count": len(case_rows_data),
        "policy_table_row_count": len(policy_rows),
        "policy_rows_with_case_signal_count": sum(1 for row in policy_rows if row.get("case_count", 0) > 0),
        "policy_priority_summary": counter_dict(priority_counter),
        "policy_signal_case_summary": counter_dict(signal_counter),
        "policy_category_case_counts": category_case_counts,
        "case_domain_occurrence_summary": counter_dict(domain_counter),
        "case_issue_type_summary": counter_dict(issue_counter),
        "manual_review_required_case_count": as_dict(simulator_spec.get("summary")).get("manual_review_required_case_count", 0),
        "source_required_quality_signal_summary": as_dict(spec_summary.get("required_quality_signal_summary")),
        "next_version_recommendation": "v0.4.8.3 policy table human review worksheet",
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "rag_query_integration": "disallowed",
    }


def build_assertions(
    source_blockers: list[str],
    policy_rows: list[dict[str, Any]],
    simulator_spec: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_case_ids = {
        text(row.get("case_id"))
        for row in case_rows(simulator_spec)
    }
    covered_case_ids = {
        text(case_id)
        for row in policy_rows
        for case_id in as_list(row.get("applicable_case_ids"))
    }
    return [
        {
            "name": "source_reports_are_ready_for_policy_table_draft",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "confirmed_cases_have_policy_table_coverage",
            "status": "passed"
            if source_case_ids and source_case_ids.issubset(covered_case_ids)
            else "failed",
            "source_case_count": len(source_case_ids),
            "covered_case_count": len(covered_case_ids),
            "missing_case_ids": sorted(source_case_ids - covered_case_ids),
        },
        {
            "name": "policy_rows_are_draft_only",
            "status": "passed"
            if len(policy_rows) == EXPECTED_TABLE_ROW_COUNT
            and all(row.get("policy_status") == "draft_for_manual_review" for row in policy_rows)
            and all(row.get("runtime_adoption_status") == "not_allowed" for row in policy_rows)
            and all(row.get("implementation_allowed") is False for row in policy_rows)
            else "failed",
            "policy_table_row_count": len(policy_rows),
            "expected": EXPECTED_TABLE_ROW_COUNT,
        },
        {
            "name": "manual_review_gate_is_preserved",
            "status": "passed"
            if as_dict(simulator_spec.get("manual_review_gate")).get("status") == "manual_review_required_before_runtime_policy"
            and as_dict(simulator_spec.get("manual_review_gate")).get("runtime_policy_adoption_allowed_without_review") is False
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
    simulator_spec_report_path: Path = DEFAULT_SIMULATOR_SPEC_REPORT_PATH,
    intake_report_path: Path = DEFAULT_INTAKE_REPORT_PATH,
    audit_report_path: Path = DEFAULT_AUDIT_REPORT_PATH,
    confirmation_report_path: Path = DEFAULT_CONFIRMATION_REPORT_PATH,
) -> dict[str, Any]:
    simulator_spec = load_json(simulator_spec_report_path)
    intake = load_json(intake_report_path)
    audit_report = load_json(audit_report_path)
    confirmation = load_json(confirmation_report_path)
    source_blockers = source_contract_blockers(simulator_spec, intake, audit_report, confirmation)
    table_ready = not source_blockers
    policy_rows = build_policy_table_rows(simulator_spec, table_ready)
    status = "ready_for_manual_review_policy_table_draft" if table_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_table_draft",
        "scope": "offline final evidence selection policy table draft only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_simulator_spec": source_meta(simulator_spec_report_path, simulator_spec),
            "policy_intake": source_meta(intake_report_path, intake),
            "final_selection_audit": source_meta(audit_report_path, audit_report),
            "human_closeout_confirmation": source_meta(confirmation_report_path, confirmation),
        },
        "guardrails": POLICY_TABLE_GUARDRAILS,
        "non_goals": NON_GOALS,
        "policy_table_gate": {
            "status": status,
            "allowed_use": "offline_policy_table_draft_only" if table_ready else "blocked",
            "saved_report_only": True,
            "policy_table_draft_allowed": table_ready,
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
        "summary": build_summary(status, policy_rows, simulator_spec),
        "input_contract": build_input_contract(),
        "policy_candidate_categories": as_list(simulator_spec.get("policy_candidate_categories")),
        "failure_signal_catalog": as_list(simulator_spec.get("failure_signal_catalog")),
        "policy_table_contract": build_policy_table_contract(),
        "policy_table_rows": policy_rows,
        "manual_review_gate": build_manual_review_gate(policy_rows, simulator_spec),
        "next_version_handoff": {
            "recommended_next_version": "v0.4.8.3",
            "recommended_artifact": "policy table human review worksheet",
            "handoff_status": "design_table_ready_for_manual_review" if table_ready else "blocked",
            "allowed_next_step": "review_policy_table_against_saved_report_signals" if table_ready else "resolve_source_contract_blockers",
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
            "source_case_ids": [row.get("case_id") for row in case_rows(simulator_spec)],
            "source_policy_ids": [row.get("policy_id") for row in policy_rows],
            "source_reports": [
                str(simulator_spec_report_path),
                str(intake_report_path),
                str(audit_report_path),
                str(confirmation_report_path),
            ],
            "source_simulator_spec_version": simulator_spec.get("version"),
            "source_intake_version": intake.get("version"),
            "source_audit_version": audit_report.get("version"),
            "source_confirmation_version": confirmation.get("version"),
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        policy_rows,
        simulator_spec,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["policy_table_gate"]["status"] = "blocked"
        report["policy_table_gate"]["allowed_use"] = "blocked"
        report["policy_table_gate"]["policy_table_draft_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["policy_table_gate"]["blockers"] = sorted_unique(report["policy_table_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("policy_table_gate"))
    summary = as_dict(report.get("summary"))
    manual_review = as_dict(report.get("manual_review_gate"))
    lines = [
        "# v0.4.8.2 Final Evidence Selection Policy Table Draft",
        "",
        "本文档是最终证据选择策略表草案。它只把 v0.4.8.1 saved-report simulator spec 中的 preservation、coverage、definition-only 和 manual-review 信号整理成人工可审阅的策略表；它不是 runtime policy 实现，也不修改 rerank、prompt、eval case 或 RAG 主流程。",
        "",
        "## Overview",
        "",
        f"- Table status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Confirmed cases: {summary.get('confirmed_case_count')}",
        f"- Policy table rows: {summary.get('policy_table_row_count')}",
        f"- Rows with case signal: {summary.get('policy_rows_with_case_signal_count')}",
        f"- Manual-review cases: {manual_review.get('high_risk_manual_review_case_count')}",
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
        "## Policy Table Rows",
        "",
        "| Policy | Category | Priority | Signal | Cases | Manual review trigger |",
        "|---|---|---|---|---:|---|",
    ])
    for row in as_list(report.get("policy_table_rows")):
        lines.append(
            f"| `{row.get('policy_id')}` | `{row.get('policy_category')}` | "
            f"{row.get('priority')} | `{row.get('required_quality_signal')}` | "
            f"{row.get('case_count')} | {row.get('must_emit_manual_review_when')} |"
        )

    lines.extend([
        "",
        "## Preservation Rules",
        "",
        "| Policy | Preservation requirement | Acceptable substitution |",
        "|---|---|---|",
    ])
    for row in as_list(report.get("policy_table_rows")):
        lines.append(
            f"| `{row.get('policy_id')}` | {row.get('preservation_requirement')} | "
            f"{row.get('acceptable_substitution_condition')} |"
        )

    lines.extend([
        "",
        "## Manual Review Gate",
        "",
        f"- Status: `{manual_review.get('status')}`",
        f"- Policy rows requiring review: {manual_review.get('policy_rows_requiring_review_count')}",
        f"- High-risk manual-review cases: {manual_review.get('high_risk_manual_review_case_count')}",
        f"- Policy table draft allowed: {manual_review.get('policy_table_draft_allowed')}",
        f"- Runtime policy adoption allowed without review: {manual_review.get('runtime_policy_adoption_allowed_without_review')}",
        "",
        "## Boundaries",
        "",
        "- 本版本是 RAG grounding quality governance 的 saved-report policy table draft，不是样本修补工具。",
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
    parser = argparse.ArgumentParser(description="Build final evidence selection policy table draft.")
    parser.add_argument("--simulator-spec-report", type=Path, default=DEFAULT_SIMULATOR_SPEC_REPORT_PATH)
    parser.add_argument("--intake-report", type=Path, default=DEFAULT_INTAKE_REPORT_PATH)
    parser.add_argument("--audit-report", type=Path, default=DEFAULT_AUDIT_REPORT_PATH)
    parser.add_argument("--confirmation-report", type=Path, default=DEFAULT_CONFIRMATION_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        args.simulator_spec_report,
        args.intake_report,
        args.audit_report,
        args.confirmation_report,
    )
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy table draft built: "
        f"{summary['status']}, "
        f"{summary['policy_table_row_count']} rows, "
        f"{summary['confirmed_case_count']} cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
