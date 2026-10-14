from __future__ import annotations

import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.external_risk.schemas import (
    ExternalRiskContextResponse,
    ExternalRiskIntelligenceStatusResponse,
    ExternalRiskFindingListResponse,
    ExternalRiskMarketDashboardResponse,
    ExternalRiskQuoteSeriesResponse,
    ExternalRiskResponseMeta,
    ExternalRiskProviderStatusResponse,
    ExternalRiskSignalListResponse,
    ExternalRiskWorkflowGraph,
    ExternalRiskWorkflowMergeRequest,
    ExternalRiskWorkflowGraphResponse,
    LegalQueryPlanResponse,
    WebSearchRequest,
    WebSearchResponse,
)
from src.external_risk.service import (
    ExternalRiskDataError,
    ExternalRiskService,
    ExternalRiskWorkflowConflictError,
)
from src.external_risk.web_search import OnlineSearchService


router = APIRouter(prefix="/external-risk", tags=["external-risk"])
service = ExternalRiskService()


def _external_risk_error_response(exc: ExternalRiskDataError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "EXTERNAL_RISK_DATA_ERROR", "message": str(exc)}},
    )


@router.get("/context", response_model=ExternalRiskContextResponse)
async def external_risk_context(company_id: str | None = None, as_of: str | None = None):
    try:
        return ExternalRiskContextResponse(data=service.context(company_id=company_id, as_of=as_of))
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/signals", response_model=ExternalRiskSignalListResponse)
async def external_risk_signals(
    company_id: str | None = None,
    signal_type: str | None = None,
    severity: str | None = None,
):
    try:
        return ExternalRiskSignalListResponse(
            items=service.signals(company_id=company_id, signal_type=signal_type, severity=severity)
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/findings", response_model=ExternalRiskFindingListResponse)
async def external_risk_findings(
    company_id: str | None = None,
    risk_domain: str | None = None,
    severity: str | None = None,
):
    try:
        return ExternalRiskFindingListResponse(
            items=service.findings(company_id=company_id, risk_domain=risk_domain, severity=severity)
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/legal-query-plan", response_model=LegalQueryPlanResponse)
async def external_risk_legal_query_plan(
    company_id: str | None = None,
    risk_domain: str | None = None,
    severity: str | None = None,
    include_live: bool = True,
):
    try:
        data = await asyncio.to_thread(
            service.legal_query_plan,
            company_id=company_id,
            risk_domain=risk_domain,
            severity=severity,
            include_live=include_live,
        )
        return LegalQueryPlanResponse(
            data=data
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/provider-status", response_model=ExternalRiskProviderStatusResponse)
async def external_risk_provider_status():
    try:
        return ExternalRiskProviderStatusResponse(items=service.provider_statuses())
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/market-dashboard", response_model=ExternalRiskMarketDashboardResponse)
async def external_risk_market_dashboard(
    company_id: str | None = None,
    include_live: bool = True,
    limit: int = 12,
):
    try:
        data = await asyncio.to_thread(
            service.market_dashboard,
            company_id=company_id,
            include_live=include_live,
            limit=limit,
        )
        meta = ExternalRiskResponseMeta(data_source=data.summary.data_mode)
        return ExternalRiskMarketDashboardResponse(data=data, meta=meta)
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/live-signals", response_model=ExternalRiskSignalListResponse)
async def external_risk_live_signals(
    provider: str = "composite",
    signal_type: str | None = None,
    symbol: str | None = None,
    commodity_group: str | None = None,
):
    try:
        items = await asyncio.to_thread(
            service.live_signals,
            provider=provider,
            signal_type=signal_type,
            symbol=symbol,
            commodity_group=commodity_group,
        )
        provider_status = service.live_provider_status()
        meta = _live_signal_meta(provider_status.runtime_access, bool(items))
        return ExternalRiskSignalListResponse(items=items, meta=meta)
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.post("/intelligence/refresh", response_model=ExternalRiskSignalListResponse)
async def external_risk_refresh_intelligence():
    try:
        items = await asyncio.to_thread(service.refresh_intelligence)
        provider_status = service.intelligence_provider_status()
        return ExternalRiskSignalListResponse(
            items=items,
            meta=_intelligence_meta(provider_status.runtime_access, bool(items)),
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/intelligence/status", response_model=ExternalRiskIntelligenceStatusResponse)
async def external_risk_intelligence_status():
    try:
        data = service.intelligence_status()
        return ExternalRiskIntelligenceStatusResponse(
            data=data,
            meta=_intelligence_meta(data.provider.runtime_access, bool(data.cached_signal_count)),
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/quote-series", response_model=ExternalRiskQuoteSeriesResponse)
async def external_risk_quote_series(
    symbol: str = "sh000001",
    interval: str = "intraday",
):
    try:
        data = await asyncio.to_thread(service.quote_series, symbol=symbol, interval=interval)
        meta = ExternalRiskResponseMeta(
            data_source=(
                "unavailable_live_provider"
                if data.source == "provider_unavailable"
                else "live_provider"
            )
        )
        return ExternalRiskQuoteSeriesResponse(data=data, meta=meta)
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/workflow", response_model=ExternalRiskWorkflowGraphResponse)
async def external_risk_workflow():
    try:
        data = service.workflow_graph()
        return ExternalRiskWorkflowGraphResponse(
            data=data,
            meta=ExternalRiskResponseMeta(data_source="fixture_sample"),
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.put("/workflow", response_model=ExternalRiskWorkflowGraphResponse)
async def external_risk_save_workflow(graph: ExternalRiskWorkflowGraph):
    try:
        data = service.save_workflow_graph(graph)
        return ExternalRiskWorkflowGraphResponse(
            data=data,
            meta=ExternalRiskResponseMeta(data_source="fixture_sample"),
        )
    except ExternalRiskWorkflowConflictError as exc:
        # Return the server snapshot and a compact diff.  The browser retains
        # its draft and can offer an explicit, named additive merge instead of
        # overwriting a colleague's saved map.
        return JSONResponse(
            status_code=409,
            content={
                "error": {"code": "EXTERNAL_RISK_WORKFLOW_CONFLICT", "message": str(exc)},
                "current_graph": exc.current_graph.model_dump(mode="json"),
                "diff": exc.diff,
                "merge_required": True,
            },
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.post("/workflow/merge", response_model=ExternalRiskWorkflowGraphResponse)
async def external_risk_merge_workflow(request: ExternalRiskWorkflowMergeRequest):
    try:
        data = service.merge_workflow_graph(request)
        return ExternalRiskWorkflowGraphResponse(
            data=data,
            meta=ExternalRiskResponseMeta(data_source="fixture_sample"),
        )
    except ExternalRiskDataError as exc:
        return _external_risk_error_response(exc)


@router.get("/web-search/status")
async def external_risk_web_search_status():
    provider = OnlineSearchService()
    status = provider.status()
    return {
        "status": "ok",
        "data": {
            "provider_id": status.provider_id,
            "enabled": status.enabled,
            "message": status.message,
            "runtime_access": status.runtime_access,
        },
    }


@router.post("/web-search", response_model=WebSearchResponse)
async def external_risk_web_search(request: WebSearchRequest):
    search_service = OnlineSearchService()
    plan = search_service.plan(
        request.question,
        mode=request.mode,
        domain=request.domain,
        max_results=request.max_results,
    )
    items = search_service.search(plan)
    status = search_service.status()
    return WebSearchResponse(
        plan=plan,
        items=items,
        provider_id=status.provider_id,
        provider_enabled=status.enabled,
        runtime_access=status.runtime_access,
        searched_at=(items[0].fetched_at if items else None),
        error=(
            None if items or not plan.should_search else
            (status.message if not status.enabled else "online search returned no eligible sources")
        ),
    )


def _live_signal_meta(runtime_access: str, has_items: bool) -> ExternalRiskResponseMeta:
    if has_items:
        data_source = "live_provider"
    elif runtime_access == "live_called":
        data_source = "unavailable_live_provider"
    else:
        data_source = "disabled_live_provider"
    return ExternalRiskResponseMeta(
        data_source=data_source,
        runtime_data_access={
            "rag": "not_called",
            "qdrant": "not_called",
            "llm": "not_called",
            "market_data": runtime_access,
            "commodity_data": runtime_access,
            "supply_chain_data": "fixture_only",
            "company_data": "fixture_only",
        },
    )


def _intelligence_meta(runtime_access: str, has_items: bool) -> ExternalRiskResponseMeta:
    if has_items:
        data_source = "live_provider"
    elif runtime_access == "live_called":
        data_source = "unavailable_live_provider"
    else:
        data_source = "disabled_live_provider"
    return ExternalRiskResponseMeta(
        data_source=data_source,
        runtime_data_access={
            "rag": "not_called",
            "qdrant": "not_called",
            "llm": "not_called",
            "market_data": "not_called",
            "commodity_data": "not_called",
            "news_policy_data": runtime_access,
            "supply_chain_data": "fixture_only",
            "company_data": "fixture_only",
        },
    )
