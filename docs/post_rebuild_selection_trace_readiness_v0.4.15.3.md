# v0.4.15.3 Selection Trace Readiness

## 结论

- status: `passed`
- blockers: `[]`
- runtime behavior change: `False`
- recommended next step: `run_targeted_repeat_with_debug_trace_capture`

## 本版本新增的调试信号

- `debug_info.rerank_full_score_order`: 记录 Cross-Encoder score 返回后的全量稳定排序、输入位次和候选标识。
- `debug_info.final_evidence_selection_trace`: 记录 final evidence selector 的输入数量、选中项、未选中项、final rank、rerank rank 和 fallback 模式。
- 这些字段只在 `debug=True` 时写入返回结果，不参与排序、筛选、prompt、risk supplement 或 term preservation。

## Synthetic Sample

- selected chunk ids: `['a24', 'a48', 'b20']`
- not selected chunk ids: `['a24-sibling']`

## 边界

本版本是 RAG 主链路可观测性补丁，不是 rerank 调参，也不是 selector 行为修复。
不修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures、eval cases 或 Qdrant。
