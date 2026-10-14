# v0.4.18.3 Product View Model Contract

## 目的

本版本是 v0.4.18.2 产品设计简报的结构化后继：在正式 UI 还未定稿、接口还未接入之前，先定义未来产品页面可以消费的离线 view model contract，避免前端设计和后端数据结构各自漂移。

## 新增产物

- `tests/fixtures/product_view_models_v0.4.18.3.json`
- `tools/check_product_view_model_contract.py`
- `tests/test_product_view_model_contract.py`
- `tests/product_view_model_contract_v0.4.18.3_report.json`

## 覆盖模块

fixture 定义了五类产品 view model：

1. `dashboard_summary`：首页风险驾驶舱，包含综合风险、关键指标、风险卡片、预警、任务、最近报告和数据源状态。
2. `legal_workspace`：法律风控 RAG 工作台，包含会话、活动问答、证据链、上传类型和报告动作。
3. `market_signals`：市场行情与外部风险信号，包含监管、行情或外部事件对风险事项的影响。
4. `supply_chain_map`：供应链地图，包含节点、边、区域 overlay 和风险关联。
5. `lifecycle_risk`：企业全生命周期风险流程，包含阶段节点、风险、证据引用和建议动作。

同时定义了跨模块共享的 `product_risks`，让 dashboard、法律工作台、市场信号、供应链地图和生命周期视图都通过 `risk_id` 关联到同一组产品级风险事项。

## Checker 规则

`tools/check_product_view_model_contract.py` 检查：

- 顶层版本、guardrails、shared enums、product risks 和 view models 是否存在。
- `dashboard_summary`、`legal_workspace`、`market_signals`、`supply_chain_map`、`lifecycle_risk` 五个 view model 是否齐全。
- product risk 的 `risk_id`、`risk_level`、`source_modules` 是否有效。
- 各模块引用的 `risk_id` 是否存在于 `product_risks`。
- supply-chain edge 引用的 node 是否存在。
- lifecycle stage 引用的 evidence 是否存在于 legal workspace evidence chain。
- guardrails 是否保持 `not_started` / `not_called`。

当前报告 `tests/product_view_model_contract_v0.4.18.3_report.json` 显示：

- `status=passed`
- `view_model_count=5`
- `product_risk_count=3`
- `dashboard_risk_cards=3`
- `market_signal_count=2`
- `supply_chain_node_count=2`
- `lifecycle_stage_count=3`
- `issue_count=0`

## 边界

- 不实现 UI。
- 不新增正式 API。
- 不启动 FastAPI 服务。
- 不调用 `rag_query`、`analyze_risk`、`generate_risk_report` 或报告导出链路。
- 不访问 Qdrant。
- 不调用 LLM。
- 不接真实行情、地图、供应链或权限系统。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval cases、hidden seed 或 Qdrant 数据。
- fixture 是离线 UI/view-model 样例，不是真实业务数据、不是 eval case、不是 completed manual decision，也不是 ready action。

## 下一步

后续可以在此基础上继续做：

- dashboard / legal workspace / map / lifecycle 的 mock endpoint contract；
- UI 原型与 view model 字段对齐；
- 文件上传和报告生成入口的产品态数据约束；
- 等 UI 方向稳定后，再决定是否把这些 view models 接入正式 API。
