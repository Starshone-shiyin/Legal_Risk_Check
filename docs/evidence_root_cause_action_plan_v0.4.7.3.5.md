# Evidence Root Cause Action Plan v0.4.7.3.5

## 定位

本版本收束 v0.4.7.3.x Evidence Coverage Quality Series。它把 coverage diagnostics、coverage triage、manual review dataset 和 gate draft 汇总为下一阶段行动计划。

它不修复任何 case，也不改变 RAG 主链路。

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

## 当前计划摘要

- Total planned actions：6
- P0：1
- P1：2
- P2：3
- Gate draft passed：true
- Next series：`0.4.7.4.x Evidence Quality Action Series`

## Actions

| Priority | Target Version | Action | Root Cause |
|---|---|---|---|
| P0 | `0.4.7.4.6` | High-Risk Manual Review Queue | `low_final_coverage` |
| P1 | `0.4.7.4.2` | Scenario Registry Calibration | `scenario_core_gap` |
| P1 | `0.4.7.4.6` | Primary Evidence Manual Review Loop | `final_primary_gap` |
| P2 | `0.4.7.4.3` | Base Retrieval Quality Audit | `base_retrieval_gap` |
| P2 | `0.4.7.4.4` | Anchor Dependency Audit | `anchor_dependency` |
| P2 | `0.4.7.4.5` | Final Evidence Selection Audit | `final_selection_loss` |

## 下一阶段原则

v0.4.7.4.x 应继续保持：

- 先 audit，后修复。
- 先确认 root cause，再改变主链路。
- 所有小版本仍需独立报告、独立测试、独立文档。
- 不用 hidden seed 打补丁。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_evidence_root_cause_action_plan.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_root_cause_action_plan
.\venv\Scripts\python.exe tools\build_evidence_root_cause_action_plan.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --manual-review-dataset tests\evidence_manual_review_dataset.json --gate-draft-report tests\evidence_coverage_gate_draft_report.json --output tests\evidence_root_cause_action_plan.json
```
