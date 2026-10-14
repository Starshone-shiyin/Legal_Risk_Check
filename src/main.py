import asyncio
import json
import logging
import re
import time
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.core.citations import assess_citation_coverage, citation_coverage_messages, citation_failure_messages, verify_citation_integrity
from src.core.vectorstore import COLLECTION_NAME
from src.rag.retriever import rag_query
from src.rag.local_fallback import answer_from_local_knowledge
from src.rag.general_chat import answer_general_chat
from src.rag.query_routing import decide_ask_route
from src.risk.analyzer import analyze_risk, has_domain_relevant_evidence
from src.risk.report import generate_risk_report_export, generate_risk_report
from src.product.router import router as product_router
from src.supply_chain.router import router as supply_chain_router
from src.developer_debug.router import router as developer_debug_router
from src.external_risk.provider_config import load_provider_config
from src.external_risk.router import router as external_risk_router, service as external_risk_service
from src.external_risk.schemas import SearchDomain, SearchMode
from src.external_risk.web_search import OnlineSearchService, search_results_to_evidence, should_search_for_retrieval_gap
from src.document_ingest.router import router as document_ingest_router
from src.document_ingest.service import DocumentIngestError, DocumentIngestService
from src.internal_risk.router import router as internal_risk_router
from src.risk_intake.router import router as risk_intake_router, service as risk_intake_service
from src.risk_intake.schemas import ExternalSyncSourceHealth
from src.runtime_settings.router import router as runtime_settings_router
from src.skills.router import configure_execution_handler, router as skills_router
from src.skills.schemas import SkillExecutionStep, SkillRecord, SkillRunRequest, SkillRunResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="风控系统", version="0.5.4")


class ErrorDetail(BaseModel):
    code: str
    message: str


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product_router)
app.include_router(supply_chain_router)
app.include_router(developer_debug_router)
app.include_router(external_risk_router)
app.include_router(document_ingest_router)
app.include_router(internal_risk_router)
app.include_router(risk_intake_router)
app.include_router(runtime_settings_router)
app.include_router(skills_router)


@app.on_event("startup")
async def start_external_intelligence_monitor() -> None:
    config = load_provider_config()
    if not (config.intelligence_scheduler_enabled and config.live_enabled and config.intelligence_enabled):
        return

    async def monitor() -> None:
        while True:
            try:
                signals = await asyncio.to_thread(external_risk_service.poll_intelligence)
                intelligence = await asyncio.to_thread(external_risk_service.intelligence_status)
                provider_failed = intelligence.provider.status == "unavailable"
                blocked_source_ids = [
                    feed.feed_id for feed in intelligence.feeds
                    if feed.status in {"failed", "not_called"}
                ]
                health = ExternalSyncSourceHealth(
                    source_name=intelligence.provider.provider_id,
                    status="failed" if provider_failed else ("healthy" if intelligence.cache_fresh else "stale"),
                    fresh=bool(intelligence.cache_fresh and not provider_failed),
                    cache_updated_at=intelligence.cache_updated_at,
                    blocked_source_ids=blocked_source_ids,
                    message=intelligence.provider.message,
                )
                await asyncio.to_thread(risk_intake_service.sync_polled_signals, signals, health)
            except Exception as exc:
                logger.exception("External intelligence polling failed")
                try:
                    await asyncio.to_thread(risk_intake_service.record_poll_failure, str(exc))
                except Exception:
                    logger.exception("Failed to record external intelligence polling failure")
            await asyncio.sleep(max(config.intelligence_poll_seconds, 30))

    app.state.external_intelligence_task = asyncio.create_task(monitor())


@app.on_event("shutdown")
async def stop_external_intelligence_monitor() -> None:
    task = getattr(app.state, "external_intelligence_task", None)
    if task:
        task.cancel()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    k: int = Field(default=5, ge=1, le=20)
    collection_name: str = COLLECTION_NAME
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
    score_threshold: float | None = Field(default=None, ge=0, le=1)
    document_task_ids: list[str] = Field(default_factory=list, max_length=3)
    debug: bool = False
    online_search_mode: SearchMode = "auto"
    online_search_domain: SearchDomain = "general"
    # Optional business context makes the evidence-to-domain gate explicit.
    expected_risk_domain: Literal[
        "data_model_governance",
        "technology_ip",
        "product_commercialization",
        "cross_border_supply_chain",
        "corporate_finance_governance",
    ] | None = None


class AskResponse(BaseModel):
    answer: str
    confidence_score: float | None
    answer_confidence: float | None = None
    retrieval_confidence: float | None = None
    needs_human_review: bool = False
    missing_evidence: list[str] = Field(default_factory=list)
    risk_level: str | None = None
    risk_types: list[str] = Field(default_factory=list)
    risk_type_evidence: list[dict] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    recommended_action_evidence: list[dict] = Field(default_factory=list)
    citation_integrity: dict = Field(default_factory=dict)
    evidence_chain: list[dict]
    rejected_evidence: list[dict] = Field(default_factory=list)
    evidence_sufficiency: dict = Field(default_factory=dict)
    material_sources: list[dict] = Field(default_factory=list)
    retrieval_status: dict = Field(default_factory=dict)
    filters: dict
    debug_info: dict | None = None


