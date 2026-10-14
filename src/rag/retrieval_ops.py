from __future__ import annotations

import logging

from langchain_core.documents import Document

from src.core.vectorstore import get_qdrant_client, get_vectorstore
from src.rag.filters import RetrievalFilters, build_metadata_filter, should_fallback_to_unfiltered
from src.rag.qdrant_access import point_to_document, point_to_document_from_dict


logger = logging.getLogger(__name__)


def merge_union(
    dense_results: list[tuple[Document, float]],
    sparse_results: list[tuple[Document, float]],
) -> list[tuple[Document, float]]:
    """Merge dense-first candidates with sparse supplemental candidates."""
    seen = set()
    merged = []
    for doc, score in dense_results:
        key = doc.metadata.get("parent_article_id") or doc.page_content[:120]
        if key not in seen:
            seen.add(key)
            merged.append((doc, score))
    for doc, _score in sparse_results:
        key = doc.metadata.get("parent_article_id") or doc.page_content[:120]
        if key not in seen:
            seen.add(key)
            merged.append((doc, 0.5))
    return merged


def retrieve_with_sparse(
    query: str,
    collection_name: str = "legal_knowledge",
    k: int = 50,
    filters: RetrievalFilters | None = None,
) -> list[tuple[Document, float]]:
    """Run Qdrant sparse-vector search."""
    from src.rag.bm25_encoder import get_bm25_encoder

    encoder = get_bm25_encoder()
    indices, values = encoder.encode(query)
    if not indices:
        return []

    qdrant_filter = filters.to_qdrant_filter() if filters else None

    try:
        import requests
        from src.config import get_settings

        settings = get_settings()
        url = f"http://{settings.qdrant_host}:{settings.qdrant_port}/collections/{collection_name}/points/query"
        payload: dict = {
            "query": {"indices": indices, "values": values},
            "using": "bm25",
            "limit": k,
            "with_payload": True,
        }
        if qdrant_filter:
            payload["filter"] = qdrant_filter.model_dump() if hasattr(qdrant_filter, "model_dump") else qdrant_filter
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [(point_to_document_from_dict(point), float(point["score"])) for point in data["result"]["points"]]
    except Exception:
        logger.warning("Sparse vector search failed", exc_info=True)
        return []


def retrieve_with_keyword_match(
    query: str,
    collection_name: str = "legal_knowledge",
    k: int = 40,
    filters: RetrievalFilters | None = None,
) -> list[tuple[Document, float]]:
    """Use Qdrant scroll payloads for a lightweight keyword recall fallback."""
    qdrant_filter = filters.to_qdrant_filter() if filters else None

    import jieba

    terms = list(jieba.cut(query))
    terms = [term.strip() for term in terms if len(term.strip()) >= 2]

    if not terms:
        return []

    try:
        points, _ = get_qdrant_client().scroll(
            collection_name=collection_name,
            scroll_filter=qdrant_filter,
            limit=k * 2,
            with_payload=True,
            with_vectors=False,
        )
    except Exception:
        logger.warning("Keyword match scroll failed, returning empty", exc_info=True)
        return []

    results = []
    for point in points:
        content = point.payload.get("page_content", "")
        score = sum(1.0 for term in terms if term in content) / max(len(terms), 1)
        if score > 0:
            results.append((point_to_document(point), score))

    results.sort(key=lambda item: item[1], reverse=True)
    return results[:k]


def collapse_parent_results(results: list[tuple], limit: int) -> list[tuple]:
    """Keep the highest-ranked hit per parent article to reduce duplicate context."""
    collapsed = []
    seen = set()
    for result in results:
        doc = result[0]
        metadata = doc.metadata
        key = metadata.get("parent_article_id") or (
            metadata.get("source"),
            metadata.get("article"),
            metadata.get("article_no"),
        )
        if key in seen:
            continue
        seen.add(key)
        collapsed.append(result)
        if len(collapsed) >= limit:
            break
    return collapsed


def retrieve(
    query: str,
    collection_name: str = "legal_knowledge",
    k: int = 5,
    doc_type: str | None = "article",
    block_type: str | None = None,
    document_type: str | None = None,
    law_name: str | None = None,
    source: str | None = None,
    law_level: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
    category: str | None = None,
    version: str | None = None,
):
    """Retrieve relevant legal documents."""
    vectorstore = get_vectorstore(collection_name)
    metadata_filter = build_metadata_filter(
        doc_type=doc_type,
        block_type=block_type,
        document_type=document_type,
        law_name=law_name,
        source=source,
        law_level=law_level,
        authority_level=authority_level,
        jurisdiction=jurisdiction,
        issuing_authority=issuing_authority,
        legal_effect=legal_effect,
        standard_type=standard_type,
        case_type=case_type,
        patent_type=patent_type,
        category=category,
        version=version,
    )
    results = vectorstore.similarity_search(query, k=k, filter=metadata_filter)
    if not results and should_fallback_to_unfiltered(
        doc_type,
        block_type,
        document_type,
        law_name,
        source,
        law_level,
        authority_level,
        jurisdiction,
        issuing_authority,
        legal_effect,
        standard_type,
        case_type,
        patent_type,
        category,
        version,
    ):
        results = vectorstore.similarity_search(query, k=k)
    return results


def retrieve_with_scores(
    query: str,
    collection_name: str = "legal_knowledge",
    k: int = 5,
    doc_type: str | None = "article",
    block_type: str | None = None,
    document_type: str | None = None,
    law_name: str | None = None,
    source: str | None = None,
    law_level: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
    category: str | None = None,
    version: str | None = None,
    score_threshold: float | None = None,
):
    """Retrieve relevant legal documents with vector scores."""
    vectorstore = get_vectorstore(collection_name)
    metadata_filter = build_metadata_filter(
        doc_type=doc_type,
        block_type=block_type,
        document_type=document_type,
        law_name=law_name,
        source=source,
        law_level=law_level,
        authority_level=authority_level,
        jurisdiction=jurisdiction,
        issuing_authority=issuing_authority,
        legal_effect=legal_effect,
        standard_type=standard_type,
        case_type=case_type,
        patent_type=patent_type,
        category=category,
        version=version,
    )
    results = vectorstore.similarity_search_with_score(
        query,
        k=k,
        filter=metadata_filter,
        score_threshold=score_threshold,
    )
    if not results and should_fallback_to_unfiltered(
        doc_type,
        block_type,
        document_type,
        law_name,
        source,
        law_level,
        authority_level,
        jurisdiction,
        issuing_authority,
        legal_effect,
        standard_type,
        case_type,
        patent_type,
        category,
        version,
    ):
        results = vectorstore.similarity_search_with_score(
            query,
            k=k,
            score_threshold=score_threshold,
        )
    return results
