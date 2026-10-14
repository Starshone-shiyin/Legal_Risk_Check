# Workbench Intake Contract v0.4.7.7.0

## 定位

本版本开启 v0.4.7.7.x Manual Review Intake Gate，定义人工填写 workbench 的导入契约。

这是导入前契约，不读取或写入真实人工结论。

## 严格边界

- 不覆盖原始 decision schema。
- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。

## 新增内容

- `tools/build_workbench_intake_contract.py`
- `tests/test_workbench_intake_contract.py`
- `tests/manual_review_intake_contract_report.json`

## 当前报告摘要

- Importable reviewer fields：10
- Read-only context fields：12
- Allowed decisions：5
- Allowed root causes：9
- Allowed follow-up actions：10
- Prohibited change targets：12

## 契约要点

- `case_id` 是唯一对齐键。
- 未知 case 拒绝导入。
- 重复 case 拒绝导入。
- 只导入 reviewer 字段，不导入上下文字段。
- 只输出 proposed schema，不覆盖原始 schema。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_workbench_intake_contract.py
.\venv\Scripts\python.exe -m unittest tests.test_workbench_intake_contract
.\venv\Scripts\python.exe tools\build_workbench_intake_contract.py --output tests\manual_review_intake_contract_report.json
```
