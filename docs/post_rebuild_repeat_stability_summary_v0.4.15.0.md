# v0.4.15.0 Post-Rebuild Repeat Stability Summary

## 结论

- 状态：`needs_triage`
- repeat：`3`
- pass counts：`[60, 60, 59]` / totals `[60, 60, 60]`
- all runs full pass：`False`
- unstable cases：`1`
- label variation cases：`2`
- final evidence identity drift cases：`1`
- answer drift cases：`60`
- blockers：`['baseline_failed_check_drift', 'baseline_pass_status_drift', 'repeat_evidence_identity_drift', 'repeat_not_all_runs_full_pass', 'repeat_pass_count_below_total', 'repeat_unstable_cases_present']`
- 推荐下一步：`triage_repeat_output_instability_before_runtime_change`

## 关键发现

本版本读取已保存的 repeat full RAG eval 报告和 v0.4.14.34 单次 60/60 基线，未重新运行评测，也未连接 Qdrant 或 LLM。

出现波动的 case：
- `risk_tort_product_liability_001`：`answer_or_check_instability_with_stable_retrieval`；pass_by_run=`[True, True, False]`；failed_checks_by_run=`[[], [], ['expected_answer_keywords']]`。

## 基线对比

- missing cases：`[]`
- new cases：`[]`
- pass status drifts：`1`
- retrieval stage drifts：`0`
- failed check drifts：`1`
- evidence identity drifts：`1`

## 边界

这是 RAG 质量稳定性诊断，不是样本修补工具，不是新增 gate 链，也不是 runtime 调参授权。本版本不修改 anchor、prompt、rerank、risk supplement、term preservation、scenario registry、hidden seed、fixtures 或 eval cases。
