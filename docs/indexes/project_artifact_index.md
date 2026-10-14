# 项目产物索引
## v0.5.2 Controlled Experiment addendum

- `docs/core_tech_experiment_results_20260815.md`、`docs/core_tech_judge_packet_20260815.md`：C0-C6 受控消融、改写鲁棒性、ESG 和端到端抽样的可声明结论与边界。
- `tests/rag_controlled_ablation_20260815_raw.json`、`tests/rag_controlled_ablation_20260815_recomputed.json`、`tests/rag_controlled_ablation_20260815_judge.json`、`tests/rag_controlled_ablation_20260815_esg_judge.json`：C0-C6 受控消融的原始运行、指标重算与内部裁判材料。
- `tests/rag_robustness_cases_20260815.json`、`tests/rag_robustness_20260815_raw.json`、`tests/rag_robustness_20260815_recomputed.json`：改写鲁棒性题集、原始运行与重算材料。
- `tests/rag_robustness_perturbation_cases_20260815.json`、`tests/rag_robustness_perturbation_20260815_raw.json`、`tests/rag_robustness_perturbation_20260815_recomputed.json`、`tests/rag_robustness_perturbation_20260815_esg_judge.json`、`tests/rag_robustness_perturbation_20260815_summary.json`：扰动鲁棒性题集、原始运行、重算、ESG 裁判与摘要材料。
- `tests/rag_end_to_end_sample_20260815.json`：端到端抽样材料；仅用于检查流程表现，不表示法律结论正确率。
- `tests/core_tech_experiment_final_judge_20260815.json`：实验材料完整性与内部一致性裁判，不代表法律结论正确率。
- `reports/core_tech_20260815/`：控制消融、时延和改写鲁棒性科研图表；图表尺寸、色彩模式和 DPI 已由裁判记录核验。

## Core Technology and Skill acceptance addendum

- 自定义 Skill 使用与高级扩展手册：`docs/skill_customization_guide.md`。说明内置模板、固定节点编排、运行边界，以及受控服务端插件的第三层扩展方向。

- 民法典与复杂案例评测：`tests/civil_code_corpus_integrity_report.json`、`tests/civil_code_coverage_judge_report.json`、`tests/civil_code_eval_cases.json`、`tests/civil_code_eval_report.json`、`tests/civil_code_multi_issue_eval_report.json`、`tests/complex_case_eval_cases.json`、`tests/complex_case_eval_report.json`。
- 法规语料和 staging 诊断：`tests/legal_corpus_integrity_after_expansion.json`、`tests/legal_staging_collection_dry_run.json`、`tests/legal_staging_collection_report.json`。
- 检索消融原始、复现和裁判工件：`tests/rag_ablation_report.json`、`tests/rag_ablation_report_no_proxy.json`、`tests/rag_ablation_current_run.json`、`tests/rag_ablation_current_recomputed_report.json`、`tests/rag_ablation_current_judge_report.json`、`tests/rag_ablation_current_esg_judge_report.json`、`tests/rag_ablation_current_recomputed_judge_report.json`、`tests/rag_ablation_current_recomputed_esg_judge_report.json`、`tests/rag_ablation_judge_report.json`、`tests/rag_ablation_judge_report_20260810.json`、`tests/rag_ablation_no_proxy_judge_report.json`、`tests/rag_smoke_after_ablation.json`。
- ESG 实验和裁判工件：`tests/rag_esg_m4_report.json`、`tests/rag_esg_m4_judge_report.json`、`tests/rag_esg_smoke_cases.json`、`tests/rag_esg_smoke_report.json`、`tests/rag_esg_smoke_judge_report.json`。
- 复现图表质量报告：`tests/core_tech_reproduced_figure_quality_report.json`。
- 自定义 Skill 实现证据与裁判：`tests/skill_api_acceptance_evidence.json`、`tests/skill_runtime_acceptance_evidence.json`、`tests/skill_module_judge_report.json`。这些文件仅记录固定节点、服务边界与离线验证，不含模型、Qdrant 或联网调用结果。

## v0.4.18.9 Product Backend Closeout addendum

- `docs/product_backend_closeout_v0.4.18.9.md`：product backend 收口 runbook 和前端/真实 provider 交接说明。
- `tests/product_backend_closeout_v0.4.18.9_report.json`：product backend closeout 交接报告。

## v0.4.18.8 Product Data Source Boundary addendum

- `docs/product_data_source_boundary_v0.4.18.8.md`：product backend 数据源/repository 边界说明文档。
- `tests/product_data_source_boundary_v0.4.18.8.json`：fixture-backed product API 数据源边界目录。

## v0.4.18.7 Product API Status Catalog addendum

- `docs/product_api_status_catalog_v0.4.18.7.md`：product API 状态与错误目录说明文档。
- `tests/product_api_status_catalog_v0.4.18.7.json`：fixture-backed product API 状态与错误目录。

## v0.4.18.6 Product API Field Catalog addendum

- `docs/product_api_field_catalog_v0.4.18.6.md`：product API 字段目录说明文档。
- `tests/product_api_field_catalog_v0.4.18.6.json`：fixture-backed `/product/*` 接口字段目录。

## v0.4.18.5 Product API Backend Integration addendum

- `docs/product_api_backend_integration_v0.4.18.5.md`：fixture-backed product API 后端接入说明文档。
- `tests/product_api_contract_v0.4.18.5_report.json`：product API contract 校验报告，当前 `status=passed`。

## v0.4.18.4 Product Mock Endpoint Contract addendum

- `docs/product_mock_endpoint_contract_v0.4.18.4.md`：产品 mock endpoint contract 说明文档。
- `tests/product_mock_endpoint_contract_v0.4.18.4_report.json`：product mock endpoint contract 校验报告，当前 `status=passed`。

## v0.4.18.3 Product View Model Contract addendum

- `docs/product_view_model_contract_v0.4.18.3.md`：产品 view model contract 说明文档。
- `tests/fixtures/product_view_models_v0.4.18.3.json`：dashboard、legal workspace、market signals、supply-chain map 和 lifecycle risk 的离线 view model fixture。
- `tests/product_view_model_contract_v0.4.18.3_report.json`：product view model contract 校验报告，当前 `status=passed`。

## v0.4.18.2 Product Design Brief addendum

- `docs/product_design_brief_v0.4.18.2.md`：面向设计专员的产品设计简报和 UI handoff brief。

## v0.4.18.1 Legal Corpus Integrity Baseline addendum

- `docs/legal_corpus_integrity_baseline_v0.4.18.1.md`：法规扩容前的本地 corpus integrity 基线说明。
- `tests/legal_corpus_integrity_v0.4.18.1_report.json`：只读 manifest 与本地文本的 corpus integrity 报告，当前 `status=passed`，`generated_documents=7177`。

## v0.4.17.7 RAG Full Eval Closeout addendum

- `docs/rag_full_eval_closeout_v0.4.17.7.md`：RAG evidence independence 系列 full eval 收口说明。
- `tests/rag_eval_report_v0.4.17.7.json`：v0.4.17.6 后的当前 RAG 主链路 full eval 报告，结果为 `59/60` passed，retrieval `PASS=60`。

## v0.4.17.6 Unfair Competition Confusion Metadata Patch addendum

- `docs/unfair_competition_confusion_metadata_patch_v0.4.17.6.md`：反不正当竞争混淆 case 元数据旧编号修正文档。
- `tests/rag_expected_level_review_packet_v0.4.17.6_report.json`：元数据修正后的 expected-level review packet。
- `tests/legal_text_version_verification_packet_v0.4.17.6_report.json`：元数据修正后的法律文本版本核验报告。

## v0.4.17.5 Legal Text Version Verification addendum

- `docs/legal_text_version_verification_packet_v0.4.17.5.md`：法律文本版本核验说明文档。
- `tests/legal_text_version_snapshot_v0.4.17.5.json`：法律文本版本快照。
- `tools/build_legal_text_version_verification_packet.py`：法律文本版本核验工具。
- `tests/test_legal_text_version_verification_packet.py`：法律文本版本核验单测。
- `tests/legal_text_version_verification_packet_v0.4.17.5_report.json`：现行法第七条/旧法第六条编号漂移核验报告。

## v0.4.17.4 RAG Expected-Level Review Packet addendum

- `docs/rag_expected_level_review_packet_v0.4.17.4.md`：expected-level review packet 说明文档。
- `tools/build_rag_expected_level_review_packet.py`：固定失败分类工具。
- `tests/test_rag_expected_level_review_packet.py`：固定失败分类单测。
- `tests/rag_expected_level_review_packet_v0.4.17.4_report.json`：`risk_unfair_competition_confusion_001` 的 expected-level/fact-strength 复核包。

## v0.4.17.3 RAG Targeted Repeat Closeout addendum

- `docs/rag_targeted_repeat_closeout_v0.4.17.3.md`：17 个 case targeted repeat 实跑收口文档。
- `tests/targeted_rag_evidence_independence_v0.4.17.3_report.json`：v0.4.17.2 packet 的 3 轮 targeted repeat 报告。

## v0.4.17.2 RAG Targeted Rerun Packet addendum

- `docs/rag_targeted_rerun_packet_v0.4.17.2.md`：targeted rerun packet 说明文档。
- `tools/build_rag_targeted_rerun_packet.py`：saved-report-only 候选包生成工具。
- `tests/test_rag_targeted_rerun_packet.py`：候选包单测。
- `tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`：17 个 case 的 bounded targeted repeat 候选包。

## v0.4.17.1 RAG Evidence Independence Baseline addendum

- `docs/rag_evidence_independence_baseline_v0.4.17.1.md`：RAG evidence independence 基线说明文档。
- `tools/build_rag_evidence_independence_baseline.py`：saved-report-only 依赖归因工具。
- `tests/test_rag_evidence_independence_baseline.py`：依赖归因单测。
- `tests/rag_evidence_independence_baseline_v0.4.17.1_report.json`：主链路依赖归因基线报告，属于 RAG 质量诊断资产。

## v0.4.16.12 API Contract Stability Closeout addendum

- `docs/api_contract_stability_closeout_v0.4.16.12.md`：v0.4.16.x API contract stability 系列收口与离线 handoff runbook 文档。

## v0.4.16.11 API Contract Consistency Checker addendum

- `docs/api_contract_consistency_checker_v0.4.16.11.md`：API contract consistency checker 说明文档。
- `tools/check_api_contract_consistency.py`：离线 API 契约一致性检查工具。
- `tests/test_api_contract_consistency.py`：API 契约一致性单测。
- `tests/api_contract_consistency_v0.4.16.11_report.json`：一致性诊断报告，属于 schema/fixture 诊断类资产，不是 eval report。

## v0.4.16.10 API Field Catalog addendum

- `docs/api_field_catalog_v0.4.16.10.md`：API field catalog 说明文档。
- `tools/export_api_field_catalog.py`：离线导出 API field catalog 的工具。
- `tests/api_field_catalog_v0.4.16.10.json`：field catalog 产物，属于 schema/fixture 类资产。

## v0.4.16.9 API Error Example Contract addendum

- `tests/api_contract_bundle_v0.4.16.9.json`：包含 `error_examples` 的新 API contract bundle 产物。
- `docs/api_contract_bundle_v0.4.16.8.md`：补充说明 v0.4.16.9 起 bundle 包含错误状态样例。

## v0.4.16.8 API Contract Bundle addendum

- `docs/api_contract_bundle_v0.4.16.8.md`：API contract bundle 说明文档。
- `tools/export_api_contract_bundle.py`：离线 bundle 导出工具，合并 OpenAPI schema 与 example payload fixture。
- `tests/api_contract_bundle_v0.4.16.8.json`：bundle 产物，属于 schema/fixture 类资产，不是 eval report。

## v0.4.16.7 Roadmap Next-Step Hygiene addendum

- `docs/project_review_and_roadmap.md`：清理 `## 推荐下一步` 历史完成项污染，改为当前下一步短判断。
- `docs/final_report_version_guide.md`：新增 v0.4.16.7 roadmap next-step hygiene 报告素材。

