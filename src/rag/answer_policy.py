from __future__ import annotations

import re
from typing import Any


REALTIME_FACT_HINTS = [
    "市场数据",
    "实时数据",
    "最新",
    "今天",
    "近期",
    "新闻",
    "行情",
    "股价",
    "估值",
    "融资",
    "舆情",
    "竞争格局",
    "市场份额",
    "行业大会",
    "监管动态",
]


ACTION_QUESTION_HINTS = [
    "怎么办",
    "如何补救",
    "如何整改",
    "如何应对",
    "建议",
    "制度",
    "流程",
    "优先级",
    "时间表",
    "内控",
    "管理制度",
    "防范",
]


NESTED_SECTION_LABELS = {
    "共同点",
    "相同点",
    "不同点",
    "差异点",
    "区别",
    "主要依据",
    "依据要点",
    "依据",
    "建议动作",
    "建议",
    "补救",
    "应对动作",
    "补救/应对动作",
    "缺少依据",
    "缺少依据/需补充材料",
}

LIST_MARKER_PATTERN = re.compile(r"^\s*(?:\d+[\.、)]|[一二三四五六七八九十]+[、.)]|[-*•])\s*(.+?)\s*$")
SUBLIST_MARKER_PATTERN = re.compile(r"^\s*(?:[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩])\s*(.+?)\s*$")
RICH_ANSWER_MARKUP_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:#{1,6}\s+|[-+]\s+|>\s+|```)|"
    r"(?:\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^\)]+\)|</?[a-zA-Z][^>]*>)"
)


RISK_ANALYSIS_HINTS = [
    "是否合规",
    "是否合法",
    "是否构成",
    "能否追究",
    "法律责任",
    "风险",
    "违规",
    "侵权",
    "投诉",
    "处罚",
    "数据出境",
    "自动化决策",
    "商业秘密",
    "反垄断",
]


def determine_answer_mode(question: str, complex_case_plans: list[dict[str, Any]] | None = None) -> str:
    """Route generation into a stable answer style without changing retrieval."""
    if complex_case_plans:
        return "complex_case"
    if any(hint in question for hint in ACTION_QUESTION_HINTS):
        return "action_plan"
    if any(hint in question for hint in RISK_ANALYSIS_HINTS) or len(question) >= 180:
        return "risk_analysis"
    return "legal_qa"


def detect_external_fact_needs(question: str) -> dict[str, Any]:
    matched = [hint for hint in REALTIME_FACT_HINTS if hint in question]
    return {
        "requires_external_facts": bool(matched),
        "matched_hints": matched,
        "boundary": (
            "当前 RAG 仅使用已入库法律/合规材料；实时市场、新闻、监管动态和公司经营数据需要接入独立事实源后才能作为事实依据。"
            if matched
            else ""
        ),
    }


def _append_missing_once(missing: list[str], note: str) -> list[str]:
    if note and note not in missing:
        missing.append(note)
    return missing


def _citation_from_evidence_item(item: dict[str, Any]) -> str:
    source = item.get("law_name") or item.get("source") or "已入库依据"
    article = item.get("article") or item.get("section_no") or item.get("article_no") or ""
    return f"[《{source}》{article}]" if article else f"[《{source}》]"


def _citation_labels(evidence_chain: list[dict[str, Any]], limit: int = 4) -> list[str]:
    labels: list[str] = []
    for item in evidence_chain:
        citation = item.get("citation") or _citation_from_evidence_item(item)
        if citation and citation not in labels:
            labels.append(citation)
        if len(labels) >= limit:
            break
    return labels


def _looks_structured_answer(answer: str) -> bool:
    section_markers = ["风险结论", "简要结论", "依据", "建议", "补救", "应对动作", "缺少依据"]
    numbered_items = len(re.findall(r"(?:^|\n)\s*\d+[\.、)]\s*", answer))
    return any(marker in answer for marker in section_markers) or numbered_items >= 2


def _uses_rich_answer_markup(answer: str) -> bool:
    """Keep valid Markdown and safe HTML available to the presentation layer."""
    return bool(RICH_ANSWER_MARKUP_PATTERN.search(str(answer or "")))


