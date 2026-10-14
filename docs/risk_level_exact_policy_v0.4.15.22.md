# v0.4.15.22 Risk Level Exact Policy

## 定位

本版本修复 RAG eval runner 的风险等级验收口径。旧逻辑把 `actual risk_level >= expected_risk_level` 视为通过，因此 `risk_level=high, expected=medium` 会被判 OK。对于企业法律风控系统，这会掩盖 false positive 和风险分级过重问题。

## 实施内容

- `expected_risk_level` 改为 exact policy：actual 必须等于 expected。
- check message 增加 `policy=exact` 与 `mismatch_type`。
- check details 增加结构化字段：
  - `policy`
  - `actual_level`
  - `expected_level`
  - `mismatch_type`
- run summary 增加 `risk_level_mismatch_summary`，列出 mismatch counts 和 mismatch cases。

## 验证结果

### Targeted

`tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json`：

- 2/6 passed。
- retrieval stage：`PASS=6`。
- `risk_level_mismatch_summary={"over_risk":4,"exact_match":2}`。

### Full Compact Eval

`tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json`：

- 55/60 passed。
- retrieval stage：`PASS=60`。
- `risk_level_mismatch_summary={"exact_match":45,"over_risk":5}`。

严格口径暴露的 5 个 full-eval risk-level mismatch：

- `risk_property_management_001`
- `risk_trademark_generic_name_001`
- `risk_trademark_non_use_001`
- `risk_vat_mixed_sales_001`
- `risk_unfair_competition_confusion_001`

## 边界

- 不修改 `rag_query` 主流程。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation。
- 不修改 eval cases、hidden seed、fixtures、scenario registry 或 Qdrant。
- 本版本不是为了把 full eval 维持在 60/60，而是让评测报告真实暴露风险等级过高的质量债。

## 后续建议

下一步应针对 `over_risk` cases 做风险等级归因：区分是风险 taxonomy 规则过强、risk supplement 输出过强、LLM answer overstatement，还是 expected risk level 本身需要人工复核。该工作必须独立进行，不能通过恢复宽松评测口径来掩盖。
