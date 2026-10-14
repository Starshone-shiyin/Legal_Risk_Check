"""Citation extraction and integrity checks for evidence-grounded outputs."""

from __future__ import annotations

import re
from typing import Any


CITATION_PATTERN = re.compile(r"\[《[^》]+》[^\]]*\]")
ARTICLE_PREFIX_PATTERN = re.compile(r"^(\[《[^》]+》[^第\]]*第[一二三四五六七八九十百千万零〇两\d]+条)")
MARKDOWN_PREFIX_PATTERN = re.compile(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.、)]\s+|[（(]?\d+[）)]\s+)")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
COMPOSITE_CITATION_PATTERN = re.compile(r"^\[《(?P<source>[^》]+)》(?P<references>.+)\]$")
INLINE_LAW_ARTICLE_PATTERN = re.compile(
    r"《(?P<source>[^》]+)》(?P<article>第[一二三四五六七八九十百千万零〇两\d]+条)"
)
BARE_ARTICLE_PATTERN = re.compile(
    r"[（(](?P<article>第[一二三四五六七八九十百千万零〇两\d]+条)[）)]"
)
LEGAL_BASIS_HEADING_PATTERN = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:法律依据|判断依据|主要依据|依据要点)(?:[与及和].*)?\s*[：:]?\s*$"
)
CORE_LEGAL_CLAIM_MARKERS = (
    "构成",
    "不构成",
    "违法",
    "合法",
    "侵权",
    "承担责任",
    "赔偿",
    "行政处罚",
    "罚款",
    "无效",
    "有效",
    "有权",
    "无权",
    "不得",
    "高风险",
    "中风险",
    "低风险",
)


def normalize_citation(value: str) -> str:
    """Normalize citation strings for exact support checks."""
    return re.sub(r"\s+", "", str(value or "").strip())


def citation_support_keys(value: str) -> set[str]:
    """Return exact and article-level keys for citation support matching."""
    normalized = normalize_citation(value)
    if not normalized:
        return set()
    keys = {normalized}
    match = ARTICLE_PREFIX_PATTERN.match(normalized)
    if match:
        keys.add(f"{match.group(1)}]")
    return keys


def extract_citations(text: str) -> list[str]:
    """Extract bracketed Chinese legal citations from text."""
    citations = []
    current_source = ""

    def add(value: str) -> None:
        normalized = normalize_citation(value)
        if normalized and normalized not in citations:
            citations.append(normalized)

    for line in str(text or "").splitlines() or [str(text or "")]:
        bracket_matches = list(CITATION_PATTERN.finditer(line))
        for match in bracket_matches:
            add(match.group(0))
            source_match = re.search(r"《(?P<source>[^》]+)》", match.group(0))
            if source_match:
                current_source = source_match.group("source")
        explicit_matches = list(INLINE_LAW_ARTICLE_PATTERN.finditer(line))
        for match in explicit_matches:
            if any(start <= match.start() < end for start, end in (item.span() for item in bracket_matches)):
                continue
            current_source = match.group("source")
            add(f"[《{current_source}》{match.group('article')}]")
        if current_source:
            for match in BARE_ARTICLE_PATTERN.finditer(line):
                add(f"[《{current_source}》{match.group('article')}]")
    return citations


def collect_supported_citations(items: list[dict[str, Any]]) -> set[str]:
    """Collect citations from evidence_chain or legal_basis-like structures."""
    supported: set[str] = set()
    for item in items or []:
        citation = item.get("citation")
        if citation:
            supported.update(citation_support_keys(citation))
        for nested in item.get("citations", []) or []:
            supported.update(citation_support_keys(nested))
    return supported