## v0.4.16.6 API Endpoint Smoke Contract addendum

- `docs/final_report_version_guide.md`：新增 v0.4.16.6 endpoint smoke contract 报告素材，说明 mock 覆盖范围、边界和验证结果。
- `docs/project_review_and_roadmap.md`：更新当前版本和 v0.4.16.x 阶段摘要，并按 roadmap 保留窗口清理 v0.4.16.4 当前事项。

## v0.4.16.5 Roadmap and Final Report Maintenance addendum

- `docs/project_review_and_roadmap.md`：新增 roadmap 已完成事项保留窗口规则，并清理过期小版本流水账。
- `docs/final_report_version_guide.md`：将 v0.4.16 新增版本素材统一为中文并按自然升序维护。

## v0.4.16.4 API Example Payload Fixture addendum

- `docs/api_example_payloads_v0.4.16.4.md`：API example payload fixture 说明文档，记录用途、覆盖接口、契约校验方式和边界。
- `tests/fixtures/api_contract_example_payloads_v0.4.16.4.json`：schema/fixture 类资产，用于前端接入前离线联调参考；不是 eval report、manual decision 或正式前端产物。

## v0.4.16.1 API Contract Baseline addendum

- `docs/api_contract_stability_v0.4.16.1.md`：前后端接入前的 API contract 基线说明，记录接口路径、请求默认值、响应字段和边界。
- `docs/api_error_and_export_contract_v0.4.16.2.md`：统一错误响应与 `/risk/report/export` Markdown/JSON 内容类型契约说明。
- `tests/openapi_schema_v0.4.16.3.json`：当前 FastAPI OpenAPI schema 快照，供后续前端接入前比对。
- `docs/openapi_schema_snapshot_v0.4.16.3.md`：OpenAPI schema 快照说明文档。

## v0.4.15.26 Process Over-Risk Runtime Hardening addendum

- `tests/targeted_process_overrisk_trace_v0.4.15.26_report.json`：修复前程序/民事管理 over-risk 目标 case 定位产物。
- `tests/targeted_process_overrisk_patch_v0.4.15.26_report.json`：修复后目标验证产物，2/2 passed。
- `tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json`：商标 hardening 回归验证产物，2/2 passed。
- `tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json`：VAT 混合销售窄口径修复和高风险负例回归产物，5/5 passed。
- `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json`：hardening 后 compact full RAG eval，59/60 passed，retrieval `PASS=60`。
- `docs/process_overrisk_runtime_hardening_v0.4.15.26.md`：记录修复范围、法律边界、回归结果和剩余 strict-risk 技术债。

## v0.4.15.25 Trademark Over-Risk Runtime Patch addendum

- `tests/targeted_trademark_overrisk_trace_v0.4.15.25_report.json`: pre-patch targeted trace showing 2/2 trademark cases as exact-policy `over_risk` with retrieval `PASS`.
- `tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json`: post-patch targeted validation, 2/2 passed.
- `tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json`: compact full RAG eval after patch, 56/60 passed with retrieval `PASS=60`.
- `docs/trademark_overrisk_runtime_patch_v0.4.15.25.md`: scope, legal boundary, regression result, and remaining strict-risk debt.

## v0.4.15.24 Risk Level Over-Risk Legal Review Packet addendum

- `tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json`: saved-report-only preliminary legal review packet for 5 exact-policy `over_risk` cases.
- `docs/risk_level_overrisk_legal_review_packet_v0.4.15.24.md`: scope, per-case legal reasonableness summary, boundary, and follow-up notes.

## v0.4.15.23 Risk Level Over-Risk Attribution addendum

- `tests/risk_level_overrisk_attribution_v0.4.15.23_report.json`: saved-report-only attribution for 5 exact-policy `over_risk` cases.
- `docs/risk_level_overrisk_attribution_v0.4.15.23.md`: scope, result, interpretation boundaries, and follow-up review notes.

## v0.4.15.22 Risk Level Exact Policy addendum

- `tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json`: targeted exact-risk-level policy validation, 2/6 passed and 4 `over_risk` mismatches exposed.
- `tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json`: compact full RAG eval under exact risk-level policy, 55/60 passed with retrieval `PASS=60`.
- `docs/risk_level_exact_policy_v0.4.15.22.md`: scope, result, boundary, and follow-up notes for risk-level evaluation strictness.

## v0.4.15.21 Base Candidate Depth Runtime Patch addendum

- `tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json`: targeted base-candidate-depth runtime validation, 7/7 passed.
- `tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json`: compact full RAG eval after conservative patch, 60/60 passed.
- `docs/base_candidate_depth_runtime_patch_v0.4.15.21.md`: scope, result, rejected aggressive expansion, boundary, and verification notes.

## v0.4.15.20 Base Candidate Dense Live Probe addendum

- `tests/base_candidate_dense_live_probe_v0.4.15.20_report.json`: explicit dense-enabled live probe; status `completed_with_dense_probe`.
- `docs/base_candidate_dense_live_probe_v0.4.15.20.md`: scope, result, interpretation, boundary, and verification notes.

## v0.4.15.19 Base Candidate Live Read-Only Probe addendum

- `tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json`: live read-only Qdrant probe; status `completed_requires_dense_probe`.
- `docs/base_candidate_live_readonly_probe_v0.4.15.19.md`: scope, result, interpretation, boundary, and verification notes.

## v0.4.15.18 Base Candidate Mismatch Summary addendum

- `tests/base_candidate_mismatch_summary_v0.4.15.18_report.json`: saved-report source/article drift summary; status `qdrant_or_live_retrieval_needed`.
- `docs/base_candidate_mismatch_summary_v0.4.15.18.md`: scope, result, interpretation, boundary, and verification notes.

## v0.4.15.17 Base Retrieval / Query Inspection addendum

- `tests/base_retrieval_query_inspection_v0.4.15.17_report.json`: saved-report inspection; status `base_retrieval_query_inspection_needed`.
- `docs/base_retrieval_query_inspection_v0.4.15.17.md`: scope, result, interpretation, boundary, and verification notes.

## v0.4.15.16 Dependency Trace Summary addendum

- `tests/targeted_dependency_trace_v0.4.15.16_report.json`: non-compact targeted full-debug trace packet, 8/8 passed.
- `tests/dependency_trace_summary_v0.4.15.16_report.json`: saved-report dependency trace summary; 7/8 cases are `base_union_gap_anchor_filled`.
- `docs/dependency_trace_summary_v0.4.15.16.md`: scope, result, interpretation, boundary, and verification notes.

## v0.4.15.15 RAG Quality Triage addendum

- `tests/rag_quality_triage_v0.4.15.15_report.json`: saved-report-only quality triage; status `passed_with_high_dependency`.
- `docs/rag_quality_triage_v0.4.15.15.md`: scope, result, interpretation, boundary, and verification notes.

## v0.4.15.14 Roadmap Maintenance & Compact Eval Baseline addendum

- `docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md`: archived long-form roadmap snapshot before compaction.
- `docs/roadmap_maintenance_compact_eval_baseline_v0.4.15.14.md`: scope, result, boundary, and verification notes.
- `tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json`: compact full RAG eval baseline, 60/60 passed.

## v0.4.15.13 RAG Eval Compact Report Profile addendum

- `tests/targeted_compact_report_profile_v0.4.15.13_report.json`: focused compact smoke for `risk_algorithm_bias_001`, 1/1 passed, compact profile enabled.
- `docs/rag_eval_compact_report_profile_v0.4.15.13.md`: scope, preserved fields, removed fields, boundary, and verification notes.

## v0.4.15.12 Same-Bucket Signal Calibration addendum

- `tests/targeted_same_bucket_baseline_v0.4.15.12_report.json`: 4-case targeted baseline x 3 repeats, pass counts `[4, 4, 4]`.
- `tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json`: baseline full RAG eval, 60/60 passed, all retrieval stages `PASS`.
- `tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json`: calibrated full eval, 59/60 passed, all retrieval stages `PASS`; same-bucket risk count is 0 and observations remain 111.
- `tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json`: `risk_employee_facial_001` focused repeat, 5/5 passed.
- `docs/same_bucket_signal_calibration_v0.4.15.12.md`: version scope, boundary, and verification notes.

## v0.4.15.11 Hidden-Seed Signal Diagnostics & Output Stability addendum

- `tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json`: 产品责任 case 5 轮 repeat，5/5 passed，验证“请求赔偿/追偿/惩罚性赔偿”术语保留。
- `tests/targeted_output_stability_v0.4.15.11_report.json`: 4 个输出波动重点 case × 3 轮 targeted repeat，pass counts `[4, 4, 4]`，`unstable_cases=[]`。
- `tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json`: full RAG eval 60/60 passed，并写入 `quality_signal_diagnostics`；质量信号摘要包含 18 个 `same_bucket_selection_order_risk`。
- `docs/hidden_seed_signal_diagnostics_output_stability_v0.4.15.11.md`: 本版诊断信号、输出稳定化修复点、验证结果和边界说明。

## v0.4.15.10 Standard Contract Term Preservation addendum

- `tests/targeted_data_export_term_preservation_v0.4.15.10_report.json`: `data_export_contract_trigger_001` 5轮 repeat，全过且贡献标签为 `TERM_PRESERVATION_PASS`。
- `tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json`: 8重点 case × 3轮 targeted repeat，pass counts `[8, 8, 8]`。
- `tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json`: full RAG eval 60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- `docs/standard_contract_term_preservation_v0.4.15.10.md`: 标准合同术语保留修复说明。

## v0.4.15.9 Main-Chain Stability Closeout addendum

- `tests/targeted_main_chain_stability_v0.4.15.9_report.json`: 8重点 case × 3轮 targeted repeat，全过且 `unstable_cases=[]`。
- `tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json`: 单轮 full RAG eval，59/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- `tests/targeted_data_export_answer_stability_v0.4.15.9_report.json`: `data_export_contract_trigger_001` 5轮 focused repeat，全过，用于确认 full eval 单次失败是答案措辞波动。
- `docs/post_near_tie_main_chain_stability_closeout_v0.4.15.9.md`: 稳定性收口说明与边界记录。

## v0.4.15.8 Main-Chain Repair addendum

- `tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json`: regression reproduction report; full RAG eval was 31/60 before scope repair.
- `tests/targeted_post_near_tie_regression_v0.4.15.8_report.json`: targeted repeat for five near-tie/regression-sensitive cases; repeat 3 passed.
- `tests/targeted_antitrust_risk_level_v0.4.15.8_report.json`: targeted repeat for taxonomy risk-level repair; repeat 3 passed.
- `tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json`: final full RAG eval after v0.4.15.8 repairs; 60/60 passed.
- `docs/post_near_tie_patch_main_chain_repair_v0.4.15.8.md`: human-readable repair summary, boundary, and validation record.

## v0.4.15.7 Near-Tie Patch Closeout addendum

- `tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json`: saved-report closeout for the v0.4.15.6 same-bucket near-tie runtime patch; current status is `closed_for_next_real_rag_quality_task`.
- `docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md`: human-readable closeout summary confirming 5/5 targeted repeat, passed validation, stable final evidence identity, and passed project health.
- Boundary: closeout only; it does not run eval, call `rag_query`, access Qdrant, or change anchors, prompts, rerank scores, risk rules, fixtures, eval cases, or hidden seeds.

## v0.4.15.6 Near-Tie Runtime Patch Validation addendum

- `tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json`: raw post-patch targeted repeat report for `risk_algorithm_bias_001`; 5/5 passed and the final evidence chain stayed stable.
- `tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json`: validation report for v0.4.15.6; current status is `passed` after a 5/5 post-patch targeted repeat run.
- `docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md`: human-readable summary of runtime patch scope, validation state, and the 5/5 targeted repeat result.

## v0.4.15.5 Post-Rebuild Near-Tie Stability Policy Design 补充

