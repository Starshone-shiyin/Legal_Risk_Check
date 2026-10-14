# Manual Review Loop v0.4.7.4.6

## 定位

本版本收束 v0.4.7.4.x Evidence Quality Action Series。目标是把 scenario calibration、base retrieval audit、anchor dependency audit、final evidence selection audit 汇总成可人工复核的 review loop package。

这是 RAG grounding quality diagnostics，不是人工结论写入、eval case 修补或 hidden seed 修补工具。

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 anchor 规则。
- 不修改 rerank。
- 不修改 final evidence selection / truncation 逻辑。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不写入人工复核结论。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/build_manual_review_loop.py`
- `tests/test_manual_review_loop.py`
- `tests/evidence_manual_review_loop_report.json`

## 汇总输入

- `tests/evidence_manual_review_dataset.json`
- `tests/scenario_registry_calibration_report.json`
- `tests/base_retrieval_quality_audit_report.json`
- `tests/anchor_dependency_audit_report.json`
- `tests/final_evidence_selection_audit_report.json`

## 当前报告摘要

- Review packages：36
- Pending review packages：36
- Queue summary：
  - `base_retrieval_quality_review=34`
  - `anchor_dependency_review=33`
  - `scenario_registry_calibration=8`
  - `primary_evidence_review=8`
  - `final_evidence_selection_review=7`
  - `high_risk_grounding_review=8`
- Follow-up action summary：
  - `metadata_chunking_or_query_coverage_review=34`
  - `anchor_dependency_governance_review=33`
  - `scenario_registry_core_article_review=8`
  - `primary_evidence_fixture_candidate_review=8`
  - `final_evidence_selection_policy_review=7`
  - `high_risk_manual_grounding_review=8`
- Fixture candidate review items：8

## 解释

本版本把前序离线审计从“多个报告”收束成以 case 为中心的人工复核包。每个 package 保留 queue tags、issue types、evidence context、suggested review questions、follow-up candidates 和 reviewer fields，但所有 reviewer fields 均为空，表示尚未写入人工结论。

下一阶段应先由人工确认这些 root causes，再决定哪些进入 fixtures、metadata/chunking 治理、scenario core article 调整或 final evidence selection 策略设计。当前仍不应直接改 rerank、prompt、anchor 或 risk supplement。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_loop.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_loop
.\venv\Scripts\python.exe tools\build_manual_review_loop.py --manual-review-dataset tests\evidence_manual_review_dataset.json --scenario-calibration-report tests\scenario_registry_calibration_report.json --base-audit-report tests\base_retrieval_quality_audit_report.json --anchor-audit-report tests\anchor_dependency_audit_report.json --final-selection-audit-report tests\final_evidence_selection_audit_report.json --output tests\evidence_manual_review_loop_report.json
```
