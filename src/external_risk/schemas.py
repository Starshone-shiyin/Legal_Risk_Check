from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.external_risk.contracts import (
    EXTERNAL_RISK_API_VERSION,
    EXTERNAL_RISK_FIXTURE_VERSION,
    RUNTIME_ACCESS_GUARDRAILS,
)


Severity = Literal["low", "medium", "high", "critical"]
SignalType = Literal["market", "commodity_futures", "supply_chain", "news", "policy"]
RiskDomain = Literal[
    "market",
    "supply_chain",
    "contract",
    "disclosure",
    "ip",
    "data_compliance",
    "export_control",
    "corporate_governance",
]

SearchMode = Literal["off", "auto", "force"]
SearchDomain = Literal["legal", "regulatory", "market", "company", "general"]
SearchIntent = Literal[
    "none",
    "legal_update",
    "legal_reference",
    "market_event",
    "company_event",
    "general_realtime",
]


class ExternalRiskResponseMeta(BaseModel):
    contract_version: str = EXTERNAL_RISK_API_VERSION
    fixture_version: str = EXTERNAL_RISK_FIXTURE_VERSION
    data_source: Literal[
        "fixture_sample",
        "live_provider",
        "hybrid_provider",
        "disabled_live_provider",
        "unavailable_live_provider",
    ] = "fixture_sample"
    runtime_data_access: dict[str, str] = Field(default_factory=lambda: dict(RUNTIME_ACCESS_GUARDRAILS))


class CompanyProfile(BaseModel):
    company_id: str
    name: str
    tech_sector: str
    lifecycle_stage: str
    listed_board: str | None = None
    financing_stage: str | None = None
    core_products: list[str] = Field(default_factory=list)
    key_materials: list[str] = Field(default_factory=list)
    key_regions: list[str] = Field(default_factory=list)
    sensitive_domains: list[RiskDomain] = Field(default_factory=list)


