# Manual Review Governance Report v0.4.7.5.4

## 定位

本版本收束 v0.4.7.5.x Manual Review Decision & Governance Layer，把 decision schema、validator、action candidates 和 fixture candidate pool 汇总为治理报告。

这是治理摘要，不是修复执行器。

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

- `tools/build_manual_review_governance_report.py`
- `tests/test_manual_review_governance_report.py`
- `tests/evidence_manual_review_governance_report.json`

## 当前报告摘要

- Decision records：36
- Pending decisions：36
- Invalid decisions：0
- Ready action candidates：0
- Blocked action candidates：106
- Ready fixture candidates：0
- Blocked fixture candidates：58
- Readiness state：`manual_review_required`

## 当前建议

- `P0 complete_manual_review_decisions_first`
- `P1 plan_metadata_chunking_query_coverage_governance`
- `P1 plan_anchor_dependency_governance_after_manual_confirmation`
- `P2 plan_scenario_core_article_review_after_manual_confirmation`
- `P2 plan_final_evidence_policy_design_after_manual_confirmation`
- `P2 keep_fixture_candidates_blocked_until_valid_decisions`

## 解释

v0.4.7.5.x 把前序 evidence diagnostics 变成了可人工确认、可校验、可阻断越界修复的治理层。当前没有任何 ready candidate，因此下一步不应直接改检索、anchor、rerank、prompt 或 eval case，而应先完成人工复核 decision records。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_governance_report.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_governance_report
.\venv\Scripts\python.exe tools\build_manual_review_governance_report.py --decision-schema tests\evidence_manual_review_decision_schema.json --validation-report tests\evidence_manual_review_decision_validation_report.json --action-candidates tests\evidence_manual_review_action_candidates.json --fixture-pool tests\evidence_fixture_candidate_pool.json --output tests\evidence_manual_review_governance_report.json
```
