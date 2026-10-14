# v0.4.14.23 Production Rebuild Live Preflight Real Read-Only Probe

本版本开始接入真实 Qdrant 只读 preflight probe。它读取项目现有 Qdrant 配置和 collection 元信息，但不写入 Qdrant，不运行 RAG，不执行 production rebuild。

## 摘要

- 状态：`blocked`
- 阻断项：`authorization_record_not_accepted`、`backup_or_snapshot_reference_missing`
- 真实 Qdrant 只读 probe：`true`
- Qdrant collection：`legal_knowledge`
- points count：`7177`
- 抽样 payload：已观察到 1 条 payload，且 metadata 包含 `chunk_id` / `qdrant_point_id`
- 是否允许写入 Qdrant：`false`
- 是否允许 production rebuild：`false`

## 边界

- 只读方法：`get_collection`、`count`、`scroll(with_vectors=False, limit=1)`。
- 不调用 `ensure_collection_with_sparse()`、`create_collection()`、`delete_collection()`、`recreate_collection()`、`update_collection()`、`upsert()`、`add_documents()`、`update_vectors()` 或 alias/switch API。
- 不调用 `rag_query()`、embedding、LLM 或 full eval。
- 即使真实 collection 可达，本版本仍不会把 `authorization_status=not_collected` 升级成正式授权。

## 结论

v0.4.14.23 已经从纯 mock scaffold 推进到真实 Qdrant 只读可达性验证。当前阻断项是执行前治理条件，而不是 Qdrant 连接失败；下一步应处理真实授权/backup/snapshot 边界或继续做只读 preflight acceptance gate，不能直接进入写入或 rebuild。
