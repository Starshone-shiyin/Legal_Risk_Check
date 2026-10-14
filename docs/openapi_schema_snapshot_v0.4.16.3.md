# v0.4.16.3 OpenAPI Schema Snapshot

## 定位

本版本为后续前端接入准备可比对的 OpenAPI schema 快照。它不启动服务、不调用 RAG，也不生成真实风险报告，只把当前 FastAPI schema 导出为 JSON 产物。

## 新增工具

- `tools/export_openapi_schema.py`

默认输出：

- `tests/openapi_schema_v0.4.16.3.json`

## 边界

- 不启动 FastAPI 服务。
- 不调用 `rag_query`、Qdrant、LLM、Cross-Encoder 或报告生成。
- 不修改 retriever、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。
- 不接正式前端，不重跑 full eval。

## 验证

- `./venv/Scripts/python.exe tools/export_openapi_schema.py --output tests/openapi_schema_v0.4.16.3.json`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
