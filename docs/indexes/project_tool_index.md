# 项目工具索引
## v0.5.2 Controlled Experiment addendum

- `tools/judge_controlled_ablation.py`：只读 C0-C6 消融报告，验证相邻配置只改变一个开关、冻结案例哈希与汇总指标；不调用 RAG、Qdrant 或 LLM。
- `tools/summarize_robustness_perturbations.py`：只读已保存的改写扰动报告，输出扰动类别与配置的检索稳定性汇总；不调用 RAG、Qdrant 或 LLM。
- `tools/judge_core_tech_experiments.py`：汇总控制消融、ESG、鲁棒性、端到端抽样和科研图表的内部一致性；不衡量法律结论正确率或生产性能。
- `tools/build_controlled_experiment_assets.py`：从已完成的受控实验报告生成科研图表和摘要；只读取 JSON，不调用 RAG、Qdrant 或 LLM。

## v0.5.0 Index Maintenance addendum

- `tools/build_legal_staging_collection.py`：构建隔离的法律 staging collection，属于会访问 Qdrant 的敏感入口，须按其显式参数和运行前检查执行。
- `tools/judge_civil_code_coverage.py`：只读 Civil Code coverage 报告并输出覆盖判定，不调用 RAG、Qdrant 或 LLM。
- `tools/judge_developer_debug_run.py`：只读 developer debug run 报告并检查其结果结构，不调用 RAG、Qdrant 或 LLM。
- `tools/run_developer_debug_scenario.py`：执行开发调试场景，属于后端调试入口；应只在本地开发环境和明确输入下使用。

## Core Technology Ablation addendum

- `tools/run_rag_ablation.py`：在固定测试集上执行 M1_dense、M2_hybrid、M3_concept、M4_full 四档**仅检索**消融；输出每题证据、Recall@K、MRR、nDCG、多来源覆盖和延迟。会调用 `rag_query`、Qdrant、BM25 和 M4 的重排服务；只读知识库，不写入 Qdrant。
- `tools/judge_rag_ablation.py`：检查消融报告是否使用冻结测试集、四档配置和完整指标，并验证 M4 的主 Recall@K 不低于 M1；只读取 JSON，不调用 RAG、Qdrant 或 LLM。
- `tools/build_core_tech_report_assets.py`：把已完成的消融 JSON 转换为报告用 PNG 图和 Markdown 摘要；只读取报告，不调用 RAG、Qdrant 或 LLM。
- `tools/judge_evidence_sufficiency.py`：核验 Evidence Sufficiency Gate（ESG）报告的题级字段、汇总一致性和基准资格；明确将缺少期望证据的 smoke 检索指标标注为诊断用途。只读取 JSON，不调用 RAG、Qdrant 或 LLM。
- `tools/build_esg_report_assets.py`：将已完成的 ESG 报告转换为 300 dpi 报告图和 Markdown 摘要；只读取报告，不调用 RAG、Qdrant 或 LLM。
- `tools/recompute_rag_ablation_metrics.py`：从已保存的检索证据链和同一冻结题集离线重算检索指标，用于修正指标实现后保留原始检索结果与计时；校验题集哈希，不调用 RAG、Qdrant 或 LLM。
- `tools/check_research_figure_assets.py`：离线核验核心技术图表的文件完整性、2400×1350 尺寸、300 dpi 与 RGB/RGBA 色彩模式；只读 PNG 并输出 JSON，不调用 RAG、Qdrant、LLM 或网络。

## User-Defined Skill addendum

- `tools/build_skill_acceptance_evidence.py`：以临时 JSON 仓储离线执行 Skill 配置校验、CRUD、内置模板保护、执行计划与前端公开接口边界检查，输出供裁判读取的两份 JSON；不调用 RAG、Qdrant、LLM 或网络。
- `tools/judge_skill_module.py`：只读 Skill API 与运行验证 JSON，核验固定节点白名单、无环图、配置校验、CRUD、内置模板保护、前端边界和执行计划；不调用 RAG、Qdrant、LLM 或网络。

## v0.4.18.9 Product Backend Closeout addendum

- `tools/build_product_backend_closeout.py`：汇总既有 product backend contract、字段目录、状态目录和数据源边界，导出后端收口交接报告；不启动服务、不运行 eval、不调用 RAG/Qdrant/LLM、不接真实行情、地图或供应链数据。

## v0.4.18.8 Product Data Source Boundary addendum

- `tools/export_product_data_source_boundary.py`：导出 fixture-backed `/product/*` 后端的数据源/repository 边界目录；记录当前只连接 `fixture_sample`，并声明未来 RAG、行情、地图、供应链和权限 provider 只是预留槽位，不在本版本接入。

## v0.4.18.7 Product API Status Catalog addendum

- `tools/export_product_api_status_catalog.py`：导出 fixture-backed `/product/*` 接口成功状态、空结果语义和产品错误码目录；不启动服务、不调用 RAG/Qdrant/LLM、不接真实行情、地图或供应链数据。

## v0.4.18.6 Product API Field Catalog addendum

- `tools/export_product_api_field_catalog.py`：导出 fixture-backed `/product/*` 后端接口字段目录，覆盖 query params、response envelope、meta 字段和从 fixture 推导出的 response field paths；不启动服务、不调用 RAG/Qdrant/LLM、不接真实行情、地图或供应链数据。

## v0.4.18.5 Product API Backend Integration addendum

- `tools/check_product_api_contract.py`：使用 FastAPI `TestClient` 检查 fixture-backed `/product/*` 接口是否进入 OpenAPI、是否返回统一 envelope、是否标记 `data_source=fixture_sample` 和外部依赖 `not_called`；不启动服务、不调用 RAG/Qdrant/LLM、不接真实行情、地图或供应链数据。

## v0.4.18.4 Product Mock Endpoint Contract addendum

- `tools/check_product_mock_endpoint_contract.py`：从 v0.4.18.3 product view model fixture 派生并校验离线 product mock endpoint contract；检查只读 `GET`、`/product/` 命名空间、view model 引用、`risk_id` 引用和响应 envelope。v0.4.18.5 后 FastAPI surface 暴露由 `tools/check_product_api_contract.py` 负责验证 fixture-backed runtime 边界。不启动服务、不调用 RAG/Qdrant/LLM、不接真实行情、地图或供应链数据。

## v0.4.18.3 Product View Model Contract addendum

- `tools/check_product_view_model_contract.py`：校验离线 product view model fixture 的必填字段、guardrails、枚举、跨模块 `risk_id`、供应链 node/edge 和 lifecycle evidence 引用关系；不启动服务、不调用 RAG/Qdrant/LLM、不接真实行情或地图。

## v0.4.18.1 Legal Corpus Integrity Baseline addendum

- `tools/check_legal_corpus_integrity.py`：只读 `knowledge_manifest.json` 和 `src/knowledge/**/*.txt`，复用 `load_txt()` 检查 manifest、文件覆盖、核心 metadata、chunk 边界、citation、expected anchors、per-domain summary 和 high-risk manual review；不访问 Qdrant、不运行 eval、不调用 RAG/LLM、不修改知识库或 runtime。

## v0.4.17.5 Legal Text Version Verification addendum

- `tools/build_legal_text_version_verification_packet.py`：只读法律文本版本快照和 v0.4.17.4 review packet，核验《反不正当竞争法》混淆行为条文编号；不联网、不运行 eval、不调用 RAG/Qdrant/LLM、不修改 runtime 或 eval case。

## v0.4.17.4 RAG Expected-Level Review Packet addendum

- `tools/build_rag_expected_level_review_packet.py`：只读 targeted repeat 报告和现有 eval case 元数据，分类固定失败是否属于 expected-level/fact-strength review；不运行 eval，不调用 RAG/Qdrant/LLM，不修改 runtime 或 eval case。

## v0.4.17.2 RAG Targeted Rerun Packet addendum

- `tools/build_rag_targeted_rerun_packet.py`：只读 v0.4.17.1 evidence independence baseline，输出小批量 targeted rerun 候选、分组理由和建议命令；工具本身不运行 eval，不调用 RAG/Qdrant/LLM，不修改 runtime。

## v0.4.17.1 RAG Evidence Independence Baseline addendum

- `tools/build_rag_evidence_independence_baseline.py`：只读既有 RAG eval 保存报告，输出 anchor/risk supplement/term preservation/pure LLM 依赖归因、依赖热区和下一步 triage 候选；不运行 eval、不调用 RAG/Qdrant/LLM、不修改 runtime。

## v0.4.16.11 API Contract Consistency Checker addendum

- `tools/check_api_contract_consistency.py`：离线检查 OpenAPI schema、API contract bundle、API field catalog 与 example payload fixture 是否一致；不启动服务，不调用 RAG、Qdrant、LLM 或真实报告生成。

## v0.4.16.10 API Field Catalog addendum

- `tools/export_api_field_catalog.py`：离线导出请求/响应模型字段目录、必填项和默认值。

## v0.4.16.8 API Contract Bundle addendum

- `tools/export_api_contract_bundle.py`：离线导出 API contract bundle，合并当前 OpenAPI schema 与 example payload fixture；不启动服务，不调用 RAG、Qdrant、LLM 或报告生成。

## v0.4.16.3 OpenAPI Schema Snapshot addendum

- `tools/export_openapi_schema.py`：离线导出 FastAPI OpenAPI schema；默认输出路径跟随当前 `app.version`，历史 v0.4.16.3 快照保留在 `tests/openapi_schema_v0.4.16.3.json`；不启动服务，不调用 RAG、Qdrant、LLM 或报告生成。

## v0.4.15.26 Process Over-Risk Runtime Hardening addendum

- 未新增 CLI 工具。
- 运行时修复范围：`src/rag/retriever.py` 的 risk payload 后处理。
- 关键产物：`tests/targeted_process_overrisk_trace_v0.4.15.26_report.json`、`tests/targeted_process_overrisk_patch_v0.4.15.26_report.json`、`tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json`、`tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json` 和 `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json`。
- 边界：未修改 hidden seed、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures、eval cases、Qdrant 或 evidence selector。

## v0.4.15.25 Trademark Over-Risk Runtime Patch addendum

- No new CLI tool.
- Validation uses existing `tools/run_rag_eval.py` for targeted and compact full eval.
- Key outputs: `tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json` and `tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json`.
- Boundary: runtime change is limited to `src/rag/retriever.py`; no anchor, prompt, rerank, risk supplement, term preservation, eval case, hidden seed, or Qdrant change.

## v0.4.15.24 Risk Level Over-Risk Legal Review Packet addendum

- `tools/build_risk_level_overrisk_legal_review_packet.py`: saved-report-only legal review packet builder for exact-policy `over_risk` cases.
- Key output: `tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json`.
- Boundary: reads saved eval reports, attribution reports, eval case metadata, and optional scenario registry only; does not run eval, call `rag_query`, access Qdrant/LLM, or mutate retrieval, anchors, prompts, rerank, taxonomy, risk supplement rules, fixtures, eval cases, scenario registry, or hidden seeds.

## v0.4.15.23 Risk Level Over-Risk Attribution addendum

- `tools/build_risk_level_overrisk_attribution.py`: saved-report-only attribution builder for exact-policy `over_risk` cases.
- Key output: `tests/risk_level_overrisk_attribution_v0.4.15.23_report.json`.
- Boundary: reads saved eval reports only; does not run eval, call `rag_query`, access Qdrant/LLM, or mutate retrieval, anchors, prompts, rerank, taxonomy, risk supplement rules, fixtures, or eval cases.

## v0.4.15.20 Base Candidate Dense Live Probe addendum