- `tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json`: near-tie stability policy 设计报告；状态为 `ready_for_near_tie_policy_review`，建议未来只在既有 Cross-Encoder stable-score bucket 内做 deterministic ordering。
- `docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md`: 面向人工审阅的 Markdown 摘要；说明本版本是 design-only，不授权 runtime patch。

## v0.4.15.4 Post-Rebuild Selection Trace Attribution 补充

- `tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json`: `risk_algorithm_bias_001` 5 轮 targeted repeat trace capture 原始报告；5/5 passed，但第三席 final evidence 仍在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移。
- `tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json`: saved trace attribution 报告；归因为 `raw_rerank_order_boundary_drift_not_selector_replacement`，状态为 `needs_near_tie_stability_design`。
- `docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md`: 面向人工审阅的 Markdown 摘要；说明本版本不是 runtime fix，下一步应设计 near-tie stability policy。

## v0.4.15.3 Post-Rebuild Selection Trace Readiness 补充

- `tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json`: debug-only selection trace readiness 报告；确认 full rerank score order 与 final evidence selection trace 字段结构可用于下一轮 targeted repeat 归因。
- `docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md`: 面向人工审阅的 Markdown 摘要；说明本版本是 RAG 主链路可观测性补丁，不是 rerank 调参或 selector 行为修复。

## v0.4.15.2 Post-Rebuild Final Evidence Drift Attribution 补充

- `tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json`: `risk_algorithm_bias_001` final evidence 第三席漂移归因报告；确认核心 expected evidence 稳定，漂移首次可观察于 saved reranked/final top-3 边界。
- `docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md`: 面向人工审阅的 Markdown 摘要；说明当前 saved report 缺少完整 raw rerank score order 与 selector decision trace，因此不授权 runtime fix。

## v0.4.15.1 Post-Rebuild Repeat Instability Triage 补充

- `tests/targeted_repeat_product_liability_v0.4.15.1_report.json`: `risk_tort_product_liability_001` 5 轮 targeted repeat 原始报告；本轮 5/5 passed，final evidence identity 稳定。
- `tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json`: `risk_algorithm_bias_001` 5 轮 targeted repeat 原始报告；本轮 5/5 passed，但 final evidence identity drift 复现。
- `tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json`: targeted triage 摘要；将产品责任 case 降级为输出措辞观察项，将算法偏见 case 保留为证据稳定性阻断项。
- `docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md`: 面向人工审阅的 Markdown 摘要；说明本版本不是新 gate 链或 runtime fix 授权。

## v0.4.15.0 Post-Rebuild Repeat Stability Summary 补充

- `tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json`: 3 轮 post-rebuild full RAG eval repeat 原始结果；第 3 轮出现 59/60 的真实稳定性信号。
- `tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json`: repeat 稳定性摘要；汇总 unstable case、label variation、final evidence identity drift、baseline drift 和 high-risk manual review list。
- `docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md`: 面向人工审阅的 Markdown 摘要；说明本版本是 RAG quality stability diagnostics，不是样本修补工具或 runtime fix 授权。

## v0.4.14.35 Production Rebuild / Post-Rebuild Series Closeout 补充

- `tests/production_rebuild_post_rebuild_series_closeout_report.json`: v0.4.14.35 收口报告；只读归档生产重建、post-validation、smoke 25/25、初次 full RAG eval 58/60、selector 修复与收紧后 full RAG eval 60/60 的证据链，状态为 `closed_for_next_real_rag_quality_task`。
- `docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md`: 面向人工审阅的 Markdown 摘要；说明本版本是 saved-report closeout，不是新增 gate，不运行 full eval，不连接 Qdrant，不修改运行时代码。

## v0.4.14.34 Post-Rebuild Alignment Retention Tightening 补充

- `tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`: v0.4.14.34 selector 收紧后的正式 post-rebuild full RAG eval 报告；60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- `docs/post_rebuild_alignment_retention_tightening_v0.4.14.34.md`: 本版本 Markdown 摘要，说明 final evidence selector 的通用收紧点、protected evidence 硬保护、验证结果和禁止范围；本版本不新增 anchor、不修改 rerank/prompt/risk supplement/eval case。

## v0.4.14.33 Post-Rebuild Alignment Retention Delta 补充

- `tests/post_rebuild_alignment_retention_delta_report.json`: v0.4.14.32 selector 修复前后的 full RAG eval evidence delta 报告；记录 9 个 evidence changed cases、7 个 replacement delta、2 个 citation-only delta、0 个 removed expected evidence 和 0 个 regression。
- `docs/post_rebuild_alignment_retention_delta_v0.4.14.33.md`: 本版本 Markdown 摘要，列出需要抽样复核的 warn/关注项和下一步收口条件。

## v0.4.14.32 Post-Rebuild Evidence Alignment Retention 补充

- `tests/post_rebuild_rag_eval_after_alignment_retention_report.json`: selector 修复后的 post-rebuild full RAG eval 报告；60 个 cases 全部通过，`retrieval_failure_stage_summary={"PASS": 60}`。
- `docs/post_rebuild_alignment_retention_v0.4.14.32.md`: 本版本 Markdown 摘要，说明 selector-only evidence alignment retention 的修复内容、验证结果和边界。

## v0.4.14.31 Post-Rebuild Full RAG Eval Summary 补充

- `tests/post_rebuild_rag_eval_report.json`: 重建后 full RAG eval 报告；baseline 为 60/60，post-rebuild 为 58/60，失败项为 1 个答案关键词缺口和 1 个 expected evidence 缺口。
- `tests/post_rebuild_rag_eval_summary_report.json`: 重建后 full RAG eval 摘要；记录 2 个 baseline 回归、`answer_keyword_coverage_gap=1`、`final_evidence_selection_drop=1`。
- `docs/post_rebuild_rag_eval_summary_v0.4.14.31.md`: 面向人工审阅的 Markdown 摘要，说明下一步应进入两个明确回归的主链路排查，而不是继续新增 gate。

## v0.4.14.30 Post-Rebuild Quality Summary 补充

- `tests/post_rebuild_smoke_eval_report.json`: 重建后 smoke 复测报告；25 个 smoke cases 全部通过，覆盖当前 15 个 manifest 文档。
- `tests/post_rebuild_quality_summary_report.json`: 重建后质量摘要；baseline smoke 25/25、post-rebuild smoke 25/25、回归 case 0、post-validation passed、`missing_chunk_fields={}`。
- `docs/post_rebuild_quality_summary_v0.4.14.30.md`: 面向人工审阅的 Markdown 摘要，说明当前可进入 targeted 或 full RAG eval 复测。

## v0.4.14.29 Production Rebuild Execution 补充

- `tests/production_rebuild_execution_report.json`: 正式 production rebuild 执行记录；使用既有授权记录和已通过只读 preflight，调用 `rag_admin.py --rebuild` 重建 `legal_knowledge`，记录执行前后 `points_count=7177`、manifest 15 个文档、命令返回码与状态 `succeeded`。
- `tests/production_rebuild_post_validation_report.json`: 重建后只读验证报告；抽样扫描 Qdrant payload，确认 structured blocks 中已观测 `chunk_index/chunk_count`，并检查点数与执行记录一致。
- `docs/production_rebuild_execution_v0.4.14.29.md`: 本版本 Markdown 摘要，说明本版本是真实生产 collection rebuild，不是新增 gate；未运行 full eval。

## v0.4.14.28 Production Rebuild Authorization Record Intake 补充

- `tests/production_rebuild_authorization_record.json`: 正式 production rebuild 授权记录输入；记录 `authorization_status=accepted`、`target_collection=legal_knowledge`、snapshot reference、source lineage reference 与用户授权原文。
- `tests/production_rebuild_live_preflight_report.json`: v0.4.14.28 正式只读 live preflight 报告；真实读取 `legal_knowledge` collection，记录 `points_count=7177`、授权记录安全检查通过、`formal_authorization_accepted=true`、`blockers=[]`，并保持 `qdrant_write_allowed=false`、`production_rebuild_allowed=false`。
- `docs/production_rebuild_authorization_record_intake_v0.4.14.28.md`: 本版本 Markdown 摘要，说明授权记录只进入只读 preflight 判断，不是 Qdrant 写入许可或 production rebuild 执行记录。

## v0.4.14.27 Production Rebuild Read-Only Live Preflight Runner 补充

- `tests/production_rebuild_live_preflight_report.json`: v0.4.14.27 正式只读 live preflight 报告；真实读取 `legal_knowledge` collection，记录 `points_count=7177`、sample payload metadata keys、snapshot/source lineage 状态和当前 blocker `authorization_record_not_accepted`，并保持 `qdrant_write_allowed=false`、`production_rebuild_allowed=false`。
- `docs/production_rebuild_live_preflight_runner_v0.4.14.27.md`: 该 runner 的 Markdown 摘要，说明本版本是只读 live preflight 执行收口，不是新的 gate 链条；下一步应补授权引用并重跑同一 runner。

## v0.4.14.26 Production Rebuild Formal Authorization Gate 补充

- `tests/production_rebuild_formal_authorization_gate_report.json`: v0.4.14.26 正式 production rebuild 授权门禁报告；只读取 saved reports，确认 snapshot reference 已满足但正式 rebuild 授权仍未接受，因此 production rebuild 仍 blocked。
- `docs/production_rebuild_formal_authorization_gate_v0.4.14.26.md`: 该 gate 的 Markdown 摘要，说明 snapshot 创建授权不能自动升级为 rebuild 授权，下一步只能是收集正式授权并重新运行 fail-closed live preflight。

## v0.4.14.25 Production Rebuild Live Preflight Snapshot Create Reference Capture 补充

- `tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json`: v0.4.14.25 真实授权 Qdrant snapshot 创建与 reference 捕获报告；创建 `legal_knowledge-2019706566507018-2026-06-05-09-50-24.snapshot`，生成 `qdrant-snapshot://collection/legal_knowledge/legal_knowledge-2019706566507018-2026-06-05-09-50-24.snapshot`，但仍不授权 production rebuild。
- `docs/production_rebuild_live_preflight_snapshot_create_reference_capture_v0.4.14.25.md`: 该版本的 Markdown 摘要，说明 backup/snapshot reference 已补齐，后续阻断项缩小为正式 rebuild 授权未接受。

## v0.4.14.24 Production Rebuild Live Preflight Snapshot Reference Probe 补充

- `tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json`: v0.4.14.24 真实 Qdrant snapshot reference 只读 probe 报告；`legal_knowledge` collection 可访问，但 `snapshot_count=0`，没有可用 `backup_or_snapshot_reference`，因此继续 blocked。
- `docs/production_rebuild_live_preflight_snapshot_reference_probe_v0.4.14.24.md`: 该 probe 的 Markdown 摘要，说明本版本只检查现有 snapshot reference，不创建 snapshot，不写 Qdrant，也不授权 rebuild。

## v0.4.14.23 Production Rebuild Live Preflight Real Read-Only Probe 补充

- `tests/production_rebuild_live_preflight_real_readonly_probe_report.json`: v0.4.14.23 真实 Qdrant 只读 probe 报告；`legal_knowledge` collection 可达，`points_count=7177`，抽样 payload metadata 含 `chunk_id` / `qdrant_point_id`，但因未接受正式授权和缺 backup/snapshot 继续 blocked。
- `docs/production_rebuild_live_preflight_real_readonly_probe_v0.4.14.23.md`: 该 probe 的 Markdown 摘要，说明本版本已进入真实只读链路，但仍不授权写入或 rebuild。
## v0.4.14.22 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Gate 补充

- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json`: v0.4.14.22 gate 结果，记录 13 项检查、0 failure；确认 runner scaffold 仍是 standard-library-only、mock-only、fail-closed，正式 live preflight 输出未创建。
- `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md`: 该 gate 的 Markdown 摘要，说明通过后仍不能直接运行 live preflight 或 production rebuild。
## v0.4.14.21 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold 补充

- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json`: v0.4.14.21 scaffold status report，记录最小 runner scaffold 和 mock-only 单测已创建；正式 live preflight 输出仍未创建。
- `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_v0.4.14.21.md`: 该 scaffold 的 Markdown 摘要，说明本版本是 fail-closed scaffold 落地，不是生产 live preflight 或 rebuild 授权。
## v0.4.14.20 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design Gate 补充

- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json`: v0.4.14.20 gate 结果，记录 14 项检查、0 failure；确认 v0.4.14.19 scaffold design 的 future files 仍未创建，contract、placeholder tests、forbidden content 和 guardrails 稳定。
- `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md`: 该 gate 的 Markdown 摘要，说明通过后只开放最小 scaffold 创建，仍不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。
## v0.4.14.19 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design 补充

- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json`: v0.4.14.19 design 结果，记录未来 runner scaffold 的 3 个文件结构、不可执行占位策略、6 个 placeholder tests 和禁止内容；不创建 runner 文件、未来测试文件或未来输出报告。
- `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md`: 该 design 的 Markdown 摘要，说明本版本只开放 scaffold design gate，仍不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。

## v0.4.14.18 Production Rebuild Live Preflight Runner Minimal Implementation Design Gate 补充

- `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json`: v0.4.14.18 gate 结果，记录 15 项检查、0 failure；确认 v0.4.14.17 design 的 future files、CLI/function contract、read-only strategy、mock test strategy 和 fail-closed rules 稳定。
- `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_v0.4.14.18.md`: 该 gate 的 Markdown 摘要，说明通过后只开放 scaffold design，仍不创建 runner 文件、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。

## v0.4.14.17 Production Rebuild Live Preflight Runner Minimal Implementation Design 补充

- `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json`: v0.4.14.17 design 结果，记录未来 runner 的 3 个文件边界、CLI/函数契约、只读策略、6 个 mock tests 和 6 个 fail-closed rules；不创建 runner 文件。
- `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_v0.4.14.17.md`: 该 design 的 Markdown 摘要，说明本版本只开放 implementation design gate，仍不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。

## v0.4.14.16 Production Rebuild Live Preflight Runner Design Gate 补充

- `tests/production_rebuild_live_preflight_runner_design_gate_report.json`: v0.4.14.16 gate 结果，记录 15 项检查、0 failure；确认 v0.4.14.15 design 的 lineage、summary、guardrails、contract、fail-closed 与 scaffold cutoff policy 稳定。
- `docs/production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md`: 该 gate 的 Markdown 摘要，说明通过后只开放最小实现设计，仍不创建或运行 runner、不访问或写入 Qdrant、不执行 production rebuild。

## v0.4.14.15 Production Rebuild Live Preflight Runner Design 补充

- `tests/production_rebuild_live_preflight_runner_design_report.json`: v0.4.14.15 design 结果，记录 6 个 future inputs、8 个 preflight checks、10 个 output fields 与 8 个 blocking conditions；只开放 design gate，不创建或执行 runner。
- `docs/production_rebuild_live_preflight_runner_design_v0.4.14.15.md`: 该 design 的 Markdown 摘要，说明本版本仍不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild，并继续禁止 `input/importer scaffold` 扩张。

## v0.4.14.14 Production Rebuild Readiness Cutoff 补充

- `tests/production_rebuild_readiness_cutoff_report.json`: v0.4.14.14 cutoff 结果，确认 source patch、post-patch dry-run、authorization chain、execution design、input scaffold gate 与 project health 均满足转入 live preflight runner design 的最低条件；同时记录仍禁止 live preflight、Qdrant write、production rebuild 和正式授权接受。
- `docs/production_rebuild_readiness_cutoff_v0.4.14.14.md`: 该 cutoff 的 Markdown 摘要，说明本版本停止继续堆 input/importer scaffold 报告，下一步转入 `production_rebuild_live_preflight_runner_design`，但仍不代表已经允许生产执行。

## v0.4.14.13 Human Rebuild Authorization Record Input Form Scaffold Gate 补充

- `tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json`: v0.4.14.13 gate 结果，记录 17 项检查、0 failure；确认 v0.4.14.12 空白 input form scaffold 的 10 个字段、7 个分区、中文标签、未来控件提示、空值/export/import/validation 状态、guardrails、future policy 和 handoff boundary 稳定。
- `docs/human_rebuild_authorization_record_input_form_scaffold_gate_v0.4.14.13.md`: 该 form scaffold gate 的 Markdown 摘要，说明本 gate 仍不创建可运行输入表单或 importer、不导出/导入或校验真实审批值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.12 Human Rebuild Authorization Record Input Form Scaffold 补充

- `tests/human_rebuild_authorization_record_input_form_scaffold_report.json`: v0.4.14.12 scaffold 结果，记录 10 个空白表单字段、7 个分区、0 个已收集人工值；只开放 `human_rebuild_authorization_record_input_form_scaffold_gate`，仍不授权可运行表单、真实人工值、importer、审批导入、正式授权、live preflight、Qdrant write 或 production rebuild。
- `docs/human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md`: 该 input form scaffold 的 Markdown 摘要，说明本版本仍不创建可运行输入表单或 importer、不导出/导入或校验真实审批值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.11 Human Rebuild Authorization Record Input Packet Scaffold Gate 补充

- `tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json`: v0.4.14.11 gate 结果，记录 16 项检查、0 failure；确认 v0.4.14.10 空白 input packet scaffold 的 10 个字段、7 个分区、空值/import/validation 状态、guardrails、future policy 和 handoff boundary 稳定。
- `docs/human_rebuild_authorization_record_input_packet_scaffold_gate_v0.4.14.11.md`: 该 scaffold gate 的 Markdown 摘要，说明本 gate 仍不创建输入表单或 importer、不导入或校验真实审批值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.10 Human Rebuild Authorization Record Input Packet Scaffold 补充

- `tests/human_rebuild_authorization_record_input_packet_scaffold_report.json`: v0.4.14.10 scaffold 结果，记录 10 个空白输入字段、7 个分区、0 个已收集人工值；只开放 `human_rebuild_authorization_record_input_packet_scaffold_gate`，仍不授权真实人工值、输入入口、审批导入、正式授权、live preflight、Qdrant write 或 production rebuild。
- `docs/human_rebuild_authorization_record_input_packet_scaffold_v0.4.14.10.md`: 该 input packet scaffold 的 Markdown 摘要，说明本版本仍不创建可填写输入表单或 importer、不导入或校验真实审批值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.9 Human Rebuild Authorization Record Input Workflow Design Gate 补充

- `tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json`: v0.4.14.9 gate 结果，记录 14 项检查、0 failure；确认 v0.4.14.8 输入流程设计的 6 个未来流程阶段、10 个字段输入契约、guardrails、future validation/import policy 和 handoff boundary 稳定。
- `docs/human_rebuild_authorization_record_input_workflow_design_gate_v0.4.14.9.md`: 该 gate 的 Markdown 摘要，说明本版本仍不收集人工值、不创建输入表单或 importer、不导入或校验真实审批值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.8 Human Rebuild Authorization Record Input Workflow Design 补充

- `tests/human_rebuild_authorization_record_input_workflow_design_report.json`: v0.4.14.8 input workflow design 结果，记录 6 个未来流程阶段、10 个字段输入契约、0 个已收集人工值；只开放 `human_rebuild_authorization_record_input_workflow_design_gate`，仍不授权真实人工值、正式授权、live preflight、Qdrant write 或 production rebuild。
- `docs/human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md`: 该 input workflow design 的 Markdown 摘要，说明本版本仍不收集人工值、不创建输入表单或 importer、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.7 Human Rebuild Authorization Record Draft Scaffold Gate 补充

- `tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json`: v0.4.14.7 gate 结果，记录 13 项检查、0 failure；确认 v0.4.14.6 空白 scaffold 的字段顺序、分区、空值、guardrails、future validation policy 和 handoff boundary 稳定。
- `docs/human_rebuild_authorization_record_draft_scaffold_gate_v0.4.14.7.md`: 该 gate 的 Markdown 摘要，说明本版本仍不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.6 Human Rebuild Authorization Record Draft Scaffold 补充

- `tests/human_rebuild_authorization_record_draft_scaffold_report.json`: v0.4.14.6 draft scaffold 结果，记录 10 个空白字段、7 个分区、0 个已收集人工值；只开放 `human_rebuild_authorization_record_draft_scaffold_gate`，仍不授权真实人工值、正式授权、live preflight、Qdrant write 或 production rebuild。
- `docs/human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md`: 该 draft scaffold 的 Markdown 摘要，说明本版本仍不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.5 Human Rebuild Authorization Record Draft Design Gate 补充

- `tests/human_rebuild_authorization_record_draft_design_gate_report.json`: v0.4.14.5 gate 结果，记录 13 项检查、0 failure；确认 v0.4.14.4 draft design 的字段映射、分区、guardrails、future validation policy 和 handoff boundary 稳定。
- `docs/human_rebuild_authorization_record_draft_design_gate_v0.4.14.5.md`: 该 gate 的 Markdown 摘要，说明本版本仍不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.4 Human Rebuild Authorization Record Draft Design 补充

- `tests/human_rebuild_authorization_record_draft_design_report.json`: v0.4.14.4 draft design 结果，记录 10 个字段映射、7 个草案分区、0 个已收集人工值；只开放 `human_rebuild_authorization_record_draft_design_gate`，仍不授权填写正式授权、live preflight、Qdrant write 或 production rebuild。
- `docs/human_rebuild_authorization_record_draft_design_v0.4.14.4.md`: 该 draft design 的 Markdown 摘要，说明本版本仍不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.3 Human Rebuild Authorization Record Scaffold Gate 补充

- `tests/human_rebuild_authorization_record_scaffold_gate_report.json`: v0.4.14.3 gate 结果，记录 13 项检查、0 failure；确认 v0.4.14.2 scaffold 的字段顺序、空白值、guardrails、packet 和 handoff boundary 稳定。
- `docs/human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md`: 该 gate 的 Markdown 摘要，说明本版本仍不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.2 Human Rebuild Authorization Record Scaffold 补充

- `tests/human_rebuild_authorization_record_scaffold_report.json`: v0.4.14.2 scaffold 结果，记录 10 个未来授权字段、0 个已收集人工值、`authorization_granted=false`、`rebuild_allowed=false`；只开放 `human_rebuild_authorization_record_scaffold_gate`。
- `docs/human_rebuild_authorization_record_scaffold_v0.4.14.2.md`: 该 scaffold 的 Markdown 摘要，说明本版本仍不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.1 Production Rebuild Execution Design Gate 补充

- `tests/production_rebuild_execution_design_gate_report.json`: v0.4.14.1 gate 结果，记录 16 项检查、0 failure；确认 v0.4.14.0 design 的 closeout-only lineage、record contracts、guardrails 和 handoff boundary 稳定。
- `docs/production_rebuild_execution_design_gate_v0.4.14.1.md`: 该 gate 的 Markdown 摘要，说明本版本仍不创建或接受人工授权记录、不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.14.0 Production Rebuild Execution Design 补充

- `tests/production_rebuild_execution_design_report.json`: v0.4.14.0 design 结果，只基于 v0.4.13.18 closeout report，定义未来生产 rebuild execution series 的 5 类记录契约、7 个执行阶段、8 个 preflight checks 与 9 个 abort conditions；只开放 `production_rebuild_execution_design_gate`，`rebuild_allowed=false`。
- `docs/production_rebuild_execution_design_v0.4.14.0.md`: 该 design 的 Markdown 摘要，说明本版本仍不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.13.18 Ingestion Metadata Rebuild Planning Series Closeout 补充

- `tests/ingestion_metadata_rebuild_planning_series_closeout_report.json`: v0.4.13.18 closeout 结果，确认 v0.4.13 ingestion metadata patch and rebuild planning series 已收口；`allowed_next_step=production_rebuild_execution_design`，`rebuild_allowed=false`。
- `docs/ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md`: 该 closeout 的 Markdown 摘要，说明本版本仍不运行 live preflight、不访问或写入 Qdrant、不 rebuild。

