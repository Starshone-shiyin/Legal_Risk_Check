# v0.4.18.7 Product API Status / Error Catalog

## 目的

本版本为 fixture-backed `/product/*` 后端接口补齐状态与错误目录，明确成功、空结果、fixture 异常和未来真实数据源降级时的前后端处理口径。

## 新增产物

- `src/product/status.py`
- `tools/export_product_api_status_catalog.py`
- `tests/test_product_api_status_catalog.py`
- `tests/product_api_status_catalog_v0.4.18.7.json`
- `docs/product_api_status_catalog_v0.4.18.7.md`

## 状态语义

- `ok`：HTTP 200，正常返回 `status + data/items + meta`。
- `empty_items`：HTTP 200，当前用于 `/product/risks` 过滤无结果，返回空 `items=[]`，前端展示空态，不作为系统错误。

## 错误目录

当前 catalog 记录 6 个错误码：

- `PRODUCT_VIEW_MODEL_UNAVAILABLE`：fixture 缺失或不可读。
- `PRODUCT_VIEW_MODEL_INVALID_JSON`：fixture JSON 格式异常。
- `PRODUCT_VIEW_MODEL_VERSION_MISMATCH`：fixture source version 与预期不一致。
- `PRODUCT_VIEW_MODEL_MISSING`：fixture 缺少必要 view model。
- `PRODUCT_DATA_SOURCE_DEGRADED`：未来真实数据源部分不可用。
- `PRODUCT_DATA_SOURCE_UNAVAILABLE`：未来真实数据源整体不可用。

当前运行态只使用 fixture 相关错误码；真实数据源错误码只作为后续接入时的 contract reserved codes。

## 边界

- 不接真实数据源。
- 不启动服务。
- 不调用 RAG/Qdrant/LLM。
- 不运行 eval。
- 不修改知识库、eval case、anchor、prompt、rerank 或 risk supplement。
