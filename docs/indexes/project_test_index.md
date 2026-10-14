# 项目测试资产索引
## v0.5.2 Controlled Experiment and Runtime addendum

- `tests/test_judge_controlled_ablation.py`、`tests/test_judge_core_tech_experiments.py`：C0-C6 控制变量、冻结输入、裁判汇总与实验口径回归。
- `tests/test_robustness_perturbation_cases.py`：人工成对改写集的结构、配对关系和扰动类型覆盖检查。
- `tests/test_llm_provider_adapters.py`：OpenAI-compatible、Anthropic Messages、Gemini Generate Content 适配器请求与响应归一化测试。
- `tests/test_external_risk_api.py`、`tests/test_runtime_settings_api.py`、`tests/test_document_ingest.py`、`tests/test_developer_debug_api.py`：补充期货情报、运行时提供方选择、文档解析兼容与 API 异步边界回归。

## User-Defined Skill addendum

- `tests/test_skills.py`：固定节点 DAG、参数边界、内置模板不可编辑/删除、JSON 持久化、CRUD 与通过 `/ask` 主链路的真实 Skill 运行集成测试。
- `tests/test_skill_frontend_contract.py`：我的技能导航、编辑器、公开接口、节点字段与六节点上限的静态前后端契约测试。
- `tests/test_skill_acceptance_evidence.py`：离线构建 Skill 实现证据并验证其可被 Skill 裁判接受。
- `tests/test_judge_skill_module.py`：Skill 裁判对正常、未知节点、环路和内置模板保护失败的回归测试。

## RAG Evidence and Figure addendum

- `tests/test_core_tech_report_artifacts.py`：核心技术报告、ESG 流程和消融/裁判材料的一致性测试。
- `tests/test_evidence_sufficiency.py`、`tests/test_judge_evidence_sufficiency.py`：ESG 分数、路由与正式/冒烟检索指标资格测试。
- `tests/test_research_figure_assets.py`：科研图表的 2400×1350、300 dpi、RGB/RGBA 与文件完整性测试。
- `tests/test_web_search.py`：受控联网检索配置、来源边界和接口测试。

## v0.5.0 RAG Quality Runtime addendum

- `tests/test_answer_generation.py`：答案模式计划的结构、可用引文和检索缺口提示单测。
- `tests/test_legal_concepts.py`：声明式法律概念识别、法域路由、查询扩展、直接法源映射和缺口提示单测。
- `tests/test_rag_eval_metrics.py`：Evidence Recall@K、MRR、nDCG、多来源覆盖和延迟汇总指标单测。
- `tests/test_retrieval_ablation_profiles.py`：四档仅检索消融 profile 的开关隔离与未知 profile 拒绝单测。
- `tests/test_legal_appendix_ingestion.py`：紧凑条文和法律附表的独立切分、元数据及引用边界单测。
- `tests/test_answer_policy.py`、`tests/test_complex_case_eval_cases.py`、`tests/test_civil_code_coverage.py`：回答策略、复杂案例和民法典覆盖回归。
- `tests/test_developer_debug_api.py`、`tests/test_document_ingest.py`、`tests/test_frontend_backend_routing.py`、`tests/test_external_risk_api.py`、`tests/test_internal_risk_api.py`、`tests/test_internal_risk_service.py`、`tests/test_risk_intake_api.py`、`tests/test_risk_intake_service.py`、`tests/test_runtime_settings_api.py`、`tests/test_supply_chain_api.py`：已存在的产品/后端接口回归测试索引补齐；本次仅补充索引，不改变这些测试的行为。

## v0.4.18.9 Product Backend Closeout addendum

- `tests/test_product_backend_closeout.py`：product backend closeout/runbook 单测，验证当前后端设计收口状态、交接清单、未来 provider 接入顺序和缺失产物阻断逻辑。
- `tests/product_backend_closeout_v0.4.18.9_report.json`：product backend closeout 交接报告。

## v0.4.18.8 Product Data Source Boundary addendum

- `tests/test_product_data_source_boundary.py`：product backend repository boundary 单测，覆盖 service 通过 repository 读取、fixture 版本漂移 fail closed、未来 provider 槽位只登记不接入。
- `tests/product_data_source_boundary_v0.4.18.8.json`：product data source boundary 导出目录。

## v0.4.18.7 Product API Status Catalog addendum

- `tests/test_product_api_status_catalog.py`：product API status/error catalog 单测。
- `tests/product_api_status_catalog_v0.4.18.7.json`：fixture-backed product API 状态与错误目录。

## v0.4.18.6 Product API Field Catalog addendum

- `tests/test_product_api_field_catalog.py`：product API field catalog 单测。
- `tests/product_api_field_catalog_v0.4.18.6.json`：fixture-backed product API 字段目录。

## v0.4.18.5 Product API Backend Integration addendum

- `tests/test_product_api_contract.py`：fixture-backed `/product/*` FastAPI 接口契约单测。
- `tests/product_api_contract_v0.4.18.5_report.json`：product API contract 校验报告。

## v0.4.18.4 Product Mock Endpoint Contract addendum

- `tests/test_product_mock_endpoint_contract.py`：product mock endpoint contract checker 单测。
- `tests/product_mock_endpoint_contract_v0.4.18.4_report.json`：product mock endpoint contract 校验报告。

## v0.4.18.3 Product View Model Contract addendum

- `tests/test_product_view_model_contract.py`：product view model contract checker 单测。
- `tests/fixtures/product_view_models_v0.4.18.3.json`：产品 view model fixture。
- `tests/product_view_model_contract_v0.4.18.3_report.json`：产品 view model contract 校验报告。

## v0.4.18.1 Legal Corpus Integrity Baseline addendum

- `tests/test_legal_corpus_integrity.py`：legal corpus integrity checker 单测。
- `tests/legal_corpus_integrity_v0.4.18.1_report.json`：法规扩容前的本地 corpus integrity 基线报告。

## v0.4.17.7 RAG Full Eval Closeout addendum

- `tests/rag_eval_report_v0.4.17.7.json`：当前 RAG 主链路 full eval 收口报告；唯一失败仍为 `risk_unfair_competition_confusion_001` 的 expected-level/fact-strength 复核项。

## v0.4.17.6 Unfair Competition Confusion Metadata Patch addendum

- `tests/rag_expected_level_review_packet_v0.4.17.6_report.json`：修正旧编号文字后，metadata warning 清零但 fixed failure 仍分类为 expected-level/fact-strength review。
- `tests/legal_text_version_verification_packet_v0.4.17.6_report.json`：修正后分类为 `current_law_evidence_valid`。

## v0.4.17.5 Legal Text Version Verification addendum

- `tests/test_legal_text_version_verification_packet.py`：法律文本版本核验单测，覆盖现行第七条证据有效、旧第六条表述漂移和映射异常分流。
- `tests/legal_text_version_snapshot_v0.4.17.5.json`：联网核验后固化的法律文本版本快照。
- `tests/legal_text_version_verification_packet_v0.4.17.5_report.json`：法律文本版本核验报告。

## v0.4.17.4 RAG Expected-Level Review Packet addendum

- `tests/test_rag_expected_level_review_packet.py`：expected-level review packet 单测，覆盖风险等级单点失败、检索失败分流和其他输出检查失败分流。
- `tests/rag_expected_level_review_packet_v0.4.17.4_report.json`：固定失败分类报告，结论为 expected-level/fact-strength review，不建议 runtime patch。

## v0.4.17.3 RAG Targeted Repeat Closeout addendum

- `tests/targeted_rag_evidence_independence_v0.4.17.3_report.json`：17 个 case、3 轮 targeted repeat 报告；每轮 retrieval stage 均为 `PASS=17`，固定失败为 expected-level/fact-strength 复核项。

## v0.4.17.2 RAG Targeted Rerun Packet addendum

- `tests/test_rag_targeted_rerun_packet.py`：targeted rerun packet 单测，覆盖候选分组、失败 case 分流、控制组和非 runtime patch 结论。
- `tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`：只读候选包报告，提供下一轮 bounded targeted repeat 的 case 列表和建议命令。

## v0.4.17.1 RAG Evidence Independence Baseline addendum

- `tests/test_rag_evidence_independence_baseline.py`：主链路证据独立性基线单测，覆盖依赖桶、失败 case 分流、优先级列表和通用诊断逻辑。
- `tests/rag_evidence_independence_baseline_v0.4.17.1_report.json`：saved-report-only 依赖归因基线报告，不运行 eval、不调用 RAG/Qdrant/LLM。

## v0.4.16.11 API Contract Consistency Checker addendum

- `tests/test_api_contract_consistency.py`：离线 API 契约一致性测试，覆盖 OpenAPI schema、bundle、field catalog 与 example payload 之间的字段、必填项、路由引用和 guardrails 对齐。
- `tests/api_contract_consistency_v0.4.16.11_report.json`：API contract consistency checker 报告，属于 schema/fixture 诊断类资产，不运行 RAG、Qdrant、LLM 或 full eval。
- `tests/test_api_contract.py`：清理重复 field catalog 测试定义，保留既有 API contract 回归覆盖。

## v0.4.16.10 API Field Catalog addendum

- `tests/api_field_catalog_v0.4.16.10.json`：离线 API field catalog 产物，覆盖请求/响应模型字段、必填项和默认值，供前端表单和展示映射使用。
- `tests/test_api_contract.py`：新增 field catalog 校验。

## v0.4.16.9 API Error Example Contract addendum

- `tests/api_contract_bundle_v0.4.16.9.json`：包含成功 payload 和 422/504/500 错误状态样例的离线 API contract bundle。
- `tests/test_api_contract.py`：新增 `/ask` timeout mock 与 bundle 错误样例校验。

## v0.4.16.8 API Contract Bundle addendum

- `tests/api_contract_bundle_v0.4.16.8.json`：离线 API contract bundle 产物，合并当前 OpenAPI schema 与 example payload fixture，供前端/工作台联调用。
- `tests/test_api_contract.py`：新增 bundle 校验，确认 bundle 同时包含 schema、example payload 与 guardrails。

## v0.4.16.7 Roadmap Next-Step Hygiene addendum

- `tests/test_roadmap_hygiene.py`：检查 `docs/project_review_and_roadmap.md` 的 `## 推荐下一步` 不得包含已完成版本流水账，防止 roadmap 再次膨胀。

## v0.4.16.6 API Endpoint Smoke Contract addendum

- `tests/test_api_contract.py`：新增 `/ask`、`/risk/analyze`、`/risk/report` 的 `TestClient + mock` endpoint smoke contract，验证路由入口、响应契约和请求过滤参数透传；不调用真实 RAG、Qdrant、LLM 或报告生成。

## v0.4.16.5 Roadmap and Final Report Maintenance addendum

- `tests/project_health_check_report.json`：记录 v0.4.16.5 文档治理与版本一致性 health check 结果。
- `tests/encoding_hygiene_report.json`：记录 v0.4.16.5 后的 UTF-8/乱码卫生检查结果。

## v0.4.16.4 API Example Payload Fixture addendum

- `tests/test_api_contract.py`：新增 API example payload fixture 契约校验，确认 `/ask`、`/risk/analyze`、`/risk/report` 与 `/risk/report/export` 样例可通过现有 Pydantic 模型和最小导出结构检查。
- `tests/fixtures/api_contract_example_payloads_v0.4.16.4.json`：前端接入前的离线 API example payload fixture；不调用 RAG、Qdrant、LLM 或真实报告生成。