- `tools/build_base_candidate_dense_live_probe.py`: explicit dense-enabled wrapper around the live read-only probe for dense rank/cutoff attribution.
- Key output: `tests/base_candidate_dense_live_probe_v0.4.15.20_report.json`.
- Boundary: read-only Qdrant access; dense query embedding is explicit opt-in; no `rag_query`, eval, LLM/reranker, runtime mutation, or Qdrant write.

## v0.4.15.19 Base Candidate Live Read-Only Probe addendum

- `tools/build_base_candidate_live_readonly_probe.py`: targeted Qdrant live read-only probe for payload existence, runtime metadata filters, sparse high-k visibility, and base union reconstruction.
- Key output: `tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json`.
- Boundary: read-only Qdrant access only; does not write Qdrant, run eval, call `rag_query`, call LLM/reranker, or mutate runtime configuration. Dense probe is explicit opt-in.

## v0.4.15.18 Base Candidate Mismatch Summary addendum

- `tools/build_base_candidate_mismatch_summary.py`: saved-report-only summary for base union candidate source/article drift, missing final refs, source distribution, and query overlap.
- Key output: `tests/base_candidate_mismatch_summary_v0.4.15.18_report.json`.
- Boundary: does not run eval, call `rag_query`, access Qdrant/LLM, or mutate runtime configuration.

## v0.4.15.17 Base Retrieval / Query Inspection addendum

- `tools/build_base_retrieval_query_inspection.py`: saved-report-only inspection for base union retrieval gaps, query lexical hints, and anchor-filled final refs.
- Key output: `tests/base_retrieval_query_inspection_v0.4.15.17_report.json`.
- Boundary: does not run eval, call `rag_query`, access Qdrant/LLM, or mutate runtime configuration.

## v0.4.15.16 Dependency Trace Summary addendum

- `tools/build_dependency_trace_summary.py`: saved-report-only summary builder for full-debug dependency trace packets.
- Trace input artifact: `tests/targeted_dependency_trace_v0.4.15.16_report.json`.
- Key output: `tests/dependency_trace_summary_v0.4.15.16_report.json`.
- Boundary: does not run eval, call `rag_query`, access Qdrant/LLM, or mutate runtime configuration.

## v0.4.15.15 RAG Quality Triage addendum

- `tools/build_rag_quality_triage.py`: saved-report-only triage builder for pass quality, contribution dependency, quality signals, and manual-review markers.
- Key output: `tests/rag_quality_triage_v0.4.15.15_report.json`.
- Boundary: does not run eval, call `rag_query`, access Qdrant/LLM, or mutate runtime configuration.

## v0.4.15.14 Roadmap Maintenance & Compact Eval Baseline addendum

- No new CLI tool.
- Validation uses existing `tools/run_rag_eval.py --compact-report` to produce `tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json`.
- Roadmap maintenance is documentation-only and does not change runtime paths.

## v0.4.15.13 RAG Eval Compact Report Profile addendum

- `tools/run_rag_eval.py`: adds opt-in `--compact-report`; default saved reports remain full.
- Compact output removes full per-case `debug_info` and `contribution_trace`, while preserving `retrieval_diagnostics`, `quality_signal_diagnostics`, and summary counts.
- Key output: `tests/targeted_compact_report_profile_v0.4.15.13_report.json`.

## v0.4.15.12 Same-Bucket Signal Calibration addendum

- `tools/run_rag_eval.py`: `quality_signal_diagnostics` now records same-bucket alternatives as `score_order_observations` and upgrades only coverage-critical candidates to `score_order_risks` / `same_bucket_selection_order_risk`.
- Key outputs: `tests/targeted_same_bucket_baseline_v0.4.15.12_report.json`, `tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json`, `tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json`, `tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json`.

## v0.4.15.11 Hidden-Seed Signal Diagnostics & Output Stability addendum

- 本版本无新增 CLI 工具；扩展既有 `tools/run_rag_eval.py`，在每个 case 报告中写入 `quality_signal_diagnostics`。
- 关键输出：`tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json`、`tests/targeted_output_stability_v0.4.15.11_report.json`、`tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json`。
- 边界：新增诊断只写报告，不改变 `rag_query` 检索、rerank、anchor、prompt、risk supplement、eval cases、hidden seed 或 Qdrant。

## v0.4.15.10 Standard Contract Term Preservation addendum

- 本版本无新增 CLI 工具；验证入口继续使用既有 `tools/run_rag_eval.py`。
- 关键输出：`tests/targeted_data_export_term_preservation_v0.4.15.10_report.json`、`tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json`、`tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json`。
- 边界：不修改 prompt、anchor、risk supplement、hidden seed、scenario registry、fixtures、eval cases、rerank 或 Qdrant。

## v0.4.15.9 Main-Chain Stability Closeout addendum

- 本版本无新增 CLI 工具；验证入口继续使用既有 `tools/run_rag_eval.py`。
- 关键输出：`tests/targeted_main_chain_stability_v0.4.15.9_report.json`、`tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json`、`tests/targeted_data_export_answer_stability_v0.4.15.9_report.json`。
- 边界：不新增 gate，不修改 retriever、rerank、prompt、anchor、risk supplement、term preservation、hidden seed、scenario registry、fixtures 或 eval cases。

## v0.4.15.8 Main-Chain Repair addendum

- 本版本无新增 CLI 工具；运行时修复位于 `src/rag/retriever.py` 与 `src/risk/taxonomy.py`。
- 验证入口继续使用既有 `tools/run_rag_eval.py`。
- 关键输出：`tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json`、`tests/targeted_post_near_tie_regression_v0.4.15.8_report.json`、`tests/targeted_antitrust_risk_level_v0.4.15.8_report.json`、`tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json`。
- 边界：不新增工具、不新增 gate、不修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases；不写 Qdrant、不 rebuild。

## v0.4.15.7 Near-Tie Patch Closeout addendum

- `tools/build_post_rebuild_near_tie_patch_closeout.py`: saved-report-only closeout builder that reads the v0.4.15.6 targeted repeat, patch validation, and project health reports.
- Default outputs: `tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json` and `docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md`.
- Boundary: no eval execution, no `rag_query`, no Qdrant, no LLM, no runtime patch, and no hidden seed, anchor, prompt, rerank score, risk supplement, term preservation, scenario registry, fixture, or eval case mutation.

## v0.4.15.6 Near-Tie Runtime Patch Validation addendum

- `tools/build_post_rebuild_near_tie_patch_validation.py`: saved-report-only validator for the post-patch targeted repeat report; it checks whether same-bucket deterministic ordering stabilizes final evidence identity and fails closed when the repeat report is missing.
- Default outputs: `tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json` and `docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md`.
- Boundary: no eval execution, no `rag_query`, no Qdrant, no LLM, no hidden seed, anchor, prompt, rerank score, risk supplement, term preservation, scenario registry, fixtures, or eval case mutation.

## v0.4.15.5 Post-Rebuild Near-Tie Stability Policy Design 补充

- `tools/build_post_rebuild_near_tie_stability_policy_design.py`: 只读取 v0.4.15.4 trace attribution saved report，输出 near-tie stability policy 设计、禁区和后续实现 gate。
- 默认输出：`tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json` 和 `docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md`。
- 边界：design-only；不运行 eval，不调用 `rag_query`，不连接 Qdrant，不调用 LLM，不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.15.4 Post-Rebuild Selection Trace Attribution 补充

- `tools/build_post_rebuild_selection_trace_attribution.py`: 只读取 v0.4.15.4 targeted trace saved report，汇总 `risk_algorithm_bias_001` 第三席 final evidence 漂移的 full rerank order 与 selection trace 归因。
- 默认输出：`tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json` 和 `docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md`。
- 边界：不运行 eval，不调用 `rag_query`，不连接 Qdrant，不调用 LLM，不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.15.3 Post-Rebuild Selection Trace Readiness 补充

- `tools/build_post_rebuild_selection_trace_readiness.py`: 使用 synthetic documents 检查 `debug_info.rerank_full_score_order` 与 `debug_info.final_evidence_selection_trace` 的字段结构和 selector 行为边界。
- 默认输出：`tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json` 和 `docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md`。
- 边界：不运行 eval，不调用 `rag_query`，不连接 Qdrant，不调用 LLM，不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.15.2 Post-Rebuild Final Evidence Drift Attribution 补充

- `tools/build_post_rebuild_final_evidence_drift_attribution.py`: 只读取 targeted repeat saved report、v0.4.15.1 triage 和 eval case metadata，归因 `risk_algorithm_bias_001` 的 final evidence 第三席漂移。
- 默认输出：`tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json` 和 `docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md`。
- 边界：不运行 eval，不调用 `rag_query`，不连接 Qdrant，不调用 LLM，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.15.1 Post-Rebuild Repeat Instability Triage 补充

- `tools/build_post_rebuild_repeat_instability_triage.py`: 只读取 targeted repeat saved reports、v0.4.15.0 repeat baseline/summary 和 v0.4.14.34 单次 baseline，生成两类 repeat instability 的 targeted triage。
- 默认输出：`tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json` 和 `docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md`。
- 边界：builder 不运行 eval，不调用 `rag_query`，不连接 Qdrant，不调用 LLM，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.15.0 Post-Rebuild Repeat Stability Summary 补充

- `tools/build_post_rebuild_repeat_stability_summary.py`: 只读取 repeat full RAG eval saved report、v0.4.14.34 单次 baseline 和可选 eval case metadata，生成 post-rebuild repeat 稳定性摘要。
- 默认输出：`tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json` 和 `docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md`。
- 边界：不运行 full eval，不调用 `rag_query`，不连接 Qdrant，不调用 LLM，不修改 anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.14.35 Production Rebuild / Post-Rebuild Series Closeout 补充

- `tools/build_production_rebuild_post_rebuild_series_closeout.py`: 只读取 v0.4.14.29-v0.4.14.34 saved reports，生成生产重建与 post-rebuild RAG 质量链条收口报告。
- 默认输出：`tests/production_rebuild_post_rebuild_series_closeout_report.json` 和 `docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md`。
- 边界：saved reports only；不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk supplement、term preservation、scenario registry、fixtures 或 eval cases；不是新的 gate。

## v0.4.14.34 Post-Rebuild Alignment Retention Tightening 补充

- 本版本无新增 CLI 工具；运行时改动位于 `src/rag/retriever.py` 的 final evidence selector。
- 验证入口继续使用既有 `tools/run_rag_eval.py`；正式输出为 `tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`，60/60 passed。
- 边界：不新增 anchor、不修改 rerank/prompt/risk supplement/term preservation/eval case；不接入新的 gate，也不新增主链路外的补样本工具。

## v0.4.14.33 Post-Rebuild Alignment Retention Delta 补充

- `tools/build_post_rebuild_alignment_retention_delta.py`: 只读比较 `tests/post_rebuild_rag_eval_report.json` 与 `tests/post_rebuild_rag_eval_after_alignment_retention_report.json`，并结合 `tests/rag_eval_cases.json` 的 expected evidence metadata 输出 evidence delta、risk flags 和 recommended triage。
- 默认输出：`tests/post_rebuild_alignment_retention_delta_report.json` 和 `docs/post_rebuild_alignment_retention_delta_v0.4.14.33.md`。
- 边界：saved reports only；不调用 RAG/Qdrant/LLM，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

## v0.4.14.32 Post-Rebuild Evidence Alignment Retention 补充

