# v0.4.13.15 Human Rebuild Authorization Worksheet

本 worksheet 只列出未来人工授权需要填写的字段。当前没有收集任何人工值，没有创建授权记录，也没有授予生产 rebuild 权限。

## 摘要

- 状态: `ready_for_human_rebuild_authorization_review`
- 字段数: `10`
- 已收集字段数: `0`
- 是否已经授权: `False`
- 是否允许 rebuild: `False`
- 允许的下一步: `human_rebuild_authorization_worksheet_gate`

## Worksheet 字段

- `target_collection`: required=['collection_name', 'environment', 'endpoint_class', 'operator_visible_target_confirmation']; optional=['notes']; status=`not_collected`
- `rebuild_scope`: required=['full_collection_or_isolated_replacement', 'expected_law_corpus', 'excluded_data', 'source_manifest_or_equivalent_reference']; optional=['scope_notes']; status=`not_collected`
- `source_version`: required=['code_version', 'v0.4.13.8_source_patch_report', 'v0.4.13.11_dry_run_report', 'v0.4.13.12_runner_gate_report']; optional=['repository_state_note']; status=`not_collected`
- `expected_id_drift_acknowledgement`: required=['chunk_id_drift_expected', 'qdrant_point_id_drift_expected', 'reason_chunk_index_chunk_count_changed_identity']; optional=['drift_review_note']; status=`not_collected`
- `backup_plan`: required=['snapshot_or_export_location', 'rollback_collection_name', 'verification_owner']; optional=['backup_verification_note']; status=`not_collected`
- `rollback_plan`: required=['restore_or_swap_steps', 'stop_conditions', 'operator_responsibility']; optional=['rollback_test_reference']; status=`not_collected`
- `operator_approval`: required=['approver_name', 'approved_at', 'explicit_yes_no_authorization']; optional=['approval_channel_reference']; status=`not_collected`
- `maintenance_window`: required=['start_time', 'end_time', 'communication_owner']; optional=['stakeholder_notice_reference']; status=`not_collected`
- `post_rebuild_validation_plan`: required=['metadata_boundary_check', 'id_drift_accounting', 'limited_smoke', 'rollback_readiness', 'full_eval_policy']; optional=['validation_owner']; status=`not_collected`
- `abort_conditions_acknowledgement`: required=['missing_backup_or_snapshot', 'target_collection_unclear_or_unexpected', 'source_patch_or_dry_run_lineage_stale', 'rebuild_scope_unclear', 'rollback_plan_missing_or_untested', 'operator_approval_missing', 'expected_id_drift_not_acknowledged', 'v0.4.13.12_gate_not_passed', 'post_rebuild_validation_plan_missing']; optional=['additional_abort_condition']; status=`not_collected`

通过本 worksheet 只允许进入 worksheet gate，仍不代表已经允许生产 Qdrant rebuild。
