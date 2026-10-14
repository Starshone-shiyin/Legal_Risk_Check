"""Small, explicit routing layer for the legal workspace ask pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.external_risk.web_search import classify_search_intent, is_recent_risk_overview_question
from src.rag.legal_concepts import detect_legal_concepts
from src.rag.rules import GENERAL_LEGAL_TERMS, LEGAL_QUERY_EXPANSIONS


AskRouteName = Literal[
    "recent_risk_observation",
    "legal_rag_with_web",
    "legal_rag",
    "general_chat",
]


LEGAL_DECISION_MARKERS = (
    "法律", "法规", "法条", "合规", "违法", "是否合法", "是否合规",
    "是否构成", "责任", "赔偿", "处罚", "侵权", "诉讼", "仲裁",
)

# These requests do not necessarily ask for a legal conclusion, but they do
# ask the product to make or support a business risk decision.  They must not
# silently fall through to the ungrounded general-chat response path.
EVIDENCE_FIRST_RISK_MARKERS = (
    "风险", "供应链", "套保", "期货", "采购", "客户名单", "商业秘密",
    "离职", "保密义务", "竞业", "整改", "尽调", "审计",
)


def _requires_legal_rag(text: str) -> bool:
    if any(marker in text for marker in LEGAL_DECISION_MARKERS):
        return True
    if any(marker in text for marker in GENERAL_LEGAL_TERMS):
        return True
    if any(term in text for term in LEGAL_QUERY_EXPANSIONS):
        return True
    # The expansion table is authored as ``concept -> related terms``.  A user
    # will often type a related term (for example "并购") rather than the
    # concept key ("经营者集中"); treating only keys as legal signals sends
    # those questions to general chat without evidence.
    if any(term in text for terms in LEGAL_QUERY_EXPANSIONS.values() for term in terms):
        return True
    if text.endswith("问题"):
        return True
    return bool(detect_legal_concepts(text))


@dataclass(frozen=True)
class AskRoute:
    name: AskRouteName
    reason: str


def decide_ask_route(question: str, *, has_uploaded_materials: bool = False) -> AskRoute:
    """Select evidence policy before retrieval or generation.

    A broad recent-risk request is an external fact-observation task.  A request
    containing a legal decision signal, or accompanied by user material, stays
    on the evidence-gated legal RAG path.
    """
    text = str(question or "").strip().lower()
    if has_uploaded_materials:
        return AskRoute("legal_rag", "uploaded_materials_require_case_specific_review")

    requires_legal_rag = _requires_legal_rag(text)
    # A broad "recent risks" query is still an external-fact observation.  It
    # should not be mistaken for a legal/RAG decision merely because it has the
    # word "风险" in it.
    if is_recent_risk_overview_question(text) and not requires_legal_rag:
        return AskRoute("recent_risk_observation", "broad_current_risk_request")

    intent, _ = classify_search_intent(text)
    if intent in {"legal_update", "legal_reference"}:
        return AskRoute("legal_rag_with_web", "current_or_requested_legal_source")
    if requires_legal_rag:
        return AskRoute("legal_rag", "legal_concept_or_decision_request")
    if any(marker in text for marker in EVIDENCE_FIRST_RISK_MARKERS):
        return AskRoute("legal_rag", "business_risk_decision_requires_evidence")
    return AskRoute("general_chat", "ordinary_conversation")