class RiskAnalyzeRequest(BaseModel):
    scenario: str = Field(..., min_length=1)
    k: int = Field(default=5, ge=1, le=20)
    collection_name: str = COLLECTION_NAME
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
    score_threshold: float | None = Field(default=None, ge=0, le=1)
    document_task_ids: list[str] = Field(default_factory=list, max_length=3)
    debug: bool = False
    expected_risk_domain: Literal[
        "data_model_governance",
        "technology_ip",
        "product_commercialization",
        "cross_border_supply_chain",
        "corporate_finance_governance",
    ] | None = None


class RiskAnalyzeResponse(BaseModel):
    scenario: str
    summary: str
    risk_level: str | None
    risk_types: list[str] = Field(default_factory=list)
    risk_categories: list[dict] = Field(default_factory=list)
    legal_basis: list[dict] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: dict
    needs_human_review: bool = False
    missing_evidence: list[str] = Field(default_factory=list)
    citation_integrity: dict = Field(default_factory=dict)
    risk_type_evidence: list[dict] = Field(default_factory=list)
    recommended_action_evidence: list[dict] = Field(default_factory=list)
    evidence_chain: list[dict] = Field(default_factory=list)
    rejected_evidence: list[dict] = Field(default_factory=list)
    material_sources: list[dict] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)
    debug_info: dict | None = None


class RiskReportResponse(BaseModel):
    title: str
    scenario: str
    executive_summary: str
    risk_level: str | None
    risk_findings: list[dict] = Field(default_factory=list)
    action_plan: list[dict] = Field(default_factory=list)
    legal_basis: list[dict] = Field(default_factory=list)
    confidence: dict = Field(default_factory=dict)
    human_review_required: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    citation_integrity: dict = Field(default_factory=dict)
    evidence_chain: list[dict] = Field(default_factory=list)
    rejected_evidence: list[dict] = Field(default_factory=list)
    material_sources: list[dict] = Field(default_factory=list)
    source_analysis: dict = Field(default_factory=dict)


class RiskReportExportRequest(RiskAnalyzeRequest):
    export_format: Literal["markdown", "json"] = "markdown"
    include_evidence_chain: bool = True
    include_source_analysis: bool = False


INSUFFICIENT_ANSWER_MARKERS = [
    "无法回答",
    "无法基于",
    "无法理解",
    "不包含",
    "未包含",
    "缺乏",
    "无关",
    "未提供具体",
]

HARD_INSUFFICIENT_ANSWER_MARKERS = [
    "未检索到足以回答",
    "未检索到可引用",
    "无法基于现有依据回答",
    "无法基于现有证据回答",
    "无法基于现有材料回答",
]

OPEN_GUIDANCE_HINTS = [
    "如何",
    "怎么",
    "怎么办",
    "建议",
    "方案",
    "步骤",
    "流程",
    "低成本",
    "初创",
    "没有专门法务",
    "开展",
]

DATA_COMPLIANCE_HINTS = [
    "数据合规",
    "个人信息",
    "隐私",
    "数据安全",
    "网络安全",
    "通讯录",
    "用户数据",
    "数据处理",
]

OPEN_GUIDANCE_PLACEHOLDER_MARKERS = [
    "未包含针对",
    "未提供针对",
    "缺少针对",
    "没有针对",
    "无法给出具体",
]


def _is_insufficient_answer(result: dict[str, Any]) -> bool:
    answer = str(result.get("answer") or "")
    if any(marker in answer for marker in HARD_INSUFFICIENT_ANSWER_MARKERS):
        return True
    if "不包含" in answer and "无法基于" in answer:
        return True
    return not result.get("evidence_chain")


def _has_substantive_guidance(result: dict[str, Any]) -> bool:
    answer = str(result.get("answer") or "")
    if len(answer.strip()) >= 80 and any(term in answer for term in ["建议", "应当", "可以", "需要", "步骤", "措施"]):
        return True
    return bool(result.get("recommended_actions") or result.get("risk_types"))


def _has_open_guidance_placeholder(result: dict[str, Any]) -> bool:
    """Only replace an explicit placeholder, never a substantive RAG answer."""
    answer = str(result.get("answer") or "")
    return any(marker in answer for marker in OPEN_GUIDANCE_PLACEHOLDER_MARKERS)


def _is_open_data_compliance_guidance(question: str) -> bool:
    if _is_complex_case_question(question):
        return False
    return any(hint in question for hint in OPEN_GUIDANCE_HINTS) and any(
        hint in question for hint in DATA_COMPLIANCE_HINTS
    )


def _is_complex_case_question(question: str) -> bool:
    markers = ["公司背景", "事件经过", "问题清单", "融资尽调", "IPO", "序号", "事件1", "事件2"]
    if any(marker in question for marker in markers):
        return True
    numbered_questions = len(re.findall(r"(?:^|\n)\s*(?:\d+|[一二三四五六七八九十]+)[\.、\s]", question))
    if numbered_questions >= 3:
        return True
    return len(question) >= 900 and question.count("？") + question.count("?") >= 3


def _citation_label(item: dict[str, Any]) -> str:
    law_name = item.get("law_name") or item.get("source") or "已检索依据"
    article = item.get("article") or item.get("section_no") or item.get("citation") or ""
    return f"{law_name}{article}" if article and str(article) not in str(law_name) else str(law_name)


