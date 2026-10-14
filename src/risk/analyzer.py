"""Risk engine facade over the RAG layer."""

from __future__ import annotations

from typing import Any

from src.core.citations import (
    assess_citation_coverage,
    citation_coverage_messages,
    citation_failure_messages,
    verify_citation_integrity,
)
from src.rag.retriever import rag_query
from src.risk.taxonomy import (
    classify_risk_categories,
    infer_taxonomy_risk_level,
    normalize_risk_level,
    stronger_level,
)


def analyze_risk(
    scenario: str,
    *,
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
    debug: bool = False,
    user_materials: list[dict[str, Any]] | None = None,
    expected_risk_domain: str | None = None,
) -> dict[str, Any]:
    """Analyze a business scenario and return a stable risk-control result."""
    rag_result = rag_query(
        scenario,
        collection_name=collection_name,
        k=k,
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
        score_threshold=score_threshold,
        debug=debug,
        user_materials=user_materials,
    )
    return build_risk_analysis(scenario, rag_result, expected_risk_domain=expected_risk_domain)


def build_risk_analysis(
    scenario: str,
    rag_result: dict[str, Any],
    *,
    expected_risk_domain: str | None = None,
) -> dict[str, Any]:
    """Convert rag_query output into a risk-engine contract."""
    rag_level = normalize_risk_level(rag_result.get("risk_level"), fallback="medium")
    if rag_level == "low":
        categories = []
        risk_level = "low"
    else:
        categories = classify_risk_categories(
            scenario,
            rag_result.get("answer", ""),
            rag_result.get("risk_types", []),
            rag_result.get("recommended_actions", []),
        )
        taxonomy_level = infer_taxonomy_risk_level(categories, fallback=rag_level)
        risk_level = stronger_level(rag_level, taxonomy_level)
    legal_basis = build_legal_basis(rag_result.get("evidence_chain", []))
    risk_types = normalize_output_risk_types(rag_result.get("risk_types", []), categories)
    citation_integrity = dict(rag_result.get("citation_integrity") or verify_citation_integrity(
        [rag_result.get("answer", "")],
        rag_result.get("evidence_chain", []),
    ))
    coverage = citation_integrity.get("coverage")
    if not isinstance(coverage, dict):
        coverage = assess_citation_coverage(
            [rag_result.get("answer", "")], rag_result.get("evidence_chain", []),
        )
        citation_integrity["coverage"] = coverage
    missing_evidence = list(rag_result.get("missing_evidence", []))
    for message in citation_failure_messages(citation_integrity):
        if message not in missing_evidence:
            missing_evidence.append(message)
    for message in citation_coverage_messages(coverage):
        if message not in missing_evidence:
            missing_evidence.append(message)

    result = {
        "scenario": scenario,
        "summary": rag_result.get("answer", ""),
        "risk_level": risk_level,
        "risk_types": risk_types,
        "risk_categories": categories,
        "legal_basis": legal_basis,
        "recommended_actions": rag_result.get("recommended_actions", []),
        "confidence": {
            "answer": rag_result.get("answer_confidence", rag_result.get("confidence_score")),
            "retrieval": rag_result.get("retrieval_confidence"),
            "overall": calculate_overall_confidence(
                rag_result.get("answer_confidence", rag_result.get("confidence_score")),
                rag_result.get("retrieval_confidence"),
            ),
        },
        "needs_human_review": (
            bool(rag_result.get("needs_human_review"))
            or not citation_integrity.get("passed", True)
            or bool(coverage.get("requires_review"))
        ),
        "missing_evidence": missing_evidence,
        "citation_integrity": citation_integrity,
        "risk_type_evidence": rag_result.get("risk_type_evidence", []),
        "recommended_action_evidence": rag_result.get("recommended_action_evidence", []),
        "evidence_chain": rag_result.get("evidence_chain", []),
        "material_sources": rag_result.get("material_sources", []),
        "filters": rag_result.get("filters", {}),
    }
    _apply_evidence_guardrails(result, expected_risk_domain=expected_risk_domain)
    if "debug_info" in rag_result:
        result["debug_info"] = rag_result["debug_info"]
    return result


