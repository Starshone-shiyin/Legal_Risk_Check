"""Deterministic evidence sufficiency scoring for legal RAG answers.

The score is deliberately distinct from vector similarity.  It estimates whether
the selected evidence is sufficiently citable, authoritative, and diverse for a
legal answer, and exposes a routing recommendation for the orchestration layer.
"""
from __future__ import annotations

from typing import Any


LEGAL_QUERY_MARKERS = (
    "\u6cd5", "\u89c4\u5b9a", "\u4fb5\u6743", "\u8fdd\u6cd5", "\u8bc9\u8bbc", "\u4ef2\u88c1", "\u5408\u540c",
    "\u6743\u5229", "\u4e49\u52a1", "\u8d23\u4efb", "\u5408\u89c4", "\u884c\u653f", "\u53f8\u6cd5",
    "\u4e2a\u4eba\u4fe1\u606f", "\u6570\u636e\u51fa\u5883", "\u654f\u611f\u4e2a\u4eba\u4fe1\u606f", "\u5546\u4e1a\u79d8\u5bc6",
    "\u7ade\u4e1a\u9650\u5236", "\u53cd\u5784\u65ad", "\u6d88\u8d39\u8005", "\u52b3\u52a8\u4e89\u8bae", "\u51fa\u53e3\u7ba1\u5236",
)
LOCAL_LEGAL_DOCUMENT_TYPES = {"\u6cd5\u5f8b\u6cd5\u89c4", "\u884c\u653f\u6cd5\u89c4", "\u53f8\u6cd5\u89e3\u91ca", "\u89c4\u7ae0"}
AUTHORITATIVE_LEVELS = {"\u6cd5\u5f8b", "\u884c\u653f\u6cd5\u89c4", "\u53f8\u6cd5\u89e3\u91ca", "official"}


def assess_evidence_sufficiency(
    evidence_chain: list[dict[str, Any]],
    *,
    question: str,
    requested_k: int,
) -> dict[str, Any]:
    """Score support quality and produce a transparent routing recommendation.

    It makes no claim about substantive legal correctness.  For legal questions,
    external web sources can supplement facts but cannot by themselves pass the
    local-primary-law-source gate.
    """
    evidence = list(evidence_chain or [])
    target_count = min(max(int(requested_k or 1), 1), 3)
    is_legal_question = _looks_like_legal_question(question)
    web_items = [item for item in evidence if item.get("type") == "web_result"]
    local_items = [item for item in evidence if item.get("type") != "web_result"]
    cited_items = [item for item in evidence if str(item.get("citation") or "").strip()]
    local_legal_items = [item for item in local_items if _is_local_legal_evidence(item)]
    authoritative_items = [item for item in evidence if _is_authoritative(item)]
    source_count = len({
        str(item.get("source") or item.get("law_name") or "").strip()
        for item in evidence
        if str(item.get("source") or item.get("law_name") or "").strip()
    })

    coverage = min(1.0, len(evidence) / target_count)
    citation_ratio = len(cited_items) / len(evidence) if evidence else 0.0
    authority_ratio = len(authoritative_items) / len(evidence) if evidence else 0.0
    diversity = min(1.0, source_count / min(target_count, 2)) if evidence else 0.0
    local_primary = bool(local_legal_items)
    local_primary_score = 1.0 if (not is_legal_question or local_primary) else 0.0
    score = round(
        0.25 * coverage
        + 0.25 * citation_ratio
        + 0.20 * authority_ratio
        + 0.10 * diversity
        + 0.20 * local_primary_score,
        2,
    )

    gaps: list[str] = []
    if not evidence:
        gaps.append("\u672a\u68c0\u7d22\u5230\u53ef\u7528\u8bc1\u636e")
    if coverage < 1.0:
        gaps.append("\u8bc1\u636e\u6570\u91cf\u672a\u8fbe\u5230\u9884\u671f\u8986\u76d6")
    if citation_ratio < 1.0:
        gaps.append("\u90e8\u5206\u8bc1\u636e\u7f3a\u5c11\u53ef\u5f15\u7528\u6807\u8bc6")
    if authority_ratio < 0.5:
        gaps.append("\u9ad8\u6743\u5a01\u6765\u6e90\u5360\u6bd4\u4e0d\u8db3")
    if is_legal_question and not local_primary:
        gaps.append("\u7f3a\u5c11\u53ef\u76f4\u63a5\u652f\u6491\u6cd5\u5f8b\u7ed3\u8bba\u7684\u672c\u5730\u6cd5\u6e90")

    if score >= 0.78 and not gaps:
        status = "sufficient"
        recommended_route = "answer_with_evidence"
    elif is_legal_question and not local_primary:
        status = "insufficient"
        recommended_route = "web_supplement"
    else:
        status = "review"
        recommended_route = "human_review"

    return {
        "status": status,
        "score": score,
        "recommended_route": recommended_route,
        "is_legal_question": is_legal_question,
        "coverage": round(coverage, 2),
        "citation_ratio": round(citation_ratio, 2),
        "authority_ratio": round(authority_ratio, 2),
        "source_diversity": round(diversity, 2),
        "evidence_count": len(evidence),
        "local_legal_evidence_count": len(local_legal_items),
        "external_web_evidence_count": len(web_items),
        "gaps": gaps,
    }


def summarize_evidence_sufficiency(reports: list[dict[str, Any]]) -> dict[str, float | int]:
    """Aggregate ESG routing indicators for reproducible retrieval experiments."""
    if not reports:
        return {
            "case_count": 0,
            "mean_score": 0.0,
            "sufficient_rate": 0.0,
            "web_supplement_rate": 0.0,
            "human_review_rate": 0.0,
            "local_primary_law_coverage": 0.0,
        }
    count = len(reports)
    return {
        "case_count": count,
        "mean_score": round(sum(float(item.get("score") or 0.0) for item in reports) / count, 6),
        "sufficient_rate": round(sum(item.get("status") == "sufficient" for item in reports) / count, 6),
        "web_supplement_rate": round(
            sum(item.get("recommended_route") == "web_supplement" for item in reports) / count,
            6,
        ),
        "human_review_rate": round(
            sum(item.get("recommended_route") == "human_review" for item in reports) / count,
            6,
        ),
        "local_primary_law_coverage": round(
            sum(int(item.get("local_legal_evidence_count") or 0) > 0 for item in reports) / count,
            6,
        ),
    }


def _looks_like_legal_question(question: str) -> bool:
    normalized = str(question or "")
    return any(marker in normalized for marker in LEGAL_QUERY_MARKERS)


def _is_local_legal_evidence(item: dict[str, Any]) -> bool:
    if item.get("type") == "web_result":
        return False
    if str(item.get("document_type") or "").strip() in LOCAL_LEGAL_DOCUMENT_TYPES:
        return True
    if str(item.get("law_level") or "").strip() in AUTHORITATIVE_LEVELS:
        return True
    return bool(item.get("article_no")) and bool(item.get("citation"))


def _is_authoritative(item: dict[str, Any]) -> bool:
    if str(item.get("authority_level") or "").strip() == "official":
        return True
    if str(item.get("law_level") or "").strip() in AUTHORITATIVE_LEVELS:
        return True
    return str(item.get("document_type") or "").strip() in LOCAL_LEGAL_DOCUMENT_TYPES
