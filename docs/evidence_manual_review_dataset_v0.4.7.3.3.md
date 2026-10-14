# Evidence Manual Review Dataset v0.4.7.3.3

## 定位

本版本属于 v0.4.7.3.x Evidence Coverage Quality Series。它将 high-priority evidence coverage review cases 固化为人工复核数据集。

数据集的目标是让后续人工确认 root cause，而不是自动修复样本、修改 eval case 或改变 RAG 主链路。

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
- 不写入人工结论。

## 输出

`tests/evidence_manual_review_dataset.json` 每条 review item 包含：

- `case_id`
- `review_status`
- `priority_score`
- `risk_level`
- `expected_domains`
- `root_causes`
- `detected_issues`
- `recommended_actions`
- `review_questions`
- `coverage_flow`
- `final_evidence_coverage`
- `scenario_core_coverage`
- `functional_type_coverage`
- `missing_final_expected`
- `missing_scenario_core`
- `final_evidence`
- `reviewer_fields`

`reviewer_fields` 只提供占位：
- `reviewer`
- `reviewed_at`
- `decision`
- `confirmed_root_causes`
- `rejected_root_causes`
- `notes`
- `follow_up_action`

## 当前报告摘要

- Total review items：12
- Pending review items：12
- Priority score：min 5、max 14

Root cause summary：
- `base_retrieval_gap=10`
- `anchor_dependency=9`
- `final_primary_gap=8`
- `scenario_core_gap=8`
- `final_selection_loss=7`
- `low_final_coverage=3`

Risk summary：
- high：8
- low：4

Domain summary：
- 数据合规：10
- 市场秩序：2
- 财税：1

存在跨域 case，因此 domain summary 按 expected domains 计数会大于 review item 总数。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_evidence_manual_review_dataset.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_manual_review_dataset
.\venv\Scripts\python.exe tools\build_evidence_manual_review_dataset.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --output tests\evidence_manual_review_dataset.json
```
