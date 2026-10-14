# v0.4.14.27 Production Rebuild Read-Only Live Preflight Runner

本版本把 `tools/run_production_rebuild_live_preflight.py` 从 scaffold 推进为可显式运行的只读 live preflight runner。它会访问 Qdrant 读取 collection 元信息、point count 和 1 条 payload 样本，并写出正式 preflight 报告，但仍不写 Qdrant、不切换 collection、不执行 production rebuild。

## 摘要

- 输出：`tests/production_rebuild_live_preflight_report.json`
- 当前状态：`blocked`
- 唯一阻断项：`authorization_record_not_accepted`
- Qdrant collection：`legal_knowledge`
- points count：`7177`
- 只读方法：`get_collection`、`count`、`scroll(with_vectors=False, limit=1)`
- 是否允许 Qdrant 写入：`false`
- 是否允许 production rebuild：`false`

## 执行口径

新增显式 CLI 模式：

```powershell
.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight.py --run-readonly-live-preflight --collection legal_knowledge --authorization-status not_collected --backup-or-snapshot-reference <snapshot-reference> --source-lineage-reference ingestion-metadata-source-patch-v0.4.13.8 --output tests\production_rebuild_live_preflight_report.json --allow-blocked-output
```

默认不运行 live preflight，仍可写历史 scaffold status report。只有传入 `--run-readonly-live-preflight` 才会执行真实只读 probe。

## 边界

- 不写入 Qdrant，不创建/删除/恢复 snapshot。
- 不切换 collection 或 alias。
- 不运行 RAG、embedding、LLM、eval。
- 不执行 production rebuild。
- `authorization_status=accepted` 还必须配合非空 `authorization_reference` 才能通过正式授权检查。
- 即使 preflight 未来通过，也仍只代表“执行前只读检查通过”，不自动执行 rebuild。

## 结论

v0.4.14.27 已经开始真正连接执行前主链路：正式 preflight 报告已生成，Qdrant 可达、snapshot reference 可用、source lineage 可用，但正式 rebuild 授权仍未接受。下一步应补齐正式授权引用，然后重新运行同一个只读 live preflight，而不是再增加 gate。