def verify_citation_integrity(
    texts: list[str],
    supported_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check whether all citations in texts are supported by provided evidence."""
    cited: list[str] = []
    for text in texts:
        for citation in extract_citations(text):
            if citation not in cited:
                cited.append(citation)

    supported = collect_supported_citations(supported_items)
    unsupported = [
        citation
        for citation in cited
        if not _citation_is_supported(citation, supported)
    ]
    return {
        "passed": not unsupported,
        "cited": cited,
        "supported": sorted(supported),
        "unsupported": unsupported,
    }


def assess_citation_coverage(
    texts: list[str],
    supported_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check whether an evidence-grounded answer actually cites available support."""
    integrity = verify_citation_integrity(texts, supported_items)
    cited = integrity["cited"]
    supported = collect_supported_citations(supported_items)
    supported_cited = [
        citation
        for citation in cited
        if _citation_is_supported(citation, supported)
    ]
    evidence_has_citations = bool(supported)
    substantive_units = _substantive_units(texts)
    cited_units = _units_with_inherited_citations(substantive_units, supported)
    cited_unit_count = sum(cited_units)
    uncited_unit_count = len(substantive_units) - cited_unit_count
    core_units = [unit for unit in substantive_units if _is_core_legal_claim(unit)]
    uncited_core_unit_count = sum(
        1
        for index, unit in enumerate(substantive_units)
        if _is_core_legal_claim(unit) and not cited_units[index]
    )
    has_structured_legal_basis = _has_structured_legal_basis(texts, supported)
    review_uncited_core_count = 0 if has_structured_legal_basis else uncited_core_unit_count
    return {
        "evidence_has_citations": evidence_has_citations,
        "has_any_citation": bool(cited),
        "supported_citations": supported_cited,
        "substantive_unit_count": len(substantive_units),
        "cited_substantive_unit_count": cited_unit_count,
        "uncited_substantive_unit_count": uncited_unit_count,
        "core_legal_claim_unit_count": len(core_units),
        "uncited_core_legal_claim_unit_count": uncited_core_unit_count,
        "has_structured_legal_basis": has_structured_legal_basis,
        "warnings": (
            ["部分一般性说明或执行建议未在相邻位置重复标注法源"]
            if uncited_unit_count > uncited_core_unit_count
            else []
        ),
        "requires_review": evidence_has_citations and (not supported_cited or review_uncited_core_count > 0),
    }


def _substantive_units(texts: list[str]) -> list[str]:
    """Return answer paragraphs/list items that need nearby evidence support.

    Headings, short labels, and citation-only lines are ignored.  The check is
    intentionally structural: it enforces local traceability without claiming
    to decide whether a cited article substantively proves the conclusion.
    """
    units: list[str] = []
    for text in texts:
        normalized_text = re.sub(
            r"</(?:p|li|blockquote|h[1-6]|tr)\s*>|<br\s*/?>",
            "\n",
            str(text or ""),
            flags=re.IGNORECASE,
        )
        for raw_line in normalized_text.splitlines():
            line = raw_line.strip()
            line = HTML_TAG_PATTERN.sub("", line).strip()
            without_citations = CITATION_PATTERN.sub("", line)
            chinese_char_count = len(re.findall(r"[\u4e00-\u9fff]", without_citations))
            if chinese_char_count >= 12 or extract_citations(line):
                units.append(line)
    return units


def _is_core_legal_claim(unit: str) -> bool:
    normalized = CITATION_PATTERN.sub("", unit)
    return any(marker in normalized for marker in CORE_LEGAL_CLAIM_MARKERS)


def _units_with_inherited_citations(units: list[str], supported: set[str]) -> list[bool]:
    """Allow one cited introductory paragraph to support its contiguous list.

    The generator often states a single article immediately before enumerating
    that article's elements. The citation applies to the following list, but
    must not spill into a later, unrelated paragraph or section.
    """
    cited = [
        any(_citation_is_supported(item, supported) for item in extract_citations(unit))
        for unit in units
    ]
    for index, unit in enumerate(units):
        if not cited[index] or not _introduces_following_list(unit):
            continue
        for follow_index in range(index + 1, len(units)):
            following = units[follow_index]
            if _is_heading_unit(following) or not _is_list_item_unit(following):
                break
            cited[follow_index] = True
    for index, unit in enumerate(units[1:], start=1):
        if cited[index] or not cited[index - 1] or not _is_reference_summary(unit):
            continue
        cited[index] = True
    for index, unit in enumerate(units):
        if not cited[index] or not _is_reference_summary(unit):
            continue
        for previous_index in range(index - 1, -1, -1):
            if not _is_list_item_unit(units[previous_index]):
                break
            cited[previous_index] = True
    return cited


def _is_list_introduction(unit: str) -> bool:
    return bool(re.search(r"(?:下列情形之一|下列情形|如下|以下事项|以下|包括|重点评估|主要有|具体为)[：:]?\s*$", CITATION_PATTERN.sub("", unit)))


def _introduces_following_list(unit: str) -> bool:
    """Recognize a cited rule sentence that explicitly opens a list."""
    return _is_list_introduction(unit) or unit.rstrip().endswith((":", "："))


def _is_list_item_unit(unit: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*+]\s+|\d+[.、]|[（(]\d+[）)])", unit))


def _is_heading_unit(unit: str) -> bool:
    return bool(re.match(r"^\s*#{1,6}\s+", unit))


def _is_reference_summary(unit: str) -> bool:
    """Identify a short immediate restatement of the preceding cited point."""
    without_citations = CITATION_PATTERN.sub("", unit).strip()
    return bool(re.match(r"^(?:上述|前述|其中|由此|据此)", without_citations))


def _citation_is_supported(citation: str, supported: set[str]) -> bool:
    """Accept a compact citation only if every referenced section is available."""
    if citation_support_keys(citation).intersection(supported):
        return True
    match = COMPOSITE_CITATION_PATTERN.match(normalize_citation(citation))
    if not match or "、" not in match.group("references"):
        return False
    source = match.group("source")
    references = [item.strip() for item in match.group("references").split("、") if item.strip()]
    return bool(references) and all(
        citation_support_keys(f"[《{source}》{reference}]").intersection(supported)
        for reference in references
    )


def _has_structured_legal_basis(texts: list[str], supported: set[str]) -> bool:
    """Allow a conclusion section to inherit a later dedicated, cited basis section."""
    for text in texts:
        lines = str(text or "").splitlines()
        for index, line in enumerate(lines):
            normalized_heading = MARKDOWN_PREFIX_PATTERN.sub("", HTML_TAG_PATTERN.sub("", line)).strip()
            is_basis_heading = bool(LEGAL_BASIS_HEADING_PATTERN.match(line)) or bool(
                re.search(r"(?:依据|情形|要求|动作)", normalized_heading)
                and normalized_heading.endswith(("情形", "要求", "动作", "依据"))
            )
            if not is_basis_heading:
                continue
            section_text = "\n".join(lines[index + 1:])
            if any(citation_support_keys(citation).intersection(supported) for citation in extract_citations(section_text)):
                return True
    return False


def citation_failure_messages(integrity: dict[str, Any]) -> list[str]:
    """Return human-review messages for unsupported citations."""
    return [f"引用未在证据链中找到: {citation}" for citation in integrity.get("unsupported", [])]


def citation_coverage_messages(coverage: dict[str, Any]) -> list[str]:
    """Return a user-facing warning when available evidence was not cited."""
    if (
        coverage.get("evidence_has_citations")
        and coverage.get("uncited_core_legal_claim_unit_count", 0) > 0
        and not coverage.get("has_structured_legal_basis")
    ):
        return [
            "回答中存在未就近标注可用法律依据的核心法律判断，建议人工复核"
        ]
    if coverage.get("requires_review"):
        return ["回答未引用证据链中的可用法律依据，建议人工复核"]
    return []
