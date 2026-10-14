# v0.4.16.1 API Contract Baseline

## 定位

本版本进入前后端接入前的 API contract 稳定层。目标不是开发正式前端，也不是继续修 RAG 分数，而是把现有 FastAPI 接口中前端可以依赖的字段先固化为测试和文档。

## 覆盖范围

- `/health`
- `/ask`
- `/risk/analyze`
- `/risk/report`
- `/risk/report/export`

## 固化内容

- 核心路径必须出现在 OpenAPI schema 中。
- `AskRequest`、`RiskAnalyzeRequest`、`RiskReportExportRequest` 的默认值保持稳定。
- `AskResponse`、`RiskAnalyzeResponse`、`RiskReportResponse` 的前端必需字段保持稳定。
- 统一错误响应保持 `{ "error": { "code": "...", "message": "..." } }` 结构。

## 边界

- 不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。
- 不新增 runtime 能力，不新增 gate，不重跑 full eval。
- 本版本只是为后续前后端接入建立契约底线。

## 验证

- `./venv/Scripts/python.exe -m py_compile src/main.py tests/test_api_contract.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