## v0.4.13.17 Rebuild Runbook / Preflight Contract 补充

- `tests/rebuild_runbook_preflight_contract_report.json`: v0.4.13.17 contract 结果，记录 7 个 runbook phases、8 个 preflight checks、7 个 abort conditions；`live_preflight_run=false`、`rebuild_allowed=false`。
- `docs/rebuild_runbook_preflight_contract_v0.4.13.17.md`: 该 contract 的 Markdown 摘要，说明本版本仍不运行 live preflight、不访问 Qdrant、不 rebuild。

## v0.4.13.16 Human Rebuild Authorization Worksheet Gate 补充

- `tests/human_rebuild_authorization_worksheet_gate_report.json`: v0.4.13.16 worksheet gate 结果，记录 7 项检查、0 failure；确认 worksheet 仍为空白未授权状态。
- `docs/human_rebuild_authorization_worksheet_gate_v0.4.13.16.md`: 该 gate 的 Markdown 摘要，说明本版本仍不收集人工值、不创建授权记录、不访问 Qdrant、不 rebuild。

## v0.4.13.15 Human Rebuild Authorization Worksheet 补充

- `tests/human_rebuild_authorization_worksheet_report.json`: v0.4.13.15 worksheet 结果，记录 10 行授权字段、required/optional 标签、0 个已收集人工值；`authorization_granted=false`、`rebuild_allowed=false`。
- `docs/human_rebuild_authorization_worksheet_v0.4.13.15.md`: 该 worksheet 的 Markdown 摘要，说明本版本仍不创建授权记录、不访问 Qdrant、不 rebuild、不调用 RAG/LLM/full eval。

## v0.4.13.14 Rebuild Authorization Design Gate 补充

- `tests/rebuild_authorization_design_gate_report.json`: v0.4.13.14 design gate 结果，记录 12 项检查、0 failure；确认 v0.4.13.13 design 的 lineage、必填授权字段、终止条件、output contract 和 handoff boundaries 稳定。
- `docs/rebuild_authorization_design_gate_v0.4.13.14.md`: 该 gate 的 Markdown 摘要，说明本版本仍不创建人工授权记录、不访问 Qdrant、不 rebuild、不调用 RAG/LLM/full eval。

## v0.4.13.13 Rebuild Authorization Design 补充

- `tests/rebuild_authorization_design_report.json`: v0.4.13.13 rebuild 授权设计结果，记录未来人工授权必须包含的 target collection、scope、source lineage、expected ID drift acknowledgement、backup/rollback plan、operator approval、maintenance window、post-rebuild validation 和 abort conditions。
- `docs/rebuild_authorization_design_v0.4.13.13.md`: 该 design 的 Markdown 摘要，说明本版本仍不创建授权、不访问 Qdrant、不 rebuild、不调用 RAG/LLM/full eval。

## v0.4.13.12 Post-Patch Rebuild Dry-Run Runner Gate 补充

- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json`: v0.4.13.12 runner gate 结果，记录 11 项检查、0 failure；确认 v0.4.13.11 saved report 的 3 个样本、9 行对比、metadata presence、expected ID drift、0 forbidden drift、0 blocker 与 guardrails 稳定。
- `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_v0.4.13.12.md`: 该 gate 的 Markdown 摘要，记录只读 saved-report 边界，以及仍禁止 Qdrant/rebuild/RAG/LLM/full eval 的限制。

## v0.4.13.11 Post-Patch Rebuild Dry-Run Runner 补充

- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json`: v0.4.13.11 runner 结果，记录 3 个本地样本、9 行对比、9 行边界元数据存在、9 行预期 `chunk_id/qdrant_point_id` drift、0 forbidden drift、0 blocking condition；只开放 runner gate。
- `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_v0.4.13.11.md`: 该 runner 的 Markdown 摘要，记录样本覆盖、对比结果和仍禁止 Qdrant/rebuild/RAG/LLM/full eval 的边界。

## v0.4.13.10 Post-Patch Rebuild Dry-Run Design Gate 补充

- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json`: v0.4.13.10 design gate 结果，确认 21 项检查通过、0 failure；只开放 post-patch rebuild dry-run runner，且本版本不创建 runner、不写 Qdrant、不 rebuild。
- `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_v0.4.13.10.md`: 该 gate 的 Markdown 摘要，记录检查项、通过状态和继续禁止 runner creation/Qdrant/rebuild 的边界。

## v0.4.13.9 Post-Patch Rebuild Dry-Run Design 补充

- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json`: v0.4.13.9 post-patch rebuild dry-run design 报告，定义未来 runner 的 allowed/forbidden inputs、comparison fields、output contract 和 blocking conditions；本报告不创建 runner、不写 Qdrant、不 rebuild。
- `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_v0.4.13.9.md`: 该 design 的 Markdown 摘要，记录 design-only 边界和下一步 design gate。

## v0.4.13.8 入库元数据源码补丁补充

- `tests/ingestion_metadata_source_patch_report.json`: v0.4.13.8 源码补丁检查结果，确认 15 项检查通过、0 failure；普通法律 article/paragraph/item 块已补齐 `chunk_index/chunk_count`，但仍不授权 Qdrant 写入或 rebuild。
- `docs/ingestion_metadata_source_patch_v0.4.13.8.md`: 该源码补丁检查的 Markdown 摘要，记录检查项、通过状态和下一步 post-patch rebuild dry-run design 边界。

## v0.4.13.7 Ingestion Metadata Patch Actual Design Gate 补充

- `tests/ingestion_metadata_patch_actual_design_gate_report.json`: v0.4.13.7 actual design gate 结果，确认 31 项检查通过、0 failure；只开放 minimal ingestion metadata source patch，不代表已修改 ingestion、已重建索引或已授权 Qdrant 写入。
- `docs/ingestion_metadata_patch_actual_design_gate_v0.4.13.7.md`: 该 gate 的 Markdown 摘要，记录检查项、通过状态和下一步最小源码 patch 边界。

## v0.4.13.6 Ingestion Metadata Patch Actual Design 补充

- `tests/ingestion_metadata_patch_actual_design_report.json`: v0.4.13.6 actual patch design report，限定未来 patch 只能触及 `src/rag/ingestion.py::build_article_documents`，并记录 parent/child chunk metadata 规则、post-patch 验证计划和仍禁止的动作。
- `docs/ingestion_metadata_patch_actual_design_v0.4.13.6.md`: 该 design 的 Markdown 摘要；不代表已修改 ingestion、已重建索引或已授权 Qdrant 写入。

## v0.4.13.5 Ingestion Metadata Patch Local Dry-Run Gate 补充

- `tests/ingestion_metadata_patch_local_dry_run_gate_report.json`: v0.4.13.5 local dry-run gate 结果，确认 25 项检查通过、0 failure；只开放 actual ingestion metadata patch design，不代表已修改 ingestion、已重建索引或已授权 Qdrant 写入。
- `docs/ingestion_metadata_patch_local_dry_run_gate_v0.4.13.5.md`: 该 gate 的 Markdown 摘要，记录检查项、通过状态和继续禁止实现/rebuild 的边界。

## v0.4.13.4 Ingestion Metadata Patch Local Dry-Run Runner 补充

- `tests/ingestion_metadata_patch_local_dry_run_report.json`: v0.4.13.4 local dry-run 结果，记录 3 个 in-memory 样例的 boundary metadata drift、`chunk_id`/`qdrant_point_id` drift 和 forbidden drift 状态；不代表已修改 ingestion 或已重建索引。
- `docs/ingestion_metadata_patch_local_dry_run_v0.4.13.4.md`: 该 dry-run 的 Markdown 摘要，记录样例、漂移计数和下一步 gate 边界。

## v0.4.13.3 Ingestion Metadata Patch Dry-Run Design Gate 补充

- `tests/ingestion_metadata_patch_dry_run_design_gate_report.json`：v0.4.13.3 ingestion metadata patch dry-run design gate，用于确认 v0.4.13.2 design 的 local-only scope、expected/forbidden drift、output contract 和 blocking conditions 稳定；本报告不实现 runner、不授权 patch、不写 Qdrant。
- `docs/ingestion_metadata_patch_dry_run_design_gate_v0.4.13.3.md`：该 gate 的 Markdown 摘要，记录 checks、failed checks 与下一步 local dry-run runner。

## v0.4.13.2 Ingestion Metadata Patch Dry-Run Design 补充

- `tests/ingestion_metadata_patch_dry_run_design_report.json`：v0.4.13.2 ingestion metadata patch dry-run design，用于定义未来 local dry-run 如何比较 patch 前后的 metadata、`chunk_id`、`qdrant_point_id` 漂移；本报告不授权实现、不写 Qdrant、不改主链路。
- `docs/ingestion_metadata_patch_dry_run_design_v0.4.13.2.md`：该 design 的 Markdown 摘要，记录 comparison strategy、expected drift、forbidden drift 和 blocking conditions。

## v0.4.13.1 Ingestion Metadata Patch Contract Gate 补充

- `tests/ingestion_metadata_patch_contract_gate_report.json`：v0.4.13.1 ingestion metadata patch contract gate，用于确认 v0.4.13.0 contract 的 allowed file/function、parent/child rules、rebuild/stable ID impact、Qdrant 禁止和主链路禁止边界稳定；本报告不授权实现、不写 Qdrant、不改主链路。
- `docs/ingestion_metadata_patch_contract_gate_v0.4.13.1.md`：该 gate 的 Markdown 摘要，记录 checks、failed checks 与下一步 dry-run design。

## v0.4.13.0 Ingestion Metadata Patch Contract 补充

- `tests/ingestion_metadata_patch_contract_report.json`：v0.4.13.0 ingestion metadata patch contract，用于限定未来 patch 只能在 `src/rag/ingestion.py::build_article_documents` 增加 deterministic `chunk_index/chunk_count` metadata；本报告不授权实现、不写 Qdrant、不改主链路。
- `docs/ingestion_metadata_patch_contract_v0.4.13.0.md`：该 contract 的 Markdown 摘要，记录 patch boundary、parent/child chunk rules、future tests 与 rebuild dry-run requirements。

## v0.4.12.3 Metadata/Chunking Series Closeout 补充

- `tests/metadata_chunking_series_closeout_report.json`：v0.4.12.3 metadata/chunking series closeout report，用于确认 v0.4.12.0-v0.4.12.2 链条完整，并把下一系列限定为 ingestion metadata patch and rebuild dry-run planning；本报告不授权实现、不写 Qdrant、不改主链路。
- `docs/metadata_chunking_series_closeout_v0.4.12.3.md`：该 closeout 的 Markdown 摘要，记录 completed steps、handoff、must-not-do next 与 required next inputs。

## v0.4.12.2 Metadata/Chunking Fix Design Gate 补充

- `tests/metadata_chunking_fix_design_gate_report.json`：v0.4.12.2 metadata/chunking fix design gate report，用于确认 v0.4.12.1 fix design 已记录 stable ID impact、rebuild required、direct payload patch 禁止和 runtime implementation 禁止边界；本报告不授权实现、不写 Qdrant、不改主链路。
- `docs/metadata_chunking_fix_design_gate_v0.4.12.2.md`：该 gate 的 Markdown 摘要，记录 checks、failed checks 与下一步 series closeout。

## v0.4.12.1 Metadata/Chunking Fix Design 补充

- `tests/metadata_chunking_fix_design_report.json`：v0.4.12.1 metadata/chunking fix design report，用于把 v0.4.12.0 root-cause 转成 article/paragraph/item chunk boundary metadata 修复设计；本报告不授权实现、不写 Qdrant、不改主链路。
- `docs/metadata_chunking_fix_design_v0.4.12.1.md`：该 fix design 的 Markdown 摘要，记录 proposed patch plan、metadata contract、stable ID impact、future validations 与禁止动作。

## v0.4.12.0 Metadata/Chunking Root-Cause Report 补充

