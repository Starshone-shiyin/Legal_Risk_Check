# v0.4.7.8.18 Manual Review Visual Workbench Pilot Review Assist

本版本把 v0.4.7.8.17 生成的 `manual_review_pilot_case_review_assist_report.json` 接入离线人工复核网页，作为“试点审阅辅助”只读面板。

## 定位

这是 RAG grounding 质量治理中的阅读辅助，不是样本修补工具，也不是半自动填表器。

面板用于帮助 reviewer 看懂 5 个 pilot case：

- 案件为什么进入试点复核。
- 原 LLM 输出中涉及了哪些风险类型和整改动作。
- 当前 evidence chain 可能缺少哪些主争点、场景核心或最终证据。
- reviewer 应优先核对哪些问题。

## 边界

- 不生成 completed manual decision。
- 不写入或导入 `reviewer_input_template`。
- 不提供“复制到草稿”按钮。
- 不进入 `ai_suggestion` 或 `applyAiSuggestion()` 路径。
- 导出 JSON/CSV 时剥离 `pilot_review_assist`。
- 不接入 `rag_query`、后端 API、Qdrant 或 LLM。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。

## 安全处理

构建器只接受满足以下条件的报告作为 case 辅助信息：

- `schema_kind == advisory_pilot_case_review_assist`
- `advisory_packet_only == true`
- `contains_completed_manual_decisions != true`
- `summary.completed_manual_decisions == 0`

此外，构建 payload 前会递归剥离只读报告中的危险字段：

- `reviewer_input_template`
- `reviewer_decision`
- `workbench_items`
- `decision_status`

## 页面输出

“决策”页新增 `试点审阅辅助 / Pilot review assist` 面板，显示：

- 只读辅助提示。
- 案件简述。
- 辅助倾向与证据支撑状态。
- 通用 assist signals。
- 原 LLM 风险类型和整改动作。
- 建议人工核对问题。
- 辅助理由。
- 缺失或流失证据示例。

这些内容仅帮助阅读，不改变人工表单的必填项。真正可导出的内容仍必须由 reviewer 填写 reviewer、reviewed_at、decision 和 rationale 等字段。

## 验证重点

- payload 中 5 个 pilot case 均挂载只读 `pilot_review_assist`。
- build report 声明 `supports_pilot_review_assist_panel=true`。
- 单测验证危险键不会进入 case 辅助投影或顶层 assist report。
- 可执行前端导出测试验证 `pilot_review_assist` 不会进入 exported workbench item。
- 静态扫描验证没有调用 `fetch`、`XMLHttpRequest`、`/ask`、`rag_query`、`ChatOpenAI` 或 `QdrantClient`。
