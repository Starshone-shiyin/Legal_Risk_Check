# Manual Review Export Pipeline Dry Run v0.4.7.8.14

## 目标

本版本新增一个离线 dry-run 工具，用来验证 visual workbench 导出的 filled workbench 是否能够安全进入既有治理链路：

`filled workbench -> importer -> diff -> proposed validator -> promotion dry run -> closeout`

它不是修复工具，不会覆盖原始 decision schema，也不会修改 RAG 主流程。

## 新增内容

- 新增 `tools/build_manual_review_export_pipeline_dry_run.py`。
- 新增 `tests/manual_review_export_pipeline_dry_run_report.json`。
- 新增隔离中间产物目录 `tests/manual_review_export_pipeline_dry_run_artifacts/`。
- 新增 `tests/test_manual_review_export_pipeline_dry_run.py`。

## 默认 dry-run 结果

默认输入为 `tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json`。该文件只是 AI suggestion 安全稿，不是人工复核结论。

当前结果：

- `pipeline_conclusion=blocked_as_expected_ai_suggestion_only`
- `gate_status=blocked`
- `input_rows=12`
- `imported_rows=0`
- `rejected_rows=12`
- `empty_importable_content=12`
- `promotion_candidates=0`
- `ready_action_candidates=0`

这说明 AI suggestion 不会被误提升为 completed manual decision。

## 正向链路保证

单测构造了一个最小人工 ready filled workbench：

- importer 可生成 proposed schema。
- diff 可识别 changed case。
- proposed validator 可给出 valid record。
- promotion dry run 可产生 promotion candidate 和 ready action。
- closeout gate 可变为 `open`。

这证明链路可用，但只有真实人工 completed + valid decision 才能进入后续治理。

## 保守阻断规则

即使既有 closeout gate 因存在有效人工记录而显示 `open`，本 dry-run 仍会额外检查导入质量：

- 如果存在 `rejected_rows`，输出 `blocked_input_rejections_require_review`。
- 如果存在 `missing_case_id`、`unknown_case_id`、`duplicate_case_id` 或 `empty_importable_content`，会写入 `dry_run_blockers`。
- CLI 不允许把 dry-run report 直接写到 canonical pipeline artifact 文件名上，例如 `proposed_manual_review_decision_schema.json`。

这条规则用于避免“一个有效人工结论夹杂坏行”被误读为可直接进入后续治理。

## 安全边界

- 不覆盖 `tests/proposed_manual_review_decision_schema.json` 等 canonical pipeline 产物。
- 不把 prescreen 或 AI suggestion 当人工结论。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- 不接入 `rag_query`、Qdrant、LLM 或后端 API。
- 不自动生成工程修复任务。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_export_pipeline_dry_run.py tests\test_manual_review_export_pipeline_dry_run.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_export_pipeline_dry_run
.\venv\Scripts\python.exe tools\build_manual_review_export_pipeline_dry_run.py
rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient" tools\build_manual_review_export_pipeline_dry_run.py
```