def _enhance_open_data_compliance_guidance(result: dict[str, Any], question: str) -> dict[str, Any]:
    if (
        not _is_open_data_compliance_guidance(question)
        or not result.get("evidence_chain")
        or not _has_open_guidance_placeholder(result)
    ):
        return result

    normalized = dict(result)
    evidence_chain = list(normalized.get("evidence_chain") or [])
    citations = [_citation_label(item) for item in evidence_chain[:4]]
    citation_text = "、".join(citations) if citations else "当前证据链"
    normalized["answer"] = (
        "可以把这类开放性问题拆成“最低合规底座 + 高风险事项升级处理”。"
        f"当前证据主要支持你需要建立个人信息/数据处理的合规审计、自评估和安全管理机制（参考：{citation_text}），"
        "但不会替你给出某个行业的完整制度模板。\n"
        "建议按低成本路径推进：\n"
        "1. 先做数据清单：列出收集哪些数据、来自哪里、给谁用、保存多久、是否共享或出境。\n"
        "2. 做场景分级：优先处理通讯录、位置、身份信息、敏感个人信息、对外共享和委托处理等高风险场景。\n"
        "3. 补齐最小文件包：隐私政策/告知文本、授权同意记录、员工权限表、第三方数据处理协议、删除和响应流程。\n"
        "4. 建立轻量审计节奏：每季度自查一次数据清单、权限、第三方接口、日志和用户投诉，不必一开始搭复杂系统。\n"
        "5. 需要升级时再请外部律师或安全顾问复核：例如大规模处理个人信息、处理敏感个人信息、数据出境、发生安全事件或融资尽调。\n"
        "因此，低成本做法不是“不做合规”，而是先把高频、高风险、可留痕的基础动作固化下来。"
    )
    actions = list(normalized.get("recommended_actions") or [])
    suggested_actions = [
        "建立数据清单和处理目的台账。",
        "按个人信息、敏感个人信息、对外共享、委托处理和出境场景做风险分级。",
        "补齐隐私告知、授权同意、权限控制、第三方协议和日志留痕。",
        "设置季度自查机制，重大变化时再做专项复核。",
    ]
    for action in suggested_actions:
        if action not in actions:
            actions.append(action)
    normalized["recommended_actions"] = actions
    risk_types = list(normalized.get("risk_types") or [])
    for risk_type in ["数据合规体系不足", "个人信息处理合规风险"]:
        if risk_type not in risk_types:
            risk_types.append(risk_type)
    normalized["risk_types"] = risk_types
    missing = [
        item
        for item in list(normalized.get("missing_evidence") or [])
        if "当前知识库缺少与该问题直接相关" not in str(item)
    ]
    coverage_note = "当前证据支持基础合规义务和自查方向；具体制度模板、行业监管细则和公司业务数据清单仍需人工补充。"
    if coverage_note not in missing:
        missing.insert(0, coverage_note)
    normalized["missing_evidence"] = missing
    normalized["needs_human_review"] = True
    normalized["confidence_score"] = min(float(normalized.get("confidence_score") or 0.55), 0.65)
    normalized["answer_confidence"] = min(float(normalized.get("answer_confidence") or normalized["confidence_score"]), 0.65)
    normalized["filters"] = {
        **dict(normalized.get("filters") or {}),
        "answer_status": "guidance_with_limited_direct_basis",
    }
    normalized["debug_info"] = {
        **dict(normalized.get("debug_info") or {}),
        "postprocess": "open_data_compliance_guidance",
    }
    return normalized


def _missing_evidence_hint(question: str) -> str:
    if "竞业" in question or "保密" in question or "员工" in question:
        return "当前知识库缺少与竞业限制、保密义务、经济补偿、违约金、适用人员和期限直接相关的劳动法律法规依据。"
    if len(question.strip()) < 8 or question.strip().isascii():
        return "当前问题不够具体，尚不能匹配到可引用的法律法规依据；请补充业务场景、主体和争议事实。"
    return "当前知识库缺少与该问题直接相关的法律法规依据；请补充相应法律法规、司法解释或内部制度条文后重试。"


def _ask_evidence_gate(
    result: dict[str, Any],
    *,
    expected_risk_domain: str | None,
) -> tuple[dict[str, Any], list[str]]:
    """Return independently checked citation data and all decision blockers."""
    evidence = list(result.get("evidence_chain") or [])
    answer = str(result.get("answer") or "")
    supplied = dict(result.get("citation_integrity") or {})
    recomputed = verify_citation_integrity([answer], evidence)
    coverage = assess_citation_coverage([answer], evidence)
    integrity = {
        **supplied,
        **recomputed,
        "passed": bool(supplied.get("passed", True)) and bool(recomputed.get("passed", True)),
        "coverage": coverage,
    }
    blockers: list[str] = []
    if not integrity["passed"]:
        blockers.append("引用完整性校验失败，不能输出风险等级、风险标签或处置建议")
    if coverage.get("requires_review"):
        blockers.append("引用覆盖不足，核心法律判断不能进入风险决策门槛")
    if expected_risk_domain and not has_domain_relevant_evidence(evidence, expected_risk_domain):
        blockers.append("检索证据与申报风险领域不匹配，不能输出风险等级、风险标签或处置建议")
    return integrity, blockers


