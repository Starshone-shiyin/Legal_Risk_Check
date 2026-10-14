# v0.4.17.4 RAG Expected-Level Review Packet

本版本承接 v0.4.17.3 的 targeted repeat 结果，只对固定失败 case 做保存报告复核分类。它不运行 eval，不调用 RAG/Qdrant/LLM，也不修改主链路或 eval case。

## 结论

`risk_unfair_competition_confusion_001` 被分类为 `expected_level_fact_strength_review`。

依据：

- 3 轮 targeted repeat 均为同一个 case 固定失败。
- 该 case 每轮 `retrieval_failure_stage=PASS`。
- dense、sparse、union、anchor、rerank_input、final 层均命中 expected evidence。
- `expected_evidence`、答案关键词、风险类型、置信度和整改动作检查均通过。
- 唯一失败检查是 `expected_risk_level`：actual `high`，expected `medium`，mismatch type `over_risk`。

因此，本版本不建议修改 retriever、anchor、prompt、rerank、risk supplement 或 eval case。下一步应把该 case 作为法律事实强度 / expected-level 复核项处理，必要时由人工决定 expected medium 是否仍然成立。

## 产物

- 新增 `tools/build_rag_expected_level_review_packet.py`
- 新增 `tests/test_rag_expected_level_review_packet.py`
- 新增 `tests/rag_expected_level_review_packet_v0.4.17.4_report.json`
- 新增本文档

## 边界

- 不运行 full eval 或 targeted eval。
- 不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant 数据。
- 本版本输出的是复核分类，不是样本修补授权。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/build_rag_expected_level_review_packet.py tests/test_rag_expected_level_review_packet.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_expected_level_review_packet tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/build_rag_expected_level_review_packet.py --repeat-report tests/targeted_rag_evidence_independence_v0.4.17.3_report.json --cases tests/rag_eval_cases.json --output tests/rag_expected_level_review_packet_v0.4.17.4_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`
