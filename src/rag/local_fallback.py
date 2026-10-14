from __future__ import annotations

import re
from pathlib import Path
from typing import Any


KNOWLEDGE_ROOT = Path("src/knowledge/data_compliance")


FALLBACK_REFERENCES = [
    ("中华人民共和国个人信息保护法", "第三十八条", "中华人民共和国个人信息保护法.txt"),
    ("中华人民共和国个人信息保护法", "第三十九条", "中华人民共和国个人信息保护法.txt"),
    ("中华人民共和国个人信息保护法", "第四十条", "中华人民共和国个人信息保护法.txt"),
    ("个人信息出境标准合同办法", "第四条", "个人信息出境标准合同办法.txt"),
    ("个人信息出境标准合同办法", "第五条", "个人信息出境标准合同办法.txt"),
    ("数据出境安全评估办法", "第四条", "数据出境安全评估办法.txt"),
    ("数据出境安全评估办法", "第五条", "数据出境安全评估办法.txt"),
]

DATA_FALLBACK_HINTS = [
    "数据出境",
    "境外",
    "跨境",
    "云服务商",
    "个人信息",
    "客户数据",
    "敏感个人信息",
    "数据合规",
    "数据安全",
    "隐私",
]


def _is_data_compliance_question(question: str) -> bool:
    return any(hint in question for hint in DATA_FALLBACK_HINTS)


def _read_reference(filename: str) -> str:
    return (KNOWLEDGE_ROOT / filename).read_text(encoding="utf-8", errors="replace")


def _extract_article(text: str, article: str) -> str:
    pattern = rf"({re.escape(article)}[\s\S]*?)(?=\n第[一二三四五六七八九十百零〇]+条|\Z)"
    match = re.search(pattern, text)
    if not match:
        return ""
    excerpt = re.sub(r"\s+", " ", match.group(1)).strip()
    return excerpt[:360]


def _build_evidence_chain() -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for law_name, article, filename in FALLBACK_REFERENCES:
        text = _read_reference(filename)
        excerpt = _extract_article(text, article)
        if not excerpt:
            continue
        evidence.append(
            {
                "evidence_id": f"local-{filename}-{article}",
                "law_name": law_name,
                "article": article,
                "jurisdiction": "CN",
                "legal_functional_type": "fallback_reference",
                "excerpt": excerpt,
                "source": str(KNOWLEDGE_ROOT / filename),
                "score": 0.58,
            }
        )
    return evidence


def answer_from_local_knowledge(question: str, error: Exception | None = None) -> dict[str, Any]:
    """Fallback /ask payload when vector RAG is unavailable.

    This is intentionally conservative: it uses local law texts only, avoids LLM
    generation, and always marks the result as requiring human review.
    """

    if not _is_data_compliance_question(question):
        return {
            "answer": "当前 RAG 检索服务暂时不可用，且本地保守 fallback 未覆盖该问题所属法域。请稍后重试，或补充明确法域后再问。",
            "confidence_score": 0.0,
            "answer_confidence": 0.0,
            "retrieval_confidence": 0.0,
            "needs_human_review": True,
            "missing_evidence": ["RAG/Qdrant 不可用，且本地保守 fallback 未覆盖该问题所属法域。"],
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "citation_integrity": {
                "status": "fallback_domain_not_covered",
                "requires_human_review": True,
            },
            "evidence_chain": [],
            "filters": {
                "fallback": "local_knowledge_unavailable_for_domain",
                "question": question,
            },
            "debug_info": {
                "fallback": "domain_not_covered",
                "rag_query": "failed",
                "llm": "not_called",
                "source_error": type(error).__name__ if error else None,
            },
        }

    evidence_chain = _build_evidence_chain()
    answer = (
        "需要重点关注以下法律风险：\n"
        "1. 个人信息出境路径是否合法：客户数据如包含个人信息，向境外云服务商传输通常需要满足个人信息出境条件，"
        "例如通过安全评估、个人信息保护认证、订立标准合同，或符合法律法规规定的其他条件。\n"
        "2. 告知与单独同意：应向个人告知境外接收方名称或姓名、联系方式、处理目的、处理方式、个人信息种类，"
        "以及个人行使权利的方式和程序，并核查是否需要取得单独同意。\n"
        "3. 安全评估或标准合同触发：如果属于关键信息基础设施运营者、处理个人信息达到规定数量，或涉及重要数据、"
        "较大规模个人信息、敏感个人信息出境，应重点判断是否需要申报数据出境安全评估；未触发安全评估但走标准合同路径的，"
        "还要核查适用门槛、影响评估、合同订立和备案要求。\n"
        "4. 境外云服务商安全保障义务：合同或其他法律文件应约定数据出境目的、范围、方式、保存地点和期限、再转移限制、"
        "安全措施、事件通知、审计协助、终止后的删除或返还等义务。\n"
        "5. 数据分类与本地化要求：应区分普通个人信息、敏感个人信息、重要数据以及关键信息基础设施运营场景，"
        "避免把本应本地存储或安全评估的数据直接外传。\n"
        "6. 持续合规与变更风险：云服务区域、处理目的、数据范围、保存期限、境外接收方法规环境或再转移安排变化时，"
        "可能需要重新评估、补充合同或重新申报。"
    )
    return {
        "answer": answer,
        "confidence_score": 0.62,
        "answer_confidence": 0.62,
        "retrieval_confidence": 0.58,
        "needs_human_review": True,
        "missing_evidence": [
            "具体传输的数据类型、个人信息数量、敏感个人信息数量、云服务商所在国家或地区、是否涉及重要数据或关键信息基础设施。"
        ],
        "risk_level": "high",
        "risk_types": [
            "个人信息出境合规",
            "数据出境安全评估",
            "境外接收方安全保障",
            "合同与备案义务",
        ],
        "risk_type_evidence": evidence_chain[:4],
        "recommended_actions": [
            "梳理出境数据清单，区分个人信息、敏感个人信息和重要数据。",
            "核查是否触发数据出境安全评估；未触发时判断是否适用标准合同或认证路径。",
            "完成个人信息保护影响评估并留存记录。",
            "与境外云服务商补齐标准合同、数据处理协议、安全措施、再转移限制和审计协助条款。",
            "补齐告知与单独同意机制，并确认个人权利响应流程。",
        ],
        "recommended_action_evidence": evidence_chain,
        "citation_integrity": {
            "status": "fallback_local_knowledge",
            "requires_human_review": True,
            "note": "RAG/Qdrant 不可用时使用本地法规文本生成的保守答案。",
        },
        "evidence_chain": evidence_chain,
        "filters": {
            "fallback": "local_knowledge",
            "category": "data_compliance",
            "question": question,
        },
        "debug_info": {
            "fallback": "local_knowledge",
            "rag_query": "failed",
            "llm": "not_called",
            "source_error": type(error).__name__ if error else None,
        },
    }