def _recent_risk_observation_integrity() -> dict[str, Any]:
    """Describe the deliberate non-legal-evidence route used by risk snapshots."""
    return {
        "passed": True,
        "cited": [],
        "supported": [],
        "unsupported": [],
        "status": "external_fact_observation",
        "coverage": {
            "evidence_has_citations": False,
            "has_any_citation": False,
            "supported_citations": [],
            "substantive_unit_count": 0,
            "cited_substantive_unit_count": 0,
            "uncited_substantive_unit_count": 0,
            "core_legal_claim_unit_count": 0,
            "uncited_core_legal_claim_unit_count": 0,
            "has_structured_legal_basis": False,
            "warnings": [],
            "requires_review": False,
        },
    }


def _recent_risk_observation_payload(
    question: str,
    *,
    evidence: list[dict[str, Any]],
    search_mode: str,
) -> dict[str, Any]:
    """Return a bounded external-risk snapshot without making legal findings."""
    scope_note = "问题未说明企业、行业、地区或项目阶段，以下仅为宽口径外部风险观察。"
    if not evidence:
        reason = "联网检索已关闭" if search_mode == "off" else "当前未获取到可追溯的实时风险信号"
        return {
            "answer": (
                "## 近期风险观察\n\n"
                f"{reason}，因此暂不能形成“近期风险事项”清单。\n\n"
                "这不表示不存在风险，只表示当前没有足以核验的实时事实来源。"
                "请补充企业/行业、地区和关注周期，或在市场风险服务中刷新信号后再评估。"
            ),
            "confidence_score": 0.0,
            "answer_confidence": 0.0,
            "retrieval_confidence": 0.0,
            "needs_human_review": True,
            "missing_evidence": [reason, scope_note],
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "citation_integrity": _recent_risk_observation_integrity(),
            "evidence_chain": [],
            "evidence_sufficiency": {
                "status": "external_signals_unavailable",
                "legal_conclusion_permitted": False,
                "external_signal_count": 0,
            },
            "material_sources": [],
            "filters": {
                "answer_status": "recent_risk_signals_unavailable",
                "answer_mode": "recent_risk_observation",
                "fact_source_policy": "external_signals_only",
                "requires_external_facts": True,
            },
            "debug_info": {"postprocess": "recent_risk_observation_unavailable"},
        }

    observations: list[str] = []
    trust_scores: list[float] = []
    for index, item in enumerate(evidence[:5], start=1):
        title = str(item.get("section_title") or "未命名外部信号").strip()
        content = str(item.get("content") or "").split("\n")
        summary = next((line.strip() for line in content[1:] if line.strip() and not line.startswith(("URL:", "抓取时间:"))), "")
        source = str(item.get("source") or "").strip()
        fetched_at = next((line.removeprefix("抓取时间:").strip() for line in content if line.startswith("抓取时间:")), "未知")
        observations.append(
            f"### {index}. 待核验信号：{title}\n"
            f"{summary or '检索结果未提供可摘要内容。'}\n\n"
            f"- 来源：{source or '未知'}\n- 抓取时间：{fetched_at}"
        )
        try:
            trust_scores.append(float(item.get("trust_score") or 0.0))
        except (TypeError, ValueError):
            pass

    confidence = round(min(0.7, max(0.25, (sum(trust_scores) / len(trust_scores)) if trust_scores else 0.25)), 2)
    return {
        "answer": (
            "## 近期风险观察\n\n"
            f"{scope_note} 下列内容是外部信息信号，**不是对任何主体的违法、责任或风险等级认定**。\n\n"
            + "\n\n".join(observations)
            + "\n\n## 使用边界\n\n"
            "请先核验原始网页、发布时间和与本主体的关联性；只有补充具体事实并匹配适用法源后，才可形成法律风险结论或整改要求。"
        ),
        "confidence_score": confidence,
        "answer_confidence": confidence,
        "retrieval_confidence": confidence,
        "needs_human_review": True,
        "missing_evidence": [scope_note, "外部网页仅用于事实观察，不能替代法律法规或其他一级法源。"],
        "risk_level": None,
        "risk_types": [],
        "risk_type_evidence": [],
        "recommended_actions": [],
        "recommended_action_evidence": [],
        "citation_integrity": _recent_risk_observation_integrity(),
        "evidence_chain": evidence,
        "evidence_sufficiency": {
            "status": "external_signal_observation",
            "legal_conclusion_permitted": False,
            "external_signal_count": len(evidence),
        },
        "material_sources": [],
        "filters": {
            "answer_status": "recent_risk_observation",
            "answer_mode": "recent_risk_observation",
            "fact_source_policy": "external_signals_only",
            "requires_external_facts": True,
        },
        "debug_info": {"postprocess": "recent_risk_observation"},
    }


