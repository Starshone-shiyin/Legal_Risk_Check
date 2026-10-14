# v0.4.18.6 Product API Field Catalog

## 目的

本版本为 v0.4.18.5 已接入的 fixture-backed `/product/*` 后端接口生成字段目录，方便 UI 设计、前端原型和后端实现继续对齐。

它是后端接口交接目录，不是新数据源接入。

## 新增产物

- `tools/export_product_api_field_catalog.py`
- `tests/test_product_api_field_catalog.py`
- `tests/product_api_field_catalog_v0.4.18.6.json`
- `docs/product_api_field_catalog_v0.4.18.6.md`

## Catalog 内容

字段目录覆盖 6 个产品接口：

- `GET /product/dashboard/summary`
- `GET /product/legal/workspace`
- `GET /product/market/signals`
- `GET /product/supply-chain/map`
- `GET /product/lifecycle/risk`
- `GET /product/risks`

每个 endpoint 记录：

- endpoint id、method、path、view model 和 response key；
- query params；
- response envelope 必需字段；
- meta 字段；
- 从 fixture 推导出的 response field paths；
- 是否因字段过多被截断。

当前 catalog 摘要：

- `endpoint_count=6`
- `query_param_count=14`
- `source_version_matches=true`
- 当前 fixture 字段未被截断。

## 边界

- 不启动服务。
- 不调用 RAG/Qdrant/LLM。
- 不接真实行情、地图、供应链或权限系统。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry、eval cases、hidden seed 或知识库数据。
- 只读取 `tests/fixtures/product_view_models_v0.4.18.3.json` 和 product endpoint constants。