- `tests/metadata_chunking_root_cause_report.json`：v0.4.12.0 metadata/chunking root-cause report，用于把 v0.4.11.x 真实 Qdrant payload snapshot findings 与 `src/rag/ingestion.py` 静态信号对齐，确认 primary root cause 为 legal article ingestion path 缺少 chunk boundary metadata；本报告不授权修复、不写 Qdrant、不改主链路。
- `docs/metadata_chunking_root_cause_v0.4.12.0.md`：该 root-cause report 的 Markdown 摘要，记录 primary cause、supporting signals、stable ID impact、prohibited actions 与下一步 fix design 边界。

## v0.4.11.3 Evidence Metadata Snapshot Series Closeout 补充

- `tests/evidence_metadata_snapshot_series_closeout_report.json`：v0.4.11.3 series closeout 报告，用于确认 v0.4.11.0-v0.4.11.2 只读 snapshot 链条完整，并将 `chunk_boundary_ambiguity` 作为下一系列 root-cause/fix design 输入。
- `docs/evidence_metadata_snapshot_series_closeout_v0.4.11.3.md`：该 closeout 的 Markdown 摘要，记录 completed steps、primary finding、recommended next series 和 boundaries。

## v0.4.11.2 Evidence Metadata Snapshot Gate 补充

- `tests/evidence_metadata_snapshot_gate_report.json`：v0.4.11.2 snapshot gate 报告，用于确认 v0.4.11.1 确实完成 Qdrant payload read、vectors disabled、19 行诊断和 finding 分布；不代表已授权 metadata/chunk 修复。
- `docs/evidence_metadata_snapshot_gate_v0.4.11.2.md`：该 gate 的 Markdown 摘要，记录 primary finding、blocked target count 和下一步 closeout。

## v0.4.11.1 Evidence Metadata Snapshot Runner 补充

- `tests/evidence_metadata_snapshot_report.json`：v0.4.11.1 read-only Qdrant payload snapshot 报告，记录 19 个 evidence targets、7177 个 scanned points、19 个 `chunk_boundary_ambiguity` findings；不代表已授权 metadata/chunk 修复。
- `docs/evidence_metadata_snapshot_v0.4.11.1.md`：该 snapshot runner 的 Markdown 摘要，记录 Qdrant payload read、diagnostic row count、blocked target count 和 boundaries。

## v0.4.11.0 Evidence Metadata Snapshot Contract 补充

- `tests/evidence_metadata_snapshot_contract_report.json`：v0.4.11.0 evidence metadata snapshot contract 报告，用于定义未来只读 Qdrant payload snapshot runner 的 19 个 evidence targets、输出字段、failure buckets 和 guardrails；不代表已读取 Qdrant 或已授权修复。
- `docs/evidence_metadata_snapshot_contract_v0.4.11.0.md`：该 contract 的 Markdown 摘要，记录 target count、allowed next step 和 boundaries。

## v0.4.10.3 Metadata/Chunking Diagnostic Runner Series Closeout 补充

- `tests/metadata_chunking_diagnostic_runner_series_closeout_report.json`：v0.4.10.3 series closeout 报告，用于确认 v0.4.10.0-v0.4.10.2 saved-report runner 链条完整；不代表已读取 evidence-level metadata snapshot、已访问 Qdrant 或已授权修复。
- `docs/metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md`：该 closeout 的 Markdown 摘要，记录 completed steps、recommended next series 和 boundaries。

## v0.4.10.2 Metadata/Chunking Saved-Report Runner Gate 补充

- `tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json`：v0.4.10.2 saved-report runner gate 报告，用于确认 v0.4.10.1 runner 输出 40 行、0 blocked rows、字段契约完整，并继续保持 saved-report-only 边界。
- `docs/metadata_chunking_diagnostic_saved_report_runner_gate_v0.4.10.2.md`：该 gate 的 Markdown 摘要，记录检查项、通过状态、开放的下一步和禁止越界动作。

## v0.4.10.1 Metadata/Chunking Saved-Report Diagnostic Runner 补充

- `tests/metadata_chunking_diagnostic_saved_report_runner_report.json`：v0.4.10.1 saved-report scope metadata/chunking diagnostic runner 报告，用于验证 40 个 manifest items 的诊断输入与输出契约；不代表已读取 evidence-level metadata snapshot、已访问 Qdrant 或已授权修复。
- `docs/metadata_chunking_diagnostic_saved_report_runner_v0.4.10.1.md`：该 runner 的 Markdown 摘要，记录诊断行数、限制和 boundaries。

## v0.4.10.0 Metadata/Chunking Diagnostic Runner Manifest 补充

- `tests/metadata_chunking_diagnostic_runner_manifest_report.json`：v0.4.10.0 metadata/chunking diagnostic runner manifest 报告，用于定义 8 个 sample cases x 5 个 check groups 的只读诊断输入矩阵；不代表已创建 runner、已运行 diagnostic 或已授权修复。
- `docs/metadata_chunking_diagnostic_runner_manifest_v0.4.10.0.md`：该 manifest 的 Markdown 摘要，记录输入来源、manifest item 数量和 boundaries。

## v0.4.9.11 Retrieval Input Quality Series Closeout 补充

- `tests/retrieval_input_quality_series_closeout_report.json`：v0.4.9.11 retrieval input quality series closeout 报告，用于确认 v0.4.9.0-v0.4.9.10 saved reports、工具、测试和非运行时边界完整闭环；不代表已创建 runner、已运行 diagnostic 或已授权修复。
- `docs/retrieval_input_quality_series_closeout_v0.4.9.11.md`：该 closeout 的 Markdown 摘要，记录 completed steps、recommended next series 和 boundaries。

## v0.4.9.10 Metadata/Chunking Diagnostic Dry-Run Contract 补充

- `tests/metadata_chunking_diagnostic_dry_run_contract_report.json`：v0.4.9.10 metadata/chunking diagnostic dry-run contract 报告，用于定义未来只读 runner 的 CLI、输入 saved reports、输出字段、failure handling 与非运行时边界；不代表已创建 runner、已运行 diagnostic 或已授权修复。
- `docs/metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md`：该 contract 的 Markdown 摘要，记录 contract rows、output contract 和 prohibited actions。

## v0.4.9.9 Metadata/Chunking Diagnostic Runner Design Gate 补充

- `tests/metadata_chunking_diagnostic_runner_design_gate_report.json`：v0.4.9.9 metadata/chunking diagnostic runner design gate 报告，用于确认 v0.4.9.8 runner design 契约未漂移且未授权 runtime；不代表已运行 diagnostic 或已授权修复。
- `docs/metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md`：该 gate 的 Markdown 摘要，记录 checks、next allowed step 和非运行时边界。

## v0.4.9.8 Metadata/Chunking Diagnostic Runner Design 补充

- `tests/metadata_chunking_diagnostic_runner_design_report.json`：v0.4.9.8 metadata/chunking diagnostic runner design 报告，用于定义未来只读 runner 的输入契约、输出字段、failure buckets 与非运行时边界；不代表已运行 diagnostic 或已授权修复。
- `docs/metadata_chunking_diagnostic_runner_design_v0.4.9.8.md`：该 runner design 的 Markdown 摘要，记录 design rows、output contract 和 prohibited actions。

## v0.4.9.7 Metadata/Chunking Diagnostic Spec Gate 补充

- `tests/metadata_chunking_diagnostic_spec_gate_report.json`：v0.4.9.7 metadata/chunking diagnostic spec gate 报告，用于确认 v0.4.9.6 spec 可以稳定进入 runner design；不代表已运行 diagnostic 或已授权修复。
- `docs/metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md`：该 gate 的 Markdown 摘要，记录 checks、next allowed step 和非运行时边界。

## v0.4.9.6 Metadata/Chunking Diagnostic Spec 补充

- `tests/metadata_chunking_diagnostic_spec_report.json`：v0.4.9.6 metadata/chunking diagnostic spec，定义 5 个未来检查组、10 个核心 metadata/chunking 字段覆盖、8 个 sample case scope 与禁止动作。
- `docs/metadata_chunking_diagnostic_spec_v0.4.9.6.md`：对应 Markdown spec summary，用于说明 check groups、sample case scope、prohibited actions 和不运行 diagnostic 的边界。

## v0.4.9.5 Retrieval Input Quality Diagnostic Prioritization Gate 补充

- `tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json`：v0.4.9.5 prioritization gate，确认 v0.4.9.4 priority matrix 完整、顺序稳定、17 项检查全部通过，且只开放 metadata/chunking diagnostic spec。
- `docs/retrieval_input_quality_diagnostic_prioritization_gate_v0.4.9.5.md`：对应 Markdown gate summary，用于说明检查项、通过状态和禁止 runtime change 的边界。

## v0.4.9.4 Retrieval Input Quality Diagnostic Prioritization 补充

- `tests/retrieval_input_quality_diagnostic_prioritization_report.json`：v0.4.9.4 diagnostic prioritization，将 metadata/chunking、anchor dependency、query lexical coverage、source/article identity、legal domain boundary 排成 5 条诊断优先级。
- `docs/retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md`：对应 Markdown planning summary，用于说明 priority matrix、entry conditions、prohibited actions 和禁止 runtime change 的边界。

## v0.4.9.3 Retrieval Input Quality Offline Audit Gate 补充

- `tests/retrieval_input_quality_offline_audit_gate_report.json`：v0.4.9.3 offline audit gate，确认 v0.4.9.2 audit report 完整、顺序稳定、15 项检查全部通过且保持非运行时边界。
- `docs/retrieval_input_quality_offline_audit_gate_v0.4.9.3.md`：对应 Markdown gate summary，用于说明 gate status、检查项和只允许进入 diagnostic planning 的边界。

## v0.4.9.2 Retrieval Input Quality Offline Audit 补充

- `tests/retrieval_input_quality_offline_audit_report.json`：v0.4.9.2 offline audit，按 v0.4.9.1 audit spec 读取既有 saved reports，输出 5 个 bucket 的 impacted case count、sample cases、evidence signals、severity 和 recommended next route。
- `docs/retrieval_input_quality_offline_audit_v0.4.9.2.md`：对应 Markdown audit summary，用于说明 5 个离线审计结果、严重度分布、下一步 gate 建议和禁止 runtime change 的边界。

## v0.4.9.1 Retrieval Input Quality Audit Spec 补充

- `tests/retrieval_input_quality_audit_spec_report.json`：v0.4.9.1 audit spec，将 source/article identity、metadata/chunking、query lexical coverage、legal domain boundary 与 anchor dependency 五类 bucket 转成离线审计契约。
- `docs/retrieval_input_quality_audit_spec_v0.4.9.1.md`：对应 Markdown spec summary，用于说明 5 个 audit specs、required outputs、gate checks 和禁止 runtime change 的边界。

## v0.4.9.0 Retrieval Input Quality Intake 补充

- `tests/retrieval_input_quality_intake_report.json`：v0.4.9.0 retrieval input quality intake，基于既有 saved reports 汇总 source/article identity、metadata/chunking、query lexical coverage、legal domain boundary 与 anchor dependency 五类治理 bucket。
- `docs/retrieval_input_quality_intake_v0.4.9.0.md`：对应 Markdown intake summary，用于说明 5 个 bucket、12 个 sample cases、下一步 audit spec 和禁止 runtime change 的边界。

## 已合并的历史产物锚点

- `tests/ready_action_design_pack_report.json`：历史 ready action 设计包报告，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。
- `tests/ready_action_design_review_brief_report.json`：历史 ready action 设计评审简报报告，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。
- `tests/ready_action_design_review_gate_report.json`：历史 ready action 设计评审 gate 报告，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。
- `tests/filled_manual_review_workbench_pilot5_cleaned_2026-05-13.json`：pilot 5 清洗后的 filled workbench export 副本，只作为历史治理输入锚点保留。
- `tests/pilot_manual_review_bedside_advisory_feedback_2026-05-13.json`：pilot bedside advisory feedback 快照，只作人工理解和核对材料。
- `tests/pilot_manual_review_local_draft_import_candidate_2026-05-13.json`：visual workbench 本地草稿候选，不能绕过正式 filled export/importer 契约。

