# 项目维护索引
## v0.4.18.9 维护补充

- 当前应用与健康检查版本：`0.4.18.9`。
- 当前重点：收口 v0.4.18.x product backend 设计，明确 fixture-backed API、字段目录、状态目录、数据源边界和未来 provider 接入顺序。
- 新增工具：`tools/build_product_backend_closeout.py`。
- 新增测试：`tests/test_product_backend_closeout.py`。
- 新增报告：`tests/product_backend_closeout_v0.4.18.9_report.json`。
- 新增说明文档：`docs/product_backend_closeout_v0.4.18.9.md`。
- 边界：closeout/runbook only；不接真实数据源、不调用 RAG/Qdrant/LLM、不运行 eval、不修改 anchor/prompt/rerank/risk supplement/eval case。

## v0.4.18.8 维护补充

- 当前应用与健康检查版本：`0.4.18.8`。
- 当前重点：把 fixture-backed `/product/*` 后端的数据读取层收束到 repository boundary，方便未来真实 provider 逐项接入。
- 新增模块：`src/product/repository.py`。
- 新增工具：`tools/export_product_data_source_boundary.py`。
- 新增测试：`tests/test_product_data_source_boundary.py`。
- 新增目录产物：`tests/product_data_source_boundary_v0.4.18.8.json`。
- 新增说明文档：`docs/product_data_source_boundary_v0.4.18.8.md`。
- 边界：只定义数据源替换边界；不接真实数据源、不调用 RAG/Qdrant/LLM、不访问行情、地图或供应链数据。

## v0.4.18.7 维护补充

- 当前应用与健康检查版本：`0.4.18.7`。
- 当前重点：补齐 fixture-backed `/product/*` 后端接口的状态语义和错误码目录。
- 新增状态模块：`src/product/status.py`。
- 新增工具：`tools/export_product_api_status_catalog.py`。
- 新增测试：`tests/test_product_api_status_catalog.py`。
- 新增目录产物：`tests/product_api_status_catalog_v0.4.18.7.json`。
- 新增说明文档：`docs/product_api_status_catalog_v0.4.18.7.md`。
- 边界：只定义状态/错误契约；不接真实数据源、不调用 RAG/Qdrant/LLM。

## v0.4.18.6 维护补充

- 当前应用与健康检查版本：`0.4.18.6`。
- 当前重点：为 fixture-backed `/product/*` 后端接口生成字段目录，方便 UI/前端/后端对齐。
- 新增工具：`tools/export_product_api_field_catalog.py`。
- 新增测试：`tests/test_product_api_field_catalog.py`。
- 新增目录产物：`tests/product_api_field_catalog_v0.4.18.6.json`。
- 新增说明文档：`docs/product_api_field_catalog_v0.4.18.6.md`。
- 边界：只读取 fixture 和 endpoint constants；不启动服务、不调用 RAG/Qdrant/LLM、不接真实外部数据源。

## v0.4.18.5 维护补充

- 当前应用与健康检查版本：`0.4.18.5`。
- 当前重点：将 v0.4.18.4 的 product mock endpoint contract 接入为真实 FastAPI fixture-backed 产品接口。
- 新增后端分层：`src/product/contracts.py`、`src/product/schemas.py`、`src/product/service.py`、`src/product/router.py`。
- 新增工具：`tools/check_product_api_contract.py`。
- 新增测试：`tests/test_product_api_contract.py`。
- 新增报告：`tests/product_api_contract_v0.4.18.5_report.json`。
- 新增说明文档：`docs/product_api_backend_integration_v0.4.18.5.md`。
- 边界：接口真实暴露，但数据源仍为 fixture sample；不调用 RAG/Qdrant/LLM，不接真实行情、地图、供应链或权限系统。

## v0.4.18.4 维护补充

- 当前应用与健康检查版本：`0.4.18.4`。
- 当前重点：将 product view model contract 映射为离线 product mock endpoint contract，供 UI handoff 和未来接口讨论使用。
- 新增工具：`tools/check_product_mock_endpoint_contract.py`。
- 新增测试：`tests/test_product_mock_endpoint_contract.py`。
- 新增报告：`tests/product_mock_endpoint_contract_v0.4.18.4_report.json`。
- 新增说明文档：`docs/product_mock_endpoint_contract_v0.4.18.4.md`。
- 边界：不新增正式 FastAPI 路由、不启动服务、不接 UI、不调用 RAG/Qdrant/LLM、不修改知识库、eval case、anchor、prompt、rerank 或 risk supplement。