def _normalize_ask_result(
    result: dict[str, Any],
    question: str,
    expected_risk_domain: str | None = None,
) -> dict[str, Any]:
    if dict(result.get("filters") or {}).get("answer_status") in {
        "recent_risk_observation",
        "recent_risk_signals_unavailable",
    }:
        return result
    result = _enhance_open_data_compliance_guidance(result, question)
    integrity, evidence_blockers = _ask_evidence_gate(
        result, expected_risk_domain=expected_risk_domain,
    )
    if not _is_insufficient_answer(result) and not evidence_blockers:
        if dict(result.get("filters") or {}).get("answer_status") == "guidance_with_limited_direct_basis":
            normalized = dict(result)
            normalized["citation_integrity"] = integrity
            return normalized
        if result.get("missing_evidence") and _has_substantive_guidance(result) and result.get("evidence_chain"):
            normalized = dict(result)
            normalized["citation_integrity"] = integrity
            normalized["needs_human_review"] = True
            normalized["filters"] = {
                **dict(normalized.get("filters") or {}),
                "answer_status": "answered_with_review_note",
            }
            normalized["debug_info"] = {
                **dict(normalized.get("debug_info") or {}),
                "postprocess": "preserved_evidence_with_review_note",
            }
            return normalized
        normalized = dict(result)
        normalized["citation_integrity"] = integrity
        return normalized

    normalized = dict(result)
    rejected_evidence = list(normalized.get("evidence_chain") or [])
    missing = list(normalized.get("missing_evidence", []))
    hint = _missing_evidence_hint(question)
    if hint not in missing:
        missing.insert(0, hint)
    for blocker in evidence_blockers:
        if blocker not in missing:
            missing.append(blocker)
    for message in citation_failure_messages(integrity) + citation_coverage_messages(integrity.get("coverage") or {}):
        if message not in missing:
            missing.append(message)
    normalized.update(
        {
            "answer": "当前证据未通过风险决策门槛，暂不输出风险等级、风险标签或处置建议；请补充直接适用且可追溯的证据后由人工复核。",
            "confidence_score": min(float(normalized.get("confidence_score") or 0.25), 0.25),
            "answer_confidence": min(float(normalized.get("answer_confidence") or 0.25), 0.25),
            "retrieval_confidence": min(float(normalized.get("retrieval_confidence") or 0.2), 0.2),
            "needs_human_review": True,
            "missing_evidence": missing,
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "evidence_chain": [],
            "rejected_evidence": rejected_evidence,
            "citation_integrity": {
                **integrity,
                "status": "insufficient_direct_evidence",
                "requires_human_review": True,
            },
            "filters": {
                **dict(normalized.get("filters") or {}),
                "answer_status": "insufficient_direct_evidence",
                "expected_risk_domain": expected_risk_domain,
            },
            "debug_info": {
                **dict(normalized.get("debug_info") or {}),
                "postprocess": "insufficient_direct_evidence",
            },
        }
    )
    return normalized


def _build_retrieval_status(result: dict[str, Any]) -> dict[str, Any]:
    """Expose a compact, user-safe provenance summary for the workbench.

    This deliberately distinguishes a completed RAG retrieval with no usable
    evidence from a route that did not retrieve at all and from a local
    fail-safe answer.  It is not debug trace data and does not disclose server
    paths, credentials, or internal provider responses.
    """
    filters = dict(result.get("filters") or {})
    answer_status = str(filters.get("answer_status") or "")
    fallback = str(filters.get("fallback") or "")
    evidence_count = len(result.get("evidence_chain") or [])
    material_count = len(result.get("material_sources") or [])
    retrieval_confidence = result.get("retrieval_confidence")

    base = {
        "evidence_count": evidence_count,
        "material_count": material_count,
        "retrieval_confidence": retrieval_confidence,
        "answer_status": answer_status or None,
        "route": filters.get("ask_route"),
        "route_reason": filters.get("ask_route_reason"),
    }
    if answer_status == "general_chat":
        return {
            **base,
            "mode": "general_chat",
            "attempted": False,
            "label": "通用对话（未执行 RAG 检索）",
            "reason": "该问题未被识别为需要证据的风险或合规决策。",
        }
    if fallback:
        return {
            **base,
            "mode": "local_fallback",
            "attempted": True,
            "label": "本地法规兜底（RAG 服务异常）",
            "reason": "本次回答来自受控本地法规文本，需人工复核，不能视为正常 RAG 命中。",
        }
    if answer_status in {"recent_risk_observation", "recent_risk_signals_unavailable"}:
        return {
            **base,
            "mode": "external_observation",
            "attempted": True,
            "label": "外部事实观察",
            "reason": "该结果用于观察外部信号，不构成法律风险结论。",
        }
    if answer_status == "insufficient_direct_evidence" or evidence_count == 0:
        return {
            **base,
            "mode": "rag_no_usable_evidence",
            "attempted": True,
            "label": "RAG 已检索，但没有可用于决策的直接证据",
            "reason": "系统未将无关或不足的候选材料伪装成可引用结论。",
        }
    return {
        **base,
        "mode": "rag",
        "attempted": True,
        "label": "RAG 检索与证据校验已完成",
        "reason": "回答中的结论应结合右侧证据与人工复核使用。",
    }


def _ask_response_payload(normalized_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "answer": normalized_result["answer"],
        "confidence_score": normalized_result.get("confidence_score"),
        "answer_confidence": normalized_result.get("answer_confidence"),
        "retrieval_confidence": normalized_result.get("retrieval_confidence"),
        "needs_human_review": normalized_result.get("needs_human_review", False),
        "missing_evidence": normalized_result.get("missing_evidence", []),
        "risk_level": normalized_result.get("risk_level"),
        "risk_types": normalized_result.get("risk_types", []),
        "risk_type_evidence": normalized_result.get("risk_type_evidence", []),
        "recommended_actions": normalized_result.get("recommended_actions", []),
        "recommended_action_evidence": normalized_result.get("recommended_action_evidence", []),
        "citation_integrity": normalized_result.get("citation_integrity", {}),
        "evidence_chain": normalized_result.get("evidence_chain", []),
        "rejected_evidence": normalized_result.get("rejected_evidence", []),
        "evidence_sufficiency": normalized_result.get("evidence_sufficiency", {}),
        "material_sources": normalized_result.get("material_sources", []),
        "retrieval_status": _build_retrieval_status(normalized_result),
        "filters": normalized_result.get("filters", {}),
        "debug_info": normalized_result.get("debug_info"),
    }


