# v0.4.16.2 API Error and Export Contract

## 定位

本版本继续前后端接入前的 API contract 稳定工作，聚焦错误响应和报告导出响应。目标是让前端未来能可靠区分 JSON 导出、Markdown 导出和统一错误结构。

## 固化内容

- 统一错误响应结构为 `{ "error": { "code": "...", "message": "..." } }`。
- `/risk/report/export` 的 `export_format="markdown"` 返回 `text/markdown; charset=utf-8`。
- `/risk/report/export` 的 `export_format="json"` 返回 `application/json`。
- 未知 `export_format` 在进入 runtime 之前由请求校验拒绝。

## 边界

- 测试使用 `TestClient` 和 mock，不调用真实 `generate_risk_report_export`、`rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。
- 不接正式前端，不新增 full eval 或 gate。

## 验证

- `./venv/Scripts/python.exe -m py_compile src/main.py tests/test_api_contract.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
