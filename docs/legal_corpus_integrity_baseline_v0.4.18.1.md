# v0.4.18.1 Legal Corpus Integrity Baseline

## 目的

本版本启动 v0.4.18.x 法规扩容前的入库质量硬化系列。目标是在继续增加法律、法规、标准入库之前，先建立一个可重复运行的本地 corpus integrity baseline，确认现有 `knowledge_manifest.json`、`src/knowledge/**/*.txt` 与 `load_txt()` 生成的 Document metadata 是否一致、完整、可追踪。

## 新增工具

- `tools/check_legal_corpus_integrity.py`
- 默认输入：`knowledge_manifest.json` 与 `src/knowledge`
- 默认输出：`tests/legal_corpus_integrity_v0.4.18.1_report.json`

该工具只读取本地 manifest 和文本文件，并复用 `src.rag.ingestion.load_txt()` 生成离线 Document 对象。它不访问 Qdrant，不调用 `rag_query`，不运行 eval，不调用 LLM，不修改知识库文本，也不修改 runtime 行为。

## 检查信号

- manifest 必填字段完整性：`source`、`file_path`、`document_type`、`law_level`、`authority_level`、`jurisdiction`、`issuing_authority`、`category`、`domain`、`version`、`effective_date`。
- manifest 唯一性：`source` 与 `file_path` 不重复。
- 知识库覆盖：`src/knowledge/**/*.txt` 不应存在 manifest 外孤儿文件。
- 文件路径边界：manifest 文件必须位于 `src/knowledge` 下并指向 `.txt`。
- 离线生成完整性：`load_txt()` 对每个 manifest 文档都能生成 Document。
- 核心 metadata：生成文档具备 `source`、`document_type`、`law_level`、`authority_level`、`jurisdiction`、`issuing_authority`、`category`、`version`、`chunk_id`、`qdrant_point_id`。
- chunk 边界：`article`、`paragraph`、`item`、`standard_section` 必须具备有效的 `chunk_index/chunk_count`。
- citation：条文和标准正文块必须具备 citation。
- expected anchors：manifest 中声明的 `article_no` 或 `section_no` 必须能在生成文档中找到。
- per-domain summary：按 `domain` 汇总文档数、通过数、失败数、错误/警告数和生成 chunk 数。
- high-risk manual review：当存在错误时输出待人工复核清单。

## 当前结果

`tests/legal_corpus_integrity_v0.4.18.1_report.json` 显示：

- `status=passed`
- `manifest_documents=15`
- `generated_documents=7177`
- `passed_documents=15`
- `failed_documents=0`
- `error_count=0`
- `warning_count=0`
- `orphan_knowledge_file_count=0`

按 domain 统计，现有 corpus 覆盖 `civil_law`、`corporate`、`data_compliance`、`data_compliance_standard`、`data_export`、`intellectual_property`、`market_regulation`、`security_compliance` 和 `tax`。

## 工程结论

现有 15 份法规/标准在离线 manifest 与 `load_txt()` 生成层面通过完整性基线。v0.4.18.x 后续可以在此基础上继续推进法规扩容前的 source/version lineage、单法新增 dry-run、targeted smoke 和扩容影响评估。

## 边界

- 不访问 Qdrant。
- 不重建 `legal_knowledge`。
- 不运行 RAG eval、risk eval、report eval 或 hidden eval。
- 不修改 anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry 或 eval case。
- 不修改知识库文本和 manifest 内容。
- 本版本是入库质量诊断基线，不是样本修补工具。
