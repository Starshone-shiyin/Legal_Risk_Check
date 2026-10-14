# v0.4.14.25 Production Rebuild Live Preflight Snapshot Create Reference Capture

本版本在用户明确授权后，为 `legal_knowledge` collection 创建一个 Qdrant snapshot，并捕获可用于后续 fail-closed live preflight 的 `backup_or_snapshot_reference`。它不写入 collection points，不切换 collection，不恢复或删除 snapshot，不运行 RAG/LLM/eval，也不执行 production rebuild。

## 摘要

- 状态：`passed`
- 用户授权：`user_explicitly_authorized_snapshot_creation`
- Qdrant collection：`legal_knowledge`
- 方法顺序：`list_snapshots -> create_snapshot(wait=True) -> list_snapshots`
- 创建前 snapshot 数量：`0`
- 创建后 snapshot 数量：`1`
- 生成 snapshot：`legal_knowledge-2019706566507018-2026-06-05-09-50-24.snapshot`
- `backup_or_snapshot_reference`：`qdrant-snapshot://collection/legal_knowledge/legal_knowledge-2019706566507018-2026-06-05-09-50-24.snapshot`
- 是否允许 production rebuild：`false`

## 边界

- snapshot 创建仅限本次用户明确授权的 `legal_knowledge` collection snapshot。
- 工具通过 `--authorized-snapshot-create` 显式开关防止误执行；collection 不是 `legal_knowledge` 时会在调用 client 前 blocked。
- `delete_snapshot`、`recover_snapshot`、full/shard snapshot create、collection mutation、alias/switch、upsert、RAG、embedding、LLM、full eval 和 production rebuild 均不在本版本范围内。
- snapshot reference 已补齐，但正式 rebuild 授权仍未接受；因此后续 live preflight 仍应 fail-closed。

## 结论

v0.4.14.25 已补齐 production rebuild 前置条件中的 backup/snapshot reference。随后重新运行真实只读 preflight 后，阻断项已缩小为 `authorization_record_not_accepted`；这说明 Qdrant 可达性与 backup/snapshot 条件已经具备，但仍不能执行 rebuild，直到正式 rebuild 授权记录被接受。
