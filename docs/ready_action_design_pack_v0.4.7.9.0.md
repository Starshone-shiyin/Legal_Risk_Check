# v0.4.7.9.0 Ready Action Design Pack

本文件是 RAG grounding quality governance 的只读设计包，不是样本修补工具，也不是自动实施计划。

## 总览

- 状态：`ready_for_design_review`
- 进入设计包的 ready actions：18
- 来源 promotion candidates：5
- 排除的 pending records：31
- 设计轨道数量：5
- 实施是否允许：False

## 设计轨道

### final_evidence_selection_policy_review

- 数量：5
- 覆盖案例：pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_app_location_ads_002, risk_employee_data_export_001, risk_employee_facial_001
- 设计意图：为已通过人工复核的案例整理最终证据选择策略评审方案，重点关注重要法律依据在进入最终 evidence_chain 前被筛掉的问题。
- 下一步允许：撰写设计说明和测试计划草案，交由后续人工评审。
- 当前禁止：rerank_change, prompt_change, runtime_selection_policy_patch, eval_case_change

### functional_typing_fixture_review

- 数量：1
- 覆盖案例：risk_employee_facial_001
- 设计意图：整理 legal functional typing 的 fixture 复核要求，用于补强条款功能类型的黄金样例质量。
- 下一步允许：准备 typing fixture 复核说明和候选验收检查。
- 当前禁止：functional_type_config_change, golden_fixture_write, eval_case_change, automatic_label_change

### high_risk_manual_grounding_review

- 数量：3
- 覆盖案例：risk_ai_medical_training_export_001, risk_app_location_ads_002, risk_employee_data_export_001
- 设计意图：为已验证的高风险案例准备人工 grounding 复核队列，重点核对风险结论或整改动作是否被证据支撑。
- 下一步允许：准备高风险 grounding 复核队列和逐项复核问题。
- 当前禁止：risk_rule_change, answer_policy_change, prompt_change, automatic_case_closure

### primary_evidence_fixture_candidate_review

- 数量：5
- 覆盖案例：pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_app_location_ads_002, risk_employee_data_export_001, risk_employee_facial_001
- 设计意图：整理主证据缺口对应的 fixture 候选复核要求，但不把候选样本写入 eval case。
- 下一步允许：准备 fixture 候选复核说明和候选进入标准。
- 当前禁止：fixture_write_to_eval, eval_case_change, knowledge_base_mutation, automatic_fixture_promotion

### scenario_registry_core_article_review

- 数量：4
- 覆盖案例：pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_employee_data_export_001, risk_employee_facial_001
- 设计意图：从已验证案例中整理 scenario registry 核心条文范围的复核问题，但不修改 registry 或 expected evidence。
- 下一步允许：准备 scenario core 条文复核清单，等待人工批准。
- 当前禁止：scenario_registry_change, expected_evidence_change, anchor_change, eval_case_change

## 边界

- 只读取既有 promotion dry-run 与 export pipeline dry-run 报告。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case 或主流程。
- 31 个 pending records 只作为背景统计，不进入工程设计任务。
- 后续若要实施任何代码或配置变更，需要另开版本、另做审议和测试计划。

## 来源

- Promotion dry-run：`tests\validated_decision_promotion_dry_run_report.json`
- Export pipeline dry-run：`tests\manual_review_export_pipeline_dry_run_report.json`
