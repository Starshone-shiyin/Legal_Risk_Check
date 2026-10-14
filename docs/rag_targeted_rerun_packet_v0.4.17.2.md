# v0.4.17.2 RAG Targeted Rerun Packet

本版本承接 v0.4.17.1 的 evidence independence baseline，把高依赖样本转成小批量 targeted rerun 候选包。它仍然只读取保存报告，不执行 eval，不调用 RAG/Qdrant/LLM，也不修改主链路。

## 目标

- 从 v0.4.17.1 报告中按通用 `next_action` 信号选择候选 case。
- 输出可复制的 targeted rerun 命令，方便下一步真正重跑时控制范围。
- 把 base retrieval lexical triage、output rule dependency、失败/预期等级复核、pure LLM 对照组分开，避免把不同问题混成一个 runtime patch。

## 边界

- 不新增 anchor。
- 不修改 prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。
- 不运行 full eval 或 targeted eval。
- 不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不给出 runtime patch 结论；本版本只给出下一轮验证队列。

## 产物

- 新增 `tools/build_rag_targeted_rerun_packet.py`
- 新增 `tests/test_rag_targeted_rerun_packet.py`
- 新增 `tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`
- 新增本文档

## 结果摘要

基于 `tests/rag_evidence_independence_baseline_v0.4.17.1_report.json` 生成候选包：

- 状态：`targeted_rerun_packet_ready`
- selected case：17
- base retrieval lexical triage：8
- output rule dependency review：5
- failed / expected-level review：1
- pure LLM control：3

建议的下一步不是直接改主链路，而是执行该 packet 给出的 bounded targeted repeat，确认高依赖信号是否稳定。如果重跑显示 base retrieval 问题稳定复现，再进入具体检索覆盖或证据选择修复；如果只是 output rule 扩张，再进入输出规则/风险等级归因，而不是补 anchor。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/build_rag_targeted_rerun_packet.py tests/test_rag_targeted_rerun_packet.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/build_rag_targeted_rerun_packet.py --input tests/rag_evidence_independence_baseline_v0.4.17.1_report.json --output tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`