class ExternalRiskSignal(BaseModel):
    signal_id: str
    signal_type: SignalType
    title: str
    severity: Severity
    direction: Literal["negative", "positive", "neutral", "mixed"] = "neutral"
    as_of: str
    entity: str
    metric: str
    value: float | str | None = None
    threshold: float | str | None = None
    affected_domains: list[RiskDomain] = Field(default_factory=list)
    affected_supply_links: list[str] = Field(default_factory=list)
    evidence: str
    source: str
    confidence: float = Field(default=0.7, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TechCompanyRiskFinding(BaseModel):
    finding_id: str
    title: str
    severity: Severity
    risk_domain: RiskDomain
    summary: str
    triggering_signal_ids: list[str] = Field(default_factory=list)
    legal_query_seeds: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    requires_human_review: bool = True


class LegalQueryTask(BaseModel):
    task_id: str
    finding_id: str
    risk_domain: RiskDomain
    severity: Severity
    query: str
    fact_background: str
    triggering_signal_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    suggested_filters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LegalQueryPlan(BaseModel):
    company: CompanyProfile
    as_of: str
    scope: Literal["external_fact_to_legal_rag_query_plan"] = "external_fact_to_legal_rag_query_plan"
    tasks: list[LegalQueryTask] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class ExternalRiskContext(BaseModel):
    company: CompanyProfile
    as_of: str
    signals: list[ExternalRiskSignal] = Field(default_factory=list)
    findings: list[TechCompanyRiskFinding] = Field(default_factory=list)
    legal_fusion_hints: list[str] = Field(default_factory=list)


class ExternalRiskContextResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ExternalRiskContext
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class ExternalRiskSignalListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[ExternalRiskSignal]
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class ExternalRiskFindingListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[TechCompanyRiskFinding]
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class LegalQueryPlanResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: LegalQueryPlan
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class ExternalRiskProviderStatus(BaseModel):
    provider_id: str
    provider_type: Literal["market", "commodity_futures", "supply_chain", "company_profile", "news_policy"]
    status: Literal["available", "unavailable", "not_configured", "fixture_only"]
    mode: Literal["live", "fixture", "disabled"] = "fixture"
    message: str = ""
    required_package: str | None = None
    runtime_access: str = "not_called"


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source_name: str = ""
    source_tier: Literal["official", "primary_public", "trusted_media", "unverified_web"] = "unverified_web"
    trust_score: float = Field(default=0.35, ge=0, le=1)
    published_at: str | None = None
    fetched_at: str | None = None


class WebSearchPlan(BaseModel):
    mode: SearchMode
    intent: SearchIntent
    trigger: str
    queries: list[str] = Field(default_factory=list, max_length=3)
    allowed_domains: list[str] = Field(default_factory=list)
    max_results: int = Field(default=5, ge=1, le=10)
    should_search: bool = False
    requires_human_review: bool = True


class WebSearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    mode: SearchMode = "auto"
    domain: SearchDomain = "general"
    max_results: int = Field(default=5, ge=1, le=10)


class WebSearchResponse(BaseModel):
    status: Literal["ok"] = "ok"
    plan: WebSearchPlan
    items: list[WebSearchResult] = Field(default_factory=list)
    provider_id: str
    provider_enabled: bool
    runtime_access: str = "not_called"
    searched_at: str | None = None
    error: str | None = None


class ExternalRiskProviderStatusResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[ExternalRiskProviderStatus]
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class IntelligenceFeedHealth(BaseModel):
    feed_id: str
    source_name: str
    adapter: str
    url: str
    signal_type: SignalType
    risk_relevance: float = Field(default=1.0, ge=0.1, le=1.0)
    # "empty" means the HTTP request succeeded but the adapter found no article records.
    # It is intentionally distinct from a usable, successful feed.
    status: Literal["success", "empty", "failed", "not_called"] = "not_called"
    last_checked_at: str | None = None
    last_success_at: str | None = None
    item_count: int = Field(default=0, ge=0)
    signal_count: int = Field(default=0, ge=0)
    error: str | None = None


class ExternalRiskIntelligenceStatus(BaseModel):
    provider: ExternalRiskProviderStatus
    cache_fresh: bool = False
    cache_updated_at: str | None = None
    cached_signal_count: int = Field(default=0, ge=0)
    poll_seconds: int = Field(default=300, ge=1)
    feeds: list[IntelligenceFeedHealth] = Field(default_factory=list)


class ExternalRiskIntelligenceStatusResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ExternalRiskIntelligenceStatus
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class ExternalRiskDashboardSummary(BaseModel):
    headline: str
    signal_count: int
    live_signal_count: int = 0
    high_or_above_count: int = 0
    legal_task_count: int = 0
    risk_coefficient: float = 0.0
    risk_coefficient_level: Literal["low", "medium", "high", "critical"] = "low"
    risk_coefficient_formula: str = ""
    risk_coefficient_components: dict[str, float] = Field(default_factory=dict)
    risk_coefficient_quality: float = Field(default=0.0, ge=0, le=1)
    provider_mode: Literal["fixture", "disabled", "live", "hybrid"] = "fixture"
    data_mode: Literal[
        "fixture_sample",
        "live_provider",
        "hybrid_provider",
        "unavailable_live_provider",
    ] = "fixture_sample"


class ExternalRiskDataQuality(BaseModel):
    """Auditable boundary between live observations and scenario records.

    Market/RSS providers may be called at dashboard refresh time, while the
    enterprise supplier register and the relationship graph can still be a
    competition scenario.  Keeping these dimensions separate prevents a live
    price from being mistaken for proof of a commercial relationship.
    """

    market_data_access: str = "not_called"
    commodity_data_access: str = "not_called"
    news_policy_data_access: str = "not_called"
    supply_chain_data_access: Literal["scenario_record", "fixture_only", "live_verified"] = "fixture_only"
    relationship_evidence_counts: dict[str, int] = Field(default_factory=dict)
    relationship_boundary: str = ""


class ExternalRiskChainAlert(BaseModel):
    alert_id: str
    signal_id: str
    severity: Severity
    source_symbol: str | None = None
    affected_node_ids: list[str] = Field(default_factory=list)
    affected_symbols: list[str] = Field(default_factory=list)
    path_node_ids: list[str] = Field(default_factory=list)
    association_type: Literal["workflow", "industry", "mixed"] = "workflow"
    association_tags: list[str] = Field(default_factory=list)
    external_instruments: list[str] = Field(default_factory=list)
    transmission_score: float = Field(default=0.0, ge=0, le=1)
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    relationship_evidence_grade: Literal[
        "unverified", "scenario_proxy", "document_referenced", "contract_verified",
    ] = "unverified"
    relationship_boundary: str = ""


class ExternalRiskMarketDashboard(BaseModel):
    company: CompanyProfile
    as_of: str
    summary: ExternalRiskDashboardSummary
    signals: list[ExternalRiskSignal] = Field(default_factory=list)
    # Broad industry-chain observations are useful context, but are kept out
    # of the enterprise score until they match the company or canvas scope.
    market_observations: list[ExternalRiskSignal] = Field(default_factory=list)
    chain_alerts: list[ExternalRiskChainAlert] = Field(default_factory=list)
    findings: list[TechCompanyRiskFinding] = Field(default_factory=list)
    legal_query_tasks: list[LegalQueryTask] = Field(default_factory=list)
    provider_statuses: list[ExternalRiskProviderStatus] = Field(default_factory=list)
    # Keep the feed-level polling snapshot with the dashboard response so the
    # UI can explain freshness without issuing a second, potentially stale call.
    intelligence_status: ExternalRiskIntelligenceStatus | None = None
    data_quality: ExternalRiskDataQuality = Field(default_factory=ExternalRiskDataQuality)
    guardrails: list[str] = Field(default_factory=list)


class ExternalRiskMarketDashboardResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ExternalRiskMarketDashboard
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class ExternalRiskQuotePoint(BaseModel):
    time: str
    timestamp: int | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float
    volume: float | None = None
    pct_change: float | None = None
    baseline_price: float | None = None


class ExternalRiskQuoteSeries(BaseModel):
    symbol: str
    name: str
    provider: str = "tencent_http_provider"
    interval: Literal["intraday", "daily", "weekly", "monthly"]
    source: Literal[
        "live_provider",
        "sina_global_futures",
        "sina_cn_futures",
        "eastmoney_provider",
        "yahoo_chart",
        "provider_unavailable",
    ] = "provider_unavailable"
    as_of: str
    points: list[ExternalRiskQuotePoint] = Field(default_factory=list)
    reference_price: float | None = None
    change_rate: float | None = None
    change_basis: Literal[
        "previous_close",
        "listing_reference",
        "period_open",
        "first_available",
        "unavailable",
    ] = "unavailable"
    instrument_status: Literal["normal", "new_listing", "st", "unknown"] = "unknown"
    price_limit_rate: float | None = None
    price_limit_label: str = ""


class ExternalRiskQuoteSeriesResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ExternalRiskQuoteSeries
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)