## v0.4.18.3 维护补充

- 当前应用与健康检查版本：`0.4.18.3`。
- 当前重点：定义 dashboard、legal workspace、market signals、supply-chain map 和 lifecycle risk 的离线产品 view model contract。
- 新增工具：`tools/check_product_view_model_contract.py`。
- 新增测试：`tests/test_product_view_model_contract.py`。
- 新增 fixture：`tests/fixtures/product_view_models_v0.4.18.3.json`。
- 新增报告：`tests/product_view_model_contract_v0.4.18.3_report.json`。
- 新增说明文档：`docs/product_view_model_contract_v0.4.18.3.md`。
- 维护边界：只做 offline view model contract，不实现 UI、不新增正式 API、不接行情/地图/供应链、不调用 RAG/Qdrant/LLM、不修改主链路。

## v0.4.18.2 维护补充

- 当前应用与健康检查版本：`0.4.18.2`。
- 当前重点：将项目定位、模块和视觉方向整理成给设计专员的产品设计简报。
- 新增文档：`docs/product_design_brief_v0.4.18.2.md`。
- 维护边界：只做 UI handoff brief，不实现 UI、不新增 API、不接行情/地图、不调用 RAG/Qdrant/LLM、不修改主链路。

## v0.4.18.1 维护补充

- 当前应用与健康检查版本：`0.4.18.1`。
- 当前重点：法规扩容前先跑 `tools/check_legal_corpus_integrity.py`，确认 manifest、本地文本和 `load_txt()` 生成 metadata 仍一致。
- 新增工具：`tools/check_legal_corpus_integrity.py`。
- 新增测试：`tests/test_legal_corpus_integrity.py`。
- 新增报告：`tests/legal_corpus_integrity_v0.4.18.1_report.json`。
- 新增说明文档：`docs/legal_corpus_integrity_baseline_v0.4.18.1.md`。
- 维护边界：该 checker 是 offline-only 质量基线，不访问 Qdrant、不运行 eval、不修改 runtime、anchor、prompt、rerank、risk supplement 或 eval case。

## v0.4.17.6 维护补充

- 当前应用与健康检查版本：`0.4.17.6`。
- 当前重点：人工确认后修正 `risk_unfair_competition_confusion_001` 的旧法编号元数据文字。
- 新增报告：`tests/rag_expected_level_review_packet_v0.4.17.6_report.json`、`tests/legal_text_version_verification_packet_v0.4.17.6_report.json` 与 `docs/unfair_competition_confusion_metadata_patch_v0.4.17.6.md`。
- 维护边界：仅修改 `legal_reasoning` 说明文字；不改变 expected evidence、expected risk level、anchor、prompt、rerank、risk rule、hidden seed 或 Qdrant 数据。

## v0.4.17.5 维护补充

- 当前应用与健康检查版本：`0.4.17.5`。
- 当前重点：固化《反不正当竞争法》混淆行为条文编号核验，确认现行法第七条证据有效。
- 新增工具条目：`tools/build_legal_text_version_verification_packet.py`。
- 新增报告：`tests/legal_text_version_snapshot_v0.4.17.5.json`、`tests/legal_text_version_verification_packet_v0.4.17.5_report.json` 与 `docs/legal_text_version_verification_packet_v0.4.17.5.md`。
- 维护边界：工具运行不联网、不运行 eval，不修改 runtime、anchor、prompt、rerank、risk rule、eval case、hidden seed 或 Qdrant 数据。

## v0.4.17.4 维护补充

- 当前应用与健康检查版本：`0.4.17.4`。
- 当前重点：只读 v0.4.17.3 targeted repeat 报告，分类固定失败的真实性质。
- 新增工具条目：`tools/build_rag_expected_level_review_packet.py`。
- 新增报告：`tests/rag_expected_level_review_packet_v0.4.17.4_report.json` 与 `docs/rag_expected_level_review_packet_v0.4.17.4.md`。
- 维护边界：不运行 eval，不修改 runtime、anchor、prompt、rerank、risk rule、eval case、hidden seed 或 Qdrant 数据。

