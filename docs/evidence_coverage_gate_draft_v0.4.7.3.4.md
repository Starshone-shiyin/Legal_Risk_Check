# Coverage Gate Draft v0.4.7.3.4

## 定位

本版本属于 v0.4.7.3.x Evidence Coverage Quality Series。它把 evidence coverage、coverage triage 和 manual review dataset 汇总为非强制 gate 草案，用于观察未来版本是否回退。

它不是强制发布门禁，也不改变主链路。

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。
- 不调用 LLM、embedding、Qdrant 或 rerank。
- 不默认 fail。

## Draft Gates

当前草案包含 7 个 gate：

- `draft.high_priority_review.max`
- `draft.review_ratio.max`
- `draft.final_coverage.min`
- `draft.enrichment_ratio.min`
- `draft.final_selection_loss.max`
- `draft.scenario_core_gap.max`
- `draft.manual_review_dataset.pending.max`

默认行为是 non-enforcing。只有显式传入 `--fail-on-blocking`，并且出现 `blocking_draft` 失败时，工具才会返回非零。

## 当前报告摘要

- Total gates：7
- Passed gates：7
- Failed gates：0
- Blocking draft failures：0
- Default exit behavior：`always_zero_unless_fail_on_blocking_is_set`

当前阈值以 v0.4.7.3.4 基线为草案：
- high-priority review：`<= 12`
- review ratio：`<= 0.6`
- final coverage：`>= 0.9`
- enrichment ratio：`>= 0.99`
- final selection loss：`<= 7`
- scenario core gap：`<= 8`
- pending manual review items：`<= 12`

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\draft_evidence_coverage_gates.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage_gate_draft
.\venv\Scripts\python.exe tools\draft_evidence_coverage_gates.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --manual-review-dataset tests\evidence_manual_review_dataset.json --output tests\evidence_coverage_gate_draft_report.json
```