## v0.4.8.15 Final Evidence Selection Policy Series Closeout 补充

- `tests/final_evidence_selection_policy_series_closeout_report.json`：v0.4.8.15 series closeout，确认 v0.4.8.x 已完成离线设计、模拟、gate 与 adoption draft 链条，但不记录正式用户采纳、不授权 runtime implementation。
- `docs/final_evidence_selection_policy_series_closeout_v0.4.8.15.md`：对应 Markdown closeout summary，用于说明 16 个完成步骤、后续建议和禁止 runtime adoption 的边界。

## v0.4.8.14 Final Evidence Selection Policy Adoption Decision Draft 补充

- `tests/final_evidence_selection_policy_adoption_decision_draft_report.json`：v0.4.8.14 adoption decision draft，基于 v0.4.8.13 gate 与 v0.4.8.12 simulation，生成 8 条待用户确认的 adoption route rows。
- `docs/final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md`：对应 Markdown draft summary，用于说明 adoption options、用户确认要求和禁止 runtime adoption 的边界。

## v0.4.8.13 Final Evidence Selection Policy Offline Simulation Gate 补充

- `tests/final_evidence_selection_policy_offline_simulation_gate_report.json`：v0.4.8.13 离线模拟结果门禁，确认 v0.4.8.12 simulation report 完整、顺序稳定、0 个 blocking failure 且保持非运行时边界。
- `docs/final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md`：对应 Markdown gate summary，用于说明检查项、通过状态和只允许进入 adoption decision draft 的边界。

## v0.4.8.12 Final Evidence Selection Policy Offline Simulation 补充

- `tests/final_evidence_selection_policy_offline_simulation_report.json`：v0.4.8.12 最终证据选择策略离线模拟结果，只消费 v0.4.8.11 输入契约，记录 8 条 policy category 的模拟信号。
- `docs/final_evidence_selection_policy_offline_simulation_v0.4.8.12.md`：对应 Markdown summary，用于说明模拟结果、manual review signals 和禁止 runtime adoption 的边界。

## v0.4.8.11 Final Evidence Selection Policy Offline Simulation Input Contract 补充

- `tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json`：v0.4.8.11 最终证据选择策略离线模拟输入契约，来源于 v0.4.8.7 confirmed record 与 v0.4.8.10 language confirmation record。
- `docs/final_evidence_selection_policy_offline_simulation_input_contract_v0.4.8.11.md`：对应 Markdown contract，用于说明 8 条 simulation input rows、来源类别和禁止 runtime adoption 的边界。
- `tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py`：生成上述只读 input contract，不运行 simulation、不授权代码实现、不接入主链路。

## v0.4.8.10 Final Evidence Selection Policy Language Revision Confirmation Record 补充

- `tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json`：v0.4.8.10 最终证据选择策略语言修订确认记录，来源于 `tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json` 和用户确认文本。
- `docs/final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md`：对应 Markdown record，用于说明 3 条 confirmed wording、确认上下文、offline simulation design handoff 和禁止 runtime adoption 的边界。
- `tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py`：生成上述只读 confirmation record，不授权代码实现、不接入主链路。

## v0.4.8.9 Final Evidence Selection Policy Language Revision Closeout Draft 补充

- `tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json`：v0.4.8.9 最终证据选择策略语言修订收口草案，来源于 `tests/final_evidence_selection_policy_language_revision_worksheet_report.json`。
- `docs/final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md`：对应 Markdown draft，用于说明 3 条 suggested wording、must-not-mean、acceptance boundary 和 confirmation question。
- `tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py`：生成上述只读 confirmation draft，不记录最终 wording、不授权代码实现、不接入主链路。

## v0.4.8.8 Final Evidence Selection Policy Language Revision Worksheet 补充

- `tests/final_evidence_selection_policy_language_revision_worksheet_report.json`：v0.4.8.8 最终证据选择策略语言修订 worksheet，来源于 `tests/final_evidence_selection_policy_closeout_confirmed_record_report.json`。
- `docs/final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md`：对应 Markdown worksheet，用于说明 3 条 revision rows、wording risk、target boundary、acceptance checks 和 simulation entry condition。
- `tools/build_final_evidence_selection_policy_language_revision_worksheet.py`：生成上述只读 worksheet，不形成最终 wording、不授权代码实现、不接入主链路。
## v0.4.8.7 Final Evidence Selection Policy Closeout Confirmed Record 补充

- `tests/final_evidence_selection_policy_closeout_confirmed_record_report.json`：v0.4.8.7 最终证据选择策略收口正式确认记录，来源于 `tests/final_evidence_selection_policy_closeout_confirmation_record_report.json` 和用户明确确认文本。
- `docs/final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md`：对应 Markdown confirmed record，用于说明 8 条 confirmed rows、后续离线分流和禁止 runtime adoption 的边界。
- `tools/build_final_evidence_selection_policy_closeout_confirmed_record.py`：生成上述只读 confirmed record，不授权代码实现、不接入主链路。
## v0.4.8.6 Final Evidence Selection Policy Closeout Confirmation Record Scaffold 补充

- `tests/final_evidence_selection_policy_closeout_confirmation_record_report.json`：v0.4.8.6 最终证据选择策略收口确认记录脚手架报告，来源于 `tests/final_evidence_selection_policy_closeout_decision_draft_report.json`。
- `docs/final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md`：对应 Markdown confirmation scaffold，用于说明 8 条 `pending_user_confirmation` rows、空确认字段、可选确认项和禁止 runtime adoption 的边界。
- `tools/build_final_evidence_selection_policy_closeout_confirmation_record.py`：生成上述只读 confirmation scaffold，不伪造用户确认、不记录正式人工结论、不授权实现。
## v0.4.8.5 Final Evidence Selection Policy Closeout Decision Draft 补充

- `tests/final_evidence_selection_policy_closeout_decision_draft_report.json`：v0.4.8.5 最终证据选择策略收口决策草案报告，来源于 `tests/final_evidence_selection_policy_closeout_envelope_report.json`。
- `docs/final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md`：对应 Markdown decision draft，用于说明 8 条 user-confirmation draft rows、suggested closeout options、confirmation questions、required basis 和禁止 runtime adoption 的边界。
- `tools/build_final_evidence_selection_policy_closeout_decision_draft.py`：生成上述只读 user-confirmation draft，不记录正式人工结论、不授权实现。
## v0.4.8.4 Final Evidence Selection Policy Closeout Envelope 补充

- `tests/final_evidence_selection_policy_closeout_envelope_report.json`：v0.4.8.4 最终证据选择策略收口外壳报告，来源于 `tests/final_evidence_selection_policy_human_review_worksheet_report.json`。
- `docs/final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md`：对应 Markdown closeout envelope，用于说明 8 条 pending closeout rows、candidate routes、minimum human basis、recommended options 和禁止 runtime adoption 的边界。
- `tools/build_final_evidence_selection_policy_closeout_envelope.py`：生成上述只读 closeout envelope，不记录正式人工结论、不授权实现。

更新日期：2026-05-16

## 定位

本文档用于说明项目中常见报告、测试产物和工具输出的归属。它不是迁移计划，也不是新的运行入口。

当前权威产物仍主要在 `tests/` 下；`reports/` 下的分组目录只是未来整理目录时的脚手架。除非某个工具或文档明确说明，默认不要把 `reports/` 当成当前报告输出位置。

## 快速判断

| 位置 | 当前作用 | 是否权威 |
|---|---|---|
| `tests/*.json` | 当前主要评测、诊断、审阅、dry-run 报告 | 是 |
| `tests/*.csv` | 人工复核工作台导出的表格辅助文件 | 仅作人工阅读/核对；正式 importer 不再接受 CSV |
| `tests/fixtures/` | 单测夹具和小型样例输入 | 是 |
| `tests/manual_review_export_pipeline_dry_run_artifacts/` | export pipeline dry-run 的隔离中间产物 | 是，但仅供 dry-run 使用 |
| `tools/manual_review_visual_workbench/index.html` | 本地离线人工复核工作台页面 | 是 |
| `docs/` | 版本说明、维护说明、最终报告素材 | 是 |
| `reports/eval` | 未来 eval 报告分组镜像位置 | 否，当前 scaffold |
| `reports/audits` | 未来审计/诊断报告分组镜像位置 | 否，当前 scaffold |
| `reports/manual_review` | 未来人工复核报告分组镜像位置 | 否，当前 scaffold |
| `reports/dry_run` | 未来 dry-run 报告分组镜像位置 | 否，当前 scaffold |

## Eval 与回归报告

这些文件回答“RAG / 风控 / 场景评测现在表现如何”。

- `tests/rag_eval_report.json`：RAG 主评测报告，包含问题、LLM 输出、证据链、风险字段和评测结果。
- `tests/risk_eval_report.json`：风险引擎评测报告。
- `tests/report_eval_report.json`：报告层评测报告。
- `tests/smoke_eval_report.json`：smoke 评测报告。
- `tests/targeted_eval_report.json`：定向小集合评测报告。
- `tests/scenario_eval_report.json`：scenario registry 相关场景评测报告。
- `tests/scenario_eval_summary.md`：scenario eval 摘要。
- `tests/impact_eval_report.json`：影响面评测报告。
- `tests/rag_stability_report.json`：稳定性评测报告。
- `tests/rag_stability_summary.md`：稳定性评测摘要。
- `tests/rerank_on.json`、`tests/rerank_off.json`：rerank 对照实验产物，不是配置开关。
- `tests/rag_eval_cases.json`、`tests/smoke_eval_cases.json`：评测输入题库，不是输出报告。

未来镜像分组：`reports/eval`。

## Evidence 与检索质量诊断

这些文件回答“证据链为什么不够好、问题可能出在哪一层”。

- `tests/evidence_alignment_report.json`：答案与 evidence_chain 的对齐诊断。
- `tests/evidence_coverage_report.json`：主要争点、证据覆盖和缺口诊断。
- `tests/evidence_coverage_triage_report.json`：coverage loss 的分流/优先级报告。
- `tests/evidence_coverage_gate_draft_report.json`：coverage gate 草案。
- `tests/evidence_root_cause_action_plan.json`：证据问题根因与动作计划草案。
- `tests/evidence_action_series_baseline.json`：后续 action series 的基线材料。
- `tests/evidence_enrichment_hardening_report.json`：证据 enrichment hardening 检查报告。
- `tests/evidence_fixture_candidate_pool.json`：fixture 候选池，不等于已进入 eval case。
- `tests/base_retrieval_quality_audit_report.json`：基础召回质量审计。
- `tests/anchor_dependency_audit_report.json`：anchor 依赖审计。
- `tests/final_evidence_selection_audit_report.json`：最终证据选择流失审计。
- `tests/qdrant_index_integrity_report.json`：索引完整性检查报告。
- `tests/ingestion_quality_report.json`：入库质量检查报告。
- `tests/scenario_registry_calibration_report.json`：scenario registry coverage calibration 报告。
- `tests/rule_debt_report.json`：规则债审计报告。

未来镜像分组：`reports/audits`。

## Legal Functional Typing

这些文件回答“法律条款的功能类型识别是否稳定”。

- `tests/legal_functional_typing_report.json`：法律功能类型识别报告。
- `tests/legal_functional_type_config_report.json`：功能类型配置 gate 报告。
- `tests/legal_functional_typing_error_analysis_report.json`：错误分析报告。
- `tests/legal_functional_typing_fixture_report.json`：fixture 检查报告。
- `tests/fixtures/legal_functional_typing_golden.json`：golden fixture 数据。

这类产物属于 RAG grounding 基建，不是针对单个 hidden seed 的修补工具。

## Manual Review 与治理闭环

这些文件回答“哪些 case 需要人看、人看完能不能进入工程修复”。

