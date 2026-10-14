from __future__ import annotations

from dataclasses import dataclass

import qdrant_client.http.models as models


@dataclass
class RetrievalFilters:
    """Unified retrieval filter params shared by vector and sparse search."""

    doc_type: str | None = "article"
    block_type: str | None = None
    document_type: str | None = None
    law_name: str | None = None
    source: str | None = None
    law_level: str | None = None
    authority_level: str | None = None
    jurisdiction: str | None = None
    issuing_authority: str | None = None
    legal_effect: str | None = None
    standard_type: str | None = None
    case_type: str | None = None
    patent_type: str | None = None
    category: str | None = None
    version: str | None = None

    def to_qdrant_filter(self) -> models.Filter | None:
        """Convert public filter fields to a Qdrant metadata filter."""
        conditions = []
        mapping = {
            "type": self.doc_type,
            "block_type": self.block_type,
            "document_type": self.document_type,
            "law_name": self.law_name,
            "source": self.source,
            "law_level": self.law_level,
            "authority_level": self.authority_level,
            "jurisdiction": self.jurisdiction,
            "issuing_authority": self.issuing_authority,
            "legal_effect": self.legal_effect,
            "standard_type": self.standard_type,
            "case_type": self.case_type,
            "patent_type": self.patent_type,
            "category": self.category,
            "version": self.version,
        }
        for key, value in mapping.items():
            if value is not None:
                conditions.append(models.FieldCondition(
                    key=f"metadata.{key}",
                    match=models.MatchValue(value=value),
                ))
        return models.Filter(must=conditions) if conditions else None

    def is_default_article_filter(self) -> bool:
        """Whether only the default article filter is active."""
        return (
            self.doc_type == "article"
            and self.block_type is None
            and self.document_type is None
            and self.law_name is None
            and self.source is None
            and self.law_level is None
            and self.authority_level is None
            and self.jurisdiction is None
            and self.issuing_authority is None
            and self.legal_effect is None
            and self.standard_type is None
            and self.case_type is None
            and self.patent_type is None
            and self.category is None
            and self.version is None
        )

    def to_payload(self, candidate_k: int, score_threshold: float | None = None) -> dict:
        """Build API/debug payload for the active filters."""
        return {
            "doc_type": self.doc_type,
            "block_type": self.block_type,
            "document_type": self.document_type,
            "law_name": self.law_name,
            "source": self.source,
            "law_level": self.law_level,
            "authority_level": self.authority_level,
            "jurisdiction": self.jurisdiction,
            "issuing_authority": self.issuing_authority,
            "legal_effect": self.legal_effect,
            "standard_type": self.standard_type,
            "case_type": self.case_type,
            "patent_type": self.patent_type,
            "category": self.category,
            "version": self.version,
            "score_threshold": score_threshold,
            "candidate_k": candidate_k,
        }


def build_metadata_filter(*args, **kwargs):
    filters = RetrievalFilters(*args, **kwargs)
    return filters.to_qdrant_filter()


def should_fallback_to_unfiltered(*args, **kwargs):
    filters = RetrievalFilters(*args, **kwargs)
    return filters.is_default_article_filter()
