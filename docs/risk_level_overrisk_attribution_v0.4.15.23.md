# v0.4.15.23 Risk Level Over-Risk Attribution

## 定位

本版本读取 v0.4.15.22 strict risk-level eval 报告，对 `over_risk` case 做只读归因候选和人工复核分流。它不是风险规则修复工具，也不声称能凭 compact report 精确判定根因。

## 输入与输出

输入：

- `tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json`

输出：

- `tests/risk_level_overrisk_attribution_v0.4.15.23_report.json`

## 结果摘要

- 状态：`overrisk_attribution_ready`
- over-risk case count：5
- attribution counts：`output_rule_amplification_review=5`
- review route counts：
  - `risk_supplement_rule_review=4`
  - `scene_output_rule_review=4`
  - `answer_wording_overstatement_review=4`
- confidence counts：`strong_signal=5`
- retrieval failure stage summary：`PASS=60`

高优先级人工复核清单：

- `risk_property_management_001`
- `risk_trademark_generic_name_001`
- `risk_trademark_non_use_001`
- `risk_vat_mixed_sales_001`
- `risk_unfair_competition_confusion_001`

## 解释边界

compact report 能支持以下判断：

- 5 个 case 均为 exact risk-level `over_risk`。
- retrieval 全部为 `PASS`，不是召回失败。
- output contribution counts 显示 risk supplement 或 scene output rule 参与了多数 case 的输出。

compact report 不能严格证明：

- 具体 taxonomy category 或 default level 是否错误。
- 具体 risk supplement rule id 是否错误。
- LLM 原始输出在后处理前是否已过度定级。
- expected risk level 是否应由人工改为 high。

因此本版本只输出 `suspected_root_causes`、`confidence`、`review_reason` 和 `recommended_next_step`，不自动修改规则。

## 后续建议

下一步应针对 5 个 high-priority case 运行 full trace 或人工复核，重点检查：

- risk supplement rule 是否把 medium 场景提升成 high。
- scene output rule 是否注入了过重的整改动作或责任表述。
- risk_types/actions 数量过多是否放大了风险等级。
- expected risk level 是否存在业务判断争议。

在完成复核前，不应恢复宽松 risk-level eval，也不应直接修改 anchor、retriever 或 prompt。