## v0.4.16.1 API Contract Baseline addendum

- `tests/test_api_contract.py`：离线覆盖 FastAPI 核心路径、请求默认值、响应必需字段、统一错误响应结构、`/risk/report/export` Markdown/JSON 内容类型，以及 OpenAPI schema 快照 guardrails；不调用 RAG、Qdrant 或 LLM。
- `tests/openapi_schema_v0.4.16.3.json`：由 `tools/export_openapi_schema.py` 生成的 OpenAPI schema 快照产物。

## v0.4.15.26 Process Over-Risk Runtime Hardening addendum

- `tests/test_retriever_contract.py`：新增物业公共区域 medium cap、严重侵占负例、缺少业主同意缺口负例、股权转让未通知 cap、上市/国资/司法执行/质押/欺诈伪造负例、VAT 混合销售 cap、VAT 虚开/故意拒不补缴负例，以及商标权滥用措辞稳定性覆盖。
- `tests/targeted_process_overrisk_trace_v0.4.15.26_report.json`：修复前程序/民事管理 over-risk 定位产物。
- `tests/targeted_process_overrisk_patch_v0.4.15.26_report.json`：修复后程序/民事管理目标 eval 产物，2/2 passed。
- `tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json`：商标 hardening 回归 eval 产物，2/2 passed。
- `tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json`：VAT 混合销售目标和高风险负例回归 eval 产物，5/5 passed。
- `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json`：compact full eval 产物，59/60 passed，retrieval `PASS=60`。

## v0.4.15.25 Trademark Over-Risk Runtime Patch addendum

- `tests/test_retriever_contract.py`: extends retriever contract coverage for trademark generic-name and non-use `high -> medium` calibration, plus an infringement/confusion negative case that must remain high.
- `tests/targeted_trademark_overrisk_trace_v0.4.15.25_report.json`: pre-patch targeted trace artifact for two trademark over-risk cases.
- `tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json`: post-patch targeted eval artifact, 2/2 passed.
- `tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json`: compact full eval artifact, 56/60 passed.

## v0.4.15.24 Risk Level Over-Risk Legal Review Packet addendum

- `tests/test_risk_level_overrisk_legal_review_packet.py`: covers generic over-risk legal review logic for trademark non-use, tax underpayment boundary cases, clean no-overrisk status, attribution preservation, expected evidence refs, and `rule_change_allowed=false`.
- `tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json`: saved-report-only legal review packet artifact for exact-policy over-risk cases.

## v0.4.15.23 Risk Level Over-Risk Attribution addendum

- `tests/test_risk_level_overrisk_attribution.py`: covers output-rule amplification, taxonomy/LLM wording routing, no-overrisk clean status, confidence and review fields.
- `tests/risk_level_overrisk_attribution_v0.4.15.23_report.json`: saved-report-only attribution artifact for exact-policy over-risk cases.

## v0.4.15.22 Risk Level Exact Policy addendum

- `tests/test_rag_eval_diagnostics.py`: covers exact risk-level policy, `over_risk`/`under_risk` classification, and mismatch summary aggregation.
- `tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json`: targeted exact-policy validation artifact.
- `tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json`: compact full eval artifact under exact risk-level policy.

## v0.4.15.21 Base Candidate Depth Runtime Patch addendum

- `tests/test_candidate_budget.py`: covers the conservative runtime candidate budget constants for sparse/base union/rerank input/base quota/anchor quota.
- `tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json`: targeted runtime validation artifact, 7/7 passed.
- `tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json`: compact full RAG eval artifact, 60/60 passed.

## v0.4.15.20 Base Candidate Dense Live Probe addendum

- `tests/test_base_candidate_dense_live_probe.py`: covers that the wrapper forces dense probing, updates schema/version, and records explicit dense-probe guardrails.
- `tests/base_candidate_dense_live_probe_v0.4.15.20_report.json`: explicit dense-enabled live probe artifact.

## v0.4.15.19 Base Candidate Live Read-Only Probe addendum

- `tests/test_base_candidate_live_readonly_probe.py`: covers payload absence, metadata-filter exclusion, sparse high-k rank cutoff, no Qdrant writes, and default dense-probe suppression.
- `tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json`: live read-only Qdrant probe artifact.

## v0.4.15.18 Base Candidate Mismatch Summary addendum

- `tests/test_base_candidate_mismatch_summary.py`: covers source/article drift classification, final refs already present in union, empty inspection lists, and mixed final-ref cases.
- `tests/base_candidate_mismatch_summary_v0.4.15.18_report.json`: saved-report base candidate mismatch summary artifact.

## v0.4.15.17 Base Retrieval / Query Inspection addendum

- `tests/test_base_retrieval_query_inspection.py`: covers anchor-filled final ref classification and manual-review/output-rule classification.
- `tests/base_retrieval_query_inspection_v0.4.15.17_report.json`: saved-report base retrieval/query inspection artifact.

## v0.4.15.16 Dependency Trace Summary addendum

- `tests/test_dependency_trace_summary.py`: covers dependency reason classification for anchor-filled base retrieval gaps and manual-review/output-rule dependency.
- `tests/targeted_dependency_trace_v0.4.15.16_report.json`: non-compact targeted full-debug trace artifact.
- `tests/dependency_trace_summary_v0.4.15.16_report.json`: saved-report dependency trace summary artifact.

## v0.4.15.15 RAG Quality Triage addendum

- `tests/test_rag_quality_triage.py`: covers dependency classification, quality-risk priority, and ranked triage ordering.
- `tests/rag_quality_triage_v0.4.15.15_report.json`: saved-report quality triage artifact.

## v0.4.15.14 Roadmap Maintenance & Compact Eval Baseline addendum

- `tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json`: compact full RAG eval baseline, 60/60 passed with retrieval `PASS=60`.

## v0.4.15.13 RAG Eval Compact Report Profile addendum

- `tests/test_rag_eval_diagnostics.py`: covers compact debug summary, compact case reports, and compact single/repeat report profiles.
- `tests/targeted_compact_report_profile_v0.4.15.13_report.json`: focused compact-profile smoke artifact.

## v0.4.15.12 Same-Bucket Signal Calibration addendum

- `tests/test_rag_eval_diagnostics.py`: covers same-bucket risk preservation and observation-only suppression boundaries.
- `tests/targeted_same_bucket_baseline_v0.4.15.12_report.json`: targeted baseline artifact.
- `tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json`: baseline full eval artifact.
- `tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json`: calibrated full eval artifact.
- `tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json`: focused output-stability artifact.

## v0.4.15.11 Hidden-Seed Signal Diagnostics & Output Stability addendum

- `tests/test_rag_eval_diagnostics.py`: 新增 `quality_signal_diagnostics` 单测，覆盖 ref 映射、known-bad 泄漏、污染领域、定义替代规范条款、主争点缺证据和同桶选择顺序风险。
- `tests/test_retriever_contract.py`: 新增产品责任术语保留、商标通用名称最低风险、违法分红措辞保留、股权转让未通知最低风险测试。
- `tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json`: 产品责任 focused repeat artifact。
- `tests/targeted_output_stability_v0.4.15.11_report.json`: 输出稳定性 targeted repeat artifact。
- `tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json`: 带 `quality_signal_diagnostics` 的 full RAG eval artifact。

## v0.4.15.10 Standard Contract Term Preservation addendum

- `tests/test_retriever_contract.py`: adds standard-contract reassessment term-preservation coverage and a negative source-boundary test.
- `tests/targeted_data_export_term_preservation_v0.4.15.10_report.json`: focused repeat artifact for `data_export_contract_trigger_001`.
- `tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json`: targeted stability packet after the term preservation patch.
- `tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json`: full RAG eval artifact; 60/60 passed.

## v0.4.15.9 Main-Chain Stability Closeout addendum

- `tests/targeted_main_chain_stability_v0.4.15.9_report.json`: targeted stability validation artifact covering eight recent/high-risk cases across three repeats.
- `tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json`: single full RAG eval artifact; retrieval stage remains all pass.
- `tests/targeted_data_export_answer_stability_v0.4.15.9_report.json`: focused repeat artifact for the only full-eval wording miss.

## v0.4.15.8 Main-Chain Repair addendum

- `tests/test_candidate_budget.py`: adds coverage that same-bucket stabilization must not reorder large buckets.
- `tests/test_taxonomy.py`: adds coverage that a structured canonical taxonomy risk type name can trigger risk-level inference.
- `tests/test_risk_analyzer.py`: covers risk analyzer upgrade from medium to high when structured `risk_types` already contains the canonical high-risk taxonomy name.
- `tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json`: final full RAG eval validation artifact; 60/60 passed.

## v0.4.15.7 Near-Tie Patch Closeout addendum

- `tests/test_post_rebuild_near_tie_patch_closeout.py`: covers default paths, closeout guardrails, clean saved-report closeout, fail-closed missing validation, unstable evidence identity, health failure, Markdown boundary, and CLI output.
- `tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json`: v0.4.15.7 closeout output; current status is `closed_for_next_real_rag_quality_task`.
- Existing v0.4.15.6 validation tests remain the runtime patch validation layer; this version only closes the saved-report loop.

## v0.4.15.6 Near-Tie Runtime Patch Validation addendum

- `tests/test_candidate_budget.py`: covers same-bucket deterministic ordering, input-order independence inside a bucket, and preserved Cross-Encoder bucket priority across buckets.
- `tests/test_post_rebuild_near_tie_patch_validation.py`: covers default paths, guardrails, final selection trace parsing, stable/unstable repeat decisions, missing repeat report fail-closed behavior, and CLI output.
- `tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json`: v0.4.15.6 validation output; current status is passed after the real targeted repeat report was generated.

## v0.4.15.5 Post-Rebuild Near-Tie Stability Policy Design 补充

- `tests/test_post_rebuild_near_tie_stability_policy_design.py`: 验证 near-tie policy design builder 的默认路径、guardrails、错误分类阻断、真实 v0.4.15.4 attribution 解析、Markdown 边界和 CLI 写出。
- `tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json`: v0.4.15.5 design-only 输出，状态为 `ready_for_near_tie_policy_review`。

## v0.4.15.4 Post-Rebuild Selection Trace Attribution 补充

- `tests/test_post_rebuild_selection_trace_attribution.py`: 验证 trace attribution builder 的默认路径、guardrails、synthetic drift attribution、真实 v0.4.15.4 trace report 解析、Markdown 边界和 CLI 写出。
- `tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json`: `risk_algorithm_bias_001` 5 轮 targeted repeat trace capture 原始报告。
- `tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json`: v0.4.15.4 saved trace attribution 输出，状态为 `needs_near_tie_stability_design`。

## v0.4.15.3 Post-Rebuild Selection Trace Readiness 补充

- `tests/test_post_rebuild_selection_trace_readiness.py`: 验证 readiness builder 的默认路径、guardrails、trace 字段、synthetic selector 行为边界和 Markdown 输出。
- `tests/test_candidate_budget.py`: 新增 debug trace helper 覆盖，确认 full rerank order 能保留 input/rerank rank，final selection trace 能展示 selected/not_selected 且不改变 selector 结果。
- `tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json`: v0.4.15.3 readiness 输出，状态为 `passed`。

## v0.4.15.2 Post-Rebuild Final Evidence Drift Attribution 补充

