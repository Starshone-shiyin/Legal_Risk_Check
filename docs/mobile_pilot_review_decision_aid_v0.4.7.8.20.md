# v0.4.7.8.20 Mobile Pilot Review Decision Aid

## 定位

这是手机端确认前草稿，用来减少远程操作时的阅读负担。它不是人工复核结论，不会写入可导入字段，也不能直接进入 dry-run。

## 摘要

- 手机卡片：5
- 需要用户确认：5
- Completed manual decisions：0
- Promotion candidates：0
- Ready action candidates：0
- Gate status：`blocked_until_real_human_review_export_passes_dry_run`

## 手机复核卡片

### 1. risk_employee_data_export_001

- 案由：案由线索是“公司对内部人员行为负有管理责任，需证明已采取合理保护措施”。需要复核的问题是：某公司员工私自将100万条客户名单（包含联系方式）导出并出售给竞争对手，公司应承担什么风险？
- 原回答：风险包括 个人信息泄露风险、行政处罚风险、民事赔偿风险、刑事责任风险、内部人员违规、数据泄露、管理失职
- 证据状态：较可能存在证据支撑缺口，需要人工确认
- 关键缺口：[《中华人民共和国个人信息保护法》第六十六条]
- 建议倾向：建议优先考虑：确认诊断成立
- 建议根因：functional_typing_metadata, final_evidence_selection_policy, primary_evidence_gap
- 建议动作：functional_typing_fixture_review, final_evidence_selection_policy_review, primary_evidence_fixture_candidate_review
- 你只需确认：案由和原 LLM 输出是否在讨论同一个法律问题？
- 确认前草稿：`confirm_diagnostic_issue`
- 建议理由：当前支持包显示主争点或关键证据存在缺口。该建议仅用于减少手机端阅读负担，不能替代你的人工确认；如你不同意，应在网页工作台中选择其他结论。
- 边界：这不是人工复核结论；你可以同意、修改或驳回。

### 4. pipl_data_export_conditions_001

- 案由：案由线索是“可跨法律召回，至少命中中华人民共和国个人信息保护法第38条或个人信息出境标准合同办法第五条”。需要复核的问题是：个人信息出境需要具备哪些条件？
- 原回答：风险包括 个人信息出境合规风险、安全评估申报义务风险
- 证据状态：较可能存在证据支撑缺口，需要人工确认
- 关键缺口：[《个人信息出境标准合同办法》第五条]
- 建议倾向：建议优先考虑：确认诊断成立
- 建议根因：functional_typing_metadata, final_evidence_selection_policy, primary_evidence_gap
- 建议动作：functional_typing_fixture_review, final_evidence_selection_policy_review, primary_evidence_fixture_candidate_review
- 你只需确认：案由和原 LLM 输出是否在讨论同一个法律问题？
- 确认前草稿：`confirm_diagnostic_issue`
- 建议理由：当前支持包显示主争点或关键证据存在缺口。该建议仅用于减少手机端阅读负担，不能替代你的人工确认；如你不同意，应在网页工作台中选择其他结论。
- 边界：这不是人工复核结论；你可以同意、修改或驳回。

### 2. risk_ai_medical_training_export_001

- 案由：案由线索是“复合风险：敏感个人信息 + 数据出境”。需要复核的问题是：某AI医疗公司使用包含患者病历的数据训练模型，并将训练数据同步至境外服务器进行计算，已取得用户一般同意但未单独告知出境，是否合规？
- 原回答：风险包括 敏感个人信息处理风险、个人信息出境风险、超出授权范围使用、超出原授权范围使用
- 证据状态：较可能存在证据支撑缺口，需要人工确认
- 关键缺口：[《中华人民共和国个人信息保护法》第三十九条]
- 建议倾向：建议优先考虑：确认诊断成立
- 建议根因：functional_typing_metadata, final_evidence_selection_policy, primary_evidence_gap
- 建议动作：functional_typing_fixture_review, final_evidence_selection_policy_review, primary_evidence_fixture_candidate_review
- 你只需确认：案由和原 LLM 输出是否在讨论同一个法律问题？
- 确认前草稿：`confirm_diagnostic_issue`
- 建议理由：当前支持包显示主争点或关键证据存在缺口。该建议仅用于减少手机端阅读负担，不能替代你的人工确认；如你不同意，应在网页工作台中选择其他结论。
- 边界：这不是人工复核结论；你可以同意、修改或驳回。

### 3. risk_employee_facial_001

- 案由：案由线索是“人脸属于敏感信息，必须单独告知并获取同意”。需要复核的问题是：某公司在员工入口处安装人脸识别考勤机，未告知员工人脸信息用途和存储期限，是否存在法律风险？
- 原回答：风险包括 敏感个人信息处理风险、未履行告知义务风险、未取得单独同意风险
- 证据状态：较可能存在证据支撑缺口，需要人工确认
- 关键缺口：[《中华人民共和国个人信息保护法》第三十条]
- 建议倾向：建议优先考虑：确认诊断成立
- 建议根因：functional_typing_metadata, final_evidence_selection_policy, primary_evidence_gap
- 建议动作：functional_typing_fixture_review, final_evidence_selection_policy_review, primary_evidence_fixture_candidate_review
- 你只需确认：案由和原 LLM 输出是否在讨论同一个法律问题？
- 确认前草稿：`confirm_diagnostic_issue`
- 建议理由：当前支持包显示主争点或关键证据存在缺口。该建议仅用于减少手机端阅读负担，不能替代你的人工确认；如你不同意，应在网页工作台中选择其他结论。
- 边界：这不是人工复核结论；你可以同意、修改或驳回。

### 5. risk_app_location_ads_002

- 案由：案由线索是“高风险场景：精准位置属于敏感信息，未告知且用于广告，违反个保法第13、17、28、29条”。需要复核的问题是：某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？
- 原回答：风险包括 敏感个人信息处理风险、告知义务缺失风险、单独同意缺失风险、目的变更未重新告知风险、未履行告知义务、敏感个人信息违规处理
- 证据状态：较可能存在证据支撑缺口，需要人工确认
- 关键缺口：[《中华人民共和国个人信息保护法》第十三条]
- 建议倾向：建议优先考虑：确认诊断成立
- 建议根因：functional_typing_metadata, final_evidence_selection_policy, primary_evidence_gap
- 建议动作：functional_typing_fixture_review, final_evidence_selection_policy_review, primary_evidence_fixture_candidate_review
- 你只需确认：案由和原 LLM 输出是否在讨论同一个法律问题？
- 确认前草稿：`confirm_diagnostic_issue`
- 建议理由：当前支持包显示主争点或关键证据存在缺口。该建议仅用于减少手机端阅读负担，不能替代你的人工确认；如你不同意，应在网页工作台中选择其他结论。
- 边界：这不是人工复核结论；你可以同意、修改或驳回。

## 边界

- 本报告不写 `reviewer_input_template`。
- 本报告不生成 `reviewer_decision` 或 completed manual decision。
- 本报告不生成 promotion candidate 或 ready action candidate。
- 本报告不接入 `rag_query`、后端 API、Qdrant 或 LLM。
- 本报告不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- 真正结论必须由用户在 visual workbench 中确认或修改。
