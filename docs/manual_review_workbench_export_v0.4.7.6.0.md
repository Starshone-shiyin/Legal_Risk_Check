# Manual Review Workbench Export v0.4.7.6.0

## 定位

本版本开启 v0.4.7.6.x Manual Review Execution Kit，把 pending decision records 导出为 reviewer 可使用的 JSON/CSV 工作台。

这是人工复核执行入口，不是人工结论写入工具，也不是修复工具。

## 严格边界

- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不写入真实人工结论。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/export_manual_review_workbench.py`
- `tests/test_manual_review_workbench_export.py`
- `tests/evidence_manual_review_workbench.json`
- `tests/evidence_manual_review_workbench.csv`

## 当前报告摘要

- Workbench items：36
- Pending items：36
- High-priority items：36

## 输出说明

- JSON 保留完整 diagnostic summary、evidence context 和 reviewer input template。
- CSV 提供可排序、可浏览、可人工填写的扁平字段。
- reviewer 字段全部保持空白，不写入任何人工结论。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\export_manual_review_workbench.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_workbench_export
.\venv\Scripts\python.exe tools\export_manual_review_workbench.py --decision-schema tests\evidence_manual_review_decision_schema.json --output tests\evidence_manual_review_workbench.json --csv-output tests\evidence_manual_review_workbench.csv
```