- `tests/test_post_rebuild_final_evidence_drift_attribution.py`: 验证 attribution builder 的双候选进入 rerank input 后第三席漂移、无漂移通过、真实报告解析和 Markdown 边界。
- `tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json`: v0.4.15.2 saved-report attribution 输出，状态为 `needs_selector_stability_design`。

## v0.4.15.1 Post-Rebuild Repeat Instability Triage 补充

- `tests/test_post_rebuild_repeat_instability_triage.py`: 验证 targeted triage builder 的输出措辞波动非阻断、final evidence identity drift 阻断、真实 targeted repeat 报告解析和 Markdown 边界。
- `tests/targeted_repeat_product_liability_v0.4.15.1_report.json`: 产品责任 case 5 轮 targeted repeat 原始报告，结果为 5/5 passed。
- `tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json`: 算法偏见 case 5 轮 targeted repeat 原始报告，结果为 5/5 passed，但 final evidence identity drift 复现。
- `tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json`: v0.4.15.1 saved-report triage 输出，状态为 `needs_evidence_stability_triage`。

## v0.4.15.0 Post-Rebuild Repeat Stability Summary 补充

- `tests/test_post_rebuild_repeat_stability_summary.py`: 验证 repeat summary builder 的 clean repeat、59/60 输出波动、证据身份漂移、citation 展示差异不误报、case set drift、dense fallback drift、真实报告解析和 Markdown 边界。
- `tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json`: 授权运行的 3 轮 full RAG eval repeat 原始报告，结果为 `[60, 60, 59]`。
- `tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json`: v0.4.15.0 saved-report summary 输出，状态为 `needs_triage`。

## v0.4.14.35 Production Rebuild / Post-Rebuild Series Closeout 补充

- `tests/test_production_rebuild_post_rebuild_series_closeout.py`: 验证 closeout builder 的真实输入收口、saved-report-only guardrails、缺失输入阻断、最终 full eval drift 阻断、初次回归 lineage 要求、delta removed expected evidence 阻断和 Markdown 边界。
- `tests/production_rebuild_post_rebuild_series_closeout_report.json`: v0.4.14.35 closeout 输出；状态为 `closed_for_next_real_rag_quality_task`，用于证明 v0.4.14 production rebuild / post-rebuild RAG 质量链条已收口。

## v0.4.14.34 Post-Rebuild Alignment Retention Tightening 补充

- `tests/test_candidate_budget.py`: 补充 final evidence selector 的通用收紧覆盖，包括短语级责任后果识别、同源远距离条文 outlier 防护、同源近邻争点补齐、protected evidence 不可被 `issue_candidate` 分支替换，以及 selector 不消费 rerank query 中既有“场景锚点法条”提示行的边界。
- `tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`: v0.4.14.34 收紧后的正式 full RAG eval 报告；60/60 passed，用于证明 post-rebuild alignment retention tightening 没有回归。

## v0.4.14.33 Post-Rebuild Alignment Retention Delta 补充

- `tests/test_post_rebuild_alignment_retention_delta.py`: 验证修复前后 full RAG eval delta 的 case id 对齐、canonical evidence key、citation-only delta、商标 explained improvement、unchanged-pass replacement warn、removed expected evidence blocker、pass-to-fail blocker 和 saved-report-only contract。
- `tests/post_rebuild_alignment_retention_delta_report.json`: v0.4.14.33 delta runner 输出；用于 post-fix stabilization 和 v0.4.14.34 收口/收紧判断。

## v0.4.14.32 Post-Rebuild Evidence Alignment Retention 补充

- `tests/test_candidate_budget.py`: 新增 final evidence selector 的通用 alignment retention 测试，覆盖高重合法律后果保留、无关后果拒绝、无后果信号拒绝和已覆盖后果不重复替换。
- `tests/post_rebuild_rag_eval_after_alignment_retention_report.json`: v0.4.14.32 修复后的 full RAG eval 报告；60/60 passed。

## v0.4.14.31 Post-Rebuild Full RAG Eval Summary 补充

- `tests/test_post_rebuild_rag_eval_summary.py`: 验证 full RAG eval summary 在无回归时 passed；当 expected evidence 从 rerank input 到 final evidence 掉出时分类为 `final_evidence_selection_drop`；当 final evidence 已满足但答案关键词缺失时分类为 `answer_keyword_coverage_gap`。
- `tests/post_rebuild_rag_eval_report.json`: v0.4.14.31 重建后 full RAG eval 报告；60 个 cases 中 58 个通过，2 个相对 baseline 回归。
- `tests/post_rebuild_rag_eval_summary_report.json`: 汇总 post-rebuild full RAG eval 与 baseline full RAG eval 的差异，记录 failed checks、issue type summary 与 recommended triage。

## v0.4.14.30 Post-Rebuild Quality Summary 补充

- `tests/test_post_rebuild_quality_summary.py`: 验证重建后 smoke 无回归且 post-validation 通过时 summary passed；baseline 已通过 case 在 post-rebuild 失败时 summary fail-closed。
- `tests/post_rebuild_smoke_eval_report.json`: v0.4.14.30 重建后 smoke 复测报告；覆盖 15 个 manifest 文档对应的 25 个 smoke cases，结果 25/25 passed。
- `tests/post_rebuild_quality_summary_report.json`: 汇总 baseline smoke、post-rebuild smoke 和 post-validation；记录 0 个回归 case、0 个缺失 case、post-validation passed。

## v0.4.14.29 Production Rebuild Execution 补充

- `tests/test_production_rebuild_execution.py`: 验证执行记录器的授权/preflight 输入校验、dry-run 不执行、执行模式调用既有 `rag_admin.py --rebuild`、自动输入确认和 UTF-8 子进程输出处理。
- `tests/test_production_rebuild_post_validation.py`: 验证 post-validation 报告在执行成功且 chunk metadata 已观测时通过，在扫描到 structured block 缺少 `chunk_index/chunk_count` 时失败。
- `tests/production_rebuild_execution_report.json`: v0.4.14.29 生产重建执行记录；记录 `legal_knowledge` 从 7177 points 重建后仍为 7177 points，执行状态 `succeeded`。
- `tests/production_rebuild_post_validation_report.json`: v0.4.14.29 生产重建后只读验证报告；记录抽样 payload metadata 检查结果。

## v0.4.14.28 Production Rebuild Authorization Record Intake 补充

- `tests/test_production_rebuild_live_preflight_runner.py`: 更新为 v0.4.14.28 基线；验证授权记录读取、非对象 JSON 拒绝、授权记录/CLI 冲突、执行型字段 fail-closed、授权记录通过后仍不授权 Qdrant write 或 production rebuild。
- `tests/production_rebuild_authorization_record.json`: 正式授权记录输入；记录用户在当前线程明确同意生产重建、目标 collection、snapshot reference 与 source lineage reference。
- `tests/production_rebuild_live_preflight_report.json`: v0.4.14.28 正式只读 live preflight 报告；记录 `legal_knowledge` 可达、`points_count=7177`、授权记录已接受、blockers 为空，但 `qdrant_write_allowed=false`、`production_rebuild_allowed=false`、`authorization_granted=false`。

## v0.4.14.27 Production Rebuild Read-Only Live Preflight Runner 补充

- `tests/test_production_rebuild_live_preflight_runner.py`: 更新为 v0.4.14.27 基线；验证正式 runner version、fake/real readonly probe 注入、accepted status 必须带非空 `authorization_reference`、CLI 只读 live preflight output、write/rebuild 禁止态和 forbidden-call source scan。
- `tests/test_production_rebuild_live_preflight_real_readonly_probe.py`: 验证独立 real readonly probe 可透传 `authorization_reference`，并继续保持只读调用与 write/rebuild 禁止边界。
- `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py`: 更新历史 scaffold gate 预期，使其保留 traceability，不再因为正式 preflight report 已存在而误判失败。
- `tests/production_rebuild_live_preflight_report.json`: v0.4.14.27 正式只读 live preflight 报告；记录 `legal_knowledge` 可达、`points_count=7177`、snapshot/source lineage 已满足、当前仅因 `authorization_record_not_accepted` blocked。

## v0.4.14.26 Production Rebuild Formal Authorization Gate 补充

- `tests/test_production_rebuild_formal_authorization_gate.py`: 验证默认路径、当前 saved reports 只因正式授权 blocked、accepted status 必须带非空 reference、snapshot 缺失 fail-closed、异常 preflight blocker fail-closed、CLI blocked output 和 source 中无 Qdrant/RAG/LLM/eval/rebuild 执行调用。
- `tests/production_rebuild_formal_authorization_gate_report.json`: 由 v0.4.14.26 gate 生成；记录 snapshot reference 已满足、真实只读 preflight 仅剩 `authorization_record_not_accepted`，并保持 `production_rebuild_allowed=false`。

## v0.4.14.25 Production Rebuild Live Preflight Snapshot Create Reference Capture 补充

- `tests/test_production_rebuild_live_preflight_snapshot_create_reference_capture.py`: 验证未授权不调用 client、错误 collection 调用前 blocked、授权 snapshot 创建与 reference 捕获、`None` 返回 fail-closed、创建异常 fail-closed、CLI 缺授权开关非零退出和 source 中无删除/恢复 snapshot、point write、RAG、LLM、eval、rebuild 调用。
- `tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json`: 由真实授权 snapshot 创建工具生成；记录创建前后 snapshot 数量、created snapshot、checksum、`backup_or_snapshot_reference` 和仍不授权 rebuild 的边界。

## v0.4.14.24 Production Rebuild Live Preflight Snapshot Reference Probe 补充

- `tests/test_production_rebuild_live_preflight_snapshot_reference_probe.py`: 验证 fake Qdrant client 只读调用、snapshot reference 格式、最新 snapshot 选择、无 snapshot blocked、probe error fail-closed、CLI blocked output 和 source 中无 snapshot 创建/删除/恢复、Qdrant 写入、RAG、LLM、eval、rebuild 调用。
- `tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json`: 由真实只读 probe 生成；记录 `legal_knowledge` collection 可访问但现有 snapshot 数量为 `0`，因此缺少 `backup_or_snapshot_reference` 并继续 blocked。

## v0.4.14.23 Production Rebuild Live Preflight Real Read-Only Probe 补充

- `tests/test_production_rebuild_live_preflight_real_readonly_probe.py`: 验证 fake Qdrant client 只读调用、未授权/缺 backup blocked、accepted mock preflight 不授权 write/rebuild、CLI blocked output 和 source 中无写入/rebuild/RAG/LLM 调用。
- `tests/production_rebuild_live_preflight_real_readonly_probe_report.json`: 由真实只读 probe 生成；记录 `legal_knowledge` collection 可达、points count、抽样 payload metadata keys、阻断项和 write/rebuild 禁止态。
## v0.4.14.22 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Gate 补充

- `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py`: 验证 scaffold gate 默认路径、真实 v0.4.14.21 scaffold 通过、scaffold report 权限漂移、runner 缺失、正式输出误创建、禁止 import/text、mock-only 测试漂移、CLI 输出一致性和 Markdown 中文边界。
- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json`: 由 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py` 生成的 gate 报告；记录 13 项检查、0 failure，只开放 `production_rebuild_live_preflight_runner_mock_preflight_contract_gate`。
## v0.4.14.21 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold 补充