class ExternalRiskWorkflowNode(BaseModel):
    id: str
    symbol: str
    name: str | None = None
    # ``enterprise`` is a listed company or counterparty shown for industry
    # context. Only ``supplier`` nodes are candidates for supply-map binding.
    node_kind: Literal["market", "supplier", "enterprise"] = "market"
    supplier_id: str | None = None
    x: float = 0
    y: float = 0
    lane: str | None = None
    group: str | None = None
    recommendations: list[str] = Field(default_factory=list)


class ExternalRiskWorkflowLink(BaseModel):
    """Canonical external-risk relationship entity.

    The supplier workspace, product supply-chain map and commodity canvas are
    projections of this record.  Older map files only contained endpoints and
    remain valid: identity and the unconfirmed state are filled on read.
    """
    relation_id: str | None = Field(default=None, max_length=160)
    source: str
    target: str
    sourcePort: Literal["left", "right"] = "right"
    targetPort: Literal["left", "right"] = "left"
    relation: str | None = "supply"
    source_kind: Literal[
        "manual_canvas", "supplier_master", "commodity_catalog", "imported", "legacy",
    ] = "legacy"
    correlation_layers: list[Literal["material", "region", "counterparty", "path", "risk_domain"]] = Field(
        default_factory=list
    )
    evidence_grade: Literal[
        "unverified", "scenario_proxy", "document_referenced", "contract_verified",
    ] = "unverified"
    relationship_scope: Literal[
        "industry_proxy", "cost_proxy", "commercial_relationship", "peer_reference",
    ] = "industry_proxy"
    evidence_refs: list[str] = Field(default_factory=list, max_length=24)
    boundary_note: str = Field(default="", max_length=500)
    confirmed_by: str | None = Field(default=None, max_length=120)
    confirmed_at: str | None = None
    updated_at: str | None = None


class ExternalRiskRelationshipProjection(BaseModel):
    """A light-weight view of canonical relation IDs for a business surface."""
    projection: Literal["supplier_master", "product_supply_chain", "commodity_futures"]
    relation_ids: list[str] = Field(default_factory=list)


class ExternalRiskSupplyChainSyncItem(BaseModel):
    node_id: str
    symbol: str
    name: str | None = None
    category: str | None = None


class ExternalRiskSupplyChainSync(BaseModel):
    """Reconciles the canvas with the separately managed supplier map."""
    status: Literal["synchronized", "action_required"] = "synchronized"
    bound_supplier_ids: list[str] = Field(default_factory=list)
    synchronized_supplier_ids: list[str] = Field(default_factory=list)
    missing_supplier_ids: list[str] = Field(default_factory=list)
    unbound_supplier_nodes: list[ExternalRiskSupplyChainSyncItem] = Field(default_factory=list)
    message: str = ""


class ExternalRiskWorkflowMergeRequest(BaseModel):
    """A deliberate, additive merge of a stale local canvas draft."""
    base_revision: int = Field(ge=0)
    draft: "ExternalRiskWorkflowGraph"
    confirmed_by: str = Field(min_length=1, max_length=120)
    confirmation_note: str = Field(min_length=1, max_length=500)


class ExternalRiskWorkflowGraph(BaseModel):
    version: str = "0.1.0"
    # Monotonically increasing optimistic-lock token.  It is deliberately
    # separate from the document format version above.
    revision: int = Field(default=0, ge=0)
    nodes: list[ExternalRiskWorkflowNode] = Field(default_factory=list)
    links: list[ExternalRiskWorkflowLink] = Field(default_factory=list)
    # Supplier records and canvas nodes remain separate views, but this list
    # makes every persisted supplier-node relationship explicit and auditable.
    bound_supplier_ids: list[str] = Field(default_factory=list)
    relationship_projections: list[ExternalRiskRelationshipProjection] = Field(default_factory=list)
    supply_chain_sync: ExternalRiskSupplyChainSync = Field(default_factory=ExternalRiskSupplyChainSync)
    merge_audit: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: str | None = None
    storage_path: str | None = None


class ExternalRiskWorkflowGraphResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ExternalRiskWorkflowGraph
    meta: ExternalRiskResponseMeta = Field(default_factory=ExternalRiskResponseMeta)
