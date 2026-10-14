# v0.4.13.17 Rebuild Runbook / Preflight Contract

本 contract 只定义未来 rebuild execution series 的 runbook 和 preflight 报告契约。它不运行 live preflight，不访问 Qdrant，不 rebuild。

## 摘要

- 状态: `ready_for_series_closeout`
- 允许的下一步: `v0.4.13_series_closeout`
- live preflight: `False`
- 是否已经授权: `False`
- 是否允许 rebuild: `False`

## Preflight Checks

- `authorization_record_present_and_valid`
- `target_collection_confirmed`
- `backup_or_rollback_collection_verified`
- `source_lineage_confirmed`
- `expected_id_drift_acknowledged`
- `maintenance_window_active`
- `rollback_owner_available`
- `post_rebuild_validation_owner_available`

通过本 contract 只允许进入 v0.4.13 series closeout，仍不代表已经允许生产 Qdrant rebuild。
