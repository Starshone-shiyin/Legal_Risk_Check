# v0.4.13.9 补丁后 rebuild dry-run 设计

本报告只设计未来的补丁后 rebuild dry-run。它不写入 Qdrant、不重建 collection、不调用 RAG、不调用 embedding 模型、不调用 LLM，也不运行 full eval。

## 摘要

- 状态: `ready_for_post_patch_rebuild_dry_run_design_gate`
- 允许的下一步: `post_patch_rebuild_dry_run_design_gate`
- 是否允许实现: `False`
- 是否允许创建 runner: `False`
- 是否允许写入 Qdrant: `False`
- 是否允许 rebuild: `False`

## 未来 Runner 设计

- 未来 runner: `run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`
- runner 状态: `not_created_in_this_version`
- 样本策略: `{'minimum_samples': 3, 'required_shapes': ['single paragraph article', 'paragraph plus item article', 'multi-paragraph article'], 'case_id_dependency': 'disallowed', 'hidden_seed_dependency': 'disallowed'}`

## 对比字段

- `must_be_present_after_patch`: `['chunk_index', 'chunk_count']`
- `expected_to_change_if_rebuild_materializes`: `['chunk_id', 'qdrant_point_id']`
- `must_remain_stable`: `['page_content', 'citation', 'block_type', 'paragraph_no', 'item_no', 'item_label', 'parent_article_id']`

## 输出契约

- Summary fields: `['status', 'sample_count', 'row_count', 'metadata_presence_rows', 'expected_id_drift_rows', 'forbidden_drift_count', 'blocking_condition_count', 'allowed_next_step', 'qdrant_write_allowed', 'rebuild_allowed', 'full_eval']`
- Row fields: `['sample_id', 'document_role', 'block_type', 'before_metadata', 'after_metadata', 'chunk_index', 'chunk_count', 'chunk_id_drift', 'qdrant_point_id_drift', 'content_stable', 'citation_stable', 'block_metadata_stable', 'detected_drifts', 'blocking_conditions']`
- Blocking conditions: `['source_patch_report_missing_or_failed', 'chunk_boundary_metadata_missing', 'forbidden_content_or_citation_drift', 'unexpected_standard_section_drift', 'qdrant_write_requested', 'collection_rebuild_requested', 'rag_or_llm_call_requested', 'eval_case_or_fixture_mutation_requested']`

## 仍不允许

- create the rebuild dry-run runner
- write Qdrant
- rebuild collection
- modify ingestion or retrieval source
- modify anchors, risk rules, scenario registry, fixtures, or eval cases
- run full eval as a substitute for the rebuild dry-run contract
