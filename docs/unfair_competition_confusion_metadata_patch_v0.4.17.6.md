# v0.4.17.6 Unfair Competition Confusion Metadata Patch

本版本根据 v0.4.17.5 的法律文本版本核验结果，对 `risk_unfair_competition_confusion_001` 做一个人工确认后的元数据文字修正。

## 修改内容

- 将 `tests/rag_eval_cases.json` 中该 case 的 `legal_reasoning` 从旧编号“《反不正当竞争法》第6条”改为现行法“《反不正当竞争法》第7条”。
- 保持 `expected_evidence` 为第七条。
- 保持 `expected_risk_level=medium`。
- 不修改 question、expected keywords、expected risk types、expected actions 或 evidence match policy。

## 依据

v0.4.17.5 已核验：

- 2025 年第二次修订后的现行《反不正当竞争法》中，混淆行为条款为第七条。
- 2019 年修正文本中，混淆行为条款为第六条。
- 本项目向量库、manifest、anchor、expected evidence 和三轮 evidence chain 均指向第七条。

因此，这次修正属于旧编号元数据文字清理，不是样本放宽，也不是主链路修复。

## 结果

- v0.4.17.6 expected-level review packet 仍将固定失败分类为 `expected_level_fact_strength_review`。
- `metadata_warning_counts` 已清零。
- legal text version verification packet 分类变为 `current_law_evidence_valid`。
- 该 case 是否应保持 `medium` 或接受 `high`，仍属于 expected-level / fact-strength 复核问题。

## 边界

- 不新增 anchor。
- 不修改 prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、hidden seed 或 Qdrant 数据。
- 不改变 expected evidence 或 expected risk level。
- 不运行 full eval；本版本只重建相关保存报告并运行项目健康检查。

## 验证

- `./venv/Scripts/python.exe tools/build_rag_expected_level_review_packet.py --repeat-report tests/targeted_rag_evidence_independence_v0.4.17.3_report.json --cases tests/rag_eval_cases.json --output tests/rag_expected_level_review_packet_v0.4.17.6_report.json`
- `./venv/Scripts/python.exe tools/build_legal_text_version_verification_packet.py --review-packet tests/rag_expected_level_review_packet_v0.4.17.6_report.json --snapshot tests/legal_text_version_snapshot_v0.4.17.5.json --output tests/legal_text_version_verification_packet_v0.4.17.6_report.json`
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_legal_text_version_verification_packet tests.test_rag_expected_level_review_packet tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`
