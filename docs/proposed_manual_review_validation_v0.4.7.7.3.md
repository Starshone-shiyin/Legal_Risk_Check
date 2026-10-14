# Proposed Manual Review Validation v0.4.7.7.3

## 定位

本版本对 importer 输出的 proposed decision schema 单独运行 validator。

这是 proposed schema 校验，不执行 promotion，也不覆盖原始 schema。

## 严格边界

- 不 promotion。
- 不覆盖原始 decision schema。
- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。

## 新增内容

- `tools/validate_proposed_manual_review_decisions.py`
- `tests/test_proposed_manual_review_validation.py`
- `tests/proposed_manual_review_decision_validation_report.json`

## 当前报告摘要

- Total records：36
- Valid records：0
- Pending records：36
- Invalid records：0

当前 proposed schema 没有导入任何人工结论，因此全部仍为 pending。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\validate_proposed_manual_review_decisions.py
.\venv\Scripts\python.exe -m unittest tests.test_proposed_manual_review_validation
.\venv\Scripts\python.exe tools\validate_proposed_manual_review_decisions.py --proposed-schema tests\proposed_manual_review_decision_schema.json --output tests\proposed_manual_review_decision_validation_report.json --fail-on-invalid
```
