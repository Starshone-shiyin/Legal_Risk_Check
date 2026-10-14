from __future__ import annotations

import re

from langchain_core.documents import Document


def _candidate_article_key(doc: Document):
    """Return the same coarse diversity key used by retriever.py."""
    metadata = doc.metadata
    source = metadata.get("source") or metadata.get("law_name") or ""
    parent_article_id = metadata.get("parent_article_id")
    if parent_article_id:
        return ("parent", source, parent_article_id)
    article_no = metadata.get("article_no")
    if article_no is not None:
        return ("article", source, article_no)
    section_no = metadata.get("section_no")
    if section_no:
        return ("section", source, section_no)
    return ("chunk", metadata.get("chunk_id") or doc.page_content[:100])


def _candidate_exact_key(doc: Document):
    metadata = doc.metadata
    return (
        metadata.get("chunk_id")
        or f"{metadata.get('source')}_{metadata.get('article_no') or metadata.get('section_no')}"
        or doc.page_content[:100]
    )


def summarize_debug_results(results: list[tuple], limit: int = 20) -> list[dict]:
    """Compact candidate results so debug responses do not return full texts."""
    items = []
    for rank, result in enumerate(results[:limit], start=1):
        if len(result) == 4:
            doc, score, rerank_score, keyword_hits = result
        else:
            doc, score = result
            rerank_score = None
            keyword_hits = []
        metadata = doc.metadata
        preview = re.sub(r"\s+", " ", doc.page_content).strip()
        items.append({
            "rank": rank,
            "source": metadata.get("source", ""),
            "law_name": metadata.get("law_name", metadata.get("source", "")),
            "document_type": metadata.get("document_type", ""),
            "law_level": metadata.get("law_level", ""),
            "type": metadata.get("type", ""),
            "block_type": metadata.get("block_type", ""),
            "article": metadata.get("article", ""),
            "article_no": metadata.get("article_no"),
            "section_no": metadata.get("section_no", ""),
            "section_title": metadata.get("section_title", ""),
            "chunk_id": metadata.get("chunk_id", ""),
            "citation": metadata.get("citation", ""),
            "similarity_score": float(score),
            "rerank_score": float(rerank_score) if rerank_score is not None else None,
            "keyword_hits": keyword_hits,
            "content_preview": preview[:220],
        })
    return items


def _debug_rerank_candidate_snapshot(
    doc: Document,
    score: float,
    *,
    input_rank: int | None = None,
    rerank_rank: int | None = None,
    final_rank: int | None = None,
) -> dict:
    metadata = doc.metadata
    preview = re.sub(r"\s+", " ", doc.page_content).strip()
    item = {
        "score": float(score),
        "exact_key": _candidate_exact_key(doc),
        "article_key": str(_candidate_article_key(doc)),
        "source": metadata.get("source", ""),
        "law_name": metadata.get("law_name", metadata.get("source", "")),
        "block_type": metadata.get("block_type", ""),
        "article_no": metadata.get("article_no"),
        "section_no": metadata.get("section_no", ""),
        "citation": metadata.get("citation", ""),
        "chunk_id": metadata.get("chunk_id", ""),
        "content_preview": preview[:220],
    }
    if input_rank is not None:
        item["input_rank"] = input_rank
    if rerank_rank is not None:
        item["rerank_rank"] = rerank_rank
    if final_rank is not None:
        item["final_rank"] = final_rank
    return item


def _debug_rerank_full_score_order(
    input_docs: list[Document],
    reranked: list[tuple[Document, float]],
) -> list[dict]:
    input_rank_by_id = {id(doc): rank for rank, doc in enumerate(input_docs, start=1)}
    return [
        _debug_rerank_candidate_snapshot(
            doc,
            score,
            input_rank=input_rank_by_id.get(id(doc)),
            rerank_rank=rank,
        )
        for rank, (doc, score) in enumerate(reranked, start=1)
    ]


def _debug_final_evidence_selection_trace(
    input_docs: list[Document],
    reranked: list[tuple[Document, float]],
    selected: list[tuple[Document, float]],
    *,
    mode: str,
    top_k: int,
    score_epsilon: float = 0.1,
    reason: str | None = None,
) -> dict:
    input_rank_by_id = {id(doc): rank for rank, doc in enumerate(input_docs, start=1)}
    rerank_rank_by_id = {id(doc): rank for rank, (doc, _) in enumerate(reranked, start=1)}
    selected_ids = {id(doc) for doc, _ in selected}
    trace = {
        "mode": mode,
        "top_k": top_k,
        "score_epsilon": score_epsilon,
        "input_count": len(input_docs),
        "full_rerank_count": len(reranked),
        "selected_count": len(selected),
        "selected": [
            _debug_rerank_candidate_snapshot(
                doc,
                score,
                input_rank=input_rank_by_id.get(id(doc)),
                rerank_rank=rerank_rank_by_id.get(id(doc)),
                final_rank=rank,
            )
            for rank, (doc, score) in enumerate(selected, start=1)
        ],
        "not_selected": [
            _debug_rerank_candidate_snapshot(
                doc,
                score,
                input_rank=input_rank_by_id.get(id(doc)),
                rerank_rank=rank,
            )
            for rank, (doc, score) in enumerate(reranked, start=1)
            if id(doc) not in selected_ids
        ],
    }
    if reason:
        trace["reason"] = reason
    return trace
