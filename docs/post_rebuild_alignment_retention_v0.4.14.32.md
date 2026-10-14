# v0.4.14.32 Post-Rebuild Evidence Alignment Retention

## 版本定位

v0.4.14.32 是生产重建后的主链路质量修复版本。它针对 v0.4.14.31 full RAG eval 暴露的 `final_evidence_selection_drop`，在 final evidence selector 增加一个保守的 evidence alignment retention 机制。

本版本不是新增 gate，也不是通过新增 anchor、修改 prompt、修改 rerank、修改 risk supplement 或修改 eval case 来补结果。它只在 Cross-Encoder 已经看过的候选内部，补救“高相关法律后果证据已进入 rerank input，但因 final top-3 cap 被挤出 evidence_chain”的情况。

## 修复内容

- `src/rag/retriever.py::_select_diverse_rerank_top` 保留原有 Cross-Encoder 排序和去重逻辑。
- 新增 selector-only 的 `_retain_high_alignment_evidence`：
  - 只检查已经进入 rerank input 的候选。
  - 最多替换 final top-3 中一个较弱证据，不扩大 evidence_chain 数量。
  - 要求候选同时满足用户问题核心片段重合与法律后果/责任词重合。
  - 如果 final evidence 已覆盖同一法律后果，不重复替换。
- 典型修复目标是商标连续三年不使用场景中，含“连续三年不使用/撤销”的商标法第 49 条已经进入 rerank input，但被 final top-3 挤出的问题。

## 验证结果

- targeted `risk_trademark_non_use_001`：通过；商标法第 49 条进入 final evidence。
- targeted `risk_tort_product_liability_001`：通过；本版本未改 prompt 或 risk supplement。
- full RAG eval：`tests/post_rebuild_rag_eval_after_alignment_retention_report.json`，60/60 passed。
- `tests/test_candidate_budget.py` 增加 4 条 selector 覆盖测试：
  - 高重合法律后果证据可从 rerank input 保留。
  - 无关后果词候选不会被保留。
  - 高词面重合但无法律后果信号不会被保留。
  - final evidence 已覆盖同一后果时不会重复替换。

## 边界

- 未修改 hidden seed。
- 未新增 anchor。
- 未修改 rerank model、rerank score、rerank prompt 或排序调用。
- 未修改 prompt。
- 未修改 risk supplement / term preservation 规则。
- 未修改 eval case、fixture 或 scenario registry。
- 未改变 evidence_chain 的 top_k 数量。

## 下一步

v0.4.14.32 已将 post-rebuild full RAG eval 从 58/60 恢复到 60/60。下一步应进入轻量的 post-fix stabilization：比较 `tests/post_rebuild_rag_eval_report.json` 与 `tests/post_rebuild_rag_eval_after_alignment_retention_report.json` 的 evidence delta，确认 selector retention 的实际触发范围和是否存在可解释的证据变化。