- `tests/test_production_rebuild_live_preflight_runner.py`: 验证 runner scaffold 默认无 live probe fail-closed、fake read-only probe 成功但不授权 write/rebuild、缺少授权、target mismatch、backup/source lineage 缺失、probe error、write-like method exposure、CLI scaffold report、临时输出写入和 runtime service import 禁止。
- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json`: 由 `tools/run_production_rebuild_live_preflight.py` 生成的 scaffold status report；记录 runner 文件和 mock-only 单测已创建，正式 `tests/production_rebuild_live_preflight_report.json` 未创建。
## v0.4.14.20 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design Gate 补充

- `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py`: 验证 scaffold design gate 默认路径、真实 v0.4.14.19 design 通过、status/lineage/blocker drift、scaffold contract drift、权限/guardrail drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 中文边界。
- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json`: 由 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py` 生成的 gate 报告；记录 14 项检查、0 failure，只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold`，不创建或运行 runner，不授权 Qdrant write 或 production rebuild。
## v0.4.14.19 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design 补充

- `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py`: 验证 scaffold design 默认路径、真实 v0.4.14.18 gate 输入通过、gate status/next-step drift、权限漂移、forbidden output key、CLI 输出一致性、runtime service import 禁止、未来文件不存在和 Markdown 边界。
- `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json`: 由 `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py` 生成的 design 报告；只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate`，不创建 runner 文件、未来测试文件或未来输出报告，不授权 Qdrant write 或 production rebuild。

## v0.4.14.18 Production Rebuild Live Preflight Runner Minimal Implementation Design Gate 补充

- `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py`: 验证 minimal implementation design gate 默认路径、真实 v0.4.14.17 design 通过、status/lineage drift、future file/CLI drift、权限/strategy drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json`: 由 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py` 生成的 gate 报告；记录 15 项检查、0 failure，只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design`，不创建 runner 文件、不运行 live preflight、不授权 Qdrant write 或 production rebuild。

## v0.4.14.17 Production Rebuild Live Preflight Runner Minimal Implementation Design 补充

- `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_design.py`: 验证 minimal implementation design 默认路径、真实 v0.4.14.16 gate 输入通过、gate status/next-step drift、权限漂移、forbidden output key、CLI 输出一致性、runtime service import 禁止、无 Qdrant 连接参数和 Markdown 边界。
- `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json`: 由 `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py` 生成的 design 报告；只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design_gate`，不创建 runner 文件、不运行 live preflight、不授权 Qdrant write 或 production rebuild。

## v0.4.14.16 Production Rebuild Live Preflight Runner Design Gate 补充

- `tests/test_production_rebuild_live_preflight_runner_design_gate.py`: 验证 design gate 默认路径、真实 v0.4.14.15 design 通过、status/lineage drift、contract drift、权限/guardrail/scaffold drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/production_rebuild_live_preflight_runner_design_gate_report.json`: 由 `tools/check_production_rebuild_live_preflight_runner_design_gate.py` 生成的 gate 报告；记录 15 项检查、0 failure，只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design`，不创建或运行 runner、不授权 Qdrant write 或 production rebuild。

## v0.4.14.15 Production Rebuild Live Preflight Runner Design 补充

- `tests/test_production_rebuild_live_preflight_runner_design.py`: 验证 live preflight runner design 默认路径、真实 readiness cutoff 通过、cutoff status/next-step drift、权限漂移、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/production_rebuild_live_preflight_runner_design_report.json`: 由 `tools/build_production_rebuild_live_preflight_runner_design.py` 生成的 design 报告；状态为 `ready_for_live_preflight_runner_design_gate`，只开放 `production_rebuild_live_preflight_runner_design_gate`，不创建 runner、不运行 live preflight、不授权 Qdrant write 或 production rebuild。

## v0.4.14.14 Production Rebuild Readiness Cutoff 补充

- `tests/test_production_rebuild_readiness_cutoff.py`: 验证 readiness cutoff 默认路径、真实 saved reports 通过、source patch/dry-run drift、authorization/execution/input gate drift、project health drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/production_rebuild_readiness_cutoff_report.json`: 由 `tools/build_production_rebuild_readiness_cutoff.py` 生成的 cutoff 报告；状态为 `ready_for_live_preflight_runner_design_cutoff`，只开放 `production_rebuild_live_preflight_runner_design`，不授权 live preflight、Qdrant write 或 production rebuild。

## v0.4.14.13 Human Rebuild Authorization Record Input Form Scaffold Gate 补充

- `tests/test_human_rebuild_authorization_record_input_form_scaffold_gate.py`: 验证 input form scaffold gate 默认路径、真实 v0.4.14.12 scaffold 通过、version/schema/status/source lineage drift、人工值/form/export/import/validation/authorization/Qdrant/rebuild 权限漂移、internal gate/guardrails、section/field contract、`operator_approval` future-only、future policy、handoff、traceability、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json`: 由 `tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py` 生成的只读 gate 报告；它只开放 `human_rebuild_authorization_record_input_importer_design`，不授权填写真实人工值、创建 importer、导入审批值、正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.12 Human Rebuild Authorization Record Input Form Scaffold 补充

- `tests/test_human_rebuild_authorization_record_input_form_scaffold.py`: 验证 input form scaffold 默认路径、真实 v0.4.14.10/11 输入通过、10 个字段顺序、7 个分区、中文标签、未来控件提示、空白值状态、不可编辑/不可提交/不可导出/不可导入/不可授权、`operator_approval` future-only、source drift、contract/policy/handoff/traceability drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_input_form_scaffold_report.json`: 由 `tools/build_human_rebuild_authorization_record_input_form_scaffold.py` 生成的空白输入表单 scaffold 报告；它只开放 `human_rebuild_authorization_record_input_form_scaffold_gate`，不授权填写真实人工值、创建 importer、导入审批值、正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.11 Human Rebuild Authorization Record Input Packet Scaffold Gate 补充

- `tests/test_human_rebuild_authorization_record_input_packet_scaffold_gate.py`: 验证 input packet scaffold gate 默认路径、真实 v0.4.14.10 scaffold 通过、version/schema/status/source lineage drift、人工值/import/validation/authorization/Qdrant/rebuild 权限漂移、internal gate/guardrails、section/row contract、`operator_approval` future-only、future policy、handoff、traceability、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json`: 由 `tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py` 生成的只读 gate 报告；它只开放 `human_rebuild_authorization_record_input_form_scaffold`，不授权填写真实人工值、创建 importer、导入审批值、正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.10 Human Rebuild Authorization Record Input Packet Scaffold 补充

- `tests/test_human_rebuild_authorization_record_input_packet_scaffold.py`: 验证 input packet scaffold 默认路径、真实 v0.4.14.8/9 输入通过、10 个字段顺序、7 个分区、空白值状态、`operator_approval` future-only、design/gate drift、人工值/权限漂移、contract/policy/handoff/traceability drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_input_packet_scaffold_report.json`: 由 `tools/build_human_rebuild_authorization_record_input_packet_scaffold.py` 生成的空白输入包 scaffold 报告；它只开放 `human_rebuild_authorization_record_input_packet_scaffold_gate`，不授权填写真实人工值、创建输入入口、导入审批值、正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.9 Human Rebuild Authorization Record Input Workflow Design Gate 补充

- `tests/test_human_rebuild_authorization_record_input_workflow_design_gate.py`: 验证 input workflow design gate 默认路径、真实 v0.4.14.8 design 通过、status/source lineage drift、人工值/权限漂移、internal gate/guardrail drift、workflow phase drift、field input contract drift、future policy/import policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json`: 由 `tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py` 生成的只读 gate 报告；它只开放 `human_rebuild_authorization_record_input_packet_scaffold`，不授权填写真实人工值、创建输入入口、导入审批值、正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.8 Human Rebuild Authorization Record Input Workflow Design 补充

- `tests/test_human_rebuild_authorization_record_input_workflow_design.py`: 验证 input workflow design 默认路径、真实 draft scaffold/gate 输入通过、字段输入契约顺序和空值、workflow phases design-only、`operator_approval` 不构成当前批准、scaffold/gate drift、权限漂移、row/section drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_input_workflow_design_report.json`: 由 `tools/build_human_rebuild_authorization_record_input_workflow_design.py` 生成的输入流程设计报告；它只开放 `human_rebuild_authorization_record_input_workflow_design_gate`，不授权填写真实人工值、创建输入入口、导入审批值、正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.7 Human Rebuild Authorization Record Draft Scaffold Gate 补充

- `tests/test_human_rebuild_authorization_record_draft_scaffold_gate.py`: 验证 draft scaffold gate 默认路径、真实 scaffold 通过、status/source lineage drift、人工值/授权漂移、internal gate/guardrail drift、section/row drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性和 Markdown 边界。
- `tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json`: 由 `tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py` 生成的 gate 报告；它只开放 `human_rebuild_authorization_record_input_workflow_design`，不授权填写真实人工值、创建或接受正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.6 Human Rebuild Authorization Record Draft Scaffold 补充

- `tests/test_human_rebuild_authorization_record_draft_scaffold.py`: 验证 draft scaffold 默认路径、真实 draft design/gate 输入通过、字段顺序和 `not_collected` / `null` 空白值、分区契约、`operator_approval` 不构成当前批准、design/gate drift、权限漂移、section/field mapping drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_draft_scaffold_report.json`: 由 `tools/build_human_rebuild_authorization_record_draft_scaffold.py` 生成的空白草案 scaffold 报告；它只开放 `human_rebuild_authorization_record_draft_scaffold_gate`，不授权填写真实人工值、创建或接受正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.5 Human Rebuild Authorization Record Draft Design Gate 补充

- `tests/test_human_rebuild_authorization_record_draft_design_gate.py`: 验证 draft design gate 默认路径、真实 draft design 通过、status/source lineage drift、人工值/授权漂移、internal gate/guardrail drift、section/field mapping drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性和 Markdown 边界。
- `tests/human_rebuild_authorization_record_draft_design_gate_report.json`: 由 `tools/check_human_rebuild_authorization_record_draft_design_gate.py` 生成的 gate 报告；它只开放 `human_rebuild_authorization_record_draft_scaffold`，不授权填写真实人工值、创建或接受正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.4 Human Rebuild Authorization Record Draft Design 补充

- `tests/test_human_rebuild_authorization_record_draft_design.py`: 验证 draft design 默认路径、真实 scaffold/gate 输入通过、字段映射顺序和 `not_collected` / `null` 空白值、`operator_approval` 不构成当前批准、scaffold/gate drift、权限漂移、guardrail/contract drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_draft_design_report.json`: 由 `tools/build_human_rebuild_authorization_record_draft_design.py` 生成的草案设计报告；它只开放 `human_rebuild_authorization_record_draft_design_gate`，不授权填写正式授权、live preflight、Qdrant write 或 production rebuild。

## v0.4.14.3 Human Rebuild Authorization Record Scaffold Gate 补充

- `tests/test_human_rebuild_authorization_record_scaffold_gate.py`: 验证 scaffold gate 默认路径、真实 scaffold 通过、status/source lineage drift、人工值/授权漂移、guardrail drift、row blank contract drift、input contract drift、packet/handoff drift、assertion drift 和 Markdown 边界。
- `tests/human_rebuild_authorization_record_scaffold_gate_report.json`: 由 `tools/check_human_rebuild_authorization_record_scaffold_gate.py` 生成的 gate 报告；它只开放 `human_rebuild_authorization_record_draft_design`，不授权填写正式授权、live preflight、Qdrant write 或生产 rebuild。

## v0.4.14.2 Human Rebuild Authorization Record Scaffold 补充

- `tests/test_human_rebuild_authorization_record_scaffold.py`: 验证 scaffold 默认路径、真实 design/gate 输入通过、字段顺序和 `not_collected` 空白值、`operator_approval` 不构成当前批准、input lineage drift、权限漂移、已填值/授权漂移、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/human_rebuild_authorization_record_scaffold_report.json`: 由 `tools/build_human_rebuild_authorization_record_scaffold.py` 生成的空白授权记录 scaffold 报告；它只开放 `human_rebuild_authorization_record_scaffold_gate`，不授权 live preflight、Qdrant write 或生产 rebuild。

