# v0.4.14.24 Production Rebuild Live Preflight Snapshot Reference Probe

本版本把 production rebuild 前置检查继续往真实主链路推进：只读查询 `legal_knowledge` collection 是否已经存在可引用的 Qdrant snapshot。它不创建 snapshot，不删除 snapshot，不恢复 snapshot，不写 Qdrant，不运行 RAG/LLM/eval，也不执行 production rebuild。

## 摘要

- 状态：`blocked`
- Qdrant collection：`legal_knowledge`
- 只读方法：`list_snapshots`
- 已存在 snapshot 数量：`0`
- 可用 `backup_or_snapshot_reference`：无
- 阻断项：`backup_or_snapshot_reference_missing`
- 是否允许写入 Qdrant：`false`
- 是否允许 production rebuild：`false`

## 边界

- 本版本只证明“当前是否已有可引用 snapshot”。
- 如果没有现成 snapshot，只输出 blocked report，不自动创建 snapshot。
- `create_snapshot`、`delete_snapshot`、`recover_snapshot`、collection mutation、alias/switch、upsert、RAG、embedding、LLM、full eval 和 production rebuild 均不在本版本范围内。
- 即使未来发现现成 snapshot，本工具也只提供 preflight 输入信号，不授予正式授权或 rebuild 权限。

## 结论

v0.4.14.24 说明当前 Qdrant collection 可访问，但没有现成 snapshot reference。生产重建链路不能继续执行，直到人工明确授权创建 snapshot 或提供外部 backup/snapshot reference，并且正式授权记录也被接受。
