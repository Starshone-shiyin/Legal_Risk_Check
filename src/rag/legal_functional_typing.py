"""Offline legal functional typing for evidence diagnostics.

This module is intentionally read-only and deterministic. It classifies text
or evidence metadata for audit/reporting tools, but it does not drive retrieval,
rerank, prompt construction, anchor injection, or risk supplement behavior.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/legal_functional_types.json")

FUNCTION_DEFINITION = "definition"
FUNCTION_PRINCIPLE = "principle"
FUNCTION_OPERATIVE_RULE = "operative_rule"
FUNCTION_PROCEDURAL = "procedural"
FUNCTION_LIABILITY = "liability"
FUNCTION_RIGHTS_REMEDY = "rights_remedy"
FUNCTION_SCOPE = "scope"
FUNCTION_TECHNICAL_STANDARD = "technical_standard"
FUNCTION_UNRELATED_OR_CONTEXTUAL = "unrelated_or_contextual"
FUNCTION_UNCLASSIFIED = "unclassified"

DEFAULT_OPERATIVE_SUPPORT_TYPES = {
    FUNCTION_OPERATIVE_RULE,
    FUNCTION_PROCEDURAL,
    FUNCTION_RIGHTS_REMEDY,
    FUNCTION_LIABILITY,
    FUNCTION_TECHNICAL_STANDARD,
}


@dataclass(frozen=True)
class FunctionalTypeResult:
    functional_type: str
    confidence: str
    matched_rule: str
    matched_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "functional_type": self.functional_type,
            "confidence": self.confidence,
            "matched_rule": self.matched_rule,
            "matched_terms": list(self.matched_terms),
        }


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", "", normalize_text(value))


def _is_structural_context_text(text: str) -> bool:
    primary = normalize_text(text)
    compact = _compact_text(primary)
    if not compact:
        return False
    if len(compact) > 40:
        return False

    structural_patterns = (
        r"^目录$",
        r"^第[一二三四五六七八九十百零〇]+[章节编部分].{0,16}$",
        r"^（?\d{4}年\d{1,2}月\d{1,2}日.{0,24}通过）?$",
        r"^(中华人民共和国)?[\u4e00-\u9fff]{2,36}(法|条例|办法|规定|规则|细则|解释)$",
    )
    return any(re.fullmatch(pattern, compact) for pattern in structural_patterns)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


@lru_cache(maxsize=8)
def load_functional_type_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {
            "functional_types": [],
            "operative_support_types": sorted(DEFAULT_OPERATIVE_SUPPORT_TYPES),
            "rules": [],
        }
    return json.loads(config_path.read_text(encoding="utf-8"))


def configured_functional_type_ids(config: dict[str, Any] | None = None) -> set[str]:
    payload = config or load_functional_type_config()
    return {
        item.get("id")
        for item in _as_list(payload.get("functional_types"))
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def operative_support_types(config: dict[str, Any] | None = None) -> set[str]:
    payload = config or load_functional_type_config()
    values = {
        str(item)
        for item in _as_list(payload.get("operative_support_types"))
        if str(item).strip()
    }
    return values or set(DEFAULT_OPERATIVE_SUPPORT_TYPES)


def functional_type_from_metadata(metadata: dict[str, Any]) -> str | None:
    for key in ("functional_type", "legal_functional_type"):
        value = normalize_text(metadata.get(key))
        if value:
            return value
    values = metadata.get("functional_types")
    if isinstance(values, list) and values:
        first = normalize_text(values[0])
        if first:
            return first
    return None


def text_from_evidence(evidence: dict[str, Any]) -> str:
    keys = (
        "content",
        "page_content",
        "text",
        "content_preview",
        "matched_content",
        "citation",
        "section_title",
        "article_title",
        "source",
        "law_name",
    )
    return " ".join(normalize_text(evidence.get(key)) for key in keys if evidence.get(key))


def classify_legal_function(
    text: str = "",
    metadata: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> FunctionalTypeResult:
    metadata = metadata or {}
    payload = config or load_functional_type_config()

    metadata_type = functional_type_from_metadata(metadata)
    allowed_types = configured_functional_type_ids(payload)
    if metadata_type and (not allowed_types or metadata_type in allowed_types):
        return FunctionalTypeResult(
            functional_type=metadata_type,
            confidence="metadata",
            matched_rule="metadata.functional_type",
        )

    source = normalize_text(metadata.get("source") or metadata.get("law_name"))
    document_type = normalize_text(metadata.get("document_type"))
    if "标准" in document_type or "GB" in source:
        return FunctionalTypeResult(
            functional_type=FUNCTION_TECHNICAL_STANDARD,
            confidence="metadata",
            matched_rule="metadata.document_type",
        )

    primary_text = normalize_text(text)
    if _is_structural_context_text(primary_text):
        return FunctionalTypeResult(
            functional_type=FUNCTION_UNRELATED_OR_CONTEXTUAL,
            confidence="rule_low",
            matched_rule="structural_context_text",
            matched_terms=(primary_text,),
        )

    combined = " ".join(part for part in (primary_text, text_from_evidence(metadata)) if part)
    if not combined:
        return FunctionalTypeResult(
            functional_type=FUNCTION_UNCLASSIFIED,
            confidence="none",
            matched_rule="empty_text",
        )

    rules = sorted(
        [rule for rule in _as_list(payload.get("rules")) if isinstance(rule, dict)],
        key=lambda rule: int(rule.get("priority", 0)),
        reverse=True,
    )
    for rule in rules:
        matched_terms = []
        for term in _as_list(rule.get("contains")):
            term_text = normalize_text(term)
            if term_text and term_text in combined:
                matched_terms.append(term_text)
        for pattern in _as_list(rule.get("regex")):
            pattern_text = normalize_text(pattern)
            if not pattern_text:
                continue
            try:
                if re.search(pattern_text, combined):
                    matched_terms.append(pattern_text)
            except re.error:
                continue
        if matched_terms:
            return FunctionalTypeResult(
                functional_type=normalize_text(rule.get("functional_type")) or FUNCTION_UNCLASSIFIED,
                confidence=normalize_text(rule.get("confidence")) or "rule",
                matched_rule=f"rule:{rule.get('functional_type')}",
                matched_terms=tuple(dict.fromkeys(matched_terms)),
            )

    return FunctionalTypeResult(
        functional_type=FUNCTION_UNCLASSIFIED,
        confidence="none",
        matched_rule="no_rule_match",
    )


def classify_evidence_function(
    evidence: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> FunctionalTypeResult:
    return classify_legal_function(
        text=text_from_evidence(evidence),
        metadata=evidence,
        config=config,
    )


def has_operative_support(functional_types: list[str] | set[str], config: dict[str, Any] | None = None) -> bool:
    return bool(set(functional_types) & operative_support_types(config))
