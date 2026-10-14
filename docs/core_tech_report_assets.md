# 核心技术报告展示方案

本文档是比赛报告的图表与讲解底稿，强调“已实现并验证”的功能边界，不把规划能力写成现有能力。

## 1. 建议报告主线

1. **问题定义**：法律问答不能只追求语言流畅，还要回答可追溯、法源可核验、证据不足时主动降级。
2. **系统方法**：问题分析 -> 稠密/稀疏候选召回 -> 法律概念与场景锚点补充 -> 候选裁剪 -> Cross-Encoder 重排 -> 证据链构建 -> 受约束生成 -> 引用校验。
3. **可信机制**：法律法规证据与用户上传材料分层；本地法源支撑法律结论；外部实时事实仅作为背景信号，不直接替代法源。
4. **实验方法**：固定同一批问题、同一知识库和同一 `K`，比较四档检索配置，报告 Recall@K、MRR、nDCG、多来源覆盖率和延迟。
5. **边界与改进**：锚点对部分概念题有明显贡献；纯召回不足时输出证据缺口并建议人工复核；实时市场/监管数据需显示来源、时间和新鲜度。

## 2. 图表清单

| 编号 | 图表 | 展示重点 | 数据来源 |
|---|---|---|---|
| Fig.1 | 系统总体架构 | Web、API、RAG、Qdrant、LLM、外部风险模块边界 | `docs/diagrams/system_architecture.mmd` |
| Fig.2 | 法律文本入库流程 | 文本解析、条文切分、元数据、向量与稀疏索引 | `docs/diagrams/legal_ingestion.mmd` |
| Fig.3 | 检索与证据选择流程 | Dense/BM25 union、概念锚点、规则锚点、重排 | `docs/diagrams/retrieval_pipeline.mmd` |
| Fig.4 | 证据约束生成 | 证据链、缺口识别、回答生成、引用完整性 | `docs/diagrams/evidence_generation.mmd` |
| Fig.5 | 用户材料隔离 | 合同材料与本地法律法源分层显示 | `docs/diagrams/material_boundary.mmd` |
| Fig.6 | 消融实验 | 四档配置的证据指标与延迟 | `tests/rag_ablation_report.json`（Qdrant 可用后生成） |
| Fig.7 | 民法典覆盖与 Judge | 条文覆盖、专项回归和验收状态 | `tests/civil_code_eval_cases.json` 与现有 Judge 报告 |

## 3. 四档消融定义

| 配置 | 稠密 | BM25 | 概念扩展/锚点 | 规则锚点 | 复杂问题规划 | Cross-Encoder |
|---|---:|---:|---:|---:|---:|---:|
| M1_dense | 是 | 否 | 否 | 否 | 否 | 否 |
| M2_hybrid | 是 | 是 | 否 | 否 | 否 | 否 |
| M3_concept | 是 | 是 | 是 | 否 | 否 | 否 |
| M4_full | 是 | 是 | 是 | 是 | 是 | 是* |

`*` 复杂多问题会使用现有快速规划路径，按问题拆解结果组织证据，不应在报告中表述为每道题都经过 Cross-Encoder。

运行命令：

```text
venv\Scripts\python.exe tools\run_rag_ablation.py --cases tests\rag_eval_cases.json --output tests\rag_ablation_report.json
venv\Scripts\python.exe tools\judge_rag_ablation.py tests\rag_ablation_report.json --output tests\rag_ablation_judge_report.json
```

## 4. 评委展示时的口径

- `Evidence Recall@K` 衡量期望法源是否进入前 K 条证据，不等于回答准确率。
- 历史回归中的回答字段通过率和检索命中率应分开陈述，不能合并为“模型准确率”。
- 锚点依赖是已识别的系统边界：部分概念题依赖确定性法条锚点；因此实验必须保留 M1/M2/M3 作为对照。
- 外部事实模块必须展示来源、链接、采集时间、有效期和置信度；外部事实与本地法律条文分区展示。
- 未完成的实时消融、联网检索或未入库法规，不在报告中写成已验证结论。

## 5. 推荐答辩顺序

先演示普通法律概念题，再演示多选/多问题案例，最后演示上传合同材料后的“材料证据 + 法律法源”双栏引用。答辩追问时展示 `debug_info` 中的候选、锚点、重排模式、证据缺口和检索耗时。
