# v0.4.15.12 Same-Bucket Signal Calibration

## Scope

本版本校准 `tools/run_rag_eval.py` 中的 `quality_signal_diagnostics`，把同一 coarse rerank bucket 内的高分未选候选拆成两层：

- `score_order_observations`：保留所有同桶高分候选观察，供后续人工或统计分析。
- `score_order_risks`：只在候选对应缺失且未达标的 `expected_evidence`，或缺失的 operative `expected_statutes` 时升级为 `same_bucket_selection_order_risk`。

## Why

v0.4.15.11 的 full eval 已经 60/60 passed，但诊断仍把 18 个同桶高分候选标为 review risk。v0.4.15.12 先尝试过运行时排序/选择修复，targeted 验证显示会破坏已稳定通过的 evidence chain。因此本版本不改 retriever，而是校准诊断口径：系统已满足 expected evidence 时，同桶候选保留为 observation，不再误报为风险。

## Outputs

- `tests/targeted_same_bucket_baseline_v0.4.15.12_report.json`：4 个高风险/代表 case x 3 轮，pass counts `[4, 4, 4]`。
- `tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json`：未改诊断前基线 full eval，60/60 passed，retrieval stage 全部 `PASS`。
- `tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json`：校准后 full eval，59/60 passed，retrieval stage 全部 `PASS`；唯一失败为 `risk_employee_facial_001` 单次答案关键词波动。
- `tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json`：`risk_employee_facial_001` 5/5 passed，确认该失败不是检索或 evidence chain 回归。

## Boundary

- 未修改 retriever、rerank、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant。
- 本版本是 RAG grounding quality diagnostics 校准，不是样本修补工具。
- 同桶信号仍保留 observation 可观测性；只有影响期望证据或核心规范覆盖时才升级为 risk。

## Verification

- `.\venv\Scripts\python.exe -m py_compile tools\run_rag_eval.py tests\test_rag_eval_diagnostics.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_rag_eval_diagnostics`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_same_bucket_baseline_v0.4.15.12_report.json --check-risk --case-id risk_algorithm_bias_001 --case-id risk_ai_medical_training_export_001 --case-id risk_employee_data_export_001 --case-id pipl_sensitive_definition_001 --repeat 3`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json --check-risk`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json --check-risk`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_employee_facial_output_stability_v0.4.15.12_report.json --check-risk --case-id risk_employee_facial_001 --repeat 5`
