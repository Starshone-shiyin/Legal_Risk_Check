# Scenario Registry v0.4.6.0

## 定位

`config/scenario_registry.json` 是法律风险场景的统一注册表雏形，用来登记分散在 Anchor Rules、Risk Supplement Rules、术语保真和评测集中的场景信息。本版本只建立注册表、校验工具、覆盖审计和单元测试，不接入 RAG 主流程，不改变检索、rerank、anchor 或风险补全行为。

## 首批场景

| scenario_id | domain | risk_level | 说明 |
|---|---|---|---|
| `trade_secret_customer_list_leak` | 市场秩序 | high | 客户名单、员工离职、内部导出与商业秘密侵权/数据泄露交叉场景 |
| `pipl_children_consent` | 数据合规 | high | 儿童个人信息处理、专门规则与有效监护人同意场景 |
| `pipl_automated_decision_bias` | 数据合规 | high | 自动化决策、算法歧视、差异化待遇和人工复核场景 |
| `pipl_cross_border_sensitive_medical` | 数据合规 | high | 医疗健康等敏感个人信息出境、目的变更和单独同意场景 |
| `vat_false_invoice_deduction` | 财税 | high | 虚开发票、进项税额抵扣违规与税务/刑事风险场景 |

## 字段约束

每个 scenario 至少包含：

```json
{
  "scenario_id": "...",
  "domain": "...",
  "description": "...",
  "risk_level": "low|medium|high",
  "core_articles": [],
  "risk_types": [],
  "required_actions": [],
  "legal_terms": [],
  "linked_anchor_rule_ids": [],
  "linked_risk_rule_ids": [],
  "eval_case_ids": []
}
```

## 校验工具

新增 `tools/check_scenario_registry.py`，执行以下检查：

- `scenario_id` 唯一，且使用 lowercase snake_case。
- `domain` 必须属于 `config/rag_anchor_rules.json` 中已有法域。
- `risk_level` 必须为 `low`、`medium` 或 `high`。
- `core_articles`、`risk_types`、`required_actions`、`legal_terms` 不得为空。
- `linked_anchor_rule_ids` 必须能在 `config/rag_anchor_rules.json` 中找到。
- `linked_risk_rule_ids` 必须能在 `config/risk_payload_supplement_rules.json` 中找到。
- 已经写入规则配置的 `scenario_id` 必须进入 registry，并且反向链接对应 Anchor/Risk rule id。
- `eval_case_ids` 如提供，必须能在 `tests/rag_eval_cases.json` 中找到。

运行：

```bash
python tools/check_scenario_registry.py --registry config/scenario_registry.json --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --eval-cases tests/rag_eval_cases.json
```

## Coverage Audit

checker 同时输出覆盖审计：

- `scenarios_missing_anchor_link`
- `scenarios_missing_risk_supplement_link`
- `scenarios_missing_eval_case`
- `rule_scenario_ids_missing_registry`

当前 v0.4.6.0 目标是四类缺口均为 `0`。这只表示首批 5 个 registry 场景与现有配置链接闭合，不表示全部规则已经完成 scenario 化。

## 边界

本版本不修改 `src/rag/retriever.py`，不删除、不合并现有规则，不改变任何规则匹配逻辑。后续版本可在 checker 稳定后，逐步把更多规则补充到 registry，再决定是否引入只读引用或治理视图。

## v0.4.6.1 只读加载层

v0.4.6.1 新增 `src/rag/scenario_registry.py`，让 Python 代码可以读取 registry，但仍不接入 `rag_query` 主链路，不改变检索、rerank、anchor 或 risk supplement 行为。

Loader API：

- `load_scenario_registry(path="config/scenario_registry.json")`
- `get_scenario_by_id(scenario_id)`
- `list_scenarios(domain=None)`
- `get_scenarios_by_anchor_rule(rule_id)`
- `get_scenarios_by_risk_rule(rule_id)`
- `get_core_articles_for_scenario(scenario_id)`
- `get_required_actions_for_scenario(scenario_id)`
- `clear_scenario_registry_cache()`

