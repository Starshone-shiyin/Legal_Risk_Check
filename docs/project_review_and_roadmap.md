# 项目审查与下一阶段开发路线

更新日期：2026-09-03（当前代码版本为 v0.5.4）

## 维护规则

本文件只保留项目阶段、当前工程基线、主要风险和下一步计划，不再逐条堆叠每个小版本。详细版本流水账以 `changelog.md` 为准，最终报告素材以 `docs/final_report_version_guide.md` 为准，历史长版路线图已归档到 `docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md`。

后续更新本文件时：

- 只在阶段状态、当前基线、风险判断或开放任务真实变化时更新。
- 小版本完成记录写入 `changelog.md`，不要继续扩写成本文件的大段历史。
- 已完成的小版本事项最多只在 roadmap 保留最近两个版本；超过两个版本的完成细节应从 roadmap 删除，以 `changelog.md`、专题文档和 `docs/final_report_version_guide.md` 为准。
- `## 推荐下一步` 只能写当前待办和最近一次下一步判断，不得堆放已完成版本流水账；完成后应在下一版本更新或删除。
- 若需要保留阶段性长说明，优先新增 `docs/archive/*snapshot*.md` 或专题文档，再在本文件放一行链接。
- 不把 gate、design、worksheet、dry-run 等治理产物写成 runtime 能力。

## 当前定位

本项目目标是建设 Harvey 风格的企业法律风控系统：以高质量法律 RAG 为基础，逐步支持企业行为、外部地缘政治和监管变化等风险信号，最终输出可追溯、可复核、可交付的法律风险报告。

当前阶段重点是 **RAG grounding quality、主链路稳定性与可评测性**。原则仍然是：不靠 hidden seed 打补丁，不通过为单个样本追加场景规则、改 eval case 或任意放宽 rerank 来掩盖证据质量问题；确需修改主链路时，必须能解释其通用性、边界和回归验证。

## 当前能力基线

- 知识库层：已入库 15 部法规/标准，覆盖数据合规、安全合规、公司治理、市场秩序、知识产权、财税、民商事等领域。
- RAG 层：支持 Dense/BM25 分层召回、稳定去重、确定性锚点、Cross-Encoder rerank、final evidence selector、证据链、检索置信度、debug trace 和人工复核标记。
- 风险引擎层：已形成 28 类风险 taxonomy，支持风险等级、风险类型、法律依据和整改动作输出。
- 报告层：支持结构化风险报告、Markdown/JSON 导出和报告层评测。
- 治理层：已形成 RAG Eval、Risk Eval、Report Eval、Smoke、scenario targeted eval、stability diagnostics、evidence diagnostics、manual review governance、retrieval input quality governance 和项目 health check。

## 阶段摘要

| 阶段 | 状态 | 当前结论 |
|---|---|---|
| v0.1.x-v0.3.x | 已完成 | 基础工程、法律文本结构化、风险引擎、报告导出和三层评测已建立。 |
| v0.4.0-v0.4.6.x | 已完成 | Harvey 风格分层召回、BM25/Cross-Encoder、scenario registry 和 targeted eval 基线已建立。 |
| v0.4.7.x-v0.4.8.x | 已完成离线治理 | Hidden seed 结构化、Evidence Coverage、Manual Review Workbench、Final Evidence Selection Policy 离线链路已形成；未把离线 policy 直接接入 runtime。 |
| v0.4.9.x-v0.4.12.x | 已完成诊断闭环 | retrieval input quality 指向 metadata/chunking；root cause 为普通法律 article/paragraph/item 入库路径缺 `chunk_index/chunk_count`。 |
| v0.4.13.x | 已完成源码补丁与 rebuild 规划 | `build_article_documents` 已补齐 deterministic `chunk_index/chunk_count`；生产 rebuild 前置设计、授权和 dry-run 链路完成。 |
| v0.4.14.x | 已完成生产重建与回归修复 | `legal_knowledge` 已重建，post-validation 和 smoke 通过；post-rebuild full eval 回归已通过 selector 收紧修复至 60/60。 |
| v0.4.15.x | 已完成 | 主链路稳定性与风险等级收口完成；检索层保持 `PASS=60`，风险等级从 55/60 修复到 59/60。剩余 `risk_unfair_competition_confusion_001` 属于法律事实强度/expected-level 复核债，不作为 runtime 缺陷继续硬修。 |
| v0.4.16.x | 已收口 | 前后端接入前的 API contract 稳定层已形成离线契约包；已固化核心接口路径、请求默认值、响应必需字段、统一错误结构、报告导出内容类型、OpenAPI schema 快照、离线 API example payload fixture、mock endpoint smoke contract、离线 API contract bundle、错误状态样例、API field catalog、API contract consistency checker 和系列 closeout/runbook。 |
| v0.4.17.x | 已收口 | RAG evidence independence / retrieval quality hardening 系列完成主链路确认；full eval 为 `59/60`，retrieval `PASS=60`，唯一剩余项为 expected-level/fact-strength 复核，不作为 runtime 缺陷继续硬修。 |
| v0.4.18.x | 已收口 | RAG 收口后进入产品化后端准备；已建立 legal corpus integrity baseline，并形成 fixture-backed `/product/*` 接口、字段目录、状态目录、数据源/repository boundary 和后端 closeout runbook。 |
| v0.4.19.x | 已完成 | 外部风险与任务流底座已形成，RAG 已完成模块拆分、复杂问题回答契约和后端桥接。 |
| v0.5.0 | 已完成 | 概念检索、附表证据边界、用户材料隔离、引用覆盖及仅检索消融基线已接入。 |
| v0.5.1 | 已完成 | ESG、受控联网补证、可视化 Skill 编排与冻结集实验材料已接入；网页证据、用户配置与法律法源的边界已明确。 |
| v0.5.2 | 已完成 | 完成多协议 LLM 运行时、期货供应链情报、受控 C0-C6 消融和改写鲁棒性材料；比赛演示快照已固化，情报配置变化保持 fail-closed，规则增益与法律结论正确率严格区分。 |
| v0.5.3 | 已完成 | 完成材料接入、证据优先路由与门禁、内部风险任务流、外部风险关系同步和前端后端连接收口；未改变知识库原文或评测锚点。 |
| v0.5.4 | RAG 候选快照 | 单独固化敏感个人信息/个人信息出境的 Anchor 触发与连续证据窗口，便于回退和与 v0.5.3 对比；尚未通过 full eval，不作为生产基线。 |

