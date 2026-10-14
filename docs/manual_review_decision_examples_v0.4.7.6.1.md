# Manual Review Decision Examples v0.4.7.6.1

## 定位

本版本提供 completed manual review decision 的合成示例，帮助 reviewer 理解如何填写 valid confirmation、valid rejection、valid defer，以及哪些越界目标会被 validator 拒绝。

这是示例与训练夹具，不是真实人工结论。

## 严格边界

- 不写入真实 decision records。
- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/build_manual_review_decision_examples.py`
- `tests/test_manual_review_decision_examples.py`
- `tests/manual_review_decision_examples.json`

## 当前报告摘要

- Total examples：4
- Valid examples：3
- Invalid examples：1
- Expectation mismatches：0

## 示例类型

- `valid_confirm_metadata`
- `valid_reject_issue`
- `valid_defer`
- `invalid_prohibited_target`

## 解释

示例文件独立于真实 `tests/evidence_manual_review_decision_schema.json`，不得合并回真实人工复核记录。它的作用是培训 reviewer 和防止非法填写模式进入后续工程链路。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_decision_examples.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_examples
.\venv\Scripts\python.exe tools\build_manual_review_decision_examples.py --decision-schema tests\evidence_manual_review_decision_schema.json --output tests\manual_review_decision_examples.json
```