实现约束：

- loader 启动时复用 `tools/check_scenario_registry.py` 的校验逻辑。
- 校验失败时抛出 `ScenarioRegistryError`。
- 未知 `scenario_id` 返回 `None`；文章和整改动作 helper 对未知场景返回空列表。
- 对外返回防御性深拷贝，调用方修改返回对象不会污染缓存。
- 本层只用于只读查询和后续治理工具复用，不用 scenario 驱动检索或输出。

## v0.4.6.2 Targeted 验证

v0.4.6.2 新增 `tools/run_scenario_eval.py`，按 registry 中的 `eval_case_ids` 分组运行现有 RAG Eval 等价逻辑，验证首批 scenario 与当前 RAG 行为没有断链。

运行：

```bash
python tools/run_scenario_eval.py --registry config/scenario_registry.json --output tests/scenario_eval_report.json --summary tests/scenario_eval_summary.md
```

输出文件：

- `tests/scenario_eval_report.json`
- `tests/scenario_eval_summary.md`

报告包含：

- 每个 scenario 的 `pass/total`。
- 每个 scenario 的 `retrieval_failure_stage_summary`。
- 每个 scenario 的 `contribution_summary`。
- `missing_case_ids`。
- `scenarios_without_eval_case_ids`。
- `scenarios_all_failed`。

v0.4.6.2 targeted 结果：

| scenario_id | pass/total | retrieval stages | contribution labels |
|---|---:|---|---|
| `trade_secret_customer_list_leak` | 2/2 | PASS:2 | ANCHOR_PASS:1, RISK_SUPPLEMENT_PASS:2 |
| `pipl_children_consent` | 1/1 | PASS:1 | ANCHOR_PASS:1, RISK_SUPPLEMENT_PASS:1 |
| `pipl_automated_decision_bias` | 2/2 | PASS:2 | ANCHOR_PASS:2, RISK_SUPPLEMENT_PASS:2 |
| `pipl_cross_border_sensitive_medical` | 2/2 | PASS:2 | ANCHOR_PASS:2, RISK_SUPPLEMENT_PASS:2 |
| `vat_false_invoice_deduction` | 1/1 | PASS:1 | ANCHOR_PASS:1, TERM_PRESERVATION_PASS:1, RISK_SUPPLEMENT_PASS:1 |

汇总：5 个 scenario、8 个唯一 eval case 全部通过；`missing_case_ids=0`、`scenarios_without_eval_case_ids=0`、`scenarios_all_failed=0`。

本版本仍不接入 `rag_query` 主流程，不用 scenario 驱动检索或输出。

## v0.4.6.3 轻量门禁

v0.4.6.3 新增 `tools/check_scenario_eval_report.py`，把 v0.4.6.2 生成的 scenario targeted eval 报告纳入发布前机器检查。

运行：

```bash
python tools/check_scenario_eval_report.py --report tests/scenario_eval_report.json
```

门禁检查项：

- `missing_case_ids` 必须为空，即 missing case groups 为 `0`。
- `scenarios_without_eval_case_ids` 必须为空。
- `scenarios_all_failed` 必须为空。
- `total_scenarios >= 5`，可用 `--min-scenarios` 调整。
- `total_unique_eval_cases >= 8`，可用 `--min-cases` 调整。
- 每个 scenario summary 必须包含 `passed`、`total` 和 `retrieval_failure_stage_summary`。
- 每个 scenario 的 `total > 0`。
- 每个 scenario 的 `passed > 0`。
- 默认允许部分通过；如需强制每个 scenario 全部通过，可使用 `--no-allow-partial-pass`。

至此，scenario 治理链条形成闭环：

```text
registry → loader → targeted eval → eval gate
```

本门禁仍只读取报告，不接入 `rag_query` 主流程，也不用 scenario 驱动检索或输出。

## v0.4.6.4 第二批精选补全