## 当前治理基线

- 当前代码版本：v0.5.4。
- v0.4.16.12 已收口 API contract stability 系列，离线契约包可供后续 mock service / UI handoff 使用。
- v0.4.17.1 只读 v0.4.15.26 RAG eval 保存报告建立 evidence independence baseline：`59/60` passed，retrieval `PASS=60`，`high_dependency_ratio=0.8`。
- v0.4.17.2 只读 evidence independence baseline 生成 targeted rerun packet：17 个候选 case，覆盖 base retrieval lexical triage、output rule dependency、failed/expected-level review 和 pure LLM control。
- v0.4.17.3 按 packet 实跑 targeted repeat：pass counts `[16, 16, 16]`，retrieval stage 每轮 `PASS=17`，`unstable_cases=0`，固定失败为 `risk_unfair_competition_confusion_001`。
- v0.4.17.4 只读 v0.4.17.3 repeat 报告生成 expected-level review packet：固定失败分类为 `expected_level_fact_strength_review`，并记录 legal reasoning 第6条与 expected evidence 第7条的元数据复核提醒。
- v0.4.17.5 联网核验并固化法律文本版本快照：现行 2025 修订《反不正当竞争法》混淆行为为第七条，2019 修正文本混淆行为为第六条；本地证据链使用第七条合理。
- v0.4.17.6 人工确认后仅修正 `risk_unfair_competition_confusion_001` 的 `legal_reasoning` 旧编号文字；`expected_risk_level` 与 `expected_evidence` 未改变。
- v0.4.17.7 运行当前 RAG full eval 收口确认：`59/60` passed，retrieval `PASS=60`，唯一失败仍为 `risk_unfair_competition_confusion_001` 的 expected-level/fact-strength 复核项。
- v0.4.18.1 建立 legal corpus integrity baseline：manifest 覆盖 15 份法规/标准，本地 `load_txt()` 生成 7177 个片段，`error_count=0`，`warning_count=0`。
- v0.4.18.2 新增产品设计简报，明确首页、外部风险、供应链地图、法律 RAG 工作台和企业生命周期风险概览的设计方向。
- v0.4.18.3 新增离线 product view model contract，定义 dashboard、legal workspace、market signals、supply-chain map 和 lifecycle risk 的数据骨架。
- v0.4.18.4 新增离线 product mock endpoint contract，将产品 view model 映射为 6 个 UI handoff endpoint contract，但未新增正式 API 路由。
- v0.4.18.5 将 6 个 `/product/*` endpoint 接入 FastAPI fixture-backed 后端分层；接口真实暴露，但数据仍来自离线样例，不调用 RAG/Qdrant/LLM 或外部数据源。
- v0.4.18.6 新增 product API field catalog，整理 `/product/*` query params、response envelope、meta 字段和 fixture-derived field paths。
- v0.4.18.7 新增 product API status/error catalog，明确成功态、空结果和产品错误码语义。
- v0.4.18.9 收口 product backend runbook，确认后端设计基本完成，可供 UI 原型对接 fixture-backed `/product/*`，真实 provider 仍需分版本接入。
- v0.4.19.0 开始外部风险与任务流底座：新增 `/external-risk/*` 后端接口、fixture-safe 外部风险上下文、行情/消息 provider 降级边界、外部事实到法律检索任务的 query plan、RAG 模块化拆分、复杂案例与开放问答 answer policy。
- v0.5.0 接入 RAG 运行质量与评测基线：法律概念映射、仅检索消融、附表独立证据块、用户材料/法律法源隔离和引用覆盖率信号均已可复核；尚未将本地消融运行产物写成正式效果结论。
- v0.5.1 接入 ESG、受控联网补证、固定节点 Skill 编排、指标重算和冻结集裁判材料；网页证据独立标注，用户 Skill 配置与运行状态不作为源码基线提交。
- v0.5.2 建立 C0-C6 单变量消融和人工改写鲁棒性材料；结果明确披露场景规则是冻结集主要增益来源，并新增多协议 LLM、期货供应链情报与按配置刷新、默认 fail-closed 的运行时边界。比赛提交额外固化 anchor、风险图谱/业务状态、manifest 状态和论文图件；这些是可复放演示资产，不替代生产核验。
- v0.5.3 将材料接入、图片事实观察、通用/外部风险/法律 RAG 路由、`/ask` 证据门禁、内部风险异步任务和外部风险关系同步接入现有后端；完整回归 `1670` 项、health check `583/583` 通过。该版本没有把运行状态、历史备份或知识库原文改动混入质量结论。
- v0.5.4 将一组待验证的 RAG Anchor 行为单独提交，覆盖轨迹/精准定位等敏感个人信息表述和个人信息出境条件的连续条文证据；完整回归 `1671` 项、health check `583/583` 通过，但尚未运行 full eval，不作为生产质量结论。
- 当前分支系列：v0.5 RAG quality runtime。
- 权威运行报告仍在 `tests/*.json`；`reports/` 仍是未来目录分组 scaffold，不是默认输出位置。
- `tools/run_rag_eval.py --compact-report` 仅是 opt-in 报告体积控制；默认 full report 不变。

