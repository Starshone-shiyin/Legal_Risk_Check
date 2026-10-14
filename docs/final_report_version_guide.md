# 最终报告版本演进指南

本文档用于把项目每个版本的技术工作转化为可写入结题报告、答辩材料或阶段总结的表达。后续每次版本更新时，建议同步补充本文件中的“版本报告素材”，避免最后整理报告时只剩零散的 changelog。当前维护方式为把新版本补充到“版本报告素材”末尾，并尽量保留既有历史顺序；正式整理报告时可再按章节重排。

## 维护顺序说明

- `版本报告素材` 按版本号自然升序排列，从早期版本到最新版本。
- 新版本只追加到 `版本报告素材` 的最底部，不插入到文件开头或历史区块中间。
- 每次更新本文件时，先检查是否有倒序、重复或过时说明；需要清理时只整理文档顺序，不改变版本事实。

## 写作口径

本项目的演进可以概括为四个阶段：

1. 基础设施阶段：搭建 LLM、Embedding、Qdrant、FastAPI 和基础 RAG 链路。
2. 法律 RAG 阶段：围绕法律文本结构、元数据、检索质量、证据链和评测体系持续增强。
3. 风控引擎阶段：从“法律问答”升级为“场景风险识别”，形成风险分类、风险等级、整改动作和复核机制。
4. 报告交付阶段：将风险分析结果转化为可展示、可归档、可评测的企业合规风险报告。
5. 质量治理阶段：围绕 evidence grounding、scenario registry、manual review governance、visual workbench、AI suggestion isolation 和 export dry run 建立可复核闭环。

建议最终报告中不要按“改了哪些文件”写，而应按“解决了什么问题、形成了什么能力、如何验证”来写。

补充口径：advisory report、prescreen、AI suggestion、mobile aid 只能写成“辅助人工理解和排序的质量治理材料”，不能写成 completed manual decision。只有 reviewer 在 visual workbench 中填写并通过 importer、validator、promotion dry run 与 closeout gate 后，才能描述为正式人工复核结果。

结构维护口径：2026-05-13 的项目结构维护只应写成“为后续工程整理新增目录脚手架、健康检查和迁移边界说明”。不要写成已经完成目录迁移；当前 `tests/*.json` 报告和根目录 `tools/*.py` 入口仍是权威路径。

兼容层口径：Project Layout Compatibility Layer 可以写成“为未来目录整理建立路径映射和兼容检查”，不能写成“报告已迁移到 reports/”。该层当前只提供 `tests/` 到 `reports/<group>/` 的显式 mirror/fallback 计算，并通过健康检查确认 legacy 路径仍为默认选择。

兼容层试点口径：首批接入只覆盖离线诊断工具的默认路径表达方式，工程意义是降低未来迁移风险；报告中不要写成“目录已经整理完成”或“工具已经迁移到子目录”。

第二批兼容层试点口径：evidence report builders 的接入仍属于维护性重构，只能描述为“统一 legacy report path 表达并增加健康检查覆盖”，不能描述为报告路径迁移。

第三批兼容层试点口径：manual review/workbench 工具链的接入仍是维护性重构，只能描述为“让人工复核相关报告默认路径通过兼容层表达，并由健康检查证明默认位置仍为 `tests/*.json`”。不要写成 HTML、Markdown、schema、CSV、eval case、config 或 dry-run artifact 已迁移，也不要写成 manual review gate 已打开。

报告索引维护口径：`docs/indexes/project_artifact_index.md` 可以写成“为降低项目产物理解成本，建立报告/测试产物/人工复核产物的归属索引，并纳入 health check”。不要写成目录迁移、报告迁移或 RAG 能力升级；它是维护和可审阅性增强。

工具索引维护口径：`docs/indexes/project_tool_index.md` 可以写成“为降低 CLI 工具入口理解成本，建立 root-level `tools/*.py` 的用途、输入输出、advisory 属性和 RAG/Qdrant/LLM 边界索引，并纳入 health check”。不要写成工具已迁移到子目录、默认路径已切换或 RAG 能力升级；它是维护和可审阅性增强。

工具索引一致性维护口径：`tools/check_tool_index_consistency.py` 可以写成“为避免新增 CLI 工具后漏更新工具索引，新增 root-level `tools/*.py` 覆盖检查和敏感入口信号报告”。不要写成工具自动迁移、自动修复或运行 RAG/Qdrant/LLM；该工具只输出维护信号。

编码卫生维护口径：`tools/check_encoding_hygiene.py` 可以写成“为避免控制台显示问题和历史产物污染被误判，新增 UTF-8/mojibake/临时目录的离线诊断报告”。不要写成知识库清洗、RAG 修复或自动删除临时文件；该工具只输出维护信号。

## 版本报告素材

### v0.1.0：项目基础设施与最小 RAG 原型

阶段定位：完成企业风控 AI 系统的基础工程骨架。

解决的问题：项目从零开始，需要先建立可运行的 LLM 调用、向量数据库、配置管理和基础 API 服务。

关键实现：
- 建立 `src/core`、`src/rag`、`src/agents`、`src/api`、`tests` 等工程目录。
- 使用 DeepSeek 作为对话模型，使用 BGE-M3 Embedding，使用 Qdrant 作为向量数据库。
- 实现最小版 `ingestion.py` 和 `retriever.py`，支持文本切片、向量入库、相似检索和 LLM 回答。
- 搭建 FastAPI 服务与 `/health` 健康检查。

报告写法：
> 在 v0.1.0 阶段，系统完成了从环境配置到 RAG 原型的闭环搭建。该阶段重点验证了“法律文本入库、向量检索、LLM 生成回答”的最小可行链路，为后续法律风控能力建设提供了基础设施。

验证方式：
- 成功运行 Qdrant。
- 成功导入个人信息保护法节选。
- 能够基于检索证据回答基础法律问题。

### v0.2.0：法律文本元数据增强与证据链输出

阶段定位：从普通文本问答升级为法律 RAG。

解决的问题：法律文本不能只作为普通段落处理，必须保留法律名称、效力层级、分类、版本、条号和章节结构。

关键实现：
- 入库 metadata 增加 `law_level`、`category`、`version`、`article_no`。
- 识别“第X章”“第X节”“第X条”等法律结构。
- `rag_query` 输出 `evidence_chain` 与 `confidence_score`。
- FastAPI `/ask` 返回结构化 JSON。

报告写法：
> v0.2.0 将 RAG 系统从通用问答改造为面向法律文本的结构化检索系统。系统能够识别法律条文层级，并在回答中返回证据链和置信度，使回答具备可追溯性和可解释性。

验证方式：
- 能够返回条号、来源、章节、相似度等证据链字段。
- `/ask` 接口能够稳定输出 `answer`、`confidence_score` 和 `evidence_chain`。

### v0.2.1：API 安全性与检索默认行为修复

阶段定位：修复早期接口和检索风险。

解决的问题：检索结果可能混入章节标题或说明文本；接口参数缺少限制；异常信息可能暴露内部细节。

关键实现：
- 默认优先检索 `type="article"`。
- 限制 `/ask` 的 `question` 和 `k` 参数。
- 对外返回统一错误信息，内部记录日志。
- `rag_admin.py` 支持维护新增元数据。

报告写法：
> v0.2.1 对系统进行了工程安全加固，避免非条文内容污染 LLM 上下文，并对外部 API 参数和异常信息进行约束，提高了系统作为企业服务接口的可靠性。

验证方式：
- Swagger 参数校验生效。
- 默认证据链不再优先混入章节标题。

### v0.2.2：元数据过滤与跨法规检索控制

阶段定位：增强面向多法规、多类别知识库的检索控制。

解决的问题：随着法规数量增加，系统必须支持按法律名称、效力层级、分类、版本等条件过滤。

关键实现：
- `/ask` 支持 `doc_type`、`law_name`、`source`、`law_level`、`category`、`version` 等过滤参数。
- 返回 `filters` 字段，便于排查实际使用的过滤条件。
- 证据标题加入法律名称、章节、条号和相似度。

报告写法：
> v0.2.2 建立了面向多源法律知识库的过滤检索能力。系统可根据法律名称、效力层级和业务分类限定检索范围，降低跨文件误召回风险。

验证方式：
- 指定 `law_name` 或 `category` 后仅在限定范围内检索。
- 返回结果包含实际过滤条件。

### v0.2.3：轻量重排与确定性条文补充

阶段定位：解决常见法律问题召回不准。

解决的问题：纯向量检索对“原则”“同意”“敏感个人信息”等概念型问题不稳定，可能漏掉关键总则条文。

关键实现：
- 扩大候选召回池。
- 增加关键词扩展和轻量重排。
- 原则类问题确定性补充个保法第五条至第八条。
- 证据链加入 `rerank_score`、`keyword_hits`、`used_query`。

报告写法：
> v0.2.3 在不引入外部 reranker 的前提下，通过候选扩展、关键词重排和确定性条文补充，提高了法律原则类问题的召回稳定性。

验证方式：
- “个人信息保护核心原则”能够稳定命中第五条至第八条。
- 证据链可解释命中原因。

### v0.2.4：父子块结构与条款级上下文补充

阶段定位：增强法律条文上下文理解。

解决的问题：法律条文存在“前款规定”等指代，过细切片会导致 LLM 断章取义。

关键实现：
- 入库时生成父条文块，并拆分款、项子块。
- 元数据增加 `parent_article_id`、`block_type`、`paragraph_no`、`item_no`、`citation` 等字段。
- 命中子块时，LLM 上下文使用父条文全文。

报告写法：
> v0.2.4 引入父子文档块结构，使系统既能通过子块精准匹配，又能在生成回答时读取完整父条文，从而降低条款指代和断章取义风险。

验证方式：
- 证据链能够显示父条文、款、项信息。
- 回答引用格式升级为标准法律来源标签。

### v0.2.5：PDF/OCR 清洗、标准类文件入库与文档分类体系

阶段定位：扩展法律法规以外的合规知识来源。

解决的问题：国标、指南、PDF OCR 文本与普通法律条文格式不同，直接入库会导致结构丢失或乱码污染。

关键实现：
- 新增 PDF 文本质量检测工具。
- 新增 MinerU OCR Markdown 清洗工具。
- 新增文档分类推断：法律法规、标准、案例、专利等。
- 支持标准类编号章节解析，如 `3.1`、`5.2`、附录等。
- 国家标准检索自动补充过滤条件和定义章节锚点。

报告写法：
> v0.2.5 将知识库从法律条文扩展到标准类文本，建立了 OCR 清洗、文档分类、标准章节切片和标准引用标签能力，为引入国标和行业规范奠定了基础。

验证方式：
- GB/T 35273-2020 清洗后可按标准章节检索。
- 标准引用格式可显示为 `[《标准名称》5.2 章节标题]`。

### v0.2.6：检索诊断模式

阶段定位：提升 RAG 调试效率。

解决的问题：当回答质量不理想时，需要知道是向量召回、过滤条件、确定性补充还是重排出了问题。

关键实现：
- `/ask` 增加 `debug` 参数。
- 返回 `debug_info`，包含查询扩展、过滤条件、向量候选、确定性补充、重排候选和最终候选。

报告写法：
> v0.2.6 增加检索诊断模式，使开发者能够定位 RAG 链路中的召回、过滤和重排问题，显著提高调试效率。

验证方式：
- `debug=true` 时可查看完整候选流转过程。

### v0.2.7：RAG 回归评测框架

阶段定位：建立可重复的 RAG 质量验证机制。

解决的问题：每次修改检索、Prompt 或入库逻辑后，手工测试成本高且不稳定。

关键实现：
- 新增 `tools/run_rag_eval.py`。
- 题库支持 `expected_evidence`、`expected_answer_keywords`、`min_confidence_score`。
- 评测报告可保存为 JSON。

报告写法：
> v0.2.7 建立了 RAG 回归评测框架，使系统质量不再依赖人工主观试问，而是通过题库对证据命中、答案覆盖和置信度进行持续验证。

验证方式：
- 当前基础 RAG 题库可稳定通过。

### v0.2.8：场景型风控输出与风险字段评测

阶段定位：从法律问答走向风控场景判断。

解决的问题：比赛或业务展示更关注“是否有风险、风险是什么、如何整改”，而不是单纯背法条。

关键实现：
- `rag_query` 输出 `risk_level`、`risk_types`、`recommended_actions`。
- 新增高频风控场景确定性锚点。
- `run_rag_eval.py` 支持 `--check-risk`。
- 题库扩展为包含 15 条风控场景题。

报告写法：
> v0.2.8 将 RAG 输出升级为面向风控场景的结构化判断，系统能够在回答法律问题的同时给出风险等级、风险类型和整改建议。

验证方式：
- 风控场景题能够校验风险等级、风险类型和整改动作。

### v0.2.9：RAG 输出契约与人工复核标记

阶段定位：让 RAG 成为后续 Agent 的可靠底座。

解决的问题：后续 Multi-Agent 需要判断“检索是否可靠”“是否需要升级复核”，不能只依赖 LLM 自评。

关键实现：
- 增加 `retrieval_confidence`，与 `answer_confidence` 分离。
- 增加 `needs_human_review` 和 `missing_evidence`。
- 增加风险类型和整改动作的证据绑定。
- 新增检索契约单元测试。

报告写法：
> v0.2.9 建立了面向 Agent 编排的 RAG 输出契约，将回答置信度、检索置信度和人工复核标记分离，使系统能够在证据不足或高风险低置信场景下触发复核机制。

验证方式：
- 单元测试覆盖检索置信度、人工复核和证据绑定逻辑。

### v0.3.0：风险引擎层

阶段定位：正式从 RAG 问答升级为企业风险分析系统。

解决的问题：RAG 能回答问题，但企业风控需要稳定的风险分类、风险等级、法律依据和整改动作。

关键实现：
- 新增 `src/risk/taxonomy.py` 风险分类体系。
- 新增 `src/risk/analyzer.py`，封装 `analyze_risk()`。
- 新增 `POST /risk/analyze`。
- 输出 `risk_level`、`risk_categories`、`legal_basis`、`confidence` 等字段。

报告写法：
> v0.3.0 在 RAG 之上构建风险引擎层，将自然语言场景转化为标准化风控结果，实现从法律知识问答到企业合规风险识别的关键跃迁。

验证方式：
- 风控场景题能够输出结构化风险分析结果。

### v0.3.1：风险引擎回归评测

阶段定位：为风险引擎建立独立质量门禁。

解决的问题：RAG 通过不代表风险引擎可靠，需要单独校验风险等级、类别、整改动作和依据绑定。

关键实现：
- 新增 `tools/run_risk_eval.py`。
- 复用风控题库，自动筛选风险场景。
- 校验 `risk_level`、`risk_types`、`recommended_actions`、`legal_basis`、`confidence.overall`。

报告写法：
> v0.3.1 为风险引擎建立了独立回归评测机制，确保风险分类、风险等级和整改动作在后续迭代中保持稳定。

验证方式：
- 当前风控场景题 `15/15 passed`。

### v0.3.2：风险报告层

阶段定位：将风险分析结果转化为业务可读报告。

解决的问题：风险分析 JSON 适合系统调用，但不适合直接给业务、评委或人工复核人员阅读。

关键实现：
- 新增 `src/risk/report.py`。
- 新增 `POST /risk/report`。
- 输出 `executive_summary`、`risk_findings`、`action_plan`、`legal_basis`、`review_reasons`。
- 修复 LLM JSON 包裹文本解析失败问题。

报告写法：
> v0.3.2 建立风险报告层，将底层风险分析结果转化为面向业务方的报告结构，包含执行摘要、风险发现、整改计划和法律依据。

验证方式：
- 报告构建单元测试通过。
- RAG、Risk 两层回归均通过。

### v0.3.3：报告导出能力

阶段定位：让报告可展示、可归档、可集成。

解决的问题：系统需要把风险报告导出为 Markdown 或瘦身 JSON，用于前端、答辩 Demo、人工复核和归档。

关键实现：
- 新增 Markdown/JSON 导出函数。
- 新增 `POST /risk/report/export`。
- 支持 `include_evidence_chain` 和 `include_source_analysis` 控制输出体积。

报告写法：
> v0.3.3 增加风险报告导出能力，使系统分析结果能够以 Markdown 或 JSON 形式交付，满足展示、归档和系统集成需求。

验证方式：
- Markdown 导出包含固定报告章节。
- JSON 导出可按需移除底层证据链。

### v0.3.4：报告质量评测与命令行导出

阶段定位：建立报告层的可持续质量保障。

解决的问题：后续修改 RAG、风险引擎或报告模板时，需要确认最终交付报告没有结构退化。

关键实现：
- 新增 `tools/run_report_eval.py`。
- 新增 `tools/export_risk_report.py`。
- 新增 `reports/` 默认导出目录。
- 报告评测覆盖结构完整性、风险发现、行动计划、法律依据、Markdown/JSON 导出。

报告写法：
> v0.3.4 将风险报告纳入独立回归评测，并提供命令行报告导出工具，使系统具备从场景输入到报告交付的完整后端闭环。

验证方式：
- 报告回归评测 `15/15 passed`。
- 可按 `case_id` 或自定义场景导出报告。

### v0.3.5：法规清单与增量影响评测

阶段定位：支撑法规知识库扩容的测试效率优化阶段。

解决的问题：随着法规和标准数量增加，如果每新增或修改一部文档都运行完整 RAG、Risk、Report 回归，测试成本会迅速上升。系统需要一种按受影响法规、领域或文档类型筛选用例的增量评测机制。

关键实现：
- 新增 `knowledge_manifest.json`，登记法规/标准的 source、文件路径、效力层级、领域、施行日期、关键锚点和 smoke case。
- 新增 `tests/smoke_eval_cases.json`，为核心法规和标准配置轻量级验证题。
- 新增 `tools/run_impact_eval.py`，支持按 `source`、`domain`、`category`、`document_type` 或 Git 变更筛选评测范围。
- 支持按层运行 RAG、Risk、Report 评测，避免不必要的全量调用。

报告写法：
> v0.3.5 建立了法规扩容场景下的增量影响评测机制。系统通过知识库清单记录每部法规和标准的元数据、关键锚点和轻量验证用例，并可在新增或修改单部法规后仅运行受影响的 smoke case，从而降低测试成本，同时保留版本发布前的完整回归能力。

验证方式：
- 单元测试覆盖影响范围筛选逻辑。
- 按《中华人民共和国个人信息保护法》筛选出 3 条相关 smoke case。
- 增量评测 `3/3 passed`，其中风险场景用例同时通过 RAG、Risk、Report 三层验证。

### v0.3.6：入库质量门禁

阶段定位：法规扩容前的数据质量保障阶段。

解决的问题：随着法规、标准和 OCR 文本不断加入知识库，如果源文件存在乱码、目录残留、章节识别失败或关键条文缺失，会直接影响 RAG 召回质量。系统需要在写入 Qdrant 前先进行本地结构检查。

关键实现：
- 新增 `tools/check_ingestion_quality.py`，直接调用 `load_txt()` 检查真实入库前生成的 Document。
- 支持按 `source`、`domain`、`category` 筛选 manifest 文档。
- 检查源文件存在性、中文可读率、OCR/乱码噪声、条文/标准章节数量、citation 数量和关键锚点。
- 新增 `tests/test_ingestion_quality.py`，覆盖锚点匹配、文档摘要统计和中文可读率。

报告写法：
> v0.3.6 在知识库扩容流程中加入入库质量门禁。系统可在法规或标准写入向量数据库前，自动检查源文件质量、条文/章节解析结果和关键锚点是否存在，从而降低错误文本或结构缺失对后续检索准确率的影响。

验证方式：
- 单元测试 `26/26 passed`。
- 当前 manifest 中 6 部法规/标准入库质量检查 `6/6 passed`。

### v0.3.7：引用完整性校验

阶段定位：法律输出可信度与证据约束增强阶段。

解决的问题：法律风控系统最重要的质量要求之一，是回答或报告中的法条引用必须真实来自检索证据。如果模型生成了看似权威但证据链中不存在的引用，会显著降低系统可信度。

关键实现：
- 新增 `src/core/citations.py`，用于抽取 `[《...》...]` 引用并校验证据支持。
- `/ask`、`/risk/analyze`、`/risk/report` 均新增 `citation_integrity` 字段。
- 如发现未被证据链支持的引用，系统会自动触发人工复核标记。
- 风险报告层会对摘要、风险发现和行动计划中的引用再次校验。

报告写法：
> v0.3.7 在 RAG 与风险报告链路中加入引用完整性校验机制。系统能够识别回答或报告正文中的法条引用，并检查其是否来自实际检索证据；对于未被证据链支持的引用，系统会自动标记人工复核，从而增强法律输出的可追溯性和审慎性。

验证方式：
- 单元测试 `31/31 passed`。
- 按《中华人民共和国个人信息保护法》运行增量评测 `3/3 passed`。

### v0.3.8：多领域知识库扩容与评测体系规模化

阶段定位：从单领域（数据合规）向多法律领域（公司治理、市场秩序、知识产权、财税、民商事、安全合规）扩展，建立跨领域评测基线和质量门禁。

解决的问题：
- 知识库仅覆盖数据合规，无法支撑企业全面法律风控需求。
- 新领域法规入库后，缺少对应场景测试用例和快速验证机制。
- 评审答辩场景下，缺乏展示知识覆盖度和工程成熟度的量化数据。

关键实现：
- 知识库从 6 部法规扩容至 **15 部**，新增 9 部法律法规覆盖 **6 个法律领域**。
- 为每部新法规登记完整元数据（source、domain、category、version、expected_anchors、smoke_cases），纳入 `knowledge_manifest.json` 统一管理。
- 新增 **35 条**跨领域 RAG 评测案例（公司治理 6 条、市场秩序 6 条、知识产权 6 条、财税 6 条、民商事 5 条、合规反例 6 条），题库总量从 25 条增至 **60 条**。
- 新增 **17 条**新领域 smoke case，全部通过入库质量门禁（**15/15 passed**）。
- 检索模块新增 **14 组**跨领域查询扩展词和 6 个领域的确定性场景锚点（共 50+ 条规则）。
- 风险 taxonomy 从 11 类（仅数据合规）扩展至 **28 类**（覆盖 5 个新领域）。
- 评测体系扩容：RAG 26→60 题，Risk 15→50 题，Report 15→50 题，Smoke 8→25 题。

报告写法：
> v0.3.8 实现了从「数据合规专用系统」向「多法律领域平台」的关键跃迁。知识库从 6 部法规扩展至 15 部，覆盖公司治理、市场秩序、知识产权、财税、民商事、安全合规等领域；评测题库从 25 条扩展至 60 条，形成跨领域质量基线。数据合规域通过率保持 96%，新领域已建立完整的基础设施、元数据体系和评测门禁，为 v0.4.0 的领域路由和准确率提升奠定基础。

验证方式：
- 单元测试 `31/31 passed`。
- 入库质量门禁 `15/15 passed`。
- RAG Eval `30/60 passed`（数据合规域 15/15=100%，无过滤域 10/10=100%，新领域为 v0.4.0 域路由前基线）。
- Risk Eval `24/50 passed`，Report Eval `24/50 passed`。
- 增量评测 `8/25 passed`。

后续影响：
- 为 v0.4.0 的领域路由、风险 taxonomy 精调和多领域准确率提升提供了完整的测试基础设施。
- 确立了「每部新法规 → manifest + smoke case + quality gate」的扩容标准流程。

### v0.3.9：多法域 RAG 稳定化 — 规则解耦与领域路由

阶段定位：将 RAG 检索引擎从"单域硬编码"升级为"规则驱动 + 领域路由"架构，使多法域维护成本从"改 Python"降为"改 JSON"。

解决的问题：
- v0.3.8 中新增的 50+ 条场景锚点写死在 Python 代码中，法律专业人员无法直接维护。
- 缺乏领域分类能力，新法域容易出现跨域污染。
- 全量评测（60 题）耗时过长，日常开发反馈慢。

关键实现：
- **锚点规则库**：`config/rag_anchor_rules.json`，按 7 个领域组织，每条规则包含触发词、目标法律、条号、风险类型、建议动作，可由法律专业人员直接编辑。
- **领域路由器**：`src/rag/domain_router.py`，基于关键词密度匹配的确定性分类器，输出 domain + category + confidence。
- **三层评测体系**：所有评测脚本支持 `--smoke`（25 题秒级验证）、`--domain`（单域 6-10 题）、不加参数（全量 60 题）。
- 修复 `infer_filters_from_question` 对"专利""商标"等词误设 `document_type` 导致确定性锚点被跳过的 bug。

报告写法：
> v0.3.9 完成了 RAG 检索引擎的规则解耦与领域路由架构升级。确定性锚点从硬编码 Python 迁移为结构化 JSON 配置文件，支持按 7 个法律领域独立维护触发词、法条锚点和风险动作。新增领域路由器可自动判断问题所属法域，为 v0.4.0 的完整领域路由奠定基础。评测体系从单层全量升级为 smoke→domain→full 三层，日常开发从 60 题降为 25 题 smoke，迭代成本大幅降低。

验证方式：
- 单元测试 `31/31 passed`。
- 入库质量门禁 `15/15 passed`。
- RAG Eval `30/60 passed`（数据合规域 100%，新领域基线保持）。
- Smoke Eval 可用（25 题）。
- 单域评测可用（`--domain` 参数已验证）。

后续影响：
- 后续新法域的触发词精调、锚点补充只需编辑 `config/rag_anchor_rules.json`。
- 领域路由器可直接用于 v0.4.0 的强制 category 过滤，减少跨域污染。
- 三层评测体系使"快速迭代→单域验证→全量发布"的开发流程标准化。

### v0.4.0：Hybrid RAG 基础设施 + Cross-Encoder Reranker

阶段定位：引入语义精排能力，为后续 Hybrid RAG 建立基础设施。

解决的问题：
- keyword_boost 依赖手工规则，新法域覆盖不足。
- 缺乏可选的语义精排能力用于高风险场景。

关键实现：
- 通过 SiliconFlow API 集成 `BAAI/bge-reranker-v2-m3` Cross-Encoder，支持 `rag_query(use_reranker=True)` 按需开启。
- 确定锚点保护：锚点文章（score ≥ 1.0）自动提升到 2.0 锁定首位，不被 reranker 触及。
- 实现 `retrieve_with_keyword_match()`（Qdrant 全文索引）、`_rrf_fusion()`（RRF 融合）等 BM25 混合检索基础设施。

报告写法：
> v0.4.0 引入 Cross-Encoder Reranker 作为可选的语义精排组件，同时建立了确定性锚点保护机制和 BM25 混合检索基础设施。Reranker 通过 SiliconFlow API 调用，默认关闭以优先使用成熟的 keyword_boost 方案，高风险场景可按需开启。

验证方式：单元测试 31/31 passed，RAG Eval 25/60 passed。

### v0.4.0.1：Reranker A/B 测试与故障根因分析

阶段定位：通过严格的 A/B 测试确定 Reranker 的实际效果，并进行系统的故障根因分类。

解决的问题：
- 新领域评测通过率低（25/60），需要确定真正的瓶颈在哪里，避免在无效方向投入工程资源。

关键发现：
- Cross-Encoder Reranker 对当前架构**无显著影响**（92% 用例证据排序完全一致，delta=-3 来自 LLM 非确定性）。
- 故障分类：QUERY_UNDERSTANDING 40%、RETRIEVAL_MISS 31%、ANCHOR_FAILURE 28%、RERANK_ERROR 0%。
- 改进优先级：P0 锚点触发词扩充 > P1 查询扩展域化 > P2 评测关键词松弛 > P3 Reranker 暂不启用。

报告写法：
> v0.4.0.1 通过严格的 A/B 对比测试发现，Cross-Encoder Reranker 在当前锚点保护机制下对评测结果无显著边际收益。系统性地将 32 个失败用例分类为四类根因，明确了后续优化的优先级：扩充 JSON 锚点规则的触发词密度（修复 28% 故障）、增加新法域查询扩展术语（修复 31% 故障）、松弛评测关键词期望（修复 40% 故障）。

验证方式：A/B 对比测试报告 `tests/rerank_off.json` / `tests/rerank_on.json`。

### v0.4.3：Harvey 风格分层召回与单一精排

阶段定位：将检索主路径从“多路信号融合 + 规则置顶”收敛为“分层召回 + Cross-Encoder 唯一排序”的法律 RAG 检索架构。

解决的问题：
- 旧路径中 dense、BM25、规则 anchor、keyword boost/RRF 等信号混杂，难以判断评测退化的根因。
- Anchor 保护和末尾补充会绕过语义精排，使 reranker 很难真正决定最终证据顺序。
- BM25 从排序参与者变为召回扩充器后，仍需要明确进入 rerank 前的候选边界，避免候选过载。

关键实现：
- `rag_query()` 主路径固定为 Dense top-5 → BM25 top-10 → stable union 去重 → Anchor 注入 → 候选裁剪到 15 → Cross-Encoder top-3。
- 禁止 dense/sparse 分数融合、RRF 融合和 hybrid 兜底排序，Cross-Encoder 成为唯一最终排序器。
- Cross-Encoder 失败时严格 fallback 到 dense top-3，避免 sparse 或 anchor 在异常路径中改变排序语义。
- API 签名保持兼容，`use_hybrid` / `use_reranker` 参数保留，但主路径不再分叉。

报告写法：
> v0.4.3 对法律 RAG 检索链路进行了收敛式重构：系统先通过 BGE-M3 稠密向量和 BM25 稀疏向量进行分层召回，再对候选集合做稳定去重和规则锚点注入，最后统一交由 Cross-Encoder 进行语义精排。该版本取消 RRF 和分数融合，使检索证据顺序由单一 reranker 决定，更接近 Harvey 类法律检索系统的“广召回、强精排、少融合”架构，也让后续评测归因更清晰。

验证方式：
- `python -m py_compile src/rag/retriever.py`。
- `python -m py_compile src/main.py src/risk/analyzer.py tools/run_rag_eval.py`。

后续影响：
- 后续准确率优化应优先围绕候选召回覆盖率、anchor 规则质量和 Cross-Encoder 评测稳定性展开。
- 如果需要恢复 hybrid 或 RRF，应作为实验分支进行 A/B，不再混入 `rag_query()` 默认主路径。

### v0.4.5.4：测评质量修复批次

阶段定位：v0.4.5.x 作为测评质量修复线，从“排序链路可信”继续推进到“候选预算、rerank 输入、过滤器和生成表达”四类问题的收敛修复。

解决的问题：
- rerank API 返回结果可能按相关性排序并携带 `index`，旧逻辑直接按返回顺序 zip 回候选，导致高分错配到错误法条。
- anchor 在 union 后追加，但 15 条候选裁剪可能把新注入 anchor 删除，形成 `ANCHOR_CUT_MISS`。
- 同一条文的多个 paragraph/item sibling 会挤占 top-15 候选预算，导致其他条文进不了 rerank。
- item/paragraph 短片段缺少完整父条文语境，Cross-Encoder 容易误排。
- 专利问题被误推断为 `document_type="专利"`，而当前专利法规入库为 `document_type="法律法规"`，导致专利检索为空。
- 部分样本 evidence 已命中，但答案未保留法定关键词，造成 expected answer keywords 失败。

关键变更：
- `_call_siliconflow_rerank()` 按 `index` 回填 relevance score。
- `rag_query()` 保持 Dense → Sparse → Union → Anchor → Cut → Rerank 顺序，同时使用 article-aware candidate budget，且 rerank 前仍不超过 15 条候选。
- Cross-Encoder 文档侧输入改为 `citation + source/article + parent_content`。
- Cross-Encoder 查询侧使用既有 `build_search_query()` 法律概念扩展；Dense/Sparse 召回仍使用原始问题。
- 专利问题默认过滤到 `法律法规`。
- 系统提示要求保留关键法定表述和要件原词。
- 新增 `tests/test_rerank_api.py`、`tests/test_candidate_budget.py`。

报告写法：
> v0.4.5.x 作为测评质量修复线，在不恢复 RRF、不引入分数融合的前提下，连续修复 rerank 分数错配、候选预算挤占、rerank 输入短片段、专利过滤误判和答案关键词遗漏问题。最终 smoke 评测从 `2/25 passed` 提升到 `15/25 passed`，`RETRIEVAL_MISS` 降为 `0`，retrieval 层 `PASS` 达到 `20/25`。剩余问题集中在少数 all-evidence 评测口径、reranker 对多依据并列问题的 top-3 取舍，以及生成表达稳定性。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_rerank_api`、`tests.test_qdrant_index_integrity`、`tests.test_rag_eval_diagnostics`。
- Smoke RAG Eval：`15/25 passed`，`retrieval_failure_stage_summary={"RERANK_MISS": 3, "PASS": 20, "CANDIDATE_CUT_MISS": 2}`。

后续影响：
- 默认检索主路径仍保持 Harvey 风格分层召回 + 单一 rerank。
- 下一阶段质量提升不应恢复 RRF，而应继续沿失败阶段处理：少数 `CANDIDATE_CUT_MISS` 用 anchor/预算策略，`RERANK_MISS` 用 query/document 表达和评测口径校准，answer keyword 失败用生成约束和结构化答案模板。

### v0.4.5.5：剩余 Retrieval 失败专项处理

阶段定位：继续沿 v0.4.5.x 测评质量修复线，专门处理剩余 `CANDIDATE_CUT_MISS` 和 `RERANK_MISS`，并控制 API 额度消耗。

关键变更：
- `tools/run_rag_eval.py` 新增 `--case-id`，支持只运行指定失败样本。
- 候选预算改为优先保留直接 anchor，再补充 base recall；仍保持 rerank 前最多 15 条候选。
- 场景锚点命中时跳过宽泛 category fallback anchors，减少非目标法条噪声。
- Cross-Encoder top-3 选择按条文去重，避免同一条文 sibling 占满最终证据。
- Cross-Encoder 分数近似相等时保持候选稳定顺序，降低分数饱和造成的抖动。
- 修正 `pipl_location_ads`、新增 `unfair_competition_general_acts`，并限制民法典原则问题误触发 PIPL 原则补充。

报告写法：
> v0.4.5.5 将剩余 retrieval-stage 失败从“全量 smoke 反复验证”改为“指定 case 小跑验证”。系统现在可以只运行剩余失败样本，降低 API 额度消耗。同时，候选预算、场景锚点和 rerank top-3 选择进一步收敛：直接锚点优先进入候选，宽泛 category 锚点不再覆盖场景锚点，同一条文 sibling 不再挤占最终证据位。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_rerank_api`、`tests.test_rag_eval_diagnostics`。
- 语法检查：`src/rag/retriever.py`、`tools/run_rag_eval.py`、`tests/test_candidate_budget.py`。
- JSON 检查：`config/rag_anchor_rules.json` 可解析。
- Targeted Eval：只运行 5 条剩余 retrieval-stage case；`smoke_antitrust_abuse_dominance` 的 expected evidence 已进入 final。

后续影响：
- 后续验证优先使用 `--case-id` 指定小样本，不需要每次跑完整 smoke。
- 剩余 broad/all-evidence case 应继续围绕 rerank top-3 取舍与评测口径合理性处理，暂不进入生成关键词批次。

### v0.4.5.6：剩余 Candidate/Rerank Retrieval 专项收敛

阶段定位：继续沿 v0.4.5.x 测评质量修复线，专门收敛上一轮剩余的 `CANDIDATE_CUT_MISS` 与 `RERANK_MISS`，暂不进入生成关键词批次。

关键变更：
- Anchor 注入后，rerank 输入按规则锚点顺序稳定组织；候选仍不超过 15，最终仍由单一 Cross-Encoder 排序。
- 场景锚点优先于宽泛原则补充，避免 base recall 或通用原则补充在 rerank 分数饱和时抢占 top-3。
- 规则注入条文按配置中的 article 顺序排列，降低 Qdrant 返回顺序不稳定造成的证据漂移。
- 定位/行踪轨迹场景补充“单独同意”rerank 查询词；民商事原则场景补充“平等、自愿、公平、诚信、公序良俗”等法定原则词。
- 通用原则硬编码补充收敛到 PIPL/数据合规，民法典原则问题交由 JSON 场景锚点驱动。

报告写法：
> v0.4.5.6 将上一轮剩余的 retrieval 失败进一步拆到候选顺序和 rerank 查询表达两个根因。系统不恢复 RRF、不引入分数融合，而是在 Cross-Encoder 前稳定规则锚点候选顺序，并补齐场景化法定术语，使剩余 5 条 targeted case 的 retrieval 层全部通过。Full smoke 进一步确认 25 条样本 retrieval 层全部 PASS，当前剩余失败已从检索层转移到答案关键词生成层，后续应单独处理生成模板或关键词保留策略。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_rerank_api`、`tests.test_rag_eval_diagnostics`。
- 语法检查：`src/rag/retriever.py`、`tools/run_rag_eval.py`、`tests/test_candidate_budget.py`。
- Targeted Eval：5 条剩余 retrieval-stage case，`4/5 passed`，`retrieval_failure_stage_summary={"PASS": 5}`。
- Full Smoke Eval：`19/25 passed`，`retrieval_failure_stage_summary={"PASS": 25}`。

后续影响：
- 本轮 2 个 `CANDIDATE_CUT_MISS` 与 3 个 `RERANK_MISS` 已在 targeted 范围内清零，full smoke 中 retrieval 层也已全部通过。
- 下一步不要回退到融合排序；应处理生成关键词稳定性。

### v0.4.5.7：生成关键词稳定性专项

阶段定位：在 retrieval 全部 PASS 后，专门处理 evidence 已命中但答案漏掉法定关键词的问题。

关键变更：
- 新增 `enrich_answer_legal_terms()`，在 LLM 生成后、返回前补充证据支持的法定原词。
- 覆盖股东权利、反不正当竞争行为、滥用市场支配地位、商标侵权、不得注册、增值税不得抵扣、专利侵权等易被同义改写的表达。
- 仅当问题语义和 evidence source 同时匹配时补充“术语归纳”，避免无证据扩写。
- 不改变 Dense/Sparse 召回、Anchor 注入、候选预算或 Cross-Encoder 排序。

报告写法：
> v0.4.5.7 将质量修复从检索层推进到生成层。在 v0.4.5.6 已确认 full smoke 的 retrieval 层全部通过后，该版本针对 LLM 同义改写导致的答案关键词缺失增加确定性法定原词保留层。修复后 smoke 评测达到 `25/25 passed`，同时 `retrieval_failure_stage_summary={"PASS": 25}`，说明当前 25 条 smoke 样本已形成“检索全命中 + 生成关键词稳定”的闭环。

验证方式：
- 单元测试：`tests.test_retriever_contract`、`tests.test_candidate_budget`、`tests.test_rerank_api`、`tests.test_rag_eval_diagnostics`。
- Targeted Eval：7 条生成关键词稳定性样本，`7/7 passed`。
- Full Smoke Eval：`25/25 passed`，`retrieval_failure_stage_summary={"PASS": 25}`。

后续影响：
- v0.4.5.x 可作为测评质量修复线的稳定检查点。
- 下一步应扩大到全量 RAG Eval / Risk Eval，而不是继续针对 smoke 做小修。

### v0.4.5.8：全量 RAG Eval 召回契约与锚点校准

阶段定位：从 smoke 闭环进入 60 题全量 RAG Eval，专门处理 smoke 之外暴露出的过时评测契约、法条条号漂移和场景锚点 rerank 意图不稳定问题。

关键变更：
- `tools/run_rag_eval.py` 新增 `expected_evidence_min_match`，支持 top-3 evidence 下的核心证据命中数校验。
- `rag_query()` 在单一 Cross-Encoder rerank query 中追加场景锚点法条提示，不恢复 RRF、不引入 dense/sparse 分数融合。
- PIPL 定位、人脸、合规反例等场景补齐第 13、17、28、29 条锚点覆盖，并将 4-5 条 evidence 的旧全量期望收敛为 top-3 可验证的 min-match。
- 按当前知识库条文核对并修正全量题库中反不正当竞争法条号：虚假宣传为第 9 条，商业秘密为第 10 条。
- 生成后处理补齐 PIPL 原则题的“公开透明、信息质量”，以及客户名单离职使用场景的“商业秘密侵权 / 停止使用相关信息”。

报告写法：
> v0.4.5.8 将质量修复从 smoke 扩大到 60 题全量 RAG Eval。该版本没有回退到 RRF 或 hybrid 融合，而是把评测契约、规则锚点和 rerank 查询意图对齐到当前 top-3 evidence 架构。修复后 targeted 7 条全部通过；全量 RAG Eval 从 `19/60 passed` 提升到 `22/60 passed`，retrieval 层从 `PASS=38` 提升到 `PASS=47`，且 `RETRIEVAL_MISS` 与 `PARTIAL_RECALL_MISS` 清零。剩余问题集中为 `RERANK_MISS=13` 与生成字段稳定性。

验证方式：
- 单元测试：`56 tests OK`。
- Targeted Eval：7 条，`7/7 passed`，`retrieval_failure_stage_summary={"PASS": 7}`。
- Full RAG Eval：`22/60 passed`，`retrieval_failure_stage_summary={"PASS": 47, "RERANK_MISS": 13}`。

后续影响：
- 下一步不应恢复 RRF/hybrid；应专门处理剩余 13 个 `RERANK_MISS` 和 retrieval 已 PASS 但风险字段/关键词生成不稳的样本。
- 全量题库后续需要继续做“条文真实内容核对 + top-3 契约校准”，避免旧题库把不可达的 all-evidence 期望误报为系统质量失败。

### v0.4.5.9：剩余 RERANK_MISS 清零与风险字段稳定性切分

阶段定位：沿 v0.4.5.x 测评质量修复线，专门处理全量 RAG Eval 中最后一批 rerank top-3 证据错排样本，并把剩余失败类型从检索问题切分到生成字段稳定性问题。

关键变更：
- 收窄“数据出境安全评估内容”规则，避免出境合规问题被评估内容类锚点抢占。
- 为内部员工导出/出售客户名单场景补充个保法第 9、51、57、66、69 条相关 rerank 查询词。
- 新增民商事数据处理协议责任分配锚点，稳定注入民法典第 509、577 条。
- 补齐反垄断协同定价、独立定价正例的场景锚点，稳定命中反垄断法第 17 条。
- 在生成后处理层对数据处理协议泄露责任、横向垄断协议、独立定价正例做窄场景风险字段补全。

报告写法：
> v0.4.5.9 完成了 v0.4.5.x 质量修复线中检索侧最关键的收敛：全量 60 题 RAG Eval 的 retrieval stage 达到 `PASS=60/60`，不再存在 `RERANK_MISS`。该版本仍然保持 Harvey 风格的 Dense/Sparse 分层召回、Union、Anchor、单一 Cross-Encoder rerank 架构，没有恢复 RRF 或 dense/sparse 分数融合。全量通过率从 `31/60` 提升到 `35/60`，剩余失败已从检索问题转为风险字段、答案关键词和正例 low-risk 输出稳定性问题。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`，`26 tests OK`。
- Targeted Eval：5 条，`5/5 passed`，`retrieval_failure_stage_summary={"PASS": 5}`。
- Full RAG Eval：`35/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

后续影响：
- v0.4.5.x 后续不应继续扩大检索规则，而应转入生成字段稳定性专项。
- 下一阶段重点是以 taxonomy/schema 方式稳定 `risk_types`、`recommended_actions`、`risk_level` 和法定关键词，而不是回到融合检索。

### v0.4.5.10：RAG Eval 输出层全量闭环

阶段定位：在 v0.4.5.9 已将 retrieval stage 收敛到 `PASS=60/60` 后，继续沿 Harvey 风格路线处理“证据已进入上下文但结构化输出不稳定”的问题。该版本不再扩大检索规则，也不恢复 RRF / hybrid 融合，而是把风险类型、整改动作、风险等级和法定术语保留收束到证据支持的 taxonomy / policy 输出层。

关键变更：
- 新增基于 `rag_anchor_rules.json` 命中场景的风险 taxonomy 与整改动作补全，已命中的规则只影响结构化输出，不参与候选排序。
- 增加显式合规正例识别，稳定出资、分红、税务申报、真实广告、独立定价等场景的 `risk_level=low`。
- 对自动化决策、格式条款、劳务派遣、产品责任、商标、专利、公司治理、增值税、经营者集中等场景补齐风险等级和结构化字段。
- 扩展证据支持的法定术语保真，覆盖撤回同意便捷方式、个人信息安全规范定义题、个人信息出境影响评估、数据分类分级、专利无效宣告、公司人格否认、虚开发票刑事责任等波动点。

报告写法：
> v0.4.5.10 完成了 v0.4.5.x RAG Eval 质量修复线的全量闭环：在不改变 Dense/BM25 分层召回、Union、Anchor、单一 Cross-Encoder rerank 架构的前提下，将 retrieval 已 PASS 后暴露出的生成字段波动收束到证据支持的 taxonomy / policy 输出层。全量 RAG Eval 达到 `60/60 passed`，retrieval stage 保持 `PASS=60/60`，说明当前质量瓶颈已从检索与 rerank 侧转为后续更高阶的评测泛化、法规扩容和报告层一致性治理。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`，`26 tests OK`。
- Targeted Eval：剩余失败 5 条 `5/5 passed`；术语/置信度 4 条 `4/4 passed`。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

后续影响：
- v0.4.5.x 质量修复线可以暂时视为 RAG Eval 当前题库闭环。
- 下一阶段不应继续按单题硬补检索规则，而应转入更系统的回归稳健性、报告层评测、法规扩容门禁和 taxonomy 配置化治理。

### v0.4.5.11：代码债清理与输出规则表驱动化

阶段定位：在 v0.4.5.10 已实现当前 RAG Eval 全量闭环后，专门偿还检索与生成后处理层的代码债，避免质量修复阶段留下的临时逻辑继续扩大。

关键变更：
- 删除旧 `rerank_with_cross_encoder()`、`_rerank_fallback()`、`rerank_results()`，清掉 Harvey 主路径外残留的分数混合和 keyword fallback 语义。
- 将法定术语保真从长 if 链改为 `LEGAL_TERM_PRESERVATION_RULES` 规则表，集中维护问题条件、证据来源、必须保留术语、补充句和最低置信度。
- 增加 payload helper，用于后续继续把风险 taxonomy、动作建议和法言法语输出迁出大函数。
- 不改变 `rag_query()` 的 Dense/BM25 分层召回、Union、Anchor、单一 Cross-Encoder rerank 和 dense-only fallback。

报告写法：
> v0.4.5.11 是一次质量闭环后的代码债清理版本：系统删除了不再使用的旧混合排序函数，避免 Harvey 主路径外继续残留 RRF/keyword boost 思路；同时将法定术语保真逻辑改为规则表驱动，使后续扩展“法言法语”输出能力时不再依赖继续堆叠 if 链。该版本保持 full RAG Eval `60/60 passed`，retrieval stage `PASS=60/60`，说明代码整理没有破坏当前质量基线。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`，`26 tests OK`。
- Targeted Eval：术语/结构化输出 6 条，`6/6 passed`。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

后续影响：
- 继续沿配置化方向清理 `enrich_risk_payload()`，把风险 taxonomy、整改动作、正例 low-risk 和法言法语模板逐步迁到配置层。
- 代码整理应以保持 full RAG Eval 全绿为门槛，避免把质量修复成果折损成新的不稳定因素。

### v0.4.5.12：风险输出补全规则表驱动化

阶段定位：在 v0.4.5.11 删除旧混合排序函数并完成法定术语规则表化后，继续偿还输出治理层代码债，把风险场景补全从大函数分支迁入集中规则表。

关键变更：
- 新增 `RISK_PAYLOAD_SUPPLEMENT_RULES`，集中维护场景匹配条件、风险类型、整改动作、风险等级、最低置信度和补充结论句。
- 新增 `payload_rule_matches()`、`apply_payload_supplement_rule()`、`set_risk_level()` 等 helper，使 `enrich_risk_payload()` 保留主控流程，减少长 if 链继续扩张。
- 补齐儿童个人信息、监护人同意、人脸/生物识别等输出保真边角，降低 LLM 对关键法言法语同义改写造成的评测波动。
- 不改变 `rag_query()` 的 Dense/BM25 分层召回、Union、Anchor、单一 Cross-Encoder rerank 和 dense-only fallback。

报告写法：
> v0.4.5.12 继续沿 Harvey 风格路线偿还输出层代码债：检索主路径保持 Dense/BM25 分层召回、Union、Anchor、单一 Cross-Encoder rerank，不恢复 RRF 或 hybrid 分数融合；风险输出补全则迁入 `RISK_PAYLOAD_SUPPLEMENT_RULES` 规则表，便于后续把 taxonomy、整改动作和法言法语模板进一步配置化。该版本保持 full RAG Eval `60/60 passed`，retrieval stage `PASS=60/60`，说明代码债清理没有牺牲当前质量基线。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`，`26 tests OK`。
- Targeted Eval：`risk_employee_facial_001`、`risk_children_data_001` 均通过。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

后续影响：
- 下一步应把当前 Python 规则表继续外迁到配置化 taxonomy / action rules，并配套 schema 校验，减少未来法规扩容时的代码改动。
- 继续以 retrieval 分层诊断和 targeted eval 作为日常门禁，版本发布前再跑 full RAG Eval。

### v0.4.5.13：风险输出补全配置化与规则门禁

阶段定位：在 v0.4.5.12 已将风险输出补全整理成 Python 规则表后，继续把该规则表外迁到配置层，并为配置结构增加启动校验和单元测试门禁。

关键变更：
- 新增 `config/risk_payload_supplement_rules.json`，集中维护风险补全匹配条件、风险类型、整改动作、风险等级、最低置信度和补充结论句。
- 新增 `load_risk_payload_supplement_rules()` 与 `validate_risk_payload_supplement_rules()`，对未知字段、列表字段、`question_any_groups`、`risk_level`、`risk_level_mode` 和 `confidence_min` 做结构校验。
- `enrich_risk_payload()` 仍通过同一规则循环执行补全，保持运行时语义不变，但后续扩展 taxonomy / actions 可以先改 JSON。
- 为虚假宣传场景补齐“误导消费者”法言法语输出保真，降低生成层随机同义改写造成的评测波动。
- 不改变 `rag_query()` 的 Dense/BM25 分层召回、Union、Anchor、单一 Cross-Encoder rerank 和 dense-only fallback。

报告写法：
> v0.4.5.13 将风险输出补全从 Python 内部规则表进一步外迁到 JSON 配置，并增加 schema 校验和单测门禁。该版本延续 Harvey 风格路线：检索主路径不恢复 RRF 或 hybrid 分数融合，输出治理则向可维护配置层收束。Full RAG Eval 保持 `60/60 passed`，retrieval stage `PASS=60/60`，说明规则配置化没有破坏当前质量基线，也为后续法规扩容和专业人员维护 taxonomy / action rules 打下基础。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`，`30 tests OK`。
- Targeted Eval：代表性 4 条 `4/4 passed`；虚假宣传修复样本 `1/1 passed`。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

后续影响：
- 下一步可继续把 `LEGAL_TERM_PRESERVATION_RULES` 外迁，并把风险补全配置与 `rag_anchor_rules.json` 的场景锚点逐步打通。
- 配置更新应默认先跑 schema 单测和 targeted eval，再在版本发布前跑 full RAG Eval。

### v0.4.5.14：稳定性回归与规则贡献归因

阶段定位：在 v0.4.5.13 完成风险输出补全配置化后，进一步回答“60/60 是检索链路自然足够强，还是输出治理规则兜底较多”的质量归因问题。

关键变更：
- `tools/run_rag_eval.py` 新增 `--repeat`，同一题库可连续运行多轮并输出 `stability_summary`。
- 每个 case 增加贡献标签：`PURE_LLM_PASS`、`TERM_PRESERVATION_PASS`、`RISK_SUPPLEMENT_PASS`、`ANCHOR_PASS`、`DENSE_FALLBACK_PASS`。
- `rag_query()` debug 信息记录 `output_contributions` 与 `rerank_dense_fallback`，便于把检索贡献、anchor 贡献和输出治理贡献拆开观察。
- 多轮回归发现商业秘密与商标连续三年不使用两个输出波动点后，通过配置规则补齐风险等级、置信度和法言法语补充句。
- 稳定性报告采用双实验口径：保留 v0.4.5.13 原始 repeat 基线，同时记录 v0.4.5.14 patch 后 repeat 结果，避免用修复后结果覆盖原始稳定性结论。
- 不改变 Harvey 风格检索主链路，不恢复 RRF、hybrid 分数融合或 sparse fallback。

报告写法：
> v0.4.5.14 将 RAG Eval 从“是否通过”推进到“为什么通过、是否稳定通过”。需要区分两组实验对象：v0.4.5.13 原始 repeat 基线在 3 轮中分别为 `58/60`、`59/60`、`60/60`，说明单次 `60/60` 不能直接等同于稳定质量，波动点集中在商标连续三年不使用和商业秘密场景的输出治理；v0.4.5.14 patch 后 repeat 才是修复后的验证，连续 3 轮 full RAG Eval 均达到 `60/60 passed`，`unstable_cases=0`，`DENSE_FALLBACK_PASS=0`。这说明 patch 后质量基线不是依赖 fallback 兜底，但不能倒推覆盖 v0.4.5.13 的原始稳定性结论。多标签统计还显示风险补全和 anchor 仍承担较多法律输出稳定化职责，后续应继续把这些确定性规则配置化、可审计化，而不是回到 RRF 或分数融合路线。

验证方式：
- 单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`、`tests.test_rag_eval_diagnostics`，`38 tests OK`。
- Targeted Repeat Eval：两个曾波动 case 连续 3 轮均 `2/2 passed`。
- 原始基线 Repeat Eval（v0.4.5.13 pre-patch）：`58/60`、`59/60`、`60/60`，两个输出稳定性波动点，retrieval stage 仍保持 PASS。
- Patch 后 Full Repeat RAG Eval（v0.4.5.14 post-patch）：60 题连续 3 轮均 `60/60 passed`，`unstable_cases=0`，`label_variation_cases=2`，`DENSE_FALLBACK_PASS=0`。

后续影响：
- 贡献标签应成为后续扩容评测的重要维度：新增法规时不仅看 pass/fail，也要看是否过度依赖输出规则或 anchor。
- 下一步宜把贡献报告纳入发布门禁，并继续治理法定术语保真配置、anchor 与风险补全规则的重复条件。

### v0.4.5.15a：RAG 稳定性 Markdown 摘要报告

阶段定位：在 v0.4.5.14 已生成稳定性与贡献归因 JSON 后，把机器可读结果转化为人可读的阶段报告，便于审查“通过来自哪里”。

关键变更：
- 新增 `tools/summarize_rag_stability.py`，从 `tests/rag_stability_report.json` 生成 `tests/rag_stability_summary.md`。
- Markdown 摘要显式保留 v0.4.5.13 原始 repeat 基线与 v0.4.5.14 patch 后 repeat 的实验边界。
- 按 run 展示 `PURE_LLM_PASS`、`ANCHOR_PASS`、`RISK_SUPPLEMENT_PASS`、`TERM_PRESERVATION_PASS`、`DENSE_FALLBACK_PASS`。
- 单列贡献标签波动 case，以及同时依赖 `ANCHOR_PASS + RISK_SUPPLEMENT_PASS` 的规则依赖较高 case。

报告写法：
> v0.4.5.15a 将稳定性 JSON 进一步转化为可审查的 Markdown 摘要，使研发者和评审者无需直接阅读大型 JSON，也能看到两组实验边界、每轮贡献标签分布、标签波动样本和规则依赖较高样本。该版本仍不改变 RAG 检索主路径，重点是让质量结论更可读、更便于复核。

验证方式：
- 生成摘要：`tools/summarize_rag_stability.py --report tests/rag_stability_report.json --output tests/rag_stability_summary.md`。
- 单元测试：`tests.test_rag_stability_tools` 摘要相关用例通过。

后续影响：
- 后续版本发布时，稳定性报告不应只保留 JSON，还应同步生成 Markdown 摘要。
- 规则依赖较高 case 将作为 v0.4.5.16 规则债盘点的输入。

### v0.4.5.15b：RAG 稳定性轻量门禁

阶段定位：在 v0.4.5.15a 完成可读报告后，进一步把稳定性结论固化为发布前检查，防止 unstable、fallback 或实验对象混写悄悄进入版本报告。

关键变更：
- 新增 `tools/check_rag_stability_report.py`，默认检查 `unstable_cases=0` 与 `DENSE_FALLBACK_PASS=0`。
- 校验 `repeat`、`runs`、`stability_summary` 的 pass/total 计数一致，防止报告结构漂移。
- 校验 `experiment_comparison` 同时包含 `v0.4.5.13-pre-patch-repeat` 与 `v0.4.5.14-post-patch-repeat`，且顶层 runs 对应 patch 后实验。
- FastAPI 服务版本同步为 `0.4.5.15b`。

报告写法：
> v0.4.5.15b 将 RAG 稳定性报告从“人工阅读材料”进一步升级为“轻量发布门禁”。系统默认拒绝存在 unstable case、dense fallback 通过样本或实验对象混写的稳定性报告，从而保证后续版本不会把修复后结果误写成原始基线，也不会在 fallback 兜底不透明的情况下宣称质量稳定。

验证方式：
- 门禁检查：`tools/check_rag_stability_report.py --report tests/rag_stability_report.json`，通过。
- 相关单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`、`tests.test_rag_eval_diagnostics`、`tests.test_rag_stability_tools`，`44 tests OK`。

后续影响：
- 后续涉及检索、prompt 或输出规则的版本，发布前应先生成稳定性摘要，再运行稳定性门禁。
- v0.4.5.16 可基于 `tests/rag_stability_summary.md` 中的规则依赖较高 case，盘点 anchor 规则与风险补全规则的重复触发条件。

### v0.4.5.16：规则债盘点报告

阶段定位：在 v0.4.5.15b 已建立稳定性摘要与门禁后，进一步审查规则维护层的结构性债务，回答“哪些场景同时维护在 Anchor 和风险输出补全两处”。

关键变更：
- 新增 `tools/audit_rule_debt.py`，扫描 `config/rag_anchor_rules.json` 与 `config/risk_payload_supplement_rules.json`。
- 生成 `tests/rule_debt_report.json` 与 `docs/rule_debt_report_v0.4.5.16.md`。
- 报告覆盖重复 trigger、跨配置 trigger 重叠、疑似同场景多处维护、缺失共享 `scenario_id`、高规则依赖 case 到规则的映射。
- 当前扫描结果显示：Anchor rules `75`，Risk supplement rules `39`，重复 trigger `111`，跨配置 trigger 重叠 `94`，疑似同场景多处维护 `43`，高规则依赖 case `25`。
- 本版本只生成报告和测试，不合并规则，不修改 `src/rag/retriever.py`，避免影响当前质量基线。

报告写法：
> v0.4.5.16 没有继续增加规则，而是对现有规则维护方式做审计。通过自动扫描 Anchor 配置、风险输出补全配置和稳定性报告中的高规则依赖 case，系统定位出重复 trigger、跨配置同场景维护、缺失共享 scenario_id 等规则债。该版本的价值在于把“规则兜底是否越来越难维护”变成可量化清单，为后续配置收敛提供依据，同时不改变 Harvey 风格检索主路径和当前稳定质量基线。

验证方式：
- 生成报告：`tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md`。
- 相关单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`、`tests.test_rag_eval_diagnostics`、`tests.test_rag_stability_tools`、`tests.test_rule_debt_audit`，`49 tests OK`。
- `tests/rule_debt_report.json` JSON 解析通过。

后续影响：
- 后续若要合并规则，应先引入共享 `scenario_id`，再逐场景迁移，不能直接删除现有 Anchor 或风险补全规则。
- 高规则依赖 case 应作为规则合并或配置收敛时的回归保护样本。

### v0.4.5.17：规则收敛设计稿

阶段定位：在 v0.4.5.16 已把规则债可视化后，先设计规则收敛方式，而不是直接修改配置，避免为了清债破坏当前稳定性。

关键变更：
- 新增 `docs/rule_convergence_plan_v0.4.5.17.md`，定义共享 `scenario_id` 命名规范和 Anchor / Risk Supplement 职责边界。
- 选取 5 个高重叠场景作为第一批设计对象：`pipl_automated_decision_bias`、`trade_secret_customer_list_leak`、`pipl_cross_border_sensitive_medical`、`vat_false_invoice_deduction`、`pipl_children_consent`。
- 每个场景都列出当前涉及规则、收敛设计、迁移顺序和验证命令。
- 新增 `tools/check_rule_convergence_plan.py` 与 `tests.test_rule_convergence_plan`，检查设计稿结构、`scenario_id` 命名和发布门禁命令。
- 本版本不修改 `config/rag_anchor_rules.json`、`config/risk_payload_supplement_rules.json` 或 `src/rag/retriever.py`。

报告写法：
> v0.4.5.17 将规则债盘点结果转化为可执行的收敛设计。系统先定义共享 `scenario_id`、职责边界、迁移顺序和验证门禁，再考虑实际配置迁移，避免直接删除或合并规则破坏当前 RAG Eval 稳定性。该版本体现了从“质量修复”转向“规则治理工程化”的过渡：先设计、可检查、可回滚，再小步迁移。

验证方式：
- 设计稿检查：`tools/check_rule_convergence_plan.py --plan docs/rule_convergence_plan_v0.4.5.17.md`，通过。
- 相关单元测试：`tests.test_candidate_budget`、`tests.test_retriever_contract`、`tests.test_rag_eval_diagnostics`、`tests.test_rag_stability_tools`、`tests.test_rule_debt_audit`、`tests.test_rule_convergence_plan`，`54 tests OK`。

后续影响：
- 下一步可选择一个低风险场景做 metadata-only `scenario_id` 试点。
- 每个实际迁移版本都必须绑定 targeted eval、3 轮稳定性回归、稳定性门禁和规则债复扫。

### v0.4.5.18.1：Scenario ID Metadata 试点

阶段定位：在 v0.4.5.17 完成规则收敛设计稿后，选择一个高价值但可控的场景进行 metadata-only 试点，验证共享 `scenario_id` 能否跨 Anchor 与 Risk Supplement 建立场景身份，而不改变运行行为。

关键变更：
- 选择 `trade_secret_customer_list_leak` 作为第一批试点场景。
- Anchor 侧仅新增 `scenario_id` 到 `pipl_data_leak`、`pipl_internal_leak`、`unfair_competition_trade_secret`。
- Risk Supplement 侧仅新增 `scenario_id` 到 `risk_rule_0` 与 `risk_rule_4`。
- 不删除 trigger、不合并规则、不改变匹配逻辑、不改变候选召回、rerank 或输出补全行为。
- 新增 `tools/check_scenario_links.py` 与 `tests.test_scenario_links`，校验同一 `scenario_id` 同时存在于 Anchor 与 Risk Supplement 配置，并可要求具体规则 id 必须绑定。
- `validate_risk_payload_supplement_rules()` 仅把 `scenario_id` 作为 metadata 字段纳入白名单并校验非空字符串，不参与匹配或输出逻辑。

报告写法：
> v0.4.5.18.1 是规则收敛路线的第一个 metadata-only 试点。系统没有删除或合并任何规则，也没有改变检索或输出逻辑，只为“客户名单/商业秘密/内部导出”复合场景建立共享 `scenario_id=trade_secret_customer_list_leak`。复扫结果显示 Anchor 缺共享 `scenario_id` 从 `75` 降至 `72`，Risk 缺 `scenario_id` 从 `39` 降至 `37`，说明场景身份层开始落地，但质量基线仍由原有规则行为承担。

验证方式：
- 语法与相关单元测试：`60 tests OK`。
- Scenario link 检查：`tools/check_scenario_links.py --required-scenario trade_secret_customer_list_leak ...`，通过。
- Stability gate：`tools/check_rag_stability_report.py --report tests/rag_stability_report.json`，通过。
- Rule debt audit：生成 `docs/rule_debt_report_v0.4.5.18.1.md` 与 `tests/rule_debt_report.json`，通过。
- Full Eval：本版本按计划不运行。

后续影响：
- 下一步可选择同一场景补 targeted eval 验证，或选择第二个低风险场景继续 metadata-only 试点。
- 所有 `scenario_id` 迁移都应保持 metadata-only，直到稳定性门禁和规则债复扫证明其不会破坏现有质量基线。

### v0.4.6.0：Scenario Registry 雏形

阶段定位：在完成单个 `scenario_id` metadata-only 试点后，把分散在 Anchor Rules、Risk Supplement Rules 和评测集中的场景身份抽象成统一注册表，但暂不接入主流程。

关键变更：
- 新增 `config/scenario_registry.json`，首批登记 5 个场景：`trade_secret_customer_list_leak`、`pipl_children_consent`、`pipl_automated_decision_bias`、`pipl_cross_border_sensitive_medical`、`vat_false_invoice_deduction`。
- 每个场景登记法域、说明、风险等级、核心条文、风险类型、整改动作、法定术语、Anchor rule 链接、Risk Supplement rule 链接和 eval case 链接。
- 新增 `tools/check_scenario_registry.py`，校验场景唯一性、法域合法性、风险等级、核心字段非空、规则链接存在性和已有 `scenario_id` 的反向链接闭合。
- 新增 `tests.test_scenario_registry` 和 `docs/scenario_registry_v0.4.6.0.md`，将 registry 校验与 coverage audit 固化。
- 本版本不修改 `src/rag/retriever.py`，不改变检索、rerank、anchor 或 risk supplement 行为。

报告写法：
> v0.4.6.0 将规则治理从“单条规则添加 metadata”推进到“场景注册表”。系统开始用 `scenario_registry.json` 统一登记法律风险场景、核心法条、风险类型、整改动作、规则链接和评测样本，为后续规则收敛、覆盖审计和场景级质量门禁提供结构化基础。本版本仍保持只读治理属性，不接入 RAG 主流程，因此不会改变已有评测行为。

验证方式：
- 语法检查：`py_compile src/main.py tools/check_scenario_registry.py`，通过。
- Scenario registry checker：四类 coverage 缺口均为 `0`。
- 相关单元测试：`tests.test_scenario_registry`，`7 tests OK`。
- Full Eval：本版本按计划不运行。

后续影响：
- 下一步可继续补充更多 metadata-only 场景到 registry，但仍应先通过 checker 与 targeted eval 证明覆盖闭合。
- 当 registry 稳定后，再评估是否把其作为规则治理视图或发布门禁输入，而不是直接接入检索主链路。

### v0.4.6.1：Scenario Registry 只读加载层

阶段定位：在建立 `scenario_registry.json` 后，新增 Python 只读加载层，让工具和后续治理代码能够安全读取场景注册表，但不把 scenario 接入检索或输出主流程。

关键变更：
- 新增 `src/rag/scenario_registry.py`，提供 `load_scenario_registry()`、`get_scenario_by_id()`、`list_scenarios()`、Anchor/Risk rule 反查、核心条文和整改动作读取 helper。
- loader 启动时复用 `tools/check_scenario_registry.py` 的校验逻辑，校验失败时抛出 `ScenarioRegistryError`。
- 对外返回防御性深拷贝，避免调用方修改返回对象污染缓存。
- 新增 `tests.test_scenario_registry_loader`，覆盖当前 5 个 scenario 的加载、查询、过滤、反查和异常路径。
- 本版本不修改 `rag_query` 主链路，不改变 RAG Eval 行为。

报告写法：
> v0.4.6.1 将 Scenario Registry 从静态配置推进为可被工程代码安全读取的只读能力。系统可以通过 Python API 查询场景、法域、规则链接、核心条文和整改动作，但这些信息仍不参与检索、排序或输出生成。该版本为后续 targeted eval、覆盖审计和规则治理工具提供复用入口，同时保持主链路行为不变。

验证方式：
- 语法检查：`py_compile src/main.py src/rag/scenario_registry.py tools/check_scenario_registry.py`，通过。
- Loader 单元测试：`tests.test_scenario_registry_loader`，`9 tests OK`。
- Scenario registry checker：继续通过。
- Full Eval：本版本按计划不运行。

后续影响：
- 下一步可基于只读 loader 做 scenario 级 targeted eval 报告，但仍不应让 registry 直接驱动召回、anchor 或风险补全。
- 当 scenario 级评测报告稳定后，再评估是否将 registry 作为发布门禁输入。

### v0.4.6.2：Scenario Registry Targeted 验证

阶段定位：在 registry 和只读 loader 都建立后，验证 registry 绑定的 eval case 与当前 RAG 行为一致，避免出现“文档登记完整，但评测行为断链”的治理空转。

关键变更：
- 新增 `tools/run_scenario_eval.py`，读取 `config/scenario_registry.json`，按 `eval_case_ids` 分组运行现有 RAG Eval 等价逻辑。
- 输出 `tests/scenario_eval_report.json` 与 `tests/scenario_eval_summary.md`。
- 每个 scenario 汇总 `pass/total`、`retrieval_failure_stage_summary` 和 `contribution_summary`。
- 报告显式列出 `missing_case_ids`、`scenarios_without_eval_case_ids` 和 `scenarios_all_failed`。
- 本版本不修改 `rag_query` 主链路，不用 scenario 驱动检索或输出。

报告写法：
> v0.4.6.2 将 Scenario Registry 从“可读取”推进到“可验证”。系统按 registry 中 5 个场景绑定的 8 个评测样本执行 targeted eval，验证场景登记、评测样本和当前 RAG 行为之间没有断链。结果显示 5 个 scenario 均通过，retrieval failure stage 全部为 `PASS`，说明 registry 不是单纯文档化，而是已经能对应到可回归的行为样本。

验证方式：
- 语法检查：`py_compile src/main.py tools/run_scenario_eval.py tools/run_rag_eval.py`，通过。
- Scenario eval 单元测试：`tests.test_scenario_eval`，`8 tests OK`。
- Scenario targeted eval：5 个 scenario、8 个唯一 case 全部通过。
- Scenario registry checker：继续通过。
- Full Eval：本版本未运行 full eval，仅运行 registry 绑定 case 的 targeted eval。

后续影响：
- 下一步可把 `tools/run_scenario_eval.py` 作为发布前轻量门禁，先发现 registry 与行为样本的断链。
- 扩展新 scenario 时，应同时补 registry、eval case 和 scenario targeted report。

### v0.4.6.3：Scenario Eval 轻量门禁

阶段定位：在 scenario targeted eval 已能生成报告后，把报告转化为发布前机器门禁，避免 scenario registry 后续扩展时出现缺 case、空场景、全失败场景或报告结构漂移。

关键变更：
- 新增 `tools/check_scenario_eval_report.py`，检查 `tests/scenario_eval_report.json` 的关键质量信号。
- 门禁要求 `missing_case_ids`、`scenarios_without_eval_case_ids`、`scenarios_all_failed` 均为空。
- 门禁要求 scenario 数量和唯一 eval case 数量达到阈值，默认分别为 5 和 8。
- 门禁要求每个 scenario 具备 `passed`、`total`、`retrieval_failure_stage_summary`，且 `total > 0`、`passed > 0`。
- 新增 `tests.test_scenario_eval_gate`，覆盖正常报告、失败信号、阈值、关键字段和部分通过开关。

报告写法：
> v0.4.6.3 将 Scenario Registry 的治理链条收口为可门禁流程。系统不仅能登记 scenario、读取 scenario、按 scenario 跑 targeted eval，还能在发布前自动检查 targeted eval 报告是否存在断链。至此形成 `registry → loader → targeted eval → eval gate` 的闭环，为后续 hidden eval 和企业场景层建设提供了稳定的治理基础。

验证方式：
- 语法检查：`py_compile src/main.py tools/check_scenario_eval_report.py`，通过。
- Scenario eval gate 单元测试：`tests.test_scenario_eval_gate`，`12 tests OK`。
- Scenario eval gate：`tools/check_scenario_eval_report.py --report tests/scenario_eval_report.json`，通过。
- Scenario registry、scenario links、RAG stability gate 均继续通过。
- Full Eval：本版本未运行 full eval。

后续影响：
- v0.4.6.x 的 scenario 基建可以暂时收口。
- 下一阶段可进入 hidden eval / 企业场景层，把真实业务样本作为不直接参与规则调参的质量验证集。

### v0.4.6.4：Scenario Registry 第二批精选补全

阶段定位：在 scenario 治理链条已经闭环后，谨慎扩充第二批高价值企业法律风控场景，验证 registry 能承载更多真实业务风险单元，而不是停留在首批样本。

关键变更：
- 新增 5 个 scenario：人脸识别考勤、数据出境安全评估、第三方共享未同意、合同格式条款、横向固定价格。
- 仅补充 registry 条目和已有规则的 `scenario_id` metadata，不修改检索、rerank、anchor、risk supplement 或术语保真逻辑。
- Scenario targeted eval 扩展到 10 个 scenario、15 个唯一 eval case，结果全部通过。
- Scenario eval gate 默认阈值提升为 `min_scenarios=10`、`min_cases=15`。
- `pipl_facial_recognition_attendance` 暂无 Risk Supplement 规则，保留 coverage audit 缺口，作为后续规则治理候选。
- `check_scenario_links` 增加显式 allowlist 参数，允许已知 anchor-only 场景通过，同时保持其它缺边场景可被拦截。

报告写法：
> v0.4.6.4 将 Scenario Registry 从首批 5 个样本扩展到 10 个企业高价值风控场景，覆盖数据合规、民商事和市场秩序。系统仍然不让 scenario 参与检索或输出生成，而是把 scenario 作为可验证的法律风险知识单元：每个场景绑定核心条文、规则链接和 eval case，并通过 targeted eval 与 gate 进行回归。该版本还保留了人脸考勤场景缺 Risk Supplement link 的审计缺口，体现了“不为覆盖率临时造规则”的治理原则。

验证方式：
- Scenario targeted eval：10 个 scenario、15 个唯一 case 全部通过。
- Scenario eval gate：通过。
- Scenario registry checker：通过，并暴露 1 个 Risk Supplement coverage 缺口。
- Scenario links、RAG stability gate：继续通过。
- Full Eval：本版本未运行 full eval。

后续影响：
- v0.4.6.x 已具备 registry、loader、targeted eval、eval gate 和精选扩容能力。
- 下一阶段更适合进入 hidden eval / 企业场景层，而不是继续堆 scenario metadata。


### v0.4.7.0：Hidden Eval / Issue Hierarchy 设计稿

阶段定位：从公开 RAG Eval 的稳定性修复，转入 hidden eval / 企业复杂场景层的法律依据控制设计。

关键变更：
- 新增 `docs/legal_issue_hierarchy_plan_v0.4.7.0.md`，基于 7 条真实 hidden seed 总结 evidence_chain 与法律推理脱节的问题。
- 将问题拆解为 Legal Domain Routing、Issue Hierarchy、Legal Functional Typing、Evidence Coverage Scoring 和 Confidence Split。
- 明确 syntactic grounding 不等于 legal grounding：引用来自 evidence_chain 只能说明形式可追溯，不能说明证据本身适用。
- 本版本只做设计，不修改 `rag_query` 主链路，不改变检索、rerank、anchor 或 risk supplement 行为。

报告写法：
> v0.4.7.0 标志着项目从“公开评测集过关”进入“复杂企业场景法律依据控制”阶段。系统在 hidden seed 中已经表现出较强的法律推理能力，但 evidence_chain 仍可能出现法域污染、定义条文替代规范条文、主争点缺证据和置信度过高等问题。本版本不急于调整 rerank 或补 anchor，而是先把这些问题抽象为离线诊断框架，为后续 evidence alignment checker 奠定标准。

验证方式：
- 文档审查：`docs/legal_issue_hierarchy_plan_v0.4.7.0.md` 完成。
- `py_compile src/main.py` 通过。
- Full Eval：本版本不运行。

### v0.4.7.0b：Hidden Seed 结构化清单

阶段定位：把 7 条 hidden seed 从人工观察样本固化为可机器校验的离线标注输入。

关键变更：
- 新增 `config/hidden_eval_seed_cases.json`，记录 7 条 hidden seed 的 expected domains、primary/secondary/peripheral issues、expected statutes、contaminating domains 和 known bad evidence。
- 新增 `tools/check_hidden_eval_seeds.py`，校验 case id 唯一、7 条 seed 齐备、法域合法、主争点和期望法条非空、法条功能类型合法、污染法域不与期望法域重叠。
- 新增 `tests.test_hidden_eval_seed_cases`，覆盖结构校验和仓库真实清单。
- FastAPI 服务版本同步为 `0.4.7.0b`。
- 本版本不接入主流程，不运行 full eval。

报告写法：
> v0.4.7.0b 将 hidden eval 的主观观察转化为可复用的结构化标注。每条复杂企业场景不再只是“某次回答效果不好”的记录，而是明确标出应进入的法域、主争点、次争点、期望法条、污染法域和已知坏证据。这样后续工具可以自动判断一次 RAG 输出到底是检索没覆盖、rerank 排错、法域污染，还是答案生成脱离证据。

验证方式：
- `py_compile tools/check_hidden_eval_seeds.py src/main.py` 通过。
- `tools/check_hidden_eval_seeds.py --seeds config/hidden_eval_seed_cases.json` 通过，7 条 seed 齐备。
- `tests.test_hidden_eval_seed_cases` 通过，11 tests OK。
- Full Eval：本版本不运行。

后续影响：
- v0.4.7.1 已承接该结构化清单，进一步形成离线 Evidence Alignment Checker。
- 后续仍不应直接改 rerank 或新增 anchor 来定向修 hidden seed，应先把 grounding 质量问题转化为可复用的诊断信号和功能类型 metadata。

### v0.4.7.1：Evidence Alignment Checker 离线诊断层

阶段定位：在不修改 RAG 主流程、不修 hidden seed 的前提下，为现有 RAG 报告增加 evidence alignment 离线诊断层，判断答案、证据链和 scenario metadata 是否在法律依据层面对齐。

关键变更：
- 新增 `tools/check_evidence_alignment.py`，读取 `tests/rag_eval_report.json`、可选 `tests/hidden_eval_report.json` 与可选 `config/scenario_registry.json`，生成 `tests/evidence_alignment_report.json`。
- 新增通用诊断信号：法域污染、主争点缺证据、定义条款替代规范条款、答案-证据脱节、证据覆盖不足，以及需要人工复核时的 `review_reasons`。
- 新增 `tests.test_evidence_alignment`，只验证通用诊断逻辑，不要求某个 hidden seed 必须通过。
- 新增 `docs/evidence_alignment_checker_v0.4.7.1.md`，明确该工具是 RAG grounding quality diagnostics，不是样本修补工具。
- FastAPI 服务版本同步为 `0.4.7.1`。
- 本版本不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.1 将 hidden eval 暴露出的“推理结果强但证据链不一定法律适配”的问题，推进为可复用的离线 grounding 质量诊断。系统不再把问题简单归因于某个样本没过，也不通过补 anchor、改 rerank 或改 prompt 临时修复，而是基于已有报告、evidence_chain 和 scenario metadata 输出法域污染、主争点缺证据、definition-only、答案-证据脱节和覆盖不足等信号。该版本的价值在于建立人工复核清单和 issue/domain summary，为后续 Legal Functional Typing、Evidence Coverage 和 Confidence Split 提供可审计输入。

验证方式：
- `py_compile tools/check_evidence_alignment.py src/main.py` 通过。
- `tests.test_evidence_alignment` 通过。
- `tools/check_evidence_alignment.py --rag-report tests/rag_eval_report.json --hidden-report tests/hidden_eval_report.json --scenario-registry config/scenario_registry.json --output tests/evidence_alignment_report.json` 可在现有报告上运行；若 hidden report 不存在则记录为 skipped input。
- Full Eval：本版本不运行，仅读取已有报告。

后续影响：
- v0.4.7.2 可基于 checker 的 review list 做 Legal Functional Typing 试点，把定义、义务、责任、程序、后果等法条功能从启发式诊断逐步沉淀为可维护 metadata。
- Evidence Alignment Checker 应作为诊断和复核入口，而不是替代 RAG Eval 的 pass/fail 门禁；如需强制门禁，应另行定义阈值并先验证误报成本。

### v0.4.7.2：Legal Functional Typing 离线诊断层

阶段定位：把法条功能类型从 evidence alignment checker 内的临时启发式，推进为可维护 taxonomy、通用分类 API 和知识库 coverage audit，为后续大量法律入库提供 grounding metadata 路线。

关键变更：
- 新增 `config/legal_functional_types.json`，定义 `definition`、`principle`、`operative_rule`、`procedural`、`liability`、`rights_remedy`、`scope`、`technical_standard`、`unrelated_or_contextual` 和 `unclassified` 等功能类型。
- 新增 `src/rag/legal_functional_typing.py`，提供只读确定性分类 API：优先读取 evidence/chunk metadata，其次按通用文本线索分类，最后回退到 `unclassified`。
- 新增 `tools/audit_legal_functional_typing.py`，复用现有 ingestion loader 扫描 `knowledge_manifest.json`，输出全局和逐文档的 functional type coverage。
- 新增 `tests.test_legal_functional_typing` 和 `docs/legal_functional_typing_v0.4.7.2.md`。
- `tools/check_evidence_alignment.py` 改为复用 functional typing API，不再在 checker 内维护具体法条号到功能类型的映射。
- FastAPI 服务版本同步为 `0.4.7.2`。
- 本版本不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.2 没有继续围绕 hidden seed 做定向补丁，而是把 evidence alignment 中最关键的“法条功能是否足以支撑结论”抽象成可维护的离线 metadata 层。系统新增统一 taxonomy 和分类 API，使 definition-only、operative support coverage 等诊断不再依赖某部法第几条的硬编码。对现有 15 部知识库文档的 audit 显示，7177 个 chunk 中未分类比例为 `0.288`，operative support 比例为 `0.637`，其中增值税法因未分类比例 `0.5` 进入人工复核清单。这说明 functional typing 已能成为后续大量法律入库时的质量治理入口，而不是临时修样本工具。

验证方式：
- `py_compile src/rag/legal_functional_typing.py tools/audit_legal_functional_typing.py tools/check_evidence_alignment.py src/main.py` 通过。
- `tests.test_legal_functional_typing` 与 `tests.test_evidence_alignment` 通过。
- `tools/audit_legal_functional_typing.py --manifest knowledge_manifest.json --config config/legal_functional_types.json --output tests/legal_functional_typing_report.json` 通过。
- Full Eval：本版本不运行，仅读取本地知识库文本和 manifest 做离线 audit。

后续影响：
- 下一步可进入 v0.4.7.3，基于 audit review list 补充财税、公司治理、知识产权等领域的通用功能类型线索。
- 在 functional typing 稳定前，不应把功能类型直接接入召回、rerank 或 prompt；应继续作为 grounding quality diagnostics 和人工复核清单使用。

### v0.4.7.2.1：Legal Functional Typing Config Gate

阶段定位：进入 Legal Functional Typing 质量修复线，先保护 taxonomy 和规则配置本身的可维护性，防止后续大量法律入库时配置漂移、regex 损坏或 operative support 引用失真。

关键变更：
- 新增 `tools/check_legal_functional_type_config.py`，校验 `config/legal_functional_types.json` 的结构、功能类型唯一性、必备类型、operative support 引用、规则字段、priority、confidence 和 regex 可编译性。
- 新增 `tests.test_legal_functional_type_config`，覆盖正常配置、未知规则类型、重复 functional type id、非法 regex、未知 operative support type 和仓库真实配置。
- 新增 `tests/legal_functional_type_config_report.json`，保存配置门禁结果。
- 新增 `docs/legal_functional_type_config_gate_v0.4.7.2.1.md`，明确本版本是 functional typing 基建质量修复，不是主流程改动。
- FastAPI 服务版本同步为 `0.4.7.2.1`。
- 本版本不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.2.1 没有继续扩展 functional typing 规则，而是先为 `legal_functional_types.json` 建立配置门禁。该门禁要求功能类型 taxonomy、operative support 类型、规则 priority、confidence 和 regex 处于可机器校验状态，防止后续质量修复线变成不可维护的规则堆积。当前配置门禁通过，0 errors、0 warnings，包含 10 个 functional types、7 条 rules、73 个 contains cues 和 19 个 regex cues。该版本体现的原则是：functional typing 是 Harvey 式 evidence grounding 的基础设施，必须先保证配置质量，再做领域规则增强或入库 metadata 写回。

验证方式：
- `py_compile tools/check_legal_functional_type_config.py src/main.py` 通过。
- `tests.test_legal_functional_type_config` 通过。
- `tools/check_legal_functional_type_config.py --config config/legal_functional_types.json --report-output tests/legal_functional_type_config_report.json` 通过。
- Full Eval：本版本不运行，仅检查 functional typing 配置质量。

后续影响：
- 下一步建议 v0.4.7.2.2 建立 golden fixtures，而不是直接扩财税规则或写回 ingestion metadata。
- 后续每次修改 `config/legal_functional_types.json`，都应先跑 config gate，再跑 functional typing audit 和 evidence alignment checker。

### v0.4.7.2.2：Legal Functional Typing Golden Fixtures

阶段定位：继续 Legal Functional Typing 质量修复线，在配置结构门禁之后，建立分类行为门禁，防止后续规则修改破坏核心功能类型边界。

关键变更：
- 新增 `tests/fixtures/legal_functional_typing_golden.json`，包含 16 条可读、可维护的功能类型基准片段，覆盖 definition、principle、operative_rule、procedural、liability、rights_remedy、scope、technical_standard、unclassified、metadata priority 和边界样本。
- 新增 `tools/check_legal_functional_typing_fixtures.py`，逐条调用 `src/rag/legal_functional_typing.py` 并比对 expected/actual type，输出 matched rule、matched terms 和失败分布。
- 新增 `tests.test_legal_functional_typing_fixtures`，覆盖仓库真实 fixtures、未知 expected type、重复 case id 和失败明细汇总。
- 新增 `tests/legal_functional_typing_fixture_report.json` 与 `docs/legal_functional_typing_golden_fixtures_v0.4.7.2.2.md`。
- 调整 `config/legal_functional_types.json` 的 principle 规则：新增高优先级原则组合短语规则，同时保留宽泛原则词为低优先级，修复原则条款被误判为普通义务条款的问题。
- FastAPI 服务版本同步为 `0.4.7.2.2`。
- 本版本不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.2.2 将 functional typing 质量修复从“配置能否被机器校验”推进到“分类行为是否稳定”。Golden fixtures 首轮即暴露了原则条款和普通义务条款之间的边界问题：含有“应当/不得”的原则条款会被错误归入 `operative_rule`。本版本没有通过样本补丁绕过问题，而是新增高优先级原则组合短语规则，并把宽泛原则词保留在低优先级，从而避免普通义务条款中的“必要”“公开”等词被误判为原则。修复后 16 条 fixtures 全部通过，config gate 继续 0 errors/0 warnings，functional typing audit 保持 `unclassified_ratio=0.288`，`operative_support_ratio=0.633`。operative support 比例略降是预期质量修复结果，因为部分原则条款不再被误计为义务支撑。

验证方式：
- `py_compile tools/check_legal_functional_typing_fixtures.py tools/check_legal_functional_type_config.py src/rag/legal_functional_typing.py src/main.py` 通过。
- `tests.test_legal_functional_typing_fixtures`、`tests.test_legal_functional_type_config`、`tests.test_legal_functional_typing`、`tests.test_evidence_alignment` 通过。
- `tools/check_legal_functional_type_config.py --config config/legal_functional_types.json --report-output tests/legal_functional_type_config_report.json` 通过。
- `tools/check_legal_functional_typing_fixtures.py --fixtures tests/fixtures/legal_functional_typing_golden.json --config config/legal_functional_types.json --report-output tests/legal_functional_typing_fixture_report.json` 通过。
- `tools/audit_legal_functional_typing.py --manifest knowledge_manifest.json --config config/legal_functional_types.json --output tests/legal_functional_typing_report.json` 通过。
- Full Eval：本版本不运行，仅检查 functional typing 配置、fixture 和离线 audit。

后续影响：
- 下一步建议 v0.4.7.2.3 生成误报/漏报分析报告，把 fixture gate、functional typing audit 和 evidence alignment report 的信号合并为可行动的质量归因。
- 在 error analysis 稳定前，仍不建议把 functional type 写回 ingestion metadata 或接入主流程。

### v0.4.7.2.3：Legal Functional Typing Error Analysis Report

阶段定位：继续 Legal Functional Typing 质量修复线，把 fixture gate、functional typing audit 和 evidence alignment report 汇总成误报/漏报分析，输出下一步质量修复优先级。

关键变更：
- 新增 `tools/analyze_legal_functional_typing_errors.py`，读取 `tests/legal_functional_typing_fixture_report.json`、`tests/legal_functional_typing_report.json` 和 `tests/evidence_alignment_report.json`。
- 新增 `tests.test_legal_functional_typing_error_analysis`，覆盖 fixture failure P0、高未分类 P1、alignment issue 汇总和文件报告生成。
- 新增 `tests/legal_functional_typing_error_analysis_report.json` 与 `docs/legal_functional_typing_error_analysis_v0.4.7.2.3.md`。
- 输出 prioritized action list：P0 fixture failure、P1 high-unclassified documents、P1 definition-only、P2 low operative support、P2 missing-primary evidence、P3 answer-evidence disconnect。
- FastAPI 服务版本同步为 `0.4.7.2.3`。
- 本版本不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.2.3 将 Legal Functional Typing 的质量修复从单点 gate 推进到综合误报/漏报归因。当前 fixture gate 无失败，因此不存在 P0；functional typing audit 显示 `中华人民共和国增值税法` 未分类比例 `0.5`，成为 P1；evidence alignment 显示 12 条 missing-primary cases 和 48 条 answer-evidence disconnect cases，分别作为 P2/P3 进入后续分析。该版本的重点不是直接新增规则，而是把“下一步应该修哪里”变成可审计清单，避免在没有归因的情况下扩规则、改 rerank 或修 hidden seed。

验证方式：
- `py_compile tools/analyze_legal_functional_typing_errors.py tools/check_legal_functional_typing_fixtures.py tools/check_legal_functional_type_config.py tools/audit_legal_functional_typing.py tools/check_evidence_alignment.py src/rag/legal_functional_typing.py src/main.py` 通过。
- `tests.test_legal_functional_typing_error_analysis`、`tests.test_legal_functional_typing_fixtures`、`tests.test_legal_functional_type_config`、`tests.test_legal_functional_typing`、`tests.test_evidence_alignment` 通过。
- Config gate、fixture gate、functional typing audit、evidence alignment checker、error analysis 均通过。
- Full Eval：本版本不运行，仅读取已有离线报告。

后续影响：
- 下一步建议 v0.4.7.2.4 优先处理税法/财税语言线索，但规则应保持领域中性法律语言，不做 case-specific patch。
- Answer-evidence disconnect 不应在本阶段直接通过 prompt 或 risk supplement 修复，应先单独归因。

### v0.4.7.2.4：Tax / Domain-Neutral Cue Quality Fix

阶段定位：继续 Legal Functional Typing 质量修复线，承接 v0.4.7.2.3 的 P1 high-unclassified 行动项，优先降低增值税法未分类比例，同时保护标题、目录、章节等结构性材料不被误计为有效证据支撑。

关键变更：
- `src/rag/legal_functional_typing.py` 新增结构性正文短文本识别，将法律标题、通过日期、目录和章节标题归入 `unrelated_or_contextual`。
- `config/legal_functional_types.json` 补充财税/税务通用功能线索，覆盖税率、征收率、应纳税额、计税方法、销项税额、进项税额、抵扣、免征、税收优惠、申报纳税、办理登记、纳税地点、纳税义务发生时间等。
- `tests/fixtures/legal_functional_typing_golden.json` 从 16 条扩展到 25 条，新增税率、抵扣、免征、税务程序、责任优先级和结构性文本边界样例。
- `tools/audit_legal_functional_typing.py`、`tools/check_legal_functional_typing_fixtures.py`、`tools/check_legal_functional_type_config.py` 和 `tools/analyze_legal_functional_typing_errors.py` 的报告版本跟随 functional typing 配置版本。
- 新增 `docs/legal_functional_typing_tax_cue_quality_v0.4.7.2.4.md`。
- FastAPI 服务版本同步为 `0.4.7.2.4`。
- 本版本不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.2.4 没有通过 hidden seed 或具体 case 补丁来改善报告数字，而是沿 Legal Functional Typing 基建路线补充财税/税务通用法律语言线索，并把标题、目录、章节等结构性材料明确归入 `unrelated_or_contextual`。修复后 `中华人民共和国增值税法` 的 `unclassified_ratio` 从 `0.5` 降至 `0.167`，`operative_support_ratio` 从 `0.353` 升至 `0.628`；全局 audit 变为 15 documents、7177 chunks、0 review documents、`unclassified_ratio=0.25`、`operative_support_ratio=0.635`。Fixture gate 扩展到 25 条且全部通过，error analysis 中 high-unclassified documents 清零。剩余 12 条 missing-primary evidence 和 48 条 answer-evidence disconnect 仍保留为后续 P2/P3，不在本版本通过 prompt、rerank 或风险补全规则提前修复。

验证方式：
- `py_compile tools/analyze_legal_functional_typing_errors.py tools/check_legal_functional_typing_fixtures.py tools/check_legal_functional_type_config.py tools/audit_legal_functional_typing.py tools/check_evidence_alignment.py src/rag/legal_functional_typing.py src/main.py` 通过。
- `tests.test_legal_functional_typing_error_analysis`、`tests.test_legal_functional_typing_fixtures`、`tests.test_legal_functional_type_config`、`tests.test_legal_functional_typing`、`tests.test_evidence_alignment` 通过。
- Config gate：0 errors、0 warnings、10 functional types、8 rules、102 contains cues、20 regex cues。
- Fixture gate：25/25 passed。
- Functional typing audit：15 documents、7177 chunks、0 review documents。
- Evidence alignment checker：60 cases、10 pass、50 review；`tests/hidden_eval_report.json` 不存在时按 optional input 跳过。
- Error analysis：0 fixture failures、0 high-unclassified documents、2 prioritized actions。
- Full Eval：本版本不运行。

后续影响：
- 下一步建议 v0.4.7.3 转向 Evidence Coverage Diagnostics，优先拆解 missing-primary evidence 和 answer-evidence disconnect。
- 不建议在没有 coverage 归因前继续扩 functional typing 规则，更不应把 functional type 直接接入召回、rerank、prompt 或风险输出。

### v0.4.7.3：Evidence Coverage Diagnostics

阶段定位：在不改动 RAG 主链路的前提下，把 missing-primary evidence 和 answer-evidence disconnect 拆解为可审计的 evidence coverage 质量信号。

关键变更：
- 新增 `tools/check_evidence_coverage.py`，只读取 `tests/rag_eval_report.json`、可选 `tests/hidden_eval_report.json` 和 `config/scenario_registry.json`。
- 新增 `tests/test_evidence_coverage.py`，覆盖 final evidence gap、scenario core gap、functional type gap、optional hidden report skip 和报告构建。
- 新增 `tests/evidence_coverage_report.json`，输出 case 级 coverage status、detected issues、review reasons、layer coverage、functional type coverage、issue summary、per-domain summary 和 high-priority manual review list。
- 新增 `docs/evidence_coverage_diagnostics_v0.4.7.3.md`。
- FastAPI 服务版本同步为 `0.4.7.3`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.3 将 Evidence Alignment Checker 暴露的 missing-primary evidence 与 answer-evidence disconnect 进一步拆到 evidence coverage 层。工具在离线状态下比较 dense、sparse、union、anchor、rerank_input 和 final 六层的 expected evidence 覆盖情况，输出 `final_primary_gap`、`scenario_core_gap`、`anchor_dependent_coverage`、`layer_coverage_regression` 和 `low_final_coverage` 等通用质量信号。当前报告显示 60 个 case 中 24 个 ok、36 个需要 review；final 覆盖为 `95/104=0.913`，anchor 与 rerank_input 覆盖为 `103/104=0.99`，说明当前主要矛盾不是盲目扩大规则或修改 prompt，而是进一步归因 anchor 依赖和 final evidence 选择中的覆盖流失。

验证方式：
- `py_compile tools/check_evidence_coverage.py tools/analyze_legal_functional_typing_errors.py tools/check_legal_functional_typing_fixtures.py tools/check_legal_functional_type_config.py tools/audit_legal_functional_typing.py tools/check_evidence_alignment.py src/rag/legal_functional_typing.py src/main.py` 通过。
- `tests.test_evidence_coverage`、`tests.test_legal_functional_typing_error_analysis`、`tests.test_legal_functional_typing_fixtures`、`tests.test_legal_functional_type_config`、`tests.test_legal_functional_typing`、`tests.test_evidence_alignment` 通过。
- Evidence coverage checker：60 cases、24 ok、36 review；`tests/hidden_eval_report.json` 不存在时按 optional input 跳过。
- Issue summary：`anchor_dependent_coverage=33`、`final_primary_gap=8`、`scenario_core_gap=8`、`layer_coverage_regression=7`、`low_final_coverage=3`。
- Layer summary：dense `0.135`、sparse `0.365`、union `0.375`、anchor `0.99`、rerank_input `0.99`、final `0.913`。
- Full Eval：本版本不运行。

后续影响：
- 下一步建议进入 v0.4.7.3.x 质量修复线，先做 Coverage Loss Triage，优先分析 final primary gap、scenario core gap、anchor dependency 和 rerank_input 到 final 的覆盖流失。
- 如果后续要把 functional type 纳入 evidence coverage，应先补齐 evidence text 或 functional type metadata 的离线可评价性，而不是直接把分类器接入召回、rerank 或 prompt。

### v0.4.7.3.1：Coverage Loss Triage Report

阶段定位：在 v0.4.7.3 的 evidence coverage diagnostics 之上，继续保持离线只读边界，把 review cases 拆成可行动的 coverage loss root causes。

关键变更：
- 新增 `tools/triage_evidence_coverage_loss.py`，只读取 `tests/evidence_coverage_report.json`。
- 新增 `tests/test_evidence_coverage_triage.py`，覆盖基础召回缺口、anchor 依赖、final selection loss、scenario core gap、metadata 不可评价边界和报告构建。
- 新增 `tests/evidence_coverage_triage_report.json`，输出 case 级 root causes、priority score、recommended actions、coverage flow 和 high-priority manual review list。
- 新增 `docs/evidence_coverage_triage_v0.4.7.3.1.md`。
- FastAPI 服务版本同步为 `0.4.7.3.1`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.3.1 没有直接修复任何 case，而是将 v0.4.7.3 的 36 个 review cases 进一步归因。报告显示 60 个 case 中 24 个 ok、24 个普通 review、12 个 high-priority review；主要 root causes 是 `base_retrieval_gap=34`、`anchor_dependency=33`、`final_primary_gap=8`、`scenario_core_gap=8`、`final_selection_loss=7`。这说明当前 RAG grounding 质量问题主要集中在基础召回覆盖不足、对 anchor 的依赖、以及少量从 rerank_input 到 final 的证据选择流失。`functional_metadata_not_evaluable=60` 被单独记录为报告字段限制，仅该项存在时不触发 review，避免把 evidence text/metadata 缺口误当成法律证据缺口。

验证方式：
- `py_compile tools/triage_evidence_coverage_loss.py tools/check_evidence_coverage.py src/main.py` 通过。
- `tests.test_evidence_coverage_triage`、`tests.test_evidence_coverage` 通过。
- Evidence coverage checker：60 cases、24 ok、36 review。
- Coverage loss triage：60 cases、24 ok、24 review、12 high-priority review。
- Full Eval：本版本不运行。

后续影响：
- 下一步建议 v0.4.7.3.2 做 Evidence Report Enrichment，优先补齐离线 evidence text preview 或 functional type metadata，让功能类型覆盖变为可评价信号。
- 仍不建议在没有人工归因样本前改 rerank、prompt、anchor 或 risk supplement。

### v0.4.7.3.2：Evidence Report Enrichment

阶段定位：在不改变 RAG 主链路的前提下，补强离线 evidence coverage report 的可评价性，让 final evidence 能带上正文预览和法律功能类型。

关键变更：
- `tools/check_evidence_coverage.py` 新增 enrichment index，读取 `knowledge_manifest.json` 与 `config/legal_functional_types.json`，复用 ingestion loader 从本地知识文件匹配 `source + article_no/section_no`。
- coverage report 中的 final evidence、layer missing/matched evidence 和 scenario core evidence 可补充 `content_preview`、`functional_type`、`functional_type_confidence`、`functional_type_matched_rule` 和 `enrichment_status`。
- CLI 新增 `--knowledge-manifest`、`--functional-type-config` 与 `--no-enrichment`。
- `tests/test_evidence_coverage.py` 增加 manifest enrichment 单测。
- `tools/triage_evidence_coverage_loss.py` 报告版本同步为 `0.4.7.3.2`。
- FastAPI 服务版本同步为 `0.4.7.3.2`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.3.2 解决了 evidence coverage diagnostics 的一个关键盲点：此前 RAG eval report 中的 evidence 只有 `source/article_no/citation` 等引用字段，导致 functional coverage 全部 `evaluable=false`。本版本通过只读 manifest 和本地知识文件构建 enrichment index，为 180 条 final evidence 中的 179 条补齐正文预览和 functional type，命中率 `0.994`；60/60 cases 均变为 functional coverage 可评价。与此同时，coverage issue 数字保持不变，说明本版本只是提升诊断可解释性，没有通过修改主链路或样本让 case “变好看”。

验证方式：
- `py_compile tools/check_evidence_coverage.py tools/triage_evidence_coverage_loss.py src/main.py` 通过。
- `tests.test_evidence_coverage`、`tests.test_evidence_coverage_triage` 通过。
- Evidence coverage checker：60 cases、24 ok、36 review；enrichment `179/180=0.994`。
- Coverage loss triage：60 cases、24 ok、24 review、12 high-priority review；`functional_metadata_not_evaluable` 已消除。
- Full Eval：本版本不运行。

后续影响：
- 下一步建议 v0.4.7.3.3 做 Manual Review Dataset，把 high-priority review cases 转成可维护的人工复核样本。
- 仍不建议直接改 rerank、prompt、anchor 或 risk supplement；先让人工复核样本沉淀出稳定的治理依据。

### v0.4.7.3.3：Evidence Manual Review Dataset

阶段定位：将 evidence coverage triage 的 high-priority review list 转换为可维护、可人工复核的数据集，为后续 root cause 确认和 fixtures 沉淀做准备。

关键变更：
- 新增 `tools/build_evidence_manual_review_dataset.py`，读取 `tests/evidence_coverage_report.json` 与 `tests/evidence_coverage_triage_report.json`。
- 新增 `tests/test_evidence_manual_review_dataset.py`，覆盖 review questions、review item 结构、high-priority only 筛选和 reviewer fields。
- 新增 `tests/evidence_manual_review_dataset.json`。
- 新增 `docs/evidence_manual_review_dataset_v0.4.7.3.3.md`。
- FastAPI 服务版本同步为 `0.4.7.3.3`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.3.3 没有继续扩大诊断规则，而是把 v0.4.7.3.2 中 12 条 high-priority review cases 固化为人工复核数据集。每条样本保留 root causes、priority score、coverage flow、missing final expected、missing scenario core、final evidence、functional type coverage 和 reviewer fields。这样后续可以由人工确认 root cause 是否真实成立，再决定是否进入 fixtures、scenario registry calibration 或 evidence control layer，而不是直接根据自动诊断修改 rerank、prompt 或 anchor。

验证方式：
- `py_compile tools/build_evidence_manual_review_dataset.py tools/check_evidence_coverage.py tools/triage_evidence_coverage_loss.py src/main.py` 通过。
- `tests.test_evidence_manual_review_dataset`、`tests.test_evidence_coverage`、`tests.test_evidence_coverage_triage` 通过。
- Manual review dataset：12 pending review items。
- Root cause summary：`base_retrieval_gap=10`、`anchor_dependency=9`、`final_primary_gap=8`、`scenario_core_gap=8`、`final_selection_loss=7`、`low_final_coverage=3`。
- Full Eval：本版本不运行。

后续影响：
- 下一步建议 v0.4.7.3.4 做 Coverage Gate Draft，只设计 gate 和趋势指标，不默认 fail。
- 人工复核数据集后续可用于确认 scenario core 是否过宽、final evidence selection 是否流失，以及哪些样本适合沉淀为 fixtures。

### v0.4.7.3.4：Coverage Gate Draft

阶段定位：在 evidence coverage diagnostics、triage 和 manual review dataset 之上，设计非强制 evidence coverage quality gate 草案，用于观察未来版本是否出现回退。

关键变更：
- 新增 `tools/draft_evidence_coverage_gates.py`。
- 新增 `tests/test_evidence_coverage_gate_draft.py`。
- 新增 `tests/evidence_coverage_gate_draft_report.json`。
- 新增 `docs/evidence_coverage_gate_draft_v0.4.7.3.4.md`。
- FastAPI 服务版本同步为 `0.4.7.3.4`。
- 默认 non-enforcing，仅在显式传入 `--fail-on-blocking` 时才会因为 blocking draft failures 返回非零。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.3.4 将 evidence coverage 质量信号整理为 gate 草案，但没有把它们直接变成强制发布门禁。当前 7 条 draft gates 全部通过，覆盖 high-priority review ceiling、review ratio ceiling、final coverage floor、enrichment ratio floor、final selection loss ceiling、scenario core gap ceiling 和 pending manual review workload ceiling。该版本的价值在于建立趋势观察标准：未来版本如果 high-priority review、final selection loss 或 scenario core gap 恶化，系统能先以 draft gate 形式暴露，而不是悄悄把问题带入主链路。

验证方式：
- `py_compile tools/draft_evidence_coverage_gates.py tools/build_evidence_manual_review_dataset.py tools/check_evidence_coverage.py tools/triage_evidence_coverage_loss.py src/main.py` 通过。
- `tests.test_evidence_coverage_gate_draft`、`tests.test_evidence_manual_review_dataset`、`tests.test_evidence_coverage`、`tests.test_evidence_coverage_triage` 通过。
- Coverage gate draft：7/7 gates passed，0 blocking draft failures。
- Full Eval：本版本不运行。

后续影响：
- 下一步建议 v0.4.7.3.5 做 Root Cause Action Plan，把诊断结果分流到 v0.4.7.4.x 的具体审计路线。
- Gate 草案暂不应强制启用，至少等人工复核样本确认后再考虑 release gate。

### v0.4.7.3.5：Evidence Root Cause Action Plan

阶段定位：收束 v0.4.7.3.x Evidence Coverage Quality Series，把诊断、triage、manual review dataset 和 gate draft 转换为 v0.4.7.4.x 的行动路线。

关键变更：
- 新增 `tools/build_evidence_root_cause_action_plan.py`。
- 新增 `tests/test_evidence_root_cause_action_plan.py`。
- 新增 `tests/evidence_root_cause_action_plan.json`。
- 新增 `docs/evidence_root_cause_action_plan_v0.4.7.3.5.md`。
- FastAPI 服务版本同步为 `0.4.7.3.5`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.3.5 将 evidence coverage 质量线从“诊断与样本沉淀”推进到“行动路线规划”。该版本生成 6 条 planned actions，其中 P0 1 条、P1 2 条、P2 3 条，分别映射到 v0.4.7.4.x 的 scenario registry calibration、base retrieval quality audit、anchor dependency audit、final evidence selection audit 和 manual review loop。它仍然不修复任何 case，也不修改主链路，而是保证后续每个修复方向都有明确输入、边界和优先级。

验证方式：
- `py_compile tools/build_evidence_root_cause_action_plan.py tools/draft_evidence_coverage_gates.py tools/build_evidence_manual_review_dataset.py tools/check_evidence_coverage.py tools/triage_evidence_coverage_loss.py src/main.py` 通过。
- `tests.test_evidence_root_cause_action_plan`、`tests.test_evidence_coverage_gate_draft`、`tests.test_evidence_manual_review_dataset`、`tests.test_evidence_coverage`、`tests.test_evidence_coverage_triage` 通过。
- Evidence root cause action plan：6 planned actions。
- Gate draft：7/7 passed。
- Full Eval：本版本不运行。

后续影响：
- 下一步进入 v0.4.7.4.x Evidence Quality Action Series。
- v0.4.7.4.x 应继续保持“先 audit，后修复”的原则，不直接修改 rerank、prompt、anchor 或 risk supplement。

### v0.4.7.4.0：Evidence Quality Action Series Baseline

阶段定位：进入 v0.4.7.4.x Evidence Quality Action Series 前，固化执行顺序、输入依赖、输出文件和全局边界。

关键变更：
- 新增 `tools/build_evidence_action_series_baseline.py`。
- 新增 `tests/test_evidence_action_series_baseline.py`。
- 新增 `tests/evidence_action_series_baseline.json`。
- 新增 `docs/evidence_action_series_baseline_v0.4.7.4.0.md`。
- FastAPI 服务版本同步为 `0.4.7.4.0`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.4.0 是 Evidence Quality Action Series 的基线版本。它不新增诊断算法，也不执行修复，而是把 v0.4.7.3.5 形成的 action plan 固化为 6 个连续步骤：enrichment hardening、scenario registry calibration、base retrieval audit、anchor dependency audit、final evidence selection audit 和 manual review loop。该版本的意义在于确保后续小版本按顺序推进，每一步都有明确输入、输出和不可越界事项。

验证方式：
- `py_compile tools/build_evidence_action_series_baseline.py tools/build_evidence_root_cause_action_plan.py src/main.py` 通过。
- `tests.test_evidence_action_series_baseline`、`tests.test_evidence_root_cause_action_plan` 通过。
- Evidence action-series baseline：6 planned steps。
- Full Eval：本版本不运行。

后续影响：
- 下一步 v0.4.7.4.1 做 Evidence Report Enrichment Hardening，先检查 enrichment 未命中的 1 条 evidence 和字段稳定性。

### v0.4.7.4.1：Evidence Report Enrichment Hardening

阶段定位：对 v0.4.7.3.2 的 evidence enrichment 做字段稳定性加固，处理唯一未命中的标准类 evidence。

关键变更：
- `tools/check_evidence_coverage.py` 新增 citation location fallback 和标准章节 title fallback。
- 新增 `tools/check_evidence_enrichment_hardening.py`。
- 新增 `tests/test_evidence_enrichment_hardening.py`。
- 新增 `tests/evidence_enrichment_hardening_report.json`。
- FastAPI 服务版本同步为 `0.4.7.4.1`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.4.1 将 evidence enrichment 从“基本可用”推进到“字段稳定”。v0.4.7.3.2 中 180 条 final evidence 有 1 条标准类证据未命中，原因是 RAG eval report 中该证据只有 citation `[《信息安全技术 个人信息安全规范》C.1 概述]`，而 `section_no` 为空。本版本增加 citation/location fallback 和标准章节 title fallback 后，final evidence enrichment 达到 180/180，必需字段缺失为 0。该修复只影响离线诊断报告，不写回知识库 metadata，也不改变召回、rerank、prompt 或风险输出。

验证方式：
- `py_compile tools/check_evidence_coverage.py tools/check_evidence_enrichment_hardening.py src/main.py` 通过。
- `tests.test_evidence_enrichment_hardening`、`tests.test_evidence_coverage` 通过。
- Evidence enrichment hardening：180/180 matched，0 unmatched，field stability passed。
- Full Eval：本版本不运行。

后续影响：
- 下一步 v0.4.7.4.2 做 Scenario Registry Calibration，审计 scenario core gap 是否来自 registry core articles 过宽、缺漏或证据链真实缺失。

### v0.4.7.4.2：Scenario Registry Calibration

阶段定位：在不修改 scenario registry 的前提下，对 `scenario_core_gap` 做只读校准诊断，区分 registry core set 过宽候选与 evidence chain 真实缺口。

关键变更：
- 新增 `tools/calibrate_scenario_registry_coverage.py`。
- 新增 `tests/test_scenario_registry_calibration.py`。
- 新增 `tests/scenario_registry_calibration_report.json`。
- 新增 `docs/scenario_registry_calibration_v0.4.7.4.2.md`。
- FastAPI 服务版本同步为 `0.4.7.4.2`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不修改 `config/scenario_registry.json`、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.4.2 将 scenario core gap 从单一“缺证据”信号拆成可校准的 registry/evidence 两类问题。当前报告显示 8 个 scenario core gap cases，其中 7 个进入 high-priority review；4 个 case 同时出现 `evidence_chain_gap_candidate` 与 `final_primary_gap_overlap`，更像 final evidence 真实缺口；另 4 个 case 标记为 `registry_core_scope_review_candidate`，说明 final expected evidence 已覆盖，但 scenario core set 可能更宽，需要人工判断哪些 core articles 才应被视作该场景的必需核心证据。本版本只输出校准报告，不修改 registry、eval case 或 RAG 主链路。

验证方式：
- `py_compile tools/calibrate_scenario_registry_coverage.py src/main.py` 通过。
- `tests.test_scenario_registry_calibration` 通过。
- Scenario registry calibration：8 scenario-gap cases，7 high-priority review。
- Full Eval：本版本不运行。

后续影响：
- 下一步 v0.4.7.4.3 做 Base Retrieval Quality Audit，审计 dense/sparse/union 覆盖缺口是否来自基础召回、metadata/chunking 或 source coverage 问题。

### v0.4.7.4.3：Base Retrieval Quality Audit

阶段定位：在不改动 RAG 主链路的前提下，对 dense、sparse、union 三个基础召回层做只读质量审计，判断 base retrieval gap 更像 metadata/chunking 问题、source/index coverage 问题，还是 dense/sparse 单路召回偏弱。

关键变更：
- 新增 `tools/audit_base_retrieval_quality.py`。
- 新增 `tests/test_base_retrieval_quality_audit.py`。
- 新增 `tests/base_retrieval_quality_audit_report.json`。
- 新增 `docs/base_retrieval_quality_audit_v0.4.7.4.3.md`。
- FastAPI 服务版本同步为 `0.4.7.4.3`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.4.3 将 `base_retrieval_gap` 从单一 root cause 拆成 dense/sparse/union 层面的召回质量信号。当前报告显示 34 个 base-gap cases 全部进入 high-priority review；dense、sparse、union 三层均有 34 个 gap cases，且 `zero_base_recall=25`、`no_union_gain=34`。同时 33 个 case 出现 `anchor_rescue_pattern` 和 `metadata_or_chunking_review_candidate`，说明 expected evidence 大多可以被后续 anchor 层恢复，后续应优先审计 metadata、chunking、query lexical coverage 和 source/article 标识一致性，而不是直接修改 rerank 或 prompt。本版本只输出离线审计报告，不改变任何检索或生成行为。

验证方式：
- `py_compile tools/audit_base_retrieval_quality.py src/main.py` 通过。
- `tests.test_base_retrieval_quality_audit` 通过。
- Base retrieval quality audit：34 base-gap cases，34 high-priority review。
- Full Eval：本版本不运行。

后续影响：
- 下一步 v0.4.7.4.4 做 Anchor Dependency Audit，区分健康 anchor support 与 anchor masking weak base retrieval。

### v0.4.7.4.4：Anchor Dependency Audit

阶段定位：在不新增或修改 anchor 的前提下，对 `anchor_dependency` 做只读审计，区分健康 anchor support 与 anchor masking weak base retrieval。

关键变更：
- 新增 `tools/audit_anchor_dependency.py`。
- 新增 `tests/test_anchor_dependency_audit.py`。
- 新增 `tests/anchor_dependency_audit_report.json`。
- 新增 `docs/anchor_dependency_audit_v0.4.7.4.4.md`。
- FastAPI 服务版本同步为 `0.4.7.4.4`。
- 本版本不修 hidden seed、不新增 anchor、不修改 anchor 规则、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.4.4 将 anchor dependency 从“anchor 有帮助”拆成“健康补充”与“掩盖基础召回弱”两类治理信号。当前报告显示 33 个 anchor-dependency cases 全部进入 high-priority review，且全部为 `anchor_masking_base_retrieval_gap`、`anchor_rescue_success` 和 `high_anchor_gain`；其中 25 个 case 是 `zero_base_to_anchor_recovery`。这说明 anchor 当前主要在兜底 base retrieval，而不是仅作轻量增强。后续应优先治理 metadata、chunking、query lexical coverage 和 source/article 标识一致性；本版本不新增 anchor，也不修改任何 anchor 规则。

验证方式：
- `py_compile tools/audit_anchor_dependency.py src/main.py` 通过。
- `tests.test_anchor_dependency_audit` 通过。
- Anchor dependency audit：33 anchor-dependency cases，33 high-priority review。
- Full Eval：本版本不运行。

后续影响：
- 下一步 v0.4.7.4.5 做 Final Evidence Selection Audit，审计 anchor/rerank_input 已覆盖但 final evidence 丢失的情况。

### v0.4.7.4.5：Final Evidence Selection Audit

阶段定位：在不修改 rerank 或 final evidence selection 逻辑的前提下，对 `rerank_input -> final evidence` 的覆盖流失做只读审计。

关键变更：
- 新增 `tools/audit_final_evidence_selection.py`。
- 新增 `tests/test_final_evidence_selection_audit.py`。
- 新增 `tests/final_evidence_selection_audit_report.json`。
- 新增 `docs/final_evidence_selection_audit_v0.4.7.4.5.md`。
- FastAPI 服务版本同步为 `0.4.7.4.5`。
- 本版本不修 hidden seed、不新增 anchor、不修改 rerank、不修改 final evidence selection / truncation 逻辑、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.4.5 将 final evidence selection loss 从“覆盖下降”拆成证据功能和来源层面的可复核信号。当前报告显示 7 个 selection-loss cases，其中 5 个进入 high-priority review；7 个 case 全部出现 `primary_evidence_lost`，6 个出现 `operative_evidence_lost`，4 个出现 `scenario_core_lost`，1 个出现 `liability_evidence_lost`。这说明 final selection 丢失的不是无关背景材料，而是会影响 grounding 的主要法条支撑。本版本只输出审计报告，不修改 rerank、prompt 或 final selection 逻辑。

验证方式：
- `py_compile tools/audit_final_evidence_selection.py src/main.py` 通过。
- `tests.test_final_evidence_selection_audit` 通过。
- Final evidence selection audit：7 selection-loss cases，5 high-priority review。
- Full Eval：本版本不运行。

后续影响：
- 下一步 v0.4.7.4.6 做 Manual Review Loop，把前述审计信号沉淀成可人工确认、可转化为后续 fixtures 或治理行动的 review package。

### v0.4.7.4.6：Manual Review Loop

阶段定位：收束 v0.4.7.4.x Evidence Quality Action Series，把前序多个离线 audit 合并为 case-centered manual review packages。

关键变更：
- 新增 `tools/build_manual_review_loop.py`。
- 新增 `tests/test_manual_review_loop.py`。
- 新增 `tests/evidence_manual_review_loop_report.json`。
- 新增 `docs/manual_review_loop_v0.4.7.4.6.md`。
- FastAPI 服务版本同步为 `0.4.7.4.6`。
- 本版本不修 hidden seed、不新增 anchor、不修改 anchor 规则、不修改 rerank、不修改 final evidence selection / truncation 逻辑、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不写入人工复核结论、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.4.6 将前序 evidence quality audits 从多个分散 JSON 收束成 36 个 case-centered manual review packages，全部保持 `pending`。队列显示 `base_retrieval_quality_review=34`、`anchor_dependency_review=33`、`scenario_registry_calibration=8`、`primary_evidence_review=8`、`final_evidence_selection_review=7`、`high_risk_grounding_review=8`；后续行动候选包括 metadata/chunking/query coverage review、anchor dependency governance、scenario core article review、primary evidence fixture candidate review 和 final evidence selection policy review。该版本只建立人工复核闭环，不写入人工结论，也不修改任何主链路行为。

验证方式：
- `py_compile tools/build_manual_review_loop.py src/main.py` 通过。
- `tests.test_manual_review_loop` 通过。
- Manual review loop package：36 packages，36 pending。
- Full Eval：本版本不运行。

后续影响：
- v0.4.7.4.x 质量行动系列完成。下一阶段建议先人工确认 review packages，再决定是否进入 fixtures、metadata/chunking 治理、scenario core article 调整或 final evidence selection policy 设计。

### v0.4.7.5.0：Manual Review Decision Schema

阶段定位：开启 Manual Review Decision & Governance Layer，把 v0.4.7.4.6 的 pending review packages 转换为可填写、可校验、可追溯的人工复核 decision records。

关键变更：
- 新增 `tools/build_manual_review_decision_schema.py`。
- 新增 `tests/test_manual_review_decision_schema.py`。
- 新增 `tests/evidence_manual_review_decision_schema.json`。
- 新增 `docs/manual_review_decision_schema_v0.4.7.5.0.md`。
- 本版本不修 hidden seed、不新增或修改 anchor、不修改 rerank、不改 prompt、不改 risk supplement / term preservation 规则、不改 eval case、不接入 `rag_query` 主流程。

报告写法：
> v0.4.7.5.0 将 36 个 pending manual review packages 转换为 36 条 decision records，并定义允许的 decision、root cause、follow-up action、必填 reviewer fields、禁止变更目标和全局 guardrails。所有 reviewer decision 字段均保持空白，表示诊断建议尚未被人工确认。本版本把“诊断结果”与“修复授权”明确分开。

验证方式：
- `py_compile tools/build_manual_review_decision_schema.py` 通过。
- `tests.test_manual_review_decision_schema` 通过。
- Decision schema report：36 records，36 pending。
- Full Eval：本版本不运行。

后续影响：
- 下一步必须先校验人工填写结论，不能从诊断建议直接进入修复。

### v0.4.7.5.1：Manual Review Decision Validator

阶段定位：为人工复核 decision records 增加离线 validator，防止人工结论越界或引用非法 action/root cause。

关键变更：
- 新增 `tools/validate_manual_review_decisions.py`。
- 新增 `tests/test_manual_review_decision_validation.py`。
- 新增 `tests/evidence_manual_review_decision_validation_report.json`。
- 新增 `docs/manual_review_decision_validator_v0.4.7.5.1.md`。
- 本版本只校验离线人工复核结论，不修改主链路、不运行 full eval。

报告写法：
> v0.4.7.5.1 建立人工复核结论的机器校验入口。completed decision 必须包含 reviewer、reviewed_at、decision 和 rationale；confirmed root cause/action 必须来自 schema；proposed change targets 不得指向 hidden seed、anchor、rerank、prompt、risk supplement、eval case 或 `rag_query` 主流程。当前 36 条记录全部 pending，invalid records 为 0。

验证方式：
- `py_compile tools/validate_manual_review_decisions.py` 通过。
- `tests.test_manual_review_decision_validation` 通过。
- 校验报告：36 条记录，0 条无效，36 条待处理。
- Full Eval：本版本不运行。

后续影响：
- 只有 completed 且 valid 的 decision 才能进入 action candidates 的 ready 状态。

### v0.4.7.5.2：Manual Review Action Candidates

阶段定位：从 decision records 与 validation report 生成 action candidates，并区分 ready 与 blocked。

关键变更：
- 新增 `tools/build_manual_review_action_candidates.py`。
- 新增 `tests/test_manual_review_action_candidates.py`。
- 新增 `tests/evidence_manual_review_action_candidates.json`。
- 新增 `docs/manual_review_action_candidates_v0.4.7.5.2.md`。
- 本版本只生成候选行动，不修改 scenario registry、knowledge manifest、chunking、selection policy 或主链路。

报告写法：
> v0.4.7.5.2 将人工复核治理层推进到候选行动层，但严格区分 readiness。当前报告生成 106 个 action candidates，其中 ready action candidates 为 0，blocked pending candidates 为 106。这说明所有候选动作仍只是诊断建议，尚未被人工确认，不应作为工程修复指令。

验证方式：
- `py_compile tools/build_manual_review_action_candidates.py` 通过。
- `tests.test_manual_review_action_candidates` 通过。
- Action candidates report：106 candidates，0 ready，106 blocked。
- Full Eval：本版本不运行。

后续影响：
- 后续工程版本只能消费 `ready_from_valid_decision`，不能消费 `blocked_pending_manual_review`。

### v0.4.7.5.3：Evidence Fixture Candidate Pool

阶段定位：把与 primary evidence、functional typing、final selection、scenario core 相关的 action candidates 沉淀为未来 fixture 候选池。

关键变更：
- 新增 `tools/build_evidence_fixture_candidate_pool.py`。
- 新增 `tests/test_evidence_fixture_candidate_pool.py`。
- 新增 `tests/evidence_fixture_candidate_pool.json`。
- 新增 `docs/evidence_fixture_candidate_pool_v0.4.7.5.3.md`。
- 本版本不写入 eval cases、golden fixtures 或 hidden seeds。

报告写法：
> v0.4.7.5.3 生成 58 个 evidence fixture candidates，覆盖 primary evidence grounding、functional typing、final selection grounding 和 scenario core scope 四类未来 fixture 方向。当前 ready fixture candidates 为 0，blocked fixture candidates 为 58，因此这些候选只能用于人工复核和后续草案准备，不能写入 eval cases 或 hidden seed。

验证方式：
- `py_compile tools/build_evidence_fixture_candidate_pool.py` 通过。
- `tests.test_evidence_fixture_candidate_pool` 通过。
- Fixture candidate pool：58 candidates，0 ready，58 blocked。
- Full Eval：本版本不运行。

后续影响：
- 只有人工 completed 且 validator 通过后，fixture candidate 才能进入 fixture 草案阶段。

### v0.4.7.5.4：Manual Review Governance Report

阶段定位：收束 v0.4.7.5.x，把 schema、validator、action candidates 和 fixture pool 汇总为治理报告。

关键变更：
- 新增 `tools/build_manual_review_governance_report.py`。
- 新增 `tests/test_manual_review_governance_report.py`。
- 新增 `tests/evidence_manual_review_governance_report.json`。
- 新增 `docs/manual_review_governance_report_v0.4.7.5.4.md`。
- FastAPI 服务版本同步为 `0.4.7.5.4`。
- 本版本只生成治理摘要，不修改主链路或任何规则配置。

报告写法：
> v0.4.7.5.4 将人工复核治理层收束为统一入口。当前治理报告显示 36 条 decision records 全部 pending，invalid decisions 为 0；ready action candidates 为 0，blocked action candidates 为 106；ready fixture candidates 为 0，blocked fixture candidates 为 58；readiness state 为 `manual_review_required`。这意味着下一步应先完成人工复核决策，而不是直接修改检索、anchor、rerank、prompt、risk supplement 或 eval case。

验证方式：
- `py_compile tools/build_manual_review_governance_report.py src/main.py` 通过。
- `tests.test_manual_review_governance_report` 通过。
- Governance report：36 decisions，0 ready actions，106 blocked actions，58 blocked fixture candidates。
- Full Eval：本版本不运行。

后续影响：
- v0.4.7.5.x 完成。下一阶段建议做 v0.4.7.6.x Manual Review Execution Kit，让 reviewer 能高效填写并校验 completed decisions。

### v0.4.7.6.0：Manual Review Workbench Export

阶段定位：开启 Manual Review Execution Kit，把 pending decision records 导出为 reviewer 可使用的 JSON/CSV 工作台。

关键变更：
- 新增 `tools/export_manual_review_workbench.py`。
- 新增 `tests/test_manual_review_workbench_export.py`。
- 新增 `tests/evidence_manual_review_workbench.json`。
- 新增 `tests/evidence_manual_review_workbench.csv`。
- 新增 `docs/manual_review_workbench_export_v0.4.7.6.0.md`。
- 本版本不写入真实人工结论，不修改主链路。

报告写法：
> v0.4.7.6.0 将 36 条 pending decision records 导出为 reviewer workbench。JSON 保留完整 diagnostic summary、evidence context 和 reviewer input template；CSV 提供可排序、可浏览、可填写的扁平字段。所有 reviewer 字段均保持空白，确保导出动作不会被误认为人工结论。

验证方式：
- `py_compile tools/export_manual_review_workbench.py` 通过。
- `tests.test_manual_review_workbench_export` 通过。
- Workbench export：36 items，36 pending。
- Full Eval：本版本不运行。

后续影响：
- reviewer 已具备可操作入口，但仍需示例和进度报告防止错误填写。

### v0.4.7.6.1：Manual Review Decision Examples

阶段定位：提供 completed/rejected/deferred/invalid 的合成示例，培训 reviewer 并验证 validator 行为。

关键变更：
- 新增 `tools/build_manual_review_decision_examples.py`。
- 新增 `tests/test_manual_review_decision_examples.py`。
- 新增 `tests/manual_review_decision_examples.json`。
- 新增 `docs/manual_review_decision_examples_v0.4.7.6.1.md`。
- 示例不写入真实 decision records。

报告写法：
> v0.4.7.6.1 生成 4 条合成人工复核示例，其中 3 条 valid，1 条 invalid。invalid 示例故意将 proposed change target 指向 `rag_anchor_rules`，验证 validator 会拒绝 anchor mutation。该文件只用于 reviewer 训练和校验夹具，不得合并回真实人工复核记录。

验证方式：
- `py_compile tools/build_manual_review_decision_examples.py` 通过。
- `tests.test_manual_review_decision_examples` 通过。
- Decision examples：4 examples，3 valid，1 invalid，0 expectation mismatches。
- Full Eval：本版本不运行。

后续影响：
- reviewer 填写规则更清楚，非法填写模式可以在进入真实链路前被拦截。

### v0.4.7.6.2：Manual Review Progress Report

阶段定位：汇总真实 decision schema、validation report、workbench、action candidates 和 fixture pool，形成复核进度与阻塞报告。

关键变更：
- 新增 `tools/build_manual_review_progress_report.py`。
- 新增 `tests/test_manual_review_progress_report.py`。
- 新增 `tests/evidence_manual_review_progress_report.json`。
- 新增 `docs/manual_review_progress_report_v0.4.7.6.2.md`。
- 本版本不推断人工结论，不写入真实 decision records。

报告写法：
> v0.4.7.6.2 将人工复核执行状态可视化。当前 36 个 cases 全部 pending，completed cases 为 0，invalid cases 为 0；ready action candidates 为 0，blocked action candidates 为 106；ready fixture candidates 为 0，blocked fixture candidates 为 58。该结果说明执行入口已建立，但下游工程动作仍全部阻塞在人工复核前。

验证方式：
- `py_compile tools/build_manual_review_progress_report.py` 通过。
- `tests.test_manual_review_progress_report` 通过。
- Progress report：36 cases，0 completed，36 pending。
- Full Eval：本版本不运行。

后续影响：
- 后续可用该报告追踪 reviewer 进度、非法结论和 blocked candidates。

### v0.4.7.6.3：Ready Action Routing Dry Run

阶段定位：收束 Manual Review Execution Kit，只对 ready action candidates 做 dry-run 路由，并确认 blocked candidates 不会被路由。

关键变更：
- 新增 `tools/build_ready_action_routing_dry_run.py`。
- 新增 `tests/test_ready_action_routing_dry_run.py`。
- 新增 `tests/ready_action_routing_dry_run_report.json`。
- 新增 `docs/ready_action_routing_dry_run_v0.4.7.6.3.md`。
- FastAPI 服务版本同步为 `0.4.7.6.3`。
- 本版本不执行任何修复，不修改主链路。

报告写法：
> v0.4.7.6.3 对 ready action candidates 做路由预演。当前 ready routes 为 0，blocked candidates 为 106，manual review completed cases 为 0，pending cases 为 36，readiness state 仍为 `manual_review_required`。这说明系统不会把 pending 诊断自动变成工程任务；下一步必须先完成人工复核。

验证方式：
- `py_compile tools/build_ready_action_routing_dry_run.py src/main.py` 通过。
- `tests.test_ready_action_routing_dry_run` 通过。
- Routing dry run：0 ready routes，106 blocked candidates。
- Full Eval：本版本不运行。

后续影响：
- v0.4.7.6.x 完成。下一步应填写 workbench 中的人工复核结论，并重新运行 validator/progress/routing，而不是直接进入 retrieval、anchor、rerank 或 prompt 修改。

### v0.4.7.7.0：Workbench Intake Contract

阶段定位：开启 Manual Review Intake Gate，定义人工填写 workbench 的导入契约。

关键变更：
- 新增 `tools/build_workbench_intake_contract.py`。
- 新增 `tests/test_workbench_intake_contract.py`。
- 新增 `tests/manual_review_intake_contract_report.json`。
- 新增 `docs/workbench_intake_contract_v0.4.7.7.0.md`。
- 本版本不读取或写入真实人工结论。

报告写法：
> v0.4.7.7.0 定义 workbench intake contract，明确 10 个可导入 reviewer 字段、12 个只读上下文字段、case_id 对齐规则、枚举值和写入策略。契约规定 importer 只能输出 proposed schema，不得覆盖原始 decision schema，也不得触碰 hidden seed、anchor、rerank、prompt、risk supplement、eval case 或 `rag_query` 主流程。

验证方式：
- `py_compile tools/build_workbench_intake_contract.py` 通过。
- `tests.test_workbench_intake_contract` 通过。
- Intake contract：10 importable fields，12 read-only fields。
- Full Eval：本版本不运行。

后续影响：
- importer 必须按该契约接收 CSV/JSON 填写结果。

### v0.4.7.7.1：Manual Review Workbench Importer

阶段定位：读取填写后的 workbench CSV/JSON，生成 proposed decision schema 和 import report。

关键变更：
- 新增 `tools/import_manual_review_workbench.py`。
- 新增 `tests/test_manual_review_workbench_import.py`。
- 新增 `tests/proposed_manual_review_decision_schema.json`。
- 新增 `tests/manual_review_workbench_import_report.json`。
- 新增 `docs/manual_review_workbench_importer_v0.4.7.7.1.md`。
- 本版本不覆盖原始 decision schema。

报告写法：
> v0.4.7.7.1 建立 workbench 导入入口，但只输出 proposed schema。当前真实 CSV 中 36 行 reviewer 字段均为空，因此 importer 正确输出 0 imported、36 rejected，拒绝原因均为 empty importable content。该行为证明空白 workbench 不会被误提升为人工结论。

验证方式：
- `py_compile tools/import_manual_review_workbench.py` 通过。
- `tests.test_manual_review_workbench_import` 通过。
- Workbench import：0 imported，36 rejected。
- Full Eval：本版本不运行。

后续影响：
- 下一步必须审计 proposed schema 与原 schema 的差异。

### v0.4.7.7.2：Manual Review Decision Diff & Audit Trail

阶段定位：比较原始 decision schema 与 proposed decision schema，输出字段级 diff 和 prohibited target 审计。

关键变更：
- 新增 `tools/audit_manual_review_decision_diff.py`。
- 新增 `tests/test_manual_review_decision_diff.py`。
- 新增 `tests/manual_review_decision_diff_report.json`。
- 新增 `docs/manual_review_decision_diff_v0.4.7.7.2.md`。
- 本版本不 promotion，不覆盖任何 schema。

报告写法：
> v0.4.7.7.2 为 proposed decisions 增加 audit trail。当前 proposed schema 没有导入任何真实变更，因此 diff report 显示 0 changed cases、0 blocked cases、0 missing/new cases。单测覆盖 completed decision diff 和 `rag_anchor_rules` 等 prohibited target 阻断。

验证方式：
- `py_compile tools/audit_manual_review_decision_diff.py` 通过。
- `tests.test_manual_review_decision_diff` 通过。
- Diff report：0 changed cases，0 blocked cases。
- Full Eval：本版本不运行。

后续影响：
- 只有 diff 不含 blocked case 的 proposed schema 才能进入 validation。

### v0.4.7.7.3：Proposed Manual Review Decision Validation

阶段定位：对 proposed decision schema 单独运行 validator。

关键变更：
- 新增 `tools/validate_proposed_manual_review_decisions.py`。
- 新增 `tests/test_proposed_manual_review_validation.py`。
- 新增 `tests/proposed_manual_review_decision_validation_report.json`。
- 新增 `docs/proposed_manual_review_validation_v0.4.7.7.3.md`。
- 本版本不 promotion，不覆盖原 schema。

报告写法：
> v0.4.7.7.3 复用既有 validator 对 proposed schema 做独立校验。当前 proposed schema 仍为 36 条 pending records，valid records 为 0、invalid records 为 0。这说明导入门禁尚未接收任何真实 completed decision。

验证方式：
- `py_compile tools/validate_proposed_manual_review_decisions.py` 通过。
- `tests.test_proposed_manual_review_validation` 通过。
- Proposed validation：36 records，0 invalid，36 pending。
- Full Eval：本版本不运行。

后续影响：
- promotion dry run 只能消费 completed + valid proposed decisions。

### v0.4.7.7.4：Validated Decision Promotion Dry Run

阶段定位：只筛选 completed + valid 的 proposed decisions，生成 promotion dry-run report。

关键变更：
- 新增 `tools/build_validated_decision_promotion_dry_run.py`。
- 新增 `tests/test_validated_decision_promotion_dry_run.py`。
- 新增 `tests/validated_decision_promotion_dry_run_report.json`。
- 新增 `docs/validated_decision_promotion_dry_run_v0.4.7.7.4.md`。
- 本版本不覆盖原 schema，不执行工程修复。

报告写法：
> v0.4.7.7.4 将 promotion 条件收紧为 completed + valid。当前 proposed validation 没有 valid completed decision，因此 promotion candidates 为 0、ready action candidates 为 0。单测覆盖 completed + valid 记录可以生成 ready action 的路径，保证未来人工填写后链路可用。

验证方式：
- `py_compile tools/build_validated_decision_promotion_dry_run.py` 通过。
- `tests.test_validated_decision_promotion_dry_run` 通过。
- Promotion dry run：0 promotion candidates，0 ready actions。
- Full Eval：本版本不运行。

后续影响：
- 若未来出现 promotion candidates，才能进入 ready action planning。

### v0.4.7.7.5：Manual Review Intake Gate Closeout

阶段定位：收束 Manual Review Intake Gate，汇总 contract、import、diff、validation 和 promotion dry run。

关键变更：
- 新增 `tools/build_manual_review_intake_gate_closeout.py`。
- 新增 `tests/test_manual_review_intake_gate_closeout.py`。
- 新增 `tests/manual_review_intake_gate_closeout_report.json`。
- 新增 `docs/manual_review_intake_gate_closeout_v0.4.7.7.5.md`。
- FastAPI 服务版本同步为 `0.4.7.7.5`。
- 本版本不 promotion，不修改主链路。

报告写法：
> v0.4.7.7.5 将 intake gate 汇总为单一判定入口。当前 gate status 为 `blocked`：imported rows 为 0、rejected rows 为 36、changed cases 为 0、valid proposed records 为 0、promotion candidates 为 0、ready action candidates 为 0。阻塞原因包括 `no_imported_review_rows`、`no_promotion_candidates` 和 `no_ready_action_candidates`。这说明下一步仍是填写人工复核 workbench，而不是启动工程修复。

验证方式：
- `py_compile tools/build_manual_review_intake_gate_closeout.py src/main.py` 通过。
- `tests.test_manual_review_intake_gate_closeout` 通过。
- Intake gate closeout：blocked，0 promotion candidates。
- Full Eval：本版本不运行。

后续影响：
- v0.4.7.7.x 完成。只有当 closeout gate open 后，才建议进入 v0.4.7.8.x Ready Action Planning。

### v0.4.7.8.0：Manual Review Visual Workbench Contract

阶段定位：开启 Visual Manual Review Workbench 系列，先定义离线视觉审阅台的数据契约、UI 信息架构和安全边界。

关键变更：
- 新增 `tools/build_manual_review_visual_workbench_contract.py`。
- 新增 `tests/test_manual_review_visual_workbench_contract.py`。
- 新增 `tests/manual_review_visual_workbench_contract_report.json`。
- 新增 `docs/manual_review_visual_workbench_contract_v0.4.7.8.0.md`。
- FastAPI 服务版本同步为 `0.4.7.8.0`。
- 本版本只定义视觉审阅台契约，不实现正式 UI，不导入 reviewer 结论，不覆盖原始 schema。

报告写法：
> v0.4.7.8.0 将人工复核从 CSV/JSON 文件操作推进到可视化审阅台设计层，但仍保持离线治理边界。当前 visual contract ready 为 `true`，可读取 36 个 workbench items，其中 36 个仍为 pending，29 个为 high priority；intake gate 仍为 `blocked`，promotion candidates 与 ready action candidates 均为 0。这说明视觉工具可以帮助 reviewer 看懂并填写复核结论，但不会绕过 importer、diff、validator、promotion dry run 和 closeout gate。

验证方式：
- `py_compile tools/build_manual_review_visual_workbench_contract.py src/main.py` 通过。
- `tests.test_manual_review_visual_workbench_contract` 通过。
- Visual workbench contract：36 cases，gate blocked，contract ready true。
- Full Eval：本版本不运行。

后续影响：
- v0.4.7.8.1 可在该契约上实现静态本地 HTML dashboard，优先做只读 case list/detail 和 gate/status 展示。

### v0.4.7.8.1：Manual Review Visual Workbench Static UI

阶段定位：把视觉审阅台从契约推进到可打开的本地静态页面。

关键变更：
- 新增 `tools/build_manual_review_visual_workbench.py`。
- 新增 `tools/manual_review_visual_workbench/index.html`。
- 新增 `tests/manual_review_visual_workbench_build_report.json`。
- 新增 `tests/test_manual_review_visual_workbench.py`。
- 新增 `tests/test_manual_review_visual_workbench_build_artifact.py`。
- 新增 `docs/manual_review_visual_workbench_static_v0.4.7.8.1.md`。

报告写法：
> v0.4.7.8.1 生成了一个自包含本地 HTML 审阅台，可直接读取嵌入的离线 reports 展示 36 个 manual review cases。页面支持队列、搜索、case detail、overview、evidence 和 questions，不需要启动后端、数据库或 RAG 服务。

验证方式：
- `py_compile tools/build_manual_review_visual_workbench.py` 通过。
- `tests.test_manual_review_visual_workbench` 通过。
- Static build report：36 cases，36 pending，29 high priority。

### v0.4.7.8.2：Manual Review Visual Workbench Export

阶段定位：把静态看板推进到可填写、可导出的 reviewer 工具。

关键变更：
- 本地 HTML 支持 reviewer form。
- 草稿保存在浏览器 localStorage。
- 支持导出 filled workbench JSON/CSV。
- 新增 `docs/manual_review_visual_workbench_export_v0.4.7.8.2.md`。

报告写法：
> v0.4.7.8.2 让 reviewer 可以在页面里填写人工复核字段，并导出 filled workbench JSON/CSV。导出结果仍必须进入 importer、diff、validator、promotion dry run 和 closeout，页面本身不写回原始 schema，也不执行工程修复。

验证方式：
- 单测覆盖 HTML 自包含、导出控件、localStorage 草稿和无后端主流程调用。
- Full Eval：本版本不运行。

### v0.4.7.8.3：Manual Review Visual Workbench Status

阶段定位：补齐视觉审阅台的治理状态面板，收束 v0.4.7.8.x 为可落地工具。

关键变更：
- 页面展示 import、diff、validation、promotion 和 closeout gate 状态。
- 新增 `docs/manual_review_visual_workbench_status_v0.4.7.8.3.md`。
- FastAPI 服务版本同步为 `0.4.7.8.3`。

报告写法：
> v0.4.7.8.3 完成了可落地的本地人工审阅工具：reviewer 可以打开 HTML、筛选高风险 case、查看诊断和证据上下文、填写复核结论、导出 JSON/CSV，并回到既有治理链路运行 importer、diff、validator、promotion dry run 和 closeout。当前 gate 仍为 `blocked`，因为真实 reviewer 结论尚未导入。

验证方式：
- `py_compile tools/build_manual_review_visual_workbench.py tools/build_manual_review_visual_workbench_contract.py src/main.py` 通过。
- `tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_contract tests.test_manual_review_visual_workbench_build_artifact` 通过。
- Static workbench build：36 cases，gate blocked，支持 case list/detail/form/export/pipeline status。
- Full Eval：本版本不运行。

### v0.4.7.8.4：Manual Review Visual Workbench Guide & Language

阶段定位：补强视觉审阅台的操作可理解性和语言扩展入口。

关键变更：
- 左侧新增 `操作指南` 面板。
- case detail 新增 `Guide` 页签。
- 顶部新增统一风格语言选择器，当前支持 `简体中文`。
- 新增 `docs/manual_review_visual_workbench_guide_language_v0.4.7.8.4.md`。
- FastAPI 服务版本同步为 `0.4.7.8.4`。

报告写法：
> v0.4.7.8.4 让视觉审阅台更适合非工程 reviewer 使用：页面直接说明先选队列、再看 case、再填写 Decision、最后导出并运行既有治理链路。语言选择器当前支持简体中文，控件保持统一的法律风控工作台风格，并为后续多语言扩展预留入口。

### v0.4.7.8.5：Manual Review Visual Workbench i18n

阶段定位：把视觉审阅台的语言入口从“预留控件”修复为真实可用的双语界面能力。

关键实现：
- `tools/build_manual_review_visual_workbench.py` 新增统一 `ui.messages` 双语字典，默认 `zh-CN`，支持 `简体中文` 与 `English`。
- 页面标题、队列、状态、KPI、案例列表、详情页签、证据表头、复核表单、pipeline、导出按钮和操作指南均改为语言驱动。
- 语言选择写入浏览器 `localStorage`，刷新后保留 reviewer 的界面语言选择。
- 新增 `docs/manual_review_visual_workbench_i18n_v0.4.7.8.5.md`。
- FastAPI 服务版本同步为 `0.4.7.8.5`。

报告写法：
> v0.4.7.8.5 修复了 visual workbench 的可用性问题：语言选择不再只是显示控件，而是能在简体中文和英文之间切换整套界面，包括操作指南。该版本仍保持离线静态工具边界，不接入 RAG 主流程，不调用后端，不修改检索、prompt、rerank、anchor 或 eval case。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

### v0.4.7.8.6：Manual Review Visual Workbench Label Glossary

阶段定位：让非系统设计者也能读懂 case 内部英文标签，同时保持导出数据与治理链路兼容。

关键实现：
- case detail 取消单独 `Guide` 页签，操作指南保留在左下角。
- 新增 `标签说明 / Glossary` 页签，解释当前 case 出现的 queue tags、issue types、root causes、follow-up actions、diagnostics、evidence context、gate blockers、import errors 和 guardrails。
- 页面展示采用“可读名称 / 原始代码”，悬停显示解释；跳转按钮可回到相关页签。
- 新增本地导出状态：导出后记录 `last_exported_at`，草稿更新晚于导出时提示“有未导出的更新”。
- 新增 `docs/manual_review_visual_workbench_label_glossary_v0.4.7.8.6.md`。
- FastAPI 服务版本同步为 `0.4.7.8.6`。

报告写法：
> v0.4.7.8.6 将 visual workbench 从“工程人员可用”推进到“业务 reviewer 可读”。内部英文枚举不再裸露为难懂标签，而是配有中文名称、原始代码和解释；操作指南保持在左下角，详情页新增标签说明和跳转。导出状态也改为本地自动提示，避免 reviewer 填完后不知道是否已经导出。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

验证方式：
- `py_compile tools/build_manual_review_visual_workbench.py src/main.py` 通过。
- `tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact` 通过。
- Static workbench build：支持 operation guide，supported languages 为 `zh-CN`。
- Full Eval：本版本不运行。

### v0.4.7.8.7：Manual Review Visual Workbench Case Context

阶段定位：补齐非工程 reviewer 的案由理解能力，让审阅台不再只显示 case id 和内部诊断标签。

关键实现：
- `tools/build_manual_review_visual_workbench.py` 新增只读 `case_context` 合并逻辑，读取 `tests/rag_eval_report.json`、`tests/rag_eval_cases.json` 和 `config/scenario_registry.json`。
- 左侧 case 列表在 case id 下方展示案由线索和待审问题。
- 概览页顶部新增案由线索块，展示案由、待审问题、风险场景、涉及领域、预期风险类型、预期整改动作和上下文来源。
- 搜索框可搜索案由、问题、场景描述、预期风险类型和整改动作。
- JSON 导出保留 `case_context`；CSV 导出新增只读 `case_topic` 与 `question` 列，importer 仍只读取 reviewer 可导入字段。
- 新增 `docs/manual_review_visual_workbench_case_context_v0.4.7.8.7.md`。
- FastAPI 服务版本同步为 `0.4.7.8.7`。

报告写法：
> v0.4.7.8.7 修复了 visual workbench 的关键可用性缺口：reviewer 现在能先看到“这个案子在审什么”，再判断证据链和诊断标签是否合理。该版本通过已有离线评测报告和 scenario registry 自动带出案由线索，不新增样本、不修改检索策略、不改 prompt/rerank/anchor，也不接入 RAG 主流程。当前 36/36 个 workbench cases 均有真实 case context，intake gate 仍保持 `blocked`，等待人工复核填写。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- 静态扫描确认未出现 `fetch(`、`XMLHttpRequest`、`/ask`、`rag_query(`、`ChatOpenAI`。

### v0.4.7.8.8：Manual Review Visual Workbench Decision Tab Clarity

阶段定位：继续降低非工程 reviewer 使用门槛，让“决策”页不再只是字段表单，而是清楚说明要判断什么、怎么判断、每个选项代表什么。

关键实现：
- 决策页新增复核判断摘要，集中展示案由线索、主要诊断、建议根因、建议后续动作、当前结论和导出状态。
- 新增建议审阅顺序：先核对案由/问题/证据，再选择复核结论，最后确认根因、后续动作和回归测试样本候选。
- 复核结论改为带说明的单选卡片，根因和后续动作勾选项继续显示可读名称、说明和原始代码。
- 为复核信息、结论、根因、后续动作和治理备注增加区块说明与输入提示。
- 将 `fixture candidate` 面向 reviewer 的显示改为“回归测试样本候选”，强调不会直接写入 eval case。
- 新增 `docs/manual_review_visual_workbench_decision_tab_v0.4.7.8.8.md`。
- FastAPI 服务版本同步为 `0.4.7.8.8`。

报告写法：
> v0.4.7.8.8 将 visual workbench 的“决策”页从工程字段填写表单升级为可审阅的人工判断界面。reviewer 现在可以先看到案由、诊断和建议治理动作，再按“核对证据、选择结论、确认治理”的顺序填写判断。页面继续保留原始代码以兼容 importer、diff、validator 和 closeout gate，但对外显示改为法律/合规 reviewer 可理解的中文标签和说明。该版本仍是离线静态治理工具，不修改检索、prompt、rerank、anchor、eval case 或 RAG 主流程。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- Build report：`supports_decision_tab_readability=true`，36 cases，gate `blocked`。

### v0.4.7.8.9：Manual Review Visual Workbench Import Replay

阶段定位：补齐可视化人工复核台的续审能力，让导出的人工复核文件可以重新导回页面，自动回填到对应案例草稿。

解决的问题：reviewer 在页面导出 filled workbench 后，如果关闭页面或换设备继续审阅，过去只能手工重新定位每个 case 和字段，容易漏填或填错。

关键实现：
- 新增 `导入 JSON/CSV` 控件时曾支持读取页面导出的 filled workbench JSON/CSV；维护加固后正式导入已收紧为 filled JSON，CSV 仅作人工阅读/核对。
- 浏览器使用 `FileReader` 离线读取用户选择的本地文件，不访问后端。
- 按 `case_id` 匹配当前 workbench case，只回填 reviewer 字段到本地草稿。
- 导入后自动刷新队列、侧栏状态、badge 和当前 case detail。
- 输出导入摘要，区分已回填、未匹配、空白跳过和错误。
- Build report 新增 `supports_review_export_import=true`。
- 新增 `docs/manual_review_visual_workbench_import_v0.4.7.8.9.md`。
- FastAPI 服务版本同步为 `0.4.7.8.9`。

报告写法：
> v0.4.7.8.9 将可视化人工复核台从“一次性填写导出”推进到“可暂停、可恢复的离线审阅工具”。维护加固后，reviewer 只能把之前从页面导出的 filled JSON 重新导入页面，系统按 case_id 自动放回本地草稿，并提示未匹配或空白记录；CSV 仅用于表格查看和人工核对。该能力只改善人工审阅体验，不写项目文件、不绕过 importer / diff / validator / closeout，也不修改检索、prompt、rerank、anchor、eval case 或 RAG 主流程。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- 静态扫描确认未出现 `fetch(`、`XMLHttpRequest`、`/ask`、`rag_query(`、`ChatOpenAI`。

### v0.4.7.8.10：Manual Review Visual Workbench Field Requirement Labels

阶段定位：继续降低非工程 reviewer 的填写压力，明确哪些字段必须填、哪些字段只有条件触发时才需要填、哪些字段可以留空。

解决的问题：人工复核表单字段较多，reviewer 容易误以为每一项都必须填写，导致审阅负担过重，或者在不确定时为了“填满表格”而误填治理动作。

关键实现：
- 决策页字段新增 `必填 / 条件必填 / 可选` 标记。
- 复核人、复核日期、复核结论和理由标为必填。
- 确认的根因标为条件必填，仅在确认诊断成立或确认需要范围校准时要求填写。
- 驳回根因、后续动作、变更目标、回归测试样本候选和备注标为可选。
- 每个关键字段增加简短说明，提示不确定时可以如何处理。
- Build report 新增 `supports_field_requirement_labels=true`。
- 新增 `docs/manual_review_visual_workbench_field_requirements_v0.4.7.8.10.md`。
- FastAPI 服务版本同步为 `0.4.7.8.10`。

报告写法：
> v0.4.7.8.10 进一步改善人工复核台的可用性：页面不再让 reviewer 猜测哪些字段必须填写，而是直接标明必填、条件必填和可选。该能力减少了非工程 reviewer 的填写压力，也降低了不确定情况下误填后续治理动作的风险。该版本只改变界面说明，不改变导出 schema、validator 规则、检索、prompt、rerank、anchor、eval case 或 RAG 主流程。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- 静态扫描确认未出现 `fetch(`、`XMLHttpRequest`、`/ask`、`rag_query(`、`ChatOpenAI`。

### v0.4.7.8.11：Manual Review Visual Workbench Manual Save Button

阶段定位：增强离线人工复核台的草稿保存确认感，让 reviewer 明确知道当前 case 草稿已经手动保存。

解决的问题：页面此前已经自动把输入暂存在浏览器本地，但非工程 reviewer 很难确认“是否保存成功”，容易担心关闭页面后内容丢失。

关键实现：
- 决策页新增 `保存草稿 / Save draft` 按钮。
- 点击保存后写入当前 case 草稿的 `saved_at` 时间戳。
- case header 显示 `上次保存` 或 `有未手动保存的更新`。
- 保留原自动暂存机制，手动保存只增加明确反馈。
- Build report 新增 `supports_manual_draft_save=true`。
- 新增 `docs/manual_review_visual_workbench_manual_save_v0.4.7.8.11.md`。
- FastAPI 服务版本同步为 `0.4.7.8.11`。

报告写法：
> v0.4.7.8.11 让可视化人工复核台具备更符合普通用户预期的“保存草稿”反馈。页面仍会自动把输入暂存在浏览器本地，但 reviewer 现在可以显式点击保存，并看到上次保存时间或未手动保存的更新提示。该版本只增强本地 UI 反馈，不改变导出 schema、validator、检索、prompt、rerank、anchor、eval case 或 RAG 主流程。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- 静态扫描确认未出现 `fetch(`、`XMLHttpRequest`、`/ask`、`rag_query(`、`ChatOpenAI`。

### v0.4.7.8.12：Manual Review Prescreen Report

阶段定位：在人工复核台正式填写前，增加一层离线预筛建议，帮助非工程 reviewer 先知道哪些 case 最值得优先看、为什么需要看，以及哪些只是检索基建稳定性告警。

解决的问题：36 个待审 case 对非 CS 背景用户仍然信息量过大。此前页面已经能展示案由、证据、标签说明和决策表单，但 reviewer 仍需要逐个 case 判断优先级。本版本把既有 alignment、coverage、rag_eval 和 workbench 信号汇总为预筛报告，给出建议分类、置信度、需要用户拍板原因和普通语言解释。

关键实现：
- 新增 `tools/build_manual_review_prescreen_report.py`。
- 输出 `tests/manual_review_prescreen_report.json` 和 `docs/manual_review_prescreen_report_v0.4.7.8.12.md`。
- 每个 case 包含预筛分类、建议复核结论、置信度、问题、原 LLM 输出摘要、证据快照、主要原因、需用户拍板原因和可读指导。
- 明确区分“主证据/最终证据缺口”与“base retrieval / anchor dependency 检索基建告警”，避免把基建质量信号直接当成原法律结论错误。
- 新增 `tests/test_manual_review_prescreen_report.py`。
- FastAPI 服务版本同步为 `0.4.7.8.12`。

报告写法：
> v0.4.7.8.12 将可视化人工复核台前移了一步：系统不再只把 36 个待审 case 平铺给 reviewer，而是基于既有离线诊断报告生成 prescreen 清单，标出高风险、高置信度和需要人工拍板的案件。该报告只是排序和解释工具，不写入 reviewer decision，也不绕过 importer、diff、validator、promotion dry run 和 closeout。当前预筛显示 36 个 case 中 12 个为 high confidence，32 个仍建议用户拍板，符合“法律风控宁可保守复核，不让工具替人作最终判断”的治理原则。

验证方式：
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_prescreen_report.py src\main.py tests\test_manual_review_prescreen_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_prescreen_report`
- `.\venv\Scripts\python.exe tools\build_manual_review_prescreen_report.py --output tests\manual_review_prescreen_report.json --markdown-output docs\manual_review_prescreen_report_v0.4.7.8.12.md`
- 静态扫描确认工具未调用 `rag_query(`、`ChatOpenAI`、`QdrantClient`、`fetch(`、`XMLHttpRequest` 或 `/ask`。

### v0.4.7.8.13：Manual Review AI Suggestion Isolation

阶段定位：在 prescreen 与 visual workbench 之间增加 AI suggestion isolation，解决 AI 辅助预填容易被误导入为人工决定的问题。

关键实现：
- 新增 `tools/build_manual_review_ai_suggestion_prefill.py`。
- 新增 `tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json`。
- Visual workbench 新增 AI 建议面板、复制建议到草稿、清除建议和人工确认采纳开关。
- Safe suggestion 文件只写 `ai_review_suggestion`，不写 `reviewer_input_template`。
- 导出 JSON/CSV 时只写人工草稿字段，不继承源模板，不导出 AI 来源标记。
- 导出 JSON/CSV 只包含 ready 人工草稿；未确认 AI 复制草稿会被计入 blocked draft，不写入正式 `workbench_items`。
- 重新复制 AI 建议会重置人工确认状态，避免旧确认误覆盖新建议内容。
- 新增可执行前端导出回归，验证未确认 AI copied draft 导出 0、人工确认 ready 后导出 1、重新复制后再次导出 0。
- FastAPI 服务版本同步为 `0.4.7.8.13`。

报告写法：
> v0.4.7.8.13 将 AI 辅助预填从“可导入 reviewer 字段”降级为“只读建议源”。safe suggestion 文件即使被直接喂给 importer，也会因没有人工可导入字段而得到 0 imported、12 rejected，确保 AI 建议不会被误提升为人工复核结论。reviewer 可以把建议复制到本地草稿，但必须人工确认采纳并满足 ready 条件后，才会被写入正式 filled workbench；未确认或缺字段的草稿只保留在本地，不进入导出 `workbench_items`。

验证方式：
- `py_compile tools/build_manual_review_visual_workbench.py tools/build_manual_review_ai_suggestion_prefill.py tests/test_manual_review_ai_suggestion_prefill.py tests/test_manual_review_visual_workbench.py tests/test_manual_review_visual_workbench_build_artifact.py` 通过。
- `tests.test_manual_review_visual_workbench_build_artifact tests.test_manual_review_ai_suggestion_prefill tests.test_manual_review_visual_workbench` 通过，含 AI suggestion export isolation executable regression。
- Safe suggestion build：12 suggestions。
- Import safety check：0 imported，12 rejected，`empty_importable_content=12`。
- Visual workbench build：36 cases，gate `blocked`，`supports_ai_suggestion_isolation=true`，`exports_ready_human_drafts_only=true`。
- 静态扫描确认未出现 RAG、LLM、Qdrant 或后端调用入口。

### v0.4.7.8.14：Manual Review Export Pipeline Dry Run

阶段定位：在 visual workbench 导出之后增加离线 pipeline dry run，预演 filled workbench 是否能安全进入 importer、diff、validator、promotion dry run 和 closeout。

关键实现：
- 新增 `tools/build_manual_review_export_pipeline_dry_run.py`。
- 新增 `tests/manual_review_export_pipeline_dry_run_report.json`。
- 新增隔离中间产物目录 `tests/manual_review_export_pipeline_dry_run_artifacts/`，不覆盖 canonical proposed schema 或正式 pipeline 报告。
- 新增 `tests/test_manual_review_export_pipeline_dry_run.py`。
- 新增 `docs/manual_review_export_pipeline_dry_run_v0.4.7.8.14.md`。
- 新增 `dry_run_blockers`，对 rejected/unknown/duplicate/empty 导入行做保守阻断。
- CLI 输出路径拒绝 canonical pipeline artifact 文件名。
- FastAPI 服务版本同步为 `0.4.7.8.14`。

报告写法：
> v0.4.7.8.14 将“导出后再进入治理链路”固化为可重复 dry run。默认用 AI suggestion 安全稿作为负例，结果为 `blocked_as_expected_ai_suggestion_only`、`0 imported / 12 rejected`、`empty_importable_content=12`、`0 promotion candidates`，closeout gate 保持 `blocked`。单测同时证明，只有真实人工 completed + valid filled workbench 才能通过 importer、diff、validator、promotion dry run 和 closeout，进入 governed action planning dry-run 状态；若输入中夹杂 rejected rows，dry-run 会保守输出 `blocked_input_rejections_require_review`，避免把混合坏行误读为可治理。

验证方式：
- `py_compile tools/build_manual_review_export_pipeline_dry_run.py src/main.py tests/test_manual_review_export_pipeline_dry_run.py` 通过。
- `tests.test_manual_review_export_pipeline_dry_run` 通过，覆盖 AI suggestion 阻断、人工 ready 正向链路、混合坏行阻断和 canonical output denylist。
- `tools/build_manual_review_export_pipeline_dry_run.py` 生成 dry-run report。
- 静态扫描确认未出现 RAG、LLM、Qdrant 或后端调用入口。

### v0.4.7.8.15：Manual Review Pilot Batch

阶段定位：把 36 个待人工复核 case 收束为首批 5 个可读确认包，降低 reviewer 第一次执行人工复核的负担。
关键实现：
- 新增 `tools/build_manual_review_pilot_batch.py`。
- 新增 `tests/manual_review_pilot_batch_report.json`。
- 新增 `tests/test_manual_review_pilot_batch.py`。
- 新增 `docs/manual_review_pilot_batch_v0.4.7.8.15.md`。
- 输出 `schema_kind=advisory_pilot_packet`、`contains_completed_manual_decisions=false`、`advisory_packet_only=true`，并将 AI/预筛结论、根因、后续动作和样本候选字段命名为 advisory，降低被误导入为人工结论的风险。
- FastAPI 服务版本同步为 `0.4.7.8.15`。
报告写法：
> v0.4.7.8.15 将人工复核从“面对 36 个待审 case”收束为首批 5 个 high risk / high confidence case 的 pilot batch。每个 case 均包含案由线索、待审问题、原 LLM 输出摘录、最终证据链、缺失/丢失证据、预筛理由和隔离 AI 参考建议。该报告仍是 advisory packet，不写 `reviewer_input_template`，不生成 completed manual decision、promotion candidate 或 ready action candidate；真实人工填写并通过 export pipeline dry run 前，治理 gate 继续保持 blocked。
验证方式：
- `py_compile tools/build_manual_review_pilot_batch.py src/main.py tests/test_manual_review_pilot_batch.py` 通过。
- `tests.test_manual_review_pilot_batch` 通过，覆盖 3-5 case 选择、AI advisory 隔离、递归安全扫描、无 completed decision、无 promotion/ready action、synthetic case id 选择，以及 pilot packet 被误用为 dry-run 输入时仍被阻断。
- `tools/build_manual_review_pilot_batch.py` 生成 pilot batch report。
- 静态扫描确认未出现 RAG、LLM、Qdrant 或后端调用入口。

### v0.4.7.8.16：Manual Review Pilot Batch Queue

阶段定位：把首批 5 个 pilot case 从独立 JSON/文档推进到离线视觉审阅台内，使 reviewer 可以直接在页面左侧筛选“首批试点”，并在同一“决策”页阅读只读判断清单和填写真实人工结论。
关键实现：
- `tools/build_manual_review_visual_workbench.py` 新增 `--pilot-batch-report`，默认读取 `tests/manual_review_pilot_batch_report.json`。
- Workbench payload 新增 `pilot_batch_report` 与 `pilot_batch` summary，并将匹配到的 pilot case 作为只读 `item.pilot_batch` 附加到现有 workbench item。
- UI 新增“首批试点 / Pilot batch”队列和“首批试点人工判断清单”，展示优先审阅原因、证据摘要、待核对证据、预筛参考、AI advisory 建议和人工判断选项。
- 导出时继续只导出 ready human drafts，并剥离 `pilot_batch` 元数据；清单勾选只作为本地已读标记，不会写入 `reviewer_input_template`。
- 新增 `docs/manual_review_visual_workbench_pilot_batch_v0.4.7.8.16.md`。
- FastAPI 服务版本同步为 `0.4.7.8.16`。
报告写法：
> v0.4.7.8.16 将首批人工复核 pilot batch 接入本地视觉审阅台，新增“首批试点”队列和每案只读判断清单。该清单帮助 reviewer 理解为什么优先看该 case、应核对哪些证据以及预筛/AI 建议如何参考，但不会自动写入人工结论。只有 reviewer 在表单中亲自填写复核人、日期、结论和理由，并满足 ready 条件后，导出文件才会包含 `reviewer_input_template`；只勾选清单或查看 AI 建议不会产生 completed manual decision。
验证方式：
- `py_compile tools/build_manual_review_visual_workbench.py src/main.py tests/test_manual_review_visual_workbench.py tests/test_manual_review_visual_workbench_build_artifact.py tests/test_manual_review_export_pipeline_dry_run.py` 通过。
- `tests.test_manual_review_pilot_batch tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact tests.test_manual_review_export_pipeline_dry_run` 通过。
- `tools/build_manual_review_visual_workbench.py --output tools/manual_review_visual_workbench/index.html --report-output tests/manual_review_visual_workbench_build_report.json` 成功生成静态页面与 build report。
- `tests.test_manual_review_visual_workbench_build_artifact` 通过，包含 JS 可执行回归：pilot checklist-only 不导出人工结论，真实人工 ready draft 才导出。
- 静态扫描确认 workbench、pilot batch 和 export pipeline dry run 工具中未出现 RAG、LLM、Qdrant 或后端调用入口。

### v0.4.7.8.17：Pilot Case Review Assist

阶段定位：在首批 pilot case 正式人工填写前，新增一份只读审阅辅助报告，把“这个案子在问什么、原 LLM 说了什么、最终 evidence_chain 支撑到哪里、哪些证据缺失或流失”用普通中文整理出来，帮助非工程背景 reviewer 更容易判断。
关键实现：
- 新增 `tools/build_manual_review_pilot_case_review_assist.py`。
- 新增 `tests/manual_review_pilot_case_review_assist_report.json`。
- 新增 `tests/test_manual_review_pilot_case_review_assist.py`。
- 新增 `docs/manual_review_pilot_case_review_assist_v0.4.7.8.17.md`。
- 输出 `schema_kind=advisory_pilot_case_review_assist`、`contains_completed_manual_decisions=false`、`advisory_packet_only=true`。
- 支持通用辅助信号：主争点缺证据、案由核心条文缺口、候选证据进入最终证据时流失、答案与证据链可能脱节、定义条款替代规范条款复核、基础检索或 anchor 依赖稳定性复核。
- 报告只保留 `advisory_review_assist` 和 `source_signals`，不输出 `reviewer_input_template`、`reviewer_decision` 或 `workbench_items`。
- FastAPI 服务版本同步为 `0.4.7.8.17`。
报告写法：
> v0.4.7.8.17 为首批 5 个 pilot case 生成只读审阅辅助报告。报告把案由、原 LLM 风险/动作、最终证据链、缺失/流失证据和复核问题清单转成普通中文，并标出需要重点人工确认的 grounding 信号。它仍然不是人工复核结论，不会写入 `reviewer_input_template`，不会生成 completed manual decision、promotion candidate 或 ready action candidate；即使被误作为 export pipeline dry-run 输入，也会保持 `0 imported` 和 gate blocked。真实治理动作仍必须由 reviewer 在视觉审阅台亲自填写并通过 dry run。
验证方式：
- `py_compile tools/build_manual_review_pilot_case_review_assist.py src/main.py tests/test_manual_review_pilot_case_review_assist.py` 通过。
- `tests.test_manual_review_pilot_case_review_assist` 通过，覆盖通用辅助信号、advisory-only 护栏、递归危险键扫描、无 completed decision、无 promotion/ready action，以及 8.17 报告被误用为 dry-run 输入时仍被阻断。
- `tools/build_manual_review_pilot_case_review_assist.py` 成功生成 5 个 case 的 review assist report。
- 相关 manual review 回归测试通过。
- 静态扫描确认该工具未出现 RAG、LLM、Qdrant 或后端调用入口。

### v0.4.7.8.18：可视化人工复核工作台试点审阅辅助

阶段定位：把 pilot case 审阅辅助从独立 JSON 报告接入离线可视化工作台，但保持严格只读和非结论属性。

解决的问题：v0.4.7.8.17 已经能为 5 个 pilot case 生成普通 reviewer 能读懂的审阅辅助，但用户在网页审阅时仍需要在文件和页面之间切换。v0.4.7.8.18 将这些辅助信息放到“决策”页，减少人工理解成本，同时不让辅助信息变成人工结论。

关键实现：
- `tools/build_manual_review_visual_workbench.py` 新增 `--pilot-review-assist-report` 输入。
- 按 `case_id` 将 `tests/manual_review_pilot_case_review_assist_report.json` 投影为只读 `pilot_review_assist` 面板。
- 面板显示案由简述、辅助倾向、证据支撑状态、assist signals、原 LLM 风险/动作摘录、人工核对问题、辅助理由和缺失/流失证据示例。
- 构建 payload 前递归剥离 `reviewer_input_template`、`reviewer_decision`、`workbench_items`、`decision_status`。
- 导出 JSON/CSV 时显式剥离 `pilot_review_assist`，仍只导出 ready human drafts。

报告写法：
> v0.4.7.8.18 将 pilot case 审阅辅助接入离线可视化工作台，使 reviewer 能在同一页面查看“为什么要审、重点审什么、证据链可能缺什么”。该能力只提升人工复核可读性，不生成 completed manual decision，也不绕过 importer、validator、promotion dry run 或 closeout gate。

验证方式：
- py_compile 覆盖 visual workbench、FastAPI 版本和相关单测。
- 单测覆盖只读投影、危险字段剥离、completed-decision 报告拒绝、前端导出不泄漏。
- 重新生成 `tools/manual_review_visual_workbench/index.html` 与 `tests/manual_review_visual_workbench_build_report.json`。
- 静态扫描确认没有 `fetch`、`XMLHttpRequest`、`/ask`、`rag_query`、`ChatOpenAI` 或 `QdrantClient`。

### v0.4.7.8.19：人工复核第一轮试点支持包

阶段定位：进入 5 个 pilot case 的真实人工复核准备阶段，但仍不自动生成结论。

解决的问题：用户需要判断 5 个首批试点案件，但直接看 workbench、pilot batch、assist report 和 RAG eval 信息成本较高。v0.4.7.8.19 将这些材料整理成逐案复核支持包，帮助 reviewer 看懂“案由是什么、原回答说了什么、证据是否支撑、哪些点必须拍板”。

关键实现：
- 新增 `tools/build_pilot_manual_review_round1_support.py`。
- 输出 `tests/pilot_manual_review_round1_support_report.json` 与 `docs/pilot_manual_review_round1_support_v0.4.7.8.19.md`。
- 每案包含案由、原 LLM 输出摘录、风险类型、整改动作、证据状态、辅助信号、缺失/流失证据示例、人工核对问题和人工结论选项解释。
- 报告 schema 明确为 `advisory_pilot_manual_review_round1_support`，不含 completed manual decision。
- 单测验证该报告不能被 export pipeline dry run 导入为人工结论，promotion candidates 和 ready action candidates 均为 0。

报告写法：
> v0.4.7.8.19 标志着项目从“搭建人工复核工具”进入“辅助真实人工复核”的阶段。系统把 5 个 pilot case 的既有诊断材料整理成人可读的逐案复核支持包，但仍坚持不替 reviewer 作出法律判断；真正结论必须由人工在 visual workbench 中填写，并通过 importer、validator、promotion dry run 和 closeout gate。

验证方式：
- py_compile 覆盖新增工具、FastAPI 版本和单测。
- 单测覆盖 advisory-only schema、危险字段缺失、dry-run 不导入、markdown 边界说明。
- 生成默认 JSON/Markdown 报告。
- 静态扫描确认不调用 RAG、后端、Qdrant 或 LLM。

### v0.4.7.8.20：Mobile Pilot Review Decision Aid

阶段定位：适配用户手机远程操作场景，把 5 个 pilot case 压缩成可快速确认的移动端复核卡片。

解决的问题：用户当前不方便在桌面网页中逐项阅读和填写。v0.4.7.8.20 将 v0.4.7.8.19 的逐案复核支持包进一步压缩为每案 5-8 行的手机端确认前草稿，帮助用户快速看案由、原回答、证据缺口、建议倾向和需要确认的问题。

关键实现：
- 新增 `tools/build_mobile_pilot_review_decision_aid.py`。
- 输出 `tests/mobile_pilot_review_decision_aid_report.json` 与 `docs/mobile_pilot_review_decision_aid_v0.4.7.8.20.md`。
- 每案输出 `mobile_advisory_tendency`、`mobile_advisory_root_cause_codes`、`mobile_advisory_follow_up_action_codes`、`mobile_review_lines` 和 `mobile_user_confirmation_required`。
- 避免使用 importer 可识别的人工复核字段名，例如 `decision`、`rationale`、`reviewer_input_template`、`reviewer_decision`。
- 单测验证该报告不能被 dry run 导入为 completed manual review。

报告写法：
> v0.4.7.8.20 面向手机远程审阅场景，将 5 个 pilot case 的复核材料整理为简短卡片，降低用户最后确认的操作成本。该版本仍坚持“AI 只做确认前草稿”，不生成正式人工结论，也不产生 promotion candidate 或 ready action candidate。

验证方式：
- py_compile 覆盖新增工具、FastAPI 版本和单测。
- 单测覆盖移动端 advisory 字段、禁止字段缺失、dry-run 不导入和 Markdown 边界说明。
- 默认生成 JSON/Markdown 报告。
- 静态扫描确认不调用 RAG、后端、Qdrant 或 LLM。

### v0.4.7.8.21：Offline Workbench Authority & Gate Display Clarity

阶段定位：离线人工复核工作台的可用性和治理表达收口。

解决的问题：用户在工作台里看到“试点、辅助、AI、预筛”等材料时，不容易判断正式结论到底听谁的；同时 gate 已经 open 的 5 案清洗链路仍会出现 `0 blocked` 或 blocked queue 一类误导性展示。v0.4.7.8.21 将页面表达收紧为“参考材料只参考，正式结论只听人工填写区”，并修复 open gate 的展示。

关键实现：
- 导出/导入按钮改为 `导出复核记录 JSON`、`下载 CSV`、`导入复核 JSON`。
- pilot batch、AI 预填、证据阅读提示等面板统一使用 `参考：...` 表达。
- “决策”页保留 `听人工填写区` 权威提示，说明参考材料、系统预筛和 AI 参考不会自动导出为结论。
- closeout gate 为 `open` 时显示 `无阻断`，并隐藏 `准入未通过` 队列。
- build report 增加人工权威提示、按钮精简、open gate 无阻断展示、open 时隐藏 blocked queue 等质量信号。

报告写法：
> v0.4.7.8.21 解决了离线人工复核工作台中的“到底听谁的”和“门禁 open 还显示 0 blocked”两类可用性问题。该版本不改变任何 RAG 主流程或人工复核 schema，只让 reviewer 更清楚地区分参考材料与正式人工填写区，并让已开放的 5 案试点治理链路在页面中显示为 `无阻断`。

验证方式：
- py_compile 覆盖 workbench 生成器、FastAPI、health check 和相关测试。
- 单测覆盖 workbench payload、生成 HTML、open gate 显示和 blocked queue 隐藏。
- 重新生成 `tools/manual_review_visual_workbench/index.html` 与 `tests/manual_review_visual_workbench_build_report.json`。
- 编码卫生和 project health check 均通过。

### v0.4.7.8.22：Offline Workbench Global Process Placement

阶段定位：离线人工复核工作台的信息架构修复，降低非系统设计者误读全局流程状态的风险。

解决的问题：原先“后续状态”位于单个案例详情标签中，用户很容易理解为“这个案例自己的后续状态”。实际上该区域展示的是整份复核导出经过 importer、diff、validation、promotion dry run、closeout gate 的整批处理结果。v0.4.7.8.22 将该信息移到左侧栏，并命名为 `整份导出处理结果`，明确它不是当前案例状态。

关键实现：
- 左侧栏新增 `整份导出处理结果` 面板，集中展示导入复核记录、检查变更差异、检查记录完整性、生成待处理动作和是否允许进入后续治理。
- 面板说明写明：`这是本次导出的整份复核 JSON 的处理结果，不代表当前选中的单个案例。`
- 移除案例详情标签里的 `后续状态`，并清理旧的单案例流程渲染入口。
- 顶部副标题改为“查看整份复核导出的处理结果”，避免继续使用容易混淆的“后续准入检查状态”。
- build report 增加并验证 `moves_pipeline_status_to_global_sidebar` 和 `removes_pipeline_from_case_tabs` 两个质量信号。

报告写法：
> v0.4.7.8.22 修复了离线人工复核工作台的流程信息位置问题：整份导出的处理结果不再放在单案例详情标签里，而是移动到左侧 `整份导出处理结果` 面板。该版本不改变 RAG、人工复核 schema 或治理链路，只让 reviewer 更直观地区分“当前案例内容”和“整份导出的处理状态”。

验证方式：
- py_compile 覆盖 workbench 生成器、FastAPI、health check 和相关测试。
- 单测覆盖全局流程面板、旧 `后续状态` 缺失、旧 pipeline case tab 缺失和 open gate `无阻断` 展示。
- 重新生成 `tools/manual_review_visual_workbench/index.html` 与 `tests/manual_review_visual_workbench_build_report.json`。
- 编码卫生和 project health check 均通过。

### v0.4.7.8.23：Offline Workbench Panel Scroll Sync

阶段定位：离线人工复核工作台的布局稳定性修复，解决左侧栏加长后右侧案例队列和详情页不同步的问题。

解决的问题：v0.4.7.8.22 将整份导出的处理结果移动到左侧栏后，左侧内容变长；右侧案例列表和案例详情正文仍容易按旧的视口高度限制表现，用户会看到二级/三级内容区没有跟上整体页面。v0.4.7.8.23 将桌面端收敛为固定高度工作台，让左栏、案例列表和详情正文分别滚动。

关键实现：
- 桌面端 `body` 和 `.app-shell` 固定为视口高度，整页不再被左侧栏撑高。
- 左侧栏设置独立滚动边界，容纳全局流程和操作指南。
- 右侧 `.main`、`.workspace`、`.queue-panel`、`.detail-panel` 使用明确的 `minmax(0, 1fr)` 布局，案例列表和详情正文各自滚动。
- 移除旧的 `calc(100vh - ...)` 高度依赖，避免二级/三级面板和外壳脱节。
- 窄屏端恢复自然纵向布局，保持手机端可读。
- build report 新增 `uses_fixed_height_app_shell`、`keeps_sidebar_scroll_independent`、`restores_natural_mobile_flow`。

报告写法：
> v0.4.7.8.23 修复了离线人工复核工作台的布局同步问题。左侧栏新增全局流程后不再撑高整页，右侧案例队列和案例详情正文也不再按旧高度脱节；桌面端变成左右独立滚动的工作台，移动端继续保持自然纵向浏览。该版本只改离线 UI、测试和文档，不改变 RAG、人工复核 schema、导入治理链路或任何复核结论。

验证方式：
- py_compile 覆盖 workbench 生成器、FastAPI、health check 和相关测试。
- 单测覆盖固定工作台外壳、左侧栏独立滚动、右侧二级/三级面板独立滚动、旧 `calc(100vh - ...)` 限制缺失和窄屏自然流。
- 重新生成 `tools/manual_review_visual_workbench/index.html` 与 `tests/manual_review_visual_workbench_build_report.json`。
- manual review/workbench/export pipeline 相关回归、编码卫生和 project health check 均通过。

### v0.4.7.9.0：Ready Action Design Pack

阶段定位：从“首批 5 案人工复核链路跑通”进入“受治理工程设计评审”阶段，但仍不实施 RAG 修改。

解决的问题：v0.4.7.8.x 已经让 5 个清洗后的 pilot case 通过 importer、validator、promotion dry run 和 closeout gate，形成 18 个 ready action candidates。直接把这些候选动作写成代码修改会过早、也容易把 31 个 pending cases 混进工程任务。v0.4.7.9.0 将 18 个候选动作整理为可审议的设计包，明确哪些轨道可以进入设计评审，哪些边界仍然禁止触碰。

关键实现：
- 新增 `tools/build_ready_action_design_pack.py`。
- 输出 `tests/ready_action_design_pack_report.json` 与 `docs/ready_action_design_pack_v0.4.7.9.0.md`。
- 报告按 5 条设计轨道组织：final evidence selection policy、primary evidence fixture candidate、scenario registry core article、high-risk manual grounding、functional typing fixture。
- `planning_gate` 明确 `open_for_design_review`，但 `implementation_allowed=false`、`code_patch_authorized=false`。
- 31 个 pending records 只作为 excluded scope 背景统计，不进入设计任务。

报告写法：
> v0.4.7.9.0 将已通过人工复核治理链路的 5 个 pilot case 和 18 个 ready actions 整理成 Ready Action Design Pack。该版本的意义不是“已经修好 RAG”，而是把人工确认的问题转化为可追溯、可审议、可测试计划化的工程设计输入。设计包只开放 design review，不授权修改 hidden seed、anchor、rerank、prompt、risk supplement、scenario registry、eval case 或 RAG 主流程。

验证方式：
- py_compile 覆盖新增工具、health check、FastAPI 版本和相关单测。
- 单测覆盖真实 5/18/31 报告基线、5 类 action group、blocked gate 阻断、traceability 保留和禁止自动实施。
- 默认生成 JSON/Markdown 设计包。
- 编码卫生、索引一致性和 project health check 作为收尾检查。

### v0.4.7.9.1：Ready Action Design Review Brief

阶段定位：从“受治理工程设计包”进入“人工可审的设计评审简报”阶段，仍不实施 RAG 修改。

解决的问题：v0.4.7.9.0 已经把 5 个 pilot case / 18 个 ready action candidates 整理成设计包，但其中的 action type、planning gate、fixture、grounding 等术语对非系统设计者不够直观。v0.4.7.9.1 将这些材料改写成评审顺序、问题清单、进入/退出标准、禁止项和后续验证要求，让人工评审能先判断方向是否成立，再决定是否另开实现版本。

关键实现：
- 新增 `tools/build_ready_action_design_review_brief.py`。
- 输出 `tests/ready_action_design_review_brief_report.json` 与 `docs/ready_action_design_review_brief_v0.4.7.9.1.md`。
- 固定评审顺序：final evidence selection policy、primary evidence fixture candidate、high-risk manual grounding、scenario registry core article、functional typing fixture。
- 继续保持 `implementation_allowed=false`、`code_patch_authorized=false`、`implementation_requires_future_explicit_approval=true`。
- 31 个 pending records 只作为背景统计，不进入评审方向或任务清单。

报告写法：
> v0.4.7.9.1 将 Ready Action Design Pack 改写成面向人工审议的 Design Review Brief。该版本的意义不是“开始修 RAG”，而是让每条设计方向的评审问题、准入标准、退出标准和禁止项更清楚。它只读取既有设计包，不改 hidden seed、anchor、rerank、prompt、risk supplement、scenario registry、eval case、fixture 或 RAG 主流程。

验证方式：
- py_compile 覆盖新增工具、health check、FastAPI 版本和相关单测。
- 单测覆盖真实 5/18/31 报告基线、P0/P1 排序、traceability、blocked source pack、防 pending 任务化和 no implementation authorization。
- 默认生成 JSON/Markdown 简报。
- 编码卫生、索引一致性和 project health check 作为收尾检查。

### v0.4.7.9.2：Ready Action Design Review Gate

阶段定位：从“人工可审的设计评审简报”进入“实施前门禁确认”阶段，仍不实施 RAG 修改。

解决的问题：v0.4.7.9.1 已经把 5 条设计方向整理成人工评审简报，但如果没有单独 gate，后续维护者容易把“可以评审”误读成“可以开始改代码”。v0.4.7.9.2 新增只读门禁，专门确认该简报只能用于人工设计评审，并继续阻断 implementation approval。

关键实现：
- 新增 `tools/check_ready_action_design_review_gate.py`。
- 输出 `tests/ready_action_design_review_gate_report.json` 与 `docs/ready_action_design_review_gate_v0.4.7.9.2.md`。
- 检查 source brief 版本、schema、brief gate、assertions、traceability、review order 和 guardrails。
- gate open 时只输出 `open_for_human_design_review_only` 与 `human_design_review_discussion_only`。
- 继续保持 `implementation_allowed=false`、`code_patch_authorized=false`、`handoff_to_implementation=not_allowed`。
- source brief 中一旦出现实现授权、advisory/AI 信号、pending/backlog/task 化信号或 guardrail 漂移，gate 会保守阻断。

报告写法：
> v0.4.7.9.2 为 Ready Action Design Review Brief 增加实施前门禁。它的意义不是“开始修 RAG”，而是把“可以开人工设计评审会”和“可以写代码实现”明确拆开：当前只允许讨论 5 条设计方向，不允许修改 hidden seed、anchor、rerank、prompt、risk supplement、scenario registry、eval case、fixture 或 RAG 主流程。

验证方式：
- py_compile 覆盖新增 gate、health check、FastAPI 版本和相关单测。
- 单测覆盖真实 5/18/31 基线、wrong schema、blocked brief、source assertion failure、implementation authorization、pending/advisory signals、traceability drift、guardrail mismatch 和禁止运行时/后端模式。
- 默认生成 JSON/Markdown gate 报告。
- 编码卫生、索引一致性和 project health check 作为收尾检查。

### v0.4.7.9.3：Ready Action Design Review Worksheet

阶段定位：从“实施前门禁确认”进入“人工设计复核会议材料”阶段，仍不实施 RAG 修改。

解决的问题：v0.4.7.9.2 已经确认设计评审 gate 可以打开，但 gate 报告偏门禁语义，不适合直接作为人工评审会材料。v0.4.7.9.3 将 gate 与 brief 合并成 decision matrix / worksheet，让 reviewer 可以按 5 条轨道逐项讨论优先级、核心问题、后续可能系列和当前禁止项，同时避免把讨论材料误读为 implementation approval。

关键实现：
- 新增 `tools/build_ready_action_design_review_worksheet.py`。
- 输出 `tests/ready_action_design_review_worksheet_report.json` 与 `docs/ready_action_design_review_worksheet_v0.4.7.9.3.md`。
- 决策矩阵固定 5 条评审轨道：final evidence selection policy、primary evidence fixture candidate、high-risk manual grounding、scenario registry core article、functional typing fixture。
- 继续保持 `implementation_allowed=false`、`code_patch_authorized=false`、`handoff_to_implementation=not_allowed`、`captures_formal_review_outcome=false`。
- 对 gate/brief schema、版本、数量、顺序、traceability、advisory/forbidden keys 和文本可读性做保守检查。

报告写法：
> v0.4.7.9.3 将设计评审 gate 和 brief 转换为人工复核会可直接使用的 decision matrix。该版本不是 RAG 修复，也不是实现授权；它的作用是帮助团队判断 5 条设计方向下一步应进入哪类设计讨论，并继续禁止修改 hidden seed、anchor、rerank、prompt、risk supplement、scenario registry、eval case、fixture 或 RAG 主流程。

验证方式：
- py_compile 覆盖 worksheet 工具、health check、FastAPI 版本和相关单测。
- 单测覆盖真实 5/18/31 基线、source gate/brief contract、implementation authorization 阻断、数量/顺序漂移、path mismatch、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown worksheet。
- 编码卫生、索引一致性和 project health check 作为收尾检查。

### v0.4.7.9.4：Ready Action Design Review Closeout Envelope

阶段定位：从“人工设计复核会议材料”进入“待人工收口确认”阶段，仍不实施 RAG 修改。

解决的问题：v0.4.7.9.3 已经提供 decision matrix，但 matrix 本身仍偏讨论材料。v0.4.7.9.4 将 5 条设计轨道进一步整理为 closeout envelope：每条轨道列出候选分流、收口问题、最小人工依据和可选收口口径，但默认仍为 `pending_human_closeout`，不替 reviewer 作出正式结论。

关键实现：
- 新增 `tools/build_ready_action_design_review_closeout.py`。
- 输出 `tests/ready_action_design_review_closeout_report.json` 与 `docs/ready_action_design_review_closeout_v0.4.7.9.4.md`。
- 固定 5 条 closeout rows，并保留 18 个 design actions、5 个 source cases、31 个 pending records excluded。
- 每条轨道保持 `formal_human_outcome_recorded=false`、`candidate_route_authorized=false`、`implementation_allowed=false`。
- 对 source worksheet 的 schema、版本、数量、顺序、traceability、advisory/forbidden keys 和文本可读性做保守检查。

报告写法：
> v0.4.7.9.4 将 design review worksheet 转成 closeout envelope，帮助人工评审会逐条确认 5 个设计方向是否继续、暂缓、需要法律/fixture 范围复核或等待更多案例。该版本仍不是 RAG 修复，也不是实现授权；所有候选分流都必须等待后续人工收口和独立版本计划。

验证方式：
- py_compile 覆盖 closeout 工具、health check、FastAPI 版本和相关单测。
- 单测覆盖真实 5/18/31 基线、source worksheet contract、implementation authorization 阻断、数量/顺序漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown closeout envelope。
- 编码卫生、索引一致性和 project health check 作为收尾检查。

### v0.4.7.9.5：Ready Action Human Closeout Decision Draft

阶段定位：从“待人工收口确认”进入“待用户确认的收口草案”阶段，仍不实施 RAG 修改。

解决的问题：v0.4.7.9.4 已经列出 5 条设计轨道的候选分流和最小人工依据，但用户仍需要一份更直接的草案来确认或修改。v0.4.7.9.5 将 closeout envelope 转成 draft matrix：每条轨道给出建议方向、建议理由、需要用户确认的问题和候选后续，但明确不是正式人工结论，也不能导入 importer。

关键实现：
- 新增 `tools/build_ready_action_human_closeout_decision_draft.py`。
- 输出 `tests/ready_action_human_closeout_decision_draft_report.json` 与 `docs/ready_action_human_closeout_decision_draft_v0.4.7.9.5.md`。
- 固定 5 条 draft rows，并保留 18 个 design actions、5 个 source cases、31 个 pending records excluded。
- 每条轨道保持 `requires_user_confirmation=true`、`formal_human_outcome_recorded=false`、`draft_is_importable_decision=false`、`implementation_allowed=false`。
- 对 source closeout 的 schema、版本、数量、顺序、traceability、正式结论/授权字段、advisory/forbidden keys 和文本可读性做保守检查。

报告写法：
> v0.4.7.9.5 将 closeout envelope 转换为待用户确认的人工收口草案，帮助 reviewer 快速确认 5 条设计方向下一步是否继续、复核、暂缓或关闭。该版本仍不是正式人工结论，不可导入 manual review importer，也不授权修改 RAG、配置、样例或主流程。

验证方式：
- py_compile 覆盖 draft 工具、health check、FastAPI 版本和相关单测。
- 单测覆盖真实 5/18/31 基线、source closeout contract、formal outcome/implementation authorization 阻断、数量/顺序漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown decision draft。
- 编码卫生、索引一致性和 project health check 作为收尾检查。

### v0.4.7.9.6：Ready Action Human Closeout Confirmation Record

阶段定位：从“待用户确认的收口草案”进入“已确认的设计收口方向记录”阶段，仍不实施 RAG 修改。

解决的问题：v0.4.7.9.5 已经形成待用户确认的 5 条草案方向。v0.4.7.9.6 将用户确认固化成可追溯记录，用于后续设计规划排序，但继续把它和 manual review importer 的 completed decision、工程任务、实现授权严格区分。

关键实现：
- 新增 `tools/build_ready_action_human_closeout_confirmation_record.py`。
- 输出 `tests/ready_action_human_closeout_confirmation_record_report.json` 与 `docs/ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md`。
- 固定 5 条 confirmation rows，并保留 18 个 design actions、5 个 source cases、31 个 pending records excluded。
- 每条轨道保持 `manual_review_importable=false`、`not_completed_manual_review_decision=true`、`implementation_allowed=false`。
- 对 source draft 的 schema、版本、数量、顺序、traceability、importer/正式复核字段、advisory/forbidden keys 和文本可读性做保守检查。

报告写法：
> v0.4.7.9.6 将用户对 5 条设计方向的确认转化为可追溯的 design closeout confirmation record。该记录只允许作为未来设计规划输入，不是 manual review importer 的 completed decision，也不授权修改 RAG、配置、样例、scenario registry 或主流程。

验证方式：
- py_compile 覆盖 confirmation 工具、health check、FastAPI 版本和相关单测。
- 单测覆盖真实 5/18/31 基线、source draft contract、formal outcome/importer/implementation authorization 阻断、数量/顺序漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown confirmation record。
- 编码卫生、索引一致性和 project health check 作为收尾检查。

### v0.4.7.9.7：Future Version Ordering Correction

阶段定位：路线图维护修正，不新增 RAG 能力，也不实施策略。

解决的问题：此前部分报告和 dry-run 路由把 v0.4.8.x / v0.4.9.x 的后续系列含义写反。v0.4.7.9.7 将未来顺序统一为：v0.4.8.x 先做最终证据选择策略设计；v0.4.9.x 再做 Retrieval Input Quality Governance。

关键实现：
- 修正 ready-action routing dry-run 与 9.3-9.6 设计收口链路中的后续系列标签。
- 重新生成 worksheet、closeout、decision draft 和 confirmation record 的 JSON/Markdown。
- 更新 roadmap、changelog、FastAPI 与 health check 版本。
- 增加 routing dry-run 单测，防止未来再次把两个系列互换。

报告写法：
> v0.4.7.9.7 是未来版本顺序修正：它只统一路线编号和生成产物，不改变 RAG 主流程、rerank、prompt、scenario registry、eval case 或任何人工复核结论。

验证方式：
- py_compile 覆盖受影响工具、health check、FastAPI 和相关单测。
- 单测覆盖 routing dry-run、9.3-9.6 设计收口链路和 project health。
- 重新生成受影响报告与 Markdown。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 收尾。

### v0.4.8.0：Final Evidence Selection Policy Design Intake

阶段定位：正式进入 v0.4.8.x 最终证据选择策略设计系列，但第一步只做设计输入，不实现策略。

解决的问题：v0.4.7.9.6/9.7 已确认最终证据选择是下一步优先方向，但直接改 rerank 或 final selection runtime 风险过高。v0.4.8.0 将 confirmation record、design pack 和 final selection audit 中的已确认信号整理成 policy intake，作为后续 simulator 和策略草案的输入。

关键输出：
- 新增 `tools/build_final_evidence_selection_policy_intake.py`。
- 输出 `tests/final_evidence_selection_policy_intake_report.json` 与 `docs/final_evidence_selection_policy_intake_v0.4.8.0.md`。
- 固定 5 个 confirmed final selection cases，并对齐 final selection audit 的 high-priority review cases。
- 输出 6 条 policy questions 与 6 条 preservation discussion items：主证据、义务/行为规则、程序、责任、场景核心、final coverage floor。
- 规划 v0.4.8.1 simulator，但限定为 saved reports only，不接主流程。

报告写法：
> v0.4.8.0 是最终证据选择策略设计的 intake 版本。它把人工确认的 final evidence selection loss 和既有审计信号转化为可审议的 policy questions、preservation discussion items 和 simulator 计划；该版本不修改 rerank、不实现 runtime policy、不改 eval case，也不接入 RAG 主流程。

验证方式：
- py_compile 覆盖 intake 工具、health check、FastAPI 版本和相关单测。
- 单测覆盖真实报告构建、源报告/audit 漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown intake。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.1：Final Evidence Selection Policy Simulator Spec

阶段定位：在 v0.4.8.0 policy intake 之后，定义最终证据选择策略模拟器的离线契约和质量信号，而不是实现 runtime policy。

解决的问题：已有 intake 能说明哪些 final evidence selection loss 需要策略讨论，但直接进入 rerank 或 runtime selection patch 风险仍过高。v0.4.8.1 将下一步收束为 saved-report simulator spec：明确模拟器只能读取已保存报告，输出可审阅的 preservation、coverage floor、definition-only substitution 和 manual-review-required 信号。

关键输出：
- 新增 `tools/build_final_evidence_selection_policy_simulator_spec.py`。
- 输出 `tests/final_evidence_selection_policy_simulator_spec_report.json` 与 `docs/final_evidence_selection_policy_simulator_spec_v0.4.8.1.md`。
- 定义 input contract：v0.4.8.0 intake、final evidence selection audit、human closeout confirmation record。
- 定义 output contract：case-level simulation result、quality signals、manual review list、traceability 和 assertions。
- 定义 6 类 policy candidate categories：primary、operative、procedural、liability、scenario_core、definition_only。
- 定义 8 类 failure/manual-review signals，并将 5 个 high-risk cases 标记为 policy draft 前需人工复核。

报告写法：
> v0.4.8.1 把最终证据选择策略设计推进到 saved-report policy simulator spec。它只定义离线模拟器应如何读取既有治理报告、产生 preservation 与质量信号，并识别需要人工复核或阻断的情形；该版本不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。

验证方式：
- py_compile 覆盖 simulator spec 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源报告漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown spec。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.2：Final Evidence Selection Policy Table Draft

阶段定位：在 v0.4.8.1 saved-report simulator spec 之后，将最终证据选择质量信号整理成可人工审阅的策略表草案，而不是实现 runtime policy。

解决的问题：v0.4.8.1 已经定义了 preservation、coverage floor、definition-only substitution 和 manual-review-required 信号，但这些信号仍偏契约层。v0.4.8.2 将它们转成 8 条 policy table rows，让非实现阶段也能审阅“触发条件、保留要求、可接受替代、何时必须人工复核、覆盖下限和定义条款防线”。

关键输出：
- 新增 `tools/build_final_evidence_selection_policy_table_draft.py`。
- 输出 `tests/final_evidence_selection_policy_table_draft_report.json` 与 `docs/final_evidence_selection_policy_table_draft_v0.4.8.2.md`。
- 定义 8 条 draft policy rows：primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor、high_risk_manual_review。
- 每条 policy row 固定 `policy_status=draft_for_manual_review`、`runtime_adoption_status=not_allowed`、`implementation_allowed=false`。
- 保留 5 个 high-risk cases 的 manual review gate，继续阻断未经复核的 runtime adoption。

报告写法：
> v0.4.8.2 将最终证据选择策略设计推进到人工可审阅的 policy table draft。它基于已保存 simulator spec，把主证据保留、规范条款保留、程序/责任证据保留、场景核心、定义条款替代、coverage floor 和 high-risk manual review 规则整理为 8 条草案行；该版本不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。

验证方式：
- py_compile 覆盖 policy table draft 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源报告漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown policy table draft。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.3：Final Evidence Selection Policy Human Review Worksheet

阶段定位：在 v0.4.8.2 policy table draft 之后，将 8 条最终证据选择策略草案整理为人工复核 worksheet；仍不实现 runtime policy。
解决的问题：v0.4.8.2 已经形成 policy table rows，但 reviewer 仍需要逐条判断“该规则是否表达了正确的证据保留要求、可接受替代是否过宽、是否应进入后续 closeout”。v0.4.8.3 把每条 policy row 转成 review goal、review questions、acceptance checks 和 discussion options，让策略复核先完成治理收口，而不是直接改 rerank 或 final selection runtime。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_human_review_worksheet.py`。
- 输出 `tests/final_evidence_selection_policy_human_review_worksheet_report.json` 与 `docs/final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md`。
- 生成 8 条 review worksheet rows，对齐 primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor 和 high_risk_manual_review。
- 每条 review row 固定 `implementation_allowed=false`、`code_patch_authorized=false`、`runtime_adoption_status=not_allowed`、`captures_formal_review_outcome=false`。
- 保留 5 个 source case 的 traceability，但不记录正式人工结论，不生成工程任务。
报告写法：
> v0.4.8.3 将最终证据选择策略表草案推进为人工复核 worksheet。它只读取 v0.4.8.2 saved report，把 8 条 policy rows 转成 reviewer 可逐条审议的问题、验收检查点和讨论选项；该版本不记录 formal review outcome，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 worksheet 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源报告漂移、实现授权漂移、policy row 顺序/数量漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown human review worksheet。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.4：Final Evidence Selection Policy Closeout Envelope

阶段定位：在 v0.4.8.3 human review worksheet 之后，把 8 条最终证据选择策略 review rows 整理成待人工收口的 closeout envelope；仍不记录正式人工结论，不授权实现。

解决的问题：v0.4.8.3 已经形成 reviewer 可逐条审议的问题和验收检查点，但还缺少一个可追溯的“收口讨论外壳”。v0.4.8.4 将每条 review row 转成 closeout row，补齐 closeout question、minimum human basis、candidate route 和 recommended closeout option，让下一步可以形成 v0.4.8.5 decision draft，而不是直接改 rerank 或 final selection runtime。

关键输出：
- 新增 `tools/build_final_evidence_selection_policy_closeout_envelope.py`。
- 输出 `tests/final_evidence_selection_policy_closeout_envelope_report.json` 与 `docs/final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md`。
- 生成 8 条 closeout rows，对齐 primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor 和 high_risk_manual_review。
- 每条 closeout row 固定 `pending_human_closeout`、`formal_human_outcome_recorded=false`、`candidate_route_authorized=false`、`implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
- 保留 5 个 source case 的 traceability，但不记录正式人工结论，不生成工程任务。

报告写法：
> v0.4.8.4 将最终证据选择策略人工复核 worksheet 推进为 closeout envelope。它只读取 v0.4.8.3 saved report，把 8 条 review rows 转成待人工收口的候选路径、最小人工依据和收口选项；该版本不记录 formal review outcome，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。

验证方式：
- py_compile 覆盖 closeout envelope 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源报告漂移、正式结论/实现授权泄漏、row 数量/顺序漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown closeout envelope。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.5：Final Evidence Selection Policy Closeout Decision Draft

阶段定位：在 v0.4.8.4 closeout envelope 之后，把 8 条 pending closeout rows 转成待用户确认的收口决策草案；仍不记录正式人工结论，不授权实现。

解决的问题：v0.4.8.4 已经形成 closeout question、minimum human basis 和 recommended closeout option，但这些仍是讨论外壳。v0.4.8.5 将每条 pending closeout row 转成 user-confirmation draft row，明确 suggested closeout option、confirmation question、required basis 和 draft next step，让下一步可以形成 v0.4.8.6 confirmation record，而不是直接改 rerank 或 final selection runtime。

关键输出：
- 新增 `tools/build_final_evidence_selection_policy_closeout_decision_draft.py`。
- 输出 `tests/final_evidence_selection_policy_closeout_decision_draft_report.json` 与 `docs/final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md`。
- 生成 8 条 decision draft rows，对齐 primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor 和 high_risk_manual_review。
- 每条 draft row 固定 `requires_user_confirmation=true`、`formal_human_outcome_recorded=false`、`draft_is_importable_decision=false`、`candidate_route_authorized=false`、`implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
- 保留 5 个 source case 的 traceability，但不记录正式人工结论，不生成工程任务。

报告写法：
> v0.4.8.5 将最终证据选择策略 closeout envelope 推进为用户确认草案。它只读取 v0.4.8.4 saved report，把 8 条 pending closeout rows 转成 suggested closeout option、confirmation question、required basis 和 draft next step；该版本不记录 formal review outcome，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。

验证方式：
- py_compile 覆盖 closeout decision draft 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源报告漂移、正式结论/实现授权泄漏、row 数量/顺序漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown closeout decision draft。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.6：Final Evidence Selection Policy Closeout Confirmation Record Scaffold

阶段定位：在 v0.4.8.5 closeout decision draft 之后，生成待用户确认的收口确认记录脚手架；本版本不伪造用户确认，不记录正式人工结论，也不授权任何实现。
解决的问题：v0.4.8.5 已把 8 条收口草稿整理成 suggested closeout options，但系统还缺一个可审计的“等待用户确认”记录容器。v0.4.8.6 固定 8 条 `pending_user_confirmation` 脚手架行，把可选确认项、空确认字段和禁止实现边界放在同一份 saved report 中，避免后续把草稿误读为已确认结论。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_closeout_confirmation_record.py`。
- 输出 `tests/final_evidence_selection_policy_closeout_confirmation_record_report.json` 与 `docs/final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md`。
- 生成 8 条 confirmation scaffold rows，对齐 primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor 和 high_risk_manual_review。
- 每条 row 固定 `confirmation_status=pending_user_confirmation`、`user_confirmation_recorded=false`、`formal_human_outcome_recorded=false`、`implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
- 保留 5 个 source case traceability，但不记录正式确认选项，不生成工程任务。
报告写法：
> v0.4.8.6 将最终证据选择策略收口草稿推进为“待用户确认记录脚手架”。它只读取 v0.4.8.5 saved report，并为 8 条策略收口项生成 pending confirmation rows；该版本没有记录用户确认结果，没有形成 formal review outcome，也没有授权 runtime policy、rerank、prompt、eval case 或 RAG 主流程修改。
验证方式：
- py_compile 覆盖 confirmation record 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源草稿漂移、正式结论/实现授权污染、row 数量/顺序漂移、advisory/forbidden keys、可读性、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown confirmation scaffold。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。
### v0.4.8.7：Final Evidence Selection Policy Closeout Confirmed Record

阶段定位：在 v0.4.8.6 confirmation scaffold 之后，记录用户对 8 条 suggested closeout options 的明确确认；本版本只作为后续离线设计规划输入，不授权任何 runtime 或代码实现。
解决的问题：v0.4.8.6 已形成 8 条 `pending_user_confirmation` 脚手架行，但不能作为正式确认。v0.4.8.7 将用户确认文本“确认以上 8 条，按 suggested closeout option 生成 v0.4.8.7。”写入 `confirmation_context`，并把每条 row 的 `suggested_closeout_option` 固化为 `confirmed_closeout_option`，从而形成可追溯的策略收口确认记录。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_closeout_confirmed_record.py`。
- 输出 `tests/final_evidence_selection_policy_closeout_confirmed_record_report.json` 与 `docs/final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md`。
- 生成 8 条 confirmed rows，对齐 primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor 和 high_risk_manual_review。
- 5 条进入 `future_offline_simulation_design_candidate`，3 条进入 `policy_language_revision_required_before_simulation`。
- 所有 row 继续固定 `implementation_allowed=false`、`code_patch_authorized=false`、`candidate_route_authorized=false` 和 `runtime_adoption_status=not_allowed`。
报告写法：
> v0.4.8.7 将最终证据选择策略收口脚手架转成正式用户确认记录。它只读取 v0.4.8.6 saved report，并按用户明确确认把 8 条 suggested closeout options 写为 confirmed closeout options；该版本只允许作为后续离线设计规划输入，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 confirmed record 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源脚手架漂移、已确认/实现授权污染、row 数量/顺序/建议项漂移、advisory/forbidden keys、可读性、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown confirmed record。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。
### v0.4.8.8：Final Evidence Selection Policy Language Revision Worksheet

阶段定位：在 v0.4.8.7 confirmed record 之后，专门处理 `liability`、`scenario_core`、`coverage_floor` 三条被确认需要先修订语言的策略行；本版本只生成离线 worksheet，不形成最终 wording，也不授权任何实现。
解决的问题：v0.4.8.7 已确认 8 条 closeout options，其中 5 条可进入后续离线模拟设计，3 条仍需先收窄 policy language。v0.4.8.8 将这 3 条拆成语言修订工作表，明确 wording risk、target boundary、acceptance checks、review questions 和 simulation entry condition，避免把过宽规则直接带入 simulator。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_language_revision_worksheet.py`。
- 输出 `tests/final_evidence_selection_policy_language_revision_worksheet_report.json` 与 `docs/final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md`。
- 生成 3 条 revision worksheet rows：`liability`、`scenario_core`、`coverage_floor`。
- 明确 5 条已确认可进入 offline simulation design 的 category 仍需等待这 3 条语言修订收口后再合并规划。
- 所有 row 继续固定 `implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
报告写法：
> v0.4.8.8 将最终证据选择策略中的三条语言债拆成离线 revision worksheet。它只读取 v0.4.8.7 saved report，为 liability、scenario_core、coverage_floor 分别给出 wording risk、target boundary 和 simulation entry condition；该版本不形成最终 policy wording，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 language revision worksheet 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源确认记录漂移、实现授权污染、revision row 数量/顺序漂移、advisory/forbidden keys、可读性、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown language revision worksheet。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.9：Final Evidence Selection Policy Language Revision Closeout Draft

阶段定位：在 v0.4.8.8 language revision worksheet 之后，将 `liability`、`scenario_core`、`coverage_floor` 三条语言债推进为待用户确认的 narrowed wording 草案；本版本仍不形成最终 policy wording，也不授权任何实现。
解决的问题：v0.4.8.8 已经指出三条策略行的 wording risk、target boundary 和 simulation entry condition，但还不能直接进入 offline simulation design。v0.4.8.9 为每条 row 给出 suggested wording、must-not-mean、acceptance boundary、confirmation question 和 post-confirmation route，方便下一步由用户明确确认或继续修订。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py`。
- 输出 `tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json` 与 `docs/final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md`。
- 生成 3 条 pending user confirmation draft rows：`liability`、`scenario_core`、`coverage_floor`。
- 明确 offline simulation design 仍需等待用户确认语言收口，`next_version_handoff.may_enter_offline_simulation_design=false`。
- 所有 draft rows 继续固定 `implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
报告写法：
> v0.4.8.9 将最终证据选择策略中的三条语言债从 worksheet 推进为待用户确认的 closeout draft。它只读取 v0.4.8.8 saved report，为 liability、scenario_core、coverage_floor 分别给出 suggested wording、must-not-mean 和 confirmation question；该版本不记录最终 policy wording，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 language revision closeout draft 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源 worksheet 漂移、实现授权污染、revision row 数量/顺序漂移、缺失语言字段、advisory/forbidden keys、可读性、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown language revision closeout draft。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.10：Final Evidence Selection Policy Language Revision Confirmation Record

阶段定位：在 v0.4.8.9 language revision closeout draft 之后，记录用户对 `liability`、`scenario_core`、`coverage_floor` 三条 narrowed wording 的明确确认；confirmed wording 只作为后续 offline simulation design 输入，不授权 runtime 或代码实现。
解决的问题：v0.4.8.9 已形成 3 条待确认 suggested wording，但仍不能作为已确认策略语言。v0.4.8.10 将用户确认文本“确认以上三条。”写入 confirmation context，并把三条草案固化为 `confirmed_policy_wording`、`confirmed_must_not_mean` 和 `confirmed_acceptance_boundary`，为后续离线模拟设计提供可追溯输入。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py`。
- 输出 `tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json` 与 `docs/final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md`。
- 生成 3 条 confirmed rows：`liability`、`scenario_core`、`coverage_floor`。
- `offline_simulation_design_handoff.handoff_status=ready_for_future_offline_simulation_design`，但仍要求另开版本才能进入 simulation 或 runtime 工作。
- 所有 confirmed rows 继续固定 `implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
报告写法：
> v0.4.8.10 将最终证据选择策略三条语言债的用户确认固化为离线 confirmation record。它只读取 v0.4.8.9 saved report，并按用户“确认以上三条。”把 liability、scenario_core、coverage_floor 的 suggested wording 写为 confirmed wording；该版本只允许作为后续 offline simulation design 输入，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 language revision confirmation record 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源 draft 漂移、实现授权污染、row 数量/顺序漂移、缺失语言字段、advisory/forbidden keys、可读性、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown language revision confirmation record。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.11：Final Evidence Selection Policy Offline Simulation Input Contract

阶段定位：在 v0.4.8.10 language confirmation record 之后，将 v0.4.8.7 已接受的 5 条 policy category 与 v0.4.8.10 已确认的 3 条 wording 合并为后续 saved-report offline simulation 的输入契约；本版本不运行模拟、不授权实现。
解决的问题：前序版本已经完成 policy closeout 与 language confirmation，但后续模拟器不能直接从多个来源自由拼接输入。v0.4.8.11 固定 8 条 simulation input rows 的来源、顺序、wording 状态和边界，避免后续模拟阶段误读未确认材料。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py`。
- 输出 `tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json` 与 `docs/final_evidence_selection_policy_offline_simulation_input_contract_v0.4.8.11.md`。
- 生成 8 条 contract rows：primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor、high_risk_manual_review。
- 明确 `simulation_not_run=true`，本版本只准备输入契约。
报告写法：
> v0.4.8.11 将最终证据选择策略的已确认材料合并为 saved-report offline simulation input contract。它只读取 v0.4.8.7 和 v0.4.8.10 saved reports，形成 8 条有序 policy rows；该版本不运行 simulation，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 input contract 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实报告构建、源报告漂移、category 顺序漂移、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown input contract。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.12：Final Evidence Selection Policy Offline Simulation

阶段定位：在 v0.4.8.11 input contract 之后，运行 saved-report-only offline simulation runner，验证 8 条已确认 policy category 是否能形成稳定的离线模拟信号；本版本仍不进入 runtime implementation。
解决的问题：前序版本已经把输入契约固定，但还没有模拟结果记录。v0.4.8.12 只读取该契约，生成 8 条 simulation result rows，明确 0 个 blocking failure 与 2 个 manual-review signals，为下一步 simulation result gate 提供输入。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_offline_simulation.py`。
- 输出 `tests/final_evidence_selection_policy_offline_simulation_report.json` 与 `docs/final_evidence_selection_policy_offline_simulation_v0.4.8.12.md`。
- 生成 8 条 simulation result rows：primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor、high_risk_manual_review。
- 明确 `blocking_failure_count=0`、`manual_review_signal_count=2`，且仍保持 `implementation_allowed=false`。
报告写法：
> v0.4.8.12 将最终证据选择策略输入契约推进到 saved-report offline simulation。它只读取 v0.4.8.11 saved report，生成 8 条 deterministic simulation result rows；该版本不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 offline simulation 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实 contract 模拟、blocked contract、category 顺序漂移、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown offline simulation report。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.13：Final Evidence Selection Policy Offline Simulation Gate

阶段定位：在 v0.4.8.12 offline simulation 之后，新增 saved-report-only result gate，确认模拟结果完整、顺序稳定、无 blocking failure，并继续阻断 runtime adoption。
解决的问题：v0.4.8.12 已生成 simulation result rows，但还缺少发布前门禁来判断这些结果能否进入 adoption decision draft。v0.4.8.13 固化 12 项检查，避免把格式漂移、字段缺失或实现授权污染带入下一步。
关键输出：
- 新增 `tools/check_final_evidence_selection_policy_offline_simulation_gate.py`。
- 输出 `tests/final_evidence_selection_policy_offline_simulation_gate_report.json` 与 `docs/final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md`。
- 检查 schema/version、gate status、8 条 rows、policy category 顺序、0 blocking failure、manual-review signal、必需字段和非运行时边界。
- gate 通过后只允许进入 `policy_adoption_decision_draft`。
报告写法：
> v0.4.8.13 为最终证据选择策略离线模拟结果增加门禁。它只读取 v0.4.8.12 saved report，确认 12 项检查全部通过；该版本只允许进入 adoption decision draft，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 simulation gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实 simulation report、blocking failure、缺失字段、category 顺序漂移、runtime adoption 污染、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown simulation gate report。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.14：Final Evidence Selection Policy Adoption Decision Draft

阶段定位：在 v0.4.8.13 simulation gate 通过后，生成待用户确认的 adoption decision draft；本版本仍不是正式采纳结论，也不进入 runtime implementation。
解决的问题：simulation gate 已允许进入 adoption decision draft，但还没有把 8 条 policy category 的后续采纳路径写成可复核草案。v0.4.8.14 将每条 category 转成 suggested adoption option，并固定需要用户确认和单独未来授权的边界。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_adoption_decision_draft.py`。
- 输出 `tests/final_evidence_selection_policy_adoption_decision_draft_report.json` 与 `docs/final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md`。
- 生成 8 条 `pending_user_confirmation` draft rows。
- 每条 row 都保持 `requires_user_confirmation=true`、`implementation_allowed=false`、`runtime_adoption_status=not_allowed`。
报告写法：
> v0.4.8.14 将通过 gate 的离线模拟结果转成最终证据选择策略采纳决策草案。它只读取 v0.4.8.13 gate 与 v0.4.8.12 simulation saved reports，生成 8 条待用户确认 adoption rows；该版本不记录正式用户结论，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 adoption draft 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实来源构建、blocked gate、simulation 顺序漂移、blocking failure、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown adoption decision draft。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.8.15：Final Evidence Selection Policy Series Closeout

阶段定位：在 v0.4.8.14 adoption decision draft 之后，对 v0.4.8.x 最终证据选择策略离线设计系列做收口；本版本标记 offline design chain 完成，但不记录正式用户采纳，也不授权 runtime implementation。
解决的问题：v0.4.8.x 已完成 intake、policy table、worksheet、closeout、language confirmation、input contract、simulation、gate 与 adoption draft，需要一个明确的系列终态来避免继续在同一系列里追加临时任务。v0.4.8.15 将本系列关闭为离线设计成果，并把后续路线收敛到 v0.4.9.x retrieval input quality governance 或另行批准的 runtime design。
关键输出：
- 新增 `tools/build_final_evidence_selection_policy_series_closeout.py`。
- 输出 `tests/final_evidence_selection_policy_series_closeout_report.json` 与 `docs/final_evidence_selection_policy_series_closeout_v0.4.8.15.md`。
- 记录 16 个 completed steps，从 v0.4.8.0 design intake 到 v0.4.8.15 series closeout。
- 明确 `formal_user_adoption_recorded=false`、`implementation_allowed=false`，以及 adoption draft 仍为 `pending_user_confirmation`。
报告写法：
> v0.4.8.15 将最终证据选择策略 v0.4.8.x 系列收口为 offline design completed。它只读取 v0.4.8.14/13/12/11 saved reports，确认离线设计、模拟、gate 与 adoption draft 链条完整；该版本不记录正式用户采纳，不实现 runtime policy，不修改 rerank、prompt、eval case 或 RAG 主流程。
验证方式：
- py_compile 覆盖 series closeout 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实来源收口、blocked adoption draft、category 顺序漂移、实现授权污染、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown series closeout report。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.0：Retrieval Input Quality Intake

阶段定位：在 v0.4.8.x 最终证据选择策略离线设计收口后，开启 v0.4.9.x Retrieval Input Quality Governance。v0.4.9.0 只做入口归因，把既有 saved reports 中的 base retrieval gap、anchor dependency 和 root-cause action plan 信号整理成后续质量审计 bucket；本版本不改检索逻辑。
解决的问题：此前评估显示 anchor 正在大量补救基础召回缺口，且最终证据选择策略不能替代底层输入质量治理。v0.4.9.0 把问题从“调 rerank/加 anchor”收敛为 source/article identity、metadata/chunking、query lexical coverage、legal domain boundary、anchor dependency 五类治理对象。
关键输出：
- 新增 `tools/build_retrieval_input_quality_intake.py`。
- 输出 `tests/retrieval_input_quality_intake_report.json` 与 `docs/retrieval_input_quality_intake_v0.4.9.0.md`。
- 记录 5 个 intake buckets、12 个 sample cases。
- 关键基线：34 个 base-gap cases、33 个 anchor-dependency cases、33 个 metadata/chunking candidates、25 个 zero-base-recall cases。
报告写法：
> v0.4.9.0 将项目从最终证据选择策略离线设计推进到 retrieval input quality governance。它只读取既有 saved reports，把基础召回、anchor dependency、metadata/chunking、lexical coverage 和 domain boundary 信号整理成 5 个治理 bucket；该版本不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 intake 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实 saved reports、source version drift、空 gap source、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown retrieval input quality intake。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.1：Retrieval Input Quality Audit Spec

阶段定位：在 v0.4.9.0 intake 之后，将 5 个 retrieval input quality bucket 固化为离线审计规格；本版本只定义审计契约，不运行审计、不改检索逻辑。
解决的问题：v0.4.9.0 已把问题收敛为五类治理对象，但还缺少可执行前的契约边界。v0.4.9.1 为每个 bucket 定义 required inputs、required output fields、gate checks 和 success condition，避免后续 audit runner 变成临时脚本或直接修复。
关键输出：
- 新增 `tools/build_retrieval_input_quality_audit_spec.py`。
- 输出 `tests/retrieval_input_quality_audit_spec_report.json` 与 `docs/retrieval_input_quality_audit_spec_v0.4.9.1.md`。
- 生成 5 个 audit specs，其中 P0 为 source/article identity、metadata/chunking、anchor dependency；P1 为 query lexical coverage、legal domain boundary。
- 明确 `audits_not_run=true`、`implementation_allowed=false`、`retrieval_logic_change_allowed=false`。
报告写法：
> v0.4.9.1 将 v0.4.9.0 的 retrieval input quality intake 转成离线审计规格。它只读取 intake saved report，为五类治理 bucket 固化 required inputs、required outputs、gate checks 和 success conditions；该版本不运行 audit，不调用 RAG/Qdrant/LLM，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 audit spec 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖真实 intake、版本漂移、bucket 顺序漂移、实现授权污染、Markdown 边界和禁止运行时/后端模式。
- 默认生成 JSON/Markdown retrieval input quality audit spec。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.2：Retrieval Input Quality Offline Audit

阶段定位：在 v0.4.9.1 audit spec 之后，严格消费既有 saved reports，生成 5 个 retrieval input quality bucket 的离线审计结果；本版本只输出审计结果和下一步诊断 route，不改检索逻辑。
解决的问题：v0.4.9.1 已有契约，但还没有按契约落地的统一离线审计输出。v0.4.9.2 将 source/article identity、metadata/chunking、query lexical coverage、legal domain boundary 与 anchor dependency 五类 bucket 转成可 gate 的审计结果。
关键输出：
- 新增 `tools/build_retrieval_input_quality_offline_audit.py`。
- 输出 `tests/retrieval_input_quality_offline_audit_report.json` 与 `docs/retrieval_input_quality_offline_audit_v0.4.9.2.md`。
- 生成 5 条 offline audit rows：3 条 high severity、2 条 medium severity，total impacted signal count 为 140，unique sample cases 为 9。
- 明确 `implementation_allowed=false`、`code_patch_authorized=false`、`retrieval_logic_change_allowed=false`，下一步只允许做 offline audit gate。
报告写法：
> v0.4.9.2 按 v0.4.9.1 audit spec 读取既有 saved reports，生成 retrieval input quality 的离线审计结果。它为五类治理 bucket 输出 impacted case count、sample cases、evidence signals、severity 和 recommended next route；该版本不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 offline audit 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_retrieval_input_quality_offline_audit` 与 `tests.test_project_health_check`。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.3：Retrieval Input Quality Offline Audit Gate

阶段定位：在 v0.4.9.2 offline audit 之后，为离线审计报告增加发布前轻量门禁；本版本只检查报告结构、bucket 顺序、字段完整性、severity/route 完整性和非运行时边界。
解决的问题：v0.4.9.2 已输出审计结果，但还缺少可重复执行的 gate 来确认该报告没有结构漂移、字段缺失或 runtime 授权污染。v0.4.9.3 将该报告纳入门禁，保证后续 diagnostic prioritization 有稳定输入。
关键输出：
- 新增 `tools/check_retrieval_input_quality_offline_audit_gate.py`。
- 输出 `tests/retrieval_input_quality_offline_audit_gate_report.json` 与 `docs/retrieval_input_quality_offline_audit_gate_v0.4.9.3.md`。
- 生成 15 项 gate checks，状态为 `open_for_retrieval_input_quality_diagnostic_planning`，failed check count 为 0。
- 明确 `implementation_allowed=false`、`code_patch_authorized=false`、`retrieval_logic_change_allowed=false`，通过只允许进入 diagnostic planning。
报告写法：
> v0.4.9.3 为 v0.4.9.2 retrieval input quality offline audit 增加轻量门禁。它检查 schema/version、5 个 bucket 顺序、required row fields、row content、severity summary、recommended routes、case signal floor、runtime flags、forbidden keys 和 readability；该版本不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_retrieval_input_quality_offline_audit_gate` 与 `tests.test_project_health_check`。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.4：Retrieval Input Quality Diagnostic Prioritization

阶段定位：在 v0.4.9.3 offline audit gate 通过之后，将 5 条 recommended diagnostic routes 排成可审阅的离线诊断优先级；本版本只做规划，不进入任何 runtime 修复。
解决的问题：v0.4.9.3 已确认 offline audit 报告结构稳定，但还缺少先查哪一层、为什么先查、进入条件和禁止事项。v0.4.9.4 将五类诊断路线排序，避免直接跳到 domain routing、anchor 加规则或检索参数调优。
关键输出：
- 新增 `tools/build_retrieval_input_quality_diagnostic_prioritization.py`。
- 输出 `tests/retrieval_input_quality_diagnostic_prioritization_report.json` 与 `docs/retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md`。
- 诊断优先级为：metadata/chunking、anchor dependency、query lexical coverage、source/article identity、legal domain boundary。
- 每条 route 记录 entry conditions、prohibited actions、recommended artifact 和非运行时边界。
报告写法：
> v0.4.9.4 基于 v0.4.9.3 gate 与 v0.4.9.2 offline audit，生成 retrieval input quality 的诊断优先级矩阵。它将 metadata/chunking 排为第一优先级，将 anchor dependency 作为第二层症状诊断，将 query lexical coverage 排为第三；source/article identity 和 legal domain boundary 先保持窄口径诊断。该版本不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 prioritization 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_retrieval_input_quality_diagnostic_prioritization` 与 `tests.test_project_health_check`。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.5：Retrieval Input Quality Diagnostic Prioritization Gate

阶段定位：在 v0.4.9.4 diagnostic prioritization 之后，为诊断优先级矩阵增加发布前轻量门禁；本版本只检查 route order、priority rank、recommended artifacts、entry conditions、prohibited actions 和非运行时边界。
解决的问题：v0.4.9.4 已把 5 条诊断路线排好序，但还需要确认优先级不会漂移，尤其要固定 metadata/chunking 作为第一条后续诊断规格入口，而不是直接进入 anchor、query expansion 或 domain routing。
关键输出：
- 新增 `tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py`。
- 输出 `tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json` 与 `docs/retrieval_input_quality_diagnostic_prioritization_gate_v0.4.9.5.md`。
- 生成 17 项 gate checks，状态为 `open_for_metadata_chunking_diagnostic_spec`，failed check count 为 0。
- 明确 `implementation_allowed=false`、`code_patch_authorized=false`、`retrieval_logic_change_allowed=false`，通过只允许进入 metadata/chunking diagnostic spec。
报告写法：
> v0.4.9.5 为 v0.4.9.4 retrieval input quality diagnostic prioritization 增加轻量门禁。它确认 priority matrix 顺序稳定、第一入口为 metadata/chunking、每条 route 都具备 entry conditions 与 prohibited actions，并继续阻断 runtime implementation；该版本不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 prioritization gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_retrieval_input_quality_diagnostic_prioritization_gate` 与 `tests.test_project_health_check`。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.6：Metadata/Chunking Diagnostic Spec

阶段定位：在 v0.4.9.5 prioritization gate 之后，定义第一优先级 metadata/chunking diagnostic 的检查契约；本版本只固化未来诊断要检查的字段、sample case scope、输出状态和禁止动作，不运行诊断、不修数据、不改主流程。
解决的问题：v0.4.9.5 已确认下一步只能进入 metadata/chunking diagnostic spec，但还需要明确未来诊断到底检查哪些字段，避免把 metadata/chunking 问题直接误写成 chunk 合并、metadata 修补、ingestion 修改、retrieval 参数调整或新增 anchor。
关键输出：
- 新增 `tools/build_metadata_chunking_diagnostic_spec.py`。
- 输出 `tests/metadata_chunking_diagnostic_spec_report.json` 与 `docs/metadata_chunking_diagnostic_spec_v0.4.9.6.md`。
- 定义 5 个 check groups：metadata identity、chunk boundary、article locator、sample case mapping、diagnostic output contract。
- 覆盖 `chunk_id`、`parent_article_id`、`article_no/section_no`、`chunk_index/chunk_count`、`block_type`、`citation`、`law_name/source` 与 sample case mapping。
- 明确禁止 merge/rewrite chunks、edit metadata、change ingestion、tune retrieval parameters、add anchor rules、modify eval cases or fixtures。
报告写法：
> v0.4.9.6 将 metadata/chunking 诊断从“下一步方向”收敛为可检查的离线规格。它只读取 v0.4.9.5 gate 与 v0.4.9.4 prioritization saved reports，形成 5 个未来检查组、8 个 sample cases 和明确禁止动作；该版本不运行 diagnostic，不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 metadata/chunking spec 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_spec` 与 `tests.test_project_health_check`。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.7：Metadata/Chunking Diagnostic Spec Gate

阶段定位：在 v0.4.9.6 metadata/chunking diagnostic spec 之后，为该规格增加发布前轻量门禁；本版本只检查 saved spec report 的结构、字段覆盖、sample scope、prohibited actions 和非运行时边界，不运行 diagnostic，也不授权任何代码或数据修复。
解决的问题：v0.4.9.6 已经定义了未来 metadata/chunking 诊断契约，但还需要一个可重复执行的 gate 来防止 spec report 出现版本漂移、row 顺序漂移、字段覆盖缺口、sample scope 缺口或 runtime 授权污染。v0.4.9.7 将“可进入 runner design”的条件固化为 16 项检查。
关键输出：
- 新增 `tools/check_metadata_chunking_diagnostic_spec_gate.py`。
- 输出 `tests/metadata_chunking_diagnostic_spec_gate_report.json` 与 `docs/metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md`。
- 生成 16 项 gate checks，状态为 `open_for_metadata_chunking_diagnostic_runner_design`，failed check count 为 0。
- 明确 `diagnostic_run=not_run`、`implementation_allowed=false`、`code_patch_authorized=false`、`retrieval_logic_change_allowed=false`。
- 继续阻断 merge/rewrite chunks、edit metadata、change ingestion、tune retrieval parameters、add anchor rules、modify eval cases or fixtures。
报告写法：
> v0.4.9.7 为 metadata/chunking diagnostic spec 增加发布前门禁。它只读取 v0.4.9.6 saved spec report，检查 spec schema/version、5 个 check group 顺序、必要 metadata 字段覆盖、8 个 sample cases、source priority row、prohibited actions、row content、runtime flags、forbidden keys 和 readability；该版本不运行 diagnostic，不调用 RAG/Qdrant/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只开放 metadata/chunking diagnostic runner design。
验证方式：
- py_compile 覆盖 metadata/chunking spec gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_spec_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.8：Metadata/Chunking Diagnostic Runner Design

阶段定位：在 v0.4.9.7 spec gate 之后，定义未来只读 metadata/chunking diagnostic runner 的输入、输出和失败分桶契约；本版本只做 runner design，不读取 Qdrant，不扫描知识库全文，不运行 diagnostic，也不授权任何代码或数据修复。
解决的问题：v0.4.9.7 已确认 metadata/chunking diagnostic spec 可以进入 runner design，但如果直接写 runner，容易把诊断执行和数据修复混在一起。v0.4.9.8 先把未来 runner 的输入来源、输出字段、failure buckets、sample case handling 和 prohibited actions 固化为 saved report，确保后续实现仍保持只读边界。
关键输出：
- 新增 `tools/build_metadata_chunking_diagnostic_runner_design.py`。
- 输出 `tests/metadata_chunking_diagnostic_runner_design_report.json` 与 `docs/metadata_chunking_diagnostic_runner_design_v0.4.9.8.md`。
- 生成 5 条 runner design rows，对齐 metadata identity、chunk boundary、article locator、sample case mapping 和 diagnostic output contract。
- 定义输出字段契约：`case_id`、`source_spec_row_id`、`check_group`、`metadata_completeness_status`、`chunk_boundary_status`、`parent_article_link_status`、`citation_identity_status`、`article_locator_status`、`diagnostic_followup` 和 `blocking_findings`。
- 明确 failure buckets：metadata completeness gap、chunk boundary ambiguity、parent article link gap、citation identity gap、article locator gap 和 sample case mapping gap。
报告写法：
> v0.4.9.8 将 metadata/chunking diagnostic 从“可进入 runner design”推进为明确的只读 runner 契约。它只读取 v0.4.9.7 gate 与 v0.4.9.6 spec saved reports，形成输入契约、输出字段契约、failure buckets 和禁止动作；该版本不读取 Qdrant，不扫描知识库全文，不运行 diagnostic，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只开放 runner design gate。
验证方式：
- py_compile 覆盖 metadata/chunking runner design 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_runner_design` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown runner design 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.9：Metadata/Chunking Diagnostic Runner Design Gate

阶段定位：在 v0.4.9.8 runner design 之后，增加只读 gate，确认 runner design 的 schema、版本、输入来源、5 条 design rows、输出字段、failure buckets、prohibited actions 和非运行时边界未漂移。
解决的问题：v0.4.9.8 已经定义未来 runner 契约，但如果没有 gate，后续 dry-run contract 或 runner 实现可能在无意中扩张到 Qdrant 读取、知识库全文扫描、diagnostic 执行或数据修复。v0.4.9.9 将这些边界固化为 saved gate report。
关键输出：
- 新增 `tools/check_metadata_chunking_diagnostic_runner_design_gate.py`。
- 输出 `tests/metadata_chunking_diagnostic_runner_design_gate_report.json` 与 `docs/metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md`。
- 生成 16 项 gate checks，状态为 `open_for_metadata_chunking_diagnostic_dry_run_contract`，failed check count 为 0。
- 明确下一步只开放 `metadata_chunking_diagnostic_dry_run_contract`。
报告写法：
> v0.4.9.9 将 metadata/chunking diagnostic runner design 纳入发布前门禁。该版本只读取 v0.4.9.8 runner design saved report，检查 design 契约、输出字段、failure buckets、prohibited actions 和非运行时边界；不读取 Qdrant，不扫描知识库全文，不运行 diagnostic，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只开放 dry-run contract。
验证方式：
- py_compile 覆盖 metadata/chunking runner design gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_runner_design_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.10：Metadata/Chunking Diagnostic Dry-Run Contract

阶段定位：在 v0.4.9.9 runner design gate 之后，定义未来只读 metadata/chunking diagnostic runner 的 dry-run 入口契约；本版本只做 contract，不创建真实 runner，不读取 Qdrant，不扫描知识库全文，不运行 diagnostic。
解决的问题：runner design gate 已经确认契约稳定，但直接进入真实 runner 仍然容易把 CLI、输入来源、输出字段、失败处理和 runtime 边界混在一起。v0.4.9.10 先把 dry-run runner 的接口边界固化，确保后续实现仍按 saved reports 与只读边界推进。
关键输出：
- 新增 `tools/build_metadata_chunking_diagnostic_dry_run_contract.py`。
- 输出 `tests/metadata_chunking_diagnostic_dry_run_contract_report.json` 与 `docs/metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md`。
- 生成 5 条 contract rows，对齐 input saved report、CLI argument、diagnostic output、failure handling 和 non-runtime boundary。
- 明确未来 dry-run 输出字段、failure buckets、prohibited actions 和 runner 未实现状态。
报告写法：
> v0.4.9.10 将 metadata/chunking diagnostic 从“runner design gate 已通过”推进为 dry-run contract。它只读取 v0.4.9.9 gate 与 v0.4.9.8 runner design saved reports，形成未来只读 runner 的 CLI、输入、输出和失败处理契约；该版本不创建 runner，不读取 Qdrant，不扫描知识库全文，不运行 diagnostic，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只开放 v0.4.9 series closeout。
验证方式：
- py_compile 覆盖 dry-run contract 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_dry_run_contract` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown contract 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.9.11：Retrieval Input Quality Series Closeout

阶段定位：收口 v0.4.9.x retrieval input quality governance 系列，确认从 intake、audit spec、offline audit、audit gate、prioritization、prioritization gate 到 metadata/chunking spec、spec gate、runner design、runner design gate 和 dry-run contract 的 saved-report 链条完整。
解决的问题：v0.4.9.x 已完成检索输入质量治理链条，但如果没有明确 closeout，后续容易在同一系列里继续追加真实 runner 或临时修复。v0.4.9.11 将本系列关闭为离线治理成果，并把真实只读 diagnostic runner 移入后续系列。
关键输出：
- 新增 `tools/build_retrieval_input_quality_series_closeout.py`。
- 输出 `tests/retrieval_input_quality_series_closeout_report.json` 与 `docs/retrieval_input_quality_series_closeout_v0.4.9.11.md`。
- 记录 11 个 completed steps，从 v0.4.9.0 intake 到 v0.4.9.10 dry-run contract。
- 明确 diagnostic runner 未实现、diagnostic 未运行、runtime 未授权。
报告写法：
> v0.4.9.11 将 retrieval input quality v0.4.9.x 系列收口为 offline governance completed。它只读取 v0.4.9.0-v0.4.9.10 saved reports，确认治理链条完整；该版本不创建或运行 diagnostic runner，不读取 Qdrant，不扫描知识库全文，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。后续真实 runner 应进入单独批准的 v0.4.10.x 只读诊断系列。
验证方式：
- py_compile 覆盖 series closeout 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_retrieval_input_quality_series_closeout` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown closeout 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.10.0：Metadata/Chunking Diagnostic Runner Manifest

阶段定位：启动 v0.4.10.x 只读 metadata/chunking diagnostic runner 系列，先将 v0.4.9.10 dry-run contract 与 v0.4.9.6 spec 展开为明确的 runner manifest；本版本只生成诊断输入矩阵，不创建 runner、不运行 diagnostic。
解决的问题：v0.4.9.x 已经完成治理链条，但真实 runner 仍需要一个稳定输入清单，避免直接从 spec/contract 临时拼装执行对象。v0.4.10.0 将 8 个 sample cases 与 5 个 check groups 固化为 40 个 manifest items。
关键输出：
- 新增 `tools/build_metadata_chunking_diagnostic_runner_manifest.py`。
- 输出 `tests/metadata_chunking_diagnostic_runner_manifest_report.json` 与 `docs/metadata_chunking_diagnostic_runner_manifest_v0.4.10.0.md`。
- 记录 40 个 manifest items，并保留 required fields、failure signals、source spec row id 与非运行时边界。
报告写法：
> v0.4.10.0 将 metadata/chunking diagnostic 从离线治理链条推进到 runner 输入清单。它只读取 v0.4.9.11 closeout、v0.4.9.10 dry-run contract 与 v0.4.9.6 spec saved reports，生成 8 x 5 的只读 manifest；该版本不创建或运行 diagnostic runner，不读取 Qdrant，不扫描知识库全文，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 runner manifest 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_runner_manifest` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown manifest 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.10.1：Metadata/Chunking Saved-Report Diagnostic Runner

阶段定位：在 v0.4.10.0 manifest 之后，执行 saved-report scope 的 metadata/chunking diagnostic runner；本版本只验证 manifest 与 contract 层的诊断输入/输出是否完整，不读取 evidence-level metadata snapshot。
解决的问题：v0.4.10.0 已生成 40 个 manifest items，但仍未证明 runner 可以稳定输出 contract 形状。v0.4.10.1 跑通 saved-report runner，生成 40 行诊断结果，同时明确真实 metadata/chunk 质量尚未被检查。
关键输出：
- 新增 `tools/run_metadata_chunking_diagnostic_saved_report.py`。
- 输出 `tests/metadata_chunking_diagnostic_saved_report_runner_report.json` 与 `docs/metadata_chunking_diagnostic_saved_report_runner_v0.4.10.1.md`。
- 记录 40 行 diagnostic rows、0 个 blocked rows、8 个 sample cases 与 5 个 check groups。
- 明确 `evidence_level_metadata_snapshot_read=false`，结果含义为 contract/readiness diagnostic，不是 evidence-level metadata quality verdict。
报告写法：
> v0.4.10.1 执行 saved-report scope 的 metadata/chunking diagnostic runner。它只读取 v0.4.10.0 manifest 与 v0.4.9.10 dry-run contract，输出 40 行诊断结果；该版本不读取 Qdrant，不扫描知识库全文，不调用 RAG/LLM，不读取 evidence-level metadata snapshot，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 saved-report runner 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_saved_report_runner` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown runner 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.10.2：Metadata/Chunking Saved-Report Runner Gate

阶段定位：在 v0.4.10.1 saved-report runner 之后，增加发布前轻量门禁，确认 runner 输出仍然停留在 saved-report scope，且没有被误解释为真实 evidence-level metadata snapshot。
解决的问题：v0.4.10.1 已经输出 40 行诊断结果，但仍需确认输出行数、字段契约、blocked rows 和非运行时边界没有漂移。v0.4.10.2 将这些检查固化为可重复执行的 gate，并只开放 v0.4.10 series closeout。
关键输出：
- 新增 `tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py`。
- 输出 `tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json` 与 `docs/metadata_chunking_diagnostic_saved_report_runner_gate_v0.4.10.2.md`。
- 生成 gate report，确认 40 diagnostic rows、0 blocked rows、required output fields 完整、`evidence_level_metadata_snapshot_read=false`。
- 明确 `implementation_allowed=false`、`retrieval_logic_change_allowed=false`、`metadata_mutation=disallowed`、`chunk_mutation=disallowed`。
报告写法：
> v0.4.10.2 为 saved-report scope 的 metadata/chunking diagnostic runner 增加门禁。它只读取 v0.4.10.1 runner saved report，检查 40 行输出、0 blocked rows、字段契约和 saved-report-only 边界；该版本不读取 Qdrant，不扫描知识库全文，不调用 RAG/LLM，不读取 evidence-level metadata snapshot，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只开放 v0.4.10 series closeout。
验证方式：
- py_compile 覆盖 runner gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_saved_report_runner_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.10.3：Metadata/Chunking Diagnostic Runner Series Closeout

阶段定位：收束 v0.4.10.x saved-report metadata/chunking diagnostic runner 系列，确认 manifest、saved-report runner 与 runner gate 的治理链条完整；本版本仍不进入真实 evidence-level metadata snapshot，也不授权修复。
解决的问题：v0.4.10.0-v0.4.10.2 已经从 runner manifest 推进到 saved-report runner 和 runner gate，但需要明确系列边界，避免后续把 saved-report contract readiness 误当成真实知识库 metadata/chunk 质量结论。v0.4.10.3 将本系列关闭为 saved-report diagnostic completed。
关键输出：
- 新增 `tools/build_metadata_chunking_diagnostic_runner_series_closeout.py`。
- 输出 `tests/metadata_chunking_diagnostic_runner_series_closeout_report.json` 与 `docs/metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md`。
- 确认 v0.4.10.0 manifest、v0.4.10.1 runner、v0.4.10.2 gate 均存在且顺序完整。
- 确认 40 个 manifest items 与 40 行 diagnostic rows 对齐，blocked rows 为 0。
- 明确下一阶段只能进入单独批准的 v0.4.11.x evidence-level metadata snapshot read-only diagnostic design。
报告写法：
> v0.4.10.3 将 v0.4.10.x metadata/chunking diagnostic runner 系列收口为 saved-report diagnostic completed。它只读取 v0.4.10.0 manifest、v0.4.10.1 saved-report runner 与 v0.4.10.2 runner gate saved reports，确认 40 个 manifest items、40 行 diagnostic rows、0 blocked rows 和非运行时边界；该版本不读取 Qdrant，不扫描知识库全文，不调用 RAG/LLM，不读取 evidence-level metadata snapshot，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 series closeout 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_diagnostic_runner_series_closeout` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown closeout 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.11.0：Evidence Metadata Snapshot Contract

阶段定位：启动 v0.4.11.x evidence-level metadata snapshot 只读诊断系列，先定义未来 Qdrant payload snapshot runner 的输入、输出和失败阻断契约；本版本不连接 Qdrant。
解决的问题：v0.4.10.x 只证明 saved-report runner contract 可跑通，尚未读取真实 evidence-level metadata。v0.4.11.0 将 8 个 sample cases 的 expected evidence 展开为 19 个 snapshot targets，并定义只读 payload scroll、字段检查、failure buckets 和禁止动作。
关键输出：
- 新增 `tools/build_evidence_metadata_snapshot_contract.py`。
- 输出 `tests/evidence_metadata_snapshot_contract_report.json` 与 `docs/evidence_metadata_snapshot_contract_v0.4.11.0.md`。
- 定义 required metadata fields、output fields、failure buckets 和 read-only policy。
- 明确本版本 `qdrant_access=not_run_in_contract`，下一步才允许只读 payload scroll。
报告写法：
> v0.4.11.0 将 evidence-level metadata snapshot 从方向收敛为 runner contract。它只读取 v0.4.10.3 closeout、v0.4.10.0 manifest 和 RAG eval cases，生成 8 个 sample cases、19 个 evidence targets 与只读输出契约；该版本不连接 Qdrant，不扫描知识库全文，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 snapshot contract 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_evidence_metadata_snapshot_contract` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown contract 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.11.1：Evidence Metadata Snapshot Runner

阶段定位：在 v0.4.11.0 contract 后，首次读取真实 Qdrant payload metadata，生成 evidence-level snapshot 诊断；本版本仍只读，不运行 RAG/LLM，不修数据。
解决的问题：此前只能证明 saved-report contract 可执行，不能判断真实库中 metadata/chunk 字段是否完整。v0.4.11.1 按 19 个 evidence targets 对 Qdrant collection 做 payload-only scroll，并将结果转为可门禁的诊断行。
关键输出：
- 新增 `tools/run_evidence_metadata_snapshot.py`。
- 输出 `tests/evidence_metadata_snapshot_report.json` 与 `docs/evidence_metadata_snapshot_v0.4.11.1.md`。
- 实际扫描 7177 个 Qdrant points，输出 19 行 diagnostic rows。
- 当前 19/19 targets 均命中 `chunk_boundary_ambiguity`，主要信号为匹配 evidence payload 缺少 `chunk_index/chunk_count`。
报告写法：
> v0.4.11.1 执行 read-only evidence metadata snapshot runner。它按 v0.4.11.0 contract 只读 Qdrant payload，`with_vectors=false`，扫描 7177 个 points 并输出 19 行 evidence target 诊断；该版本不调用 rag_query、embedding、LLM，不运行 full eval，不写 Qdrant，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。当前真实信号是 19/19 evidence targets 存在 chunk boundary ambiguity，应进入 gate 固化结论。
验证方式：
- py_compile 覆盖 snapshot runner、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_evidence_metadata_snapshot` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown snapshot 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.11.2：Evidence Metadata Snapshot Gate

阶段定位：在 v0.4.11.1 真实 Qdrant payload snapshot 后，增加门禁确认 snapshot 行为和 findings 可信；本版本不重新连接 Qdrant，不修复 metadata/chunk。
解决的问题：v0.4.11.1 输出了 19 行真实诊断，但需要区分“可接受的 findings”与“runner 越界/环境失败”。v0.4.11.2 确认 payload read 为真、vectors disabled、row count 对齐 contract，并将 `chunk_boundary_ambiguity` 固化为主 findings。
关键输出：
- 新增 `tools/check_evidence_metadata_snapshot_gate.py`。
- 输出 `tests/evidence_metadata_snapshot_gate_report.json` 与 `docs/evidence_metadata_snapshot_gate_v0.4.11.2.md`。
- 确认 19 diagnostic rows、19 targets、7177 scanned points、0 gate failures。
- 记录 primary finding 为 `chunk_boundary_ambiguity`。
报告写法：
> v0.4.11.2 为 evidence metadata snapshot 增加门禁。它只读取 v0.4.11.1 snapshot 与 v0.4.11.0 contract saved reports，确认 Qdrant payload read、`with_vectors=false`、19 行诊断与 findings 分布；该版本不连接 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只开放 v0.4.11 series closeout。
验证方式：
- py_compile 覆盖 snapshot gate、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_evidence_metadata_snapshot_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.11.3：Evidence Metadata Snapshot Series Closeout

阶段定位：收束 v0.4.11.x evidence metadata snapshot 只读诊断系列，确认从 contract、真实 Qdrant payload snapshot 到 gate 的链条完整；本版本仍不授权修复。
解决的问题：v0.4.11.0-v0.4.11.2 已经完成真实 evidence-level metadata 读取和门禁，但需要明确结论边界，避免直接跳到 metadata/chunk 修复或主链路调整。v0.4.11.3 将该系列关闭，并把 findings 移交给 v0.4.12 root-cause/fix design。
关键输出：
- 新增 `tools/build_evidence_metadata_snapshot_series_closeout.py`。
- 输出 `tests/evidence_metadata_snapshot_series_closeout_report.json` 与 `docs/evidence_metadata_snapshot_series_closeout_v0.4.11.3.md`。
- 确认 19 targets、19 diagnostic rows、7177 scanned points。
- 明确 primary finding 为 `chunk_boundary_ambiguity`，下一系列为 metadata/chunking root-cause and fix design。
报告写法：
> v0.4.11.3 将 evidence metadata snapshot 系列收口为 read-only diagnostic completed。它只读取 v0.4.11.0 contract、v0.4.11.1 snapshot 与 v0.4.11.2 gate saved reports，确认真实 Qdrant payload snapshot 已完成，主信号为 19/19 evidence targets 的 `chunk_boundary_ambiguity`；该版本不连接 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
验证方式：
- py_compile 覆盖 series closeout、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_evidence_metadata_snapshot_series_closeout` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown closeout 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.12.0：Metadata/Chunking Root-Cause Report

阶段定位：启动 v0.4.12.x metadata/chunking root-cause and fix design 系列，先把 v0.4.11.x 的真实 evidence metadata snapshot findings 与 ingestion 静态实现对齐；本版本只形成根因报告，不授权修复。

解决的问题：v0.4.11.x 已确认 19/19 evidence targets 存在 `chunk_boundary_ambiguity`，但还不能直接判定要改检索、rerank、anchor 或 prompt。v0.4.12.0 将该 finding 追溯到 ingestion 层：标准类 `build_standard_section_documents` 已写入 `chunk_index/chunk_count`，普通法律 `build_article_documents` 生成的 article/paragraph/item 块缺少对应 chunk boundary metadata。

关键输出：
- 新增 `tools/build_metadata_chunking_root_cause_report.py`。
- 输出 `tests/metadata_chunking_root_cause_report.json` 与 `docs/metadata_chunking_root_cause_v0.4.12.0.md`。
- 确认 primary root cause 为 `ingestion_article_chunks_missing_boundary_metadata`，confidence 为 high。
- 记录 `assign_stable_chunk_ids` 已把 `chunk_index` 纳入 identity，因此未来修复会影响 stable chunk IDs，必须先做 fix design 与 rebuild/dry-run plan。

报告写法：
> v0.4.12.0 将 v0.4.11.x 的真实 Qdrant payload snapshot findings 收敛为 ingestion 层根因报告。它只读取 saved reports 和 `src/rag/ingestion.py` 源码文本，确认普通法律 article/paragraph/item 块缺少 chunk boundary metadata，而标准章节路径已有该字段；该版本不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 root-cause report 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_root_cause_report` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown root-cause 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.12.1：Metadata/Chunking Fix Design

阶段定位：在 v0.4.12.0 root-cause report 之后，把根因转成可评审的修复设计；本版本仍不改 ingestion、不重建 Qdrant、不改主链路。

解决的问题：v0.4.12.0 已确认普通法律 article/paragraph/item ingestion 路径缺少 `chunk_index/chunk_count`，但直接补字段会影响 `assign_stable_chunk_ids`，进而改变 chunk ID 和 Qdrant point ID。v0.4.12.1 先把修复目标、metadata contract、stable ID impact 和未来 rebuild/dry-run 验证要求写清楚。

关键输出：
- 新增 `tools/build_metadata_chunking_fix_design.py`。
- 输出 `tests/metadata_chunking_fix_design_report.json` 与 `docs/metadata_chunking_fix_design_v0.4.12.1.md`。
- 提出修复目标为 `build_article_documents_chunk_boundary_metadata`。
- 明确 direct Qdrant payload patch 仍被禁止，未来必须先通过 rebuild dry-run。

报告写法：
> v0.4.12.1 将 metadata/chunking 根因转成修复设计。它只读取 v0.4.12.0 root-cause saved report，提出未来应在 legal article ingestion 路径为 article、paragraph、item 块补齐 deterministic `chunk_index/chunk_count`；由于 stable chunk ID 已包含 `chunk_index`，该修复预计会改变 chunk IDs 和 Qdrant point IDs，因此必须通过 rebuild/dry-run 方案进入后续版本。本版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 fix design 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_fix_design` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown fix design 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.12.2：Metadata/Chunking Fix Design Gate

阶段定位：在 v0.4.12.1 fix design 之后，增加发布前门禁，确认修复设计没有漂移为直接实现或直接改库；本版本仍不改 ingestion、不重建 Qdrant、不改主链路。

解决的问题：metadata/chunking 修复容易误走两条路：一是直接给 Qdrant payload 打补丁，二是直接改 ingestion 后重建而没有 stable ID 影响评估。v0.4.12.2 将 stable ID impact、Qdrant point ID impact、rebuild required、direct payload patch disallowed 和 implementation disallowed 固化为 gate checks。

关键输出：
- 新增 `tools/check_metadata_chunking_fix_design_gate.py`。
- 输出 `tests/metadata_chunking_fix_design_gate_report.json` 与 `docs/metadata_chunking_fix_design_gate_v0.4.12.2.md`。
- 确认 14 项 gate checks 全部通过，`failed_check_count=0`。
- 通过后只开放 v0.4.12 series closeout，不开放 runtime implementation。

报告写法：
> v0.4.12.2 将 metadata/chunking fix design 固化为门禁。它只读取 v0.4.12.1 fix design 与 v0.4.12.0 root-cause saved reports，确认 future fix 必须承认 stable ID/Qdrant point ID 变化，并通过 rebuild/dry-run 进入后续版本；该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 fix design gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_fix_design_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.12.3：Metadata/Chunking Series Closeout

阶段定位：收束 v0.4.12.x metadata/chunking root-cause and fix design 系列，确认 root-cause、fix design 和 gate 链条完整；本版本仍不授权实现。

解决的问题：v0.4.12.0-v0.4.12.2 已完成从真实 metadata snapshot finding 到修复设计门禁的闭环，但需要明确下一系列只能进入 rebuild-safe ingestion metadata planning，而不是直接改主链路或直接写 Qdrant。

关键输出：
- 新增 `tools/build_metadata_chunking_series_closeout.py`。
- 输出 `tests/metadata_chunking_series_closeout_report.json` 与 `docs/metadata_chunking_series_closeout_v0.4.12.3.md`。
- 确认 completed steps 为 v0.4.12.0 root-cause、v0.4.12.1 fix design、v0.4.12.2 fix design gate。
- 明确下一系列为 v0.4.13.x ingestion metadata patch and rebuild dry-run planning。

报告写法：
> v0.4.12.3 将 metadata/chunking root-cause and fix design 系列收口。它只读取 v0.4.12.0、v0.4.12.1 和 v0.4.12.2 saved reports，确认普通法律 article/paragraph/item 块缺少 chunk boundary metadata 的根因、修复设计和 gate 均已形成；该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。下一系列必须先做 ingestion metadata patch planning 和 rebuild dry-run。

验证方式：
- py_compile 覆盖 series closeout 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_metadata_chunking_series_closeout` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown closeout 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.0：Ingestion Metadata Patch Contract

阶段定位：启动 v0.4.13.x ingestion metadata patch and rebuild dry-run planning 系列，先把未来 patch 的文件、函数、字段、禁止范围和 rebuild dry-run 前置要求写成 contract；本版本不实现 patch。

解决的问题：v0.4.12.x 已经确认普通法律 article/paragraph/item 块缺少 chunk boundary metadata，但实际修复会影响 stable chunk ID 和 Qdrant point ID。v0.4.13.0 先限定未来只允许在 `src/rag/ingestion.py::build_article_documents` 增加 deterministic `chunk_index/chunk_count` metadata，不允许改 `rag_query`、标准章节路径、stable ID 函数、规则或 eval cases。

关键输出：
- 新增 `tools/build_ingestion_metadata_patch_contract.py`。
- 输出 `tests/ingestion_metadata_patch_contract_report.json` 与 `docs/ingestion_metadata_patch_contract_v0.4.13.0.md`。
- 定义父条文块规则：`block_type=article` 时 `chunk_index=1`、`chunk_count=1`，且不改变 content。
- 定义款/项子块规则：`paragraph/item` 按 `article_parts` 生成顺序使用 1-based `chunk_index`，`chunk_count=len(article_parts)`，且不改变 content。
- 明确下一步只能是 contract gate，不开放 implementation。

报告写法：
> v0.4.13.0 将 future ingestion metadata patch 收敛为 contract。它只读取 v0.4.12.3 closeout、v0.4.12.1 fix design 和 `src/rag/ingestion.py` 源码文本，规定未来 patch 只能触及 `build_article_documents`，目标是为普通法律 article、paragraph、item 块补齐 deterministic `chunk_index/chunk_count`；该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 contract 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_contract` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown contract 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.1：Ingestion Metadata Patch Contract Gate

阶段定位：在 v0.4.13.0 contract 之后，增加门禁确认 patch 范围没有漂移；本版本仍不改 ingestion、不重建 Qdrant、不改主链路。

解决的问题：即使 contract 已限定未来 patch，也需要可重复执行的 gate 防止后续把 `src/rag/retriever.py`、规则、eval cases、standard section 路径或 stable ID 函数误纳入修复范围。v0.4.13.1 将 allowed file/function、parent/child chunk rules、Qdrant 禁止、retrieval 禁止和 eval/fixture 禁止固化为 15 项检查。

关键输出：
- 新增 `tools/check_ingestion_metadata_patch_contract_gate.py`。
- 输出 `tests/ingestion_metadata_patch_contract_gate_report.json` 与 `docs/ingestion_metadata_patch_contract_gate_v0.4.13.1.md`。
- 确认 contract gate `status=passed`，`failed_check_count=0`。
- 通过后只开放 ingestion metadata patch dry-run design，不开放 implementation。

报告写法：
> v0.4.13.1 将 ingestion metadata patch contract 固化为门禁。它只读取 v0.4.13.0 contract saved report，确认 future patch 仍只能触及 `src/rag/ingestion.py::build_article_documents`，且 Qdrant write、retrieval change、eval case mutation 和 fixture mutation 均保持禁止；该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 contract gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_contract_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.2：Ingestion Metadata Patch Dry-Run Design

阶段定位：在 v0.4.13.1 contract gate 之后，设计未来本地 dry-run 如何比较 patch 前后的 metadata 和 ID drift；本版本仍不改 ingestion、不读写 Qdrant、不改主链路。

解决的问题：实际 patch 会新增 `chunk_index/chunk_count`，并预期导致 `chunk_id` 与 `qdrant_point_id` 改变。v0.4.13.2 先定义 dry-run 应如何在内存中构造 pre/post documents、比较 expected drift 与 forbidden drift，并明确哪些输出字段和 blocking conditions 必须存在。

关键输出：
- 新增 `tools/build_ingestion_metadata_patch_dry_run_design.py`。
- 输出 `tests/ingestion_metadata_patch_dry_run_design_report.json` 与 `docs/ingestion_metadata_patch_dry_run_design_v0.4.13.2.md`。
- 定义 future dry-run comparison strategy：current builder vs isolated simulation helper、clone 后运行 `assign_stable_chunk_ids`、比较 content/citation/block metadata/chunk metadata/ID drift。
- 明确 expected drift 为 `chunk_index`、`chunk_count`、`chunk_id`、`qdrant_point_id`；forbidden drift 为 content、citation、block_type、paragraph/item metadata 等。
- 通过后只开放 dry-run design gate，不开放 implementation。

报告写法：
> v0.4.13.2 将 ingestion metadata patch 的未来 dry-run 设计成可门禁的本地比较流程。它只读取 v0.4.13.0 contract 与 v0.4.13.1 contract gate saved reports，规定未来 runner 只能在内存中模拟 `build_article_documents` 增加 `chunk_index/chunk_count` 后的结果，并比较 metadata 与 stable ID drift；该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 dry-run design 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_dry_run_design` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown dry-run design 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.3：Ingestion Metadata Patch Dry-Run Design Gate

阶段定位：在 v0.4.13.2 dry-run design 之后，增加门禁确认 future dry-run runner 的设计没有漂移；本版本仍不实现 runner、不改 ingestion、不读写 Qdrant、不改主链路。

解决的问题：dry-run design 需要保证 future runner 真正做到 local-only、可解释漂移，并且不能把 full eval、Qdrant scroll 或知识库全文扫描伪装成 dry-run。v0.4.13.3 将 expected drift、forbidden drift、allowed/forbidden inputs、output contract 和 blocking conditions 固化为 18 项 gate checks。

关键输出：
- 新增 `tools/check_ingestion_metadata_patch_dry_run_design_gate.py`。
- 输出 `tests/ingestion_metadata_patch_dry_run_design_gate_report.json` 与 `docs/ingestion_metadata_patch_dry_run_design_gate_v0.4.13.3.md`。
- 确认 dry-run design gate `status=passed`，`failed_check_count=0`。
- 通过后只开放 local dry-run runner，不开放 actual patch/rebuild。

报告写法：
> v0.4.13.3 将 ingestion metadata patch dry-run design 固化为门禁。它只读取 v0.4.13.2 dry-run design saved report，确认 future runner 仍必须停留在本地内存比较，不允许 Qdrant scroll、knowledge fulltext scan、RAG/LLM/embedding 输入，也不允许用 full eval 替代 dry-run；该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM，不运行 full eval，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 dry-run design gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_dry_run_design_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.4：Ingestion Metadata Patch Local Dry-Run Runner

阶段定位：在 v0.4.13.3 dry-run design gate 之后，实现真正的本地内存 dry-run runner；本版本仍不修改 ingestion、不重建 Qdrant、不改主链路。

解决的问题：未来给普通法律 article/paragraph/item 块补齐 `chunk_index/chunk_count` 会导致 stable chunk ID 和 Qdrant point ID 变化。v0.4.13.4 先用 3 个小型 in-memory 样例验证“预期漂移”和“禁止漂移”是否可被稳定观测，避免直接进入实际 patch 或重建。

关键输出：
- 新增 `tools/run_ingestion_metadata_patch_local_dry_run.py`。
- 输出 `tests/ingestion_metadata_patch_local_dry_run_report.json` 与 `docs/ingestion_metadata_patch_local_dry_run_v0.4.13.4.md`。
- 报告确认 3 个样例、8 个 pre/post documents；`chunk_index/chunk_count`、`chunk_id`、`qdrant_point_id` 出现预期漂移；content、citation、block_type、paragraph/item metadata 等 forbidden drift 为 0。
- 通过后只开放 `ingestion_metadata_patch_local_dry_run_gate`，仍不开放 actual ingestion patch 或 rebuild。

报告写法：
> v0.4.13.4 将 ingestion metadata patch 从设计推进到本地内存 dry-run。它复用当前 `build_article_documents`，在克隆文档上模拟补齐 `chunk_index/chunk_count`，再运行 stable ID 生成逻辑比较 pre/post metadata 与 ID drift。该版本证明未来 patch 会产生预期 ID 漂移，同时不会改变内容、引用或块结构；但它不修改 `src/rag/ingestion.py`，不写 Qdrant，不调用 RAG/LLM/embedding，不运行 full eval，也不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。

验证方式：
- py_compile 覆盖 local dry-run runner、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_local_dry_run` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown local dry-run 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.5：Ingestion Metadata Patch Local Dry-Run Gate

阶段定位：在 v0.4.13.4 local dry-run 之后增加发布前门禁；本版本只验证报告，不重新运行 runner、不修改 ingestion、不重建 Qdrant、不改主链路。

解决的问题：local dry-run 已证明预期 ID 漂移和 0 forbidden drift，但仍需要一个可重复 gate 防止后续报告漂移、样例缺失、row 字段缺失、content/citation 被改动、Qdrant/rebuild 权限误放开等问题。v0.4.13.5 将这些条件固化为 25 项检查。

关键输出：
- 新增 `tools/check_ingestion_metadata_patch_local_dry_run_gate.py`。
- 输出 `tests/ingestion_metadata_patch_local_dry_run_gate_report.json` 与 `docs/ingestion_metadata_patch_local_dry_run_gate_v0.4.13.5.md`。
- gate 检查 v0.4.13.4 report 的 schema/version、3 个样例、8 行 row、预期 metadata/ID drift、0 forbidden drift、content/citation 稳定、post boundary metadata 存在和 guardrails 未漂移。
- 通过后只开放 `actual_ingestion_metadata_patch_design`，仍不授权 actual patch、Qdrant write、collection rebuild 或 retrieval change。

报告写法：
> v0.4.13.5 将 local dry-run 结果纳入门禁。它只读取 v0.4.13.4 saved report，确认样例、row-level drift、禁止漂移和 guardrails 稳定；该版本不重新运行 dry-run，不修改 `src/rag/ingestion.py`，不写 Qdrant，不调用 RAG/LLM/embedding，不运行 full eval，也不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只允许进入 actual ingestion metadata patch design，仍不允许直接实现或 rebuild。

验证方式：
- py_compile 覆盖 gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_local_dry_run_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.6：Ingestion Metadata Patch Actual Design

阶段定位：在 v0.4.13.5 local dry-run gate 之后，将真正 patch 前的代码边界、实现草图和验证计划写成设计报告；本版本仍不修改 ingestion、不重建 Qdrant、不改主链路。

解决的问题：local dry-run 和 gate 已证明补齐 `chunk_index/chunk_count` 会产生预期 stable ID drift，且不会改变 content/citation/块结构。v0.4.13.6 把未来实际修改收敛为唯一文件、唯一函数、唯一字段集合，避免 patch 扩散到 retriever、stable ID 函数、规则或 eval cases。

关键输出：
- 新增 `tools/build_ingestion_metadata_patch_actual_design.py`。
- 输出 `tests/ingestion_metadata_patch_actual_design_report.json` 与 `docs/ingestion_metadata_patch_actual_design_v0.4.13.6.md`。
- 设计限定未来只可修改 `src/rag/ingestion.py::build_article_documents`，只补 deterministic `chunk_index/chunk_count`。
- 明确 parent article 块使用 `chunk_index=1/chunk_count=1`，paragraph/item 子块按 `article_parts` emission order 使用 1-based `chunk_index`，`chunk_count=len(article_parts)`。
- 明确 v0.4.13.4 pre-patch drift runner 是基线，不应在 patch 后继续期待同样 drift；actual patch 后应以直接 metadata 单测和限定 diff check 为准。

报告写法：
> v0.4.13.6 将 ingestion metadata patch 从 dry-run gate 推进为 actual patch design。它只读取 v0.4.13.0 contract、v0.4.13.4 local dry-run 和 v0.4.13.5 gate saved reports，规定未来 patch 只能触及 `build_article_documents` 并只补齐 `chunk_index/chunk_count`。该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM/embedding，不运行 full eval，也不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只允许进入 design gate，仍不允许直接实现或 rebuild。

验证方式：
- py_compile 覆盖 actual design 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_actual_design` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown design 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.7：Ingestion Metadata Patch Actual Design Gate

阶段定位：在 v0.4.13.6 actual patch design 之后增加发布前门禁；本版本仍不修改 ingestion，不重建 Qdrant，不改主链路。

解决的问题：actual design 已经收敛到 `src/rag/ingestion.py::build_article_documents`，但实际动源码前仍需要可重复 gate 防止范围漂移。v0.4.13.7 读取 v0.4.13.6 design，确认 allowed file/function、parent/child metadata rules、post-patch validation plan、guardrails 和 handoff boundary 都稳定。

关键输出：
- 新增 `tools/check_ingestion_metadata_patch_actual_design_gate.py`。
- 输出 `tests/ingestion_metadata_patch_actual_design_gate_report.json` 与 `docs/ingestion_metadata_patch_actual_design_gate_v0.4.13.7.md`。
- gate 共 31 项检查，0 failure；通过后只开放 `minimal_ingestion_metadata_source_patch`。
- 新增 `tests/test_ingestion_metadata_patch_actual_design_gate.py`，覆盖 scope drift、child count drift、validation plan gaps、implementation/Qdrant/rebuild drift 与 handoff boundary drift。

报告写法：
> v0.4.13.7 将 v0.4.13.6 actual patch design 固化为源码修改前门禁。它只读取 design saved report，确认下一步仍只能最小修改 `src/rag/ingestion.py::build_article_documents`，且只补齐 article/paragraph/item 的 deterministic `chunk_index/chunk_count` metadata。该版本不修改 ingestion，不写 Qdrant，不调用 RAG/LLM/embedding，不运行 full eval，也不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。通过后只允许进入 minimal ingestion metadata source patch，仍不允许 rebuild 或主链路改造。

验证方式：
- py_compile 覆盖 actual design gate 工具、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_patch_actual_design_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。
### v0.4.13.8：入库元数据源码补丁

阶段定位：在 v0.4.13.7 gate 通过后执行最小源码 patch；本版本只修改普通法律条文 ingestion metadata，不重建 Qdrant，不改 RAG 主链路。

解决的问题：v0.4.11-v0.4.13.7 已经把 `chunk_boundary_ambiguity` 收敛到普通法律 article/paragraph/item 路径缺少 `chunk_index/chunk_count`。v0.4.13.8 正式在 `src/rag/ingestion.py::build_article_documents` 补齐这两个字段，使未来重建后的 evidence payload 能区分同一条文下的父块、款块和项块边界。

关键输出：
- 修改 `src/rag/ingestion.py::build_article_documents`，parent article 使用 `chunk_index=1/chunk_count=1`。
- paragraph/item 子块按 `article_parts` emission order 使用 1-based `chunk_index`，`chunk_count=len(article_parts)`。
- 新增 `tests/test_ingestion_metadata_source_patch.py`，直接验证 parent/child metadata 和 standard section 路径不变。
- 新增 `tools/check_ingestion_metadata_source_patch.py`，输出 `tests/ingestion_metadata_source_patch_report.json` 与 `docs/ingestion_metadata_source_patch_v0.4.13.8.md`；15 项检查全部通过。
- 调整历史 dry-run/root-cause 测试，明确 saved report 是 pre-patch 实验对象，当前源码是 post-patch 实验对象。

报告写法：
> v0.4.13.8 完成 ingestion metadata 的最小源码 patch。该版本只触及 `build_article_documents`，为普通法律 article、paragraph、item 文档补齐 deterministic `chunk_index/chunk_count`，并用直接单测和源码补丁 checker 证明 content、citation、block metadata 与 standard section 路径保持稳定。该版本不写 Qdrant，不 rebuild collection，不调用 RAG/LLM/embedding，不运行 full eval，也不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。下一步只能进入 post-patch rebuild dry-run design，不能直接重建生产索引。

验证方式：
- py_compile 覆盖源码补丁 checker、ingestion、对应单测、health check、FastAPI 版本和相关维护测试。
- 单测覆盖 `tests.test_ingestion_metadata_source_patch`、`tests.test_ingestion_metadata_source_patch_check`、受影响历史测试与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown 源码补丁检查报告。
- restricted diff 确认未修改 `src/rag/retriever.py`、规则文件或 eval cases。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。
### v0.4.13.9：Post-Patch Rebuild Dry-Run Design

阶段定位：在 v0.4.13.8 源码补丁通过后，为未来 rebuild dry-run runner 设计输入、输出、对比字段和阻断条件；本版本不创建 runner，不写 Qdrant，不 rebuild，不改 RAG 主链路。

解决的问题：v0.4.13.8 已经把普通法律条文 ingestion 路径补齐 `chunk_index/chunk_count`，但真实 collection rebuild 会影响 `chunk_id` 与 `qdrant_point_id`。v0.4.13.9 先定义 dry-run 如何在本地、可复核地比较 post-patch payload，避免直接重建生产索引。

关键输出：
- 新增 `tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py`，只读取 `tests/ingestion_metadata_source_patch_report.json`。
- 新增 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json`，定义 future runner 的 allowed inputs、forbidden inputs、sample strategy、comparison fields、expected drift、forbidden drift 和 output contract。
- 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py`，验证输入漂移阻断、guardrails、future runner contract 和 design-only Markdown。
- 将 v0.4.13.8 最新展示文档局部中文化，同时保留 JSON key、枚举值、路径、命令和检查项原文，避免影响系统运行。

报告写法：
> v0.4.13.9 将 post-patch rebuild dry-run 的未来运行方式先固化成设计契约。该版本确认下一步只能 gate 这个 design，不能直接创建 runner、写 Qdrant、rebuild collection、调用 RAG/LLM/embedding、运行 full eval，或修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures、eval cases。它的核心价值是把未来 rebuild 前必须比较的 `chunk_index/chunk_count`、`chunk_id`、`qdrant_point_id`、content、citation 和 block metadata 字段先定义清楚。

验证方式：
- py_compile 覆盖 v0.4.13.9 builder、v0.4.13.8 checker、FastAPI 版本、health check 和相关单测。
- 单测覆盖 `tests.test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design`、`tests.test_ingestion_metadata_source_patch_check` 和 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown design 报告。
- restricted diff 确认未修改 `src/rag/retriever.py`、规则文件或 eval cases。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。

### v0.4.13.10：Post-Patch Rebuild Dry-Run Design Gate

阶段定位：在 v0.4.13.9 设计完成后，对 post-patch rebuild dry-run design 做只读门禁；本版本只检查设计是否稳定，不创建 runner、不写 Qdrant、不 rebuild、不改 RAG 主链路。

解决的问题：v0.4.13.9 已定义未来 runner，但在真正创建 runner 前，需要确认 source patch 输入、guardrails、sample strategy、comparison fields、output contract、blocking conditions 和 handoff 边界没有漂移。v0.4.13.10 将这一步固化成可重复 gate。

关键输出：
- 新增 `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py`，只读取 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json`。
- 新增 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json`，记录 21 项检查、0 failure，状态为 `passed`。
- 新增 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_v0.4.13.10.md`，记录 gate 摘要和非运行时边界。
- 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py`，覆盖输入漂移、runner creation 权限漂移、sample strategy、comparison fields、output contract、guardrails 和 handoff 边界。

报告写法：
> v0.4.13.10 将 post-patch rebuild dry-run design 固化为 runner 前门禁。该版本确认 v0.4.13.9 的设计完整覆盖 allowed/forbidden inputs、sample strategy、comparison fields、output contract 和 blocking conditions，并继续禁止本版本创建 runner、写 Qdrant、rebuild collection、调用 RAG/LLM/embedding、运行 full eval，或修改 ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。通过后只允许进入 post-patch rebuild dry-run runner，而不是直接重建生产索引。

验证方式：
- py_compile 覆盖 v0.4.13.10 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖 `tests.test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown gate 报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check` 作为收尾检查。
### v0.4.13.11：Post-Patch Rebuild Dry-Run Runner

阶段定位：在 v0.4.13.10 design gate 通过后，创建真正的 post-patch rebuild dry-run runner；本版本只做本地、只读、确定性样本对比，不写 Qdrant、不 rebuild、不改 RAG 主链路。

解决的问题：v0.4.13.8 已补齐普通法律 article/paragraph/item 的 `chunk_index/chunk_count`，但生产 collection rebuild 会物化新的 `chunk_id/qdrant_point_id`。v0.4.13.11 用本地样本模拟 pre-patch metadata，再与当前 post-patch `build_article_documents` 输出比较，确认预期 ID drift 可观测，且 content、citation 和 block identity metadata 没有 forbidden drift。

关键输出：
- 新增 `tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`。
- 输出 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json` 与 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_v0.4.13.11.md`。
- 报告记录 3 个 deterministic samples、9 行对比、9 行 `chunk_index/chunk_count` presence、9 行预期 `chunk_id/qdrant_point_id` drift、0 forbidden drift、0 blocking condition。
- 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`，覆盖默认路径、真实输入、样本形态、row-level drift、输入漂移阻断、forbidden drift 阻断和 Markdown 边界。

报告写法：
> v0.4.13.11 将 post-patch rebuild dry-run 从设计推进到本地 runner。它只读取 v0.4.13.8 source patch、v0.4.13.9 design 和 v0.4.13.10 design gate saved reports，并使用本地 deterministic samples 验证当前 `build_article_documents` 输出已经具备 boundary metadata；同时确认如果未来 rebuild 物化，`chunk_id/qdrant_point_id` 会出现预期漂移，而 content、citation、block metadata 保持稳定。该版本不写 Qdrant，不 rebuild collection，不调用 RAG/LLM/embedding，不运行 full eval，也不修改 ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。通过后只允许进入 runner gate，不能直接重建生产索引。

验证方式：
- py_compile 覆盖 v0.4.13.11 runner、对应单测、health check 和 FastAPI 版本。
- 单测覆盖 `tests.test_ingestion_metadata_patch_post_patch_rebuild_dry_run` 与 `tests.test_project_health_check`。
- 默认生成 JSON/Markdown runner 报告。
- 索引一致性、编码卫生、project health check、restricted diff 和 `git diff --check` 作为收尾检查。
### v0.4.13.12：Post-Patch Rebuild Dry-Run Runner Gate

阶段定位：这是 v0.4.13.11 runner 的只读门禁版本，用于确认 saved runner report 是否足以进入 rebuild authorization design。它不是 production rebuild，不是 Qdrant 写入许可，也不是 full eval。

解决的问题：v0.4.13.11 已经生成 post-patch rebuild dry-run runner report，但仍需要独立 gate 验证该报告的 lineage、summary、sample contract、row contract、comparison contract、guardrails 和 handoff boundaries，避免把一次 runner 输出直接解释为生产 rebuild 授权。

关键输出：

- 新增 `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py`。
- 输出 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json` 与 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_v0.4.13.12.md`。
- 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py`。
- gate 检查确认 3 个样本、9 行对比、9/9 `chunk_index/chunk_count` presence、9/9 expected `chunk_id/qdrant_point_id` drift、0 forbidden drift、0 blocker。

报告写法：

> v0.4.13.12 对 v0.4.13.11 post-patch rebuild dry-run runner 输出进行只读 gate。该 gate 只读取 saved report，不重跑 runner，不重新生成样本，不访问或写入 Qdrant，不 rebuild collection，不调用 `rag_query`、embedding、LLM 或 full eval，也不修改 ingestion/retriever/rerank/prompt/anchor/risk rules/scenario registry/fixtures/eval cases。gate 通过后只开放 `rebuild_authorization_design`，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.13.12 gate、对应单测、health check 和 FastAPI 版本。
- 新增单测覆盖真实报告通过、summary drift、guardrail drift、sample drift、row drift、lineage drift、handoff drift 和 Markdown 边界。
- gate 可在现有 saved report 上运行；未运行 full eval，未访问 Qdrant。

### v0.4.13.13：Rebuild Authorization Design

阶段定位：这是生产 rebuild 授权设计版本，位于 v0.4.13.12 runner gate 之后。它只设计未来授权 envelope，不创建人工授权记录，不访问 Qdrant，不执行 rebuild，也不运行 full eval。

解决的问题：v0.4.13.11/0.4.13.12 已证明 post-patch dry-run 输出稳定，但技术 dry-run 成功不能等同于生产 rebuild 许可。v0.4.13.13 把生产 rebuild 所需的人工确认字段、风险确认、备份回滚和验证计划单独固化。

关键输出：

- 新增 `tools/build_rebuild_authorization_design.py`。
- 输出 `tests/rebuild_authorization_design_report.json` 与 `docs/rebuild_authorization_design_v0.4.13.13.md`。
- 新增 `tests/test_rebuild_authorization_design.py`。
- 设计要求未来授权记录必须确认 `target_collection`、`rebuild_scope`、`source_version`、`expected_id_drift_acknowledgement`、`backup_plan`、`rollback_plan`、`operator_approval`、`maintenance_window`、`post_rebuild_validation_plan` 和 `abort_conditions_acknowledgement`。

报告写法：

> v0.4.13.13 将 post-patch rebuild 从技术 dry-run 推进到生产授权设计。该版本只读取 v0.4.13.12 gate report 与既有 saved reports，定义未来是否允许 rebuild collection 所需的人工确认字段、target collection、backup/rollback plan、risk acknowledgement、dry-run evidence 和 post-rebuild validation；它不访问或写入 Qdrant，不 rebuild collection，不调用 RAG/LLM/embedding，不运行 full eval，也不修改主链路。通过后只允许进入 authorization gate，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.13.13 design、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实输入通过、必填授权字段、runner gate drift、runner summary drift、handoff 边界和 Markdown 边界。
- 默认生成 JSON/Markdown design 报告；未运行 full eval，未访问 Qdrant。

### v0.4.13.14：Rebuild Authorization Design Gate

阶段定位：这是 v0.4.13.13 生产 rebuild 授权设计的只读门禁版本。它只检查 saved design report，不创建人工授权记录，不访问 Qdrant，不执行 rebuild，也不运行 full eval。

解决的问题：v0.4.13.13 定义了授权 envelope，但还需要独立 gate 确认 lineage、必填授权字段、终止条件、output contract 和 handoff boundaries 稳定，防止 design 被误用为生产 rebuild 批准。

关键输出：

- 新增 `tools/check_rebuild_authorization_design_gate.py`。
- 输出 `tests/rebuild_authorization_design_gate_report.json` 与 `docs/rebuild_authorization_design_gate_v0.4.13.14.md`。
- 新增 `tests/test_rebuild_authorization_design_gate.py`。
- gate 检查确认 `authorization_granted=false`、`human_authorization_record_created=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`、`full_eval=not_run`。

报告写法：

> v0.4.13.14 对 v0.4.13.13 rebuild authorization design 执行只读 gate。该 gate 验证来源 lineage、必填授权字段、终止条件、output contract 和 handoff boundaries，同时确认没有创建人工授权记录、没有放开 Qdrant write/rebuild、没有调用 RAG/LLM/embedding、没有运行 full eval。通过后只开放 `human_rebuild_authorization_worksheet`，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.13.14 gate、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实设计通过、lineage drift、授权/rebuild 权限漂移、未来授权记录提前创建、必填字段缺失、终止条件缺失、handoff drift 和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.13.15：Human Rebuild Authorization Worksheet

阶段定位：这是人工 rebuild 授权 worksheet 版本，位于 v0.4.13.14 design gate 之后。它只把授权设计转成可审阅字段表，不收集人工值、不创建授权记录、不执行 rebuild。

解决的问题：生产 rebuild 授权需要用户未来填写和确认多项信息。v0.4.13.15 将 `target_collection`、`rebuild_scope`、`source_version`、`backup_plan`、`rollback_plan`、`operator_approval` 等字段转成 10 行 worksheet，并标明 required/optional 子字段。

关键输出：

- 新增 `tools/build_human_rebuild_authorization_worksheet.py`。
- 输出 `tests/human_rebuild_authorization_worksheet_report.json` 与 `docs/human_rebuild_authorization_worksheet_v0.4.13.15.md`。
- 新增 `tests/test_human_rebuild_authorization_worksheet.py`。
- worksheet 中所有人工值仍为 `not_collected`，`authorization_granted=false`，`rebuild_allowed=false`。

报告写法：

> v0.4.13.15 将 rebuild authorization design 转为人工 review worksheet。该版本只准备字段表和填写提示，不收集人工值、不创建授权记录、不批准 Qdrant write/rebuild、不调用 RAG/LLM/embedding、不运行 full eval。通过后只允许进入 worksheet gate/validation，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.13.15 worksheet、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实输入通过、字段顺序、required/optional 标签、operator approval 不构成批准、abort conditions、gate drift、字段 drift、rebuild permission drift 和 Markdown 边界。
- 默认生成 JSON/Markdown worksheet 报告；未运行 full eval，未访问 Qdrant。

### v0.4.13.16：Human Rebuild Authorization Worksheet Gate

阶段定位：这是 v0.4.13.15 空白授权 worksheet 的只读门禁版本。它只验证 worksheet 结构和未授权边界，不收集人工值、不创建授权记录、不执行 rebuild。

解决的问题：v0.4.13.15 生成了人工授权字段表，但还需要 gate 确认字段顺序、required/optional 标签、0 个已收集人工值，以及 `authorization_granted=false`、`rebuild_allowed=false` 等边界没有漂移。

关键输出：

- 新增 `tools/check_human_rebuild_authorization_worksheet_gate.py`。
- 输出 `tests/human_rebuild_authorization_worksheet_gate_report.json` 与 `docs/human_rebuild_authorization_worksheet_gate_v0.4.13.16.md`。
- 新增 `tests/test_human_rebuild_authorization_worksheet_gate.py`。
- gate 检查确认 worksheet 仍为空白未授权状态。

报告写法：

> v0.4.13.16 对 v0.4.13.15 human rebuild authorization worksheet 执行只读 gate。该 gate 确认 worksheet 的 10 行授权字段、required/optional 标签、未收集人工值和未授权边界稳定；它不创建授权记录、不访问 Qdrant、不 rebuild、不调用 RAG/LLM/embedding、不运行 full eval。通过后只开放 runbook/preflight contract design，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.13.16 gate、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 worksheet 通过、字段顺序、人工值被收集、授权/rebuild 权限漂移、optional 标签缺失和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.13.17：Rebuild Runbook / Preflight Contract

阶段定位：这是未来 rebuild execution series 的 runbook/preflight 契约版本。它只定义未来执行系列需要的阶段、检查项、终止条件和报告字段，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.13.16 已确认 worksheet 结构完整但未授权。v0.4.13.17 将未来执行前需要的 preflight、backup/rollback verification、target collection confirmation、post-rebuild validation 和 abort conditions 固化为契约，供下一系列使用。

关键输出：

- 新增 `tools/build_rebuild_runbook_preflight_contract.py`。
- 输出 `tests/rebuild_runbook_preflight_contract_report.json` 与 `docs/rebuild_runbook_preflight_contract_v0.4.13.17.md`。
- 新增 `tests/test_rebuild_runbook_preflight_contract.py`。
- contract 记录 7 个 runbook phases、8 个 preflight checks、7 个 abort conditions。

报告写法：

> v0.4.13.17 定义未来生产 rebuild execution series 的 runbook/preflight contract。该版本只读取 saved worksheet/gate reports，定义未来执行前的授权记录校验、target collection confirmation、backup/rollback verification、source lineage confirmation、post-rebuild validation 和 abort conditions；它不运行 live preflight、不访问或写入 Qdrant、不 rebuild collection、不调用 RAG/LLM/embedding、不运行 full eval。通过后只开放 v0.4.13 series closeout，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.13.17 contract、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实输入通过、failed gate 阻断、rebuild permission drift 阻断和 Markdown 边界。
- 默认生成 JSON/Markdown contract 报告；未运行 full eval，未访问 Qdrant。

### v0.4.13.18：Ingestion Metadata Rebuild Planning Series Closeout

阶段定位：这是 v0.4.13 ingestion metadata patch and rebuild planning series 的收口版本。它只读取 saved reports，总结源码补丁、post-patch dry-run、授权设计、人工授权 worksheet 和 runbook/preflight contract，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.13.8 已完成最小 ingestion metadata source patch，v0.4.13.11-v0.4.13.12 已用 post-patch dry-run 证明 metadata presence 与 expected ID drift 可观测，v0.4.13.13-v0.4.13.17 已把生产 rebuild 前的授权、worksheet 和 preflight 契约拆开。v0.4.13.18 负责把这一系列关闭，并把未来工作限定为单独的 `production_rebuild_execution_design`。

关键输出：

- 新增 `tools/build_ingestion_metadata_rebuild_planning_series_closeout.py`。
- 输出 `tests/ingestion_metadata_rebuild_planning_series_closeout_report.json` 与 `docs/ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md`。
- 新增 `tests/test_ingestion_metadata_rebuild_planning_series_closeout.py`。
- closeout 检查 v0.4.13.13-v0.4.13.17 source lineage、allowed next step、授权/rebuild/Qdrant/full eval 边界和 guardrail drift。

报告写法：

> v0.4.13.18 对 ingestion metadata patch and rebuild planning series 进行收口。该版本只读取既有 saved reports，确认本系列已经完成从 metadata root-cause、最小源码 patch、post-patch dry-run，到生产 rebuild 授权设计、人工 worksheet 和 runbook/preflight contract 的治理闭环。它不运行 live preflight、不访问或写入 Qdrant、不 rebuild collection、不调用 RAG/LLM/embedding、不运行 full eval，也不修改 prompt、rerank、anchors、risk rules、scenario registry、fixtures 或 eval cases。通过后唯一开放的下一步是 `production_rebuild_execution_design`，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.13.18 closeout 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实输入通过、source lineage、缺失 source 阻断、version/schema/status/next-step drift、授权/rebuild 权限漂移、guardrail drift 与 Markdown 边界。
- 默认生成 JSON/Markdown closeout 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.0：Production Rebuild Execution Design

阶段定位：这是生产 rebuild 执行系列的设计版本。它位于 v0.4.13 planning closeout 之后，只定义未来执行所需的记录契约、阶段顺序、preflight checks、rollback/backup 校验、post-rebuild validation 和 abort/acceptance decision，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.13 已经完成 ingestion metadata patch、post-patch rebuild dry-run、授权设计、人工授权 worksheet、runbook/preflight contract 和 planning closeout，但这仍不等于生产 rebuild 授权。v0.4.14.0 把未来真正执行前必须留下的审计记录、阻断条件和验收口径先设计清楚，避免把 closeout 误解为可以直接写 Qdrant。

关键输出：

- 新增 `tools/build_production_rebuild_execution_design.py`。
- 输出 `tests/production_rebuild_execution_design_report.json` 与 `docs/production_rebuild_execution_design_v0.4.14.0.md`。
- 新增 `tests/test_production_rebuild_execution_design.py`。
- design 定义 5 类 record contracts、7 个 execution phases、8 个 preflight checks 和 9 个 abort conditions。

报告写法：

> v0.4.14.0 将生产 rebuild 从“计划收口”推进到“执行设计”。该版本只读取 v0.4.13.18 closeout report，定义未来执行系列必须具备的 `preflight_record`、`backup_or_rollback_record`、`rebuild_execution_record`、`post_rebuild_validation_record` 和 `abort_or_acceptance_decision_record`。它不创建或接受人工授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection，不调用 RAG/LLM/embedding，不运行 full eval，也不修改 ingestion、retriever、prompt、rerank、anchors、risk rules、scenario registry、fixtures 或 eval cases。通过后只开放 `production_rebuild_execution_design_gate`，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.0 design 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖 `tests.test_production_rebuild_execution_design` 与 `tests.test_project_health_check`。
- 单测覆盖真实 closeout 输入通过、closeout-only source lineage、record contract counts、缺失 closeout 阻断、version/schema/status/next-step drift、授权/rebuild/live preflight 权限漂移、guardrail drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown design 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.1：Production Rebuild Execution Design Gate

阶段定位：这是 v0.4.14.0 execution design 的只读门禁版本。它只检查 design report 的记录契约、阶段顺序、preflight checks、abort conditions、guardrails 和 handoff boundary，不创建或接受人工授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.0 已经设计了未来执行系列，但设计本身仍需要 gate 来防止“设计完成”被误解为“可以执行”。v0.4.14.1 将这一点固化为可重复检查，确认所有生产动作仍被阻断。

关键输出：

- 新增 `tools/check_production_rebuild_execution_design_gate.py`。
- 输出 `tests/production_rebuild_execution_design_gate_report.json` 与 `docs/production_rebuild_execution_design_gate_v0.4.14.1.md`。
- 新增 `tests/test_production_rebuild_execution_design_gate.py`。
- gate 记录 16 项检查、0 failure，并只开放 `human_rebuild_authorization_record_scaffold`。

报告写法：

> v0.4.14.1 对 production rebuild execution design 执行只读 gate。该版本确认 v0.4.14.0 的 closeout-only lineage、5 类 record contracts、7 个 execution phases、8 个 preflight checks、9 个 abort conditions、decision policy 和 handoff boundaries 稳定；同时继续禁止创建或接受人工授权记录、运行 live preflight、访问或写入 Qdrant、rebuild collection、调用 RAG/LLM/embedding、运行 full eval，或修改 runtime、ingestion、retriever、prompt、rerank、anchors、risk rules、scenario registry、fixtures、eval cases。通过后只开放 `human_rebuild_authorization_record_scaffold`，仍不代表已经允许生产 Qdrant rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.1 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 design 通过、closeout lineage drift、授权/执行权限漂移、guardrail drift、record contract 缺失或额外混入、preflight check drift、abort condition drift、rebuild record 提前创建、decision policy drift、handoff drift 和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.2：Human Rebuild Authorization Record Scaffold

阶段定位：这是生产 rebuild 人工授权记录的空白 scaffold 版本。它只把 v0.4.14.0 design 中要求的授权字段转成未来正式记录模板，不收集人工值，不创建或接受授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.1 已确认 execution design gate 通过，但下一步不能直接让用户“口头同意”或把 worksheet 当作授权。v0.4.14.2 先定义未来正式授权记录应有哪些字段、字段填写提示和阻断边界，并把所有值保持为 `not_collected`。

关键输出：

- 新增 `tools/build_human_rebuild_authorization_record_scaffold.py`。
- 输出 `tests/human_rebuild_authorization_record_scaffold_report.json` 与 `docs/human_rebuild_authorization_record_scaffold_v0.4.14.2.md`。
- 新增 `tests/test_human_rebuild_authorization_record_scaffold.py`。
- scaffold 记录 10 个授权字段、0 个已收集人工值，并只开放 `human_rebuild_authorization_record_scaffold_gate`。

报告写法：

> v0.4.14.2 将 production rebuild 的人工授权记录先固化为空白 scaffold。该版本只读取 v0.4.14.0 execution design 与 v0.4.14.1 gate，生成 `target_collection`、`rebuild_scope`、`source_version`、`expected_id_drift_acknowledgement`、`backup_plan`、`rollback_plan`、`operator_approval`、`maintenance_window`、`post_rebuild_validation_plan` 和 `abort_conditions_acknowledgement` 10 个未来授权字段。所有字段均保持 `not_collected` / `null`，`human_authorization_record_created=false`，`human_authorization_record_accepted=false`，`authorization_granted=false`，`qdrant_write_allowed=false`，`rebuild_allowed=false`。通过后只开放 scaffold gate，仍不代表已经允许 live preflight、Qdrant write 或 production rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.2 scaffold 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 design/gate 输入通过、input lineage drift、权限漂移、字段顺序、`operator_approval` 不构成当前批准、已填值/授权漂移、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown scaffold 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.3：Human Rebuild Authorization Record Scaffold Gate

阶段定位：这是 v0.4.14.2 空白授权记录 scaffold 的只读门禁版本。它只检查 scaffold saved report 的版本、schema、source lineage、guardrails、字段顺序、空白值、packet、handoff 和 assertions，不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.2 生成了未来正式授权记录的空白 scaffold，但 scaffold 本身仍需要 gate 来防止它被误用成授权记录或执行许可。v0.4.14.3 将“空白、未授权、不可执行”固化为可重复检查。

关键输出：

- 新增 `tools/check_human_rebuild_authorization_record_scaffold_gate.py`。
- 输出 `tests/human_rebuild_authorization_record_scaffold_gate_report.json` 与 `docs/human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md`。
- 新增 `tests/test_human_rebuild_authorization_record_scaffold_gate.py`。
- gate 记录 13 项检查、0 failure，并只开放 `human_rebuild_authorization_record_draft_design`。

报告写法：

> v0.4.14.3 对 human rebuild authorization record scaffold 执行只读 gate。该版本确认 v0.4.14.2 scaffold 的 10 个授权字段顺序、`not_collected` 空白值、`formal_authorization_record_created=false`、`authorization_granted=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`、guardrails、packet 和 handoff boundary 均稳定。通过后只开放 `human_rebuild_authorization_record_draft_design`，仍不代表已经允许填写正式授权、运行 live preflight、写入 Qdrant 或执行生产 rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.3 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 scaffold 通过、status/source lineage drift、人工值/授权漂移、guardrail drift、row blank contract drift、input contract drift、packet/handoff drift、assertion drift 和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.4：Human Rebuild Authorization Record Draft Design

阶段定位：这是未来正式授权记录草案的设计版本。它只把 v0.4.14.2 scaffold 中的 10 个授权字段映射成草案字段、分区结构和未来校验口径，不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.3 已确认空白 scaffold 稳定，但系统仍需要先定义未来正式授权记录草案的结构，避免后续人工填写时字段、顺序、审批语义和执行许可混淆。v0.4.14.4 将草案结构设计为 7 个分区和 10 个字段映射，并保持所有值为空。

关键输出：

- 新增 `tools/build_human_rebuild_authorization_record_draft_design.py`。
- 输出 `tests/human_rebuild_authorization_record_draft_design_report.json` 与 `docs/human_rebuild_authorization_record_draft_design_v0.4.14.4.md`。
- 新增 `tests/test_human_rebuild_authorization_record_draft_design.py`。
- draft design 记录 10 个字段映射、7 个草案分区、0 个已收集人工值，并只开放 `human_rebuild_authorization_record_draft_design_gate`。

报告写法：

> v0.4.14.4 将 human rebuild authorization record scaffold 推进到 draft design。该版本只读取 v0.4.14.2 scaffold 与 v0.4.14.3 gate，设计 `target_collection`、`rebuild_scope`、`source_version`、`expected_id_drift_acknowledgement`、`backup_plan`、`rollback_plan`、`operator_approval`、`maintenance_window`、`post_rebuild_validation_plan` 和 `abort_conditions_acknowledgement` 10 个字段的正式授权记录草案映射，并分为 target/scope、source lineage、risk acknowledgement、safeguards、formal authorization inputs、execution window 和 post-rebuild validation 7 个分区。所有字段仍为 `not_collected` / `null`，`draft_record_created=false`，`formal_authorization_record_created=false`，`authorization_granted=false`，`qdrant_write_allowed=false`，`rebuild_allowed=false`。通过后只开放 draft design gate，仍不代表已经允许填写正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.4 draft design 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 scaffold/gate 输入通过、scaffold/gate drift、字段顺序与空值、`operator_approval` 不构成当前批准、权限漂移、guardrail/contract drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown draft design 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.5：Human Rebuild Authorization Record Draft Design Gate

阶段定位：这是 v0.4.14.4 draft design 的只读门禁版本。它只检查正式授权记录草案设计的字段映射、分区顺序、空值状态、guardrails、future validation policy、handoff 和 forbidden output key 边界，不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.4 已经定义未来正式授权记录草案结构，但设计本身仍需要 gate 来防止“草案设计完成”被误解为“可以填写真实授权值”或“可以进入执行”。v0.4.14.5 将该边界固化为 13 项可重复检查，并只开放下一步空白 draft scaffold。

关键输出：

- 新增 `tools/check_human_rebuild_authorization_record_draft_design_gate.py`。
- 输出 `tests/human_rebuild_authorization_record_draft_design_gate_report.json` 与 `docs/human_rebuild_authorization_record_draft_design_gate_v0.4.14.5.md`。
- 新增 `tests/test_human_rebuild_authorization_record_draft_design_gate.py`。
- gate 记录 13 项检查、0 failure，并只开放 `human_rebuild_authorization_record_draft_scaffold`。

报告写法：

> v0.4.14.5 对 human rebuild authorization record draft design 执行只读 gate。该版本确认 v0.4.14.4 draft design 的 v0.4.14.2/v0.4.14.3 saved-report lineage、10 个字段映射、7 个草案分区、空值状态、future validation policy、guardrails、handoff boundary 和 forbidden output key 边界稳定。通过后只开放 `human_rebuild_authorization_record_draft_scaffold`，仍不代表已经允许填写真实人工值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.5 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 draft design 通过、status/source lineage drift、人工值/授权漂移、internal gate/guardrail drift、section/field mapping drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.6：Human Rebuild Authorization Record Draft Scaffold

阶段定位：这是未来正式授权记录的空白草案 scaffold 版本。它只把 v0.4.14.4 draft design 中的字段映射和分区结构转成未来可填写的空白 scaffold，不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.5 已确认 draft design 稳定，但下一步仍不能让用户直接填写真实审批值。v0.4.14.6 先生成空白草案 scaffold，把 10 个字段、7 个分区、填写提示和未来校验策略固化下来，同时继续保持 `not_collected` / `null`。

关键输出：

- 新增 `tools/build_human_rebuild_authorization_record_draft_scaffold.py`。
- 输出 `tests/human_rebuild_authorization_record_draft_scaffold_report.json` 与 `docs/human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md`。
- 新增 `tests/test_human_rebuild_authorization_record_draft_scaffold.py`。
- draft scaffold 记录 10 个空白字段、7 个分区、0 个已收集人工值，并只开放 `human_rebuild_authorization_record_draft_scaffold_gate`。

报告写法：

> v0.4.14.6 将 human rebuild authorization record draft design 推进为空白 draft scaffold。该版本只读取 v0.4.14.4 draft design 与 v0.4.14.5 gate，生成 10 个未来授权字段、7 个分区、字段填写顺序和 future validation policy。所有字段仍为 `not_collected` / `null`，`draft_record_created=false`，`formal_authorization_record_created=false`，`authorization_granted=false`，`qdrant_write_allowed=false`，`rebuild_allowed=false`。通过后只开放 `human_rebuild_authorization_record_draft_scaffold_gate`，仍不代表已经允许填写真实人工值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.6 draft scaffold 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 draft design/gate 输入通过、字段顺序与空值、分区契约、`operator_approval` 不构成当前批准、design/gate drift、权限漂移、section/field mapping drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown draft scaffold 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.7：Human Rebuild Authorization Record Draft Scaffold Gate

阶段定位：这是 v0.4.14.6 空白 draft scaffold 的只读门禁版本。它只检查 scaffold 的字段顺序、分区、空值状态、guardrails、future validation policy、handoff 和 forbidden output key 边界，不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.6 生成了空白 scaffold，但 scaffold 本身仍需要 gate 来防止它被误用成正式授权记录或执行许可。v0.4.14.7 将“空白、未授权、不可执行”固化为 13 项检查，并只开放下一步人工输入流程设计。

关键输出：

- 新增 `tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py`。
- 输出 `tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json` 与 `docs/human_rebuild_authorization_record_draft_scaffold_gate_v0.4.14.7.md`。
- 新增 `tests/test_human_rebuild_authorization_record_draft_scaffold_gate.py`。
- gate 记录 13 项检查、0 failure，并只开放 `human_rebuild_authorization_record_input_workflow_design`。

报告写法：

> v0.4.14.7 对 human rebuild authorization record draft scaffold 执行只读 gate。该版本确认 v0.4.14.6 的 10 个空白字段、7 个分区、`not_collected` / `null` 空值、future validation policy、guardrails、handoff boundary 和 forbidden output key 边界稳定。通过后只开放 `human_rebuild_authorization_record_input_workflow_design`，仍不代表已经允许填写真实人工值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.7 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 scaffold 通过、status/source lineage drift、人工值/授权漂移、internal gate/guardrail drift、section/row drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.8：Human Rebuild Authorization Record Input Workflow Design

阶段定位：这是未来人工授权输入流程的设计版本。它只把 v0.4.14.6 空白 draft scaffold 和 v0.4.14.7 gate 转成未来人工输入、导入、校验、确认和 handoff 的流程蓝图，不收集真实人工值，不创建输入表单或 importer，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.7 已确认空白 scaffold 稳定，但下一步仍不能直接开放输入入口。v0.4.14.8 先定义未来输入流程的 6 个阶段和 10 个字段输入契约，明确“完整性校验”和“授权成立”分离，避免把未来校验流程误解为当前授权或执行许可。

关键输出：

- 新增 `tools/build_human_rebuild_authorization_record_input_workflow_design.py`。
- 输出 `tests/human_rebuild_authorization_record_input_workflow_design_report.json` 与 `docs/human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md`。
- 新增 `tests/test_human_rebuild_authorization_record_input_workflow_design.py`。
- design 记录 6 个未来流程阶段、10 个字段输入契约、0 个已收集人工值，并只开放 `human_rebuild_authorization_record_input_workflow_design_gate`。

报告写法：

> v0.4.14.8 将 human rebuild authorization record draft scaffold gate 推进到 input workflow design。该版本只读取 v0.4.14.6 空白 draft scaffold 与 v0.4.14.7 gate，设计未来人工输入、导入、校验、确认和 formal record candidate handoff 的流程蓝图。所有字段仍为 `not_collected` / `null`，`input_form_created=false`，`input_values_imported=false`，`input_values_validated=false`，`formal_authorization_record_created=false`，`authorization_granted=false`，`qdrant_write_allowed=false`，`rebuild_allowed=false`。通过后只开放 `human_rebuild_authorization_record_input_workflow_design_gate`，仍不代表已经允许填写真实人工值、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：

- py_compile 覆盖 v0.4.14.8 input workflow design 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 draft scaffold/gate 输入通过、字段输入契约顺序和空值、workflow phases design-only、`operator_approval` 不构成当前批准、scaffold/gate drift、权限漂移、row/section drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown input workflow design 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.9：Human Rebuild Authorization Record Input Workflow Design Gate

阶段定位：这是 v0.4.14.8 input workflow design 的只读门禁版本。它只检查已保存的流程设计报告，不收集人工值，不创建输入表单或 importer，不导入或校验真实审批值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.8 已定义未来人工输入、导入、校验、确认和 handoff 流程，但设计本身仍需 gate 防止被误解为“可以开始填值或授权”。v0.4.14.9 将流程阶段、字段输入契约、future validation/import policy、guardrails、handoff 和 forbidden output key 边界固化为 14 项可重复检查。

关键输出：
- 新增 `tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py`。
- 输出 `tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json` 与 `docs/human_rebuild_authorization_record_input_workflow_design_gate_v0.4.14.9.md`。
- 新增 `tests/test_human_rebuild_authorization_record_input_workflow_design_gate.py`。
- gate 记录 14 项检查、0 failure，并只开放 `human_rebuild_authorization_record_input_packet_scaffold`。

报告写法：
> v0.4.14.9 对 human rebuild authorization record input workflow design 执行只读 gate。该版本确认 v0.4.14.8 的 6 个未来流程阶段、10 个字段输入契约、0 个已收集人工值、`input_form_created=false`、`input_values_imported=false`、`input_values_validated=false`、`formal_authorization_record_created=false`、`authorization_granted=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`、future validation/import policy、guardrails、handoff boundary 和 forbidden output key 边界稳定。通过后只开放 `human_rebuild_authorization_record_input_packet_scaffold`，仍不代表已经允许填写真实人工值、创建输入入口、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.9 input workflow design gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 v0.4.14.8 design 通过、status/source lineage drift、人工值/权限漂移、internal gate/guardrail drift、workflow phase drift、field contract drift、future policy/import policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.10：Human Rebuild Authorization Record Input Packet Scaffold

阶段定位：这是未来人工授权输入包的空白 scaffold 版本。它只把 v0.4.14.8 input workflow design 与 v0.4.14.9 gate 中已经通过的字段、分区和输入流程转成未来可填的 input packet scaffold，不收集人工值，不创建输入表单或 importer，不导入或校验真实审批值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.9 已确认输入流程设计稳定，但仍不能直接进入真实填写或授权。v0.4.14.10 先生成 10 个字段、7 个分区的空白 input packet scaffold，并把每个字段固定为 `blank` / `not_collected` / `not_imported` / `not_run`，让下一步 gate 可以检查输入包结构，而不是检查真实审批内容。

关键输出：
- 新增 `tools/build_human_rebuild_authorization_record_input_packet_scaffold.py`。
- 输出 `tests/human_rebuild_authorization_record_input_packet_scaffold_report.json` 与 `docs/human_rebuild_authorization_record_input_packet_scaffold_v0.4.14.10.md`。
- 新增 `tests/test_human_rebuild_authorization_record_input_packet_scaffold.py`。
- scaffold 记录 10 个未来输入字段、7 个分区、0 个已收集人工值，并只开放 `human_rebuild_authorization_record_input_packet_scaffold_gate`。

报告写法：
> v0.4.14.10 将 human rebuild authorization record input workflow design gate 推进为空白 input packet scaffold。该版本只读取 v0.4.14.8 workflow design 与 v0.4.14.9 gate，生成 `target_collection`、`rebuild_scope`、`source_version`、`expected_id_drift_acknowledgement`、`backup_plan`、`rollback_plan`、`operator_approval`、`maintenance_window`、`post_rebuild_validation_plan` 和 `abort_conditions_acknowledgement` 10 个未来输入字段，并按 target/scope、source lineage、risk acknowledgement、safeguards、formal authorization inputs、execution window 和 post-rebuild validation 7 个分区组织。所有字段仍为 `blank` / `not_collected` / `null`，`input_form_created=false`，`input_values_imported=false`，`input_values_validated=false`，`formal_authorization_record_created=false`，`authorization_granted=false`，`qdrant_write_allowed=false`，`rebuild_allowed=false`。通过后只开放 input packet scaffold gate，仍不代表已经允许填写真实人工值、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.10 input packet scaffold 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 workflow design/gate 输入通过、字段顺序与空值、分区契约、`operator_approval` 不构成当前批准、source lineage drift、权限漂移、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown input packet scaffold 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.11：Human Rebuild Authorization Record Input Packet Scaffold Gate

阶段定位：这是 v0.4.14.10 空白 input packet scaffold 的只读门禁版本。它只检查已保存的 scaffold report，不创建输入表单或 importer，不收集、导入或校验真实审批值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.10 已生成未来人工输入包的空白 scaffold，但 scaffold 本身仍需要 gate 来防止它被误用成可填写表单、importer 或授权记录。v0.4.14.11 将字段顺序、分区、空值状态、import/validation 状态、future validation/import policy、packet completion policy、handoff 和 forbidden output key 边界固化为 16 项可重复检查。

关键输出：
- 新增 `tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py`。
- 输出 `tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json` 与 `docs/human_rebuild_authorization_record_input_packet_scaffold_gate_v0.4.14.11.md`。
- 新增 `tests/test_human_rebuild_authorization_record_input_packet_scaffold_gate.py`。
- gate 记录 16 项检查、0 failure，并只开放 `human_rebuild_authorization_record_input_form_scaffold`。

报告写法：
> v0.4.14.11 对 human rebuild authorization record input packet scaffold 执行只读 gate。该版本确认 v0.4.14.10 的 10 个空白输入字段、7 个分区、`blank` / `not_collected` / `not_imported` / `not_run` 状态、`operator_approval` future-only 语义、future validation/import policy、packet completion policy、guardrails、handoff boundary 和 forbidden output key 边界稳定。通过后只开放 `human_rebuild_authorization_record_input_form_scaffold`，仍不代表已经允许填写真实人工值、创建 importer、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.11 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 v0.4.14.10 scaffold 通过、status/source lineage drift、人工值/import/validation/authorization/Qdrant/rebuild 权限漂移、internal gate/guardrail drift、section/row contract drift、`operator_approval` current authorization drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.12：Human Rebuild Authorization Record Input Form Scaffold

阶段定位：这是未来人工授权输入表单的空白 scaffold 版本。它只把 v0.4.14.10 input packet scaffold 与 v0.4.14.11 gate 中已经通过的字段、分区、空值状态和 future policy 转成表单结构说明，不创建可运行输入表单或 importer，不收集、导出、导入或校验真实审批值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.11 已确认空白 input packet scaffold 稳定，但仍不能直接开放真实填写界面。v0.4.14.12 先生成 10 个空白表单字段、7 个分区、中文标签、未来控件提示、帮助文本和 form completion/export policy，让下一步 gate 可以检查表单结构，而不是检查真实输入内容。

关键输出：
- 新增 `tools/build_human_rebuild_authorization_record_input_form_scaffold.py`。
- 输出 `tests/human_rebuild_authorization_record_input_form_scaffold_report.json` 与 `docs/human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md`。
- 新增 `tests/test_human_rebuild_authorization_record_input_form_scaffold.py`。
- scaffold 记录 10 个未来表单字段、7 个分区、0 个已收集人工值，并只开放 `human_rebuild_authorization_record_input_form_scaffold_gate`。

报告写法：
> v0.4.14.12 将 human rebuild authorization record input packet scaffold gate 推进为空白 input form scaffold。该版本只读取 v0.4.14.10 packet scaffold 与 v0.4.14.11 gate，生成 `target_collection`、`rebuild_scope`、`source_version`、`expected_id_drift_acknowledgement`、`backup_plan`、`rollback_plan`、`operator_approval`、`maintenance_window`、`post_rebuild_validation_plan` 和 `abort_conditions_acknowledgement` 10 个未来表单字段，并提供中文标签、未来控件提示和帮助文本。所有字段仍为不可编辑、`blank` / `not_collected` / `null`，`runnable_input_form_created=false`，`input_importer_created=false`，`form_values_exported=false`，`input_values_imported=false`，`input_values_validated=false`，`authorization_granted=false`，`qdrant_write_allowed=false`，`rebuild_allowed=false`。通过后只开放 input form scaffold gate，仍不代表已经允许填写真实人工值、创建 importer、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.12 input form scaffold 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 packet scaffold/gate 输入通过、字段顺序与空值、分区契约、中文标签、未来控件提示、不可编辑/不可提交/不可导出/不可导入状态、`operator_approval` 不构成当前批准、source drift、policy/handoff/traceability drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown input form scaffold 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.13：Human Rebuild Authorization Record Input Form Scaffold Gate

阶段定位：这是 v0.4.14.12 空白 input form scaffold 的只读门禁版本。它只检查已保存的 scaffold report，不创建可运行输入表单或 importer，不收集、导出、导入或校验真实审批值，不创建或接受正式授权记录，不运行 live preflight，不访问 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.12 已生成未来人工授权输入表单结构，但该结构仍需要 gate 来防止它被误用成可填写表单、提交入口、importer 或授权记录。v0.4.14.13 将字段顺序、分区、中文标签、未来控件提示、空值状态、form completion/export policy、guardrails、handoff 和 forbidden output key 边界固化为 17 项可重复检查。

关键输出：
- 新增 `tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py`。
- 输出 `tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json` 与 `docs/human_rebuild_authorization_record_input_form_scaffold_gate_v0.4.14.13.md`。
- 新增 `tests/test_human_rebuild_authorization_record_input_form_scaffold_gate.py`。
- gate 记录 17 项检查、0 failure，并只开放 `human_rebuild_authorization_record_input_importer_design`。

报告写法：
> v0.4.14.13 对 human rebuild authorization record input form scaffold 执行只读 gate。该版本确认 v0.4.14.12 的 10 个空白表单字段、7 个分区、中文标签、未来控件提示、`blank` / `not_collected` / `not_imported` / `not_run` 状态、`operator_approval` future-only 语义、future validation/import policy、form completion/export policy、guardrails、handoff boundary 和 forbidden output key 边界稳定。通过后只开放 `human_rebuild_authorization_record_input_importer_design`，仍不代表已经允许填写真实人工值、创建 importer、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.13 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 v0.4.14.12 scaffold 通过、status/source lineage drift、人工值/form/export/import/validation/authorization/Qdrant/rebuild 权限漂移、internal gate/guardrail drift、section/field contract drift、`operator_approval` current authorization drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.14：Production Rebuild Readiness Cutoff

阶段定位：这是 v0.4.14 生产 rebuild 执行前的收口判断版本。它只读取已保存报告，判断是否应停止继续扩 `input/importer scaffold` 链条，并将下一步切换为 live preflight runner 的工程设计；不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.2-v0.4.14.13 已连续生成 authorization/input scaffold 与 gate，但继续做 importer/input scaffold 会把项目拖回治理报告堆叠。v0.4.14.14 用 cutoff 明确：source patch、post-patch dry-run、authorization chain、execution design、input scaffold gate 与 project health 已满足转入 live preflight runner design 的最低条件；剩下的阻断项是执行前真实条件，不应再用 scaffold 报告替代。

关键输出：
- 新增 `tools/build_production_rebuild_readiness_cutoff.py`。
- 输出 `tests/production_rebuild_readiness_cutoff_report.json` 与 `docs/production_rebuild_readiness_cutoff_v0.4.14.14.md`。
- 新增 `tests/test_production_rebuild_readiness_cutoff.py`。
- cutoff 状态为 `ready_for_live_preflight_runner_design_cutoff`，只开放 `production_rebuild_live_preflight_runner_design`。

报告写法：
> v0.4.14.14 对生产 rebuild 前治理链条执行 readiness cutoff。该版本确认 v0.4.13.8 source patch、v0.4.13.11/12 post-patch dry-run、v0.4.13.13-v0.4.13.17 authorization/runbook 链、v0.4.13.18 closeout、v0.4.14.0/1 execution design gate、v0.4.14.13 input form scaffold gate 与当前 project health 均满足进入 live preflight runner design 的最低条件。因此本版本停止继续扩 `input/importer scaffold`，下一步只开放 `production_rebuild_live_preflight_runner_design`。这仍不代表已经允许运行 live preflight、创建或接受正式人工授权、访问或写入 Qdrant、切换 collection 或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.14 cutoff 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 saved reports 通过、source patch/dry-run drift、authorization/execution/input gate drift、project health drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown cutoff 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.15：Production Rebuild Live Preflight Runner Design

阶段定位：这是生产 rebuild 前 live preflight runner 的最小设计版本。它只读取 v0.4.14.14 readiness cutoff report，把未来 runner 要检查的输入、检查项、输出字段和阻断条件固化为契约；不创建 runner，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.14 已经停止继续扩 `input/importer scaffold`，但下一步不能直接跑生产 preflight。v0.4.14.15 将执行前真实条件压成最小 runner 设计：正式授权记录、目标 collection、backup/snapshot、source lineage、expected ID drift、维护窗口、post-rebuild validation plan 等都只能作为未来检查项，不得被解释为当前授权或执行许可。

关键输出：
- 新增 `tools/build_production_rebuild_live_preflight_runner_design.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_design_report.json` 与 `docs/production_rebuild_live_preflight_runner_design_v0.4.14.15.md`。
- 新增 `tests/test_production_rebuild_live_preflight_runner_design.py`。
- design 状态为 `ready_for_live_preflight_runner_design_gate`，只开放 `production_rebuild_live_preflight_runner_design_gate`。

报告写法：
> v0.4.14.15 将 production rebuild live preflight runner 固化为 design-only 契约。该版本只读取 v0.4.14.14 readiness cutoff，定义 6 个 future inputs、8 个 preflight checks、10 个 output fields 与 8 个 blocking conditions。它继续禁止 `input/importer scaffold` 扩张，不创建 runner，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权，不执行 production rebuild，也不修改 RAG 主流程、prompt、rerank、anchor、risk rules 或 eval cases。通过后只开放 `production_rebuild_live_preflight_runner_design_gate`。

验证方式：
- py_compile 覆盖 v0.4.14.15 design 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 cutoff 输入通过、cutoff status/next-step drift、权限漂移、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown design 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.16：Production Rebuild Live Preflight Runner Design Gate

阶段定位：这是 v0.4.14.15 live preflight runner design 的只读门禁版本。它只检查已保存的 design report，不创建 runner，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不执行 rebuild。

解决的问题：v0.4.14.15 已把未来 runner 契约固化，但在进入最小实现设计前，需要确认它没有把 future inputs 误写成当前授权、没有打开 Qdrant 或 rebuild 权限、没有回到 input/importer scaffold 扩张。v0.4.14.16 将 lineage、summary、guardrails、future inputs、preflight checks、output fields、blocking conditions、fail-closed contract、scaffold cutoff policy 和 forbidden output key 边界固化为 15 项可重复检查。

关键输出：
- 新增 `tools/check_production_rebuild_live_preflight_runner_design_gate.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_design_gate_report.json` 与 `docs/production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md`。
- 新增 `tests/test_production_rebuild_live_preflight_runner_design_gate.py`。
- gate 记录 15 项检查、0 failure，并只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design`。

报告写法：
> v0.4.14.16 对 production rebuild live preflight runner design 执行只读 gate。该版本确认 v0.4.14.15 的唯一 lineage 为 v0.4.14.14 readiness cutoff，summary 未授权 runner 创建/执行、live preflight、Qdrant write、production rebuild 或 full eval；同时确认 6 个 future inputs、8 个 preflight checks、10 个 output fields、8 个 blocking conditions、fail-closed contract 和 scaffold cutoff policy 稳定。通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design`，仍不代表已经允许创建或运行 runner、访问或写入 Qdrant、创建或接受正式授权或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.16 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 design 通过、status/lineage drift、contract drift、权限/guardrail/scaffold drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.17：Production Rebuild Live Preflight Runner Minimal Implementation Design

阶段定位：这是未来 live preflight runner 的最小实现设计版本。它只读取 v0.4.14.16 design gate report，定义未来 runner 文件边界、CLI/函数契约、只读策略、mock 测试策略和 fail-closed 规则；不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.16 已确认 runner design gate 通过，但仍不能直接创建或运行 runner。v0.4.14.17 将实现前必须确定的边界前置：未来 entrypoint、测试文件、输出报告路径、CLI 参数形态、函数输入/返回契约、只读 probe 抽象、mock-only 测试策略和 fail-closed 行为。该版本刻意不提供真实 Qdrant 连接参数或可执行命令。

关键输出：
- 新增 `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json` 与 `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_v0.4.14.17.md`。
- 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_design.py`。
- design 状态为 `ready_for_minimal_implementation_design_gate`，只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design_gate`。

报告写法：
> v0.4.14.17 将 production rebuild live preflight runner 的最小实现边界固化为 design-only 契约。该版本只读取 v0.4.14.16 design gate，定义未来 runner entrypoint、mock-only 测试文件、未来输出报告、CLI/函数契约、只读策略、6 个 mock tests 和 6 个 fail-closed rules。它不创建 `tools/run_production_rebuild_live_preflight.py`，不提供真实 Qdrant 连接参数，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权，不执行 production rebuild。通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design_gate`。

验证方式：
- py_compile 覆盖 v0.4.14.17 design 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 gate 输入通过、gate status/next-step drift、权限漂移、forbidden output key drift、CLI 输出一致性、runtime service import 禁止、无 Qdrant 连接参数和 Markdown 边界。
- 默认生成 JSON/Markdown design 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.18：Production Rebuild Live Preflight Runner Minimal Implementation Design Gate

阶段定位：这是 v0.4.14.17 minimal implementation design 的只读门禁版本。它只检查已保存的 design report，不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权记录，不执行 rebuild。

解决的问题：v0.4.14.17 已定义未来 runner 的实现边界，但仍需要 gate 防止实现设计被误读成可创建 runner 或可连接 Qdrant。v0.4.14.18 将 future files、CLI/function contract、read-only strategy、mock test strategy、fail-closed rules、guardrails 和 forbidden output key 边界固化为 15 项可重复检查，并确认未来 runner 文件仍不存在。

关键输出：
- 新增 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json` 与 `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_v0.4.14.18.md`。
- 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py`。
- gate 记录 15 项检查、0 failure，并只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design`。

报告写法：
> v0.4.14.18 对 production rebuild live preflight runner minimal implementation design 执行只读 gate。该版本确认 v0.4.14.17 的唯一 lineage 为 v0.4.14.16 design gate，summary 未授权 runner 文件创建、runner 执行、live preflight、Qdrant access/write、production rebuild 或 full eval；同时确认 3 个 future files 均未创建，CLI/function contract、read-only strategy、6 个 mock tests、6 个 fail-closed rules 和 forbidden output key 边界稳定。通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design`，仍不代表已经允许创建或运行 runner、访问或写入 Qdrant、创建或接受正式授权或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.18 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 design 通过、status/lineage drift、future file/CLI drift、权限/strategy drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.19：Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design

阶段定位：这是未来 live preflight runner 最小 scaffold 的设计版本。它只读取 v0.4.14.18 implementation design gate report，定义未来 scaffold 的文件结构、不可执行占位策略、mock-only test shape、fail-closed defaults 和禁止内容；不创建 runner 文件、未来测试文件或未来输出报告，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.18 已确认最小实现设计 gate 通过，但仍不能直接创建 runner 文件。v0.4.14.19 将未来 scaffold 的文件角色和内容边界写清楚：entrypoint 只能是不可执行占位，测试只能是 mock-only，未来输出报告只能在明确授权执行后生成；同时禁止真实 Qdrant 连接、执行命令、RAG/LLM 调用、collection mutation 和 rebuild steps。

关键输出：
- 新增 `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json` 与 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md`。
- 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py`。
- design 状态为 `ready_for_minimal_implementation_scaffold_design_gate`，只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate`。

报告写法：
> v0.4.14.19 将 production rebuild live preflight runner 的最小 scaffold 固化为 design-only 契约。该版本只读取 v0.4.14.18 implementation design gate，定义未来 `tools/run_production_rebuild_live_preflight.py`、`tests/test_production_rebuild_live_preflight_runner.py` 和 `tests/production_rebuild_live_preflight_report.json` 的文件角色、不可执行占位策略、6 个 placeholder tests 和禁止内容。它不创建这些文件，不运行 live preflight，不访问或写入 Qdrant，不创建或接受正式授权，不执行 production rebuild。通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate`。

验证方式：
- py_compile 覆盖 v0.4.14.19 design 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 gate 输入通过、gate status/next-step drift、权限漂移、forbidden output key drift、CLI 输出一致性、runtime service import 禁止、未来文件不存在和 Markdown 边界。
- 默认生成 JSON/Markdown design 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.20：Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design Gate

阶段定位：这是 v0.4.14.19 scaffold design 的只读门禁版本。它只检查已保存的 scaffold design report，不创建未来 runner、不运行 live preflight、不访问或写入 Qdrant、不创建或接受正式授权记录、不执行 rebuild。

解决的问题：v0.4.14.19 已定义未来最小 scaffold 的文件结构和禁止内容，但仍需要 gate 防止 design 被误读成可创建可执行 runner、可连接 Qdrant 或可进入 production rebuild。v0.4.14.20 将 lineage、summary、guardrails、future files、scaffold contract、placeholder tests、forbidden scaffold content 和 forbidden output key 固化为 14 项可重复检查，并确认未来三件套仍不存在。

关键输出：
- 新增 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json` 与 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md`。
- 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py`。
- gate 记录 14 项检查、0 failure，并只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold`。

报告写法：
> v0.4.14.20 对 production rebuild live preflight runner minimal implementation scaffold design 执行只读 gate。该版本确认 v0.4.14.19 的唯一 lineage 为 v0.4.14.18 implementation design gate，summary 未授权 runner 文件创建、runner 执行、live preflight、Qdrant access/write、production rebuild 或 full eval；同时确认 3 个 future files 均未创建，entry function、probe injection、默认输出路径、no live probe、no Qdrant import、no write methods、fail-closed contract、6 个 placeholder tests 和 forbidden scaffold content 边界稳定。通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold`，仍不代表已经允许运行 live preflight、访问或写入 Qdrant、接受正式授权或执行 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.20 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 design 通过、status/lineage/blocker drift、scaffold contract drift、权限/guardrail drift、forbidden output key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 中文边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.21：Production Rebuild Live Preflight Runner Minimal Implementation Scaffold

阶段定位：这是 production rebuild live preflight runner 的最小 scaffold 落地版本。它创建 runner 文件和 mock-only 单测，但默认不连接真实服务、不运行 live preflight、不访问或写入 Qdrant、不创建正式 live preflight 输出、不执行 rebuild。

解决的问题：前序版本已经完成 runner design、implementation design、scaffold design 和 gate，但仍停留在报告层。v0.4.14.21 把最小 runner scaffold 落成可测试代码：核心函数只接受显式注入的 `qdrant_readonly_probe`，没有默认 live probe；所有缺失、未知、mismatch、probe error 和 write-like method exposure 都 fail closed；fake read-only probe 通过也不授予 Qdrant write、production rebuild 或 authorization。

关键输出：
- 新增 `tools/run_production_rebuild_live_preflight.py`。
- 新增 `tests/test_production_rebuild_live_preflight_runner.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json`。
- 新增 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_v0.4.14.21.md`。

报告写法：
> v0.4.14.21 将 production rebuild live preflight runner 从 scaffold design 推进到最小可测试 scaffold。该版本创建标准库-only runner 文件和 mock-only 单测，默认没有 live probe、没有真实 Qdrant endpoint、没有 Qdrant client import，也不生成正式 `tests/production_rebuild_live_preflight_report.json`。在 fake read-only probe 通过时，报告只表明预检结构可通过 mock 检查，仍保持 `qdrant_write_allowed=false`、`production_rebuild_allowed=false`、`authorization_granted=false`。因此本版本是 fail-closed scaffold 落地，不是生产 live preflight 或 rebuild 授权。

验证方式：
- py_compile 覆盖 runner scaffold、对应单测、health check 和 FastAPI 版本。
- 单测覆盖默认无 live probe fail-closed、fake read-only probe 成功但不授权 write/rebuild、缺少授权、target mismatch、backup/source lineage 缺失、probe error、write-like method exposure、CLI scaffold report 和 runtime service import 禁止。
- 默认生成 scaffold status report；未运行 full eval，未访问 Qdrant，未创建正式 live preflight report。

### v0.4.14.22：Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Gate

阶段定位：这是 v0.4.14.21 最小 runner scaffold 的只读门禁版本。它只检查 scaffold report、runner 源码和 mock-only 测试，不运行 live preflight、不访问 Qdrant、不写正式 preflight report、不执行 rebuild。

解决的问题：v0.4.14.21 已经创建 runner scaffold，需要立即确认它没有因为“runner 文件存在”而变成生产执行器。v0.4.14.22 将版本流转、文件边界、默认正式输出未创建、summary/guardrails 权限锁、runtime import 禁止、write/rebuild 参数禁止、核心 fail-closed contract 和 mock-only 测试覆盖固化为 13 项 gate 检查。

关键输出：
- 新增 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py`。
- 输出 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json` 与 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md`。
- 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py`。

报告写法：
> v0.4.14.22 对最小 live preflight runner scaffold 执行只读 gate。该版本确认 v0.4.14.21 scaffold report 状态为 `ready_for_minimal_scaffold_gate`，runner 文件和 mock-only 测试存在，正式 `tests/production_rebuild_live_preflight_report.json` 未创建；源码中没有 `qdrant_client`、OpenAI、RAG、risk 或 eval import，也没有 write/rebuild/switch 参数和 collection mutation 调用。通过后只开放 `production_rebuild_live_preflight_runner_mock_preflight_contract_gate`，仍不代表可以运行真实 live preflight 或 production rebuild。

验证方式：
- py_compile 覆盖 v0.4.14.22 gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖真实 scaffold 通过、scaffold report 权限漂移、runner 缺失、正式输出误创建、禁止 import/text、mock-only 测试漂移、CLI 输出一致性和 Markdown 中文边界。
- 默认生成 JSON/Markdown gate 报告；未运行 full eval，未访问 Qdrant。

### v0.4.14.23：Production Rebuild Live Preflight Real Read-Only Probe

阶段定位：这是 production rebuild preflight 链路从 mock scaffold 走向真实只读 Qdrant 接入的版本。它复用项目现有 `get_qdrant_client()`，只执行 collection 元信息、count 和 1 条 payload 抽样读取，不写 Qdrant、不运行 RAG、不执行 rebuild。

解决的问题：前序版本已经证明 runner scaffold 是 fail-closed，但仍未触达真实链路。v0.4.14.23 用显式 opt-in 工具跑真实只读 probe，确认 `legal_knowledge` collection 可达、points count 为 7177、抽样 payload metadata 含 `chunk_id` 与 `qdrant_point_id`；同时继续因正式授权未接受、backup/snapshot 缺失而 blocked。

关键输出：
- 新增 `tools/run_production_rebuild_live_preflight_real_readonly_probe.py`。
- 新增 `tests/test_production_rebuild_live_preflight_real_readonly_probe.py`。
- 输出 `tests/production_rebuild_live_preflight_real_readonly_probe_report.json`。
- 新增 `docs/production_rebuild_live_preflight_real_readonly_probe_v0.4.14.23.md`。

报告写法：
> v0.4.14.23 将 production rebuild live preflight 从 mock scaffold 推进到真实 Qdrant 只读 probe。该版本复用项目 Qdrant 配置和 client factory，只调用 `get_collection`、`count`、`scroll(with_vectors=False, limit=1)`，确认 `legal_knowledge` collection 可达且共有 7177 points，抽样 payload metadata 包含 `chunk_id` 与 `qdrant_point_id`。由于正式授权未接受且 backup/snapshot reference 缺失，preflight 仍 fail-closed；本版本不写 Qdrant、不切换 collection、不运行 RAG/embedding/LLM/full eval、不执行 production rebuild。

验证方式：
- py_compile 覆盖 real read-only probe 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖 fake client 只读调用、未授权/缺 backup blocked、accepted mock preflight 不授权 write/rebuild、CLI blocked output 和禁止写入/rebuild 调用。
- 实际运行一次真实 Qdrant 只读 probe；未创建 rebuild 输出，未写 Qdrant。

### v0.4.14.24：Production Rebuild Live Preflight Snapshot Reference Probe

阶段定位：这是 production rebuild 前置检查继续接入真实 Qdrant 状态的版本。它只读查询目标 collection 的现有 snapshots，判断是否已有可引用的 `backup_or_snapshot_reference`，不创建 snapshot，不写 Qdrant，不执行 rebuild。

解决的问题：v0.4.14.23 已确认 `legal_knowledge` collection 可达，但 `backup_or_snapshot_reference` 仍缺失。v0.4.14.24 直接检查真实 Qdrant snapshot 列表，确认当前 snapshot 数量为 `0`，因此阻断项不是抽象设计缺口，而是真实执行前置条件缺失。

关键输出：
- 新增 `tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py`。
- 新增 `tests/test_production_rebuild_live_preflight_snapshot_reference_probe.py`。
- 输出 `tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json`。
- 新增 `docs/production_rebuild_live_preflight_snapshot_reference_probe_v0.4.14.24.md`。

报告写法：
> v0.4.14.24 将 production rebuild preflight 从 collection 可达性检查推进到 snapshot reference 前置条件检查。该版本复用项目 Qdrant client factory，只调用 `list_snapshots(collection_name)` 查询 `legal_knowledge` 的现有 collection snapshots。真实运行结果显示 `snapshot_count=0`，没有可用 `backup_or_snapshot_reference`，因此 preflight 仍 fail-closed。该版本不创建、删除或恢复 snapshot，不写 Qdrant，不切换 collection，不运行 RAG/embedding/LLM/full eval，也不执行 production rebuild。下一步必须由人工明确授权创建 snapshot 或提供外部 backup/snapshot reference，并同时补齐正式授权记录。

验证方式：
- py_compile 覆盖 snapshot reference probe 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖 fake client 只读调用、snapshot reference 格式、最新 snapshot 选择、无 snapshot blocked、probe error fail-closed、CLI blocked output 和 source 中禁止 snapshot write/recover、Qdrant write、RAG、LLM、eval、rebuild 调用。
- 实际运行一次真实 Qdrant snapshot reference 只读 probe；未创建 snapshot，未写 Qdrant。

### v0.4.14.25：Production Rebuild Live Preflight Snapshot Create Reference Capture

阶段定位：这是 production rebuild 前置条件中 backup/snapshot reference 的真实补齐版本。它在用户明确授权后创建 `legal_knowledge` collection snapshot，并捕获后续 preflight 可引用的 snapshot reference。

解决的问题：v0.4.14.24 确认当前没有现成 snapshot reference，生产重建不能继续。v0.4.14.25 在用户明确授权后执行一次受限状态变更，只创建 collection snapshot，不写入 points，不切换 collection，不执行 rebuild。完成后重新运行只读 snapshot reference probe，确认 `snapshot_count=1` 且 reference 可用；重新运行真实只读 preflight 后，阻断项缩小为 `authorization_record_not_accepted`。

关键输出：
- 新增 `tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py`。
- 新增 `tests/test_production_rebuild_live_preflight_snapshot_create_reference_capture.py`。
- 输出 `tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json`。
- 新增 `docs/production_rebuild_live_preflight_snapshot_create_reference_capture_v0.4.14.25.md`。

报告写法：
> v0.4.14.25 在用户明确授权后，为 `legal_knowledge` collection 创建 Qdrant snapshot，并捕获 `qdrant-snapshot://collection/legal_knowledge/legal_knowledge-2019706566507018-2026-06-05-09-50-24.snapshot` 作为后续 preflight 的 backup/snapshot reference。该版本的允许方法序列限定为 `list_snapshots -> create_snapshot(wait=True) -> list_snapshots`，并通过 CLI 显式开关与 collection 锁避免误执行。该版本不删除或恢复 snapshot，不写入 collection points，不切换 collection，不运行 RAG/embedding/LLM/full eval，也不执行 production rebuild。snapshot reference 已补齐后，真实只读 preflight 的阻断项缩小为正式授权未接受。

验证方式：
- py_compile 覆盖 snapshot create reference capture 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖未授权不调用 client、错误 collection 调用前 blocked、授权创建与 reference 捕获、`None` 返回 fail-closed、创建异常 fail-closed、CLI 缺授权开关非零退出和 forbidden-call source scan。
- 实际创建一次 Qdrant collection snapshot，随后运行 snapshot reference probe 和真实只读 preflight probe；未执行 rebuild，未生成正式 live preflight pass report。

### v0.4.14.26：Production Rebuild Formal Authorization Gate

阶段定位：这是 production rebuild 前的正式授权门禁版本。它只读取已保存的 snapshot capture 报告和真实 Qdrant 只读 preflight 报告，不访问 Qdrant、不运行 live preflight、不执行 rebuild。

解决的问题：v0.4.14.25 已补齐 backup/snapshot reference，但这不能自动视为 production rebuild 授权。v0.4.14.26 将当前状态固化为机器可检查 gate：snapshot reference 已满足，真实只读 preflight 仅剩 `authorization_record_not_accepted`，因此必须等待正式授权记录。

关键输出：
- 新增 `tools/check_production_rebuild_formal_authorization_gate.py`。
- 新增 `tests/test_production_rebuild_formal_authorization_gate.py`。
- 输出 `tests/production_rebuild_formal_authorization_gate_report.json`。
- 新增 `docs/production_rebuild_formal_authorization_gate_v0.4.14.26.md`。

报告写法：
> v0.4.14.26 将 production rebuild 前的剩余条件固化为正式授权门禁。该版本只读取 saved reports，确认 `backup_or_snapshot_reference` 已存在，且真实只读 preflight 的阻断项已经缩小为 `authorization_record_not_accepted`。由于当前没有 `authorization_status=accepted` 和非空 `authorization_reference`，gate 仍 fail-closed，`production_rebuild_allowed=false`。该版本不访问 Qdrant，不创建或恢复 snapshot，不写入 collection points，不切换 collection/alias，不运行 RAG/embedding/LLM/full eval，也不执行 production rebuild。下一步只能是收集正式 production rebuild 授权并重新运行带授权的 fail-closed live preflight。

验证方式：
- py_compile 覆盖 formal authorization gate 工具、对应单测、health check 和 FastAPI 版本。
- 单测覆盖当前 saved reports 默认 blocked、accepted status/reference 条件、snapshot/preflight drift fail-closed、CLI blocked output 和 forbidden-call source scan。
- 默认生成 gate 报告；未运行 full eval，未访问 Qdrant，未生成正式 live preflight pass report。

### v0.4.14.27：Production Rebuild Read-Only Live Preflight Runner

阶段定位：这是 production rebuild 前置检查从“只读 probe / saved gate”推进到正式只读 live preflight runner 的版本。它真实访问 Qdrant 读取目标 collection 状态，并生成正式 preflight 报告，但仍不写入、不切换、不 rebuild。

解决的问题：前序版本已经补齐 snapshot reference，并确认剩余阻断是正式授权。v0.4.14.27 不再继续扩设计或 gate 链条，而是让 `tools/run_production_rebuild_live_preflight.py` 具备显式只读执行模式，直接输出 `tests/production_rebuild_live_preflight_report.json`，把执行前状态固定为可复跑、可审阅的报告。

关键输出：
- 扩展 `tools/run_production_rebuild_live_preflight.py`，新增 `--run-readonly-live-preflight`。
- 更新 `tools/run_production_rebuild_live_preflight_real_readonly_probe.py` 的授权引用透传。
- 输出 `tests/production_rebuild_live_preflight_report.json`。
- 新增 `docs/production_rebuild_live_preflight_runner_v0.4.14.27.md`。

报告写法：
> v0.4.14.27 将 production rebuild preflight 推进到正式只读 live runner。该版本通过显式 `--run-readonly-live-preflight` 参数访问 `legal_knowledge` collection，只调用 `get_collection`、`count` 和 `scroll(with_vectors=False, limit=1)`，确认 collection 可达、`points_count=7177`、snapshot reference 与 source lineage 已满足。当前正式 preflight 报告仍因缺少已接受的授权记录和非空授权引用而 blocked，`qdrant_write_allowed=false`、`production_rebuild_allowed=false`。该版本不写 Qdrant、不创建/删除/恢复 snapshot、不切换 collection/alias、不运行 RAG/embedding/LLM/full eval，也不执行 production rebuild。下一步应补齐正式授权引用并重跑同一个只读 runner，而不是继续新增 gate。

验证方式：
- py_compile 覆盖正式 runner、real readonly probe、历史 scaffold gate、对应单测、health check 和 FastAPI 版本。
- 单测覆盖 fake/真实只读 probe 注入、accepted status 必须带 authorization reference、历史 scaffold gate traceability 和 health check 版本锚点。
- 实际运行一次正式只读 live preflight runner，生成 `tests/production_rebuild_live_preflight_report.json`；未执行 full eval，未写 Qdrant。

### v0.4.14.28：Production Rebuild Authorization Record Intake

阶段定位：这是只读 live preflight runner 的正式授权记录接入版本。它让 runner 能读取授权记录 JSON 并参与 fail-closed 判断，但不创建 gate，不执行 rebuild。

解决的问题：v0.4.14.27 已经证明只读 live preflight 可运行，剩余阻断是正式授权。v0.4.14.28 增加 `--authorization-record <json>`，让真实授权记录可作为输入进入同一个 runner，同时防止授权记录携带执行命令或写入许可。

关键输出：
- 扩展 `tools/run_production_rebuild_live_preflight.py`。
- 新增 `tests/production_rebuild_authorization_record.json`。
- 输出 `tests/production_rebuild_live_preflight_report.json`。
- 新增 `docs/production_rebuild_authorization_record_intake_v0.4.14.28.md`。

报告写法：
> v0.4.14.28 将正式授权记录接入只读 live preflight runner。该版本支持从 JSON 授权记录读取 `authorization_status`、`authorization_reference`、`target_collection`、`backup_or_snapshot_reference` 和 `source_lineage_reference`，并检查 CLI 参数与授权记录是否冲突。若授权记录携带 `commands`、`authorized_actions`、`rebuild_steps`、`ready_to_apply`、`qdrant_write_allowed` 或 `production_rebuild_allowed` 等执行型字段，runner 会 fail-closed。本版本用 `tests/production_rebuild_authorization_record.json` 重跑真实只读 preflight，结果为 `passed` 且 `blockers=[]`；但 `qdrant_write_allowed=false`、`production_rebuild_allowed=false` 和 `authorization_granted=false` 仍保持不变。实际 production rebuild 必须进入下一独立版本执行并记录执行结果。

验证方式：
- py_compile 覆盖 runner、runner 单测、health check 和 FastAPI 版本。
- 单测覆盖授权记录读取、非对象 JSON 拒绝、授权记录/CLI 冲突、执行型字段 fail-closed、授权记录通过后仍不授权 Qdrant write 或 production rebuild。
- 实际运行正式只读 live preflight runner；未运行 full eval，未写 Qdrant，未执行 rebuild。

### v0.4.14.29：Production Rebuild Execution

阶段定位：这是正式生产 collection rebuild 执行版本。它基于 v0.4.14.28 的授权记录和已通过只读 preflight，实际重建 `legal_knowledge`，并保留执行记录与重建后只读验证。

解决的问题：v0.4.13.8 已修复普通法律条文路径缺少 `chunk_index/chunk_count` 的 ingestion metadata 问题，但真实 Qdrant collection 仍是旧索引。v0.4.14.29 将该源码补丁通过生产 rebuild 落到 `legal_knowledge`。

关键输出：
- 新增 `tools/run_production_rebuild_execution.py`。
- 输出 `tests/production_rebuild_execution_report.json`。
- 新增 `tools/check_production_rebuild_post_validation.py`。
- 输出 `tests/production_rebuild_post_validation_report.json`。
- 新增 `docs/production_rebuild_execution_v0.4.14.29.md`。

报告写法：
> v0.4.14.29 执行正式 `legal_knowledge` production rebuild。该版本读取 `tests/production_rebuild_authorization_record.json` 与已通过的 `tests/production_rebuild_live_preflight_report.json`，调用既有 `rag_admin.py --rebuild` 重建 collection。执行记录显示 rebuild 前后均为 `7177` points，manifest 15 个文档均存在，执行状态为 `succeeded`。重建后 post-validation 只读扫描 1000 个 points，观测到 `paragraph/article/item/standard_section` 的 `chunk_index/chunk_count`，缺失数为 0。本版本真实写入 Qdrant，但不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases，也不运行 full eval。下一步应做重建后 targeted smoke / RAG eval 质量复测。

验证方式：
- py_compile 覆盖 execution runner、post-validation、live preflight、health check、对应单测和 FastAPI 版本。
- 单测覆盖执行器 dry-run/execute wrapper、UTF-8 子进程输出、post-validation passed/failed 情形、live preflight 授权记录逻辑和 health check。
- 实际执行 production rebuild，随后运行 post-validation 与只读 live preflight；未运行 full eval。

### v0.4.14.30：Post-Rebuild Quality Summary

阶段定位：这是生产重建后的第一轮质量复测版本。它运行 smoke RAG eval，并汇总 baseline smoke、post-rebuild smoke 与 post-validation，判断核心法规链路是否在重建后保持稳定。

解决的问题：v0.4.14.29 已完成真实生产 rebuild，但还需要确认重建后核心 smoke case 没有回归。v0.4.14.30 先跑轻量 smoke 复测，再生成可读摘要，避免直接把大 JSON 交给 reviewer。

关键输出：
- 输出 `tests/post_rebuild_smoke_eval_report.json`。
- 新增 `tools/build_post_rebuild_quality_summary.py`。
- 输出 `tests/post_rebuild_quality_summary_report.json` 与 `docs/post_rebuild_quality_summary_v0.4.14.30.md`。
- 新增 `tests/test_post_rebuild_quality_summary.py`。

报告写法：
> v0.4.14.30 对 production rebuild 后的 `legal_knowledge` 执行 smoke 质量复测。该版本运行 25 个 smoke cases，结果 25/25 passed；与 baseline `tests/smoke_eval_report.json` 对比没有回归 case、没有缺失 case。post-validation 继续 passed，Qdrant points 为 7177，扫描 1000 个 points 中 structured block 的 `chunk_index/chunk_count` 缺失为 0。本版本会调用 RAG/Qdrant/LLM 运行 smoke eval，但不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases，也不运行 full eval。下一步应进入 targeted 或 full RAG eval。

验证方式：
- py_compile 覆盖 summary builder、对应单测、health check 和 FastAPI 版本。
- 单测覆盖 smoke 无回归通过、baseline 已通过 case 回归时 fail-closed。
- 实际运行 post-rebuild smoke eval 与 quality summary；未运行 full eval。

### v0.4.14.31：Post-Rebuild Full RAG Eval Summary

阶段定位：这是生产重建后的 full RAG eval 复测收口版本。它保留真实 full eval 输出，并用只读 summary builder 把回归类型、失败检查和下一步排查方向压缩成可执行输入。

解决的问题：v0.4.14.30 只证明 smoke 25/25 仍稳定，但不能代表全部 60 个 RAG eval case 都稳定。v0.4.14.31 运行 full RAG eval 后发现 post-rebuild 为 58/60 passed，相比 baseline 60/60 出现 2 个回归；因此项目下一步应进入主链路排查，而不是继续堆授权、设计或 gate 报告。

关键输出：
- 输出 `tests/post_rebuild_rag_eval_report.json`。
- 新增 `tools/build_post_rebuild_rag_eval_summary.py`。
- 输出 `tests/post_rebuild_rag_eval_summary_report.json` 与 `docs/post_rebuild_rag_eval_summary_v0.4.14.31.md`。
- 新增 `tests/test_post_rebuild_rag_eval_summary.py`。

报告写法：
> v0.4.14.31 对 production rebuild 后的 `legal_knowledge` 执行 full RAG eval 复测，并生成只读摘要。baseline `tests/rag_eval_report.json` 为 60/60 passed；post-rebuild `tests/post_rebuild_rag_eval_report.json` 为 58/60 passed。两个回归分别为：`risk_trademark_non_use_001` 的 expected evidence 缺失，商标法第 49 条已在 sparse/union/anchor/rerank_input 命中但从 final evidence 掉出，分类为 `final_evidence_selection_drop`；`risk_tort_product_liability_001` 的 final evidence 已满足，但答案缺少关键词“赔偿”，分类为 `answer_keyword_coverage_gap`。summary builder 本身只读取 saved reports，不调用 RAG/Qdrant/LLM，也不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。下一步应做最小主链路排查与 targeted 修复验证。

### v0.4.14.32：Post-Rebuild Evidence Alignment Retention

阶段定位：生产重建后的 RAG 主链路质量修复。

解决的问题：v0.4.14.31 full RAG eval 显示，商标连续三年不使用场景中，商标法第 49 条已经进入 sparse/union/anchor/rerank_input，却在 final evidence top-3 阶段掉出，导致 post-rebuild full eval 从 baseline 60/60 下降到 58/60。

关键实现：
- 在 `src/rag/retriever.py::_select_diverse_rerank_top` 后增加 selector-only 的 evidence alignment retention。
- 保持 Cross-Encoder 排序、top-3 证据数量和原有 dedupe，不新增 anchor、不改 prompt、不改 rerank、不改 eval case。
- 只有当未入选候选同时覆盖用户问题核心片段和法律后果/责任词，且 final evidence 尚未覆盖该后果时，才最多替换一个较弱 final evidence。
- 在 `tests/test_candidate_budget.py` 中增加保留、拒绝误保留和不重复替换的通用测试。

报告写法：
> v0.4.14.32 将重建后暴露的 final evidence selection drop 转化为主链路 selector 质量修复。系统不通过新增锚点或修改评测样本补结果，而是在 Cross-Encoder 已经看过的候选内部，保守保留能够补足主争点法律后果的证据。修复后 post-rebuild full RAG eval 恢复到 60/60 passed。

验证方式：
- targeted `risk_trademark_non_use_001` 通过，商标法第 49 条进入 final evidence。
- targeted `risk_tort_product_liability_001` 通过，且未修改 prompt 或 risk supplement。
- full RAG eval 输出 `tests/post_rebuild_rag_eval_after_alignment_retention_report.json`，结果为 60/60 passed。
- 项目健康检查、编码卫生、索引一致性、全量单测和 restricted diff 通过。

### v0.4.14.33：Post-Rebuild Alignment Retention Delta

阶段定位：主链路修复后的证据变化稳定化。

解决的问题：v0.4.14.32 已把 post-rebuild full RAG eval 从 58/60 恢复到 60/60，但仍需要确认 selector retention 没有在其他已通过 case 中造成不可解释的 final evidence 替换。

关键实现：
- 新增 `tools/build_post_rebuild_alignment_retention_delta.py`，只读比较修复前后 full RAG eval saved reports。
- 引入 canonical evidence key `(source, article_no, section_no)`，区分 citation-only delta、score-only delta 和真实 replacement delta。
- 读取 `tests/rag_eval_cases.json` 中的 expected evidence metadata，用于识别 added/removed expected evidence。
- 对“原本通过但 evidence 法条替换”的 case 标记 warn，对 removed expected evidence 或 pass-to-fail 标记 blocker。

报告写法：
> v0.4.14.33 对 v0.4.14.32 的主链路修复做了 saved-report delta 稳定化。结果显示修复后 full RAG eval 为 60/60，且没有 pass-to-fail 或 expected evidence 被移除；同时识别出 5 个原本通过但 evidence 法条替换的 warn 项，要求在系列收口前进行抽样复核。

验证方式：
- 生成 `tests/post_rebuild_alignment_retention_delta_report.json` 与 `docs/post_rebuild_alignment_retention_delta_v0.4.14.33.md`。
- delta summary：9 个 evidence changed cases、7 个 replacement delta、2 个 citation-only delta、1 个 added expected evidence、0 个 removed expected evidence、0 个 regression。
- `tests/test_post_rebuild_alignment_retention_delta.py` 覆盖通用 delta 逻辑和 saved-report-only 边界。

验证方式：
- py_compile 覆盖 summary builder、对应单测、health check 和 FastAPI 版本。
- 单测覆盖无回归通过、final evidence selection drop 分类、answer keyword coverage gap 分类。
- 实际运行 full RAG eval、summary builder、索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.14.34：Post-Rebuild Alignment Retention Tightening

阶段定位：生产重建后 RAG 主链路 selector 质量收紧。

解决的问题：v0.4.14.33 的 delta 复核显示，v0.4.14.32 的 selector retention 虽然能恢复 60/60，但仍存在远距离泛化条文、弱片段误判、同源近邻核心争点条文掉出 final evidence 等风险。v0.4.14.34 将这些风险收敛为通用 selector 规则，而不是新增 anchor 或修改样本。

关键实现：
- 在 `src/rag/retriever.py` 中收紧 consequence 识别，避免把“有限责任公司”中的“责任”误判为法律后果。
- 增加同源远距离条文 outlier 防护，防止产品责任核心条文组被远距离泛化条文替换。
- 明确 selector 不解析或消费 rerank query 中的“场景锚点法条”行，避免把 anchor hint 变成新的隐性规则来源。
- 增加同源近邻争点覆盖补齐，使公司法第 84/86 条、个人信息保护法第 39 条、增值税法第 13 条等已进入 rerank input 的核心证据能稳定进入 final evidence。
- 增加 protected evidence 最终硬过滤，避免 `issue_candidate` 分支替换已保护的核心争点证据。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、eval case、fixture 或 scenario registry。

报告写法：
> v0.4.14.34 将 post-rebuild selector 修复从单点 evidence retention 推进为更稳的 evidence group retention。系统仍只在 Cross-Encoder 已看过的候选内调整 final evidence，并保持 top-3 证据数量不变；修复重点是避免核心条文被弱片段、远距离泛化条文或同组后序条文挤出，并补上 protected evidence 不可被后续 replacement 绕过的硬保护。覆盖复跑后的 full RAG eval 输出 `tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`，结果为 60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。中途曾出现一次产品责任场景答案关键词生成波动，targeted 复核通过后已用正式 full eval 覆盖。

验证方式：
- `tests.test_candidate_budget` 30 项通过。
- targeted `risk_data_export_overseas_001` 与 `risk_tort_product_liability_001` 通过。
- full RAG eval：`tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`，60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- 项目健康检查、编码卫生、索引一致性、全量 unittest 和 restricted diff 通过。

### v0.4.14.35：Production Rebuild / Post-Rebuild Series Closeout

阶段定位：v0.4.14 生产重建与 post-rebuild RAG 质量链条的收口归档版本。它只读取已有报告，不新增 gate，不运行 full eval，不连接 Qdrant，不调用 `rag_query` 或 LLM，也不修改运行时代码。

解决的问题：v0.4.14.29 已完成生产重建，v0.4.14.30-v0.4.14.34 已完成 post-validation、smoke、full eval 回归暴露、selector retention 修复、delta 复核和 tightening 后 60/60 覆盖。v0.4.14.35 将这条证据链压缩成一份可引用的 closeout ledger，明确下一步应进入真实 RAG 质量任务，而不是继续堆设计或 gate。

关键输出：
- 新增 `tools/build_production_rebuild_post_rebuild_series_closeout.py`。
- 输出 `tests/production_rebuild_post_rebuild_series_closeout_report.json` 与 `docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md`。
- 新增 `tests/test_production_rebuild_post_rebuild_series_closeout.py`。

报告写法：
> v0.4.14.35 关闭 v0.4.14 production rebuild and post-rebuild RAG quality chain。closeout 显示生产重建已成功执行，post-validation passed，post-rebuild smoke 为 25/25，初次 full RAG eval 暴露 58/60 的真实回归，后续 selector retention 与 tightening 将 full RAG eval 恢复并稳定到 60/60，最终 `retrieval_failure_stage_summary={"PASS": 60}`。本版本是 saved-report closeout，不是新增 gate，不授权下一次 rebuild，不新增 anchor，不修改 prompt、rerank、eval cases、risk supplement、term preservation、scenario registry 或 fixtures。

验证方式：
- py_compile 覆盖 closeout builder、单测、health check 与 FastAPI 版本。
- 单测覆盖真实输入收口、缺失输入阻断、最终 full eval drift、初次回归 lineage、delta removed expected evidence 和 Markdown 边界。
- 实际生成 closeout JSON/Markdown；运行索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.15.0：Post-Rebuild Repeat Stability Summary

阶段定位：这是 v0.4.14 生产重建与 selector 收口后的真实 RAG 质量稳定性基线版本。它先运行授权的 3 轮 full RAG eval repeat，再用 saved-report-only summary 将波动压缩成可审阅信号；summary builder 本身不运行 eval、不调用 `rag_query`、不连接 Qdrant、不调用 LLM。

解决的问题：单次 full RAG eval 60/60 不能证明生产重建后的链路足够稳定。v0.4.15.0 通过 repeat eval 暴露真实波动：第 3 轮从 60/60 降为 59/60，同时出现一个 final evidence identity drift case。这些信号应进入 triage，而不是通过改 eval case、新增 anchor、改 prompt 或改 rerank 直接掩盖。

关键输出：
- 新增 `tools/build_post_rebuild_repeat_stability_summary.py`。
- 输出 `tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json`。
- 输出 `tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json` 与 `docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md`。
- 新增 `tests/test_post_rebuild_repeat_stability_summary.py`。

报告写法：
> v0.4.15.0 将 post-rebuild RAG 质量从“单次 60/60”推进到 repeat 稳定性观察。3 轮 full RAG eval repeat 的 pass counts 为 `[60, 60, 59]`，summary 状态为 `needs_triage`。主要信号包括：`risk_tort_product_liability_001` 在第 3 轮 retrieval stage 仍为 `PASS`、final evidence 仍覆盖《民法典》第 1203/1204/1207 条，但答案缺少关键词“赔偿”；`risk_algorithm_bias_001` 第 3 轮 final evidence 从《网络安全法》第 20 条漂移到《个人信息保护法》第 56 条。该版本不授权 runtime fix，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures 或 eval cases；下一步应先做 targeted triage。

验证方式：
- 授权运行 `tools/run_rag_eval.py --repeat 3` 生成 repeat 原始报告；退出码为 1 是因为第 3 轮 59/60，属于本版本记录的真实质量信号。
- py_compile 覆盖 summary builder、单测、health check 与 FastAPI 版本。
- 单测覆盖 clean repeat、59/60 输出波动、证据身份漂移、citation 展示差异不误报、case set drift、dense fallback drift、真实报告解析和 Markdown 边界。
- 实际生成 summary JSON/Markdown；运行索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.15.1：Post-Rebuild Repeat Instability Triage

阶段定位：这是 v0.4.15.0 repeat 稳定性基线之后的 targeted triage 版本。它对两个真实不稳定信号分别运行小范围 repeat，再用 saved-report-only builder 归档结论；builder 不运行 eval、不调用 `rag_query`、不连接 Qdrant、不调用 LLM。

解决的问题：v0.4.15.0 同时暴露了产品责任场景的答案关键词波动和算法偏见场景的 final evidence identity drift。v0.4.15.1 将二者拆开复核，避免把输出措辞波动误当成检索修复任务，也避免把证据身份漂移隐藏在全量 59/60 的大报告里。

关键输出：
- 新增 `tools/build_post_rebuild_repeat_instability_triage.py`。
- 输出 `tests/targeted_repeat_product_liability_v0.4.15.1_report.json`。
- 输出 `tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json`。
- 输出 `tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json` 与 `docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md`。
- 新增 `tests/test_post_rebuild_repeat_instability_triage.py`。

报告写法：
> v0.4.15.1 对 v0.4.15.0 的两个 repeat instability 信号进行 targeted triage。`risk_tort_product_liability_001` 在 5 轮 targeted repeat 中全部通过，检索阶段、失败检查、贡献标签和 final evidence identity 均稳定，仅答案文本存在措辞变化，因此降级为非阻断观察项。`risk_algorithm_bias_001` 同样 5/5 通过，但 final evidence 第三条在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移，说明 evidence identity drift 已复现，下一步应先定位 final evidence 选择稳定性原因。该版本不授权 runtime fix，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

验证方式：
- 对两个目标 case 分别运行 `tools/run_rag_eval.py --repeat 5 --check-risk`。
- py_compile 覆盖 targeted triage builder、单测、health check 与 FastAPI 版本。
- 单测覆盖输出措辞波动非阻断、final evidence identity drift 阻断、真实 targeted repeat 报告解析和 Markdown 边界。
- 实际生成 triage JSON/Markdown；运行索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.15.2：Post-Rebuild Final Evidence Drift Attribution

阶段定位：这是 v0.4.15.1 targeted triage 之后的 saved-report attribution 版本。它不运行新的 RAG eval，而是读取既有 targeted repeat debug_info，把 `risk_algorithm_bias_001` 的 final evidence identity drift 定位到可观察阶段。

解决的问题：v0.4.15.1 已确认算法偏见 case 的第三条 final evidence 在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移，但还不能判断是 rerank 分数波动、selector replacement 还是候选预算问题。v0.4.15.2 将已保存的 dense/sparse/union/anchor/rerank_input/reranked/final candidates 串起来，明确当前证据能证明什么、不能证明什么。

关键输出：
- 新增 `tools/build_post_rebuild_final_evidence_drift_attribution.py`。
- 输出 `tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json` 与 `docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md`。
- 新增 `tests/test_post_rebuild_final_evidence_drift_attribution.py`。

报告写法：
> v0.4.15.2 对 `risk_algorithm_bias_001` 的 final evidence identity drift 做 saved-report attribution。报告确认核心 expected evidence《个人信息保护法》第 24 条与第 48 条在 5 轮 targeted repeat 中稳定进入 final evidence；漂移只发生在第三席 alternate evidence，《个人信息保护法》第 56 条出现 3 次、《网络安全法》第 20 条出现 2 次。两者均已进入 rerank input，因此漂移首次可观察于 saved `reranked_candidates/final_candidates` top-3 边界。由于现有 debug_info 未保存完整 raw Cross-Encoder score order 和 selector decision trace，本版本不能直接定责为 rerank score jitter 或 selector replacement，也不授权 runtime fix。下一步应先设计 selection trace / full rerank score capture。

验证方式：
- py_compile 覆盖 attribution builder、单测、health check 与 FastAPI 版本。
- 单测覆盖双候选进入 rerank input 后第三席漂移、无漂移通过、真实报告解析和 Markdown 边界。
- 实际生成 attribution JSON/Markdown；运行索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.15.3：Post-Rebuild Selection Trace Readiness

阶段定位：这是 RAG 主链路可观测性补丁版本。它不修改 rerank 分数、排序函数或 selector 选择语义，而是在 `debug=True` 时把 full rerank score order 和 final evidence selection trace 写入 `debug_info`，为下一轮 targeted repeat 定位漂移根因提供证据。

解决的问题：v0.4.15.2 已确认 `risk_algorithm_bias_001` 的第三席证据漂移首次可观察于 saved reranked/final top-3 边界，但旧 debug_info 没有完整 raw score order 和 selector trace。v0.4.15.3 解决的是“看不见选择过程”的问题，让后续能区分 raw rerank score/order 波动与 selector replacement 边界波动。

关键输出：
- `rag_query(debug=True)` 新增 `debug_info.rerank_full_score_order`。
- `rag_query(debug=True)` 新增 `debug_info.final_evidence_selection_trace`。
- 新增 `tools/build_post_rebuild_selection_trace_readiness.py`。
- 输出 `tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json` 与 `docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md`。
- 新增 `tests/test_post_rebuild_selection_trace_readiness.py`，并扩展 `tests/test_candidate_budget.py`。

报告写法：
> v0.4.15.3 在不改变 RAG 检索、Cross-Encoder rerank、anchor、prompt 或 selector 选择语义的前提下，增强了主链路 debug 可观测性。系统现在能够在 `debug=True` 时输出完整 rerank score order、输入位次、rerank 位次、最终证据位次，以及 selected/not_selected 候选列表。该版本不是行为修复，而是为下一轮 `risk_algorithm_bias_001` targeted repeat capture 提供证据，使后续可以判断漂移来自 raw score/order 波动还是 selector replacement 边界波动。

验证方式：
- py_compile 覆盖 `src/rag/retriever.py`、selection trace readiness builder 和相关测试。
- 单测覆盖 full rerank order trace、final selection trace、synthetic selector 行为不变和报告边界。
- 实际生成 readiness JSON/Markdown；运行索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.15.4：Post-Rebuild Selection Trace Attribution

阶段定位：这是基于 v0.4.15.3 trace 的 targeted attribution 版本。它只运行 `risk_algorithm_bias_001` 单 case targeted repeat，不运行 full eval，并用保存下来的 full rerank order 和 selection trace 解释第三席 final evidence 漂移。

解决的问题：v0.4.15.2 能看到漂移发生在 reranked/final top-3 边界，但不能判断是 selector replacement 额外替换，还是 rerank order 本身在近分边界上波动。v0.4.15.4 用 trace 证明每轮最终第三席都来自 `final_evidence_selection_trace.selected`，并且总是两个漂移候选中 full rerank order 更靠前者。

关键输出：
- 输出 `tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json`，5 轮 targeted repeat 均通过。
- 新增 `tools/build_post_rebuild_selection_trace_attribution.py`。
- 输出 `tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json` 与 `docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md`。
- 新增 `tests/test_post_rebuild_selection_trace_attribution.py`。

报告写法：
> v0.4.15.4 对算法偏见 case 进行带 trace 的 targeted repeat。结果显示 case 5/5 通过，核心证据《个人信息保护法》第 24 条和第 48 条稳定保留；第三席证据仍在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移。通过 `rerank_full_score_order` 和 `final_evidence_selection_trace` 可确认，最终第三席始终跟随两个漂移候选中 full rerank order 更靠前的一项，因此漂移的直接原因更接近 raw rerank stable order / near-tie boundary，而不是 selector replacement 额外替换。该版本不授权 runtime fix，下一步应设计 near-tie stability policy。

验证方式：
- 运行单 case targeted repeat：`tools/run_rag_eval.py --case-id risk_algorithm_bias_001 --repeat 5 --check-risk`。
- py_compile 覆盖 trace attribution builder 和单测。
- 单测覆盖 synthetic drift attribution、真实 trace report 解析、Markdown 边界和 CLI 写出。
- 实际生成 attribution JSON/Markdown；运行索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.15.5：Post-Rebuild Near-Tie Stability Policy Design

阶段定位：这是 near-tie stability 的设计收口版本。它不实现 runtime patch，而是把 v0.4.15.4 的 trace attribution 转化为可审阅、可验证、边界明确的最小修复设计。

解决的问题：v0.4.15.4 已证明第三席漂移不是 selector replacement 额外替换，而是 full rerank order 在近分边界上不稳定。v0.4.15.5 进一步限定后续修复只能围绕既有 Cross-Encoder stable-score bucket 内的 deterministic ordering 展开，避免走回新增 anchor、改 prompt、改 eval case 或调 rerank score 的旧路。

关键输出：
- 新增 `tools/build_post_rebuild_near_tie_stability_policy_design.py`。
- 输出 `tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json` 与 `docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md`。
- 新增 `tests/test_post_rebuild_near_tie_stability_policy_design.py`。

报告写法：
> v0.4.15.5 将 trace attribution 结果转化为 near-tie stability policy 设计。该设计建议未来只在既有 Cross-Encoder stable-score bucket 内做 deterministic ordering，不改变 Cross-Encoder 分数、模型、query、`score_epsilon`、top_k、anchor、prompt 或 eval case；同时明确禁止 case id 分支和硬编码某部法律或某个条文为赢家。该版本仍不是 runtime patch，后续实现必须另行授权并以 targeted repeat trace、候选选择单测、project health 和 restricted diff 验证。

验证方式：
- py_compile 覆盖 near-tie policy design builder 与单测。
- 单测覆盖错误分类阻断、真实 v0.4.15.4 attribution 解析、Markdown 边界和 CLI 写出。
- 实际生成 design JSON/Markdown；运行索引一致性、编码卫生、project health、全量 unittest 和 restricted diff。

### v0.4.15.6: Near-Tie Runtime Patch Validation

Stage: this is the minimal runtime patch version authorized after v0.4.15.5. It connects the near-tie policy to the main RAG path without adding another design gate.

Problem solved: v0.4.15.4 showed that `risk_algorithm_bias_001` final evidence drift came from raw rerank order at the near-tie boundary, not from selector replacement. v0.4.15.6 adds `_stabilize_same_bucket_rerank_order()` after `_sort_rerank_scores_stable()` and before `_select_diverse_rerank_top()`.

Key outputs:
- Modified `src/rag/retriever.py`.
- Added `tools/build_post_rebuild_near_tie_patch_validation.py`.
- Added `tests/test_post_rebuild_near_tie_patch_validation.py`.
- Generated `tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json`.
- Generated `tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json` and `docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md`.

Report wording:
> v0.4.15.6 implements the minimum near-tie runtime patch. The patch stabilizes candidate order only inside existing Cross-Encoder stable-score buckets. It does not change Cross-Encoder scores, model, query, `score_epsilon`, top_k, anchor, prompt, risk supplement, term preservation, scenario registry, fixtures, eval cases, or hidden seed. The authorized targeted repeat for `risk_algorithm_bias_001` passed 5/5, and the final evidence identity chain was stable across all five runs.

Verification:
- py_compile covered the retriever patch, validation builder, and tests.
- Unit tests covered same-bucket input-order independence, cross-bucket priority preservation, and validator passed/blocked/fail-closed paths.
- The authorized targeted repeat passed 5/5.
- The validation report status is `passed` with `unique_selected_evidence_chains=1`.

## 最终报告建议结构

最终报告可按以下章节组织：

1. 项目背景与问题定义：企业合规、数据合规、供应链与法律风控需求。
2. 系统总体架构：知识库层、RAG 检索层、风险引擎层、报告输出层、未来 Agent 编排层。
3. 法律知识库建设：文本清洗、法律条文结构化、标准类文件入库、元数据体系。
4. RAG 检索与证据链：分层召回、稳定去重、Anchor 注入、Cross-Encoder 精排、置信度、人工复核。
5. 风险识别引擎：风险分类体系、风险等级、整改动作、依据绑定。
6. 报告生成与导出：执行摘要、风险发现、行动计划、Markdown/JSON 导出。
7. 评测体系：RAG Eval、Risk Eval、Report Eval 三层回归。
8. 质量治理与人工复核闭环：scenario registry、hidden/evidence diagnostics、manual review decision schema、visual workbench、AI suggestion isolation、export pipeline dry run。
9. 当前不足与未来工作：法规覆盖、增量测试、法律效力冲突、跨领域 Agent，以及人工复核完成后才允许进入的 retrieval input quality / final evidence selection policy 治理。

### v0.4.15.7: Near-Tie Patch Closeout

Stage: saved-report closeout for the v0.4.15.6 same-bucket near-tie runtime patch. This version does not add another runtime patch or design gate.

Problem solved: v0.4.15.6 had already stabilized `risk_algorithm_bias_001` final evidence identity in a 5/5 targeted repeat. v0.4.15.7 records the post-patch closeout by reading the targeted repeat report, the v0.4.15.6 validation report, and project health.

Key outputs:
- Added `tools/build_post_rebuild_near_tie_patch_closeout.py`.
- Added `tests/test_post_rebuild_near_tie_patch_closeout.py`.
- Generated `tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json` and `docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md`.
- Cleaned the v0.4.15.6 validation Markdown output for readability.

Report wording:
> v0.4.15.7 closes the near-tie patch validation loop. It only reads saved reports and confirms the targeted repeat is 5/5 passed, patch validation is `passed`, final evidence identity has one stable chain, and project health is passed. It does not run eval, call `rag_query`, access Qdrant, call an LLM, or modify runtime behavior. No hidden seed, anchor, prompt, rerank score, `score_epsilon`, top_k, risk supplement, term preservation, scenario registry, fixture, or eval case change is authorized.

Verification:
- py_compile covered the closeout builder, validation builder, health runner, health test, and versioned app entry.
- Unit tests covered closeout pass/block paths and existing v0.4.15.6 validation behavior.
- The closeout report status is `closed_for_next_real_rag_quality_task`.

### v0.4.15.8: Post Near-Tie Patch Main-Chain Repair

Stage: main RAG path regression repair after the near-tie patch closeout.

Problem solved: a full RAG eval after v0.4.15.7 exposed that the same-bucket stabilization added in v0.4.15.6 was too broad. It reordered large stable-score buckets and caused 28 `RERANK_MISS` failures, reducing the full eval result to 31/60. v0.4.15.8 limits stabilization to small true near-tie groups and preserves Cross-Encoder order for broad buckets.

Key outputs:
- Modified `src/rag/retriever.py`.
- Modified `src/risk/taxonomy.py`.
- Added `tests/test_risk_analyzer.py`.
- Extended `tests/test_candidate_budget.py` and `tests/test_taxonomy.py`.
- Generated `tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json`, `tests/targeted_post_near_tie_regression_v0.4.15.8_report.json`, `tests/targeted_antitrust_risk_level_v0.4.15.8_report.json`, and `tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json`.
- Added `docs/post_near_tie_patch_main_chain_repair_v0.4.15.8.md`.

Report wording:
> v0.4.15.8 repairs the post near-tie patch main-chain regression. The original regression was reproduced at 31/60 full RAG eval with 28 rerank misses. The fix narrows deterministic same-bucket ordering to small true near-tie groups and preserves Cross-Encoder order for large buckets. A second repair lets the risk taxonomy recognize canonical structured risk type names such as `滥用市场支配地位风险`. The final full RAG eval returns to 60/60 passed with all retrieval stages `PASS`.

Verification:
- Targeted near-tie regression repeat: 5 cases, repeat 3, all passed.
- Targeted antitrust risk-level repeat: repeat 3, all passed.
- Final full RAG eval: 60/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`.
- Unit tests cover large-bucket non-reordering, taxonomy exact-name inference, and risk analyzer level upgrade.

### v0.4.15.9: Post Near-Tie Main-Chain Stability Closeout

Stage: stability closeout after the v0.4.15.8 main-chain repair.

Problem solved: v0.4.15.8 restored full RAG eval to 60/60, but the project still needed a practical stability check before leaving the near-tie repair thread. v0.4.15.9 runs targeted repeats on recent/high-risk cases, a single full eval, and a focused repeat for the only single-run full-eval wording miss.

Key outputs:
- Generated `tests/targeted_main_chain_stability_v0.4.15.9_report.json`.
- Generated `tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json`.
- Generated `tests/targeted_data_export_answer_stability_v0.4.15.9_report.json`.
- Added `docs/post_near_tie_main_chain_stability_closeout_v0.4.15.9.md`.

Report wording:
> v0.4.15.9 closes the post near-tie main-chain stability check. The 8-case targeted packet passed across three repeats with no unstable cases. A single full RAG eval returned 59/60, but all 60 cases had retrieval stage `PASS`; the only miss was a single answer keyword wording variance in `data_export_contract_trigger_001`. A focused five-run repeat for that case passed 5/5, confirming that the evidence path was stable and no prompt, eval case, anchor, or retriever patch should be made for this single wording variance.

Verification:
- Targeted stability packet: `[8, 8, 8]`, `all_runs_full_pass=true`.
- Single full eval: 59/60, `retrieval_failure_stage_summary={"PASS": 60}`.
- Focused data-export repeat: `[1, 1, 1, 1, 1]`, `all_runs_full_pass=true`.

### v0.4.15.10: Standard Contract Term Preservation

Stage: evidence-driven output stabilization for a post-repair answer wording gap.

Problem solved: v0.4.15.9 showed that retrieval and evidence were stable, but `data_export_contract_trigger_001` could miss the wording `补充订立` in one full eval run. The supporting evidence was already present: Article 8 of the `个人信息出境标准合同办法` says the processor should reassess and supplement or re-enter the standard contract and complete filing procedures.

Key outputs:
- Modified `src/rag/retriever.py`.
- Extended `tests/test_retriever_contract.py`.
- Generated `tests/targeted_data_export_term_preservation_v0.4.15.10_report.json`.
- Generated `tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json`.
- Generated `tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json`.
- Added `docs/standard_contract_term_preservation_v0.4.15.10.md`.

Report wording:
> v0.4.15.10 adds an evidence-driven term preservation rule for standard-contract reassessment answers. When the question asks about standard-contract reassessment and the evidence source is `个人信息出境标准合同办法`, the answer preserves the supported follow-up action that the processor should supplement or re-enter the standard contract and complete filing procedures. This closes the single-run wording variance without modifying prompts, anchors, eval cases, hidden seeds, risk supplement rules, rerank behavior, or Qdrant.

Verification:
- Data-export focused repeat: 5/5 passed, contribution label `TERM_PRESERVATION_PASS`.
- 8-case targeted repeat: `[8, 8, 8]`, no unstable cases.
- Full RAG eval: 60/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`.

### v0.4.15.11: Hidden-Seed Signal Diagnostics & Output Stability

Stage: main-chain diagnostics and evidence-driven output stability repair.

Problem solved: hidden seed annotations showed that future legal RAG review needs generic evidence-alignment signals, while current public eval still had occasional answer wording/risk-level variance when the evidence chain was already correct. v0.4.15.11 adds report-only diagnostics and stabilizes narrowly scoped output terms without modifying retrieval, rerank, anchors, prompts, eval cases, hidden seeds, risk supplement rules, scenario registry, fixtures, or Qdrant.

Key outputs:
- Modified `tools/run_rag_eval.py`.
- Modified `src/rag/retriever.py`.
- Extended `tests/test_rag_eval_diagnostics.py`.
- Extended `tests/test_retriever_contract.py`.
- Generated `tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json`.
- Generated `tests/targeted_output_stability_v0.4.15.11_report.json`.
- Generated `tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json`.
- Added `docs/hidden_seed_signal_diagnostics_output_stability_v0.4.15.11.md`.

Report wording:
> v0.4.15.11 adds `quality_signal_diagnostics` to the existing RAG eval report, covering major evidence gaps, known-bad evidence leakage, domain pollution, definition-only substitution, and same-bucket selection-order risk. It also adds evidence-driven output stabilization for product liability compensation terms, generic trademark-name risk, illegal dividend loss-coverage wording, and unnotified share-transfer risk level. Full RAG eval is 60/60, and the new diagnostics surface 18 same-bucket selection-order review signals for future analysis.

Verification:
- Product-liability focused repeat: 5/5 passed.
- Output-stability targeted repeat: `[4, 4, 4]`, `unstable_cases=[]`.
- Full RAG eval: 60/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`.

### v0.4.15.12: Same-Bucket Signal Calibration

Stage: RAG eval quality-signal calibration after v0.4.15.11 surfaced noisy same-bucket review signals.

Problem solved: v0.4.15.11 correctly added same-bucket diagnostics, but the signal over-reported review risks even when the final evidence already satisfied expected evidence. A direct runtime sorting/selection repair was tested and rejected because it broke stable evidence chains. v0.4.15.12 keeps the main RAG path unchanged and calibrates diagnostics instead.

Key outputs:
- Modified `tools/run_rag_eval.py`.
- Extended `tests/test_rag_eval_diagnostics.py`.
- Generated `tests/targeted_same_bucket_baseline_v0.4.15.12_report.json`.
- Generated `tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json`.
- Generated `tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json`.
- Generated `tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json`.
- Added `docs/same_bucket_signal_calibration_v0.4.15.12.md`.

Report wording:
> v0.4.15.12 calibrates same-bucket selection-order diagnostics without changing retrieval, rerank, anchors, prompts, risk rules, eval cases, hidden seeds, or Qdrant. Same-bucket high-score candidates remain visible as `score_order_observations`, while `same_bucket_selection_order_risk` is reserved for candidates that affect missing expected evidence or operative statute coverage. Baseline full eval is 60/60; calibrated full eval has all 60 retrieval stages passing, with one single-run answer keyword variance confirmed stable by a 5/5 focused repeat.

Verification:
- Diagnostic unit tests passed.
- Targeted same-bucket baseline: `[4, 4, 4]`, `all_runs_full_pass=true`.
- Baseline full eval: 60/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`.
- Calibrated full eval: 59/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`, `same_bucket_selection_order_risk=0`.
- Focused `risk_employee_facial_001` repeat: 5/5 passed.

### v0.4.15.13: RAG Eval Compact Report Profile

Stage: RAG eval report maintainability and review ergonomics.

Problem solved: recent full RAG eval reports can become very large because each case stores full debug payloads. This is useful for deep attribution, but it makes routine report review, indexing, and repository maintenance harder. v0.4.15.13 adds a compact report profile that is available only when explicitly requested.

Key outputs:
- Modified `tools/run_rag_eval.py`.
- Extended `tests/test_rag_eval_diagnostics.py`.
- Generated `tests/targeted_compact_report_profile_v0.4.15.13_report.json`.
- Added `docs/rag_eval_compact_report_profile_v0.4.15.13.md`.

Report wording:
> v0.4.15.13 adds an opt-in `--compact-report` profile to RAG eval output. Default reports remain full and unchanged. Compact reports remove bulky per-case `debug_info` and `contribution_trace` payloads while keeping case outcomes, evidence chains, retrieval diagnostics, quality-signal diagnostics, and compact summary counts. This improves routine review and repository maintainability without changing retrieval, rerank, anchors, prompts, risk rules, eval cases, hidden seeds, fixtures, or Qdrant.

Verification:
- Diagnostic unit tests passed.
- Focused compact smoke: 1/1 passed, `retrieval_failure_stage_summary={"PASS": 1}`.
- Default full smoke retained full `debug_info`.
- Compact smoke wrote `report_profile="compact"`, removed full `debug_info`, and retained `debug_info_summary`.

### v0.4.15.14: Roadmap Maintenance & Compact Eval Baseline

Stage: roadmap maintainability and lightweight current-state RAG baseline.

Problem solved: the project roadmap had drifted back into a long small-version ledger, which made it harder to see current engineering direction. v0.4.15.14 archives the old long roadmap and turns the active roadmap into a current-state document. It also uses the v0.4.15.13 compact report profile to produce a lightweight full RAG eval baseline.

Key outputs:
- Updated `docs/project_review_and_roadmap.md`.
- Archived `docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md`.
- Added `docs/roadmap_maintenance_compact_eval_baseline_v0.4.15.14.md`.
- Generated `tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json`.

Report wording:
> v0.4.15.14 reduces roadmap maintenance debt by converting the active roadmap into a current-state planning document and preserving the previous long ledger as an archive snapshot. A compact full RAG eval baseline was also generated and passed 60/60 with all retrieval stages `PASS`, confirming there is no immediate full-eval regression to repair.

Verification:
- Compact full RAG eval: 60/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`.

### v0.4.15.15: RAG Quality Triage

Stage: saved-report quality triage after full eval returned to 60/60.

Problem solved: a 60/60 full eval answers whether the current eval suite passes, but not how heavily the pass depends on anchors, risk supplement rules, term preservation, or other support layers. v0.4.15.15 adds a saved-report-only triage builder to identify dependency-heavy passing cases without changing runtime behavior.

Key outputs:
- Added `tools/build_rag_quality_triage.py`.
- Added `tests/test_rag_quality_triage.py`.
- Generated `tests/rag_quality_triage_v0.4.15.15_report.json`.
- Added `docs/rag_quality_triage_v0.4.15.15.md`.

Report wording:
> v0.4.15.15 confirms there is no immediate full-eval failure to repair: the compact baseline is 60/60 with retrieval `PASS=60` and `score_order_risks=0`. The main quality signal is pass dependency concentration: `ANCHOR_PASS=31`, `RISK_SUPPLEMENT_PASS=44`, and only 6 pure LLM passes. The next engineering work should be dependency-reduction triage, not a runtime fix.

Verification:
- Triage unit tests passed.
- Saved-report triage status: `passed_with_high_dependency`.

### v0.4.15.16: Dependency Trace Summary

Stage: targeted observability for dependency-heavy passing cases.

Problem solved: v0.4.15.15 identified high dependency concentration but did not include full debug traces. v0.4.15.16 reruns a small targeted packet without `--compact-report` and summarizes the full debug trace without changing runtime behavior.

Key outputs:
- Generated `tests/targeted_dependency_trace_v0.4.15.16_report.json`.
- Added `tools/build_dependency_trace_summary.py`.
- Added `tests/test_dependency_trace_summary.py`.
- Generated `tests/dependency_trace_summary_v0.4.15.16_report.json`.
- Added `docs/dependency_trace_summary_v0.4.15.16.md`.

Report wording:
> v0.4.15.16 confirms that dependency-heavy priority cases still pass: targeted trace is 8/8 with retrieval `PASS=8`. The trace summary shows that 7/8 cases are `base_union_gap_anchor_filled`, meaning base union retrieval did not satisfy expected evidence before anchor supplementation. One case has union retrieval satisfied but still carries manual-review/output-rule dependency. The next work should inspect query lexical coverage and base retrieval, not directly change anchors or risk supplements.

Verification:
- Targeted full-debug trace: 8/8 passed.
- Dependency trace summary status: `needs_dependency_reduction_trace_review`.

### v0.4.15.17: Base Retrieval / Query Inspection

Stage: saved-report inspection of base retrieval gaps in dependency-heavy passing cases.

Problem solved: v0.4.15.16 showed that 7/8 dependency-heavy passing cases were anchor-filled, but did not distinguish whether the issue was missing query hints or base union candidate coverage. v0.4.15.17 inspects saved full-debug traces to compare query features, union candidates, final refs, and anchor-filled final refs.

Key outputs:
- Added `tools/build_base_retrieval_query_inspection.py`.
- Added `tests/test_base_retrieval_query_inspection.py`.
- Generated `tests/base_retrieval_query_inspection_v0.4.15.17_report.json`.
- Added `docs/base_retrieval_query_inspection_v0.4.15.17.md`.

Report wording:
> v0.4.15.17 shows that the dependency issue is not simply missing query hints. The inspected anchor-filled cases already include related concepts and scenario anchor statute hints in the rerank query, but base union retrieval still misses the final legal refs later supplied by anchors. The next step should inspect base candidate sources and query term coverage before any runtime change.

Verification:
- Base retrieval/query inspection unit test passed.
- Saved-report inspection status: `base_retrieval_query_inspection_needed`.

### v0.4.15.18: Base Candidate Source / Lexical Mismatch Summary

Stage: saved-report source/article drift and lexical mismatch summary before Qdrant inspection.

Problem solved: v0.4.15.17 confirmed that the seven anchor-filled cases already had related concepts and scenario anchor statute hints in the rerank query, but base union retrieval still missed final refs. v0.4.15.18 narrows that signal to base candidate source/article drift using existing saved reports only.

Key outputs:
- Added `tools/build_base_candidate_mismatch_summary.py`.
- Added `tests/test_base_candidate_mismatch_summary.py`.
- Generated `tests/base_candidate_mismatch_summary_v0.4.15.18_report.json`.
- Added `docs/base_candidate_mismatch_summary_v0.4.15.18.md`.

Report wording:
> v0.4.15.18 shows that the next boundary is Qdrant/live retrieval inspection. Saved reports can identify that seven anchor-filled cases have `same_source_article_drift` and 14 final refs missing from base union candidates, but cannot prove whether those refs are absent from Qdrant payloads, filtered before candidate collection, or scored below candidate cutoffs.

Boundary:
- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation, scenario registry, fixture, eval case, Qdrant, retriever, or `rag_query` change.
- This is an offline RAG grounding diagnostic, not a gate and not a runtime fix.

Verification:
- Base candidate mismatch summary unit tests passed.
- Saved-report summary status: `qdrant_or_live_retrieval_needed`.

### v0.4.15.19: Base Candidate Live Read-Only Probe

Stage: targeted Qdrant live read-only inspection for the final refs missing from base union candidates.

Problem solved: v0.4.15.18 showed that saved reports could not prove whether missing refs were absent from Qdrant, filtered before candidate collection, or lost by retrieval rank/cutoff. v0.4.15.19 performs a targeted read-only probe against `legal_knowledge` without writing Qdrant or calling the RAG main flow.

Key outputs:
- Added `tools/build_base_candidate_live_readonly_probe.py`.
- Added `tests/test_base_candidate_live_readonly_probe.py`.
- Generated `tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json`.
- Added `docs/base_candidate_live_readonly_probe_v0.4.15.19.md`.

Report wording:
> v0.4.15.19 rules out Qdrant payload absence and runtime metadata-filter exclusion for the 14 missing final refs: all 14 are present in `legal_knowledge` and pass the runtime metadata filters. Ten refs are visible in sparse high-k but lost before the production base union, pointing to sparse rank/cutoff and candidate-depth behavior. Four refs still require explicit dense rank inspection because dense probing is disabled by default to avoid unplanned embedding-service calls.

Boundary:
- Qdrant access is read-only; no write, delete, collection rebuild, alias switch, or upsert is performed.
- No `rag_query`, eval, LLM, Cross-Encoder, anchor, prompt, rerank, risk supplement, term preservation, scenario registry, fixture, eval case, or retriever runtime change.

Verification:
- Live read-only probe unit tests passed.
- Default live probe status: `completed_requires_dense_probe`.

### v0.4.15.20: Base Candidate Dense Live Probe

Stage: explicit dense-enabled live read-only probe for the remaining base retrieval attribution gap.

Problem solved: v0.4.15.19 ruled out Qdrant payload absence and runtime metadata-filter exclusion, but left four refs requiring dense rank inspection. v0.4.15.20 explicitly enables dense probing to complete the rank/cutoff attribution.

Key outputs:
- Added `tools/build_base_candidate_dense_live_probe.py`.
- Added `tests/test_base_candidate_dense_live_probe.py`.
- Generated `tests/base_candidate_dense_live_probe_v0.4.15.20_report.json`.
- Added `docs/base_candidate_dense_live_probe_v0.4.15.20.md`.

Report wording:
> v0.4.15.20 closes the live retrieval attribution loop. All 14 missing final refs exist in Qdrant and pass runtime metadata filters. Ten are sparse rank/cutoff losses, two are dense rank/cutoff losses, and two remain confirmed base retrieval gaps even with dense high-k and sparse high-k probes. This supports a minimal runtime validation patch around base candidate depth and union collection, not anchor expansion.

Boundary:
- Qdrant access is read-only; no write, rebuild, alias switch, or upsert is performed.
- Dense query embedding is explicitly allowed for this diagnostic version.
- No `rag_query`, eval, LLM, Cross-Encoder, anchor, prompt, rerank, risk supplement, term preservation, scenario registry, fixture, eval case, or retriever runtime change.

Verification:
- Dense live probe wrapper unit test passed.
- Dense live probe status: `completed_with_dense_probe`.

### v0.4.15.21: Base Candidate Depth Runtime Patch

Stage: minimal runtime candidate-depth patch after live retrieval attribution.

Problem solved: v0.4.15.19-v0.4.15.20 showed that the missing final refs were present in Qdrant and usually lost by sparse/base candidate cutoff. v0.4.15.21 applies the smallest passing runtime change: increase sparse retrieval depth from 10 to 20 while keeping dense depth, base union size, rerank input size, and base/anchor quotas at their prior effective budgets.

Key outputs:
- Modified `src/rag/retriever.py`.
- Updated `tests/test_candidate_budget.py`.
- Generated `tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json`.
- Generated `tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json`.
- Added `docs/base_candidate_depth_runtime_patch_v0.4.15.21.md`.

Report wording:
> v0.4.15.21 is a conservative base retrieval runtime patch. It raises sparse candidate depth to 20 after live probes confirmed sparse rank/cutoff loss, but keeps base union, rerank input, and base/anchor quotas unchanged. A broader candidate expansion was rejected because it caused IP-domain evidence regressions. The final patch passes targeted validation 7/7 and compact full RAG eval 60/60.

Boundary:
- No hidden seed, anchor, prompt, rerank algorithm, risk supplement, term preservation, scenario registry, fixture, or eval case change.
- No Qdrant write, rebuild, alias switch, or upsert.
- This is a general base retrieval candidate collection fix, not a sample patch and not another gate.

Verification:
- Candidate budget and retriever contract unit tests passed.
- Targeted base-candidate-depth validation: 7/7 passed.
- Compact full RAG eval: 60/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`.

### v0.4.15.22: Risk Level Exact Policy

Stage: eval runner quality repair for risk-level acceptance.

Problem solved: `tools/run_rag_eval.py` previously treated `actual risk_level >= expected_risk_level` as a pass for non-low expected levels. That allowed `risk_level=high, expected=medium` to be reported as OK, masking false-positive risk severity. v0.4.15.22 changes `expected_risk_level` to exact matching and records structured mismatch details.

Key outputs:
- Modified `tools/run_rag_eval.py`.
- Extended `tests/test_rag_eval_diagnostics.py`.
- Generated `tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json`.
- Generated `tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json`.
- Added `docs/risk_level_exact_policy_v0.4.15.22.md`.

Report wording:
> v0.4.15.22 tightens RAG eval risk-level acceptance from minimum-threshold matching to exact matching. This is an eval quality repair, not a RAG runtime patch. Under the stricter policy, retrieval remains healthy with full-eval retrieval `PASS=60`, but full eval becomes 55/60 because five cases are now correctly exposed as `over_risk` mismatches.

Boundary:
- No `rag_query`, retriever, anchor, prompt, rerank, risk supplement, term preservation, scenario registry, fixture, eval case, hidden seed, or Qdrant change.
- The 55/60 result is expected under stricter evaluation and should be treated as a risk-level quality debt baseline.

Verification:
- RAG eval diagnostic unit tests passed.
- Targeted exact-risk-level validation: 2/6 passed, 4 `over_risk` mismatches, retrieval `PASS=6`.
- Compact full RAG eval: 55/60 passed, retrieval `PASS=60`, `risk_level_mismatch_summary={"exact_match":45,"over_risk":5}`.

### v0.4.15.23: Risk Level Over-Risk Attribution

Stage: saved-report-only attribution for strict risk-level over-risk failures.

Problem solved: v0.4.15.22 exposed five exact-policy `over_risk` failures, but did not classify whether they were likely caused by output rules, taxonomy/LLM wording, or expected-level ambiguity. v0.4.15.23 adds a read-only attribution builder that routes these cases into review buckets without changing runtime behavior or risk rules.

Key outputs:
- Added `tools/build_risk_level_overrisk_attribution.py`.
- Added `tests/test_risk_level_overrisk_attribution.py`.
- Generated `tests/risk_level_overrisk_attribution_v0.4.15.23_report.json`.
- Added `docs/risk_level_overrisk_attribution_v0.4.15.23.md`.

Report wording:
> v0.4.15.23 classifies the five exact-policy `over_risk` cases from v0.4.15.22 as attribution candidates, not proven root causes. All five retain retrieval `PASS`; all five show strong saved-report signals for output-rule amplification, with four involving risk supplement rules and four involving scene output rules. The next step should be targeted full-trace or manual review before changing any risk rules.

Boundary:
- Saved-report-only; no eval run, `rag_query`, Qdrant, LLM, Cross-Encoder, retriever, anchor, prompt, rerank, risk supplement, term preservation, taxonomy, scenario registry, fixture, eval case, or hidden seed change.
- Compact report fields are insufficient to prove concrete rule ids or taxonomy default-level root causes.

Verification:
- Over-risk attribution unit tests passed.
- Attribution report status: `overrisk_attribution_ready`.
- Over-risk case count: 5.
- Attribution counts: `output_rule_amplification_review=5`.

### v0.4.15.24: Risk Level Over-Risk Legal Review Packet

Stage: saved-report-only preliminary legal review for strict risk-level over-risk failures.

Problem solved: v0.4.15.23 identified five output-rule amplification candidates, but the next engineering step still needed a legal reasonableness split: which failures look like true over-risk, and which may be defensible high-risk legal assessments. v0.4.15.24 creates that split without changing runtime rules.

Key outputs:
- Added `tools/build_risk_level_overrisk_legal_review_packet.py`.
- Added `tests/test_risk_level_overrisk_legal_review_packet.py`.
- Generated `tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json`.
- Added `docs/risk_level_overrisk_legal_review_packet_v0.4.15.24.md`.

Report wording:
> v0.4.15.24 converts the five exact-policy `over_risk` failures into a preliminary legal review packet. Two trademark cases are likely overstated at `high`, one property-management case is more consistent with `medium`, and the VAT mixed-sales and unfair-competition confusion cases are legally defensible boundary cases requiring fact-strength review. The packet keeps `rule_change_allowed=false`; it is a review basis for targeted full trace or minimal rule repair, not a rule change.

Boundary:
- Saved-report-only; no eval run, `rag_query`, Qdrant, LLM, Cross-Encoder, retriever, anchor, prompt, rerank, risk supplement, term preservation, taxonomy, scenario registry, fixture, eval case, or hidden seed change.
- Legal judgments are preliminary diagnostics based on current report facts and evidence chains, not final legal opinions.

Verification:
- Over-risk legal review packet unit tests passed.
- Generated packet status: `legal_review_packet_ready`.
- Legal reasonableness counts: `actual_high_likely_overstated=2`, `expected_medium_likely_reasonable=1`, `actual_high_potentially_defensible=2`.

### v0.4.15.25: Trademark Over-Risk Runtime Patch

Stage: narrow RAG runtime risk-level repair.

Problem solved: strict risk-level eval exposed two trademark cases where evidence retrieval and answer coverage were healthy, but the final `risk_level` was overstated as `high`. v0.4.15.25 adds a narrow medium cap for trademark generic-name invalidity and three-year non-use cancellation scenarios, while explicitly excluding infringement, confusion, fake-mark, reverse passing-off, and compensation scenarios.

Key outputs:
- Modified `src/rag/retriever.py`.
- Extended `tests/test_retriever_contract.py`.
- Generated `tests/targeted_trademark_overrisk_trace_v0.4.15.25_report.json`.
- Generated `tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json`.
- Generated `tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json`.
- Added `docs/trademark_overrisk_runtime_patch_v0.4.15.25.md`.

Report wording:
> v0.4.15.25 is the first strict risk-level over-risk runtime repair after the exact-policy baseline. It fixes two clearly overstated trademark cases through a narrow, legally bounded calibration in `enrich_risk_payload`: generic-name invalidity and continuous three-year non-use cancellation are capped at `medium`, while infringement, confusion, fake-mark and compensation facts remain `high`. Targeted validation is 2/2 passed, and compact full eval improves to 56/60 with retrieval still `PASS=60`.

Boundary:
- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation, taxonomy, scenario registry, fixture, eval case, or Qdrant change.
- This is a runtime quality repair for a general trademark legal pattern, not a sample-specific patch and not a new gate.

Verification:
- Retriever contract unit tests passed.
- Targeted trademark over-risk patch eval: 2/2 passed.
- Compact full RAG eval: 56/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`, remaining strict failures are 4 `over_risk` cases.

### v0.4.15.26: Process Over-Risk Runtime Hardening

Stage: strict risk-level runtime hardening for procedural and civil-management over-risk cases.

Problem solved: after v0.4.15.25, several remaining failures were not retrieval failures but risk-severity overstatements. `risk_property_management_001`, `risk_company_share_transfer_001`, and ordinary `risk_vat_mixed_sales_001` are better treated as medium-risk civil/procedural/accounting disputes absent severe facts. v0.4.15.26 adds narrow medium caps and hardens the trademark generic-name cap against wording drift.

Key outputs:
- Modified `src/rag/retriever.py`.
- Extended `tests/test_retriever_contract.py`.
- Generated `tests/targeted_process_overrisk_trace_v0.4.15.26_report.json`.
- Generated `tests/targeted_process_overrisk_patch_v0.4.15.26_report.json`.
- Generated `tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json`.
- Generated `tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json`.
- Generated `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json`.
- Added `docs/process_overrisk_runtime_hardening_v0.4.15.26.md`.

Report wording:
> v0.4.15.26 continues the strict risk-level repair by capping narrowly defined procedural/civil-management/accounting cases at `medium`: property-management common-area commercial use without owner consent, LLC outward share transfer without notice to other shareholders in the priority-purchase-right context, and ordinary VAT mixed-sales rate/accounting misclassification without aggravating tax facts. It also hardens the trademark generic-name cap so evaluative wording like `商标权滥用风险` does not block the medium calibration. The compact full eval improves to 59/60 with retrieval still `PASS=60`; the remaining unfair-competition confusion case is legally defensible as high and should be reviewed before further runtime change.

Boundary:
- No hidden seed, anchor, prompt, rerank, risk supplement config, term preservation, taxonomy, scenario registry, fixture, eval case, Qdrant, or evidence selector change.
- Severe property misappropriation, generic property-income disputes without an owner-consent gap, listed-company disclosure, state-owned transfers, judicial execution, pledged shares, fraudulent share transfers, VAT false invoices/tax evasion/export-refund/non-filing/refusal or criminal-administrative escalation facts, and real trademark infringement/confusion/fake-mark scenarios remain high.
- This is runtime risk-level hardening, not a new gate or sample patch.

Verification:
- Retriever contract unit tests passed.
- Targeted process over-risk validation: 2/2 passed.
- Targeted trademark over-risk validation: 2/2 passed.
- Compact full RAG eval: 59/60 passed, retrieval `PASS=60`; remaining failure is `risk_unfair_competition_confusion_001`.

### v0.4.15.27: RAG Quality/Stability Series Closeout

Stage: v0.4.15.x series closeout and next-stage boundary setting.

Problem solved: after v0.4.15.26, the remaining strict eval failure is no longer a retrieval, grounding, or obvious runtime-calibration defect. `risk_unfair_competition_confusion_001` has known-brand similarity and actual consumer confusion facts, making the runtime `high` assessment legally defensible even though the current eval expectation is `medium`.

Key outputs:
- Updated `src/main.py` version to `0.4.15.27`.
- Updated `tools/run_project_health_check.py` version to `0.4.15.27`.
- Updated `changelog.md` and `docs/project_review_and_roadmap.md`.
- No new runtime rule, gate, anchor, eval case, or saved eval report.

Report wording:
> v0.4.15.27 formally closes the v0.4.15.x RAG quality/stability series. The closeout keeps v0.4.15.26 as the evidence baseline: compact full RAG eval is 59/60 with retrieval `PASS=60`, and the only remaining strict risk-level miss is the unfair-competition confusion case. Because the facts include known-brand similarity and actual consumer confusion, the system's `high` risk level is legally defensible; the next step should be expected-level or fact-strength review, not another runtime patch.

Boundary:
- No retriever, anchor, prompt, rerank, risk supplement config, term preservation, taxonomy, scenario registry, fixture, eval case, Qdrant, or evidence selector change.
- This is a release closeout, not a new product capability and not a sample repair.

Verification:
- Version consistency and project health check passed.
- Existing v0.4.15.26 compact full eval report remains the closeout baseline.

### v0.4.16.1：API Contract Baseline

阶段：前后端接入前的 API contract 稳定层。

解决的问题：v0.4.15.x 收口后，项目需要先固定当前 FastAPI 表面，再考虑正式 UI 接入。本版本确认核心路径、请求默认值、响应必需字段和统一错误结构，不改变 RAG runtime。

关键输出：
- 新增 `tests/test_api_contract.py`。
- 新增 `docs/api_contract_stability_v0.4.16.1.md`。
- 同步 `src/main.py` 与 `tools/run_project_health_check.py` 版本为 `0.4.16.1`。

报告写法：
> v0.4.16.1 启动前后端接入前的 API contract 基线。它不接正式前端，也不修改检索或风险逻辑，而是在 schema 层固定当前 FastAPI 表面：`/health`、`/ask`、`/risk/analyze`、`/risk/report`、`/risk/report/export`、请求默认值、响应必需字段和统一错误结构。

边界：不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder；不修改 retriever、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry、fixture 或 eval case。

验证：API contract 单测与项目 health check 通过。

### v0.4.16.2：API Error and Export Contract

阶段：前后端接入前的 API 错误与导出契约稳定层。

解决的问题：未来前端需要在正式 UI 集成前知道失败响应和报告导出的稳定形状。本版本固定统一错误 envelope，并固定 `/risk/report/export` 的 Markdown/JSON content-type 行为。

关键输出：
- 扩展 `tests/test_api_contract.py`。
- 新增 `docs/api_error_and_export_contract_v0.4.16.2.md`。
- 同步服务与 health check 版本为 `0.4.16.2`。

报告写法：
> v0.4.16.2 稳定未来前端可依赖的 API 错误与导出契约。错误响应统一为 `{error: {code, message}}`，Markdown 报告导出返回 `text/markdown`，JSON 报告导出返回 `application/json`，不支持的导出格式会在运行时调用前被请求校验拦截。

边界：仅使用 `TestClient` 与 mock；不调用真实报告生成、RAG、Qdrant、LLM 或 Cross-Encoder；不修改 retriever、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry、fixture 或 eval case。

验证：API contract 单测与项目 health check 通过。

### v0.4.16.3：OpenAPI Schema Snapshot

阶段：前后端接入前的 OpenAPI schema 交付物。

解决的问题：正式前端集成前，需要一份可审阅、可比对的 API schema 文件。本版本把当前 FastAPI OpenAPI schema 导出为保存的 JSON 产物，并明确记录未调用 RAG 或报告生成。

关键输出：
- 新增 `tools/export_openapi_schema.py`。
- 生成 `tests/openapi_schema_v0.4.16.3.json`。
- 新增 `docs/openapi_schema_snapshot_v0.4.16.3.md`。
- 扩展 `tests/test_api_contract.py`。

报告写法：
> v0.4.16.3 生成供后续前端交接使用的 OpenAPI schema 快照。该快照覆盖当前 FastAPI 表面，不启动服务、不调用 RAG/Qdrant/LLM，为未来 UI 工作提供可比对的稳定 schema 文件。

边界：不启动服务，不调用 RAG、Qdrant、LLM、Cross-Encoder 或报告生成；不修改 retriever、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry、fixture 或 eval case。

验证：OpenAPI schema 导出成功，API contract 单测与项目 health check 通过。

### v0.4.16.4：API Example Payload Fixture

阶段：前后端接入前的 API example payload 稳定层。

解决的问题：前端和离线工作台规划需要形状真实的样例数据，但样例不能触发 RAG、Qdrant、LLM 或真实报告生成。本版本新增一份通过模型校验的 fixture，覆盖当前 API 的主要请求/响应形状。

关键输出：
- 新增 `tests/fixtures/api_contract_example_payloads_v0.4.16.4.json`。
- 新增 `docs/api_example_payloads_v0.4.16.4.md`。
- 扩展 `tests/test_api_contract.py`。
- 同步服务与 health check 版本为 `0.4.16.4`。

报告写法：
> v0.4.16.4 新增离线 API example payload，供未来前端交接参考。fixture 覆盖 `/ask`、`/risk/analyze`、`/risk/report` 和 `/risk/report/export` 的 Markdown/JSON 样例，单测会用当前 Pydantic 契约验证这些样例，且不调用 RAG、Qdrant、LLM 或真实报告生成。

边界：仅新增 API example payload fixture；不修改 RAG fixture、eval case、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry 或 Qdrant。

验证：API contract 单测与项目 health check 通过。

### v0.4.16.5：Roadmap and Final Report Maintenance

阶段：前后端接入前文档治理收口。

解决的问题：v0.4.16.x 开始后，roadmap 与 final report guide 需要继续保持可审阅，而不是重新堆小版本流水账。本版本明确 roadmap 的维护规则，并把 final report guide 中 v0.4.16 新增版本素材统一为中文、按版本号自然升序维护。

关键输出：
- 更新 `docs/project_review_and_roadmap.md`，新增“已完成事项最多保留最近两个版本”的维护规则。
- 更新 `docs/final_report_version_guide.md`，统一 v0.4.16 素材写法。
- 同步服务与 health check 版本为 `0.4.16.5`。

报告写法：
> v0.4.16.5 收口文档治理口径：roadmap 只保留当前阶段判断和最近两个版本完成事项，详细流水账继续归入 `changelog.md`；final report guide 使用中文记录新增版本素材，并保持自然升序，避免后续交付材料再次失序。

边界：不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。

验证：文档和版本一致性检查、项目 health check 通过。

### v0.4.16.6：API Endpoint Smoke Contract

阶段：前后端接入前的 API 路由层 smoke contract。

解决的问题：此前已有 schema、响应模型和 example payload，但 `/ask`、`/risk/analyze`、`/risk/report` 仍缺少路由层 mock smoke 覆盖。本版本用 `TestClient + mock` 验证请求确实进入对应 runtime 入口，并能返回符合契约的响应。

关键输出：
- 扩展 `tests/test_api_contract.py`，新增三个 endpoint smoke contract。
- 覆盖 `/ask -> rag_query`、`/risk/analyze -> analyze_risk`、`/risk/report -> generate_risk_report`。
- 验证 `collection_name`、`k`、`doc_type`、`category`、`jurisdiction`、`score_threshold`、`debug` 以及其他可选过滤字段的透传。
- 同步服务与 health check 版本为 `0.4.16.6`。

报告写法：
> v0.4.16.6 补齐前端接入前的 API 路由层 smoke contract。测试通过 mock 隔离真实 RAG/Qdrant/LLM，只验证路由入口、响应契约和请求过滤参数透传，降低未来 UI 联调时出现接口漂移的风险。

边界：不调用真实 RAG、Qdrant、LLM、Cross-Encoder 或报告生成；不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。

验证：API contract 单测与项目 health check 通过。

### v0.4.16.7：Roadmap Next-Step Hygiene

阶段：roadmap 下一步区块治理。

解决的问题：`docs/project_review_and_roadmap.md` 的 `## 推荐下一步` 区块曾残留已完成版本流水账，和“roadmap 不继续堆历史”的维护规则冲突。本版本清理该污染，并新增测试防止该区块再次变成长历史账本。

关键输出：
- 清理 `docs/project_review_and_roadmap.md` 的 `## 推荐下一步` 区块，只保留当前下一步判断。
- 新增 `tests/test_roadmap_hygiene.py`。
- 修正 `tests/test_project_health_check.py` 的旧版本硬编码，使 health report 版本断言跟随当前工具版本。
- 同步服务与 health check 版本为 `0.4.16.7`。

报告写法：
> v0.4.16.7 修复 roadmap 的“推荐下一步”污染：该区块不再堆放旧版本完成记录，而只保留当前待办和下一步边界。新增 roadmap hygiene 测试后，如果后续再次把已完成版本流水账写回该区块，测试会直接暴露。

边界：不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。

验证：Roadmap hygiene 单测、API contract 回归、project health check 单测与项目 health check 通过。

### v0.4.16.8：API Contract Bundle

阶段：前后端接入前的离线 API 交付物整合。

解决的问题：已有 OpenAPI schema、example payload fixture 和路由 mock smoke contract，但前端和工作台还需要一个一站式机器可读 bundle。本版本把 schema 与样例合并，方便后续界面接入和审阅。

关键输出：
- 新增 `tools/export_api_contract_bundle.py`。
- 新增 `tests/api_contract_bundle_v0.4.16.8.json`。
- 新增 `docs/api_contract_bundle_v0.4.16.8.md`。
- 扩展 `tests/test_api_contract.py`，验证 bundle 同时包含 schema、example payload 和 guardrails。
- 同步服务与 health check 版本为 `0.4.16.8`。

报告写法：
> v0.4.16.8 把当前 OpenAPI schema 和离线 example payload 组合成一个 API contract bundle。该 bundle 便于前端或工作台一次性读取接口、样例和 guardrails，但不启动服务，也不调用真实 RAG、Qdrant 或 LLM。

边界：不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。

验证：API contract bundle 单测与项目 health check 通过。

### v0.4.16.9：API Error Example Contract

阶段：前后端接入前的错误状态契约补齐。

解决的问题：前端除了成功响应，还需要稳定的异常态样例来设计展示和重试逻辑。本版本把 422 validation、504 timeout、500 internal error 纳入 API contract bundle，并用 `/ask` timeout mock 验证统一 504 envelope。

关键输出：
- 扩展 `tools/export_api_contract_bundle.py`，新增 `error_examples`。
- 扩展 `tests/test_api_contract.py`，验证错误样例和 `/ask` timeout 响应。
- 新增 `tests/api_contract_bundle_v0.4.16.9.json`。
- 同步服务与 health check 版本为 `0.4.16.9`。

报告写法：
> v0.4.16.9 补齐 API contract 的错误状态样例。bundle 现在同时包含成功样例和 422/504/500 异常态说明，前端可以据此设计校验错误、模型超时和内部错误的展示，而不需要调用真实 RAG、Qdrant 或 LLM。

边界：不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。

验证：API contract 单测与项目 health check 通过。

### v0.4.16.10：API Field Catalog

阶段：前后端接入前的字段目录交付。

解决的问题：前端表单、字段说明和展示映射不能只依赖 schema 快照，还需要一份更直接的模型字段目录。本版本导出请求/响应模型字段、必填项、默认值和 schema 片段。

关键输出：
- 新增 `tools/export_api_field_catalog.py`。
- 新增 `tests/api_field_catalog_v0.4.16.10.json`。
- 新增 `docs/api_field_catalog_v0.4.16.10.md`。
- 扩展 `tests/test_api_contract.py`，验证 field catalog 覆盖请求与响应模型字段、必填项和默认值。
- 同步服务与 health check 版本为 `0.4.16.10`。

报告写法：
> v0.4.16.10 新增 API field catalog，把请求/响应模型字段、必填项和默认值导出为离线 JSON。它服务于未来前端表单和展示映射，不接正式前端，也不改变 RAG 或 API runtime 行为。

边界：只做离线字段目录交付；不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。

验证：API contract 单测、索引检查、编码检查与项目 health check 通过。

### v0.4.16.11：API Contract Consistency Checker

阶段：前后端接入前的 API 契约交叉一致性诊断。

解决的问题：v0.4.16.x 已经形成 OpenAPI schema、example payload、bundle 和 field catalog 多个离线交付物。若这些文件之间悄悄漂移，未来前端接入会很难判断到底该相信哪一个。本版本新增只读一致性 checker，把这些产物放在同一张诊断表里比较。

关键输出：
- 新增 `tools/check_api_contract_consistency.py`。
- 新增 `tests/test_api_contract_consistency.py`。
- 新增 `tests/api_contract_consistency_v0.4.16.11_report.json`。
- 新增 `docs/api_contract_consistency_checker_v0.4.16.11.md`。
- 清理 `tests/test_api_contract.py` 中重复的 field catalog import 和重复测试定义。
- 同步服务与 health check 版本为 `0.4.16.11`。

报告写法：
> v0.4.16.11 新增 API contract consistency checker，用于离线比对 OpenAPI schema、API contract bundle、API field catalog 和 example payload fixture。它检查模型字段、必填项、核心路径 request/response 引用、bundle 来源和 guardrails 是否一致，当前结果为 `passed` 且 `issue_count=0`。

边界：不启动服务，不调用 `rag_query`、Qdrant、LLM 或真实报告生成；不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。

验证：API contract consistency checker、相关单测、索引检查、编码检查与项目 health check 通过。

### v0.4.16.12：API Contract Stability Closeout

阶段：前后端接入前 API contract stability 系列收口。

解决的问题：v0.4.16.x 已经形成多份离线契约材料，需要一个短收口文档说明这些材料的使用顺序、当前验证基线和后续边界，避免继续扩展设计型 gate。

关键输出：
- 新增 `docs/api_contract_stability_closeout_v0.4.16.12.md`。
- 同步服务与 health check 版本为 `0.4.16.12`。
- 更新 roadmap、changelog、final report guide、产物索引和维护索引。

报告写法：
> v0.4.16.12 收口 API contract stability 系列。当前离线契约包已包含 OpenAPI schema、example payload、API contract bundle、错误样例、field catalog 和 consistency checker；一致性基线为 `passed`、`issue_count=0`。下一阶段可以进入最小 mock service / UI handoff 准备，或另开正式前端接入设计。

边界：只做 closeout/runbook；不新增 checker，不启动服务，不接正式前端，不调用 `rag_query`、Qdrant、LLM 或真实报告生成；不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。

验证：API contract 相关单测、索引检查、编码检查与项目 health check 通过。

### v0.4.17.1：RAG Evidence Independence Baseline

阶段：RAG evidence independence / retrieval quality hardening 系列启动。

解决的问题：v0.4.15.26 的 RAG 基线虽然达到 `59/60` 且 retrieval stage `PASS=60`，但通过结果仍大量依赖 anchor、risk supplement 和 term preservation。本版本先只读 saved report 建立依赖归因基线，不直接改 runtime。

关键输出：
- 新增 `tools/build_rag_evidence_independence_baseline.py`。
- 新增 `tests/test_rag_evidence_independence_baseline.py`。
- 新增 `tests/rag_evidence_independence_baseline_v0.4.17.1_report.json`。
- 新增 `docs/rag_evidence_independence_baseline_v0.4.17.1.md`。
- 同步服务与 health check 版本为 `0.4.17.1`。

报告写法：
> v0.4.17.1 建立 RAG 主链路证据独立性基线。报告显示当前 `59/60` 通过、retrieval `PASS=60`，但高依赖 case 为 48/60，`high_dependency_ratio=0.8`；其中 `ANCHOR_PASS=29`、`RISK_SUPPLEMENT_PASS=43`、`TERM_PRESERVATION_PASS=8`、`PURE_LLM_PASS=7`。这说明下一阶段应先做小批量 targeted rerun 和依赖归因，而不是补 anchor 或改 prompt。

边界：只读 saved report；不运行 full eval 或 targeted eval；不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder；不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。

验证：依赖归因单测、索引检查、编码检查与项目 health check 通过。

### v0.4.17.2：RAG Targeted Rerun Packet

阶段：RAG evidence independence / retrieval quality hardening 系列的行动化收敛。

解决的问题：v0.4.17.1 已经说明高依赖比例较高，但如果直接改主链路，容易再次变成针对个别样本的补丁。本版本把高依赖信号转成小批量 targeted rerun 候选包，明确下一轮应验证哪些 case、为什么验证、如何运行。

关键输出：
- 新增 `tools/build_rag_targeted_rerun_packet.py`。
- 新增 `tests/test_rag_targeted_rerun_packet.py`。
- 新增 `tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`。
- 新增 `docs/rag_targeted_rerun_packet_v0.4.17.2.md`。
- 同步服务与 health check 版本为 `0.4.17.2`。

报告写法：
> v0.4.17.2 将 RAG evidence independence baseline 转化为 bounded targeted rerun packet。候选包共选出 17 个 case，其中 base retrieval lexical triage 8 个、output rule dependency review 5 个、failed/expected-level review 1 个、pure LLM control 3 个，并生成可复制的 targeted repeat 命令。本版本不运行 eval、不改主链路，结论是先验证依赖信号稳定性，再决定是否进入 runtime patch。

边界：只读 saved report；不运行 full eval 或 targeted eval；不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder；不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。

验证：候选包单测、依赖归因单测、索引检查、编码检查与项目 health check 通过。

### v0.4.17.3：RAG Targeted Repeat Closeout

阶段：RAG evidence independence / retrieval quality hardening 系列的实跑验证。

解决的问题：v0.4.17.2 只生成候选包，还没有证明高依赖样本在当前主链路中的实际稳定性。本版本按候选包执行 17 个 case、3 轮 targeted repeat，用真实运行结果判断是否需要立即进入 runtime patch。

关键输出：
- 新增 `tests/targeted_rag_evidence_independence_v0.4.17.3_report.json`。
- 新增 `docs/rag_targeted_repeat_closeout_v0.4.17.3.md`。
- 同步服务与 health check 版本为 `0.4.17.3`。

报告写法：
> v0.4.17.3 按 v0.4.17.2 packet 执行 17 个 case 的 targeted repeat。三轮 pass counts 均为 `16/17`，retrieval stage 每轮均为 `PASS=17`，`unstable_cases=0`；base retrieval lexical triage、output rule dependency review 和 pure LLM control 组均稳定通过。唯一固定失败仍是 `risk_unfair_competition_confusion_001` 的 `over_risk` expected-level/fact-strength 复核项，因此本版本不建议因该 packet 直接修改 retriever、anchor 或 prompt。

边界：运行 targeted eval，但不运行 full eval；不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant 数据。

验证：targeted repeat 报告成功写出；相关单测、索引检查、编码检查与项目 health check 通过。

### v0.4.17.4：RAG Expected-Level Review Packet

阶段：RAG evidence independence / retrieval quality hardening 系列的固定失败隔离。

解决的问题：v0.4.17.3 证明 targeted repeat 的唯一固定失败不是检索层失败，但仍需要把它从“主链路待修问题”中正式隔离出来，避免为了追求全绿而补 anchor、改 prompt 或直接改 eval case。

关键输出：
- 新增 `tools/build_rag_expected_level_review_packet.py`。
- 新增 `tests/test_rag_expected_level_review_packet.py`。
- 新增 `tests/rag_expected_level_review_packet_v0.4.17.4_report.json`。
- 新增 `docs/rag_expected_level_review_packet_v0.4.17.4.md`。
- 同步服务与 health check 版本为 `0.4.17.4`。

报告写法：
> v0.4.17.4 将 `risk_unfair_competition_confusion_001` 的固定失败分类为 `expected_level_fact_strength_review`。三轮 repeat 中该 case 的 retrieval stage 均为 `PASS`，expected evidence、关键词、风险类型、置信度和整改动作均通过，唯一失败项是 `expected_risk_level` 的 `over_risk`。报告同时记录元数据口径提醒：case 的 `legal_reasoning` 提到第6条，而 expected evidence 与实际证据链均为第7条。该结论不授权 runtime patch、anchor change 或未经人工复核的 eval case 修改。

边界：只读 saved report；不运行 full eval 或 targeted eval；不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder；不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant 数据。

验证：expected-level review packet 单测、候选包单测、依赖归因单测、索引检查、编码检查与项目 health check 通过。

### v0.4.17.5：Legal Text Version Verification Packet

阶段：RAG evidence independence / retrieval quality hardening 系列的法律文本版本核验。

解决的问题：v0.4.17.4 发现 `risk_unfair_competition_confusion_001` 的 `legal_reasoning` 提到第6条，而 expected evidence 和证据链均为第7条。本版本联网核验权威法律文本，判断这是否属于当前知识库错误、证据链错误，还是历史编号残留。

关键输出：
- 新增 `tests/legal_text_version_snapshot_v0.4.17.5.json`。
- 新增 `tools/build_legal_text_version_verification_packet.py`。
- 新增 `tests/test_legal_text_version_verification_packet.py`。
- 新增 `tests/legal_text_version_verification_packet_v0.4.17.5_report.json`。
- 新增 `docs/legal_text_version_verification_packet_v0.4.17.5.md`。
- 同步服务与 health check 版本为 `0.4.17.5`。

报告写法：
> v0.4.17.5 核验《反不正当竞争法》条文版本后确认：2025 年第二次修订后的现行法中，混淆行为条款为第七条；2019 年修正文本中，混淆行为条款为第六条。`risk_unfair_competition_confusion_001` 的 expected evidence 和三轮最终证据链均使用第七条，符合现行法；`legal_reasoning` 中的第6条属于旧编号/元数据表述漂移。该结论不授权 runtime patch、anchor change 或未经人工复核的 eval case 修改。

边界：本轮人工核验使用联网来源；入库工具与单测只读取保存快照，不联网；不运行 full eval 或 targeted eval；不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder；不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant 数据。

验证：法律文本版本核验单测、expected-level review 单测、候选包单测、依赖归因单测、索引检查、编码检查与项目 health check 通过。

### v0.4.17.6：Unfair Competition Confusion Metadata Patch

阶段：RAG evidence independence / retrieval quality hardening 系列的元数据口径清理。

解决的问题：v0.4.17.5 已确认混淆行为在现行《反不正当竞争法》中为第七条，但 `risk_unfair_competition_confusion_001` 的 `legal_reasoning` 仍保留旧编号第6条。本版本在人工确认后只修正该说明文字，避免旧编号继续污染后续复核材料。

关键输出：
- 修改 `tests/rag_eval_cases.json` 中该 case 的 `legal_reasoning`。
- 新增 `docs/unfair_competition_confusion_metadata_patch_v0.4.17.6.md`。
- 新增 `tests/rag_expected_level_review_packet_v0.4.17.6_report.json`。
- 新增 `tests/legal_text_version_verification_packet_v0.4.17.6_report.json`。
- 同步服务与 health check 版本为 `0.4.17.6`。

报告写法：
> v0.4.17.6 在不改变 expected evidence 和 expected risk level 的前提下，将 `risk_unfair_competition_confusion_001` 的 `legal_reasoning` 从旧编号第6条修正为现行法第7条。修正后 expected-level review packet 的 metadata warning 清零，legal text verification packet 分类变为 `current_law_evidence_valid`；固定失败仍属于 expected-level/fact-strength review，不授权 runtime patch、anchor change 或 prompt/rerank/risk rule 修改。

边界：只修改 eval case 的说明文字；不改变 expected evidence、expected risk level、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、hidden seed 或 Qdrant 数据；不运行 full eval。

验证：元数据修正后的 expected-level review packet 与 legal text verification packet 已重建；相关单测、索引检查、编码检查与项目 health check 通过。

### v0.4.17.7：RAG Full Eval Closeout

阶段：RAG evidence independence / retrieval quality hardening 系列的主链路收口确认。

解决的问题：v0.4.17.6 修正旧条文编号说明后，需要用当前 RAG 主链路 full eval 确认是否还有新的 retrieval、evidence-chain 或 runtime 回归，避免继续围绕已隔离 case 堆诊断。

关键输出：
- 新增 `tests/rag_eval_report_v0.4.17.7.json`。
- 新增 `docs/rag_full_eval_closeout_v0.4.17.7.md`。
- 同步服务与 health check 版本为 `0.4.17.7`。

报告写法：
> v0.4.17.7 运行当前 RAG full eval，结果为 `59/60` passed，retrieval stage 保持 `PASS=60`。唯一失败仍为 `risk_unfair_competition_confusion_001` 的 expected risk level `over_risk`：系统输出 `high`，预期为 `medium`；该 case 的 expected evidence、关键词、置信度、风险类型和整改动作均通过，证据命中现行《中华人民共和国反不正当竞争法》第七条。因此 v0.4.17.x 可以收口：剩余问题是 expected-level/fact-strength 复核项，不是新的 retrieval、evidence-chain 或 runtime 回归。

边界：运行 full RAG eval，但不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、hidden seed、Qdrant 数据、eval case、expected evidence 或 expected risk level；不把本版本写成新的 gate。

验证：full RAG eval 报告成功写出；命令因保留已知 expected-level 失败而返回 `1`，报告结论为 `59/60` 与 retrieval `PASS=60`。`py_compile`、roadmap/health 相关单测、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.18.1：Legal Corpus Integrity Baseline

阶段：法规扩容前的入库质量硬化系列启动。

解决的问题：RAG 主链路已收口后，下一阶段要支持更多法律入库。直接扩容会放大 source、version、domain、jurisdiction、chunk boundary 和 expected anchor 漂移风险，因此本版本先建立本地 corpus integrity baseline。

关键输出：
- 新增 `tools/check_legal_corpus_integrity.py`。
- 新增 `tests/test_legal_corpus_integrity.py`。
- 新增 `tests/legal_corpus_integrity_v0.4.18.1_report.json`。
- 新增 `docs/legal_corpus_integrity_baseline_v0.4.18.1.md`。
- 同步服务与 health check 版本为 `0.4.18.1`。

报告写法：
> v0.4.18.1 建立法规扩容前的 legal corpus integrity baseline。checker 只读取 `knowledge_manifest.json` 和 `src/knowledge/**/*.txt`，复用 `load_txt()` 离线生成 Document metadata，不访问 Qdrant、不调用 RAG/LLM、不修改知识库。当前结果为 `status=passed`：manifest 覆盖 15 份法规/标准，离线生成 7177 个片段，`error_count=0`，`warning_count=0`，`orphan_knowledge_file_count=0`。后续可在该基线上推进 source/version lineage、单法新增 dry-run、targeted smoke 和扩容影响评估。

边界：不访问 Qdrant，不重建 `legal_knowledge`，不运行 eval，不修改知识库文本、manifest、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval case 或 Qdrant 数据。

验证：新增 checker 单测、既有 ingestion/Qdrant integrity 相关单测、索引一致性检查、编码卫生检查、roadmap/health 单测和项目 health check 通过；checker 在现有 corpus 上运行并输出 passed 报告。

### v0.4.18.2：Product Design Brief / UI Handoff Brief

阶段：RAG 内核收口后的产品化设计交接。

解决的问题：UI 还在设计中，但设计专员需要先理解项目定位、用户、模块边界和视觉方向。本版本将项目内容整理为产品设计简报，避免后续 UI 被设计成普通聊天机器人、行情看板或营销页。

关键输出：
- 新增 `docs/product_design_brief_v0.4.18.2.md`。
- 同步服务与 health check 版本为 `0.4.18.2`。

报告写法：
> v0.4.18.2 新增产品设计简报，面向设计专员说明本项目是 Harvey 风格企业法律风控系统。简报覆盖首页风险驾驶舱、市场行情与外部风险、供应链地图与区域风险、法律风控 RAG 工作台、企业全生命周期风险概览五个模块，并明确第一阶段只需要产品骨架、核心页面和专业视觉方向，不要求真实行情接口、真实地图数据、完整权限系统或正式 UI 实现。

边界：只新增设计交接文档；不实现 UI，不新增 API，不接行情或地图数据，不调用 RAG/Qdrant/LLM，不修改 retriever、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry、eval case 或知识库数据。

验证：`py_compile`、产物索引一致性、编码卫生、roadmap/health 单测、项目 health check 和 `git diff --check` 通过。

### v0.4.18.3：Risk Data Contract / Product View Models

阶段：产品化前的数据契约建设。

解决的问题：UI 还在设计中，但前端未来需要稳定的数据骨架。若等视觉稿完成后再临时拼字段，容易造成首页、法律工作台、市场信号、供应链地图和生命周期流程图各自漂移。本版本先固化离线 product view model contract。

关键输出：
- 新增 `tests/fixtures/product_view_models_v0.4.18.3.json`。
- 新增 `tools/check_product_view_model_contract.py`。
- 新增 `tests/test_product_view_model_contract.py`。
- 新增 `tests/product_view_model_contract_v0.4.18.3_report.json`。
- 新增 `docs/product_view_model_contract_v0.4.18.3.md`。
- 同步服务与 health check 版本为 `0.4.18.3`。

报告写法：
> v0.4.18.3 定义产品级 Risk Data Contract / Product View Models。fixture 覆盖 `dashboard_summary`、`legal_workspace`、`market_signals`、`supply_chain_map` 和 `lifecycle_risk` 五个 view model，并通过 3 个 `product_risks` 统一跨模块风险引用。checker 验证必填字段、guardrails、枚举、`risk_id`、supply-chain node/edge 和 lifecycle evidence 引用关系，当前报告为 `status=passed`、`issue_count=0`。

边界：只定义离线 view model fixture 和 checker；不实现 UI，不新增正式 API，不接真实行情、地图、供应链或权限系统，不调用 RAG/Qdrant/LLM，不修改主链路、eval case 或知识库。

验证：product view model contract 单测、roadmap/health 单测、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.18.4：Product Mock Endpoint Contract

阶段：产品化前的 UI handoff 接口契约建设。

解决的问题：v0.4.18.3 已经有产品数据骨架，但设计和前端讨论仍需要知道“每个页面未来从哪个产品态端点取什么形状的数据”。本版本用离线契约提前固定 endpoint 形状，避免正式 API 还没写时字段口径各自漂移。

关键输出：
- 新增 `tools/check_product_mock_endpoint_contract.py`。
- 新增 `tests/test_product_mock_endpoint_contract.py`。
- 新增 `tests/product_mock_endpoint_contract_v0.4.18.4_report.json`。
- 新增 `docs/product_mock_endpoint_contract_v0.4.18.4.md`。
- 同步服务与 health check 版本为 `0.4.18.4`。

报告写法：
> v0.4.18.4 在 product view model contract 之上定义离线 Product Mock Endpoint Contract。契约覆盖 `/product/dashboard/summary`、`/product/legal/workspace`、`/product/market/signals`、`/product/supply-chain/map`、`/product/lifecycle/risk` 和 `/product/risks` 六个只读 mock endpoint，并从 v0.4.18.3 fixture 派生响应样例。checker 验证 endpoint method、path namespace、view model 引用、`risk_id` 引用、响应 envelope 和当前 FastAPI surface 未暴露 mock path，当前报告为 `status=passed`、`issue_count=0`。

边界：本版本不是正式 API 接入，不新增 FastAPI 路由，不启动服务，不接 UI，不调用 RAG/Qdrant/LLM，不接真实行情、地图、供应链或权限系统；mock endpoint response 只是 UI handoff 样例，不是法律结论、eval case、completed manual decision 或 ready action。

验证：product mock endpoint contract 单测、product view model contract 单测、roadmap/health 单测、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.18.5：Product API Backend Integration

阶段：产品后端接口接入与分层落地。

解决的问题：v0.4.18.4 已经定义了 `/product/*` mock endpoint contract，但还不能被前端或 UI 原型真实请求。本版本把这些 endpoint 接入 FastAPI，同时保持数据源为 fixture sample，先完成后端层级和 HTTP contract，不提前接真实行情、地图、供应链或 RAG。

关键输出：
- 新增 `src/product/contracts.py`、`src/product/schemas.py`、`src/product/service.py`、`src/product/router.py`。
- 在 `src/main.py` 中通过 `app.include_router(product_router)` 接入 6 个 `/product/*` GET 接口。
- 新增 `tools/check_product_api_contract.py`。
- 新增 `tests/test_product_api_contract.py`。
- 新增 `tests/product_api_contract_v0.4.18.5_report.json`。
- 新增 `docs/product_api_backend_integration_v0.4.18.5.md`。
- 同步服务与 health check 版本为 `0.4.18.5`。

报告写法：
> v0.4.18.5 将产品视图契约接入为真实 FastAPI 后端接口。系统新增独立 `src/product` 分层，暴露 `/product/dashboard/summary`、`/product/legal/workspace`、`/product/market/signals`、`/product/supply-chain/map`、`/product/lifecycle/risk` 和 `/product/risks` 六个只读接口。接口统一返回 `status`、`data/items` 和 `meta` envelope，`meta` 明确声明 `data_source=fixture_sample`，并标记 RAG、Qdrant、LLM、行情、地图和供应链外部数据均未调用。当前 checker 报告为 `status=passed`、`endpoint_count=6`、`openapi_passed=6`、`response_passed=6`、`issue_count=0`。

边界：本版本完成真实后端接口接线，但不是正式业务数据源接入；不调用 RAG/Qdrant/LLM，不接真实行情、地图、供应链、权限系统或外部数据源，不修改知识库、eval case、anchor、prompt、rerank 或 risk supplement。`/product/legal/workspace` 返回的是展示态样例，不是实时 RAG 问答。

验证：product API contract 单测、既有 API contract 回归、product mock/view model contract 单测、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.18.6：Product API Field Catalog

阶段：产品后端接口字段交接目录建设。

解决的问题：v0.4.18.5 已经真实暴露 fixture-backed `/product/*` 接口，但接口深层字段仍主要隐含在 fixture 中。设计、前端和后端如果没有统一字段目录，后续 UI 对接容易出现字段名、层级、空值语义和展示边界不一致。

关键输出：
- 新增 `tools/export_product_api_field_catalog.py`。
- 新增 `tests/test_product_api_field_catalog.py`。
- 新增 `tests/product_api_field_catalog_v0.4.18.6.json`。
- 新增 `docs/product_api_field_catalog_v0.4.18.6.md`。
- 同步服务与 health check 版本为 `0.4.18.6`。

报告写法：
> v0.4.18.6 为产品后端接口生成 Product API Field Catalog。字段目录覆盖 6 个 `/product/*` fixture-backed endpoint，记录 query params、response envelope、meta 字段和从 fixture 推导出的 nested response field paths。该目录使 UI 设计、前端原型和后端实现能够围绕同一份字段口径协作；当前 catalog 摘要为 `endpoint_count=6`、`query_param_count=13`、`source_version_matches=true`，且当前 fixture 字段未被截断。

边界：本版本只生成字段目录，不启动服务，不调用 RAG/Qdrant/LLM，不接真实行情、地图、供应链、权限系统或外部数据源，不修改知识库、eval case、anchor、prompt、rerank 或 risk supplement。

验证：product API field catalog 单测、product API/mock/view model contract 单测、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.18.7：Product API Status / Error Catalog

阶段：产品后端接口状态与错误契约建设。

解决的问题：v0.4.18.5-v0.4.18.6 已经有真实 fixture-backed 接口和字段目录，但前端还需要知道哪些情况是正常空态，哪些是系统错误，以及未来真实数据源降级时应如何展示。本版本补齐产品接口的成功态、空结果语义和错误码目录。

关键输出：
- 新增 `src/product/status.py`。
- 新增 `tools/export_product_api_status_catalog.py`。
- 新增 `tests/test_product_api_status_catalog.py`。
- 新增 `tests/product_api_status_catalog_v0.4.18.7.json`。
- 新增 `docs/product_api_status_catalog_v0.4.18.7.md`。
- 同步服务与 health check 版本为 `0.4.18.7`。

报告写法：
> v0.4.18.7 为产品后端接口补齐 Product API Status / Error Catalog。目录明确 `ok` 与 `empty_items` 两类成功/空态语义，并定义 `PRODUCT_VIEW_MODEL_UNAVAILABLE`、`PRODUCT_VIEW_MODEL_INVALID_JSON`、`PRODUCT_VIEW_MODEL_VERSION_MISMATCH`、`PRODUCT_VIEW_MODEL_MISSING` 等 fixture runtime 错误码，以及未来真实数据源接入时可使用的 degraded/unavailable reserved code。`/product/risks` 过滤无结果继续返回 HTTP 200 和 `items=[]`，前端应展示空态而非系统错误。

边界：本版本只定义状态和错误契约，不接真实数据源，不启动服务，不调用 RAG/Qdrant/LLM，不运行 eval，不修改知识库、eval case、anchor、prompt、rerank 或 risk supplement。

验证：product API status catalog 单测、product API/field catalog 单测、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.18.8：Product Data Source Boundary

阶段：产品后端数据源替换边界建设。

解决的问题：v0.4.18.5-v0.4.18.7 已经形成 fixture-backed `/product/*` 接口、字段目录和状态目录，但数据读取逻辑仍需要一个清晰边界，避免未来接 RAG 摘要、行情、地图、供应链或权限上下文时直接改 router 或把真实客户端混进 service。

关键输出：
- 新增 `src/product/repository.py`。
- 修改 `src/product/service.py`，使 `ProductViewModelService` 依赖 `ProductViewRepository`。
- 新增 `tools/export_product_data_source_boundary.py`。
- 新增 `tests/test_product_data_source_boundary.py`。
- 新增 `tests/product_data_source_boundary_v0.4.18.8.json`。
- 新增 `docs/product_data_source_boundary_v0.4.18.8.md`。
- 同步服务与 health check 版本为 `0.4.18.8`。

报告写法：
> v0.4.18.8 为产品后端补齐 Product Data Source Boundary。当前 `/product/*` 接口仍只连接 `fixture_sample`，默认 repository 为 `FixtureProductViewRepository`；router 依赖 `ProductViewModelService`，service 依赖 `ProductViewRepository.load_payload()`。未来 `legal_rag_summary_provider`、`market_signal_provider`、`supply_chain_provider`、`lifecycle_risk_provider` 和 `permission_context_provider` 只是预留槽位，尚未接入真实数据源。当前 boundary catalog 显示 `real_data_source_connected=false`，RAG、Qdrant、LLM、行情、地图和供应链访问均为 `not_called`。

边界：本版本只定义数据源替换边界；不接真实数据源，不调用 RAG/Qdrant/LLM，不访问真实行情、地图或供应链数据，不运行 eval，不修改知识库、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry 或 eval case。

验证：Product data source boundary 单测、product API/field/status catalog 回归、边界目录导出、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.18.9：Product Backend Closeout

阶段：产品后端设计收口与前端/真实 provider 交接。

解决的问题：v0.4.18.3-v0.4.18.8 已经分别形成 product view model、mock endpoint contract、真实 fixture-backed API、字段目录、状态目录和数据源边界，但还需要一个简短 runbook 说明当前到底能用什么、不能用什么、前端如何对接、未来真实 provider 如何逐项接入。

关键输出：
- 新增 `tools/build_product_backend_closeout.py`。
- 新增 `tests/test_product_backend_closeout.py`。
- 新增 `tests/product_backend_closeout_v0.4.18.9_report.json`。
- 新增 `docs/product_backend_closeout_v0.4.18.9.md`。
- 同步服务与 health check 版本为 `0.4.18.9`。

报告写法：
> v0.4.18.9 收口 product backend 设计。当前 6 个 fixture-backed `/product/*` FastAPI route 已可供 UI 原型对接，字段目录、状态/错误目录和 repository boundary 已齐备；closeout report 显示 `status=passed`、`backend_design_status=basically_complete`、`endpoint_count=6`、`openapi_passed=6`、`response_passed=6`、`currently_connected_provider_count=1`。后续若接真实数据源，应一次只接一个 provider，并通过 targeted smoke 与降级状态测试后再让 UI opt-in 使用非 fixture 数据。

边界：本版本是 closeout/runbook，不接真实数据源，不启动服务，不运行 eval，不调用 RAG/Qdrant/LLM，不访问真实行情、地图或供应链数据，不修改知识库、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry 或 eval case。

验证：product backend closeout 单测、product API/field/status/data source boundary 回归、closeout 报告导出、索引一致性检查、编码卫生检查、项目 health check 和 `git diff --check` 通过。

### v0.4.19.0：External Risk / Taskflow Bridge

阶段：从产品后端静态样例走向外部风险信号和法律检索任务协作的桥接阶段。

解决的问题：产品层已具备可供 UI 对接的 fixture-backed 接口，但企业风险系统还需要把外部行情、政策与地缘政治等事实信号，稳定地转为后续法律分析任务，同时保持真实 provider 未启用时的可用性与边界清晰。

关键输出：
- 新增 `/external-risk/*` 后端分层、fixture-safe 外部风险上下文及 provider 降级状态。
- 建立外部事实到法律检索任务计划的桥接，并将 RAG 中回答生成、复杂案例、证据链、查询规划、过滤、重排和风险补充拆分为独立模块。
- 建立复杂案例和开放式法律问题的回答策略，保留本地 fallback 与结构化调试信息。

报告写法：
> v0.4.19.0 完成外部风险与任务流桥接的基础分层。系统可以在不依赖实时 provider 的情况下，以 fixture-safe 外部风险上下文生成可追溯的法律检索任务；真实行情、消息和数据源仍需显式启用，并保留降级状态。该版本同时完成 RAG 模块拆分和复杂问题回答契约，为后续把外部风险、企业行为和法律依据汇总到同一报告链路提供了后端边界。

边界：本版本不是实时数据生产接入，不把外部事实当作法律依据；不修改知识库、eval case、场景配置或 Qdrant 数据。前端原型与生成运行产物不与该后端桥接版本混合表述。

验证：外部风险 API、回答策略、复杂案例、API contract、retriever contract 和风险引擎回归，语法检查与 `git diff --check` 通过。

### v0.5.0：RAG Quality Runtime and Evaluation Baseline

阶段：从“RAG 已可运行”进入“RAG 的证据质量、材料边界与改进效果能够被单独验证”的工程基线阶段。

解决的问题：法律 RAG 在概念题、法规附表和合同材料审查中，容易把不同性质的信息混为同一类证据，也难以区分“检索是否召回了正确法源”和“最终语言是否流畅”。因此需要同时强化证据结构，并提供不会污染生产默认行为的可重复对照实验。

关键输出：
- 将法律概念映射以声明式配置接入路由、查询扩展和直接法源召回；概念缺少主条文证据时给出明确缺口，而非用相邻材料替代。
- 法律入库解析能够把紧凑相邻条文和附表独立成可引用 evidence block，避免附表被错误并入末条正文。
- 回答输出区分用户上传材料和法律法源：上传材料仅说明事实背景，不能作为法律依据或指令来源；同时增加相邻引用覆盖率信号与人工复核提示。
- 新增四档仅检索消融（M1_dense、M2_hybrid、M3_concept、M4_full），以 Evidence Recall@K、MRR、nDCG、多来源覆盖和延迟观察每一层检索能力的实际贡献。

报告写法：
> v0.5.0 将法律 RAG 的改进目标从“给出看起来合理的回答”进一步收紧为“能说明使用了什么证据、缺少什么证据、不同检索组件实际带来多少证据收益”。系统对法律概念、条文附表、用户上传材料和法律法源建立了更清晰的边界；同时建立四档仅检索对照实验，使后续优化可以用同一问题集、同一知识库和同一指标验证，而不再依赖单个案例的主观感受。

边界：法律概念映射使用现有声明式配置，不为某个 hidden case 追加场景规则；不修改 `scenario_registry`、eval case、hidden seed、风险 taxonomy 或 risk supplement，也不写入 Qdrant。消融报告是可再生运行产物，只有在固定环境重新执行并通过校验后，才能作为具体效果数字写入正式报告。

验证：RAG 源码与消融工具语法检查通过；新增 20 项单测与附表、引用、回答策略、复杂案例及 retriever contract 共 73 项直接回归测试通过；`git diff --check` 通过。完整消融和 full RAG eval 需要在固定 Qdrant/模型环境中另行运行，不在本版本伪造结果。

### v0.5.1：Evidence Sufficiency、受控联网与 Skill 编排

阶段：从“检索到什么”进一步进入“证据是否足以支撑下一步，以及何时该补证或人工复核”。

解决的问题：法律 RAG 即使能召回材料，也需要区分本地法源、网页事实、用户材料和证据缺口；同时，用户需要能组合受控分析步骤，但不能因此获得直接执行模型、向量库或外部脚本的权限。

关键输出：
- 引入 ESG，对本地法律证据、来源层级和问题性质进行结构化评分与路由；网页证据始终保持为外部事实补充。
- 提供默认关闭的受控联网补证：法律和监管问题优先官方域名，结果带 URL、采集时间和可信等级，不自动写入 Qdrant。
- 提供固定节点、无环、参数受限的 Skill 编排与运行接口；自建 Skill 只经既有问答服务边界运行，内置模板不可修改。
- 固化 60 题冻结集上的检索消融、指标离线重算、ESG 裁判及图表质量核验材料。

报告写法：
> v0.5.1 建立了“本地法律证据优先、网页事实受控补充、证据不足可升级人工复核”的闭环。系统不仅展示检索结果，还会显示证据充分性与来源边界；用户可通过固定节点编排复用审查流程，但底层模型、向量库、密钥与外网访问仍由服务端统一控制。内部冻结集上的 M4 检索与 ESG 指标用于证明工程检索和路由能力，而不被表述为法律意见正确率。

边界：网页结果不替代法条、不自动入库；ESG 不是法律结论置信概率；自建 Skill 配置与业务运行数据不纳入源码基线。本版本不将新增 anchor 配置并入提交，避免以评测结果反向修补样本。

验证：完整 Python 回归、消融裁判、ESG 裁判、图表质量核验、索引一致性检查、项目 health check 和 `git diff --check` 均应作为版本交付记录；单机时延只作为当前环境观测，不外推为生产 SLA。

### v0.5.2：受控消融、鲁棒性与多协议运行时

阶段：将 RAG 的工程提升拆分为可逐层观察的实验变量，并扩展面向企业风险工作的模型协议和市场/供应链信号适配能力。

解决的问题：仅比较“基础检索”和“完整管线”无法识别每一层模块的真实贡献；同时，企业部署需要在不改变证据边界的前提下兼容不同模型服务，并从商品期货等公开市场信息中提取可复核的供应链风险线索。

关键输出：
- C0-C6 受控消融逐步启用 Dense、BM25、查询扩展、概念锚点、既有场景锚点、复杂规划和 Cross-Encoder，并以冻结集、collection snapshot 与裁判报告固化实验条件。
- 24 题人工成对改写集检验口语化、术语替换和多问题重组下的检索稳定性；6 题端到端抽样检查证据、风险字段、建议动作和引用链的工程闭环。
- 新增 Anthropic、Gemini 和 OpenAI-compatible 的运行时协议边界；新增受限的商品/期货情报解析及供应链相关性过滤。
- 外部风险情报 provider 按运行时配置指纹刷新，关闭实时源后保持 fail-closed，不复用先前配置下的缓存结果。

报告写法：
> v0.5.2 不再把完整管线的提升笼统归因于“模型更强”，而是通过 C0-C6 逐层控制实验显示：在当前冻结集上，既有场景规则贡献了主要检索增益，Cross-Encoder 进一步改善排序并增加延迟。系统同时以改写集观察措辞变化下的稳定性，以多协议运行时和期货供应链信号扩展企业部署边界。所有指标仍被严格限定为内部检索、路由和工程断言，不被表述为法律意见正确率。

边界：为比赛演示，本版本固化新增 anchor、本地业务状态图、manifest 状态和论文图件，以便复放展示；它们不构成对模型能力、真实企业事实或法源生效状态的独立证明。期货与网页信息是可追溯风险线索，不构成交易建议、事实终局认定或法律依据；真实法律判断仍由有效法源和人工复核决定。

验证：C0-C6 控制变量裁判、ESG 裁判、改写鲁棒性汇总、端到端抽样和图表质量核验均通过；版本提交前需以完整单元测试、health check 和 `git diff --check` 收口。

### v0.5.3：证据优先主链路、材料接入与风险任务流

阶段：将 RAG 的证据门禁和路由能力接入企业风控工作台，并补齐用户材料、内部风险和外部风险之间的后端协作边界。

解决的问题：企业风险工作台需要同时处理普通对话、近期外部事实观察、法律问题和用户上传材料。如果所有问题都直接进入同一条回答路径，系统容易把无依据的通用回答当成法律意见，也容易把用户材料、网页事实和法律法源混成同一种证据。因此本版本把路由、材料来源、引用覆盖和风险决策门禁显式化，并让内部/外部风险任务可以被审计和复核。

关键输出：
- 支持 PDF、Word、PowerPoint、Excel、图片、TXT、Markdown 和 CSV 材料接入；文本本地提取，MineU 解析结果默认不入库。
- 图片只通过有界视觉调用提取可见事实，不进入法律依据、证据链或法条引用；视觉调用失败不阻断普通材料流程。
- `/ask` 增加 `general_chat`、`recent_risk_observation`、`legal_rag` 和受控联网法律路由；风险/合规决策和上传材料不会静默降级为无证据通用回答。
- 增加引用完整性、引文覆盖和申报风险领域匹配的独立门禁，并以 `retrieval_status` 告知本次是否实际执行 RAG、是否为本地兜底或外部观察。
- 内部风控形成业务状态、模板版本、基线双人确认、异步评估任务、证据关联和追加式审计；外部风险形成供应链关系证据等级、绑定同步、静态信号时效过滤和并发合并。
- 前端支持材料上传/拖放/粘贴、后端地址故障回退和工作地址持久化；自定义远程地址仍保持显式配置边界。

报告写法：
> v0.5.3 将法律 RAG 从单一问答入口推进为证据优先的企业风控主链路。系统先区分普通对话、外部事实观察和法律风险决策，再根据问题与材料来源选择对应路径；对法律风险输出独立执行引用完整性、引文覆盖和风险领域匹配校验，证据不足时不输出风险等级或整改建议。与此同时，用户上传材料、内部业务状态、外部风险信号和供应链关系均带有来源、状态或审计边界，便于前后端联调与人工复核。

边界：本版本增强的是运行时路由、证据治理和产品协作能力，不等于法律结论正确率提升；不修改知识库原文、hidden seed、anchor、prompt、rerank、risk supplement 或评测案例，不重建 Qdrant，不把网页/期货信息当作法律依据。图片视觉结果、外部风险信号和本地 fallback 只能作为事实观察或辅助材料，最终法律判断仍需可追溯法源与人工复核。

验证：完整 Python 回归测试 `1670` 项通过；项目 health check `583/583` 通过；编码卫生报告为 `passed` 且 `error_count=0`。本版本未运行 full eval，不能据此宣称 Recall、法律意见准确率或生产 SLA 改善。

### v0.5.4：RAG Anchor 行为候选快照

阶段：将一组需要独立评估的敏感个人信息与个人信息出境证据选择行为从 `v0.5.3` 主链路提交中分离，形成可回退、可对比的 RAG 快照。

解决的问题：用户可能用“精确轨迹、行驶轨迹、精准定位”等业务词描述敏感个人信息，也可能用“向境外传输个人信息”等非固定短语询问出境条件。当前候选改动尝试把这些通用表述映射到既有法源的连续条文证据窗口，但它会改变 Anchor 触发和最终证据选择，因此必须单独验证，不能直接视为质量提升。

关键输出：
- 在 `src/rag/retriever.py` 增加可读的敏感个人信息信号识别。
- 将个人信息出境条件的候选证据窗口扩展为第 38 至 40 条；敏感信息场景同时保留第 28 条，并保留标准合同措施条款的关联证据。
- 新增 `tests/test_retriever_contract.py` 的通用触发词测试，验证敏感表述与普通功耗统计表述的区分。

报告写法：
> v0.5.4 将一组 RAG Anchor 行为改动独立固化为可回退快照：系统尝试识别业务表述中的敏感个人信息信号，并在个人信息出境条件问题中保留连续的路径、同意、门槛/本地化条文证据。该版本只证明代码和通用契约可运行，不证明这些规则已经改善法律检索质量；后续必须以 targeted regression、full eval 和误触发复核决定是否采用。

边界：本版本不修改 prompt、rerank、risk supplement、hidden seed、评测案例或知识库原文，不重建 Qdrant。它是 RAG 候选行为快照，不是生产默认基线，也不是针对某个 hidden case 的修补结论。

验证：`tests/` 回归 `1671` 项通过，`py_compile`、health check `583/583`、编码卫生和 `git diff --check` 通过；未运行 full eval，不能据此宣称 Recall、法律意见准确率或生产 SLA 改善。