## v0.4.17.3 维护补充

- 当前应用与健康检查版本：`0.4.17.3`。
- 当前重点：按 v0.4.17.2 packet 执行 17 个 case 的 targeted repeat，并收口解释结果。
- 新增报告：`tests/targeted_rag_evidence_independence_v0.4.17.3_report.json` 与 `docs/rag_targeted_repeat_closeout_v0.4.17.3.md`。
- 维护边界：运行 targeted eval 但不修改 runtime、anchor、prompt、rerank、risk rule、eval case、hidden seed 或 Qdrant 数据。

## v0.4.17.2 维护补充

- 当前应用与健康检查版本：`0.4.17.2`。
- 当前重点：只读取 v0.4.17.1 evidence independence baseline，生成 bounded targeted rerun packet。
- 新增工具条目：`tools/build_rag_targeted_rerun_packet.py`。
- 新增报告：`tests/rag_targeted_rerun_packet_v0.4.17.2_report.json` 与 `docs/rag_targeted_rerun_packet_v0.4.17.2.md`。
- 维护边界：仅生成候选包和建议命令；不运行 eval，不调用 RAG/Qdrant/LLM，不修改 anchor、prompt、rerank、risk rule 或 eval case。

## v0.4.17.1 维护补充

- 当前应用与健康检查版本：`0.4.17.1`。
- 当前重点：只读取保存报告，建立 RAG evidence independence 基线。
- 新增工具条目：`tools/build_rag_evidence_independence_baseline.py`。
- 新增报告：`tests/rag_evidence_independence_baseline_v0.4.17.1_report.json` 与 `docs/rag_evidence_independence_baseline_v0.4.17.1.md`。
- 维护边界：仅诊断；不运行 eval，不调用 RAG/Qdrant/LLM，不修改 anchor、prompt、rerank、risk rule 或 eval case。

## v0.4.16.12 maintenance addendum

- Current app and health version: `0.4.16.12`.
- Current focus: close out the v0.4.16.x API contract stability series.
- New report doc: `docs/api_contract_stability_closeout_v0.4.16.12.md`.
- Maintenance boundary: closeout/runbook only; no new checker, no frontend integration, no RAG/Qdrant/LLM call, and no runtime behavior change.

## v0.4.16.11 maintenance addendum

- Current app and health version: `0.4.16.11`.
- Current focus: API contract consistency checker for offline frontend handoff artifacts.
- New tool entry: `tools/check_api_contract_consistency.py`.
- New reports: `tests/api_contract_consistency_v0.4.16.11_report.json` and `docs/api_contract_consistency_checker_v0.4.16.11.md`.
- Maintenance boundary: do not treat this checker as frontend integration or RAG quality repair. It only compares offline OpenAPI schema, bundle, field catalog, example payload, route refs, and guardrails.

## v0.4.16.10 maintenance addendum

- Current app and health version: `0.4.16.10`.
- Current focus: API field catalog for frontend form/display mapping.
- New tool entry: `tools/export_api_field_catalog.py`.
- New reports: `tests/api_field_catalog_v0.4.16.10.json` and `docs/api_field_catalog_v0.4.16.10.md`.
- Maintenance boundary: field catalog is an offline handoff artifact; it does not start service, call RAG/Qdrant/LLM, or change runtime behavior.

## v0.4.15.10 maintenance addendum

- Current app and health version: `0.4.15.10`.
- Runtime scope: evidence-driven term preservation in `src/rag/retriever.py`.
- No prompt, anchor, eval case, hidden seed, risk supplement, rerank, or Qdrant change.
- Validation evidence: data-export focused repeat 5/5, 8-case targeted repeat `[8, 8, 8]`, full RAG eval 60/60.

## v0.4.15.9 maintenance addendum

- Current app and health version: `0.4.15.9`.
- No runtime patch was made in this version.
- Stability evidence: targeted packet 8/8 across 3 repeats, single full eval retrieval stage `PASS=60`, and focused data-export repeat 5/5.
- The single full-eval 59/60 result is recorded as answer wording variance, not retrieval or evidence-chain regression.

## v0.4.15.8 maintenance addendum

