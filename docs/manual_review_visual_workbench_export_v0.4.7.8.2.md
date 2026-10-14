# Manual Review Visual Workbench Export v0.4.7.8.2

## 定位

本版本把静态审阅台从“只读看板”推进到“可填写、可导出”的人工复核工具。

reviewer 可以在浏览器中填写复核字段，草稿保存在浏览器 localStorage 中。导出时页面只生成 filled workbench JSON/CSV，后续仍必须使用既有 importer、diff、validator、promotion dry run 和 closeout 工具链处理。

## 支持填写字段

- `reviewer`
- `reviewed_at`
- `decision`
- `confirmed_root_causes`
- `rejected_root_causes`
- `confirmed_follow_up_actions`
- `proposed_change_targets`
- `fixture_candidate`
- `rationale`
- `notes`

## 导出

- `filled_manual_review_workbench.json`
- `filled_manual_review_workbench.csv`

## 内置提示

页面会提示草稿是否缺少 reviewer、reviewed_at、decision、rationale、confirmed root cause，或包含禁止 target。

这些提示只是前端辅助，不替代 `tools/import_manual_review_workbench.py` 和 `tools/validate_proposed_manual_review_decisions.py`。

## 严格边界

- 页面不直接写文件系统。
- 页面不覆盖原始 decision schema。
- 页面不 promotion。
- 页面不修改任何 RAG、检索、prompt、anchor、risk 或 eval 配置。

## 后续命令

导出 filled workbench 后，应使用：

```powershell
.\venv\Scripts\python.exe tools\import_manual_review_workbench.py --decision-schema tests\evidence_manual_review_decision_schema.json --workbench-input <filled_workbench.csv> --output tests\proposed_manual_review_decision_schema.json --report-output tests\manual_review_workbench_import_report.json
.\venv\Scripts\python.exe tools\audit_manual_review_decision_diff.py --original-schema tests\evidence_manual_review_decision_schema.json --proposed-schema tests\proposed_manual_review_decision_schema.json --output tests\manual_review_decision_diff_report.json
.\venv\Scripts\python.exe tools\validate_proposed_manual_review_decisions.py --proposed-schema tests\proposed_manual_review_decision_schema.json --output tests\proposed_manual_review_decision_validation_report.json --fail-on-invalid
.\venv\Scripts\python.exe tools\build_validated_decision_promotion_dry_run.py --proposed-schema tests\proposed_manual_review_decision_schema.json --validation-report tests\proposed_manual_review_decision_validation_report.json --output tests\validated_decision_promotion_dry_run_report.json
.\venv\Scripts\python.exe tools\build_manual_review_intake_gate_closeout.py --contract-report tests\manual_review_intake_contract_report.json --import-report tests\manual_review_workbench_import_report.json --diff-report tests\manual_review_decision_diff_report.json --validation-report tests\proposed_manual_review_decision_validation_report.json --promotion-report tests\validated_decision_promotion_dry_run_report.json --output tests\manual_review_intake_gate_closeout_report.json
```