def _clean_answer_line_markup(line: str) -> str:
    """Clean common malformed Markdown emitted by models around Chinese labels."""
    cleaned = str(line or "").strip()
    cleaned = re.sub(r"^\*+([^*：:]{1,40}[：:])\*+\s*", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+?)\*", r"\1", cleaned)
    cleaned = cleaned.replace("*", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _strip_list_marker(line: str) -> tuple[str, bool]:
    stripped = _clean_answer_line_markup(line)
    match = LIST_MARKER_PATTERN.match(stripped)
    if match:
        return _clean_answer_line_markup(match.group(1)), True
    sub_match = SUBLIST_MARKER_PATTERN.match(stripped)
    if sub_match:
        return _clean_answer_line_markup(sub_match.group(1)), True
    return stripped, False


def _parse_section_label(text: str) -> tuple[str, str] | None:
    cleaned = _clean_answer_line_markup(text)
    plain = cleaned.rstrip("：:").strip()
    if plain in NESTED_SECTION_LABELS:
        return plain, ""
    match = re.match(r"^([^：:]{1,40})[：:]\s*(.*)$", cleaned)
    if not match:
        return None
    label = match.group(1).strip()
    content = match.group(2).strip()
    if label in NESTED_SECTION_LABELS:
        return label, content
    return None


def normalize_answer_text(answer: str) -> str:
    """Normalize legal answer structure before streaming/rendering."""
    normalized_answer = str(answer or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if _uses_rich_answer_markup(normalized_answer):
        return normalized_answer

    normalized_lines: list[str] = []
    active_section: str | None = None
    active_count = 0

    for raw_line in normalized_answer.split("\n"):
        if not raw_line.strip():
            if normalized_lines and normalized_lines[-1] != "":
                normalized_lines.append("")
            continue

        body, had_list_marker = _strip_list_marker(raw_line)
        section = _parse_section_label(body)
        if section:
            label, content = section
            if normalized_lines and normalized_lines[-1] != "":
                normalized_lines.append("")
            normalized_lines.append(f"{label}：")
            active_section = label
            active_count = 0
            if content:
                active_count += 1
                normalized_lines.append(f"（{active_count}）{content}")
            continue

        if active_section and had_list_marker:
            active_count += 1
            normalized_lines.append(f"（{active_count}）{body}")
            continue

        active_section = None
        active_count = 0
        normalized_lines.append(_clean_answer_line_markup(raw_line))

    while normalized_lines and normalized_lines[-1] == "":
        normalized_lines.pop()
    return "\n".join(normalized_lines).strip()


def _build_answer_scaffold(
    mode: str,
    answer: str,
    evidence_chain: list[dict[str, Any]],
    recommended_actions: list[str],
    missing_evidence: list[str],
) -> str:
    answer = str(answer or "").strip()
    if not answer or _looks_structured_answer(answer) or _uses_rich_answer_markup(answer):
        return answer

    citations = _citation_labels(evidence_chain)
    basis = "、".join(citations) if citations else "当前证据链不足，需人工补充直接依据"
    action_lines = "\n".join(f"{index}. {item}" for index, item in enumerate(recommended_actions[:5], start=1))
    missing_lines = "\n".join(f"{index}. {item}" for index, item in enumerate(missing_evidence[:3], start=1))

    if mode == "legal_qa":
        parts = [
            "简要结论：",
            answer,
            "",
            "依据要点：",
            basis,
        ]
    elif mode == "action_plan":
        parts = [
            "处理结论：",
            answer,
            "",
            "建议动作：",
            action_lines or "1. 先补齐事实、合同和直接法规依据，再形成正式处置意见。",
            "",
            "依据与复核：",
            basis,
        ]
    else:
        parts = [
            "风险结论：",
            answer,
            "",
            "主要依据：",
            basis,
            "",
            "建议动作：",
            action_lines or "1. 固定事实证据并补充直接法律依据后再作最终判断。",
        ]

    if missing_lines:
        parts.extend(["", "缺少依据/需补充材料：", missing_lines])
    return "\n".join(parts).strip()


def apply_answer_mode_policy(
    payload: dict[str, Any],
    *,
    question: str,
    mode: str,
    external_fact_needs: dict[str, Any],
    evidence_chain: list[dict[str, Any]],
) -> dict[str, Any]:
    """Normalize final answer shape and expose fact-source boundaries."""
    normalized = dict(payload)
    missing = list(normalized.get("missing_evidence") or [])
    filters = dict(normalized.get("filters") or {})
    has_debug_info = normalized.get("debug_info") is not None
    debug_info = dict(normalized.get("debug_info") or {})
    normalized.setdefault("needs_human_review", False)

    if external_fact_needs.get("requires_external_facts"):
        _append_missing_once(missing, external_fact_needs["boundary"])
        normalized["needs_human_review"] = True

    if mode in {"risk_analysis", "action_plan", "complex_case"} and normalized.get("risk_level") is None:
        normalized["risk_level"] = "medium" if evidence_chain else None

    normalized["answer"] = normalize_answer_text(_build_answer_scaffold(
        mode,
        str(normalized.get("answer") or ""),
        evidence_chain,
        list(normalized.get("recommended_actions") or []),
        missing,
    ))
    normalized["missing_evidence"] = missing
    normalized["filters"] = {
        **filters,
        "answer_mode": mode,
        "answer_contract_version": "v2_markdown_html",
        "fact_source_policy": "legal_corpus_only",
        "requires_external_facts": bool(external_fact_needs.get("requires_external_facts")),
    }
    if has_debug_info:
        normalized["debug_info"] = {
            **debug_info,
            "answer_mode_policy": {
                "mode": mode,
                "external_fact_needs": external_fact_needs,
                "legal_evidence_count": len(evidence_chain),
            },
        }
    return normalized
