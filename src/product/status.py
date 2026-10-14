from __future__ import annotations


PRODUCT_STATUS_CATALOG_VERSION = "0.4.18.7"

PRODUCT_SUCCESS_STATES = [
    {
        "state": "ok",
        "http_status": 200,
        "body_shape": "status_data_or_items_meta",
        "frontend_meaning": "正常展示产品视图数据。",
    },
    {
        "state": "empty_items",
        "http_status": 200,
        "body_shape": "status_items_meta",
        "frontend_meaning": "过滤条件合法但没有命中风险事项，展示空态而非错误。",
    },
]

PRODUCT_ERROR_CATALOG = [
    {
        "code": "PRODUCT_VIEW_MODEL_UNAVAILABLE",
        "http_status": 500,
        "source": "fixture_missing_or_unreadable",
        "frontend_severity": "blocking",
        "message": "产品视图样例数据暂不可用，请稍后重试。",
    },
    {
        "code": "PRODUCT_VIEW_MODEL_INVALID_JSON",
        "http_status": 500,
        "source": "fixture_json_invalid",
        "frontend_severity": "blocking",
        "message": "产品视图样例数据格式异常，请联系维护人员。",
    },
    {
        "code": "PRODUCT_VIEW_MODEL_VERSION_MISMATCH",
        "http_status": 500,
        "source": "source_view_model_version_drift",
        "frontend_severity": "blocking",
        "message": "产品视图样例数据版本不匹配，请联系维护人员。",
    },
    {
        "code": "PRODUCT_VIEW_MODEL_MISSING",
        "http_status": 500,
        "source": "view_model_missing",
        "frontend_severity": "blocking",
        "message": "产品视图样例数据缺少必要模块，请联系维护人员。",
    },
    {
        "code": "PRODUCT_DATA_SOURCE_DEGRADED",
        "http_status": 503,
        "source": "future_real_data_source_partial_unavailable",
        "frontend_severity": "degraded",
        "message": "部分产品数据源暂不可用，当前结果可能不完整。",
    },
    {
        "code": "PRODUCT_DATA_SOURCE_UNAVAILABLE",
        "http_status": 503,
        "source": "future_real_data_source_unavailable",
        "frontend_severity": "blocking",
        "message": "产品数据源暂不可用，请稍后重试。",
    },
]

PRODUCT_ERROR_BY_CODE = {item["code"]: item for item in PRODUCT_ERROR_CATALOG}
