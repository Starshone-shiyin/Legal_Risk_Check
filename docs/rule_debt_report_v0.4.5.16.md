# v0.4.5.16 规则债盘点报告

范围：只扫描并输出报告，不合并规则，不修改 `src/rag/retriever.py`。

## 摘要

- Anchor rules：`75`
- Risk supplement rules：`39`
- 重复 trigger：`111`
- 跨配置 trigger 重叠：`94`
- 疑似同场景多处维护：`43`
- Anchor 缺共享 scenario_id：`75`
- Risk 缺 scenario_id：`39`
- 高规则依赖 case：`25`

## 重复 Trigger Top 30

| trigger | count | kinds | rules |
|---|---:|---|---|
| 客户名单 | 5 | anchor, risk | anchor:pipl_data_leak, anchor:pipl_internal_leak, anchor:unfair_competition_trade_secret, risk:risk_rule_0, risk:risk_rule_4 |
| 第三方 | 5 | anchor, risk | anchor:civil_data_processing_liability, anchor:pipl_privacy_policy_sharing, anchor:pipl_third_party_marketing, anchor:pipl_third_party_sharing, risk:risk_rule_15 |
| 泄露 | 4 | anchor, risk | anchor:civil_data_processing_liability, anchor:pipl_security_incident, anchor:state_secrets_leak, risk:risk_rule_5 |
| ai算法 | 3 | anchor, risk | anchor:pipl_automated_decision, anchor:pipl_automated_decision_full, risk:risk_rule_6 |
| 价格歧视 | 3 | anchor, risk | anchor:pipl_automated_decision, anchor:pipl_automated_decision_full, risk:risk_rule_6 |
| 关联交易 | 3 | anchor, risk | anchor:corp_director_duty, risk:risk_rule_28, risk:risk_rule_29 |
| 出售给竞争对手 | 3 | anchor, risk | anchor:pipl_data_leak, anchor:pipl_internal_leak, risk:risk_rule_4 |
| 出境 | 3 | anchor, risk | anchor:pipl_data_export, anchor:pipl_sensitive_export, risk:risk_rule_9 |
| 员工私自 | 3 | anchor, risk | anchor:pipl_data_leak, anchor:pipl_internal_leak, risk:risk_rule_4 |
| 境外 | 3 | anchor, risk | anchor:pipl_data_export, anchor:pipl_sensitive_export, risk:risk_rule_9 |
| 境外服务器 | 3 | anchor, risk | anchor:pipl_data_export, anchor:pipl_sensitive_export, risk:risk_rule_9 |
| 客服聊天记录 | 3 | anchor, risk | anchor:pipl_ai_training, anchor:pipl_ai_training_purpose_change, risk:risk_rule_2 |
| 导出 | 3 | anchor, risk | anchor:pipl_data_leak, anchor:pipl_internal_leak, risk:risk_rule_4 |
| 差异化定价 | 3 | anchor, risk | anchor:pipl_automated_decision, anchor:pipl_automated_decision_full, risk:risk_rule_6 |
| 未申报 | 3 | anchor, risk | anchor:antitrust_concentration, anchor:vat_non_filing, risk:risk_rule_35 |
| 未经许可 | 3 | anchor, risk | anchor:trademark_infringement, risk:risk_rule_19, risk:risk_rule_22 |
| 用户行为数据 | 3 | anchor | anchor:pipl_ai_training, anchor:pipl_ai_training_purpose_change, anchor:pipl_anonymized_training |
| 病历 | 3 | anchor, risk | anchor:pipl_sensitive_export, anchor:pipl_sensitive_info, risk:risk_rule_9 |
| 税率 | 3 | anchor, risk | anchor:vat_tax_rate, anchor:vat_taxpayer_rate, risk:risk_rule_11 |
| 筛选简历 | 3 | anchor, risk | anchor:pipl_automated_decision, anchor:pipl_automated_decision_full, risk:risk_rule_6 |
| 算法歧视 | 3 | anchor, risk | anchor:pipl_automated_decision, anchor:pipl_automated_decision_full, risk:risk_rule_6 |
| 职务发明 | 3 | anchor, risk | anchor:patent_employee_invention, risk:risk_rule_23, risk:risk_rule_24 |
| 职务行为 | 3 | anchor, risk | anchor:patent_employee_invention, risk:risk_rule_23, risk:risk_rule_24 |
| 自动化决策 | 3 | anchor, risk | anchor:pipl_automated_decision, anchor:pipl_automated_decision_full, risk:risk_rule_6 |
| 营销公司 | 3 | anchor, risk | anchor:pipl_third_party_marketing, anchor:pipl_third_party_sharing, risk:risk_rule_15 |
| 董事 | 3 | anchor, risk | anchor:corp_director_duty, risk:risk_rule_28, risk:risk_rule_29 |
| 虚开发票 | 3 | anchor, risk | anchor:vat_invoice, risk:risk_rule_33, risk:risk_rule_34 |
| 训练ai | 3 | anchor, risk | anchor:pipl_ai_training, anchor:pipl_ai_training_purpose_change, risk:risk_rule_2 |
| 训练模型 | 3 | anchor, risk | anchor:pipl_ai_training, anchor:pipl_ai_training_purpose_change, risk:risk_rule_2 |
| 跨境 | 3 | anchor, risk | anchor:pipl_data_export, anchor:pipl_sensitive_export, risk:risk_rule_9 |