## v0.4.14.1 Production Rebuild Execution Design Gate 补充

- `tests/test_production_rebuild_execution_design_gate.py`: 验证 gate 默认路径、真实 design 通过、closeout lineage drift、授权/执行权限漂移、guardrail drift、record contract 缺失或额外混入、preflight check drift、abort condition drift、rebuild record 提前创建、decision policy drift、handoff drift 和 Markdown 边界。
- `tests/production_rebuild_execution_design_gate_report.json`: 由 `tools/check_production_rebuild_execution_design_gate.py` 生成的 gate 报告；它只开放 `human_rebuild_authorization_record_scaffold`，不授权 live preflight、Qdrant write 或生产 rebuild。

## v0.4.14.0 Production Rebuild Execution Design 补充

- `tests/test_production_rebuild_execution_design.py`: 验证 execution design 默认路径、真实输入通过、closeout-only source lineage、执行记录契约、缺失 closeout 阻断、version/schema/status/next-step drift、授权/rebuild 权限漂移、guardrail drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- `tests/production_rebuild_execution_design_report.json`: 由 `tools/build_production_rebuild_execution_design.py` 生成的 design 报告；它只开放 `production_rebuild_execution_design_gate`，不授权 live preflight、Qdrant write 或生产 rebuild。

## v0.4.13.18 Ingestion Metadata Rebuild Planning Series Closeout 补充

- `tests/test_ingestion_metadata_rebuild_planning_series_closeout.py`: 验证 closeout 默认路径、真实输入通过、source lineage、缺失 source 阻断、version/schema/status/next-step drift 阻断、授权/rebuild 权限漂移、guardrail 漂移、非运行时边界和 Markdown 边界。
- `tests/ingestion_metadata_rebuild_planning_series_closeout_report.json`: 由 `tools/build_ingestion_metadata_rebuild_planning_series_closeout.py` 生成的 closeout 报告；它只开放 `production_rebuild_execution_design`，不授权 live preflight、Qdrant write 或生产 rebuild。

## v0.4.13.17 Rebuild Runbook / Preflight Contract 补充

- `tests/test_rebuild_runbook_preflight_contract.py`: 验证 contract 默认路径、真实输入通过、failed gate 阻断、rebuild permission drift 阻断和 Markdown 非运行时边界。
- `tests/rebuild_runbook_preflight_contract_report.json`: 由 `tools/build_rebuild_runbook_preflight_contract.py` 生成的 contract 报告；它只开放 v0.4.13 series closeout，不授权 Qdrant rebuild 或生产写入。

## v0.4.13.16 Human Rebuild Authorization Worksheet Gate 补充

- `tests/test_human_rebuild_authorization_worksheet_gate.py`: 验证 gate 默认路径、真实 worksheet 通过、字段顺序、人工值被收集、授权/rebuild 权限漂移、optional 标签缺失和 Markdown 非运行时边界。
- `tests/human_rebuild_authorization_worksheet_gate_report.json`: 由 `tools/check_human_rebuild_authorization_worksheet_gate.py` 生成的 gate 报告；它只开放 `rebuild_runbook_preflight_contract`，不授权 Qdrant rebuild 或生产写入。

## v0.4.13.15 Human Rebuild Authorization Worksheet 补充

- `tests/test_human_rebuild_authorization_worksheet.py`: 验证 worksheet 默认路径、真实输入通过、10 行字段顺序、required/optional 标签、operator approval 不构成当前批准、abort conditions、gate drift、字段 drift、rebuild permission drift 和 Markdown 非运行时边界。
- `tests/human_rebuild_authorization_worksheet_report.json`: 由 `tools/build_human_rebuild_authorization_worksheet.py` 生成的 worksheet 报告；它只开放 worksheet gate，不授权 Qdrant rebuild 或生产写入。

## v0.4.13.14 Rebuild Authorization Design Gate 补充

- `tests/test_rebuild_authorization_design_gate.py`: 验证 gate 默认路径、真实设计通过、lineage drift、授权/rebuild 权限漂移、未来授权记录提前创建、必填字段缺失、终止条件缺失、handoff drift 和 Markdown 非运行时边界。
- `tests/rebuild_authorization_design_gate_report.json`: 由 `tools/check_rebuild_authorization_design_gate.py` 生成的 gate 报告；它只开放 `human_rebuild_authorization_worksheet`，不授权 Qdrant rebuild 或生产写入。

## v0.4.13.13 Rebuild Authorization Design 补充

- `tests/test_rebuild_authorization_design.py`: 验证 design 默认路径、真实输入通过、必填人工授权字段、runner gate drift、runner summary drift、handoff 操作边界和 Markdown 非运行时边界。
- `tests/rebuild_authorization_design_report.json`: 由 `tools/build_rebuild_authorization_design.py` 生成的 design 报告；它只开放 `rebuild_authorization_design_gate`，不授权 Qdrant rebuild 或生产写入。

## v0.4.13.12 Post-Patch Rebuild Dry-Run Runner Gate 补充

- `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py`: 验证 gate 默认路径、真实 v0.4.13.11 runner saved report 通过、summary drift、guardrail drift、sample drift、row drift、lineage drift、handoff drift 与 Markdown 非运行时边界。
- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json`: 由 `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py` 生成的 gate 报告；它只开放 `rebuild_authorization_design`，不授权 Qdrant rebuild 或生产写入。

## v0.4.13.11 Post-Patch Rebuild Dry-Run Runner 补充

- `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`: 验证 runner 默认路径、真实 saved-report 输入、样本形态、row-level `chunk_index/chunk_count` presence、预期 `chunk_id/qdrant_point_id` drift、forbidden drift 阻断、输入漂移阻断和 Markdown 非运行时边界。
- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json`: 由 `tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py` 生成的 dry-run 报告；它只开放下一步 runner gate，不授权 Qdrant rebuild 或生产写入。

## v0.4.13.10 Post-Patch Rebuild Dry-Run Design Gate 补充

