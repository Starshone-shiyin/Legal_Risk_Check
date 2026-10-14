# Manual Review AI Suggestion Isolation v0.4.7.8.13

## 安全补强

- 导出 JSON/CSV 时只包含 `ready` 的人工草稿；未满足人工确认、复核人、复核日期、结论、理由等条件的草稿不会写入 `workbench_items`。
- 复制 AI 建议到草稿后，`human_confirmed_ai_suggestion` 会重置为 `false`，避免旧确认误覆盖新复制内容。
- 导出摘要新增 `export_policy=ready_human_drafts_only`、`exported_draft_items` 和 `blocked_draft_items`，用于区分已导出的正式人工草稿与被阻断的本地草稿。
- Build report 新增 `exports_ready_human_drafts_only=true`，明确本工具的导出边界。
- 新增可执行前端导出回归：未确认 AI copied draft 导出 0，人工确认且 ready 后导出 1，重新复制 AI 建议后再次导出 0。

## 目标

本版本把 AI 辅助预填从“可被 importer 读取的人工复核字段”降级为“只读建议源”。它用于帮助 reviewer 看懂和参考诊断，不代表人工复核结论。

## 关键变化

- 新增 `tools/build_manual_review_ai_suggestion_prefill.py`。
- 新增 `tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json`，把 12 条 high confidence 预填内容放入 `ai_review_suggestion`。
- Visual workbench 新增 AI 建议面板，可展示建议结论、建议根因、建议动作、理由和备注。
- AI 建议可以复制到本地草稿，但不会复制复核人和复核日期。
- 复制 AI 建议后，必须勾选“我已人工复核并确认采纳这条 AI 建议”，否则草稿不会进入 ready 状态。
- 导出 JSON/CSV 时只导出浏览器本地人工草稿字段，不继承源 `reviewer_input_template`，也不导出 AI 来源标记。

## 安全边界

- AI 建议不是 reviewer decision。
- Safe suggestion 文件不写 `reviewer_input_template`。
- Safe suggestion 文件即使直接喂给 importer，也应被拒绝，而不是生成 completed decision。
- 本版本不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case 或 `rag_query` 主流程。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py tools\build_manual_review_ai_suggestion_prefill.py tests\test_manual_review_ai_suggestion_prefill.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench_build_artifact tests.test_manual_review_ai_suggestion_prefill tests.test_manual_review_visual_workbench
.\venv\Scripts\python.exe tools\build_manual_review_ai_suggestion_prefill.py --input tests\manual_review_prefill_high_confidence_12_v2.json --output tests\manual_review_ai_suggestion_prefill_high_confidence_12_v2.json
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
.\venv\Scripts\python.exe tools\import_manual_review_workbench.py --decision-schema tests\evidence_manual_review_decision_schema.json --workbench-input tests\manual_review_ai_suggestion_prefill_high_confidence_12_v2.json --output tests\proposed_manual_review_decision_schema_ai_suggestion_safety_check.json --report-output tests\manual_review_ai_suggestion_prefill_import_safety_check.json
rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient" tools\manual_review_visual_workbench\index.html tools\build_manual_review_visual_workbench.py tools\build_manual_review_ai_suggestion_prefill.py
```

结果：

- 定向单测：12 tests OK。
- Safe suggestion：12 suggestions。
- Import safety check：0 imported，12 rejected，`empty_importable_content=12`。
- Visual workbench build report：36 cases，gate `blocked`，`supports_ai_suggestion_isolation=true`。
- 静态扫描未发现 RAG、LLM、Qdrant 或后端调用入口。
