from __future__ import annotations


EXTERNAL_RISK_API_VERSION = "0.1.0"
EXTERNAL_RISK_FIXTURE_VERSION = "0.1.0"

EXTERNAL_RISK_ENDPOINTS = [
    {
        "endpoint_id": "external_risk_context",
        "method": "GET",
        "path": "/external-risk/context",
        "response_key": "data",
        "query_params": ["company_id", "as_of"],
    },
    {
        "endpoint_id": "external_risk_signals",
        "method": "GET",
        "path": "/external-risk/signals",
        "response_key": "items",
        "query_params": ["company_id", "signal_type", "severity"],
    },
    {
        "endpoint_id": "external_risk_findings",
        "method": "GET",
        "path": "/external-risk/findings",
        "response_key": "items",
        "query_params": ["company_id", "risk_domain", "severity", "include_live"],
    },
    {
        "endpoint_id": "external_risk_legal_query_plan",
        "method": "GET",
        "path": "/external-risk/legal-query-plan",
        "response_key": "data",
        "query_params": ["company_id", "risk_domain", "severity"],
    },
    {
        "endpoint_id": "external_risk_provider_status",
        "method": "GET",
        "path": "/external-risk/provider-status",
        "response_key": "items",
        "query_params": [],
    },
    {
        "endpoint_id": "external_risk_market_dashboard",
        "method": "GET",
        "path": "/external-risk/market-dashboard",
        "response_key": "data",
        "query_params": ["company_id", "include_live", "limit"],
    },
    {
        "endpoint_id": "external_risk_live_signals",
        "method": "GET",
        "path": "/external-risk/live-signals",
        "response_key": "items",
        "query_params": ["provider", "signal_type", "symbol", "commodity_group"],
    },
    {
        "endpoint_id": "external_risk_refresh_intelligence",
        "method": "POST",
        "path": "/external-risk/intelligence/refresh",
        "response_key": "items",
        "query_params": [],
    },
    {
        "endpoint_id": "external_risk_intelligence_status",
        "method": "GET",
        "path": "/external-risk/intelligence/status",
        "response_key": "data",
        "query_params": [],
    },
    {
        "endpoint_id": "external_risk_quote_series",
        "method": "GET",
        "path": "/external-risk/quote-series",
        "response_key": "data",
        "query_params": ["symbol", "interval"],
    },
    {
        "endpoint_id": "external_risk_workflow",
        "method": "GET",
        "path": "/external-risk/workflow",
        "response_key": "data",
        "query_params": [],
    },
    {
        "endpoint_id": "external_risk_save_workflow",
        "method": "PUT",
        "path": "/external-risk/workflow",
        "response_key": "data",
        "query_params": [],
    },
    {
        "endpoint_id": "external_risk_merge_workflow",
        "method": "POST",
        "path": "/external-risk/workflow/merge",
        "response_key": "data",
        "query_params": [],
    },
    {
        "endpoint_id": "external_risk_web_search",
        "method": "POST",
        "path": "/external-risk/web-search",
        "response_key": "items",
        "query_params": [],
    },
    {
        "endpoint_id": "external_risk_web_search_status",
        "method": "GET",
        "path": "/external-risk/web-search/status",
        "response_key": "data",
        "query_params": [],
    },
]

RUNTIME_ACCESS_GUARDRAILS = {
    "rag": "not_called",
    "qdrant": "not_called",
    "llm": "not_called",
    "market_data": "fixture_only",
    "commodity_data": "fixture_only",
    "news_policy_data": "not_called",
    "supply_chain_data": "fixture_only",
    "company_data": "fixture_only",
    "web_search": "not_called",
}