def _run_ask_request(request: AskRequest) -> dict[str, Any]:
    route = decide_ask_route(
        request.question,
        has_uploaded_materials=bool(request.document_task_ids),
    )
    if route.name == "recent_risk_observation":
        external_evidence: list[dict[str, Any]] = []
        if request.online_search_mode != "off":
            search_service = OnlineSearchService()
            search_plan = search_service.plan(
                request.question,
                mode=request.online_search_mode,
                domain=request.online_search_domain,
            )
            if search_plan.should_search:
                external_evidence = search_results_to_evidence(search_service.search(search_plan))
        return _ask_response_payload(_recent_risk_observation_payload(
            request.question,
            evidence=external_evidence,
            search_mode=request.online_search_mode,
        ))
    # An explicit force-search setting is a user override of the default
    # conversation route and preserves the existing retrieval API contract.
    if route.name == "general_chat" and request.online_search_mode != "force":
        chat_result = answer_general_chat(request.question)
        chat_result["filters"] = {
            **dict(chat_result.get("filters") or {}),
            "ask_route": route.name,
            "ask_route_reason": route.reason,
        }
        return _ask_response_payload(chat_result)

    document_service = DocumentIngestService()
    user_materials = document_service.build_llm_materials(request.document_task_ids)
    external_evidence = []
    if request.online_search_mode == "force":
        search_service = OnlineSearchService()
        search_plan = search_service.plan(
            request.question,
            mode=request.online_search_mode,
            domain=request.online_search_domain,
        )
        external_evidence = search_results_to_evidence(search_service.search(search_plan))
    result = rag_query(
        request.question,
        collection_name=request.collection_name,
        k=request.k,
        doc_type=request.doc_type,
        block_type=request.block_type,
        document_type=request.document_type,
        law_name=request.law_name,
        source=request.source,
        law_level=request.law_level,
        authority_level=request.authority_level,
        jurisdiction=request.jurisdiction,
        issuing_authority=request.issuing_authority,
        legal_effect=request.legal_effect,
        standard_type=request.standard_type,
        case_type=request.case_type,
        patent_type=request.patent_type,
        category=request.category,
        version=request.version,
        score_threshold=request.score_threshold,
        user_materials=user_materials,
        external_evidence=external_evidence,
        debug=request.debug,
    )
    if request.online_search_mode == "auto":
        search_service = OnlineSearchService()
        search_plan = search_service.plan(
            request.question,
            mode="auto",
            domain=request.online_search_domain,
        )
        if not search_plan.should_search and should_search_for_retrieval_gap(
            result,
            question=request.question,
            domain=request.online_search_domain,
        ):
            search_plan = search_service.plan(
                request.question,
                mode="force",
                domain=request.online_search_domain,
            )
        if search_plan.should_search:
            external_evidence = search_results_to_evidence(search_service.search(search_plan))
            if external_evidence:
                result = rag_query(
                    request.question,
                    collection_name=request.collection_name,
                    k=request.k,
                    doc_type=request.doc_type,
                    block_type=request.block_type,
                    document_type=request.document_type,
                    law_name=request.law_name,
                    source=request.source,
                    law_level=request.law_level,
                    authority_level=request.authority_level,
                    jurisdiction=request.jurisdiction,
                    issuing_authority=request.issuing_authority,
                    legal_effect=request.legal_effect,
                    standard_type=request.standard_type,
                    case_type=request.case_type,
                    patent_type=request.patent_type,
                    category=request.category,
                    version=request.version,
                    score_threshold=request.score_threshold,
                    user_materials=user_materials,
                    external_evidence=external_evidence,
                    debug=request.debug,
                )
    result["filters"] = {
        **dict(result.get("filters") or {}),
        "ask_route": route.name,
        "ask_route_reason": route.reason,
    }
    normalized_result = _normalize_ask_result(
        result, request.question, expected_risk_domain=request.expected_risk_domain,
    )
    return _ask_response_payload(normalized_result)


def _skill_step_parameters(plan: list[SkillExecutionStep], node_type: str) -> dict[str, Any]:
    for step in plan:
        if step.node_type == node_type:
            return step.parameters
    return {}


