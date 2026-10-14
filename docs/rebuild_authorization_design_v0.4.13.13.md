# v0.4.13.13 Rebuild Authorization Design

本报告只设计未来生产 rebuild 的人工授权 envelope。它不创建授权记录，不访问 Qdrant，不写 collection，不 rebuild，不调用 RAG/embedding/LLM，也不运行 full eval。

## 摘要

- 状态: `ready_for_rebuild_authorization_design_gate`
- 允许的下一步: `rebuild_authorization_design_gate`
- 是否需要人工授权: `True`
- 是否已经授权: `False`
- 是否允许写入 Qdrant: `False`
- 是否允许 rebuild: `False`
- full eval: `not_run`

## 必填授权字段

- `target_collection`
- `rebuild_scope`
- `source_version`
- `expected_id_drift_acknowledgement`
- `backup_plan`
- `rollback_plan`
- `operator_approval`
- `maintenance_window`
- `post_rebuild_validation_plan`
- `abort_conditions_acknowledgement`

## 终止条件

- `missing_backup_or_snapshot`
- `target_collection_unclear_or_unexpected`
- `source_patch_or_dry_run_lineage_stale`
- `rebuild_scope_unclear`
- `rollback_plan_missing_or_untested`
- `operator_approval_missing`
- `expected_id_drift_not_acknowledged`
- `v0.4.13.12_gate_not_passed`
- `post_rebuild_validation_plan_missing`

## 边界

- create or accept human authorization record
- write Qdrant
- rebuild collection
- run rebuild preflight against a live collection
- call rag_query
- call embedding or LLM services
- run full eval as a substitute for authorization
- modify ingestion, retriever, rerank, prompt, anchors, risk rules, scenario registry, fixtures, or eval cases

通过本设计只允许进入 `rebuild_authorization_design_gate`，仍不代表已经允许生产 Qdrant rebuild。