- Current app and health version: `0.4.15.8`.
- Runtime maintenance scope: narrow existing same-bucket near-tie stabilization so large Cross-Encoder buckets keep their order.
- Risk taxonomy maintenance scope: allow canonical taxonomy `name` matches from structured risk type payloads.
- New report doc: `docs/post_near_tie_patch_main_chain_repair_v0.4.15.8.md`.
- New validation artifacts are tracked in health and artifact indexes; no file migration, Qdrant rebuild, anchor change, prompt change, or eval case change was performed.

## v0.4.15.7 maintenance addendum

- Current focus: near-tie runtime patch validation is closed. The v0.4.15.6 same-bucket deterministic ordering patch remains the only runtime change in this mini-sequence.
- New tool entry: `tools/build_post_rebuild_near_tie_patch_closeout.py`.
- New reports: `tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json` and `docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md`.
- Maintenance boundary: do not turn this closeout into another design gate chain. Future work should be regression monitoring or broader RAG quality engineering under the existing no-anchor/no-prompt/no-eval-case boundary.

## v0.4.15.6 maintenance addendum

- Current focus: near-tie runtime patch is connected to the main RAG path, but only stabilizes ordering inside existing Cross-Encoder stable-score buckets; it does not change scores, model, query, anchor, prompt, or eval cases.
- New tool entry: `tools/build_post_rebuild_near_tie_patch_validation.py`.
- New reports: `tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json` and `docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md`.
- Maintenance boundary: the validation report is passed after the targeted repeat was generated; keep future work inside the same no-anchor, no-prompt, no-eval-case boundary.

## v0.4.15.5 维护补充

- 当前重点：near-tie stability policy 已进入 review-ready design；未来若授权实现，只能做既有 stable-score bucket 内的 deterministic ordering，不能改 Cross-Encoder 分数、模型、query、anchor、prompt 或 eval case。
- 新增工具入口：`tools/build_post_rebuild_near_tie_stability_policy_design.py`。
- 新增报告：`tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json`、`docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md`。
- 维护边界：design-only；不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases；runtime patch 仍需另行授权。

## v0.4.15.4 维护补充

- 当前重点：带 v0.4.15.3 trace 的 targeted repeat 已把 `risk_algorithm_bias_001` 第三席漂移归因到 raw rerank stable order / near-tie boundary，而不是 selector replacement 额外替换。
- 新增工具入口：`tools/build_post_rebuild_selection_trace_attribution.py`。
- 新增报告：`tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json`、`tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json`、`docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md`。
- 维护边界：不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases；下一步应先设计 near-tie stability policy。

## v0.4.15.3 维护补充

- 当前重点：在不改变 rerank/selector 行为的前提下，为 `rag_query(debug=True)` 增加 full rerank score order 与 final evidence selection trace，给下一轮 targeted repeat 归因提供可观察证据。
- 新增工具入口：`tools/build_post_rebuild_selection_trace_readiness.py`。
- 新增报告：`tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json`、`docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md`。
- 维护边界：不修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases；不重跑 reranker，不改变 selector 选择语义。

## v0.4.15.2 维护补充

- 当前重点：`risk_algorithm_bias_001` 的 final evidence identity drift 已归因到 saved reranked/final top-3 边界；现有 saved report 不足以定责到 raw rerank score jitter 或 selector replacement。
- 新增工具入口：`tools/build_post_rebuild_final_evidence_drift_attribution.py`。
- 新增报告：`tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json`、`docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md`。
- 维护边界：不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases；下一步先补 selection trace，而不是直接 runtime patch。

## v0.4.15.1 维护补充

- 当前重点：targeted repeat triage 已把 v0.4.15.0 的两个信号拆开；产品责任 case 仅保留为输出措辞观察项，算法偏见 case 的 final evidence identity drift 复现，下一步应先定位漂移原因。
- 新增工具入口：`tools/build_post_rebuild_repeat_instability_triage.py`。
- 新增报告：`tests/targeted_repeat_product_liability_v0.4.15.1_report.json`、`tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json`、`tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json`、`docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md`。
- 维护边界：不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.15.0 维护补充

