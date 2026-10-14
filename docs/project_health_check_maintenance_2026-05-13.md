# Project Health Check Maintenance - 2026-05-13

## 定位

本次是工程质量维护，不单独升业务版本。当前 `src/main.py` 仍保持 `0.4.7.8.20`。

目标是收紧离线人工复核链路的安全边界，并提供后续每个小版本收尾可重复运行的轻量健康检查。该工具会写出一个健康检查报告，但不会运行 RAG、后端、Qdrant、LLM 或修改检索/规则/样本。

## 主要调整

- `tools/import_manual_review_workbench.py` 现在只接受 visual workbench 正式导出的 JSON：`scope="filled visual manual review workbench export"` 且 `summary.export_policy="ready_human_drafts_only"`；CSV 仅用于人工阅读，不再作为正式 importer 输入。
- importer 会逐项拒绝 advisory / AI suggestion / human-confirmation 标记，避免辅助稿或旧预填被当成 completed manual decision。
- advisory/mobile/pilot 文件即使误带 `workbench_items` 和 `reviewer_input_template`，也会被 importer 拒绝。
- importer 在标记 `completed` 前先检查 `reviewer`、`reviewed_at`、`decision`、`rationale`，避免不完整人工字段提前进入 proposed completed 状态。
- visual workbench 只会挂载合法的 advisory pilot batch；非 advisory 或包含 completed manual decisions 的 pilot batch 不会进入页面队列。
- 新增 `tools/run_project_health_check.py`，输出 `tests/project_health_check_report.json`。
- 新增 `tools/_shared/layout.py`，提供项目根目录识别、legacy report path、future report scaffold path、显式 fallback 解析和 compatibility contract。
- 第三批 layout helper 试点覆盖 manual review/workbench 工具链：visual workbench builder、workbench importer、export pipeline dry run、Round 1 support 和 mobile decision aid。该试点只统一直接 `tests/<report>.json` 报告默认路径的表达方式，不迁移 HTML、Markdown、schema、CSV、eval case、config 或 dry-run artifact 目录。
- 新增 `docs/indexes/project_artifact_index.md`，用面向维护者和 reviewer 的方式说明 eval、evidence diagnostics、manual review、dry-run、schema、fixture、docs 和 future `reports/` scaffold 的文件归属。
- 新增 `docs/indexes/project_tool_index.md`，用面向维护者和 reviewer 的方式说明当前 root-level `tools/*.py` CLI 入口、输入输出、advisory-only 属性，以及是否可能触发 RAG/Qdrant/LLM。
- 新增 `tools/check_encoding_hygiene.py` 和 `tests/encoding_hygiene_report.json`，用于扫描 UTF-8 解码错误、非预期 mojibake 标记、可疑 `。?` 分隔符和临时目录残留；该工具只输出报告，不修改或删除文件。
- 新增 `tools/check_tool_index_consistency.py` 和 `tests/tool_index_consistency_report.json`，用于扫描 root-level `tools/*.py` 是否全部进入 `docs/indexes/project_tool_index.md`，并标注可能触发 RAG/Qdrant/LLM 的敏感入口。

## 健康检查覆盖

- 关键工具源码语法检查，使用内置 `compile()`，不写 `.pyc` 字节码。
- 关键报告存在性。
- Round 1/mobile advisory 报告不含 importer 可识别的人工复核字段。
- 离线工具未出现 `rag_query`、`/ask`、`ChatOpenAI`、`QdrantClient` 等主流程/后端/LLM 入口。
- 结构维护脚手架目录存在性：`reports/eval`、`reports/audits`、`reports/manual_review`、`reports/dry_run`、`docs/indexes`、`docs/archive`、`tools/_shared` 及后续工具分组目录。
- 结构维护脚手架纯度：上述新目录当前只能包含占位文件、说明文件和明确允许的 `_shared` 兼容层模块，不能夹带迁移后的工具脚本或生成报告。
- Layout compatibility contract：确认 legacy `tests/*.json` 报告仍是权威路径，future `reports/<group>/` 只作为显式 mirror/fallback 计算目标，不会自动迁移。
- Layout helper pilot defaults：确认首批诊断工具、第二批 evidence report builders 和第三批 manual review/workbench 工具已使用 `legacy_report_path()` 表达适用的报告默认路径，且默认值仍指向 `tests/*.json`。
- Dry-run artifact contract：确认 `tests/manual_review_export_pipeline_dry_run_artifacts` 仍是隔离中间产物目录，没有被映射或重定向到 `reports/`。
- Artifact index：确认 `docs/indexes/project_artifact_index.md` 存在，并覆盖关键报告锚点和 future report scaffold 锚点，避免后续新增产物后用户无法判断文件用途。
- Tool index：确认 `docs/indexes/project_tool_index.md` 存在，并覆盖关键 CLI 入口、代表性产物、future tool scaffold、advisory 边界和 RAG/Qdrant/LLM 触发风险锚点。
- Encoding hygiene report：确认编码卫生报告存在、状态通过、UTF-8/error 计数为 0，并保留“不修改扫描文件、不删除或移动文件”的 guardrail。
- Tool index consistency report：确认 root-level `tools/*.py` 均被工具索引覆盖，关键边界锚点存在，且敏感入口只作为诊断信号报告，不触发实际 RAG/Qdrant/LLM 调用。
- `src/main.py` 版本与当前维护基线一致。

## 边界

- 不修改 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。
- 不生成 completed manual decision、promotion candidate 或 ready action candidate。
- 不迁移现有 `tests/*.json` 报告或 `tools/*.py` 入口；新目录只是后续兼容迁移的脚手架。
- 不改变任何工具默认输出路径；`tools/_shared/layout.py` 只提供路径计算和健康检查信号。
- 不把 visual workbench HTML、Markdown 文档、decision schema、CSV 输入、eval case、config 或 dry-run artifact 目录纳入 report migration。
- 不把 artifact index 写成精确迁移清单；它只说明当前文件归属和维护规则。
- 不把 tool index 写成工具迁移清单；它只说明当前 root-level CLI 入口和运行边界。
- 不把 tool index consistency report 写成自动迁移或自动修复工具；它只报告索引覆盖和敏感入口信号。
- 已在确认无引用且目录为空后删除临时目录 `tests/tmp3wfrvcjf`；未删除任何非空产物目录。

## 运行方式

```powershell
.\venv\Scripts\python.exe tools\run_project_health_check.py --output tests\project_health_check_report.json
```
