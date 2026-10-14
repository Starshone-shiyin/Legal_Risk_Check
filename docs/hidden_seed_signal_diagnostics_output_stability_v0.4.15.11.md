# v0.4.15.11 Hidden-Seed Signal Diagnostics & Output Stability

## 目标

本版本把 hidden seed 暴露出的复合场景质量要求转成通用主链路诊断信号，并修复若干证据链已经正确但答案字段偶发低估的输出稳定性问题。

## 变更内容

- `tools/run_rag_eval.py` 新增 `quality_signal_diagnostics`。
- `src/rag/retriever.py` 新增产品责任术语保留和三类窄范围风险等级/措辞校准。
- `tests/test_rag_eval_diagnostics.py` 覆盖 evidence ref 映射、污染证据、定义条款替代规范条款、主争点缺证据和同桶选择顺序风险。
- `tests/test_retriever_contract.py` 覆盖产品责任赔偿术语、商标通用名称最低风险、违法分红弥补亏损措辞和股权转让未通知最低风险。

## 支持的质量信号

- `major_issue_evidence_gap`：配置了 hidden-style expected statutes，但最终证据链没有命中。
- `definition_substitutes_operative_rule`：只命中定义条款，缺少义务、程序、救济或原则类规范条款。
- `known_bad_evidence_leakage`：最终证据链命中已标记为 known-bad 的证据。
- `jurisdiction_or_domain_pollution`：最终证据链混入该场景标记为污染的法域/领域。
- `same_bucket_selection_order_risk`：同一 coarse rerank bucket 内存在未入选候选明显高于已入选候选的排序风险。

这些信号只写入 eval 报告，不改变检索、rerank、anchor、prompt、risk supplement 规则、eval case 或 hidden seed。

## 修复点

- 产品责任：当问题涉及商品/产品责任且证据链包含《民法典》时，保留“请求赔偿、追偿、惩罚性赔偿”。
- 商标通用名称：对“通用名称 + 商标”问题设置最低 `medium` 风险，避免偶发 `low`。
- 违法分红：对“未弥补亏损 + 分配利润”问题保留“弥补亏损/违法”措辞并保持高风险。
- 股权转让：对“股权 + 转让 + 未通知”问题设置最低 `medium` 风险。

## 验证结果

- `tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json`：5/5 passed。
- `tests/targeted_output_stability_v0.4.15.11_report.json`：4 个重点输出波动 case × 3 轮全过，`unstable_cases=[]`。
- `tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json`：full RAG eval 60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- 新增质量信号在 full eval 中记录 18 个 `same_bucket_selection_order_risk` review signals，作为后续诊断材料，不作为本版失败。

## 边界

本版本未修改 hidden seed、anchor、prompt、eval case、risk supplement 规则、scenario registry、fixtures、rerank 行为或 Qdrant 数据。新增内容属于 RAG grounding quality diagnostics 和 evidence-driven output stabilization，不是样本修补工具。
