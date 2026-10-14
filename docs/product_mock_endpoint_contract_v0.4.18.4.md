# v0.4.18.4 Product Mock Endpoint Contract

## 目的

本版本把 v0.4.18.3 的 product view model contract 转成离线 mock endpoint contract，方便后续 UI 设计、前端原型和后端接口讨论围绕同一组产品态数据形状展开。

它是 UI handoff contract，不是正式 API 实现。

## 新增产物

- `tools/check_product_mock_endpoint_contract.py`
- `tests/test_product_mock_endpoint_contract.py`
- `tests/product_mock_endpoint_contract_v0.4.18.4_report.json`
- `docs/product_mock_endpoint_contract_v0.4.18.4.md`

## Mock Endpoint 范围

本版本定义 6 个只读 mock endpoint contract：

1. `GET /product/dashboard/summary`：首页风险驾驶舱。
2. `GET /product/legal/workspace`：法律风控 RAG 工作台状态。
3. `GET /product/market/signals`：市场、监管和外部风险信号。
4. `GET /product/supply-chain/map`：供应链地图节点、边和区域 overlay。
5. `GET /product/lifecycle/risk`：企业生命周期风险流程。
6. `GET /product/risks`：跨模块共享的产品级风险列表。

每个 endpoint 都从 `tests/fixtures/product_view_models_v0.4.18.3.json` 派生响应样例，并通过 `risk_id` 继续连接共享的 `product_risks`。

## Checker 规则

`tools/check_product_mock_endpoint_contract.py` 检查：

- source fixture 版本必须为 `0.4.18.3`。
- endpoint 必须是只读 `GET` contract。
- endpoint path 必须位于 `/product/` 命名空间。
- endpoint route 不得重复。
- endpoint 引用的 view model 必须存在。
- `data` response 必须是 JSON object，`items` response 必须是 JSON array。
- response 中出现的 `risk_id` / `risk_ids` 必须能在 `product_risks` 中找到。
- mock endpoint path 不得已经写入当前 `src/main.py` 的 FastAPI surface。

当前报告 `tests/product_mock_endpoint_contract_v0.4.18.4_report.json` 显示：

- `status=passed`
- `endpoint_count=6`
- `view_endpoint_count=5`
- `shared_endpoint_count=1`
- `product_risk_count=3`
- `issue_count=0`

## 边界

- 不新增正式 FastAPI 路由。
- 不启动服务。
- 不接 UI。
- 不实现 mock service daemon。
- 不调用 `rag_query`、`analyze_risk`、`generate_risk_report` 或报告导出链路。
- 不访问 Qdrant。
- 不调用 LLM。
- 不接真实行情、地图、供应链、权限系统或外部数据源。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval cases、hidden seed 或知识库数据。
- mock endpoint response 是产品态样例，不是法律结论、不是 eval case、不是 completed manual decision，也不是 ready action。

## 下一步

后续更合理的推进方式是：

- 等 UI 原型稳定后，按这些 mock endpoint contract 对齐页面字段；
- 若要进入真实后端实现，应另开版本，把正式 API 路由、鉴权、数据来源、缓存和回归测试作为工程变更处理；
- 法规扩容侧仍应优先推进 source/version lineage、单法新增 dry-run、targeted smoke 和扩容影响评估。
