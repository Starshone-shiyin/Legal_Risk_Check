# v0.4.7.8.16 Manual Review Pilot Batch Queue

## 目标

本版本把 v0.4.7.8.15 生成的首批 5 个人工复核 case 接入离线视觉审阅台，方便 reviewer 在同一个页面里筛选、阅读案由、核对证据、查看预筛/AI 参考建议，并继续在原有“决策”表单中填写真正的人工结论。

这是 **RAG grounding quality review execution support**，不是样本修补工具，也不是自动判案工具。

## 新增能力

- 视觉审阅台新增“首批试点”队列，只显示 pilot packet 中能按 `case_id` 匹配到 workbench 的 case。
- 每个 pilot case 的“决策”页新增只读“首批试点人工判断清单”。
- 清单展示优先审阅原因、证据问题摘要、最终证据链、缺失/曾丢失证据、预筛参考、AI 参考建议和人工判断选项。
- 清单中的 AI 字段继续使用 `advisory_decision`、`advisory_root_causes`、`advisory_follow_up_actions`，不混同为人工字段。
- 页面允许 reviewer 勾选“已阅读试点清单”，但该标记只用于本地页面状态，不会导出为人工结论。

## 安全边界

- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- 不接入 `rag_query`、后端 API、Qdrant 或 LLM。
- 不把 pilot packet 写入 `reviewer_input_template`。
- 不把预筛建议或 AI 建议自动提升为 completed manual decision。
- 导出 JSON 时会剥离 `pilot_batch` 只读元数据；只有 reviewer 亲自填写并满足 ready 条件的人工草稿才进入 `workbench_items`。

## 验证结果

- `py_compile` 通过。
- `tests.test_manual_review_visual_workbench` 通过。
- `tests.test_manual_review_visual_workbench_build_artifact` 通过，包含 JS 可执行回归：只勾选 pilot checklist 不会导出人工结论。
- `tests.test_manual_review_export_pipeline_dry_run` 通过，包含 checklist-only export 的 dry-run 阻断负例。
- 重新生成 `tools/manual_review_visual_workbench/index.html` 和 `tests/manual_review_visual_workbench_build_report.json`。

## Reviewer 使用方式

打开 `tools/manual_review_visual_workbench/index.html` 后，左侧选择“首批试点”。进入某个 case 的“决策”页，先看案由、原 LLM 输出、证据链和试点清单；如果确定要形成结论，再在下方表单填写复核人、日期、结论和理由。看不准可以留空或暂缓，不需要为了导出而硬填。