- `tests/evidence_manual_review_dataset.json`：从证据诊断中抽取出的人工复核数据集。
- `tests/evidence_manual_review_workbench.json`：人工复核工作台数据源。
- `tests/evidence_manual_review_workbench.csv`：工作台表格辅助输出，仅供人工阅读/核对，不作为正式 importer 输入。
- `tests/evidence_manual_review_decision_schema.json`：正式人工复核 decision schema。
- `tests/evidence_manual_review_decision_validation_report.json`：正式人工复核 decision schema 校验报告。
- `tests/evidence_manual_review_action_candidates.json`：人工复核 action candidates 报告。
- `tests/evidence_manual_review_loop_report.json`：人工复核 loop 报告。
- `tests/proposed_manual_review_decision_schema.json`：拟议人工复核 decision schema。
- `tests/manual_review_decision_examples.json`：人工复核 decision examples。
- `tests/manual_review_intake_contract_report.json`：人工复核 intake contract 报告。
- `tests/manual_review_prescreen_report.json`：人工复核前的离线预筛报告。
- `tests/manual_review_pilot_batch_report.json`：首批 pilot case 审阅包。
- `tests/manual_review_pilot_case_review_assist_report.json`：pilot case 只读审阅辅助。
- `tests/pilot_manual_review_round1_support_report.json`：Round 1 逐案支持包。
- `tests/mobile_pilot_review_decision_aid_report.json`：手机端压缩审阅卡片。
- `tests/manual_review_visual_workbench_build_report.json`：离线视觉工作台构建报告。
- `tests/manual_review_visual_workbench_contract_report.json`：视觉工作台契约报告。
- `tests/manual_review_workbench_import_report.json`：workbench 导入报告。
- `tests/manual_review_decision_diff_report.json`：人工 decision diff 报告。
- `tests/proposed_manual_review_decision_validation_report.json`：拟议 decision 校验报告。
- `tests/validated_decision_promotion_dry_run_report.json`：validated decision promotion dry-run 报告。
- `tests/manual_review_intake_gate_closeout_report.json`：当前治理 gate closeout 报告。
- `tests/evidence_manual_review_progress_report.json`：人工复核进度报告。
- `tests/evidence_manual_review_governance_report.json`：人工复核治理报告。

未来镜像分组：`reports/manual_review`。

## Dry-Run 与安全隔离产物

这些文件回答“某个导出或建议稿误进入治理链路时会不会被拦住”。

- `tests/manual_review_export_pipeline_dry_run_report.json`：export pipeline dry-run 总报告。
- `tests/manual_review_export_pipeline_dry_run_artifacts/`：dry-run 中间产物目录，避免覆盖正式报告。
- `tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json`：AI suggestion prefill 建议稿，只作辅助材料。
- `tests/manual_review_ai_suggestion_prefill_import_safety_check.json`：AI suggestion 导入安全检查。
- `tests/manual_review_prefill_high_confidence_12.json`、`tests/manual_review_prefill_high_confidence_12.csv`：legacy prefill 辅助稿。
- `tests/manual_review_prefill_high_confidence_12_import_report.json`：legacy prefill 导入报告。
- `tests/manual_review_prefill_high_confidence_12_v2.json`、`tests/manual_review_prefill_high_confidence_12_v2.csv`：v2 prefill 辅助稿。
- `tests/manual_review_prefill_high_confidence_12_v2_import_report.json`：v2 prefill 导入报告。
- `tests/proposed_manual_review_decision_schema_ai_suggestion_safety_check.json`：AI suggestion proposed schema 安全检查。
- `tests/proposed_manual_review_decision_schema_prefill_high_confidence_12.json`：legacy prefill proposed schema。
- `tests/proposed_manual_review_decision_schema_prefill_high_confidence_12_v2.json`：v2 prefill proposed schema。
- `tests/proposed_manual_review_validation_prefill_high_confidence_12.json`：legacy prefill proposed validation。
- `tests/proposed_manual_review_validation_prefill_high_confidence_12_v2.json`：v2 prefill proposed validation。
- `tests/ready_action_routing_dry_run_report.json`：ready action routing dry-run 报告。
- `tests/ready_action_human_closeout_confirmation_record_report.json`：人工收口确认记录，可作为未来设计规划输入，但不是 importer completed decision、不授权实现。
- `tests/final_evidence_selection_policy_intake_report.json`：最终证据选择策略设计 intake 报告，只整理设计输入，不实现策略、不改 rerank、不接主流程。
- `tests/final_evidence_selection_policy_simulator_spec_report.json`：最终证据选择策略 saved-report simulator spec 报告，只定义模拟器契约、质量信号和人工复核 gate，不实现 runtime policy、不改 rerank/prompt/eval、不接主流程。
- `tests/final_evidence_selection_policy_table_draft_report.json`：最终证据选择策略表草案报告，只整理人工可审阅 policy rows，不实现 runtime policy、不改 rerank/prompt/eval、不接主流程。
- `tests/final_evidence_selection_policy_human_review_worksheet_report.json`：最终证据选择策略人工复核 worksheet，只整理 review questions、acceptance checks 和 discussion options，不记录正式人工结论、不授权实现。
- `tests/ready_action_human_closeout_decision_draft_report.json`：待用户确认的人工收口草案报告，不是正式人工结论、不可导入 importer、不授权实现。
- `tests/ready_action_design_review_closeout_report.json`：设计评审 closeout envelope 报告，只供人工收口讨论，不记录正式结论、不授权实现。
- `tests/ready_action_design_review_worksheet_report.json`：设计复核 worksheet 报告，只供人工评审会讨论，不授权实现。

未来镜像分组：`reports/dry_run`。

## Health Check 与结构维护

这些文件回答“当前项目边界、目录脚手架和离线工具是否仍保持安全”。

- `tests/project_health_check_report.json`：项目轻量健康检查报告。
- `tests/encoding_hygiene_report.json`：编码与临时产物卫生审计报告。
- `tests/tool_index_consistency_report.json`：工具索引覆盖与敏感入口诊断报告。
- `tests/test_index_consistency_report.json`：测试索引覆盖诊断报告。
- `tests/artifact_index_consistency_report.json`：产物索引覆盖诊断报告。
- `tests/layout_migration_readiness_report.json`：目录迁移准备度诊断报告。
- `tests/maintenance_closeout_report.json`：维护系列收束报告。
- `tools/run_project_health_check.py`：健康检查工具。
- `tools/check_encoding_hygiene.py`：编码卫生检查工具，只输出报告，不修改或删除被扫描文件。
- `tools/check_tool_index_consistency.py`：工具索引一致性检查工具，只输出报告，不移动工具、不改默认路径。
- `tools/check_test_index_consistency.py`：测试索引一致性检查工具，只输出报告，不移动测试文件。
- `tools/check_artifact_index_consistency.py`：产物索引一致性检查工具，只输出报告，不迁移报告。
- `tools/check_layout_migration_readiness.py`：目录迁移准备度检查工具，只输出报告，不移动文件。
- `tools/build_maintenance_closeout_report.py`：维护系列收束报告工具，只汇总既有维护报告。
- `docs/project_health_check_maintenance_2026-05-13.md`：健康检查维护说明。
- `docs/project_layout_compatibility_layer_2026-05-13.md`：路径兼容层说明。
- `docs/project_structure_refactor_plan.md`：后续目录整理计划。
- `docs/indexes/project_structure_index.md`：结构维护索引。
- `docs/indexes/project_artifact_index.md`：本文档。

健康检查不会运行 full eval，不调用 `rag_query`，不连接后端、Qdrant 或 LLM。

## 工具入口与产物关系

当前大多数工具入口仍在 `tools/*.py` 根目录。新增的 `tools/eval`、`tools/evidence_diagnostics`、`tools/manual_review`、`tools/ops`、`tools/ingestion` 只是未来分组脚手架，不代表工具已经迁移。

常见关系：

- `tools/run_rag_eval.py` 读取 eval case，输出 `tests/rag_eval_report.json` 或调用方指定的 eval 报告。
- `tools/check_evidence_alignment.py` 读取已有 eval report，输出 `tests/evidence_alignment_report.json`。
- `tools/check_evidence_coverage.py` 读取已有 eval report，输出 `tests/evidence_coverage_report.json`。
- `tools/build_manual_review_visual_workbench.py` 读取治理报告，生成 `tools/manual_review_visual_workbench/index.html` 和 `tests/manual_review_visual_workbench_build_report.json`。
- `tools/import_manual_review_workbench.py` 只接受正式 filled visual workbench export，输出 `tests/manual_review_workbench_import_report.json`。
- `tools/build_manual_review_export_pipeline_dry_run.py` 使用隔离目录预演导出链路，输出 `tests/manual_review_export_pipeline_dry_run_report.json`。
- `tools/build_ready_action_design_review_worksheet.py` 读取设计评审 gate/brief，输出 `tests/ready_action_design_review_worksheet_report.json` 与 `docs/ready_action_design_review_worksheet_v0.4.7.9.3.md`。
- `tools/build_ready_action_design_review_closeout.py` 读取设计复核 worksheet，输出 `tests/ready_action_design_review_closeout_report.json` 与 `docs/ready_action_design_review_closeout_v0.4.7.9.4.md`。
- `tools/build_ready_action_human_closeout_decision_draft.py` 读取设计评审 closeout envelope，输出 `tests/ready_action_human_closeout_decision_draft_report.json` 与 `docs/ready_action_human_closeout_decision_draft_v0.4.7.9.5.md`。
- `tools/build_ready_action_human_closeout_confirmation_record.py` 读取人工收口确认草案，输出 `tests/ready_action_human_closeout_confirmation_record_report.json` 与 `docs/ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md`。
- `tools/build_final_evidence_selection_policy_intake.py` 读取人工收口确认记录、设计包和 final selection audit，输出 `tests/final_evidence_selection_policy_intake_report.json` 与 `docs/final_evidence_selection_policy_intake_v0.4.8.0.md`。
- `tools/build_final_evidence_selection_policy_simulator_spec.py` 读取 v0.4.8.0 intake、final selection audit 和 confirmation record，输出 `tests/final_evidence_selection_policy_simulator_spec_report.json` 与 `docs/final_evidence_selection_policy_simulator_spec_v0.4.8.1.md`。
- `tools/build_final_evidence_selection_policy_table_draft.py` 读取 v0.4.8.1 simulator spec 与既有 saved reports，输出 `tests/final_evidence_selection_policy_table_draft_report.json` 与 `docs/final_evidence_selection_policy_table_draft_v0.4.8.2.md`。
- `tools/build_final_evidence_selection_policy_human_review_worksheet.py` 读取 v0.4.8.2 policy table draft saved report，输出 `tests/final_evidence_selection_policy_human_review_worksheet_report.json` 与 `docs/final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md`。
- `tools/run_project_health_check.py` 输出 `tests/project_health_check_report.json`。
- `tools/check_tool_index_consistency.py` 输出 `tests/tool_index_consistency_report.json`。
- `tools/check_test_index_consistency.py` 输出 `tests/test_index_consistency_report.json`。
- `tools/check_artifact_index_consistency.py` 输出 `tests/artifact_index_consistency_report.json`。
- `tools/check_layout_migration_readiness.py` 输出 `tests/layout_migration_readiness_report.json`。
- `tools/build_maintenance_closeout_report.py` 输出 `tests/maintenance_closeout_report.json`。

## 维护规则

- 新增报告时，优先写清楚它是 eval、audit、manual review、dry-run、schema、fixture 还是 docs。
- 新增重要产物后，应更新本文档的对应类别。
- 不要把 AI suggestion、prescreen、pilot assist、mobile aid 写成 completed manual decision。
- 不要把 `tests/evidence_fixture_candidate_pool.json` 写成已经进入 eval case。
- 不要把 `reports/` scaffold 写成当前权威输出目录。
- 若将来真的迁移目录，必须先有兼容读取、双输出或明确 fallback，并同步更新 health check。
