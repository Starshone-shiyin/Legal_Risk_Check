# Manual Review Decision Validator v0.4.7.5.1

## 定位

本版本为 `v0.4.7.5.0` 的人工复核 decision records 增加离线校验。目标是保证人工填写后的结论结构化、可追溯、不会越过既定边界。

这是 RAG grounding quality governance validator，不是自动修复工具。

## 严格边界

- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不根据 pending 诊断直接生成可执行修复。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/validate_manual_review_decisions.py`
- `tests/test_manual_review_decision_validation.py`
- `tests/evidence_manual_review_decision_validation_report.json`

## 校验规则

Validator 支持以下通用校验：

- pending 记录允许保持空白。
- completed 记录必须包含 reviewer、reviewed_at、decision 和 rationale。
- completed confirmation 必须至少确认 root cause 或 follow-up action。
- confirmed root cause 必须在 schema 允许列表内。
- confirmed follow-up action 必须在 schema 允许列表内。
- follow-up action 必须能由 confirmed root cause 推导。
- `no_action` 不能和其他 action 混用。
- reject decision 不能同时确认修复 action。
- proposed change targets 不得指向 hidden seed、anchor、rerank、prompt、risk supplement、eval case 或 `rag_query` 主流程。

## 当前报告摘要

- Total records：36
- Valid records：0
- Pending records：36
- Invalid records：0

当前全部记录仍为 pending，因此 validator 只确认模板合法、未发现越界结论。

## 解释

本版本的意义是把后续治理动作的入口收紧：只有通过 validator 的 completed decision 才能进入后续 action candidates。pending 记录可以用于工作量统计和建议摘要，但不能被视为已确认工程行动。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\validate_manual_review_decisions.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_validation
.\venv\Scripts\python.exe tools\validate_manual_review_decisions.py --decision-schema tests\evidence_manual_review_decision_schema.json --output tests\evidence_manual_review_decision_validation_report.json --fail-on-invalid
```
