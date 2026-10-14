# v0.4.14.28 Production Rebuild Authorization Record Intake

本版本把正式授权记录接入到既有只读 live preflight runner。它不是新的 gate，也不是 production rebuild 执行器。

## 摘要

- 工具：`tools/run_production_rebuild_live_preflight.py`
- 新增输入：`--authorization-record <json>`
- 输出：`tests/production_rebuild_live_preflight_report.json`
- 授权记录：`tests/production_rebuild_authorization_record.json`
- 当前状态：`passed`
- 当前阻断项：无

## 授权记录字段

runner 可从授权记录 JSON 读取以下字段：

- `authorization_status`
- `authorization_reference`
- `target_collection`
- `backup_or_snapshot_reference`
- `source_lineage_reference`

授权记录中的字段会与 CLI 参数进行一致性检查；如果两边都提供且不一致，preflight fail-closed。

## 禁止字段

授权记录不能携带执行型字段，例如：

- `commands`
- `authorized_actions`
- `rebuild_steps`
- `operation_log`
- `ready_to_apply`
- `qdrant_write_allowed`
- `production_rebuild_allowed`
- `collection_switch_allowed`

一旦出现这些字段，runner 会 fail-closed。授权记录只能解除只读 preflight 的授权 blocker，不能授予写入、切换 collection 或执行 rebuild。

## 边界

- 不写 Qdrant。
- 不创建、删除或恢复 snapshot。
- 不切换 collection 或 alias。
- 不运行 RAG、embedding、LLM 或 full eval。
- 不执行 production rebuild。
- 即使授权记录通过，`qdrant_write_allowed`、`production_rebuild_allowed` 和 `authorization_granted` 仍保持 `false`。

## 当前结论

用户已明确同意生产重建；本版本将该授权记录为 `tests/production_rebuild_authorization_record.json`，并用它重跑同一个只读 live preflight runner。当前报告已经 `passed` 且 blockers 为空。

这仍不等于已经执行生产 rebuild。下一步应作为独立版本执行生产 rebuild，并保留 snapshot、运行记录和 post-rebuild validation。