## 跨配置 Trigger 重叠 Top 30

| trigger | anchor rules | risk rules |
|---|---|---|
| 客户名单 | pipl_data_leak, pipl_internal_leak, unfair_competition_trade_secret | risk_rule_0, risk_rule_4 |
| 第三方 | civil_data_processing_liability, pipl_privacy_policy_sharing, pipl_third_party_marketing, pipl_third_party_sharing | risk_rule_15 |
| 泄露 | civil_data_processing_liability, pipl_security_incident, state_secrets_leak | risk_rule_5 |
| ai算法 | pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 |
| 价格歧视 | pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 |
| 关联交易 | corp_director_duty | risk_rule_28, risk_rule_29 |
| 出售给竞争对手 | pipl_data_leak, pipl_internal_leak | risk_rule_4 |
| 出境 | pipl_data_export, pipl_sensitive_export | risk_rule_9 |
| 员工私自 | pipl_data_leak, pipl_internal_leak | risk_rule_4 |
| 境外 | pipl_data_export, pipl_sensitive_export | risk_rule_9 |
| 境外服务器 | pipl_data_export, pipl_sensitive_export | risk_rule_9 |
| 客服聊天记录 | pipl_ai_training, pipl_ai_training_purpose_change | risk_rule_2 |
| 导出 | pipl_data_leak, pipl_internal_leak | risk_rule_4 |
| 差异化定价 | pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 |
| 未申报 | antitrust_concentration, vat_non_filing | risk_rule_35 |
| 未经许可 | trademark_infringement | risk_rule_19, risk_rule_22 |
| 病历 | pipl_sensitive_export, pipl_sensitive_info | risk_rule_9 |
| 税率 | vat_tax_rate, vat_taxpayer_rate | risk_rule_11 |
| 筛选简历 | pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 |
| 算法歧视 | pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 |
| 职务发明 | patent_employee_invention | risk_rule_23, risk_rule_24 |
| 职务行为 | patent_employee_invention | risk_rule_23, risk_rule_24 |
| 自动化决策 | pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 |
| 营销公司 | pipl_third_party_marketing, pipl_third_party_sharing | risk_rule_15 |
| 董事 | corp_director_duty | risk_rule_28, risk_rule_29 |
| 虚开发票 | vat_invoice | risk_rule_33, risk_rule_34 |
| 训练ai | pipl_ai_training, pipl_ai_training_purpose_change | risk_rule_2 |
| 训练模型 | pipl_ai_training, pipl_ai_training_purpose_change | risk_rule_2 |
| 跨境 | pipl_data_export, pipl_sensitive_export | risk_rule_9 |
| 高度相似 | trademark_infringement, unfair_competition_confusion | risk_rule_19 |

## 疑似同场景多处维护 Top 30

