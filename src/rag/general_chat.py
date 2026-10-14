"""Non-RAG conversational responses for the legal workspace."""
from __future__ import annotations

from typing import Any

from src.core.llm import get_llm


GENERAL_CHAT_PROMPT = """你是法律风控工作台中的通用助手。
用户的问题已被判断为普通对话，不需要检索法律知识库。请用自然、简洁的中文直接回答。
不要编造法律条文、实时新闻、市场数据或个案结论；若用户实际上需要法律意见、风险判断或可追溯依据，提示其明确主体、事实和法域后再提问。

用户问题：
"""


def answer_general_chat(question: str) -> dict[str, Any]:
    """Answer ordinary conversation without retrieval or legal-evidence claims."""
    try:
        response = get_llm().invoke(GENERAL_CHAT_PROMPT + str(question or ""), config={"timeout": 30})
        answer = str(response.content or "").strip()
        if not answer:
            raise RuntimeError("general chat model returned an empty response")
    except Exception:
        answer = "普通对话服务暂时不可用，请稍后再试。"
        return _general_chat_payload(answer, available=False)
    return _general_chat_payload(answer, available=True)


def _general_chat_payload(answer: str, *, available: bool) -> dict[str, Any]:
    return {
        "answer": answer,
        "confidence_score": None,
        "answer_confidence": None,
        "retrieval_confidence": None,
        "needs_human_review": False,
        "missing_evidence": [],
        "risk_level": None,
        "risk_types": [],
        "risk_type_evidence": [],
        "recommended_actions": [],
        "recommended_action_evidence": [],
        "citation_integrity": {
            "passed": True,
            "status": "not_applicable_general_chat",
            "requires_human_review": False,
        },
        "evidence_chain": [],
        "evidence_sufficiency": {
            "status": "not_requested_general_chat",
            "legal_conclusion_permitted": False,
        },
        "material_sources": [],
        "filters": {
            "answer_status": "general_chat",
            "answer_mode": "general_chat",
            "fact_source_policy": "no_retrieval",
        },
        "debug_info": {"postprocess": "general_chat", "llm_available": available},
    }