- 本版本无新增 CLI 工具；运行时改动位于 `src/rag/retriever.py` 的 final evidence selector。
- 验证入口继续使用既有 `tools/run_rag_eval.py`，输出 `tests/post_rebuild_rag_eval_after_alignment_retention_report.json`。
- 边界：不新增 anchor、不修改 rerank/prompt/risk supplement/eval case；不扩大 evidence_chain 数量。

## v0.4.14.31 Post-Rebuild Full RAG Eval Summary 补充

- `tools/build_post_rebuild_rag_eval_summary.py`: 读取 post-rebuild full RAG eval 报告和 baseline full RAG eval 报告，汇总 passed/failed、baseline 回归、failed checks、retrieval stage、issue type 和下一步 triage 建议。
- 默认输出：`tests/post_rebuild_rag_eval_summary_report.json` 和 `docs/post_rebuild_rag_eval_summary_v0.4.14.31.md`。
- 边界：summary builder 只读 saved reports；不调用 RAG/Qdrant/LLM，不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

## v0.4.14.30 Post-Rebuild Quality Summary 补充

- `tools/build_post_rebuild_quality_summary.py`: 读取重建后的 smoke eval 报告、baseline smoke eval 报告和 production rebuild post-validation 报告，汇总 smoke 是否保持全通过、是否出现 baseline 回归、metadata 验证是否通过。
- 默认输出：`tests/post_rebuild_quality_summary_report.json` 和 `docs/post_rebuild_quality_summary_v0.4.14.30.md`。
- 边界：saved-report summary only；不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

## v0.4.14.29 Production Rebuild Execution 补充

- `tools/run_production_rebuild_execution.py`: 在正式授权记录和已通过只读 preflight 基础上调用既有 `rag_admin.py --rebuild`，并记录生产重建前后 Qdrant collection 状态、manifest 覆盖、命令结果和 snapshot reference。
- 默认输出：`tests/production_rebuild_execution_report.json`。
- `tools/check_production_rebuild_post_validation.py`: 生产重建后的只读验证工具；扫描重建后的 `legal_knowledge` payload，确认点数与执行记录一致，并抽查 article/paragraph/item/standard_section 是否具备 `chunk_index/chunk_count`。
- 默认输出：`tests/production_rebuild_post_validation_report.json`。
- 边界：authorized production rebuild execution and read-only post-validation；执行工具会写 Qdrant 并 rebuild collection，验证工具只读；不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases；不运行 full eval。

## v0.4.14.28 Production Rebuild Authorization Record Intake 补充

- `tools/run_production_rebuild_live_preflight.py`: 在正式只读 live preflight runner 中新增 `--authorization-record <json>`；可从授权记录读取 `authorization_status`、`authorization_reference`、`target_collection`、`backup_or_snapshot_reference` 与 `source_lineage_reference`。
- 默认授权记录输入：`tests/production_rebuild_authorization_record.json`（由命令显式传入，不自动读取）。
- 默认输出：`tests/production_rebuild_live_preflight_report.json`。
- 边界：authorization record intake only；只解除只读 preflight 的授权阻断，不授予 `qdrant_write_allowed`、`production_rebuild_allowed` 或 `authorization_granted`；授权记录如携带 `commands`、`authorized_actions`、`rebuild_steps`、`ready_to_apply`、`qdrant_write_allowed`、`production_rebuild_allowed` 等执行型字段则 fail-closed；不写 Qdrant，不切换 collection，不执行 production rebuild。

## v0.4.14.27 Production Rebuild Read-Only Live Preflight Runner 补充

- `tools/run_production_rebuild_live_preflight.py`: 正式只读 live preflight runner；显式传入 `--run-readonly-live-preflight` 后读取 `legal_knowledge` collection 元信息、point count 和 1 条 payload 样本，并输出正式 preflight report。
- 默认输出：`tests/production_rebuild_live_preflight_report.json`。
- 边界：read-only live preflight only；只调用 `get_collection`、`count`、`scroll(with_vectors=False, limit=1)`；不写 Qdrant，不创建/删除/恢复 snapshot，不切换 collection/alias，不调用 RAG/embedding/LLM/full eval，不执行 production rebuild。
- `tools/run_production_rebuild_live_preflight_real_readonly_probe.py`: 继续保留独立真实只读 probe 入口，并在 v0.4.14.27 透传 `authorization_reference`，与正式 runner 的授权判断保持一致。

## v0.4.14.26 Production Rebuild Formal Authorization Gate 补充

- `tools/check_production_rebuild_formal_authorization_gate.py`: 只读取 snapshot capture 与真实只读 preflight saved reports，检查正式 production rebuild 授权是否已被接受；当前默认 blocked 于 `authorization_record_not_accepted`。
- 默认输出：`tests/production_rebuild_formal_authorization_gate_report.json`。
- 边界：saved-report-only；不访问 Qdrant，不创建/删除/恢复 snapshot，不写入 collection points，不切换 collection/alias，不调用 RAG/LLM/eval，也不接入主链路或执行 rebuild。

## v0.4.14.25 Production Rebuild Live Preflight Snapshot Create Reference Capture 补充

- `tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py`: 在用户明确授权并提供 `--authorized-snapshot-create` 后，为 `legal_knowledge` 创建 Qdrant collection snapshot，并捕获可用于后续 fail-closed preflight 的 `backup_or_snapshot_reference`。
- 默认输出：`tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json`。
- 边界：authorized collection snapshot creation only；只允许 `list_snapshots -> create_snapshot(wait=True) -> list_snapshots`；不删除或恢复 snapshot，不写 collection points，不切换 collection，不调用 RAG、embedding、LLM 或 full eval，不执行 production rebuild。

## v0.4.14.24 Production Rebuild Live Preflight Snapshot Reference Probe 补充

- `tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py`: 复用 `src.core.vectorstore.get_qdrant_client()` 只读查询 `legal_knowledge` collection 的现有 Qdrant snapshots，只调用 `list_snapshots(collection_name)`，并输出是否存在可用于 preflight 的 `backup_or_snapshot_reference`。
- 默认输出：`tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json`。
- 边界：real read-only snapshot reference probe only；不创建、删除或恢复 snapshot；不写 Qdrant；不切换 collection；不调用 RAG、embedding、LLM 或 full eval；不授权 production rebuild。

## v0.4.14.23 Production Rebuild Live Preflight Real Read-Only Probe 补充

- `tools/run_production_rebuild_live_preflight_real_readonly_probe.py`: 复用 `src.core.vectorstore.get_qdrant_client()` 执行真实 Qdrant 只读 preflight probe，只调用 `get_collection`、`count`、`scroll(with_vectors=False, limit=1)`，并将结果注入 fail-closed preflight scaffold。
- 默认输出：`tests/production_rebuild_live_preflight_real_readonly_probe_report.json`。
- 边界：real read-only probe only；不调用 ingestion/retriever/RAG，不写 Qdrant，不切换 collection，不创建或接受正式授权记录，不执行 production rebuild，不运行 embedding、LLM 或 full eval。
## v0.4.14.22 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Gate 补充

- `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py`: 只读取 v0.4.14.21 scaffold report 并扫描 runner/test 源码，检查 version、schema、summary、guardrails、正式 live preflight 输出未创建、runtime import 禁止、write/rebuild 参数禁止和 mock-only 测试覆盖。
- 默认输出：`tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json` 和 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md`。
- 边界：gate only；不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval。
## v0.4.14.21 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold 补充

- `tools/run_production_rebuild_live_preflight.py`: 最小 runner scaffold，提供 `build_live_preflight_report(...)` 和 scaffold status report；核心逻辑只接受注入的 `qdrant_readonly_probe`，默认无 live probe，不导入 `qdrant_client`，不授权写入或 rebuild。
- 默认 scaffold 输出：`tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json`；正式 live preflight 输出路径 `tests/production_rebuild_live_preflight_report.json` 仍未创建。
- 边界：mock-only scaffold；不运行 live preflight，不访问真实 Qdrant，不写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval。
## v0.4.14.20 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design Gate 补充

- `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py`: 只读取 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json`，检查 v0.4.14.19 scaffold design 的 lineage、summary、guardrails、future files、contract、placeholder tests、forbidden scaffold content 和 forbidden output key 边界。
- 默认输出：`tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json` 和 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md`。
- 边界：gate only；不创建 runner 文件、未来测试文件或未来输出报告，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval。
## v0.4.14.19 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design 补充

- `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py`: 只读取 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json`，设计未来 runner scaffold 的文件结构、不可执行占位策略、mock-only test shape、fail-closed defaults 和禁止内容。
- 默认输出：`tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json` 和 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md`。
- 边界：scaffold design only；不创建 runner 文件、未来测试文件或未来输出报告，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.14.18 Production Rebuild Live Preflight Runner Minimal Implementation Design Gate 补充

- `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py`: 只读取 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json`，检查 v0.4.14.17 design 的 lineage、summary、guardrails、future files、CLI/function contract、read-only strategy、mock test strategy、fail-closed rules 和 forbidden output key 边界。
- 默认输出：`tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json` 和 `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_v0.4.14.18.md`。
- 边界：gate only；不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.17 Production Rebuild Live Preflight Runner Minimal Implementation Design 补充

- `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py`: 只读取 `tests/production_rebuild_live_preflight_runner_design_gate_report.json`，设计未来 runner 的文件边界、CLI/函数契约、只读策略、mock 测试策略和 fail-closed 规则。
- 默认输出：`tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json` 和 `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_v0.4.14.17.md`。
- 边界：implementation design only；不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.16 Production Rebuild Live Preflight Runner Design Gate 补充

- `tools/check_production_rebuild_live_preflight_runner_design_gate.py`: 只读取 `tests/production_rebuild_live_preflight_runner_design_report.json`，检查 v0.4.14.15 design 的 lineage、summary、guardrails、future inputs、preflight checks、output fields、blocking conditions、fail-closed contract 和 scaffold cutoff policy。
- 默认输出：`tests/production_rebuild_live_preflight_runner_design_gate_report.json` 和 `docs/production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md`。
- 边界：gate only；不创建 runner，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts，不继续扩 `input/importer scaffold`。

## v0.4.14.15 Production Rebuild Live Preflight Runner Design 补充

- `tools/build_production_rebuild_live_preflight_runner_design.py`: 只读取 `tests/production_rebuild_readiness_cutoff_report.json`，定义未来 live preflight runner 的最小输入、检查项、输出字段和阻断条件。
- 默认输出：`tests/production_rebuild_live_preflight_runner_design_report.json` 和 `docs/production_rebuild_live_preflight_runner_design_v0.4.14.15.md`。
- 边界：design only；不创建 runner，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts，不继续扩 `input/importer scaffold`。

## v0.4.14.14 Production Rebuild Readiness Cutoff 补充

- `tools/build_production_rebuild_readiness_cutoff.py`: 只读取 source patch、post-patch dry-run、authorization、execution design、input scaffold gate 与 project health saved reports，判断是否应停止继续扩 `input/importer scaffold` 链条，并开放 live preflight runner design。
- 默认输出：`tests/production_rebuild_readiness_cutoff_report.json` 和 `docs/production_rebuild_readiness_cutoff_v0.4.14.14.md`。
- 边界：cutoff only；不创建 importer，不收集、导入、解析、标准化或校验真实人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion/retriever/rerank/prompt/anchors/risk rules/scenario registry/eval cases/runtime artifacts。

## v0.4.14.13 Human Rebuild Authorization Record Input Form Scaffold Gate 补充

