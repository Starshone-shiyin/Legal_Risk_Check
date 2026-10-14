# Legal Functional Typing v0.4.7.2

## 定位

v0.4.7.2 是离线法律功能类型诊断层，不是检索、排序或生成策略改动。

本版本目标是为后续大量法律入库建立可治理的 `functional_type` 路线：先用通用文本线索和 metadata 生成候选功能类型，再用 audit 报告暴露未分类、高风险缺口和 definition-only 风险，最后由人工只复核高价值缺口。

## 边界

- 不接入 `rag_query` 主流程。
- 不修改 rerank。
- 不修改 prompt。
- 不新增 anchor。
- 不修改 risk supplement / term preservation 规则。
- 不修改 eval case。
- 不运行 full eval。

## 功能类型

配置文件：`config/legal_functional_types.json`

当前 taxonomy：

- `definition`：定义条款。
- `principle`：原则条款。
- `operative_rule`：义务、禁止、条件、合规措施等实体规则。
- `procedural`：申报、备案、评估、通知、审查、期限等程序要求。
- `liability`：责令改正、罚款、赔偿、处罚、刑责等法律责任。
- `rights_remedy`：查阅、复制、更正、删除、撤回同意、投诉举报等权利救济。
- `scope`：适用范围、主体范围、地域范围。
- `technical_standard`：标准、规范、指南类技术要求。
- `unrelated_or_contextual`：背景或边缘上下文。
- `unclassified`：暂无法稳定判断。

## 实现方式

`src/rag/legal_functional_typing.py` 提供只读、确定性的分类 API：

- `classify_legal_function(text, metadata)`
- `classify_evidence_function(evidence)`
- `has_operative_support(functional_types)`

分类优先级：

1. 如果 chunk/evidence 已有 `functional_type` metadata，则优先使用 metadata。
2. 如果 `document_type` 是标准或来源包含 GB 标识，则归为 `technical_standard`。
3. 否则按 `config/legal_functional_types.json` 的通用关键词和正则规则分类。
4. 仍无法判断时归为 `unclassified`。

这避免在代码里维护“某部法第几条等于某功能类型”的硬编码。

## Audit 工具

命令：

```powershell
.\venv\Scripts\python.exe tools\audit_legal_functional_typing.py `
  --manifest knowledge_manifest.json `
  --config config\legal_functional_types.json `
  --output tests\legal_functional_typing_report.json
```

输出：

- 全局 chunk 数、未分类比例、operative support 比例。
- `functional_type_summary`。
- `per_domain_summary`。
- 每部文档的功能类型分布、样本、复核原因。
- `manual_review_documents`。

## 当前结果

基于现有 `knowledge_manifest.json`：

- 文档数：15
- chunk 数：7177
- 进入复核文档：1
- 未分类 chunk：2064，比例 `0.288`
- operative support chunk：4571，比例 `0.637`
- 当前主要复核对象：`中华人民共和国增值税法`，原因是未分类比例 `0.5`，说明财税条款需要补充更贴近税法语言的功能类型线索。

## 与 Evidence Alignment Checker 的关系

`tools/check_evidence_alignment.py` 已改为复用 `src/rag/legal_functional_typing.py`，但仍只做离线诊断，不接入主流程。

后续 evidence alignment 的 definition-only、operative support coverage 等信号，应优先依赖 functional typing metadata 或通用文本分类器，而不是在 checker 内写死具体法条号。

## 后续方向

- 为财税、公司治理、知识产权等领域补充领域中性的 functional typing 线索。
- 在 ingestion 侧评估是否只写入 metadata 候选，不改变召回或排序。
- 将人工复核限制在高风险、未分类比例高、definition-only 或缺 operative support 的文档/条款上。
