# 高置信度人工复核预填草稿 v2（12 条）

这是收窄后的 Codex 辅助填写草稿。v2 删除了部分过宽根因，并将 cross_law_export_assessment_001 调整为范围校准。它仍不是最终法律复核意见；导入审阅台后请人工确认。

边界：未修改 hidden seed、anchor、rerank、prompt、risk supplement、eval case 或 RAG 主流程；未覆盖正式 decision schema。

| case | 建议结论 | 根因 | fixture | 理由摘要 |
| --- | --- | --- | --- | --- |
| `risk_employee_data_export_001` | confirm_diagnostic_issue | primary_evidence_gap, scenario_core_scope, final_evidence_selection_policy, metadata_chunking_or_query_coverage, anchor_dependency_governance, high_risk_grounding_gap | true | 最终证据缺少 2 个预期主要条文；场景核心条文缺少 1 个，可能需要校准案由/场景登记；有 2 个条文曾在候选层出现但未进入最终 evidence_chain。 |
| `pipl_data_export_conditions_001` | confirm_diagnostic_issue | primary_evidence_gap, final_evidence_selection_policy | true | 最终证据缺少 1 个预期主要条文；场景核心条文缺少 1 个，可能需要校准案由/场景登记；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。 |
| `risk_ai_medical_training_export_001` | confirm_diagnostic_issue | primary_evidence_gap, scenario_core_scope, final_evidence_selection_policy, metadata_chunking_or_query_coverage, anchor_dependency_governance, high_risk_grounding_gap, functional_typing_metadata | true | 最终证据缺少 1 个预期主要条文；场景核心条文缺少 1 个，可能需要校准案由/场景登记；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。 |
| `risk_employee_facial_001` | confirm_diagnostic_issue | primary_evidence_gap, scenario_core_scope, final_evidence_selection_policy, metadata_chunking_or_query_coverage, anchor_dependency_governance, high_risk_grounding_gap, functional_typing_metadata | true | 最终证据缺少 1 个预期主要条文；场景核心条文缺少 1 个，可能需要校准案由/场景登记；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。 |
| `risk_app_location_ads_002` | confirm_diagnostic_issue | primary_evidence_gap, final_evidence_selection_policy, metadata_chunking_or_query_coverage, anchor_dependency_governance, high_risk_grounding_gap | true | 最终证据缺少 1 个预期主要条文；有 1 个条文曾在候选层出现但未进入最终 evidence_chain；基础检索层存在缺口，说明不应只依赖 anchor 补救。 |
| `risk_unfair_competition_trade_secret_001` | confirm_diagnostic_issue | scenario_core_scope, high_risk_grounding_gap | false | 场景核心条文缺少 2 个，可能需要校准案由/场景登记；Alignment: One or more primary expected legal issues lack matching evidence；Alignment: Risk outputs include terms or actions not visibly supported by evidence text. |
| `risk_data_export_overseas_001` | confirm_diagnostic_issue | metadata_chunking_or_query_coverage, anchor_dependency_governance, high_risk_grounding_gap | false | 场景核心条文缺少 1 个，可能需要校准案由/场景登记；基础检索层存在缺口，说明不应只依赖 anchor 补救；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。 |
| `risk_privacy_policy_sharing_001` | confirm_diagnostic_issue | metadata_chunking_or_query_coverage, anchor_dependency_governance, high_risk_grounding_gap | false | 场景核心条文缺少 1 个，可能需要校准案由/场景登记；基础检索层存在缺口，说明不应只依赖 anchor 补救；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。 |
| `risk_compliant_case_001` | confirm_diagnostic_issue | primary_evidence_gap, final_evidence_selection_policy, metadata_chunking_or_query_coverage, anchor_dependency_governance | true | 最终证据缺少 1 个预期主要条文；有 1 个条文曾在候选层出现但未进入最终 evidence_chain；基础检索层存在缺口，说明不应只依赖 anchor 补救。 |
| `pipl_principles_001` | confirm_diagnostic_issue | primary_evidence_gap, final_evidence_selection_policy, metadata_chunking_or_query_coverage, anchor_dependency_governance | true | 最终证据缺少 1 个预期主要条文；有 1 个条文曾在候选层出现但未进入最终 evidence_chain；基础检索层存在缺口，说明不应只依赖 anchor 补救。 |
| `cross_law_export_assessment_001` | confirm_scope_adjustment_needed | scenario_core_scope, metadata_chunking_or_query_coverage, anchor_dependency_governance | false | 场景核心条文缺少 2 个，可能需要校准案由/场景登记；基础检索层存在缺口，说明不应只依赖 anchor 补救；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。 |
| `positive_vat_compliance_001` | confirm_diagnostic_issue | primary_evidence_gap, metadata_chunking_or_query_coverage | true | 最终证据缺少 1 个预期主要条文；基础检索层存在缺口，说明不应只依赖 anchor 补救；Alignment: One or more primary expected legal issues lack matching evidence. |