- `tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py`: 只读取 `tests/human_rebuild_authorization_record_input_form_scaffold_report.json`，检查 v0.4.14.12 空白 input form scaffold 的版本、schema、source lineage、guardrails、分区、字段、中文标签、未来控件提示、form completion/export policy、handoff 和 forbidden output key 边界。
- 默认输出：`tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json` 和 `docs/human_rebuild_authorization_record_input_form_scaffold_gate_v0.4.14.13.md`。
- 边界：read-only gate；不创建可运行输入表单或 importer，不收集、导出、导入、解析、标准化或校验真实人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.12 Human Rebuild Authorization Record Input Form Scaffold 补充

- `tools/build_human_rebuild_authorization_record_input_form_scaffold.py`: 只读取 `tests/human_rebuild_authorization_record_input_packet_scaffold_report.json` 与 `tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json`，生成未来人工授权输入表单的空白 scaffold；字段包含中文标签、未来控件提示、必填状态和帮助文本，但所有字段保持不可编辑、`not_collected` / `null`。
- 默认输出：`tests/human_rebuild_authorization_record_input_form_scaffold_report.json` 和 `docs/human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md`。
- 边界：blank form scaffold only；不创建可运行输入表单或 importer，不收集、导入、解析、标准化、导出或校验真实人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.11 Human Rebuild Authorization Record Input Packet Scaffold Gate 补充

- `tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py`: 只读取 `tests/human_rebuild_authorization_record_input_packet_scaffold_report.json`，检查 v0.4.14.10 空白 input packet scaffold 的版本、schema、source lineage、guardrails、字段行、分区、future validation/import policy、packet completion policy、handoff 和 forbidden output key 边界。
- 默认输出：`tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json` 和 `docs/human_rebuild_authorization_record_input_packet_scaffold_gate_v0.4.14.11.md`。
- 边界：read-only gate；不创建输入表单或 importer，不收集、导入、解析、标准化或校验真实人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.10 Human Rebuild Authorization Record Input Packet Scaffold 补充

- `tools/build_human_rebuild_authorization_record_input_packet_scaffold.py`: 只读取 `tests/human_rebuild_authorization_record_input_workflow_design_report.json` 与 `tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json`，生成未来人工授权输入包的空白 scaffold；所有字段保持 `not_collected` / `null`，不创建真实输入表单或 importer。
- 默认输出：`tests/human_rebuild_authorization_record_input_packet_scaffold_report.json` 和 `docs/human_rebuild_authorization_record_input_packet_scaffold_v0.4.14.10.md`。
- 边界：blank scaffold only；不收集、导入、解析、标准化或校验真实人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.9 Human Rebuild Authorization Record Input Workflow Design Gate 补充

- `tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py`: 只读取 `tests/human_rebuild_authorization_record_input_workflow_design_report.json`，检查 v0.4.14.8 input workflow design 的版本、schema、source lineage、guardrails、流程阶段、字段输入契约、future validation/import policy、handoff 和 forbidden output key 边界。
- 默认输出：`tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json` 和 `docs/human_rebuild_authorization_record_input_workflow_design_gate_v0.4.14.9.md`。
- 边界：gate only；不收集人工值，不创建输入表单或 importer，不导入或校验真实审批值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.8 Human Rebuild Authorization Record Input Workflow Design 补充

- `tools/build_human_rebuild_authorization_record_input_workflow_design.py`: 只读取 `tests/human_rebuild_authorization_record_draft_scaffold_report.json` 与 `tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json`，设计未来人工输入、导入、校验和确认流程；不收集真实人工值，不创建输入表单或 importer，不创建正式授权记录。
- 默认输出：`tests/human_rebuild_authorization_record_input_workflow_design_report.json` 和 `docs/human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md`。
- 边界：workflow design only；不收集人工值，不导入审批值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.7 Human Rebuild Authorization Record Draft Scaffold Gate 补充

- `tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py`: 只读取 `tests/human_rebuild_authorization_record_draft_scaffold_report.json`，检查 v0.4.14.6 空白 draft scaffold 的版本、schema、source lineage、guardrails、字段顺序、分区、空值、future validation policy、handoff 和 forbidden output key 边界。
- 默认输出：`tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json` 和 `docs/human_rebuild_authorization_record_draft_scaffold_gate_v0.4.14.7.md`。
- 边界：gate only；不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.6 Human Rebuild Authorization Record Draft Scaffold 补充

- `tools/build_human_rebuild_authorization_record_draft_scaffold.py`: 只读取 `tests/human_rebuild_authorization_record_draft_design_report.json` 与 `tests/human_rebuild_authorization_record_draft_design_gate_report.json`，生成未来正式授权记录的空白草案 scaffold；所有字段保持 `not_collected` / `null`，不创建正式授权记录。
- 默认输出：`tests/human_rebuild_authorization_record_draft_scaffold_report.json` 和 `docs/human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md`。
- 边界：blank draft scaffold only；不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.5 Human Rebuild Authorization Record Draft Design Gate 补充

- `tools/check_human_rebuild_authorization_record_draft_design_gate.py`: 只读取 `tests/human_rebuild_authorization_record_draft_design_report.json`，检查 v0.4.14.4 draft design 的版本、schema、source lineage、guardrails、字段映射、分区结构、future validation policy、handoff 和 forbidden output key 边界。
- 默认输出：`tests/human_rebuild_authorization_record_draft_design_gate_report.json` 和 `docs/human_rebuild_authorization_record_draft_design_gate_v0.4.14.5.md`。
- 边界：gate only；不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.4 Human Rebuild Authorization Record Draft Design 补充

- `tools/build_human_rebuild_authorization_record_draft_design.py`: 只读取 `tests/human_rebuild_authorization_record_scaffold_report.json` 与 `tests/human_rebuild_authorization_record_scaffold_gate_report.json`，设计未来正式授权记录草案的字段映射、分区结构和未来校验口径；不收集人工值，不创建正式授权记录。
- 默认输出：`tests/human_rebuild_authorization_record_draft_design_report.json` 和 `docs/human_rebuild_authorization_record_draft_design_v0.4.14.4.md`。
- 边界：draft design only；不收集人工值，不接受授权，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.3 Human Rebuild Authorization Record Scaffold Gate 补充

- `tools/check_human_rebuild_authorization_record_scaffold_gate.py`: 只读取 `tests/human_rebuild_authorization_record_scaffold_report.json`，检查 v0.4.14.2 空白 scaffold 的版本、schema、source lineage、guardrails、字段顺序、空白值、packet、handoff 和 assertions。
- 默认输出：`tests/human_rebuild_authorization_record_scaffold_gate_report.json` 和 `docs/human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md`。
- 边界：gate only；不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.2 Human Rebuild Authorization Record Scaffold 补充

- `tools/build_human_rebuild_authorization_record_scaffold.py`: 只读取 `tests/production_rebuild_execution_design_report.json` 与 `tests/production_rebuild_execution_design_gate_report.json`，生成未来人工授权记录的空白 scaffold；所有人工值保持 `not_collected`，不创建正式授权记录。
- 默认输出：`tests/human_rebuild_authorization_record_scaffold_report.json` 和 `docs/human_rebuild_authorization_record_scaffold_v0.4.14.2.md`。
- 边界：scaffold only；不收集人工值，不接受授权，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.1 Production Rebuild Execution Design Gate 补充

- `tools/check_production_rebuild_execution_design_gate.py`: 只读取 `tests/production_rebuild_execution_design_report.json`，验证 v0.4.14.0 design 的 source lineage、record contracts、preflight checks、abort conditions、guardrails 与 handoff boundary。
- 默认输出：`tests/production_rebuild_execution_design_gate_report.json` 和 `docs/production_rebuild_execution_design_gate_v0.4.14.1.md`。
- 边界：gate only；不创建或接受人工授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.14.0 Production Rebuild Execution Design 补充

- `tools/build_production_rebuild_execution_design.py`: 只读取 v0.4.13.18 closeout report，设计未来生产 rebuild execution series 的记录契约、preflight/rollback/validation/acceptance 门禁顺序；不创建授权记录，不运行 live preflight，不访问 Qdrant；只开放 `production_rebuild_execution_design_gate`。
- 默认输出：`tests/production_rebuild_execution_design_report.json` 和 `docs/production_rebuild_execution_design_v0.4.14.0.md`。
- 边界：design only；不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion、retriever、prompt、rerank、anchors、risk rules、scenario registry、fixtures 或 eval cases。

## v0.4.13.18 Ingestion Metadata Rebuild Planning Series Closeout 补充

- `tools/build_ingestion_metadata_rebuild_planning_series_closeout.py`: 只读取 v0.4.13.13-v0.4.13.17 saved reports，关闭 v0.4.13 ingestion metadata patch and rebuild planning series，并只开放 `production_rebuild_execution_design`。
- 默认输出：`tests/ingestion_metadata_rebuild_planning_series_closeout_report.json` 和 `docs/ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md`。
- 边界：closeout only；不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 prompt、rerank、anchors、risk rules、scenario registry、fixtures 或 eval cases。

## v0.4.13.17 Rebuild Runbook / Preflight Contract 补充

- `tools/build_rebuild_runbook_preflight_contract.py`: 只读取 v0.4.13.15 worksheet 与 v0.4.13.16 gate，定义未来 rebuild execution series 的 runbook/preflight 契约；不运行 live preflight，不访问 Qdrant，不 rebuild。
- 默认输出：`tests/rebuild_runbook_preflight_contract_report.json` 和 `docs/rebuild_runbook_preflight_contract_v0.4.13.17.md`。
- 边界：contract only；不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 runtime/eval artifacts。

## v0.4.13.16 Human Rebuild Authorization Worksheet Gate 补充

- `tools/check_human_rebuild_authorization_worksheet_gate.py`: 只读取 v0.4.13.15 worksheet，检查字段顺序、required/optional 标签、未收集人工值、未授权和 handoff 边界。
- 默认输出：`tests/human_rebuild_authorization_worksheet_gate_report.json` 和 `docs/human_rebuild_authorization_worksheet_gate_v0.4.13.16.md`。
- 边界：gate only；不收集人工值，不创建授权记录，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.13.15 Human Rebuild Authorization Worksheet 补充

- `tools/build_human_rebuild_authorization_worksheet.py`: 只读取 v0.4.13.13 design 与 v0.4.13.14 gate，生成 10 行空白人工授权 worksheet；不收集人工值，不创建授权记录，不访问 Qdrant，不 rebuild。
- 默认输出：`tests/human_rebuild_authorization_worksheet_report.json` 和 `docs/human_rebuild_authorization_worksheet_v0.4.13.15.md`。
- 边界：worksheet only；不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion/retriever/rules/eval cases。

## v0.4.13.14 Rebuild Authorization Design Gate 补充

- `tools/check_rebuild_authorization_design_gate.py`: 只读取 v0.4.13.13 rebuild authorization design report，检查 lineage、summary、guardrails、必填授权字段、终止条件、output contract 与 handoff boundaries。
- 默认输出：`tests/rebuild_authorization_design_gate_report.json` 和 `docs/rebuild_authorization_design_gate_v0.4.13.14.md`。
- 边界：gate only；不创建人工授权记录，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion/retriever/rules/eval cases。

## v0.4.13.13 Rebuild Authorization Design 补充

- `tools/build_rebuild_authorization_design.py`: 只读取 v0.4.13.11 runner report 与 v0.4.13.12 runner gate report，生成未来生产 rebuild 所需的人工授权设计，不创建授权、不访问 Qdrant、不 rebuild。
- 默认输出：`tests/rebuild_authorization_design_report.json` 和 `docs/rebuild_authorization_design_v0.4.13.13.md`。
- 边界：design only；不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion/retriever/rules/eval cases。

## v0.4.13.12 Post-Patch Rebuild Dry-Run Runner Gate 补充

