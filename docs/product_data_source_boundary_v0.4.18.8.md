# v0.4.18.8 Product Data Source Boundary

本版本把 fixture-backed `/product/*` 后端接口的数据读取层从 service 中拆出，形成明确的 repository boundary。目标是让未来真实 RAG 摘要、行情、地图、供应链和权限上下文可以逐项接入，而不是继续把 fixture 路径、真实客户端或临时逻辑塞进 router/service。

## 新增内容

- `src/product/repository.py`：新增 `ProductViewRepository` 协议、`FixtureProductViewRepository` 默认实现、`ProductViewModelError` 和 `PRODUCT_DATA_SOURCE_BOUNDARY`。
- `src/product/service.py`：`ProductViewModelService` 改为依赖 repository boundary；默认仍使用 `FixtureProductViewRepository`。
- `tools/export_product_data_source_boundary.py`：导出当前数据源边界目录。
- `tests/test_product_data_source_boundary.py`：验证 service 通过 repository 读取、fixture 版本漂移 fail closed、未来 provider 只登记槽位但未接入。
- `tests/product_data_source_boundary_v0.4.18.8.json`：当前边界导出结果。

## 当前边界

- 当前唯一已连接 provider：`fixture_sample`。
- 默认 repository：`FixtureProductViewRepository`。
- router 只依赖 `ProductViewModelService`，不读取 fixture path，也不创建真实数据客户端。
- service 依赖 `ProductViewRepository.load_payload()`，后续真实 provider 应实现该协议。
- 未来可接入槽位包括 `legal_rag_summary_provider`、`market_signal_provider`、`supply_chain_provider`、`lifecycle_risk_provider` 和 `permission_context_provider`。

## 明确未接入

本版本不接入真实数据源，不调用 RAG/Qdrant/LLM，不访问真实行情、地图或供应链数据，不启动服务，不运行 eval，也不修改知识库、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry 或 eval case。

## 验证结果

当前导出报告显示：

- `currently_connected_provider_count=1`
- `future_allowed_provider_count=5`
- `real_data_source_connected=false`
- `rag_query=not_called`
- `qdrant_access=not_called`
- `llm_access=not_called`

这说明 v0.4.18.8 完成的是产品后端数据源替换边界，不是正式业务数据源接入。