- 当前重点：post-rebuild repeat full RAG eval 已暴露真实稳定性信号，状态为 `needs_triage`；下一步应先 triage 输出措辞波动和 final evidence identity drift，不要继续堆 gate。
- 新增工具入口：`tools/build_post_rebuild_repeat_stability_summary.py`。
- 新增报告：`tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json`、`tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json`、`docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md`。
- 维护边界：不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

## v0.4.14.35 维护补充

- 当前重点：v0.4.14 production rebuild / post-rebuild RAG quality chain 已收口；不要继续把已闭环事项包装成新的 gate。
- 新增工具入口：`tools/build_production_rebuild_post_rebuild_series_closeout.py`。
- 新增报告：`tests/production_rebuild_post_rebuild_series_closeout_report.json`、`docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md`。
- 下一步：转入真实 RAG 质量任务，例如 retrieval input quality、final evidence explanation audit、法规扩容前 targeted smoke 或 repeat-eval stability；不要新增 anchor 或改 prompt/rerank/eval case 来掩盖质量问题。

## v0.4.14.34 维护补充

- 当前重点：post-rebuild alignment retention 已完成 selector 收紧与 protected evidence 硬保护；full RAG eval 覆盖复跑为 60/60 passed，本轮是 runtime selector 的通用质量修复，不继续堆 gate。
- 正式 RAG 报告：`tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`。
- 新增说明文档：`docs/post_rebuild_alignment_retention_tightening_v0.4.14.34.md`。
- 维护边界：不新增 anchor，不修改 rerank、prompt、risk supplement、term preservation、scenario registry、eval case 或 hidden seed。

## v0.4.14.33 维护补充

- 当前重点：selector 修复后的 delta stabilization 已完成，post-rebuild full RAG eval 仍为 60/60，且 0 个 regression、0 个 removed expected evidence。
- 新增工具入口：`tools/build_post_rebuild_alignment_retention_delta.py`。
- 新增报告：`tests/post_rebuild_alignment_retention_delta_report.json`、`docs/post_rebuild_alignment_retention_delta_v0.4.14.33.md`。
- 下一步只做 7 个 warn/关注项的抽样复核；若可解释则 v0.4.14.34 收口，若不可解释则 v0.4.14.34 收紧 selector，不继续扩展设计链。

## v0.4.14.32 维护补充

- 当前重点：post-rebuild full RAG eval 已从 58/60 恢复到 60/60；下一步应做 evidence delta stabilization，确认 selector retention 触发范围可解释。
- 新增正式报告：`tests/post_rebuild_rag_eval_after_alignment_retention_report.json`。
- 新增说明文档：`docs/post_rebuild_alignment_retention_v0.4.14.32.md`。
- 维护边界：不把该 selector 修复写成新增 gate，也不写成 v0.4.8.x final evidence policy 已整体采纳。

## v0.4.17.7 维护补充

- 当前重点：v0.4.17.x RAG evidence independence / retrieval quality hardening 系列已完成 full eval 收口确认；`tests/rag_eval_report_v0.4.17.7.json` 为 `59/60` passed，retrieval `PASS=60`。
- 新增说明文档：`docs/rag_full_eval_closeout_v0.4.17.7.md`。
- 维护边界：不因 `risk_unfair_competition_confusion_001` 继续补 anchor、改 prompt、改 rerank、改 risk supplement 或改 eval case；若追求全绿，先走人工法律事实强度复核。

## v0.4.14.31 维护补充

- 当前重点：重建后 full RAG eval 已从 baseline 60/60 变为 58/60；下一步应排查 `final_evidence_selection_drop` 与 `answer_keyword_coverage_gap`，不继续堆设计 gate。
- 新增工具入口：`tools/build_post_rebuild_rag_eval_summary.py`。
- 新增报告：`tests/post_rebuild_rag_eval_summary_report.json`、`docs/post_rebuild_rag_eval_summary_v0.4.14.31.md`。
- 维护边界：不修改 hidden seed、anchor、rerank、prompt、risk supplement、scenario registry、fixtures 或 eval cases 来掩盖回归。

更新日期：2026-05-16

## 定位

本文档是维护系统总入口，用于告诉维护者“想查什么去哪里”。它不改变任何工具默认路径、不迁移目录、不运行 RAG。

## 维护索引入口

