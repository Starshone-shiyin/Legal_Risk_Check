"""Build a governed ready-action design pack from validated review reports.

The design pack is a read-only planning artifact. It only reads saved
promotion and export-pipeline dry-run reports, groups ready action candidates
for engineering design review, and explicitly blocks implementation. It does
not mutate retrieval, rerank, prompts, anchors, risk rules, eval cases, hidden
seeds, schema files, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.9.0"

DEFAULT_PROMOTION_REPORT_PATH = legacy_report_path("validated_decision_promotion_dry_run_report.json")
DEFAULT_EXPORT_PIPELINE_DRY_RUN_REPORT_PATH = legacy_report_path("manual_review_export_pipeline_dry_run_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ready_action_design_pack_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ready_action_design_pack_v0.4.7.9.0.md")

READINESS_READY = "ready_from_valid_decision"
SOURCE_DECISION_COMPLETED = "completed"
VALIDATION_VALID = "valid"

DESIGN_ONLY_GUARDRAILS = {
    "design_only": True,
    "not_action_approval": True,
    "implementation_patch_generation": "disallowed",
    "automatic_migration_ready": False,
    "code_patch_authorized": False,
    "schema_mutation": "disallowed",
    "manual_review_schema_mutation": "disallowed",
    "manual_review_importer_mutation": "disallowed",
    "manual_review_dry_run_contract_mutation": "disallowed",
    "fixture_write_to_eval": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "rag_query_integration": "disallowed",
    "main_flow_mutation": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
}

NON_GOALS = [
    "不修 hidden seed。",
    "不新增或修改 anchor。",
    "不修改 rerank。",
    "不修改 prompt。",
    "不修改 risk supplement 或 term preservation 规则。",
    "不修改 eval case。",
    "不接入 RAG 请求主流程。",
    "不把 pending manual-review records 当成已确认工程任务。",
]

DESIGN_TRACK_PROFILES = {
    "final_evidence_selection_policy_review": {
        "design_track_id": "final_evidence_selection_policy_design",
        "action_category": "final_evidence_policy",
        "priority_band": "P0",
        "design_intent": (
            "为已通过人工复核的案例整理最终证据选择策略评审方案，重点关注重要法律依据在进入最终 "
            "evidence_chain 前被筛掉的问题。"
        ),
        "allowed_next_step": "撰写设计说明和测试计划草案，交由后续人工评审。",
        "prohibited_now": [
            "rerank_change",
            "prompt_change",
            "runtime_selection_policy_patch",
            "eval_case_change",
        ],
        "acceptance_checks": [
            "每一条拟议策略都能追溯到 completed + valid 的人工复核结论。",
            "只展示草案级 before/after 预期，不修改 retrieval 或 rerank。",
            "后续若进入实现，必须先定义回归检查。",
        ],
    },
    "primary_evidence_fixture_candidate_review": {
        "design_track_id": "primary_evidence_fixture_candidate_review",
        "action_category": "fixture_candidate_governance",
        "priority_band": "P0",
        "design_intent": (
            "整理主证据缺口对应的 fixture 候选复核要求，但不把候选样本写入 eval case。"
        ),
        "allowed_next_step": "准备 fixture 候选复核说明和候选进入标准。",
        "prohibited_now": [
            "fixture_write_to_eval",
            "eval_case_change",
            "knowledge_base_mutation",
            "automatic_fixture_promotion",
        ],
        "acceptance_checks": [
            "fixture 候选在明确批准前必须与 eval case 分离。",
            "每个候选都保留 case 来源和 reviewer 理由。",
            "任何候选变成可执行测试数据前，都需要后续实现评审。",
        ],
    },
    "scenario_registry_core_article_review": {
        "design_track_id": "scenario_registry_core_article_review",
        "action_category": "scenario_registry_governance",
        "priority_band": "P1",
        "design_intent": (
            "从已验证案例中整理 scenario registry 核心条文范围的复核问题，但不修改 registry 或 expected evidence。"
        ),
        "allowed_next_step": "准备 scenario core 条文复核清单，等待人工批准。",
        "prohibited_now": [
            "scenario_registry_change",
            "expected_evidence_change",
            "anchor_change",
            "eval_case_change",
        ],
        "acceptance_checks": [
            "区分 registry 范围问题、召回问题和最终证据选择问题。",
            "扩展核心条文范围前必须经过法律复核。",
            "pending cases 不参与范围判断。",
        ],
    },
    "high_risk_manual_grounding_review": {
        "design_track_id": "high_risk_manual_grounding_review",
        "action_category": "manual_grounding_review",
        "priority_band": "P0",
        "design_intent": (
            "为已验证的高风险案例准备人工 grounding 复核队列，重点核对风险结论或整改动作是否被证据支撑。"
        ),
        "allowed_next_step": "准备高风险 grounding 复核队列和逐项复核问题。",
        "prohibited_now": [
            "risk_rule_change",
            "answer_policy_change",
            "prompt_change",
            "automatic_case_closure",
        ],
        "acceptance_checks": [
            "明确列出需要证据支撑的风险类型、整改动作或结论。",
            "法律结论变更仍以人工复核为准。",
            "在后续实现和测试完成前，不宣称风险输出质量已经提升。",
        ],
    },
    "functional_typing_fixture_review": {
        "design_track_id": "legal_functional_typing_fixture_review",
        "action_category": "functional_typing_quality",
        "priority_band": "P1",
        "design_intent": (
            "整理 legal functional typing 的 fixture 复核要求，用于补强条款功能类型的黄金样例质量。"
        ),
        "allowed_next_step": "准备 typing fixture 复核说明和候选验收检查。",
        "prohibited_now": [
            "functional_type_config_change",
            "golden_fixture_write",
            "eval_case_change",
            "automatic_label_change",
        ],
        "acceptance_checks": [
            "typing fixture 候选在批准前不得写入 golden fixture。",
            "每个候选标签必须能追溯到已复核的法律功能和来源 case。",
            "未来任何 label/config 变更前必须先有 fixture 测试。",
        ],
    },
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


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def text(value: Any) -> str:
    return str(value or "").strip()


def sorted_unique(values: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return sorted(result, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))


def counter_dict(counter: Counter) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "scope": data.get("scope"),
        "schema_kind": data.get("schema_kind"),
    }


def source_gate(export_report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(export_report.get("summary"))
    return {
        "pipeline_conclusion": summary.get("pipeline_conclusion") or "",
        "gate_status": summary.get("gate_status") or "",
        "gate_blockers": as_list(summary.get("gate_blockers")),
        "dry_run_blockers": as_list(summary.get("dry_run_blockers")),
        "input_rows": summary.get("input_rows", 0),
        "imported_rows": summary.get("imported_rows", 0),
        "rejected_rows": summary.get("rejected_rows", 0),
        "valid_proposed_records": summary.get("valid_proposed_records", 0),
        "invalid_proposed_records": summary.get("invalid_proposed_records", 0),
        "pending_proposed_records": summary.get("pending_proposed_records", 0),
        "promotion_candidates": summary.get("promotion_candidates", 0),
        "ready_action_candidates": summary.get("ready_action_candidates", 0),
        "safe_ai_suggestion_input": summary.get("safe_ai_suggestion_input", False),
    }


def gate_errors(gate: dict[str, Any]) -> list[str]:
    errors = []
    if gate.get("pipeline_conclusion") != "ready_for_governed_action_planning":
        errors.append("pipeline_not_ready_for_governed_action_planning")
    if gate.get("gate_status") != "open":
        errors.append("closeout_gate_not_open")
    if gate.get("gate_blockers"):
        errors.append("gate_blockers_present")
    if gate.get("dry_run_blockers"):
        errors.append("dry_run_blockers_present")
    if gate.get("rejected_rows", 0) != 0:
        errors.append("rejected_rows_present")
    if gate.get("invalid_proposed_records", 0) != 0:
        errors.append("invalid_proposed_records_present")
    return errors


def candidate_contexts(promotion_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for candidate in as_list(promotion_report.get("promotion_candidates")):
        if not isinstance(candidate, dict):
            continue
        case_id = text(candidate.get("case_id"))
        if not case_id:
            continue
        contexts[case_id] = {
            "case_id": case_id,
            "reviewer": candidate.get("reviewer") or "",
            "reviewed_at": candidate.get("reviewed_at") or "",
            "source_review_outcome": candidate.get("decision") or "",
            "confirmed_root_causes": as_list(candidate.get("confirmed_root_causes")),
            "confirmed_follow_up_actions": as_list(candidate.get("confirmed_follow_up_actions")),
        }
    return contexts


def action_validation_errors(action: dict[str, Any], seen: set[tuple[str, str]]) -> list[str]:
    errors = []
    case_id = text(action.get("case_id"))
    action_type = text(action.get("action_type"))
    if not case_id:
        errors.append("missing_case_id")
    if not action_type:
        errors.append("missing_action_type")
    if action.get("readiness") != READINESS_READY:
        errors.append("readiness_not_ready_from_valid_decision")
    if action.get("source_decision_status") != SOURCE_DECISION_COMPLETED:
        errors.append("source_decision_not_completed")
    if action.get("validation_status") != VALIDATION_VALID:
        errors.append("validation_not_valid")
    if text(action.get("blocked_reason")):
        errors.append("blocked_reason_present")
    if action_type and action_type not in DESIGN_TRACK_PROFILES:
        errors.append("unmapped_action_type")
    key = (case_id, action_type)
    if case_id and action_type and key in seen:
        errors.append("duplicate_case_action_type")
    return errors


def design_action(action: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    action_type = text(action.get("action_type"))
    profile = DESIGN_TRACK_PROFILES[action_type]
    return {
        "design_action_id": f"{text(action.get('case_id'))}::{action_type}",
        "case_id": text(action.get("case_id")),
        "action_type": action_type,
        "action_category": action.get("action_category") or profile["action_category"],
        "design_track_id": profile["design_track_id"],
        "readiness": action.get("readiness") or "",
        "source_decision_status": action.get("source_decision_status") or "",
        "validation_status": action.get("validation_status") or "",
        "blocked_reason": action.get("blocked_reason") or "",
        "priority_score": action.get("priority_score"),
        "risk_level": action.get("risk_level") or "",
        "expected_domains": as_list(action.get("expected_domains")),
        "confirmed_root_causes": as_list(action.get("confirmed_root_causes")),
        "confirmed_follow_up_actions": as_list(context.get("confirmed_follow_up_actions")),
        "target_areas": as_list(action.get("target_areas")),
        "reviewer": context.get("reviewer") or "",
        "reviewed_at": context.get("reviewed_at") or "",
        "source_review_outcome": context.get("source_review_outcome") or "",
        "rationale": action.get("rationale") or "",
        "notes": action.get("notes") or "",
        "planning_status": "design_review_only",
    }


def collect_design_actions(promotion_report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contexts = candidate_contexts(promotion_report)
    ready_actions = []
    excluded = []
    seen: set[tuple[str, str]] = set()
    for candidate in as_list(promotion_report.get("promotion_candidates")):
        if not isinstance(candidate, dict):
            continue
        case_id = text(candidate.get("case_id"))
        context = contexts.get(case_id, {"case_id": case_id})
        for action in as_list(candidate.get("ready_action_candidates")):
            if not isinstance(action, dict):
                continue
            errors = action_validation_errors(action, seen)
            key = (text(action.get("case_id")), text(action.get("action_type")))
            if not errors:
                seen.add(key)
                ready_actions.append(design_action(action, context))
            else:
                excluded.append({
                    "case_id": text(action.get("case_id")),
                    "action_type": text(action.get("action_type")),
                    "excluded_reasons": errors,
                })
    return sorted(ready_actions, key=lambda item: (item["action_type"], -int(item.get("priority_score") or 0), item["case_id"])), excluded


def summarize_domains(actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    domains: dict[str, dict[str, Any]] = {}
    for action in actions:
        expected_domains = action.get("expected_domains") or ["unknown"]
        for domain in expected_domains:
            key = text(domain) or "unknown"
            row = domains.setdefault(
                key,
                {
                    "ready_action_candidates": 0,
                    "source_cases": set(),
                    "action_type_summary": Counter(),
                    "risk_level_summary": Counter(),
                },
            )
            row["ready_action_candidates"] += 1
            row["source_cases"].add(action["case_id"])
            row["action_type_summary"][action["action_type"]] += 1
            row["risk_level_summary"][action.get("risk_level") or "unknown"] += 1
    return {
        domain: {
            "ready_action_candidates": row["ready_action_candidates"],
            "case_count": len(row["source_cases"]),
            "source_case_ids": sorted(row["source_cases"]),
            "action_type_summary": counter_dict(row["action_type_summary"]),
            "risk_level_summary": counter_dict(row["risk_level_summary"]),
        }
        for domain, row in sorted(domains.items())
    }


def summarize_target_areas(actions: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter()
    for action in actions:
        for target in action.get("target_areas") or ["unknown"]:
            counter[text(target) or "unknown"] += 1
    return counter_dict(counter)


def grouped_design_tracks(actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in actions:
        grouped[action["action_type"]].append(action)

    result: dict[str, dict[str, Any]] = {}
    for action_type in sorted(grouped):
        source_actions = sorted(grouped[action_type], key=lambda item: (-int(item.get("priority_score") or 0), item["case_id"]))
        profile = DESIGN_TRACK_PROFILES[action_type]
        root_counter = Counter()
        target_counter = Counter()
        domains = set()
        risks = Counter()
        for action in source_actions:
            root_counter.update(action.get("confirmed_root_causes") or [])
            target_counter.update(action.get("target_areas") or ["unknown"])
            risks[action.get("risk_level") or "unknown"] += 1
            domains.update(text(domain) or "unknown" for domain in action.get("expected_domains") or ["unknown"])
        result[action_type] = {
            "design_track_id": profile["design_track_id"],
            "action_type": action_type,
            "action_category": profile["action_category"],
            "priority_band": profile["priority_band"],
            "ready_action_count": len(source_actions),
            "case_count": len({action["case_id"] for action in source_actions}),
            "source_case_ids": sorted({action["case_id"] for action in source_actions}),
            "expected_domains": sorted(domains),
            "risk_level_summary": counter_dict(risks),
            "confirmed_root_cause_summary": counter_dict(root_counter),
            "target_area_summary": counter_dict(target_counter),
            "design_intent": profile["design_intent"],
            "allowed_next_step": profile["allowed_next_step"],
            "prohibited_now": profile["prohibited_now"],
            "acceptance_checks": profile["acceptance_checks"],
            "candidate_actions": source_actions,
        }
    return result


def case_design_matrix(actions: list[dict[str, Any]], contexts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in actions:
        grouped[action["case_id"]].append(action)
    rows = []
    for case_id in sorted(grouped):
        case_actions = sorted(grouped[case_id], key=lambda item: item["action_type"])
        context = contexts.get(case_id, {})
        rows.append({
            "case_id": case_id,
            "reviewed_at": context.get("reviewed_at") or "",
            "reviewer": context.get("reviewer") or "",
            "source_review_outcome": context.get("source_review_outcome") or "",
            "confirmed_root_causes": as_list(context.get("confirmed_root_causes")),
            "confirmed_follow_up_actions": as_list(context.get("confirmed_follow_up_actions")),
            "ready_action_count": len(case_actions),
            "action_types": [action["action_type"] for action in case_actions],
            "target_areas": sorted_unique([target for action in case_actions for target in action.get("target_areas") or []]),
            "expected_domains": sorted_unique([domain for action in case_actions for domain in action.get("expected_domains") or []]),
            "highest_priority_score": max(int(action.get("priority_score") or 0) for action in case_actions),
            "risk_levels": sorted_unique([action.get("risk_level") or "unknown" for action in case_actions]),
        })
    return rows


def build_assertions(
    gate: dict[str, Any],
    source_ready_count: int,
    actions: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
    gate_error_list: list[str],
) -> list[dict[str, Any]]:
    action_types = Counter(action["action_type"] for action in actions)
    return [
        {
            "name": "source_gate_open_for_design_planning",
            "status": "passed" if not gate_error_list else "failed",
            "details": gate,
        },
        {
            "name": "ready_action_count_matches_source_summary",
            "status": "passed" if len(actions) == source_ready_count and not excluded else "failed",
            "source_ready_action_candidates": source_ready_count,
            "design_ready_action_candidates": len(actions),
            "excluded_candidate_count": len(excluded),
        },
        {
            "name": "only_completed_valid_ready_actions_included",
            "status": "passed"
            if all(
                action["readiness"] == READINESS_READY
                and action["source_decision_status"] == SOURCE_DECISION_COMPLETED
                and action["validation_status"] == VALIDATION_VALID
                and not action["blocked_reason"]
                for action in actions
            )
            else "failed",
        },
        {
            "name": "design_tracks_are_known_and_grouped",
            "status": "passed" if set(action_types) <= set(DESIGN_TRACK_PROFILES) else "failed",
            "action_type_summary": counter_dict(action_types),
        },
        {
            "name": "implementation_is_not_authorized",
            "status": "passed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
        },
    ]


def build_planning_gate(gate_error_list: list[str], excluded: list[dict[str, Any]], actions: list[dict[str, Any]]) -> dict[str, Any]:
    blocker_reasons = list(gate_error_list)
    if excluded:
        blocker_reasons.append("candidate_validation_errors_present")
    if not actions and not blocker_reasons:
        blocker_reasons.append("no_ready_actions_available")
    design_allowed = not blocker_reasons and bool(actions)
    return {
        "status": "open_for_design_review" if design_allowed else "blocked_for_design_review",
        "design_planning_allowed": design_allowed,
        "implementation_allowed": False,
        "implementation_status": "not_started",
        "implementation_requires_future_explicit_approval": True,
        "blocked_reasons": blocker_reasons,
        "reason": (
            "Validated ready actions may be reviewed as design material only."
            if design_allowed
            else "Design review is blocked until source gate and candidate validation issues are resolved."
        ),
    }


def build_summary(
    gate: dict[str, Any],
    planning_gate: dict[str, Any],
    actions: list[dict[str, Any]],
    source_summary: dict[str, Any],
    excluded: list[dict[str, Any]],
) -> dict[str, Any]:
    action_counts = Counter(action["action_type"] for action in actions)
    risk_counts = Counter()
    for action in actions:
        risk_counts[action.get("risk_level") or "unknown"] += 1
    return {
        "status": "ready_for_design_review" if planning_gate["design_planning_allowed"] else "blocked_for_design_review",
        "design_only": True,
        "implementation_allowed": False,
        "promotion_candidates": source_summary.get("promotion_candidates", len({action["case_id"] for action in actions})),
        "ready_action_candidates": len(actions),
        "source_ready_action_candidates": source_summary.get("ready_action_candidates", 0),
        "excluded_ready_action_candidates": len(excluded),
        "ready_case_count": len({action["case_id"] for action in actions}),
        "pending_records_excluded": gate.get("pending_proposed_records", 0),
        "pending_records_are_not_design_tasks": True,
        "design_track_count": len(action_counts),
        "action_type_summary": counter_dict(action_counts),
        "confirmed_root_cause_summary": dict(sorted(as_dict(source_summary.get("confirmed_root_cause_summary")).items())),
        "risk_level_summary": counter_dict(risk_counts),
        "per_domain_summary": summarize_domains(actions),
        "target_area_summary": summarize_target_areas(actions),
    }


def build_report(
    promotion_report_path: Path = DEFAULT_PROMOTION_REPORT_PATH,
    export_pipeline_dry_run_report_path: Path = DEFAULT_EXPORT_PIPELINE_DRY_RUN_REPORT_PATH,
) -> dict[str, Any]:
    promotion_report = load_json(promotion_report_path)
    export_report = load_json(export_pipeline_dry_run_report_path)
    gate = source_gate(export_report)
    gate_error_list = gate_errors(gate)
    contexts = candidate_contexts(promotion_report)
    source_actions, excluded = collect_design_actions(promotion_report)
    if gate_error_list:
        excluded = excluded + [
            {
                "case_id": action["case_id"],
                "action_type": action["action_type"],
                "excluded_reasons": ["source_gate_not_open_for_design_review"],
            }
            for action in source_actions
        ]
        design_actions: list[dict[str, Any]] = []
    else:
        design_actions = source_actions
    source_summary = as_dict(promotion_report.get("summary"))
    planning = build_planning_gate(gate_error_list, excluded, design_actions)
    action_groups = grouped_design_tracks(design_actions)
    summary = build_summary(gate, planning, design_actions, source_summary, excluded)
    assertions = build_assertions(
        gate,
        int(source_summary.get("ready_action_candidates") or 0),
        design_actions,
        excluded,
        gate_error_list,
    )
    return {
        "version": VERSION,
        "schema_kind": "governed_ready_action_design_pack",
        "scope": "offline ready action design pack",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "promotion_dry_run_report": source_meta(promotion_report_path, promotion_report),
            "export_pipeline_dry_run_report": source_meta(export_pipeline_dry_run_report_path, export_report),
        },
        "source_gate": gate,
        "guardrails": DESIGN_ONLY_GUARDRAILS,
        "non_goals": NON_GOALS,
        "planning_gate": planning,
        "summary": summary,
        "action_groups": action_groups,
        "design_tracks": list(action_groups.values()),
        "case_design_matrix": case_design_matrix(design_actions, contexts),
        "excluded_scope": {
            "pending_records_excluded": gate.get("pending_proposed_records", 0),
            "pending_records_are_not_confirmed_tasks": True,
            "excluded_ready_action_candidates": excluded,
            "pending_case_policy": "Pending manual-review records remain outside this design pack.",
        },
        "traceability": {
            "source_case_ids": sorted({action["case_id"] for action in design_actions}),
            "design_action_ids": [action["design_action_id"] for action in design_actions],
            "source_reports": [str(promotion_report_path), str(export_pipeline_dry_run_report_path)],
        },
        "assertions": assertions,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    planning = report["planning_gate"]
    lines = [
        "# v0.4.7.9.0 Ready Action Design Pack",
        "",
        "本文件是 RAG grounding quality governance 的只读设计包，不是样本修补工具，也不是自动实施计划。",
        "",
        "## 总览",
        "",
        f"- 状态：`{summary['status']}`",
        f"- 进入设计包的 ready actions：{summary['ready_action_candidates']}",
        f"- 来源 promotion candidates：{summary['promotion_candidates']}",
        f"- 排除的 pending records：{summary['pending_records_excluded']}",
        f"- 设计轨道数量：{summary['design_track_count']}",
        f"- 实施是否允许：{planning['implementation_allowed']}",
        "",
        "## 设计轨道",
        "",
    ]
    for action_type, group in report["action_groups"].items():
        lines.extend([
            f"### {action_type}",
            "",
            f"- 数量：{group['ready_action_count']}",
            f"- 覆盖案例：{', '.join(group['source_case_ids'])}",
            f"- 设计意图：{group['design_intent']}",
            f"- 下一步允许：{group['allowed_next_step']}",
            f"- 当前禁止：{', '.join(group['prohibited_now'])}",
            "",
        ])
    lines.extend([
        "## 边界",
        "",
        "- 只读取既有 promotion dry-run 与 export pipeline dry-run 报告。",
        "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case 或主流程。",
        "- 31 个 pending records 只作为背景统计，不进入工程设计任务。",
        "- 后续若要实施任何代码或配置变更，需要另开版本、另做审议和测试计划。",
        "",
        "## 来源",
        "",
        f"- Promotion dry-run：`{report['inputs']['promotion_dry_run_report']['path']}`",
        f"- Export pipeline dry-run：`{report['inputs']['export_pipeline_dry_run_report']['path']}`",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build governed ready-action design pack.")
    parser.add_argument("--promotion-report", type=Path, default=DEFAULT_PROMOTION_REPORT_PATH)
    parser.add_argument("--export-pipeline-dry-run-report", type=Path, default=DEFAULT_EXPORT_PIPELINE_DRY_RUN_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.promotion_report, args.export_pipeline_dry_run_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Ready action design pack built: "
        f"{summary['status']}, "
        f"{summary['ready_action_candidates']} ready actions, "
        f"{summary['design_track_count']} design tracks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
