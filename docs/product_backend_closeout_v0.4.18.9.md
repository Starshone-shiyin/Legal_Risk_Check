# v0.4.18.9 Product Backend Closeout

本版本收口 v0.4.18.x 的产品后端设计。结论是：当前后端设计已经基本完成，可以支持 UI 原型和前端按照 fixture-backed `/product/*` 接口做联调准备；但真实 RAG 摘要、行情、地图、供应链和权限数据源尚未接入，后续必须按 provider 逐项接入。

## 读取顺序

1. `docs/product_design_brief_v0.4.18.2.md`
2. `docs/product_view_model_contract_v0.4.18.3.md`
3. `docs/product_mock_endpoint_contract_v0.4.18.4.md`
4. `docs/product_api_backend_integration_v0.4.18.5.md`
5. `docs/product_api_field_catalog_v0.4.18.6.md`
6. `docs/product_api_status_catalog_v0.4.18.7.md`
7. `docs/product_data_source_boundary_v0.4.18.8.md`
8. `docs/product_backend_closeout_v0.4.18.9.md`

## 当前可用接口

- `GET /product/dashboard/summary`
- `GET /product/legal/workspace`
- `GET /product/market/signals`
- `GET /product/supply-chain/map`
- `GET /product/lifecycle/risk`
- `GET /product/risks`

这些接口是真实 FastAPI route，但数据源仍是 `fixture_sample`。前端可以用它们做页面结构、状态、字段和空态对接；不能把返回内容视为实时业务结论。

## 后端分层

- `src/product/contracts.py`：endpoint contract。
- `src/product/schemas.py`：统一 response envelope。
- `src/product/router.py`：`/product/*` route。
- `src/product/service.py`：产品视图 service。
- `src/product/repository.py`：数据源/repository boundary。
- `src/product/status.py`：状态与错误码目录。

## 前端现在可以做什么

- 按 `/product/*` 接口对齐页面数据结构。
- 按字段目录映射页面文案、层级、表格列、卡片字段和筛选条件。
- 按状态目录处理 `ok`、`empty_items`、fixture runtime error 和未来数据源降级错误。
- 按 data source boundary 约定，把真实 provider 接入视为后续独立版本，不在 UI 原型阶段硬连真实数据。

## 后续真实数据源接入规则

1. 一次只接一个 provider，优先选择 `legal_rag_summary_provider` 或 `market_signal_provider`。
2. provider 必须在 repository/provider adapter 后面实现，不能直接改 router。
3. 接入前先定义 targeted smoke、降级状态和错误语义。
4. 接入后再允许 UI 对该 provider opt-in 使用非 fixture 数据。

## 禁止事项

- 不把 `/product/legal/workspace` 当作实时 RAG 问答。
- 不在本 closeout 中接 RAG/Qdrant/LLM。
- 不接真实行情、地图、供应链或权限系统。
- 不新增 anchor，不修改 prompt、rerank、risk supplement、taxonomy、scenario registry 或 eval cases。

## 验收命令

```powershell
.\venv\Scripts\python.exe -m unittest tests.test_product_api_contract tests.test_product_api_field_catalog tests.test_product_api_status_catalog tests.test_product_data_source_boundary tests.test_product_backend_closeout
.\venv\Scripts\python.exe tools\build_product_backend_closeout.py --output tests\product_backend_closeout_v0.4.18.9_report.json
.\venv\Scripts\python.exe tools\run_project_health_check.py --output tests\project_health_check_report.json --fail-on-error
```

当前 closeout report 显示 `status=passed`、`backend_design_status=basically_complete`、`endpoint_count=6`、`openapi_passed=6`、`response_passed=6`、`currently_connected_provider_count=1`。
