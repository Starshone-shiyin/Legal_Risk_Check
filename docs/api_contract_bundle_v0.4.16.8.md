# v0.4.16.8 API Contract Bundle

## 定位

本版本新增离线 API contract bundle，把当前 OpenAPI schema 与 example payload fixture 合并成一个机器可读交付物。它服务于前端、离线工作台和文档审阅，不是正式前端接入，也不触发真实 RAG 链路。

## 新增产物

- `tools/export_api_contract_bundle.py`
- `tests/api_contract_bundle_v0.4.16.8.json`

## 契约内容

bundle 包含：

- 当前 FastAPI OpenAPI schema。
- `tests/fixtures/api_contract_example_payloads_v0.4.16.4.json` 中的离线 example payload。
- v0.4.16.9 起，bundle 还包含 `validation_error_422`、`llm_timeout_504`、`internal_error_500` 错误状态样例。
- `guardrails`、`sources` 和 `summary` 结构，便于前端直接识别是否可用于离线联调。

## 边界

- 不启动服务。
- 不调用 `rag_query`、`analyze_risk`、`generate_risk_report`、Qdrant、LLM 或真实报告生成。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixture 或 eval case。
- 不接正式前端，不新增 gate，不运行 full eval。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/export_api_contract_bundle.py tests/test_api_contract.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
