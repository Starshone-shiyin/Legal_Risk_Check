# Manual Review Workbench Importer v0.4.7.7.1

## 定位

本版本读取填写后的 visual manual review workbench JSON，并生成 proposed decision schema。

这是 proposed import，不覆盖真实 decision schema。

维护补充（2026-05-13）：正式 importer 已收紧为只接受页面导出的 filled JSON：`scope="filled visual manual review workbench export"` 且 `summary.export_policy="ready_human_drafts_only"`。CSV 仅保留为人工阅读/表格辅助产物，不再作为正式导入入口。

## 严格边界

- 不覆盖 `tests/evidence_manual_review_decision_schema.json`。
- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。

## 新增内容

- `tools/import_manual_review_workbench.py`
- `tests/test_manual_review_workbench_import.py`
- `tests/proposed_manual_review_decision_schema.json`
- `tests/manual_review_workbench_import_report.json`

## 当前报告摘要

基于当前清洗后的 5 个 pilot case filled JSON：

- Input rows：5
- Imported rows：5
- Rejected rows：0

该 JSON 来自页面导出后人工清洗，已通过 importer、diff、validator、promotion dry run 与 closeout gate。

## 导入规则

- 仅导入页面 filled JSON 中 `reviewer_input_template` 的人工复核字段。
- CSV、任意 JSON array、缺少 filled export 契约的 JSON 均拒绝。
- 单项中出现 advisory、AI suggestion、human confirmation required 或 AI 预填标记时拒绝。
- 未知 case 拒绝。
- 重复 case 拒绝。
- 空 reviewer 内容拒绝。
- 只输出 proposed schema，不覆盖原始 schema。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\import_manual_review_workbench.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_workbench_import
.\venv\Scripts\python.exe tools\import_manual_review_workbench.py --decision-schema tests\evidence_manual_review_decision_schema.json --workbench-input tests\filled_manual_review_workbench_pilot5_cleaned_2026-05-13.json --output tests\proposed_manual_review_decision_schema.json --report-output tests\manual_review_workbench_import_report.json
```