- `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py`: 只读取 v0.4.13.11 runner saved report，检查 lineage、summary、sample contract、row contract、comparison contract、guardrails 与 handoff boundaries。
- 默认输出：`tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json` 和 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_v0.4.13.12.md`。
- 边界：gate only；不重跑 runner，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion/retriever/rules/eval cases。

## v0.4.13.11 Post-Patch Rebuild Dry-Run Runner 补充

- `tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`: 只读取 v0.4.13.8 source patch、v0.4.13.9 design 与 v0.4.13.10 design gate saved reports，并使用本地 deterministic article samples 校验当前 `build_article_documents` 的 post-patch boundary metadata 与预期 ID drift。
- 默认输出：`tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json` 和 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_v0.4.13.11.md`。
- 边界：local/read-only dry-run；不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion/retriever/rules/eval cases。

## v0.4.13.10 Post-Patch Rebuild Dry-Run Design Gate 补充

- `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py`: 只读取 v0.4.13.9 post-patch rebuild dry-run design report，检查 source patch 输入、guardrails、future runner contract、sample strategy、comparison fields、output contract 和 handoff 边界。
- 默认输出：`tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json` 和 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_v0.4.13.10.md`。
- 边界：gate only；不创建 runner，不访问或写入 Qdrant，不 rebuild，不调用 `rag_query`、embedding、LLM 或 full eval，不修改 ingestion/retriever/rules/eval cases。

## v0.4.13.9 Post-Patch Rebuild Dry-Run Design 补充

- `tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py`: 只读取 v0.4.13.8 源码补丁检查报告，定义未来 post-patch rebuild dry-run runner 的输入、对比字段、输出契约和阻断条件。
- 默认输出：`tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json` 和 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_v0.4.13.9.md`。
- 边界：design only；不创建 runner，不访问或写入 Qdrant，不 rebuild，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.13.8 入库元数据源码补丁补充

- `tools/check_ingestion_metadata_source_patch.py`: 读取 v0.4.13.7 actual design gate，并验证 `build_article_documents` 已为普通法律 article/paragraph/item 块补齐 `chunk_index/chunk_count`。
- 默认输出：`tests/ingestion_metadata_source_patch_report.json` 和 `docs/ingestion_metadata_source_patch_v0.4.13.8.md`。
- 边界：只做源码补丁检查；不访问或写入 Qdrant，不 rebuild，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.13.7 Ingestion Metadata Patch Actual Design Gate 补充

- `tools/check_ingestion_metadata_patch_actual_design_gate.py`: 只读取 v0.4.13.6 actual patch design report，检查单文件/单函数 scope、parent/child chunk 规则、post-patch 验证计划和禁止动作。
- 默认输出：`tests/ingestion_metadata_patch_actual_design_gate_report.json` 和 `docs/ingestion_metadata_patch_actual_design_gate_v0.4.13.7.md`。
- 边界：gate only；不修改 `src/rag/ingestion.py`，不访问或写入 Qdrant，不 rebuild，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.13.6 Ingestion Metadata Patch Actual Design 补充

- `tools/build_ingestion_metadata_patch_actual_design.py`: 只读取 contract、local dry-run 和 local dry-run gate saved reports，生成 actual patch 的设计契约。
- 默认输出：`tests/ingestion_metadata_patch_actual_design_report.json` 和 `docs/ingestion_metadata_patch_actual_design_v0.4.13.6.md`。
- 边界：design only；不修改 `src/rag/ingestion.py`，不访问或写入 Qdrant，不 rebuild，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.13.5 Ingestion Metadata Patch Local Dry-Run Gate 补充

- `tools/check_ingestion_metadata_patch_local_dry_run_gate.py`: 只读取 v0.4.13.4 local dry-run report，检查样例、row 字段、expected drift、forbidden drift、guardrails 和 handoff 边界。
- 默认输出：`tests/ingestion_metadata_patch_local_dry_run_gate_report.json` 和 `docs/ingestion_metadata_patch_local_dry_run_gate_v0.4.13.5.md`。
- 边界：gate only；不重新运行 runner，不修改 `src/rag/ingestion.py`，不访问或写入 Qdrant，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.13.4 Ingestion Metadata Patch Local Dry-Run Runner 补充

- `tools/run_ingestion_metadata_patch_local_dry_run.py`: 只使用小型 in-memory article_parts 样例和当前 `build_article_documents`，模拟补齐 `chunk_index/chunk_count` 后的 metadata 与 ID drift。
- 默认输出：`tests/ingestion_metadata_patch_local_dry_run_report.json` 和 `docs/ingestion_metadata_patch_local_dry_run_v0.4.13.4.md`。
- 边界：local dry-run only；不修改 `src/rag/ingestion.py`，不访问或写入 Qdrant，不调用 `rag_query`、embedding、LLM 或 full eval。

## v0.4.13.3 Ingestion Metadata Patch Dry-Run Design Gate 补充

- `tools/check_ingestion_metadata_patch_dry_run_design_gate.py`：只读取 v0.4.13.2 dry-run design report，检查 local-only scope、expected/forbidden drift、output contract、blocking conditions 和禁止实现边界。
- 默认输出：`tests/ingestion_metadata_patch_dry_run_design_gate_report.json` 和 `docs/ingestion_metadata_patch_dry_run_design_gate_v0.4.13.3.md`。
- 边界：gate only；不实现 dry-run runner，不修改 ingestion，不重建 Qdrant，不改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.13.2 Ingestion Metadata Patch Dry-Run Design 补充

- `tools/build_ingestion_metadata_patch_dry_run_design.py`：只读取 v0.4.13.0 contract report 和 v0.4.13.1 contract gate report，定义未来 local dry-run 的 pre/post metadata 与 ID drift 对比口径。
- 默认输出：`tests/ingestion_metadata_patch_dry_run_design_report.json` 和 `docs/ingestion_metadata_patch_dry_run_design_v0.4.13.2.md`。
- 边界：dry-run design only；不修改 ingestion，不重建 Qdrant，不改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.13.1 Ingestion Metadata Patch Contract Gate 补充

- `tools/check_ingestion_metadata_patch_contract_gate.py`：只读取 v0.4.13.0 contract report，检查 allowed file/function、parent/child chunk rules、Qdrant 禁止、retrieval 禁止和 eval/fixture 禁止边界。
- 默认输出：`tests/ingestion_metadata_patch_contract_gate_report.json` 和 `docs/ingestion_metadata_patch_contract_gate_v0.4.13.1.md`。
- 边界：gate only；不修改 ingestion，不重建 Qdrant，不改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.13.0 Ingestion Metadata Patch Contract 补充

- `tools/build_ingestion_metadata_patch_contract.py`：只读取 v0.4.12.3 closeout、v0.4.12.1 fix design 和 `src/rag/ingestion.py` 源码，生成 future ingestion metadata patch scope contract。
- 默认输出：`tests/ingestion_metadata_patch_contract_report.json` 和 `docs/ingestion_metadata_patch_contract_v0.4.13.0.md`。
- 边界：contract only；不修改 ingestion，不重建 Qdrant，不改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.12.3 Metadata/Chunking Series Closeout 补充

- `tools/build_metadata_chunking_series_closeout.py`：只读取 v0.4.12.0 root-cause、v0.4.12.1 fix design 和 v0.4.12.2 gate reports，生成 metadata/chunking 系列收口报告。
- 默认输出：`tests/metadata_chunking_series_closeout_report.json` 和 `docs/metadata_chunking_series_closeout_v0.4.12.3.md`。
- 边界：closeout only；不修改 ingestion，不重建 Qdrant，不改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.12.2 Metadata/Chunking Fix Design Gate 补充

- `tools/check_metadata_chunking_fix_design_gate.py`：只读取 v0.4.12.1 fix design report 和 v0.4.12.0 root-cause report，检查 stable ID impact、rebuild required、direct payload patch 禁止和 runtime implementation 禁止边界。
- 默认输出：`tests/metadata_chunking_fix_design_gate_report.json` 和 `docs/metadata_chunking_fix_design_gate_v0.4.12.2.md`。
- 边界：gate only；不修改 ingestion，不重建 Qdrant，不改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.12.1 Metadata/Chunking Fix Design 补充

- `tools/build_metadata_chunking_fix_design.py`：只读取 v0.4.12.0 root-cause report，生成 article/paragraph/item chunk boundary metadata 修复设计。
- 默认输出：`tests/metadata_chunking_fix_design_report.json` 和 `docs/metadata_chunking_fix_design_v0.4.12.1.md`。
- 边界：fix design only；不修改 ingestion，不重建 Qdrant，不改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.12.0 Metadata/Chunking Root-Cause Report 补充

- `tools/build_metadata_chunking_root_cause_report.py`：只读取 v0.4.11.3 closeout、v0.4.11.1 snapshot、Qdrant integrity report 和 `src/rag/ingestion.py` 源码，生成 chunk boundary root-cause 诊断。
- 默认输出：`tests/metadata_chunking_root_cause_report.json` 和 `docs/metadata_chunking_root_cause_v0.4.12.0.md`。
- 边界：root-cause report only；不连接 Qdrant，不修 ingestion，不重建库，不修改 retriever、rerank、prompt、rules 或 eval cases。

## v0.4.11.3 Evidence Metadata Snapshot Series Closeout 补充

- `tools/build_evidence_metadata_snapshot_series_closeout.py`：只读取 v0.4.11.0 contract、v0.4.11.1 snapshot 与 v0.4.11.2 gate 报告，收束 evidence metadata snapshot 只读诊断系列。
- 默认输出：`tests/evidence_metadata_snapshot_series_closeout_report.json` 和 `docs/evidence_metadata_snapshot_series_closeout_v0.4.11.3.md`。
- 边界：series closeout only；不连接 Qdrant，不修 metadata/chunk，不修改 ingestion、retriever、rerank、prompt、rules 或 eval cases。

## v0.4.11.2 Evidence Metadata Snapshot Gate 补充

- `tools/check_evidence_metadata_snapshot_gate.py`：只读取 v0.4.11.1 snapshot 与 v0.4.11.0 contract，确认 Qdrant payload read、`with_vectors=false`、19 行诊断与 finding 分布。
- 默认输出：`tests/evidence_metadata_snapshot_gate_report.json` 和 `docs/evidence_metadata_snapshot_gate_v0.4.11.2.md`。
- 边界：gate only；不连接 Qdrant，不修 metadata/chunk，不修改 ingestion、retriever、rerank、prompt、rules 或 eval cases。

## v0.4.11.1 Evidence Metadata Snapshot Runner 补充

- `tools/run_evidence_metadata_snapshot.py`：按 v0.4.11.0 contract 对 Qdrant collection 做只读 payload scroll，`with_vectors=false`，生成 19 个 evidence targets 的 metadata snapshot 诊断。
- 默认输出：`tests/evidence_metadata_snapshot_report.json` 和 `docs/evidence_metadata_snapshot_v0.4.11.1.md`。
- 边界：sensitive read-only Qdrant diagnostic；不调用 `rag_query`、embedding、LLM 或 full eval，不写 Qdrant，不修改 metadata/chunk/ingestion/retriever/rerank/prompt/rules/eval cases。

## v0.4.11.0 Evidence Metadata Snapshot Contract 补充

