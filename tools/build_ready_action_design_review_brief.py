"""Build a read-only design review brief from the ready-action design pack.

The brief is a human review aid. It only reads the saved v0.4.7.9.0 design
pack, preserves its implementation block, and rewrites the five design tracks
as clearer review questions and exit criteria. It does not call RAG, contact a
backend, read Qdrant, use an LLM, or mutate retrieval, prompts, rules, fixtures,
scenario registry entries, eval cases, hidden seeds, anchors, or the main flow.
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


VERSION = "0.4.7.9.1"

DEFAULT_DESIGN_PACK_REPORT_PATH = legacy_report_path("ready_action_design_pack_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ready_action_design_review_brief_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ready_action_design_review_brief_v0.4.7.9.1.md")

SOURCE_SCHEMA_KIND = "governed_ready_action_design_pack"

PROHIBITED_KEY_NAMES = {
    "implementation_plan",
    "patch_plan",
    "files_to_change",
    "commands",
    "migration_steps",
    "ready_to_apply",
    "reviewer_input_template",
    "reviewer_decision",
    "workbench_items",
}

REQUIRED_SOURCE_GUARDRAILS = {
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

BRIEF_GUARDRAILS = {
    "brief_only": True,
    "source_design_pack_only": True,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "pending_records_to_tasks": "disallowed",
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

DOMAIN_DISPLAY_NAMES = {
    "数据合规": "数据合规",
    "市场秩序": "市场秩序",
}

TRACK_PROFILES = {
    "final_evidence_selection_policy_review": {
        "priority_order": 10,
        "priority_band": "P0",
        "display_name": "最终证据选择策略评审",
        "plain_language_name": "系统最后留下哪些证据",
        "review_focus": "确认关键法律条文是否在进入最终 evidence_chain 前被筛掉。",
        "why_this_matters": (
            "RAG 可能已经找到了重要条文，但最终答案只引用了次要证据。"
            "如果不先审这个方向，后续改样例或改规则都可能只是绕开问题。"
        ),
        "review_questions": [
            "关键条文是召回阶段没有出现，还是出现后没有进入最终证据链？",
            "答案中的风险结论是否依赖了最终证据链没有保留的条文？",
            "同一类问题是否需要统一的最终证据选择准入标准？",
        ],
        "decision_points": [
            "是否进入后续最终证据选择策略设计版本。",
            "是否需要先补一组只读对照报告，再讨论任何排序或选择规则。",
            "是否存在必须由法律复核人确认的条文优先级。",
        ],
        "entry_criteria": [
            "来源必须是 completed + valid 的人工复核记录。",
            "每个候选事项必须能追溯到 source case 与 design action id。",
            "当前只讨论设计说明和测试口径，不讨论代码补丁。",
        ],
        "exit_criteria": [
            "能说明问题发生在召回、最终选择还是场景法律范围。",
            "能列出后续实现前必须保护的回归检查。",
            "仍保持 implementation_allowed=false。",
        ],
        "future_validation_before_implementation": [
            "实现前先定义 before/after 对照报告。",
            "实现前先确认不会改 prompt、rerank、anchor 或 eval case。",
            "实现后必须跑目标单测和小集合评估，不能只看单案表现。",
        ],
    },
    "primary_evidence_fixture_candidate_review": {
        "priority_order": 20,
        "priority_band": "P0",
        "display_name": "主证据测试样例候选评审",
        "plain_language_name": "以后可能拿来做测试样例的材料",
        "review_focus": "确认哪些缺失证据适合作为未来测试样例候选，但现在不写入 eval。",
        "why_this_matters": (
            "fixture 可以帮助系统长期回归检查，但未经审议直接写入样例，"
            "会把当前诊断变成针对少数 case 的硬补丁。"
        ),
        "review_questions": [
            "候选证据是否真的是主争点所需证据，而不是补充性材料？",
            "候选材料是否有清楚的来源 case、法律领域和复核理由？",
            "它更适合作为测试样例、知识入库候选，还是人工复核备注？",
        ],
        "decision_points": [
            "是否进入后续 fixture 候选池设计版本。",
            "是否需要法律复核人先确认条文与争点的对应关系。",
            "是否需要把候选按领域和主争点分层。",
        ],
        "entry_criteria": [
            "只纳入已经 valid 的 pilot decisions。",
            "候选不得直接进入 eval case 或 golden fixture。",
            "必须保留 source case 与 source design action id。",
        ],
        "exit_criteria": [
            "能解释每个候选为什么是主证据，而不是次要证据。",
            "能区分 fixture 候选、知识库候选和场景清单候选。",
            "仍不产生自动写入样例的授权。",
        ],
        "future_validation_before_implementation": [
            "实现前先新增候选池验收测试。",
            "实现前先定义人工批准字段和回滚方式。",
            "实现后必须证明没有修改现有 eval case。",
        ],
    },
    "high_risk_manual_grounding_review": {
        "priority_order": 30,
        "priority_band": "P0",
        "display_name": "高风险结论证据支撑评审",
        "plain_language_name": "高风险判断有没有证据托住",
        "review_focus": "核对风险类型、整改动作和结论是否都有 evidence_chain 支撑。",
        "why_this_matters": (
            "企业风控报告里，高风险结论最容易影响决策。"
            "如果结论没有证据支撑，报告看起来完整但可信度会下降。"
        ),
        "review_questions": [
            "答案中的高风险结论对应了哪些具体证据？",
            "整改动作是否能从证据链推出，还是只是模型自行补充？",
            "是否需要人工标注哪些结论必须有强证据才能输出？",
        ],
        "decision_points": [
            "是否进入后续高风险 grounding 复核队列设计。",
            "是否需要把风险类型、整改动作、法律后果拆开验收。",
            "是否有结论需要先降级为人工复核提示。",
        ],
        "entry_criteria": [
            "只处理已经确认有 high_risk_grounding_gap 的 valid case。",
            "只审证据支撑关系，不改风险规则或答案策略。",
            "必须保留来源 case 和对应候选动作。",
        ],
        "exit_criteria": [
            "能指出风险类型、整改动作、结论三者各自的证据要求。",
            "能区分证据不足、措辞过强和法律结论缺失。",
            "仍不宣称高风险输出质量已经提升。",
        ],
        "future_validation_before_implementation": [
            "实现前先定义高风险结论的最小证据门槛。",
            "实现前先准备人工复核样例和拒绝样例。",
            "实现后必须跑风险报告和证据链一致性检查。",
        ],
    },
    "scenario_registry_core_article_review": {
        "priority_order": 40,
        "priority_band": "P1",
        "display_name": "场景核心条文范围评审",
        "plain_language_name": "场景应该看哪些核心法律依据",
        "review_focus": "确认 scenario registry 的核心条文范围是否需要人工复核，但现在不修改 registry。",
        "why_this_matters": (
            "场景清单决定系统认为某类问题应优先看哪些法律依据。"
            "这个方向很重要，但应先分清是清单范围问题、召回问题还是最终选择问题。"
        ),
        "review_questions": [
            "缺失条文是否属于该场景的核心依据，还是只是补充依据？",
            "当前 case 的问题是否真的代表一个通用场景范围缺口？",
            "是否需要法律复核人确认核心条文清单的边界？",
        ],
        "decision_points": [
            "是否进入后续 scenario registry 范围评审版本。",
            "是否需要先做条文范围清单，不直接改配置。",
            "是否有跨领域场景需要拆分。",
        ],
        "entry_criteria": [
            "来源必须是 valid pilot decisions。",
            "不得把单案缺失直接写成 registry 修改。",
            "不得修改 expected evidence、anchor 或 eval case。",
        ],
        "exit_criteria": [
            "能区分场景范围缺口和证据选择缺口。",
            "能列出需人工确认的核心条文范围问题。",
            "仍不修改 scenario registry。",
        ],
        "future_validation_before_implementation": [
            "实现前先有法律复核后的范围清单。",
            "实现前先定义 registry 变更的回归测试。",
            "实现后必须验证不会污染其他法域或场景。",
        ],
    },
    "functional_typing_fixture_review": {
        "priority_order": 50,
        "priority_band": "P1",
        "display_name": "法律功能类型样例评审",
        "plain_language_name": "条文功能标签是否值得补样例",
        "review_focus": "确认 legal functional typing 的样例候选是否需要后续评审。",
        "why_this_matters": (
            "legal functional typing 是 RAG 识别定义、义务、责任、程序等条文功能的基础设施。"
            "但本轮只有一个候选，应作为附属评审，不抢 P0。"
        ),
        "review_questions": [
            "候选条文的功能类型是否明确，例如义务、责任、程序或定义？",
            "这个候选是否能帮助未来减少定义条款替代规范条款的问题？",
            "是否需要先补人工标签规范，再考虑 golden fixture？",
        ],
        "decision_points": [
            "是否进入后续 functional typing fixture 评审版本。",
            "是否需要新增人工标签解释，而不是直接改 config。",
            "是否应等待更多 case 后再形成通用样例。",
        ],
        "entry_criteria": [
            "只把它作为候选，不写入 golden fixture。",
            "必须保留来源 case 和复核理由。",
            "不得修改 functional type config。",
        ],
        "exit_criteria": [
            "能说明候选条文的功能类型和争点价值。",
            "能决定是否需要更多样本再进入实现。",
            "仍不改配置或测试样例。",
        ],
        "future_validation_before_implementation": [
            "实现前先定义标签验收标准。",
            "实现前先补测试，防止定义条款误替代规范条款。",
            "实现后必须跑 typing fixture 检查。",
        ],
    },
}

GLOSSARY = {
    "ready action candidates": "已具备进入设计评审条件的候选事项，不代表已经批准执行。",
    "design track": "评审方向，用来把类似问题放在一起讨论。",
    "grounding": "答案中的结论、风险和整改建议是否被证据链支撑。",
    "fixture": "以后可能作为测试样例或回归检查材料的候选，不等于已经写入测试。",
    "scenario registry": "场景与核心法律依据清单，用来帮助系统知道某类问题应关注哪些法律依据。",
    "planning gate": "治理门禁；本轮只允许进入设计评审，不允许动手实现。",
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


def normalize_domain(value: Any) -> str:
    raw = text(value)
    return DOMAIN_DISPLAY_NAMES.get(raw, raw or "unknown")


def counter_dict(values: list[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "scope": data.get("scope"),
        "schema_kind": data.get("schema_kind"),
    }


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def source_blockers(design_pack: dict[str, Any]) -> list[str]:
    if not design_pack:
        return ["missing_or_invalid_design_pack_report"]

    summary = as_dict(design_pack.get("summary"))
    planning_gate = as_dict(design_pack.get("planning_gate"))
    guardrails = as_dict(design_pack.get("guardrails"))
    excluded_scope = as_dict(design_pack.get("excluded_scope"))
    assertions = as_list(design_pack.get("assertions"))
    blockers: list[str] = []

    if design_pack.get("schema_kind") != SOURCE_SCHEMA_KIND:
        blockers.append("source_schema_kind_not_ready_action_design_pack")
    if summary.get("status") != "ready_for_design_review":
        blockers.append("source_summary_not_ready_for_design_review")
    if summary.get("design_only") is not True:
        blockers.append("source_summary_not_design_only")
    if summary.get("implementation_allowed") is not False:
        blockers.append("source_summary_implementation_not_blocked")
    if planning_gate.get("status") != "open_for_design_review":
        blockers.append("source_planning_gate_not_open_for_design_review")
    if planning_gate.get("design_planning_allowed") is not True:
        blockers.append("source_design_planning_not_allowed")
    if planning_gate.get("implementation_allowed") is not False:
        blockers.append("source_planning_gate_implementation_not_blocked")
    if planning_gate.get("implementation_status") != "not_started":
        blockers.append("source_implementation_status_not_not_started")
    if planning_gate.get("implementation_requires_future_explicit_approval") is not True:
        blockers.append("source_missing_future_explicit_approval")
    if summary.get("pending_records_are_not_design_tasks") is not True:
        blockers.append("pending_records_not_marked_as_excluded_from_tasks")
    if excluded_scope.get("pending_records_are_not_confirmed_tasks") is not True:
        blockers.append("excluded_scope_pending_policy_missing")

    for key, expected in REQUIRED_SOURCE_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            blockers.append(f"source_guardrail_mismatch:{key}")

    if not assertions:
        blockers.append("source_assertions_missing")
    elif any(as_dict(item).get("status") != "passed" for item in assertions):
        blockers.append("source_assertions_not_all_passed")

    action_groups = as_dict(design_pack.get("action_groups"))
    if not action_groups:
        blockers.append("source_action_groups_missing")

    unknown_tracks = sorted(action_type for action_type in action_groups if action_type not in TRACK_PROFILES)
    for action_type in unknown_tracks:
        blockers.append(f"unknown_design_track:{action_type}")

    for action_type, group in action_groups.items():
        for candidate in as_list(as_dict(group).get("candidate_actions")):
            action = as_dict(candidate)
            if action.get("readiness") != "ready_from_valid_decision":
                blockers.append(f"candidate_not_ready:{text(action.get('design_action_id')) or action_type}")
            if action.get("source_decision_status") != "completed":
                blockers.append(f"candidate_source_not_completed:{text(action.get('design_action_id')) or action_type}")
            if action.get("validation_status") != "valid":
                blockers.append(f"candidate_validation_not_valid:{text(action.get('design_action_id')) or action_type}")
            if text(action.get("blocked_reason")):
                blockers.append(f"candidate_blocked_reason_present:{text(action.get('design_action_id')) or action_type}")

    return blockers


def track_sort_key(item: tuple[str, dict[str, Any]]) -> tuple[int, int, int, str]:
    action_type, group = item
    profile = TRACK_PROFILES.get(action_type, {})
    band = text(as_dict(group).get("priority_band") or profile.get("priority_band"))
    band_order = {"P0": 0, "P1": 1, "P2": 2}.get(band, 9)
    profile_order = int(profile.get("priority_order", 999))
    ready_count = int(as_dict(group).get("ready_action_count") or 0)
    return (band_order, profile_order, -ready_count, action_type)


def candidate_action_ids(group: dict[str, Any]) -> list[str]:
    ids = []
    for item in as_list(group.get("candidate_actions")):
        design_action_id = text(as_dict(item).get("design_action_id"))
        if design_action_id:
            ids.append(design_action_id)
    return ids


def build_track_brief(action_type: str, group: dict[str, Any], source_reports: list[Any]) -> dict[str, Any]:
    profile = TRACK_PROFILES[action_type]
    expected_domains = [normalize_domain(domain) for domain in as_list(group.get("expected_domains"))]
    source_case_ids = sorted(text(case_id) for case_id in as_list(group.get("source_case_ids")) if text(case_id))
    design_action_ids = candidate_action_ids(group)
    candidate_priorities = [
        int(as_dict(candidate).get("priority_score") or 0)
        for candidate in as_list(group.get("candidate_actions"))
        if as_dict(candidate).get("priority_score") is not None
    ]
    return {
        "design_track_id": group.get("design_track_id") or action_type,
        "action_type": action_type,
        "priority_band": group.get("priority_band") or profile["priority_band"],
        "priority_order": profile["priority_order"],
        "display_name": profile["display_name"],
        "plain_language_name": profile["plain_language_name"],
        "review_focus": profile["review_focus"],
        "why_this_matters": profile["why_this_matters"],
        "current_scope": {
            "ready_for_design_review_candidates": group.get("ready_action_count", 0),
            "source_case_count": group.get("case_count", len(source_case_ids)),
            "source_case_ids": source_case_ids,
            "expected_domains": expected_domains,
            "highest_source_priority_score": max(candidate_priorities) if candidate_priorities else 0,
            "risk_level_summary": as_dict(group.get("risk_level_summary")),
            "confirmed_root_cause_summary": as_dict(group.get("confirmed_root_cause_summary")),
            "target_area_summary": as_dict(group.get("target_area_summary")),
        },
        "review_questions": profile["review_questions"],
        "decision_points": profile["decision_points"],
        "entry_criteria": profile["entry_criteria"],
        "exit_criteria": profile["exit_criteria"],
        "prohibited_now": as_list(group.get("prohibited_now")),
        "future_validation_before_implementation": profile["future_validation_before_implementation"],
        "what_this_does_not_mean": [
            "不是已批准的代码修改。",
            "不是 eval case、fixture、scenario registry 或规则变更。",
            "不是对 31 个 pending records 的人工复核结论。",
        ],
        "traceability": {
            "source_case_ids": source_case_ids,
            "design_action_ids": design_action_ids,
            "source_reports": [text(item) for item in source_reports if text(item)],
        },
    }


def build_summary(design_pack: dict[str, Any], blockers: list[str], track_briefs: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = as_dict(design_pack.get("summary"))
    priority_counts = counter_dict([text(track.get("priority_band")) for track in track_briefs])
    return {
        "status": "ready_for_human_design_review" if not blockers else "blocked_for_human_design_review",
        "source_design_pack_status": source_summary.get("status"),
        "source_design_pack_version": design_pack.get("version"),
        "promotion_candidates": source_summary.get("promotion_candidates", 0),
        "ready_for_design_review_candidates": source_summary.get("ready_action_candidates", 0) if not blockers else 0,
        "source_ready_action_candidates": source_summary.get("source_ready_action_candidates", 0),
        "ready_case_count": source_summary.get("ready_case_count", 0) if not blockers else 0,
        "design_track_count": len(track_briefs),
        "priority_band_summary": priority_counts,
        "pending_records_excluded": source_summary.get("pending_records_excluded", 0),
        "pending_records_are_not_tasks": True,
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "requires_future_explicit_approval": True,
        "review_order": [track["action_type"] for track in track_briefs],
        "blocker_count": len(blockers),
    }


def build_assertions(design_pack: dict[str, Any], blockers: list[str], track_briefs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_traceability = as_dict(design_pack.get("traceability"))
    source_action_ids = set(text(item) for item in as_list(source_traceability.get("design_action_ids")) if text(item))
    brief_action_ids = {
        text(item)
        for track in track_briefs
        for item in as_list(as_dict(track.get("traceability")).get("design_action_ids"))
        if text(item)
    }
    source_summary = as_dict(design_pack.get("summary"))
    track_count_matches = len(track_briefs) == int(source_summary.get("design_track_count") or 0) if not blockers else not track_briefs
    return [
        {
            "name": "source_design_pack_ready_for_brief",
            "status": "passed" if not blockers else "failed",
            "blockers": blockers,
        },
        {
            "name": "implementation_is_not_authorized",
            "status": "passed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
        },
        {
            "name": "pending_records_are_excluded_from_tasks",
            "status": "passed" if as_dict(design_pack.get("summary")).get("pending_records_are_not_design_tasks") is True else "failed",
            "pending_records_excluded": as_dict(design_pack.get("summary")).get("pending_records_excluded", 0),
        },
        {
            "name": "track_count_matches_source_design_pack",
            "status": "passed" if track_count_matches else "failed",
            "source_design_track_count": source_summary.get("design_track_count", 0),
            "brief_track_count": len(track_briefs),
        },
        {
            "name": "traceability_ids_come_from_source_pack",
            "status": "passed" if brief_action_ids <= source_action_ids else "failed",
            "source_design_action_count": len(source_action_ids),
            "brief_design_action_count": len(brief_action_ids),
            "unexpected_design_action_ids": sorted(brief_action_ids - source_action_ids),
        },
    ]


def build_report(design_pack_report_path: Path = DEFAULT_DESIGN_PACK_REPORT_PATH) -> dict[str, Any]:
    design_pack = load_json(design_pack_report_path)
    blockers = source_blockers(design_pack)
    source_traceability = as_dict(design_pack.get("traceability"))
    source_reports = as_list(source_traceability.get("source_reports"))
    action_groups = as_dict(design_pack.get("action_groups"))
    track_briefs = []
    if not blockers:
        for action_type, group in sorted(action_groups.items(), key=track_sort_key):
            track_briefs.append(build_track_brief(action_type, as_dict(group), source_reports))

    summary = build_summary(design_pack, blockers, track_briefs)
    brief_gate = {
        "status": "open_for_design_review_brief" if not blockers else "blocked_for_design_review_brief",
        "human_design_review_allowed": not blockers,
        "implementation_allowed": False,
        "implementation_status": "not_started",
        "implementation_requires_future_explicit_approval": True,
        "blockers": blockers,
        "reason": (
            "The source design pack is ready; this brief may be used for human design review only."
            if not blockers
            else "The source design pack is not safe to summarize as a review brief."
        ),
    }
    excluded_scope = as_dict(design_pack.get("excluded_scope"))
    report = {
        "version": VERSION,
        "schema_kind": "ready_action_design_review_brief",
        "scope": "offline ready action design review brief",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ready_action_design_pack_report": source_meta(design_pack_report_path, design_pack),
        },
        "source_design_pack": {
            "version": design_pack.get("version"),
            "schema_kind": design_pack.get("schema_kind"),
            "scope": design_pack.get("scope"),
            "summary_status": as_dict(design_pack.get("summary")).get("status"),
            "planning_gate_status": as_dict(design_pack.get("planning_gate")).get("status"),
        },
        "guardrails": {
            **BRIEF_GUARDRAILS,
            "inherited_source_guardrails_checked": True,
        },
        "brief_gate": brief_gate,
        "summary": summary,
        "track_briefs": track_briefs,
        "excluded_scope": {
            "pending_records_excluded": excluded_scope.get(
                "pending_records_excluded",
                as_dict(design_pack.get("summary")).get("pending_records_excluded", 0),
            ),
            "pending_records_policy": "Pending records are background only and must not enter this brief as tasks.",
            "excluded_ready_action_candidates": len(as_list(excluded_scope.get("excluded_ready_action_candidates"))),
            "source_pending_policy": excluded_scope.get("pending_case_policy", ""),
        },
        "traceability": {
            "source_case_ids": as_list(source_traceability.get("source_case_ids")),
            "design_action_ids": [
                action_id
                for track in track_briefs
                for action_id in as_list(as_dict(track.get("traceability")).get("design_action_ids"))
            ],
            "source_reports": [str(design_pack_report_path), *[text(item) for item in source_reports if text(item)]],
        },
        "glossary": GLOSSARY,
        "assertions": build_assertions(design_pack, blockers, track_briefs),
    }
    forbidden_keys = []
    for node in walk_dicts(report):
        forbidden_keys.extend(sorted(PROHIBITED_KEY_NAMES & set(node)))
    if forbidden_keys:
        report["brief_gate"]["status"] = "blocked_for_design_review_brief"
        report["brief_gate"]["human_design_review_allowed"] = False
        report["brief_gate"]["blockers"] = sorted(set(report["brief_gate"]["blockers"] + ["forbidden_output_key_present"]))
        report["summary"]["status"] = "blocked_for_human_design_review"
        report["summary"]["blocker_count"] = len(report["brief_gate"]["blockers"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    brief_gate = as_dict(report.get("brief_gate"))
    lines = [
        "# v0.4.7.9.1 Ready Action Design Review Brief",
        "",
        "本文件是给人工评审使用的简报。它把上一版设计包中的候选事项翻译成更容易审阅的评审方向、问题清单和退出标准。",
        "",
        "它不修 RAG，不改检索、rerank、prompt、hidden seed、anchor、risk supplement、scenario registry、eval case、fixture 或主流程。",
        "",
        "## 总览",
        "",
        f"- 状态：`{summary.get('status')}`",
        f"- 来源设计包版本：`{summary.get('source_design_pack_version')}`",
        f"- 可进入设计评审的候选事项：{summary.get('ready_for_design_review_candidates')}",
        f"- 覆盖案例数：{summary.get('ready_case_count')}",
        f"- 评审方向数：{summary.get('design_track_count')}",
        f"- 被排除的 pending records：{summary.get('pending_records_excluded')}",
        f"- 是否允许实现：{brief_gate.get('implementation_allowed')}",
        "",
        "## 推荐评审顺序",
        "",
        "| 顺序 | 优先级 | 评审方向 | 覆盖候选 | 覆盖案例 | 通俗解释 |",
        "|---|---|---|---:|---:|---|",
    ]
    for index, track in enumerate(as_list(report.get("track_briefs")), start=1):
        scope = as_dict(track.get("current_scope"))
        lines.append(
            f"| {index} | {track.get('priority_band')} | {track.get('display_name')} | "
            f"{scope.get('ready_for_design_review_candidates')} | {scope.get('source_case_count')} | "
            f"{track.get('plain_language_name')} |"
        )

    lines.extend([
        "",
        "## 逐项评审",
        "",
    ])
    for track in as_list(report.get("track_briefs")):
        scope = as_dict(track.get("current_scope"))
        lines.extend([
            f"### {track.get('display_name')}",
            "",
            f"- 优先级：`{track.get('priority_band')}`",
            f"- 覆盖候选事项：{scope.get('ready_for_design_review_candidates')}",
            f"- 覆盖案例：{', '.join(as_list(scope.get('source_case_ids')))}",
            f"- 关注点：{track.get('review_focus')}",
            f"- 为什么重要：{track.get('why_this_matters')}",
            "",
            "需要问的问题：",
        ])
        for question in as_list(track.get("review_questions")):
            lines.append(f"- {question}")
        lines.extend([
            "",
            "当前禁止：",
        ])
        for item in as_list(track.get("prohibited_now")):
            lines.append(f"- `{item}`")
        lines.extend([
            "",
            "进入后续实现前还需要：",
        ])
        for item in as_list(track.get("future_validation_before_implementation")):
            lines.append(f"- {item}")
        lines.append("")

    lines.extend([
        "## 术语",
        "",
    ])
    for key, value in as_dict(report.get("glossary")).items():
        lines.append(f"- `{key}`：{value}")

    excluded_scope = as_dict(report.get("excluded_scope"))
    lines.extend([
        "",
        "## 边界",
        "",
        "- 本简报只读取上一版 ready action design pack。",
        "- 31 个 pending records 只作为背景统计，不进入评审方向，也不是工程任务。",
        "- 所有后续代码、配置或数据变更都必须另开版本、重新确认边界并补测试。",
        f"- Pending policy：{excluded_scope.get('pending_records_policy')}",
        "",
        "## 来源",
        "",
        f"- Source design pack：`{report['inputs']['ready_action_design_pack_report']['path']}`",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a ready-action design review brief.")
    parser.add_argument("--design-pack-report", type=Path, default=DEFAULT_DESIGN_PACK_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.design_pack_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Ready action design review brief built: "
        f"{summary['status']}, "
        f"{summary['ready_for_design_review_candidates']} review candidates, "
        f"{summary['design_track_count']} tracks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
