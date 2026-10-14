# v0.4.16.4 API Example Payload Fixtures

## 定位

本版本为后续前端、离线工作台或接口文档审阅准备一组稳定的 API example payload。它解决的是“界面和联调需要真实形状的样例数据”问题，不是正式接入前端，也不是运行 RAG 主链路。

## 新增产物

- `tests/fixtures/api_contract_example_payloads_v0.4.16.4.json`

该 fixture 覆盖：

- `/ask` 请求与响应样例。
- `/risk/analyze` 请求与响应样例。
- `/risk/report` 请求与响应样例。
- `/risk/report/export` Markdown 文本样例。
- `/risk/report/export` JSON 结构样例。

## 契约校验

`tests/test_api_contract.py` 新增离线校验，确认样例可以通过现有 Pydantic 模型：

- `AskRequest`
- `AskResponse`
- `RiskAnalyzeRequest`
- `RiskAnalyzeResponse`
- `RiskReportResponse`

`/risk/report/export` 当前没有声明 `response_model`，因此 JSON 导出样例只验证为与 `RiskReportResponse` 兼容的报告结构，不声称 FastAPI 已强制该响应模型。

## 边界

- 不启动 FastAPI 服务。
- 不调用 `rag_query`、Qdrant、LLM、Cross-Encoder 或真实报告生成。
- 不修改 retriever、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。
- 不接入正式前端，不新增 runtime 能力，不运行 full eval。
- 样例内容仅用于契约和界面联调参考，不应作为法律结论或评测样本。

## 验证

- `./venv/Scripts/python.exe -m py_compile src/main.py tests/test_api_contract.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
