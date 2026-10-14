from __future__ import annotations

import json
import logging
import re

from src.rag.rules import (
    GENERAL_LEGAL_TERMS,
    INFORMATION_SCOPE_QUERY_HINTS,
    LEGAL_QUERY_EXPANSIONS,
    PIPL_LAW_NAME,
    PRINCIPLE_QUERY_TERMS,
    STANDARD_QUERY_HINTS,
    _load_anchor_rules,
)
from src.rag.legal_concepts import get_concept_anchors, get_concept_query_terms


logger = logging.getLogger(__name__)


def expand_query_terms(question: str, domain: str | None = None) -> list[str]:
    """Expand legal query terms from rule hints, domain anchors, and source text."""
    terms = []
    terms.extend(get_concept_query_terms(question))
    for trigger, expanded_terms in LEGAL_QUERY_EXPANSIONS.items():
        if trigger in question:
            terms.extend(expanded_terms)

    rules = _load_anchor_rules()
    domains_to_check = [domain] if domain else list(rules.get("domains", {}).keys())
    for domain_name in domains_to_check:
        domain_rules = rules.get("domains", {}).get(domain_name)
        if not domain_rules:
            continue
        for rule in domain_rules.get("scene_anchors", []):
            triggers = rule.get("triggers", [])
            context_any = rule.get("context_any", [])
            if not any(trigger in question for trigger in triggers):
                continue
            if context_any and not any(context in question for context in context_any):
                continue
            terms.extend(rule.get("query_expansion", []))

    for term in GENERAL_LEGAL_TERMS:
        if term in question:
            terms.append(term)

    for token in re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{2,}", question):
        terms.append(token)

    seen = set()
    unique_terms = []
    for term in terms:
        if term and term not in seen:
            seen.add(term)
            unique_terms.append(term)
    return unique_terms


def analyze_query_with_llm(question: str) -> dict:
    """Use the LLM as an optional query-understanding layer; fail closed."""
    try:
        from src.core.llm import get_llm

        llm = get_llm()
        prompt = (
            '你是法律专家，请分析用户问题，输出 JSON。\n'
            '领域可选值：数据合规, 公司治理, 市场秩序, 知识产权, 财税, 民商事, 安全合规\n\n'
            '用户问题："' + question + '"\n\n'
            '只输出 JSON：{"legal_concepts":["法律概念"],"domain":"领域","intent":"是否合法|责任认定|义务范围|条件判断|风险识别","keywords":["补充关键词"]}'
        )
        response = llm.invoke(prompt, config={"timeout": 10})
        content = response.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        result = json.loads(content)
        return {
            "legal_concepts": result.get("legal_concepts", []),
            "domain": result.get("domain", ""),
            "intent": result.get("intent", ""),
            "keywords": result.get("keywords", []),
        }
    except Exception:
        logger.debug("LLM reasoning fallback", exc_info=True)
        return {"legal_concepts": [], "domain": "", "intent": "", "keywords": []}


def build_search_query(question: str, domain: str | None = None, reasoning: dict | None = None) -> str:
    """Build an expanded query for retrieval/rerank without changing user facts."""
    expanded_terms = expand_query_terms(question, domain=domain)
    if "原则" in question and (
        "个人信息" in question
        or domain == "数据合规"
    ):
        expanded_terms = PRINCIPLE_QUERY_TERMS + expanded_terms
    if "原则" in question and domain == "民商事":
        expanded_terms = ["平等", "自愿", "公平", "诚信", "公序良俗", "绿色原则"] + expanded_terms
    if any(hint in question for hint in STANDARD_QUERY_HINTS):
        expanded_terms = [
            "个人信息",
            "个人敏感信息",
            "个人信息控制者",
            "产品或服务",
            "个人信息安全规范",
        ] + expanded_terms

    if reasoning:
        for concept in reasoning.get("legal_concepts", []):
            if concept and concept not in expanded_terms:
                expanded_terms.append(concept)
        for keyword in reasoning.get("keywords", []):
            if keyword and keyword not in expanded_terms:
                expanded_terms.append(keyword)

    if not expanded_terms:
        return question
    return f"{question}\n相关检索概念：{' '.join(expanded_terms)}"


def calculate_keyword_boost(question: str, content: str, metadata: dict) -> tuple[float, list[str]]:
    """Calculate lightweight keyword boosts for candidate diagnostics and ordering."""
    terms = expand_query_terms(question)
    haystack = " ".join([
        content,
        metadata.get("article", "") or "",
        metadata.get("chapter", "") or "",
        metadata.get("section", "") or "",
    ])
    hits = [term for term in terms if term in haystack]

    boost = 0.0
    if hits:
        boost += min(0.24, len(hits) * 0.04)

    article_no = metadata.get("article_no")
    law_name = metadata.get("law_name")
    source = metadata.get("source")
    category = metadata.get("category")

    if "原则" in question and (
        "个人信息" in question
        or category == "数据合规"
        or law_name == PIPL_LAW_NAME
        or source == PIPL_LAW_NAME
    ):
        if "原则" in content:
            boost += 0.35
        if any(term in content for term in ["合法", "正当", "必要", "诚信", "公开", "透明", "自愿", "平等", "公平"]):
            boost += 0.18
        if isinstance(article_no, int) and 1 <= article_no <= 9:
            boost += 0.16
        if "总则" in (metadata.get("chapter", "") or ""):
            boost += 0.06

    if any(hint in question for hint in STANDARD_QUERY_HINTS):
        if metadata.get("document_type") == "标准":
            boost += 0.35
        if metadata.get("law_level") == "国家标准":
            boost += 0.16
        if metadata.get("standard_type"):
            boost += 0.08
        if any(term in content for term in ["个人信息包括", "个人敏感信息包括", "个人信息控制者", "产品或服务"]):
            boost += 0.18
        if any(hint in question for hint in INFORMATION_SCOPE_QUERY_HINTS):
            if metadata.get("section_no") in {"3.1", "3.2"}:
                boost += 0.42
            if "个人信息包括" in content or "个人敏感信息包括" in content:
                boost += 0.22
        if "最小必要" in question and metadata.get("section_no") == "5.2":
            boost += 0.5
        if "查询" in question and metadata.get("section_no") == "8.1":
            boost += 0.5

    try:
        concept_anchors = get_concept_anchors(question)
        if concept_anchors:
            anchor_source = law_name or source
            for target_source, article_numbers in concept_anchors.items():
                if anchor_source and anchor_source != target_source:
                    continue
                if isinstance(article_no, int) and article_no in article_numbers:
                    boost += 0.9
                    break

        rules = _load_anchor_rules()
        for domain_rules in rules.get("domains", {}).values():
            for rule in domain_rules.get("scene_anchors", []):
                triggers = rule.get("triggers", [])
                context_any = rule.get("context_any", [])
                if not any(trigger in question for trigger in triggers):
                    continue
                if context_any and not any(context in question for context in context_any):
                    continue
                for anchor in rule.get("anchors", []):
                    if law_name != anchor.get("source"):
                        continue
                    if "articles" in anchor and isinstance(article_no, int) and article_no in anchor["articles"]:
                        boost += 0.85
                        break
                    if "section_nos" in anchor and metadata.get("section_no") in anchor["section_nos"]:
                        boost += 0.85
                        break
    except Exception:
        logger.warning("Failed to load anchor rules for keyword boost, falling back to basic retrieval", exc_info=True)

    if metadata.get("block_type") == "article":
        boost += 0.04

    return boost, hits