async def _execute_skill_run(
    skill: SkillRecord,
    request: SkillRunRequest,
    plan: list[SkillExecutionStep],
) -> SkillRunResponse:
    """Run a validated Skill through the same bounded ask pipeline as the legal workspace."""
    retrieval = _skill_step_parameters(plan, "retrieve")
    web = _skill_step_parameters(plan, "web_supplement")
    gate = _skill_step_parameters(plan, "evidence_gate")
    review = _skill_step_parameters(plan, "human_review")
    output = _skill_step_parameters(plan, "report_output")
    extract = _skill_step_parameters(plan, "document_extract")

    document_ids = request.document_task_ids
    if extract:
        document_ids = document_ids[: int(extract.get("max_documents", 3))]
    ask_request = AskRequest(
        question=request.question,
        k=int(retrieval.get("top_k", 5)),
        document_task_ids=document_ids,
        online_search_mode=web.get("mode", "off"),
        online_search_domain="legal",
        debug=request.debug,
    )
    result = await asyncio.to_thread(_run_ask_request, ask_request)
    score = float((result.get("evidence_sufficiency") or {}).get("score") or 0.0)
    threshold = float(gate.get("min_score", 0.0))
    if review.get("on_insufficient_evidence") and score < threshold:
        result["needs_human_review"] = True
        result.setdefault("missing_evidence", []).append("Skill evidence threshold was not met; human review is required.")

    return SkillRunResponse(
        status="completed",
        skill_id=skill.skill_id,
        execution_plan=plan,
        result=result,
        run_metadata={
            "source": "validated_skill_orchestrator",
            "online_search_mode": ask_request.online_search_mode,
            "output_format": output.get("format", "markdown"),
            "evidence_threshold": threshold,
            "node_count": len(plan),
        },
    )


configure_execution_handler(_execute_skill_run)


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _classify_answer_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "break"
    if re.match(r"^(?:\d+[\.、)]|[一二三四五六七八九十]+[、.)]|[-*•])\s*", stripped):
        return "list_item"
    if len(stripped) <= 28 and re.search(r"(结论|依据|证据|建议|动作|风险|优先级|问题|补救|维权|制度)[:：]?$", stripped):
        return "heading"
    return "paragraph"


def _split_answer_line(line: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    pending = line
    punctuation = "。；;！？!?，,：:"
    while pending:
        if len(pending) <= max_chars:
            pieces.append(pending)
            break
        window = pending[:max_chars]
        split_at = max(window.rfind(mark) for mark in punctuation)
        if split_at < max_chars // 3:
            split_at = max_chars - 1
        pieces.append(pending[: split_at + 1])
        pending = pending[split_at + 1 :].lstrip()
    return pieces


def _answer_chunks(answer: str, max_chars: int = 150) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    normalized = str(answer or "").replace("\r\n", "\n").replace("\r", "\n")
    for raw_line in normalized.splitlines(keepends=True):
        has_newline = raw_line.endswith("\n")
        line = raw_line[:-1] if has_newline else raw_line
        kind = _classify_answer_line(line)
        if kind == "break":
            chunks.append({"text": "\n", "kind": kind})
            continue
        pieces = _split_answer_line(line, max_chars)
        for index, piece in enumerate(pieces):
            text = piece
            if index == len(pieces) - 1 and has_newline:
                text += "\n"
            chunks.append({"text": text, "kind": kind})
    if not chunks and normalized:
        chunks.append({"text": normalized, "kind": "paragraph"})
    return chunks


def _answer_chunk_delay(chunk: dict[str, Any]) -> float:
    text = str(chunk.get("text") or "")
    kind = chunk.get("kind")
    if kind == "break":
        return 0.08
    if kind == "heading":
        return 0.28
    ceiling = 0.78 if kind == "list_item" else 0.66
    return min(ceiling, max(0.2, 0.14 + len(text.strip()) * 0.004))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, response_model_exclude_none=True)
async def ask(request: AskRequest):
    try:
        return AskResponse(**_run_ask_request(request))
    except TimeoutError:
        logger.error("LLM timeout on /ask")
        return _error_response(504, "LLM_TIMEOUT", "AI 模型响应超时，请简化问题后重试。")
    except DocumentIngestError as exc:
        return _error_response(exc.http_status, exc.code, exc.message)
    except Exception as exc:
        logger.exception("Failed to process /ask request, falling back to local knowledge")
        return AskResponse(**_ask_response_payload(answer_from_local_knowledge(request.question, exc)))


@app.post("/ask/stream")
async def ask_stream(request: AskRequest):
    async def event_stream():
        started_at = time.perf_counter()

        def elapsed_ms() -> int:
            return int((time.perf_counter() - started_at) * 1000)

        yield _sse_event(
            "status",
            {"stage": "accepted", "label": "已接收问题", "elapsed_ms": elapsed_ms()},
        )
        await asyncio.sleep(0.02)

        task = asyncio.create_task(asyncio.to_thread(_run_ask_request, request))
        progress = [
            ("planning", "拆解问题与识别法域"),
            ("retrieving", "检索法规和证据链"),
            ("checking", "校验证据充分性"),
            ("drafting", "组织风险结论"),
        ]
        progress_index = 0
        try:
            while not task.done():
                stage, label = progress[min(progress_index, len(progress) - 1)]
                yield _sse_event(
                    "status",
                    {"stage": stage, "label": label, "elapsed_ms": elapsed_ms()},
                )
                progress_index += 1
                await asyncio.sleep(0.8)

            payload = await task
            yield _sse_event(
                "status",
                {"stage": "streaming_answer", "label": "输出分析结果", "elapsed_ms": elapsed_ms()},
            )
            for chunk in _answer_chunks(payload.get("answer", "")):
                yield _sse_event("answer_delta", chunk)
                await asyncio.sleep(_answer_chunk_delay(chunk))
            yield _sse_event("final", {"result": payload, "elapsed_ms": elapsed_ms()})
            yield _sse_event("done", {"elapsed_ms": elapsed_ms()})
        except TimeoutError:
            logger.error("LLM timeout on /ask/stream")
            yield _sse_event(
                "error",
                {
                    "code": "LLM_TIMEOUT",
                    "message": "AI 模型响应超时，请简化问题后重试。",
                    "elapsed_ms": elapsed_ms(),
                },
            )
        except DocumentIngestError as exc:
            yield _sse_event(
                "error",
                {"code": exc.code, "message": exc.message, "elapsed_ms": elapsed_ms()},
            )
        except Exception as exc:
            logger.exception("Failed to process /ask/stream request, falling back to local knowledge")
            fallback = answer_from_local_knowledge(request.question, exc)
            fallback["filters"] = {
                **dict(fallback.get("filters") or {}),
                "ask_route": "legal_rag",
                "ask_route_reason": "stream_fallback",
            }
            fallback = _ask_response_payload(fallback)
            yield _sse_event(
                "status",
                {"stage": "fallback", "label": "启用本地保守兜底", "elapsed_ms": elapsed_ms()},
            )
            for chunk in _answer_chunks(fallback.get("answer", "")):
                yield _sse_event("answer_delta", chunk)
                await asyncio.sleep(_answer_chunk_delay(chunk))
            yield _sse_event("final", {"result": fallback, "elapsed_ms": elapsed_ms()})
            yield _sse_event("done", {"elapsed_ms": elapsed_ms()})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/risk/analyze", response_model=RiskAnalyzeResponse, response_model_exclude_none=True)
