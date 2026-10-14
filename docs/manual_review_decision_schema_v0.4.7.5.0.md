# Manual Review Decision Schema v0.4.7.5.0

## 定位

本版本开启 v0.4.7.5.x Manual Review Decision & Governance Layer。目标是把 `v0.4.7.4.6` 的 pending review packages 转换为可填写、可校验、可追溯的人工复核 decision records。

这是 RAG grounding quality governance，不是样本修补工具，也不是自动修复入口。

## 严格边界

- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不把诊断信号直接当作修复指令。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/build_manual_review_decision_schema.py`
- `tests/test_manual_review_decision_schema.py`
- `tests/evidence_manual_review_decision_schema.json`

## 输入与输出

输入：

- `tests/evidence_manual_review_loop_report.json`

输出：

- `schema`：允许的 decision、root cause、follow-up action、必填 reviewer fields、禁止变更目标与全局 guardrails。
- `decision_records`：每个 case 一条 pending 人工决策记录。
- `summary`：pending 数、queue 分布、issue 分布、建议 root cause/action 分布和高优先级人工决策清单。

## 当前报告摘要

- Decision records：36
- Pending decisions：36
- Completed decisions：0
- Deferred decisions：0

本版本只生成空白决策模板和建议项，所有 `reviewer_decision` 字段均为空，等待人工填写。

## 支持的治理信号

- `metadata_chunking_or_query_coverage`
- `source_or_index_coverage`
- `anchor_dependency_governance`
- `scenario_core_scope`
- `final_evidence_selection_policy`
- `primary_evidence_gap`
- `high_risk_grounding_gap`
- `functional_typing_metadata`
- `insufficient_saved_evidence`

## 解释

`suggested_root_causes` 和 `suggested_follow_up_actions` 只是根据现有离线诊断生成的复核提示，不代表已经确认的工程结论。后续版本必须先校验人工填写的 `reviewer_decision`，再生成 action candidates 或 fixture candidates。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_decision_schema.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_schema
.\venv\Scripts\python.exe tools\build_manual_review_decision_schema.py --manual-review-loop tests\evidence_manual_review_loop_report.json --output tests\evidence_manual_review_decision_schema.json
```
