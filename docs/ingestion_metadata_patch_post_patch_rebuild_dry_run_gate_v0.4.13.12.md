# v0.4.13.12 Post-Patch Rebuild Dry-Run Runner Gate

本门禁只读取 v0.4.13.11 saved report，验证 post-patch rebuild dry-run runner 的输出是否稳定。它不重跑 runner，不访问 Qdrant，不写 collection，不 rebuild，不调用 RAG/embedding/LLM，也不运行 full eval。

## 摘要

- 状态: `passed`
- 检查项: `11`
- 失败项: `0`
- 允许的下一步: `rebuild_authorization_design`
- 是否允许重跑 runner: `False`
- 是否允许写入 Qdrant: `False`
- 是否允许 rebuild: `False`
- full eval: `not_run`

## 检查项

- `PASS` `runner_report_version`: Runner report must be v0.4.13.11.
- `PASS` `runner_report_schema`: Runner report schema must match the post-patch rebuild dry-run runner.
- `PASS` `runner_scope`: Runner report must remain local saved-report dry-run scoped.
- `PASS` `lineage`: Runner lineage must reference the passed v0.4.13.8 source patch, v0.4.13.9 design, and v0.4.13.10 design gate reports.
- `PASS` `summary_contract`: Summary must show 3 samples, 9 rows, full metadata presence, expected ID drift, zero forbidden drift, zero blockers, and no runtime permissions.
- `PASS` `guardrails_locked`: Guardrails must keep saved-report/local scope and block Qdrant, rebuild, RAG, embedding, LLM, full eval, ingestion/retrieval/rules/eval mutation.
- `PASS` `sample_contract`: Samples must cover the three required shapes without case-id or hidden-seed dependency, with expected document counts and no blockers.
- `PASS` `row_contract`: Each row must have chunk_index/chunk_count, expected chunk_id/qdrant_point_id drift, stable content/citation/block metadata, required drift tags, and no blockers.
- `PASS` `comparison_contract`: Comparison contract must describe simulated pre-patch metadata, current build_article_documents output, expected boundary/ID drift, and forbidden content/citation/block drift.
- `PASS` `blockers_empty`: Runner report must have no top-level blockers.
- `PASS` `handoff_boundaries`: Handoff must keep Qdrant write, rebuild, rag_query, embedding/LLM, full eval substitution, and runtime/eval mutation blocked.

## 边界

- 只读取 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json`。
- 不重新生成样本，不重跑 runner，不访问或写入 Qdrant，不 rebuild collection。
- 不调用 `rag_query`、embedding、LLM 或 full eval。
- 不修改 ingestion、retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
- 通过后只开放 rebuild authorization design，不代表已经允许生产 rebuild。