- `docs/indexes/project_structure_index.md`：结构维护索引。
- `docs/indexes/project_artifact_index.md`：报告、测试产物、dry run 和人工复核产物索引。
- `docs/indexes/project_tool_index.md`：root-level `tools/*.py` CLI 入口索引。
- `docs/indexes/project_test_index.md`：`tests/` 测试套件与测试资产索引。
- `docs/maintenance_terms_guide.md`：维护术语和写作口径。

## 维护检查工具

- `tools/run_project_health_check.py`：项目轻量健康检查总入口。
- `tools/check_encoding_hygiene.py`：编码卫生检查。
- `tools/check_tool_index_consistency.py`：工具索引一致性检查。
- `tools/check_test_index_consistency.py`：测试索引一致性检查。
- `tools/check_artifact_index_consistency.py`：产物索引一致性检查。
- `tools/check_layout_migration_readiness.py`：目录迁移准备度检查。
- `tools/build_maintenance_closeout_report.py`：维护系列收束报告。
- `tools/build_ready_action_design_review_worksheet.py`：人工设计复核 worksheet 生成器；只读 gate/brief，不授权实现。
- `tools/build_ready_action_design_review_closeout.py`：人工设计评审收口外壳生成器；只读 worksheet，不记录正式结论、不授权实现。
- `tools/build_ready_action_human_closeout_decision_draft.py`：人工收口确认草案生成器；只读 closeout envelope，不记录正式结论、不授权实现。
- `tools/build_ready_action_human_closeout_confirmation_record.py`：人工收口确认记录生成器；只读 decision draft，不作为 importer completed decision、不授权实现。
- `tools/build_final_evidence_selection_policy_intake.py`：最终证据选择策略 intake 生成器；只读已保存治理/审计报告，不实现策略、不改 rerank、不接主流程。
- `tools/build_final_evidence_selection_policy_simulator_spec.py`：最终证据选择策略 saved-report simulator spec 生成器；只读 intake/audit/confirmation 报告，不实现 runtime policy、不改 rerank/prompt/eval、不接主流程。
- `tools/build_final_evidence_selection_policy_table_draft.py`：最终证据选择策略表草案生成器；只读 simulator spec 和既有 saved reports，不实现 runtime policy、不改 rerank/prompt/eval、不接主流程。

## 维护报告

- `tests/project_health_check_report.json`
- `tests/encoding_hygiene_report.json`
- `tests/tool_index_consistency_report.json`
- `tests/test_index_consistency_report.json`
- `tests/artifact_index_consistency_report.json`
- `tests/layout_migration_readiness_report.json`
- `tests/maintenance_closeout_report.json`
- `tests/ready_action_design_review_worksheet_report.json`
- `tests/ready_action_design_review_closeout_report.json`
- `tests/ready_action_human_closeout_decision_draft_report.json`
- `tests/ready_action_human_closeout_confirmation_record_report.json`
- `tests/final_evidence_selection_policy_intake_report.json`
- `tests/final_evidence_selection_policy_simulator_spec_report.json`
- `tests/final_evidence_selection_policy_table_draft_report.json`

## 当前权威路径

- 当前权威 CLI 入口：root-level `tools/*.py`。
- 当前权威测试与报告路径：`tests/`。
- 当前权威人工复核工作台页面：`tools/manual_review_visual_workbench/index.html`。
- 未来脚手架：`reports/eval`、`reports/audits`、`reports/manual_review`、`reports/dry_run`、`tools/eval`、`tools/evidence_diagnostics`、`tools/manual_review`、`tools/ops`、`tools/ingestion`。

## 日常维护顺序

1. 新增工具后，更新 `project_tool_index.md` 并运行 `check_tool_index_consistency.py`。
2. 新增测试后，更新 `project_test_index.md` 并运行 `check_test_index_consistency.py`。
3. 新增报告产物后，更新 `project_artifact_index.md` 并运行 `check_artifact_index_consistency.py`。
4. 文档或报告改动后，运行 `check_encoding_hygiene.py`。
5. 收尾时运行 `run_project_health_check.py`。

## 固定边界

- 不运行 full eval。
- 不调用 `rag_query`、后端、Qdrant 或 LLM。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- 不移动文件、不迁移默认路径，除非后续有明确迁移版本和兼容计划。
