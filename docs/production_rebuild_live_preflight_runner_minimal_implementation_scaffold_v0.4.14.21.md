# v0.4.14.21 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold

本版本创建最小 runner scaffold，但仍不运行 live preflight，不访问真实 Qdrant，不写入 Qdrant，不接受正式授权，不执行 production rebuild。

## 摘要

- 状态：`ready_for_minimal_scaffold_gate`
- 允许的下一步：`production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate`
- 已创建 runner scaffold：`tools/run_production_rebuild_live_preflight.py`
- 已创建 mock-only 单测：`tests/test_production_rebuild_live_preflight_runner.py`
- 未创建正式 live preflight 输出：`tests/production_rebuild_live_preflight_report.json`

## 实现边界

- 核心逻辑只使用 Python 标准库。
- 默认没有 live probe，也没有真实 Qdrant endpoint 或环境变量连接路径。
- 只有显式注入的 `qdrant_readonly_probe` 才能参与 mock/read-only 检查。
- fake probe 通过时，也仍保持 `qdrant_write_allowed=false`、`production_rebuild_allowed=false`、`authorization_granted=false`。
- 缺少授权、目标 collection 不匹配、backup/source lineage 缺失、probe 抛错、probe 暴露写方法时全部 fail closed。

## 结论

v0.4.14.21 只证明 runner scaffold 可以以 mock-only、fail-closed 方式落地。它不代表已经允许连接生产 Qdrant、运行 live preflight、接受正式人工授权或执行 production rebuild。
