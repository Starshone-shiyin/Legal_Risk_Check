# Evidence Fixture Candidate Pool v0.4.7.5.3

## 定位

本版本把 manual review action candidates 中与 primary evidence、functional typing、final selection、scenario core 相关的项目沉淀为未来 fixture 候选池。

这是 fixture governance pool，不是 eval case 修改工具。

## 严格边界

- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不写入 fixtures 或 golden cases。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/build_evidence_fixture_candidate_pool.py`
- `tests/test_evidence_fixture_candidate_pool.py`
- `tests/evidence_fixture_candidate_pool.json`

## 当前报告摘要

- Total fixture candidates：58
- Ready fixture candidates：0
- Blocked fixture candidates：58
- Ready case count：0
- Blocked case count：36

当前没有人工 completed decision，因此所有 fixture candidates 都不能写入 eval cases 或 golden fixtures。

## 支持的 fixture types

- `primary_evidence_grounding_fixture`
- `functional_typing_fixture`
- `final_selection_grounding_fixture`
- `scenario_core_scope_fixture`

## 解释

本版本只是保留候选 fixture 的来源、证据上下文和阻塞原因。后续只有在人工复核 completed 且 validator 通过后，才可以把 ready fixture candidate 转成真正的 fixture 草案。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_evidence_fixture_candidate_pool.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_fixture_candidate_pool
.\venv\Scripts\python.exe tools\build_evidence_fixture_candidate_pool.py --decision-schema tests\evidence_manual_review_decision_schema.json --action-candidates tests\evidence_manual_review_action_candidates.json --output tests\evidence_fixture_candidate_pool.json
```
