from __future__ import annotations

import qdrant_client.http.models as models
from langchain_core.documents import Document

from src.core.vectorstore import get_qdrant_client
from src.rag.filters import RetrievalFilters, build_metadata_filter


def point_to_document(point) -> Document:
    """Convert a Qdrant scroll point into a LangChain Document."""
    payload = point.payload or {}
    content = payload.get("page_content") or payload.get("content") or ""
    metadata = payload.get("metadata", {})
    return Document(page_content=content, metadata=metadata)


def point_to_document_from_dict(point_dict: dict) -> Document:
    """Convert a Qdrant HTTP API point dict into a LangChain Document."""
    payload = point_dict.get("payload", {})
    content = payload.get("page_content", "") or payload.get("content", "") or ""
    metadata = payload.get("metadata", {})
    return Document(page_content=content, metadata=metadata)


def fetch_article_range_with_scores(
    collection_name: str,
    start_article_no: int,
    end_article_no: int,
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
) -> list[tuple[Document, float]]:
    """Fetch deterministic article-range candidates for recall supplementation."""
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
    conditions = list(metadata_filter.must) if metadata_filter else []
    conditions.append(
        models.FieldCondition(
            key="metadata.article_no",
            range=models.Range(gte=start_article_no, lte=end_article_no),
        )
    )

    points, _ = get_qdrant_client().scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(must=conditions),
        limit=100,
        with_payload=True,
    )
    return [(point_to_document(point), 1.0) for point in points]


def fetch_article_numbers_with_scores(
    collection_name: str,
    article_numbers: list[int],
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
) -> list[tuple[Document, float]]:
    """Fetch deterministic article-number candidates in one batched scroll."""
    if not article_numbers:
        return []
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
    conditions = list(metadata_filter.must) if metadata_filter else []
    conditions.append(
        models.FieldCondition(
            key="metadata.article_no",
            match=models.MatchAny(any=sorted(set(article_numbers))),
        )
    )

    points, _ = get_qdrant_client().scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(must=conditions),
        limit=max(100, len(set(article_numbers)) * 20),
        with_payload=True,
    )
    return [(point_to_document(point), 1.0) for point in points]


def fetch_standard_sections_with_scores(
    collection_name: str,
    section_numbers: list[str],
    doc_type: str | None = "article",
    block_type: str | None = "standard_section",
    document_type: str | None = "标准",
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
) -> list[tuple[Document, float]]:
    """Fetch deterministic standard-section candidates in one batched scroll."""
    if not section_numbers:
        return []
    filters = RetrievalFilters(
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
    qdrant_filter = filters.to_qdrant_filter()
    conditions = list(qdrant_filter.must) if qdrant_filter else []
    conditions.append(
        models.FieldCondition(
            key="metadata.section_no",
            match=models.MatchAny(any=list(section_numbers)),
        )
    )
    points, _ = get_qdrant_client().scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(must=conditions),
        limit=max(50, len(section_numbers) * 20),
        with_payload=True,
    )
    return [(point_to_document(point), 1.0) for point in points]


def merge_results(primary_results: list[tuple], extra_results: list[tuple]) -> list[tuple]:
    """Merge candidate results by evidence identity and keep the highest score."""
    merged_by_key = {}
    for doc, score in primary_results + extra_results:
        metadata = doc.metadata
        key = (
            metadata.get("parent_article_id") or metadata.get("source"),
            metadata.get("block_type"),
            metadata.get("paragraph_no"),
            metadata.get("item_no"),
            doc.page_content,
        )
        existing = merged_by_key.get(key)
        if existing and existing[1] >= score:
            continue
        merged_by_key[key] = (doc, score)
    return list(merged_by_key.values())