- `tools/build_evidence_metadata_snapshot_contract.py`：只读取 v0.4.10.3 closeout、v0.4.10.0 manifest 与 `tests/rag_eval_cases.json`，生成未来只读 Qdrant payload snapshot runner 的输入/输出契约。
- 默认输出：`tests/evidence_metadata_snapshot_contract_report.json` 和 `docs/evidence_metadata_snapshot_contract_v0.4.11.0.md`。
- 边界：contract only；本版本不连接 Qdrant，不运行 RAG/LLM/full eval，不修改 metadata/chunk/ingestion/retriever/rerank/prompt/rules/eval cases。

## v0.4.10.3 Metadata/Chunking Diagnostic Runner Series Closeout 补充

- `tools/build_metadata_chunking_diagnostic_runner_series_closeout.py`：只读取 v0.4.10.0 manifest、v0.4.10.1 saved-report runner 与 v0.4.10.2 gate 报告，确认 saved-report runner 链条闭环。
- 默认输出：`tests/metadata_chunking_diagnostic_runner_series_closeout_report.json` 和 `docs/metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md`。

## v0.4.10.2 Metadata/Chunking Saved-Report Runner Gate 补充

- `tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py`：只读取 v0.4.10.1 saved-report runner report，检查 40 行输出、0 blocked rows、contract 字段和 saved-report-only 边界。
- 默认输出：`tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json` 和 `docs/metadata_chunking_diagnostic_saved_report_runner_gate_v0.4.10.2.md`。
- 边界：gate only；不运行 diagnostic，不读取 evidence-level metadata snapshot，不读取 Qdrant，不扫描知识库全文，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.10.1 Metadata/Chunking Saved-Report Diagnostic Runner 补充

- `tools/run_metadata_chunking_diagnostic_saved_report.py`：只读取 v0.4.10.0 manifest 与 v0.4.9.10 dry-run contract，执行 saved-report scope 的 metadata/chunking diagnostic runner。
- 默认输出：`tests/metadata_chunking_diagnostic_saved_report_runner_report.json` 和 `docs/metadata_chunking_diagnostic_saved_report_runner_v0.4.10.1.md`。
- 边界：saved-report runner only；不读取 evidence-level metadata snapshot，不读取 Qdrant，不扫描知识库全文，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.10.0 Metadata/Chunking Diagnostic Runner Manifest 补充

- `tools/build_metadata_chunking_diagnostic_runner_manifest.py`：只读取 v0.4.9.11 closeout、v0.4.9.10 dry-run contract 与 v0.4.9.6 spec saved reports，将 8 个 sample cases 与 5 个 check groups 展开为 40 个只读 runner manifest items。
- 默认输出：`tests/metadata_chunking_diagnostic_runner_manifest_report.json` 和 `docs/metadata_chunking_diagnostic_runner_manifest_v0.4.10.0.md`。
- 边界：manifest only；不创建或运行 diagnostic runner，不读取 Qdrant，不扫描知识库全文，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.9.11 Retrieval Input Quality Series Closeout 补充

- `tools/build_retrieval_input_quality_series_closeout.py`：只读取 v0.4.9.0-v0.4.9.10 saved reports，确认 retrieval input quality governance 系列完整收口。
- 默认输出：`tests/retrieval_input_quality_series_closeout_report.json` 和 `docs/retrieval_input_quality_series_closeout_v0.4.9.11.md`。
- 边界：series closeout only；不创建或运行 diagnostic runner，不读取 Qdrant，不扫描知识库全文，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.9.10 Metadata/Chunking Diagnostic Dry-Run Contract 补充

- `tools/build_metadata_chunking_diagnostic_dry_run_contract.py`：只读取 v0.4.9.9 runner design gate 与 v0.4.9.8 runner design saved reports，定义未来只读 dry-run runner 的 CLI、输入、输出和失败处理契约。
- 默认输出：`tests/metadata_chunking_diagnostic_dry_run_contract_report.json` 和 `docs/metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md`。
- 边界：contract only；不创建真实 runner，不读取 Qdrant，不扫描知识库全文，不运行 diagnostic，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.9.9 Metadata/Chunking Diagnostic Runner Design Gate 补充

- `tools/check_metadata_chunking_diagnostic_runner_design_gate.py`：只读取 v0.4.9.8 runner design saved report，检查 runner design 契约、输出字段、failure buckets、prohibited actions 和非运行时边界。
- 默认输出：`tests/metadata_chunking_diagnostic_runner_design_gate_report.json` 和 `docs/metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md`。
- 边界：gate only；不读取 Qdrant，不扫描知识库全文，不运行 diagnostic，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.9.8 Metadata/Chunking Diagnostic Runner Design 补充

- `tools/build_metadata_chunking_diagnostic_runner_design.py`：只读取 v0.4.9.7 spec gate 与 v0.4.9.6 spec saved reports，生成未来只读 metadata/chunking diagnostic runner 的输入/输出契约。
- 默认输出：`tests/metadata_chunking_diagnostic_runner_design_report.json` 和 `docs/metadata_chunking_diagnostic_runner_design_v0.4.9.8.md`。
- 边界：runner design only；不读取 Qdrant，不扫描知识库全文，不运行 diagnostic，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.9.7 Metadata/Chunking Diagnostic Spec Gate 补充

- `tools/check_metadata_chunking_diagnostic_spec_gate.py`：只读取 v0.4.9.6 metadata/chunking diagnostic spec saved report，检查 spec 结构、字段覆盖、sample scope、prohibited actions 和非运行时边界。
- 默认输出：`tests/metadata_chunking_diagnostic_spec_gate_report.json` 和 `docs/metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md`。
- 边界：gate only；不运行 diagnostic，不合并 chunk，不修改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.9.6 Metadata/Chunking Diagnostic Spec 补充

- `tools/build_metadata_chunking_diagnostic_spec.py`：只读取 v0.4.9.5 prioritization gate 与 v0.4.9.4 prioritization saved reports，定义 metadata/chunking diagnostic 的未来检查契约。
- 默认输出：`tests/metadata_chunking_diagnostic_spec_report.json` 与 `docs/metadata_chunking_diagnostic_spec_v0.4.9.6.md`。
- 边界：spec only；不运行 diagnostic，不合并 chunk，不改 metadata/ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。

## v0.4.9.5 Retrieval Input Quality Diagnostic Prioritization Gate 补充

- `tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py`：只读取 v0.4.9.4 diagnostic prioritization saved report，检查 route order、priority rank、recommended artifacts、entry conditions、prohibited actions 和非运行时边界。
- 默认输出：`tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json` 与 `docs/retrieval_input_quality_diagnostic_prioritization_gate_v0.4.9.5.md`。
- 边界：gate only；通过只允许进入 `metadata_chunking_diagnostic_spec`，不授权 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases 修改。

## v0.4.9.4 Retrieval Input Quality Diagnostic Prioritization 补充

- `tools/build_retrieval_input_quality_diagnostic_prioritization.py`：只读取 v0.4.9.3 gate 与 v0.4.9.2 offline audit saved reports，将 5 条 recommended route 排成诊断优先级矩阵。
- 默认输出：`tests/retrieval_input_quality_diagnostic_prioritization_report.json` 与 `docs/retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md`。
- 边界：diagnostic prioritization only；不调用 RAG/Qdrant/LLM，不运行 full eval，不授权 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases 修改。

## v0.4.9.3 Retrieval Input Quality Offline Audit Gate 补充

- `tools/check_retrieval_input_quality_offline_audit_gate.py`：只读取 v0.4.9.2 offline audit saved report，检查 schema/version、5 个 bucket 顺序、required fields、severity/route 完整性和非运行时边界。
- 默认输出：`tests/retrieval_input_quality_offline_audit_gate_report.json` 与 `docs/retrieval_input_quality_offline_audit_gate_v0.4.9.3.md`。
- 边界：gate only；通过只允许进入 retrieval input quality diagnostic planning，不授权 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases 修改。

## v0.4.9.2 Retrieval Input Quality Offline Audit 补充

- `tools/build_retrieval_input_quality_offline_audit.py`：只读取 v0.4.9.1 audit spec、v0.4.9.0 intake 与既有 base/anchor saved reports，生成 5 个 retrieval input quality bucket 的离线审计结果。
- 默认输出：`tests/retrieval_input_quality_offline_audit_report.json` 与 `docs/retrieval_input_quality_offline_audit_v0.4.9.2.md`。
- 边界：offline audit only；不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

## v0.4.9.1 Retrieval Input Quality Audit Spec 补充

- `tools/build_retrieval_input_quality_audit_spec.py`：只读取 v0.4.9.0 intake saved report，将 5 个治理 bucket 固化为离线审计契约。
- 默认输出：`tests/retrieval_input_quality_audit_spec_report.json` 与 `docs/retrieval_input_quality_audit_spec_v0.4.9.1.md`。
- 边界：audit spec only；不运行 audit，不调用 RAG/Qdrant/LLM，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

## v0.4.9.0 Retrieval Input Quality Intake 补充

- `tools/build_retrieval_input_quality_intake.py`：只读取既有 saved reports，整合 base retrieval gap、anchor dependency、root-cause action plan 与 v0.4.8 closeout，生成 retrieval input quality 治理入口。
- 默认输出：`tests/retrieval_input_quality_intake_report.json` 与 `docs/retrieval_input_quality_intake_v0.4.9.0.md`。
- 边界：intake only；不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

## 已合并的历史工具锚点

- `tools/build_ready_action_design_pack.py`：历史 ready action 设计包入口，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。
- `tests/ready_action_design_pack_report.json`：该入口的历史只读设计包报告。
- `tools/build_ready_action_design_review_brief.py`：历史 ready action 设计评审简报入口，现已并入 manual review governance 与 final evidence selection policy 设计链路说明。
- `tests/ready_action_design_review_brief_report.json`：该入口的历史只读设计评审简报报告。

## v0.4.8.15 Final Evidence Selection Policy Series Closeout 补充

- `tools/build_final_evidence_selection_policy_series_closeout.py`：只读取 v0.4.8.14 adoption draft、v0.4.8.13 gate、v0.4.8.12 simulation 与 v0.4.8.11 input contract saved reports，生成 v0.4.8.x 系列收口报告。
- 默认输出：`tests/final_evidence_selection_policy_series_closeout_report.json` 与 `docs/final_evidence_selection_policy_series_closeout_v0.4.8.15.md`。
- 边界：series closeout only；标记 v0.4.8.x 离线设计链条完成，但不记录正式用户采纳、不授权 runtime policy、rerank、prompt 或 eval case 修改。

## v0.4.8.14 Final Evidence Selection Policy Adoption Decision Draft 补充

- `tools/build_final_evidence_selection_policy_adoption_decision_draft.py`：只读取 v0.4.8.13 simulation gate 与 v0.4.8.12 simulation saved reports，生成 8 条待用户确认的 adoption decision draft rows。
- 默认输出：`tests/final_evidence_selection_policy_adoption_decision_draft_report.json` 与 `docs/final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md`。
- 边界：decision draft only；不记录用户正式结论，不授权 runtime policy、rerank、prompt 或 eval case 修改。

## v0.4.8.13 Final Evidence Selection Policy Offline Simulation Gate 补充

- `tools/check_final_evidence_selection_policy_offline_simulation_gate.py`：只读取 v0.4.8.12 offline simulation saved report，检查 schema/version、8 条 row、category 顺序、0 blocking failure、必需字段和非运行时边界。
- 默认输出：`tests/final_evidence_selection_policy_offline_simulation_gate_report.json` 与 `docs/final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md`。
- 边界：gate only；通过只允许进入 policy adoption decision draft，不授权 runtime policy、rerank、prompt 或 eval case 修改。

## v0.4.8.12 Final Evidence Selection Policy Offline Simulation 补充