RISK_DOMAIN_RELEVANCE_TERMS: dict[str, tuple[str, ...]] = {
    "cross_border_supply_chain": (
        "出口", "进口", "海关", "关税", "原产地", "供应链", "国际贸易", "货物",
        "贸易", "运输", "物流", "制裁", "出口管制", "外汇",
    ),
    "technology_ip": ("专利", "商标", "著作权", "商业秘密", "技术秘密", "许可", "侵权"),
    "product_commercialization": ("产品", "广告", "宣传", "消费者", "质量", "不正当竞争", "反垄断"),
    "corporate_finance_governance": ("公司", "股东", "董事", "融资", "财务", "证券", "审计", "治理"),
    "data_model_governance": (
        "数据", "个人信息", "隐私", "网络", "算法", "模型", "信息安全", "数据出境",
    ),
}


def _apply_evidence_guardrails(result: dict[str, Any], *, expected_risk_domain: str | None) -> None:
    """Fail closed when the evidence cannot support a domain-specific label.

    Uploaded business documents can establish facts, but are intentionally not
    treated as legal authority.  A risk level/type is therefore withheld when
    citation verification fails or the retrieved legal evidence is unrelated to
    the event's declared risk domain.
    """
    integrity = result.get("citation_integrity") or {}
    coverage = integrity.get("coverage") or {}
    evidence = list(result.get("evidence_chain") or [])
    domain_relevant = has_domain_relevant_evidence(evidence, expected_risk_domain)
    failures: list[str] = []
    if not integrity.get("passed", True):
        failures.append("引用完整性校验失败，不能形成风险等级或领域标签")
    if coverage.get("requires_review"):
        failures.append("引用覆盖不足，核心法律判断未获得可追溯证据支持")
    if expected_risk_domain and not domain_relevant:
        failures.append("检索到的法源与申报风险领域不匹配，需补充直接适用法源")
    if not failures:
        result["evidence_guardrail"] = {
            "status": "passed",
            "expected_risk_domain": expected_risk_domain,
            "domain_relevant_evidence": domain_relevant,
            "citation_coverage": coverage,
        }
        return

    missing = list(result.get("missing_evidence") or [])
    for failure in failures:
        if failure not in missing:
            missing.append(failure)
    result.update({
        "summary": "现有证据不足以形成该风险领域的具体法律结论；请补充直接适用法源后由人工复核。",
        "risk_level": None,
        "risk_types": [],
        "risk_categories": [],
        "recommended_actions": [],
        "risk_type_evidence": [],
        "recommended_action_evidence": [],
        "needs_human_review": True,
        "missing_evidence": missing,
        "decision_state": "pending_evidence",
        "evidence_guardrail": {
            "status": "blocked",
            "expected_risk_domain": expected_risk_domain,
            "domain_relevant_evidence": domain_relevant,
            "citation_coverage": coverage,
            "reasons": failures,
        },
    })


def has_domain_relevant_evidence(
    evidence_chain: list[dict[str, Any]],
    expected_risk_domain: str | None,
) -> bool:
    if not expected_risk_domain:
        return bool(evidence_chain)
    terms = RISK_DOMAIN_RELEVANCE_TERMS.get(expected_risk_domain)
    if not terms:
        return bool(evidence_chain)
    for item in evidence_chain:
        if item.get("type") == "web_result":
            continue
        searchable = " ".join(str(item.get(key) or "") for key in (
            "source", "law_name", "document_type", "category", "content", "article", "section_no",
        ))
        if any(term in searchable for term in terms):
            return True
    return False


def build_legal_basis(evidence_chain: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    basis = []
    seen = set()
    for item in evidence_chain:
        citation = item.get("citation") or item.get("source")
        if not citation or citation in seen:
            continue
        seen.add(citation)
        basis.append({
            "citation": citation,
            "source": item.get("source", ""),
            "law_name": item.get("law_name", item.get("source", "")),
            "document_type": item.get("document_type", ""),
            "law_level": item.get("law_level", ""),
            "article_no": item.get("article_no"),
            "section_no": item.get("section_no", ""),
            "rerank_score": item.get("rerank_score"),
        })
        if len(basis) >= limit:
            break
    return basis


def normalize_output_risk_types(raw_types: list[str], categories: list[dict]) -> list[str]:
    normalized = []
    for item in raw_types or []:
        if item and item not in normalized:
            normalized.append(item)
    for category in categories:
        name = category["name"]
        if name not in normalized:
            normalized.append(name)
    return normalized


def calculate_overall_confidence(answer_confidence: float | None, retrieval_confidence: float | None) -> float | None:
    if answer_confidence is None and retrieval_confidence is None:
        return None
    if answer_confidence is None:
        return round(float(retrieval_confidence), 2)
    if retrieval_confidence is None:
        return round(float(answer_confidence), 2)
    return round(min(float(answer_confidence), float(retrieval_confidence)), 2)
