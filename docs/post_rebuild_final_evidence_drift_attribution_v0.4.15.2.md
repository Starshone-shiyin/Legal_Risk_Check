# v0.4.15.2 最终证据漂移归因报告

## 结论

- status: `needs_selector_stability_design`
- classification: `rerank_top3_boundary_drift_after_core_evidence_locked`
- blockers: `['selected_alternate_candidate_changed_across_runs', 'both_alternates_present_before_final_selection']`
- 每轮选中的备选第三证据: `['中华人民共和国个人信息保护法|56', '中华人民共和国个人信息保护法|56', '中华人民共和国网络安全法|20', '中华人民共和国个人信息保护法|56', '中华人民共和国网络安全法|20']`
- 备选第三证据计数: `{'中华人民共和国个人信息保护法|56': 3, '中华人民共和国网络安全法|20': 2}`
- 建议下一步: `design_selection_trace_before_runtime_change`
- 是否授权运行时修复: `False`

## 归因

- 核心预期证据在多轮 targeted repeat 的最终证据中保持存在。
- 两个备选第三证据在每一轮最终选择前都已经进入候选层。
- 当前保存报告能观察到的首次分叉位于 `reranked_candidates/final_candidates` 的 top-3 边界。
- 漂移项是最终证据的第三个备选项，不是核心预期证据对。
- 现有保存报告不包含完整 raw Cross-Encoder score order，也不包含 selector decision trace。
- 局限: Saved debug_info stores selected reranked/final candidates but not the full raw Cross-Encoder score order for every rerank_input candidate; this report can attribute the drift to final third-slot alternate selection, but cannot prove whether the immediate cause is raw rerank score jitter or selector replacement logic.

## 边界

本报告是 saved-report attribution，不是运行时修复，也不是新增 gate 链。
本版本不修改 hidden seeds、anchors、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures、eval cases 或 Qdrant。