- `tools/build_final_evidence_selection_policy_offline_simulation.py`：只读取 v0.4.8.11 offline simulation input contract saved report，生成 8 条 policy category 的离线模拟结果信号。
- 默认输出：`tests/final_evidence_selection_policy_offline_simulation_report.json` 与 `docs/final_evidence_selection_policy_offline_simulation_v0.4.8.12.md`。
- 边界：saved-report offline simulation only；不调用 RAG/Qdrant/LLM，不运行 full eval，不授权 runtime policy、rerank、prompt 或 eval case 修改。

## v0.4.8.11 Final Evidence Selection Policy Offline Simulation Input Contract 补充

- `tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py`：只读取 v0.4.8.7 confirmed record 与 v0.4.8.10 language confirmation record，合并 8 条 policy rows 作为后续 saved-report offline simulation 输入。
- 默认输出：`tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json` 与 `docs/final_evidence_selection_policy_offline_simulation_input_contract_v0.4.8.11.md`。
- 边界：只生成 simulation input contract，不运行 simulation，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。

## v0.4.8.10 Final Evidence Selection Policy Language Revision Confirmation Record 补充

- `tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py`：只读取 `tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json`，按用户“确认以上三条。”生成 3 条语言修订确认记录。
- 默认输出：`tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json` 与 `docs/final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md`。
- 边界：confirmed wording 只允许作为后续 offline simulation design 输入，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。

## v0.4.8.9 Final Evidence Selection Policy Language Revision Closeout Draft 补充

- `tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py`：只读取 `tests/final_evidence_selection_policy_language_revision_worksheet_report.json`，为 `liability`、`scenario_core`、`coverage_floor` 三条语言债生成待用户确认的 narrowed wording 草案。
- 默认输出：`tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json` 与 `docs/final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md`。
- 边界：只形成 user confirmation draft，不记录最终 policy wording，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。

## v0.4.8.8 Final Evidence Selection Policy Language Revision Worksheet 补充

- `tools/build_final_evidence_selection_policy_language_revision_worksheet.py`：只读取 `tests/final_evidence_selection_policy_closeout_confirmed_record_report.json`，为 3 条需修订语言的最终证据选择策略行生成 worksheet。
- 默认输出：`tests/final_evidence_selection_policy_language_revision_worksheet_report.json` 与 `docs/final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md`。
- 边界：只处理 `liability`、`scenario_core`、`coverage_floor` 的 wording risk、target boundary 和 simulation entry condition；不形成最终 wording，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.7 Final Evidence Selection Policy Closeout Confirmed Record 补充

- `tools/build_final_evidence_selection_policy_closeout_confirmed_record.py`：只读取 `tests/final_evidence_selection_policy_closeout_confirmation_record_report.json`，按用户明确确认生成最终证据选择策略收口正式确认记录。
- 默认输出：`tests/final_evidence_selection_policy_closeout_confirmed_record_report.json` 与 `docs/final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md`。
- 边界：只把 8 条 pending confirmation scaffold rows 固化为 confirmed closeout options；可作为后续离线设计规划输入，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.6 Final Evidence Selection Policy Closeout Confirmation Record Scaffold 补充

- `tools/build_final_evidence_selection_policy_closeout_confirmation_record.py`：只读取 `tests/final_evidence_selection_policy_closeout_decision_draft_report.json`，生成最终证据选择策略收口确认记录脚手架。
- 默认输出：`tests/final_evidence_selection_policy_closeout_confirmation_record_report.json` 与 `docs/final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md`。
- 边界：只把 8 条 user-confirmation draft rows 整理成 `pending_user_confirmation` scaffold rows；不伪造用户确认，不记录 formal review outcome，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.5 Final Evidence Selection Policy Closeout Decision Draft 补充

- `tools/build_final_evidence_selection_policy_closeout_decision_draft.py`：只读取 `tests/final_evidence_selection_policy_closeout_envelope_report.json`，生成最终证据选择策略收口决策草案。
- 默认输出：`tests/final_evidence_selection_policy_closeout_decision_draft_report.json` 与 `docs/final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md`。
- 边界：只把 8 条 pending closeout rows 整理成 user-confirmation draft rows、suggested closeout options、confirmation questions 和 required basis；不记录 formal review outcome，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。
## v0.4.8.4 Final Evidence Selection Policy Closeout Envelope 补充

- `tools/build_final_evidence_selection_policy_closeout_envelope.py`：只读取 `tests/final_evidence_selection_policy_human_review_worksheet_report.json`，生成最终证据选择策略收口外壳。
- 默认输出：`tests/final_evidence_selection_policy_closeout_envelope_report.json` 与 `docs/final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md`。
- 边界：只把 8 条 review rows 整理成 pending closeout rows、candidate routes、minimum human basis 和 recommended options；不记录 formal review outcome，不授权实现，不接入 `rag_query`，不修改 rerank、prompt、eval case 或 RAG 主流程。

## 定位

本索引用来帮助维护者和 reviewer 快速判断当前 CLI 工具入口的用途、输入、输出和运行边界。

当前权威入口仍是 root-level `tools/*.py`。`tools/eval`、`tools/evidence_diagnostics`、`tools/manual_review`、`tools/ops`、`tools/ingestion` 只是后续目录整理的 scaffold / 脚手架，不代表工具已经迁移，也不改变任何默认路径。

## 快速判断

- 需要真正跑 RAG 评测或报告链路时，优先查看“评测执行与报告导出”。
- 只想审阅已保存报告、证据覆盖、manual review 状态时，优先查看“离线诊断与治理工具”。
- 只想确认项目结构、编码、离线边界是否健康时，优先查看“健康检查与维护工具”。
- 看到 advisory-only 输出时，只能把它当作人工复核辅助材料，不能当作 completed manual decision。
- 不确定某个工具是否会触发 `rag_query`、`Qdrant` 或 `LLM` 时，先按本索引的“可能调用 RAG/Qdrant/LLM”列判断。

## 工具入口与产物关系

| 类别 | 代表工具 | 主要输入 | 主要输出 | 可能调用 RAG/Qdrant/LLM | Advisory-only |
|---|---|---|---|---|---|
| 入库预处理与知识质量 | `tools/pdf_to_txt.py`, `tools/clean_mineru_standard_md.py`, `tools/check_ingestion_quality.py`, `tools/audit_legal_functional_typing.py` | PDF、Markdown、`knowledge_manifest.json`、`config/legal_functional_types.json` | TXT、清洗报告、`tests/ingestion_quality_report.json`、`tests/legal_functional_typing_report.json` | 通常不调用 RAG/Qdrant/LLM；部分工具复用入库解析函数 | 否 |
| Qdrant/索引一致性 | `tools/check_qdrant_index_integrity.py`, `tools/check_eval_consistency.py` | `knowledge_manifest.json`、eval cases、collection 名称 | `tests/qdrant_index_integrity_report.json` 或一致性报告 | 会访问 Qdrant；通常不直接调用 LLM | 否 |
| 评测执行与报告导出 | `tools/run_rag_eval.py`, `tools/run_impact_eval.py`, `tools/run_scenario_eval.py`, `tools/run_risk_eval.py`, `tools/run_report_eval.py`, `tools/export_risk_report.py` | `tests/rag_eval_cases.json`、`tests/smoke_eval_cases.json`、scenario/case 参数 | `tests/rag_eval_report.json`、`tests/*_eval_report.json`、`tests/scenario_eval_summary.md`、`reports/<case>/<timestamp>.md/json` | 会或可能调用 `rag_query`、RAG 检索链路、Qdrant 或 LLM；不要当作离线诊断工具 | 否 |
| 稳定性汇总 | `tools/summarize_rag_stability.py`, `tools/check_rag_stability_report.py` | 已保存的 eval/stability 报告 | 稳定性摘要、stability gate 结果 | 不重新运行 RAG；读取既有报告 | 否 |
| Evidence alignment / coverage 诊断 | `tools/check_evidence_alignment.py`, `tools/check_evidence_coverage.py`, `tools/triage_evidence_coverage_loss.py` | `tests/rag_eval_report.json`、`tests/hidden_eval_report.json`、`tests/evidence_coverage_report.json` | `tests/evidence_alignment_report.json`、`tests/evidence_coverage_report.json`、`tests/evidence_coverage_triage_report.json` | 不调用 RAG/Qdrant/LLM；只读取 saved reports | 否 |
| Evidence retrieval audit | `tools/audit_base_retrieval_quality.py`, `tools/audit_anchor_dependency.py`, `tools/audit_final_evidence_selection.py`, `tools/audit_rule_debt.py` | RAG eval、coverage、scenario registry、rule 配置等已保存材料 | `tests/*_audit_report.json`、audit Markdown | 不调用 RAG/Qdrant/LLM；只做离线审计 | 否 |
| Evidence 治理计划与门禁草案 | `tools/build_evidence_manual_review_dataset.py`, `tools/draft_evidence_coverage_gates.py`, `tools/build_evidence_root_cause_action_plan.py`, `tools/build_evidence_action_series_baseline.py`, `tools/build_evidence_fixture_candidate_pool.py`, `tools/calibrate_scenario_registry_coverage.py` | 覆盖率报告、triage 报告、manual review dataset、scenario registry | `tests/evidence_manual_review_dataset.json`、`tests/evidence_coverage_gate_draft_report.json`、`tests/evidence_root_cause_action_plan.json` 等 | 不调用 RAG/Qdrant/LLM | 否 |
| Legal functional typing | `tools/check_legal_functional_type_config.py`, `tools/check_legal_functional_typing_fixtures.py`, `tools/analyze_legal_functional_typing_errors.py`, `tools/audit_legal_functional_typing.py` | `config/legal_functional_types.json`、fixture、RAG/evidence 报告 | `tests/legal_functional_type_config_report.json`、typing fixture/report | 不调用 RAG/Qdrant/LLM | 否 |
| Scenario / rule governance | `tools/check_scenario_registry.py`, `tools/check_scenario_links.py`, `tools/check_scenario_eval_report.py`, `tools/check_rule_convergence_plan.py` | scenario registry、scenario eval、rule convergence plan | registry/link/eval/rule 检查结果 | 不调用 RAG/Qdrant/LLM；读取配置和报告 | 否 |
| 人工复核核心工作流 | `tools/build_manual_review_loop.py`, `tools/build_manual_review_decision_schema.py`, `tools/build_manual_review_decision_examples.py`, `tools/validate_manual_review_decisions.py`, `tools/validate_proposed_manual_review_decisions.py`, `tools/build_manual_review_action_candidates.py`, `tools/export_manual_review_workbench.py`, `tools/import_manual_review_workbench.py`, `tools/audit_manual_review_decision_diff.py` | manual-review loop/schema/workbench JSON、decision records | schema、decision examples、validation report、action candidates、workbench JSON/CSV、import/diff report | 不调用 RAG/Qdrant/LLM | 通常否；导入器只接受正式 filled JSON，CSV 仅作人工阅读辅助，并会拒绝 advisory 输入成为 completed decision |
| 人工复核治理与 dry-run | `tools/build_manual_review_governance_report.py`, `tools/build_manual_review_progress_report.py`, `tools/build_ready_action_routing_dry_run.py`, `tools/build_validated_decision_promotion_dry_run.py`, `tools/build_manual_review_intake_gate_closeout.py`, `tools/build_manual_review_export_pipeline_dry_run.py`, `tools/check_ready_action_design_review_gate.py`, `tools/build_ready_action_design_review_worksheet.py`, `tools/build_ready_action_design_review_closeout.py`, `tools/build_ready_action_human_closeout_decision_draft.py`, `tools/build_ready_action_human_closeout_confirmation_record.py`, `tools/build_final_evidence_selection_policy_intake.py`, `tools/build_final_evidence_selection_policy_simulator_spec.py`, `tools/build_final_evidence_selection_policy_table_draft.py`, `tools/build_final_evidence_selection_policy_human_review_worksheet.py` | validation/action/progress/import/diff/promotion 报告、设计评审简报、设计评审 gate、worksheet、closeout envelope、confirmation draft、final evidence selection policy intake、saved-report simulator spec、policy table draft、policy human review worksheet | governance/progress/routing/promotion/closeout/dry-run 报告、`tests/manual_review_export_pipeline_dry_run_report.json`、`tests/ready_action_design_review_gate_report.json`、`tests/ready_action_design_review_worksheet_report.json`、`tests/ready_action_design_review_closeout_report.json`、`tests/ready_action_human_closeout_decision_draft_report.json`、`tests/ready_action_human_closeout_confirmation_record_report.json`、`tests/final_evidence_selection_policy_intake_report.json`、`tests/final_evidence_selection_policy_simulator_spec_report.json`、`tests/final_evidence_selection_policy_table_draft_report.json`、`tests/final_evidence_selection_policy_human_review_worksheet_report.json` | 不调用 RAG/Qdrant/LLM；dry-run / gate / worksheet / closeout / draft / confirmation / intake / simulator spec / table draft / policy worksheet 只模拟、校验和整理人工评审材料 | 否 |
| Advisory 人工复核辅助包 | `tools/build_manual_review_ai_suggestion_prefill.py`, `tools/build_manual_review_prescreen_report.py`, `tools/build_manual_review_pilot_batch.py`, `tools/build_manual_review_pilot_case_review_assist.py`, `tools/build_pilot_manual_review_round1_support.py`, `tools/build_mobile_pilot_review_decision_aid.py` | workbench、prescreen、pilot batch、saved RAG eval/report | `tests/manual_review_*_report.json`、`tests/pilot_manual_review_round1_support_report.json`、`tests/mobile_pilot_review_decision_aid_report.json`、对应 docs Markdown | 不调用 RAG/Qdrant/LLM；只读取保存结果并生成辅助说明 | 是 |
| 可视化工作台 | `tools/build_manual_review_visual_workbench.py`, `tools/build_manual_review_visual_workbench_contract.py`, `tools/build_workbench_intake_contract.py` | workbench、contract、progress、governance、pilot/advisory reports | `tools/manual_review_visual_workbench/index.html`、`tests/manual_review_visual_workbench_build_report.json`、contract reports | 不调用 RAG/Qdrant/LLM；生成静态 HTML/契约报告 | 混合：页面可显示 advisory 辅助，但导出仍要求人工 ready draft |
| 健康检查与维护工具 | `tools/run_project_health_check.py`, `tools/check_encoding_hygiene.py`, `tools/check_tool_index_consistency.py`, `tools/check_test_index_consistency.py`, `tools/check_artifact_index_consistency.py`, `tools/check_layout_migration_readiness.py`, `tools/build_maintenance_closeout_report.py`, `tools/check_evidence_enrichment_hardening.py`, `tools/check_hidden_eval_seeds.py` | repo 文本、已保存报告、hidden seed config、维护索引 | `tests/project_health_check_report.json`、`tests/encoding_hygiene_report.json`、`tests/tool_index_consistency_report.json`、`tests/test_index_consistency_report.json`、`tests/artifact_index_consistency_report.json`、`tests/layout_migration_readiness_report.json`、`tests/maintenance_closeout_report.json`、hardening/seed 检查报告 | 不实际调用 RAG/Qdrant/LLM；`run_project_health_check.py` 只扫描禁止模式字符串 | 否 |

