# v0.4.16.12 API Contract Stability Closeout

本版本收口 v0.4.16.x API contract stability 系列。它只做离线交付物总览、使用顺序和边界说明，不新增 runtime 能力，不接正式前端，不调用 RAG、Qdrant 或 LLM。

## 系列结论

v0.4.16.x 已形成前后端接入前的离线 API 契约包：

- API 基线：`docs/api_contract_stability_v0.4.16.1.md`
- 错误与导出契约：`docs/api_error_and_export_contract_v0.4.16.2.md`
- OpenAPI schema 快照：`tests/openapi_schema_v0.4.16.3.json`
- example payload fixture：`tests/fixtures/api_contract_example_payloads_v0.4.16.4.json`
- endpoint mock smoke contract：`tests/test_api_contract.py`
- API contract bundle：`tests/api_contract_bundle_v0.4.16.9.json`
- API field catalog：`tests/api_field_catalog_v0.4.16.10.json`
- API contract consistency report：`tests/api_contract_consistency_v0.4.16.11_report.json`

当前一致性基线为：`status=passed`，`issue_count=0`。

## 最小使用顺序

1. 先读 `tests/api_contract_bundle_v0.4.16.9.json`，获得核心路径、成功样例和错误样例。
2. 再读 `tests/api_field_catalog_v0.4.16.10.json`，获得请求/响应模型字段、必填项和默认值。
3. 用 `tests/fixtures/api_contract_example_payloads_v0.4.16.4.json` 做离线 UI/mock 数据。
4. 如需确认契约未漂移，运行：

```powershell
.\venv\Scripts\python.exe tools\check_api_contract_consistency.py --output tests\api_contract_consistency_v0.4.16.11_report.json --fail-on-error
```

5. 如需重新导出 schema、bundle 或 field catalog，先更新版本号，再分别运行对应 export 工具，并同步索引、changelog 和 final report guide。

## 核心路径

- `GET /health`
- `POST /ask`
- `POST /risk/analyze`
- `POST /risk/report`
- `POST /risk/report/export`

`/risk/report/export` 的 `200` 响应包含 Markdown 或 JSON 两种实际内容形态；当前 closeout 不把它改造成单一 OpenAPI response model。

## 边界

- 不启动 FastAPI 服务。
- 不接正式前端。
- 不调用 `rag_query`。
- 不访问 Qdrant。
- 不调用 LLM 或 Cross-Encoder。
- 不运行 full eval。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。

## 后续建议

v0.4.16.x 可以视为已收口。下一阶段若继续向前端方向推进，建议二选一：

- 做最小 mock service / UI handoff 准备，仍不连接真实 RAG。
- 开正式前端接入设计，但先明确页面范围、接口调用边界、错误态展示和人工复核入口。

如果下一阶段回到 RAG 主链路，应另开新系列版本，并按主链路修改要求重新定义目标、验证范围和回归策略。
