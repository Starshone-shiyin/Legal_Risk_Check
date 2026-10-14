# v0.4.17.1 RAG Evidence Independence Baseline

本版本启动 v0.4.17.x RAG evidence independence / retrieval quality hardening 系列。它只读取既有 RAG eval 保存报告，建立主链路依赖归因基线；不运行 eval，不启动 Qdrant，不调用 `rag_query`，不修改 runtime。

## 目标

v0.4.15.26 的收口基线显示：compact full RAG eval 为 `59/60`，retrieval stage 为 `PASS=60`。但贡献标签显示通过结果仍有较高规则辅助依赖：

- `ANCHOR_PASS`
- `RISK_SUPPLEMENT_PASS`
- `TERM_PRESERVATION_PASS`
- `PURE_LLM_PASS`

本版本把这些信号按 case 归因，输出依赖热区、检索层缺口和下一步 triage 候选。

## 输出

- 新增 `tools/build_rag_evidence_independence_baseline.py`
- 新增 `tests/test_rag_evidence_independence_baseline.py`
- 新增 `tests/rag_evidence_independence_baseline_v0.4.17.1_report.json`

报告包含：

- `summary.label_counts`
- `summary.dependency_bucket_counts`
- `summary.retrieval_layer_gap_counts`
- `priority_lists.dependency_hotspots`
- `priority_lists.base_retrieval_query_lexical_triage`
- `priority_lists.targeted_rerun_before_runtime_change`
- `priority_lists.output_rule_dependency_review`
- `case_rows[*].independence_score`

## 边界

- 只读 saved report。
- 不运行 full eval 或 targeted eval。
- 不调用 `rag_query`。
- 不启动或访问 Qdrant。
- 不调用 LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。

## 当前结果

本版本不宣称 RAG 能力提升，只建立后续质量修复的基线。当前输出为：

- `status=has_failed_cases_and_dependency_hotspots`
- `passed_cases=59/60`
- `retrieval_failure_stage_summary={"PASS": 60}`
- `high_dependency_case_count=48`
- `high_dependency_ratio=0.8`
- `ANCHOR_PASS=29`
- `RISK_SUPPLEMENT_PASS=43`
- `TERM_PRESERVATION_PASS=8`
- `PURE_LLM_PASS=7`

这说明当前 RAG 不是“召回完全不可用”，而是通过结果中仍有较高比例依赖 anchor、risk supplement 或 term preservation。后续版本应从高依赖但已通过的 case 中挑选小批量 targeted rerun，确认哪些通过依赖稳定、哪些需要通用检索或证据选择改进。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/build_rag_evidence_independence_baseline.py tests/test_rag_evidence_independence_baseline.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_evidence_independence_baseline tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/build_rag_evidence_independence_baseline.py --input tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json --output tests/rag_evidence_independence_baseline_v0.4.17.1_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`
