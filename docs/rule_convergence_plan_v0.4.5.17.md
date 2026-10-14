# v0.4.5.17 规则收敛设计稿

范围：只设计共享 `scenario_id`、迁移顺序和验证保护；不修改 `config/rag_anchor_rules.json`、不修改 `config/risk_payload_supplement_rules.json`、不修改 `src/rag/retriever.py`。

## 目标

v0.4.5.16 已经确认：Anchor 配置与风险输出补全配置存在大量重复 trigger 和疑似同场景多处维护。v0.4.5.17 的目标不是合并规则，而是先定义一套可迁移、可验证、可回滚的规则收敛设计，避免后续直接删除规则导致当前 60/60 稳定性受损。

## Scenario ID 命名规范

`scenario_id` 用于把同一业务场景在 Anchor、Risk Supplement、Eval case 和报告中的身份统一起来。

命名规则：
- 只能使用小写英文字母、数字和下划线：`^[a-z][a-z0-9_]*$`
- 推荐结构：`domain_subject_risk`
- 不使用条号、版本号、测试编号或中文。
- 一个 `scenario_id` 只表示一个业务场景，不表示一个法条或一条规则。
- 迁移初期只新增 `scenario_id` 元数据，不改变触发词、法条、风险类型、整改动作和排序逻辑。

示例：
- `pipl_automated_decision_bias`
- `trade_secret_customer_list_leak`
- `pipl_cross_border_sensitive_medical`
- `vat_false_invoice_deduction`
- `pipl_children_consent`

## 职责边界

Anchor 规则负责：
- 在分层召回后补齐关键法条证据。
- 维护场景到法律条文的映射。
- 提供必要的 rerank query hint。
- 不负责最终风险等级、置信度或答案兜底表述。

Risk Supplement 规则负责：
- 在证据进入上下文后稳定结构化输出。
- 维护风险类型、整改动作、风险等级、最低置信度和法言法语补充。
- 不参与候选召回、候选排序或 evidence 注入。

共享 `scenario_id` 负责：
- 标识“这是同一个业务场景”。
- 支持审计、报告、迁移和 targeted eval 绑定。
- 不直接参与运行时判断，至少第一阶段保持 metadata-only。

## 候选场景

### `pipl_automated_decision_bias`

现状信号：
- v0.4.5.16 报告中 `pipl_automated_decision_full` 与 `risk_rule_6` 的疑似同场景分数最高。
- 重复 trigger 包括：`自动化决策`、`算法歧视`、`差异化定价`、`价格歧视`、`AI算法`、`筛选简历`。

当前涉及规则：
- Anchor candidates：`pipl_automated_decision`、`pipl_automated_decision_full`
- Risk candidates：`risk_rule_6`
- Eval cases：`risk_algorithm_bias_001`、`risk_user_profile_overuse_001`

收敛设计：
- 先为两个 anchor 与对应 risk rule 增加同一个 `scenario_id=pipl_automated_decision_bias`。
- 保留两个 anchor 的触发词差异，暂不合并；先观察是否一个偏原则召回、一个偏完整场景召回。
- Risk rule 继续负责 `自动化决策不当`、`算法歧视`、公平性审计和人工复核输出。

验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_algorithm_bias_001 --case-id risk_user_profile_overuse_001
python tools/run_rag_eval.py --check-risk --repeat 3 --output tests/rag_stability_report.json
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

### `trade_secret_customer_list_leak`

现状信号：
- 重复 trigger Top 1 为 `客户名单`，同时出现在 `pipl_data_leak`、`pipl_internal_leak`、`unfair_competition_trade_secret`、`risk_rule_0`、`risk_rule_4`。
- v0.4.5.13 原始 repeat 曾在商业秘密场景暴露 `risk_level` 波动。

当前涉及规则：
- Anchor candidates：`pipl_data_leak`、`pipl_internal_leak`、`unfair_competition_trade_secret`
- Risk candidates：`risk_rule_0`、`risk_rule_4`
- Eval cases：`risk_employee_data_export_001`、`risk_unfair_competition_trade_secret_001`

收敛设计：
- `trade_secret_customer_list_leak` 应覆盖“客户名单被离职员工导出、出售或带到竞争对手使用”的场景。
- Anchor 层保留两类证据职责：个人信息/数据泄露证据与商业秘密侵权证据。
- Risk Supplement 层区分两类输出职责：公司数据安全管理失职、商业秘密侵权。
- 不在第一阶段删除任何一个 anchor；先通过共享 `scenario_id` 标出它们属于复合场景。

验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_employee_data_export_001 --case-id risk_unfair_competition_trade_secret_001
python tools/run_rag_eval.py --check-risk --repeat 3 --output tests/rag_stability_report.json
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

