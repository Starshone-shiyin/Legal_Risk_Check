# v0.4.16.10 API Field Catalog

## 定位

本版本新增离线 API field catalog，把请求/响应模型的字段、必填项、默认值和 schema 说明导出出来。它主要给前端表单、字段解释和展示映射用，不是正式前端接入，也不触发真实 runtime。

## 新增产物

- `tools/export_api_field_catalog.py`
- `tests/api_field_catalog_v0.4.16.10.json`

## 契约内容

field catalog 覆盖：

- `AskRequest`
- `RiskAnalyzeRequest`
- `RiskReportExportRequest`
- `AskResponse`
- `RiskAnalyzeResponse`
- `RiskReportResponse`

每个模型包含：

- `required_fields`
- `field_count`
- `fields`

单个字段包含：

- `name`
- `required`
- `annotation`
- `default`
- `title`
- `description`
- `json_schema`

## 边界

- 不启动服务。
- 不调用 `rag_query`、`analyze_risk`、`generate_risk_report`、Qdrant、LLM 或真实报告生成。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixture 或 eval case。
- 不接正式前端，不新增 gate，不运行 full eval。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/export_api_field_catalog.py tests/test_api_contract.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
