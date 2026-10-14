# v0.4.15.24 Risk Level Over-Risk Legal Review Packet

## 定位

本版本读取 v0.4.15.22 strict risk-level eval 报告、v0.4.15.23 over-risk attribution 报告和现有 eval case metadata，为 5 个 `over_risk` case 生成只读法律复核包。

这是 RAG risk-level grounding quality diagnostics，不是样本修补工具，也不是风险规则修复工具。它只给出基于现有事实、证据链和 metadata 的初步法律合理性判断，供下一步人工复核或 targeted full trace 使用。

## 输入与输出

输入：
- `tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json`
- `tests/risk_level_overrisk_attribution_v0.4.15.23_report.json`
- `tests/rag_eval_cases.json`
- `config/scenario_registry.json`（可选辅助输入）

输出：
- `tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json`

## 结果摘要

- 状态：`legal_review_packet_ready`
- over-risk case count：5
- legal reasonableness counts：
  - `actual_high_likely_overstated=2`
  - `expected_medium_likely_reasonable=1`
  - `actual_high_potentially_defensible=2`
- high-risk manual review list：
  - `risk_trademark_generic_name_001`
  - `risk_trademark_non_use_001`
  - `risk_property_management_001`

逐案初判：
- `risk_trademark_generic_name_001`：`actual_high_likely_overstated`。行业通用名称缺乏显著性，核心风险更接近商标无效或正当使用抗辩，除非存在恶意维权或重大市场损害，high 偏重。
- `risk_trademark_non_use_001`：`actual_high_likely_overstated`。连续三年不使用通常是条件触发型撤销风险，缺少核心资产或重大损失事实时，high 偏重。
- `risk_property_management_001`：`expected_medium_likely_reasonable`。共有部分处分和物业管理违规成立，但主轴偏民事合规和共有权纠纷，medium 更稳妥。
- `risk_vat_mixed_sales_001`：`actual_high_potentially_defensible`。低税率导致少缴税款、补税和滞纳金时，high 有法律语义基础；但缺少金额、持续性或处罚事实时，medium 也可成立。
- `risk_unfair_competition_confusion_001`：`actual_high_potentially_defensible`。事实包含知名品牌近似和消费者误认，接近混淆行为核心要件；是否 high 取决于混淆事实和损害强度。

## 边界

- 不运行 eval，不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。
- 不授权直接改风险规则。报告中所有 case 均保留 `rule_change_allowed=false`。
- 法律判断是 preliminary review，不是最终法律意见；下一步仍需要人工复核或 targeted full trace。

## 后续建议

下一步应优先处理两个明显偏高的商标 case：
1. 检查 risk supplement / scene output rule 是否把无效、撤销、正当使用类 medium 风险放大为 high。
2. 若 full trace 证明是输出措辞或规则放大，应做最小风险等级修复，并用 targeted eval + compact full eval 验证。
3. 对增值税和反不正当竞争两个边界 case，先确认 expected medium 是否需要保留，避免把法律上可辩护的 high 错改掉。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/build_risk_level_overrisk_legal_review_packet.py tests/test_risk_level_overrisk_legal_review_packet.py`
- `./venv/Scripts/python.exe -m unittest tests.test_risk_level_overrisk_legal_review_packet`
- `./venv/Scripts/python.exe tools/build_risk_level_overrisk_legal_review_packet.py --eval-report tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json --attribution-report tests/risk_level_overrisk_attribution_v0.4.15.23_report.json --cases tests/rag_eval_cases.json --scenario-registry config/scenario_registry.json --output tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json`
