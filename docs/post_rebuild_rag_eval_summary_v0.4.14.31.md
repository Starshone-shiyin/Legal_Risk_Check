# v0.4.14.31 Post-Rebuild Full RAG Eval Summary

## 结论

- 状态：`needs_triage`
- baseline full RAG eval：`60/60`
- post-rebuild full RAG eval：`58/60`
- 回归 case：`2`
- failed check summary：`{'expected_answer_keywords': 1, 'expected_evidence': 1}`
- issue type summary：`{'answer_keyword_coverage_gap': 1, 'final_evidence_selection_drop': 1}`

## 失败样例

- `risk_tort_product_liability_001`
  - 是否 baseline 回归：`True`
  - retrieval stage：`PASS`
  - failed checks：`['expected_answer_keywords']`
  - 分类：`answer_keyword_coverage_gap`
  - 建议：`inspect_answer_grounding_and_eval_keyword_contract`
- `risk_trademark_non_use_001`
  - 是否 baseline 回归：`True`
  - retrieval stage：`RERANK_MISS`
  - failed checks：`['expected_evidence']`
  - 分类：`final_evidence_selection_drop`
  - 建议：`inspect_final_evidence_selection_without_changing_eval_cases`

## 边界

- 本摘要只读取已保存的 full RAG eval 报告和 baseline 报告。
- 本摘要不调用 RAG、Qdrant 或 LLM，不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
- 结论不是 runtime 修复；下一步应围绕两个真实回归做最小主链路排查。

## 下一步

- `triage_post_rebuild_full_rag_regressions`
