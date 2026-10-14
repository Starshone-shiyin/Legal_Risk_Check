# v0.4.15.4 Selection Trace Attribution

## 结论

- status: `needs_near_tie_stability_design`
- classification: `raw_rerank_order_boundary_drift_not_selector_replacement`
- blockers: `['selected_alternate_candidate_changed_across_trace_runs', 'selected_alternate_follows_full_rerank_order_boundary']`
- selected alternate by run: `['中华人民共和国网络安全法|20', '中华人民共和国个人信息保护法|56', '中华人民共和国个人信息保护法|56', '中华人民共和国网络安全法|20', '中华人民共和国网络安全法|20']`
- selected alternate counts: `{'中华人民共和国个人信息保护法|56': 2, '中华人民共和国网络安全法|20': 3}`
- recommended next step: `design_near_tie_stability_policy_before_runtime_change`
- runtime fix authorized: `False`

## 归因

- 核心证据《个人信息保护法》第 24 条和第 48 条在本轮 trace repeat 中保持稳定。
- 第三席证据继续在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移。
- 每一轮最终选中的第三席都能在 `final_evidence_selection_trace.selected` 中找到。
- 选中的第三席始终是两个漂移候选中 full rerank order 更靠前的候选。
- 因此本轮可将直接原因归到 raw rerank stable order / near-tie boundary drift，而不是 selector replacement 额外替换。

## 边界

本报告只读取 v0.4.15.4 targeted repeat saved report，不运行 eval、不调用 `rag_query`、不连接 Qdrant 或 LLM。
本版本不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