v0.4.6.4 新增 5 个高价值企业法律风控 scenario，使 registry 从首批治理样本扩展为 10 个可评测场景：

| scenario_id | domain | linked anchor rules | linked risk rules | eval cases |
|---|---|---|---|---|
| `pipl_facial_recognition_attendance` | 数据合规 | `pipl_sensitive_info` | - | `risk_employee_facial_001` |
| `pipl_data_export_security_assessment` | 数据合规 | `pipl_data_export`, `pipl_data_export_assessment` | `risk_rule_9` | `risk_data_export_overseas_001`, `cross_law_export_assessment_001`, `pipl_data_export_conditions_001` |
| `pipl_third_party_sharing_without_consent` | 数据合规 | `pipl_third_party_sharing`, `pipl_privacy_policy_sharing`, `pipl_third_party_marketing` | `risk_rule_15` | `risk_privacy_policy_sharing_001`, `risk_third_party_marketing_001` |
| `contract_unfair_standard_terms` | 民商事 | `civil_standard_form_terms` | `risk_rule_16` | `risk_contract_auto_renewal_001` |
| `antitrust_horizontal_price_fixing` | 市场秩序 | `antitrust_monopoly_agreement` | `risk_rule_37` | `risk_antitrust_price_fixing_001` |

本版本只补 registry 条目和已有规则的 `scenario_id` metadata，不合并规则、不删除 trigger、不改变匹配逻辑。`pipl_facial_recognition_attendance` 当前没有成熟 Risk Supplement 规则，因此 `linked_risk_rule_ids` 保持为空，并由 coverage audit 暴露为后续规则治理候选。

`tools/check_scenario_links.py` 支持使用 `--allow-missing-risk-scenario pipl_facial_recognition_attendance` 显式放行该 anchor-only 场景；未列入 allowlist 的缺 Risk Supplement 场景仍会失败。

Scenario targeted eval 结果：

| scenario_id | pass/total | retrieval stages | contribution labels |
|---|---:|---|---|
| `trade_secret_customer_list_leak` | 2/2 | PASS:2 | ANCHOR_PASS:1, RISK_SUPPLEMENT_PASS:2 |
| `pipl_children_consent` | 1/1 | PASS:1 | ANCHOR_PASS:1, RISK_SUPPLEMENT_PASS:1 |
| `pipl_automated_decision_bias` | 2/2 | PASS:2 | ANCHOR_PASS:2, RISK_SUPPLEMENT_PASS:2 |
| `pipl_cross_border_sensitive_medical` | 2/2 | PASS:2 | ANCHOR_PASS:2, RISK_SUPPLEMENT_PASS:2 |
| `vat_false_invoice_deduction` | 1/1 | PASS:1 | ANCHOR_PASS:1, TERM_PRESERVATION_PASS:1, RISK_SUPPLEMENT_PASS:1 |
| `pipl_facial_recognition_attendance` | 1/1 | PASS:1 | ANCHOR_PASS:1 |
| `pipl_data_export_security_assessment` | 3/3 | PASS:3 | ANCHOR_PASS:1, RISK_SUPPLEMENT_PASS:1, PURE_LLM_PASS:1, TERM_PRESERVATION_PASS:1 |
| `pipl_third_party_sharing_without_consent` | 2/2 | PASS:2 | ANCHOR_PASS:2, RISK_SUPPLEMENT_PASS:1 |
| `contract_unfair_standard_terms` | 1/1 | PASS:1 | ANCHOR_PASS:1, RISK_SUPPLEMENT_PASS:1 |
| `antitrust_horizontal_price_fixing` | 1/1 | PASS:1 | ANCHOR_PASS:1, RISK_SUPPLEMENT_PASS:1 |

汇总：10 个 scenario、15 个唯一 eval case 全部通过；`missing_case_ids=0`、`scenarios_without_eval_case_ids=0`、`scenarios_all_failed=0`。Scenario eval gate 默认阈值同步提升为 `min_scenarios=10`、`min_cases=15`。
