from __future__ import annotations

import re
from typing import Any


def normalize_score(score: float) -> float:
    """Clamp vector or rerank scores into a 0-1 range for confidence math."""
    return max(0.0, min(1.0, float(score)))


def build_evidence_chain(results, used_query: str = ""):
    """Convert retrieval results into an auditable evidence chain."""
    evidence_chain = []
    for rank, result in enumerate(results, start=1):
        if len(result) == 4:
            doc, score, rerank_score, keyword_hits = result
        else:
            doc, score = result
            rerank_score = normalize_score(score)
            keyword_hits = []
        metadata = doc.metadata
        parent_content = metadata.get("parent_content") or doc.page_content
        evidence_chain.append({
            "rank": rank,
            "type": metadata.get("type", ""),
            "block_type": metadata.get("block_type", ""),
            "source": metadata.get("source", ""),
            "law_name": metadata.get("law_name", metadata.get("source", "")),
            "document_type": metadata.get("document_type", ""),
            "law_level": metadata.get("law_level", ""),
            "authority_level": metadata.get("authority_level", ""),
            "jurisdiction": metadata.get("jurisdiction", ""),
            "issuing_authority": metadata.get("issuing_authority", ""),
            "legal_effect": metadata.get("legal_effect", ""),
            "standard_type": metadata.get("standard_type", ""),
            "case_type": metadata.get("case_type", ""),
            "patent_type": metadata.get("patent_type", ""),
            "category": metadata.get("category", ""),
            "version": metadata.get("version", ""),
            "chapter": metadata.get("chapter", ""),
            "section": metadata.get("section", ""),
            "heading_level": metadata.get("heading_level", ""),
            "article": metadata.get("article", ""),
            "article_no": metadata.get("article_no"),
            "section_no": metadata.get("section_no", ""),
            "section_title": metadata.get("section_title", ""),
            "section_level": metadata.get("section_level"),
            "appendix": metadata.get("appendix", ""),
            "chunk_index": metadata.get("chunk_index"),
            "chunk_count": metadata.get("chunk_count"),
            "paragraph_no": metadata.get("paragraph_no"),
            "item_no": metadata.get("item_no"),
            "item_label": metadata.get("item_label", ""),
            "parent_article_id": metadata.get("parent_article_id", ""),
            "citation": metadata.get("citation", ""),
            "similarity_score": float(score),
            "rerank_score": float(rerank_score),
            "keyword_hits": keyword_hits,
            "used_query": used_query,
            "matched_content": doc.page_content,
            "content": parent_content,
        })
    return evidence_chain


def calculate_retrieval_confidence(evidence_chain: list[dict], requested_k: int) -> float:
    """Estimate how reliable the retrieval step is before LLM self-assessment."""
    if not evidence_chain:
        return 0.0

    top = evidence_chain[0]
    top_similarity = max(0.0, min(1.0, float(top.get("similarity_score") or 0.0)))
    top_rerank = max(0.0, float(top.get("rerank_score") or 0.0))
    second_rerank = (
        max(0.0, float(evidence_chain[1].get("rerank_score") or 0.0))
        if len(evidence_chain) > 1
        else 0.0
    )

    confidence = top_similarity * 0.55
    if top.get("citation"):
        confidence += 0.12
    if top.get("type") == "article" and top.get("block_type") in {"article", "paragraph", "item", "standard_section"}:
        confidence += 0.08
    if top_rerank >= 1.5:
        confidence += 0.15
    if second_rerank:
        confidence += min(0.06, max(0.0, top_rerank - second_rerank) * 0.03)
    if len(evidence_chain) >= min(max(requested_k, 1), 3):
        confidence += 0.08

    if top_similarity < 0.45 and top_rerank < 1.5:
        confidence -= 0.2
    if not any(item.get("citation") for item in evidence_chain):
        confidence -= 0.15

    return round(max(0.0, min(1.0, confidence)), 2)


def build_missing_evidence(evidence_chain: list[dict], retrieval_confidence: float, requested_k: int) -> list[str]:
    """Explain evidence gaps in machine-readable, user-facing terms."""
    missing = []
    if not evidence_chain:
        return ["未检索到可引用的法律法规、标准或合规依据"]

    top_similarity = float(evidence_chain[0].get("similarity_score") or 0.0)
    if top_similarity < 0.45 and float(evidence_chain[0].get("rerank_score") or 0.0) < 1.5:
        missing.append("最高相似度偏低，检索依据可能不足")
    if len(evidence_chain) < min(max(requested_k, 1), 3):
        missing.append("有效证据数量少于预期")
    if not any(item.get("citation") for item in evidence_chain):
        missing.append("证据缺少可引用标签")
    if retrieval_confidence < 0.65 and not missing:
        missing.append("检索置信度偏低，建议人工复核")
    return missing


def should_request_human_review(
    retrieval_confidence: float,
    answer_confidence: float | None,
    risk_level: str | None,
    missing_evidence: list[str],
) -> bool:
    """Mark answers that should be routed to a human reviewer or senior agent."""
    answer_score = answer_confidence if answer_confidence is not None else 0.0
    if missing_evidence:
        return True
    if retrieval_confidence < 0.65 or answer_score < 0.65:
        return True
    return risk_level == "high" and min(retrieval_confidence, answer_score) < 0.8


def select_supporting_citations(text: str, evidence_chain: list[dict], limit: int = 3) -> list[str]:
    """Bind a risk/action phrase to the most relevant available citations."""
    citations = []
    normalized_text = text or ""
    for item in evidence_chain:
        citation = item.get("citation")
        if not citation or citation in citations:
            continue
        content = " ".join([
            item.get("content", ""),
            item.get("matched_content", ""),
            item.get("article", ""),
            item.get("section_no", ""),
            item.get("section_title", ""),
        ])
        keyword_hits = item.get("keyword_hits") or []
        if any(hit and hit in normalized_text for hit in keyword_hits) or any(
            term in content for term in re.findall(r"[\u4e00-\u9fff]{2,}", normalized_text)[:6]
        ):
            citations.append(citation)
        if len(citations) >= limit:
            return citations

    for item in evidence_chain:
        citation = item.get("citation")
        if citation and citation not in citations:
            citations.append(citation)
        if len(citations) >= limit:
            break
    return citations


def build_supported_items(items: list[str], evidence_chain: list[dict]) -> list[dict]:
    """Attach citation support to risk types or recommended actions."""
    return [
        {
            "text": item,
            "citations": select_supporting_citations(item, evidence_chain),
        }
        for item in items
    ]


def build_context(evidence_chain: list[dict]) -> str:
    """Build the readable legal-evidence context passed to the LLM."""
    context_items = []
    for item in evidence_chain:
        location_parts = [
            item.get("citation") or item.get("law_name") or item.get("source", ""),
            item.get("chapter", ""),
            item.get("section", ""),
        ]
        location = " ".join(part for part in location_parts if part)
        if item.get("type") == "web_result":
            score_label = f"trust={float(item.get('trust_score') or 0.0):.2f}"
        else:
            score_label = f"score={float(item.get('similarity_score') or 0.0):.4f}"
        context_items.append(
            f"【{location} {score_label}】{item.get('content', '')}"
        )
    return "\n\n".join(context_items)
