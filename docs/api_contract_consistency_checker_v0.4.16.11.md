# v0.4.16.11 API Contract Consistency Checker

本版本新增离线 API contract consistency checker，用来比对 OpenAPI schema、API contract bundle、API field catalog 和 example payload fixture 是否相互一致。它是前后端接入前的契约质量诊断，不是正式前端接入，也不触发真实 RAG 主链路。

## 范围

- 新增 `tools/check_api_contract_consistency.py`。
- 新增 `tests/test_api_contract_consistency.py`。
- 生成 `tests/api_contract_consistency_v0.4.16.11_report.json`。

## 检查内容

- OpenAPI schema 与 field catalog 的模型字段、必填字段和字段计数是否一致。
- example payload 是否缺少对应模型的必填字段，或包含 schema 外字段。
- API contract bundle 是否与当前生成的 OpenAPI schema、example fixture 和错误样例一致。
- 核心路径的请求/响应模型引用是否符合契约矩阵。
- 离线 guardrails 是否仍然声明不启动服务、不调用 RAG/Qdrant/LLM、不生成真实报告。

## 边界

- 不启动 FastAPI 服务。
- 不调用 `rag_query`。
- 不访问 Qdrant。
- 不调用 LLM。
- 不生成真实风险报告。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。

## 结果

当前报告状态为 `passed`，`issue_count=0`。这说明现有离线 API 契约产物之间没有发现字段、路由引用、bundle source 或 guardrail 不一致。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/check_api_contract_consistency.py tests/test_api_contract_consistency.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract tests.test_api_contract_consistency tests.test_roadmap_hygiene tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/check_api_contract_consistency.py --output tests/api_contract_consistency_v0.4.16.11_report.json --fail-on-error`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`
