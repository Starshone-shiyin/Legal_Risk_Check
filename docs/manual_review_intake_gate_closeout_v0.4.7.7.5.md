# Manual Review Intake Gate Closeout v0.4.7.7.5

## 定位

本版本收束 v0.4.7.7.x Manual Review Intake Gate，汇总 intake contract、workbench importer、decision diff、proposed validation 和 promotion dry run。

这是 intake gate 总报告，不执行 promotion，不进入工程修复。

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

- `tools/build_manual_review_intake_gate_closeout.py`
- `tests/test_manual_review_intake_gate_closeout.py`
- `tests/manual_review_intake_gate_closeout_report.json`

## 当前报告摘要

- Gate status：`blocked`
- Imported rows：0
- Rejected rows：36
- Changed cases：0
- Blocked diff cases：0
- Valid proposed records：0
- Invalid proposed records：0
- Pending proposed records：36
- Promotion candidates：0
- Ready action candidates：0

## 阻塞原因

- `no_imported_review_rows`
- `no_promotion_candidates`
- `no_ready_action_candidates`

## 解释

当前真实 workbench 仍未填写，因此 intake gate 正确保持 blocked。下一步应填写 workbench 并重新运行 importer、diff、validation、promotion dry run 和 closeout，而不是直接进入工程修复。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_intake_gate_closeout.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_intake_gate_closeout
.\venv\Scripts\python.exe tools\build_manual_review_intake_gate_closeout.py --contract-report tests\manual_review_intake_contract_report.json --import-report tests\manual_review_workbench_import_report.json --diff-report tests\manual_review_decision_diff_report.json --validation-report tests\proposed_manual_review_decision_validation_report.json --promotion-report tests\validated_decision_promotion_dry_run_report.json --output tests\manual_review_intake_gate_closeout_report.json
```