## 当前主要风险

### 1. Roadmap 与报告继续膨胀

项目已经有大量 gate、design、dry-run、worksheet 和 saved report。后续应把小版本事实写入 `changelog.md`，roadmap 只记录阶段判断，避免路线图本身成为新的维护负担。

### 2. Anchor 仍可能掩盖基础召回弱点

历史诊断显示 base retrieval gap 与 anchor dependency 高度重叠。后续不能为了单个 case 继续加 anchor，应优先从入库质量、query lexical coverage、source/article identity、final evidence selector 可解释性入手。

### 3. Final evidence selector 已进入主链路，需要严控回归

v0.4.14.32-v0.4.14.34 的 selector 修复把 post-rebuild full eval 恢复到 60/60，但 selector 已是 runtime 行为。后续任何相关改动必须跑 targeted regression、full eval 或 repeat stability，不应只靠离线诊断判断。

### 4. 法规扩容不能早于质量基线

大量法律入库前，需要法规清单、metadata 登记、ingestion quality check、source/index integrity、impact eval 或 targeted smoke。否则法规越多，误召回、法域污染和冲突解释风险越高。

## 推荐下一步

### 当前建议：以现有主链路做受控产品联调

- 用固定的企业材料、外部信号和法律问题做前后端 smoke，确认上传、解析、证据门禁、人工复核和报告导出能串成一条可观察链路。
- 在不改变 RAG 证据边界的前提下补充人工标注的“引文是否支持结论、是否遗漏关键例外”评测，并记录标注分歧处理方式。
- 单独建立含发布日期与采集时间的时效性法规、监管和市场事实集；不将网页事实混入法条 Recall@K。
- 真实 provider 仍按单一来源逐项验证；新增 anchor 或知识库内容必须经过独立通用性审查和回归，不能用来掩盖基础质量问题。

## 失败处理规则

如果未来 compact/full eval 出现失败，先判断失败属于：

- retrieval/evidence-chain 回归；
- answer wording / keyword variance；
- risk taxonomy 或 recommended action 覆盖；
- 仅 compact 输出展示问题。

只有确认是通用主链路问题，才进入代码修复。

## 日常验证策略

### 文档或离线诊断工具

```powershell
.\venv\Scripts\python.exe -m py_compile tools\<tool>.py
.\venv\Scripts\python.exe -m unittest tests.test_<target>
.\venv\Scripts\python.exe tools\run_project_health_check.py --output tests\project_health_check_report.json --fail-on-error
```

### RAG 主链路或 eval 输出改动

```powershell
.\venv\Scripts\python.exe -m py_compile tools\run_rag_eval.py
.\venv\Scripts\python.exe -m unittest tests.test_rag_eval_diagnostics
.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\<versioned_report>.json --check-risk
```

大报告可额外使用 `--compact-report`，但深度 selector/debug 归因仍需 full report。

### 法规扩容前

建议流程：

1. 法规清单和 metadata 登记。
2. 单法规 ingestion quality check。
3. source/index integrity check。
4. impact eval 或 targeted smoke。
5. 通过后再合入 manifest。

## 暂不建议

- 为个别 hidden seed 新增 anchor。
- 直接修改 prompt、eval case 或 risk supplement 来补输出关键词。
- 把 design/gate/worksheet 继续拉成长链条。
- 把 AI suggestion、legacy prefill 或 pilot assist 当成 completed manual review records。
- 在没有 targeted smoke 的情况下大规模扩法规。
