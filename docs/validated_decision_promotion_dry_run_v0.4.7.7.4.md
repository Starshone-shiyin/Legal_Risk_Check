# Validated Decision Promotion Dry Run v0.4.7.7.4

## 定位

本版本只筛选 completed + valid 的 proposed decisions，生成 promotion dry-run report。

这是 promotion 预演，不覆盖原始 schema，不执行任何工程修复。

## 严格边界

- 不覆盖原始 decision schema。
- 不改 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。

## 新增内容

- `tools/build_validated_decision_promotion_dry_run.py`
- `tests/test_validated_decision_promotion_dry_run.py`
- `tests/validated_decision_promotion_dry_run_report.json`

## 当前报告摘要

- Promotion candidates：0
- Ready action candidates：0
- Valid records：0
- Invalid records：0
- Pending records：36

当前 proposed schema 没有 completed + valid decision，因此没有可 promotion 项目。

## Promotion Policy

- 必须是 completed decision。
- 必须通过 proposed validation。
- 只输出 dry-run report。
- 不覆盖真实 schema。
- 不修改主流程或 eval case。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_validated_decision_promotion_dry_run.py
.\venv\Scripts\python.exe -m unittest tests.test_validated_decision_promotion_dry_run
.\venv\Scripts\python.exe tools\build_validated_decision_promotion_dry_run.py --proposed-schema tests\proposed_manual_review_decision_schema.json --validation-report tests\proposed_manual_review_decision_validation_report.json --output tests\validated_decision_promotion_dry_run_report.json
```
