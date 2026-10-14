# Final Evidence Selection Audit v0.4.7.4.5

## 定位

本版本属于 v0.4.7.4.x Evidence Quality Action Series。目标是只读审计 `rerank_input -> final evidence` 的覆盖流失，判断哪些已进入 rerank input 的证据没有被保留到 final evidence。

这是 RAG grounding quality diagnostics，不是 rerank 或 final 截断逻辑修补工具。

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 rerank。
- 不修改 final evidence selection / truncation 逻辑。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/audit_final_evidence_selection.py`
- `tests/test_final_evidence_selection_audit.py`
- `tests/final_evidence_selection_audit_report.json`

## 支持的 final selection 信号

- `final_selection_review_needed`
- `rerank_input_to_final_loss`
- `anchor_supported_but_final_lost`
- `primary_evidence_lost`
- `scenario_core_lost`
- `operative_evidence_lost`
- `liability_evidence_lost`
- `low_final_coverage_after_selection`

## 当前报告摘要

- Final selection loss cases：7
- High-priority review cases：5
- Issue summary：
  - `rerank_input_to_final_loss=7`
  - `primary_evidence_lost=7`
  - `anchor_supported_but_final_lost=6`
  - `operative_evidence_lost=6`
  - `scenario_core_lost=4`
  - `low_final_coverage_after_selection=2`
  - `liability_evidence_lost=1`
- Selection loss summary：
  - `loss_0_25_to_0_499=6`
  - `loss_0_5_or_more=1`
- Lost functional types：`operative_rule=3`、`procedural=3`、`liability=2`

## 解释

当前 final selection loss 不是单纯丢失背景材料。7 个 case 全部丢失 primary evidence，6 个 case 丢失 operative/procedural 支撑，4 个 case 丢失 scenario core，说明 final evidence selection 需要被单独治理。但本版本只输出诊断报告，不修改 rerank、prompt 或 final evidence selection 逻辑。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\audit_final_evidence_selection.py
.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_audit
.\venv\Scripts\python.exe tools\audit_final_evidence_selection.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --anchor-audit-report tests\anchor_dependency_audit_report.json --output tests\final_evidence_selection_audit_report.json
```