async def risk_analyze(request: RiskAnalyzeRequest):
    try:
        result = analyze_risk(
            request.scenario,
            collection_name=request.collection_name,
            k=request.k,
            doc_type=request.doc_type,
            block_type=request.block_type,
            document_type=request.document_type,
            law_name=request.law_name,
            source=request.source,
            law_level=request.law_level,
            authority_level=request.authority_level,
            jurisdiction=request.jurisdiction,
            issuing_authority=request.issuing_authority,
            legal_effect=request.legal_effect,
            standard_type=request.standard_type,
            case_type=request.case_type,
            patent_type=request.patent_type,
            category=request.category,
            version=request.version,
            score_threshold=request.score_threshold,
            debug=request.debug,
            user_materials=DocumentIngestService().build_llm_materials(request.document_task_ids),
            expected_risk_domain=request.expected_risk_domain,
        )
        return RiskAnalyzeResponse(**result)
    except DocumentIngestError as exc:
        return _error_response(exc.http_status, exc.code, exc.message)
    except Exception as exc:
        logger.exception("Failed to process /risk/analyze request")
        return _error_response(500, "INTERNAL_ERROR", "内部服务错误，请稍后重试。")


@app.post("/risk/report", response_model=RiskReportResponse, response_model_exclude_none=True)
async def risk_report(request: RiskAnalyzeRequest):
    try:
        result = generate_risk_report(
            request.scenario,
            collection_name=request.collection_name,
            k=request.k,
            doc_type=request.doc_type,
            block_type=request.block_type,
            document_type=request.document_type,
            law_name=request.law_name,
            source=request.source,
            law_level=request.law_level,
            authority_level=request.authority_level,
            jurisdiction=request.jurisdiction,
            issuing_authority=request.issuing_authority,
            legal_effect=request.legal_effect,
            standard_type=request.standard_type,
            case_type=request.case_type,
            patent_type=request.patent_type,
            category=request.category,
            version=request.version,
            score_threshold=request.score_threshold,
            debug=request.debug,
            user_materials=DocumentIngestService().build_llm_materials(request.document_task_ids),
            expected_risk_domain=request.expected_risk_domain,
        )
        return RiskReportResponse(**result)
    except DocumentIngestError as exc:
        return _error_response(exc.http_status, exc.code, exc.message)
    except Exception as exc:
        logger.exception("Failed to process /risk/report request")
        return _error_response(500, "INTERNAL_ERROR", "内部服务错误，请稍后重试。")


@app.post("/risk/report/export")
async def risk_report_export(request: RiskReportExportRequest):
    try:
        result = generate_risk_report_export(
            request.scenario,
            export_format=request.export_format,
            include_evidence_chain=request.include_evidence_chain,
            include_source_analysis=request.include_source_analysis,
            collection_name=request.collection_name,
            k=request.k,
            doc_type=request.doc_type,
            block_type=request.block_type,
            document_type=request.document_type,
            law_name=request.law_name,
            source=request.source,
            law_level=request.law_level,
            authority_level=request.authority_level,
            jurisdiction=request.jurisdiction,
            issuing_authority=request.issuing_authority,
            legal_effect=request.legal_effect,
            standard_type=request.standard_type,
            case_type=request.case_type,
            patent_type=request.patent_type,
            category=request.category,
            version=request.version,
            score_threshold=request.score_threshold,
            debug=request.debug,
            user_materials=DocumentIngestService().build_llm_materials(request.document_task_ids),
            expected_risk_domain=request.expected_risk_domain,
        )
        if request.export_format == "json":
            return JSONResponse(content=result)
        return PlainTextResponse(content=result, media_type="text/markdown; charset=utf-8")
    except DocumentIngestError as exc:
        return _error_response(exc.http_status, exc.code, exc.message)
    except Exception as exc:
        logger.exception("Failed to process /risk/report/export request")
        return _error_response(500, "INTERNAL_ERROR", "内部服务错误，请稍后重试。")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