| anchor | risk rule | shared triggers | shared effects | score |
|---|---|---|---|---:|
| pipl_automated_decision_full | risk_rule_6 | ai算法, 价格歧视, 差异化定价, 筛选简历, 算法歧视, 自动化决策 | 优化算法规则并开展公平性审计, 算法歧视, 自动化决策不当 | 15 |
| pipl_automated_decision | risk_rule_6 | ai算法, 价格歧视, 差异化定价, 筛选简历, 算法歧视, 自动化决策 |  | 12 |
| pipl_data_leak | risk_rule_4 | 出售给竞争对手, 员工私自, 客户名单, 导出 | 内部人员违规, 完善访问权限、日志审计、异常导出拦截等管理和技术措施, 数据泄露, 管理失职 | 12 |
| pipl_internal_leak | risk_rule_4 | 出售给竞争对手, 员工私自, 客户名单, 导出 | 内部人员违规, 数据泄露, 管理失职 | 11 |
| antitrust_independent_pricing | risk_rule_38 | 未与竞争对手协商, 根据自身成本, 独立制定产品价格, 独立定价, 自主定价 |  | 10 |
| civil_data_processing_liability | risk_rule_14 | 数据处理协议, 未约定数据泄露, 未约定责任, 责任分配 | 合同责任不明确, 明确数据泄露责任分配 | 10 |
| pipl_sensitive_export | risk_rule_9 | 出境, 境外, 境外服务器, 病历, 跨境 |  | 10 |
| vat_tax_rate | risk_rule_11 | 13%, 9%, 低税率, 税率 | 更正发票, 补缴税款及滞纳金 | 10 |
| vat_mixed_sales | risk_rule_13 | 分别核算, 未区分收入, 混合销售 | 分别核算不同业务收入, 正确适用税率, 混合销售核算风险 | 9 |
| antitrust_monopoly_agreement | risk_rule_37 | 固定价格, 统一价格, 统一提高产品价格, 联合涨价 |  | 8 |
| civil_property_rights | risk_rule_7 | 业主共有, 公共区域, 共有部分, 物业 |  | 8 |
| pipl_data_export | risk_rule_9 | 出境, 境外, 境外服务器, 跨境 |  | 8 |
| pipl_security_incident | risk_rule_5 | 安全事件, 服务器被攻击, 泄露 | 安全事件处置不当, 未履行通知义务 | 8 |
| vat_export_refund | risk_rule_12 | 出口退税, 虚报出口, 虚报出口金额 | 停止违规申报, 退还多获取税款 | 8 |
| corp_director_duty | risk_rule_28 | 关联交易, 未经批准, 董事 | 完善关联交易审批 | 7 |
| patent_employee_invention | risk_rule_23 | 履行职务, 职务发明, 职务行为 | 明确职务发明制度 | 7 |
| civil_product_liability | risk_rule_18 | 产品责任, 消费者受伤, 缺陷产品 |  | 6 |
| civil_standard_form_terms | risk_rule_16 | 格式条款, 自动续费 | 显著提醒用户, 格式条款合规风险 | 6 |
| corp_information_disclosure | risk_rule_8 | 股东, 财务报表 | 依法提供资料, 股东知情权侵害 | 6 |
| pipl_ai_training | risk_rule_2 | 客服聊天记录, 训练ai, 训练模型 |  | 6 |
| pipl_ai_training_purpose_change | risk_rule_2 | 客服聊天记录, 训练ai, 训练模型 |  | 6 |
| pipl_third_party_marketing | risk_rule_15 | 手机号, 第三方, 营销公司 |  | 6 |
| vat_input_deduction | risk_rule_36 | 抵扣, 进项税额 | 区分可抵扣与不可抵扣项目, 规范费用报销类型 | 6 |
| vat_invoice | risk_rule_33 | 虚开发票 | 停止违规抵扣, 建立发票合规审核机制, 虚开发票风险, 补缴税款及滞纳金 | 6 |
| corp_capital_contribution | risk_rule_26 | 出资, 认缴 | 追究违约责任 | 5 |
| corp_director_duty | risk_rule_29 | 关联交易, 董事 | 完善关联交易审批 | 5 |
| patent_employee_invention | risk_rule_24 | 职务发明, 职务行为 | 明确职务发明制度 | 5 |
| unfair_competition_false_ad | risk_rule_1 | 虚假宣传, 虚构产品功能 | 停止虚假宣传 | 5 |
| unfair_competition_trade_secret | risk_rule_0 | 商业秘密, 客户名单 | 停止使用相关信息 | 5 |
| vat_non_filing | risk_rule_35 | 未开具发票, 未申报 | 补申报纳税 | 5 |

