from __future__ import annotations


PRODUCT_API_VERSION = "0.4.18.5"
SOURCE_VIEW_MODEL_VERSION = "0.4.18.3"

PRODUCT_ENDPOINTS = [
    {
        "endpoint_id": "product_dashboard_summary",
        "method": "GET",
        "path": "/product/dashboard/summary",
        "view_model": "dashboard_summary",
        "response_key": "data",
        "query_params": ["company_id", "as_of"],
    },
    {
        "endpoint_id": "product_legal_workspace",
        "method": "GET",
        "path": "/product/legal/workspace",
        "view_model": "legal_workspace",
        "response_key": "data",
        "query_params": ["workspace_id", "thread_id"],
    },
    {
        "endpoint_id": "product_market_signals",
        "method": "GET",
        "path": "/product/market/signals",
        "view_model": "market_signals",
        "response_key": "data",
        "query_params": ["company_id", "domain", "as_of"],
    },
    {
        "endpoint_id": "product_supply_chain_map",
        "method": "GET",
        "path": "/product/supply-chain/map",
        "view_model": "supply_chain_map",
        "response_key": "data",
        "query_params": ["company_id", "map_mode"],
    },
    {
        "endpoint_id": "product_lifecycle_risk",
        "method": "GET",
        "path": "/product/lifecycle/risk",
        "view_model": "lifecycle_risk",
        "response_key": "data",
        "query_params": ["company_id"],
    },
    {
        "endpoint_id": "product_risks",
        "method": "GET",
        "path": "/product/risks",
        "view_model": "product_risks",
        "response_key": "items",
        "query_params": ["company_id", "risk_level", "domain", "review_status"],
    },
]
