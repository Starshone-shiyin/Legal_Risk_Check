# Manual Review Visual Workbench Case Context v0.4.7.8.7

本版本补齐 visual workbench 的案由可读性缺口。此前页面能展示 case id、领域、诊断标签和证据缺口，但非系统设计者难以判断“这个案子到底在审什么”。v0.4.7.8.7 将已有离线报告中的问题文本、风险场景、预期风险类型和预期整改动作合并为 `case_context`，用于审阅台展示。

## 数据来源

- `tests/rag_eval_report.json`：读取已有 RAG eval report 中的 case question、risk level、risk types 和 recommended actions。
- `tests/rag_eval_cases.json`：读取已有 eval case 的 question、expected risk types、expected actions 和 expected risk level。
- `config/scenario_registry.json`：读取已登记 scenario 的 description、domain、risk types、required actions 和 linked eval case ids。

这些输入均为只读离线材料。工具不会修改 eval case、scenario registry、hidden seed、anchor、rerank、prompt、risk rules，也不会接入 `rag_query` 主流程。

## UI 更新

- 左侧 case 列表在 case id 下方展示案由线索和待审问题。
- 概览页顶部新增案由线索块，展示：
  - 案由线索
  - 待审问题
  - 风险场景
  - 涉及领域
  - 预期风险类型
  - 预期整改动作
  - 上下文来源
- 搜索框支持搜索 case id、案由、问题、风险类型、整改动作、场景描述、队列和领域。
- JSON 导出保留 `case_context` 只读上下文。
- CSV 导出新增只读列 `case_topic` 与 `question`，便于 reviewer 在表格中辨认案例；importer 仍只读取允许导入的 reviewer 字段。

## 质量口径

`items_with_case_context` 只统计来自已有评测报告或 scenario registry 的真实上下文信号，不把单纯的 `case_id` 当成案由。当前生成结果为 36/36。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
```

## 当前结果

- HTML：`tools/manual_review_visual_workbench/index.html`
- Build report：`tests/manual_review_visual_workbench_build_report.json`
- Workbench cases：36
- Items with case context：36
- Gate status：`blocked`
- Guardrails：仍为 offline static governance tool，不调用 backend、Qdrant、LLM 或 RAG 主流程。