## 缺失 Scenario ID

说明：Anchor 规则已有 `id`，但缺少可与风险补全配置共享的 `scenario_id`；Risk 规则目前多数只能通过 index 或触发词定位。

- Anchor 缺共享 scenario_id：`75`
- Risk 缺 scenario_id：`39`

## 高规则依赖 Case 映射

口径：稳定性报告中同时带有 `ANCHOR_PASS` 与 `RISK_SUPPLEMENT_PASS` 的 case。

| case | runs | matched anchors | matched risk rules | question |
|---|---:|---|---|---|
| positive_antitrust_independent_pricing_001 | 1, 2, 3 | antitrust_independent_pricing | risk_rule_38, risk_rule_37 | 企业根据自身成本和市场情况独立制定产品价格，未与竞争对手协商，是否合法？ |
| risk_ai_medical_training_export_001 | 1, 2, 3 | pipl_sensitive_export, pipl_data_export, pipl_ai_training, pipl_ai_training_purpose_change, pipl_anonymized_training, pipl_sensitive_info | risk_rule_9, risk_rule_2 | 某AI医疗公司使用包含患者病历的数据训练模型，并将训练数据同步至境外服务器进行计算，已取得用户一般同意但未单独告知出境，是否合规？ |
| risk_algorithm_bias_001 | 1, 2, 3 | pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 | 某招聘平台使用AI算法筛选简历，系统对特定地区求职者给出明显更低的评分，是否涉及算法歧视风险？ |
| risk_antitrust_price_fixing_001 | 1, 2, 3 | antitrust_monopoly_agreement, antitrust_independent_pricing | risk_rule_37 | 多家同行企业通过行业会议约定统一提高产品价格，该行为是否合法？ |
| risk_app_location_ads_002 | 1, 2, 3 | pipl_location_ads, pipl_standard_minimum | risk_rule_1 | 某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？ |
| risk_chatbot_training_001 | 1, 2, 3 | pipl_ai_training, pipl_ai_training_purpose_change, pipl_anonymized_training, pipl_third_party_marketing | risk_rule_2, risk_rule_15 | 某公司用客服聊天记录（包含用户姓名、手机号、咨询内容）训练AI客服模型，未获得用户明确同意，是否违规？ |
| risk_children_data_001 | 1, 2, 3 | pipl_children, civil_data_processing_liability, pipl_location_ads, pipl_standard_minimum | risk_rule_3 | 某儿童游戏APP收集儿童（8-12岁）的位置、设备信息，仅用普通用户协议征得家长同意，是否合规？ |
| risk_company_information_disclosure_001 | 1, 2, 3 | corp_information_disclosure, pipl_third_party_marketing | risk_rule_8 | 公司拒绝向股东提供财务报表等资料，是否合法？ |
| risk_company_related_transaction_001 | 1, 2, 3 | corp_director_duty | risk_rule_28, risk_rule_29 | 公司董事未经批准与公司进行交易并从中获利，该行为是否合法？ |
| risk_compliant_case_001 | 1, 2, 3 | pipl_location_ads, pipl_standard_minimum |  | 某APP明确告知用户收集位置信息用于导航服务，并取得单独同意，且用户可随时关闭定位权限，该行为是否合规？ |
| risk_contract_auto_renewal_001 | 1, 2, 3 | civil_data_processing_liability, civil_standard_form_terms | risk_rule_16, risk_rule_37 | 某视频平台在会员协议中约定自动续费，但未在扣费前以显著方式提醒用户，该条款是否有效？ |
| risk_data_breach_notification_001 | 1, 2, 3 | pipl_security_incident, civil_data_processing_liability, state_secrets_leak | risk_rule_5 | 某公司服务器被攻击，100万条用户个人信息泄露，公司未及时通知用户，是否存在违规风险？ |
| risk_data_export_overseas_001 | 1, 2, 3 | pipl_data_export, pipl_sensitive_export, antitrust_concentration, pipl_data_export_assessment, vat_non_filing | risk_rule_9, risk_rule_35 | 某跨境电商平台处理超过100万用户个人信息，并将用户订单数据（包含姓名、电话、地址）传输给境外云服务商用于订单处理，未申报数据出境安全评估，是否合规？ |
| risk_data_leak_contract_001 | 1, 2, 3 | civil_data_processing_liability, pipl_privacy_policy_sharing, pipl_security_incident, pipl_third_party_marketing, pipl_third_party_sharing, state_secrets_leak | risk_rule_14, risk_rule_15, risk_rule_37, risk_rule_5 | 某企业与第三方签订数据处理协议，但未约定数据泄露责任分配，发生泄露后责任如何认定？ |
| risk_employee_data_export_001 | 1, 2, 3 | pipl_data_leak, pipl_internal_leak, antitrust_independent_pricing, unfair_competition_trade_secret | risk_rule_4, risk_rule_0, risk_rule_37 | 某公司员工私自将100万条客户名单（包含联系方式）导出并出售给竞争对手，公司应承担什么风险？ |
| risk_gray_area_ai_training_001 | 1, 2, 3 | pipl_anonymized_training, pipl_ai_training, pipl_ai_training_purpose_change, pipl_location_ads | risk_rule_10 | 某公司使用已匿名化的用户行为数据训练推荐算法，但未明确说明是否可被重新识别，该行为是否存在风险？ |
| risk_labor_dispatch_001 | 1, 2, 3 | civil_labor_dispatch | risk_rule_17 | 某公司长期通过劳务派遣形式使用员工从事核心岗位工作，该做法是否合法？ |
| risk_patent_invalid_001 | 1, 2, 3 | patent_invalid | risk_rule_22, risk_rule_25 | 某企业申请的专利技术在申请日前已被公开，该专利是否存在被宣告无效的风险？ |
| risk_property_management_001 | 1, 2, 3 | civil_property_rights, pipl_location_ads | risk_rule_7, risk_rule_1 | 物业公司未经业主同意，将小区公共区域出租用于广告经营，是否合法？ |
| risk_third_party_marketing_001 | 1, 2, 3 | pipl_third_party_marketing, pipl_third_party_sharing, pipl_privacy_policy_sharing | risk_rule_15 | 某公司将用户手机号（未脱敏）提供给营销公司用于电话推销，未获得用户明示同意，是否违法？ |
| risk_trademark_infringement_001 | 1, 2, 3 | trademark_infringement, civil_tort_general, trademark_well_known, unfair_competition_confusion | risk_rule_19, risk_rule_20 | 某企业在未获得授权的情况下，在其产品包装上使用与知名品牌高度相似的商标标识，是否构成侵权？ |
| risk_user_profile_overuse_001 | 1, 2, 3 | antitrust_independent_pricing, pipl_automated_decision, pipl_automated_decision_full | risk_rule_6 | 某电商平台基于用户浏览记录分析消费能力，并将该结果用于差异化定价（价格歧视），是否存在法律风险？ |
| risk_vat_export_refund_001 | 1, 2, 3 | vat_export_refund | risk_rule_12 | 企业在出口退税中虚报出口金额以获取更多退税，是否合法？ |
| risk_vat_false_invoice_001 | 1, 2, 3 | vat_invoice, vat_input_deduction, vat_taxpayer_rate | risk_rule_36, risk_rule_33, risk_rule_34 | 某企业通过虚开发票抵扣增值税进项税额，该行为是否合法？ |
| risk_vat_mixed_sales_001 | 1, 2, 3 | vat_tax_rate, pipl_third_party_marketing, vat_mixed_sales, vat_taxpayer, vat_taxpayer_rate | risk_rule_11, risk_rule_13, risk_rule_35 | 企业同时销售货物并提供安装服务，但未区分收入统一按低税率纳税，是否存在风险？ |
