# Manual Review Action Candidates v0.4.7.5.2

## 定位

本版本把人工复核 decision records 转换为 action candidates，并明确区分“已确认可进入工程设计”和“仍需人工确认的诊断建议”。

这是 RAG grounding quality governance 的行动候选层，不是修复执行器。

## 严格边界

- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不修改 scenario registry、knowledge manifest、chunking 或 selection policy。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/build_manual_review_action_candidates.py`
- `tests/test_manual_review_action_candidates.py`
- `tests/evidence_manual_review_action_candidates.json`

## Readiness Policy

- `ready_from_valid_decision`：只有 completed 且 validator 通过的人工结论才能生成 ready candidate。
- `blocked_pending_manual_review`：pending 记录只能生成诊断型 blocked candidate，不能作为修复授权。
- `rejected_no_action`：人工复核拒绝诊断或选择不行动。

## 当前报告摘要

- Total action candidates：106
- Ready action candidates：0
- Blocked pending candidates：106
- Rejected no-action candidates：0

当前没有人工 completed decision，因此所有候选动作均处于 blocked 状态。

## 支持的 action categories

- `retrieval_input_quality`
- `knowledge_source_coverage`
- `anchor_governance`
- `scenario_registry_governance`
- `final_evidence_policy`
- `fixture_candidate_governance`
- `manual_grounding_review`
- `functional_typing_quality`
- `diagnostic_data_capture`

## 解释

本版本只把治理动作做成候选清单，并保留 readiness。后续工程版本只能消费 `ready_from_valid_decision`，不能把 `blocked_pending_manual_review` 当作可执行修复。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_action_candidates.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_action_candidates
.\venv\Scripts\python.exe tools\build_manual_review_action_candidates.py --decision-schema tests\evidence_manual_review_decision_schema.json --validation-report tests\evidence_manual_review_decision_validation_report.json --output tests\evidence_manual_review_action_candidates.json
```
