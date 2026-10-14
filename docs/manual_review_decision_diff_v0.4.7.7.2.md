# Manual Review Decision Diff v0.4.7.7.2

## 定位

本版本比较原始 decision schema 与 proposed decision schema，输出字段级 diff 和 audit trail。

这是审计报告，不执行 promotion，也不覆盖任何 schema。

## 严格边界

- 不覆盖原始 decision schema。
- 不 promotion。
- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。

## 新增内容

- `tools/audit_manual_review_decision_diff.py`
- `tests/test_manual_review_decision_diff.py`
- `tests/manual_review_decision_diff_report.json`

## 当前报告摘要

基于当前 proposed schema：

- Changed cases：0
- Blocked cases：0
- Missing in proposed：0
- New in proposed：0

当前 workbench 为空填写，importer 没有导入任何变更，因此 diff 为空，符合预期。

## 审计能力

- 字段级 diff。
- reviewer / reviewed_at / decision 记录。
- proposed prohibited change targets 标记。
- missing/new case 检查。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\audit_manual_review_decision_diff.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_diff
.\venv\Scripts\python.exe tools\audit_manual_review_decision_diff.py --original-schema tests\evidence_manual_review_decision_schema.json --proposed-schema tests\proposed_manual_review_decision_schema.json --output tests\manual_review_decision_diff_report.json
```
