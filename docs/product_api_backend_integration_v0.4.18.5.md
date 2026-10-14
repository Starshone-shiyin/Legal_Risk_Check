# v0.4.18.5 Product API Backend Integration

## 目的

本版本把 v0.4.18.4 的离线 product mock endpoint contract 接入为真实 FastAPI 后端接口。它完成的是后端层级和 HTTP contract 接线，不是正式业务数据源接入。

## 新增后端分层

- `src/product/contracts.py`：集中定义 product API 版本、source view model 版本和 6 个 endpoint contract。
- `src/product/schemas.py`：定义统一响应 envelope：`status`、`data/items`、`meta`。
- `src/product/service.py`：fixture-backed product view model service，只读取 `tests/fixtures/product_view_models_v0.4.18.3.json`。
- `src/product/router.py`：定义 `/product/*` 的 FastAPI router。
- `src/main.py`：通过 `app.include_router(product_router)` 接入产品接口。

## 接入接口

本版本真实暴露 6 个只读接口：

1. `GET /product/dashboard/summary`
2. `GET /product/legal/workspace`
3. `GET /product/market/signals`
4. `GET /product/supply-chain/map`
5. `GET /product/lifecycle/risk`
6. `GET /product/risks`

`/product/risks` 支持轻量过滤：`risk_level`、`domain`、`review_status`。未命中过滤时返回空 `items`，不返回 404。

## 新增质量检查

- `tools/check_product_api_contract.py`
- `tests/test_product_api_contract.py`
- `tests/product_api_contract_v0.4.18.5_report.json`

checker 使用 FastAPI `TestClient` 请求内存 app，检查：

- OpenAPI 是否暴露 6 个 `/product/*` GET 路径。
- 每个接口是否返回 `status=ok`。
- view endpoint 是否返回 `data` object。
- shared risk endpoint 是否返回 `items` list。
- `meta.contract_version` 是否为 `0.4.18.5`。
- `meta.source_view_model_version` 是否为 `0.4.18.3`。
- `meta.data_source` 是否为 `fixture_sample`。
- `meta.runtime_data_access` 是否明确声明 RAG、Qdrant、LLM、行情、地图和供应链外部数据均为 `not_called`。

当前报告 `tests/product_api_contract_v0.4.18.5_report.json` 显示：

- `status=passed`
- `endpoint_count=6`
- `openapi_passed=6`
- `response_passed=6`
- `issue_count=0`

## 边界

- 接口是真实 FastAPI route，但数据源仍是 fixture sample。
- 不调用 `rag_query`、`analyze_risk`、`generate_risk_report` 或报告导出链路。
- 不访问 Qdrant。
- 不调用 LLM。
- 不接真实行情、地图、供应链、权限系统或外部数据源。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval cases、hidden seed 或知识库数据。
- `/product/legal/workspace` 的 `active_answer` 是展示态样例，不是实时 RAG 问答结果。

## 下一步

后续若 UI 设计稳定，可以让前端先对接这些 fixture-backed product API。若要替换真实数据源，应另开版本逐项接入数据 repository、鉴权、缓存、错误语义和回归测试。