- `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py`: 验证 design gate 默认路径、真实 v0.4.13.9 design、source patch 输入漂移、runner creation permission 漂移、sample strategy、comparison fields、output contract、guardrails、handoff 边界和 Markdown 非运行时边界。
- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json`: 由 `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py` 生成的 gate 报告；它只开放下一步 runner 工作，不在本版本创建 runner、写 Qdrant 或 rebuild。

## v0.4.13.9 Post-Patch Rebuild Dry-Run Design 补充

- `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py`: 验证 post-patch rebuild dry-run design 的默认路径、真实 v0.4.13.8 输入、source patch report 漂移阻断、guardrails、future runner contract 和 Markdown 边界。
- `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json`: 由 `tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py` 生成的设计报告；它只开放 design gate，不授权创建 runner、Qdrant write 或 rebuild。

## v0.4.13.8 入库元数据源码补丁补充

- `tests/test_ingestion_metadata_source_patch.py`: 直接验证普通法律 parent article 与 paragraph/item 子块的 `chunk_index/chunk_count` metadata，并确认 standard section 路径保持原行为。
- `tests/test_ingestion_metadata_source_patch_check.py`: 验证源码补丁 checker 的默认路径、真实 patch 通过、parent/child/standard section 漂移阻断和 gate failure。
- `tests/ingestion_metadata_source_patch_report.json`: 由 `tools/check_ingestion_metadata_source_patch.py` 生成的源码补丁检查报告；它只开放 post-patch rebuild dry-run design，不授权 Qdrant write 或 rebuild。

## v0.4.13.7 Ingestion Metadata Patch Actual Design Gate 补充

- `tests/test_ingestion_metadata_patch_actual_design_gate.py`: 验证 actual design gate 的默认路径、真实报告通过、allowed file 漂移、child count 规则漂移、验证计划缺口、implementation/Qdrant/rebuild 权限漂移和 handoff 边界缺失。
- `tests/ingestion_metadata_patch_actual_design_gate_report.json`: 由 `tools/check_ingestion_metadata_patch_actual_design_gate.py` 生成的 gate 报告；它只开放最小 ingestion metadata source patch，不授权 Qdrant write 或 rebuild。

## v0.4.13.6 Ingestion Metadata Patch Actual Design 补充

- `tests/test_ingestion_metadata_patch_actual_design.py`: 验证 actual patch design 的默认路径、真实输入、单文件单函数 scope、post-patch 验证计划、gate failure 和 next-step drift。
- `tests/ingestion_metadata_patch_actual_design_report.json`: 由 `tools/build_ingestion_metadata_patch_actual_design.py` 生成的设计报告；它只开放 design gate，不授权 actual patch、Qdrant write 或 rebuild。

## v0.4.13.5 Ingestion Metadata Patch Local Dry-Run Gate 补充

- `tests/test_ingestion_metadata_patch_local_dry_run_gate.py`: 验证 local dry-run gate 的默认路径、真实报告通过、forbidden drift、缺失边界 metadata、ID drift 缺失、Qdrant guardrail 漂移和 handoff 边界缺失。
- `tests/ingestion_metadata_patch_local_dry_run_gate_report.json`: 由 `tools/check_ingestion_metadata_patch_local_dry_run_gate.py` 生成的 gate 报告；它只开放 actual ingestion metadata patch design，不授权实现或 rebuild。

## v0.4.13.4 Ingestion Metadata Patch Local Dry-Run Runner 补充

- `tests/test_ingestion_metadata_patch_local_dry_run.py`: 验证 local dry-run runner 的默认路径、样例 block shape、simulation-only 边界、prerequisite gate failure、content/citation 稳定性，并在 v0.4.13.8 后区分历史 saved report 的 pre-patch drift 与当前源码已 patch 的 0 drift。
- `tests/ingestion_metadata_patch_local_dry_run_report.json`: 由 `tools/run_ingestion_metadata_patch_local_dry_run.py` 生成的本地 dry-run 报告；它只记录预期 metadata/ID drift，不授权 actual patch 或 rebuild。

## v0.4.13.3 Ingestion Metadata Patch Dry-Run Design Gate 补充

- `tests/test_ingestion_metadata_patch_dry_run_design_gate.py`：验证 dry-run design gate 会阻断 forbidden drift 缺失、Qdrant input 漂移、blocking condition 缺失和 full eval 替代 dry-run 等风险。
- `tests/ingestion_metadata_patch_dry_run_design_gate_report.json`：由 `tools/check_ingestion_metadata_patch_dry_run_design_gate.py` 生成的 gate 报告；它不实现 runner，只开放 local dry-run runner。

## v0.4.13.2 Ingestion Metadata Patch Dry-Run Design 补充

- `tests/test_ingestion_metadata_patch_dry_run_design.py`：验证 dry-run design 的 expected/forbidden drift、blocking conditions、contract gate 依赖和 dry-run-only 边界。
- `tests/ingestion_metadata_patch_dry_run_design_report.json`：由 `tools/build_ingestion_metadata_patch_dry_run_design.py` 生成的 dry-run design 报告；它不实现 patch，只开放 dry-run design gate。

## v0.4.13.1 Ingestion Metadata Patch Contract Gate 补充

- `tests/test_ingestion_metadata_patch_contract_gate.py`：验证 contract gate 会阻断 runtime file scope drift、parent rule drift 和 Qdrant write permission drift，并保持 implementation disallowed。
- `tests/ingestion_metadata_patch_contract_gate_report.json`：由 `tools/check_ingestion_metadata_patch_contract_gate.py` 生成的 gate 报告；它不实现修复，只开放 dry-run design。

## v0.4.13.0 Ingestion Metadata Patch Contract 补充

- `tests/test_ingestion_metadata_patch_contract.py`：验证 contract 只开放 `src/rag/ingestion.py::build_article_documents`，并阻断 closeout drift、提前实现和主链路/规则范围扩散。
- `tests/ingestion_metadata_patch_contract_report.json`：由 `tools/build_ingestion_metadata_patch_contract.py` 生成的 patch contract；它不实现修复，只开放 contract gate。

## v0.4.12.3 Metadata/Chunking Series Closeout 补充

- `tests/test_metadata_chunking_series_closeout.py`：验证 v0.4.12.x closeout 依赖 root-cause、fix design 和 gate 三段链条，阻断 gate failure，并确认下一系列仍禁止 patch rag_query 或 direct Qdrant payload patch。
- `tests/metadata_chunking_series_closeout_report.json`：由 `tools/build_metadata_chunking_series_closeout.py` 生成的 series closeout；它只移交下一系列，不授权实现。

## v0.4.12.2 Metadata/Chunking Fix Design Gate 补充

- `tests/test_metadata_chunking_fix_design_gate.py`：验证 fix design gate 会阻断 stable ID impact 缺失、direct payload patch 放开等危险漂移，并保持 implementation disallowed。
- `tests/metadata_chunking_fix_design_gate_report.json`：由 `tools/check_metadata_chunking_fix_design_gate.py` 生成的 gate 报告；它不实现修复，只开放 series closeout。

## v0.4.12.1 Metadata/Chunking Fix Design 补充

- `tests/test_metadata_chunking_fix_design.py`：验证 fix design 由 v0.4.12.0 root-cause report 驱动，记录 stable ID impact、rebuild required 和 design-only 边界，并阻断 root-cause drift。
- `tests/metadata_chunking_fix_design_report.json`：由 `tools/build_metadata_chunking_fix_design.py` 生成的修复设计报告；它不修改 ingestion，只开放 fix design gate。

## v0.4.12.0 Metadata/Chunking Root-Cause Report 补充

- `tests/test_metadata_chunking_root_cause_report.py`：验证 root-cause report 的历史 saved report 保留 pre-patch root-cause 结论，同时区分当前源码在 v0.4.13.8 后已补齐 article boundary metadata。
- `tests/metadata_chunking_root_cause_report.json`：由 `tools/build_metadata_chunking_root_cause_report.py` 生成的 root-cause 报告；它不修复数据，只开放 fix design。

## v0.4.11.3 Evidence Metadata Snapshot Series Closeout 补充

- `tests/test_evidence_metadata_snapshot_series_closeout.py`：验证 series closeout 能通过真实 contract/snapshot/gate 报告，并阻断 gate drift 与 missing Qdrant read。
- `tests/evidence_metadata_snapshot_series_closeout_report.json`：由 `tools/build_evidence_metadata_snapshot_series_closeout.py` 生成的 closeout 报告；它将 19/19 `chunk_boundary_ambiguity` 移交给 v0.4.12 root-cause/fix design，不在本版本修复。

## v0.4.11.2 Evidence Metadata Snapshot Gate 补充

- `tests/test_evidence_metadata_snapshot_gate.py`：验证 snapshot gate 能接受真实 snapshot findings，并阻断 Qdrant unavailable、vector read 漂移和 row count 漂移。
- `tests/evidence_metadata_snapshot_gate_report.json`：由 `tools/check_evidence_metadata_snapshot_gate.py` 生成的 gate 报告；它保留 19/19 `chunk_boundary_ambiguity` 作为后续 root-cause/fix design 输入，不在本版本修复。

## v0.4.11.1 Evidence Metadata Snapshot Runner 补充

- `tests/test_evidence_metadata_snapshot.py`：验证 read-only snapshot runner 能阻断 contract drift、Qdrant unavailable，并能在 fake payload 下输出 19 行诊断；同时确认不调用 RAG/LLM。
- `tests/evidence_metadata_snapshot_report.json`：由 `tools/run_evidence_metadata_snapshot.py` 生成的真实 Qdrant payload 只读 snapshot 报告；当前扫描 7177 个 points，输出 19 行 evidence target 诊断。

## v0.4.11.0 Evidence Metadata Snapshot Contract 补充

- `tests/test_evidence_metadata_snapshot_contract.py`：验证 snapshot contract 能从 v0.4.10.3 closeout、v0.4.10.0 manifest 与 eval cases 生成 8 个 sample cases、19 个 evidence targets，并阻断 source report 漂移和缺失 eval case。
- `tests/evidence_metadata_snapshot_contract_report.json`：由 `tools/build_evidence_metadata_snapshot_contract.py` 生成的 contract 报告；它不连接 Qdrant，不运行 full eval，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.10.3 Metadata/Chunking Diagnostic Runner Series Closeout 补充

- `tests/test_metadata_chunking_diagnostic_runner_series_closeout.py`：验证 v0.4.10.x closeout 能通过真实 manifest/runner/gate 报告，并阻断版本漂移、snapshot read 越界、matrix 漂移和 runtime 污染。
- `tests/metadata_chunking_diagnostic_runner_series_closeout_report.json`：由 `tools/build_metadata_chunking_diagnostic_runner_series_closeout.py` 生成的 series closeout 报告；它不读取 evidence-level metadata snapshot，不运行 full eval，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.10.2 Metadata/Chunking Saved-Report Runner Gate 补充

- `tests/test_metadata_chunking_diagnostic_saved_report_runner_gate.py`：验证 saved-report runner gate 能通过真实 v0.4.10.1 report，并阻断版本漂移、blocked rows、snapshot read 越界和 runtime 污染。
- `tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json`：由 `tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py` 生成的 gate 报告；它不运行 diagnostic，不读取 evidence-level metadata snapshot，不运行 full eval，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.10.1 Metadata/Chunking Saved-Report Diagnostic Runner 补充

- `tests/test_metadata_chunking_diagnostic_saved_report_runner.py`：验证 saved-report runner 能从 v0.4.10.0 manifest 与 v0.4.9.10 contract 输出 40 行诊断结果，并阻断 manifest/contract 漂移和缺失契约字段。
- `tests/metadata_chunking_diagnostic_saved_report_runner_report.json`：由 `tools/run_metadata_chunking_diagnostic_saved_report.py` 生成的 saved-report scope 诊断报告；它不读取 evidence-level metadata snapshot，不运行 full eval，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.10.0 Metadata/Chunking Diagnostic Runner Manifest 补充

- `tests/test_metadata_chunking_diagnostic_runner_manifest.py`：验证 runner manifest 能从 v0.4.9.11 closeout、v0.4.9.10 contract 与 v0.4.9.6 spec 展开 40 个只读 manifest items，并阻断 closeout/contract/spec 漂移。
- `tests/metadata_chunking_diagnostic_runner_manifest_report.json`：由 `tools/build_metadata_chunking_diagnostic_runner_manifest.py` 生成的 manifest 报告；它不创建或运行 diagnostic runner，不运行 full eval，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.11 Retrieval Input Quality Series Closeout 补充

- `tests/test_retrieval_input_quality_series_closeout.py`：验证 v0.4.9.x saved reports 能按顺序收口，并阻断版本漂移、缺失报告和 runtime 污染。
- `tests/retrieval_input_quality_series_closeout_report.json`：由 `tools/build_retrieval_input_quality_series_closeout.py` 生成的系列收口报告；它不创建或运行 diagnostic runner，不运行 full eval，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.10 Metadata/Chunking Diagnostic Dry-Run Contract 补充

- `tests/test_metadata_chunking_diagnostic_dry_run_contract.py`：验证 dry-run contract 能从 v0.4.9.9 gate 与 v0.4.9.8 design 生成未来 runner 契约，并阻断 gate 漂移、design 漂移、row 顺序漂移、输出字段漂移和 runtime 污染。
- `tests/metadata_chunking_diagnostic_dry_run_contract_report.json`：由 `tools/build_metadata_chunking_diagnostic_dry_run_contract.py` 生成的只读 contract 报告；它不创建真实 runner，不运行 full eval，不运行 diagnostic，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.9 Metadata/Chunking Diagnostic Runner Design Gate 补充

- `tests/test_metadata_chunking_diagnostic_runner_design_gate.py`：验证 runner design gate 能从 v0.4.9.8 saved report 开放 dry-run contract，并阻断版本漂移、row 顺序漂移、输出字段漂移、failure bucket 漂移、prohibited actions 漂移和 runtime 污染。
- `tests/metadata_chunking_diagnostic_runner_design_gate_report.json`：由 `tools/check_metadata_chunking_diagnostic_runner_design_gate.py` 生成的只读 gate 报告；它不运行 full eval，不运行 diagnostic，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.8 Metadata/Chunking Diagnostic Runner Design 补充

- `tests/test_metadata_chunking_diagnostic_runner_design.py`：验证 runner design 能从 v0.4.9.7 gate 与 v0.4.9.6 spec 生成未来只读 runner 契约，并阻断 gate 漂移、spec 漂移、row 顺序漂移和运行时授权污染。
- `tests/metadata_chunking_diagnostic_runner_design_report.json`：由 `tools/build_metadata_chunking_diagnostic_runner_design.py` 生成的只读设计报告；它不运行 full eval，不运行 diagnostic，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.7 Metadata/Chunking Diagnostic Spec Gate 补充

- `tests/test_metadata_chunking_diagnostic_spec_gate.py`：验证 metadata/chunking diagnostic spec gate 能通过真实 v0.4.9.6 spec report，并阻断版本漂移、row 顺序漂移、必需字段缺失、sample scope 缺口、prohibited actions 漂移和运行时授权污染。
- `tests/metadata_chunking_diagnostic_spec_gate_report.json`：由 `tools/check_metadata_chunking_diagnostic_spec_gate.py` 生成的只读 gate 报告；它不运行 full eval，不运行 diagnostic，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.6 Metadata/Chunking Diagnostic Spec 补充

- `tests/test_metadata_chunking_diagnostic_spec.py`：验证 metadata/chunking diagnostic spec 能从 v0.4.9.5 gate 与 v0.4.9.4 prioritization 生成检查契约，并阻断 gate 漂移、top route 漂移、artifact 漂移和运行时授权污染。
- `tests/metadata_chunking_diagnostic_spec_report.json`：由 `tools/build_metadata_chunking_diagnostic_spec.py` 生成的只读 spec 报告；它不运行 full eval，不运行 diagnostic，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.5 Retrieval Input Quality Diagnostic Prioritization Gate 补充

- `tests/test_retrieval_input_quality_diagnostic_prioritization_gate.py`：验证 prioritization gate 能通过真实 v0.4.9.4 prioritization report，并阻断版本漂移、route order 漂移、缺失字段、内容缺口和运行时授权污染。
- `tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json`：由 `tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py` 生成的只读门禁报告；它不运行 full eval，不实现 runtime policy，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.4 Retrieval Input Quality Diagnostic Prioritization 补充

- `tests/test_retrieval_input_quality_diagnostic_prioritization.py`：验证 diagnostic prioritization 能从 v0.4.9.3 gate 与 v0.4.9.2 offline audit 生成 5 条优先级矩阵，并阻断 gate 漂移、audit route 漂移、bucket 顺序漂移和运行时/后端模式。
- `tests/retrieval_input_quality_diagnostic_prioritization_report.json`：由 `tools/build_retrieval_input_quality_diagnostic_prioritization.py` 生成的只读诊断优先级报告；它不运行 full eval，不实现 runtime policy，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.3 Retrieval Input Quality Offline Audit Gate 补充

- `tests/test_retrieval_input_quality_offline_audit_gate.py`：验证 offline audit gate 能通过真实 v0.4.9.2 offline audit report，并阻断版本漂移、bucket 顺序漂移、缺失字段、内容缺口和运行时授权污染。
- `tests/retrieval_input_quality_offline_audit_gate_report.json`：由 `tools/check_retrieval_input_quality_offline_audit_gate.py` 生成的只读门禁报告；它不运行 full eval，不实现 runtime policy，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.2 Retrieval Input Quality Offline Audit 补充

- `tests/test_retrieval_input_quality_offline_audit.py`：验证 offline audit runner 能按 v0.4.9.1 audit spec 消费现有 saved reports，生成 5 个 bucket 审计结果，并阻断 spec 版本漂移、bucket 顺序漂移、gate 漂移和运行时/后端模式。
- `tests/retrieval_input_quality_offline_audit_report.json`：由 `tools/build_retrieval_input_quality_offline_audit.py` 生成的只读离线审计报告；它不运行 full eval，不实现 runtime policy，也不修改 retriever、rerank、prompt、eval case 或 RAG 主流程。

## v0.4.9.1 Retrieval Input Quality Audit Spec 补充

- `tests/test_retrieval_input_quality_audit_spec.py`：验证 audit spec 能从 v0.4.9.0 intake 生成 5 个离线审计契约，并阻断 intake 版本漂移、bucket 顺序漂移、实现授权污染和运行时/后端模式。

## v0.4.9.0 Retrieval Input Quality Intake 补充

- `tests/test_retrieval_input_quality_intake.py`：验证 retrieval input quality intake 能读取既有 saved reports 生成 5 个治理 bucket 与 sample case queue，并阻断 source version drift、空 gap source 和运行时/后端模式。

## 已合并的历史测试锚点

- `tests/test_ready_action_design_pack.py`：历史 ready action 设计包测试，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。
- `tests/test_ready_action_design_review_brief.py`：历史 ready action 设计评审简报测试，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。
- `tests/test_ready_action_design_review_gate.py`：历史 ready action 设计评审 gate 测试，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。

## v0.4.8.15 Final Evidence Selection Policy Series Closeout 补充

- `tests/test_final_evidence_selection_policy_series_closeout.py`：验证 v0.4.8.x series closeout 能基于 v0.4.8.14/13/12/11 saved reports 收口为离线设计完成状态，并阻断 blocked adoption draft、category 顺序漂移、实现授权污染和运行时/后端模式。

## v0.4.8.14 Final Evidence Selection Policy Adoption Decision Draft 补充

- `tests/test_final_evidence_selection_policy_adoption_decision_draft.py`：验证 adoption decision draft 能基于 v0.4.8.13 gate 与 v0.4.8.12 simulation 生成 8 条待用户确认 rows，并阻断 blocked gate、simulation 顺序漂移、blocking failure 和运行时/后端模式。

## v0.4.8.13 Final Evidence Selection Policy Offline Simulation Gate 补充

- `tests/test_final_evidence_selection_policy_offline_simulation_gate.py`：验证离线模拟结果门禁能通过真实 v0.4.8.12 simulation report，并阻断 blocking failure、缺失字段、category 顺序漂移和 runtime adoption 污染。

## v0.4.8.12 Final Evidence Selection Policy Offline Simulation 补充

- `tests/test_final_evidence_selection_policy_offline_simulation.py`：验证最终证据选择策略离线模拟 runner 只读取 v0.4.8.11 输入契约，生成 8 条 saved-report simulation result rows，并阻断输入契约漂移、category 顺序漂移和运行时/后端模式。

## v0.4.8.11 Final Evidence Selection Policy Offline Simulation Input Contract 补充

- `tests/test_final_evidence_selection_policy_offline_simulation_input_contract.py`：验证最终证据选择策略离线模拟输入契约只读取 v0.4.8.7 与 v0.4.8.10 saved reports，生成 8 条 simulation input rows，并阻断源报告漂移、category 顺序漂移和运行时/后端模式。
- `tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json`：由 `tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py` 生成的只读 input contract 报告；它不运行 simulation，不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。

## v0.4.8.10 Final Evidence Selection Policy Language Revision Confirmation Record 补充

- `tests/test_final_evidence_selection_policy_language_revision_confirmation_record.py`：验证最终证据选择策略语言修订确认记录只读取 v0.4.8.9 closeout draft saved report，按用户确认生成 3 条 confirmed rows，并阻断源 draft 漂移、实现授权泄漏、row 顺序/数量漂移、advisory/forbidden keys、可读性污染和运行时/后端模式。
- `tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json`：由 `tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py` 生成的只读 confirmation record 报告；confirmed wording 只允许作为后续 offline simulation design 输入，不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。

## v0.4.8.9 Final Evidence Selection Policy Language Revision Closeout Draft 补充

- `tests/test_final_evidence_selection_policy_language_revision_closeout_draft.py`：验证最终证据选择策略语言修订收口草案只读取 v0.4.8.8 worksheet saved report，生成 3 条 pending user confirmation draft rows，并阻断源 worksheet 漂移、实现授权泄漏、revision row 顺序/数量漂移、advisory/forbidden keys、可读性污染和运行时/后端模式。
- `tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json`：由 `tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py` 生成的只读 closeout draft 报告；它不记录最终 policy wording，不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。

## v0.4.8.8 Final Evidence Selection Policy Language Revision Worksheet 补充

- `tests/test_final_evidence_selection_policy_language_revision_worksheet.py`：验证最终证据选择策略语言修订 worksheet 只读取 v0.4.8.7 confirmed record saved report，生成 3 条 revision rows，并阻断源确认记录漂移、实现授权泄漏、revision row 顺序/数量漂移、advisory/forbidden keys、可读性污染和运行时/后端模式。
- `tests/final_evidence_selection_policy_language_revision_worksheet_report.json`：由 `tools/build_final_evidence_selection_policy_language_revision_worksheet.py` 生成的只读 worksheet 报告；它不形成最终 wording，不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.7 Final Evidence Selection Policy Closeout Confirmed Record 补充

- `tests/test_final_evidence_selection_policy_closeout_confirmed_record.py`：验证最终证据选择策略收口确认记录只读取 v0.4.8.6 scaffold saved report，按用户明确确认生成 8 条 confirmed rows，并阻断源脚手架漂移、已确认/实现授权泄漏、row 顺序/数量/建议项漂移、advisory/forbidden keys、可读性污染和运行时/后端模式。
- `tests/final_evidence_selection_policy_closeout_confirmed_record_report.json`：由 `tools/build_final_evidence_selection_policy_closeout_confirmed_record.py` 生成的只读 confirmed record 报告；它不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.6 Final Evidence Selection Policy Closeout Confirmation Record Scaffold 补充

- `tests/test_final_evidence_selection_policy_closeout_confirmation_record.py`：验证最终证据选择策略收口确认记录脚手架只读取 v0.4.8.5 closeout decision draft saved report，生成 8 条 `pending_user_confirmation` rows，并阻断源报告漂移、正式结论/实现授权泄漏、row 顺序/数量漂移、advisory/forbidden keys、可读性污染和运行时/后端模式。
- `tests/final_evidence_selection_policy_closeout_confirmation_record_report.json`：由 `tools/build_final_evidence_selection_policy_closeout_confirmation_record.py` 生成的只读 confirmation scaffold 报告；它不记录 formal review outcome，不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.5 Final Evidence Selection Policy Closeout Decision Draft 补充

- `tests/test_final_evidence_selection_policy_closeout_decision_draft.py`：验证最终证据选择策略收口决策草案只读取 v0.4.8.4 closeout envelope saved report，生成 8 条 user-confirmation draft rows，并阻断源报告漂移、正式结论/实现授权泄漏、row 顺序/数量漂移、advisory/forbidden keys、可读性污染和运行时/后端模式。
- `tests/final_evidence_selection_policy_closeout_decision_draft_report.json`：由 `tools/build_final_evidence_selection_policy_closeout_decision_draft.py` 生成的只读 decision draft 报告；它不记录 formal review outcome，不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.4 Final Evidence Selection Policy Closeout Envelope 补充

- `tests/test_final_evidence_selection_policy_closeout_envelope.py`：验证最终证据选择策略收口外壳只读取 v0.4.8.3 human review worksheet saved report，生成 8 条 pending closeout rows，并阻断源报告漂移、正式结论/实现授权泄漏、row 顺序/数量漂移、advisory/forbidden keys、可读性污染和运行时/后端模式。
- `tests/final_evidence_selection_policy_closeout_envelope_report.json`：由 `tools/build_final_evidence_selection_policy_closeout_envelope.py` 生成的只读 closeout envelope 报告；它不记录 formal review outcome，不实现 runtime policy，也不修改 rerank、prompt、eval case 或 RAG 主流程。

更新日期：2026-05-16

## 定位与约定

本文档用于说明 `tests/` 下测试套件、报告快照、fixtures 和 dry run 中间产物的用途。它不是迁移计划，也不改变任何测试、报告或工具默认路径。

当前权威测试资产仍在 `tests/` 下：

- `tests/test_*.py`：单测入口。
- `tests/*.json`：当前主要评测、诊断、审阅、健康检查和 dry run 报告。
- `tests/*.csv`：人工复核工作台相关表格辅助文件。
- `tests/*.md`：评测或稳定性摘要。
- `tests/fixtures/`：单测夹具和小型样例输入。
- `tests/manual_review_export_pipeline_dry_run_artifacts/`：导出链路预演的隔离中间产物目录。

## 测试套件

### 工具维护与健康检查

- `tests/test_project_health_check.py`：项目轻量健康检查。
- `tests/test_tool_index_consistency.py`：工具索引覆盖与敏感入口检查。
- `tests/test_test_index_consistency.py`：测试索引覆盖检查。
- `tests/test_artifact_index_consistency.py`：产物索引覆盖检查。
- `tests/test_layout_migration_readiness.py`：目录迁移准备度检查。
- `tests/test_maintenance_closeout_report.py`：维护系列收束报告检查。
- `tests/test_encoding_hygiene.py`：编码卫生与临时目录诊断。
- `tests/test_layout_compatibility.py`：布局兼容层与 legacy `tests/` 路径契约。
- `tests/test_qdrant_index_integrity.py`：Qdrant 索引完整性工具测试。

### RAG、检索、入库与 rerank

- `tests/test_candidate_budget.py`
- `tests/test_retriever_contract.py`
- `tests/test_rerank_api.py`
- `tests/test_ingestion_quality.py`
- `tests/test_standard_ingestion.py`
- `tests/test_taxonomy.py`
- `tests/test_legal_functional_typing.py`
- `tests/test_legal_functional_type_config.py`
- `tests/test_legal_functional_typing_fixtures.py`
- `tests/test_legal_functional_typing_error_analysis.py`

### 风险、报告与引用

- `tests/test_risk_engine.py`
- `tests/test_risk_report.py`
- `tests/test_citation_integrity.py`

### Eval、scenario 与 gate

- `tests/test_hidden_eval_seed_cases.py`
- `tests/test_impact_eval.py`
- `tests/test_rag_eval_diagnostics.py`
- `tests/test_rag_stability_tools.py`
- `tests/test_scenario_eval.py`
- `tests/test_scenario_eval_gate.py`
- `tests/test_scenario_links.py`
- `tests/test_scenario_registry.py`
- `tests/test_scenario_registry_loader.py`
- `tests/test_scenario_registry_calibration.py`

### Evidence 诊断、覆盖与审计

- `tests/test_anchor_dependency_audit.py`
- `tests/test_base_retrieval_quality_audit.py`
- `tests/test_evidence_action_series_baseline.py`
- `tests/test_evidence_alignment.py`
- `tests/test_evidence_coverage.py`
- `tests/test_evidence_coverage_gate_draft.py`
- `tests/test_evidence_coverage_triage.py`
- `tests/test_evidence_enrichment_hardening.py`
- `tests/test_evidence_fixture_candidate_pool.py`
- `tests/test_evidence_manual_review_dataset.py`
- `tests/test_evidence_root_cause_action_plan.py`
- `tests/test_final_evidence_selection_audit.py`

### 人工复核、工作台与治理链路

- `tests/test_manual_review_action_candidates.py`
- `tests/test_manual_review_ai_suggestion_prefill.py`
- `tests/test_manual_review_decision_diff.py`
- `tests/test_manual_review_decision_examples.py`
- `tests/test_manual_review_decision_schema.py`
- `tests/test_manual_review_decision_validation.py`
- `tests/test_manual_review_export_pipeline_dry_run.py`
- `tests/test_manual_review_governance_report.py`
- `tests/test_manual_review_intake_gate_closeout.py`
- `tests/test_manual_review_loop.py`
- `tests/test_manual_review_pilot_batch.py`
- `tests/test_manual_review_pilot_case_review_assist.py`
- `tests/test_manual_review_prescreen_report.py`
- `tests/test_manual_review_progress_report.py`
- `tests/test_manual_review_visual_workbench.py`
- `tests/test_manual_review_visual_workbench_build_artifact.py`
- `tests/test_manual_review_visual_workbench_contract.py`
- `tests/test_manual_review_workbench_export.py`
- `tests/test_manual_review_workbench_import.py`
- `tests/test_mobile_pilot_review_decision_aid.py`
- `tests/test_pilot_manual_review_round1_support.py`
- `tests/test_proposed_manual_review_validation.py`
- `tests/test_final_evidence_selection_policy_intake.py`
- `tests/test_final_evidence_selection_policy_simulator_spec.py`
- `tests/test_final_evidence_selection_policy_table_draft.py`
- `tests/test_final_evidence_selection_policy_human_review_worksheet.py`
- `tests/test_ready_action_human_closeout_confirmation_record.py`
- `tests/test_ready_action_human_closeout_decision_draft.py`
- `tests/test_ready_action_design_review_closeout.py`
- `tests/test_ready_action_design_review_worksheet.py`
- `tests/test_ready_action_routing_dry_run.py`
- `tests/test_validated_decision_promotion_dry_run.py`
- `tests/test_workbench_intake_contract.py`

### 规则治理

- `tests/test_rule_convergence_plan.py`
- `tests/test_rule_debt_audit.py`

## 测试产物

### Eval 报告与 case 集合

- `tests/rag_eval_cases.json`、`tests/smoke_eval_cases.json`：评测输入题库。
- `tests/rag_eval_report.json`、`tests/smoke_eval_report.json`、`tests/targeted_eval_report.json`：RAG/smoke/targeted 评测报告。
- `tests/risk_eval_report.json`、`tests/report_eval_report.json`、`tests/impact_eval_report.json`：风险、报告和影响面评测报告。
- `tests/scenario_eval_report.json`、`tests/scenario_eval_summary.md`：scenario eval 报告与摘要。
- `tests/rag_stability_report.json`、`tests/rag_stability_summary.md`：稳定性报告与摘要。
- `tests/rerank_on.json`、`tests/rerank_off.json`：rerank 对照实验产物，不是配置开关。

### Evidence 报告

- `tests/evidence_alignment_report.json`
- `tests/evidence_coverage_report.json`
- `tests/evidence_coverage_triage_report.json`
- `tests/evidence_coverage_gate_draft_report.json`
- `tests/evidence_root_cause_action_plan.json`
- `tests/evidence_action_series_baseline.json`
- `tests/evidence_enrichment_hardening_report.json`
- `tests/evidence_fixture_candidate_pool.json`
- `tests/base_retrieval_quality_audit_report.json`
- `tests/anchor_dependency_audit_report.json`
- `tests/final_evidence_selection_audit_report.json`

### 人工复核 schema、数据集与工作台

- `tests/evidence_manual_review_dataset.json`
- `tests/evidence_manual_review_workbench.json`
- `tests/evidence_manual_review_workbench.csv`
- `tests/evidence_manual_review_decision_schema.json`
- `tests/evidence_manual_review_decision_validation_report.json`
- `tests/evidence_manual_review_action_candidates.json`
- `tests/evidence_manual_review_loop_report.json`
- `tests/evidence_manual_review_governance_report.json`
- `tests/evidence_manual_review_progress_report.json`
- `tests/manual_review_decision_examples.json`
- `tests/proposed_manual_review_decision_schema.json`
- `tests/proposed_manual_review_decision_validation_report.json`
- `tests/validated_decision_promotion_dry_run_report.json`

### 人工复核辅助、prefill 与 dry run

- `tests/manual_review_prescreen_report.json`
- `tests/manual_review_pilot_batch_report.json`
- `tests/manual_review_pilot_case_review_assist_report.json`
- `tests/pilot_manual_review_round1_support_report.json`
- `tests/mobile_pilot_review_decision_aid_report.json`
- `tests/manual_review_export_pipeline_dry_run_report.json`
- `tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json`
- `tests/manual_review_ai_suggestion_prefill_import_safety_check.json`
- `tests/manual_review_prefill_high_confidence_12.json`
- `tests/manual_review_prefill_high_confidence_12.csv`
- `tests/manual_review_prefill_high_confidence_12_import_report.json`
- `tests/manual_review_prefill_high_confidence_12_v2.json`
- `tests/manual_review_prefill_high_confidence_12_v2.csv`
- `tests/manual_review_prefill_high_confidence_12_v2_import_report.json`
- `tests/proposed_manual_review_decision_schema_ai_suggestion_safety_check.json`
- `tests/proposed_manual_review_decision_schema_prefill_high_confidence_12.json`
- `tests/proposed_manual_review_decision_schema_prefill_high_confidence_12_v2.json`
- `tests/proposed_manual_review_validation_prefill_high_confidence_12.json`
- `tests/proposed_manual_review_validation_prefill_high_confidence_12_v2.json`
- `tests/ready_action_routing_dry_run_report.json`
- `tests/final_evidence_selection_policy_intake_report.json`
- `tests/final_evidence_selection_policy_simulator_spec_report.json`
- `tests/final_evidence_selection_policy_table_draft_report.json`
- `tests/final_evidence_selection_policy_human_review_worksheet_report.json`
- `tests/ready_action_human_closeout_confirmation_record_report.json`
- `tests/ready_action_human_closeout_decision_draft_report.json`
- `tests/ready_action_design_review_closeout_report.json`
- `tests/ready_action_design_review_worksheet_report.json`
- `tests/manual_review_export_pipeline_dry_run_artifacts/`

### 维护、入库、规则与配置报告

- `tests/project_health_check_report.json`
- `tests/encoding_hygiene_report.json`
- `tests/tool_index_consistency_report.json`
- `tests/qdrant_index_integrity_report.json`
- `tests/ingestion_quality_report.json`
- `tests/legal_functional_type_config_report.json`
- `tests/legal_functional_typing_report.json`
- `tests/legal_functional_typing_error_analysis_report.json`
- `tests/legal_functional_typing_fixture_report.json`
- `tests/rule_debt_report.json`
- `tests/scenario_registry_calibration_report.json`

### Fixtures

- `tests/fixtures/legal_functional_typing_golden.json`
- `tests/fixtures/standard_sample.txt`

## Legacy 路径与布局契约

- 当前 `tests/` 仍是权威测试与报告路径。
- `reports/` 下的分组目录只是未来脚手架，不是当前默认输出位置。
- `tests/manual_review_export_pipeline_dry_run_artifacts/` 是隔离中间产物目录，不是正式人工复核结果目录。

## Advisory 与正式人工复核边界

- `manual_review_*pilot*`、`*_assist*`、`*_prefill*`、`*_suggestion*` 多数是辅助材料，不是正式人工复核结论。
- 正式人工复核结论必须来自人工填写并通过 importer、validator、promotion dry run 和 closeout gate 的记录。
- `proposed_manual_review_decision_schema*.json` 不能混同为最终人工复核事实源。

## 已知误读风险

- 部分 JSON 是历史诊断快照，不应默认当作可长期复用的配置源。
- `rerank_on.json` / `rerank_off.json` 是对照产物，不是开关。
- `evidence_fixture_candidate_pool.json` 是 fixture 候选池，不代表已经写入 eval case。
- `rag_stability_report.json` 体积较大，通常先阅读 `rag_stability_summary.md`。

## 重新生成入口

- Eval 报告：`tools/run_rag_eval.py`、`tools/run_risk_eval.py`、`tools/run_report_eval.py`、`tools/run_impact_eval.py`、`tools/run_scenario_eval.py`。
- Evidence 诊断：`tools/check_evidence_alignment.py`、`tools/check_evidence_coverage.py`、`tools/triage_evidence_coverage_loss.py`。
- 人工复核工作台：`tools/export_manual_review_workbench.py`、`tools/build_manual_review_visual_workbench.py`、`tools/import_manual_review_workbench.py`。
- 设计评审 worksheet：`tools/build_ready_action_design_review_worksheet.py`。
- 设计评审 closeout：`tools/build_ready_action_design_review_closeout.py`。
- 人工收口确认草案：`tools/build_ready_action_human_closeout_decision_draft.py`。
- 人工收口确认记录：`tools/build_ready_action_human_closeout_confirmation_record.py`。
- 最终证据选择策略 intake：`tools/build_final_evidence_selection_policy_intake.py`。
- 最终证据选择策略模拟器契约：`tools/build_final_evidence_selection_policy_simulator_spec.py`。
- 最终证据选择策略表草案：`tools/build_final_evidence_selection_policy_table_draft.py`。
- 最终证据选择策略人工复核 worksheet：`tools/build_final_evidence_selection_policy_human_review_worksheet.py`。
- 维护报告：`tools/check_encoding_hygiene.py`、`tools/check_tool_index_consistency.py`、`tools/run_project_health_check.py`。
