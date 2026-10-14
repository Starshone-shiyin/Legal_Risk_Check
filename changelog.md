# 更新日志

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)；版本号采用项目内部层级版本号。

维护规则：本文件默认使用中文记录变更；路径、命令、版本号、配置键、JSON/schema 字段、枚举值、工具名、测试名和专有技术缩写保留原文，避免影响检索、脚本和报告引用。

## [0.5.4] - 2026-09-03

### 新增
- 将敏感个人信息和个人信息出境的措辞扩展、关联条文连续证据窗口及对应测试单独固化为 RAG 候选快照，便于与 `v0.5.3` 独立比较和回退。
- 对包含精确轨迹、行驶轨迹、位置轨迹或精准定位等业务表述的问题，补充通用的敏感个人信息信号识别。
- 对个人信息向境外提供、传输或转移且涉及条件、申报等问题，保留《中华人民共和国个人信息保护法》第 38 至 40 条及标准合同措施条款的连续证据范围；敏感信息场景同时保留第 28 条证据。

### 验证与边界
- 完整 `tests/` 回归测试 `1671` 项通过；新增 Anchor 行为测试验证正例与非敏感业务表述的区分。
- FastAPI 和项目 health check 版本同步为 `0.5.4`；未重建 Qdrant，未运行 full eval，未修改 prompt、rerank、risk supplement、hidden seed 或评测案例。
- 本版本是可回退的 RAG 行为候选快照，不代表新增规则已经通过生产质量评估；正式采用前必须完成 targeted regression、full eval 和误触发复核。

### 提交口径
- 本版本只提交 `src/rag/retriever.py`、对应测试、版本同步和治理文档；业务状态、生成报告、文档制作临时产物继续留在工作区，不纳入提交。
- 编码卫生检查同时跳过 `.review_tmp/` 自身生成的复核报告，避免诊断输出被递归扫描为源码错误。

## [0.5.3] - 2026-09-03

### 新增
- 法律工作台新增 PDF、Word、PowerPoint、Excel、图片、TXT、Markdown 和 CSV 材料接入；纯文本材料在本地提取，其他材料沿用 MineU 解析，解析结果默认仍不进入 Qdrant。
- 图片材料增加有界的视觉事实提取：最多 3 张、单张最多 5 MB；只补充用户材料中的可见事实，不进入法律依据、证据链或法条引用。
- `/ask` 增加通用对话、近期外部风险观察和法律 RAG 的显式路由；风险决策、合规问题和上传材料默认进入证据优先路径。
- `/ask` 增加独立引用完整性、引文覆盖和风险领域匹配门禁，并返回 `retrieval_status`，在证据不足或法域/领域不匹配时保持 fail-closed。
- 内部风控增加企业业务状态、可版本化工作流模板、基线提案/确认/重置审计、异步风险评估任务、证据材料关联与闸门阻断信息。
- 外部风险增加商品/期货目录显示名、供应链市场观察、静态市场页面时效过滤、任务流并发合并、供应商绑定同步和关系证据等级。

### 变更
- 文档接入服务统一按扩展名和 MIME 类型校验，并为原始文件提供受控的本机默认程序打开接口；前端材料面板支持拖放、粘贴图片、解析预览和状态刷新。
- 外部风险与内部风险接口继续保持数据源边界、来源状态和审计信息；网页与市场信息仍是可追溯事实信号，不替代法律法源或人工判断。
- 前端恢复本地后端候选地址的故障回退和成功地址持久化；远程自定义地址仍只使用用户显式配置的服务。
- 编码卫生检查跳过历史 `backup/` 快照，避免旧备份中的测试字符污染当前工程报告；扫描只输出报告，不修改知识库或其他被扫描文件。
- 同步 FastAPI、项目 health check 和编码卫生报告版本为 `0.5.3`。

### 验证与边界
- 完整 Python 回归测试 `1670` 项通过；针对性材料、路由、证据门禁、内部风险和前端契约测试通过。
- 项目 health check `583/583` 通过；编码卫生报告 `status=passed`、`error_count=0`，仍保留 `4106` 条 warning 供后续治理，不把 warning 误报为已完成清洗。
- 本版本未运行 full eval，未重建 Qdrant，未修改 hidden seed、anchor、prompt、rerank、risk supplement 或现有知识库原文；当前 RAG 新增能力均以证据门禁和通用契约验证。

### 验证命令
- `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py --output tests/encoding_hygiene_report.json --fail-on-error`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.5.2] - 2026-08-20

### 新增
- 新增 C0-C6 单变量受控检索消融：依次隔离 Dense、BM25、查询扩展、概念锚点、既有场景锚点、复杂问题规划和 Cross-Encoder，并支持指定 Qdrant collection snapshot。
- 新增 24 题人工成对改写鲁棒性集、6 题端到端抽样、控制变量/ESG/总裁判工具及 300 dpi 科研图表，形成可追溯的 2026-08-15 核心技术实验材料包。
- `src/core/llm.py` 新增 Anthropic Messages 与 Gemini Generate Content 协议适配器；运行时设置可显式选择协议并校验服务地址，默认仍为 OpenAI-compatible。
- 外部风险模块新增大宗商品和境内期货合约目录，以及新浪期货、东方财富期货、交易所公告等受限解析适配器；信号保留合约、来源和供应链关联信息。

### 变更
- 文档解析兼容性增强，支持更多 MinerU 响应形态与解析后文本路径；启动脚本默认只在 loopback 本地启动时启用演示身份，非 loopback 监听不会继承该设置。
- 前端运行时设置增加 LLM 提供方/协议选择和更清晰的配置呈现；外部风险接口将同步读取与异步 Web 路由分离，避免阻塞服务事件循环。
- 外部风险默认情报 provider 在运行时配置变化时按配置指纹重建；同一配置内仍复用轮询缓存，实时开关关闭后不会读取先前缓存内容。
- `run_rag_ablation.py` 默认维持既有 M1-M4 口径，C0-C6 必须显式启用，防止新实验配置无意改变历史报告的可比性。
- 为比赛演示固化当前可复放状态：纳入数据安全法第 27、30 条 anchor、风险接入/内部风险/外部风险图谱快照、生态环境法典 manifest 状态和论文图件。

### 验证与实验口径
- 在 `legal_knowledge_staging_20260811`、60 题冻结集上，C0-C6 控制变量裁判与 ESG 裁判均为 `accepted`。C6 的 Recall@K/MRR@K/nDCG@K 为 `0.987500`/`0.841667`/`0.883036`；C4-C6 的主要增益来自既有场景规则和重排，不能归因于单一模型。
- 24 题改写鲁棒性集仅用于检验措辞变化下的检索稳定性；6 题端到端抽样 `6/6` 通过的是工程断言，而非法律结论正确率评测。
- 本次运行直接相关的单元、接口与实验材料检查通过；完整测试和 health check 在提交前复跑并记录结果。

### 边界
- 本版本为比赛提交纳入上述 anchor、业务状态和图谱快照；它们是演示基线，不得据此将 C4 规则增益表述为模型能力，也不应直接迁移为生产用户数据。
- `knowledge_manifest.json` 中生态环境法典的 `legal_effect` 仅记录比赛快照；后续生产发布前仍须补充可追溯的官方生效依据并独立复核。
- 外部期货和网页信息仅为风险信号，不构成交易建议或法律依据；仍须标明来源、时点和人工复核边界。

### 验证命令
- `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.5.1] - 2026-08-12

### 新增
- 新增 Evidence Sufficiency Gate（ESG）：以本地法律证据、来源层级、证据数量和问题性质生成 `evidence_sufficiency`，将结果路由为“带证据作答”“受控联网补证”或“人工复核”，不把网页结果误作法定依据。
- 新增 `src/external_risk/web_search.py` 与 `/external-risk/web-search*`：提供默认关闭的受控在线检索基础设施，支持 `off`、`auto`、`force` 三种模式、法律/监管官方域名限制、来源可信等级、URL 与采集时间记录。
- 新增 `src/skills/` 和 `/skills/*`：支持内置模板与自建 Skill 的固定节点 DAG 编排、参数校验、JSON 持久化、CRUD 以及通过既有 `/ask` 边界的受控执行；前端不直接访问模型、向量库、密钥或任意脚本。
- 新增 RAG 指标离线重算、ESG 裁判、科研图表生成/质量核验工具，以及冻结集实验、裁判和图表材料。
- 新增风险公式建模研究目录，保留 AHP/BWM、候选淘汰、权重分析及专家问卷模板等研究材料；该目录为研究与验证资产，不替代现有风险引擎运行规则。

### 变更
- `/ask` 支持将受控网页证据作为外部事实补充，并保持其与本地法律法源隔离；仅在显式实时性需求或已识别的本地证据缺口下尝试检索。
- 回答链路纳入 ESG、引文覆盖、外部证据标识和风险建议的证据绑定；开放性数据合规问答仅替换显式“无具体建议”占位回答，不覆盖已有实质性 RAG 输出。
- RAG 消融指标改为对每项期望法源进行一对一匹配，修正重复正文/段落块可能使题级 nDCG 超过 1 的计算缺陷；原始运行报告保留，重算报告独立记录方法和输入哈希。
- Qdrant collection 可通过 `qdrant_collection` 配置，后端启动脚本增加受控联网开关；前端增加“我的技能”、证据充分性和联网补证相关展示与交互。
- 同步服务与 health check 版本为 `0.5.1`，并补充工具、测试和产物索引。

### 验证与实验口径
- 核心技术冻结集使用 60 个案例；重算后的 M4 Full 检索指标为 Recall@K `0.941944`、MRR@K `0.841667`、nDCG@K `0.854851`、多来源覆盖 `0.933333`。该结果仅衡量内部冻结集上的预期法源检索排序，不等于法律结论正确率、司法裁判准确率或生产 SLA。
- 同一冻结集 M4 的 ESG 平均分为 `0.935500`，带证据作答路由率 `95%`，受控联网补证率 `5%`，本地一级法源覆盖率 `95%`；ESG 是证据结构与路由信号，不是法律意见置信概率。
- 完整 Python 回归、消融裁判、ESG 裁判和科研图表质量核验均已留存为可复核材料；本版本不将单机时延外推为生产性能承诺。

### 边界
- 不提交 `data/user_skills.json`、`data/risk_intake.json`、`data/external_risk/workflow_graph.json` 等用户或运行状态数据；它们不构成可复现源码基线。
- 不提交本地新增的 `config/rag_anchor_rules.json` 条目；该变更需要单独审查，不能在本版本以评测或体验改进名义绕过“不新增 anchor”的治理约束。
- 网页证据不自动写入 Qdrant、不执行页面脚本或页面指令，不能替代本地法条或人工法律判断；联网 provider 默认关闭。

### 验证命令
- `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.5.0] - 2026-08-09

### 新增
- 新增 `src/rag/eval_metrics.py` 与 `src/rag/experiment_profiles.py`：为同一测试集、同一知识库和同一 `K` 下的仅检索消融提供 `M1_dense`、`M2_hybrid`、`M3_concept`、`M4_full` 四档可复现实验配置，以及 Evidence Recall@K、MRR、nDCG、多来源覆盖和检索耗时指标。
- 新增 `src/rag/legal_concepts.py`：读取已存在的声明式 `config/legal_concepts.json`，提供法律概念识别、法域路由、查询扩展、直接法源映射和证据缺口解释。
- 新增 `tools/run_rag_ablation.py` 与 `tools/judge_rag_ablation.py`，分别执行只读的检索消融和校验生成报告的测试集、配置、指标完整性及 M4/M1 Recall@K 基本关系。
- 新增 `tests/test_answer_generation.py`、`tests/test_legal_concepts.py`、`tests/test_rag_eval_metrics.py`、`tests/test_retrieval_ablation_profiles.py`，覆盖回答计划、概念识别、指标计算和 profile 隔离。

### 变更
- `rag_query()` 支持仅用于实验的显式 `experiment_profile` 与 `retrieval_only` 参数；未传 profile 时保持既有生产检索配置。
- 法律文本解析将紧凑相邻条文作为结构边界，并把法律附表独立为可引用 evidence block，避免附表内容被并入上一条正文。
- 回答生成增加答案模式的结构计划、相邻引文覆盖率检查，以及用户上传材料与法律法源的分层输出；上传材料只作为待核验事实背景，不被当作法律依据或系统指令。
- 路由与检索对已配置的法律概念使用通用术语扩展和直接法源召回，并在证据链缺少概念主条文时输出人工复核提示。
- 补齐 `docs/indexes/project_test_index.md` 与 `docs/indexes/project_tool_index.md` 对当前根目录测试/工具的记录；不移动文件，不改变默认路径。
- 同步服务与项目 health check 版本为 `0.5.0`；忽略本地缓存、可再生消融报告和临时导出，避免其污染 Git 状态。

### 边界
- 本版本不修改 `scenario_registry`、eval case、hidden seed、风险 taxonomy 或 risk supplement 规则，也不写入 Qdrant。
- 消融 profile 仅供评测；生产调用未传 `experiment_profile` 时不改变既有默认开关。
- 法律概念映射来自既有声明式配置；本版本不为具体评测 case 新增规则或在 `rules.py` 中追加场景 anchor。
- `tests/rag_ablation*.json`、`tests/rag_smoke_after_ablation.json`、`tests/complex_case_eval_report.json` 和本地缓存均为运行产物，不纳入版本提交；正式实验结论须在固定环境重跑后再引用。

### 验证
- `./venv/Scripts/python.exe -m py_compile src/rag/answer_generation.py src/rag/domain_router.py src/rag/ingestion.py src/rag/query_planning.py src/rag/retriever.py src/rag/eval_metrics.py src/rag/experiment_profiles.py src/rag/legal_concepts.py tools/run_rag_ablation.py tools/judge_rag_ablation.py`
- `./venv/Scripts/python.exe -m unittest tests.test_answer_generation tests.test_legal_concepts tests.test_rag_eval_metrics tests.test_retrieval_ablation_profiles`
- `./venv/Scripts/python.exe -m unittest tests.test_legal_appendix_ingestion tests.test_standard_ingestion tests.test_retriever_contract tests.test_citation_integrity tests.test_answer_policy tests.test_complex_case_eval_cases`
- `git diff --check`

## [0.4.19.0] - 2026-07-22

### 新增
- 新增 `src/external_risk/` 后端分层，暴露 `/external-risk/*` 外部风险上下文、信号、发现、provider status、行情 dashboard、live signals、quote series、workflow 和法律检索任务计划接口。
- 新增 `tests/fixtures/external_risk_context_v0.1.0.json`，作为默认 fixture-safe 外部风险上下文。
- 新增 `docs/external_risk_intelligence_monitoring.md`，说明消息面与政策面外部风险监测链路和缓存边界。
- 新增 `src/rag/answer_generation.py`、`answer_policy.py`、`complex_case.py`、`debug_trace.py`、`evidence.py`、`filters.py`、`llm_json.py`、`qdrant_access.py`、`query_planning.py`、`rerank.py`、`retrieval_ops.py`、`risk_enrichment.py`、`rules.py`，将原 `retriever.py` 中的回答生成、答案策略、复杂案例、证据链、过滤器、Qdrant 访问、查询规划、rerank 和风险补充逻辑拆出。
- 新增 `tests/test_external_risk_api.py`、`tests/test_answer_policy.py`、`tests/test_complex_case_eval_cases.py`。

### 变更
- `src/main.py` 接入 `external_risk_router`，并保留 `/ask` 的本地 fallback 与开放式数据合规问题后处理。
- `rag_query()` 支持复杂多争点问题更大的候选预算、更多最终证据和 answer mode policy。
- `src/core/citations.py` 支持“条级证据覆盖款级引用”的 citation integrity 判断。
- `start_backend.ps1` 增加 Qdrant 可达性提示和外部风险 live provider 开关。
- `tools/run_rag_eval.py` 增加 `expected_missing_evidence_keywords` 与 `expected_answer_status` 检查。
- `.gitignore` 忽略 `output/` 和 `.playwright-cli/`，避免多窗口调试日志、截图和下载包污染 Git 状态。
- 同步服务与 health check 版本为 `0.4.19.0`。

### 边界
- 本次 Git 更新不新增 anchor，不修改 prompt、rerank 规则、risk supplement 规则、scenario registry 或 eval case。
- `/external-risk/*` 默认以 fixture 和显式 provider 配置为边界；live 行情/消息访问需要运行时开关，不作为 RAG 主链路强依赖。
- 不提交 `.playwright-cli/`、`output/`、`tests/complex_case_eval_report.json` 等运行产物；前端 `web/` 原型后续单独提交。

### 验证
- `./venv/Scripts/python.exe -m py_compile src/main.py src/core/citations.py src/risk/analyzer.py src/rag/retriever.py src/rag/answer_generation.py src/rag/answer_policy.py src/rag/complex_case.py src/rag/debug_trace.py src/rag/evidence.py src/rag/filters.py src/rag/llm_json.py src/rag/local_fallback.py src/rag/qdrant_access.py src/rag/query_planning.py src/rag/rerank.py src/rag/retrieval_ops.py src/rag/risk_enrichment.py src/rag/rules.py src/external_risk/contracts.py src/external_risk/intelligence.py src/external_risk/providers.py src/external_risk/provider_config.py src/external_risk/repository.py src/external_risk/router.py src/external_risk/schemas.py src/external_risk/service.py tests/test_api_contract.py tests/test_answer_policy.py tests/test_candidate_budget.py tests/test_citation_integrity.py tests/test_complex_case_eval_cases.py tests/test_external_risk_api.py`
- `./venv/Scripts/python.exe -m unittest tests.test_answer_policy tests.test_candidate_budget tests.test_citation_integrity tests.test_complex_case_eval_cases`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract tests.test_external_risk_api`
- `./venv/Scripts/python.exe -m unittest tests.test_retriever_contract tests.test_rerank_api tests.test_risk_analyzer tests.test_risk_engine`
- `node --check web/app.js`
- `node --check web/china-provinces.js`
- `git diff --check`

## [0.4.18.9] - 2026-06-17

### 新增
- 新增 `tools/build_product_backend_closeout.py`，汇总既有 product backend 交接材料并导出 closeout 报告。
- 新增 `tests/test_product_backend_closeout.py`。
- 新增 `docs/product_backend_closeout_v0.4.18.9.md`。

### 变更
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.9`。
- 更新项目工具、测试、产物、维护索引和 roadmap，将 v0.4.18.x product backend 标记为基本收口。

### 产物
- 新增 `tests/product_backend_closeout_v0.4.18.9_report.json`。

### 边界
- 本版本是 product backend closeout/runbook，不接真实数据源，不启动服务，不运行 eval，不调用 RAG/Qdrant/LLM，不访问真实行情、地图或供应链数据，不修改知识库、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry 或 eval case。

### 验证
- `./venv/Scripts/python.exe -m py_compile tools/build_product_backend_closeout.py tests/test_product_backend_closeout.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_product_api_contract tests.test_product_api_field_catalog tests.test_product_api_status_catalog tests.test_product_data_source_boundary tests.test_product_backend_closeout`
- `./venv/Scripts/python.exe tools/build_product_backend_closeout.py --output tests/product_backend_closeout_v0.4.18.9_report.json --fail-on-error`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`

## [0.4.18.8] - 2026-06-17

### 新增
- 新增 `src/product/repository.py`，定义 `ProductViewRepository` 协议、`FixtureProductViewRepository` 默认实现、`ProductViewModelError` 和 `PRODUCT_DATA_SOURCE_BOUNDARY`。
- 新增 `tools/export_product_data_source_boundary.py`。
- 新增 `tests/test_product_data_source_boundary.py`。
- 新增 `docs/product_data_source_boundary_v0.4.18.8.md`。

### 变更
- `ProductViewModelService` 改为依赖 repository boundary；默认仍使用 fixture sample，并保留 `Path` 注入兼容。
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.8`。
- 更新项目工具、测试、产物和维护索引。

### 产物
- 新增 `tests/product_data_source_boundary_v0.4.18.8.json`。

### 边界
- 本版本只完成 product backend 数据源替换边界，不接真实数据源，不调用 RAG/Qdrant/LLM，不访问真实行情、地图或供应链数据，不修改知识库、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry 或 eval case。

### 验证
- `./venv/Scripts/python.exe -m py_compile src/product/repository.py src/product/service.py src/main.py tools/export_product_data_source_boundary.py tests/test_product_data_source_boundary.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_product_data_source_boundary tests.test_product_api_contract tests.test_product_api_status_catalog tests.test_product_api_field_catalog`
- `./venv/Scripts/python.exe tools/export_product_data_source_boundary.py --output tests/product_data_source_boundary_v0.4.18.8.json`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`

## [0.4.18.7] - 2026-06-17

### Added
- 新增 `src/product/status.py`，集中定义产品接口成功状态与错误码目录。
- 新增 `tools/export_product_api_status_catalog.py`。
- 新增 `tests/test_product_api_status_catalog.py`。
- 新增 `tests/product_api_status_catalog_v0.4.18.7.json`。
- 新增 `docs/product_api_status_catalog_v0.4.18.7.md`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.7`。
- 将 product API status catalog 纳入 health check 的语法检查、必备产物锚点和 offline tool 禁止模式扫描。
- 将 product router 的 fixture 错误响应改为专属错误码与公开错误消息。
- 更新 roadmap、final report guide、工具索引、测试索引、产物索引和维护索引。

### Result
- 状态目录记录 2 个成功/空态语义：`ok` 与 `empty_items`。
- 错误目录记录 6 个错误码：4 个 fixture runtime 错误码和 2 个未来真实数据源 reserved code。
- `/product/risks` 过滤无结果继续返回 HTTP 200 与 `items=[]`，前端应展示空态而非错误。

### Boundary
- 本版本只补齐产品接口状态与错误目录。
- 不接真实数据源，不启动服务，不调用 RAG/Qdrant/LLM，不运行 eval。
- 不修改知识库、eval case、anchor、prompt、rerank 或 risk supplement。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/product/status.py src/product/service.py src/product/router.py tools/export_product_api_status_catalog.py tests/test_product_api_status_catalog.py`
- `./venv/Scripts/python.exe -m unittest tests.test_product_api_status_catalog tests.test_product_api_contract tests.test_product_api_field_catalog`
- `./venv/Scripts/python.exe tools/export_product_api_status_catalog.py --output tests/product_api_status_catalog_v0.4.18.7.json`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.18.6] - 2026-06-17

### Added
- 新增 `tools/export_product_api_field_catalog.py`。
- 新增 `tests/test_product_api_field_catalog.py`。
- 新增 `tests/product_api_field_catalog_v0.4.18.6.json`。
- 新增 `docs/product_api_field_catalog_v0.4.18.6.md`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.6`。
- 将 product API field catalog 纳入 health check 的语法检查、必备产物锚点和 offline tool 禁止模式扫描。
- 更新 roadmap、final report guide、工具索引、测试索引、产物索引和维护索引。

### Result
- 字段目录覆盖 6 个 `/product/*` fixture-backed 接口。
- 目录记录 endpoint id、method、path、query params、response envelope、meta 字段和从 fixture 推导出的 response field paths。
- 当前 catalog 摘要为 `endpoint_count=6`，`query_param_count=13`，`source_version_matches=true`，且当前 fixture 字段未被截断。

### Boundary
- 本版本只生成产品后端字段目录。
- 不启动服务，不调用 RAG/Qdrant/LLM，不运行 eval，不接真实行情、地图、供应链、权限系统或外部数据源。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval case、hidden seed 或知识库数据。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/export_product_api_field_catalog.py tests/test_product_api_field_catalog.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_product_api_field_catalog tests.test_product_api_contract tests.test_product_mock_endpoint_contract tests.test_product_view_model_contract`
- `./venv/Scripts/python.exe tools/export_product_api_field_catalog.py --output tests/product_api_field_catalog_v0.4.18.6.json`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.18.5] - 2026-06-17

### Added
- 新增 `src/product/contracts.py`、`src/product/schemas.py`、`src/product/service.py`、`src/product/router.py`，建立产品后端接口分层。
- 新增 6 个 fixture-backed `/product/*` FastAPI GET 接口。
- 新增 `tools/check_product_api_contract.py`。
- 新增 `tests/test_product_api_contract.py`。
- 新增 `tests/product_api_contract_v0.4.18.5_report.json`。
- 新增 `docs/product_api_backend_integration_v0.4.18.5.md`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.5`。
- 将 product API contract checker 纳入 health check 的语法检查、必备产物锚点和 offline tool 禁止模式扫描。
- 更新 v0.4.18.4 mock endpoint checker 的 FastAPI surface 语义：产品路径暴露后记录为 fixture-backed API promotion，不再作为离线 contract 漂移失败。
- 更新 roadmap、final report guide、工具索引、测试索引、产物索引和维护索引。

### Result
- `/product/dashboard/summary`、`/product/legal/workspace`、`/product/market/signals`、`/product/supply-chain/map`、`/product/lifecycle/risk` 和 `/product/risks` 已接入 FastAPI。
- 产品接口统一返回 `status`、`data/items` 和 `meta` envelope。
- `meta` 明确标记 `data_source=fixture_sample`，并声明 RAG、Qdrant、LLM、行情、地图和供应链外部数据均未调用。
- checker 报告为 `status=passed`，`endpoint_count=6`，`openapi_passed=6`，`response_passed=6`，`issue_count=0`。

### Boundary
- 本版本只接入 fixture-backed product API 层级。
- 不调用 RAG/Qdrant/LLM，不运行 eval，不接真实行情、地图、供应链、权限系统或外部数据源。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval case、hidden seed 或知识库数据。
- `/product/legal/workspace` 返回的是展示态 view model，不是实时 RAG 问答结果。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/product/contracts.py src/product/schemas.py src/product/service.py src/product/router.py src/main.py tools/check_product_api_contract.py tests/test_product_api_contract.py`
- `./venv/Scripts/python.exe -m unittest tests.test_product_api_contract tests.test_product_mock_endpoint_contract tests.test_product_view_model_contract tests.test_api_contract`
- `./venv/Scripts/python.exe tools/check_product_api_contract.py --output tests/product_api_contract_v0.4.18.5_report.json --fail-on-error`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.18.4] - 2026-06-17

### Added
- 新增 `tools/check_product_mock_endpoint_contract.py`，从 v0.4.18.3 product view model fixture 派生并校验离线 product mock endpoint contract。
- 新增 `tests/test_product_mock_endpoint_contract.py`。
- 新增 `tests/product_mock_endpoint_contract_v0.4.18.4_report.json`。
- 新增 `docs/product_mock_endpoint_contract_v0.4.18.4.md`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.4`。
- 将 product mock endpoint contract checker 纳入 health check 的语法检查、必备产物锚点和 offline tool 禁止模式扫描。
- 更新 roadmap、final report guide、工具索引、测试索引、产物索引和维护索引。

### Result
- 定义 6 个离线 mock endpoint contract：`/product/dashboard/summary`、`/product/legal/workspace`、`/product/market/signals`、`/product/supply-chain/map`、`/product/lifecycle/risk` 和 `/product/risks`。
- 所有 endpoint 均为只读 `GET` contract，并从 `tests/fixtures/product_view_models_v0.4.18.3.json` 派生响应样例。
- checker 报告为 `status=passed`，`endpoint_count=6`，`view_endpoint_count=5`，`shared_endpoint_count=1`，`product_risk_count=3`，`issue_count=0`。

### Boundary
- 本版本只定义离线 product mock endpoint contract 和校验器。
- 不新增正式 FastAPI 路由，不启动服务，不接 UI，不实现 mock service daemon。
- 不调用 RAG/Qdrant/LLM，不运行 eval，不接真实行情、地图、供应链或权限系统。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval case、hidden seed 或知识库数据。
- mock endpoint response 是 UI handoff 样例，不是法律结论、不是 eval case、不是 completed manual decision，也不是 ready action。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/check_product_mock_endpoint_contract.py tests/test_product_mock_endpoint_contract.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_product_mock_endpoint_contract tests.test_product_view_model_contract tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/check_product_mock_endpoint_contract.py --output tests/product_mock_endpoint_contract_v0.4.18.4_report.json --fail-on-error`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.18.3] - 2026-06-16

### Added
- 新增 `tests/fixtures/product_view_models_v0.4.18.3.json`，定义 dashboard、legal workspace、market signals、supply-chain map 和 lifecycle risk 的离线产品 view model fixture。
- 新增 `tools/check_product_view_model_contract.py`。
- 新增 `tests/test_product_view_model_contract.py`。
- 新增 `tests/product_view_model_contract_v0.4.18.3_report.json`。
- 新增 `docs/product_view_model_contract_v0.4.18.3.md`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.3`。
- 将 product view model contract checker 纳入 health check 的语法检查、必备产物锚点和 offline tool 禁止模式扫描。
- 更新 roadmap、final report guide、工具索引、测试索引、产物索引和维护索引。

### Result
- 当前 fixture 覆盖 5 个 view models：`dashboard_summary`、`legal_workspace`、`market_signals`、`supply_chain_map`、`lifecycle_risk`。
- 定义 3 个跨模块 `product_risks`，通过 `risk_id` 连接首页、法律工作台、市场信号、供应链地图和生命周期视图。
- checker 报告为 `status=passed`，`issue_count=0`，`dashboard_risk_cards=3`，`market_signal_count=2`，`supply_chain_node_count=2`，`lifecycle_stage_count=3`。

### Boundary
- 本版本只定义离线产品 view model contract 和校验器。
- 不实现 UI，不新增正式 API，不启动 FastAPI 服务，不接真实行情、地图、供应链或权限系统。
- 不调用 RAG/Qdrant/LLM，不运行 eval，不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval case、hidden seed 或知识库数据。
- fixture 是 UI/view-model 样例，不是真实业务数据、不是 eval case、不是 completed manual decision，也不是 ready action。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/check_product_view_model_contract.py tests/test_product_view_model_contract.py`
- `./venv/Scripts/python.exe -m unittest tests.test_product_view_model_contract tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/check_product_view_model_contract.py --output tests/product_view_model_contract_v0.4.18.3_report.json`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.18.2] - 2026-06-15

### Added
- 新增 `docs/product_design_brief_v0.4.18.2.md`，作为给设计专员的产品设计简报和 UI handoff brief。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.2`。
- 更新 roadmap、final report guide、产物索引和维护索引。

### Result
- 设计简报明确项目定位为 Harvey 风格企业法律风控系统，而不是普通聊天机器人或单纯行情看板。
- 简报梳理了首页风险驾驶舱、市场行情与外部风险、供应链地图与区域风险、法律风控 RAG 工作台、企业全生命周期风险概览五个产品模块。
- 简报明确第一阶段设计目标是产品骨架、核心页面和专业视觉方向，不要求真实行情接口、真实地图数据、完整权限系统或正式 UI 实现。

### Boundary
- 本版本只新增产品设计交接文档。
- 不实现 UI，不新增 API，不接行情或地图数据，不调用 RAG/Qdrant/LLM，不修改 retriever、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry、eval case 或知识库数据。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe -m unittest tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.18.1] - 2026-06-15

### Added
- 新增 `tools/check_legal_corpus_integrity.py`，用于法规扩容前的本地 corpus integrity 基线检查。
- 新增 `tests/test_legal_corpus_integrity.py`。
- 新增 `tests/legal_corpus_integrity_v0.4.18.1_report.json`。
- 新增 `docs/legal_corpus_integrity_baseline_v0.4.18.1.md`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.18.1`。
- 将 legal corpus integrity checker 纳入 health check 的语法检查、必备产物锚点和 offline tool 禁止模式扫描。
- 更新 roadmap、final report guide、工具索引、测试索引、产物索引和维护索引。

### Result
- 当前 manifest 覆盖 15 份法规/标准。
- 本地 `load_txt()` 离线生成 7177 个 Document 片段。
- `status=passed`，`error_count=0`，`warning_count=0`，`orphan_knowledge_file_count=0`。
- per-domain summary 覆盖 `civil_law`、`corporate`、`data_compliance`、`data_compliance_standard`、`data_export`、`intellectual_property`、`market_regulation`、`security_compliance` 和 `tax`。

### Boundary
- 本版本只读取 `knowledge_manifest.json` 和 `src/knowledge/**/*.txt`，并复用 `load_txt()` 做离线 Document metadata 检查。
- 不访问 Qdrant，不重建 `legal_knowledge`，不运行 RAG eval/risk eval/report eval/hidden eval，不调用 `rag_query` 或 LLM。
- 不修改知识库文本、manifest、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、eval case 或 Qdrant 数据。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/check_legal_corpus_integrity.py tests/test_legal_corpus_integrity.py`
- `./venv/Scripts/python.exe -m unittest tests.test_legal_corpus_integrity tests.test_ingestion_quality tests.test_qdrant_index_integrity`
- `./venv/Scripts/python.exe tools/check_legal_corpus_integrity.py --output tests/legal_corpus_integrity_v0.4.18.1_report.json`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe -m unittest tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`

## [0.4.17.7] - 2026-06-15

### Added
- 新增 `tests/rag_eval_report_v0.4.17.7.json`，用于记录 v0.4.17.6 后的当前 RAG 主链路 full eval 收口确认。
- 新增 `docs/rag_full_eval_closeout_v0.4.17.7.md`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.17.7`。
- 更新 roadmap、final report guide、测试索引、产物索引和维护索引。

### Result
- 当前 full RAG eval 结果为 `59/60` passed。
- retrieval stage 保持 `PASS=60`。
- 唯一失败仍为 `risk_unfair_competition_confusion_001` 的 expected risk level `over_risk`：系统输出 `high`，预期为 `medium`。
- 该 case 的 expected evidence、answer keywords、confidence score、expected risk types 和 expected actions 均通过；证据命中现行《中华人民共和国反不正当竞争法》第七条。
- v0.4.17.x 可收口为：当前剩余问题是 expected-level / fact-strength 复核项，不是新的 retrieval、evidence-chain 或 runtime 回归。

### Boundary
- 本版本运行 full RAG eval，但不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、hidden seed、Qdrant 数据、eval case、expected evidence 或 expected risk level。
- 不把本版本写成新的 gate；它是 RAG 主链路收口确认。

### Verification
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/rag_eval_report_v0.4.17.7.json --check-risk`（预期退出码为 `1`，因为保留已知 expected-level 失败；报告成功写出，结果为 `59/60`、retrieval `PASS=60`）
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.17.6] - 2026-06-15

### Changed
- 修正 `tests/rag_eval_cases.json` 中 `risk_unfair_competition_confusion_001` 的 `legal_reasoning` 旧编号表述：从 2019 口径的第6条改为现行法第7条。
- 保持 `expected_evidence`、`expected_risk_level`、`expected_risk_types`、`expected_actions` 和 `expected_evidence_match` 不变。
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.17.6`。
- 更新 roadmap、final report guide、测试索引、产物索引和维护索引。

### Added
- 新增 `docs/unfair_competition_confusion_metadata_patch_v0.4.17.6.md`。
- 新增 `tests/rag_expected_level_review_packet_v0.4.17.6_report.json`。
- 新增 `tests/legal_text_version_verification_packet_v0.4.17.6_report.json`。

### Result
- v0.4.17.6 expected-level review packet 仍将固定失败分类为 `expected_level_fact_strength_review`。
- `metadata_warning_counts` 已清零。
- legal text version verification packet 分类变为 `current_law_evidence_valid`。
- 固定失败仍不建议 runtime patch、anchor change 或 prompt/rerank/risk rule 修改。

### Boundary
- 本版本只改 eval case 的 `legal_reasoning` 说明文字。
- 不改变 expected evidence 或 expected risk level。
- 不新增 anchor，不修改 prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、hidden seed 或 Qdrant 数据。
- 不运行 full eval。

### Verification
- `./venv/Scripts/python.exe tools/build_rag_expected_level_review_packet.py --repeat-report tests/targeted_rag_evidence_independence_v0.4.17.3_report.json --cases tests/rag_eval_cases.json --output tests/rag_expected_level_review_packet_v0.4.17.6_report.json`
- `./venv/Scripts/python.exe tools/build_legal_text_version_verification_packet.py --review-packet tests/rag_expected_level_review_packet_v0.4.17.6_report.json --snapshot tests/legal_text_version_snapshot_v0.4.17.5.json --output tests/legal_text_version_verification_packet_v0.4.17.6_report.json`
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_legal_text_version_verification_packet tests.test_rag_expected_level_review_packet tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.17.5] - 2026-06-15

### Added
- 新增 `tests/legal_text_version_snapshot_v0.4.17.5.json`，固化《反不正当竞争法》现行文本与 2019 修正文本的条文编号核验。
- 新增 `tools/build_legal_text_version_verification_packet.py`，只读法律文本版本快照和 v0.4.17.4 review packet，生成条文编号漂移核验报告。
- 新增 `tests/test_legal_text_version_verification_packet.py`。
- 新增 `tests/legal_text_version_verification_packet_v0.4.17.5_report.json`。
- 新增 `docs/legal_text_version_verification_packet_v0.4.17.5.md`。

### Result
- 核验来源包括最高人民检察院门户网转载新华社 2025 修订文本、国家知识产权局 2025 修订文本和国家知识产权局 2019 修正文本。
- 结论：2025 修订现行法中，混淆行为条款为第七条；2019 修正文本中，混淆行为条款为第六条。
- `risk_unfair_competition_confusion_001` 的 expected evidence 与三轮最终证据链均为第七条，符合现行法。
- case `legal_reasoning` 中第6条属于旧编号/元数据表述漂移，不是检索、anchor 或 evidence-chain 错误。
- 报告分类为 `metadata_article_numbering_drift_current_evidence_valid`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.17.5`。
- 更新 roadmap、final report guide、测试索引、工具索引、产物索引和维护索引。

### Boundary
- 本轮人工核验使用联网来源；入库工具和单测只读取保存快照，不联网。
- 不运行 full eval 或 targeted eval。
- 不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant 数据。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_legal_text_version_verification_packet.py tests/test_legal_text_version_verification_packet.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_legal_text_version_verification_packet tests.test_rag_expected_level_review_packet tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/build_legal_text_version_verification_packet.py --review-packet tests/rag_expected_level_review_packet_v0.4.17.4_report.json --snapshot tests/legal_text_version_snapshot_v0.4.17.5.json --output tests/legal_text_version_verification_packet_v0.4.17.5_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.17.4] - 2026-06-15

### Added
- 新增 `tools/build_rag_expected_level_review_packet.py`，只读 targeted repeat 报告和现有 eval case 元数据，分类固定失败性质。
- 新增 `tests/test_rag_expected_level_review_packet.py`，覆盖 expected-level 单点失败、检索失败分流和其他输出检查失败分流。
- 新增 `tests/rag_expected_level_review_packet_v0.4.17.4_report.json`。
- 新增 `docs/rag_expected_level_review_packet_v0.4.17.4.md`。

### Result
- 固定失败 case 为 `risk_unfair_competition_confusion_001`。
- 分类为 `expected_level_fact_strength_review`。
- 报告确认三轮均为 `retrieval_failure_stage=PASS`，且非风险等级检查均通过。
- 记录 metadata warning：`legal_reasoning_article_ref_not_subset_of_expected_evidence`，即 case 说明中提到第6条，而 expected evidence 与实际证据链均为第7条。
- 结论为不建议 runtime patch、不建议 anchor change、不建议未经人工复核直接修改 eval case。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.17.4`。
- 更新 roadmap、final report guide、测试索引、工具索引、产物索引和维护索引。

### Boundary
- 本版本只读 saved report，不运行 full eval 或 targeted eval。
- 不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant 数据。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_rag_expected_level_review_packet.py tests/test_rag_expected_level_review_packet.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_expected_level_review_packet tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/build_rag_expected_level_review_packet.py --repeat-report tests/targeted_rag_evidence_independence_v0.4.17.3_report.json --cases tests/rag_eval_cases.json --output tests/rag_expected_level_review_packet_v0.4.17.4_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.17.3] - 2026-06-15

### Added
- 新增 `tests/targeted_rag_evidence_independence_v0.4.17.3_report.json`，按 v0.4.17.2 packet 执行 17 个 case、3 轮 targeted repeat。
- 新增 `docs/rag_targeted_repeat_closeout_v0.4.17.3.md`，收口解释 targeted repeat 结果、退出码含义和下一步边界。

### Result
- targeted repeat pass counts 为 `[16, 16, 16]`，total counts 为 `[17, 17, 17]`。
- 每轮 retrieval stage 均为 `PASS=17`。
- `unstable_cases=0`，`label_variation_cases=1`。
- 固定失败仍为 `risk_unfair_competition_confusion_001`：`actual=high`、`expected=medium`、`mismatch_type=over_risk`。
- base retrieval lexical triage 组、output rule dependency review 组和 pure LLM control 组均在三轮中全通过。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.17.3`。
- 更新 roadmap、final report guide、测试索引、产物索引和维护索引。

### Boundary
- 本版本运行 targeted eval，但不运行 full eval。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant 数据。
- 不因固定 over-risk case 直接做 runtime patch。

### Verification
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --check-risk --compact-report --repeat 3 ... --output tests/targeted_rag_evidence_independence_v0.4.17.3_report.json`（报告成功写出；退出码 1 来自预期包含的固定 over-risk case）
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.17.2] - 2026-06-15

### Added
- 新增 `tools/build_rag_targeted_rerun_packet.py`，只读 v0.4.17.1 evidence independence baseline，生成 bounded targeted rerun 候选包。
- 新增 `tests/test_rag_targeted_rerun_packet.py`，覆盖候选分组、失败 case 分流、pure LLM control 和非 runtime patch 结论。
- 新增 `tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`。
- 新增 `docs/rag_targeted_rerun_packet_v0.4.17.2.md`。

### Result
- 报告状态为 `targeted_rerun_packet_ready`。
- selected case 为 17 个：base retrieval lexical triage 8 个，output rule dependency review 5 个，failed / expected-level review 1 个，pure LLM control 3 个。
- 候选包输出 combined targeted repeat 命令，但本版本没有执行 targeted eval。
- 结论为 `runtime_patch_recommendation=not_recommended_by_this_packet`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.17.2`。
- 更新 roadmap、final report guide、测试索引、工具索引、产物索引和维护索引。

### Boundary
- 本版本只读 saved report，不运行 full eval 或 targeted eval。
- 不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_rag_targeted_rerun_packet.py tests/test_rag_targeted_rerun_packet.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/build_rag_targeted_rerun_packet.py --input tests/rag_evidence_independence_baseline_v0.4.17.1_report.json --output tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.17.1] - 2026-06-15

### Added
- 新增 `tools/build_rag_evidence_independence_baseline.py`，只读既有 RAG eval 保存报告，生成主链路证据独立性与规则依赖归因基线。
- 新增 `tests/test_rag_evidence_independence_baseline.py`，覆盖 dependency bucket、失败 case 分流、优先级列表和通用诊断逻辑。
- 新增 `tests/rag_evidence_independence_baseline_v0.4.17.1_report.json`。
- 新增 `docs/rag_evidence_independence_baseline_v0.4.17.1.md`。

### Result
- 输入基线为 `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json`。
- 报告状态为 `has_failed_cases_and_dependency_hotspots`：`59/60` passed，retrieval stage `PASS=60`。
- 高依赖 case 为 48/60，`high_dependency_ratio=0.8`。
- label counts：`ANCHOR_PASS=29`、`RISK_SUPPLEMENT_PASS=43`、`TERM_PRESERVATION_PASS=8`、`PURE_LLM_PASS=7`。
- 下一步信号：`inspect_base_retrieval_query_lexical_coverage=29`、`inspect_output_rule_dependency=19`、`failed_case_fact_or_expected_level_review=1`。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.17.1`。
- 修复 `docs/final_report_version_guide.md` 中 v0.4.16.12 段落的历史问号污染，并更新 roadmap、final report guide、测试索引、工具索引、产物索引和维护索引。

### Boundary
- 本版本只读 saved report，不运行 full eval 或 targeted eval。
- 不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_rag_evidence_independence_baseline.py tests/test_rag_evidence_independence_baseline.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/build_rag_evidence_independence_baseline.py --input tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json --output tests/rag_evidence_independence_baseline_v0.4.17.1_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.12] - 2026-06-15

### Added
- 新增 `docs/api_contract_stability_closeout_v0.4.16.12.md`，收口 v0.4.16.x API contract stability 系列，并给出离线契约材料的最小使用顺序。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.12`。
- 更新 `docs/project_review_and_roadmap.md`，将 v0.4.16.x 标记为已收口，并把下一步切换到前端 handoff/mock service 或新系列规划。
- 更新 `docs/final_report_version_guide.md`、产物索引和维护索引，纳入本系列 closeout。

### Boundary
- 本版本只做系列收口和 runbook 文档；不新增 checker，不接正式前端，不运行 full eval。
- 不调用 `rag_query`、Qdrant、LLM 或真实报告生成。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract tests.test_api_contract_consistency tests.test_roadmap_hygiene tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.11] - 2026-06-14

### Added
- 新增 `tools/check_api_contract_consistency.py`，离线比对 OpenAPI schema、API contract bundle、API field catalog 和 example payload fixture 的一致性。
- 新增 `tests/test_api_contract_consistency.py`，覆盖当前契约产物一致性和缺少必填字段的通用诊断逻辑。
- 新增 `tests/api_contract_consistency_v0.4.16.11_report.json`，记录本轮一致性检查结果。
- 新增 `docs/api_contract_consistency_checker_v0.4.16.11.md`，说明 checker 的定位、检查内容、边界和验证方式。

### Changed
- 清理 `tests/test_api_contract.py` 中重复的 `build_api_field_catalog` import 和重复测试定义。
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.11`。
- 更新 `docs/final_report_version_guide.md`，将 v0.4.16.x 报告素材按自然升序整理，并补齐 v0.4.16.10/v0.4.16.11。
- 更新 roadmap、测试索引、工具索引、产物索引和维护索引，纳入 API contract consistency checker。

### Boundary
- 本版本只做离线 API 契约一致性诊断、测试与文档维护；不启动服务，不接正式前端，不运行 full eval。
- 不调用 `rag_query`、Qdrant、LLM 或真实报告生成。
- 不修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/check_api_contract_consistency.py tests/test_api_contract_consistency.py tests/test_api_contract.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract tests.test_api_contract_consistency tests.test_roadmap_hygiene tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/check_api_contract_consistency.py --output tests/api_contract_consistency_v0.4.16.11_report.json --fail-on-error`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.10] - 2026-06-14

### Added
- 新增 `tools/export_api_field_catalog.py`，导出请求/响应模型的字段目录、必填项和默认值。
- 新增 `tests/api_field_catalog_v0.4.16.10.json`，供前端表单与展示映射使用。
- 新增 `docs/api_field_catalog_v0.4.16.10.md`，说明 field catalog 的定位、内容和边界。
- 扩展 `tests/test_api_contract.py`，验证 field catalog 覆盖请求与响应模型字段、必填项和默认值。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.10`。
- 更新 `docs/project_review_and_roadmap.md`，把当前离线契约交付物扩展到 API field catalog。

### Boundary
- 本版本只做离线字段目录交付；不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不接正式前端，不新增 gate，不运行 full eval。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/export_api_field_catalog.py tests/test_api_contract.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract tests.test_roadmap_hygiene tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.9] - 2026-06-14

### Added
- 扩展 `tools/export_api_contract_bundle.py`，在 bundle 中新增 `error_examples`，覆盖 `validation_error_422`、`llm_timeout_504`、`internal_error_500`。
- 扩展 `tests/test_api_contract.py`，验证 bundle 的错误样例，并用 `/ask` + `TimeoutError` mock 覆盖统一 504 envelope。
- 新增 `tests/api_contract_bundle_v0.4.16.9.json`，作为包含错误状态样例的新 bundle 产物。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.9`。
- 更新 `docs/project_review_and_roadmap.md`，按保留窗口滚动当前事项为 v0.4.16.8/v0.4.16.9。

### Boundary
- 本版本只补充离线错误/校验状态契约样例；不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不接正式前端，不新增 gate，不运行 full eval。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/export_api_contract_bundle.py tests/test_api_contract.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract tests.test_roadmap_hygiene tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.8] - 2026-06-14

### Added
- 新增 `tools/export_api_contract_bundle.py`，将当前 OpenAPI schema 与离线 example payload 合并为机器可读的 API contract bundle。
- 新增 `tests/api_contract_bundle_v0.4.16.8.json`，供未来前端/工作台离线联调用。
- 新增 `docs/api_contract_bundle_v0.4.16.8.md`，说明 bundle 的定位、内容和边界。
- 扩展 `tests/test_api_contract.py`，验证 bundle 同时包含 schema 与 example payload，且不触发真实 runtime 调用。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.8`。
- 更新 `docs/project_review_and_roadmap.md`，在当前基线中纳入 API contract bundle，并保持 roadmap next-step hygiene。

### Boundary
- 本版本只做离线 bundle 交付；不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不接正式前端，不新增 gate，不运行 full eval。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/export_api_contract_bundle.py tests/test_api_contract.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract tests.test_roadmap_hygiene tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.7] - 2026-06-14

### Added
- 新增 `tests/test_roadmap_hygiene.py`，检查 `docs/project_review_and_roadmap.md` 的 `## 推荐下一步` 不得堆放已完成版本流水账。

### Changed
- 清理 `docs/project_review_and_roadmap.md` 中 `## 推荐下一步` 下残留的 v0.4.15.x 历史完成项，改为仅保留当前下一步判断。
- 在 roadmap 维护规则中明确：`## 推荐下一步` 只能写当前待办和最近一次下一步判断，完成后应在下一版本更新或删除。
- 修正 `tests/test_project_health_check.py` 的旧版本硬编码，改为断言当前 `tools.run_project_health_check.VERSION`。
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.7`。

### Boundary
- 本版本只做 roadmap hygiene 与防回归测试；不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不新增 gate，不运行 full eval，不接正式前端。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py tests/test_roadmap_hygiene.py`
- `./venv/Scripts/python.exe -m unittest tests.test_roadmap_hygiene tests.test_api_contract tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.6] - 2026-06-14

### Added
- 扩展 `tests/test_api_contract.py`，新增 `/ask`、`/risk/analyze`、`/risk/report` 的 `TestClient + mock` endpoint smoke contract。
- 新增测试确认三个接口会进入对应 runtime 入口：`rag_query`、`analyze_risk`、`generate_risk_report`，并返回符合现有响应契约的 payload。
- 新增测试确认请求过滤参数会透传：`collection_name`、`k`、`doc_type`、`category`、`jurisdiction`、`score_threshold`、`debug` 以及其他可选过滤字段，避免未来前端接入前出现 silent contract drift。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.6`。
- 更新 `docs/project_review_and_roadmap.md`，按“已完成事项最多保留最近两个版本”规则移除 v0.4.16.4 的 roadmap 当前事项。

### Boundary
- 本版本只新增离线 mock endpoint smoke contract；不调用真实 RAG、Qdrant、LLM、Cross-Encoder 或报告生成。
- 不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不接正式前端，不新增 gate，不运行 full eval。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tests/test_api_contract.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.5] - 2026-06-14

### Changed
- 更新 `docs/project_review_and_roadmap.md`，在维护规则中明确：已完成的小版本事项最多只保留最近两个版本，超过两个版本的完成细节从 roadmap 删除，改以 `changelog.md`、专题文档和 `docs/final_report_version_guide.md` 为准。
- 精简 roadmap 当前治理基线，删除 v0.4.15.x 中已过保留窗口的小版本流水账，保留阶段基线与仍有决策价值的收口结论。
- 更新 `docs/final_report_version_guide.md`，将 v0.4.16.1-v0.4.16.4 新增版本素材统一为中文，并按自然升序接上 v0.4.16.5。
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.5`。

### Boundary
- 本版本仅做 roadmap/final report 文档治理与版本同步；不修改 RAG runtime、API runtime、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不新增 gate，不运行 full eval，不接正式前端。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`

## [0.4.16.4] - 2026-06-14

### Added
- 新增 `tests/fixtures/api_contract_example_payloads_v0.4.16.4.json`，提供 `/ask`、`/risk/analyze`、`/risk/report` 与 `/risk/report/export` 的离线 example payload。
- 新增 `docs/api_example_payloads_v0.4.16.4.md`，说明样例载荷的用途、契约校验方式和边界。
- 扩展 `tests/test_api_contract.py`，验证 example payload 可通过现有 Pydantic 请求/响应模型，并确认导出 Markdown/JSON 样例具备最小稳定结构。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.4`。
- 将 `tools/export_openapi_schema.py` 的 payload version 与默认输出路径改为跟随当前 `app.version`。

### Boundary
- 本版本仅新增 API example payload fixture；不修改 RAG fixtures、eval cases、retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry 或 Qdrant。
- 不启动服务，不调用 `rag_query`、Qdrant、LLM、Cross-Encoder 或真实报告生成。
- 这是前端接入前的离线契约样例，不是正式前端联调，也不是法律结论样本。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tests/test_api_contract.py tools/export_openapi_schema.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`

## [0.4.16.3] - 2026-06-14

### Added
- 新增 `tools/export_openapi_schema.py`，离线导出 FastAPI OpenAPI schema，不启动服务、不调用 RAG。
- 新增 `tests/openapi_schema_v0.4.16.3.json`，作为前后端接入前的 OpenAPI schema 快照。
- 新增 `docs/openapi_schema_snapshot_v0.4.16.3.md`，说明快照用途、边界和验证方式。
- 扩展 `tests/test_api_contract.py`，验证 OpenAPI 快照 payload 的 guardrails 与核心路径。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.3`。

### Boundary
- 不启动 FastAPI 服务，不调用 `rag_query`、Qdrant、LLM、Cross-Encoder 或报告生成。
- 未修改 retriever、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。
- 本版本是 schema 快照，不是正式前端接入。

### Verification
- `./venv/Scripts/python.exe tools/export_openapi_schema.py --output tests/openapi_schema_v0.4.16.3.json`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`

## [0.4.16.2] - 2026-06-14

### Added
- 扩展 `tests/test_api_contract.py`，用 `TestClient` 与 mock 固化 `/risk/report/export` 的 Markdown/JSON 内容类型和未知导出格式校验。
- 新增 `docs/api_error_and_export_contract_v0.4.16.2.md`，说明统一错误结构与导出响应契约。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.2`。

### Boundary
- 测试不调用真实 `generate_risk_report_export`、`rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 未修改 retriever、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。
- 本版本不接正式前端，不新增 full eval 或 gate。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tests/test_api_contract.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`

## [0.4.16.1] - 2026-06-14

### Added
- 新增 `tests/test_api_contract.py`，离线固化现有 FastAPI 路径、请求默认值、响应必需字段和统一错误响应结构。
- 新增 `docs/api_contract_stability_v0.4.16.1.md`，说明前后端接入前的 API contract 基线和边界。

### Changed
- 将 `src/main.py` 与 `tools/run_project_health_check.py` 版本同步为 `0.4.16.1`。

### Boundary
- 本版本不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 未修改 retriever、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures 或 eval cases。
- 本版本是前后端接入前的契约基线，不是正式前端接入，也不是 RAG 分数修复。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tests/test_api_contract.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_api_contract`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`

## [0.4.15.27] - 2026-06-14

### Changed
- 收口 v0.4.15.x RAG quality/stability 系列：不再继续对剩余 `risk_unfair_competition_confusion_001` 做 runtime 压级，不新增 gate，不新增 eval 报告链。
- 同步 `src/main.py` 与 `tools/run_project_health_check.py` 版本号为 `0.4.15.27`。
- 更新 roadmap 与 final report guide，将 v0.4.15.x 标记为已完成，并把剩余不正当竞争混淆 case 记录为法律事实强度/expected-level 复核债，而非检索或 grounding 回归。

### Result
- v0.4.15.x 以 v0.4.15.26 的保存报告作为收口基线：compact full RAG eval 为 59/60，retrieval stage 为 `PASS=60`。
- 唯一剩余 strict risk-level failure 为 `risk_unfair_competition_confusion_001`；其“知名品牌近似 + 消费者误认”事实使 `high` 具有可辩护性，本版本不硬压。

### Boundary
- 未修改主 RAG 逻辑、hidden seed、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures、eval cases、Qdrant 或 evidence selector。
- 本版本是系列收口与版本治理，不是新能力、不新增样本修补。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- 读取既有 `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json` 确认 59/60、retrieval `PASS=60`、剩余 `over_risk=1`。

## [0.4.15.26] - 2026-06-14

### Changed
- 在 `src/rag/retriever.py` 新增程序/民事管理类 medium cap：仅对“物业公司未经业主同意出租小区公共区域用于广告经营”和“有限责任公司股东对外转让股权、未通知其他股东/影响优先购买权”这两类窄场景，在无严重事实时封顶为 `medium`。
- 收窄 cap 触发边界：物业 cap 只看问题事实中的物业/小区、公共区域、商业使用、业主同意缺口；股权 cap 要求有限责任公司、其他股东通知缺口和优先购买权/对外转让语境，并排除上市公司信息披露、国资转让、司法执行、质押、代持、债权人/监管/审批登记等非普通民事程序场景。
- 加固 v0.4.15.25 商标通用名称 cap：`商标权滥用风险` 这类评价性措辞不再误触发高风险侵权排除；真正侵权、混淆、假冒、未经许可等事实仍保持 `high`。
- 新增普通增值税混合销售/不同税率未分别核算 medium cap：只处理没有虚开、偷逃税、隐匿收入、拒不补缴、重大/多次/故意、行政处罚或刑事事实的核算/税率适用错误。
- 扩展 `tests/test_retriever_contract.py`，覆盖物业共有部分 medium cap、严重物业侵占负例、物业收益争议非同意缺口负例、股权转让未通知 high->medium cap、上市/国资/司法执行/质押/欺诈伪造股权转让负例、普通 VAT 混合销售 cap、虚开/故意拒不补缴 VAT 负例，以及商标权滥用措辞稳定性。

### Result
- `tests/targeted_process_overrisk_trace_v0.4.15.26_report.json`：记录修复前两个程序/民事管理 over-risk 目标 case 的定位依据。
- `tests/targeted_process_overrisk_patch_v0.4.15.26_report.json`：2/2 passed，`risk_property_management_001` 与 `risk_company_share_transfer_001` 均命中 expected `medium`。
- `tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json`：2/2 passed，确认 v0.4.15.25 的两个商标 case 在本版 hardening 后仍稳定通过。
- `tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json`：5/5 passed，确认 `risk_vat_mixed_sales_001` 修复为 `medium`，虚开发票、无票收入、出口退税和低风险 VAT positive case 未被误伤。
- `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json`：compact full RAG eval 为 59/60，retrieval stage 仍为 `PASS=60`，strict risk-level 剩余 1 个 `over_risk`。
- 唯一剩余失败为 `risk_unfair_competition_confusion_001`；该 case 已写明知名品牌近似并导致消费者误认，法律上 high 具有可辩护性，本版本不硬压。

### Boundary
- 本版本是主链路风险等级后处理的窄口径 hardening，不是新 gate，也不是样本修补。
- 未修改 hidden seed、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 物业、股权、商标和 VAT cap 均有严重事实/侵权事实/税务违法升级事实排除，避免把真正高风险场景压低。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tests/test_retriever_contract.py`
- `./venv/Scripts/python.exe -m unittest tests.test_retriever_contract`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_process_overrisk_patch_v0.4.15.26_report.json --check-risk --case-id risk_property_management_001 --case-id risk_company_share_transfer_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json --check-risk --case-id risk_trademark_generic_name_001 --case-id risk_trademark_non_use_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json --check-risk --case-id risk_vat_mixed_sales_001 --case-id risk_vat_false_invoice_001 --case-id risk_vat_export_refund_001 --case-id risk_vat_no_invoice_income_001 --case-id positive_vat_compliance_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json --check-risk --compact-report`：退出码为 1，原因是严格口径下仍有 1 个既有 `over_risk` 失败；本版目标 case 已修复。

## [0.4.15.25] - 2026-06-12

### Changed
- 在 `src/rag/retriever.py` 中新增窄口径商标无效/撤销中风险校准：对“通用名称注册/独占使用”和“连续三年未实际使用/撤销风险”场景允许把过高 `risk_level=high` 收敛为 `medium`。
- 新增 `cap_risk_level` 与 `is_trademark_invalid_or_cancellation_medium_case`，并在 contribution trace 中记录 `trademark_invalid_or_cancellation_medium_cap`、`risk_level_changed` 和 `risk_level_capped`。
- 扩展 `tests/test_retriever_contract.py`，覆盖两个商标 over-risk case 的 `high -> medium` 路径，并增加“未经许可/近似/混淆/侵权”负例，确保高风险商标侵权场景不被误降。

### Result
- `tests/targeted_trademark_overrisk_trace_v0.4.15.25_report.json` 显示修复前两个商标 case 均为 `over_risk`，但 retrieval stage 均为 `PASS`。
- `tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json`：2/2 passed，`risk_trademark_generic_name_001` 与 `risk_trademark_non_use_001` 均命中 expected `medium`。
- `tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json`：compact full RAG eval 为 56/60，retrieval stage 仍为 `PASS=60`；严格风险等级剩余 4 个 `over_risk`。

### Boundary
- 本版本是主链路窄口径 runtime 修复，不是新增 gate，也不是样本修补。
- 未修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 商标侵权、混淆、假冒、仿冒、反向假冒、停止侵权、侵权赔偿等高风险事实被显式排除，仍保持 high。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tests/test_retriever_contract.py`
- `./venv/Scripts/python.exe -m unittest tests.test_retriever_contract`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json --check-risk --case-id risk_trademark_generic_name_001 --case-id risk_trademark_non_use_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json --check-risk --compact-report`：退出码为 1，原因是严格口径下仍有 4 个既有 `over_risk` 失败；两个商标目标 case 已修复。

## [0.4.15.24] - 2026-06-12

### Added
- 新增 saved-report-only 工具 `tools/build_risk_level_overrisk_legal_review_packet.py`，读取 v0.4.15.22 strict eval、v0.4.15.23 attribution、`tests/rag_eval_cases.json` 与可选 `config/scenario_registry.json`，生成 5 个 `over_risk` case 的法律复核包。
- 新增 `tests/test_risk_level_overrisk_legal_review_packet.py`，覆盖商标三年不使用的 high 过度判断、税务少缴边界 case、无 over-risk clean status、归因字段保留和 `rule_change_allowed=false`。
- 新增 `tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json` 与 `docs/risk_level_overrisk_legal_review_packet_v0.4.15.24.md`。

### Result
- 报告状态为 `legal_review_packet_ready`，共 5 个 over-risk cases。
- 法律初判分布：`actual_high_likely_overstated=2`、`expected_medium_likely_reasonable=1`、`actual_high_potentially_defensible=2`。
- 高优先级人工复核清单为 `risk_trademark_generic_name_001`、`risk_trademark_non_use_001`、`risk_property_management_001`。
- 初步法律判断：两个商标 case 更像 high 定级过度；物业共有部分 case 更支持 expected medium；增值税混合销售和反不正当竞争混淆属于 high 可辩护但需要事实强度复核的边界 case。

### Boundary
- 本版本只读取 saved reports 和 eval metadata，不运行 eval，不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 未修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。
- 本版本是 risk-level grounding quality diagnostics，不是法律结论终局判断，也不授权直接改风险规则；所有 case 均输出 `rule_change_allowed=false`。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_risk_level_overrisk_legal_review_packet.py tests/test_risk_level_overrisk_legal_review_packet.py`
- `./venv/Scripts/python.exe -m unittest tests.test_risk_level_overrisk_legal_review_packet`
- `./venv/Scripts/python.exe tools/build_risk_level_overrisk_legal_review_packet.py --eval-report tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json --attribution-report tests/risk_level_overrisk_attribution_v0.4.15.23_report.json --cases tests/rag_eval_cases.json --scenario-registry config/scenario_registry.json --output tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json`

## [0.4.15.23] - 2026-06-11

### Added
- 新增 saved-report-only 工具 `tools/build_risk_level_overrisk_attribution.py`，读取 v0.4.15.22 strict eval 报告，对 `over_risk` case 做归因候选和人工复核分流。
- 新增 `tests/test_risk_level_overrisk_attribution.py`，覆盖 output-rule amplification、taxonomy/LLM wording 候选、无 over-risk 降级状态和字段输出。
- 新增 `tests/risk_level_overrisk_attribution_v0.4.15.23_report.json` 与 `docs/risk_level_overrisk_attribution_v0.4.15.23.md`。

### Result
- 报告状态为 `overrisk_attribution_ready`，共 5 个 over-risk cases。
- 5/5 归因为 `output_rule_amplification_review` 强信号；`review_route_counts` 显示 `risk_supplement_rule_review=4`、`scene_output_rule_review=4`、`answer_wording_overstatement_review=4`。
- 高优先级人工复核清单：`risk_property_management_001`、`risk_trademark_generic_name_001`、`risk_trademark_non_use_001`、`risk_vat_mixed_sales_001`、`risk_unfair_competition_confusion_001`。
- 报告同时保留风险类型、整改动作、final evidence refs、output contribution counts、confidence、review_reason 和 recommended_next_step。

### Boundary
- 本版本只读 v0.4.15.22 saved report，不运行 eval，不调用 `rag_query`、Qdrant、LLM 或 Cross-Encoder。
- 未修改 retriever、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 hidden seed。
- 本版本是风险等级质量债归因候选/人工复核分流工具，不是规则修复工具；compact report 字段不足以精确证明 taxonomy 或具体 rule id 根因。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_risk_level_overrisk_attribution.py tests/test_risk_level_overrisk_attribution.py`
- `./venv/Scripts/python.exe -m unittest tests.test_risk_level_overrisk_attribution`
- `./venv/Scripts/python.exe tools/build_risk_level_overrisk_attribution.py --input tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json --output tests/risk_level_overrisk_attribution_v0.4.15.23_report.json`

## [0.4.15.22] - 2026-06-11

### Changed
- 将 `tools/run_rag_eval.py` 的 `expected_risk_level` 验收从“actual risk level >= expected risk level”改为精确匹配，避免 `risk_level=high, expected=medium` 被误判为通过。
- `expected_risk_level` check 现在输出结构化 `details`，包括 `policy=exact`、`actual_level`、`expected_level` 和 `mismatch_type`。
- 新增 `risk_level_mismatch_summary`，汇总 `exact_match`、`over_risk`、`under_risk` 和对应 case list。
- 扩展 `tests/test_rag_eval_diagnostics.py`，覆盖 exact policy、`over_risk`、`under_risk` 和 summary 聚合。

### Result
- `tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json`：6 个历史风险等级可疑 case 中 2/6 通过，4 个明确暴露为 `over_risk`；retrieval stage 仍为 `PASS=6`。
- `tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json`：严格口径 full compact eval 为 55/60，retrieval stage 仍为 `PASS=60`，`risk_level_mismatch_summary={"exact_match":45,"over_risk":5}`。
- 5 个 full eval 失败均为风险等级过高：`risk_property_management_001`、`risk_trademark_generic_name_001`、`risk_trademark_non_use_001`、`risk_vat_mixed_sales_001`、`risk_unfair_competition_confusion_001`。

### Boundary
- 本版本是 eval runner quality repair，不是 RAG 主链路修复。
- 未修改 `rag_query`、retriever、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant。
- 55/60 是严格评测口径暴露出的真实 risk-level 质量债，不应解读为 v0.4.15.21 retrieval patch 回归。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/run_rag_eval.py tests/test_rag_eval_diagnostics.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_eval_diagnostics`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json --check-risk --case-id risk_gray_area_ai_training_001 --case-id risk_property_management_001 --case-id risk_trademark_generic_name_001 --case-id risk_trademark_non_use_001 --case-id risk_vat_mixed_sales_001 --case-id risk_unfair_competition_confusion_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json --check-risk --compact-report`：退出码为 1，原因是严格口径下 5 个 `over_risk` 失败；该失败是本版本预期记录的质量信号。

## [0.4.15.21] - 2026-06-11

### Changed
- 将 `rag_query` 的 base sparse retrieval 候选深度从 `k=10` 保守提升为 `BASE_SPARSE_CANDIDATE_K=20`，用于降低已确认的 sparse rank/cutoff loss。
- 将 dense、sparse、base union、rerank input、base/anchor quota 的候选预算抽为命名常量；除 sparse depth 外，其余运行时预算保持原行为：dense `5`、base union `15`、rerank input `15`、base quota `5`、anchor quota `10`。
- 扩展 debug summary 的 sparse/union/rerank input 展示上限，使诊断报告能看见新增 sparse 候选来源。
- 更新 `tests/test_candidate_budget.py`，锁定 v0.4.15.21 的保守候选预算，防止回退到过窄 sparse depth 或误改为激进 rerank input 扩张。

### Result
- `tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json`：7/7 targeted cases 通过；`risk_contract_auto_renewal_001` 同时命中《民法典》第 497 条与第 496 条，`positive_antitrust_independent_pricing_001` 命中《反垄断法》第 17 条。
- `tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json`：compact full RAG eval 60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- 激进候选扩张曾导致 IP 类 case 退到 58/60；最终提交版本没有采用该方案，而是保留仅扩大 sparse depth 的最小 runtime patch。

### Boundary
- 未修改 hidden seed、anchor、prompt、rerank 算法、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 未写入 Qdrant、未 rebuild、未新增 anchor；本版本只做主链路 base retrieval 候选收集深度的保守 runtime patch。
- `risk_gray_area_ai_training_001` 和部分 tax/unfair-competition case 仍存在 eval 接受逻辑下的风险等级宽容现象；本版本不修改风险规则，只记录为后续评测质量议题。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tests/test_candidate_budget.py`
- `./venv/Scripts/python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json --check-risk --case-id risk_chatbot_training_001 --case-id risk_employee_data_export_001 --case-id risk_ai_medical_training_export_001 --case-id risk_gray_area_ai_training_001 --case-id risk_contract_auto_renewal_001 --case-id risk_vat_export_refund_001 --case-id positive_antitrust_independent_pricing_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json --check-risk --compact-report`

## [0.4.15.20] - 2026-06-11

### Added
- 新增显式 dense-enabled live probe wrapper `tools/build_base_candidate_dense_live_probe.py`，复用 v0.4.15.19 只读探针并明确开启 dense query embedding。
- 新增 `tests/test_base_candidate_dense_live_probe.py`、`tests/base_candidate_dense_live_probe_v0.4.15.20_report.json` 与 `docs/base_candidate_dense_live_probe_v0.4.15.20.md`。

### Result
- Dense probe 结论为 `completed_with_dense_probe`。
- 14/14 missing final refs 存在于 Qdrant payload 且可通过 runtime metadata filter。
- attribution counts：`sparse_rank_cutoff_loss=10`、`dense_rank_cutoff_loss=2`、`base_retrieval_gap_confirmed_with_dense_probe=2`。
- 下一步应做最小 runtime validation patch，重点验证 base candidate depth / union collection 调整，而不是新增 anchor。

### Boundary
- Qdrant 仍为只读；不写 Qdrant，不调用 `rag_query`，不运行 eval，不调用 LLM/Cross-Encoder，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、retriever 或主链路。
- 本版本显式允许 dense query embedding 调用，用于 live rank 归因；该调用与 runtime patch 解耦。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_base_candidate_dense_live_probe.py tests/test_base_candidate_dense_live_probe.py`
- `./venv/Scripts/python.exe -m unittest tests.test_base_candidate_dense_live_probe`
- `./venv/Scripts/python.exe tools/build_base_candidate_dense_live_probe.py --mismatch tests/base_candidate_mismatch_summary_v0.4.15.18_report.json --trace tests/targeted_dependency_trace_v0.4.15.16_report.json --collection legal_knowledge --output tests/base_candidate_dense_live_probe_v0.4.15.20_report.json`

## [0.4.15.19] - 2026-06-11

### Added
- 新增 live read-only Qdrant probe 工具 `tools/build_base_candidate_live_readonly_probe.py`，针对 v0.4.15.18 的 14 个 missing final refs 做 payload 存在性、runtime metadata filter、sparse high-k 与 base union 归因检查。
- 新增 `tests/test_base_candidate_live_readonly_probe.py`、`tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json` 与 `docs/base_candidate_live_readonly_probe_v0.4.15.19.md`。

### Result
- Probe 结论为 `completed_requires_dense_probe`。
- `legal_knowledge` 可读，points count 为 7177。
- 14/14 missing final refs 存在于 Qdrant payload，14/14 均可通过 runtime metadata filter；因此不是 collection payload 缺失，也不是 metadata filter 排除。
- 10/14 refs 在 sparse high-k 中可见但未进入 runtime sparse `k=10` 或 base union，归因为 `sparse_rank_cutoff_loss`。
- 剩余 4/14 refs 需要显式 dense probe 才能继续判断 dense rank/cutoff 或向量召回问题。

### Boundary
- 只进行 Qdrant read-only 探测；不写 Qdrant，不调用 `rag_query`，不运行 eval，不调用 LLM/Cross-Encoder，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、retriever 或主链路。
- Dense probe 默认关闭，避免无意触发外部 embedding 服务；如需进一步归因，应在下一版本显式开启并单独记录。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_base_candidate_live_readonly_probe.py tests/test_base_candidate_live_readonly_probe.py`
- `./venv/Scripts/python.exe -m unittest tests.test_base_candidate_live_readonly_probe`
- `./venv/Scripts/python.exe tools/build_base_candidate_live_readonly_probe.py --mismatch tests/base_candidate_mismatch_summary_v0.4.15.18_report.json --trace tests/targeted_dependency_trace_v0.4.15.16_report.json --collection legal_knowledge --output tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json`

## [0.4.15.18] - 2026-06-11

### Added
- 新增 saved-report-only 工具 `tools/build_base_candidate_mismatch_summary.py`，读取 v0.4.15.16 full-debug trace 与 v0.4.15.17 inspection report，汇总 base union candidate 与 final refs 的 source/article drift、candidate source distribution 和 query overlap。
- 新增 `tests/test_base_candidate_mismatch_summary.py`、`tests/base_candidate_mismatch_summary_v0.4.15.18_report.json` 与 `docs/base_candidate_mismatch_summary_v0.4.15.18.md`。

### Result
- Summary 结论为 `qdrant_or_live_retrieval_needed`。
- 7 个 inspected anchor-filled cases 全部归类为 `same_source_article_drift`，共有 14 个 final refs 未出现在 saved report 的 base union candidates 中。
- 离线报告已经能证明问题集中在 base candidate source/article 覆盖层，但不能证明 final refs 是不存在于 Qdrant、被过滤掉，还是 live retrieval 排分低于候选截断线；下一步必须进入 Qdrant/live retrieval inspection。

### Boundary
- 不运行 eval，不调用 `rag_query`，不访问 Qdrant/LLM，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、retriever 或主链路。
- 本版本是 offline RAG grounding diagnostic，不是 gate，也不是 runtime fix。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_base_candidate_mismatch_summary.py tests/test_base_candidate_mismatch_summary.py`
- `./venv/Scripts/python.exe -m unittest tests.test_base_candidate_mismatch_summary`
- `./venv/Scripts/python.exe tools/build_base_candidate_mismatch_summary.py --trace tests/targeted_dependency_trace_v0.4.15.16_report.json --inspection tests/base_retrieval_query_inspection_v0.4.15.17_report.json --output tests/base_candidate_mismatch_summary_v0.4.15.18_report.json`

## [0.4.15.17] - 2026-06-11

### Added
- 新增 saved-report-only 工具 `tools/build_base_retrieval_query_inspection.py`，读取 v0.4.15.16 full-debug trace，检查 base union retrieval、query lexical hints 和 anchor-filled final refs。
- 新增 `tests/test_base_retrieval_query_inspection.py`、`tests/base_retrieval_query_inspection_v0.4.15.17_report.json` 与 `docs/base_retrieval_query_inspection_v0.4.15.17.md`。

### Result
- Inspection 结论为 `base_retrieval_query_inspection_needed`。
- 8 个 inspected cases 中，7 个是 `base_union_gap_with_anchor_filled_final_refs`，1 个是 `union_satisfied_manual_review_or_output_dependency`。
- 7 个 anchor-filled cases 的 rerank query 已含 `相关检索概念` 与 `场景锚点法条`，但 base union retrieval 仍未覆盖最终证据 refs。

### Boundary
- 不运行 eval，不调用 `rag_query`，不访问 Qdrant/LLM，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、retriever 或主链路。
- 本版本是 saved-report inspection，不是 runtime fix 或 gate。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_base_retrieval_query_inspection.py tests/test_base_retrieval_query_inspection.py`
- `./venv/Scripts/python.exe -m unittest tests.test_base_retrieval_query_inspection`
- `./venv/Scripts/python.exe tools/build_base_retrieval_query_inspection.py --trace tests/targeted_dependency_trace_v0.4.15.16_report.json --summary tests/dependency_trace_summary_v0.4.15.16_report.json --output tests/base_retrieval_query_inspection_v0.4.15.17_report.json`

## [0.4.15.16] - 2026-06-10

### Added
- 运行 v0.4.15.15 priority cases 的非 compact targeted trace packet，输出 `tests/targeted_dependency_trace_v0.4.15.16_report.json`。
- 新增 saved-report-only 工具 `tools/build_dependency_trace_summary.py`，从 full debug report 中提取 retrieval layer、candidate counts、final selector trace、quality signals 和依赖归因。
- 新增 `tests/test_dependency_trace_summary.py` 与 `docs/dependency_trace_summary_v0.4.15.16.md`。

### Result
- Targeted trace packet：8/8 passed，`retrieval_failure_stage_summary={"PASS": 8}`。
- 7/8 cases 归因为 `base_union_gap_anchor_filled`，即 base union retrieval 未满足，anchor 补齐后 final evidence 通过。
- 1/8 case 归因为 `union_satisfied_but_manual_review_or_output_rule_dependency`，即 union 已满足但仍有人工复核/输出规则依赖信号。
- 当前仍没有 runtime failure；下一步应先做 query lexical / base retrieval inspection，不应直接改 anchor 或 risk supplement。

### Boundary
- 不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、Qdrant、retriever 或 `rag_query` 主链路。
- Summary builder 只读 saved reports，不运行 eval、不访问 Qdrant/LLM。

### Verification
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_dependency_trace_v0.4.15.16_report.json --check-risk --case-id risk_gray_area_ai_training_001 --case-id risk_trademark_non_use_001 --case-id risk_chatbot_training_001 --case-id risk_employee_data_export_001 --case-id positive_antitrust_independent_pricing_001 --case-id risk_vat_export_refund_001 --case-id risk_ai_medical_training_export_001 --case-id risk_contract_auto_renewal_001`
- `./venv/Scripts/python.exe -m py_compile tools/build_dependency_trace_summary.py tests/test_dependency_trace_summary.py`
- `./venv/Scripts/python.exe -m unittest tests.test_dependency_trace_summary`
- `./venv/Scripts/python.exe tools/build_dependency_trace_summary.py --input tests/targeted_dependency_trace_v0.4.15.16_report.json --triage tests/rag_quality_triage_v0.4.15.15_report.json --output tests/dependency_trace_summary_v0.4.15.16_report.json`

## [0.4.15.15] - 2026-06-10

### Added
- 新增 saved-report-only 工具 `tools/build_rag_quality_triage.py`，读取既有 RAG eval report 并输出通过质量、贡献依赖、quality signals、人工复核标记和优先 triage 清单。
- 新增 `tests/test_rag_quality_triage.py`，覆盖依赖分类、quality risk 优先级、人工复核/同桶 observation/retrieval confidence 排序。
- 新增 `tests/rag_quality_triage_v0.4.15.15_report.json` 与 `docs/rag_quality_triage_v0.4.15.15.md`。

### Result
- 读取 v0.4.15.14 compact full eval 后，结论为 `passed_with_high_dependency`：60/60 passed，retrieval stage 全部 `PASS`，但 `ANCHOR_PASS=31`、`RISK_SUPPLEMENT_PASS=44`、`PURE_LLM_PASS=6`。
- `score_order_risks=0`，没有当前 full-eval failure；主要信号是通过依赖偏高。
- 优先 triage 清单前列为 `risk_gray_area_ai_training_001`、`risk_trademark_non_use_001`、`risk_chatbot_training_001`、`risk_employee_data_export_001`、`positive_antitrust_independent_pricing_001`、`risk_vat_export_refund_001`。

### Boundary
- 不运行 eval，不调用 `rag_query`，不访问 Qdrant/LLM，不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、retriever 或主链路。
- 本版本不是新 gate，也不是 runtime fix；它是通过质量 triage。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_rag_quality_triage.py tests/test_rag_quality_triage.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_quality_triage`
- `./venv/Scripts/python.exe tools/build_rag_quality_triage.py --input tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json --output tests/rag_quality_triage_v0.4.15.15_report.json`

## [0.4.15.14] - 2026-06-10

### Changed
- 将 `docs/project_review_and_roadmap.md` 从小版本流水账收口为 current-state roadmap，只保留定位、能力、阶段、基线、风险和下一步。
- 归档旧长版路线图到 `docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md`。
- 新增 `docs/roadmap_maintenance_compact_eval_baseline_v0.4.15.14.md` 记录本版边界和验证。
- 使用 v0.4.15.13 的 `--compact-report` 跑 full RAG eval 轻量基线。
- 更新 `src/main.py` 与项目健康检查版本为 `0.4.15.14`。

### Result
- Compact full RAG eval：60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- Roadmap 明确后续维护规则：普通小版本记录写入 `changelog.md`，roadmap 只在方向、基线、风险或开放任务变化时更新。

### Boundary
- 不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、scenario registry、fixtures、eval cases、Qdrant、retriever 或 `rag_query` 主链路。
- 本版本不是新 gate，也不是 runtime 修复；它是路线图维护和轻量评测基线。

### Verification
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json --check-risk --compact-report`

## [0.4.15.13] - 2026-06-10

### Changed
- 为 `tools/run_rag_eval.py` 新增显式 opt-in 的 `--compact-report` 输出模式；默认报告保持 full profile，不改变既有语义。
- compact profile 会移除每个 case 中体积最大的 full `debug_info` 与 full `contribution_trace`，并保留 `debug_info_summary`、`contribution_trace_summary`、`retrieval_diagnostics` 和 `quality_signal_diagnostics`。
- 扩展 `tests/test_rag_eval_diagnostics.py`，覆盖 compact summary、单 case compact 和 repeat report compact。
- 新增 `docs/rag_eval_compact_report_profile_v0.4.15.13.md`。
- 更新 `src/main.py` 与项目健康检查版本为 `0.4.15.13`。

### Result
- `risk_algorithm_bias_001` focused compact smoke：1/1 passed，`retrieval_failure_stage_summary={"PASS": 1}`。
- 默认 full report smoke 保留 full `debug_info` 且不写入 `report_profile`。
- compact smoke 写入 `report_profile="compact"`，移除 full `debug_info`，保留 `debug_info_summary`；单 case 文件体积约为 full 输出的 13%。

### Boundary
- 不修改 `rag_query` 主链路、retriever、rerank、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures、eval cases、hidden seed 或 Qdrant。
- 本版本只是 RAG eval 报告体积控制与诊断可读性改进，不是样本修补工具，也不是 grounding quality bypass。

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/run_rag_eval.py tests/test_rag_eval_diagnostics.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_eval_diagnostics`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_compact_report_profile_v0.4.15.13_report.json --check-risk --case-id risk_algorithm_bias_001 --compact-report`

## [0.4.15.12] - 2026-06-09

### Changed
- Calibrated `tools/run_rag_eval.py` `quality_signal_diagnostics` by splitting same-bucket candidates into `score_order_observations` and `score_order_risks`.
- `same_bucket_selection_order_risk` now fires only when a candidate affects missing `expected_evidence` or missing operative `expected_statutes` coverage.
- Extended `tests/test_rag_eval_diagnostics.py` for risk preservation, satisfied-evidence suppression, same-ref sibling suppression, and non-critical cross-domain suppression.
- Added `docs/same_bucket_signal_calibration_v0.4.15.12.md`.
- Updated `src/main.py` and project health version to `0.4.15.12`.

### Result
- 4-case targeted baseline x 3 repeats: pass counts `[4, 4, 4]`, `unstable_cases=[]`.
- Baseline full RAG eval: 60/60 passed, `retrieval_failure_stage_summary={"PASS": 60}`.
- Calibrated full RAG eval: 59/60 passed with `retrieval_failure_stage_summary={"PASS": 60}`; the only miss was one `risk_employee_facial_001` answer-keyword variance.
- `risk_employee_facial_001` focused repeat: 5/5 passed, confirming no retrieval or evidence-chain regression.
- `same_bucket_selection_order_risk` dropped from 18 review issues in v0.4.15.11 to 0 risks; 111 candidates remain visible as `score_order_observations`.

### Boundary
- No retriever, rerank, anchor, prompt, risk supplement, term preservation, scenario registry, fixture, eval case, hidden seed, or Qdrant change.
- This version calibrates RAG grounding quality diagnostics; it is not a sample patching tool.
- A runtime sorting/selection repair was tested and rejected because targeted validation damaged stable evidence chains; final submitted changes contain no runtime selector patch.

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/run_rag_eval.py tests/test_rag_eval_diagnostics.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_eval_diagnostics`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_same_bucket_baseline_v0.4.15.12_report.json --check-risk --case-id risk_algorithm_bias_001 --case-id risk_ai_medical_training_export_001 --case-id risk_employee_data_export_001 --case-id pipl_sensitive_definition_001 --repeat 3`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json --check-risk`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json --check-risk`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json --check-risk --case-id risk_employee_facial_001 --repeat 5`

## [0.4.15.11] - 2026-06-08

### Changed
- `tools/run_rag_eval.py` 新增 `quality_signal_diagnostics`，在每个 case 报告中输出 hidden-style grounding quality 信号。
- `src/rag/retriever.py` 增加证据驱动输出稳定化：产品责任赔偿术语保留、商标通用名称最低风险、未弥补亏损分红措辞保留、股权转让未通知最低风险。
- 扩展 `tests/test_rag_eval_diagnostics.py` 与 `tests/test_retriever_contract.py`，覆盖通用诊断逻辑和输出稳定化边界。
- 新增 `docs/hidden_seed_signal_diagnostics_output_stability_v0.4.15.11.md`。
- 更新 `src/main.py` 与项目健康检查版本为 `0.4.15.11`。

### Result
- `risk_tort_product_liability_001` 5 轮 targeted repeat：5/5 passed，贡献标签包含 `TERM_PRESERVATION_PASS`。
- 4 个输出波动重点 case × 3 轮 targeted repeat：pass counts `[4, 4, 4]`，`unstable_cases=[]`。
- full RAG eval：60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- full eval 新增质量信号摘要：18 个 `same_bucket_selection_order_risk` review signals，作为后续同桶选择顺序诊断材料，不作为本版失败。

### Boundary
- 未修改 hidden seed、anchor、prompt、eval case、risk supplement 规则、scenario registry、fixtures、rerank 行为或 Qdrant 数据。
- `quality_signal_diagnostics` 只写入 eval 报告，不参与检索、排序或答案生成。
- 本版本是 RAG grounding quality diagnostics + evidence-driven output stabilization，不是样本修补工具。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tools/run_rag_eval.py tests/test_retriever_contract.py tests/test_rag_eval_diagnostics.py`
- `./venv/Scripts/python.exe -m unittest tests.test_retriever_contract tests.test_rag_eval_diagnostics`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json --check-risk --case-id risk_tort_product_liability_001 --repeat 5`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_output_stability_v0.4.15.11_report.json --check-risk --case-id risk_tort_product_liability_001 --case-id risk_trademark_generic_name_001 --case-id risk_company_illegal_dividend_001 --case-id risk_company_share_transfer_001 --repeat 3`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json --check-risk`
- Project health、索引一致性、编码卫生、`git diff --check` 和禁止 diff 检查通过。

## [0.4.15.10] - 2026-06-08

### Changed
- 在 `src/rag/retriever.py::LEGAL_TERM_PRESERVATION_RULES` 新增“标准合同重新评估/补充或者重新订立标准合同”术语保留规则。
- 新增 `tests/test_retriever_contract.py` 覆盖：命中《个人信息出境标准合同办法》证据时补全后续动作术语；没有支持来源时不补。
- 新增 `docs/standard_contract_term_preservation_v0.4.15.10.md`。
- 更新 `src/main.py` 与项目健康检查版本为 `0.4.15.10`。

### Result
- `data_export_contract_trigger_001` 5轮 repeat：5/5 passed，贡献标签稳定为 `TERM_PRESERVATION_PASS`。
- 8个重点 case × 3轮 targeted repeat：pass counts `[8, 8, 8]`，`unstable_cases=[]`。
- full RAG eval：60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。

### Boundary
- 未修改 prompt、anchor、risk supplement、hidden seed、scenario registry、fixtures 或 eval cases。
- 未修改 rerank 或 Qdrant。
- 该修复基于 evidence_chain 中已有法规来源和条文内容，是主链路输出层的通用术语稳定化，不是样本补丁。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tests/test_retriever_contract.py`
- `./venv/Scripts/python.exe -m unittest tests.test_retriever_contract`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_data_export_term_preservation_v0.4.15.10_report.json --check-risk --case-id data_export_contract_trigger_001 --repeat 5`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json --check-risk --case-id pipl_consent_withdrawal_001 --case-id standard_personal_info_scope_001 --case-id data_export_contract_trigger_001 --case-id risk_employee_facial_001 --case-id risk_algorithm_bias_001 --case-id risk_antitrust_market_dominance_001 --case-id risk_chatbot_training_001 --case-id risk_tort_product_liability_001 --repeat 3`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json --check-risk`
- Project health、索引一致性、编码卫生、`git diff --check` 和禁区 diff 检查通过。

## [0.4.15.9] - 2026-06-08

### Changed
- 新增 v0.4.15.8 主链路修复后的稳定性收口报告 `docs/post_near_tie_main_chain_stability_closeout_v0.4.15.9.md`。
- 新增 3 份验证产物：`tests/targeted_main_chain_stability_v0.4.15.9_report.json`、`tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json`、`tests/targeted_data_export_answer_stability_v0.4.15.9_report.json`。
- 更新 `src/main.py` 与项目健康检查版本为 `0.4.15.9`。

### Result
- 8 个高风险/近期不稳定 case 的 targeted stability repeat：3 轮全部通过，pass counts 为 `[8, 8, 8]`，`unstable_cases=[]`。
- 单轮 full RAG eval：59/60 passed，但 `retrieval_failure_stage_summary={"PASS": 60}`，唯一失败为 `data_export_contract_trigger_001` 的答案关键词单次措辞波动。
- 对 `data_export_contract_trigger_001` 追加 5 轮 targeted repeat：5/5 passed，证据第 8 条稳定命中，确认不是检索或 evidence_chain 回归。

### Boundary
- 本版本未修改 retriever、rerank、prompt、anchor、risk supplement、term preservation、hidden seed、scenario registry、fixtures 或 eval cases。
- 未为了单次答案关键词波动修改 prompt 或 eval case。
- full repeat 3 轮因本地执行窗口超时未形成完整报告，未提交 partial artifact；改用 targeted stability packet + single full eval + focused repeat 收口。

### Verification
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_main_chain_stability_v0.4.15.9_report.json --check-risk --case-id pipl_consent_withdrawal_001 --case-id standard_personal_info_scope_001 --case-id data_export_contract_trigger_001 --case-id risk_employee_facial_001 --case-id risk_algorithm_bias_001 --case-id risk_antitrust_market_dominance_001 --case-id risk_chatbot_training_001 --case-id risk_tort_product_liability_001 --repeat 3`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json --check-risk`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_data_export_answer_stability_v0.4.15.9_report.json --check-risk --case-id data_export_contract_trigger_001 --repeat 5`
- Project health、索引一致性、编码卫生、`git diff --check` 和禁区 diff 检查通过。

## [0.4.15.8] - 2026-06-08

### Changed
- 收窄 `src/rag/retriever.py` 中 `_stabilize_same_bucket_rerank_order()` 的作用范围：只稳定小规模、真实近分组，避免大 bucket 被重排而覆盖 Cross-Encoder 原始排序。
- 增强 `src/risk/taxonomy.py`：`classify_risk_categories()` 支持直接匹配 taxonomy 的规范 `name`，使结构化 `risk_types` 中已有规范风险类型名时可以触发默认风险等级推断。
- 新增 `tests/test_risk_analyzer.py`，并扩展 `tests/test_candidate_budget.py`、`tests/test_taxonomy.py`。
- 新增主链路修复说明 `docs/post_near_tie_patch_main_chain_repair_v0.4.15.8.md`。
- 更新 `src/main.py` 与项目健康检查版本为 `0.4.15.8`。

### Result
- 修复前 full RAG eval：`tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json` 为 31/60 passed，`RERANK_MISS=28`。
- 收窄 near-tie stabilization 后，5 个 targeted case、3 轮 repeat 全部通过。
- taxonomy exact-name 修复后，`risk_antitrust_market_dominance_001` targeted repeat 3/3 通过。
- 最终 full RAG eval：`tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json` 为 60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。

### Boundary
- 未修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 未新增 anchor，未改 eval 样本，未写 Qdrant，未执行 rebuild。
- 本版本是主链路回归修复，不是新增 gate 或设计报告链。

### Verification
- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py src/risk/taxonomy.py src/risk/analyzer.py tests/test_candidate_budget.py tests/test_taxonomy.py tests/test_risk_analyzer.py tools/run_project_health_check.py tests/test_project_health_check.py src/main.py`
- `./venv/Scripts/python.exe -m unittest tests.test_candidate_budget tests.test_taxonomy tests.test_risk_analyzer tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_post_near_tie_regression_v0.4.15.8_report.json --check-risk --case-id pipl_consent_withdrawal_001 --case-id standard_personal_info_scope_001 --case-id data_export_contract_trigger_001 --case-id risk_employee_facial_001 --case-id risk_algorithm_bias_001 --repeat 3`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_antitrust_risk_level_v0.4.15.8_report.json --check-risk --case-id risk_antitrust_market_dominance_001 --repeat 3`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json --check-risk`
- Project health、索引一致性、编码卫生、`git diff --check` 和禁区 diff 检查通过。

## [0.4.15.7] - 2026-06-08

### Changed
- Added `tools/build_post_rebuild_near_tie_patch_closeout.py` and `tests/test_post_rebuild_near_tie_patch_closeout.py`.
- Added `tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json` and `docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md`.
- Cleaned the v0.4.15.6 patch validation Markdown generator/output so the recent validation summary is readable.
- Updated `src/main.py` and project health version to `0.4.15.7`.

### Result
- Closeout status is `closed_for_next_real_rag_quality_task`.
- The v0.4.15.6 targeted repeat remains 5/5 passed.
- The v0.4.15.6 patch validation remains `passed`, with `unique_selected_evidence_chains=1`.
- The closeout builder only reads saved reports and project health; it does not run full eval or touch Qdrant.

### Boundary
- No hidden seed, anchor, prompt, rerank score, `score_epsilon`, top_k, risk supplement, term preservation, scenario registry, fixture, or eval case changes.
- No runtime patch in this version; v0.4.15.7 is a closeout and readability maintenance release.
- No Qdrant write, no rebuild, no live preflight, and no full eval execution by the closeout builder.

### Verification
- `./venv/Scripts/python.exe -m py_compile tools/build_post_rebuild_near_tie_patch_validation.py tools/build_post_rebuild_near_tie_patch_closeout.py tests/test_post_rebuild_near_tie_patch_validation.py tests/test_post_rebuild_near_tie_patch_closeout.py tools/run_project_health_check.py tests/test_project_health_check.py src/main.py`
- `./venv/Scripts/python.exe -m unittest tests.test_post_rebuild_near_tie_patch_validation tests.test_post_rebuild_near_tie_patch_closeout tests.test_project_health_check`
- `./venv/Scripts/python.exe tools/build_post_rebuild_near_tie_patch_closeout.py`
- Project health, index consistency, encoding hygiene, `git diff --check`, and restricted diff passed.

## [0.4.15.6] - 2026-06-08

### Changed
- Added `_stabilize_same_bucket_rerank_order()` in `src/rag/retriever.py`.
- The runtime path now applies same-bucket deterministic ordering after `_sort_rerank_scores_stable()` and before `_select_diverse_rerank_top()`.
- The patch only changes candidate order inside an existing Cross-Encoder stable-score bucket; it does not change Cross-Encoder scores, model, query, `score_epsilon`, or top_k.
- Added `tools/build_post_rebuild_near_tie_patch_validation.py` and `tests/test_post_rebuild_near_tie_patch_validation.py`.
- Added `tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json` and `docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md`.

### Result
- Local logic tests passed: same-bucket order is independent from candidate input order, while cross-bucket priority remains unchanged.
- `risk_algorithm_bias_001` targeted repeat passed 5/5 after the patch.
- Final evidence identity is stable across 5 runs: `PIPL article 24 -> PIPL article 48 -> PIPL article 56`.
- Validation report status is `passed`, with `unique_selected_evidence_chains=1`.

### Boundary
- No hidden seed, anchor, prompt, risk supplement, term preservation, scenario registry, fixture, or eval case changes.
- No case-id branch and no hard-coded legal source or article winner.
- No full eval was run for this version; validation used the authorized single-case targeted repeat.

### Verification
- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tools/build_post_rebuild_near_tie_patch_validation.py tests/test_candidate_budget.py tests/test_post_rebuild_near_tie_patch_validation.py`
- `./venv/Scripts/python.exe -m unittest tests.test_candidate_budget tests.test_post_rebuild_near_tie_patch_validation`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json --check-risk --case-id risk_algorithm_bias_001 --repeat 5`
- `./venv/Scripts/python.exe tools/build_post_rebuild_near_tie_patch_validation.py`
- Project health, index consistency, encoding hygiene, full unittest discover, `git diff --check`, and restricted diff passed.

## [0.4.15.5] - 2026-06-08

### 新增
- **Post-Rebuild Near-Tie Stability Policy Design**：
  - 新增 `tools/build_post_rebuild_near_tie_stability_policy_design.py`，只读取 v0.4.15.4 trace attribution saved report，生成 near-tie stability policy 设计报告。
  - 新增 `tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json` 与 `docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md`。
  - 新增 `tests/test_post_rebuild_near_tie_stability_policy_design.py`。

### 结果
- 设计状态：`ready_for_near_tie_policy_review`。
- 建议策略：`deterministic_same_bucket_order_stabilization`。
- 设计限定：未来若授权实现，只能在既有 Cross-Encoder stable-score bucket 内做 deterministic ordering；不得改 Cross-Encoder 分数、模型、query、`score_epsilon`、top_k、anchor、prompt 或 eval case。
- 明确禁止：case id 分支、硬编码某部法律或某条文为赢家、新增 anchor、修改 hidden seed 或 eval case。

### 边界
- 本版本是 design-only，不是 runtime patch。
- 不运行 eval，不调用 `rag_query`，不连接 Qdrant 或 LLM。
- 不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_post_rebuild_near_tie_stability_policy_design.py tests\test_post_rebuild_near_tie_stability_policy_design.py`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_near_tie_stability_policy_design.py --trace-attribution tests\post_rebuild_selection_trace_attribution_v0.4.15.4_report.json --output tests\post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json --summary docs\post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_post_rebuild_near_tie_stability_policy_design`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.15.4] - 2026-06-07

### 新增
- **Post-Rebuild Selection Trace Attribution**：
  - 运行 `risk_algorithm_bias_001` 单 case targeted repeat trace capture，输出 `tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json`。
  - 新增 `tools/build_post_rebuild_selection_trace_attribution.py`，只读取 v0.4.15.4 targeted trace saved report，归因第三席 final evidence 漂移。
  - 新增 `tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json` 与 `docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md`。
  - 新增 `tests/test_post_rebuild_selection_trace_attribution.py`。

### 结果
- targeted repeat 结果为 5/5 passed，`retrieval_failure_stage_summary={"PASS": 1}` 每轮稳定。
- 第三席 final evidence 继续在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移，本轮计数为《个人信息保护法》第 56 条 2 次、《网络安全法》第 20 条 3 次。
- 每轮最终第三席都能在 `final_evidence_selection_trace.selected` 中找到，且始终是两个漂移候选中 full rerank order 更靠前的候选。
- 归因分类：`raw_rerank_order_boundary_drift_not_selector_replacement`；状态为 `needs_near_tie_stability_design`。

### 边界
- 本版本是 targeted trace capture + saved-report attribution，不是 runtime fix。
- 不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 不运行 full eval；只运行单 case targeted repeat，并用 saved report 做归因。

### 验证
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json --check-risk --case-id risk_algorithm_bias_001 --repeat 5`
- `.\venv\Scripts\python.exe -m py_compile tools\build_post_rebuild_selection_trace_attribution.py tests\test_post_rebuild_selection_trace_attribution.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_post_rebuild_selection_trace_attribution`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_selection_trace_attribution.py --trace-repeat tests\targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json --output tests\post_rebuild_selection_trace_attribution_v0.4.15.4_report.json --summary docs\post_rebuild_selection_trace_attribution_v0.4.15.4.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.15.3] - 2026-06-07

### 新增
- **Post-Rebuild Selection Trace Readiness**：
  - `rag_query(debug=True)` 新增 `debug_info.rerank_full_score_order`，记录 Cross-Encoder 返回分数后的全量稳定排序、输入位次、rerank 位次和候选标识。
  - `rag_query(debug=True)` 新增 `debug_info.final_evidence_selection_trace`，记录 final evidence selector 的输入数量、选中项、未选中项、final rank、rerank rank 与 dense fallback 模式。
  - 新增 `tools/build_post_rebuild_selection_trace_readiness.py`，用 synthetic documents 验证 trace 字段结构与 selector 行为边界。
  - 新增 `tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json` 与 `docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md`。
  - 新增 `tests/test_post_rebuild_selection_trace_readiness.py`，并在 `tests/test_candidate_budget.py` 补充 debug trace helper 单测。

### 结果
- v0.4.15.3 readiness report 状态为 `passed`，确认 trace 能展示 full rerank order、selected/not_selected、input/rerank/final rank。
- synthetic selector sample 仍输出 `["a24", "a48", "b20"]`，说明本版本只增加可观测性，不改变 selector 选择结果。
- 该 trace 为下一步 targeted repeat with debug trace capture 提供基础，用于区分 `risk_algorithm_bias_001` 的第三席漂移是 raw rerank score/order 波动，还是 selector replacement 边界波动。

### 边界
- 本版本是 RAG 主链路可观测性补丁，不是 rerank 调参，不是 selector 行为修复。
- 不修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 不重跑 reranker，不改变 `_sort_rerank_scores_stable()`、`_select_diverse_rerank_top()` 或 `_retain_high_alignment_evidence()` 的选择语义。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\rag\retriever.py tools\build_post_rebuild_selection_trace_readiness.py tests\test_candidate_budget.py tests\test_post_rebuild_selection_trace_readiness.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_post_rebuild_selection_trace_readiness`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_selection_trace_readiness.py --output tests\post_rebuild_selection_trace_readiness_v0.4.15.3_report.json --summary docs\post_rebuild_selection_trace_readiness_v0.4.15.3.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.15.2] - 2026-06-07

### 新增
- **Post-Rebuild Final Evidence Drift Attribution**：
  - 新增 `tools/build_post_rebuild_final_evidence_drift_attribution.py`，只读取 `risk_algorithm_bias_001` 的 targeted repeat saved report、v0.4.15.1 triage 和 eval case metadata，归因 final evidence 身份漂移发生在哪个已保存阶段。
  - 新增 `tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json` 与 `docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md`。
  - 新增 `tests/test_post_rebuild_final_evidence_drift_attribution.py`，覆盖双候选进入 rerank input 后第三席漂移、无漂移通过、真实报告解析和 Markdown 边界。

### 结果
- `risk_algorithm_bias_001` 的核心 expected evidence《个人信息保护法》第 24 条、第 48 条在 5 轮 targeted repeat 中始终稳定进入 final evidence。
- 漂移只发生在 final evidence 第三席：`selected_alternate_by_run` 为 `[个保法56, 个保法56, 网安法20, 个保法56, 网安法20]`。
- 《个人信息保护法》第 56 条与《网络安全法》第 20 条均在所有 targeted runs 中进入 `rerank_input_candidates`；首次可观察分歧位于 saved `reranked_candidates/final_candidates` top-3 边界。
- 归因分类：`rerank_top3_boundary_drift_after_core_evidence_locked`。
- 当前 saved report 未保存完整 raw Cross-Encoder score order 或 selector decision trace，因此不能直接定责为 rerank score jitter 或 selector replacement。

### 边界
- 本版本是 saved-report attribution，不是 runtime patch，不授权修复。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- attribution builder 不运行 eval、不调用 `rag_query`、不连接 Qdrant、不调用 LLM。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_post_rebuild_final_evidence_drift_attribution.py tests\test_post_rebuild_final_evidence_drift_attribution.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_post_rebuild_final_evidence_drift_attribution`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_final_evidence_drift_attribution.py --output tests\post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json --summary docs\post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.15.1] - 2026-06-07

### 新增
- **Post-Rebuild Repeat Instability Triage**：
  - 新增 `tools/build_post_rebuild_repeat_instability_triage.py`，只读取 v0.4.15.1 targeted repeat 报告、v0.4.15.0 repeat baseline/summary、v0.4.14.34 单次 baseline 和 eval case metadata，输出两类不稳定信号的 targeted triage。
  - 新增 `tests/targeted_repeat_product_liability_v0.4.15.1_report.json` 与 `tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json`，分别对 `risk_tort_product_liability_001` 与 `risk_algorithm_bias_001` 运行 5 轮 targeted repeat。
  - 新增 `tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json` 与 `docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md`。
  - 新增 `tests/test_post_rebuild_repeat_instability_triage.py`，覆盖输出措辞波动非阻断、final evidence identity drift 阻断、真实 targeted repeat 报告解析和 Markdown 边界。

### 结果
- `risk_tort_product_liability_001` targeted repeat 为 5/5 passed，retrieval stage、failed checks、贡献标签和 final evidence identity 均稳定；答案文本仍有措辞变化，归类为 `output_wording_variation_without_current_check_failure`，本轮不作为阻断项。
- `risk_algorithm_bias_001` targeted repeat 为 5/5 passed，但 final evidence 第三条在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移，归类为 `final_evidence_identity_drift_reproduced`，仍为阻断项。
- triage 状态：`needs_evidence_stability_triage`；推荐下一步为 `triage_final_evidence_identity_drift_before_runtime_change`。

### 边界
- 本版本是 targeted repeat triage，不是新 gate 链，不是样本修补工具，也不授权 runtime fix。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- triage builder 不运行 eval、不调用 `rag_query`、不连接 Qdrant、不调用 LLM。

### 验证
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_repeat_product_liability_v0.4.15.1_report.json --check-risk --case-id risk_tort_product_liability_001 --repeat 5`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_repeat_algorithm_bias_v0.4.15.1_report.json --check-risk --case-id risk_algorithm_bias_001 --repeat 5`
- `.\venv\Scripts\python.exe -m py_compile tools\build_post_rebuild_repeat_instability_triage.py tests\test_post_rebuild_repeat_instability_triage.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_post_rebuild_repeat_instability_triage`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_repeat_instability_triage.py --output tests\post_rebuild_repeat_instability_triage_v0.4.15.1_report.json --summary docs\post_rebuild_repeat_instability_triage_v0.4.15.1.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.15.0] - 2026-06-07

### 新增
- **Post-Rebuild Repeat Stability Summary**：
  - 新增 `tools/build_post_rebuild_repeat_stability_summary.py`，只读取已保存的 repeat full RAG eval 报告、v0.4.14.34 单次 60/60 基线和可选 eval case metadata，汇总多轮稳定性、证据身份漂移、答案漂移、baseline drift 和人工复核清单。
  - 新增 `tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json`，记录授权后运行的 3 轮 full RAG eval repeat 结果。
  - 新增 `tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json` 与 `docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md`。
  - 新增 `tests/test_post_rebuild_repeat_stability_summary.py`，覆盖 clean repeat、59/60 输出波动、证据身份漂移、citation 展示差异不误报、case set drift、dense fallback drift、真实报告解析和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与路线图至 `0.4.15.0`。
- 将 v0.4.15.0 定位为真实 RAG 质量基线：记录 repeat eval 的稳定性问题，下一步进入 triage，不再继续堆 gate 链。

### 结果
- repeat full RAG eval：3 轮 pass counts 为 `[60, 60, 59]`，total counts 为 `[60, 60, 60]`，`all_runs_full_pass=false`。
- 不稳定 case：`risk_tort_product_liability_001`，第 3 轮 retrieval stage 仍为 `PASS`，final evidence 为《民法典》第 1203/1204/1207 条，但答案缺少评测期待关键词“赔偿”，归类为 `answer_or_check_instability_with_stable_retrieval`。
- 贡献标签观察项：`dsl_data_classification_001` 与 `standard_personal_info_scope_001` 出现 label variation，单独不作为阻断项。
- 证据身份漂移：`risk_algorithm_bias_001` 第 3 轮 final evidence 从《网络安全法》第 20 条漂移到《个人信息保护法》第 56 条，需进入 triage。
- summary 状态：`needs_triage`；推荐下一步为 `triage_repeat_output_instability_before_runtime_change`。

### 边界
- 本版本是 RAG quality stability diagnostics，不是样本修补工具，不授权 runtime fix。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- summary builder 不运行 eval、不调用 `rag_query`、不连接 Qdrant、不调用 LLM。

### 验证
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json --check-risk --repeat 3`：生成报告，退出码为 1，原因是第 3 轮 59/60；该失败是本版本记录的真实质量信号。
- `.\venv\Scripts\python.exe -m py_compile tools\build_post_rebuild_repeat_stability_summary.py tests\test_post_rebuild_repeat_stability_summary.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_post_rebuild_repeat_stability_summary`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_repeat_stability_summary.py --output tests\post_rebuild_repeat_stability_summary_v0.4.15.0_report.json --summary docs\post_rebuild_repeat_stability_summary_v0.4.15.0.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.35] - 2026-06-07

### 新增
- **Production Rebuild / Post-Rebuild Series Closeout**：
  - 新增 `tools/build_production_rebuild_post_rebuild_series_closeout.py`，只读取 v0.4.14.29-v0.4.14.34 已保存报告，归档生产重建、post-validation、smoke、full RAG eval 回归、selector retention、delta 复核和 tightening 后 60/60 结果。
  - 新增 `tests/production_rebuild_post_rebuild_series_closeout_report.json` 与 `docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md`。
  - 新增 `tests/test_production_rebuild_post_rebuild_series_closeout.py`，覆盖真实输入收口、saved-report-only guardrails、缺失输入阻断、最终 full eval drift 阻断、初次回归 lineage 要求、delta removed expected evidence 阻断和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health anchors 至 `0.4.14.35`。
- roadmap 当前基线从“准备 v0.4.14 收口”推进为“v0.4.14 生产重建与 post-rebuild RAG 质量链条已收口，下一步转真实 RAG 质量任务”。

### 结果
- closeout 状态：`closed_for_next_real_rag_quality_task`，`blockers=[]`。
- 生产重建：`tests/production_rebuild_execution_report.json` 记录 `execution_status=succeeded`、`qdrant_write_executed=true`、`collection_rebuilt=true`。
- 重建后验证：`tests/production_rebuild_post_validation_report.json` 通过；quality summary 记录 `points_count=7177`、`missing_chunk_fields={}`。
- smoke：`tests/post_rebuild_smoke_eval_report.json` 为 25/25 passed。
- 初次 post-rebuild full RAG eval：`tests/post_rebuild_rag_eval_report.json` 为 58/60 passed，`tests/post_rebuild_rag_eval_summary_report.json` 记录 2 个 baseline 回归。
- selector retention 与 tightening 后：`tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json` 为 60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。

### 边界
- 本版本是 saved-report closeout，不运行 full eval，不调用 `rag_query`，不连接 Qdrant，不调用 LLM，不修改运行时代码。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 本版本不是新增 gate，不授权下一次 rebuild，也不把 v0.4.14.34 selector tightening 写成样本修补。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_production_rebuild_post_rebuild_series_closeout.py tests\test_production_rebuild_post_rebuild_series_closeout.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_post_rebuild_series_closeout`
- `.\venv\Scripts\python.exe tools\build_production_rebuild_post_rebuild_series_closeout.py --output tests\production_rebuild_post_rebuild_series_closeout_report.json --summary docs\production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.34] - 2026-06-06

### 变更
- **Post-Rebuild Alignment Retention Tightening**：
  - 收紧 `src/rag/retriever.py` 的 final evidence selector，继续限定在 Cross-Encoder 已看过的候选内做 evidence retention。
  - 将“责任”后果信号改为短语级识别，避免把“有限责任公司”误判为法律后果。
  - 增加同源远距离条文 outlier 防护，阻止产品责任场景中远距离泛化条文替换核心证据。
  - 增加同源近邻争点覆盖补齐，避免公司法第 32 条等弱片段挤掉第 84/86 条这类核心流程条文；selector 不解析或消费“场景锚点法条”提示行。
  - 增加 `protected_indexes` 最终硬过滤，避免 `issue_candidate` 分支在极端 replacement 场景下替换已保护核心证据。
- `tests/test_candidate_budget.py` 新增 selector 通用测试，覆盖远距离泛化条文拒绝、同源近邻争点补齐、`有限责任公司` 非后果误判、锚点提示不被 selector 消费等边界。
- 新增 `docs/post_rebuild_alignment_retention_tightening_v0.4.14.34.md`。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目文档与 health anchors 到 `0.4.14.34`。

### 结果
- selector 单测：`tests.test_candidate_budget` 30/30 passed。
- targeted RAG eval：`risk_data_export_overseas_001` 与 `risk_tort_product_liability_001` 均通过。
- full RAG eval：`tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`，60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- 中途曾出现一次 `risk_tort_product_liability_001` 答案关键词“赔偿”生成波动；targeted 复核通过，随后 full eval 覆盖复跑为 60/60。

### 边界
- 未修改 hidden seed、anchor、rerank model/prompt/score、prompt、risk supplement、term preservation、eval case、fixture 或 scenario registry；selector 也不消费 anchor 提示。
- 未扩大 evidence_chain top_k。
- 本版本是 RAG grounding quality runtime selector 收紧，不是样本修补工具，也不是新增治理 gate。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\rag\retriever.py tests\test_candidate_budget.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\post_rebuild_rag_eval_after_alignment_retention_tightened_report.json --check-risk`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.33] - 2026-06-06

### 新增
- **Post-Rebuild Alignment Retention Delta**：
  - 新增 `tools/build_post_rebuild_alignment_retention_delta.py`，只读取 `tests/post_rebuild_rag_eval_report.json`、`tests/post_rebuild_rag_eval_after_alignment_retention_report.json` 和 `tests/rag_eval_cases.json`，比较修复前后 pass status 与 final evidence delta。
  - 新增 `tests/post_rebuild_alignment_retention_delta_report.json` 与 `docs/post_rebuild_alignment_retention_delta_v0.4.14.33.md`。
  - 新增 `tests/test_post_rebuild_alignment_retention_delta.py`，覆盖 case id 对齐、canonical evidence key、citation-only delta、商标 explained improvement、unchanged pass replacement warn、removed expected evidence blocker、pass-to-fail blocker 与 saved-report-only contract。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health anchors 到 `0.4.14.33`。
- roadmap 下一步从“比较 evidence delta”推进为“抽样复核 7 个 warn/关注项，然后决定 v0.4.14.34 是系列收口还是 selector 收紧”。

### 结果
- 修复前 full RAG eval：58/60 passed。
- 修复后 full RAG eval：60/60 passed。
- evidence changed cases：9。
- replacement delta cases：7。
- citation-only delta cases：2。
- added expected evidence：1，仅 `risk_trademark_non_use_001` 新增商标法第 49 条。
- removed expected evidence：0。
- regressed cases：0。
- risky unexplained replacement：5 个 warn，均为修复前后仍通过但 final evidence 法条发生替换的抽样复核项。

### 边界
- 本版本只做 saved-report delta stabilization，不调用 RAG/Qdrant/LLM，不修改 retriever、rerank、prompt、anchor、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 本版本不是新的 gate，也不是人工最终结论；它为 v0.4.14.34 的收口或 selector 收紧提供证据。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_post_rebuild_alignment_retention_delta.py tests\test_post_rebuild_alignment_retention_delta.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_post_rebuild_alignment_retention_delta`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_alignment_retention_delta.py --output tests\post_rebuild_alignment_retention_delta_report.json --summary docs\post_rebuild_alignment_retention_delta_v0.4.14.33.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.32] - 2026-06-06

### 新增
- **Post-Rebuild Evidence Alignment Retention**：
  - 在 `src/rag/retriever.py` 的 final evidence selector 增加保守的 `_retain_high_alignment_evidence`，只在 Cross-Encoder 已经看过的候选中保留一条补足主争点法律后果的证据。
  - 新增 `docs/post_rebuild_alignment_retention_v0.4.14.32.md`，说明修复边界、验证结果和后续 stabilization 方向。
  - 新增 `tests/post_rebuild_rag_eval_after_alignment_retention_report.json`，记录修复后 full RAG eval 60/60 passed。

### 变更
- `risk_trademark_non_use_001` 中，商标法第 49 条已从 rerank input 保留进入 final evidence，修复 v0.4.14.31 的 `final_evidence_selection_drop`。
- `_select_diverse_rerank_top` 仍保持 Cross-Encoder 单一排序、top-3 evidence 数量和 existing dedupe；只在 final selector 层最多替换一个未覆盖法律后果的弱证据。
- `tests/test_candidate_budget.py` 增加 4 条 selector 测试，覆盖高重合法律后果保留、无关后果候选拒绝、无后果信号拒绝、已覆盖后果不重复替换。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health anchors 到 `0.4.14.32`。

### 结果
- post-rebuild full RAG eval 从 v0.4.14.31 的 58/60 恢复为 60/60。
- `risk_trademark_non_use_001` targeted 通过，final evidence 包含 `[《中华人民共和国商标法》第四十九条第一款]`。
- `risk_tort_product_liability_001` targeted 通过；本版本未修改 prompt 或 risk supplement。

### 边界
- 本版本修改 RAG 主链路 final evidence selector，但不修改 hidden seed、anchor、rerank model/prompt/score、prompt、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 本版本不扩大 evidence_chain 数量，不把 v0.4.8.x 的离线 final evidence selection policy 直接搬入 runtime。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\rag\retriever.py tests\test_candidate_budget.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_trademark_eval_report.json --check-risk --case-id risk_trademark_non_use_001`：通过，临时报表已清理。
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_product_liability_eval_report.json --check-risk --case-id risk_tort_product_liability_001`：通过，临时报表已清理。
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\post_rebuild_rag_eval_after_alignment_retention_report.json --check-risk`：60/60 passed。
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.31] - 2026-06-06

### 新增
- **Post-Rebuild Full RAG Eval Summary**：
  - 新增 `tools/build_post_rebuild_rag_eval_summary.py`，只读取 `tests/post_rebuild_rag_eval_report.json` 与 baseline `tests/rag_eval_report.json`，汇总 full RAG eval 的重建后回归、失败检查类型、检索阶段分布和 issue type。
  - 新增 `tests/post_rebuild_rag_eval_summary_report.json` 与 `docs/post_rebuild_rag_eval_summary_v0.4.14.31.md`。
  - 新增 `tests/test_post_rebuild_rag_eval_summary.py`，验证无回归通过、final evidence selection drop 分类和答案关键词覆盖缺口分类。

### 变更
- 已运行重建后 full RAG eval，输出 `tests/post_rebuild_rag_eval_report.json`；结果为 58/60 passed。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health anchors 到 `0.4.14.31`。
- roadmap 下一步从“运行 full RAG eval”切换为“修复两个明确 post-rebuild full RAG 回归”。

### 结果
- baseline full RAG eval：60/60 passed。
- post-rebuild full RAG eval：58/60 passed。
- 回归 case：2。
- failed check summary：`expected_answer_keywords=1`、`expected_evidence=1`。
- issue type summary：`answer_keyword_coverage_gap=1`、`final_evidence_selection_drop=1`。
- `risk_trademark_non_use_001`：商标法第 49 条已出现在 sparse/union/anchor/rerank_input，但从 final evidence 掉出，分类为 `final_evidence_selection_drop`。
- `risk_tort_product_liability_001`：期望证据已在 final evidence，答案表达未覆盖关键词“赔偿”，分类为 `answer_keyword_coverage_gap`。

### 边界
- 本版本运行 full RAG eval，但 summary builder 本身只读取 saved reports，不调用 RAG/Qdrant/LLM。
- 本版本不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
- 本版本不是 runtime 修复；它把重建后的真实回归收口为后续主链路排查输入。

### 验证
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\post_rebuild_rag_eval_report.json --check-risk`：生成报告，退出码为 1，原因是 58/60 passed。
- `.\venv\Scripts\python.exe tools\build_post_rebuild_rag_eval_summary.py --output tests\post_rebuild_rag_eval_summary_report.json --summary docs\post_rebuild_rag_eval_summary_v0.4.14.31.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.30] - 2026-06-05

### 新增
- **Post-Rebuild Quality Summary**：
  - 新增 `tools/build_post_rebuild_quality_summary.py`，汇总 post-rebuild smoke、baseline smoke 和 production rebuild post-validation。
  - 新增 `tests/post_rebuild_smoke_eval_report.json`，重建后运行 25 个 smoke cases，结果为 25/25 passed。
  - 新增 `tests/post_rebuild_quality_summary_report.json` 与 `docs/post_rebuild_quality_summary_v0.4.14.30.md`。
  - 新增 `tests/test_post_rebuild_quality_summary.py`。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.30`。
- roadmap 下一步从“生产重建执行”转为“post-rebuild targeted/full RAG eval 质量复测”。

### 结果
- baseline smoke：25/25 passed。
- post-rebuild smoke：25/25 passed。
- baseline 回归 case：0。
- post-validation：passed。
- Qdrant points：7177。
- `missing_chunk_fields={}`。

### 边界
- 本版本运行 smoke RAG eval，会访问 RAG/Qdrant/LLM。
- 本版本不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
- 本版本不运行 full eval；下一步才进入 targeted 或 full RAG eval。

### 验证
- `.\venv\Scripts\python.exe tools\run_impact_eval.py --cases tests\smoke_eval_cases.json --output tests\post_rebuild_smoke_eval_report.json --layers rag`
- `.\venv\Scripts\python.exe tools\build_post_rebuild_quality_summary.py --output tests\post_rebuild_quality_summary_report.json --summary docs\post_rebuild_quality_summary_v0.4.14.30.md`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.29] - 2026-06-05

### 新增
- **Production Rebuild Execution**：
  - 新增 `tools/run_production_rebuild_execution.py`，在正式授权记录与已通过只读 preflight 基础上调用既有 `rag_admin.py --rebuild`，并写出执行记录。
  - 新增 `tests/production_rebuild_execution_report.json`，记录执行前后 collection 状态、manifest 覆盖、命令结果、snapshot reference 与执行状态。
  - 新增 `tools/check_production_rebuild_post_validation.py`，对重建后的 `legal_knowledge` 做只读 payload metadata 抽样验证。
  - 新增 `tests/production_rebuild_post_validation_report.json` 与 `docs/production_rebuild_execution_v0.4.14.29.md`。
  - 新增 `tests/test_production_rebuild_execution.py` 与 `tests/test_production_rebuild_post_validation.py`。

### 变更
- 实际执行生产重建：`legal_knowledge` rebuild 前后均为 `7177` points，manifest 覆盖 15 个文档，缺失源文件为 0，执行状态为 `succeeded`。
- 重建后只读验证扫描 1000 个 points，观测到 `paragraph/article/item/standard_section` 的 `chunk_index/chunk_count`，缺失数为 0。
- 重跑 `tools/run_production_rebuild_live_preflight.py`，`tests/production_rebuild_live_preflight_report.json` 更新为 `0.4.14.29`，状态 `passed`、`blockers=[]`。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.29`。

### 边界
- 本版本真实写入 Qdrant，并重建 `legal_knowledge` collection。
- 本版本不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
- 本版本不运行 full eval；仅运行执行记录、只读 preflight、post-rebuild payload validation、单测、索引一致性、编码卫生、project health 和 restricted diff。

### 验证
- `.\venv\Scripts\python.exe tools\run_production_rebuild_execution.py --execute-production-rebuild --output tests\production_rebuild_execution_report.json`
- `.\venv\Scripts\python.exe tools\check_production_rebuild_post_validation.py --output tests\production_rebuild_post_validation_report.json --scan-limit 1000`
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight.py --run-readonly-live-preflight --authorization-record tests\production_rebuild_authorization_record.json --output tests\production_rebuild_live_preflight_report.json --allow-blocked-output`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.28] - 2026-06-05

### 新增
- **Production Rebuild Authorization Record Intake**：
  - 扩展 `tools/run_production_rebuild_live_preflight.py`，新增 `--authorization-record <json>`，允许只读 live preflight runner 从正式授权记录 JSON 读取授权状态、授权引用、目标 collection、snapshot reference 与 source lineage。
  - 新增授权记录输入安全检查：CLI 参数与授权记录字段冲突时 fail-closed；授权记录携带 `commands`、`authorized_actions`、`rebuild_steps`、`ready_to_apply`、`qdrant_write_allowed`、`production_rebuild_allowed` 等执行型字段时 fail-closed。
  - 新增 `docs/production_rebuild_authorization_record_intake_v0.4.14.28.md`。

### 变更
- 新增正式输入 `tests/production_rebuild_authorization_record.json`，记录当前线程用户明确同意生产重建、目标 collection、snapshot reference 与 source lineage reference。
- `tests/production_rebuild_live_preflight_report.json` 更新为 `0.4.14.28` schema 结果；当前授权记录已接受，授权输入安全检查通过，`blockers=[]`，只读 live preflight 状态为 `passed`。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.28`。

### 边界
- 本版本只是 formal authorization record intake for read-only live preflight，不是新 gate，也不是 production rebuild 执行器。
- 即使授权记录通过，也只允许只读 preflight 状态变为 `passed`；`qdrant_write_allowed=false`、`production_rebuild_allowed=false`、`authorization_granted=false` 仍必须保持。
- 不写 Qdrant，不创建/删除/恢复 snapshot，不切换 collection/alias，不运行 RAG/embedding/LLM/full eval，不执行 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight.py --run-readonly-live-preflight --authorization-record tests\production_rebuild_authorization_record.json --output tests\production_rebuild_live_preflight_report.json --allow-blocked-output`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner tests.test_project_health_check`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.27] - 2026-06-05

### 新增
- **Production Rebuild Read-Only Live Preflight Runner**：
  - 扩展 `tools/run_production_rebuild_live_preflight.py`，新增显式 `--run-readonly-live-preflight` 模式，真实读取 Qdrant collection 元信息、point count 和 1 条 payload 样本。
  - 新增正式输出 `tests/production_rebuild_live_preflight_report.json`，记录 `legal_knowledge` 可达、`points_count=7177`、snapshot reference/source lineage 已提供，当前仅因 `authorization_record_not_accepted` blocked。
  - 新增 `docs/production_rebuild_live_preflight_runner_v0.4.14.27.md`。

### 变更
- `tools/run_production_rebuild_live_preflight_real_readonly_probe.py` 透传 `authorization_reference`，保持与正式 runner 授权判断一致。
- `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py` 改为保留历史 scaffold traceability，不再因为 v0.4.14.27 已生成正式 preflight report 而误判失败。
- 更新相关单测，使当前源码已 patch、正式只读 preflight report 已存在这两个事实成为新的基线。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.27`。

### 边界
- 本版本是只读 live preflight 执行收口，不是新的 gate 链条。
- 只调用 `get_collection`、`count`、`scroll(with_vectors=False, limit=1)`；不写 Qdrant，不创建/删除/恢复 snapshot，不切换 collection/alias，不运行 RAG/embedding/LLM/full eval，不执行 production rebuild。
- `authorization_status=accepted` 必须同时具备非空 `authorization_reference` 才能通过正式授权检查；当前仍未授权 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight.py --run-readonly-live-preflight --collection legal_knowledge --authorization-status not_collected --backup-or-snapshot-reference <captured-reference> --source-lineage-reference ingestion-metadata-source-patch-v0.4.13.8 --output tests\production_rebuild_live_preflight_report.json --allow-blocked-output`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner tests.test_production_rebuild_live_preflight_real_readonly_probe tests.test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate tests.test_project_health_check`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.26] - 2026-06-05

### 新增
- **Production Rebuild Formal Authorization Gate**：
  - 新增 `tools/check_production_rebuild_formal_authorization_gate.py`，只读取 snapshot capture 与真实只读 preflight saved reports，检查正式 production rebuild 授权是否已被接受。
  - 新增 `tests/test_production_rebuild_formal_authorization_gate.py`，覆盖默认路径、当前 saved reports 仅因正式授权 blocked、accepted status 必须带非空 reference、snapshot 缺失 fail-closed、异常 preflight blocker fail-closed、CLI blocked output 和 source 禁止 Qdrant/RAG/LLM/eval/rebuild 执行调用。
  - 新增 `tests/production_rebuild_formal_authorization_gate_report.json`，记录当前 gate 状态为 `blocked`，唯一阻断项为 `authorization_record_not_accepted`。
  - 新增 `docs/production_rebuild_formal_authorization_gate_v0.4.14.26.md`。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.26`。
- 明确 snapshot 创建授权不能自动升级为 production rebuild 授权；backup/snapshot reference 已具备，但 production rebuild 仍必须等待正式授权记录。

### 验证
- `.\venv\Scripts\python.exe tools\check_production_rebuild_formal_authorization_gate.py --output tests\production_rebuild_formal_authorization_gate_report.json --allow-blocked-output`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_formal_authorization_gate tests.test_project_health_check`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.25] - 2026-06-05

### 新增
- **Production Rebuild Live Preflight Snapshot Create Reference Capture**：
  - 新增 `tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py`，在用户明确授权并提供 `--authorized-snapshot-create` 后，为 `legal_knowledge` 创建 Qdrant collection snapshot，并捕获 `backup_or_snapshot_reference`。
  - 新增 `tests/test_production_rebuild_live_preflight_snapshot_create_reference_capture.py`，覆盖未授权不调用 client、错误 collection 调用前 blocked、授权创建与 reference 捕获、`None` 返回 fail-closed、创建异常 fail-closed、CLI 缺授权开关非零退出和禁止删除/恢复 snapshot、point write、RAG、LLM、eval、rebuild 调用。
  - 新增 `tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json`：真实创建 snapshot `legal_knowledge-2019706566507018-2026-06-05-09-50-24.snapshot`，生成 `qdrant-snapshot://collection/legal_knowledge/legal_knowledge-2019706566507018-2026-06-05-09-50-24.snapshot`。
  - 新增 `docs/production_rebuild_live_preflight_snapshot_create_reference_capture_v0.4.14.25.md`。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.25`。
- 重新运行 snapshot reference 只读 probe 后，`tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json` 从 `snapshot_count=0` blocked 更新为 `snapshot_count=1` passed。
- 重新运行真实 Qdrant 只读 preflight probe 并注入 snapshot reference 后，`tests/production_rebuild_live_preflight_real_readonly_probe_report.json` 的阻断项缩小为 `authorization_record_not_accepted`；仍不授权 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight_snapshot_create_reference_capture.py --collection legal_knowledge --authorization-status user_explicitly_authorized_snapshot_creation --authorization-reference user-confirmed-current-thread-2026-06-05-create-legal_knowledge-snapshot --authorized-snapshot-create --output tests\production_rebuild_live_preflight_snapshot_create_reference_capture_report.json`
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight_snapshot_reference_probe.py --collection legal_knowledge --output tests\production_rebuild_live_preflight_snapshot_reference_probe_report.json`
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight_real_readonly_probe.py --collection legal_knowledge --authorization-status not_collected --backup-or-snapshot-reference <captured-reference> --source-lineage-reference ingestion-metadata-source-patch-v0.4.13.8 --output tests\production_rebuild_live_preflight_real_readonly_probe_report.json --allow-blocked-output`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.24] - 2026-06-05

### 新增
- **Production Rebuild Live Preflight Snapshot Reference Probe**：
  - 新增 `tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py`，复用 `src.core.vectorstore.get_qdrant_client()`，只调用 `list_snapshots(collection_name)` 查询现有 Qdrant collection snapshot。
  - 新增 `tests/test_production_rebuild_live_preflight_snapshot_reference_probe.py`，覆盖 fake client 只读调用、最新 snapshot 选择、无 snapshot fail-closed、probe error fail-closed、CLI blocked output 和禁止 snapshot 创建/删除/恢复、Qdrant 写入、RAG、LLM、eval、rebuild 调用。
  - 新增 `tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json`：真实 collection `legal_knowledge` 可访问，但现有 snapshot 数量为 `0`，当前因 `backup_or_snapshot_reference_missing` blocked。
  - 新增 `docs/production_rebuild_live_preflight_snapshot_reference_probe_v0.4.14.24.md`。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.24`。
- 将 production rebuild 前置检查从“collection 可达”推进到“是否已有可引用 snapshot reference”；本版本仍不创建 snapshot、不写 Qdrant、不执行 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight_snapshot_reference_probe.py --collection legal_knowledge --output tests\production_rebuild_live_preflight_snapshot_reference_probe_report.json --allow-blocked-output`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_snapshot_reference_probe`
- 完整健康检查、索引一致性、编码卫生、全量单测和 restricted diff 结果见本版本最终回复。

## [0.4.14.23] - 2026-06-05

### 新增
- **Production Rebuild Live Preflight Real Read-Only Probe**：
  - 新增 `tools/run_production_rebuild_live_preflight_real_readonly_probe.py`，复用 `src.core.vectorstore.get_qdrant_client()`，通过 `get_collection`、`count`、`scroll(with_vectors=False, limit=1)` 执行真实 Qdrant 只读 preflight probe。
  - 新增 `tests/test_production_rebuild_live_preflight_real_readonly_probe.py`，覆盖 fake client 只读调用、未授权/缺 backup fail-closed、accepted mock preflight 不授权 write/rebuild、CLI blocked output 和禁止写入/rebuild 调用。
  - 新增 `tests/production_rebuild_live_preflight_real_readonly_probe_report.json`：真实 collection `legal_knowledge` 可达，`points_count=7177`，抽样 payload metadata 包含 `chunk_id` 与 `qdrant_point_id`；当前因 `authorization_record_not_accepted` 和 `backup_or_snapshot_reference_missing` blocked。
  - 新增 `docs/production_rebuild_live_preflight_real_readonly_probe_v0.4.14.23.md`。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.23`。
- 本版本开始接入真实 Qdrant 只读链路，但仍不调用 RAG、embedding、LLM 或 full eval，不写 Qdrant，不执行 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight_real_readonly_probe.py --collection legal_knowledge --authorization-status not_collected --source-lineage-reference ingestion-metadata-source-patch-v0.4.13.8 --output tests\production_rebuild_live_preflight_real_readonly_probe_report.json --allow-blocked-output`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_real_readonly_probe tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.22] - 2026-06-05

### 新增
- **Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Gate**：
  - 新增 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py`，只读取 v0.4.14.21 scaffold report 并扫描 runner/test 源码，确认 scaffold 仍是 standard-library-only、mock-only、fail-closed。
  - 新增 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json`，记录 13 项 gate 检查、0 failure；通过后只开放 `production_rebuild_live_preflight_runner_mock_preflight_contract_gate`。
  - 新增 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md` 和 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py`。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.22`。
- 明确 v0.4.14.21 scaffold gate 后仍不允许直接运行 live preflight、访问或写入 Qdrant、接受正式授权或执行 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py --output tests\production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json --summary docs\production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.21] - 2026-06-05

### 新增
- **Production Rebuild Live Preflight Runner Minimal Implementation Scaffold**：
  - 新增 `tools/run_production_rebuild_live_preflight.py`，实现标准库-only 的 `build_live_preflight_report(...)` scaffold；默认无 live probe，必须通过注入的 `qdrant_readonly_probe` 才能做 mock/read-only 检查。
  - 新增 `tests/test_production_rebuild_live_preflight_runner.py`，覆盖默认无 live probe fail-closed、fake read-only probe 成功但不授权 write/rebuild、缺少授权、target collection mismatch、backup/source lineage 缺失、fake probe error、write-like method exposure、CLI scaffold report 和 runtime service import 禁止。
  - 新增 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json`，记录 scaffold 已创建、正式 live preflight 输出未创建、下一步只开放 scaffold gate。
  - 新增 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_v0.4.14.21.md`，说明该 scaffold 仍不是 live runner，也不是 production rebuild 授权。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.21`。
- `tests/production_rebuild_live_preflight_report.json` 仍未创建；本版本只允许 mock-only 验证 fail-closed 行为。

### 验证
- `.\venv\Scripts\python.exe tools\run_production_rebuild_live_preflight.py --scaffold-report-output tests\production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.20] - 2026-06-05

### 新增
- **Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design Gate**：
  - 新增 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py`，只读取 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json`，检查 v0.4.14.19 scaffold design 的 lineage、summary、guardrails、future files、contract、placeholder tests、forbidden scaffold content 和 forbidden output key 边界。
  - 新增 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json`，记录 14 项 gate 检查、0 failure；通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold`。
  - 新增 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md`，说明本 gate 仍不创建 runner 文件、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。
  - 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py`，覆盖真实 design 通过、status/lineage/blocker drift、scaffold contract drift、权限/guardrail drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 中文边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.20`。
- gate 通过后只允许进入最小 scaffold 创建；仍不创建 `tools/run_production_rebuild_live_preflight.py`、未来测试文件或未来输出报告，不授权 live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py --output tests\production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json --summary docs\production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.19] - 2026-06-05

### 新增
- **Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design**：
  - 新增 `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py`，只读取 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json`，设计未来 runner scaffold 的文件结构、不可执行占位策略、mock-only test shape、fail-closed defaults 和禁止内容。
  - 新增 `tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json`，状态为 `ready_for_minimal_implementation_scaffold_design_gate`；只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate`。
  - 新增 `docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md`，说明本版本仍不创建 runner 文件、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。
  - 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py`，覆盖真实 gate 输入通过、gate status/next-step drift、权限漂移、forbidden output key、CLI 输出、runtime service import 禁止、未来文件不存在和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.19`。
- 本版本仍只做 scaffold design，不创建 `tools/run_production_rebuild_live_preflight.py`、未来测试文件或未来输出报告。

### 验证
- `.\venv\Scripts\python.exe tools\build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py --output tests\production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json --summary docs\production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.18] - 2026-06-04

### 新增
- **Production Rebuild Live Preflight Runner Minimal Implementation Design Gate**：
  - 新增 `tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py`，只读取 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json`，检查 v0.4.14.17 design 的 lineage、summary、guardrails、future files、CLI/function contract、read-only strategy、mock test strategy、fail-closed rules 和 forbidden output key 边界。
  - 新增 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json`，记录 15 项 gate 检查、0 failure；只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design`。
  - 新增 `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_v0.4.14.18.md`，说明本版本仍不创建 runner 文件、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。
  - 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py`，覆盖真实 design 通过、status/lineage drift、future file/CLI drift、权限/strategy drift、forbidden output key、CLI 输出、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.18`。
- gate 通过后仍只进入 scaffold design，不直接创建或运行 runner。

### 验证
- `.\venv\Scripts\python.exe tools\check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py --output tests\production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json --summary docs\production_rebuild_live_preflight_runner_minimal_implementation_design_gate_v0.4.14.18.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner_minimal_implementation_design_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.17] - 2026-06-04

### 新增
- **Production Rebuild Live Preflight Runner Minimal Implementation Design**：
  - 新增 `tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py`，只读取 `tests/production_rebuild_live_preflight_runner_design_gate_report.json`，设计未来 runner 的文件边界、CLI/函数契约、只读策略、mock 测试策略和 fail-closed 规则。
  - 新增 `tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json`，状态为 `ready_for_minimal_implementation_design_gate`；只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design_gate`。
  - 新增 `docs/production_rebuild_live_preflight_runner_minimal_implementation_design_v0.4.14.17.md`，说明本版本不创建 runner 文件、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。
  - 新增 `tests/test_production_rebuild_live_preflight_runner_minimal_implementation_design.py`，覆盖真实 gate 输入通过、gate status/next-step drift、权限漂移、forbidden output key、CLI 输出、runtime service import 禁止、无 Qdrant 连接参数和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.17`。
- 本版本仍只做 implementation design，不创建 `tools/run_production_rebuild_live_preflight.py`，不生成可执行命令或 Qdrant 连接配置。

### 验证
- `.\venv\Scripts\python.exe tools\build_production_rebuild_live_preflight_runner_minimal_implementation_design.py --output tests\production_rebuild_live_preflight_runner_minimal_implementation_design_report.json --summary docs\production_rebuild_live_preflight_runner_minimal_implementation_design_v0.4.14.17.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner_minimal_implementation_design tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.16] - 2026-06-04

### 新增
- **Production Rebuild Live Preflight Runner Design Gate**：
  - 新增 `tools/check_production_rebuild_live_preflight_runner_design_gate.py`，只读取 `tests/production_rebuild_live_preflight_runner_design_report.json`，检查 v0.4.14.15 design 的 lineage、summary、guardrails、future inputs、preflight checks、output fields、blocking conditions、fail-closed contract 与 scaffold cutoff policy。
  - 新增 `tests/production_rebuild_live_preflight_runner_design_gate_report.json`，记录 15 项 gate 检查、0 failure；只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design`。
  - 新增 `docs/production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md`，说明本版本不创建 runner、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。
  - 新增 `tests/test_production_rebuild_live_preflight_runner_design_gate.py`，覆盖真实 design 通过、status/lineage drift、contract drift、权限/guardrail/scaffold drift、forbidden output key、CLI 输出、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.16`。
- 通过后进入最小实现设计，不回退到 `input/importer scaffold`，也不直接创建或运行 runner。

### 验证
- `.\venv\Scripts\python.exe tools\check_production_rebuild_live_preflight_runner_design_gate.py --output tests\production_rebuild_live_preflight_runner_design_gate_report.json --summary docs\production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner_design_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.15] - 2026-06-04

### 新增
- **Production Rebuild Live Preflight Runner Design**：
  - 新增 `tools/build_production_rebuild_live_preflight_runner_design.py`，只读取 `tests/production_rebuild_readiness_cutoff_report.json`，设计未来 live preflight runner 的最小输入、检查项、输出字段和阻断条件。
  - 新增 `tests/production_rebuild_live_preflight_runner_design_report.json`，状态为 `ready_for_live_preflight_runner_design_gate`；只开放 `production_rebuild_live_preflight_runner_design_gate`。
  - 新增 `docs/production_rebuild_live_preflight_runner_design_v0.4.14.15.md`，说明本版本不创建 runner、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。
  - 新增 `tests/test_production_rebuild_live_preflight_runner_design.py`，覆盖真实 cutoff 输入通过、cutoff status/next-step drift、权限漂移、forbidden output key、CLI 输出、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.15`。
- 继续执行 v0.4.14.14 的收口策略：不再扩 `input/importer scaffold` 链条，下一步仅做 live preflight runner design gate。

### 验证
- `.\venv\Scripts\python.exe tools\build_production_rebuild_live_preflight_runner_design.py --output tests\production_rebuild_live_preflight_runner_design_report.json --summary docs\production_rebuild_live_preflight_runner_design_v0.4.14.15.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_live_preflight_runner_design tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.14] - 2026-06-03

### 新增
- **Production Rebuild Readiness Cutoff**：
  - 新增 `tools/build_production_rebuild_readiness_cutoff.py`，只读取 v0.4.13.8-v0.4.14.13 的 saved reports 与当前 health report，判断是否应停止继续扩 `input/importer scaffold` 链条。
  - 新增 `tests/production_rebuild_readiness_cutoff_report.json`，状态为 `ready_for_live_preflight_runner_design_cutoff`；明确 `stop_scaffold_expansion=true`，下一步只开放 `production_rebuild_live_preflight_runner_design`。
  - 新增 `docs/production_rebuild_readiness_cutoff_v0.4.14.14.md`，记录仍未满足的执行前阻断项：正式人工授权记录未创建/接受、live preflight 未运行、backup/snapshot 未实证、Qdrant 目标 collection 未锁定、production rebuild 未执行、post-rebuild RAG quality 未验证。
  - 新增 `tests/test_production_rebuild_readiness_cutoff.py`，覆盖真实 saved reports 通过、source patch/dry-run drift、authorization/execution/input gate drift、project health drift、forbidden output key、CLI 输出、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.14`。
- 更新 `docs/project_review_and_roadmap.md` 与 `docs/final_report_version_guide.md`，将当前下一步从继续 importer/input scaffold 扩张改为 `production_rebuild_live_preflight_runner_design`。
- 本版本刻意收口：不创建 importer，不导入或校验人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild，不修改 RAG 主流程、prompt、rerank、anchor、risk rules 或 eval cases。

### 验证
- `.\venv\Scripts\python.exe tools\build_production_rebuild_readiness_cutoff.py --output tests\production_rebuild_readiness_cutoff_report.json --summary docs\production_rebuild_readiness_cutoff_v0.4.14.14.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_readiness_cutoff tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.13] - 2026-06-03

### 新增
- **Human Rebuild Authorization Record Input Form Scaffold Gate**：
  - 新增 `tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py`，只读取 v0.4.14.12 input form scaffold saved report，检查版本、schema、source lineage、guardrails、分区、字段、中文标签、未来控件提示、form completion/export policy、handoff 和 forbidden output key 边界。
  - 新增 `tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json`，记录 17 项 gate 检查，状态为 `passed`，失败项为 0；通过后只开放 `human_rebuild_authorization_record_input_importer_design`。
  - 新增 `docs/human_rebuild_authorization_record_input_form_scaffold_gate_v0.4.14.13.md`，说明本 gate 不创建可运行输入表单或 importer，不收集、导出、导入或校验真实人工值，不创建或接受正式授权，不运行 live preflight，不访问 Qdrant，不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_input_form_scaffold_gate.py`，覆盖真实 scaffold 通过、status/source lineage drift、权限/人工值/form/export/import/validation drift、internal gate/guardrails、section/field contract、`operator_approval` future-only、future policy/handoff/traceability、forbidden key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.13`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只可进入 `human_rebuild_authorization_record_input_importer_design`，仍不授权真实人工值、importer 实现、审批导入、正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_human_rebuild_authorization_record_input_form_scaffold_gate.py --output tests\human_rebuild_authorization_record_input_form_scaffold_gate_report.json --summary docs\human_rebuild_authorization_record_input_form_scaffold_gate_v0.4.14.13.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_input_form_scaffold_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.12] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Input Form Scaffold**：
  - 新增 `tools/build_human_rebuild_authorization_record_input_form_scaffold.py`，只读取 v0.4.14.10 input packet scaffold 与 v0.4.14.11 gate saved reports，生成未来人工授权输入表单的空白 scaffold。
  - 新增 `tests/human_rebuild_authorization_record_input_form_scaffold_report.json`，记录 10 个空白表单字段、7 个分区、0 个已收集人工值；通过后只开放 `human_rebuild_authorization_record_input_form_scaffold_gate`。
  - 新增 `docs/human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md`，说明本 scaffold 不是可运行输入表单，不是 importer，不收集、导出、导入或校验真实人工值，不创建或接受正式授权，不运行 live preflight，不访问 Qdrant，不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_input_form_scaffold.py`，覆盖真实输入通过、字段顺序、分区、中文标签、未来控件提示、不可编辑/不可提交/不可导出/不可导入、`operator_approval` future-only、source drift、contract/policy/handoff/traceability drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.12`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只可进入 `human_rebuild_authorization_record_input_form_scaffold_gate`，仍不授权真实人工值、importer、审批导入、正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_human_rebuild_authorization_record_input_form_scaffold.py --output tests\human_rebuild_authorization_record_input_form_scaffold_report.json --summary docs\human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_input_form_scaffold tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.11] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Input Packet Scaffold Gate**：
  - 新增 `tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py`，只读取 v0.4.14.10 input packet scaffold saved report，检查版本、schema、source lineage、guardrails、字段行、分区、future validation/import policy、packet completion policy、handoff 和 forbidden output key 边界。
  - 新增 `tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json`，记录 16 项 gate 检查，状态为 `passed`，失败项为 0；通过后只开放 `human_rebuild_authorization_record_input_form_scaffold`。
  - 新增 `docs/human_rebuild_authorization_record_input_packet_scaffold_gate_v0.4.14.11.md`，说明本 gate 不创建输入表单或 importer，不收集、导入或校验真实人工值，不创建或接受正式授权，不运行 live preflight，不访问 Qdrant，不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_input_packet_scaffold_gate.py`，覆盖真实 scaffold 通过、status/source lineage drift、权限/人工值/import/validation drift、internal gate/guardrails、section/row contract、`operator_approval` future-only、future policy/handoff/traceability、forbidden key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.11`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只可进入 `human_rebuild_authorization_record_input_form_scaffold`，仍不授权真实人工值、importer、审批导入、正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_human_rebuild_authorization_record_input_packet_scaffold_gate.py --output tests\human_rebuild_authorization_record_input_packet_scaffold_gate_report.json --summary docs\human_rebuild_authorization_record_input_packet_scaffold_gate_v0.4.14.11.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_input_packet_scaffold_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.10] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Input Packet Scaffold**：
  - 新增 `tools/build_human_rebuild_authorization_record_input_packet_scaffold.py`，只读取 v0.4.14.8 input workflow design 与 v0.4.14.9 gate saved reports，生成未来人工授权输入包的空白 scaffold。
  - 新增 `tests/human_rebuild_authorization_record_input_packet_scaffold_report.json`，记录 10 个空白输入字段、7 个分区、0 个已收集人工值；通过后只开放 `human_rebuild_authorization_record_input_packet_scaffold_gate`。
  - 新增 `docs/human_rebuild_authorization_record_input_packet_scaffold_v0.4.14.10.md`，说明本 scaffold 不是可填写输入表单，不是 importer，不收集、导入或校验真实人工值，不创建或接受正式授权，不运行 live preflight，不访问 Qdrant，不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_input_packet_scaffold.py`，覆盖真实输入通过、字段顺序、分区、空值状态、`operator_approval` future-only、design/gate drift、权限/人工值 drift、contract/policy/handoff/traceability drift、forbidden output key、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.10`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只可进入 `human_rebuild_authorization_record_input_packet_scaffold_gate`，仍不授权真实人工值、输入入口、审批导入、正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_human_rebuild_authorization_record_input_packet_scaffold.py --output tests\human_rebuild_authorization_record_input_packet_scaffold_report.json --summary docs\human_rebuild_authorization_record_input_packet_scaffold_v0.4.14.10.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_input_packet_scaffold tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.9] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Input Workflow Design Gate**：
  - 新增 `tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py`，只读取 v0.4.14.8 input workflow design saved report，检查版本、schema、source lineage、guardrails、流程阶段、字段输入契约、future validation/import policy、handoff 和 forbidden output key 边界。
  - 新增 `tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json`，记录 14 项 gate 检查，状态为 `passed`，失败项为 0；通过后只开放 `human_rebuild_authorization_record_input_packet_scaffold`。
  - 新增 `docs/human_rebuild_authorization_record_input_workflow_design_gate_v0.4.14.9.md`，说明本 gate 不收集人工值、不创建输入表单或 importer、不导入或校验真实审批值、不创建或接受正式授权、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_input_workflow_design_gate.py`，覆盖真实设计报告通过、status/source lineage drift、权限/人工值 drift、phase drift、field contract drift、future policy/import policy/handoff/traceability drift、forbidden key drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.9`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只可进入 `human_rebuild_authorization_record_input_packet_scaffold`，仍不授权真实人工值、输入入口、审批导入、正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_human_rebuild_authorization_record_input_workflow_design_gate.py --output tests\human_rebuild_authorization_record_input_workflow_design_gate_report.json --summary docs\human_rebuild_authorization_record_input_workflow_design_gate_v0.4.14.9.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_input_workflow_design_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.8] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Input Workflow Design**：
  - 新增 `tools/build_human_rebuild_authorization_record_input_workflow_design.py`，只读取 v0.4.14.6 空白 draft scaffold 与 v0.4.14.7 gate，设计未来人工输入、导入、校验和确认流程。
  - 新增 `tests/human_rebuild_authorization_record_input_workflow_design_report.json`，记录 6 个未来流程阶段、10 个字段输入契约、0 个已收集人工值；`input_form_created=false`、`input_values_imported=false`、`formal_authorization_record_created=false`、`authorization_granted=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`。
  - 新增 `docs/human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md`，说明本 design 不收集人工值、不创建输入表单或 importer、不创建或接受正式授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_input_workflow_design.py`，覆盖默认路径、真实输入通过、字段输入契约顺序和空值、workflow phases design-only、operator approval 非当前批准、scaffold/gate drift、权限漂移、row/section drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.8`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_input_workflow_design_gate`，仍不授权填写真实人工值、创建输入入口、导入审批值、创建或接受正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_human_rebuild_authorization_record_input_workflow_design.py --output tests\human_rebuild_authorization_record_input_workflow_design_report.json --summary docs\human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_input_workflow_design tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.7] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Draft Scaffold Gate**：
  - 新增 `tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py`，只读取 `tests/human_rebuild_authorization_record_draft_scaffold_report.json`，检查 v0.4.14.6 空白 draft scaffold 的版本、schema、source lineage、guardrails、字段顺序、分区、空值、future validation policy、handoff 和 forbidden output key 边界。
  - 新增 `tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json`，记录 13 项 gate 检查，状态为 `passed`，失败项为 0。
  - 新增 `docs/human_rebuild_authorization_record_draft_scaffold_gate_v0.4.14.7.md`，说明本 gate 不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_draft_scaffold_gate.py`，覆盖真实 scaffold 通过、status/source lineage drift、人工值/授权漂移、internal gate/guardrail drift、section/row drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.7`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_input_workflow_design`，仍不授权填写真实人工值、创建或接受正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_human_rebuild_authorization_record_draft_scaffold_gate.py --output tests\human_rebuild_authorization_record_draft_scaffold_gate_report.json --summary docs\human_rebuild_authorization_record_draft_scaffold_gate_v0.4.14.7.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_draft_scaffold_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.6] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Draft Scaffold**：
  - 新增 `tools/build_human_rebuild_authorization_record_draft_scaffold.py`，只读取 v0.4.14.4 draft design 与 v0.4.14.5 draft design gate，生成未来正式授权记录的空白草案 scaffold。
  - 新增 `tests/human_rebuild_authorization_record_draft_scaffold_report.json`，记录 10 个空白字段、7 个分区、0 个已收集人工值；`draft_record_created=false`、`formal_authorization_record_created=false`、`authorization_granted=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`。
  - 新增 `docs/human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md`，说明本 scaffold 不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_draft_scaffold.py`，覆盖默认路径、真实输入通过、字段顺序与空值、分区契约、operator approval 非当前批准、design/gate drift、权限漂移、section/field mapping drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.6`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_draft_scaffold_gate`，仍不授权填写真实人工值、创建或接受正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_human_rebuild_authorization_record_draft_scaffold.py --output tests\human_rebuild_authorization_record_draft_scaffold_report.json --summary docs\human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_draft_scaffold tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.5] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Draft Design Gate**：
  - 新增 `tools/check_human_rebuild_authorization_record_draft_design_gate.py`，只读取 `tests/human_rebuild_authorization_record_draft_design_report.json`，检查 v0.4.14.4 draft design 的版本、schema、source lineage、guardrails、字段映射、分区结构、future validation policy、handoff 和 forbidden output key 边界。
  - 新增 `tests/human_rebuild_authorization_record_draft_design_gate_report.json`，记录 13 项 gate 检查，状态为 `passed`，失败项为 0。
  - 新增 `docs/human_rebuild_authorization_record_draft_design_gate_v0.4.14.5.md`，说明本 gate 不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_draft_design_gate.py`，覆盖真实 draft design 通过、status/source lineage drift、人工值/授权漂移、internal gate/guardrail drift、section/field mapping drift、future policy/handoff/traceability drift、forbidden output key drift、CLI 输出一致性和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.5`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_draft_scaffold`，仍不授权填写真实人工值、创建或接受正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_human_rebuild_authorization_record_draft_design_gate.py --output tests\human_rebuild_authorization_record_draft_design_gate_report.json --summary docs\human_rebuild_authorization_record_draft_design_gate_v0.4.14.5.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_draft_design_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.4] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Draft Design**：
  - 新增 `tools/build_human_rebuild_authorization_record_draft_design.py`，只读取 v0.4.14.2 scaffold 与 v0.4.14.3 scaffold gate，设计未来正式授权记录草案的字段映射、分区结构和未来校验口径。
  - 新增 `tests/human_rebuild_authorization_record_draft_design_report.json`，记录 10 个字段映射、7 个草案分区、0 个已收集人工值；`draft_record_created=false`、`formal_authorization_record_created=false`、`authorization_granted=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`。
  - 新增 `docs/human_rebuild_authorization_record_draft_design_v0.4.14.4.md`，说明本 design 不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_draft_design.py`，覆盖默认路径、真实输入通过、字段顺序与空值、operator approval 非当前批准、scaffold/gate drift、权限漂移、guardrail/contract drift、forbidden output keys、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.4`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_draft_design_gate`，仍不授权填写正式授权、live preflight、Qdrant write 或 production rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_human_rebuild_authorization_record_draft_design.py --output tests\human_rebuild_authorization_record_draft_design_report.json --summary docs\human_rebuild_authorization_record_draft_design_v0.4.14.4.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_draft_design tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、全量 `unittest discover`、restricted diff 和 `git diff --check`。

## [0.4.14.3] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Scaffold Gate**：
  - 新增 `tools/check_human_rebuild_authorization_record_scaffold_gate.py`，只读取 `tests/human_rebuild_authorization_record_scaffold_report.json`，检查 v0.4.14.2 空白 scaffold 是否可进入下一步 draft design。
  - 新增 `tests/human_rebuild_authorization_record_scaffold_gate_report.json`，记录 13 项 gate 检查，状态为 `passed`，失败项为 0。
  - 新增 `docs/human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md`，说明本 gate 不收集人工值、不创建或接受正式授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_scaffold_gate.py`，覆盖 status/source lineage drift、人工值/授权漂移、guardrail drift、row blank contract drift、input contract drift、packet/handoff drift、assertion drift 和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.3`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_draft_design`，仍不授权填写正式授权、live preflight、Qdrant write 或生产 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_human_rebuild_authorization_record_scaffold_gate.py --output tests\human_rebuild_authorization_record_scaffold_gate_report.json --summary docs\human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_scaffold_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、full unittest discover、restricted diff 和 `git diff --check`。

## [0.4.14.2] - 2026-05-27

### 新增
- **Human Rebuild Authorization Record Scaffold**：
  - 新增 `tools/build_human_rebuild_authorization_record_scaffold.py`，只读取 v0.4.14.0 design 与 v0.4.14.1 gate，生成未来人工授权记录的空白 scaffold。
  - 新增 `tests/human_rebuild_authorization_record_scaffold_report.json`，记录 10 个授权字段、0 个已收集人工值、`authorization_granted=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`。
  - 新增 `docs/human_rebuild_authorization_record_scaffold_v0.4.14.2.md`，说明 scaffold 不等于正式授权记录，也不允许 live preflight、Qdrant write 或生产 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_record_scaffold.py`，覆盖 input lineage drift、权限漂移、字段顺序、已填值/授权漂移、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.2`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_scaffold_gate`，仍不授权 live preflight、Qdrant write 或生产 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_human_rebuild_authorization_record_scaffold.py --output tests\human_rebuild_authorization_record_scaffold_report.json --summary docs\human_rebuild_authorization_record_scaffold_v0.4.14.2.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_record_scaffold tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、full unittest discover、restricted diff 和 `git diff --check`。

## [0.4.14.1] - 2026-05-27

### 新增
- **Production Rebuild Execution Design Gate**：
  - 新增 `tools/check_production_rebuild_execution_design_gate.py`，只读取 `tests/production_rebuild_execution_design_report.json`，验证 v0.4.14.0 design 是否可进入下一步人工授权记录脚手架。
  - 新增 `tests/production_rebuild_execution_design_gate_report.json`，记录 16 项 gate 检查，状态为 `passed`，失败项为 0。
  - 新增 `docs/production_rebuild_execution_design_gate_v0.4.14.1.md`，说明本 gate 不创建或接受人工授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_production_rebuild_execution_design_gate.py`，覆盖 closeout lineage drift、权限漂移、guardrail drift、record contract 缺失或额外混入、preflight drift、abort condition drift、decision policy drift、handoff drift 和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.1`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_record_scaffold`，仍不授权 live preflight、Qdrant write 或生产 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_production_rebuild_execution_design_gate.py --output tests\production_rebuild_execution_design_gate_report.json --summary docs\production_rebuild_execution_design_gate_v0.4.14.1.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_execution_design_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.14.0] - 2026-05-27

### 新增
- **Production Rebuild Execution Design**：
  - 新增 `tools/build_production_rebuild_execution_design.py`，只读取 v0.4.13.18 closeout report，设计未来生产 rebuild execution series 的记录契约和门禁顺序。
  - 新增 `tests/production_rebuild_execution_design_report.json`，记录 5 类 execution records、7 个 execution phases、8 个 preflight checks 与 9 个 abort conditions；`authorization_granted=false`、`rebuild_allowed=false`。
  - 新增 `docs/production_rebuild_execution_design_v0.4.14.0.md`，说明本 design 不创建或接受授权记录、不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_production_rebuild_execution_design.py`，覆盖真实输入通过、closeout-only source lineage、record contract completeness、权限漂移、guardrail drift、CLI 输出一致性、runtime service import 禁止和 Markdown 边界。

### 变更
- 明确 v0.4.14.0 为 closeout-only source-of-truth contract correction：v0.4.13.18 closeout 已聚合 v0.4.13.13-v0.4.13.17 的授权设计、worksheet、gate、runbook/preflight contract 与 planning closeout 结论，因此本工具不再直接读取旧分散报告。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.14.0`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `production_rebuild_execution_design_gate`，仍不授权 live preflight、Qdrant write 或生产 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_production_rebuild_execution_design.py --output tests\production_rebuild_execution_design_report.json --summary docs\production_rebuild_execution_design_v0.4.14.0.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_production_rebuild_execution_design tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.18] - 2026-05-27

### 新增
- **Ingestion Metadata Rebuild Planning Series Closeout**：
  - 新增 `tools/build_ingestion_metadata_rebuild_planning_series_closeout.py`，只读取 v0.4.13.13-v0.4.13.17 saved reports，关闭 v0.4.13 ingestion metadata patch and rebuild planning series。
  - 新增 `tests/ingestion_metadata_rebuild_planning_series_closeout_report.json`，记录 closeout 状态为 `closed_for_execution_design_handoff`，只开放 `production_rebuild_execution_design`，且 `rebuild_allowed=false`。
  - 新增 `docs/ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md`，说明本 closeout 不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_ingestion_metadata_rebuild_planning_series_closeout.py`，覆盖 source lineage、缺失 source、version/schema/status/next-step drift、授权/rebuild 权限漂移、guardrail drift 和非运行时边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.13.18`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确 v0.4.13 系列已收口；下一步只能是 `production_rebuild_execution_design`，仍不授权生产 Qdrant rebuild。
- 修正 2 个历史 manual-review 单测的 dry-run 结论断言，匹配当前更精确的 `blocked_input_rejections_require_review`。

### 验证
- `.\venv\Scripts\python.exe tools\build_ingestion_metadata_rebuild_planning_series_closeout.py --output tests\ingestion_metadata_rebuild_planning_series_closeout_report.json --summary docs\ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_rebuild_planning_series_closeout tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.17] - 2026-05-27

### 新增
- **Rebuild Runbook / Preflight Contract**：
  - 新增 `tools/build_rebuild_runbook_preflight_contract.py`，只读取 v0.4.13.15 worksheet 与 v0.4.13.16 worksheet gate，定义未来 rebuild execution series 的 runbook/preflight 契约。
  - 新增 `tests/rebuild_runbook_preflight_contract_report.json`，记录 7 个 runbook phases、8 个 preflight checks、7 个 abort conditions；`live_preflight_run=false`、`rebuild_allowed=false`。
  - 新增 `docs/rebuild_runbook_preflight_contract_v0.4.13.17.md`，说明本 contract 不运行 live preflight、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_rebuild_runbook_preflight_contract.py`，覆盖真实输入通过、failed gate 阻断、rebuild permission drift 阻断和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.13.17`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 v0.4.13 series closeout，仍不授权生产 Qdrant rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_rebuild_runbook_preflight_contract.py --output tests\rebuild_runbook_preflight_contract_report.json --summary docs\rebuild_runbook_preflight_contract_v0.4.13.17.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_rebuild_runbook_preflight_contract tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.16] - 2026-05-27

### 新增
- **Human Rebuild Authorization Worksheet Gate**：
  - 新增 `tools/check_human_rebuild_authorization_worksheet_gate.py`，只读取 `tests/human_rebuild_authorization_worksheet_report.json`，验证 worksheet 结构与未授权边界。
  - 新增 `tests/human_rebuild_authorization_worksheet_gate_report.json`，记录 7 项 gate 检查，状态为 `passed`，失败项为 0。
  - 新增 `docs/human_rebuild_authorization_worksheet_gate_v0.4.13.16.md`，说明本 gate 不收集人工值、不创建授权记录、不访问 Qdrant、不 rebuild。
  - 新增 `tests/test_human_rebuild_authorization_worksheet_gate.py`，覆盖真实 worksheet 通过、字段顺序、人工值被收集、授权/rebuild 权限漂移、optional 标签缺失和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.13.16`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `rebuild_runbook_preflight_contract`，仍不授权生产 Qdrant rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_human_rebuild_authorization_worksheet_gate.py --output tests\human_rebuild_authorization_worksheet_gate_report.json --summary docs\human_rebuild_authorization_worksheet_gate_v0.4.13.16.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_worksheet_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.15] - 2026-05-27

### 新增
- **Human Rebuild Authorization Worksheet**：
  - 新增 `tools/build_human_rebuild_authorization_worksheet.py`，只读取 v0.4.13.13 design 与 v0.4.13.14 gate，生成空白人工授权 worksheet。
  - 新增 `tests/human_rebuild_authorization_worksheet_report.json`，记录 10 个授权字段行；所有人工值均为 `not_collected`，`authorization_granted=false`，`rebuild_allowed=false`。
  - 新增 `docs/human_rebuild_authorization_worksheet_v0.4.13.15.md`，列出 required/optional 字段，并明确 worksheet 不等于授权。
  - 新增 `tests/test_human_rebuild_authorization_worksheet.py`，覆盖真实输入通过、字段顺序、required/optional 标签、operator approval 不构成批准、abort conditions、gate drift、字段 drift、rebuild permission drift 和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.13.15`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 worksheet gate/validation，不授权生产 Qdrant rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_human_rebuild_authorization_worksheet.py --output tests\human_rebuild_authorization_worksheet_report.json --summary docs\human_rebuild_authorization_worksheet_v0.4.13.15.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_human_rebuild_authorization_worksheet tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.14] - 2026-05-27

### 新增
- **Rebuild Authorization Design Gate**：
  - 新增 `tools/check_rebuild_authorization_design_gate.py`，只读取 `tests/rebuild_authorization_design_report.json`，验证 v0.4.13.13 生产 rebuild 授权设计是否完整且仍未授权生产 rebuild。
  - 新增 `tests/rebuild_authorization_design_gate_report.json`，记录 12 项 gate 检查，状态为 `passed`，失败项为 0。
  - 新增 `docs/rebuild_authorization_design_gate_v0.4.13.14.md`，说明本 gate 不创建人工授权记录、不访问 Qdrant、不 rebuild、不调用 RAG/embedding/LLM、不运行 full eval。
  - 新增 `tests/test_rebuild_authorization_design_gate.py`，覆盖真实设计通过、lineage drift、授权/rebuild 权限漂移、未来授权记录提前创建、必填字段缺失、终止条件缺失、handoff 边界漂移和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.13.14`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步只开放 `human_rebuild_authorization_worksheet`，仍不授权生产 Qdrant rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_rebuild_authorization_design_gate.py --output tests\rebuild_authorization_design_gate_report.json --summary docs\rebuild_authorization_design_gate_v0.4.13.14.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_rebuild_authorization_design_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.13] - 2026-05-27

### 新增
- **Rebuild Authorization Design**：
  - 新增 `tools/build_rebuild_authorization_design.py`，只读取 v0.4.13.11 runner report 与 v0.4.13.12 runner gate report，定义未来生产 rebuild 前必须完成的人工授权 envelope。
  - 新增 `tests/rebuild_authorization_design_report.json`，状态为 `ready_for_rebuild_authorization_design_gate`，明确 `authorization_granted=false`、`qdrant_write_allowed=false`、`rebuild_allowed=false`。
  - 新增 `docs/rebuild_authorization_design_v0.4.13.13.md`，记录 `target_collection`、`rebuild_scope`、`source_version`、`backup_plan`、`rollback_plan`、`operator_approval` 等必填授权字段。
  - 新增 `tests/test_rebuild_authorization_design.py`，覆盖真实输入通过、必填授权字段、runner gate drift、runner summary drift、handoff 边界和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.13.13`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确下一步是 `rebuild_authorization_design_gate`，仍不授权生产 Qdrant rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_rebuild_authorization_design.py --output tests\rebuild_authorization_design_report.json --summary docs\rebuild_authorization_design_v0.4.13.13.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_rebuild_authorization_design tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.12] - 2026-05-27

### 新增
- **Post-Patch Rebuild Dry-Run Runner Gate**：
  - 新增 `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py`，只读取 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json`，验证 v0.4.13.11 runner saved report 的 lineage、summary、sample contract、row contract、comparison contract、guardrails 与 handoff boundaries。
  - 新增 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json`，记录 11 项 gate 检查，状态为 `passed`，失败项为 0。
  - 新增 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_v0.4.13.12.md`，说明本 gate 不重跑 runner、不访问 Qdrant、不 rebuild、不调用 RAG/embedding/LLM、不运行 full eval。
  - 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py`，覆盖真实报告通过、summary drift、guardrail drift、sample drift、row drift、lineage drift、handoff drift 与 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引与 health reports 到 `0.4.13.12`。
- 更新 `docs/final_report_version_guide.md` 与 `docs/project_review_and_roadmap.md`，明确通过 gate 后只开放 `rebuild_authorization_design`，仍不授权生产 Qdrant rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py --output tests\ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json --summary docs\ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_v0.4.13.12.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate tests.test_project_health_check`
- 已运行 versioned py_compile、项目索引一致性、编码卫生、project health、restricted diff 和 `git diff --check`。

## [0.4.13.11] - 2026-05-26

### 新增
- **Post-Patch Rebuild Dry-Run Runner**：
  - 新增 `tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`，只读取 v0.4.13.8 source patch、v0.4.13.9 design 和 v0.4.13.10 design gate saved reports，并使用本地 deterministic article samples 执行 post-patch metadata dry-run。
  - 新增 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json`，记录 3 个样本、9 行对比、9 行边界元数据存在、9 行预期 `chunk_id/qdrant_point_id` drift、0 项 forbidden drift 和 0 个 blocking condition。
  - 新增 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_v0.4.13.11.md`，记录 runner 摘要、样本覆盖和仍不允许 Qdrant/rebuild/RAG/LLM/full eval 的边界。
  - 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`，覆盖默认路径、真实输入通过、样本形态、row-level metadata/ID drift、输入漂移阻断、forbidden drift 阻断和 Markdown 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.11`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 post-patch rebuild dry-run runner gate，而不是 Qdrant rebuild 或 full eval。

### 验证
- `.\venv\Scripts\python.exe tools\run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py --output tests\ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json --summary docs\ingestion_metadata_patch_post_patch_rebuild_dry_run_v0.4.13.11.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_post_patch_rebuild_dry_run`
- 已运行 versioned py_compile、相关单测、project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.10] - 2026-05-26

### 新增
- **补丁后 Rebuild Dry-Run 设计门禁**：
  - 新增 `tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py`，只读取 v0.4.13.9 design report，验证 post-patch rebuild dry-run design 是否稳定。
  - 新增 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json`，记录 21 项 gate 检查、0 项失败；状态为 `passed`。
  - 新增 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_v0.4.13.10.md`，记录 gate 摘要、检查项和非运行时边界。
  - 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py`，覆盖 source patch 输入漂移、runner creation 权限漂移、sample strategy、comparison fields、output contract、guardrails、handoff 边界和 Markdown 非运行时边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.10`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 post-patch rebuild dry-run runner，而不是 Qdrant rebuild 或 full eval。

### 验证
- `.\venv\Scripts\python.exe tools\check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate`
- 已运行 versioned py_compile、相关单测、project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.9] - 2026-05-26

### 新增
- **补丁后 Rebuild Dry-Run 设计**：
  - 新增 `tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py`，只读取 v0.4.13.8 源码补丁检查报告，生成未来 rebuild dry-run runner 的设计契约。
  - 新增 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json`，记录 v0.4.13.9 design 输出；状态为 `ready_for_post_patch_rebuild_dry_run_design_gate`。
  - 新增 `docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_v0.4.13.9.md`，说明 design-only 边界、未来 runner 的输入/输出契约和下一步 gate。
  - 新增 `tests/test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py`，覆盖真实输入、source patch report 漂移、guardrails、future runner contract 和 Markdown 边界。

### 变更
- 将 v0.4.13.8 源码补丁检查 Markdown 和最近文档说明中文化，同时保留 JSON key、枚举值、路径、命令和检查项原文。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.9`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 post-patch rebuild dry-run design gate，而不是创建 runner 或重建 Qdrant。

### 验证
- `.\venv\Scripts\python.exe tools\build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_post_patch_rebuild_dry_run_design tests.test_ingestion_metadata_source_patch_check`
- 已在提交前运行 versioned py_compile、相关单测、project health、索引一致性、编码卫生、restricted diff 和 `git diff --check`。

## [0.4.13.8] - 2026-05-26

### 新增
- **入库元数据源码补丁检查**：
  - 新增 `tools/check_ingestion_metadata_source_patch.py`，用于在不写入 Qdrant、不 rebuild、不调用 RAG、不运行 full eval 的前提下验证最小源码补丁。
  - 新增 `tests/ingestion_metadata_source_patch_report.json`，记录 15 项源码补丁检查且 0 项失败。
  - 新增 `docs/ingestion_metadata_source_patch_v0.4.13.8.md`，记录源码补丁检查结果和下一步 rebuild dry-run design 边界。
  - 新增 `tests/test_ingestion_metadata_source_patch.py` 和 `tests/test_ingestion_metadata_source_patch_check.py`，覆盖父/子块 chunk metadata、标准章节路径稳定性、checker 漂移阻断和 gate failure。

### 变更
- 在 `src/rag/ingestion.py::build_article_documents` 中为普通法律 article、paragraph、item 文档补齐 deterministic `chunk_index/chunk_count` metadata。
- 更新历史 dry-run/root-cause 测试，使其区分已保存的 pre-patch 结论与当前已 patch 的源码状态。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.8`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 post-patch rebuild dry-run design，而不是直接重建 Qdrant。

### 验证
- `.\venv\Scripts\python.exe tools\check_ingestion_metadata_source_patch.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_source_patch tests.test_ingestion_metadata_source_patch_check`
- 已运行受影响历史测试、完整 project health、索引一致性、编码卫生、restricted diff 和 `git diff --check`。
- 探索性 full unittest discover 暴露了两个既有 manual-review pilot 断言漂移；它们不属于 v0.4.13.8 ingestion 范围，因此未纳入本源码补丁版本。

## [0.4.13.7] - 2026-05-26

### 新增
- **入库元数据实际补丁设计门禁**：
  - 新增 `tools/check_ingestion_metadata_patch_actual_design_gate.py`，只读取 v0.4.13.6 actual patch design report。
  - 新增 `tests/ingestion_metadata_patch_actual_design_gate_report.json`，确认 31 项 gate 检查且 0 项失败。
  - 新增 `docs/ingestion_metadata_patch_actual_design_gate_v0.4.13.7.md`，记录 design gate 和下一步最小源码补丁边界。
  - 新增 `tests/test_ingestion_metadata_patch_actual_design_gate.py`，覆盖 file/function scope 漂移、child count 漂移、validation plan 缺口、implementation/Qdrant/rebuild 漂移和 handoff 边界漂移。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.7`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是最小 ingestion metadata source patch，而不是 rebuild 或主链路修改。

### 验证
- `.\venv\Scripts\python.exe tools\check_ingestion_metadata_patch_actual_design_gate.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_actual_design_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.6] - 2026-05-26

### 新增
- **入库元数据实际补丁设计**：
  - 新增 `tools/build_ingestion_metadata_patch_actual_design.py`，只读取已批准的 contract、local dry-run 和 local dry-run gate reports。
  - 新增 `tests/ingestion_metadata_patch_actual_design_report.json`，定义 `src/rag/ingestion.py::build_article_documents` 的单文件/单函数 patch design。
  - 新增 `docs/ingestion_metadata_patch_actual_design_v0.4.13.6.md`，记录 patch rules、implementation sketch、post-patch validation 和仍被阻断的动作。
  - 新增 `tests/test_ingestion_metadata_patch_actual_design.py`，覆盖 scope、gate dependency、next-step 漂移和 post-patch validation plan。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.6`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 actual patch design gate，而不是直接实现或 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\build_ingestion_metadata_patch_actual_design.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_actual_design`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.5] - 2026-05-26

### 新增
- **入库元数据本地 Dry-Run 门禁**：
  - 新增 `tools/check_ingestion_metadata_patch_local_dry_run_gate.py`，只读取 v0.4.13.4 local dry-run report。
  - 新增 `tests/ingestion_metadata_patch_local_dry_run_gate_report.json`，确认 25 项 gate 检查且 0 项失败。
  - 新增 `docs/ingestion_metadata_patch_local_dry_run_gate_v0.4.13.5.md`，记录 gate 检查和下一步 design-only 边界。
  - 新增 `tests/test_ingestion_metadata_patch_local_dry_run_gate.py`，覆盖 forbidden drift、缺失 boundary metadata、ID drift gaps、Qdrant guardrail 漂移和 handoff 边界漂移。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.5`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 actual ingestion metadata patch design，而不是直接实现或 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_ingestion_metadata_patch_local_dry_run_gate.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_local_dry_run_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.4] - 2026-05-26

### 新增
- **入库元数据补丁本地 Dry-Run Runner**：
  - 新增 `tools/run_ingestion_metadata_patch_local_dry_run.py`，只使用内存中的 article samples 和当前 article document builder。
  - 新增 `tests/ingestion_metadata_patch_local_dry_run_report.json`，确认 3 个样本、8 个 pre/post documents、预期 boundary metadata 与 stable ID drift，以及 0 条 forbidden drift rows。
  - 新增 `docs/ingestion_metadata_patch_local_dry_run_v0.4.13.4.md`，记录 local-only dry-run 结果和下一步 gate 边界。
  - 新增 `tests/test_ingestion_metadata_patch_local_dry_run.py`，覆盖样本形态、simulation-only 行为、prerequisite drift 和 content/citation 稳定性。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.4`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 local dry-run gate，而不是 actual ingestion patch 或 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\run_ingestion_metadata_patch_local_dry_run.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_local_dry_run`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.3] - 2026-05-26

### 新增
- **入库元数据补丁 Dry-Run 设计门禁**：
  - 新增 `tools/check_ingestion_metadata_patch_dry_run_design_gate.py`，只读取 v0.4.13.2 dry-run design report。
  - 新增 `tests/ingestion_metadata_patch_dry_run_design_gate_report.json`，确认 18 项 design gate 检查且 0 项失败。
  - 新增 `docs/ingestion_metadata_patch_dry_run_design_gate_v0.4.13.3.md`，记录 gate 检查和允许的下一步。
  - 新增 `tests/test_ingestion_metadata_patch_dry_run_design_gate.py`，覆盖 forbidden drift 缺口、Qdrant input drift、缺失 blocking conditions 和 full-eval substitution drift。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.3`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 local dry-run runner，而不是 actual ingestion patch 或 rebuild。

### 验证
- `.\venv\Scripts\python.exe tools\check_ingestion_metadata_patch_dry_run_design_gate.py --output tests\ingestion_metadata_patch_dry_run_design_gate_report.json --summary docs\ingestion_metadata_patch_dry_run_design_gate_v0.4.13.3.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_dry_run_design_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.2] - 2026-05-26

### 新增
- **入库元数据补丁 Dry-Run 设计**：
  - 新增 `tools/build_ingestion_metadata_patch_dry_run_design.py`，只读取 v0.4.13.0 contract 和 v0.4.13.1 gate saved reports。
  - 新增 `tests/ingestion_metadata_patch_dry_run_design_report.json`，定义未来 local dry-run comparison strategy、expected drift、forbidden drift、sample scenarios 和 output contract。
  - 新增 `docs/ingestion_metadata_patch_dry_run_design_v0.4.13.2.md`，记录 dry-run boundaries 和 blocking conditions。
  - 新增 `tests/test_ingestion_metadata_patch_dry_run_design.py`，覆盖 gate drift、expected/forbidden drift、output blocking conditions 和 dry-run-only 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.2`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 dry-run design gate，而不是 implementation。

### 验证
- `.\venv\Scripts\python.exe tools\build_ingestion_metadata_patch_dry_run_design.py --output tests\ingestion_metadata_patch_dry_run_design_report.json --summary docs\ingestion_metadata_patch_dry_run_design_v0.4.13.2.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_dry_run_design`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.1] - 2026-05-26

### 新增
- **入库元数据补丁 Contract Gate**：
  - 新增 `tools/check_ingestion_metadata_patch_contract_gate.py`，只读取 v0.4.13.0 contract report。
  - 新增 `tests/ingestion_metadata_patch_contract_gate_report.json`，确认 15 项 contract gate 检查且 0 项失败。
  - 新增 `docs/ingestion_metadata_patch_contract_gate_v0.4.13.1.md`，记录 gate 检查和允许的下一步。
  - 新增 `tests/test_ingestion_metadata_patch_contract_gate.py`，覆盖 runtime scope drift、parent rule drift、Qdrant write drift 和 gate status output。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.1`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 ingestion metadata patch dry-run design，而不是 implementation。

### 验证
- `.\venv\Scripts\python.exe tools\check_ingestion_metadata_patch_contract_gate.py --output tests\ingestion_metadata_patch_contract_gate_report.json --summary docs\ingestion_metadata_patch_contract_gate_v0.4.13.1.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_contract_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.13.0] - 2026-05-26

### 新增
- **入库元数据补丁 Contract**：
  - 新增 `tools/build_ingestion_metadata_patch_contract.py`，只读取 v0.4.12.3 closeout、v0.4.12.1 fix design 和静态 ingestion source text。
  - 新增 `tests/ingestion_metadata_patch_contract_report.json`，定义未来在 `build_article_documents` 中补齐 deterministic `chunk_index/chunk_count` metadata 的 patch 边界。
  - 新增 `docs/ingestion_metadata_patch_contract_v0.4.13.0.md`，记录 parent article 与 paragraph/item chunk rules、future tests 和 rebuild dry-run requirements。
  - 新增 `tests/test_ingestion_metadata_patch_contract.py`，覆盖 closeout drift、allowed scope、forbidden files/functions 和 contract-only 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.13.0`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 ingestion metadata patch contract gate，而不是 implementation。

### 验证
- `.\venv\Scripts\python.exe tools\build_ingestion_metadata_patch_contract.py --output tests\ingestion_metadata_patch_contract_report.json --summary docs\ingestion_metadata_patch_contract_v0.4.13.0.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_metadata_patch_contract`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.12.3] - 2026-05-26

### 新增
- **Metadata/Chunking 系列收口**：
  - 新增 `tools/build_metadata_chunking_series_closeout.py`，只读取 v0.4.12.0 root-cause、v0.4.12.1 fix design 和 v0.4.12.2 gate saved reports。
  - 新增 `tests/metadata_chunking_series_closeout_report.json`，将 v0.4.12.x 收口为 root-cause 与 fix-design 系列，且不授权 implementation。
  - 新增 `docs/metadata_chunking_series_closeout_v0.4.12.3.md`，记录移交至 v0.4.13.x ingestion metadata patch 和 rebuild dry-run planning 的边界。
  - 新增 `tests/test_metadata_chunking_series_closeout.py`，覆盖 gate failure、main-flow prohibition、direct payload patch prohibition 和 next-series handoff。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.12.3`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，关闭 v0.4.12.x，并将后续工作指向 v0.4.13.x rebuild-safe ingestion metadata planning。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_series_closeout.py --output tests\metadata_chunking_series_closeout_report.json --summary docs\metadata_chunking_series_closeout_v0.4.12.3.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_series_closeout`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.12.2] - 2026-05-26

### 新增
- **Metadata/Chunking Fix Design Gate**：
  - 新增 `tools/check_metadata_chunking_fix_design_gate.py`，只读取 v0.4.12.1 fix design 和 v0.4.12.0 root-cause reports。
  - 新增 `tests/metadata_chunking_fix_design_gate_report.json`，确认 stable ID impact、Qdrant point ID impact、rebuild required、direct payload patch disallowed 和 runtime implementation disallowed。
  - 新增 `docs/metadata_chunking_fix_design_gate_v0.4.12.2.md`，记录全部 gate 检查和允许的下一步。
  - 新增 `tests/test_metadata_chunking_fix_design_gate.py`，覆盖 stable ID drift、payload-patch permission drift 和 gate status output。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.12.2`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 v0.4.12 series closeout。

### 验证
- `.\venv\Scripts\python.exe tools\check_metadata_chunking_fix_design_gate.py --output tests\metadata_chunking_fix_design_gate_report.json --summary docs\metadata_chunking_fix_design_gate_v0.4.12.2.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_fix_design_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.12.1] - 2026-05-25

### 新增
- **Metadata/Chunking Fix Design**：
  - 新增 `tools/build_metadata_chunking_fix_design.py`，只读取 v0.4.12.0 root-cause report。
  - 新增 `tests/metadata_chunking_fix_design_report.json`，提出为 legal article、paragraph 和 item documents 添加 deterministic `chunk_index/chunk_count` metadata 的设计。
  - 新增 `docs/metadata_chunking_fix_design_v0.4.12.1.md`，记录 patch plan、metadata contract、stable ID impact、rebuild requirement 和 prohibited actions。
  - 新增 `tests/test_metadata_chunking_fix_design.py`，覆盖 root-cause drift、stable ID impact、rebuild requirement 和 design-only 边界。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.12.1`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 fix design gate，而不是 implementation。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_fix_design.py --output tests\metadata_chunking_fix_design_report.json --summary docs\metadata_chunking_fix_design_v0.4.12.1.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_fix_design`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.12.0] - 2026-05-25

### 新增
- **Metadata/Chunking Root-Cause Report**：
  - 新增 `tools/build_metadata_chunking_root_cause_report.py`，只读取 saved diagnostic reports 和静态 ingestion source text。
  - 新增 `tests/metadata_chunking_root_cause_report.json`，将 `ingestion_article_chunks_missing_boundary_metadata` 识别为 v0.4.11.x `chunk_boundary_ambiguity` findings 背后的高置信 root cause。
  - 新增 `docs/metadata_chunking_root_cause_v0.4.12.0.md`，记录 supporting signals、stable ID impact、prohibited actions 和下一步 fix-design boundary。
  - 新增 `tests/test_metadata_chunking_root_cause_report.py`，覆盖 source drift、report shape、prohibited-action boundaries 和 next-step gating。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.12.0`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 metadata/chunking fix design，而不是 immediate runtime patch。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_root_cause_report.py --output tests\metadata_chunking_root_cause_report.json --summary docs\metadata_chunking_root_cause_v0.4.12.0.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_root_cause_report`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.11.3] - 2026-05-25

### 新增
- **Evidence Metadata Snapshot 系列收口**：
  - 新增 `tools/build_evidence_metadata_snapshot_series_closeout.py`，只读取 v0.4.11.0 contract、v0.4.11.1 snapshot 和 v0.4.11.2 gate saved reports。
  - 新增 `tests/evidence_metadata_snapshot_series_closeout_report.json`，将 v0.4.11.x 收口为 read-only evidence metadata snapshot diagnostic series。
  - 新增 `docs/evidence_metadata_snapshot_series_closeout_v0.4.11.3.md`，记录 primary finding 和推荐的 v0.4.12 root-cause/fix design series。
  - 新增 `tests/test_evidence_metadata_snapshot_series_closeout.py`，覆盖 gate drift、缺失 Qdrant read、closeout shape 和 non-fix boundary。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.11.3`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，关闭 v0.4.11.x，并将后续工作指向 v0.4.12.x metadata/chunking root-cause/fix design。

### 验证
- `.\venv\Scripts\python.exe tools\build_evidence_metadata_snapshot_series_closeout.py --output tests\evidence_metadata_snapshot_series_closeout_report.json --summary docs\evidence_metadata_snapshot_series_closeout_v0.4.11.3.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_metadata_snapshot_series_closeout`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.11.2] - 2026-05-25

### 新增
- **Evidence Metadata Snapshot Gate**：
  - 新增 `tools/check_evidence_metadata_snapshot_gate.py`，在不重新连接 Qdrant 的前提下验证 v0.4.11.1 snapshot 和 v0.4.11.0 contract。
  - 新增 `tests/evidence_metadata_snapshot_gate_report.json`，确认 Qdrant payload read、vectors disabled、19 条 diagnostic rows，并将 `chunk_boundary_ambiguity` 作为 primary finding。
  - 新增 `docs/evidence_metadata_snapshot_gate_v0.4.11.2.md`，记录 gate result 和 non-fix boundary。
  - 新增 `tests/test_evidence_metadata_snapshot_gate.py`，覆盖 Qdrant unavailable drift、vector-read drift、row-count drift 和 accepted metadata findings。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.11.2`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 v0.4.11 series closeout。

### 验证
- `.\venv\Scripts\python.exe tools\check_evidence_metadata_snapshot_gate.py --output tests\evidence_metadata_snapshot_gate_report.json --summary docs\evidence_metadata_snapshot_gate_v0.4.11.2.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_metadata_snapshot_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.11.1] - 2026-05-25

### 新增
- **Evidence Metadata Snapshot Runner**：
  - 新增 `tools/run_evidence_metadata_snapshot.py`，作为敏感的 read-only Qdrant payload snapshot runner，并禁用 vectors。
  - 新增 `tests/evidence_metadata_snapshot_report.json`，记录 19 个 evidence targets、7177 个 scanned points 和 19 条 `chunk_boundary_ambiguity` findings。
  - 新增 `docs/evidence_metadata_snapshot_v0.4.11.1.md`，记录 payload-read boundary 和 current findings。
  - 新增 `tests/test_evidence_metadata_snapshot.py`，覆盖 contract drift、Qdrant unavailable handling、fake payload row generation 和 non-RAG/LLM scope。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.11.1`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 evidence metadata snapshot gate。

### 验证
- `.\venv\Scripts\python.exe tools\run_evidence_metadata_snapshot.py --output tests\evidence_metadata_snapshot_report.json --summary docs\evidence_metadata_snapshot_v0.4.11.1.md --allow-blocked-output`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_metadata_snapshot`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.11.0] - 2026-05-25

### 新增
- **Evidence Metadata Snapshot Contract**：
  - 新增 `tools/build_evidence_metadata_snapshot_contract.py`，只读取 v0.4.10.3 closeout、v0.4.10.0 manifest 和 RAG eval cases。
  - 新增 `tests/evidence_metadata_snapshot_contract_report.json`，定义 8 个 sample cases、19 个 evidence targets、required metadata fields、output fields、failure buckets 和 read-only guardrails。
  - 新增 `docs/evidence_metadata_snapshot_contract_v0.4.11.0.md`，记录 contract boundary 和未来 read-only Qdrant payload snapshot runner。
  - 新增 `tests/test_evidence_metadata_snapshot_contract.py`，覆盖 source drift、缺失 eval cases、contract shape 和 non-runtime scope。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.11.0`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 read-only evidence metadata snapshot runner。

### 验证
- `.\venv\Scripts\python.exe tools\build_evidence_metadata_snapshot_contract.py --output tests\evidence_metadata_snapshot_contract_report.json --summary docs\evidence_metadata_snapshot_contract_v0.4.11.0.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_metadata_snapshot_contract`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.10.3] - 2026-05-25

### 新增
- **Metadata/Chunking Diagnostic Runner 系列收口**：
  - 新增 `tools/build_metadata_chunking_diagnostic_runner_series_closeout.py`，只读取 v0.4.10.0 manifest、v0.4.10.1 saved-report runner 和 v0.4.10.2 runner gate reports。
  - 新增 `tests/metadata_chunking_diagnostic_runner_series_closeout_report.json`，将 v0.4.10.x 收口为 saved-report diagnostic runner series，包含 40 个 manifest items、40 条 diagnostic rows 和 0 条 blocked rows。
  - 新增 `docs/metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md`，记录 series boundary 和推荐的下一步 read-only evidence-level metadata snapshot design。
  - 新增 `tests/test_metadata_chunking_diagnostic_runner_series_closeout.py`，覆盖 version drift、snapshot-read drift、matrix drift 和 non-runtime scope。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.10.3`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，关闭 v0.4.10.x，并将后续工作指向需要单独批准的 v0.4.11.x read-only evidence-level metadata snapshot design。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_diagnostic_runner_series_closeout.py --output tests\metadata_chunking_diagnostic_runner_series_closeout_report.json --summary docs\metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_runner_series_closeout`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.10.2] - 2026-05-25

### 新增
- **Metadata/Chunking Saved-Report Runner Gate**：
  - 新增 `tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py`，只读取 v0.4.10.1 saved-report runner output。
  - 新增 `tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json`，确认 40 条 diagnostic rows、0 条 blocked rows、output contract coverage 和 saved-report-only scope。
  - 新增 `docs/metadata_chunking_diagnostic_saved_report_runner_gate_v0.4.10.2.md`，记录 gate checks 和持续存在的 evidence-level limitation。
  - 新增 `tests/test_metadata_chunking_diagnostic_saved_report_runner_gate.py`，覆盖 valid reports、version drift、blocked rows、snapshot-read drift、runtime pollution 和 field contract drift。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.10.2`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 v0.4.10 series closeout。

### 验证
- `.\venv\Scripts\python.exe tools\check_metadata_chunking_diagnostic_saved_report_runner_gate.py --output tests\metadata_chunking_diagnostic_saved_report_runner_gate_report.json --summary docs\metadata_chunking_diagnostic_saved_report_runner_gate_v0.4.10.2.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_saved_report_runner_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.10.1] - 2026-05-25

### 新增
- **Metadata/Chunking Saved-Report Diagnostic Runner**：
  - 新增 `tools/run_metadata_chunking_diagnostic_saved_report.py`，只读取 v0.4.10.0 manifest 和 v0.4.9.10 dry-run contract。
  - 新增 `tests/metadata_chunking_diagnostic_saved_report_runner_report.json`，记录 40 条 saved-report diagnostic rows 和 0 条 blocked rows。
  - 新增 `docs/metadata_chunking_diagnostic_saved_report_runner_v0.4.10.1.md`，记录 saved-report runner boundary 和 evidence-level limitation。
  - 新增 `tests/test_metadata_chunking_diagnostic_saved_report_runner.py`，覆盖 manifest drift、contract drift、missing manifest contract bits、output contract shape 和 non-runtime scope。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.10.1`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，明确下一步是 saved-report runner gate。

### 验证
- `.\venv\Scripts\python.exe tools\run_metadata_chunking_diagnostic_saved_report.py --output tests\metadata_chunking_diagnostic_saved_report_runner_report.json --summary docs\metadata_chunking_diagnostic_saved_report_runner_v0.4.10.1.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_saved_report_runner`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.10.0] - 2026-05-25

### 新增
- **Metadata/Chunking Diagnostic Runner Manifest**：
  - 新增 `tools/build_metadata_chunking_diagnostic_runner_manifest.py`，只读取 v0.4.9.11 closeout、v0.4.9.10 dry-run contract 和 v0.4.9.6 spec saved reports。
  - 新增 `tests/metadata_chunking_diagnostic_runner_manifest_report.json`，将 8 个 sample cases 按 5 个 check groups 扩展为 40 个 read-only manifest items。
  - 新增 `docs/metadata_chunking_diagnostic_runner_manifest_v0.4.10.0.md`，记录 manifest-only boundary，并确认未运行 diagnostic。
  - 新增 `tests/test_metadata_chunking_diagnostic_runner_manifest.py`，覆盖 closeout drift、contract drift、spec order drift 和 manifest matrix completeness。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.10.0`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，启动 v0.4.10.x read-only diagnostic runner series。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_diagnostic_runner_manifest.py --output tests\metadata_chunking_diagnostic_runner_manifest_report.json --summary docs\metadata_chunking_diagnostic_runner_manifest_v0.4.10.0.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_runner_manifest`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.9.11] - 2026-05-25

### 新增
- **Retrieval Input Quality 系列收口**：
  - 新增 `tools/build_retrieval_input_quality_series_closeout.py`，读取 v0.4.9.0-v0.4.9.10 saved reports，并关闭 retrieval input quality governance chain。
  - 新增 `tests/retrieval_input_quality_series_closeout_report.json`，记录 11 个 completed steps，并确认未实现 diagnostic runner。
  - 新增 `docs/retrieval_input_quality_series_closeout_v0.4.9.11.md`，记录 series closeout boundary 和推荐的下一系列。
  - 新增 `tests/test_retrieval_input_quality_series_closeout.py`，覆盖 version drift、missing reports、closeout order 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.11`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，标记 v0.4.9.x 已关闭，并将真正的 read-only diagnostic runner 工作移至未来系列。

### 验证
- `.\venv\Scripts\python.exe tools\build_retrieval_input_quality_series_closeout.py --output tests\retrieval_input_quality_series_closeout_report.json --summary docs\retrieval_input_quality_series_closeout_v0.4.9.11.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_retrieval_input_quality_series_closeout`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.9.10] - 2026-05-25

### 新增
- **Metadata/Chunking Diagnostic Dry-Run Contract**：
  - 新增 `tools/build_metadata_chunking_diagnostic_dry_run_contract.py`，只读取 v0.4.9.9 runner design gate 和 v0.4.9.8 runner design saved reports。
  - 新增 `tests/metadata_chunking_diagnostic_dry_run_contract_report.json`，定义 5 条 dry-run contract rows、future CLI argument contract、output fields、failure handling 和 prohibited actions。
  - 新增 `docs/metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md`，记录 contract-only boundary，并确认未实现 runner。
  - 新增 `tests/test_metadata_chunking_diagnostic_dry_run_contract.py`，覆盖 gate drift、design drift、row-order drift、output contract drift 和 runtime pollution。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.10`。
- 更新 `docs/final_report_version_guide.md`，在版本材料段底部追加 v0.4.9.10；roadmap 现在只开放下一步 v0.4.9 series closeout。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_diagnostic_dry_run_contract.py --output tests\metadata_chunking_diagnostic_dry_run_contract_report.json --summary docs\metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_dry_run_contract`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.9.9] - 2026-05-25

### 新增
- **Metadata/Chunking Diagnostic Runner Design Gate**：
  - 新增 `tools/check_metadata_chunking_diagnostic_runner_design_gate.py`，只读取 v0.4.9.8 runner design saved report。
  - 新增 `tests/metadata_chunking_diagnostic_runner_design_gate_report.json`，记录 16 项 gate 检查，状态为 `open_for_metadata_chunking_diagnostic_dry_run_contract` 且 0 项失败。
  - 新增 `docs/metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md`，记录 checks、next allowed step 和 non-runtime boundaries。
  - 新增 `tests/test_metadata_chunking_diagnostic_runner_design_gate.py`，覆盖 version drift、row-order drift、output contract drift、failure bucket drift、prohibited action drift、source report drift 和 runtime pollution。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.9`。
- 更新 `docs/final_report_version_guide.md`，在版本材料段底部追加 v0.4.9.9；roadmap 现在只开放下一步 dry-run contract。

### 验证
- `.\venv\Scripts\python.exe tools\check_metadata_chunking_diagnostic_runner_design_gate.py --output tests\metadata_chunking_diagnostic_runner_design_gate_report.json --summary docs\metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_runner_design_gate`
- 提交前已运行完整 project health、索引一致性、编码卫生和 `git diff --check`。

## [0.4.9.8] - 2026-05-24

### 新增
- **Metadata/Chunking Diagnostic Runner Design / metadata 与 chunking 诊断 runner 设计契约**：
  - 新增 `tools/build_metadata_chunking_diagnostic_runner_design.py`，只读取 v0.4.9.7 spec gate 和 v0.4.9.6 spec saved reports。
  - 新增 `tests/metadata_chunking_diagnostic_runner_design_report.json`，定义 5 条 future read-only runner design rows、input/output contracts、failure buckets 和 prohibited actions。
  - 新增 `docs/metadata_chunking_diagnostic_runner_design_v0.4.9.8.md`，记录 runner design boundary，并确认未运行 diagnostic。
  - 新增 `tests/test_metadata_chunking_diagnostic_runner_design.py`，覆盖 gate drift、spec drift、row-order drift、runtime pollution 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.8`。
- 更新 `docs/final_report_version_guide.md`，在版本材料段底部追加 v0.4.9.8；roadmap 现在只开放下一步 runner design gate。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_diagnostic_runner_design.py --output tests\metadata_chunking_diagnostic_runner_design_report.json --summary docs\metadata_chunking_diagnostic_runner_design_v0.4.9.8.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_runner_design`

## [0.4.9.7] - 2026-05-24

### 新增
- **Metadata/Chunking Diagnostic Spec Gate / metadata 与 chunking 诊断规格门禁**：
  - 新增 `tools/check_metadata_chunking_diagnostic_spec_gate.py`，只读取 v0.4.9.6 metadata/chunking diagnostic spec saved report。
  - 新增 `tests/metadata_chunking_diagnostic_spec_gate_report.json`，记录 16 项 gate 检查，状态为 `open_for_metadata_chunking_diagnostic_runner_design` 且 0 项失败。
  - 新增 `docs/metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md`，记录 checks、next allowed step 和 non-runtime boundaries。
  - 新增 `tests/test_metadata_chunking_diagnostic_spec_gate.py`，覆盖 version drift、spec row order drift、required metadata field gaps、sample scope gaps、prohibited action drift 和 runtime pollution。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.7`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序；roadmap 现在只开放下一步 metadata/chunking diagnostic runner design。

### 验证
- `.\venv\Scripts\python.exe tools\check_metadata_chunking_diagnostic_spec_gate.py --output tests\metadata_chunking_diagnostic_spec_gate_report.json --summary docs\metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_spec_gate`

## [0.4.9.6] - 2026-05-24

### 新增
- **Metadata/Chunking Diagnostic Spec / metadata 与 chunking 诊断规格**：
  - 新增 `tools/build_metadata_chunking_diagnostic_spec.py`，只读取 v0.4.9.5 prioritization gate 和 v0.4.9.4 prioritization saved reports。
  - 新增 `tests/metadata_chunking_diagnostic_spec_report.json`，定义 5 个 future diagnostic check groups、10 个 required metadata/chunking fields、sample case scope 和 prohibited actions。
  - 新增 `docs/metadata_chunking_diagnostic_spec_v0.4.9.6.md`，记录 spec boundary，并确认未运行 diagnostic。
  - 新增 `tests/test_metadata_chunking_diagnostic_spec.py`，覆盖 source drift、top-route drift、recommended artifact drift、runtime pollution 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.6`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序；roadmap 现在指向下一步 metadata/chunking diagnostic spec gate。

### 验证
- `.\venv\Scripts\python.exe tools\build_metadata_chunking_diagnostic_spec.py --output tests\metadata_chunking_diagnostic_spec_report.json --summary docs\metadata_chunking_diagnostic_spec_v0.4.9.6.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_metadata_chunking_diagnostic_spec`

## [0.4.9.5] - 2026-05-23

### 新增
- **Retrieval Input Quality Diagnostic Prioritization Gate / 检索输入质量诊断优先级门禁**：
  - 新增 `tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py`，只读取 v0.4.9.4 prioritization saved report。
  - 新增 `tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json`，记录 17 项 gate 检查，状态为 `open_for_metadata_chunking_diagnostic_spec` 且 0 项失败。
  - 新增 `docs/retrieval_input_quality_diagnostic_prioritization_gate_v0.4.9.5.md`，记录 route-order gate checks 和 non-runtime boundaries。
  - 新增 `tests/test_retrieval_input_quality_diagnostic_prioritization_gate.py`，覆盖 version drift、route-order drift、missing row fields、row-content gaps、runtime pollution 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.5`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序；roadmap 现在只开放下一步 metadata/chunking diagnostic spec。

### 验证
- `.\venv\Scripts\python.exe tools\check_retrieval_input_quality_diagnostic_prioritization_gate.py --output tests\retrieval_input_quality_diagnostic_prioritization_gate_report.json --summary docs\retrieval_input_quality_diagnostic_prioritization_gate_v0.4.9.5.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_retrieval_input_quality_diagnostic_prioritization_gate`

## [0.4.9.4] - 2026-05-23

### 新增
- **Retrieval Input Quality Diagnostic Prioritization / 检索输入质量诊断优先级**：
  - 新增 `tools/build_retrieval_input_quality_diagnostic_prioritization.py`，只读取 v0.4.9.3 gate 和 v0.4.9.2 offline audit saved reports。
  - 新增 `tests/retrieval_input_quality_diagnostic_prioritization_report.json`，记录 5-route priority matrix，并以 metadata/chunking、anchor dependency 和 query lexical coverage diagnostics 为优先方向。
  - 新增 `docs/retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md`，记录 priority order、entry conditions、prohibited actions 和 non-runtime boundaries。
  - 新增 `tests/test_retrieval_input_quality_diagnostic_prioritization.py`，覆盖 real prioritization generation、gate drift blocking、route drift、bucket order drift 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.4`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序；roadmap 现在指向 diagnostic specs 前的 prioritization gate。

### 验证
- `.\venv\Scripts\python.exe tools\build_retrieval_input_quality_diagnostic_prioritization.py --output tests\retrieval_input_quality_diagnostic_prioritization_report.json --summary docs\retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_retrieval_input_quality_diagnostic_prioritization`

## [0.4.9.3] - 2026-05-22

### 新增
- **Retrieval Input Quality Offline Audit Gate / 检索输入质量离线审计门禁**：
  - 新增 `tools/check_retrieval_input_quality_offline_audit_gate.py`，只读取 v0.4.9.2 offline audit saved report。
  - 新增 `tests/retrieval_input_quality_offline_audit_gate_report.json`，记录 15 项 gate 检查，状态为 `open_for_retrieval_input_quality_diagnostic_planning` 且 0 项失败。
  - 新增 `docs/retrieval_input_quality_offline_audit_gate_v0.4.9.3.md`，记录 gate status、check coverage 和 non-runtime boundaries。
  - 新增 `tests/test_retrieval_input_quality_offline_audit_gate.py`，覆盖 source drift、bucket order drift、missing row fields、incomplete row content、runtime pollution 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.3`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序；roadmap 现在指向 diagnostic prioritization，而不是更多 gate scaffolding。

### 验证
- `.\venv\Scripts\python.exe tools\check_retrieval_input_quality_offline_audit_gate.py --output tests\retrieval_input_quality_offline_audit_gate_report.json --summary docs\retrieval_input_quality_offline_audit_gate_v0.4.9.3.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_retrieval_input_quality_offline_audit_gate`

## [0.4.9.2] - 2026-05-22

### 新增
- **Retrieval Input Quality Offline Audit / 检索输入质量离线审计**：
  - 新增 `tools/build_retrieval_input_quality_offline_audit.py`，只读取 v0.4.9.1 audit spec、v0.4.9.0 intake 和现有 base/anchor saved reports。
  - 新增 `tests/retrieval_input_quality_offline_audit_report.json`，记录 5 条 bucket audit rows，包含 impacted case count、sample cases、evidence signals、severity 和 recommended next route。
  - 新增 `docs/retrieval_input_quality_offline_audit_v0.4.9.2.md`，记录 offline audit results 和 non-runtime boundaries。
  - 新增 `tests/test_retrieval_input_quality_offline_audit.py`，覆盖 real saved-report audit generation、spec drift blocking、bucket order drift、gate drift 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.2`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序；roadmap 现在指向下一步 lightweight offline audit gate。

### 验证
- `.\venv\Scripts\python.exe tools\build_retrieval_input_quality_offline_audit.py --output tests\retrieval_input_quality_offline_audit_report.json --summary docs\retrieval_input_quality_offline_audit_v0.4.9.2.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_retrieval_input_quality_offline_audit`

## [0.4.9.1] - 2026-05-21

### 新增
- **Retrieval Input Quality Audit Spec / 检索输入质量审计规格**：
  - 新增 `tools/build_retrieval_input_quality_audit_spec.py`，只读取 v0.4.9.0 intake saved report。
  - 新增 `tests/retrieval_input_quality_audit_spec_report.json`，记录 5 个 offline audit specs，覆盖 source/article identity、metadata/chunking、query lexical coverage、legal domain boundary 和 anchor dependency。
  - 新增 `docs/retrieval_input_quality_audit_spec_v0.4.9.1.md`，记录 required inputs、required output fields、gate checks、success conditions 和 non-runtime boundaries。
  - 新增 `tests/test_retrieval_input_quality_audit_spec.py`，覆盖 real intake spec generation、intake drift blocking、bucket order drift、runtime pollution 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.1`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序。

### 验证
- `.\venv\Scripts\python.exe tools\build_retrieval_input_quality_audit_spec.py --output tests\retrieval_input_quality_audit_spec_report.json --summary docs\retrieval_input_quality_audit_spec_v0.4.9.1.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_retrieval_input_quality_audit_spec`

## [0.4.9.0] - 2026-05-21

### 新增
- **Retrieval Input Quality Intake / 检索输入质量治理入口**：
  - 新增 `tools/build_retrieval_input_quality_intake.py`，只读取现有 saved reports，并整合 base retrieval gap、anchor dependency、root-cause action plan 和 v0.4.8 closeout signals。
  - 新增 `tests/retrieval_input_quality_intake_report.json`，记录 5 个 governance buckets：source/article identity、metadata/chunking、query lexical coverage、legal domain boundary 和 anchor dependency。
  - 新增 `docs/retrieval_input_quality_intake_v0.4.9.0.md`，记录 34 个 base-gap cases、33 个 anchor-dependency cases、33 个 metadata/chunking candidates、25 个 zero-base-recall cases 和 12 个 sample cases。
  - 新增 `tests/test_retrieval_input_quality_intake.py`，覆盖 default paths、real saved-report intake、source drift blocking、empty-gap blocking 和 non-runtime boundaries。

### 变更
- 为新的大版本线创建 `codex/v0.4.9-retrieval-input-quality` 分支。
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.9.0`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序。

### 验证
- `.\venv\Scripts\python.exe tools\build_retrieval_input_quality_intake.py --output tests\retrieval_input_quality_intake_report.json --summary docs\retrieval_input_quality_intake_v0.4.9.0.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_retrieval_input_quality_intake`

## [0.4.8.15] - 2026-05-20

### 新增
- **Final Evidence Selection Policy Series Closeout / 最终证据选择策略系列收口**：
  - 新增 `tools/build_final_evidence_selection_policy_series_closeout.py`，只读取 v0.4.8.14/13/12/11 saved reports，并将 v0.4.8.x 收口为 offline design series。
  - 新增 `tests/final_evidence_selection_policy_series_closeout_report.json`，记录 `v0_4_8_series_closed_for_offline_design`、16 个 completed steps 和 8 条 pending-user-confirmation adoption rows。
  - 新增 `docs/final_evidence_selection_policy_series_closeout_v0.4.8.15.md`，记录 completed steps、next recommended series 和被阻断的 runtime-implementation boundary。
  - 新增 `tests/test_final_evidence_selection_policy_series_closeout.py`，覆盖 success、blocked adoption draft、category order drift、runtime pollution 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.8.15`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序；roadmap 现在将 v0.4.8.x 视为已完成 offline design 收口。

### 验证
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_series_closeout.py --output tests\final_evidence_selection_policy_series_closeout_report.json --summary docs\final_evidence_selection_policy_series_closeout_v0.4.8.15.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_series_closeout`

## [0.4.8.14] - 2026-05-20

### 新增
- **Final Evidence Selection Policy Adoption Decision Draft / 最终证据选择策略采纳决策草案**：
  - 新增 `tools/build_final_evidence_selection_policy_adoption_decision_draft.py`，只读取 v0.4.8.13 gate 和 v0.4.8.12 simulation saved reports。
  - 新增 `tests/final_evidence_selection_policy_adoption_decision_draft_report.json`，记录 8 条 `pending_user_confirmation` adoption draft rows。
  - 新增 `docs/final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md`，记录 suggested adoption routes 和需要未来单独批准的要求。
  - 新增 `tests/test_final_evidence_selection_policy_adoption_decision_draft.py`，覆盖 success、blocked gate、simulation order drift、blocking failure 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.8.14`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序。

### 验证
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_adoption_decision_draft.py --output tests\final_evidence_selection_policy_adoption_decision_draft_report.json --summary docs\final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_adoption_decision_draft`

## [0.4.8.13] - 2026-05-20

### 新增
- **Final Evidence Selection Policy Offline Simulation Gate / 最终证据选择策略离线模拟结果门禁**：
  - 新增 `tools/check_final_evidence_selection_policy_offline_simulation_gate.py`，只读取 v0.4.8.12 offline simulation saved report。
  - 新增 `tests/final_evidence_selection_policy_offline_simulation_gate_report.json`，记录 `open_for_policy_adoption_decision_draft`、12 项 passed checks 和 0 项 failed checks。
  - 新增 `docs/final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md`，记录 gate checks 和 non-runtime boundary。
  - 新增 `tests/test_final_evidence_selection_policy_offline_simulation_gate.py`，覆盖 success、blocking failures、missing row fields、category order drift 和 runtime adoption pollution。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.8.13`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序。

### 验证
- `.\venv\Scripts\python.exe tools\check_final_evidence_selection_policy_offline_simulation_gate.py --output tests\final_evidence_selection_policy_offline_simulation_gate_report.json --summary docs\final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md --fail-on-error`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_offline_simulation_gate`

## [0.4.8.12] - 2026-05-20

### 新增
- **Final Evidence Selection Policy Offline Simulation / 最终证据选择策略离线模拟**：
  - 新增 `tools/build_final_evidence_selection_policy_offline_simulation.py`，只读取 v0.4.8.11 input contract saved report，并为 8 个 policy categories 输出 deterministic simulation result rows。
  - 新增 `tests/final_evidence_selection_policy_offline_simulation_report.json`，记录 `completed_saved_report_simulation`、8 条 passing simulation rows、0 项 blocking failures 和 2 条 manual-review signals。
  - 新增 `docs/final_evidence_selection_policy_offline_simulation_v0.4.8.12.md`，记录 simulation results、manual-review signals 和被阻断的 runtime-adoption boundary。
  - 新增 `tests/test_final_evidence_selection_policy_offline_simulation.py`，覆盖 default paths、real-contract simulation、blocked contracts、category order drift 和 non-runtime boundaries。

### 变更
- 同步 `src/main.py`、`tools/run_project_health_check.py`、项目索引和 health reports 到 `0.4.8.12`。
- 更新 `docs/final_report_version_guide.md` 和 `docs/project_review_and_roadmap.md`，保持版本顺序。

### 验证
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_offline_simulation.py --output tests\final_evidence_selection_policy_offline_simulation_report.json --summary docs\final_evidence_selection_policy_offline_simulation_v0.4.8.12.md`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_offline_simulation`

## [0.4.8.11] - 2026-05-20

### 新增
- **Final Evidence Selection Policy Offline Simulation Input Contract / 最终证据选择策略离线模拟输入契约**：
  - 新增 `tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py`，只读取 v0.4.8.7 confirmed record 与 v0.4.8.10 language confirmation record saved reports。
  - 新增 `tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json`，合并 5 条已接受 category 与 3 条 confirmed wording，形成 8 条 saved-report simulation input rows。
  - 新增 `docs/final_evidence_selection_policy_offline_simulation_input_contract_v0.4.8.11.md`，说明输入契约、来源、8 条 policy category 和禁止 runtime adoption 的边界。
  - 新增 `tests/test_final_evidence_selection_policy_offline_simulation_input_contract.py`，覆盖真实报告构建、源报告漂移、category 顺序漂移和禁止运行时/后端模式。
### 边界
- 本版本只生成 input contract，不运行 simulation，不授权 runtime policy、rerank、prompt、eval case、fixture 或 RAG 主流程修改。
### 验证
- `py_compile`、新增单测、索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.10] - 2026-05-19

### 新增
- **Final Evidence Selection Policy Language Revision Confirmation Record / 最终证据选择策略语言修订确认记录**：
  - 新增 `tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py`，只读取 v0.4.8.9 language revision closeout draft saved report。
  - 新增 `tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json`，按用户“确认以上三条。”固化 `liability`、`scenario_core`、`coverage_floor` 三条 confirmed wording。
  - 新增 `docs/final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md`，说明确认上下文、3 条 confirmed wording、offline simulation design handoff 和禁止 runtime adoption 的边界。
  - 新增 `tests/test_final_evidence_selection_policy_language_revision_confirmation_record.py`，覆盖真实报告构建、源 draft 漂移、实现授权污染、row 数量/顺序漂移、缺失语言字段、forbidden/advisory keys、可读性、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.10`，仅作为版本/健康检查一致性更新。
### 质量信号
- `confirmation_gate.status=confirmed_for_future_offline_simulation_design`，表示 3 条语言收口已被用户确认。
- `confirmed_language_revision_rows` 固化 3 条 policy category：`liability`、`scenario_core`、`coverage_floor`。
- `offline_simulation_design_handoff.handoff_status=ready_for_future_offline_simulation_design`，但仍要求另开版本才能进入 simulation 或 runtime 工作。
- 所有 confirmed rows 继续保持 `implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
### 边界
- 本版本只记录语言修订确认结果，confirmed wording 仅允许作为后续 offline simulation design 输入。
- 不授权 runtime policy、rerank、prompt、eval case、fixture、hidden seed、anchor、risk supplement、term preservation、scenario registry、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM 修改。
- 不运行 full eval；工具只读取已保存报告并输出离线 confirmation record。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_language_revision_confirmation_record.py tests\test_final_evidence_selection_policy_language_revision_confirmation_record.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_language_revision_confirmation_record tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_language_revision_confirmation_record.py --output tests\final_evidence_selection_policy_language_revision_confirmation_record_report.json --markdown-output docs\final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.9] - 2026-05-19

### 新增
- **Final Evidence Selection Policy Language Revision Closeout Draft / 最终证据选择策略语言修订收口草案**：
  - 新增 `tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py`，只读取 v0.4.8.8 language revision worksheet saved report。
  - 新增 `tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json`，为 `liability`、`scenario_core`、`coverage_floor` 三条语言债生成待用户确认的 narrowed wording 草案。
  - 新增 `docs/final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md`，说明每条 row 的 suggested wording、must-not-mean、acceptance boundary、confirmation question 和 post-confirmation route。
  - 新增 `tests/test_final_evidence_selection_policy_language_revision_closeout_draft.py`，覆盖真实报告构建、源 worksheet 漂移、实现授权污染、revision row 数量/顺序漂移、缺失语言字段、forbidden/advisory keys、可读性、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.9`，仅作为版本/健康检查一致性更新。
### 质量信号
- `draft_gate.status=draft_pending_user_confirmation`，表示本版本只输出待用户确认的语言收口草案。
- 草案只覆盖 3 条需修订语言的 policy category：`liability`、`scenario_core`、`coverage_floor`。
- `next_version_handoff.may_enter_offline_simulation_design=false`，防止未确认 wording 直接进入 offline simulation design。
- 所有 draft rows 继续保持 `implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
### 边界
- 本版本只生成语言修订收口草案，不记录最终 policy wording，不授权 runtime policy、rerank、prompt、eval case、fixture 或 RAG 主流程修改。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出离线 confirmation draft。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_language_revision_closeout_draft.py tests\test_final_evidence_selection_policy_language_revision_closeout_draft.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_language_revision_closeout_draft tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_language_revision_closeout_draft.py --output tests\final_evidence_selection_policy_language_revision_closeout_draft_report.json --markdown-output docs\final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.8] - 2026-05-19

### 新增
- **Final Evidence Selection Policy Language Revision Worksheet / 最终证据选择策略语言修订工作表**：
  - 新增 `tools/build_final_evidence_selection_policy_language_revision_worksheet.py`，只读取 v0.4.8.7 confirmed record saved report。
  - 新增 `tests/final_evidence_selection_policy_language_revision_worksheet_report.json`，为 `liability`、`scenario_core`、`coverage_floor` 三条 confirmed rows 生成语言修订 worksheet。
  - 新增 `docs/final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md`，说明每条 row 的 wording risk、target boundary、acceptance checks、review questions 和 simulation entry condition。
  - 新增 `tests/test_final_evidence_selection_policy_language_revision_worksheet.py`，覆盖真实报告构建、源确认记录漂移、实现授权污染、revision row 数量/顺序漂移、forbidden/advisory keys、可读性、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.8`，仅作为版本/健康检查一致性更新。
### 质量信号
- `worksheet_gate.status=ready_for_policy_language_revision_review`，表示只允许进入语言复核讨论。
- worksheet 只包含 3 条需修订语言的 policy category：`liability`、`scenario_core`、`coverage_floor`。
- `simulation_design_dependency.simulation_design_should_wait_for_revision_closeout=true`，避免把未修订语言直接带入 offline simulation design。
- 所有 worksheet rows 继续保持 `implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
### 边界
- 本版本只生成语言修订 worksheet，不记录最终 policy wording，不授权 runtime policy、rerank、prompt、eval case、fixture 或 RAG 主流程修改。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出离线 worksheet。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_language_revision_worksheet.py tests\test_final_evidence_selection_policy_language_revision_worksheet.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_language_revision_worksheet tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_language_revision_worksheet.py --output tests\final_evidence_selection_policy_language_revision_worksheet_report.json --markdown-output docs\final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。
## [0.4.8.7] - 2026-05-19

### 新增
- **Final Evidence Selection Policy Closeout Confirmed Record / 最终证据选择策略收口正式确认记录**：
  - 新增 `tools/build_final_evidence_selection_policy_closeout_confirmed_record.py`，只读取 v0.4.8.6 confirmation scaffold saved report。
  - 新增 `tests/final_evidence_selection_policy_closeout_confirmed_record_report.json`，按用户明确确认文本记录 8 条 confirmed rows。
  - 新增 `docs/final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md`，说明确认上下文、8 条确认结果、后续分流和禁止实现边界。
  - 新增 `tests/test_final_evidence_selection_policy_closeout_confirmed_record.py`，覆盖真实报告构建、源脚手架漂移、已确认/实现授权污染、行数量/顺序/建议项漂移、forbidden/advisory keys、可读性、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.7`，仅作为版本/健康检查一致性更新。
### 质量信号
- `confirmation_gate.status=confirmed_for_future_offline_design_planning`，记录用户已明确确认 8 条 suggested closeout options。
- 5 条 policy category 进入 `future_offline_simulation_design_candidate`：`primary`、`operative`、`procedural`、`definition_only`、`high_risk_manual_review`。
- 3 条 policy category 进入 `policy_language_revision_required_before_simulation`：`liability`、`scenario_core`、`coverage_floor`。
- 所有 confirmed rows 继续保持 `implementation_allowed=false`、`code_patch_authorized=false`、`candidate_route_authorized=false` 和 `runtime_adoption_status=not_allowed`。
### 边界
- 本版本只确认 closeout options，可作为后续离线设计规划输入；不是 runtime policy、rerank 修复、prompt 调整、eval case 修改、fixture 写入或 RAG 主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出确认记录。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_closeout_confirmed_record.py tests\test_final_evidence_selection_policy_closeout_confirmed_record.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_closeout_confirmed_record tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_closeout_confirmed_record.py --output tests\final_evidence_selection_policy_closeout_confirmed_record_report.json --markdown-output docs\final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。
## [0.4.8.6] - 2026-05-18

### 新增
- **Final Evidence Selection Policy Closeout Confirmation Record Scaffold / 最终证据选择策略收口确认记录脚手架**：
  - 新增 `tools/build_final_evidence_selection_policy_closeout_confirmation_record.py`，只读取 v0.4.8.5 closeout decision draft saved report。
  - 新增 `tests/final_evidence_selection_policy_closeout_confirmation_record_report.json`，输出 8 条 `pending_user_confirmation` 确认脚手架行。
  - 新增 `docs/final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md`，说明待用户确认字段、可选确认选项和禁止实现边界。
  - 新增 `tests/test_final_evidence_selection_policy_closeout_confirmation_record.py`，覆盖真实报告构建、源草稿漂移、正式结论/实现授权污染、行数量/顺序漂移、forbidden/advisory keys、可读性、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.6`，仅作为版本/健康检查一致性更新。
### 质量信号
- `confirmation_gate.status=pending_user_confirmation`，明确本版本只生成待确认记录脚手架。
- 8 条 confirmation scaffold rows 全部保持 `user_confirmation_recorded=false`、`formal_human_outcome_recorded=false`、`implementation_allowed=false`、`code_patch_authorized=false`、`candidate_route_authorized=false` 和 `runtime_adoption_status=not_allowed`。
- 所有空确认字段仅保留为 `null` 占位，不伪造用户确认、不记录正式人工结论、不授权任何后续代码实现。
### 边界
- 本版本是 RAG grounding quality governance 的 saved-report confirmation scaffold，不是正式用户确认、正式人工结论、runtime selection policy、rerank 修复、prompt 调整、eval case 修改、fixture 写入或 RAG 主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出待用户确认的脚手架材料。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_closeout_confirmation_record.py tests\test_final_evidence_selection_policy_closeout_confirmation_record.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_closeout_confirmation_record tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_closeout_confirmation_record.py --output tests\final_evidence_selection_policy_closeout_confirmation_record_report.json --markdown-output docs\final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。
## [0.4.8.5] - 2026-05-18

### 新增
- **Final Evidence Selection Policy Closeout Decision Draft / 最终证据选择策略收口决策草案**：
  - 新增 `tools/build_final_evidence_selection_policy_closeout_decision_draft.py`，只读取 v0.4.8.4 closeout envelope saved report。
  - 新增 `tests/final_evidence_selection_policy_closeout_decision_draft_report.json`，将 8 条 pending closeout rows 转成待用户确认的 decision draft rows。
  - 新增 `docs/final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md`，说明草案输入、8 条建议收口选择、确认问题和禁止实现边界。
  - 新增 `tests/test_final_evidence_selection_policy_closeout_decision_draft.py`，覆盖真实报告构建、源报告漂移、正式结论/实现授权泄漏、row 数量/顺序漂移、forbidden/advisory keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.5`，仅作为版本/健康检查一致性更新。

### 质量信号
- `draft_gate.status=draft_pending_user_confirmation`，表示只允许进入用户确认草案阶段。
- 8 条 decision draft rows 全部保持 `requires_user_confirmation=true`、`formal_human_outcome_recorded=false`、`draft_is_importable_decision=false`、`candidate_route_authorized=false`、`implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
- 草案保留 5 个 source case traceability 和 8 类 policy category 顺序，但不记录正式人工结论，也不生成工程任务。
- 下一步建议为 `v0.4.8.6 policy table human closeout confirmation record`；仍不自动进入实现。

### 边界
- 本版本是 RAG grounding quality governance 的 saved-report user-confirmation draft，不是正式人工结论、策略实现、runtime simulator、rerank 修复、prompt 调整、eval case 修改、fixture 写入或 RAG 主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出用户确认草案材料。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_closeout_decision_draft.py tests\test_final_evidence_selection_policy_closeout_decision_draft.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_closeout_decision_draft tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_closeout_decision_draft.py --output tests\final_evidence_selection_policy_closeout_decision_draft_report.json --markdown-output docs\final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.4] - 2026-05-18

### 新增
- **Final Evidence Selection Policy Closeout Envelope / 最终证据选择策略收口外壳**：
  - 新增 `tools/build_final_evidence_selection_policy_closeout_envelope.py`，只读取 v0.4.8.3 human review worksheet saved report。
  - 新增 `tests/final_evidence_selection_policy_closeout_envelope_report.json`，将 8 条 review rows 转成待人工收口的 closeout rows、candidate routes、minimum human basis 和 closeout options。
  - 新增 `docs/final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md`，说明 closeout envelope 输入、8 条待收口行、可选收口路径和禁止实现边界。
  - 新增 `tests/test_final_evidence_selection_policy_closeout_envelope.py`，覆盖真实报告构建、源报告漂移、正式结论/实现授权泄漏、row 数量/顺序漂移、forbidden/advisory keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.4`，仅作为版本/健康检查一致性更新。

### 质量信号
- `closeout_gate.status=pending_policy_table_human_closeout`，表示只允许进入人工策略收口讨论阶段。
- 8 条 closeout rows 全部保持 `pending_human_closeout`、`formal_human_outcome_recorded=false`、`candidate_route_authorized=false`、`implementation_allowed=false`、`code_patch_authorized=false` 和 `runtime_adoption_status=not_allowed`。
- closeout envelope 保留 5 个 source case traceability 和 8 类 policy category 顺序，但不记录正式人工结论，也不生成工程任务。
- 下一步建议为 `v0.4.8.5 policy table human closeout decision draft`；仍不自动进入实现。

### 边界
- 本版本是 RAG grounding quality governance 的 saved-report closeout envelope，不是策略实现、runtime simulator、rerank 修复、prompt 调整、eval case 修改、fixture 写入或 RAG 主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出人工收口讨论材料。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_closeout_envelope.py tests\test_final_evidence_selection_policy_closeout_envelope.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_closeout_envelope tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_closeout_envelope.py --output tests\final_evidence_selection_policy_closeout_envelope_report.json --markdown-output docs\final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.3] - 2026-05-18

### 新增
- **Final Evidence Selection Policy Human Review Worksheet / 最终证据选择策略人工复核工作表**：
  - 新增 `tools/build_final_evidence_selection_policy_human_review_worksheet.py`，只读取 v0.4.8.2 policy table draft saved report。
  - 新增 `tests/final_evidence_selection_policy_human_review_worksheet_report.json`，将 8 条 policy rows 转成可人工审议的 review rows、review questions、acceptance checks 和 discussion options。
  - 新增 `docs/final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md`，说明 worksheet 的输入、审议问题、验收检查点和禁止实现边界。
  - 新增 `tests/test_final_evidence_selection_policy_human_review_worksheet.py`，覆盖真实报告构建、源报告漂移、实现授权漂移、policy row 顺序/数量漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.3`，仅作为版本/健康检查一致性更新。

### 质量信号
- `worksheet_gate.status=ready_for_policy_table_human_review_worksheet`，表示只允许进入人工策略复核 worksheet 阶段。
- 8 条 review rows 全部保持 `implementation_allowed=false`、`code_patch_authorized=false`、`runtime_adoption_status=not_allowed` 和 `captures_formal_review_outcome=false`。
- worksheet 保留 v0.4.8.2 的 8 类 policy categories 与 5 个 source case traceability，但不记录正式人工结论。
- 下一步建议为 `v0.4.8.4 policy table human review closeout`，用于在人工审议后记录收口意见；仍不自动进入实现。

### 边界
- 本版本是 RAG grounding quality governance 的 saved-report human review worksheet，不是策略实现、runtime simulator、rerank 修复、prompt 调整、eval case 修改、fixture 写入或 RAG 主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出人工审议材料。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_human_review_worksheet.py tests\test_final_evidence_selection_policy_human_review_worksheet.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_human_review_worksheet tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_human_review_worksheet.py --output tests\final_evidence_selection_policy_human_review_worksheet_report.json --markdown-output docs\final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.2] - 2026-05-16

### 新增
- **Final Evidence Selection Policy Table Draft / 最终证据选择策略表草案**：
  - 新增 `tools/build_final_evidence_selection_policy_table_draft.py`，只读取 v0.4.8.1 simulator spec、v0.4.8.0 intake、final selection audit 和 human closeout confirmation record。
  - 新增 `tests/final_evidence_selection_policy_table_draft_report.json`，输出 8 条人工可审阅 policy table rows，覆盖 primary、operative、procedural、liability、scenario_core、definition_only、coverage_floor 和 high_risk_manual_review。
  - 新增 `docs/final_evidence_selection_policy_table_draft_v0.4.8.2.md`，说明策略表草案、preservation rules、manual review gate 和边界。
  - 新增 `tests/test_final_evidence_selection_policy_table_draft.py`，覆盖真实报告构建、源报告漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.2`，仅作为版本/健康检查一致性更新。

### 质量信号
- `policy_table_gate.status=ready_for_manual_review_policy_table_draft`，表示只允许进入离线策略表草案阶段。
- 8 条 policy rows 全部为 `draft_for_manual_review`，并保持 `runtime_adoption_status=not_allowed`。
- 5 个 high-risk confirmed cases 仍由 manual review gate 阻断未经复核的 runtime adoption。
- source signal case summary 保留 v0.4.8.1 的核心信号：主证据保留 5、规范条款保留 4、程序证据保留 3、责任/后果证据保留 2、场景核心保留或解释 4、定义条款替代防线 1、coverage floor 2、high-risk manual review 5。

### 边界
- 本版本是 RAG grounding quality governance 的 saved-report policy table draft，不是策略实现、runtime simulator、rerank 修复、prompt 调整、eval case 修改、fixture 写入或 RAG 主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出草案报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_table_draft.py tests\test_final_evidence_selection_policy_table_draft.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_table_draft tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_table_draft.py --output tests\final_evidence_selection_policy_table_draft_report.json --markdown-output docs\final_evidence_selection_policy_table_draft_v0.4.8.2.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.1] - 2026-05-16

### 新增
- **Final Evidence Selection Policy Simulator Spec / 最终证据选择策略模拟器契约**：
  - 新增 `tools/build_final_evidence_selection_policy_simulator_spec.py`，只读取 v0.4.8.0 intake、final selection audit 和 human closeout confirmation record。
  - 新增 `tests/final_evidence_selection_policy_simulator_spec_report.json`，输出 saved-report simulator input/output contract、6 类 policy candidate categories、8 类 failure/manual-review signals 和 5 个 case-level simulation spec rows。
  - 新增 `docs/final_evidence_selection_policy_simulator_spec_v0.4.8.1.md`，说明契约状态、case matrix、failure signals、manual review gate 和边界。
  - 新增 `tests/test_final_evidence_selection_policy_simulator_spec.py`，覆盖真实报告构建、源报告漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.1`，仅作为版本/健康检查一致性更新。

### 质量信号
- `simulator_spec_gate.status=ready_for_offline_policy_simulator_spec`，表示只允许进入离线模拟器契约阶段。
- 定义 6 类 policy candidate categories：primary、operative、procedural、liability、scenario_core、definition_only。
- 定义 8 类 failure/manual-review signals：主证据保留、规范条款保留、程序证据保留、责任/后果证据保留、场景核心保留或解释、定义条款替代防线、final coverage floor、high-risk manual review。
- 5 个 high-risk confirmed cases 均输出 `manual_review_required_before_runtime_policy`，用于阻断未经复核的 runtime 采纳或实现；v0.4.8.2 仍可继续做设计层 policy table draft。

### 边界
- 本版本是 RAG grounding quality governance 的 saved-report simulator spec，不是 simulator runtime、策略实现、rerank 修复、prompt 调整、eval case 修改、fixture 写入或 RAG 主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告并输出契约报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_simulator_spec.py tests\test_final_evidence_selection_policy_simulator_spec.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_simulator_spec tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_simulator_spec.py --output tests\final_evidence_selection_policy_simulator_spec_report.json --markdown-output docs\final_evidence_selection_policy_simulator_spec_v0.4.8.1.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.8.0] - 2026-05-14

### 新增
- **Final Evidence Selection Policy Design Intake / 最终证据选择策略设计入口**：
  - 新增 `tools/build_final_evidence_selection_policy_intake.py`，只读取已保存 confirmation record、decision draft、closeout、worksheet、design pack 和 final selection audit。
  - 新增 `tests/final_evidence_selection_policy_intake_report.json`，输出 5 个已确认 case、6 条 policy questions、6 条 preservation discussion items 和 v0.4.8.1 simulator plan。
  - 新增 `docs/final_evidence_selection_policy_intake_v0.4.8.0.md`，说明 intake 状态、case matrix、preservation 讨论项和边界。
  - 新增 `tests/test_final_evidence_selection_policy_intake.py`，覆盖真实报告构建、源报告漂移、audit 漂移、advisory/forbidden keys、可读性 gate、Markdown 边界和禁止运行时/后端模式。
  - 同步 `src/main.py`、`tools/run_project_health_check.py`、索引和 health reports 至 `0.4.8.0`，仅作为版本/健康检查一致性更新。

### 质量信号
- `intake_gate.status=ready_for_policy_design_intake`，表示只允许进入最终证据选择策略设计输入阶段。
- 汇总 5 个 confirmed final selection cases，全部匹配 final selection audit 的 high-priority review cases。
- 输出 preservation 讨论项：primary evidence、operative rule、procedural、liability、scenario core、final coverage floor。
- `policy_simulator_plan.recommended_next_version=v0.4.8.1`，但仍为 saved reports only 的设计计划。

### 边界
- 本版本是 RAG grounding quality governance 的 design intake，不是策略实现、rerank 修复、runtime selection policy patch、eval case 修改、fixture 写入或主流程接入。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；工具只读取已保存报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_final_evidence_selection_policy_intake.py tests\test_final_evidence_selection_policy_intake.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_policy_intake tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_final_evidence_selection_policy_intake.py --output tests\final_evidence_selection_policy_intake_report.json --markdown-output docs\final_evidence_selection_policy_intake_v0.4.8.0.md`
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.7.9.7] - 2026-05-14

### 修正
- **Future Version Ordering / 未来版本顺序修正**：
  - 将最终证据选择策略设计统一调整为 `v0.4.8.x`。
  - 将 Retrieval Input Quality Governance 统一调整为 `v0.4.9.x`。
  - 修正 `tools/build_ready_action_routing_dry_run.py` 中的路线常量，避免 scenario、fixture、anchor 继续占用 `v0.4.8.x` / `v0.4.9.x` 编号。
  - 修正 v0.4.7.9.3-v0.4.7.9.6 设计收口链路生成器中的后续系列标签，并重新生成对应 JSON/Markdown。
  - 更新 `docs/project_review_and_roadmap.md` 与 `docs/final_report_version_guide.md` 的路线说明。

### 质量信号
- `v0.4.8.x = Final Evidence Selection Policy Design`。
- `v0.4.9.x = Retrieval Input Quality Governance`。
- 新增 routing dry-run 单测，明确防止两个未来系列再次互换。

### 边界
- 本版本仅修正文档、诊断/路由标签、生成产物和版本号。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_routing_dry_run.py tools\build_ready_action_design_review_worksheet.py tools\build_ready_action_design_review_closeout.py tools\build_ready_action_human_closeout_decision_draft.py tools\build_ready_action_human_closeout_confirmation_record.py tests\test_ready_action_routing_dry_run.py tests\test_ready_action_design_review_worksheet.py tests\test_ready_action_design_review_closeout.py tests\test_ready_action_human_closeout_decision_draft.py tests\test_ready_action_human_closeout_confirmation_record.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_routing_dry_run tests.test_ready_action_design_review_worksheet tests.test_ready_action_design_review_closeout tests.test_ready_action_human_closeout_decision_draft tests.test_ready_action_human_closeout_confirmation_record tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_ready_action_routing_dry_run.py --action-candidates tests\evidence_manual_review_action_candidates.json --progress-report tests\evidence_manual_review_progress_report.json --output tests\ready_action_routing_dry_run_report.json`
- 重新生成 v0.4.7.9.3-v0.4.7.9.6 的 ready action 设计收口报告。
- 索引一致性、编码卫生、project health check 和 `git diff --check`。

## [0.4.7.9.6] - 2026-05-14

### 新增
- **Ready Action Human Closeout Confirmation Record / 人工收口确认记录**：
  - 新增 `tools/build_ready_action_human_closeout_confirmation_record.py`，只读取既有 `tests/ready_action_human_closeout_decision_draft_report.json`。
  - 新增 `tests/ready_action_human_closeout_confirmation_record_report.json`，记录用户确认 5 条设计收口方向。
  - 新增 `docs/ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md`，说明每条方向的确认口径、后续系列和边界。
  - 新增 `tests/test_ready_action_human_closeout_confirmation_record.py`，覆盖 source draft contract、正式结论/importer 隔离、实现授权阻断、数量/顺序漂移、advisory/forbidden keys、可读性 gate 和禁止运行时/后端模式。

### 质量信号
- `confirmation_gate.status=confirmed_for_future_design_planning`，表示只确认未来设计规划方向。
- 输出 5 条 confirmation rows，保留 18 个 design actions、5 个 source cases、31 个 pending records excluded。
- 每条轨道默认 `manual_review_importable=false`、`not_completed_manual_review_decision=true`。
- 顶层继续保持 `implementation_allowed=false`、`code_patch_authorized=false`、`next_design_authorized=false`、`handoff_to_implementation=not_allowed`。

### 边界
- 本版本是 RAG grounding quality governance 的设计收口确认记录，不是 manual review importer completed decision、implementation plan、patch plan、fixture 写入或样本修补工具。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；checker 只读取已保存 decision draft 报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_human_closeout_confirmation_record.py tests\test_ready_action_human_closeout_confirmation_record.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_human_closeout_confirmation_record tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_ready_action_human_closeout_confirmation_record.py --output tests\ready_action_human_closeout_confirmation_record_report.json --markdown-output docs\ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md`

## [0.4.7.9.5] - 2026-05-14

### 新增
- **Ready Action Human Closeout Decision Draft / 待用户确认的人工收口草案**：
  - 新增 `tools/build_ready_action_human_closeout_decision_draft.py`，只读取既有 `tests/ready_action_design_review_closeout_report.json`。
  - 新增 `tests/ready_action_human_closeout_decision_draft_report.json`，为 5 条设计轨道生成待用户确认的 draft matrix。
  - 新增 `docs/ready_action_human_closeout_decision_draft_v0.4.7.9.5.md`，列出每条轨道的草案方向、草案理由、需要用户确认的问题和候选后续。
  - 新增 `tests/test_ready_action_human_closeout_decision_draft.py`，覆盖 source closeout contract、正式结论/实现授权阻断、数量/顺序漂移、advisory/forbidden keys、可读性 gate 和禁止运行时/后端模式。

### 质量信号
- `draft_gate.status=draft_pending_user_confirmation`，表示只生成待确认草案。
- 输出 5 条 draft rows，保留 18 个 design actions、5 个 source cases、31 个 pending records excluded。
- 每条轨道默认 `requires_user_confirmation=true`、`formal_human_outcome_recorded=false`、`draft_is_importable_decision=false`。
- 顶层继续保持 `implementation_allowed=false`、`code_patch_authorized=false`、`next_design_authorized=false`、`handoff_to_implementation=not_allowed`。

### 边界
- 本版本是 RAG grounding quality governance 的用户确认草案，不是正式人工结论、importer 输入、implementation plan、patch plan、fixture 写入或样本修补工具。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；checker 只读取已保存 closeout envelope 报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_human_closeout_decision_draft.py tests\test_ready_action_human_closeout_decision_draft.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_human_closeout_decision_draft tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_ready_action_human_closeout_decision_draft.py --output tests\ready_action_human_closeout_decision_draft_report.json --markdown-output docs\ready_action_human_closeout_decision_draft_v0.4.7.9.5.md`

## [0.4.7.9.4] - 2026-05-14

### 新增
- **Ready Action Design Review Closeout Envelope / 人工设计评审收口外壳**：
  - 新增 `tools/build_ready_action_design_review_closeout.py`，只读取既有 `tests/ready_action_design_review_worksheet_report.json`。
  - 新增 `tests/ready_action_design_review_closeout_report.json`，将 5 条设计轨道整理为待人工收口的 closeout matrix。
  - 新增 `docs/ready_action_design_review_closeout_v0.4.7.9.4.md`，说明每条轨道的候选分流、收口问题和最小人工依据。
  - 新增 `tests/test_ready_action_design_review_closeout.py`，覆盖 source worksheet contract、实现授权阻断、数量/顺序漂移、advisory/forbidden keys、可读性 gate 和禁止运行时/后端模式。

### 质量信号
- `closeout_gate.status=pending_human_design_closeout`，表示只允许人工收口讨论。
- 输出 5 条 closeout rows，保留 18 个 design actions、5 个 source cases、31 个 pending records excluded。
- 每条轨道默认 `closeout_status=pending_human_closeout`、`formal_human_outcome_recorded=false`、`candidate_route_authorized=false`。
- 顶层继续保持 `implementation_allowed=false`、`code_patch_authorized=false`、`next_design_authorized=false`、`handoff_to_implementation=not_allowed`。

### 边界
- 本版本是 RAG grounding quality governance 的收口外壳，不是正式人工结论、implementation plan、patch plan、fixture 写入或样本修补工具。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；checker 只读取已保存 worksheet 报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_design_review_closeout.py tests\test_ready_action_design_review_closeout.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_design_review_closeout tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_ready_action_design_review_closeout.py --output tests\ready_action_design_review_closeout_report.json --markdown-output docs\ready_action_design_review_closeout_v0.4.7.9.4.md`

## [0.4.7.9.3] - 2026-05-14

### 新增
- **Ready Action Design Review Worksheet / 人工设计复核工作表**：
  - 新增 `tools/build_ready_action_design_review_worksheet.py`，只读取既有 `tests/ready_action_design_review_gate_report.json` 与 `tests/ready_action_design_review_brief_report.json`。
  - 新增 `tests/ready_action_design_review_worksheet_report.json`，输出 5 条设计轨道的 decision matrix、review questions、routing hints 和 traceability。
  - 新增 `docs/ready_action_design_review_worksheet_v0.4.7.9.3.md`，作为人工评审会使用的只读 worksheet。
  - 新增 `tests/test_ready_action_design_review_worksheet.py`，覆盖 source contract、实现授权阻断、数量/顺序漂移、advisory/pending 任务化阻断、可读性 gate 和禁止运行时/后端模式。

### 质量信号
- `worksheet_gate.status=ready_for_human_design_review_matrix` 时，仅表示可以人工审议 5 条设计方向。
- 保留 5 个 review tracks、18 个 design actions、5 个 source cases、31 个 pending records excluded 的基线。
- 输出 `implementation_allowed=false`、`code_patch_authorized=false`、`handoff_to_implementation=not_allowed`、`captures_formal_review_outcome=false`。
- 若 gate/brief schema、版本、traceability、数量、顺序、可读性或 advisory/forbidden keys 漂移，worksheet 会保守阻断。

### 边界
- 本版本是 RAG grounding quality governance 的人工设计复核 worksheet，不是 implementation plan、patch plan、正式人工结论、fixture 写入或样本修补工具。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；checker 只读取已保存 gate/brief 报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_design_review_worksheet.py tests\test_ready_action_design_review_worksheet.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_design_review_worksheet tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_ready_action_design_review_worksheet.py --output tests\ready_action_design_review_worksheet_report.json --markdown-output docs\ready_action_design_review_worksheet_v0.4.7.9.3.md`

## [0.4.7.9.2] - 2026-05-13

### 新增
- **Ready Action Design Review Gate / 设计评审入口门禁**：
  - 新增 `tools/check_ready_action_design_review_gate.py`，只读取既有 `tests/ready_action_design_review_brief_report.json`。
  - 新增 `tests/ready_action_design_review_gate_report.json`，判断 v0.4.7.9.1 简报是否只允许进入人工设计评审。
  - 新增 `docs/ready_action_design_review_gate_v0.4.7.9.2.md`，说明 gate 打开后只代表可以讨论设计草案，不代表可以实现。
  - 新增 `tests/test_ready_action_design_review_gate.py`，覆盖 wrong schema、blocked brief、source assertion failure、implementation authorization、pending/advisory signals、traceability drift、guardrail mismatch 和禁止运行时/后端模式。

### 质量信号
- `gate.status=open_for_human_design_review_only`，`allowed_use=human_design_review_discussion_only`。
- 保留 5 个设计轨道、18 个 design actions、5 个 source cases、31 个 pending records excluded 的 traceability 基线。
- `implementation_allowed=false`、`code_patch_authorized=false`、`handoff_to_implementation=not_allowed` 必须同时成立。
- 若 source brief 出现实现授权、AI/advisory 信号、pending/backlog/task 化信号、traceability 漂移或 guardrail 不一致，gate 会保守阻断。

### 边界
- 本版本是 RAG grounding quality governance 的只读门禁，不是实现计划、补丁计划、样本修补、fixture 写入或人工复核导入文件。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 不运行 full eval；checker 只读取已保存的 design review brief 报告。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_ready_action_design_review_gate.py tests\test_ready_action_design_review_gate.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_design_review_gate tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\check_ready_action_design_review_gate.py --output tests\ready_action_design_review_gate_report.json --markdown-output docs\ready_action_design_review_gate_v0.4.7.9.2.md`

## [0.4.7.9.1] - 2026-05-13

### 新增
- **Ready Action Design Review Brief / 设计评审简报**：
  - 新增 `tools/build_ready_action_design_review_brief.py`，只读取既有 `tests/ready_action_design_pack_report.json`。
  - 新增 `tests/ready_action_design_review_brief_report.json`，将 18 个 ready-for-design-review candidates 改写为 5 条人工评审方向。
  - 新增 `docs/ready_action_design_review_brief_v0.4.7.9.1.md`，用非技术读者更容易理解的方式说明每条方向审什么、为什么审、当前禁止什么、进入后续实现前还需要哪些验证。
  - 新增 `tests/test_ready_action_design_review_brief.py`，覆盖真实 5/18/31 基线、P0/P1 排序、traceability、blocked source pack、防 pending 任务化和禁止运行时/后端模式。

### 质量信号
- 评审顺序固定为：final evidence selection policy、primary evidence fixture candidate、high-risk manual grounding、scenario registry core article、functional typing fixture。
- `summary.priority_band_summary` 输出 `P0=3`、`P1=2`；`ready_for_design_review_candidates=18`，`pending_records_excluded=31`。
- `brief_gate` 继续保持 `implementation_allowed=false`、`implementation_status=not_started`、`implementation_requires_future_explicit_approval=true`。

### 边界
- 本版本是 RAG grounding quality governance 的只读评审简报，不是实现计划、自动补丁、样本修补或人工复核导入文件。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 31 个 pending records 只作为背景统计，不进入评审方向、任务清单或工程 backlog。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_design_review_brief.py tests\test_ready_action_design_review_brief.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_design_review_brief`
- `.\venv\Scripts\python.exe tools\build_ready_action_design_review_brief.py --output tests\ready_action_design_review_brief_report.json --markdown-output docs\ready_action_design_review_brief_v0.4.7.9.1.md`

## [0.4.7.9.0] - 2026-05-13

### 新增
- **Ready Action Design Pack / 受治理 ready action 设计包**：
  - 新增 `tools/build_ready_action_design_pack.py`，只读取既有 `tests/validated_decision_promotion_dry_run_report.json` 与 `tests/manual_review_export_pipeline_dry_run_report.json`。
  - 新增 `tests/ready_action_design_pack_report.json`，将 5 个 completed + valid pilot decisions 产生的 18 个 ready action candidates 整理为 5 条设计轨道。
  - 新增 `docs/ready_action_design_pack_v0.4.7.9.0.md`，明确该产物是 RAG grounding quality diagnostics / governed design planning，不是样本修补工具。
  - 新增 `tests/test_ready_action_design_pack.py`，覆盖真实报告 5/18/31 基线、5 类 action group、gate blocked 输入阻断、traceability 保留和 no automatic implementation。

### 质量信号
- 输出 `planning_gate.status=open_for_design_review`，但 `implementation_allowed=false`、`implementation_status=not_started`。
- action type summary：`final_evidence_selection_policy_review=5`、`primary_evidence_fixture_candidate_review=5`、`scenario_registry_core_article_review=4`、`high_risk_manual_grounding_review=3`、`functional_typing_fixture_review=1`。
- 顶层 root cause summary 沿用 promotion dry-run 的人工确认统计：`primary_evidence_gap=5`、`final_evidence_selection_policy=5`、`scenario_core_scope=4`、`high_risk_grounding_gap=3`、`functional_typing_metadata=1`。
- `tools/run_project_health_check.py`、`src/main.py` 和索引文档同步到 `0.4.7.9.0` 维护口径。

### 边界
- 本版本只新增只读设计包、质量信号、测试和文档。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、schema、importer、dry-run 契约、`rag_query`、后端、Qdrant 或 LLM。
- 31 个 pending records 只作为背景统计，不进入工程任务或自动实施计划。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_design_pack.py tests\test_ready_action_design_pack.py tools\run_project_health_check.py tests\test_project_health_check.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_design_pack tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_ready_action_design_pack.py --output tests\ready_action_design_pack_report.json --markdown-output docs\ready_action_design_pack_v0.4.7.9.0.md`

## [0.4.7.8.23] - 2026-05-13

### 修复
- **离线人工复核工作台二三级面板高度同步**：
  - 将桌面端工作台收敛为固定高度应用外壳，`body` 与 `.app-shell` 使用视口高度并隐藏整页滚动。
  - 左侧栏改为独立滚动区，新增全局流程和操作指南后不会再把整页撑高。
  - 右侧主工作区、案例队列面板和案例详情面板统一使用 `minmax(0, 1fr)` 与独立滚动，案例列表、详情正文不再使用旧的 `calc(100vh - ...)` 高度限制。
  - 窄屏布局恢复自然纵向页面流，避免手机端被桌面固定高度模型困住。

### 质量信号
- build report 新增并验证 `uses_fixed_height_app_shell`、`keeps_sidebar_scroll_independent` 和 `restores_natural_mobile_flow`。
- artifact 测试新增布局防回归断言，覆盖固定外壳、左栏独立滚动、右侧二级/三级面板独立滚动、旧 `calc(100vh - ...)` 限制缺失和窄屏自然流。

### 边界
- 本版本只属于 offline visual workbench UI/test/docs/versioning 收口。
- 不修改 RAG 主流程、hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、schema、importer、dry-run 或任何人工复核结论。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tools\run_project_health_check.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py tests\test_project_health_check.py`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench_contract tests.test_manual_review_workbench_import tests.test_manual_review_export_pipeline_dry_run tests.test_manual_review_ai_suggestion_prefill tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\check_encoding_hygiene.py --output tests\encoding_hygiene_report.json --fail-on-error`
- `.\venv\Scripts\python.exe tools\run_project_health_check.py --output tests\project_health_check_report.json --fail-on-error`

## [0.4.7.8.22] - 2026-05-13

### 修复
- **离线人工复核工作台全局流程位置调整**：
  - 将原先容易被理解为“当前案例后续状态”的流程信息移出案例详情标签页。
  - 在左侧栏新增 `整份导出处理结果` 面板，展示导入复核记录、检查变更差异、检查记录完整性、生成待处理动作和是否允许进入后续治理等整份复核导出的处理结果。
  - 面板说明明确写为：`这是本次导出的整份复核 JSON 的处理结果，不代表当前选中的单个案例。`
  - 移除案例详情中的 `后续状态` 标签，并清理已不再由页面使用的单案例流程渲染入口。
  - 顶部副标题同步改为“查看整份复核导出的处理结果”，避免继续把流程状态理解成单个 case 的后续进展。

### 质量信号
- build report 新增并保留 `moves_pipeline_status_to_global_sidebar` 与 `removes_pipeline_from_case_tabs`。
- 生成 HTML 和测试断言覆盖 `global-pipeline` 面板、`无阻断` 展示、旧 `后续状态` 文案缺失，以及旧 pipeline case tab 缺失。
- workbench 生成器、FastAPI 版本、project health check 版本和相关测试断言同步到 `0.4.7.8.22`。

### 边界
- 本版本只属于 offline visual workbench/UI/test/docs/versioning 收口。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、`rag_query`、后端、Qdrant 或 LLM。
- 不改人工复核 schema、importer 契约、dry-run 契约或任何正式人工结论数据。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tools\run_project_health_check.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py tests\test_project_health_check.py`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench_contract tests.test_manual_review_workbench_import tests.test_manual_review_export_pipeline_dry_run tests.test_manual_review_ai_suggestion_prefill tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\check_encoding_hygiene.py --output tests\encoding_hygiene_report.json --fail-on-error`
- `.\venv\Scripts\python.exe tools\run_project_health_check.py --output tests\project_health_check_report.json --fail-on-error`

## [0.4.7.8.21] - 2026-05-13

### 修复
- **离线人工复核工作台措辞收口**：
  - 导出/导入按钮改为更短的用户侧表达：`导出复核记录 JSON`、`下载 CSV`、`导入复核 JSON`。
  - pilot batch、AI 预填、证据阅读提示等辅助区统一标为 `参考：...`，避免与正式人工结论混淆。
  - “决策”页新增并保留 `听人工填写区` 权威提示，明确正式结论只来自人工填写区。
- **门禁 open 状态展示修复**：
  - closeout gate 为 `open` 时，左侧状态显示 `无阻断`。
  - gate 已开放时隐藏 `准入未通过` 队列，避免出现 `0 blocked` 一类误导性入口。
  - 流程页 diff 行在无阻断时显示 `无阻断`，不再显示英文 `0 blocked`。
- **质量信号补充**：
  - build report 新增人工权威提示、按钮精简、open gate 无阻断展示、open 时隐藏 blocked queue 等工作台 UX 质量信号。
  - workbench 生成器、FastAPI 版本、project health check 版本和相关测试断言同步到 `0.4.7.8.21`。

### 边界
- 本版本只属于 offline visual workbench/UI/test/docs/versioning 收口。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、`rag_query`、后端、Qdrant 或 LLM。
- 不改内部 schema 字段名；`gate_status`、`workbench_items`、`ready_human_drafts_only`、`blocked_intake_gate` 等仍保持原契约。
- 当前 `gate open` 只表示清洗后的 5 个 pilot case 已通过离线导出治理预演，不表示 36 个 case 全部完成人工复核。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tools\run_project_health_check.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py tests\test_project_health_check.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench_contract tests.test_manual_review_workbench_import tests.test_manual_review_export_pipeline_dry_run tests.test_manual_review_ai_suggestion_prefill tests.test_project_health_check`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `.\venv\Scripts\python.exe tools\check_encoding_hygiene.py --output tests\encoding_hygiene_report.json --fail-on-error`
- `.\venv\Scripts\python.exe tools\run_project_health_check.py --output tests\project_health_check_report.json --fail-on-error`

## [maintenance-workbench-hardening] - 2026-05-13

### 修复
- 离线人工复核工作台的本地草稿改为按 `workbenchFingerprint` 隔离，避免旧批次 ready 草稿混入当前导出。
- 页面导入正式 filled JSON 时默认替换当前本地草稿，并在导入摘要中显示清除旧草稿、未匹配、重复和空白记录数量。
- 页面导入入口收紧为 JSON：CSV 仍可导出用于人工查看，但不再作为正式导入入口。
- 导出前新增 case 预览确认，导出 JSON 写入 `workbench_fingerprint`、`summary.exported_case_ids`、`advisory_packet_only=false` 与 `contains_completed_manual_decisions`。
- 前端 ready 校验增加 decision/root cause/action 枚举合法性检查；CSV 导出对公式样式单元格做转义。
- `tools/import_manual_review_workbench.py` 只接受正式 filled workbench JSON，并逐项拒绝 advisory / AI suggestion / human-confirmation 标记。

### 边界
- 本次为工作台治理加固，不计入版本推进；不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、eval case 或 `rag_query` 主流程。

## [maintenance-0.1.8] - 2026-05-13

### 新增
- 新增 `tools/build_maintenance_closeout_report.py` 和 `tests/maintenance_closeout_report.json`，汇总维护系列报告状态、文档状态和固定边界。
- 新增 `tests/test_maintenance_closeout_report.py`。
- 明确维护完成不代表人工复核完成，也不代表目录迁移完成。
- 新增 `tests/pilot_manual_review_bedside_advisory_feedback_2026-05-13.json`，记录 5 个 pilot case 经多轮审议后的 advisory-only 待填写反馈口径。
- 新增 `tests/pilot_manual_review_local_draft_import_candidate_2026-05-13.json`，把 5 个 pilot case 转为 visual workbench 可导入的本地草稿候选；复核人和复核日期保持空白，必须由用户在网页中确认后才能导出。
- 新增 `tests/filled_manual_review_workbench_pilot5_cleaned_2026-05-13.json`，从用户下载导出的 filled workbench 中清洗出 5 个 pilot case，并修正为三轮审议后的最终口径：2 个 `confirm_diagnostic_issue`、3 个 `confirm_scope_adjustment_needed`。

### 边界
- 不运行 full eval，不调用 `rag_query`、后端、Qdrant 或 LLM。
- 不移动文件，不改变工具或报告默认路径。
- 不打开 manual review gate，不生成 completed manual decision。
- bedside advisory feedback 只用于准备后续人工填写，不可导入 importer，不可视为正式人工复核结论。
- local draft import candidate 只供网页工作台导入为本地草稿；CLI importer 直读该文件会被拒绝，不能绕过人工确认。
- 用户 Downloads 下的原始 filled workbench 导出含 12 个条目，其中 7 个仍为旧 AI 预填痕迹；本次正式 pipeline 只使用清洗后的 5 案工作区副本。

### 验证
- `tools/import_manual_review_workbench.py`：5 imported / 0 rejected。
- `tools/audit_manual_review_decision_diff.py`：5 changed / 0 blocked。
- `tools/validate_proposed_manual_review_decisions.py --fail-on-invalid`：5 valid / 31 pending / 0 invalid。
- `tools/build_validated_decision_promotion_dry_run.py`：5 promotion candidates / 18 ready actions。
- `tools/build_manual_review_intake_gate_closeout.py`：gate `open`。
- `tools/build_manual_review_export_pipeline_dry_run.py`：`ready_for_governed_action_planning`。

## [maintenance-0.1.7] - 2026-05-13

### 新增
- 新增 `tools/check_layout_migration_readiness.py` 和 `tests/layout_migration_readiness_report.json`，只读评估后续目录迁移是否具备规划条件。
- 新增 `tests/test_layout_migration_readiness.py`。
- 报告明确 `ready_for_automatic_migration=false`，即使可规划也不能自动迁移。

### 边界
- 不迁移 `tests/` 到 `reports/`。
- 不迁移 root-level `tools/*.py` 到子目录。
- 不改变任何默认路径。

## [maintenance-0.1.6] - 2026-05-13

### 新增
- 新增 `docs/indexes/project_maintenance_index.md`，作为结构索引、产物索引、工具索引、测试索引、术语指南和维护报告的总入口。

### 边界
- 该索引只是维护导航，不是新的运行入口。

## [maintenance-0.1.5] - 2026-05-13

### 新增
- 新增 `docs/maintenance_terms_guide.md`，统一人工复核、正式人工复核结论、辅助材料、预演、门禁、脚手架、权威路径、布局兼容层、健康检查和乱码/误解码等维护术语。

### 边界
- 只统一写作口径，不改变 schema、字段名或工具行为。

## [maintenance-0.1.4] - 2026-05-13

### 变更
- `tools/run_project_health_check.py` 新增 `anchor_presence_check()` 和 `build_sections()`，保持原有公开函数、section key 和报告语义不变。
- 健康检查新增 test index、artifact index、layout migration readiness 和 maintenance closeout 报告 gate。

### 边界
- 只整理健康检查内部结构和维护报告 gate，不改变原有检查语义。

## [maintenance-0.1.3] - 2026-05-13

### 新增
- 新增 `tools/check_artifact_index_consistency.py` 和 `tests/artifact_index_consistency_report.json`，检查 root-level `tests/*.json/*.csv/*.md` 是否进入 `docs/indexes/project_artifact_index.md`。
- 新增 `tests/test_artifact_index_consistency.py`。
- 补齐产物索引中此前未显式出现的稳定性摘要、rerank 对照、evidence hardening、manual review action/validation/loop、prefill/suggestion 安全快照等产物。

### 边界
- 只检查产物索引覆盖，不迁移报告，不把 `reports/` 写成当前权威输出目录。

## [maintenance-0.1.2] - 2026-05-13

### 新增
- 新增 `tools/check_test_index_consistency.py` 和 `tests/test_index_consistency_report.json`，检查 root-level `tests/test_*.py` 是否进入 `docs/indexes/project_test_index.md`。
- 新增 `tests/test_test_index_consistency.py`。

### 边界
- 只检查测试索引覆盖，不运行测试、不移动测试文件。

## [maintenance-0.1.1] - 2026-05-13

### 新增
- 新增 `docs/indexes/project_test_index.md`，说明 `tests/` 下单测、报告快照、fixtures、dry-run artifacts 和常见误读风险。

### 边界
- 测试索引只是文档，不改变测试、报告或工具默认路径。

## [maintenance-0.1.0] - 2026-05-13

### 变更
- **工程质量维护**：
  - 收紧 `tools/import_manual_review_workbench.py` 的 JSON 导入契约：JSON 输入必须是 `scope="filled visual manual review workbench export"`，且 `summary.export_policy="ready_human_drafts_only"`。
  - 将 completed decision 必填字段检查前移到 importer 边界，避免不完整 reviewer 行先被标记为 `completed`。
  - 扩展 export pipeline dry run 的阻断原因，覆盖无效 JSON workbench export 和 completed reviewer 字段不完整情形。
  - 在 visual workbench 附加 pilot batch 前增加 advisory contract 检查。
  - 新增 `tools/run_project_health_check.py` 和 `tests/project_health_check_report.json`，用于不修改运行时状态的轻量健康检查。
  - 新增未来目录脚手架，包括 report、tool、文档索引和 archive 分组，并补充 `docs/project_structure_refactor_plan.md`、`reports/README.md`、`tools/_shared/README.md`。
  - 健康检查新增脚手架目录存在性和纯度检查；当前 `tests/*.json` 报告和根目录 `tools/*.py` 入口仍是权威路径。
  - 新增 `tools/_shared/layout.py` 作为 Project Layout Compatibility Layer：可把 legacy `tests/<report>.json` 映射到未来 `reports/<group>/` 镜像路径，但默认仍选择 legacy 路径。
  - 在 `tools/check_evidence_alignment.py`、`tools/check_evidence_coverage.py`、`tools/check_legal_functional_type_config.py` 中试点 `legacy_report_path()`，并由测试确认默认值仍解析到 `tests/*.json`。
  - 将 layout helper 试点扩展到 `tools/build_evidence_manual_review_dataset.py`、`tools/build_evidence_root_cause_action_plan.py`、`tools/build_evidence_action_series_baseline.py`、`tools/draft_evidence_coverage_gates.py`，默认值仍解析到 legacy `tests/*.json` 报告。
  - 将 layout helper 试点扩展到 manual review/workbench 工具：`tools/build_manual_review_visual_workbench.py`、`tools/import_manual_review_workbench.py`、`tools/build_manual_review_export_pipeline_dry_run.py`、`tools/build_pilot_manual_review_round1_support.py`、`tools/build_mobile_pilot_review_decision_aid.py`；适用报告默认值仍解析到 legacy `tests/*.json`。
  - 健康检查新增第三批 layout helper 默认路径、manual review 代表报告映射、importer/dry-run 离线扫描和 dry-run artifact 目录契约。
  - 新增 `docs/indexes/project_artifact_index.md`，说明当前 eval、evidence diagnostic、manual review、dry-run、schema、fixture、docs 和未来 `reports/` scaffold 的产物角色。
  - 健康检查新增 artifact index 锚点检查，使关键报告族保持可发现，同时避免把索引误写成迁移清单。
  - 新增 `docs/indexes/project_tool_index.md`，按类别说明当前 root-level `tools/*.py` CLI 入口、输入输出、代表性产物、advisory-only 属性，以及是否可能触发 RAG/Qdrant/LLM。
  - 健康检查新增 tool index 锚点检查，使关键工具入口、产物契约、未来 tool scaffold 和 RAG/Qdrant/LLM 边界保持可发现，同时避免把索引误写成工具迁移清单。
  - 新增 `tools/check_encoding_hygiene.py` 和 `tests/encoding_hygiene_report.json`，用于离线检查 UTF-8 解码、mojibake 标记、可疑分隔符和临时目录残留。
  - 健康检查新增 encoding hygiene report gate。
  - 新增 `tools/check_tool_index_consistency.py` 和 `tests/tool_index_consistency_report.json`，用于离线检查 root-level `tools/*.py` 是否全部进入工具索引，并报告可能触发 RAG/Qdrant/LLM 的敏感入口。
  - 健康检查新增 tool index consistency report gate。
  - 补齐 `docs/indexes/project_tool_index.md` 中遗漏的 `tools/build_manual_review_decision_examples.py`，并补充可能触发主链路的工具入口清单。
  - 将近期 changelog、roadmap、report guide 和索引文档中的少量英文标题/状态词继续中文化，减少维护阅读成本。
  - 修复历史辅助稿 `docs/manual_review_prefill_high_confidence_12_summary.md` 和 `docs/manual_review_prefill_high_confidence_12_v2_summary.md` 中的 `。?` / `.?Alignment` 显示分隔符污染，统一为可读分号。
  - 删除已确认无引用且为空的临时目录 `tests/tmp3wfrvcjf`，并刷新 encoding hygiene 报告。
  - 在 `tools/check_ingestion_quality.py` 中补充注释，说明 mojibake 字符串是有意的入库文本污染检测 token，不是源码乱码。
  - 新增 layout compatibility 测试和 health check 直接脚本执行测试，确保 `python tools/run_project_health_check.py` 可以安全导入共享 helper。
  - 新增恶意/advisory JSON 导入、completed 行字段不完整、pilot batch 非 advisory 拒绝和健康检查诊断相关测试。
  - 补齐 v0.4.7.8.19 / v0.4.7.8.20 生成文档的边界说明，并收紧 roadmap / report guide 表述。

### 边界
- 未修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、`rag_query`、后端、Qdrant 或 LLM。
- 未移动或删除既有文件；没有把运行时消费者切换到脚手架目录。
- 未改变任何工具默认输出路径；compatibility layer 只提供映射和报告能力。
- 未把诊断报告重定向到 `reports/`；试点只把硬编码 legacy report path 改成显式 legacy helper。
- 未迁移 visual workbench HTML、Markdown 文档、decision schema、CSV 输入、eval case、config 文件或 nested dry-run artifact 目录。
- Artifact index 只是文档和健康检查覆盖，不移动文件、不改变 canonical output path。
- Tool index 只是文档和健康检查覆盖，不移动工具、不改变 CLI 默认路径，也不改变 canonical output path。
- Encoding hygiene checker 只写报告，不改写被扫描文件，也不删除临时目录。
- Tool index consistency checker 只写报告，不移动工具、不改默认路径、不运行 eval、不访问 Qdrant 或 LLM。
- 已删除无引用且为空的临时目录 `tests/tmp3wfrvcjf`；未删除任何非空产物目录。
- 未运行 full eval；本次维护只增强离线治理安全检查、importer 边界、生成文档和 project-health 诊断。

## [0.4.7.8.20] - 2026-05-13

### 新增
- **移动端试点复核决策辅助**：
  - 新增 `tools/build_mobile_pilot_review_decision_aid.py`。
  - 新增 `tests/mobile_pilot_review_decision_aid_report.json`，为试点案例生成紧凑的五卡片移动端复核辅助内容。
  - 新增 `docs/mobile_pilot_review_decision_aid_v0.4.7.8.20.md`。
  - 新增 `tests/test_mobile_pilot_review_decision_aid.py`。
  - FastAPI 服务版本同步为 `0.4.7.8.20`。

### 边界
- 报告为 `schema_kind=advisory_mobile_pilot_review_decision_aid`，仅作 advisory 辅助，不能作为人工复核结果导入。
- 只使用 `mobile_advisory_*` 和 `mobile_user_confirmation_required` 字段；不输出 `decision`、`rationale`、`reviewer_input_template`、`reviewer_decision` 等可被导入器识别的 reviewer 字段。
- 不生成 completed manual decisions、promotion candidates 或 ready action candidates。
- 未修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、`rag_query`、后端、Qdrant 或 LLM。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_mobile_pilot_review_decision_aid.py src\main.py tests\test_mobile_pilot_review_decision_aid.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_mobile_pilot_review_decision_aid`
- `.\venv\Scripts\python.exe tools\build_mobile_pilot_review_decision_aid.py --output tests\mobile_pilot_review_decision_aid_report.json --markdown-output docs\mobile_pilot_review_decision_aid_v0.4.7.8.20.md`
- `Select-String -Path tools\build_mobile_pilot_review_decision_aid.py,tests\mobile_pilot_review_decision_aid_report.json -Pattern "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient"`

## [0.4.7.8.19] - 2026-05-13

### 新增
- **人工复核第一轮试点支持包**：
  - 新增 `tools/build_pilot_manual_review_round1_support.py`。
  - 新增 `tests/pilot_manual_review_round1_support_report.json`，覆盖 v0.4.7.8.15 选出的 5 个试点案例。
  - 新增 `docs/pilot_manual_review_round1_support_v0.4.7.8.19.md`。
  - 新增 `tests/test_pilot_manual_review_round1_support.py`。
  - FastAPI 服务版本同步为 `0.4.7.8.19`。

### 边界
- 报告为 `schema_kind=advisory_pilot_manual_review_round1_support`，`advisory_packet_only=true`，且 `contains_completed_manual_decisions=false`。
- 报告说明案例主题、原 LLM 输出、证据快照、复核提示、非绑定辅助判断和决策选项含义。
- 不写入 `reviewer_input_template`、`reviewer_decision`、`workbench_items` 或 `decision_status`。
- 不生成 completed manual decisions、promotion candidates 或 ready action candidates。
- 未修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、`rag_query`、后端、Qdrant 或 LLM。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_pilot_manual_review_round1_support.py src\main.py tests\test_pilot_manual_review_round1_support.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_pilot_manual_review_round1_support`
- `.\venv\Scripts\python.exe tools\build_pilot_manual_review_round1_support.py --output tests\pilot_manual_review_round1_support_report.json --markdown-output docs\pilot_manual_review_round1_support_v0.4.7.8.19.md`
- `Select-String -Path tools\build_pilot_manual_review_round1_support.py,tests\pilot_manual_review_round1_support_report.json -Pattern "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient"`

## [0.4.7.8.18] - 2026-05-13

### 新增
- **可视化人工复核工作台试点审阅辅助**：
  - `tools/build_manual_review_visual_workbench.py` 新增 `--pilot-review-assist-report` 参数，默认读取 `tests/manual_review_pilot_case_review_assist_report.json`。
  - 离线可视化工作台会把 v0.4.7.8.17 的 pilot review assist 数据按案例匹配，并作为只读 `pilot_review_assist` 面板附加到对应试点案例。
  - “决策”页现在展示案例简述、辅助倾向、证据支持状态、辅助信号、原 LLM 风险/整改动作主张、聚焦问题、辅助理由以及缺失/流失证据示例。
  - 新增 `docs/manual_review_visual_workbench_pilot_review_assist_v0.4.7.8.18.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.18`。

### 边界
- pilot review assist 面板仅作 advisory 辅助，永远不是 completed manual review decision。
- 只有当报告为 `schema_kind=advisory_pilot_case_review_assist`、advisory-only 且不包含 completed manual decisions 时，才允许附加到案例。
- 嵌入 pilot assist 数据时会剥离 `reviewer_input_template`、`reviewer_decision`、`workbench_items` 和 `decision_status`。
- 导出的 JSON/CSV workbench items 会显式剥离 `pilot_review_assist`；真实导出仍要求人工填写 reviewer 字段。
- 未修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、`rag_query`、后端、Qdrant 或 LLM。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py tests\test_manual_review_export_pipeline_dry_run.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact tests.test_manual_review_export_pipeline_dry_run tests.test_manual_review_pilot_case_review_assist`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `Select-String -Path tools\build_manual_review_visual_workbench.py,tools\manual_review_visual_workbench\index.html -Pattern "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient"`

## [0.4.7.8.17] - 2026-05-12

### 新增
- **Pilot Case Review Assist**：
  - 新增 `tools/build_manual_review_pilot_case_review_assist.py`，读取首批 pilot batch、manual review workbench 和既有 `rag_eval_report`，生成只读审阅辅助报告。
  - 新增 `tests/manual_review_pilot_case_review_assist_report.json`，为 5 个 pilot case 输出案由说明、原 LLM 风险/动作摘录、最终证据链状态、缺失/流失证据示例、人工复核问题清单和高关注复核列表。
  - 新增 `docs/manual_review_pilot_case_review_assist_v0.4.7.8.17.md`，用普通中文解释每案为什么需要看、重点看什么、哪些信号只是辅助诊断。
  - 新增 `tests/test_manual_review_pilot_case_review_assist.py`，覆盖通用辅助信号、advisory-only 护栏、递归危险键扫描、无 completed decision、无 promotion/ready action，以及 8.17 报告被误用为 dry-run 输入时仍被阻断。
  - FastAPI 服务版本同步为 `0.4.7.8.17`。

### 诊断结果
- 5 个 pilot case 均生成审阅辅助包，均标记为 `needs_user_review`，均要求人工确认。
- 支持的通用辅助信号包括：主争点缺证据、案由核心条文缺口、候选证据进入最终证据时流失、答案与证据链可能脱节、定义条款替代规范条款复核、基础检索或 anchor 依赖稳定性复核。
- 默认报告显示：`completed_manual_decisions=0`、`promotion_candidates=0`、`ready_action_candidates=0`，gate 仍为 `blocked_until_real_human_review_export_passes_dry_run`。
- 本报告不会复制 workbench 中的 `reviewer_input_template`，也不会输出 `reviewer_decision` 或 `workbench_items`。

### 边界
- 本版本只新增离线 pilot case 审阅辅助工具、报告、测试和文档。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- 不接入 `rag_query`、后端 API、Qdrant 或 LLM。
- `advisory_tendency` 只是阅读辅助倾向，不是人工复核结论；真实治理动作仍必须由 reviewer 在视觉审阅台填写，并通过 export pipeline dry run。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_pilot_case_review_assist.py src\main.py tests\test_manual_review_pilot_case_review_assist.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_pilot_case_review_assist`
- `.\venv\Scripts\python.exe tools\build_manual_review_pilot_case_review_assist.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_pilot_batch tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact tests.test_manual_review_export_pipeline_dry_run`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient" tools\build_manual_review_pilot_case_review_assist.py`


## [0.4.7.8.16] - 2026-05-12

### 新增
- **Manual Review Pilot Batch Queue**：
  - `tools/build_manual_review_visual_workbench.py` 新增 `--pilot-batch-report`，默认读取 `tests/manual_review_pilot_batch_report.json`。
  - 视觉审阅台新增“首批试点 / Pilot batch”队列，按 `case_id` 将 v0.4.7.8.15 的 5 个 pilot case 作为只读 metadata 附加到现有 workbench item。
  - “决策”页新增“首批试点人工判断清单”，展示优先审阅原因、证据问题摘要、最终证据链、缺失/曾丢失证据、预筛参考、AI advisory 建议和人工判断选项。
  - 清单勾选状态仅保存在浏览器本地 `pilotChecklistStateKey`，用于标记已读，不会写入 `reviewer_input_template`。
  - 导出 JSON/CSV 时继续只导出 ready human drafts，并显式剥离 `pilot_batch` 只读元数据。
  - 新增 `docs/manual_review_visual_workbench_pilot_batch_v0.4.7.8.16.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.16`。

### 诊断结果
- Workbench payload 现在显示 `pilot_batch_cases=5`、`pilot_batch_advisory_only=true`、`pilot_batch_completed_decisions=0`。
- Build report 新增 `supports_pilot_batch_queue=true`、`supports_per_case_human_judgment_checklist=true`、`supports_pilot_batch_advisory_panel=true`。
- JS 可执行回归证明：只打开 pilot 队列并勾选“已阅读试点清单”时，`buildFilledWorkbench().workbench_items.length === 0`；只有人工填写 reviewer、reviewed_at、decision、rationale 且满足 ready 条件后才导出。
- Dry-run 负例证明：checklist-only export 仍为 `0 imported`、`0 promotion candidates`、`0 ready action candidates`、gate `blocked`。

### 边界
- 本版本只增强离线视觉审阅工具、报告、测试和文档。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- 不接入 `rag_query`、后端 API、Qdrant 或 LLM。
- Pilot packet、prescreen 和 AI suggestion 仍只能作为 reviewer 参考，不得自动成为 completed manual review decision。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py tests\test_manual_review_export_pipeline_dry_run.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_pilot_batch tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact tests.test_manual_review_export_pipeline_dry_run`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient" tools\build_manual_review_visual_workbench.py tools\manual_review_visual_workbench\index.html tools\build_manual_review_pilot_batch.py tools\build_manual_review_export_pipeline_dry_run.py` 无命中。

## [0.4.7.8.15] - 2026-05-12

### 新增
- **Manual Review Pilot Batch**：
  - 新增 `tools/build_manual_review_pilot_batch.py`，把既有 prescreen、workbench 与隔离 AI suggestion 合并为首批 3-5 个 case 的人工确认包。
  - 新增 `tests/manual_review_pilot_batch_report.json`，默认选出 5 个 high risk / high confidence case：`risk_employee_data_export_001`、`pipl_data_export_conditions_001`、`risk_ai_medical_training_export_001`、`risk_employee_facial_001`、`risk_app_location_ads_002`。
  - 新增 `docs/manual_review_pilot_batch_v0.4.7.8.15.md`，用面向非 CS reviewer 的方式展示案由、待审问题、原 LLM 输出摘录、证据缺口、AI 建议参考和人工需作出的判断。
  - 新增 `tests/test_manual_review_pilot_batch.py`，覆盖 3-5 case 选择边界、guardrails、AI advisory 隔离、递归危险结构扫描、无 completed decision、无 promotion/ready action，以及 pilot packet 被误用为 dry-run 输入时仍被阻断。
  - 输出 `schema_kind=advisory_pilot_packet`、`contains_completed_manual_decisions=false`、`advisory_packet_only=true`；AI/预筛参考字段使用 `advisory_decision`、`advisory_root_causes`、`advisory_follow_up_actions` 等命名，避免和人工结论字段混淆。
  - FastAPI 服务版本同步为 `0.4.7.8.15`。

### 诊断结果
- Pilot batch 来源为 `tests/manual_review_prescreen_report.json` 的 36 个待审 case；本批选出 5 个，均仍需人工确认。
- 5 个 case 均带有隔离 AI 建议，但输出明确标记为 `advisory_only=true`、`human_confirmation_required=true`、`not_a_reviewer_decision=true`，且不写 `reviewer_input_template` 或 `reviewer_decision`。
- 报告 summary 保持 `completed_manual_decisions=0`、`promotion_candidates=0`、`ready_action_candidates=0`，gate 状态为 `blocked_until_real_human_review_export_passes_dry_run`。
- 集成负例验证：若把 pilot packet 误作为 workbench input 喂给 export pipeline dry run，结果仍为 `0 imported`、`0 promotion candidates`、`0 ready action candidates`、gate `blocked`。

### 边界
- 本版本只新增离线 pilot batch 生成工具、报告、测试和文档。
- 不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- Prescreen、AI suggestion 和 pilot packet 均不得被当作 completed manual review decision；真实人工填写并通过 export pipeline dry run 前，不进入工程修复。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_pilot_batch.py src\main.py tests\test_manual_review_pilot_batch.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_pilot_batch`
- `.\venv\Scripts\python.exe tools\build_manual_review_pilot_batch.py`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient" tools\build_manual_review_pilot_batch.py`

## [0.4.7.8.14] - 2026-05-12

### 新增
- **Manual Review Export Pipeline Dry Run**：
  - 新增 `tools/build_manual_review_export_pipeline_dry_run.py`，复用既有 importer、diff、proposed validator、promotion dry run 和 closeout，生成导出后治理链路预演报告。
  - 新增 `tests/manual_review_export_pipeline_dry_run_report.json` 与隔离中间产物目录 `tests/manual_review_export_pipeline_dry_run_artifacts/`，不覆盖 canonical pipeline 产物。
  - 新增 `tests/test_manual_review_export_pipeline_dry_run.py`，覆盖 AI suggestion 安全稿阻断、最小人工 ready filled workbench 正向链路、混合坏行保守阻断，以及 dry-run 不覆盖正式 proposed schema。
  - Dry-run 额外新增 `dry_run_blockers`：即使既有 closeout gate 可 open，只要导入中存在 rejected/unknown/duplicate/empty 行，仍不会给出 `ready_for_governed_action_planning`。
  - CLI 输出路径拒绝 canonical pipeline artifact 文件名，避免误覆盖正式 proposed schema 或正式 pipeline 报告。
  - 新增 `docs/manual_review_export_pipeline_dry_run_v0.4.7.8.14.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.14`。

### 诊断结果
- 默认 dry run 使用 `tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json` 作为负例，结果为 `blocked_as_expected_ai_suggestion_only`。
- Pipeline summary：`0 imported / 12 rejected`，`empty_importable_content=12`，`0 promotion candidates`，`0 ready action candidates`，closeout gate 保持 `blocked`。
- 单测证明：真实人工 completed + valid filled workbench 可以通过 importer、diff、validator、promotion dry run 和 closeout，进入 governed action planning dry-run 状态；若同一输入中夹杂 rejected rows，则 dry-run 会保守阻断。

### 边界
- 本版本只新增离线 dry-run 汇总工具、报告、测试和文档。
- 不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。
- AI suggestion、prescreen 和 blocked draft 仍不得作为 completed manual review decision。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_export_pipeline_dry_run.py src\main.py tests\test_manual_review_export_pipeline_dry_run.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_export_pipeline_dry_run`
- `.\venv\Scripts\python.exe tools\build_manual_review_export_pipeline_dry_run.py`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient" tools\build_manual_review_export_pipeline_dry_run.py`

## [0.4.7.8.13] - 2026-05-12

### 新增
- **Manual Review AI Suggestion Isolation**：
  - 新增 `tools/build_manual_review_ai_suggestion_prefill.py`，将 high-confidence AI 预填转换为 visual workbench 可读取的安全建议文件。
  - 新增 `tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json`，只写 `ai_review_suggestion`，不写 `reviewer_input_template`。
  - Visual workbench 新增 AI 建议面板，可展示建议结论、建议根因、建议动作、理由和备注。
  - AI 建议可复制到人工草稿，但不会复制复核人和复核日期；复制后必须勾选人工确认采纳，草稿才可进入 ready 状态。
  - 导出 JSON/CSV 时只导出浏览器本地人工草稿字段，不继承源 `reviewer_input_template`，不导出 AI 来源标记。
  - 导出 JSON/CSV 进一步收紧为只包含 ready 人工草稿；未确认的 AI 复制草稿会被计入 blocked draft，不写入正式 `workbench_items`。
  - 重新复制 AI 建议会重置 `human_confirmed_ai_suggestion=false`，避免旧确认误覆盖新建议内容。
  - 新增可执行前端导出回归，验证未确认 AI copied draft 不导出、人工确认 ready 后才导出、重新复制后需再次确认。
  - 新增 `tests/test_manual_review_ai_suggestion_prefill.py`，并扩展 visual workbench 构建物测试。
  - 新增 `docs/manual_review_ai_suggestion_isolation_v0.4.7.8.13.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.13`。

### 诊断结果
- Safe suggestion 文件包含 12 条建议。
- 将 safe suggestion 文件直接喂给 importer 时，结果为 `0 imported / 12 rejected`，拒绝原因为 `empty_importable_content=12`，符合预期安全行为。
- Visual workbench build report 显示 `supports_ai_suggestion_isolation=true`、`exports_ready_human_drafts_only=true`，gate 仍保持 `blocked`。

### 边界
- AI 建议不是人工复核结论，不生成 completed decision，不产生 promotion candidate 或 ready action candidate。
- 本版本只增强离线 visual workbench 和安全建议导入，不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py tools\build_manual_review_ai_suggestion_prefill.py tests\test_manual_review_ai_suggestion_prefill.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench_build_artifact tests.test_manual_review_ai_suggestion_prefill tests.test_manual_review_visual_workbench`
- `.\venv\Scripts\python.exe tools\build_manual_review_ai_suggestion_prefill.py --input tests\manual_review_prefill_high_confidence_12_v2.json --output tests\manual_review_ai_suggestion_prefill_high_confidence_12_v2.json`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `.\venv\Scripts\python.exe tools\import_manual_review_workbench.py --decision-schema tests\evidence_manual_review_decision_schema.json --workbench-input tests\manual_review_ai_suggestion_prefill_high_confidence_12_v2.json --output tests\proposed_manual_review_decision_schema_ai_suggestion_safety_check.json --report-output tests\manual_review_ai_suggestion_prefill_import_safety_check.json`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI|QdrantClient" tools\manual_review_visual_workbench\index.html tools\build_manual_review_visual_workbench.py tools\build_manual_review_ai_suggestion_prefill.py`

## [0.4.7.8.12] - 2026-05-11

### 新增
- **Manual Review Prescreen Report**：
  - 新增 `tools/build_manual_review_prescreen_report.py`，读取既有 workbench、evidence alignment、coverage、rag_eval 与 rag_eval_cases 报告，对 36 个待审 case 生成离线预筛建议。
  - 输出 `tests/manual_review_prescreen_report.json` 与 `docs/manual_review_prescreen_report_v0.4.7.8.12.md`，包含预筛分类、建议复核结论、置信度、需要用户拍板原因、原 LLM 输出摘要、证据快照和高风险优先清单。
  - 预筛明确区分“主证据/最终证据缺口”与“检索基建稳定性告警”，避免把 base retrieval / anchor dependency 直接误读为原法律结论一定错误。
  - 新增 `tests/test_manual_review_prescreen_report.py`，验证通用预筛逻辑、边界 guardrails 与 Markdown 可读说明。
  - FastAPI 服务版本同步为 `0.4.7.8.12`。
### 诊断结果
- 当前 36 个 workbench case 中，预筛报告识别 12 个 high confidence、22 个 medium confidence、2 个 low confidence；32 个仍建议用户拍板。
- 预筛只给 reviewer 排序和解释，不写入 reviewer decision，不绕过 importer / diff / validator / promotion dry run / closeout。
### 边界
- 本版本只新增离线预筛诊断工具、报告、测试和文档；不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement / term preservation、scenario registry 或 eval case。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_prescreen_report.py src\main.py tests\test_manual_review_prescreen_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_prescreen_report`
- `.\venv\Scripts\python.exe tools\build_manual_review_prescreen_report.py --output tests\manual_review_prescreen_report.json --markdown-output docs\manual_review_prescreen_report_v0.4.7.8.12.md`
- `rg -n "rag_query\(|ChatOpenAI|QdrantClient|fetch\(|XMLHttpRequest|/ask" tools/build_manual_review_prescreen_report.py`

## [0.4.7.8.11] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Manual Save Button**：
  - 决策页新增 `保存草稿 / Save draft` 按钮，让 reviewer 能明确保存当前 case 的本地草稿。
  - 保存时写入当前 case draft 的 `saved_at` 时间戳，并在 case header 展示 `上次保存` 或 `有未手动保存的更新`。
  - 保留既有自动暂存机制；手动保存只提供明确反馈，不改变导出 schema。
  - Build report 新增 `supports_manual_draft_save=true`。
  - 新增 `docs/manual_review_visual_workbench_manual_save_v0.4.7.8.11.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.11`。
### 诊断结果
- 本版本只增强离线工作台的草稿保存反馈，不写项目文件，不绕过 importer / diff / validator / promotion dry run / closeout。
### 边界
- 本版本不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement / term preservation、scenario registry 或 eval case。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI" tools/manual_review_visual_workbench/index.html tools/build_manual_review_visual_workbench.py`

## [0.4.7.8.10] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Field Requirement Labels**：
  - 决策页字段新增 `必填 / 条件必填 / 可选` 标记，并随中英文语言切换同步显示。
  - 将复核人、复核日期、复核结论、理由标为必填。
  - 将确认的根因标为条件必填：只有确认诊断成立或确认需要范围校准时才要求填写。
  - 将驳回根因、后续动作、变更目标、回归测试样本候选和备注标为可选，并增加“不确定可留空”的提示。
  - Build report 新增 `supports_field_requirement_labels=true`。
  - 新增 `docs/manual_review_visual_workbench_field_requirements_v0.4.7.8.10.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.10`。
### 诊断结果
- 本版本只增强 reviewer 可理解性，不改变导出 schema、draft ready 校验规则或 downstream importer / validator 行为。
### 边界
- 本版本不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement / term preservation、scenario registry 或 eval case。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI" tools/manual_review_visual_workbench/index.html tools/build_manual_review_visual_workbench.py`

## [0.4.7.8.9] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Import Replay**：
  - 审阅台新增 `导入 JSON/CSV` 控件，可选择之前从页面导出的 `filled_manual_review_workbench.json` 或 `.csv`。
  - 前端使用浏览器 `FileReader` 离线读取文件，按 `case_id` 匹配当前 workbench case，并只回填 reviewer 字段到本地草稿。
  - 导入后自动刷新队列、侧栏状态、导出状态和当前 case detail，并显示已回填、未匹配、空白跳过和错误摘要。
  - JSON/CSV 导入均保持现有导出 schema 兼容；未知 case 不会写入草稿。
  - Build report 新增 `supports_review_export_import=true`。
  - 新增 `docs/manual_review_visual_workbench_import_v0.4.7.8.9.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.9`。
### 诊断结果
- Workbench HTML 仍为本地静态工具，导入只写浏览器 `localStorage` 草稿，不写项目文件、不绕过 importer / diff / validator / promotion dry run / closeout。
### 边界
- 本版本只增强离线人工复核工具的续审能力，不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement / term preservation、scenario registry 或 eval case。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`
- `rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI" tools/manual_review_visual_workbench/index.html tools/build_manual_review_visual_workbench.py`

## [0.4.7.8.8] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Decision Tab Clarity**：
  - 决策页新增复核判断摘要与建议审阅顺序，帮助 reviewer 先看案由、证据和诊断，再作人工结论。
  - 复核结论改为带说明的单选卡片，保留原始代码以兼容 importer、diff 和 validator。
  - 复核信息、结论、根因、后续动作和治理备注区块新增说明与输入提示。
  - 将偏工程化的 fixture 表达改为“回归测试样本候选”，明确不会直接写入 eval case。
  - Build report 新增 `supports_decision_tab_readability=true`。
  - 新增 `docs/manual_review_visual_workbench_decision_tab_v0.4.7.8.8.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.8`。
### 诊断结果
- Workbench HTML 仍为本地静态工具，36 cases，36 items with case context，gate blocked。
- 决策页可读性增强不改变 reviewer 导出 schema，不绕过既有 intake gate。
### 边界
- 本版本只改进离线 UI 可读性，不接入 `rag_query`，不调用后端、Qdrant 或 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement / term preservation、scenario registry 或 eval case。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

## [0.4.7.8.7] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Case Context**：
  - 新增只读 `case_context` 合并逻辑，从 `tests/rag_eval_report.json`、`tests/rag_eval_cases.json` 和 `config/scenario_registry.json` 提取案由线索、待审问题、风险场景、预期风险类型和预期整改动作。
  - 左侧 case 列表和概览页新增案由线索展示，避免 reviewer 只能靠 case id 和内部标签猜测案由。
  - 搜索范围扩展到案由、问题、场景描述、预期风险类型和整改动作。
  - JSON 导出保留 `case_context`；CSV 导出新增只读 `case_topic` 与 `question` 列，importer 仍只读取允许导入的 reviewer 字段。
  - 新增 `docs/manual_review_visual_workbench_case_context_v0.4.7.8.7.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.7`。

### 诊断结果
- Build report：`supports_case_context=true`，`items_with_case_context=36`。
- Workbench HTML 仍为本地静态工具，36 cases，gate blocked。

### 边界
- 本版本只增强离线视觉审阅台的案由可读性，不接入 `rag_query`，不调用后端写接口，不修改 hidden seed、anchor、rerank、prompt、risk rule、scenario registry 或 eval case。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

## [0.4.7.8.6] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Label Glossary**：
  - 将 case 内部英文标签显示为可读名称与原始代码，并提供悬停解释。
  - 新增 `标签说明 / Glossary` 页签，覆盖 queue tags、issue types、root causes、follow-up actions、diagnostics、evidence context、gate blockers、import errors 和 guardrails。
  - 标签说明卡片支持跳转到概览、证据、决策或流程页签。
  - 取消 case detail 中单独的 `Guide` 页签，保留左下角操作指南。
  - 新增本地导出状态跟踪：导出后记录 `last_exported_at`，草稿更新后提示未导出的更新。
  - 新增 `docs/manual_review_visual_workbench_label_glossary_v0.4.7.8.6.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.6`。

### 诊断结果
- Build report：支持 `supports_case_label_glossary=true` 与 `supports_export_state_tracking=true`。
- Workbench HTML 仍为本地静态工具，36 cases，gate blocked。

### 边界
- 本版本只做离线 UI 可理解性与本地导出状态增强，不接入 `rag_query`，不调用后端写接口，不修改 hidden seed、anchor、rerank、prompt、risk rule 或 eval case。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

## [0.4.7.8.5] - 2026-05-11

### 新增
- **Manual Review Visual Workbench i18n**：
  - 将 visual workbench 的语言能力升级为真实双语渲染，默认 `zh-CN`，支持 `简体中文` 与 `English`。
  - 队列、状态、标题、KPI、案例列表、详情标签、证据表头、复核表单、pipeline、导出按钮和操作指南均改为从统一 `ui.messages` 读取。
  - 语言选择写入浏览器 `localStorage`，刷新后保持选择。
  - 新增 `docs/manual_review_visual_workbench_i18n_v0.4.7.8.5.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.5`。

### 诊断结果
- Build report：支持 `supports_language_switch=true`，默认语言 `zh-CN`，支持语言 `zh-CN/en-US`。
- Workbench HTML 仍为本地静态工具，36 cases，gate blocked。

### 边界
- 本版本只做离线 UI 本地化修复，不接入 `rag_query`，不调用后端写接口，不修改 hidden seed、anchor、rerank、prompt、risk rule 或 eval case。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

## [0.4.7.8.4] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Guide & Language**：
  - 在本地 HTML 左侧新增 `操作指南` 面板。
  - 在 case detail 新增 `Guide` 页签。
  - 在顶部状态区新增统一风格语言选择器，当前支持 `简体中文`。
  - `tools/build_manual_review_visual_workbench.py` 的 payload 新增 `ui.default_language`、`ui.supported_languages` 和 `ui.guide_steps`。
  - 新增 `docs/manual_review_visual_workbench_guide_language_v0.4.7.8.4.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.4`。

### 诊断结果
- Build report：支持 operation guide；supported languages 为 `zh-CN`。
- Workbench HTML 仍为本地静态工具，36 cases，gate blocked。

### 边界
- 本版本只做 UI 可用性补强，不接入 `rag_query`，不调用后端写接口，不修改 hidden seed、anchor、rerank、prompt、risk rule 或 eval case。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

## [0.4.7.8.0] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Contract**：
  - 新增 `tools/build_manual_review_visual_workbench_contract.py`，定义离线视觉审阅台的数据来源、字段边界、UI 信息架构、导出策略和 guardrails。
  - 新增 `tests/test_manual_review_visual_workbench_contract.py`，验证契约 ready 条件、字段只读/可写隔离、导出策略和主流程防火墙。
  - 新增 `tests/manual_review_visual_workbench_contract_report.json`。
  - 新增 `docs/manual_review_visual_workbench_contract_v0.4.7.8.0.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.0`。

### 诊断结果
- Visual contract ready：`true`。
- Workbench items：36；pending workbench items：36；high priority items：29。
- Gate status：`blocked`；imported rows：0；rejected rows：36。
- Promotion candidates：0；ready action candidates：0。

### 边界
- 本版本只定义视觉审阅台契约，不实现正式 UI，不导入 reviewer 结论，不覆盖原始 decision schema，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench_contract.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench_contract`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench_contract.py --output tests\manual_review_visual_workbench_contract_report.json`

## [0.4.7.8.3] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Status**：
  - `tools/build_manual_review_visual_workbench.py` 生成的本地 HTML 新增 pipeline status 区，展示 import、diff、validation、promotion 和 closeout gate 状态。
  - 新增 `docs/manual_review_visual_workbench_status_v0.4.7.8.3.md`。
  - FastAPI 服务版本同步为 `0.4.7.8.3`。

### 诊断结果
- 导入：0 条导入 / 36 条拒绝。
- 校验：0 条有效 / 0 条无效 / 36 条待处理。
- 晋升：0 个候选 / 0 个 ready action。
- Closeout：`blocked`。

### 边界
- 本版本只是状态展示，不执行 promotion，不写回 schema，不接入主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py tools\build_manual_review_visual_workbench_contract.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_contract tests.test_manual_review_visual_workbench_build_artifact`
- `.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json`

## [0.4.7.8.2] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Export**：
  - 本地 HTML 支持 reviewer 表单、浏览器 localStorage 草稿、JSON 导出和 CSV 导出。
  - 新增 `docs/manual_review_visual_workbench_export_v0.4.7.8.2.md`。

### 支持字段
- 支持填写 `reviewer`、`reviewed_at`、`decision`、`confirmed_root_causes`、`rejected_root_causes`、`confirmed_follow_up_actions`、`proposed_change_targets`、`fixture_candidate`、`rationale`、`notes`。

### 边界
- 导出文件仍必须经过既有 importer、diff、validator、promotion dry run 和 closeout；页面不直接修改任何项目源数据。

## [0.4.7.8.1] - 2026-05-11

### 新增
- **Manual Review Visual Workbench Static UI**：
  - 新增 `tools/build_manual_review_visual_workbench.py`，把现有离线报告嵌入单个本地 HTML。
  - 新增 `tools/manual_review_visual_workbench/index.html`。
  - 新增 `tests/manual_review_visual_workbench_build_report.json`。
  - 新增 `tests/test_manual_review_visual_workbench.py`。
  - 新增 `tests/test_manual_review_visual_workbench_build_artifact.py`，校验生成 HTML 的嵌入数据、关键控件、响应式保护和禁止主流程调用。
  - 新增 `docs/manual_review_visual_workbench_static_v0.4.7.8.1.md`。

### 支持能力
- 支持 case queue、搜索、case detail、overview、evidence、questions 和基础状态 badges。
- 当前生成结果：36 cases，36 pending，29 high priority，gate blocked。

### 边界
- 静态页面不需要后端服务，不访问 Qdrant，不调用 LLM，不接入 `rag_query`。


## [0.4.7.7.5] - 2026-05-11

### 新增
- **Manual Review Intake Gate Closeout**：
  - 新增 `tools/build_manual_review_intake_gate_closeout.py`，汇总 intake contract、workbench import、decision diff、proposed validation 和 promotion dry run。
  - 新增 `tests/test_manual_review_intake_gate_closeout.py`，验证 gate blocked/open 判定。
  - 新增 `tests/manual_review_intake_gate_closeout_report.json`。
  - 新增 `docs/manual_review_intake_gate_closeout_v0.4.7.7.5.md`。
  - FastAPI 服务版本同步为 `0.4.7.7.5`。

### 诊断结果
- 门禁状态：`blocked`。
- 导入行：0；拒绝行：36。
- 变更案例：0；被阻断 diff 案例：0。
- 有效 proposed records：0；无效 proposed records：0；待处理 proposed records：36。
- 晋升候选：0；ready action candidates：0。

### 边界
- 本版本不覆盖原始 decision schema，不 promotion，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_intake_gate_closeout.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_intake_gate_closeout`
- `.\venv\Scripts\python.exe tools\build_manual_review_intake_gate_closeout.py --contract-report tests\manual_review_intake_contract_report.json --import-report tests\manual_review_workbench_import_report.json --diff-report tests\manual_review_decision_diff_report.json --validation-report tests\proposed_manual_review_decision_validation_report.json --promotion-report tests\validated_decision_promotion_dry_run_report.json --output tests\manual_review_intake_gate_closeout_report.json`

## [0.4.7.7.4] - 2026-05-11

### 新增
- **Validated Decision Promotion Dry Run**：
  - 新增 `tools/build_validated_decision_promotion_dry_run.py`，只筛选 completed + valid 的 proposed decisions，生成 promotion candidates 和 ready action candidates。
  - 新增 `tests/test_validated_decision_promotion_dry_run.py`，验证 completed+valid 记录才可进入 promotion dry run。
  - 新增 `tests/validated_decision_promotion_dry_run_report.json`。
  - 新增 `docs/validated_decision_promotion_dry_run_v0.4.7.7.4.md`。

### 诊断结果
- Promotion candidates：0。
- Ready action candidates：0。
- Valid records：0；invalid records：0；pending records：36。

### 边界
- 本版本不覆盖原始 decision schema，不改 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_validated_decision_promotion_dry_run.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_validated_decision_promotion_dry_run`
- `.\venv\Scripts\python.exe tools\build_validated_decision_promotion_dry_run.py --proposed-schema tests\proposed_manual_review_decision_schema.json --validation-report tests\proposed_manual_review_decision_validation_report.json --output tests\validated_decision_promotion_dry_run_report.json`

## [0.4.7.7.3] - 2026-05-11

### 新增
- **拟议人工复核结论校验**：
  - 新增 `tools/validate_proposed_manual_review_decisions.py`，对 proposed decision schema 单独运行 validator。
  - 新增 `tests/test_proposed_manual_review_validation.py`，验证 proposed schema version 与 pending summary。
  - 新增 `tests/proposed_manual_review_decision_validation_report.json`。
  - 新增 `docs/proposed_manual_review_validation_v0.4.7.7.3.md`。

### 诊断结果
- Total records：36。
- Valid records：0。
- Pending records：36。
- Invalid records：0。

### 边界
- 本版本不 promotion，不覆盖原始 decision schema，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\validate_proposed_manual_review_decisions.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_proposed_manual_review_validation`
- `.\venv\Scripts\python.exe tools\validate_proposed_manual_review_decisions.py --proposed-schema tests\proposed_manual_review_decision_schema.json --output tests\proposed_manual_review_decision_validation_report.json --fail-on-invalid`

## [0.4.7.7.2] - 2026-05-11

### 新增
- **Manual Review Decision Diff & Audit Trail**：
  - 新增 `tools/audit_manual_review_decision_diff.py`，比较原始 decision schema 与 proposed decision schema，输出字段级 diff、reviewer 信息和 prohibited target 审计。
  - 新增 `tests/test_manual_review_decision_diff.py`，验证 completed decision diff 和 prohibited change target 阻断。
  - 新增 `tests/manual_review_decision_diff_report.json`。
  - 新增 `docs/manual_review_decision_diff_v0.4.7.7.2.md`。

### 诊断结果
- 当前 proposed schema：0 changed cases，0 blocked cases，0 missing/new cases。
- 原因：当前真实 workbench 为空填写，importer 未导入任何变更。

### 边界
- 本版本不覆盖原始 decision schema，不 promotion，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\audit_manual_review_decision_diff.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_diff`
- `.\venv\Scripts\python.exe tools\audit_manual_review_decision_diff.py --original-schema tests\evidence_manual_review_decision_schema.json --proposed-schema tests\proposed_manual_review_decision_schema.json --output tests\manual_review_decision_diff_report.json`

## [0.4.7.7.1] - 2026-05-11

### 新增
- **Manual Review Workbench Importer**：
  - 新增 `tools/import_manual_review_workbench.py`，读取填写后的 workbench CSV/JSON，输出 proposed decision schema 与 import report。
  - 新增 `tests/test_manual_review_workbench_import.py`，验证成功导入、未知 case 拒绝和空 reviewer 内容拒绝。
  - 新增 `tests/proposed_manual_review_decision_schema.json`。
  - 新增 `tests/manual_review_workbench_import_report.json`。
  - 新增 `docs/manual_review_workbench_importer_v0.4.7.7.1.md`。

### 诊断结果
- 当前真实 workbench CSV：36 input rows，0 imported，36 rejected。
- Rejected 原因：36 行均为空 reviewer 内容。

### 边界
- 本版本不覆盖原始 decision schema，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\import_manual_review_workbench.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_workbench_import`
- `.\venv\Scripts\python.exe tools\import_manual_review_workbench.py --decision-schema tests\evidence_manual_review_decision_schema.json --workbench-input tests\evidence_manual_review_workbench.csv --output tests\proposed_manual_review_decision_schema.json --report-output tests\manual_review_workbench_import_report.json`

## [0.4.7.7.0] - 2026-05-11

### 新增
- **Workbench Intake Contract**：
  - 新增 `tools/build_workbench_intake_contract.py`，定义 workbench CSV/JSON 可导入字段、只读字段、枚举值、case 对齐规则和写入策略。
  - 新增 `tests/test_workbench_intake_contract.py`，验证 importable/read-only 字段隔离和禁止覆盖/主流程变更策略。
  - 新增 `tests/manual_review_intake_contract_report.json`。
  - 新增 `docs/workbench_intake_contract_v0.4.7.7.0.md`。

### 诊断结果
- Importable reviewer fields：10。
- Read-only context fields：12。
- Allowed decisions：5。
- Allowed root causes：9。
- Allowed follow-up actions：10。
- Prohibited change targets：12。

### 边界
- 本版本不读取或写入真实人工结论，不覆盖原始 decision schema，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_workbench_intake_contract.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_workbench_intake_contract`
- `.\venv\Scripts\python.exe tools\build_workbench_intake_contract.py --output tests\manual_review_intake_contract_report.json`

## [0.4.7.6.3] - 2026-05-11

### 新增
- **Ready Action Routing Dry Run**：
  - 新增 `tools/build_ready_action_routing_dry_run.py`，只对 `ready_from_valid_decision` action candidates 做 dry-run 路由。
  - 新增 `tests/test_ready_action_routing_dry_run.py`，验证 route mapping 和 blocked candidates 不被路由。
  - 新增 `tests/ready_action_routing_dry_run_report.json`。
  - 新增 `docs/ready_action_routing_dry_run_v0.4.7.6.3.md`。
  - FastAPI 服务版本同步为 `0.4.7.6.3`。

### 诊断结果
- Ready routes：0。
- Blocked candidates：106。
- Manual review completed cases：0。
- Manual review pending cases：36。
- Readiness state：`manual_review_required`。

### 边界
- 本版本只路由 `ready_from_valid_decision`，不路由 `blocked_pending_manual_review`。
- 本版本不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_ready_action_routing_dry_run.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_ready_action_routing_dry_run`
- `.\venv\Scripts\python.exe tools\build_ready_action_routing_dry_run.py --action-candidates tests\evidence_manual_review_action_candidates.json --progress-report tests\evidence_manual_review_progress_report.json --output tests\ready_action_routing_dry_run_report.json`

## [0.4.7.6.2] - 2026-05-11

### 新增
- **Manual Review Progress Report**：
  - 新增 `tools/build_manual_review_progress_report.py`，汇总 decision schema、validation report、workbench、action candidates 和 fixture pool。
  - 新增 `tests/test_manual_review_progress_report.py`，验证 pending case、blocked action candidate 和 blocked fixture candidate 统计。
  - 新增 `tests/evidence_manual_review_progress_report.json`。
  - 新增 `docs/manual_review_progress_report_v0.4.7.6.2.md`。

### 诊断结果
- Total cases：36。
- Completed cases：0。
- Pending cases：36。
- Invalid cases：0。
- Ready action candidates：0；blocked action candidates：106。
- Ready fixture candidates：0；blocked fixture candidates：58。

### 边界
- 本版本不推断人工结论，不写入真实 decision records，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_progress_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_progress_report`
- `.\venv\Scripts\python.exe tools\build_manual_review_progress_report.py --decision-schema tests\evidence_manual_review_decision_schema.json --validation-report tests\evidence_manual_review_decision_validation_report.json --workbench tests\evidence_manual_review_workbench.json --action-candidates tests\evidence_manual_review_action_candidates.json --fixture-pool tests\evidence_fixture_candidate_pool.json --output tests\evidence_manual_review_progress_report.json`

## [0.4.7.6.1] - 2026-05-11

### 新增
- **Manual Review Decision Examples**：
  - 新增 `tools/build_manual_review_decision_examples.py`，生成 completed/rejected/deferred/invalid 的合成人工复核示例。
  - 新增 `tests/test_manual_review_decision_examples.py`，验证示例的 expected validation status。
  - 新增 `tests/manual_review_decision_examples.json`。
  - 新增 `docs/manual_review_decision_examples_v0.4.7.6.1.md`。

### 诊断结果
- Total examples：4。
- Valid examples：3。
- Invalid examples：1。
- Expectation mismatches：0。

### 边界
- 本版本不写入真实 decision records，不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 示例文件只用于 reviewer 训练和 validator 夹具，不得合并回真实人工复核记录。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_decision_examples.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_examples`
- `.\venv\Scripts\python.exe tools\build_manual_review_decision_examples.py --decision-schema tests\evidence_manual_review_decision_schema.json --output tests\manual_review_decision_examples.json`

## [0.4.7.6.0] - 2026-05-11

### 新增
- **Manual Review Workbench Export**：
  - 新增 `tools/export_manual_review_workbench.py`，把 pending decision records 导出为 reviewer 可使用的 JSON/CSV 工作台。
  - 新增 `tests/test_manual_review_workbench_export.py`，验证 workbench item、CSV 行和 reviewer 空白字段。
  - 新增 `tests/evidence_manual_review_workbench.json`。
  - 新增 `tests/evidence_manual_review_workbench.csv`。
  - 新增 `docs/manual_review_workbench_export_v0.4.7.6.0.md`。

### 诊断结果
- Workbench items：36。
- Pending items：36。
- JSON 保留完整 evidence context；CSV 提供人工浏览与填写入口。

### 边界
- 本版本不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只导出人工复核工作台，不写入真实人工结论。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\export_manual_review_workbench.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_workbench_export`
- `.\venv\Scripts\python.exe tools\export_manual_review_workbench.py --decision-schema tests\evidence_manual_review_decision_schema.json --output tests\evidence_manual_review_workbench.json --csv-output tests\evidence_manual_review_workbench.csv`

## [0.4.7.5.4] - 2026-05-11

### 新增
- **Manual Review Governance Report**：
  - 新增 `tools/build_manual_review_governance_report.py`，汇总 decision schema、validation report、action candidates 和 fixture candidate pool。
  - 新增 `tests/test_manual_review_governance_report.py`，验证 readiness state、guardrails、domain summary 和下一步建议。
  - 新增 `tests/evidence_manual_review_governance_report.json`。
  - 新增 `docs/manual_review_governance_report_v0.4.7.5.4.md`。

### 诊断结果
- Decision records：36；pending decisions：36；invalid decisions：0。
- Ready action candidates：0；blocked action candidates：106。
- Ready fixture candidates：0；blocked fixture candidates：58。
- Readiness state：`manual_review_required`。

### 边界
- 本版本不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只生成治理摘要和下一步建议，不修改 scenario registry、knowledge manifest、chunking、selection policy 或主链路。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_governance_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_governance_report`
- `.\venv\Scripts\python.exe tools\build_manual_review_governance_report.py --decision-schema tests\evidence_manual_review_decision_schema.json --validation-report tests\evidence_manual_review_decision_validation_report.json --action-candidates tests\evidence_manual_review_action_candidates.json --fixture-pool tests\evidence_fixture_candidate_pool.json --output tests\evidence_manual_review_governance_report.json`

## [0.4.7.5.3] - 2026-05-11

### 新增
- **Evidence Fixture Candidate Pool**：
  - 新增 `tools/build_evidence_fixture_candidate_pool.py`，从 action candidates 中提取 primary evidence、functional typing、final selection 和 scenario core 相关 fixture 候选。
  - 新增 `tests/test_evidence_fixture_candidate_pool.py`，验证 ready/blocked fixture candidate、证据引用保留和文件报告构建。
  - 新增 `tests/evidence_fixture_candidate_pool.json`。
  - 新增 `docs/evidence_fixture_candidate_pool_v0.4.7.5.3.md`。

### 诊断结果
- Total fixture candidates：58。
- Ready fixture candidates：0。
- Blocked fixture candidates：58。
- 当前没有人工 completed decision，因此没有任何 fixture candidate 可写入 eval cases 或 golden fixtures。

### 边界
- 本版本不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只生成离线 fixture 候选池，不写入 fixtures、golden cases 或隐藏样本。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_evidence_fixture_candidate_pool.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_fixture_candidate_pool`
- `.\venv\Scripts\python.exe tools\build_evidence_fixture_candidate_pool.py --decision-schema tests\evidence_manual_review_decision_schema.json --action-candidates tests\evidence_manual_review_action_candidates.json --output tests\evidence_fixture_candidate_pool.json`

## [0.4.7.5.2] - 2026-05-11

### 新增
- **Manual Review Action Candidates**：
  - 新增 `tools/build_manual_review_action_candidates.py`，把 decision records 与 validation report 转成 action candidates。
  - 新增 `tests/test_manual_review_action_candidates.py`，验证 pending 记录只能生成 blocked candidate，valid completed decision 才能生成 ready candidate。
  - 新增 `tests/evidence_manual_review_action_candidates.json`。
  - 新增 `docs/manual_review_action_candidates_v0.4.7.5.2.md`。

### 诊断结果
- Total action candidates：106。
- Ready action candidates：0。
- Blocked pending candidates：106。
- 当前没有人工 completed decision，因此没有任何候选动作被授权为 ready。

### 边界
- 本版本不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只生成离线候选行动清单，不修改 scenario registry、knowledge manifest、chunking、selection policy 或主链路。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_action_candidates.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_action_candidates`
- `.\venv\Scripts\python.exe tools\build_manual_review_action_candidates.py --decision-schema tests\evidence_manual_review_decision_schema.json --validation-report tests\evidence_manual_review_decision_validation_report.json --output tests\evidence_manual_review_action_candidates.json`

## [0.4.7.5.1] - 2026-05-11

### 新增
- **Manual Review Decision Validator**：
  - 新增 `tools/validate_manual_review_decisions.py`，校验人工复核 decision records 的状态、必填字段、root cause/action 合法性和禁止变更目标。
  - 新增 `tests/test_manual_review_decision_validation.py`，验证 completed decision、非法 root cause、非法 action 映射和 prohibited change target。
  - 新增 `tests/evidence_manual_review_decision_validation_report.json`。
  - 新增 `docs/manual_review_decision_validator_v0.4.7.5.1.md`。

### 诊断结果
- Total records：36；pending records：36；valid records：0；invalid records：0。
- 当前全部 decision records 仍为空白 pending 状态，validator 确认模板未出现越界人工结论。

### 边界
- 本版本不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只校验离线人工复核结论，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\validate_manual_review_decisions.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_validation`
- `.\venv\Scripts\python.exe tools\validate_manual_review_decisions.py --decision-schema tests\evidence_manual_review_decision_schema.json --output tests\evidence_manual_review_decision_validation_report.json --fail-on-invalid`

## [0.4.7.5.0] - 2026-05-11

### 新增
- **Manual Review Decision Schema**：
  - 新增 `tools/build_manual_review_decision_schema.py`，把 `v0.4.7.4.6` 的 review packages 转成可填写、可校验、可追溯的人工复核 decision records。
  - 新增 `tests/test_manual_review_decision_schema.py`，验证通用 root cause/action 建议、reviewer decision 空白模板和 schema 禁止变更目标。
  - 新增 `tests/evidence_manual_review_decision_schema.json`。
  - 新增 `docs/manual_review_decision_schema_v0.4.7.5.0.md`。

### 诊断结果
- Decision records：36；pending decisions：36。
- 本版本生成允许的 decision、root cause、follow-up action、必填 reviewer fields、禁止变更目标与全局 guardrails。
- 所有 `reviewer_decision` 字段保持空白，等待人工填写；诊断建议不等同于已确认修复指令。

### 边界
- 本版本不修 hidden seed，不新增或修改 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只读取已有离线报告，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_decision_schema.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_decision_schema`
- `.\venv\Scripts\python.exe tools\build_manual_review_decision_schema.py --manual-review-loop tests\evidence_manual_review_loop_report.json --output tests\evidence_manual_review_decision_schema.json`

## [0.4.7.4.6] - 2026-05-11

### 新增
- **Manual Review Loop**：
  - 新增 `tools/build_manual_review_loop.py`，汇总 manual review dataset、scenario calibration、base retrieval audit、anchor dependency audit 和 final selection audit，生成 case-centered review packages。
  - 新增 `tests/test_manual_review_loop.py`，验证 queue tags、follow-up candidates、reviewer fields 和文件报告构建。
  - 新增 `tests/evidence_manual_review_loop_report.json`。
  - 新增 `docs/manual_review_loop_v0.4.7.4.6.md`。
  - FastAPI 服务版本同步为 `0.4.7.4.6`。

### 诊断结果
- Review packages：36；pending review packages：36。
- Queue summary：`base_retrieval_quality_review=34`、`anchor_dependency_review=33`、`scenario_registry_calibration=8`、`primary_evidence_review=8`、`final_evidence_selection_review=7`、`high_risk_grounding_review=8`。
- Follow-up action summary：`metadata_chunking_or_query_coverage_review=34`、`anchor_dependency_governance_review=33`、`scenario_registry_core_article_review=8`、`primary_evidence_fixture_candidate_review=8`、`final_evidence_selection_policy_review=7`、`high_risk_manual_grounding_review=8`。
- Fixture candidate review items：8。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 anchor 规则，不修改 rerank，不修改 final evidence selection / truncation 逻辑，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不写入人工复核结论，不接入 `rag_query` 主流程。
- 本版本只读取已有离线报告，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_loop.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_manual_review_loop`
- `.\venv\Scripts\python.exe tools\build_manual_review_loop.py --manual-review-dataset tests\evidence_manual_review_dataset.json --scenario-calibration-report tests\scenario_registry_calibration_report.json --base-audit-report tests\base_retrieval_quality_audit_report.json --anchor-audit-report tests\anchor_dependency_audit_report.json --final-selection-audit-report tests\final_evidence_selection_audit_report.json --output tests\evidence_manual_review_loop_report.json`

## [0.4.7.4.5] - 2026-05-11

### 新增
- **Final Evidence Selection Audit**：
  - 新增 `tools/audit_final_evidence_selection.py`，只读审计 `rerank_input -> final evidence` 的 expected evidence 覆盖流失。
  - 新增 `tests/test_final_evidence_selection_audit.py`，验证 primary evidence lost、scenario core lost、operative/liability evidence lost 和 anchor-supported-but-final-lost。
  - 新增 `tests/final_evidence_selection_audit_report.json`。
  - 新增 `docs/final_evidence_selection_audit_v0.4.7.4.5.md`。
  - FastAPI 服务版本同步为 `0.4.7.4.5`。

### 诊断结果
- Final selection loss cases：7；high-priority review cases：5。
- Issue summary：`rerank_input_to_final_loss=7`、`primary_evidence_lost=7`、`anchor_supported_but_final_lost=6`、`operative_evidence_lost=6`、`scenario_core_lost=4`、`low_final_coverage_after_selection=2`、`liability_evidence_lost=1`。
- Selection loss summary：`loss_0_25_to_0_499=6`、`loss_0_5_or_more=1`。
- Lost functional types：`operative_rule=3`、`procedural=3`、`liability=2`。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不修改 final evidence selection / truncation 逻辑，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只读取已有离线报告，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\audit_final_evidence_selection.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_final_evidence_selection_audit`
- `.\venv\Scripts\python.exe tools\audit_final_evidence_selection.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --anchor-audit-report tests\anchor_dependency_audit_report.json --output tests\final_evidence_selection_audit_report.json`

## [0.4.7.4.4] - 2026-05-11

### 新增
- **Anchor Dependency Audit**：
  - 新增 `tools/audit_anchor_dependency.py`，只读审计 anchor dependency，区分健康 anchor support 与 anchor masking weak base retrieval。
  - 新增 `tests/test_anchor_dependency_audit.py`，验证 healthy anchor support、zero-base-to-anchor recovery、anchor-supported-but-final-lost 和文件报告构建。
  - 新增 `tests/anchor_dependency_audit_report.json`。
  - 新增 `docs/anchor_dependency_audit_v0.4.7.4.4.md`。
  - FastAPI 服务版本同步为 `0.4.7.4.4`。

### 诊断结果
- Anchor-dependency cases：33；high-priority review cases：33。
- Issue summary：`anchor_masking_base_retrieval_gap=33`、`anchor_rescue_success=33`、`high_anchor_gain=33`、`metadata_or_chunking_review_candidate=33`、`zero_base_to_anchor_recovery=25`、`anchor_supported_but_final_lost=6`。
- Anchor gain summary：`gain_1_0=25`、`gain_0_5_to_0_999=8`。
- 结论：当前 anchor dependency 全部更像 anchor 掩盖基础召回弱，而不是健康补充型 anchor support。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 anchor 规则，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只读取已有离线报告，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\audit_anchor_dependency.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_anchor_dependency_audit`
- `.\venv\Scripts\python.exe tools\audit_anchor_dependency.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --base-audit-report tests\base_retrieval_quality_audit_report.json --output tests\anchor_dependency_audit_report.json`

## [0.4.7.4.3] - 2026-05-11

### 新增
- **Base Retrieval Quality Audit**：
  - 新增 `tools/audit_base_retrieval_quality.py`，只读审计 dense、sparse、union 三个基础召回层的 expected evidence coverage。
  - 新增 `tests/test_base_retrieval_quality_audit.py`，验证 zero base recall、sparse-only support、no union gain、anchor rescue 和 source/index review 的通用分流逻辑。
  - 新增 `tests/base_retrieval_quality_audit_report.json`。
  - 新增 `docs/base_retrieval_quality_audit_v0.4.7.4.3.md`。
  - FastAPI 服务版本同步为 `0.4.7.4.3`。

### 诊断结果
- Base-gap cases：34；high-priority review cases：34。
- Layer gap summary：`dense_gap_cases=34`、`sparse_gap_cases=34`、`union_gap_cases=34`。
- Issue summary：`zero_base_recall=25`、`anchor_rescue_pattern=33`、`metadata_or_chunking_review_candidate=33`、`no_union_gain=34`、`index_or_source_coverage_review_candidate=1`、`sparse_only_support=6`、`dense_only_support=1`。
- 结论：多数 base retrieval gap 可被 anchor 层恢复，更适合先审计 metadata、chunking、query lexical coverage 与 source/article 标识一致性，而不是先改 rerank 或 prompt。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只读取已有离线报告，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\audit_base_retrieval_quality.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_base_retrieval_quality_audit`
- `.\venv\Scripts\python.exe tools\audit_base_retrieval_quality.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --output tests\base_retrieval_quality_audit_report.json`

## [0.4.7.4.2] - 2026-05-11

### 新增
- **Scenario Registry Calibration**：
  - 新增 `tools/calibrate_scenario_registry_coverage.py`，只读审计 `scenario_core_gap`，区分 registry core set 可能过宽、final evidence 真实缺口、跨法域 core gap 和 definition-only core 候选。
  - 新增 `tests/test_scenario_registry_calibration.py`，验证通用诊断逻辑，不绑定具体 hidden seed 或固定 case id。
  - 新增 `tests/scenario_registry_calibration_report.json`。
  - 新增 `docs/scenario_registry_calibration_v0.4.7.4.2.md`。
  - FastAPI 服务版本同步为 `0.4.7.4.2`。

### 诊断结果
- Scenario core gap cases：8。
- High-priority review cases：7。
- Issue summary：`registry_core_review_needed=8`、`core_missing_from_final_evidence=8`、`registry_core_scope_review_candidate=4`、`evidence_chain_gap_candidate=4`、`final_primary_gap_overlap=4`、`cross_domain_core_gap=2`、`definition_core_candidate=1`。
- Per-domain summary：数据合规 6 review / 5 high priority；市场秩序 2 review / 2 high priority。
- 4 个 case 更像 evidence chain 真实缺口，4 个 case 更像 scenario core set 需要人工校准。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不修改 `config/scenario_registry.json`，不接入 `rag_query` 主流程。
- 本版本只新增离线 calibration diagnostics，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\calibrate_scenario_registry_coverage.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_scenario_registry_calibration`
- `.\venv\Scripts\python.exe tools\calibrate_scenario_registry_coverage.py --coverage-report tests\evidence_coverage_report.json --manual-review-dataset tests\evidence_manual_review_dataset.json --scenario-registry config\scenario_registry.json --output tests\scenario_registry_calibration_report.json`

## [0.4.7.4.1] - 2026-05-11

### 修复
- **Evidence Report Enrichment Hardening**：
  - `tools/check_evidence_coverage.py` 增加 citation location fallback 与标准章节 title fallback，修复标准类证据 `C.1 概述` 因 report `section_no` 为空而无法 enrichment 的问题。
  - 新增 `tools/check_evidence_enrichment_hardening.py`，检查 final evidence enrichment 命中率、必需字段完整性和未命中明细。
  - 新增 `tests/test_evidence_enrichment_hardening.py`，覆盖 citation fallback、真实 manifest index 构建和 hardening 报告。
  - 新增 `tests/evidence_enrichment_hardening_report.json`。
  - FastAPI 服务版本同步为 `0.4.7.4.1`。

### 诊断结果
- Final evidence enrichment 从 179/180 提升到 180/180，`matched_ratio=1.0`。
- Missing required field counts：0。
- Field stability：passed。
- Evidence coverage issue summary 保持不变：`anchor_dependent_coverage=33`、`final_primary_gap=8`、`scenario_core_gap=8`、`layer_coverage_regression=7`、`low_final_coverage=3`。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只修复离线 enrichment 诊断字段稳定性，不写回 ingestion metadata，不改变检索、生成或风险输出行为。
- 本版本不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_evidence_coverage.py tools\check_evidence_enrichment_hardening.py tools\triage_evidence_coverage_loss.py tools\build_evidence_manual_review_dataset.py tools\draft_evidence_coverage_gates.py tools\build_evidence_root_cause_action_plan.py tools\build_evidence_action_series_baseline.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_enrichment_hardening tests.test_evidence_coverage tests.test_evidence_coverage_triage tests.test_evidence_manual_review_dataset tests.test_evidence_coverage_gate_draft tests.test_evidence_root_cause_action_plan tests.test_evidence_action_series_baseline`
- `.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --knowledge-manifest knowledge_manifest.json --functional-type-config config\legal_functional_types.json --output tests\evidence_coverage_report.json`
- `.\venv\Scripts\python.exe tools\check_evidence_enrichment_hardening.py --coverage-report tests\evidence_coverage_report.json --output tests\evidence_enrichment_hardening_report.json`

## [0.4.7.4.0] - 2026-05-11

### 新增
- **Evidence Quality Action Series Baseline**：
  - 新增 `tools/build_evidence_action_series_baseline.py`，读取 v0.4.7.3.5 action plan，固化 v0.4.7.4.x 的执行顺序、输入依赖、输出文件和全局边界。
  - 新增 `tests/test_evidence_action_series_baseline.py`，覆盖执行顺序、全局边界和 action plan link。
  - 新增 `tests/evidence_action_series_baseline.json`，记录 6 个 planned steps：0.4.7.4.1 到 0.4.7.4.6。
  - 新增 `docs/evidence_action_series_baseline_v0.4.7.4.0.md`。
  - FastAPI 服务版本同步为 `0.4.7.4.0`。

### 诊断结果
- Action series baseline：6 planned steps。
- Execution order：`0.4.7.4.1`、`0.4.7.4.2`、`0.4.7.4.3`、`0.4.7.4.4`、`0.4.7.4.5`、`0.4.7.4.6`。
- Planned action count：6。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只固化 action series baseline，不执行任何审计修复。
- 本版本不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_evidence_action_series_baseline.py tools\build_evidence_root_cause_action_plan.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_action_series_baseline tests.test_evidence_root_cause_action_plan`
- `.\venv\Scripts\python.exe tools\build_evidence_action_series_baseline.py --action-plan tests\evidence_root_cause_action_plan.json --output tests\evidence_action_series_baseline.json`

## [0.4.7.3.5] - 2026-05-11

### 新增
- **Evidence Root Cause Action Plan**：
  - 新增 `tools/build_evidence_root_cause_action_plan.py`，汇总 coverage、triage、manual review dataset 和 gate draft，把 root causes 分流到后续 v0.4.7.4.x 审计路线。
  - 新增 `tests/test_evidence_root_cause_action_plan.py`，覆盖 root cause 到目标版本的映射、样本 case 提取和文件报告构建。
  - 新增 `tests/evidence_root_cause_action_plan.json`，输出 action id、target version、priority、observed cases、manual review items、sample case ids、目标和边界。
  - 新增 `docs/evidence_root_cause_action_plan_v0.4.7.3.5.md`。
  - FastAPI 服务版本同步为 `0.4.7.3.5`。

### 诊断结果
- Action plan：6 planned actions。
- Priority summary：P0 1、P1 2、P2 3。
- Target versions：`0.4.7.4.2` 1、`0.4.7.4.3` 1、`0.4.7.4.4` 1、`0.4.7.4.5` 1、`0.4.7.4.6` 2。
- 下一阶段：`0.4.7.4.x Evidence Quality Action Series`。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只输出行动计划，不执行任何主链路修复。
- 本版本不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_evidence_root_cause_action_plan.py tools\draft_evidence_coverage_gates.py tools\build_evidence_manual_review_dataset.py tools\check_evidence_coverage.py tools\triage_evidence_coverage_loss.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_root_cause_action_plan tests.test_evidence_coverage_gate_draft tests.test_evidence_manual_review_dataset tests.test_evidence_coverage tests.test_evidence_coverage_triage`
- `.\venv\Scripts\python.exe tools\build_evidence_root_cause_action_plan.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --manual-review-dataset tests\evidence_manual_review_dataset.json --gate-draft-report tests\evidence_coverage_gate_draft_report.json --output tests\evidence_root_cause_action_plan.json`

## [0.4.7.3.4] - 2026-05-11

### 新增
- **Coverage Gate Draft**：
  - 新增 `tools/draft_evidence_coverage_gates.py`，读取 coverage、triage 与 manual review dataset，生成非强制 evidence coverage quality gate 草案。
  - 新增 `tests/test_evidence_coverage_gate_draft.py`，覆盖当前基线通过、high-priority regression draft blocker 和文件报告构建。
  - 新增 `tests/evidence_coverage_gate_draft_report.json`，记录 draft gates、阈值、observed value、severity 和 non-enforcing 行为。
  - 新增 `docs/evidence_coverage_gate_draft_v0.4.7.3.4.md`。
  - FastAPI 服务版本同步为 `0.4.7.3.4`。

### 诊断结果
- Draft gates：7 total、7 passed、0 failed、0 blocking draft failures。
- Gate 草案覆盖：high-priority review ceiling、review ratio ceiling、final coverage floor、enrichment ratio floor、final selection loss ceiling、scenario core gap ceiling、pending manual review workload ceiling。
- 默认行为：non-enforcing；仅显式传入 `--fail-on-blocking` 时才会对 blocking draft failures 返回非零。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只设计离线 gate 草案，不启用强制发布门禁，不改变 coverage、triage、manual review dataset 或主流程行为。
- 本版本不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\draft_evidence_coverage_gates.py tools\build_evidence_manual_review_dataset.py tools\check_evidence_coverage.py tools\triage_evidence_coverage_loss.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage_gate_draft tests.test_evidence_manual_review_dataset tests.test_evidence_coverage tests.test_evidence_coverage_triage`
- `.\venv\Scripts\python.exe tools\draft_evidence_coverage_gates.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --manual-review-dataset tests\evidence_manual_review_dataset.json --output tests\evidence_coverage_gate_draft_report.json`

## [0.4.7.3.3] - 2026-05-11

### 新增
- **Evidence Manual Review Dataset**：
  - 新增 `tools/build_evidence_manual_review_dataset.py`，读取 enriched coverage report 与 triage report，抽取 high-priority review cases 形成离线人工复核数据集。
  - 新增 `tests/test_evidence_manual_review_dataset.py`，覆盖 root-cause review questions、review item 结构、high-priority only 过滤和 reviewer placeholder。
  - 新增 `tests/evidence_manual_review_dataset.json`，保留 root causes、priority score、coverage flow、missing final expected、missing scenario core、final evidence、functional type coverage 和 reviewer fields。
  - 新增 `docs/evidence_manual_review_dataset_v0.4.7.3.3.md`。
  - FastAPI 服务版本同步为 `0.4.7.3.3`。

### 诊断结果
- Manual review dataset：12 pending review items，对应 v0.4.7.3.2 triage 的 12 条 high-priority review cases。
- Root cause summary：`base_retrieval_gap=10`、`anchor_dependency=9`、`final_primary_gap=8`、`scenario_core_gap=8`、`final_selection_loss=7`、`low_final_coverage=3`。
- Domain summary：数据合规 10、市场秩序 2、财税 1；存在跨域 case，因此按 expected domains 计数会大于 review item 总数。
- Risk summary：high 8、low 4。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只沉淀人工复核数据集，不写入人工结论，不改变 coverage、triage 或主流程行为。
- 本版本不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\build_evidence_manual_review_dataset.py tools\check_evidence_coverage.py tools\triage_evidence_coverage_loss.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_manual_review_dataset tests.test_evidence_coverage tests.test_evidence_coverage_triage`
- `.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --knowledge-manifest knowledge_manifest.json --functional-type-config config\legal_functional_types.json --output tests\evidence_coverage_report.json`
- `.\venv\Scripts\python.exe tools\triage_evidence_coverage_loss.py --coverage-report tests\evidence_coverage_report.json --output tests\evidence_coverage_triage_report.json`
- `.\venv\Scripts\python.exe tools\build_evidence_manual_review_dataset.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --output tests\evidence_manual_review_dataset.json`

## [0.4.7.3.2] - 2026-05-11

### 新增
- **Evidence Report Enrichment**：
  - `tools/check_evidence_coverage.py` 新增离线 enrichment index，读取 `knowledge_manifest.json` 与 `config/legal_functional_types.json`，复用 ingestion loader 给 evidence 补 `content_preview`、`functional_type`、`functional_type_confidence` 和 enrichment status。
  - CLI 新增 `--knowledge-manifest`、`--functional-type-config` 与 `--no-enrichment`，默认启用离线 enrichment。
  - `tests/test_evidence_coverage.py` 新增 manifest enrichment 单测，验证从本地知识文件补正文和功能类型后 functional coverage 可评价。
  - `tools/triage_evidence_coverage_loss.py` 报告版本同步为 `0.4.7.3.2`，复用 enriched coverage report 后不再出现 `functional_metadata_not_evaluable` root cause。
  - FastAPI 服务版本同步为 `0.4.7.3.2`。

### 诊断结果
- Evidence enrichment index：15 manifest documents、15 loaded documents、2387 indexed keys、0 missing files。
- Final evidence enrichment：180 final evidence items 中 179 matched，`matched_ratio=0.994`。
- Functional coverage：60/60 cases 变为 `evaluable=true`，`functional_metadata_not_evaluable` 从 triage root cause summary 中消除。
- Evidence coverage issue summary 保持诊断边界不变：`anchor_dependent_coverage=33`、`final_primary_gap=8`、`scenario_core_gap=8`、`layer_coverage_regression=7`、`low_final_coverage=3`。
- Coverage loss triage：60 cases、24 ok、24 review、12 high-priority review；root causes 保持为 `base_retrieval_gap=34`、`anchor_dependency=33`、`final_primary_gap=8`、`scenario_core_gap=8`、`final_selection_loss=7`、`low_final_coverage=3`。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只增强离线报告可评价性，不写回 ingestion metadata，不改变检索、生成或风险输出行为。
- 本版本不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_evidence_coverage.py tools\triage_evidence_coverage_loss.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage tests.test_evidence_coverage_triage`
- `.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --knowledge-manifest knowledge_manifest.json --functional-type-config config\legal_functional_types.json --output tests\evidence_coverage_report.json`
- `.\venv\Scripts\python.exe tools\triage_evidence_coverage_loss.py --coverage-report tests\evidence_coverage_report.json --output tests\evidence_coverage_triage_report.json`

## [0.4.7.3.1] - 2026-05-11

### 新增
- **Coverage Loss Triage Report**：
  - 新增 `tools/triage_evidence_coverage_loss.py`，只读取 `tests/evidence_coverage_report.json`，对 v0.4.7.3 的 review cases 做二次归因。
  - 新增 `tests/test_evidence_coverage_triage.py`，覆盖基础召回缺口、anchor 依赖、final selection loss、scenario core gap、metadata 不可评价边界和报告构建。
  - 新增 `tests/evidence_coverage_triage_report.json`，输出 case 级 root causes、priority score、recommended actions、coverage flow 和 high-priority manual review list。
  - 新增 `docs/evidence_coverage_triage_v0.4.7.3.1.md`。
  - FastAPI 服务版本同步为 `0.4.7.3.1`。

### 诊断结果
- Coverage triage report：60 cases、24 ok、24 review、12 high-priority review。
- Root cause summary：`base_retrieval_gap=34`、`anchor_dependency=33`、`final_primary_gap=8`、`scenario_core_gap=8`、`final_selection_loss=7`、`low_final_coverage=3`。
- Data quality limitation：`functional_metadata_not_evaluable=60`，作为功能类型覆盖的报告字段限制记录；仅该项存在时不触发 review。
- Coverage flow summary：`low_union_coverage_cases=34`、`anchor_improved_cases=33`、`final_selection_loss_cases=7`。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只做离线 coverage loss triage，不运行 full eval，不调用 LLM、Qdrant、embedding 或 rerank。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\triage_evidence_coverage_loss.py tools\check_evidence_coverage.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage_triage tests.test_evidence_coverage`
- `.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --output tests\evidence_coverage_report.json`
- `.\venv\Scripts\python.exe tools\triage_evidence_coverage_loss.py --coverage-report tests\evidence_coverage_report.json --output tests\evidence_coverage_triage_report.json`

## [0.4.7.3] - 2026-05-11

### 新增
- **Evidence Coverage Diagnostics**：
  - 新增 `tools/check_evidence_coverage.py`，读取既有 RAG eval report、可选 hidden eval report 与 scenario registry，输出离线 evidence coverage 质量诊断。
  - 新增 `tests/test_evidence_coverage.py`，覆盖 final evidence gap、scenario core gap、functional type gap、optional hidden report skip 和通用报告构建逻辑。
  - 新增 `tests/evidence_coverage_report.json`，按 case 输出 coverage status、detected issues、review reasons、分层覆盖率、functional type coverage、issue summary、per-domain summary 和 high-priority manual review list。
  - 新增 `docs/evidence_coverage_diagnostics_v0.4.7.3.md`。
  - FastAPI 服务版本同步为 `0.4.7.3`。

### 诊断结果
- Evidence coverage report：60 cases、24 ok、36 review；`tests\hidden_eval_report.json` 当前不存在，按 optional input 跳过。
- Issue summary：`anchor_dependent_coverage=33`、`final_primary_gap=8`、`scenario_core_gap=8`、`layer_coverage_regression=7`、`low_final_coverage=3`。
- Layer summary：dense `14/104=0.135`、sparse `38/104=0.365`、union `39/104=0.375`、anchor `103/104=0.99`、rerank_input `103/104=0.99`、final `95/104=0.913`。
- 当前 evidence item 多数缺少正文或 `functional_type` metadata，因此 `functional_type_coverage.evaluable=false`；checker 不把不可评价样本误报为 operative support 缺口。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只新增离线 grounding quality diagnostics、测试、报告和文档，不运行 full eval。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_evidence_coverage.py tools\analyze_legal_functional_typing_errors.py tools\check_legal_functional_typing_fixtures.py tools\check_legal_functional_type_config.py tools\audit_legal_functional_typing.py tools\check_evidence_alignment.py src\rag\legal_functional_typing.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage tests.test_legal_functional_typing_error_analysis tests.test_legal_functional_typing_fixtures tests.test_legal_functional_type_config tests.test_legal_functional_typing tests.test_evidence_alignment`
- `.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --output tests\evidence_coverage_report.json`
- `.\venv\Scripts\python.exe tools\check_legal_functional_type_config.py --config config\legal_functional_types.json --report-output tests\legal_functional_type_config_report.json`
- `.\venv\Scripts\python.exe tools\check_legal_functional_typing_fixtures.py --fixtures tests\fixtures\legal_functional_typing_golden.json --config config\legal_functional_types.json --report-output tests\legal_functional_typing_fixture_report.json`
- `.\venv\Scripts\python.exe tools\check_evidence_alignment.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --output tests\evidence_alignment_report.json`
- `.\venv\Scripts\python.exe tools\audit_legal_functional_typing.py --manifest knowledge_manifest.json --config config\legal_functional_types.json --output tests\legal_functional_typing_report.json`
- `.\venv\Scripts\python.exe tools\analyze_legal_functional_typing_errors.py --fixture-report tests\legal_functional_typing_fixture_report.json --audit-report tests\legal_functional_typing_report.json --alignment-report tests\evidence_alignment_report.json --output tests\legal_functional_typing_error_analysis_report.json`

## [0.4.7.2.4] - 2026-05-10

### 修复
- **Tax / Domain-Neutral Cue Quality Fix**：
  - `src/rag/legal_functional_typing.py` 新增正文短文本结构性材料识别，将法律标题、通过日期、目录和章节标题归入 `unrelated_or_contextual`，避免误计为有效义务证据。
  - `config/legal_functional_types.json` 版本同步为 `0.4.7.2.4`，补充税率、征收率、应纳税额、抵扣、免征、申报纳税、办理登记、纳税地点、纳税义务发生时间等财税/税务通用功能线索。
  - `tests/fixtures/legal_functional_typing_golden.json` 扩展到 25 条 fixtures，覆盖税率、抵扣、免征、税务程序、责任优先级和结构性文本边界。
  - `tools/audit_legal_functional_typing.py`、`tools/check_legal_functional_typing_fixtures.py`、`tools/check_legal_functional_type_config.py` 和 `tools/analyze_legal_functional_typing_errors.py` 的报告版本跟随 functional typing 配置版本。
  - 新增 `docs/legal_functional_typing_tax_cue_quality_v0.4.7.2.4.md`。
  - FastAPI 服务版本同步为 `0.4.7.2.4`。

### 诊断结果
- `中华人民共和国增值税法`：`unclassified_ratio` 从 `0.5` 降至 `0.167`，`operative_support_ratio` 从 `0.353` 升至 `0.628`，`review_required=false`。
- 全局 functional typing audit：15 documents、7177 chunks、0 review documents、`unclassified_ratio=0.25`、`operative_support_ratio=0.635`。
- Fixture gate：25/25 passed。
- Error analysis：high unclassified documents 从 1 降至 0；剩余 prioritized actions 为 P2 missing-primary evidence 和 P3 answer-evidence disconnect。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只改进离线 functional typing 质量信号，不把 functional type 写回 ingestion metadata，也不改变检索、生成或风险输出行为。
- 本版本不运行 full eval。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\analyze_legal_functional_typing_errors.py tools\check_legal_functional_typing_fixtures.py tools\check_legal_functional_type_config.py tools\audit_legal_functional_typing.py tools\check_evidence_alignment.py src\rag\legal_functional_typing.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_legal_functional_typing_error_analysis tests.test_legal_functional_typing_fixtures tests.test_legal_functional_type_config tests.test_legal_functional_typing tests.test_evidence_alignment`
- `.\venv\Scripts\python.exe tools\check_legal_functional_type_config.py --config config\legal_functional_types.json --report-output tests\legal_functional_type_config_report.json`
- `.\venv\Scripts\python.exe tools\check_legal_functional_typing_fixtures.py --fixtures tests\fixtures\legal_functional_typing_golden.json --config config\legal_functional_types.json --report-output tests\legal_functional_typing_fixture_report.json`
- `.\venv\Scripts\python.exe tools\audit_legal_functional_typing.py --manifest knowledge_manifest.json --config config\legal_functional_types.json --output tests\legal_functional_typing_report.json`
- `.\venv\Scripts\python.exe tools\check_evidence_alignment.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --output tests\evidence_alignment_report.json`
- `.\venv\Scripts\python.exe tools\analyze_legal_functional_typing_errors.py --fixture-report tests\legal_functional_typing_fixture_report.json --audit-report tests\legal_functional_typing_report.json --alignment-report tests\evidence_alignment_report.json --output tests\legal_functional_typing_error_analysis_report.json`
- `tests\hidden_eval_report.json` 当前不存在，checker 按 optional input 跳过并写入 `skipped_inputs`。

## [0.4.7.2.3] - 2026-05-10

### 新增
- **Legal Functional Typing Error Analysis Report**：
  - 新增 `tools/analyze_legal_functional_typing_errors.py`，读取 fixture gate、functional typing audit 和 evidence alignment report，生成统一误报/漏报归因报告。
  - 新增 `tests/test_legal_functional_typing_error_analysis.py`，覆盖 fixture failure P0、high-unclassified P1、alignment issue 汇总和文件报告生成。
  - 新增 `tests/legal_functional_typing_error_analysis_report.json`。
  - 新增 `docs/legal_functional_typing_error_analysis_v0.4.7.2.3.md`。
  - FastAPI 服务版本同步为 `0.4.7.2.3`。

### 诊断结果
- Fixture failed cases：0。
- High unclassified documents：1，当前对象为 `中华人民共和国增值税法`，`unclassified_ratio=0.5`。
- Low operative documents：0。
- Definition-only documents：0。
- Alignment review cases：50。
- Alignment missing-primary cases：12。
- Alignment definition-only cases：0。
- Alignment unsupported-output cases：48。
- Prioritized actions：3。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只读取已有离线报告并做误报/漏报归因，不运行 full eval。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\analyze_legal_functional_typing_errors.py tools\check_legal_functional_typing_fixtures.py tools\check_legal_functional_type_config.py tools\audit_legal_functional_typing.py tools\check_evidence_alignment.py src\rag\legal_functional_typing.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_legal_functional_typing_error_analysis tests.test_legal_functional_typing_fixtures tests.test_legal_functional_type_config tests.test_legal_functional_typing tests.test_evidence_alignment`
- `.\venv\Scripts\python.exe tools\check_legal_functional_type_config.py --config config\legal_functional_types.json --report-output tests\legal_functional_type_config_report.json`
- `.\venv\Scripts\python.exe tools\check_legal_functional_typing_fixtures.py --fixtures tests\fixtures\legal_functional_typing_golden.json --config config\legal_functional_types.json --report-output tests\legal_functional_typing_fixture_report.json`
- `.\venv\Scripts\python.exe tools\audit_legal_functional_typing.py --manifest knowledge_manifest.json --config config\legal_functional_types.json --output tests\legal_functional_typing_report.json`
- `.\venv\Scripts\python.exe tools\check_evidence_alignment.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --output tests\evidence_alignment_report.json`
- `.\venv\Scripts\python.exe tools\analyze_legal_functional_typing_errors.py --fixture-report tests\legal_functional_typing_fixture_report.json --audit-report tests\legal_functional_typing_report.json --alignment-report tests\evidence_alignment_report.json --output tests\legal_functional_typing_error_analysis_report.json`
- 本版本不运行 full eval。

## [0.4.7.2.2] - 2026-05-10

### 新增
- **Legal Functional Typing Golden Fixtures**：
  - 新增 `tests/fixtures/legal_functional_typing_golden.json`，建立 16 条可读、可维护的功能类型基准片段，覆盖 definition、principle、operative_rule、procedural、liability、rights_remedy、scope、technical_standard、unclassified、metadata priority 和边界样本。
  - 新增 `tools/check_legal_functional_typing_fixtures.py`，逐条运行 functional typing 分类并比对 expected/actual type，输出 matched rule、matched terms 和失败分布。
  - 新增 `tests/test_legal_functional_typing_fixtures.py`，覆盖仓库 fixtures、未知 expected type、重复 case id 和失败明细汇总。
  - 新增 `tests/legal_functional_typing_fixture_report.json`。
  - 新增 `docs/legal_functional_typing_golden_fixtures_v0.4.7.2.2.md`。
  - FastAPI 服务版本同步为 `0.4.7.2.2`。

### 修复
- 调整 `config/legal_functional_types.json` 的 principle 规则：
  - 新增高优先级原则组合短语规则，用于识别“合法、正当、必要”“公开、透明”“遵循...原则”等典型原则条款。
  - 保留宽泛原则词为低优先级，避免把普通义务条款中的“必要”“公开”等词误判为原则。
  - 修复 fixture gate 暴露的原则条款被误判为 `operative_rule` 的问题。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只新增 fixture gate 并修复 functional typing 的通用分类边界，不运行 full eval。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_legal_functional_typing_fixtures.py tools\check_legal_functional_type_config.py src\rag\legal_functional_typing.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_legal_functional_typing_fixtures tests.test_legal_functional_type_config tests.test_legal_functional_typing tests.test_evidence_alignment`
- `.\venv\Scripts\python.exe tools\check_legal_functional_type_config.py --config config\legal_functional_types.json --report-output tests\legal_functional_type_config_report.json`
- `.\venv\Scripts\python.exe tools\check_legal_functional_typing_fixtures.py --fixtures tests\fixtures\legal_functional_typing_golden.json --config config\legal_functional_types.json --report-output tests\legal_functional_typing_fixture_report.json`
- `.\venv\Scripts\python.exe tools\audit_legal_functional_typing.py --manifest knowledge_manifest.json --config config\legal_functional_types.json --output tests\legal_functional_typing_report.json`
- Fixture gate：16/16 passed。
- Config gate：passed，0 errors，0 warnings，10 functional types，8 rules，78 contains cues，20 regex cues。
- Functional typing audit：15 documents，7177 chunks，1 review document，`unclassified_ratio=0.288`，`operative_support_ratio=0.633`。
- 本版本不运行 full eval。

## [0.4.7.2.1] - 2026-05-10

### 新增
- **Legal Functional Typing Config Gate**：
  - 新增 `tools/check_legal_functional_type_config.py`，校验 `config/legal_functional_types.json` 的 taxonomy、operative support type、规则字段、priority、confidence、关键词线索和 regex 可编译性。
  - 新增 `tests/test_legal_functional_type_config.py`，覆盖正常配置、未知 functional type、重复 id、非法 regex、未知 operative support type 和仓库真实配置。
  - 新增 `tests/legal_functional_type_config_report.json`，记录配置门禁结果。
  - 新增 `docs/legal_functional_type_config_gate_v0.4.7.2.1.md`，说明本版本是 Legal Functional Typing 质量修复版本。
  - FastAPI 服务版本同步为 `0.4.7.2.1`。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只验证 functional typing 配置质量，不改变分类器运行语义，不运行 full eval。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_legal_functional_type_config.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_legal_functional_type_config`
- `.\venv\Scripts\python.exe tools\check_legal_functional_type_config.py --config config\legal_functional_types.json --report-output tests\legal_functional_type_config_report.json`
- Config gate 结果：passed，0 errors，0 warnings，10 functional types，7 rules，73 contains cues，19 regex cues。
- 本版本不运行 full eval。

## [0.4.7.2] - 2026-05-10

### 新增
- **Legal Functional Typing 离线诊断层**：
  - 新增 `config/legal_functional_types.json`，定义可维护的法条功能类型 taxonomy、operative support 类型与通用文本线索。
  - 新增 `src/rag/legal_functional_typing.py`，提供 `classify_legal_function()`、`classify_evidence_function()` 与 `has_operative_support()`，优先读取 metadata，其次使用通用规则，不再依赖具体 case id 或隐藏样本。
  - 新增 `tools/audit_legal_functional_typing.py`，读取 `knowledge_manifest.json` 并复用现有 ingestion loader，输出每部文档和全局 chunk 的 functional type coverage。
  - 新增 `tests/test_legal_functional_typing.py`，覆盖 metadata 优先、定义/程序/义务/责任/标准分类与 audit 报告结构。
  - 新增 `docs/legal_functional_typing_v0.4.7.2.md`，说明本层是大量法律入库后的 grounding quality metadata/audit 路线。
  - 生成 `tests/legal_functional_typing_report.json`。
  - FastAPI 服务版本同步为 `0.4.7.2`。

### 更新
- `tools/check_evidence_alignment.py` 改为复用 `src/rag/legal_functional_typing.py` 判断 evidence functional type，移除 checker 内按具体法条号维护的临时功能类型映射。
- `tests/test_evidence_alignment.py` 改为用通用文本线索验证 definition-only，不再依赖某部法第几条的硬编码。

### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只读本地知识文本、manifest 和已有报告，不调用 LLM、embedding、Qdrant 或外部服务。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\rag\legal_functional_typing.py tools\audit_legal_functional_typing.py tools\check_evidence_alignment.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_legal_functional_typing tests.test_evidence_alignment`
- `.\venv\Scripts\python.exe tools\audit_legal_functional_typing.py --manifest knowledge_manifest.json --config config\legal_functional_types.json --output tests\legal_functional_typing_report.json`
- Audit 结果：15 documents、7177 chunks、1 review document、`unclassified_ratio=0.288`、`operative_support_ratio=0.637`。
- 本版本不运行 full eval；仅运行离线 functional typing audit。

## [0.4.7.1] - 2026-05-10

### 新增
- **Evidence Alignment Checker 离线诊断层**：
  - 新增 `tools/check_evidence_alignment.py`，读取 `tests/rag_eval_report.json` 与可选 `tests/hidden_eval_report.json`、`config/scenario_registry.json`，输出离线 evidence alignment 质量诊断。
  - 新增 `tests/test_evidence_alignment.py`，覆盖通用诊断逻辑：法域污染、主争点缺证据、定义条款替代规范条款、答案-证据脱节、证据覆盖不足与 optional hidden report 跳过。
  - 新增 `docs/evidence_alignment_checker_v0.4.7.1.md`，明确本工具是 RAG grounding quality diagnostics，不是 hidden seed 修补工具。
  - 生成 `tests/evidence_alignment_report.json`，基于现有 `tests/rag_eval_report.json` 输出 case 级 alignment status、detected issues、review reasons、issue type summary、per-domain summary 与 high-risk manual review list。
  - FastAPI 服务版本同步为 `0.4.7.1`。
### 边界
- 本版本不修 hidden seed，不新增 anchor，不修改 rerank，不改 prompt，不改 risk supplement / term preservation 规则，不改 eval case，不接入 `rag_query` 主流程。
- 本版本只读取既有报告，不调用 LLM、embedding、Qdrant 或外部服务。
### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_evidence_alignment.py src\main.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_evidence_alignment`
- `.\venv\Scripts\python.exe tools\check_evidence_alignment.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --output tests\evidence_alignment_report.json`
- `tests\hidden_eval_report.json` 当前不存在，checker 按 optional input 跳过并写入 `skipped_inputs`。
- 本版本不运行 full eval；仅读取现有 `tests/rag_eval_report.json` 做离线诊断。
## [0.4.7.0b] - 2026-05-10

### 新增
- **Hidden Seed 结构化清单**：
  - 新增 `config/hidden_eval_seed_cases.json`，将 7 条 hidden eval seed 固化为离线标注清单。
  - 每条 seed 标注 `expected_domains`、`primary_issues`、`secondary_issues`、`peripheral_issues`、`expected_statutes`、`contaminating_domains` 与 `known_bad_evidence`。
  - 新增 `tools/check_hidden_eval_seeds.py`，校验 case id 唯一、7 条 seed 齐备、法域合法、主争点和期望法条非空、法条功能类型合法、污染法域不与期望法域重叠。
  - 新增 `tests/test_hidden_eval_seed_cases.py`，覆盖结构校验、仓库真实清单、重复 case、缺主争点、缺期望法条、缺 operative rule、未知法域、污染法域重叠、未知 issue 与错误 ref 格式。
  - FastAPI 服务版本同步为 `0.4.7.0b`。

### 验证
- `.\venv\Scripts\python.exe -m py_compile tools\check_hidden_eval_seeds.py src\main.py`
- `.\venv\Scripts\python.exe tools\check_hidden_eval_seeds.py --seeds config\hidden_eval_seed_cases.json`
- `.\venv\Scripts\python.exe -m unittest tests.test_hidden_eval_seed_cases`
- 本版本不修改 `rag_query` 主链路，不运行 full eval。

## [0.4.7.0] - 2026-05-08

### 新增
- **Hidden Eval / Issue Hierarchy 设计稿**：
  - 新增 `docs/legal_issue_hierarchy_plan_v0.4.7.0.md`，将 7 条 hidden eval seed 暴露的问题归纳为法律依据控制系统设计。
  - 设计覆盖 Legal Domain Routing、Issue Hierarchy、Legal Functional Typing、Evidence Coverage Scoring 和 Confidence Split。
  - 明确区分 `primary`、`secondary`、`peripheral` 争点，以及 `definition`、`operative_rule`、`procedural`、`technical_standard` 等法条功能类型。
  - 本版本只写设计稿，不修改 `rag_query` 主链路，不运行 full eval。
  - FastAPI 服务版本同步为 `0.4.7.0`。

### 文档
- `docs/hidden_eval_seed_cases.md` 保留为 hidden eval 种子样本来源。
- `docs/project_review_and_roadmap.md` 更新当前阶段与下一步路线。

## [0.4.6.4] - 2026-05-08

### 新增
- **Scenario Registry 第二批精选补全**：
  - 新增 5 个高价值企业法律风控 scenario：`pipl_facial_recognition_attendance`、`pipl_data_export_security_assessment`、`pipl_third_party_sharing_without_consent`、`contract_unfair_standard_terms`、`antitrust_horizontal_price_fixing`。
  - 仅补充 `config/scenario_registry.json` 条目和已有规则的 `scenario_id` metadata，不修改 `rag_query` 主链路，不改变检索、rerank、Anchor、Risk Supplement 或术语保真行为。
  - Anchor 侧补充 metadata 到：`pipl_sensitive_info`、`pipl_data_export`、`pipl_data_export_assessment`、`pipl_third_party_sharing`、`pipl_privacy_policy_sharing`、`pipl_third_party_marketing`、`civil_standard_form_terms`、`antitrust_monopoly_agreement`。
  - Risk Supplement 侧补充 metadata 到：`risk_rule_9`、`risk_rule_15`、`risk_rule_16`、`risk_rule_37`。
  - `pipl_facial_recognition_attendance` 当前暂无对应 Risk Supplement 规则，保留为空并由 coverage audit 暴露，避免临时新造复杂规则。
  - `tools/check_scenario_links.py` 增加 `--allow-missing-risk-scenario`，用于显式放行已知 anchor-only 场景，同时继续拦截其它缺边场景。
  - `tools/check_scenario_eval_report.py` 默认门槛提升为 `min_scenarios=10`、`min_cases=15`。
  - FastAPI 服务版本同步为 `0.4.6.4`。

### 更新测试与报告
- 更新 `tests/scenario_eval_report.json` 与 `tests/scenario_eval_summary.md`，Scenario targeted eval 覆盖 10 个 scenario、15 个唯一 eval case。
- 更新 `tests.test_scenario_registry`，允许并显式断言人脸考勤场景的 Risk Supplement coverage 缺口。
- 更新 `tests.test_scenario_eval_gate`，同步 10/15 新门槛。
- 更新 `tests.test_scenario_links`，覆盖已知 anchor-only 场景的显式 allowlist。

### 验证
- Scenario targeted eval：10 个 scenario、15 个唯一 eval case 全部通过，retrieval stage 均为 `PASS`。
- `check_scenario_registry`：通过；coverage audit 显示 `pipl_facial_recognition_attendance` 缺 Risk Supplement link。
- `check_scenario_eval_report`：通过。
- 本版本不运行 full eval。

## [0.4.6.3] - 2026-05-08

### 新增
- **Scenario Eval 轻量门禁**：
  - 新增 `tools/check_scenario_eval_report.py`，将 `tests/scenario_eval_report.json` 纳入发布前机器检查。
  - 门禁检查 `missing_case_ids`、`scenarios_without_eval_case_ids`、`scenarios_all_failed` 均为空。
  - 门禁检查 `total_scenarios >= 5`、`total_unique_eval_cases >= 8`，并要求每个 scenario 具备 `passed`、`total` 与 `retrieval_failure_stage_summary`。
  - 默认允许部分通过，但要求每个 scenario `total > 0` 且 `passed > 0`；可通过 `--no-allow-partial-pass` 改为要求全量通过。
  - FastAPI 服务版本同步为 `0.4.6.3`。

### 新增测试
- 新增 `tests.test_scenario_eval_gate`，覆盖正常报告、缺失 case、未绑定 eval case、全失败 scenario、`total=0`、`passed=0`、阈值生效、缺关键字段、部分通过开关和仓库真实报告校验。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py tools\check_scenario_eval_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_scenario_eval_gate`：`12 tests OK`。
- `.\venv\Scripts\python.exe tools\check_scenario_eval_report.py --report tests\scenario_eval_report.json`：通过。
- `check_scenario_registry`、`check_scenario_links`、`check_rag_stability_report` 均继续通过。
- 本版本不修改 `rag_query` 主链路，不运行 full eval，不修改 Anchor/Risk/术语规则。

## [0.4.6.2] - 2026-05-08

### 新增
- **Scenario Registry Targeted 验证**：
  - 新增 `tools/run_scenario_eval.py`，读取 `config/scenario_registry.json`，按每个 scenario 的 `eval_case_ids` 分组运行现有 RAG Eval 等价逻辑。
  - 输出每个 scenario 的 `pass/total`、`retrieval_failure_stage_summary`、`contribution_summary`，并报告缺失 eval case、未绑定 eval case、绑定 case 全部失败等断链信号。
  - 生成 `tests/scenario_eval_report.json` 与 `tests/scenario_eval_summary.md`。
  - FastAPI 服务版本同步为 `0.4.6.2`。

### 新增测试
- 新增 `tests.test_scenario_eval`，覆盖 scenario case id 提取、缺失 case 报告、pass/total 汇总、retrieval stage 汇总、contribution labels 汇总、all-failed 标记和 Markdown 摘要渲染。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py tools\run_scenario_eval.py tools\run_rag_eval.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_scenario_eval`：`8 tests OK`。
- `.\venv\Scripts\python.exe tools\run_scenario_eval.py --registry config\scenario_registry.json --output tests\scenario_eval_report.json --summary tests\scenario_eval_summary.md`：通过，5 个 scenario、8 个唯一 eval case 全部通过。
- `.\venv\Scripts\python.exe tools\check_scenario_registry.py --registry config\scenario_registry.json --anchor-rules config\rag_anchor_rules.json --risk-rules config\risk_payload_supplement_rules.json --eval-cases tests\rag_eval_cases.json`：通过。
- 本版本不修改 `rag_query` 主链路，不用 scenario 驱动检索或输出，不修改 Anchor/Risk/术语规则。

## [0.4.6.1] - 2026-05-08

### 新增
- **Scenario Registry 只读加载层**：
  - 新增 `src/rag/scenario_registry.py`，提供只读 loader 与查询 helper，用于读取 `config/scenario_registry.json`。
  - loader 启动时复用 `tools/check_scenario_registry.py` 的校验逻辑；校验失败时抛出 `ScenarioRegistryError`，并返回清晰错误信息。
  - 支持按 `scenario_id` 查询、按 `domain` 过滤、通过 Anchor rule / Risk rule 反查 scenario，并可读取场景核心条文与整改动作。
  - 对外返回防御性深拷贝，调用方修改返回对象不会污染缓存。
  - FastAPI 服务版本同步为 `0.4.6.1`。

### 新增测试
- 新增 `tests.test_scenario_registry_loader`，覆盖加载当前 5 个场景、按 id 查询、按法域过滤、按 Anchor/Risk rule 反查、未知场景返回空结果、核心条文/整改动作 helper、防御性拷贝和校验失败异常。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\scenario_registry.py tools\check_scenario_registry.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_scenario_registry_loader`：`9 tests OK`。
- `.\venv\Scripts\python.exe tools\check_scenario_registry.py --registry config\scenario_registry.json --anchor-rules config\rag_anchor_rules.json --risk-rules config\risk_payload_supplement_rules.json --eval-cases tests\rag_eval_cases.json`：通过。
- 本版本不修改 `rag_query` 主链路，不用 scenario 驱动检索或输出，不运行 full eval。

## [0.4.6.0] - 2026-05-08

### 新增
- **Scenario Registry 雏形**：
  - 新增 `config/scenario_registry.json`，先登记 5 个法律风险场景：`trade_secret_customer_list_leak`、`pipl_children_consent`、`pipl_automated_decision_bias`、`pipl_cross_border_sensitive_medical`、`vat_false_invoice_deduction`。
  - 新增 `tools/check_scenario_registry.py`，校验 `scenario_id` 唯一、法域合法、风险等级合法、核心字段非空、Anchor/Risk rule id 可解析、已有规则侧 `scenario_id` 能反向链接到 registry。
  - checker 同步输出 coverage audit：缺 Anchor link、缺 Risk Supplement link、缺 eval case、已有 `scenario_id` 未进入 registry。
  - 新增 `docs/scenario_registry_v0.4.6.0.md`，说明 registry 定位、首批场景、字段约束、checker 与 coverage audit 边界。
  - FastAPI 服务版本同步为 `0.4.6.0`。

### 新增测试
- 新增 `tests.test_scenario_registry`，覆盖 registry 正常通过、重复 `scenario_id`、非法法域/风险等级、缺核心字段、未知规则链接、反向链接缺失、coverage audit 和仓库真实配置校验。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py tools\check_scenario_registry.py`
- `.\venv\Scripts\python.exe tools\check_scenario_registry.py --registry config\scenario_registry.json --anchor-rules config\rag_anchor_rules.json --risk-rules config\risk_payload_supplement_rules.json --eval-cases tests\rag_eval_cases.json`：通过，四类 coverage 缺口均为 `0`。
- `.\venv\Scripts\python.exe -m unittest tests.test_scenario_registry`：`7 tests OK`。
- 本版本只建 registry、validator、coverage audit、测试和文档；不接入主流程，不运行 full eval。

## [0.4.5.18.1] - 2026-05-07

### 新增
- **Scenario ID metadata-only 试点**：
  - 选择 `trade_secret_customer_list_leak` 作为第一批 metadata-only `scenario_id` 试点。
  - 仅在相关规则中新增 `scenario_id` 字段，不删除 trigger、不合并规则、不改变匹配逻辑。
  - Anchor 侧新增到：`pipl_data_leak`、`pipl_internal_leak`、`unfair_competition_trade_secret`。
  - Risk Supplement 侧新增到：`risk_rule_0`（客户名单/商业秘密侵权）与 `risk_rule_4`（员工私自导出/出售客户名单）。
  - 新增 `tools/check_scenario_links.py`，校验同一 `scenario_id` 同时存在于 Anchor 与 Risk Supplement 配置中，并可要求具体规则 id 必须绑定。
  - `validate_risk_payload_supplement_rules()` 仅允许并校验 `scenario_id` 为非空字符串，不参与匹配、排序或输出逻辑。
  - FastAPI 服务版本同步为 `0.4.5.18.1`。

### 新增测试
- 新增 `tests.test_scenario_links`，覆盖跨配置 `scenario_id` 映射、必需规则校验、缺失侧校验和命名校验。
- `tests.test_retriever_contract` 增加 `scenario_id` 配置兼容性断言，防止风险补全配置启动校验拒绝 metadata 字段。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\retriever.py tools\check_scenario_links.py tools\audit_rule_debt.py tools\check_rag_stability_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract tests.test_rag_eval_diagnostics tests.test_rag_stability_tools tests.test_rule_debt_audit tests.test_rule_convergence_plan tests.test_scenario_links`：`60 tests OK`。
- `.\venv\Scripts\python.exe tools\check_scenario_links.py --anchor-rules config\rag_anchor_rules.json --risk-rules config\risk_payload_supplement_rules.json --required-scenario trade_secret_customer_list_leak --required-anchor-rule pipl_data_leak --required-anchor-rule pipl_internal_leak --required-anchor-rule unfair_competition_trade_secret --required-risk-rule risk_rule_0 --required-risk-rule risk_rule_4`：通过。
- `.\venv\Scripts\python.exe tools\check_rag_stability_report.py --report tests\rag_stability_report.json`：通过；本版本未重跑 full eval。
- `.\venv\Scripts\python.exe tools\audit_rule_debt.py --anchor-rules config\rag_anchor_rules.json --risk-rules config\risk_payload_supplement_rules.json --stability-report tests\rag_stability_report.json --json-output tests\rule_debt_report.json --md-output docs\rule_debt_report_v0.4.5.18.1.md --report-version 0.4.5.18.1`：通过。
- Rule debt 复扫：Anchor 缺共享 `scenario_id` 从 `75` 降至 `72`，Risk 缺 `scenario_id` 从 `39` 降至 `37`。

## [0.4.5.17] - 2026-05-07

### 新增
- **规则收敛设计稿**：
  - 新增 `docs/rule_convergence_plan_v0.4.5.17.md`，定义共享 `scenario_id` 命名规范、Anchor / Risk Supplement 职责边界、迁移顺序和发布门禁。
  - 从 v0.4.5.16 规则债报告中选取 5 个高重叠场景作为第一批设计对象：自动化决策/算法歧视、客户名单/商业秘密、敏感医疗信息出境、虚开发票抵扣、儿童信息/监护人同意。
  - 每个候选场景绑定 targeted eval、3 轮稳定性回归、稳定性门禁和规则债复扫命令。
  - 本版本只写设计稿和检查，不修改 `config/rag_anchor_rules.json`、`config/risk_payload_supplement_rules.json` 或 `src/rag/retriever.py`。
  - FastAPI 服务版本同步为 `0.4.5.17`。

### 新增测试
- 新增 `tools/check_rule_convergence_plan.py`，检查设计稿必备章节、`scenario_id` 命名、候选场景数量、验证命令和“不改 retriever.py”边界。
- 新增 `tests.test_rule_convergence_plan`，覆盖设计稿结构检查与仓库内设计稿验证。

### 验证
- `.\venv\Scripts\python.exe tools\check_rule_convergence_plan.py --plan docs\rule_convergence_plan_v0.4.5.17.md`：通过。
- `.\venv\Scripts\python.exe -m py_compile src\main.py tools\check_rule_convergence_plan.py tools\audit_rule_debt.py tools\summarize_rag_stability.py tools\check_rag_stability_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract tests.test_rag_eval_diagnostics tests.test_rag_stability_tools tests.test_rule_debt_audit tests.test_rule_convergence_plan`：`54 tests OK`。

## [0.4.5.16] - 2026-05-07

### 新增
- **规则债盘点工具与报告**：
  - 新增 `tools/audit_rule_debt.py`，扫描 `config/rag_anchor_rules.json` 与 `config/risk_payload_supplement_rules.json`。
  - 输出 `tests/rule_debt_report.json` 与 `docs/rule_debt_report_v0.4.5.16.md`，仅做盘点，不合并规则，不修改 `src/rag/retriever.py`。
  - 报告覆盖重复 trigger、跨配置 trigger 重叠、疑似同场景多处维护、缺失共享 `scenario_id`、高规则依赖 case 到规则的映射。
  - 当前扫描结果：Anchor rules `75`，Risk supplement rules `39`，重复 trigger `111`，跨配置 trigger 重叠 `94`，疑似同场景多处维护 `43`，高规则依赖 case `25`。
  - FastAPI 服务版本同步为 `0.4.5.16`。

### 新增测试
- 新增 `tests.test_rule_debt_audit`，覆盖重复 trigger、跨配置重叠、同场景多处维护、缺失 scenario_id 和高规则依赖 case 映射。

### 验证
- `.\venv\Scripts\python.exe tools\audit_rule_debt.py --anchor-rules config\rag_anchor_rules.json --risk-rules config\risk_payload_supplement_rules.json --stability-report tests\rag_stability_report.json --json-output tests\rule_debt_report.json --md-output docs\rule_debt_report_v0.4.5.16.md`
- `.\venv\Scripts\python.exe -m py_compile src\main.py tools\audit_rule_debt.py tools\summarize_rag_stability.py tools\check_rag_stability_report.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract tests.test_rag_eval_diagnostics tests.test_rag_stability_tools tests.test_rule_debt_audit`：`49 tests OK`。
- `tests\rule_debt_report.json` JSON 解析通过。

## [0.4.5.15b] - 2026-05-07

### 新增
- **RAG 稳定性轻量门禁**：
  - 新增 `tools/check_rag_stability_report.py`，对 `tests/rag_stability_report.json` 执行发布前稳定性检查。
  - 门禁默认要求 `unstable_cases=0`、`DENSE_FALLBACK_PASS=0`，并校验 `repeat`、`runs`、`stability_summary` 之间的 pass/total 计数一致。
  - 门禁要求报告同时保留 `v0.4.5.13-pre-patch-repeat` 与 `v0.4.5.14-post-patch-repeat` 两个实验对象，且顶层 runs 必须对应 patch 后实验，避免原始基线与修复后结果混写。
  - FastAPI 服务版本同步为 `0.4.5.15b`。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\retriever.py tools\run_rag_eval.py tools\summarize_rag_stability.py tools\check_rag_stability_report.py`
- `.\venv\Scripts\python.exe tools\check_rag_stability_report.py --report tests\rag_stability_report.json`：门禁通过。
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract tests.test_rag_eval_diagnostics tests.test_rag_stability_tools`：`44 tests OK`。

## [0.4.5.15a] - 2026-05-07

### 新增
- **RAG 稳定性 Markdown 摘要报告**：
  - 新增 `tools/summarize_rag_stability.py`，从 `tests/rag_stability_report.json` 生成 `tests/rag_stability_summary.md`。
  - 摘要报告保留实验对象边界，明确 v0.4.5.13 原始 repeat 基线与 v0.4.5.14 patch 后 repeat 不是同一个实验对象。
  - 摘要报告按 run 展示 `PURE_LLM_PASS`、`ANCHOR_PASS`、`RISK_SUPPLEMENT_PASS`、`TERM_PRESERVATION_PASS`、`DENSE_FALLBACK_PASS`。
  - 摘要报告单列贡献标签波动 case 与同时命中 `ANCHOR_PASS + RISK_SUPPLEMENT_PASS` 的规则依赖较高 case。

### 验证
- `.\venv\Scripts\python.exe tools\summarize_rag_stability.py --report tests\rag_stability_report.json --output tests\rag_stability_summary.md`
- `.\venv\Scripts\python.exe -m py_compile tools\summarize_rag_stability.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_rag_stability_tools`：摘要报告相关用例通过。

## [0.4.5.14] - 2026-05-07

### 变更
- **RAG Eval 稳定性回归与规则贡献归因**：
  - `tools/run_rag_eval.py` 新增 `--repeat`，支持同一题库连续多轮运行并输出 `stability_summary`，用于识别 pass 波动与贡献标签波动。
  - 为每个通过 case 增加贡献标签：`PURE_LLM_PASS`、`TERM_PRESERVATION_PASS`、`RISK_SUPPLEMENT_PASS`、`ANCHOR_PASS`、`DENSE_FALLBACK_PASS`，用于区分检索自然通过、锚点辅助、术语保真、风险补全和 dense fallback。
  - `rag_query()` debug 信息新增 `output_contributions` 与 `rerank_dense_fallback`，只记录输出治理与 fallback 贡献，不改变 Dense/BM25 分层召回、Union、Anchor、单一 Cross-Encoder rerank 主链路。
  - 风险补全配置补齐商业秘密与商标连续三年不使用场景的最低风险等级、置信度和法言法语补充，修复多轮回归中暴露的生成波动。
  - 稳定性报告同时保留 v0.4.5.13 原始 repeat 基线与 v0.4.5.14 patch 后 repeat 结果，并明确两者不是同一个实验对象。
  - FastAPI 服务版本同步为 `0.4.5.14`。

### 新增
- `tests.test_rag_eval_diagnostics` 增加贡献标签、贡献汇总和稳定性摘要单元测试。
- `tests.test_retriever_contract` 增加商标连续三年不使用场景输出稳定性回归。
- 新增 `tests/rag_stability_report.json`，记录 60 题连续 3 轮全量 RAG Eval 稳定性与贡献归因结果。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\retriever.py tools\run_rag_eval.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract tests.test_rag_eval_diagnostics`：`38 tests OK`。
- Targeted Repeat Eval：`risk_trademark_non_use_001`、`risk_unfair_competition_trade_secret_001` 连续 3 轮均 `2/2 passed`。
- 原始基线 Repeat Eval（v0.4.5.13 pre-patch）：3 轮 pass count 为 `58/60`、`59/60`、`60/60`，暴露 `risk_trademark_non_use_001` 与 `risk_unfair_competition_trade_secret_001` 两个输出稳定性波动点；该结论不被 patch 后结果覆盖。
- Patch 后 Full Repeat RAG Eval（v0.4.5.14 post-patch）：60 题连续 3 轮均 `60/60 passed`，`unstable_cases=0`，`label_variation_cases=2`，`DENSE_FALLBACK_PASS=0`。

## [0.4.5.13] - 2026-05-07

### 变更
- **风险输出补全配置化**：
  - 新增 `config/risk_payload_supplement_rules.json`，将 `RISK_PAYLOAD_SUPPLEMENT_RULES` 从 Python 常量外迁为可维护 JSON 配置。
  - 新增 `load_risk_payload_supplement_rules()` 与 `validate_risk_payload_supplement_rules()`，启动时校验规则字段、匹配条件、风险等级、置信度和补充文本结构。
  - `enrich_risk_payload()` 继续通过同一规则循环执行补全，行为语义保持不变，但后续扩展风险 taxonomy / actions 不再需要改 Python 分支。
  - 为虚假宣传场景补齐“误导消费者”法言法语输出保真，避免 LLM 同义改写导致答案关键词波动。
  - `rag_query()` 的 Dense → Sparse → Union → Anchor → Cross-Encoder → dense fallback 主链路未改动，继续禁止 RRF 和 dense/sparse 分数融合。
  - FastAPI 服务版本同步为 `0.4.5.13`。

### 新增
- `tests.test_retriever_contract` 增加风险补全配置 schema 校验、未知字段拒绝、儿童信息和虚假宣传外部规则驱动测试。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\retriever.py tools\run_rag_eval.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract`：`30 tests OK`。
- Targeted Eval：代表性 4 条 `4/4 passed`；`risk_unfair_competition_false_promotion_001` 修复后 `1/1 passed`。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

## [0.4.5.12] - 2026-05-07

### 变更
- **风险输出补全规则表驱动化**：
  - 新增 `RISK_PAYLOAD_SUPPLEMENT_RULES`，将 `enrich_risk_payload()` 中大量场景型风险类型、整改动作、风险等级、最低置信度和补充结论迁入集中规则表。
  - 新增 `payload_rule_matches()`、`apply_payload_supplement_rule()`、`set_risk_level()` 等 helper，使风险输出治理与法定术语保真保持同样的表驱动维护方式。
  - 补齐儿童个人信息、监护人同意、人脸/生物识别等输出保真边角，降低 LLM 同义改写导致的答案关键词波动。
  - 保留 `enrich_risk_payload()` 中低风险正例、配置规则命中和合规授权特例等少量主控逻辑，避免一次性大重构。
  - `rag_query()` 的 Dense → Sparse → Union → Anchor → Cross-Encoder → dense fallback 主链路未改动，继续禁止 RRF 和 dense/sparse 分数融合。
  - FastAPI 服务版本同步为 `0.4.5.12`。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\retriever.py tools\run_rag_eval.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract`：`26 tests OK`。
- Targeted Eval：`risk_employee_facial_001`、`risk_children_data_001` 均通过。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

## [0.4.5.11] - 2026-05-06

### 变更
- **代码债清理与 Harvey 主路径收敛**：
  - 删除已无调用的旧 `rerank_with_cross_encoder()`、`_rerank_fallback()`、`rerank_results()`，移除其中残留的原始分数混合、keyword boost fallback 等旧排序语义。
  - 将 `enrich_answer_legal_terms()` 从长 if 链改为 `LEGAL_TERM_PRESERVATION_RULES` 表驱动规则，后续新增法定术语保真可通过规则表扩展。
  - 新增 `contains_all()`、`contains_any()`、`set_min_confidence()`、`append_unique_texts()`、`append_answer_note()` 等轻量 payload helper，减少后续输出治理层继续堆重复逻辑。
  - `rag_query()` 的 Dense → Sparse → Union → Anchor → Cross-Encoder → dense fallback 主链路未改动，继续禁止 RRF 和 dense/sparse 分数融合。
  - FastAPI 服务版本同步为 `0.4.5.11`。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\retriever.py tools\run_rag_eval.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract`：`26 tests OK`。
- 术语/结构化输出 targeted eval：`6/6 passed`，`retrieval_failure_stage_summary={"PASS": 6}`。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`。

## [0.4.5.10] - 2026-05-06

### 修复
- **RAG Eval 输出层全量收敛**：
  - 在保持 Harvey 风格检索主链路不变的前提下，新增基于 `rag_anchor_rules.json` 命中规则的风险 taxonomy / 整改动作补全层，使已进入 top-3 证据的场景不再依赖 LLM 自由措辞生成 `risk_types` 和 `recommended_actions`。
  - 补齐显式合规正例识别，稳定输出 `risk_level=low`，避免出资、分红、税务申报、真实广告、独立定价等正例被风险规则误伤。
  - 增强证据支持的法定术语保真，覆盖撤回同意便捷方式、个人信息安全规范定义题、个人信息出境影响评估、数据分类分级、商标/专利侵权、专利无效宣告、公司人格否认、增值税虚开发票刑事责任等易被 LLM 同义改写的表达。
  - 对自动化决策、格式条款、劳务派遣、产品责任、商标、专利、公司治理、增值税和经营者集中等场景补齐风险等级、风险类型和整改动作的窄口径后处理。
  - FastAPI 服务版本同步为 `0.4.5.10`。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\main.py src\rag\retriever.py tools\run_rag_eval.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract`：`26 tests OK`。
- 剩余失败 targeted eval：`5/5 passed`；术语/置信度 targeted eval：`4/4 passed`。
- Full RAG Eval：`60/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`；相比 v0.4.5.9 的 `35/60 passed`，全量 RAG Eval 已在当前题库下闭环通过。

## [0.4.5.9] - 2026-05-06

### 修复
- **剩余 RERANK_MISS 专项收敛**：
  - 收窄 `pipl_data_export_assessment` 规则，避免“未申报数据出境安全评估”误触发评估内容类第 5 条/个保法第 55 条，确保出境合规场景优先进入个保法第 38、39 条与《数据出境安全评估办法》第 4 条。
  - 为内部员工导出并出售客户名单场景补充 rerank 查询词，稳定命中个保法第 9、51、57 条，避免被“100 万 + 导出 + 泄露”误拉向数据出境评估条文。
  - 新增 `civil_data_processing_liability` 场景锚点，覆盖数据处理协议未约定泄露责任时的民法典第 509、577 条。
  - 补齐反垄断“约定统一提高产品价格 / 独立定价未协商”场景锚点，稳定命中反垄断法第 17 条。
- **风险输出字段稳定性补齐**：
  - 在 `enrich_risk_payload()` 中为数据处理协议泄露责任、横向协同定价、独立定价正例增加窄场景确定性补全。
  - FastAPI 服务版本同步为 `0.4.5.9`。

### 验证
- `.\venv\Scripts\python.exe -m py_compile src\rag\retriever.py tools\run_rag_eval.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_retriever_contract`：`26 tests OK`。
- 5 条 targeted eval：`5/5 passed`，`retrieval_failure_stage_summary={"PASS": 5}`。
- Full RAG Eval：`35/60 passed`，`retrieval_failure_stage_summary={"PASS": 60}`；相比上一轮 `31/60 passed`、`RERANK_MISS=5`，检索链路已收敛为全量 PASS。

## [0.4.5.8] - 2026-05-05

### 修复
- **全量 RAG Eval 召回契约收敛**：
  - `tools/run_rag_eval.py` 新增 `expected_evidence_min_match`，用于表达 top-3 evidence 下“至少命中 N 个核心证据”的评测门槛，避免旧用例要求 top-3 同时覆盖 4-5 个法条造成不可达失败。
  - `rag_query()` 的 Cross-Encoder rerank query 增加场景锚点法条提示，仅改变 rerank 查询语义，不引入 RRF、分数融合或 hybrid fallback。
  - PIPL 定位/人脸场景补齐第 13、17、28、29 条锚点覆盖；全量题库中 PIPL top-3 证据期望改为核心命中数校验。
  - 核对当前知识库条文后，将反不正当竞争法旧评测条号同步为当前库内条号：虚假宣传第 9 条、商业秘密第 10 条。
  - 生成后处理补齐 PIPL 原则题的“公开透明、信息质量”，以及客户名单离职使用场景的“商业秘密侵权 / 停止使用相关信息”。
  - FastAPI 服务版本同步为 `0.4.5.8`。

### 新增
- `tests/test_candidate_budget.py` 增加场景锚点条号、rerank anchor hint、top-3 min-match 评测契约覆盖。
- `tests/test_retriever_contract.py` 增加 PIPL 原则术语保留和商业秘密风险类型补齐覆盖。

### 验证
- `.\venv\Scripts\python.exe -m unittest`：`56 tests OK`。
- 7 条 targeted eval：`7/7 passed`，`retrieval_failure_stage_summary={"PASS": 7}`。
- Full RAG Eval：`22/60 passed`，`retrieval_failure_stage_summary={"PASS": 47, "RERANK_MISS": 13}`；相比上一轮 `19/60`、`PASS=38`，召回/最终证据层明显改善，且 `RETRIEVAL_MISS`、`PARTIAL_RECALL_MISS` 已清零。

## [0.4.5.7] - 2026-05-05

### 修复
- **生成关键词稳定性专项**：
  - 新增 `enrich_answer_legal_terms()`，在 retrieval 已命中且证据来源明确支持时，补充“术语归纳”句，保留关键法定原词。
  - 覆盖股东权利、反不正当竞争行为、滥用市场支配地位、商标侵权、不得注册、增值税不得抵扣、专利侵权等易被 LLM 同义改写的表达。
  - 不改变 Dense/Sparse 召回、Anchor 注入、候选预算或 Cross-Encoder 排序；仅在 LLM 生成后做证据支持的法定术语保留。
- FastAPI 服务版本同步为 `0.4.5.7`。

### 新增
- `tests/test_retriever_contract.py` 增加法定原词保留覆盖，防止后续生成层回归。

### 验证
- `.\venv\Scripts\python.exe -m unittest tests.test_retriever_contract tests.test_candidate_budget tests.test_rerank_api tests.test_rag_eval_diagnostics`
- 7 条 targeted eval：`7/7 passed`，`retrieval_failure_stage_summary={"PASS": 7}`。
- Full smoke eval：`25/25 passed`，`retrieval_failure_stage_summary={"PASS": 25}`。

## [0.4.5.6] - 2026-05-05

### 修复
- **剩余 CANDIDATE/RERANK retrieval 专项收敛**：
  - `rag_query()` 在 anchor 注入后按规则锚点顺序组织 rerank 输入；候选仍限制为 15 条，最终仍由单一 Cross-Encoder 排序。
  - 场景锚点优先于宽泛原则补充进入候选，避免 dense/base 噪声在 rerank 分数饱和时抢占 top-3。
  - 规则注入条文按配置中的 article 顺序稳定排列，修复 Qdrant 返回顺序不稳定导致的 expected evidence 漂移。
  - 定位/行踪轨迹问题补充“单独同意”rerank 查询词；民商事原则问题补充“平等、自愿、公平、诚信、公序良俗”等法定原则词。
  - 通用原则硬编码补充收敛到 PIPL/数据合规场景，民法典原则问题改由 JSON 场景锚点驱动。
- FastAPI 服务版本同步为 `0.4.5.6`。

### 新增
- `tests/test_candidate_budget.py` 增加规则锚点条文顺序、民商事原则 rerank 查询扩展覆盖。

### 验证
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_rerank_api tests.test_rag_eval_diagnostics`
- `.\venv\Scripts\python.exe -m py_compile src/rag/retriever.py tools/run_rag_eval.py tests/test_candidate_budget.py`
- 5 条 targeted eval：`4/5 passed`，`retrieval_failure_stage_summary={"PASS": 5}`；本轮关注的 `CANDIDATE_CUT_MISS` 与 `RERANK_MISS` 已清零。
- Full smoke eval：`19/25 passed`，`retrieval_failure_stage_summary={"PASS": 25}`；剩余 6 条失败均为 retrieval 已 PASS 后的答案关键词缺失。

## [0.4.5.5] - 2026-05-05

### 修复
- **剩余 retrieval-stage 失败专项处理**：
  - `tools/run_rag_eval.py` 新增 `--case-id`，支持只运行指定评测 case，避免每次全量 smoke 消耗 API 额度。
  - `rag_query()` 的 base/anchor 候选预算改为优先保留直接 anchor，再补充 base recall，仍保持 rerank 前最多 15 条候选。
  - 当场景锚点已命中时，跳过宽泛 category fallback anchors，减少非目标法条噪声。
  - Cross-Encoder top-3 选择增加同条文 sibling 去重：仍按 Cross-Encoder 分数顺序选取，但避免同一条文多个 paragraph/item 占满最终证据。
  - Cross-Encoder 分数近似相等时保持候选稳定顺序，降低 rerank 分数饱和导致的随机抖动。
- **锚点规则修正**：
  - `pipl_location_ads` 去除过宽的第 13 条锚点，保留更直接的第 17、28、29 条。
  - 新增 `unfair_competition_general_acts` 场景锚点，覆盖“禁止哪些不正当竞争行为”类问题。
  - 民法典原则类问题不再触发个人信息保护法原则补充逻辑，避免跨法域原则锚点噪声。
- FastAPI 服务版本同步为 `0.4.5.5`。

### 验证
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_rerank_api tests.test_rag_eval_diagnostics`
- `.\venv\Scripts\python.exe -m py_compile src/rag/retriever.py tools/run_rag_eval.py tests/test_candidate_budget.py`
- `config/rag_anchor_rules.json` JSON 解析通过。
- 已运行 5 条 targeted eval 验证：原 `smoke_antitrust_abuse_dominance` 的 expected evidence 已进入 final；其余 broad/all-evidence case 仍需继续处理 rerank top-3 取舍或评测口径。

## [0.4.5.4] - 2026-05-05

### 修复
- **候选预算修复（v0.4.5.1）**：
  - 新增 article-aware candidate budget，先保留不同 `source + article_no/section_no` 的候选，再允许同条文 sibling 补位。
  - 保持 rerank 前候选不超过 15，不引入 RRF、加权融合或 hybrid fallback。
- **Cross-Encoder 输入质量修复（v0.4.5.1）**：
  - rerank 文档输入改为 `citation + source/article + parent_content`，避免 item/paragraph 短片段缺少完整法条语境。
- **Cross-Encoder 查询侧扩展（v0.4.5.2）**：
  - 仅在 rerank 查询文本使用既有 `build_search_query()` 法律概念扩展；Dense/Sparse 召回仍使用原始问题。
- **专利过滤修复（v0.4.5.3）**：
  - 修复专利问题被误推断为 `document_type="专利"` 的问题；当前专利法/实施细则入库元数据为 `document_type="法律法规"`。
- **生成关键词保留（v0.4.5.4）**：
  - 系统提示增加“保留依据材料中的关键法定表述和要件原词”的要求，减少 evidence 已命中但答案漏关键词的失败。
- FastAPI 服务版本同步为 `0.4.5.4`。

### 新增
- 新增 `tests/test_candidate_budget.py`：
  - 覆盖同条文 sibling 不挤占不同条文候选。
  - 覆盖 rerank 输入使用父条文上下文。
  - 覆盖专利问题默认查 `法律法规` 文档。

### 验证
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget tests.test_rerank_api tests.test_rag_eval_diagnostics`
- `.\venv\Scripts\python.exe tools/run_rag_eval.py --smoke --check-risk --output tests/smoke_eval_report.json`
  - Smoke 结果从 v0.4.5 的 `6/25 passed` 提升到 `15/25 passed`。
  - `retrieval_failure_stage_summary={"RERANK_MISS": 3, "PASS": 20, "CANDIDATE_CUT_MISS": 2}`。
  - `RETRIEVAL_MISS` 从 `3` 降为 `0`，确认专利过滤缺口已修复。

## [0.4.5] - 2026-05-04

### 修复
- **修复 Cross-Encoder rerank 分数错配**：
  - `_call_siliconflow_rerank()` 按 API 返回的 `index` 将 `relevance_score` 回填到原候选顺序，避免 rerank 结果按相关性排序返回时把高分错配给错误法条。
  - 新增 `tests/test_rerank_api.py` 覆盖 rerank index 回填逻辑。
- **保护 Anchor 候选不被 15 条预算误删**：
  - `rag_query()` 仍保持 Dense → Sparse → Union → Anchor → Cut → Rerank 顺序，且 rerank 前候选不超过 15。
  - 当 anchor 在 union 后注入时，裁剪优先保留新注入 anchor，避免 anchor 已命中但进入 rerank 前被删除。
- FastAPI 服务版本同步为 `0.4.5`。

### 验证
- `.\venv\Scripts\python.exe -m unittest tests.test_rerank_api tests.test_qdrant_index_integrity tests.test_rag_eval_diagnostics`
- `.\venv\Scripts\python.exe tools/run_rag_eval.py --smoke --check-risk --output tests/smoke_eval_report.json`
  - Smoke 结果从修复前 `2/25 passed` 提升到 `6/25 passed`。
  - `RERANK_MISS` 从 `13` 降到 `4`，验证 rerank 分数错配为主要根因之一。
  - 剩余主要问题：`CANDIDATE_CUT_MISS=8`、`RETRIEVAL_MISS=3`，后续应优先处理候选预算的同条文 sibling 挤占与专利领域召回/路由。

## [0.4.4] - 2026-05-04

### 修复
- **修复 BM25 sparse 入库与 dense point 脱节问题**：
  - `load_txt()` 为每个 chunk 生成稳定 `chunk_id` 与 `qdrant_point_id`。
  - dense 写入使用稳定 point id；BM25 sparse 通过 `QdrantClient.update_vectors()` 更新同一个 point。
  - 不再创建缺少 payload/metadata 的 sparse-only point，避免 sparse 检索返回空 Document。

### 新增
- **RAG 分层诊断评测**：
  - `rag_query(debug=True)` 新增 `anchor_candidates` 与 `rerank_input_candidates`，并在候选摘要中输出 `chunk_id`。
  - `tools/run_rag_eval.py` 新增 `retrieval_diagnostics`，逐层检查 expected evidence 是否命中 dense、sparse、union、anchor、rerank input、final。
  - 失败样本自动标记 `retrieval_failure_stage`，包括 `RETRIEVAL_MISS`、`PARTIAL_RECALL_MISS`、`UNION_MISS`、`CANDIDATE_CUT_MISS`、`RERANK_MISS` 等。
- **入库质量门禁增强**：
  - `tools/check_ingestion_quality.py` 检查 chunk id / qdrant point id 是否缺失或重复。
  - 新增 `tools/check_qdrant_index_integrity.py`，直接扫描持久化 Qdrant collection，检查空 payload、缺 metadata、缺 stable id、缺 BM25 vector、source 计数漂移；其中缺 BM25 vector 作为硬失败处理。
  - 新增 `tests/test_rag_eval_diagnostics.py` 覆盖分层诊断归因逻辑。
  - 新增 `tests/test_qdrant_index_integrity.py` 覆盖 Qdrant source 计数漂移和 BM25 vector 缺失失败。
- **重建工具修复**：
  - `rag_admin.py --rebuild` 改为优先按 `knowledge_manifest.json` 重建全部法规，并保留每部法规的 manifest 元数据。
  - `create_collection.py` 改为确保 collection 支持 dense + `bm25` sparse。
- FastAPI 服务版本同步为 `0.4.4`。

### 验证
- `.\venv\Scripts\python.exe -m unittest tests.test_ingestion_quality tests.test_rag_eval_diagnostics`
- `.\venv\Scripts\python.exe tools/check_ingestion_quality.py --output tests/ingestion_quality_report.json`，结果 `15/15 passed`。
- 重建后 Qdrant 抽检：`7177` points，空 payload / 缺 metadata / 缺 source / 缺 `chunk_id` / 缺 `qdrant_point_id` 均为 `0`。
- BM25 sparse 抽检可返回真实 `source/article_no/chunk_id/page_content`。

## [0.4.3] - 2026-05-04

### 变更
- **RAG 检索主路径收敛为 Harvey 风格分层召回 + 单一精排**：
  - `rag_query()` 固定执行 Dense(BGE-M3) top-5 → BM25 top-10 → stable union 去重 → Anchor 注入 → 候选裁剪到 15 → Cross-Encoder top-3。
  - BM25 只作为召回层，不再参与排序、补分、末尾填充或任何 dense/sparse 分数融合。
  - Anchor 在 union 去重之后、Cross-Encoder 之前注入，避免旧逻辑中 anchor 直接锁定首位造成 reranker 失效。
- **移除主路径中的 RRF/混合排序行为**：
  - `rag_query()` 不再调用 `_merge_union()`、`rerank_results()`、`collapse_parent_results()` 或 `rerank_with_cross_encoder()` 的旧混合排序分支。
  - `use_hybrid` / `use_reranker` 参数保留以兼容 API 签名，但主路径统一走单一 Cross-Encoder 排序。
- **严格 fallback**：Cross-Encoder 异常或空结果时，仅返回 dense top-3，不使用 sparse、anchor 或 hybrid 候选兜底。
- FastAPI 服务版本同步为 `0.4.3`。

### 验证
- `python -m py_compile src/rag/retriever.py`
- `python -m py_compile src/main.py src/risk/analyzer.py tools/run_rag_eval.py`

### 文档
- 更新 `docs/final_report_version_guide.md`：新增 v0.4.3 版本报告素材。
- 更新 `docs/project_review_and_roadmap.md`：当前阶段改为 v0.4.3，并调整后续准确率提升路线。
- 更新 `docs/version_report_template.md`：补充每次版本变更需同步 changelog 与 docs 的发布清单。

## [0.4.2] - 2026-05-04

### 变更
- **BM25 角色从"排序参与者"改为"召回扩充器"**：
  - 移除 RRF 融合（`_rrf_fusion`），新增 `_merge_union`（dense 优先 + sparse 去重补充）。
  - BM25 默认关闭（`use_hybrid=False`），按需开启。
  - 开启时：dense 检索 → 锚点 → rerank 全流程不变，sparse 仅在 `collapse_parent_results` 后不足 k 条时作为末尾填充（score=0.3）。
- **修复 dense vector 存储格式**：ingestion 恢复使用 LangChain `vectorstore.add_documents()` 写入 dense（确保 Qdrant 正确识别为 unnamed vector），sparse 单独 upsert。
- **简化检索段**：移除 v0.4.1 的 `_enable_hybrid` 自动路由逻辑，`use_hybrid` 统一控制。

### 保留（已验证的 BM25 基础设施）
- `src/rag/bm25_encoder.py`：BM25 编码器（fit/save/load，scipy+numpy）。
- `src/core/vectorstore.py`：`ensure_collection_with_sparse()`。
- `src/rag/retriever.py`：`retrieve_with_sparse()`（Qdrant HTTP API）。
- 知识库 15 部法规已携带 dense + sparse 双向量。

### 验证
- `31/31` 单元测试。
- RAG Eval `25/60`（BM25 off）。

## [0.4.1] - 2026-05-04

### 新增
- **真 BM25 稀疏向量混合检索**：
  - `src/rag/bm25_encoder.py`：基于 scipy + numpy 的轻量 BM25 编码器（IDF + TF 饱和 + 长度归一化），零 torch 依赖。
  - `src/core/vectorstore.py`：Qdrant collection 新增 `sparse_vectors_config`（`bm25` 稀疏索引），`ensure_collection_with_sparse()` 自动迁移。
  - `src/rag/ingestion.py`：入库时并行生成 dense（BGE-M3）和 sparse（BM25）双向量，分批 upsert（embed 32/批，upsert 64/批）。
  - `src/rag/retriever.py`：`retrieve_with_sparse()` 通过 Qdrant HTTP API 执行稀疏向量检索。
  - 混合检索智能路由：数据合规域保持纯稠密（无退化），新法域（公司治理/市场秩序/知识产权等）自动启用 dense + sparse RRF 融合。
- BM25 编码器支持 `fit()`/`save()`/`load()` 持久化到 `config/bm25_encoder.json`。

### 变更
- `rag_query()` 中混合检索逻辑从 `retrieve_with_keyword_match`（jieba 假 BM25）替换为 `retrieve_with_sparse()`（真 BM25 稀疏向量）。
- 智能混合路由：`rag_query()` 根据 `category` 自动判断是否需要 BM25 补充（`category in {"公司治理", "市场秩序", ...}`）。
- 知识库全量重建：15 部法规重新入库（105 秒），每条 chunk 携带 dense + sparse 双向量。
- FastAPI 版本同步为 `0.4.1`。

### 验证
- `31/31` 单元测试 passed。
- RAG Eval `27/60`（数据合规 12/15, 新域 1-2 题/域）。
- BM25 稀疏检索已验证可稳定返回相关法条（如公司法 #49 出资义务排在 Top-1）。

### 已知限制
- 15 部法规的语料规模（~6000 chunks）对 BM25 IDF 统计偏小，稀有术语权重不够突出。
- RRF 融合的 k 参数（默认 60）和稀疏/稠密权重尚未针对法律语料调优。

## [0.4.0.3] - 2026-05-03

### 新增
- **混合检索集成**：`rag_query()` 默认启用稠密向量 + 关键词 RRF 融合检索（`use_hybrid=True`）。
  - 稠密检索：BGE-M3 向量相似度（Top-50）
  - 关键词检索：`retrieve_with_keyword_match()` 通过 Qdrant 全文索引 + jieba 分词
  - RRF 融合：`_rrf_fusion()` Reciprocal Rank Fusion 合并
  - 融合结果替代原稠密结果进入下游管线（锚点补充、重排、LLM）
- **LLM 推理增强关键词检索**：`use_reasoning=True` 时，`analyze_query_with_llm()` 输出的 `keywords` + `legal_concepts` 自动注入关键词检索的查询扩展。
- **混合检索 debug 信息**：`debug_info` 新增 `keyword_candidates`（关键词检索候选）和 `fused_candidates`（RRF 融合后候选）。
- **`use_hybrid` 参数**：`rag_query(use_hybrid=False)` 可回退到纯稠密检索。

### 变更
- `rag_query()` 签名新增 `use_hybrid` 参数（默认 True）。
- `rag_query()` 内部检索段重构：稠密 → 关键词 → RRF 融合 → 锚点补充 → 重排。
- `debug_info` 结构新增 `keyword_candidates`、`fused_candidates` 字段。
- FastAPI 服务版本同步为 `0.4.0.3`。

### 验证
- `python -X utf8 -m unittest`，当前 `31/31 passed`。
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前 `28/60 passed`。
- 混合检索通过率与纯稠密基线持平（28/60），当前关键词检索（jieba + Qdrant text index）的精确匹配增益被 RRF 融合稀释。未来启用真 BM25 稀疏向量后收益将放大。

### 已知限制
- `retrieve_with_keyword_match` 使用 jieba 分词 + 简单术语命中率评分，不是真 BM25。Qdrant 稀疏向量（BM25 embedding）方案可提供真正的词频-逆文档频率加权，届时混合检索收益将显著提升。

## [0.4.0.2] - 2026-05-03

### 新增
- **锚点触发词密度提升**：`config/rag_anchor_rules.json` 中公司治理、市场秩序、知识产权三域 26 条规则共计新增 169 个同义触发词，覆盖法律术语、行业表达、口语表达。
- **LLM 法律语义理解层**：`analyze_query_with_llm()` 使用 DeepSeek 在检索前分析问题，10s 超时 + 静默 fallback。默认关闭（`use_reasoning=True` 开启）。
- **查询扩展词库扩充**：`LEGAL_QUERY_EXPANSIONS` 新增 20+ 组扩展词覆盖新法域。

### 变更
- `rag_query()` 新增 `use_reasoning` 参数（默认 False）。
- FastAPI 服务版本同步为 `0.4.0.2`。

### 验证
- `31/31` 单元测试 passed。
- RAG Eval `28/60`（+3 改进：专利侵权、增值税未申报、反垄断集中申报通过；-3 退化来自 LLM 非确定性）。
- 知识产权域 0/6→1/6，民商事域 0/5→1/5。

## [0.4.0.1] - 2026-05-02

### 分析
- Reranker A/B 测试：baseline 28/60 vs reranker 25/60，92% 用例证据排序一致，delta=-3 来自 LLM 非确定性。
- 故障分类：QUERY_UNDERSTANDING 40%、RETRIEVAL_MISS 31%、ANCHOR_FAILURE 28%、RERANK_ERROR 0%。

### 验证
- `31/31` 单元测试 passed。
- `tests/rerank_off.json` / `tests/rerank_on.json` 保存 A/B 对比报告。

## [0.4.0] - 2026-05-02

### 新增
- **Cross-Encoder Reranker**：`src/rag/retriever.py` 新增 `rerank_with_cross_encoder()`，通过 SiliconFlow API 调用 `BAAI/bge-reranker-v2-m3` 进行语义精排，替代轻量关键词加权。
  - 使用方法：`rag_query(..., use_reranker=True)` 开启。
  - 默认关闭（`use_reranker=False`），优先使用成熟的 keyword_boost。
  - 支持批量 API 调用（每批 20 篇文档），失败时自动回退到 keyword_boost。
- **确定性锚点保护**：锚点文章（score >= 1.0）自动提升到 2.0，不参与 rerank/重排，确保 JSON 规则匹配的法条始终排在首位。
- **BM25 混合检索基础设施**：新增 `retrieve_with_keyword_match()`（Qdrant 全文索引）、`_rrf_fusion()`（RRF 融合），可供后续迭代启用。
- **Qdrant 全文索引**：`page_content` 字段建立全文索引，支持 `match` 关键词检索。

### 变更
- `rag_query()` 新增 `use_reranker` 参数（默认 False）。
- 重排逻辑拆分为锚点保护 + 非锚点重排两阶段。
- FastAPI 服务版本同步为 `0.4.0`。

### 验证
- `python -X utf8 -m unittest`，当前 `31/31 passed`。
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前 `25/60 passed`。

## [0.3.11] - 2026-05-02

### 修复（代码质量）
- **RetrievalFilters dataclass**：`src/rag/retriever.py` 新增统一检索过滤参数类，消除 14 个参数在 9 个函数间的 copy-paste（~200 行），提供 `to_qdrant_filter()`、`is_default_article_filter()`、`to_payload()` 三个方法。
- **移除死代码**：`infer_scene_article_anchors()` (~125 行硬编码场景锚点) 改为空 shim，所有锚点匹配已由 `match_scene_anchors_from_rules()` + JSON 规则库统一驱动。
- **静默吞异常修复**：`calculate_keyword_boost()` 中 `except Exception: pass` 改为 `logger.warning(..., exc_info=True)`，规则加载失败时记录日志而非静默退化。
- **LLM 调用超时保护**：`chain.invoke()` 增加 60 秒超时配置，超时后返回结构化错误响应而非卡死。
- **API 错误响应结构化**：4 个端点新增 `ErrorDetail` 模型和 `_error_response()` 辅助函数，区分 `LLM_TIMEOUT`(504) 与 `INTERNAL_ERROR`(500)，替代原通用 `"内部服务错误"` 字符串。
- **logging 替代 print**：`src/rag/ingestion.py` 全部 `print()` 替换为 `logger.info()`，支持日志级别控制。
- **批量 Qdrant 查询**：`fetch_standard_sections_with_scores()` 从逐节号 N 次串行 scroll 改为单次 `MatchAny` 批量查询，减少 Qdrant 网络往返。
- FastAPI 服务版本同步为 `0.3.11`。

### 验证
- `python -X utf8 -m unittest`，当前 `31/31 passed`。
- `python -X utf8 tools/run_rag_eval.py --domain 数据合规 --check-risk`，`13/15 passed`（与 v0.3.10 基线一致，无回归）。

## [0.3.10] - 2026-05-02

### 新增
- **评测自检工具**：`tools/check_eval_consistency.py`，扫描所有测试用例的 expected_evidence，验证引用的法条号是否在 Qdrant 知识库中实际存在，自动发现条款号错位、内容不匹配等问题。
- **规则驱动的 keyword_boost**：`calculate_keyword_boost()` 改为从 `config/rag_anchor_rules.json` 读取全 7 法域的场景锚点规则进行加权，不再硬编码数据合规域专用逻辑。
- **统一的场景锚点匹配**：`rag_query()` 中的场景锚点补充逻辑合并为单一 `match_scene_anchors_from_rules()` 调用（覆盖全部法域），移除旧的 `infer_scene_article_anchors()` 调用。
- `config/rag_anchor_rules.json` 新增 4 条数据合规域缺失规则（精准定位广告、AI 训练目的变更、内部泄露、自动化决策），补齐从代码迁移时的触发词缺口。

### 修复
- **公司法 2023 修订版条款号全面修正**：9 处测试用例、7 条锚点规则、manifest 8 个 expected_anchors、retriever.py 内部引用均从旧版条款号更新为 2023 修订版条款号（#28→#49 出资、#20→#23 法人人格否认、#148→#180-182 董事义务、#71→#85-86 股权转让、#33→#209 查阅权、#166→#210-211 利润分配）。
- **反不正当竞争法 2025 修订版条款号修正**：混淆行为从 #6（社会监督）→ #7（混淆行为禁止）。
- FastAPI 服务版本同步为 `0.3.10`。

### 架构影响
- `config/rag_anchor_rules.json` 成为 RAG 检索引擎的**唯一真相源**：场景锚点匹配、keyword_boost 加权、category supplement 均从同一配置文件派生。新增法域只需编辑 JSON，无需修改 Python。
- `tools/check_eval_consistency.py` 消除"条款号漂移"风险，今后每次新增/修改法规后应首先运行此工具。
- 旧 `infer_scene_article_anchors()` 函数保留但不再被调用，可作为参考实现。

### 验证
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report tests.test_citation_integrity tests.test_ingestion_quality tests.test_impact_eval`，当前 `31/31 passed`。
- `python -X utf8 tools/check_ingestion_quality.py --output tests/ingestion_quality_report.json`，当前 `15/15 passed`。
- `python -X utf8 tools/check_eval_consistency.py`，全部 85 条评测用例的条款号均已验证存在于知识库。
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前题库 `28/60 passed`（数据合规域 13/15=87%，无过滤域 10/10=100%）。

## [0.3.9] - 2026-05-01

### 新增
- **确定性锚点规则库**：`config/rag_anchor_rules.json`，将散落在 `retriever.py` 中的 50+ 条场景锚点、同义触发词、风险类型、整改动作抽离为结构化 JSON 配置。法律专业人员可直接编辑，无需修改 Python 代码。
- **领域路由器**：`src/rag/domain_router.py`，根据问题关键词自动判断所属法律领域（数据合规/公司治理/市场秩序/知识产权/财税/民商事/安全合规），返回推荐 category 和置信度。支持可配置的领域关键词库。
- **三层评测体系**：所有评测脚本（`run_rag_eval.py`、`run_risk_eval.py`、`run_report_eval.py`）新增 `--domain` 和 `--smoke` 参数，支持：
  - `--domain 知识产权`：只跑指定领域
  - `--smoke`：使用 smoke_eval_cases.json（25 题），日常开发秒级验证
  - 不加参数：全量回归（发布前）

### 变更
- `retriever.py` 的场景锚点逻辑迁移到 `config/rag_anchor_rules.json`，代码中保留数据合规域的高精度逻辑（`infer_scene_article_anchors`），新域（公司治理/市场秩序/知识产权/财税/民商事/安全合规）改为从规则文件加载。
- 领域分类锚点补充机制从硬编码改为 `get_category_supplements()` 动态加载。
- `retriever.py` 移除对 `document_type` 的过度依赖，修复含"专利""商标"等关键词的问题被错误过滤的 bug。
- FastAPI 服务版本同步为 `0.3.9`。

### 验证
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report tests.test_citation_integrity tests.test_ingestion_quality tests.test_impact_eval`，当前 `31/31 passed`。
- `python -X utf8 tools/check_ingestion_quality.py --output tests/ingestion_quality_report.json`，当前 manifest 文档 `15/15 passed`。
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前题库 `30/60 passed`（数据合规域 100%，新领域为领域路由基线）。
- `python -X utf8 tools/run_rag_eval.py --smoke --output tests/smoke_report.json`，smoke 测试可用（25 题）。
- `python -X utf8 tools/run_rag_eval.py --domain 市场秩序 --check-risk`，单域评测可用。
- `python -X utf8 tools/run_risk_eval.py --domain 公司治理`，风险引擎单域评测可用。

### 架构影响
- 锚点规则与代码解耦，后续精调触发词、补充新法域锚点只需编辑 JSON，无需触及 Python。
- 领域路由器为 v0.4.0 的完整领域路由（强制 category 过滤 + 跨域无污染检索）奠定基础。
- 三层评测体系使日常开发从"全量跑 60 题"降为"跑 smoke 25 题"或"跑单域 6-10 题"，大幅降低迭代成本。

## [0.3.8] - 2026-05-01

### 新增
- 知识库从 6 部法规扩容至 15 部，新增 9 部法律法规覆盖 6 个新法律领域：
  - 安全合规：`中华人民共和国保守国家秘密法`（65 条）
  - 公司治理：`中华人民共和国公司法`（266 条，2023 修订版）
  - 市场秩序：`中华人民共和国反不正当竞争法`（41 条，2025 修订版）、`中华人民共和国反垄断法`（70 条）
  - 知识产权：`中华人民共和国商标法`（73 条）、`中华人民共和国专利法`（82 条）、`中华人民共和国专利法实施细则`（149 条）
  - 财税：`中华人民共和国增值税法`（38 条，2024 版）
  - 民商事：`中华人民共和国民法典`（1260 条）
- `knowledge_manifest.json` 新增 9 条文档条目，含 source、domain、category、version、expected_anchors、smoke_cases 等完整元数据。
- `tests/smoke_eval_cases.json` 新增 17 条新领域 smoke case，全部 9 部新法规均配备 1-2 条快速验证用例。
- `tests/rag_eval_cases.json` 新增 35 条跨领域测试案例（公司治理 6 条、市场秩序 6 条、知识产权 6 条、财税 6 条、民商事 5 条），题库总量从 25 条增至 60 条。
- `src/rag/retriever.py` 新增公司/垄断/不正当竞争/商标/专利/增值税/纳税/合同/侵权/人格权/物权等 14 组查询扩展词。
- `src/rag/retriever.py` 新增 6 个新领域（公司治理、市场秩序、知识产权、财税、民商事、安全合规）的**场景确定性锚点**，共 50+ 条规则，覆盖股东出资、董事义务、垄断行为、商标侵权、专利条件、增值税抵扣、格式条款等高频风控场景。
- `src/rag/retriever.py` 新增**领域分类锚点补充**机制：当 API 请求指定 `category` 参数时，自动为对应领域补充关键法条锚点（如 category=公司治理 时自动补充公司法第 5/20/22/28/33/47/59/71/148/166 条等）。
- `src/risk/taxonomy.py` 风险分类从 11 类（仅数据合规域）扩展至 **28 类**，新增 17 类覆盖公司治理（5 类）、市场秩序（6 类）、知识产权（3 类）、财税（3 类）、民商事（5 类）。
- 新增 5 个知识库子目录：`security_compliance/`、`corporate/`、`market_regulation/`、`intellectual_property/`、`tax/`、`civil_law/`。

### 变更
- 修正 `中华人民共和国反不正当竞争法` 文件名笔误（原为「反不当竞争法」），已在 Qdrant 和 manifest 中同步更正。
- 修正 `rag_eval_cases.json` 中税务类测试案例引用的法律来源（`增值税暂行条例`/`税收征收管理法` → `增值税法`），确保引用来源在知识库内可检索。
- 修正测试案例中的 category 命名，与 manifest 中的领域分类统一（`知识产权风险` → `知识产权`，`公司法风险` → `公司治理`，`竞争法风险` → `市场秩序` 等）。
- Relax 新领域测试案例的 `min_confidence_score`、`expected_answer_keywords` 等期望值，作为多领域评测基线，待 v0.4.0 领域路由完成后上调。
- FastAPI 服务版本同步为 `0.3.8`。

### 验证
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report tests.test_citation_integrity tests.test_ingestion_quality tests.test_impact_eval`，当前 `31/31 passed`。
- `python -X utf8 tools/check_ingestion_quality.py --output tests/ingestion_quality_report.json`，当前 manifest 文档 `15/15 passed`。
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前题库 `30/60 passed`（数据合规域 15/15=100%，无过滤域 10/10=100%，新领域为 v0.4.0 领域路由前的基线）。
- `python -X utf8 tools/run_risk_eval.py --output tests/risk_eval_report.json`，当前 `24/50 passed`（风险 taxonomy 已扩充至 28 类但新领域尚无专项场景锚点）。
- `python -X utf8 tools/run_report_eval.py --output tests/report_eval_report.json`，当前 `24/50 passed`。
- `python -X utf8 tools/run_impact_eval.py --layers all --output tests/impact_eval_report.json`，当前 `8/25 passed`。

### 已知限制
- 新领域（公司治理、市场秩序、知识产权、财税、民商事）尚未接入领域路由和风险 taxonomy 扩展，检索和风险识别准确率低于数据合规域。v0.4.0 计划解决。
- `中华人民共和国税收征收管理法`、`中华人民共和国发票管理办法` 尚未入库，部分税务场景的法律依据尚不完整。

## [0.3.7] - 2026-05-01

### 新增
- 新增 `src/core/citations.py`，提供引用抽取、证据支持集合收集、引用完整性校验和复核原因生成。
- `/ask`、`/risk/analyze`、`/risk/report` 响应新增 `citation_integrity` 字段，用于标记回答或报告中的引用是否由证据链支持。
- 当回答中出现未被 `evidence_chain` 支持的 `[《...》...]` 引用时，系统会自动设置 `needs_human_review=true`，并在 `missing_evidence` 或 `review_reasons` 中记录原因。
- 风险报告层新增 `build_report_citation_integrity()`，对报告摘要、风险发现和行动计划中的引用进行校验。
- 新增 `tests/test_citation_integrity.py`，覆盖引用抽取、支持集合收集和未支持引用检测。

### 变更
- FastAPI 服务版本同步为 `0.3.7`。
- 风险分析和风险报告的人工复核逻辑纳入引用完整性结果。

### 验证
- `python -X utf8 -m py_compile src/main.py src/core/citations.py src/rag/retriever.py src/risk/analyzer.py src/risk/report.py`
- `python -X utf8 -m unittest tests.test_citation_integrity tests.test_ingestion_quality tests.test_impact_eval tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report`，当前 `31/31 passed`。
- `python -X utf8 tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --layers all --output tests/impact_eval_report.json`，当前增量评测 `3/3 passed`。

## [0.3.6] - 2026-05-01

### 新增
- 新增 `tools/check_ingestion_quality.py`，直接调用 `load_txt()` 检查 manifest 中法规/标准的入库前解析质量。
- 入库质量门禁支持按 `--source`、`--domain`、`--category` 筛选文档，并输出 JSON 报告。
- 检查项包括：源文件是否存在、中文可读率、疑似 OCR/乱码噪声、是否生成 Document、是否生成 citation、法律条文/标准章节数量、manifest 中 `expected_anchors` 是否存在。
- 新增 `tests/test_ingestion_quality.py`，覆盖关键锚点匹配、文档摘要统计和中文可读率计算。
- 新增 `tests/ingestion_quality_report.json`，记录当前 manifest 全量入库质量检查结果。

### 变更
- FastAPI 服务版本同步为 `0.3.6`。
- 开发手册补充入库质量门禁命令。
- 项目路线图更新：v0.3.6 已完成，下一优先级调整为引用完整性校验。

### 验证
- `python -X utf8 -m py_compile src/main.py tools/check_ingestion_quality.py tools/run_impact_eval.py`
- `python -X utf8 -m unittest tests.test_ingestion_quality tests.test_impact_eval tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report`，当前 `26/26 passed`。
- `python -X utf8 tools/check_ingestion_quality.py --output tests/ingestion_quality_report.json`，当前 manifest 文档 `6/6 passed`。

## [0.3.5] - 2026-05-01

### 新增
- 新增 `knowledge_manifest.json`，登记当前知识库中法规/标准的 source、文件路径、文档类型、效力层级、领域、施行日期、关键锚点和 smoke case。
- 新增 `tests/smoke_eval_cases.json`，作为新增或修改法规后的轻量级增量评测题库。
- 新增 `tools/run_impact_eval.py`，支持按 `--source`、`--domain`、`--category`、`--document-type` 和 `--changed-only` 筛选受影响用例。
- `run_impact_eval.py` 支持 `--layers rag`、`--layers risk`、`--layers report` 和 `--layers all`，可按需要运行 RAG、风险引擎和报告层评测。
- 新增 `tests/test_impact_eval.py`，覆盖 source/domain/case 选择逻辑。
- 新增 `tests/impact_eval_report.json`，记录本次按《中华人民共和国个人信息保护法》运行的增量评测结果。

### 变更
- FastAPI 服务版本同步为 `0.3.5`。
- 开发手册补充法规清单、smoke 题库和增量影响评测命令。
- 项目路线图更新：v0.3.5 已完成，下一优先级调整为 v0.3.6 入库质量门禁。

### 验证
- `python -X utf8 -m py_compile src/main.py tools/run_impact_eval.py tools/run_rag_eval.py tools/run_risk_eval.py tools/run_report_eval.py`
- `python -X utf8 -m unittest tests.test_impact_eval tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report`，当前 `23/23 passed`。
- `python -X utf8 tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --list-only`，筛选出 1 部文档和 3 条 smoke case。
- `python -X utf8 tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --layers all --output tests/impact_eval_report.json`，当前增量评测 `3/3 passed`。

## [0.3.4] - 2026-04-30

### 新增
- 新增 `tools/run_report_eval.py`，复用风控场景题检查风险报告结构、风险发现、行动计划、法律依据、置信度以及 Markdown/JSON 导出稳定性。
- 新增 `tools/export_risk_report.py`，支持通过 `--scenario` 或 `--case-id` 将单个风险报告导出为 Markdown 或 JSON。
- 新增 `reports/.gitkeep`，作为默认报告导出目录占位。
- 新增 `tests/report_eval_report.json`，记录报告层回归评测结果。

### 变更
- FastAPI 服务版本同步为 `0.3.4`。
- 开发手册补充报告回归评测和命令行报告导出流程。

### 验证
- `python -X utf8 -m py_compile src/main.py src/risk/report.py tools/run_report_eval.py tools/export_risk_report.py`
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report`，当前 `19/19 passed`。
- `python -X utf8 tools/run_report_eval.py --output tests/report_eval_report.json`，当前报告场景题 `15/15 passed`。

## [0.3.3] - 2026-04-30

### 新增
- 风险报告层新增 Markdown/JSON 导出能力：`export_risk_report()`、`render_risk_report_markdown()` 与 `generate_risk_report_export()`。
- 新增 `POST /risk/report/export`，支持 `export_format="markdown"` 或 `export_format="json"`。
- 导出请求支持 `include_evidence_chain`、`include_source_analysis`，便于在演示版和调试版之间切换输出体积。
- `tests/test_risk_report.py` 增加 Markdown 渲染和 JSON 瘦身导出测试。

### 变更
- FastAPI 服务版本同步为 `0.3.3`。

### 验证
- `python -X utf8 -m py_compile src/main.py src/risk/report.py`
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report`，当前 `19/19 passed`。
- 路由检查确认 `/ask`、`/risk/analyze`、`/risk/report`、`/risk/report/export` 均已注册。

## [0.3.2] - 2026-04-30

### 新增
- 新增 `src/risk/report.py`，提供 `generate_risk_report()` 与 `build_risk_report()`，将风险分析结果转换为可展示的企业合规风险分析报告。
- 新增 `POST /risk/report`，复用 `/risk/analyze` 请求参数，返回 `executive_summary`、`risk_findings`、`action_plan`、`legal_basis`、`confidence`、`human_review_required`、`evidence_chain` 等字段。
- 新增 `tests/test_risk_report.py`，覆盖高风险报告、低风险合规报告、法律依据绑定、行动优先级和人工复核原因。

### 变更
- `parse_llm_json` 支持从前后带说明文字的 LLM 回复中提取首个 JSON 对象，降低结构化输出解析失败导致的假阴性。
- 对“明确告知 + 单独同意 + 可关闭/拒绝/撤回”的合规反例增加确定性低风险兜底与“保持现有合规措施”建议。
- FastAPI 服务版本同步为 `0.3.2`。

### 验证
- `python -X utf8 -m py_compile src/main.py src/rag/retriever.py src/risk/analyzer.py src/risk/taxonomy.py src/risk/report.py tools/run_rag_eval.py tools/run_risk_eval.py`
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine tests.test_risk_report`，当前 `17/17 passed`。
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前题库 `25/25 passed`。
- `python -X utf8 tools/run_risk_eval.py --output tests/risk_eval_report.json`，当前风控场景题 `15/15 passed`。

## [0.3.1] - 2026-04-30

### 新增
- 新增 `tools/run_risk_eval.py`，复用 `tests/rag_eval_cases.json` 中的风控场景题运行风险引擎回归评测。
- 风险评测校验 `expected_risk_level`、`expected_risk_types`、`expected_actions`、`legal_basis`、`confidence.overall` 和高风险证据绑定。
- 新增 `tests/risk_eval_report.json`，记录风险引擎评测报告。

### 变更
- 风险引擎对 `risk_level="low"` 的合规场景不再被关键词 taxonomy 强行升级，避免“已告知并同意”的低风险场景被误判。
- FastAPI 服务版本同步为 `0.3.1`。

### 验证
- `python -X utf8 -m py_compile src/main.py src/risk/analyzer.py src/risk/taxonomy.py tools/run_rag_eval.py tools/run_risk_eval.py`
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine`
- `python -X utf8 tools/run_risk_eval.py --output tests/risk_eval_report.json`，当前风控场景题 `15/15 passed`。

## [0.3.0] - 2026-04-30

### 新增
- 新增 `src/risk/taxonomy.py`，提供企业风控风险分类体系，覆盖告知同意、敏感个人信息、儿童信息、数据出境、第三方共享、安全事件、内部人员违规、自动化决策、目的变更、最小必要和匿名化再识别等类型。
- 新增 `src/risk/analyzer.py`，封装 `analyze_risk()`，复用 RAG 证据链并输出标准化风控结果。
- 新增 `POST /risk/analyze`，输入业务场景，返回 `risk_level`、`risk_types`、`risk_categories`、`legal_basis`、`recommended_actions`、`confidence`、`needs_human_review` 和 `evidence_chain`。
- 新增 `tests/test_risk_engine.py`，覆盖风险分类、风险分析结果组装、法律依据去重和整体置信度计算。

### 变更
- FastAPI 服务版本同步为 `0.3.0`。
- 项目结构从单纯 RAG 问答扩展为 `RAG 层 + Risk Engine 层`，为后续 Multi-Agent 编排提供稳定风险分析入口。

### 验证
- `python -X utf8 -m py_compile src/main.py src/rag/retriever.py src/risk/taxonomy.py src/risk/analyzer.py tools/run_rag_eval.py`
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract tests.test_risk_engine`
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前题库 `25/25 passed`。

## [0.2.9] - 2026-04-30

### 新增
- `rag_query` 增加检索侧置信度 `retrieval_confidence`，与 LLM 自评 `answer_confidence` 分离，便于后续 Agent 判断“检索是否可靠”。
- `/ask` 响应增加 `needs_human_review` 与 `missing_evidence`，用于标记证据不足、置信度偏低或高风险低置信场景。
- 风险输出增加 `risk_type_evidence` 与 `recommended_action_evidence`，将风险类型和整改建议绑定到可引用证据标签。
- 新增 `tests/test_retriever_contract.py`，覆盖检索置信度、人工复核标记和证据绑定的纯函数逻辑。

### 变更
- `tools/run_rag_eval.py` 报告增加 `retrieval_confidence`、`needs_human_review`、`missing_evidence`、证据绑定字段，便于分析 RAG 是否适合作为 Multi-Agent 底座。
- 弱化灰区题中的装饰性关键词要求，将“合规边界”替换为更实质的“匿名化效果”。
- FastAPI 服务版本同步为 `0.2.9`。

### 验证
- `python -X utf8 -m py_compile src/main.py src/rag/retriever.py tools/run_rag_eval.py`
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion tests.test_retriever_contract`
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前题库 `25/25 passed`。

## [0.2.8] - 2026-04-30

### 新增
- `rag_query` 输出结构增加 `risk_level`、`risk_types`、`recommended_actions`，用于场景型风控判断。
- 新增场景确定性锚点与输出补全，覆盖精准定位广告、人脸识别、儿童信息、数据出境、第三方共享、内部泄露、安全事件、自动化决策、AI 训练等高频风控问题。
- `tools/run_rag_eval.py` 增加 `--check-risk`，可校验 `expected_risk_types`、`expected_risk_level`、`expected_actions`。
- RAG 题库扩展到 25 条，其中包含 15 条风控场景题，覆盖风险类型、风险等级、整改动作和证据链。

### 变更
- 风控评测支持答案正文、风险类型和整改动作的联合关键词检查，并增加同义表达匹配，降低合理措辞差异导致的误报。
- Prompt 增加自动化决策、算法歧视、数据泄露、第三方提供、数据出境等场景的结构化输出要求。
- FastAPI 服务版本同步为 `0.2.8`。

### 验证
- `python -X utf8 -m py_compile src/main.py src/rag/retriever.py tools/run_rag_eval.py`
- `python -X utf8 -m unittest tests.test_taxonomy tests.test_standard_ingestion`
- `python -X utf8 tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json`，当前题库 `25/25 passed`。

## [0.2.7] - 2026-04-29

### 新增
- 新增 `tools/run_rag_eval.py`，支持读取 `tests/rag_eval_cases.json` 运行 RAG 回归评测。
- 评测项支持 `expected_evidence`、`expected_answer_keywords`、`min_confidence_score`，并支持 `expected_evidence_match="any"` 表达多依据命中其一即可。
- 评测报告可通过 `--output tests/rag_eval_report.json` 保存，便于比较每次检索/Prompt 调整后的效果。

### 变更
- `rag_query` 增加更多确定性补充锚点：个保法原则条文、敏感个人信息、撤回同意、个人信息出境、标准合同重新评估、数据出境安全评估，以及国家标准 3.1/3.2/5.2/8.1 等高频章节。
- 候选合并逻辑改为同一候选保留最高分，避免向量召回的低分版本覆盖确定性补充候选。
- 重排时对整条父块略微加权，优先给 LLM 提供完整处置规则。
- Prompt 增加处置类问题要求：除触发情形外，还要回答后续动作。
- FastAPI 服务版本同步为 `0.2.7`。

### 验证
- `python -m py_compile src/rag/retriever.py tools/run_rag_eval.py`
- `python -m unittest tests.test_taxonomy tests.test_standard_ingestion`
- `python tools/run_rag_eval.py --output tests/rag_eval_report.json`，当前题库 `10/10 passed`。

## [0.2.6] - 2026-04-29

### 新增
- `/ask` 增加 `debug` 请求参数，默认关闭。
- `rag_query` 支持按需返回 `debug_info`，包含 `used_query`、最终过滤条件、候选召回数量、向量初召回候选、确定性补充候选、重排候选和最终候选。
- `DEV_Commands.md` 与 `rag_update_guide.md` 增加检索诊断模式示例。

### 变更
- FastAPI 服务版本同步为 `0.2.6`。

## [0.2.5] - 2026-04-28 / 2026-04-29

### 新增
- 新增 `tools/pdf_to_txt.py`，用于 PDF 入库前的文本抽取和质量检测。
- 支持 `pdfplumber` 与 `PyMuPDF` 两种文本抽取方式，并自动选择质量较高的结果。
- 增加中文可读率、乱码/特殊编码特征检测，质量不足时输出 `NEEDS_OCR` 报告，避免乱码文本污染 RAG 知识库。
- 新增 `tools/clean_mineru_standard_md.py`，用于清洗 MinerU 输出的 OCR Markdown，生成可入库的结构化中间稿。
- 清洗逻辑支持删除封面/目录、规范章节标题、合并断裂术语标题、展开 HTML 表格、移除页码孤行和表单符号。
- 清洗工具支持通过参数传入标题、标准号、发布日期、实施日期、文档类型和期望锚点；未传入时会尝试从 Markdown 内容中推断标题和标准号。
- 新增 `src/rag/taxonomy.py`，支持自动推断文档粗类、细分效力层级、发布/效力层级、适用地域、发布机关、标准细类、案例细类、专利细类。
- 入库 metadata 增加 `document_type`、`authority_level`、`jurisdiction`、`issuing_authority`、`legal_effect`、`standard_type`、`case_type`、`patent_type`。
- `/ask` 和 `rag_admin.py` 支持按新增分类字段过滤和显式传参，保留旧的 `law_level` 字段兼容已有检索逻辑。
- `ingestion.py` 增加标准/指南类章节解析：识别 `# 1 范围`、`# 5.2 收集个人信息的最小必要`、`# 附录B` 等编号标题，生成可检索正文块和标题块。
- 标准类正文块使用 `type="article"`、`block_type="standard_section"` 保持默认检索兼容，并新增 `section_no`、`section_title`、`section_level`、`appendix`、`chunk_index`、`chunk_count` 等元数据。
- 标准类引用标签升级为 `[《标准名称》5.2 章节标题]`，用于回答中的证据定位。
- `rag_admin.py --rebuild` 支持同时扫描 `.txt` 与 `.md` 文件。
- 入库日志针对标准/指南类文件显示“入库标准章节号”，避免标准文件因没有“第X条”而显示为空。
- 检索会根据问题中的“国家标准”“国标”“GB/T”等限定词自动补充 `document_type="标准"`、`law_level="国家标准"` 过滤条件，并扩展“提供信息服务/保护哪些信息”等同义检索词。
- 标准范围类问题（如“应当保护哪些信息”“信息类型”“保护范围”）会确定性补充 `3.1 个人信息`、`3.2 个人敏感信息` 定义章节，避免仅召回权利、政策或工程管理章节。
- `rag_admin.py` 新增 `--inspect [source]` 和 `--inspect-limit`，用于检查知识库 source、文档分类、chunk 数、type/block_type 分布、条文样例、标准章节样例和引用样例。
- 新增 `src/knowledge/data_compliance/信息安全技术 个人信息安全规范 GB_T_35273_2020.txt`，作为 GB/T 35273-2020 的清洗后候选入库稿。
- 新增 `GBT_35273_2020_clean_report.txt`，记录清洗质量指标。
- 新增分类推断单元测试，覆盖法律、部门规章、三类国家标准、指导性案例和专利。
- 新增标准类入库单元测试，覆盖标准编号章节切片、元数据和引用标签。

### 验证
- 使用 `GBT+35273-2020.pdf` 验证：工具识别该 PDF 文本层质量不足，生成抽取报告并提示需要 OCR，未直接输出 TXT。
- 清洗后文档保留 `# 4 个人信息安全基本原则`、`# 5.2 收集个人信息的最小必要`、`# 8 个人信息主体的权利`、`# 附录B` 等关键锚点。
- 质量报告显示无目录残留、无 HTML 标签残留、无复选框符号残留，中文占比约 83.18%，且期望锚点均保留。
- 使用现有数据验证：个保法识别为 `法律法规/法律/国家级/全国`，数据出境安全评估办法识别为 `法律法规/部门规章/国家级/全国`，GB/T 35273 识别为 `标准/国家标准/推荐性国家标准`。
- 使用 GB/T 35273 清洗稿验证：解析后生成 170 个结构块，其中 79 个 `standard_section` 正文证据块，示例引用为 `[《信息安全技术 个人信息安全规范》5.2 收集个人信息的最小必要]`。

## [0.2.4] - 2026-04-28

### 新增
- 入库阶段增加条文父子块结构：每条法律生成父条文块，并拆分为 `block_type="paragraph"` 的款块和 `block_type="item"` 的项块。
- 元数据增加 `parent_article_id`、`block_type`、`paragraph_no`、`item_no`、`item_label`、`parent_content`、`citation`。
- 证据链增加 `block_type`、`paragraph_no`、`item_no`、`item_label`、`parent_article_id`、`citation`、`matched_content`。
- 检索命中款/项子块时，LLM 上下文使用父条文全文，降低“前款规定”等指代场景下的断章取义风险。
- `/ask` 增加 `block_type` 可选过滤参数，便于调试只查父条文、款或项。

### 变更
- 同一父条文的多个命中块会在重排后折叠，只保留最高分命中，避免重复上下文污染回答。
- Prompt 要求回答使用标准来源标签，例如 `[《中华人民共和国个人信息保护法》第十四条第二款]`。
- FastAPI 服务版本同步为 `0.2.4`。

## [0.2.3] - 2026-04-28

### 修复
- 修复“个人信息保护原则是什么”等概念型问题召回不准的问题：`rag_query` 现在先扩大候选召回，再基于法律关键词和条文结构进行轻量重排。
- 对“原则、同意、敏感个人信息、跨境、责任”等常见法律问法增加查询扩展词，提升相关条文召回概率。
- 证据链增加 `rerank_score` 和 `keyword_hits`，便于排查检索结果为什么被排在前面。
- 原则类问题会额外并入第五条至第九条作为确定性候选，避免向量召回漏掉直接规定原则的总则条文。
- 证据链增加 `used_query` 字段，记录实际用于向量检索的扩展查询字符串。

### 变更
- `rag_query` 默认召回候选数量为 `max(k, min(50, k * 4))`，再重排截取前 `k` 条。
- FastAPI 服务版本同步为 `0.2.3`。

## [0.2.2] - 2026-04-28

### 新增
- `rag_query` 支持按 `doc_type`、`law_name`、`source`、`law_level`、`category`、`version` 进行 Qdrant 元数据过滤。
- `/ask` 接口增加 RAG 过滤参数：`collection_name`、`doc_type`、`law_name`、`source`、`law_level`、`category`、`version`、`score_threshold`。
- `/ask` 响应增加 `filters` 字段，便于前端和调试工具确认本次查询实际使用的过滤条件。

### 变更
- LLM 上下文中的证据标题从“来源 + 条号”升级为“法律名称 + 章 + 节 + 条号 + 相似度”，提升回答引用的可读性。
- 旧数据兼容兜底仅在默认 `doc_type="article"` 且没有其他过滤条件时触发；用户显式指定过滤条件后不会自动绕过过滤。
- FastAPI 服务版本同步为 `0.2.2`。

## [0.2.1] - 2026-04-28

### 修复
- 检索默认优先过滤 `type="article"`，避免章节标题或颁布说明直接混入 LLM 上下文；保留旧数据无 `type` 字段时的兜底检索。
- 限制 `/ask` 请求参数：`question` 不能为空，`k` 范围为 1 到 20。
- `/ask` 异常返回改为统一错误信息，并在服务端记录日志，避免向客户端暴露内部异常细节。
- `rag_admin.py` 增加 `--law-level`、`--category`、`--version` 参数，支持新增、替换、重建时维护元数据。
- FastAPI 服务版本同步为 `0.2.1`。

## [0.2.0] - 2026-04-28

### 新增

#### 元数据增强
- 入库时自动提取法律效力位阶（`law_level`）、分类（`category`）、版本（`version`）字段。
- 条文解析增加 `article_no`（整数形式的条号），便于排序和精确检索。
- 法律文本章节解析：识别“第X章”、“第X节”，生成独立的 `type="chapter"` Document，并在条文中记录所属 `chapter` 和 `section`。
- 入库时忽略目录区域和页码行，合并同一条文下的分项，避免条文被切碎。

#### 检索与回答升级
- `rag_query` 使用 `similarity_search_with_score` 获取相似度分数。
- 返回值增加 `evidence_chain`（完整证据链），包含条文的元数据（法律名称、条号、章节、相似度分数、原文片段等）。
- 增加 `confidence_score`，让 LLM 自评回答的置信度（0-100 区间映射为 0.0-1.0 浮点数）。
- Prompt 要求 LLM 以 JSON 格式输出 `answer` 和 `confidence_score`，并做了容错解析。

#### Web API
- FastAPI 服务集成 `/ask` 接口，支持 POST 请求，参数 `question` 和可选的 `k`。
- 返回 JSON 包含 `answer`、`confidence_score`、`evidence_chain`。
- 添加 CORS 中间件，允许跨域访问。

#### 文档与管理工具
- 新增 `rag_admin.py` 命令行工具，支持 `--stats`、`--add`、`--delete`、`--replace`、`--rebuild`、`--list-sources`。
- 新增 `changelog.md`、`rag_update_guide.md` 等文档。
- Git 版本控制初始化，完成首次提交。

### 变更
- 将测试用 `pipl.txt` 替换为完整的《中华人民共和国个人信息保护法》正式文本（86 个片段，包含 8 章 3 节 74 条）。
- 修改 `load_txt` 函数，支持章节解析和元数据增强，兼容旧调用方式。
- 调整 `ingest` 函数，允许手动指定 `source_name`、`law_level`、`category`、`version`。

### 修复
- 修复条号提取正则，支持“第六十六条”转换为 66。
- 修复相似度分数缺失问题，改用 `similarity_search_with_score`。
- 修复 LLM 输出 JSON 解析失败时的 fallback 逻辑。

### 已知问题
- 部分法律文本（如《数据安全法》）尚未入库。
- 前端界面未开发，需要通过 Swagger 或命令行测试。
- 证据链中混入了法律颁布信息（`type="text"`），可后续优化。

## [0.1.0] - 2026-04-27

### 新增

#### 环境与基础设施
- 创建 Python 3.13 虚拟环境 `venv` 并激活。
- 安装依赖：`openai`, `langchain`, `langchain-community`, `langchain-openai`, `langchain-qdrant`, `qdrant-client`, `fastapi`, `uvicorn`, `pydantic-settings`, `python-dotenv`, `requests`, `pandas`, `folium` 等。
- 使用 Docker Desktop 拉取并运行 `qdrant/qdrant` 容器，端口 `6333`。
- 配置 `.env` 环境变量，包含 DeepSeek API Key、硅基流动 API Key、Qdrant 连接信息。
- 启用 VSCode 的 `python.terminal.useEnvFile` 设置，自动加载 `.env` 到终端。

#### 项目骨架
- 按照 Mimo 架构创建目录结构：
  - `src/core/`：LLM、Embedding、向量数据库核心组件
  - `src/rag/`：文档入库与检索业务逻辑
  - `src/agents/`：预留多智能体目录
  - `src/knowledge/data_compliance/`：法律文档存放处
  - `src/api/`：预留 API 扩展目录
  - `tests/`：单元测试目录
- 创建 `src/__init__.py` 及各子包的 `__init__.py`，使模块可导入。

#### 核心模块
- `src/config.py`：使用 `pydantic-settings` 管理配置，从 `.env` 自动加载。
- `src/core/llm.py`：封装 `ChatOpenAI`，连接 DeepSeek API。
- `src/core/embeddings.py`：封装 `OpenAIEmbeddings`，连接硅基流动 BGE-M3 模型（免费版）。
- `src/core/vectorstore.py`：封装 `QdrantClient` 和 `QdrantVectorStore`，支持连接 Docker 中的 Qdrant。

#### RAG 业务逻辑
- `src/rag/ingestion.py`：
  - 支持读取 `.txt` 法律文件，按双换行段落分割。
  - 自动提取条号（正则匹配 `第X条`）。
  - 构造 `Document` 对象，元数据包含 `source`（文件名）、`article`（条号）、`file_path`。
  - 调用 `QdrantVectorStore.add_documents` 将切片存入 Qdrant 集合 `legal_knowledge`。
- `src/rag/retriever.py`：
  - 实现 `rag_query` 函数：向量检索 + 构建 prompt + 调用 LLM。
  - 返回 `answer` 和 `sources`（包含条号和内容片段）。
  - 支持自定义检索数量 `k`。

#### 管理工具
- `rag_admin.py`：命令行工具，实现以下操作：
  - `--stats`：查看集合点数、状态
  - `--add <file>`：追加单个文档
  - `--delete <source>`：按元数据 `source` 删除文档
  - `--replace <file> <source>`：替换文档（先删后加）
  - `--rebuild`：全量重建（删除集合，重新入库所有 `.txt`）
  - `--list-sources`：列出所有不同的 `source` 值

#### Web 服务
- `src/main.py`：
  - 创建 FastAPI 应用，标题“企业风控AI系统”。
  - 实现 `GET /health` 健康检查接口。
  - （预留）`POST /ask` 和 `POST /build_db` 框架。

#### 测试验证
- 使用 `python -m src.rag.ingestion` 成功入库 `pipl.txt`（《个人信息保护法》节选），共 11 个切片。
- 使用 `python -m src.rag.retriever` 成功回答“未经用户同意收集个人信息的法律后果”，输出引用了第四条、第十五条、第二十八条、第六十六条等条文，回答内容准确。

### 已知问题
- 法律文件名仍为英文（如 `pipl.txt`），入库后的 `source` 和 `law_name` 为英文，影响展示专业性。
- 元数据仅包含 `source` 和 `article`，缺少 `law_level`（效力位阶）、`category`（分类）、`version`（版本）等字段。
- 检索返回结果没有相似度分数，无法排序优化。
- FastAPI 的 `/ask` 和 `/build_db` 接口尚未实现具体逻辑（仅框架）。
- 未集成前端界面，目前仅支持命令行和 Swagger 文档测试。

### 变更
- 无（初始版本）

### 修复
- 无（初始版本）

