"""Build advisory review assistance for the manual-review pilot cases.

The output helps a human reviewer read the first pilot cases. It does not
write reviewer decisions, does not import workbench rows, and does not mutate
retrieval, rerank, prompts, anchors, risk rules, eval cases, hidden seeds, or
the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.7.8.17"

DEFAULT_PILOT_BATCH_PATH = Path("tests/manual_review_pilot_batch_report.json")
DEFAULT_WORKBENCH_PATH = Path("tests/evidence_manual_review_workbench.json")
DEFAULT_RAG_EVAL_REPORT_PATH = Path("tests/rag_eval_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/manual_review_pilot_case_review_assist_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/manual_review_pilot_case_review_assist_v0.4.7.8.17.md")

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

DANGEROUS_OUTPUT_KEYS = {
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
}

SUPPORTED_SIGNALS = [
    {
        "code": "primary_issue_missing_evidence",
        "label": "主争点缺证据",
        "plain_description": "原回答涉及的主要风险、责任后果或整改动作，最终 evidence_chain 没有保留对应的主要条文。",
    },
    {
        "code": "scenario_core_gap",
        "label": "案由核心条文缺口",
        "plain_description": "场景登记认为应覆盖的核心条文没有进入最终证据链，需要判断是 registry 范围偏宽还是 final evidence 漏选。",
    },
    {
        "code": "final_selection_loss",
        "label": "候选证据进入最终证据时流失",
        "plain_description": "条文曾在候选、anchor 或 rerank input 阶段出现，但最终没有被选进 evidence_chain。",
    },
    {
        "code": "answer_evidence_disconnect",
        "label": "答案与证据链可能脱节",
        "plain_description": "原 LLM 输出中的风险类型、整改动作或结论，未被现有 evidence_chain 直接托住。",
    },
    {
        "code": "definition_substitution_review",
        "label": "定义条款替代规范条款复核",
        "plain_description": "命中的条文可能偏定义性，缺少义务、责任、程序或后果条款，需要人工看是否足够。",
    },
    {
        "code": "retrieval_stability_review",
        "label": "基础检索或 anchor 依赖稳定性复核",
        "plain_description": "基础检索、元数据、切分或 anchor 依赖信号提示：法律库扩大后召回稳定性可能不足。",
    },
]

ISSUE_CODE_TO_SIGNAL = {
    "final_primary_gap": "primary_issue_missing_evidence",
    "missing_primary_evidence": "primary_issue_missing_evidence",
    "liability_evidence_lost": "primary_issue_missing_evidence",
    "core_missing_from_final_evidence": "scenario_core_gap",
    "scenario_core_gap": "scenario_core_gap",
    "cross_domain_core_gap": "scenario_core_gap",
    "registry_core_review_needed": "scenario_core_gap",
    "scenario_core_lost": "scenario_core_gap",
    "layer_coverage_regression": "final_selection_loss",
    "primary_evidence_lost": "final_selection_loss",
    "rerank_input_to_final_loss": "final_selection_loss",
    "anchor_supported_but_final_lost": "final_selection_loss",
    "answer_evidence_disconnect": "answer_evidence_disconnect",
    "definition_core_candidate": "definition_substitution_review",
    "metadata_or_chunking_review_candidate": "retrieval_stability_review",
    "base_retrieval_review_needed": "retrieval_stability_review",
    "anchor_dependency_review_needed": "retrieval_stability_review",
    "anchor_dependent_coverage": "retrieval_stability_review",
    "anchor_masking_base_retrieval_gap": "retrieval_stability_review",
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
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [value]


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def text(value: Any) -> str:
    return str(value or "").strip()


def compact(value: Any, limit: int = 320) -> str:
    value_text = " ".join(text(value).split())
    if len(value_text) <= limit:
        return value_text
    return value_text[: limit - 1].rstrip() + "..."


def readable_item(value: Any) -> str:
    if isinstance(value, dict):
        label = text(value.get("plain_label") or value.get("label") or value.get("code"))
        code = text(value.get("code"))
        display = f"{label}（{code}）" if label and code and label != code else label or code
        return plain_display_text(display)
    return plain_display_text(text(value))


def plain_display_text(value: str) -> str:
    replacements = {
        "grounding": "证据支撑",
        "final evidence": "最终证据",
        "evidence_chain": "证据链",
        "registry": "场景登记",
    }
    result = value
    for source, target in replacements.items():
        result = result.replace(source, target)
    return result


def readable_list(values: Any, limit: int | None = None) -> list[str]:
    items = [readable_item(item) for item in as_list(values)]
    items = [item for item in items if item]
    return items[:limit] if limit is not None else items


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "scope": data.get("scope"),
        "schema_kind": data.get("schema_kind"),
    }


def by_case(items: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in as_list(items):
        if not isinstance(item, dict):
            continue
        case_id = text(item.get("case_id") or item.get("id"))
        if case_id:
            result[case_id] = item
    return result


def rag_reports_by_case(rag_eval_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return by_case(rag_eval_report.get("reports"))


def evidence_items(source: dict[str, Any], *keys: str, limit: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in keys:
        for item in as_list(source.get(key)):
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "source": item.get("source") or item.get("law_name") or "",
                    "article_no": item.get("article_no") or item.get("article") or "",
                    "section_no": item.get("section_no") or "",
                    "citation": item.get("citation") or "",
                    "functional_type": item.get("functional_type") or item.get("legal_functional_type") or "",
                    "content_preview": compact(
                        item.get("content_preview")
                        or item.get("content")
                        or item.get("matched_content")
                        or item.get("citation")
                        or "",
                        260,
                    ),
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def count_items(source: dict[str, Any], *keys: str) -> int:
    return sum(len(as_list(source.get(key))) for key in keys)


def issue_codes(case: dict[str, Any], workbench_item: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    issue_summary = as_dict(case.get("evidence_issue_summary"))
    for issue in as_list(issue_summary.get("detected_issues")):
        if isinstance(issue, dict):
            codes.append(text(issue.get("code")))
        else:
            codes.append(text(issue))
    codes.extend(text(item) for item in as_list(workbench_item.get("issue_types")))
    return sorted({code for code in codes if code})


def evidence_counts(case: dict[str, Any], workbench_item: dict[str, Any]) -> dict[str, int]:
    issue_summary = as_dict(case.get("evidence_issue_summary"))
    summary_counts = as_dict(issue_summary.get("evidence_context_counts"))
    workbench_counts = as_dict(workbench_item.get("evidence_context_counts"))
    evidence_to_check = as_dict(case.get("evidence_to_check"))
    evidence_context = as_dict(workbench_item.get("evidence_context"))
    return {
        "final_evidence": int(
            summary_counts.get("final_evidence")
            or workbench_counts.get("final_evidence")
            or count_items(evidence_to_check, "final_evidence")
            or count_items(evidence_context, "final_evidence")
            or 0
        ),
        "missing_expected_evidence": int(
            summary_counts.get("missing_final_expected")
            or workbench_counts.get("missing_final_expected")
            or count_items(evidence_to_check, "missing_expected_evidence", "missing_final_expected")
            or count_items(evidence_context, "missing_final_expected", "missing_expected_evidence")
            or 0
        ),
        "missing_scenario_core_evidence": int(
            summary_counts.get("missing_scenario_core")
            or workbench_counts.get("missing_scenario_core")
            or count_items(evidence_to_check, "missing_scenario_core_evidence", "missing_scenario_core")
            or count_items(evidence_context, "missing_scenario_core", "missing_scenario_core_evidence")
            or 0
        ),
        "lost_before_final_evidence": int(
            summary_counts.get("lost_evidence")
            or workbench_counts.get("lost_evidence")
            or count_items(evidence_to_check, "lost_before_final_evidence", "lost_evidence")
            or count_items(evidence_context, "lost_evidence", "lost_before_final_evidence")
            or 0
        ),
    }


def evidence_examples(case: dict[str, Any], workbench_item: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    evidence_to_check = as_dict(case.get("evidence_to_check"))
    evidence_context = as_dict(workbench_item.get("evidence_context"))
    return {
        "final_evidence": evidence_items(evidence_to_check, "final_evidence")
        or evidence_items(evidence_context, "final_evidence"),
        "missing_expected_evidence": evidence_items(
            evidence_to_check,
            "missing_expected_evidence",
            "missing_final_expected",
        )
        or evidence_items(evidence_context, "missing_final_expected", "missing_expected_evidence"),
        "missing_scenario_core_evidence": evidence_items(
            evidence_to_check,
            "missing_scenario_core_evidence",
            "missing_scenario_core",
        )
        or evidence_items(evidence_context, "missing_scenario_core", "missing_scenario_core_evidence"),
        "lost_before_final_evidence": evidence_items(
            evidence_to_check,
            "lost_before_final_evidence",
            "lost_evidence",
        )
        or evidence_items(evidence_context, "lost_evidence", "lost_before_final_evidence"),
    }


def plain_case_brief(case: dict[str, Any]) -> str:
    question = text(case.get("question"))
    topic = text(case.get("case_topic"))
    if topic and question:
        return f"案由线索是“{topic}”。需要复核的问题是：{question}"
    if question:
        return f"需要复核的问题是：{question}"
    return "这个案例需要先确认案由和待审问题，再判断证据链诊断是否成立。"


def original_claims(case: dict[str, Any], rag_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "excerpt": compact(
            case.get("original_llm_output_excerpt")
            or rag_report.get("answer")
            or rag_report.get("generated_answer")
            or "",
            900,
        ),
        "risk_types": readable_list(case.get("risk_types_from_original_output") or rag_report.get("risk_types")),
        "recommended_actions": readable_list(
            case.get("recommended_actions_from_original_output") or rag_report.get("recommended_actions")
        ),
        "answer_confidence": rag_report.get("answer_confidence"),
        "source": "pilot_batch_report/rag_eval_report",
    }


def support_status(counts: dict[str, int]) -> str:
    if counts["missing_expected_evidence"] and counts["lost_before_final_evidence"]:
        return "likely_evidence_support_gap_needs_user_confirmation"
    if counts["missing_expected_evidence"]:
        return "possible_primary_evidence_gap_needs_user_confirmation"
    if counts["missing_scenario_core_evidence"]:
        return "possible_scenario_scope_gap_needs_user_confirmation"
    if counts["lost_before_final_evidence"]:
        return "possible_final_selection_loss_needs_user_confirmation"
    return "defer_needs_more_information"


def support_status_label(code: str) -> str:
    labels = {
        "likely_evidence_support_gap_needs_user_confirmation": "较可能存在证据支撑缺口，需要人工确认",
        "possible_primary_evidence_gap_needs_user_confirmation": "可能存在主证据缺口，需要人工确认",
        "possible_scenario_scope_gap_needs_user_confirmation": "可能存在案由范围或场景核心条文缺口，需要人工确认",
        "possible_final_selection_loss_needs_user_confirmation": "可能存在最终证据选择流失，需要人工确认",
        "defer_needs_more_information": "信息不足，建议暂缓判断",
    }
    return labels.get(code, "需要人工确认的证据状态")


def detect_assist_signals(
    case: dict[str, Any],
    workbench_item: dict[str, Any],
    counts: dict[str, int],
) -> list[dict[str, str]]:
    detected: dict[str, str] = {}
    if counts["missing_expected_evidence"]:
        detected["primary_issue_missing_evidence"] = (
            f"最终证据链缺少 {counts['missing_expected_evidence']} 条预期主要证据。"
        )
    if counts["missing_scenario_core_evidence"]:
        detected["scenario_core_gap"] = (
            f"场景核心证据缺少 {counts['missing_scenario_core_evidence']} 条，需要校准案由范围。"
        )
    if counts["lost_before_final_evidence"]:
        detected["final_selection_loss"] = (
            f"有 {counts['lost_before_final_evidence']} 条证据曾在候选层出现但未进入最终证据链。"
        )

    family_counts = as_dict(as_dict(case.get("evidence_issue_summary")).get("issue_family_counts"))
    if family_counts.get("functional_typing"):
        detected["definition_substitution_review"] = "存在 legal functional typing 或定义条款替代规范条款复核信号。"

    for code in issue_codes(case, workbench_item):
        signal = ISSUE_CODE_TO_SIGNAL.get(code)
        if signal and signal not in detected:
            detected[signal] = f"来源诊断命中通用问题码：{code}。"

    signal_labels = {item["code"]: item["label"] for item in SUPPORTED_SIGNALS}
    return [
        {"code": code, "label": signal_labels.get(code, code), "reason": reason}
        for code, reason in sorted(detected.items())
    ]


def advisory_tendency(counts: dict[str, int], signals: list[dict[str, str]], prescreen: dict[str, Any]) -> str:
    signal_codes = {signal["code"] for signal in signals}
    high_confidence = prescreen.get("confidence") == "high"
    if high_confidence and {"primary_issue_missing_evidence", "final_selection_loss"} <= signal_codes:
        return "likely_review_issue_confirmable_but_user_must_decide"
    if "primary_issue_missing_evidence" in signal_codes or "scenario_core_gap" in signal_codes:
        return "review_issue_plausible_needs_user_confirmation"
    if counts["lost_before_final_evidence"]:
        return "selection_loss_needs_user_confirmation"
    return "defer_need_more_information"


def advisory_tendency_label(code: str) -> str:
    labels = {
        "likely_review_issue_confirmable_but_user_must_decide": "较可能需要确认诊断，但必须由人工决定",
        "review_issue_plausible_needs_user_confirmation": "诊断问题有一定依据，需要人工确认",
        "selection_loss_needs_user_confirmation": "证据选择流失需要人工确认",
        "defer_need_more_information": "信息不足，建议暂缓判断",
    }
    return labels.get(code, "需要人工确认的辅助判断")


def rationale_lines(case: dict[str, Any], counts: dict[str, int], signals: list[dict[str, str]]) -> list[str]:
    lines = [
        "本条只是审阅辅助，不是人工复核结论。",
        "复核重点是：最终 evidence_chain 是否足以支撑原 LLM 输出里的主要风险、整改动作和结论。",
    ]
    if counts["missing_expected_evidence"]:
        lines.append(
            f"最终证据链缺少 {counts['missing_expected_evidence']} 条预期主要证据，"
            "需要你确认这些条文是否确属主争点依据。"
        )
    if counts["missing_scenario_core_evidence"]:
        lines.append(
            f"场景核心证据缺少 {counts['missing_scenario_core_evidence']} 条，"
            "需要判断是场景登记范围偏宽，还是最终证据确实漏选。"
        )
    if counts["lost_before_final_evidence"]:
        lines.append(
            f"有 {counts['lost_before_final_evidence']} 条证据曾在候选层出现但未进入最终证据链，"
            "需要复核最终证据选择策略。"
        )
    if any(signal["code"] == "definition_substitution_review" for signal in signals):
        lines.append("存在定义条款替代规范条款的复核信号，需要确认是否缺少义务、责任、程序或后果条款。")
    plain_summary = as_list(as_dict(case.get("evidence_issue_summary")).get("plain_summary"))
    lines.extend(compact(item, 160) for item in plain_summary[:3] if text(item))
    return list(dict.fromkeys(lines))


def focus_questions(case: dict[str, Any], counts: dict[str, int], signals: list[dict[str, str]]) -> list[str]:
    signal_codes = {signal["code"] for signal in signals}
    questions = [
        "案由和原 LLM 输出是否在讨论同一个法律问题？",
        "最终 evidence_chain 是否足以支撑原回答中的主要风险类型和整改动作？",
    ]
    if counts["missing_expected_evidence"]:
        questions.append("被标记为缺失的主要条文，是否确实应当进入最终证据链？")
    if counts["lost_before_final_evidence"]:
        questions.append("曾被召回但没进入最终证据链的条文，是否应当被保留？")
    if counts["missing_scenario_core_evidence"]:
        questions.append("场景核心条文缺失，是 registry 范围偏宽，还是 final evidence 漏选？")
    if "answer_evidence_disconnect" in signal_codes:
        questions.append("原回答中的风险后果、整改动作或结论，哪一项最缺少证据支撑？")
    if "definition_substitution_review" in signal_codes:
        questions.append("当前证据是否只是定义条款，而缺少真正说明义务、责任、程序或后果的条款？")
    if as_dict(case.get("ai_suggestion")).get("present"):
        questions.append("AI 参考建议中的根因和后续动作是否过宽，是否需要人工收窄？")
    questions.extend(
        compact(item, 180) for item in as_list(as_dict(case.get("prescreen_advice")).get("user_decision_reasons"))[:2]
    )
    return list(dict.fromkeys(questions))


def evidence_plain_assessment(counts: dict[str, int]) -> str:
    if support_status(counts) == "defer_needs_more_information":
        return "仅凭当前离线信号不宜下结论，建议暂缓或补充上下文。"
    return "最终证据链存在需要人工确认的证据支撑缺口。"


def build_case_assist(
    case: dict[str, Any],
    workbench_by_case: dict[str, dict[str, Any]],
    rag_by_case: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_id = text(case.get("case_id"))
    workbench_item = workbench_by_case.get(case_id, {})
    rag_report = rag_by_case.get(case_id, {})
    counts = evidence_counts(case, workbench_item)
    examples = evidence_examples(case, workbench_item)
    prescreen = as_dict(case.get("prescreen_advice"))
    ai_suggestion = as_dict(case.get("ai_suggestion"))
    signals = detect_assist_signals(case, workbench_item, counts)
    tendency_code = advisory_tendency(counts, signals, prescreen)
    support_code = support_status(counts)
    return {
        "case_id": case_id,
        "rank": case.get("rank"),
        "risk_level": case.get("risk_level"),
        "expected_domains": readable_list(case.get("expected_domains")),
        "case_topic": text(case.get("case_topic")),
        "question": text(case.get("question")),
        "plain_case_brief": plain_case_brief(case),
        "original_llm_claims": original_claims(case, rag_report),
        "evidence_support_assessment": {
            "support_status": support_code,
            "support_status_label": support_status_label(support_code),
            "counts": counts,
            "detected_assist_signals": signals,
            "final_evidence_examples": examples["final_evidence"],
            "missing_expected_evidence_examples": examples["missing_expected_evidence"],
            "missing_scenario_core_evidence_examples": examples["missing_scenario_core_evidence"],
            "lost_before_final_evidence_examples": examples["lost_before_final_evidence"],
            "plain_assessment": evidence_plain_assessment(counts),
        },
        "advisory_review_assist": {
            "review_assist_status": "needs_user_review",
            "advisory_tendency": tendency_code,
            "advisory_tendency_label": advisory_tendency_label(tendency_code),
            "advisory_rationale": rationale_lines(case, counts, signals),
            "focus_questions_for_user": focus_questions(case, counts, signals),
            "user_confirmation_required": True,
            "not_a_reviewer_decision": True,
            "safe_output_boundary": {
                "manual_import_payload_written": False,
                "completed_decision_written": False,
                "promotion_or_ready_action_written": False,
                "user_must_fill_visual_workbench": True,
            },
        },
        "source_signals": {
            "why_selected": readable_list(case.get("why_selected")),
            "prescreen_reference": {
                "category": prescreen.get("category"),
                "category_label": prescreen.get("category_label"),
                "confidence": prescreen.get("confidence"),
                "score": prescreen.get("score"),
                "prescreen_suggested_advisory_decision": prescreen.get("prescreen_suggested_advisory_decision"),
                "not_a_reviewer_decision": prescreen.get("not_a_reviewer_decision") is True,
            },
            "ai_reference": {
                "present": ai_suggestion.get("present") is True,
                "advisory_only": ai_suggestion.get("advisory_only") is True,
                "human_confirmation_required": ai_suggestion.get("human_confirmation_required") is True,
                "advisory_decision": ai_suggestion.get("advisory_decision"),
                "advisory_root_causes": readable_list(ai_suggestion.get("advisory_root_causes")),
                "advisory_follow_up_actions": readable_list(ai_suggestion.get("advisory_follow_up_actions")),
                "not_a_reviewer_decision": ai_suggestion.get("not_a_reviewer_decision") is True,
            },
            "workbench_issue_types": readable_list(workbench_item.get("issue_types")),
            "suggested_review_questions": readable_list(workbench_item.get("suggested_review_questions")),
        },
    }


def recursive_key_scan(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(recursive_key_scan(child))
    elif isinstance(value, list):
        for item in value:
            keys.extend(recursive_key_scan(item))
    return keys


def build_signal_summary(cases: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for case in cases:
        signals = case["evidence_support_assessment"]["detected_assist_signals"]
        counter.update(signal["code"] for signal in signals)
    return dict(sorted(counter.items()))


def build_domain_summary(cases: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "cases": 0,
            "high_attention_cases": 0,
            "missing_expected_evidence": 0,
            "missing_scenario_core_evidence": 0,
            "lost_before_final_evidence": 0,
        }
    )
    for case in cases:
        domains = case.get("expected_domains") or ["未标注领域"]
        counts = case["evidence_support_assessment"]["counts"]
        high_attention = bool(
            counts["missing_expected_evidence"]
            or counts["missing_scenario_core_evidence"]
            or counts["lost_before_final_evidence"]
        )
        for domain in domains:
            row = summary[domain]
            row["cases"] += 1
            row["high_attention_cases"] += int(high_attention)
            row["missing_expected_evidence"] += counts["missing_expected_evidence"]
            row["missing_scenario_core_evidence"] += counts["missing_scenario_core_evidence"]
            row["lost_before_final_evidence"] += counts["lost_before_final_evidence"]
    return dict(sorted(summary.items()))


def is_high_attention(case: dict[str, Any]) -> bool:
    counts = case["evidence_support_assessment"]["counts"]
    return bool(
        counts["missing_expected_evidence"]
        or counts["missing_scenario_core_evidence"]
        or counts["lost_before_final_evidence"]
    )


def build_report(
    pilot_batch_path: Path = DEFAULT_PILOT_BATCH_PATH,
    workbench_path: Path = DEFAULT_WORKBENCH_PATH,
    rag_eval_report_path: Path = DEFAULT_RAG_EVAL_REPORT_PATH,
) -> dict[str, Any]:
    pilot_batch = load_json(pilot_batch_path)
    workbench = load_json(workbench_path)
    rag_eval_report = load_json(rag_eval_report_path)
    workbench_by_case = by_case(workbench.get("workbench_items"))
    rag_by_case = rag_reports_by_case(rag_eval_report)
    cases = [
        build_case_assist(case, workbench_by_case, rag_by_case)
        for case in as_list(pilot_batch.get("pilot_cases"))
        if isinstance(case, dict) and text(case.get("case_id"))
    ]
    tendency_counter = Counter(case["advisory_review_assist"]["advisory_tendency"] for case in cases)
    high_attention_cases = [case for case in cases if is_high_attention(case)]
    report = {
        "version": VERSION,
        "schema_kind": "advisory_pilot_case_review_assist",
        "contains_completed_manual_decisions": False,
        "advisory_packet_only": True,
        "scope": "manual review pilot case advisory assist",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "pilot_batch_report": source_meta(pilot_batch_path, pilot_batch),
            "manual_review_workbench_report": source_meta(workbench_path, workbench),
            "rag_eval_report": source_meta(rag_eval_report_path, rag_eval_report),
        },
        "guardrails": GUARDRAILS,
        "supported_signals": SUPPORTED_SIGNALS,
        "summary": {
            "source_pilot_cases": len(as_list(pilot_batch.get("pilot_cases"))),
            "assisted_cases": len(cases),
            "needs_user_confirmation_cases": len(cases),
            "advisory_only_cases": len(cases),
            "completed_manual_decisions": 0,
            "promotion_candidates": 0,
            "ready_action_candidates": 0,
            "advisory_tendency_summary": dict(sorted(tendency_counter.items())),
            "signal_summary": build_signal_summary(cases),
            "per_domain_summary": build_domain_summary(cases),
            "high_attention_manual_review_cases": len(high_attention_cases),
            "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
        },
        "assisted_cases": cases,
        "high_attention_manual_review_list": [
            {
                "case_id": case["case_id"],
                "rank": case["rank"],
                "risk_level": case.get("risk_level"),
                "expected_domains": case.get("expected_domains", []),
                "advisory_tendency": case["advisory_review_assist"]["advisory_tendency"],
                "evidence_gap_counts": case["evidence_support_assessment"]["counts"],
                "detected_assist_signals": case["evidence_support_assessment"]["detected_assist_signals"],
                "focus_questions_for_user": case["advisory_review_assist"]["focus_questions_for_user"],
                "reason": "存在主要证据缺口、场景核心缺口或候选证据流失，必须由人工最终确认。",
            }
            for case in high_attention_cases
        ],
        "next_step": (
            "Use this advisory report and the visual workbench to make real human review decisions. "
            "Do not import this report as a completed manual review workbench."
        ),
    }
    dangerous_keys = sorted(DANGEROUS_OUTPUT_KEYS & set(recursive_key_scan(report)))
    if dangerous_keys:
        raise ValueError(f"advisory report contains dangerous import keys: {dangerous_keys}")
    return report


def render_evidence_lines(items: list[dict[str, Any]]) -> str:
    if not items:
        return "- 暂无可展示条文摘录。"
    lines = []
    for item in items:
        citation = item.get("citation") or f"{item.get('source', '')} {item.get('article_no', '')}".strip()
        functional_type = item.get("functional_type") or "未标注功能类型"
        preview = item.get("content_preview") or ""
        lines.append(f"- {citation}；功能类型：{functional_type}；摘录：{preview}")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# v0.4.7.8.17 Pilot Case Review Assist",
        "",
        "## 目标",
        "",
        "本报告把首批 pilot case 转成普通中文审阅辅助意见，帮助 reviewer 看懂案由、原 LLM 输出和证据链缺口。"
        "它不是人工复核结论，不会写入 `reviewer_input_template`，也不能作为 dry-run 或 importer 的正式输入。",
        "",
        "## 摘要",
        "",
        f"- 辅助审阅 case：{summary['assisted_cases']}",
        f"- 需要人工确认：{summary['needs_user_confirmation_cases']}",
        f"- 高关注人工复核 case：{summary['high_attention_manual_review_cases']}",
        f"- Completed manual decisions：{summary['completed_manual_decisions']}",
        f"- Promotion candidates：{summary['promotion_candidates']}",
        f"- Ready action candidates：{summary['ready_action_candidates']}",
        f"- Gate status：`{summary['gate_status']}`",
        "",
        "## 支持的辅助信号",
        "",
    ]
    for signal in report["supported_signals"]:
        lines.append(f"- {signal['label']}：{signal['plain_description']}")
    lines.extend(["", "## 每案辅助意见", ""])
    for case in report["assisted_cases"]:
        assist = case["advisory_review_assist"]
        assessment = case["evidence_support_assessment"]
        claims = case["original_llm_claims"]
        signal_labels = "、".join(signal["label"] for signal in assessment["detected_assist_signals"]) or "暂无明显信号"
        missing_and_lost = (
            assessment["missing_expected_evidence_examples"]
            + assessment["missing_scenario_core_evidence_examples"]
            + assessment["lost_before_final_evidence_examples"]
        )
        lines.extend(
            [
                f"### {case['rank']}. `{case['case_id']}`",
                "",
                f"- 案由/问题：{case['plain_case_brief']}",
                f"- 辅助倾向：{assist.get('advisory_tendency_label', '需要人工确认')}（只作参考，仍需人工确认；code：`{assist['advisory_tendency']}`）",
                f"- 证据状态：{assessment['plain_assessment']}",
                f"- 命中的辅助信号：{signal_labels}",
                f"- 原 LLM 主要风险类型：{'、'.join(claims['risk_types']) or '未提供'}",
                f"- 原 LLM 主要整改动作：{'、'.join(claims['recommended_actions']) or '未提供'}",
                "",
                "需要重点看：",
            ]
        )
        lines.extend(f"- {item}" for item in assist["focus_questions_for_user"])
        lines.extend(
            [
                "",
                "缺失、场景核心或流失证据示例：",
                render_evidence_lines(missing_and_lost),
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 本报告只辅助阅读，不写人工结论。",
            "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。",
            "- 不接入 `rag_query`、后端 API、Qdrant 或 LLM。",
            "- 真实治理动作必须等人工在视觉审阅台填写，并通过 export pipeline dry run 后再决定。",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build advisory review assistance for pilot manual-review cases.")
    parser.add_argument("--pilot-batch-report", type=Path, default=DEFAULT_PILOT_BATCH_PATH)
    parser.add_argument("--workbench", type=Path, default=DEFAULT_WORKBENCH_PATH)
    parser.add_argument("--rag-eval-report", type=Path, default=DEFAULT_RAG_EVAL_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.pilot_batch_report, args.workbench, args.rag_eval_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Manual review pilot case assist built: "
        f"{summary['assisted_cases']} cases, "
        f"{summary['high_attention_manual_review_cases']} high-attention cases, "
        f"gate={summary['gate_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
