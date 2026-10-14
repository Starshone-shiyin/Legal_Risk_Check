"""Build an offline prescreen report for manual-review workbench cases.

The prescreen report is advisory only. It reads existing saved diagnostics and
RAG evaluation artifacts, then groups workbench cases by likely review posture.
It does not write reviewer decisions, does not import proposals, and does not
modify retrieval, rerank, prompts, anchors, risk rules, eval cases, hidden
seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VERSION = "0.4.7.8.12"

DEFAULT_WORKBENCH_PATH = Path("tests/evidence_manual_review_workbench.json")
DEFAULT_ALIGNMENT_REPORT_PATH = Path("tests/evidence_alignment_report.json")
DEFAULT_COVERAGE_REPORT_PATH = Path("tests/evidence_coverage_report.json")
DEFAULT_RAG_EVAL_REPORT_PATH = Path("tests/rag_eval_report.json")
DEFAULT_RAG_EVAL_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/manual_review_prescreen_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/manual_review_prescreen_report_v0.4.7.8.12.md")

GUARDRAILS = {
    "advisory_only": True,
    "writes_reviewer_decisions": "disallowed",
    "workbench_import": "disallowed",
    "rag_query_integration": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
}

SUGGEST_CONFIRM = "confirm_diagnostic_issue"
SUGGEST_SCOPE = "confirm_scope_adjustment_needed"
SUGGEST_INSUFFICIENT = "insufficient_information"

CATEGORY_CONFIRM = "likely_confirm_diagnostic_issue"
CATEGORY_SCOPE = "scope_calibration_candidate"
CATEGORY_INFRA = "retrieval_infrastructure_review"
CATEGORY_JUDGMENT = "manual_legal_judgment_required"

CONTENT_GROUNDING_ISSUES = {
    "final_primary_gap",
    "core_missing_from_final_evidence",
    "evidence_chain_gap_candidate",
    "low_final_coverage",
    "low_final_coverage_after_selection",
    "missing_primary_evidence",
    "insufficient_evidence_coverage",
    "answer_evidence_disconnect",
    "definition_only",
}

SCENARIO_SCOPE_ISSUES = {
    "scenario_core_gap",
    "scenario_core_lost",
    "registry_core_review_needed",
    "registry_core_scope_review_candidate",
    "cross_domain_core_gap",
}

FINAL_SELECTION_ISSUES = {
    "layer_coverage_regression",
    "final_selection_review_needed",
    "rerank_input_to_final_loss",
    "primary_evidence_lost",
    "operative_evidence_lost",
    "liability_evidence_lost",
    "anchor_supported_but_final_lost",
}

BASE_RETRIEVAL_ISSUES = {
    "base_retrieval_review_needed",
    "dense_retrieval_gap",
    "sparse_retrieval_gap",
    "union_retrieval_gap",
    "zero_base_recall",
    "no_union_gain",
    "metadata_or_chunking_review_candidate",
    "index_or_source_coverage_review_candidate",
}

ANCHOR_ISSUES = {
    "anchor_dependent_coverage",
    "anchor_rescue_pattern",
    "anchor_dependency_review_needed",
    "anchor_masking_base_retrieval_gap",
    "anchor_rescue_success",
    "high_anchor_gain",
    "zero_base_to_anchor_recovery",
    "anchor_dependency_governance",
}

TYPE_METADATA_ROOTS = {
    "functional_typing_metadata",
}

ISSUE_LABELS = {
    "final_primary_gap": "最终证据缺主要法条",
    "scenario_core_gap": "场景核心条文缺失",
    "anchor_dependent_coverage": "证据覆盖依赖 anchor 补救",
    "layer_coverage_regression": "候选到最终证据时覆盖下降",
    "low_final_coverage": "最终证据覆盖偏低",
    "registry_core_review_needed": "场景登记核心条文需复核",
    "core_missing_from_final_evidence": "核心条文未进入最终证据",
    "evidence_chain_gap_candidate": "证据链缺口候选",
    "final_primary_gap_overlap": "最终主证据缺口重叠",
    "cross_domain_core_gap": "跨领域核心证据缺口",
    "definition_core_candidate": "可能以定义条款替代规范条款",
    "base_retrieval_review_needed": "基础检索质量需复核",
    "dense_retrieval_gap": "向量检索缺口",
    "sparse_retrieval_gap": "关键词检索缺口",
    "union_retrieval_gap": "合并检索缺口",
    "zero_base_recall": "基础检索零召回",
    "no_union_gain": "合并检索没有增益",
    "anchor_rescue_pattern": "anchor 补救模式",
    "metadata_or_chunking_review_candidate": "元数据、切分或查询覆盖候选",
    "anchor_dependency_review_needed": "anchor 依赖需治理复核",
    "anchor_masking_base_retrieval_gap": "anchor 掩盖基础检索缺口",
    "anchor_rescue_success": "anchor 补救成功",
    "high_anchor_gain": "anchor 增益过高",
    "anchor_supported_but_final_lost": "anchor 支持但最终证据丢失",
    "final_selection_review_needed": "最终证据选择策略需复核",
    "rerank_input_to_final_loss": "重排输入到最终证据发生丢失",
    "primary_evidence_lost": "主要证据丢失",
    "scenario_core_lost": "场景核心证据丢失",
    "liability_evidence_lost": "责任或后果证据丢失",
    "low_final_coverage_after_selection": "选择后最终覆盖偏低",
    "operative_evidence_lost": "义务或程序性证据丢失",
    "registry_core_scope_review_candidate": "场景核心范围需校准候选",
    "dense_only_support": "仅向量检索支持",
    "sparse_only_support": "仅关键词检索支持",
    "missing_primary_evidence": "主争点缺证据",
    "insufficient_evidence_coverage": "证据覆盖不足",
    "answer_evidence_disconnect": "答案与证据脱节",
    "definition_only": "只命中定义条款",
    "domain_contamination": "法域污染",
}

CATEGORY_LABELS = {
    CATEGORY_CONFIRM: "建议优先确认诊断成立",
    CATEGORY_SCOPE: "建议作为范围校准复核",
    CATEGORY_INFRA: "检索基建稳定性复核",
    CATEGORY_JUDGMENT: "需要人工法律判断",
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def case_id(item: dict[str, Any]) -> str:
    return normalize_text(item.get("case_id") or item.get("id"))


def map_by_case(items: list[dict[str, Any]], id_key: str | None = None) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        cid = normalize_text(item.get(id_key)) if id_key else case_id(item)
        if cid:
            result[cid] = item
    return result


def list_reports(payload: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        items = payload.get(key) or []
    elif isinstance(payload, list):
        items = payload
    else:
        items = []
    return [item for item in items if isinstance(item, dict)]


def compact_text(value: Any, limit: int = 280) -> str:
    text = " ".join(normalize_text(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def final_evidence_snapshot(rag_report: dict[str, Any], coverage_case: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = coverage_case.get("final_evidence") or rag_report.get("evidence") or rag_report.get("evidence_chain") or []
    snapshot = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        snapshot.append(
            {
                "source": item.get("source") or item.get("law_name"),
                "article_no": item.get("article_no"),
                "section_no": item.get("section_no") or "",
                "functional_type": item.get("functional_type") or item.get("legal_functional_type") or "",
                "content_preview": compact_text(
                    item.get("content_preview")
                    or item.get("content")
                    or item.get("matched_content")
                    or item.get("citation")
                    or ""
                ),
            }
        )
        if len(snapshot) >= 5:
            break
    return snapshot


def family_counts(issue_types: set[str], roots: set[str]) -> dict[str, int]:
    return {
        "content_grounding": len(issue_types & CONTENT_GROUNDING_ISSUES),
        "scenario_scope": len(issue_types & SCENARIO_SCOPE_ISSUES),
        "final_selection": len(issue_types & FINAL_SELECTION_ISSUES),
        "base_retrieval": len(issue_types & BASE_RETRIEVAL_ISSUES),
        "anchor_dependency": len(issue_types & ANCHOR_ISSUES) + int("anchor_dependency_governance" in roots),
        "functional_typing": int(bool(roots & TYPE_METADATA_ROOTS or "definition_core_candidate" in issue_types)),
    }


def review_score(
    workbench_item: dict[str, Any],
    issue_types: set[str],
    families: dict[str, int],
    alignment_case: dict[str, Any],
    coverage_case: dict[str, Any],
) -> int:
    score = int(workbench_item.get("priority_score") or 0)
    risk_level = normalize_text(workbench_item.get("risk_level")).lower()
    if risk_level == "high":
        score += 3
    elif risk_level == "medium":
        score += 1

    counts = workbench_item.get("evidence_context_counts") or {}
    score += 4 * int(counts.get("missing_final_expected") or 0)
    score += 3 * int(counts.get("missing_scenario_core") or 0)
    score += 3 * int(counts.get("lost_evidence") or 0)
    score += 2 * families["content_grounding"]
    score += 2 * families["scenario_scope"]
    score += families["final_selection"]
    if alignment_case.get("alignment_status") == "review":
        score += 2
    if coverage_case.get("coverage_status") == "review":
        score += 2
    if "domain_contamination" in issue_types:
        score += 2
    return score


def confidence_for(category: str, score: int, families: dict[str, int], counts: dict[str, Any]) -> str:
    final_gap_count = int(counts.get("missing_final_expected") or 0) + int(counts.get("lost_evidence") or 0)
    if category == CATEGORY_CONFIRM and (score >= 18 or final_gap_count >= 2):
        return "high"
    if category in {CATEGORY_CONFIRM, CATEGORY_SCOPE} and score >= 10:
        return "medium"
    if category == CATEGORY_INFRA and (families["base_retrieval"] or families["anchor_dependency"]):
        return "medium"
    return "low"


def classify_prescreen(
    workbench_item: dict[str, Any],
    issue_types: set[str],
    roots: set[str],
    families: dict[str, int],
) -> tuple[str, str]:
    counts = workbench_item.get("evidence_context_counts") or {}
    has_final_gap = bool(
        int(counts.get("missing_final_expected") or 0)
        or int(counts.get("lost_evidence") or 0)
        or families["content_grounding"]
        or families["final_selection"]
    )
    has_scope_gap = bool(int(counts.get("missing_scenario_core") or 0) or families["scenario_scope"])
    has_infra_gap = bool(families["base_retrieval"] or families["anchor_dependency"])

    if has_final_gap:
        return CATEGORY_CONFIRM, SUGGEST_CONFIRM
    if has_scope_gap:
        return CATEGORY_SCOPE, SUGGEST_SCOPE
    if has_infra_gap:
        return CATEGORY_INFRA, SUGGEST_CONFIRM
    if roots:
        return CATEGORY_JUDGMENT, SUGGEST_INSUFFICIENT
    return CATEGORY_JUDGMENT, SUGGEST_INSUFFICIENT


def reason_lines(
    workbench_item: dict[str, Any],
    issue_types: set[str],
    families: dict[str, int],
    alignment_case: dict[str, Any],
    coverage_case: dict[str, Any],
) -> list[str]:
    counts = workbench_item.get("evidence_context_counts") or {}
    reasons = []
    missing_final = int(counts.get("missing_final_expected") or 0)
    missing_core = int(counts.get("missing_scenario_core") or 0)
    lost = int(counts.get("lost_evidence") or 0)
    if missing_final:
        reasons.append(f"最终证据缺少 {missing_final} 个预期主要条文。")
    if missing_core:
        reasons.append(f"场景核心条文缺少 {missing_core} 个，可能需要校准案由/场景登记。")
    if lost:
        reasons.append(f"有 {lost} 个条文曾在候选层出现但未进入最终 evidence_chain。")
    if families["base_retrieval"]:
        reasons.append("基础检索层存在缺口，说明不应只依赖 anchor 补救。")
    if families["anchor_dependency"]:
        reasons.append("证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。")
    if families["functional_typing"]:
        reasons.append("存在 legal functional typing 或定义条款替代规范条款的复核信号。")
    if "domain_contamination" in issue_types:
        reasons.append("alignment 报告提示证据来源法域与预期法域不完全一致。")
    for reason in (alignment_case.get("review_reasons") or [])[:2]:
        reasons.append(f"Alignment: {reason}")
    for reason in (coverage_case.get("review_reasons") or [])[:2]:
        reasons.append(f"Coverage: {reason}")
    return list(dict.fromkeys(reasons))[:8]


def user_decision_reasons(
    category: str,
    confidence: str,
    workbench_item: dict[str, Any],
    issue_types: set[str],
    expected_domains: list[str],
) -> list[str]:
    reasons = []
    if confidence != "high":
        reasons.append("预筛置信度不是 high，需要人工确认。")
    if category == CATEGORY_INFRA:
        reasons.append("主要是检索基建稳定性问题，不等于原答案法律结论一定错误。")
    if category == CATEGORY_SCOPE:
        reasons.append("涉及场景核心条文范围，建议由你确认案由和主争点。")
    if len(expected_domains) > 1 or "cross_domain_core_gap" in issue_types:
        reasons.append("涉及多个领域或跨领域核心证据，容易出现法域边界判断。")
    if workbench_item.get("risk_level") == "high":
        reasons.append("高风险 case 即使预筛有把握，也建议人工看一眼。")
    return list(dict.fromkeys(reasons))


def plain_guidance(category: str, confidence: str, suggested_decision: str) -> str:
    if category == CATEGORY_CONFIRM:
        return (
            "先核对案由、待审问题和最终证据链；如果缺失条文确实支撑主争点，"
            "可考虑确认诊断成立。"
        )
    if category == CATEGORY_SCOPE:
        return (
            "重点看这个案子的主争点是否真的需要当前场景登记里的核心条文；"
            "如果核心条文范围过宽，应走范围校准。"
        )
    if category == CATEGORY_INFRA:
        return (
            "这类是检索底座稳定性提示，不等于原答案法律结论一定错误；"
            f"预筛建议结论为 {suggested_decision}，但最好由人工确认是否进入治理链。"
        )
    return "现有离线信号不足以直接归类，建议先补充人工判断理由。"


def build_case_prescreen(
    workbench_item: dict[str, Any],
    alignment_case: dict[str, Any],
    coverage_case: dict[str, Any],
    rag_report: dict[str, Any],
    rag_case: dict[str, Any],
) -> dict[str, Any]:
    wb_issues = set(workbench_item.get("issue_types") or [])
    alignment_issues = set(alignment_case.get("detected_issues") or [])
    coverage_issues = set(coverage_case.get("detected_issues") or [])
    issue_types = wb_issues | alignment_issues | coverage_issues
    roots = set(workbench_item.get("suggested_root_causes") or [])
    families = family_counts(issue_types, roots)
    category, suggested_decision = classify_prescreen(workbench_item, issue_types, roots, families)
    score = review_score(workbench_item, issue_types, families, alignment_case, coverage_case)
    counts = workbench_item.get("evidence_context_counts") or {}
    confidence = confidence_for(category, score, families, counts)
    expected_domains = workbench_item.get("expected_domains") or alignment_case.get("expected_domains") or coverage_case.get("expected_domains") or []
    user_reasons = user_decision_reasons(category, confidence, workbench_item, issue_types, expected_domains)
    issue_labels = [ISSUE_LABELS.get(issue, issue) for issue in sorted(issue_types)]
    question = normalize_text(rag_case.get("question") or rag_report.get("question"))
    answer = normalize_text(rag_report.get("answer"))

    return {
        "case_id": case_id(workbench_item),
        "rank": workbench_item.get("rank"),
        "risk_level": workbench_item.get("risk_level"),
        "priority_score": workbench_item.get("priority_score"),
        "expected_domains": expected_domains,
        "question": question,
        "case_notes": normalize_text(rag_case.get("notes")),
        "original_llm_output_excerpt": compact_text(answer, limit=420),
        "risk_types": rag_report.get("risk_types") or [],
        "recommended_actions": rag_report.get("recommended_actions") or [],
        "prescreen_category": category,
        "prescreen_category_label": CATEGORY_LABELS.get(category, category),
        "prescreen_suggested_decision": suggested_decision,
        "prescreen_confidence": confidence,
        "prescreen_score": score,
        "needs_user_decision": bool(user_reasons),
        "user_decision_reasons": user_reasons,
        "plain_language_guidance": plain_guidance(category, confidence, suggested_decision),
        "reason_summary": reason_lines(workbench_item, issue_types, families, alignment_case, coverage_case),
        "issue_family_counts": families,
        "detected_issue_types": sorted(issue_types),
        "detected_issue_labels": issue_labels,
        "suggested_root_causes": workbench_item.get("suggested_root_causes") or [],
        "suggested_follow_up_actions": workbench_item.get("suggested_follow_up_actions") or [],
        "suggested_review_questions": workbench_item.get("suggested_review_questions") or [],
        "evidence_context_counts": counts,
        "final_evidence_snapshot": final_evidence_snapshot(rag_report, coverage_case),
        "source_status": {
            "alignment_status": alignment_case.get("alignment_status"),
            "coverage_status": coverage_case.get("coverage_status"),
            "rag_eval_passed": rag_report.get("passed"),
            "needs_human_review": rag_report.get("needs_human_review"),
        },
    }


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(item["prescreen_category"] for item in cases)
    decision_counts = Counter(item["prescreen_suggested_decision"] for item in cases)
    confidence_counts = Counter(item["prescreen_confidence"] for item in cases)
    issue_counts = Counter(issue for item in cases for issue in item.get("detected_issue_types") or [])
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    for item in cases:
        domains = item.get("expected_domains") or ["unknown"]
        for domain in domains:
            domain_summary[domain]["cases"] += 1
            domain_summary[domain][item["prescreen_category"]] += 1
            if item.get("needs_user_decision"):
                domain_summary[domain]["needs_user_decision"] += 1
    return {
        "total_cases": len(cases),
        "needs_user_decision": sum(1 for item in cases if item.get("needs_user_decision")),
        "high_confidence_cases": confidence_counts.get("high", 0),
        "medium_confidence_cases": confidence_counts.get("medium", 0),
        "low_confidence_cases": confidence_counts.get("low", 0),
        "category_summary": dict(sorted(category_counts.items())),
        "suggested_decision_summary": dict(sorted(decision_counts.items())),
        "confidence_summary": dict(sorted(confidence_counts.items())),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
    }


def build_report(
    workbench_path: Path = DEFAULT_WORKBENCH_PATH,
    alignment_report_path: Path = DEFAULT_ALIGNMENT_REPORT_PATH,
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    rag_eval_report_path: Path = DEFAULT_RAG_EVAL_REPORT_PATH,
    rag_eval_cases_path: Path = DEFAULT_RAG_EVAL_CASES_PATH,
) -> dict[str, Any]:
    workbench = load_json(workbench_path)
    alignment = load_json(alignment_report_path)
    coverage = load_json(coverage_report_path)
    rag_eval = load_json(rag_eval_report_path)
    rag_cases = load_json(rag_eval_cases_path)

    alignment_by_case = map_by_case(list_reports(alignment, "cases"))
    coverage_by_case = map_by_case(list_reports(coverage, "cases"))
    rag_by_case = map_by_case(list_reports(rag_eval, "reports"), id_key="id")
    rag_case_by_case = map_by_case(list_reports(rag_cases, "cases"), id_key="id")

    cases = []
    for item in workbench.get("workbench_items") or []:
        if not isinstance(item, dict) or not case_id(item):
            continue
        cid = case_id(item)
        cases.append(
            build_case_prescreen(
                item,
                alignment_by_case.get(cid) or {},
                coverage_by_case.get(cid) or {},
                rag_by_case.get(cid) or {},
                rag_case_by_case.get(cid) or {},
            )
        )

    cases = sorted(
        cases,
        key=lambda item: (
            not item.get("needs_user_decision"),
            -(item.get("prescreen_score") or 0),
            item.get("rank") or 9999,
            item.get("case_id") or "",
        ),
    )
    summary = build_summary(cases)
    user_decision_list = [
        {
            "case_id": item["case_id"],
            "rank": item.get("rank"),
            "risk_level": item.get("risk_level"),
            "prescreen_category": item.get("prescreen_category"),
            "prescreen_confidence": item.get("prescreen_confidence"),
            "question": item.get("question"),
            "why_user_should_decide": item.get("user_decision_reasons"),
        }
        for item in cases
        if item.get("needs_user_decision")
    ]
    high_risk_manual_review = [
        item
        for item in user_decision_list
        if item.get("risk_level") == "high"
    ]
    return {
        "version": VERSION,
        "scope": "offline manual review prescreen report",
        "inputs": {
            "workbench": str(workbench_path),
            "workbench_version": workbench.get("version"),
            "alignment_report": str(alignment_report_path),
            "alignment_report_version": alignment.get("version"),
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage.get("version"),
            "rag_eval_report": str(rag_eval_report_path),
            "rag_eval_cases": str(rag_eval_cases_path),
        },
        "guardrails": GUARDRAILS,
        "summary": summary,
        "high_risk_user_decision_list": high_risk_manual_review,
        "user_decision_list": user_decision_list,
        "cases": cases,
    }


def markdown_case_line(item: dict[str, Any]) -> str:
    reasons = "；".join(item.get("reason_summary") or item.get("user_decision_reasons") or ["无"])
    question = compact_text(item.get("question"), 110)
    return (
        f"| `{item['case_id']}` | {item.get('risk_level') or 'unknown'} | "
        f"{item.get('prescreen_category_label')} | {item.get('prescreen_confidence')} | "
        f"{question} | {compact_text(reasons, 180)} |"
    )


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# v0.4.7.8.12 Manual Review Prescreen Report",
        "",
        "本报告是离线预筛建议，只帮助 reviewer 快速理解哪些 case 更值得优先看、哪些需要人工拍板。它不是最终人工复核结论，也不会写入 proposed decision schema。",
        "",
        "## 边界",
        "",
        "- 只读取现有 workbench、alignment、coverage、rag_eval 与 rag_eval_cases 报告。",
        "- 不调用 LLM、Qdrant、rag_query、后端 API 或任何联网能力。",
        "- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、eval case 或 RAG 主流程。",
        "- 不自动导入 reviewer decision；导入前仍需人工确认。",
        "",
        "## 总览",
        "",
        f"- 待预筛 case：{summary['total_cases']}",
        f"- 需要你拍板：{summary['needs_user_decision']}",
        f"- 高置信度建议：{summary['high_confidence_cases']}",
        f"- 中置信度建议：{summary['medium_confidence_cases']}",
        f"- 低置信度建议：{summary['low_confidence_cases']}",
        f"- 建议分类：`{json.dumps(summary['category_summary'], ensure_ascii=False)}`",
        "",
        "## 需要优先人工拍板",
        "",
        "| case | 风险 | 预筛分类 | 置信度 | 问题 | 主要原因 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    high_risk_ids = {item["case_id"] for item in report.get("high_risk_user_decision_list") or []}
    high_risk_cases = [item for item in report["cases"] if item["case_id"] in high_risk_ids]
    for item in high_risk_cases[:20]:
        lines.append(markdown_case_line(item))
    if not high_risk_cases:
        lines.append("| 无 | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## 全量预筛清单",
            "",
            "| case | 风险 | 预筛分类 | 置信度 | 问题 | 主要原因 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["cases"]:
        lines.append(markdown_case_line(item))
    lines.extend(
        [
            "",
            "## 使用建议",
            "",
            "1. 先看“需要优先人工拍板”的高风险 case。",
            "2. 对高置信度且证据缺口明确的 case，可在视觉复核台里核对后填写人工结论。",
            "3. 对“检索基建稳定性复核”类 case，不要理解成原答案一定错误；它更像是在提醒检索底座过度依赖 anchor 或基础召回不稳。",
            "4. 导入任何 reviewer decision 前，仍需由人工确认案由、证据链和理由。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build offline manual-review prescreen report.")
    parser.add_argument("--workbench", type=Path, default=DEFAULT_WORKBENCH_PATH)
    parser.add_argument("--alignment-report", type=Path, default=DEFAULT_ALIGNMENT_REPORT_PATH)
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--rag-eval-report", type=Path, default=DEFAULT_RAG_EVAL_REPORT_PATH)
    parser.add_argument("--rag-eval-cases", type=Path, default=DEFAULT_RAG_EVAL_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        workbench_path=args.workbench,
        alignment_report_path=args.alignment_report,
        coverage_report_path=args.coverage_report,
        rag_eval_report_path=args.rag_eval_report,
        rag_eval_cases_path=args.rag_eval_cases,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review prescreen built: "
        f"{summary['total_cases']} cases, "
        f"{summary['needs_user_decision']} need user decision, "
        f"{summary['high_confidence_cases']} high confidence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