## 关键入口速查

| 想做的事 | 入口 | 默认或常见产物 | 边界 |
|---|---|---|---|
| 跑 RAG eval | `tools/run_rag_eval.py` | `tests/rag_eval_report.json` | 可能触发 RAG/Qdrant/LLM；这不是轻量离线检查 |
| 检查 evidence alignment | `tools/check_evidence_alignment.py` | `tests/evidence_alignment_report.json` | 只读既有 eval report |
| 检查 evidence coverage | `tools/check_evidence_coverage.py` | `tests/evidence_coverage_report.json` | 只读既有 eval report |
| 构建可视化人工复核页面 | `tools/build_manual_review_visual_workbench.py` | `tools/manual_review_visual_workbench/index.html`, `tests/manual_review_visual_workbench_build_report.json` | 静态 HTML；不调用后端或 RAG |
| 导入人工填写的 workbench | `tools/import_manual_review_workbench.py` | `tests/manual_review_workbench_import_report.json` | 只接受正式 filled workbench export；拒绝 advisory 文件 |
| 预演导出后的治理链路 | `tools/build_manual_review_export_pipeline_dry_run.py` | `tests/manual_review_export_pipeline_dry_run_report.json` | dry-run，不生成 ready action |
| 检查设计评审入口门禁 | `tools/check_ready_action_design_review_gate.py` | `tests/ready_action_design_review_gate_report.json`, `docs/ready_action_design_review_gate_v0.4.7.9.2.md` | 只读取设计评审简报；只允许人工设计评审，不授权实现 |
| 生成设计复核工作表 | `tools/build_ready_action_design_review_worksheet.py` | `tests/ready_action_design_review_worksheet_report.json`, `docs/ready_action_design_review_worksheet_v0.4.7.9.3.md` | 只读取 gate/brief；输出 decision matrix，不记录正式结论、不授权实现 |
| 生成设计评审收口外壳 | `tools/build_ready_action_design_review_closeout.py` | `tests/ready_action_design_review_closeout_report.json`, `docs/ready_action_design_review_closeout_v0.4.7.9.4.md` | 只读取 worksheet；输出待人工收口候选分流，不记录正式结论、不授权实现 |
| 生成人工收口确认草案 | `tools/build_ready_action_human_closeout_decision_draft.py` | `tests/ready_action_human_closeout_decision_draft_report.json`, `docs/ready_action_human_closeout_decision_draft_v0.4.7.9.5.md` | 只读取 closeout envelope；输出待用户确认草案，不记录正式结论、不授权实现 |
| 生成人工收口确认记录 | `tools/build_ready_action_human_closeout_confirmation_record.py` | `tests/ready_action_human_closeout_confirmation_record_report.json`, `docs/ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md` | 只读取 decision draft；记录用户确认的设计收口方向，不是 importer completed decision、不授权实现 |
| 生成最终证据选择策略 intake | `tools/build_final_evidence_selection_policy_intake.py` | `tests/final_evidence_selection_policy_intake_report.json`, `docs/final_evidence_selection_policy_intake_v0.4.8.0.md` | 只读取 confirmation/design pack/final selection audit 等已保存报告；输出设计输入，不实现策略、不改 rerank、不接主流程 |
| 生成最终证据选择策略模拟器契约 | `tools/build_final_evidence_selection_policy_simulator_spec.py` | `tests/final_evidence_selection_policy_simulator_spec_report.json`, `docs/final_evidence_selection_policy_simulator_spec_v0.4.8.1.md` | 只读取 v0.4.8.0 intake、final selection audit 和 confirmation record；输出 saved-report simulator 输入/输出契约、质量信号和人工复核 gate，不实现 runtime policy、不改 rerank/prompt/eval、不接主流程 |
| 生成最终证据选择策略表草案 | `tools/build_final_evidence_selection_policy_table_draft.py` | `tests/final_evidence_selection_policy_table_draft_report.json`, `docs/final_evidence_selection_policy_table_draft_v0.4.8.2.md` | 只读取 v0.4.8.1 simulator spec 与既有 saved reports；输出人工可审阅 policy table draft，不实现 runtime policy、不改 rerank/prompt/eval、不接主流程 |
| 生成最终证据选择策略人工复核 worksheet | `tools/build_final_evidence_selection_policy_human_review_worksheet.py` | `tests/final_evidence_selection_policy_human_review_worksheet_report.json`, `docs/final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md` | 只读取 v0.4.8.2 policy table draft saved report；输出人工审议问题和验收检查点，不记录正式结论、不实现 runtime policy、不接主流程 |
| 做项目轻量健康检查 | `tools/run_project_health_check.py` | `tests/project_health_check_report.json` | 不运行 full eval、不接触 Qdrant 或 LLM |
| 做编码卫生检查 | `tools/check_encoding_hygiene.py` | `tests/encoding_hygiene_report.json` | 只写报告，不改写扫描文件 |
| 做入库文本质量检查 | `tools/check_ingestion_quality.py` | `tests/ingestion_quality_report.json` | 检查入库文本污染和结构问题，不修数据 |
| 检查工具索引覆盖 | `tools/check_tool_index_consistency.py` | root-level `tools/*.py`、`docs/indexes/project_tool_index.md` | `tests/tool_index_consistency_report.json` | 只读文档/源码结构，不运行 eval 或主链路 |
| 检查测试索引覆盖 | `tools/check_test_index_consistency.py` | root-level `tests/test_*.py`、`docs/indexes/project_test_index.md` | `tests/test_index_consistency_report.json` | 只读文档/测试文件名，不运行测试 |
| 检查产物索引覆盖 | `tools/check_artifact_index_consistency.py` | root-level `tests/*.json/*.csv/*.md`、`docs/indexes/project_artifact_index.md` | `tests/artifact_index_consistency_report.json` | 只读文档/产物名，不迁移报告 |
| 检查目录迁移准备度 | `tools/check_layout_migration_readiness.py` | 索引文档、维护报告、脚手架目录 | `tests/layout_migration_readiness_report.json` | 只评估规划条件，不自动迁移 |
| 生成维护收束报告 | `tools/build_maintenance_closeout_report.py` | 维护报告和维护索引 | `tests/maintenance_closeout_report.json` | 只汇总维护状态，不打开人工复核门禁 |

## 可能触发主链路的入口

这些工具不是离线诊断工具，运行前应明确是否需要 RAG、Qdrant 或 LLM：

- `tools/run_rag_eval.py`：直接调用 `rag_query`。
- `tools/run_scenario_eval.py`：通过 `tools/run_rag_eval.py` 运行 scenario eval。
- `tools/run_impact_eval.py`：按 case 类型调用 RAG、risk 或 report eval runner。
- `tools/run_risk_eval.py`：通过风险分析链路间接进入 RAG。
- `tools/run_report_eval.py`：通过报告生成链路间接进入风险/RAG。
- `tools/export_risk_report.py`：通过风险报告导出链路间接进入风险/RAG。
- `tools/check_qdrant_index_integrity.py`：访问 Qdrant。
- `tools/check_eval_consistency.py`：访问 Qdrant。

## 运行边界

- 本索引不改变任何 CLI 默认路径。
- 本索引不把工具迁移到 `tools/eval`、`tools/evidence_diagnostics`、`tools/manual_review`、`tools/ops` 或 `tools/ingestion`。
- 本索引不要求运行 full eval。
- 离线诊断工具不得接入 `rag_query`、后端接口、Qdrant 或 LLM。
- Advisory-only 报告不得直接导入为 completed manual decision。
- `tools/check_tool_index_consistency.py` 只检查索引覆盖和敏感入口信号，不移动工具、不改默认路径。
- `tools/check_test_index_consistency.py`、`tools/check_artifact_index_consistency.py`、`tools/check_layout_migration_readiness.py` 和 `tools/build_maintenance_closeout_report.py` 都只写维护报告，不运行 eval、不移动文件。
- 若未来目录整理需要迁移工具入口，必须先做兼容层、双路径说明、health check 覆盖和显式版本计划。
