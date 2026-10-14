"""Build a small manual-review pilot batch.

This tool narrows the existing manual-review queue into a readable pilot
packet for human confirmation. It is advisory only: it does not write
reviewer decisions, does not import workbench rows, and does not mutate
retrieval, rerank, prompts, anchors, risk rules, eval cases, hidden seeds, or
the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VERSION = "0.4.7.8.15"

DEFAULT_PRESCREEN_PATH = Path("tests/manual_review_prescreen_report.json")
DEFAULT_WORKBENCH_PATH = Path("tests/evidence_manual_review_workbench.json")
DEFAULT_AI_SUGGESTION_PATH = Path("tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json")
DEFAULT_OUTPUT_PATH = Path("tests/manual_review_pilot_batch_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/manual_review_pilot_batch_v0.4.7.8.15.md")

MIN_PILOT_CASES = 3
MAX_PILOT_CASES = 5

GUARDRAILS = {
    "advisory_only": True,
    "writes_reviewer_decisions": "disallowed",
    "completed_manual_decision_generation": "disallowed",
    "reviewer_input_template_written": "disallowed",
    "workbench_import": "disallowed",
    "promotion_candidate_generation": "disallowed",
    "ready_action_candidate_generation": "disallowed",
    "rag_query_integration": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
}

USER_CONFIRMATION_OPTIONS = [
    {
        "option_code": "agree_confirm_diagnostic_issue",
        "plain_label": "同意诊断成立",
        "meaning": "你认为这个 case 的证据链确实存在报告指出的问题。",
    },
    {
        "option_code": "disagree_reject_diagnostic_issue",
        "plain_label": "不同意诊断成立",
        "meaning": "你认为现有证据足够，或诊断工具把问题说重了。",
    },
    {
        "option_code": "defer_need_more_information",
        "plain_label": "暂缓判断",
        "meaning": "你需要更多法律或证据上下文，暂时不把它写成人工结论。",
    },
]

ISSUE_PLAIN_LABELS = {
    "final_primary_gap": "最终证据缺少主要法律依据",
    "missing_primary_evidence": "主争点缺少证据",
    "core_missing_from_final_evidence": "核心条文没有进入最终证据",
    "scenario_core_gap": "案由核心条文可能缺失",
    "registry_core_review_needed": "场景登记的核心条文需要人工校准",
    "cross_domain_core_gap": "跨领域核心证据缺口",
    "definition_core_candidate": "可能用定义条款替代了规范条款",
    "answer_evidence_disconnect": "答案与证据链可能脱节",
    "insufficient_evidence_coverage": "证据覆盖不足",
    "low_final_coverage": "最终证据覆盖偏低",
    "evidence_chain_gap_candidate": "证据链缺口候选",
    "layer_coverage_regression": "候选到最终证据时覆盖下降",
    "final_selection_review_needed": "最终证据选择策略需要复核",
    "rerank_input_to_final_loss": "重排输入到最终证据发生证据流失",
    "primary_evidence_lost": "主要证据曾出现但最终丢失",
    "operative_evidence_lost": "义务或程序性证据曾出现但最终丢失",
    "liability_evidence_lost": "责任或后果证据曾出现但最终丢失",
    "scenario_core_lost": "场景核心证据曾出现但最终丢失",
    "anchor_dependency_review_needed": "证据覆盖过度依赖 anchor",
    "anchor_dependent_coverage": "anchor 对覆盖有明显补救作用",
    "anchor_masking_base_retrieval_gap": "anchor 可能掩盖基础检索薄弱",
    "anchor_supported_but_final_lost": "anchor 找回的证据未保留到最终证据",
    "base_retrieval_review_needed": "基础检索质量需要复核",
    "dense_retrieval_gap": "向量检索缺口",
    "sparse_retrieval_gap": "关键词检索缺口",
    "union_retrieval_gap": "基础合并检索仍有缺口",
    "metadata_or_chunking_review_candidate": "元数据、切分或查询覆盖需要复核",
    "zero_base_recall": "基础检索零召回",
    "no_union_gain": "合并检索没有明显增益",
}

ROOT_CAUSE_LABELS = {
    "primary_evidence_gap": "主要证据缺口",
    "scenario_core_scope": "场景核心条文范围需要校准",
    "final_evidence_selection_policy": "最终证据选择策略问题",
    "metadata_chunking_or_query_coverage": "元数据、切分或查询覆盖问题",
    "anchor_dependency_governance": "anchor 依赖治理问题",
    "high_risk_grounding_gap": "高风险场景 grounding 缺口",
    "functional_typing_metadata": "法律功能类型或元数据质量问题",
    "source_or_index_coverage": "来源或索引覆盖问题",
}

ACTION_LABELS = {
    "primary_evidence_fixture_candidate_review": "复核是否沉淀主要证据回归样本",
    "scenario_registry_core_article_review": "复核场景核心条文登记",
    "final_evidence_selection_policy_review": "复核最终证据选择策略",
    "metadata_chunking_or_query_coverage_review": "复核元数据、切分或查询覆盖",
    "anchor_dependency_governance_review": "复核 anchor 依赖治理",
    "high_risk_manual_grounding_review": "高风险 grounding 人工复核",
    "functional_typing_fixture_review": "复核法律功能类型样本",
    "source_index_coverage_review": "复核来源或索引覆盖",
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def compact_text(value: Any, limit: int = 360) -> str:
    text = " ".join(normalize_text(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def map_by_case(items: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in as_list(items):
        if not isinstance(item, dict):
            continue
        case_id = normalize_text(item.get("case_id") or item.get("id"))
        if case_id:
            result[case_id] = item
    return result


def label_items(values: Any, labels: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for value in as_list(values):
        code = normalize_text(value)
        if not code:
            continue
        rows.append({"code": code, "plain_label": labels.get(code, code)})
    return rows


def evidence_refs(items: Any, limit: int = 4) -> list[dict[str, Any]]:
    refs = []
    for item in as_list(items):
        if not isinstance(item, dict):
            continue
        refs.append(
            {
                "source": item.get("source") or item.get("law_name") or "",
                "article_no": item.get("article_no") or "",
                "section_no": item.get("section_no") or "",
                "citation": item.get("citation") or "",
                "functional_type": item.get("functional_type") or item.get("legal_functional_type") or "",
                "content_preview": compact_text(
                    item.get("content_preview")
                    or item.get("content")
                    or item.get("matched_content")
                    or item.get("citation")
                    or "",
                    limit=280,
                ),
            }
        )
        if len(refs) >= limit:
            break
    return refs


def derive_case_topic(case: dict[str, Any]) -> str:
    question = normalize_text(case.get("question"))
    notes = normalize_text(case.get("case_notes"))
    if notes:
        return compact_text(notes, 80)
    if not question:
        return "待人工确认的证据链复核 case"
    markers = ["某公司", "某平台", "某APP", "某企业", "公司", "平台", "APP"]
    for marker in markers:
        if marker in question:
            return compact_text(question, 90)
    return compact_text(question, 90)


def selection_score(case: dict[str, Any], has_ai_suggestion: bool) -> int:
    score = int(case.get("prescreen_score") or 0)
    score += int(case.get("priority_score") or 0)
    if case.get("needs_user_decision"):
        score += 10
    if case.get("risk_level") == "high":
        score += 8
    if case.get("prescreen_confidence") == "high":
        score += 8
    elif case.get("prescreen_confidence") == "medium":
        score += 3
    counts = case.get("evidence_context_counts") if isinstance(case.get("evidence_context_counts"), dict) else {}
    score += 6 * int(counts.get("missing_final_expected") or 0)
    score += 4 * int(counts.get("lost_evidence") or 0)
    score += 3 * int(counts.get("missing_scenario_core") or 0)
    issue_types = set(as_list(case.get("detected_issue_types")))
    if "answer_evidence_disconnect" in issue_types:
        score += 4
    if "definition_core_candidate" in issue_types:
        score += 3
    if has_ai_suggestion:
        score += 5
    return score


def why_selected(case: dict[str, Any], has_ai_suggestion: bool) -> list[str]:
    reasons = []
    if case.get("risk_level") == "high":
        reasons.append("高风险 case，错误证据链的业务影响更大。")
    if case.get("prescreen_confidence") == "high":
        reasons.append("预筛置信度为 high，适合作为首批人工复核样本。")
    counts = case.get("evidence_context_counts") if isinstance(case.get("evidence_context_counts"), dict) else {}
    missing_final = int(counts.get("missing_final_expected") or 0)
    lost = int(counts.get("lost_evidence") or 0)
    missing_core = int(counts.get("missing_scenario_core") or 0)
    if missing_final:
        reasons.append(f"最终证据缺少 {missing_final} 个预期主要条文。")
    if lost:
        reasons.append(f"有 {lost} 个条文曾在候选层出现但未进入最终 evidence_chain。")
    if missing_core:
        reasons.append(f"有 {missing_core} 个场景核心条文需要确认是否应进入证据链。")
    domains = as_list(case.get("expected_domains"))
    if len(domains) > 1:
        reasons.append("涉及多个法域，适合检查法域边界和证据覆盖。")
    if has_ai_suggestion:
        reasons.append("已有隔离的 AI 建议草稿，可作为参考，但仍需人工确认。")
    return reasons[:6]


def merge_ai_suggestion(ai_item: dict[str, Any]) -> dict[str, Any]:
    suggestion = ai_item.get("ai_review_suggestion") if isinstance(ai_item.get("ai_review_suggestion"), dict) else {}
    if not suggestion:
        return {
            "present": False,
            "advisory_only": True,
            "human_confirmation_required": True,
        }
    return {
        "present": True,
        "advisory_only": True,
        "human_confirmation_required": True,
        "advisory_decision": suggestion.get("decision") or "",
        "advisory_root_causes": label_items(suggestion.get("confirmed_root_causes"), ROOT_CAUSE_LABELS),
        "advisory_follow_up_actions": label_items(suggestion.get("confirmed_follow_up_actions"), ACTION_LABELS),
        "advisory_fixture_candidate": bool(suggestion.get("fixture_candidate")),
        "rationale": compact_text(suggestion.get("rationale"), 520),
        "notes": compact_text(suggestion.get("notes"), 320),
        "not_a_reviewer_decision": True,
    }


def build_confirmation_packet(
    case: dict[str, Any],
    workbench_item: dict[str, Any],
    ai_item: dict[str, Any],
) -> dict[str, Any]:
    evidence_context = workbench_item.get("evidence_context") if isinstance(workbench_item.get("evidence_context"), dict) else {}
    counts = case.get("evidence_context_counts") if isinstance(case.get("evidence_context_counts"), dict) else {}
    ai_suggestion = merge_ai_suggestion(ai_item)
    return {
        "case_id": case.get("case_id"),
        "rank": case.get("rank"),
        "selection_score": selection_score(case, ai_suggestion["present"]),
        "risk_level": case.get("risk_level") or "unknown",
        "expected_domains": as_list(case.get("expected_domains")),
        "case_topic": derive_case_topic(case),
        "question": case.get("question") or "",
        "original_llm_output_excerpt": compact_text(case.get("original_llm_output_excerpt"), 560),
        "risk_types_from_original_output": as_list(case.get("risk_types")),
        "recommended_actions_from_original_output": as_list(case.get("recommended_actions")),
        "why_selected": why_selected(case, ai_suggestion["present"]),
        "evidence_issue_summary": {
            "plain_summary": as_list(case.get("reason_summary")),
            "evidence_context_counts": {
                "missing_final_expected": int(counts.get("missing_final_expected") or 0),
                "missing_scenario_core": int(counts.get("missing_scenario_core") or 0),
                "lost_evidence": int(counts.get("lost_evidence") or 0),
                "final_evidence": int(counts.get("final_evidence") or 0),
            },
            "detected_issues": label_items(case.get("detected_issue_types"), ISSUE_PLAIN_LABELS),
            "issue_family_counts": case.get("issue_family_counts") or {},
        },
        "evidence_to_check": {
            "final_evidence": evidence_refs(
                evidence_context.get("final_evidence") or case.get("final_evidence_snapshot"),
                limit=5,
            ),
            "missing_expected_evidence": evidence_refs(evidence_context.get("missing_final_expected"), limit=5),
            "missing_scenario_core_evidence": evidence_refs(evidence_context.get("missing_scenario_core"), limit=5),
            "lost_before_final_evidence": evidence_refs(evidence_context.get("lost_evidence"), limit=5),
        },
        "prescreen_advice": {
            "category": case.get("prescreen_category") or "",
            "category_label": case.get("prescreen_category_label") or "",
            "prescreen_suggested_advisory_decision": case.get("prescreen_suggested_decision") or "",
            "confidence": case.get("prescreen_confidence") or "",
            "score": case.get("prescreen_score") or 0,
            "plain_language_guidance": case.get("plain_language_guidance") or "",
            "user_decision_reasons": as_list(case.get("user_decision_reasons")),
            "not_a_reviewer_decision": True,
        },
        "ai_suggestion": ai_suggestion,
        "reviewer_decision_needed": {
            "human_confirmation_required": True,
            "allowed_options": USER_CONFIRMATION_OPTIONS,
            "minimum_fields_for_later_workbench": [
                "reviewer",
                "reviewed_at",
                "decision",
                "rationale",
            ],
            "optional_or_conditional_fields": [
                "confirmed_root_causes",
                "rejected_root_causes",
                "confirmed_follow_up_actions",
                "proposed_change_targets",
                "fixture_candidate",
                "notes",
            ],
            "plain_instruction": (
                "本包只告诉你应该先看哪些 case；请在人工复核台中核对案由、原回答和证据后，"
                "再决定同意、不同意或暂缓。"
            ),
        },
        "fields_not_written": [
            "reviewer_input_template",
            "reviewer_decision",
            "decision_status=completed",
            "promotion_candidates",
            "ready_action_candidates",
        ],
    }


def candidate_sort_key(case: dict[str, Any], ai_by_case: dict[str, dict[str, Any]]) -> tuple[Any, ...]:
    cid = normalize_text(case.get("case_id"))
    has_ai = cid in ai_by_case
    return (
        -selection_score(case, has_ai),
        case.get("rank") or 9999,
        cid,
    )


def select_pilot_cases(
    cases: list[dict[str, Any]],
    ai_by_case: dict[str, dict[str, Any]],
    limit: int = MAX_PILOT_CASES,
) -> list[dict[str, Any]]:
    normalized_limit = max(MIN_PILOT_CASES, min(MAX_PILOT_CASES, int(limit or MAX_PILOT_CASES)))
    candidates = [
        case
        for case in cases
        if isinstance(case, dict)
        and normalize_text(case.get("case_id"))
        and case.get("needs_user_decision") is not False
    ]
    sorted_candidates = sorted(candidates, key=lambda item: candidate_sort_key(item, ai_by_case))

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    # First pass favors high confidence/high risk while keeping domain coverage visible.
    domain_counts: Counter[str] = Counter()
    for case in sorted_candidates:
        cid = normalize_text(case.get("case_id"))
        domains = [normalize_text(domain) for domain in as_list(case.get("expected_domains")) if normalize_text(domain)]
        rare_domain_bonus = any(domain_counts[domain] == 0 for domain in domains)
        if len(selected) < normalized_limit and (
            len(selected) < MIN_PILOT_CASES
            or rare_domain_bonus
            or case.get("prescreen_confidence") == "high"
        ):
            selected.append(case)
            selected_ids.add(cid)
            domain_counts.update(domains or ["unknown"])
        if len(selected) >= normalized_limit:
            break

    for case in sorted_candidates:
        if len(selected) >= normalized_limit:
            break
        cid = normalize_text(case.get("case_id"))
        if cid not in selected_ids:
            selected.append(case)
            selected_ids.add(cid)

    return selected[:normalized_limit]


def build_summary(pilot_cases: list[dict[str, Any]], source_total_cases: int) -> dict[str, Any]:
    domain_summary: dict[str, Counter[str]] = defaultdict(Counter)
    issue_counter: Counter[str] = Counter()
    risk_counter = Counter(case.get("risk_level") or "unknown" for case in pilot_cases)
    confidence_counter = Counter(
        case.get("prescreen_advice", {}).get("confidence") or "unknown" for case in pilot_cases
    )
    for case in pilot_cases:
        for domain in case.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["pilot_cases"] += 1
            domain_summary[domain][case.get("risk_level") or "unknown"] += 1
        for issue in case.get("evidence_issue_summary", {}).get("detected_issues") or []:
            issue_counter[issue["code"]] += 1

    return {
        "source_total_cases": source_total_cases,
        "pilot_case_count": len(pilot_cases),
        "human_confirmation_required_cases": sum(
            1 for case in pilot_cases if case["reviewer_decision_needed"]["human_confirmation_required"]
        ),
        "advisory_ai_suggestion_cases": sum(1 for case in pilot_cases if case["ai_suggestion"]["present"]),
        "completed_manual_decisions": 0,
        "promotion_candidates": 0,
        "ready_action_candidates": 0,
        "risk_level_summary": dict(sorted(risk_counter.items())),
        "prescreen_confidence_summary": dict(sorted(confidence_counter.items())),
        "issue_type_summary": dict(sorted(issue_counter.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
    }


def build_report(
    prescreen_path: Path = DEFAULT_PRESCREEN_PATH,
    workbench_path: Path = DEFAULT_WORKBENCH_PATH,
    ai_suggestion_path: Path = DEFAULT_AI_SUGGESTION_PATH,
    limit: int = MAX_PILOT_CASES,
) -> dict[str, Any]:
    prescreen = load_json(prescreen_path)
    workbench = load_json(workbench_path)
    ai_suggestion = load_json(ai_suggestion_path)

    prescreen_cases = [
        item for item in as_list(prescreen.get("cases") if isinstance(prescreen, dict) else []) if isinstance(item, dict)
    ]
    workbench_by_case = map_by_case(workbench.get("workbench_items") if isinstance(workbench, dict) else [])
    ai_by_case = map_by_case(ai_suggestion.get("workbench_items") if isinstance(ai_suggestion, dict) else [])

    selected = select_pilot_cases(prescreen_cases, ai_by_case, limit)
    pilot_cases = [
        build_confirmation_packet(case, workbench_by_case.get(normalize_text(case.get("case_id")), {}), ai_by_case.get(normalize_text(case.get("case_id")), {}))
        for case in selected
    ]

    return {
        "version": VERSION,
        "schema_kind": "advisory_pilot_packet",
        "contains_completed_manual_decisions": False,
        "advisory_packet_only": True,
        "scope": "manual review pilot batch packet",
        "inputs": {
            "prescreen_report": str(prescreen_path),
            "prescreen_report_version": prescreen.get("version") if isinstance(prescreen, dict) else None,
            "workbench": str(workbench_path),
            "workbench_version": workbench.get("version") if isinstance(workbench, dict) else None,
            "ai_suggestion_prefill": str(ai_suggestion_path),
            "ai_suggestion_prefill_version": ai_suggestion.get("version") if isinstance(ai_suggestion, dict) else None,
        },
        "selection_policy": {
            "min_pilot_cases": MIN_PILOT_CASES,
            "max_pilot_cases": MAX_PILOT_CASES,
            "requested_limit": limit,
            "signals_used": [
                "needs_user_decision",
                "risk_level",
                "prescreen_confidence",
                "prescreen_score",
                "priority_score",
                "missing_final_expected",
                "missing_scenario_core",
                "lost_evidence",
                "answer_evidence_disconnect",
                "definition_core_candidate",
                "expected_domains",
                "presence_of_isolated_ai_suggestion",
            ],
            "signals_not_used_as_final_decision": [
                "ai_suggestion.advisory_decision",
                "prescreen_advice.prescreen_suggested_advisory_decision",
                "rag_eval_passed",
                "fixture_candidate",
            ],
            "no_case_id_hardcoding": True,
        },
        "guardrails": GUARDRAILS,
        "summary": build_summary(pilot_cases, len(prescreen_cases)),
        "pilot_cases": pilot_cases,
        "next_step": (
            "Review these pilot cases in the visual workbench. Only after a real reviewer fills and exports completed "
            "decisions should the export pipeline dry run be used to determine whether governance can proceed."
        ),
    }


def markdown_evidence_list(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"**{title}**"]
    if not rows:
        return lines + ["- 无。"]
    for row in rows:
        citation = row.get("citation") or f"{row.get('source', '')} 第{row.get('article_no', '')}条"
        preview = compact_text(row.get("content_preview"), 150)
        functional_type = row.get("functional_type") or "unknown"
        lines.append(f"- {citation}（{functional_type}）：{preview}")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# v0.4.7.8.15 Manual Review Pilot Batch",
        "",
        "本报告是首批人工复核确认包，只用于帮助 reviewer 先看少量高优先级 case。它不是人工复核结论，"
        "也不会生成 completed decision、promotion candidate 或 ready action candidate。",
        "",
        "## 边界",
        "",
        "- 只读取既有 prescreen、workbench 和隔离 AI suggestion 报告。",
        "- AI suggestion 只作为参考，不写入 reviewer_input_template。",
        "- 不导入 workbench，不写 proposed decision schema，不改变 closeout gate。",
        "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。",
        "- 不接入 rag_query，不调用后端、Qdrant、LLM 或联网能力。",
        "",
        "## 摘要",
        "",
        f"- 来源待审 case：{summary['source_total_cases']}",
        f"- 本批试点 case：{summary['pilot_case_count']}",
        f"- 仍需人工确认：{summary['human_confirmation_required_cases']}",
        f"- 含隔离 AI 建议：{summary['advisory_ai_suggestion_cases']}",
        f"- completed manual decisions：{summary['completed_manual_decisions']}",
        f"- promotion candidates：{summary['promotion_candidates']}",
        f"- ready action candidates：{summary['ready_action_candidates']}",
        f"- gate：`{summary['gate_status']}`",
        "",
        "## 判断标准与填写口径",
        "",
        "- 先判断案由是否看得懂：这个 case 在问什么法律/合规问题，是否和证据里的法规领域一致。",
        "- 再看最终证据链：已有证据是否真的能支撑原回答中的风险、整改动作或法律结论。",
        "- 再看缺失/丢失证据：报告提示缺少的条文，是否确实是回答主问题必须看的依据。",
        "- AI 建议和预筛建议只能当旁边的参考纸条，不要原样粘贴成复核结论。",
        "- 不确定时可以选“暂缓判断”；暂缓比为了填满表格而猜一个结论更安全。",
        "- 后续只在 visual workbench 的决策页填写真实人工结论；本报告不产生可导入的人工结论。",
        "",
        "## 本批 case",
        "",
        "| case | 风险 | 置信度 | 案由/问题 | 为什么先看 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in report["pilot_cases"]:
        why = compact_text("；".join(case.get("why_selected") or []), 170)
        lines.append(
            f"| `{case['case_id']}` | {case['risk_level']} | "
            f"{case['prescreen_advice']['confidence']} | {compact_text(case['case_topic'], 110)} | {why} |"
        )

    lines.extend(["", "## 每案确认包", ""])
    for index, case in enumerate(report["pilot_cases"], start=1):
        issue_summary = case["evidence_issue_summary"]
        advice = case["prescreen_advice"]
        ai = case["ai_suggestion"]
        lines.extend(
            [
                f"### {index}. `{case['case_id']}`",
                "",
                f"- 案由线索：{case['case_topic']}",
                f"- 待审问题：{case['question']}",
                f"- 预筛建议：{advice['category_label']}，置信度 `{advice['confidence']}`，分数 `{advice['score']}`。",
                f"- 人工要决定：同意诊断成立、不同意诊断成立，或暂缓判断。",
                "",
                "**原 LLM 输出摘录**",
                "",
                f"> {compact_text(case['original_llm_output_excerpt'], 520)}",
                "",
                "**主要证据问题**",
            ]
        )
        for reason in issue_summary.get("plain_summary") or ["无明确摘要。"]:
            lines.append(f"- {reason}")
        counts = issue_summary["evidence_context_counts"]
        lines.extend(
            [
                f"- 缺最终主要证据：{counts['missing_final_expected']}；缺场景核心证据：{counts['missing_scenario_core']}；候选层到最终证据丢失：{counts['lost_evidence']}。",
                "",
            ]
        )
        evidence = case["evidence_to_check"]
        lines.extend(markdown_evidence_list("最终证据链中已有证据", evidence["final_evidence"]))
        lines.extend([""])
        lines.extend(markdown_evidence_list("报告提示缺失或丢失的证据", evidence["missing_expected_evidence"] + evidence["lost_before_final_evidence"]))
        lines.extend(["", "**AI 建议状态**"])
        if ai["present"]:
            roots = "；".join(item["plain_label"] for item in ai.get("advisory_root_causes") or []) or "无"
            actions = "；".join(item["plain_label"] for item in ai.get("advisory_follow_up_actions") or []) or "无"
            lines.extend(
                [
                    f"- AI 参考建议：`{ai.get('advisory_decision')}`，但它不是人工结论。",
                    f"- 建议根因：{roots}",
                    f"- 建议后续动作：{actions}",
                    "- 仍需人工确认后，才能在 workbench 中填写真实复核结论。",
                ]
            )
        else:
            lines.append("- 无隔离 AI 建议；请完全按证据和人工判断填写。")
        lines.append("")

    lines.extend(
        [
            "## 后续步骤",
            "",
            "1. 打开 visual workbench，按本报告的 3-5 个 case 顺序逐个核对。",
            "2. 对每个 case 先看案由、原 LLM 输出、最终证据链、缺失/丢失证据，再决定同意、不同意或暂缓。",
            "3. 只有真实人工填写并导出后，才运行 export pipeline dry run。",
            "4. dry run 通过前，不进入工程修复，不改 RAG 主流程。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a manual-review pilot batch packet.")
    parser.add_argument("--prescreen", type=Path, default=DEFAULT_PRESCREEN_PATH)
    parser.add_argument("--workbench", type=Path, default=DEFAULT_WORKBENCH_PATH)
    parser.add_argument("--ai-suggestion", type=Path, default=DEFAULT_AI_SUGGESTION_PATH)
    parser.add_argument("--limit", type=int, default=MAX_PILOT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        prescreen_path=args.prescreen,
        workbench_path=args.workbench,
        ai_suggestion_path=args.ai_suggestion,
        limit=args.limit,
    )
    write_json(args.output, report)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review pilot batch built: "
        f"{summary['pilot_case_count']} cases, "
        f"{summary['human_confirmation_required_cases']} require human confirmation, "
        f"{summary['advisory_ai_suggestion_cases']} with advisory AI suggestions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
