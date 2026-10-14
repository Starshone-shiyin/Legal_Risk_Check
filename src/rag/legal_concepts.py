"""轻量法学概念识别与直接法源映射。

概念映射放在配置文件中，避免把少量常见术语硬编码到场景锚点规则里。
它只负责识别和补充召回，不替代向量、稀疏检索或生成模型的法律判断。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _load_concept_config() -> dict[str, Any]:
    # Development reloads restart this cache when the declarative map changes.
    config_path = Path(__file__).parents[2] / "config" / "legal_concepts.json"
    with config_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _concepts() -> list[dict[str, Any]]:
    concepts = _load_concept_config().get("concepts", [])
    return [concept for concept in concepts if isinstance(concept, dict)]


def detect_legal_concepts(question: str) -> list[dict[str, Any]]:
    """Return concepts whose configured terms occur in the question.

    Longer terms are considered first. A shorter term is suppressed only when
    its occurrence is physically covered by a longer occurrence, so
    ``非法人组织`` does not also match ``法人`` while
    ``法人和非法人组织`` still matches both concepts.
    """
    normalized_question = question or ""
    occurrences: list[tuple[int, int, int, dict[str, Any], str]] = []
    for concept_index, concept in enumerate(_concepts()):
        terms = [str(term).strip() for term in concept.get("terms", []) if str(term).strip()]
        for term in terms:
            start = normalized_question.find(term)
            while start >= 0:
                occurrences.append((len(term), start, concept_index, concept, term))
                start = normalized_question.find(term, start + 1)

    occurrences.sort(key=lambda item: (-item[0], item[1], item[2]))
    selected: list[tuple[int, int, int]] = []
    selected_by_concept: dict[int, dict[str, Any]] = {}
    for term_length, start, concept_index, concept, term in occurrences:
        end = start + term_length
        is_covered = any(
            selected_length > term_length and start >= selected_start and end <= selected_end
            for selected_start, selected_end, selected_length in selected
        )
        if is_covered:
            continue

        selected.append((start, end, term_length))
        entry = selected_by_concept.setdefault(
            concept_index,
            {"concept": concept, "matched_terms": [], "occurrences": []},
        )
        if term not in entry["matched_terms"]:
            entry["matched_terms"].append(term)
        entry["occurrences"].append((term_length, start, term))

    ordered_matches = sorted(
        selected_by_concept.values(),
        key=lambda item: (
            -max(match[0] for match in item["occurrences"]),
            -len(item["matched_terms"]),
            item["occurrences"][0][1],
        ),
    )
    results: list[dict[str, Any]] = []
    for entry in ordered_matches:
        concept = entry["concept"]
        matched_terms = entry["matched_terms"]
        matched_term = max(
            matched_terms,
            key=lambda term: (len(term), -normalized_question.find(term)),
        )
        result = dict(concept)
        result["matched_term"] = matched_term
        result["matched_terms"] = matched_terms
        results.append(result)
    return results


def get_concept_domain(question: str) -> str | None:
    """Return the domain supplied by the most specific matched concept."""
    matches = detect_legal_concepts(question)
    if not matches:
        return None
    domain = matches[0].get("domain")
    return str(domain) if domain else None


def get_concept_query_terms(question: str) -> list[str]:
    """Return configured retrieval terms for matched legal concepts."""
    terms: list[str] = []
    seen: set[str] = set()
    for concept in detect_legal_concepts(question):
        values = [concept.get("matched_term"), *concept.get("query_expansion", [])]
        for value in values:
            value = str(value or "").strip()
            if value and value not in seen:
                seen.add(value)
                terms.append(value)
    return terms


def get_concept_anchors(question: str) -> dict[str, list[int]]:
    """Return direct article anchors for matched concepts, preserving order."""
    anchors: dict[str, list[int]] = {}
    for concept in detect_legal_concepts(question):
        for anchor in concept.get("anchors", []):
            source = str(anchor.get("source") or "").strip()
            if not source:
                continue
            bucket = anchors.setdefault(source, [])
            for article_no in anchor.get("articles", []):
                try:
                    article_no = int(article_no)
                except (TypeError, ValueError):
                    continue
                if article_no not in bucket:
                    bucket.append(article_no)
    return anchors


def get_concept_primary_anchors(question: str) -> dict[str, list[int]]:
    """Return primary articles used to verify that a concept was recalled."""
    anchors: dict[str, list[int]] = {}
    for concept in detect_legal_concepts(question):
        primary_articles = concept.get("primary_articles", [])
        if not primary_articles:
            continue
        source = ""
        concept_anchors = concept.get("anchors", [])
        if concept_anchors:
            source = str(concept_anchors[0].get("source") or "").strip()
        if not source:
            continue
        bucket = anchors.setdefault(source, [])
        for article_no in primary_articles:
            try:
                article_no = int(article_no)
            except (TypeError, ValueError):
                continue
            if article_no not in bucket:
                bucket.append(article_no)
    return anchors


def summarize_concept_matches(question: str) -> list[dict[str, Any]]:
    """Return a compact, JSON-safe trace for debug responses and tests."""
    summaries = []
    for concept in detect_legal_concepts(question):
        summaries.append({
            "id": concept.get("id"),
            "matched_term": concept.get("matched_term"),
            "domain": concept.get("domain"),
            "intent": concept.get("intent"),
            "anchors": concept.get("anchors", []),
            "contrast_terms": concept.get("contrast_terms", []),
        })
    return summaries


def find_missing_concept_primary_anchors(
    question: str,
    evidence_chain: list[dict[str, Any]],
) -> list[str]:
    """Explain a concept-specific recall gap without claiming the law is absent."""
    expected = get_concept_primary_anchors(question)
    if not expected:
        return []

    present = {
        (
            str(item.get("source") or item.get("law_name") or "").strip(),
            _as_int(item.get("article_no")),
        )
        for item in evidence_chain
    }
    gaps: list[str] = []
    for source, article_numbers in expected.items():
        missing_articles = [
            article_no for article_no in article_numbers if (source, article_no) not in present
        ]
        if missing_articles:
            articles = "、".join(f"第{article_no}条" for article_no in missing_articles)
            gaps.append(f"已识别法学术语，但对应直接法源未召回：{source}{articles}")
    return gaps


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