### `pipl_cross_border_sensitive_medical`

现状信号：
- `出境`、`境外`、`境外服务器`、`跨境`、`病历` 同时出现在 Anchor 与 Risk Supplement 中。
- `risk_ai_medical_training_export_001` 同时命中敏感个人信息、AI 训练和数据出境语义。

当前涉及规则：
- Anchor candidates：`pipl_sensitive_export`、`pipl_data_export`、`pipl_sensitive_info`
- Risk candidates：`risk_rule_9`、`risk_rule_2`
- Eval cases：`risk_ai_medical_training_export_001`、`risk_data_export_overseas_001`

收敛设计：
- `pipl_cross_border_sensitive_medical` 仅覆盖“医疗/病历等敏感个人信息 + 出境/境外处理”的复合场景。
- AI 训练目的变更可作为相邻场景保留，不在第一阶段并入本 `scenario_id`。
- Anchor 层负责个保法敏感个人信息与出境条文组合召回。
- Risk Supplement 层负责单独同意、出境告知、安全评估或标准合同等输出稳定。

验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_ai_medical_training_export_001 --case-id risk_data_export_overseas_001
python tools/run_rag_eval.py --check-risk --repeat 3 --output tests/rag_stability_report.json
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

### `vat_false_invoice_deduction`

现状信号：
- `虚开发票` 同时出现在 `vat_invoice`、`risk_rule_33`、`risk_rule_34`。
- `risk_vat_false_invoice_001` 是高规则依赖 case，且涉及法定术语保真。

当前涉及规则：
- Anchor candidates：`vat_invoice`、`vat_input_deduction`、`vat_taxpayer_rate`
- Risk candidates：`risk_rule_33`、`risk_rule_34`、`risk_rule_36`
- Eval cases：`risk_vat_false_invoice_001`

收敛设计：
- `vat_false_invoice_deduction` 只覆盖“虚开发票并用于抵扣进项税额”的风险场景。
- Anchor 层负责发票、进项税额抵扣和税收征管相关证据召回。
- Risk Supplement 层负责 `虚开发票风险`、停止违规抵扣、补缴税款及滞纳金等输出稳定。
- 由于该 case 同时有术语保真贡献，后续迁移时必须保留 `TERM_PRESERVATION_PASS` 观察。

验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_vat_false_invoice_001
python tools/run_rag_eval.py --check-risk --repeat 3 --output tests/rag_stability_report.json
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

### `pipl_children_consent`

现状信号：
- `risk_children_data_001` 是稳定性摘要中的高规则依赖 case。
- 儿童、未成年人、普通用户协议、监护人同意等触发条件已经同时存在于 Anchor 和 Risk Supplement。

当前涉及规则：
- Anchor candidates：`pipl_children`
- Risk candidates：`risk_rule_3`
- Eval cases：`risk_children_data_001`

收敛设计：
- `pipl_children_consent` 覆盖儿童个人信息处理、普通用户协议概括同意、监护人同意不足等场景。
- Anchor 层负责儿童个人信息、敏感个人信息和监护人同意相关证据召回。
- Risk Supplement 层负责 `儿童信息保护不力`、`未取得有效监护人同意`、专门规则、监护人同意核验等输出稳定。
- 第一阶段只加共享 `scenario_id`，不减少儿童场景触发词。

验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_children_data_001
python tools/run_rag_eval.py --check-risk --repeat 3 --output tests/rag_stability_report.json
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

## 迁移顺序

1. Metadata-only：只给候选 Anchor/Risk 规则增加 `scenario_id`，不改触发词、不改行为。
2. Audit grouping：让 `tools/audit_rule_debt.py` 按 `scenario_id` 聚合报告，观察重复 trigger 是否从“不可解释重复”变成“同场景内重复”。
3. Targeted eval：每个场景只跑绑定 case，确认输出未退化。
4. Stability gate：涉及任一规则配置变更后，运行 3 轮 RAG Eval 与稳定性门禁。
5. Optional consolidation：只有当同一 `scenario_id` 下的规则职责边界清楚后，才考虑减少重复 trigger 或合并相邻规则。

## 不做事项

- 不删除 Anchor 规则。
- 不删除 Risk Supplement 规则。
- 不把 Risk Supplement 逻辑前移到检索层。
- 不把 Anchor 逻辑后移到输出层。
- 不恢复 RRF 或 hybrid 分数融合。
- 不修改 `src/rag/retriever.py`。

## 发布门禁

任何实际规则迁移版本都必须通过：

```bash
python tools/check_rule_convergence_plan.py --plan docs/rule_convergence_plan_v0.4.5.17.md
python tools/run_rag_eval.py --check-risk --repeat 3 --output tests/rag_stability_report.json
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```
