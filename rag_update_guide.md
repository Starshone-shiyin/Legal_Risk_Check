# RAG 知识库更新手册

## 使用示例

### 1. 添加文档，自动使用文件名作为 source

```bash
python rag_admin.py --add "src/knowledge/data_compliance/数据安全法.txt"
```

### 2. 添加文档，手动指定 source 名称

```bash
python rag_admin.py --add "src/knowledge/data_compliance/pipl.txt" --source "个人信息保护法"
```

### 3. 添加文档，并显式指定分类元数据

```bash
python rag_admin.py --add "src/knowledge/data_compliance/信息安全技术 个人信息安全规范 GB_T_35273_2020.txt" --document-type "标准" --law-level "国家标准" --standard-type "推荐性国家标准" --category "数据合规"
```

### 4. 删除某个 source

```bash
python rag_admin.py --delete "数据安全法"
```

### 5. 替换文档

先删除旧 source “个人信息保护法”，再入库新文件，新 source 自动取文件名：

```bash
python rag_admin.py --replace "src/knowledge/data_compliance/pipl.txt" "个人信息保护法"
```

### 6. 替换文档，同时指定新 source

```bash
python rag_admin.py --replace "src/knowledge/data_compliance/pipl.txt" "个人信息保护法" --new-source "个人信息保护法(2025版)"
```

### 7. 全量重建知识库

会扫描 `src/knowledge/data_compliance/` 下的 `.txt` 和 `.md` 文件。

```bash
python rag_admin.py --rebuild
```

### 8. 查看所有 source

```bash
python rag_admin.py --list-sources
```

### 9. 检查知识库入库结构

查看全库概览：

```bash
python rag_admin.py --inspect
```

检查单个 source：

```bash
python rag_admin.py --inspect "信息安全技术 个人信息安全规范 GB_T_35273_2020"
```

控制样例输出数量：

```bash
python rag_admin.py --inspect --inspect-limit 5
```

`--inspect` 会输出 source、文档分类、chunk 总数、`type`/`block_type` 分布、条文样例、标准章节样例和引用样例。重建或追加新文档后，建议先运行该命令确认入库结构符合预期。

## 检索诊断模式

当回答质量不理想时，可以在 `/ask` 请求中加入 `debug=true`：

```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"根据国家标准，提供信息服务一方应当保护哪些信息？\",\"k\":3,\"debug\":true}"
```

响应会额外返回 `debug_info`，包括：

- `used_query`：实际用于向量检索的扩展查询
- `filters`：自动推断和用户显式传入后的最终过滤条件
- `vector_candidates`：向量初召回候选摘要
- `deterministic_supplements`：确定性补充候选，例如原则类条文或标准定义章节
- `reranked_candidates`：重排后的候选摘要
- `final_candidates`：最终进入 `evidence_chain` 的候选摘要

普通请求不需要传 `debug`，默认不会返回 `debug_info`。

## RAG 输出契约

v0.2.9 起，`rag_query` 和 `/ask` 会在原有字段基础上返回一组稳定性字段，供后续 Multi-Agent 编排使用：

- `answer`：面向用户的自然语言回答。
- `confidence_score` / `answer_confidence`：LLM 对答案充分性的自评，二者目前保持一致，保留 `confidence_score` 是为了兼容旧调用。
- `retrieval_confidence`：检索侧置信度，根据 top 证据相似度、重排分数、引用标签、证据数量等计算，不依赖 LLM。
- `needs_human_review`：当检索置信度偏低、答案置信度偏低、证据缺口明显，或高风险场景置信度不足时为 `true`。
- `missing_evidence`：证据缺口列表，例如“最高相似度偏低”“有效证据数量少于预期”等。
- `risk_level`、`risk_types`、`recommended_actions`：场景风控结构化输出。
- `risk_type_evidence`、`recommended_action_evidence`：将每个风险类型/整改动作绑定到证据链中的引用标签。
- `evidence_chain`：完整证据链，包含来源、条号/章节号、相似度、重排分、引用标签和原文。

后续 Agent 可以按以下规则使用：

- `needs_human_review=true`：不要直接给最终结论，应进入人工复核或更高阶 Agent。
- `retrieval_confidence < 0.65`：优先要求补充检索或放宽/调整过滤条件。
- `risk_level=high` 且 `answer_confidence < 0.8`：建议进入合规专家 Agent 或人工审核。

## 风险分析接口

v0.3.0 起，系统提供 `POST /risk/analyze` 作为风险引擎入口。它复用 RAG 证据链，但输出更适合企业风控流程：

```bash
curl -X POST "http://localhost:8000/risk/analyze" -H "Content-Type: application/json" -d "{\"scenario\":\"某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？\",\"k\":5}"
```

核心输出：

- `scenario`：原始业务场景。
- `summary`：基于 RAG 的风控分析摘要。
- `risk_level`：综合 LLM 判断和风险分类后的等级。
- `risk_types`：展示给业务方看的风险类型。
- `risk_categories`：标准化风险分类，来自 `src/risk/taxonomy.py`，后续 Agent 应优先使用该字段做分流。
- `legal_basis`：从 `evidence_chain` 去重后的法律/标准依据。
- `recommended_actions`：整改动作。
- `confidence`：包含 `answer`、`retrieval` 和 `overall`。
- `needs_human_review`：是否需要人工复核或升级专家 Agent。

新增风险类型时，优先修改 `src/risk/taxonomy.py`，再补充 `tests/test_risk_engine.py`，不建议直接在 Prompt 中硬写大量分类规则。

## 风险报告接口

v0.3.2 起，系统提供 `POST /risk/report`，用于把 `/risk/analyze` 的结构化风险分析结果转换成更适合前端展示、Demo 汇报和后续 Agent 编排的报告结构。

```bash
curl -X POST "http://localhost:8000/risk/report" -H "Content-Type: application/json" -d "{\"scenario\":\"某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？\",\"k\":5}"
```

报告结构包括：
- `title`：报告标题。
- `scenario`：原始业务场景。
- `executive_summary`：业务可读的结论摘要。
- `risk_level`：综合风险等级。
- `risk_findings`：风险发现列表，包含风险类型、风险等级、分析说明和引用依据。
- `action_plan`：整改行动计划，包含优先级、动作、负责方提示和引用依据。
- `legal_basis`：去重后的法律/标准依据。
- `confidence`：回答、检索和整体置信度。
- `human_review_required` / `review_reasons`：是否建议人工或专家 Agent 复核。
- `evidence_chain`：底层 RAG 证据链，便于追溯。

如果后续接入 Multi-Agent，建议把 `/risk/report` 作为“对外稳定输出层”，而把 `/risk/analyze` 作为 Agent 内部判断层。

### 报告导出

v0.3.3 起，`POST /risk/report/export` 支持将风险报告导出为 Markdown 或瘦身 JSON：

```bash
curl -X POST "http://localhost:8000/risk/report/export" -H "Content-Type: application/json" -d "{\"scenario\":\"某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？\",\"k\":5,\"export_format\":\"markdown\"}"
```

可用参数：
- `export_format`：`markdown` 或 `json`。
- `include_evidence_chain`：是否保留底层证据链，默认 `true`。
- `include_source_analysis`：是否保留完整风险分析原始结果，默认 `false`。

建议用法：
- 前端或答辩 Demo：使用 `markdown`，可直接预览报告。
- 系统集成：使用 `json`，并按需关闭 `include_evidence_chain` 控制响应体积。
- 调试和人工复核：开启 `include_evidence_chain`，必要时再开启 `include_source_analysis`。

### 命令行导出与报告回归

v0.3.4 起，后端提供两个报告侧工具：

```bash
# 检查风险报告结构、行动计划、依据和导出稳定性
python tools/run_report_eval.py --output tests/report_eval_report.json

# 从题库导出单份 Markdown 报告
python tools/export_risk_report.py --case-id risk_app_location_ads_002 --format markdown

# 直接输入业务场景导出 JSON 报告
python tools/export_risk_report.py --scenario "某APP未告知收集精准定位用于广告推荐" --format json --no-include-evidence-chain
```

`tools/run_report_eval.py` 不是模型训练脚本，而是报告层回归测试。每次修改 `src/risk/report.py`、`src/risk/analyzer.py`、`src/rag/retriever.py` 或报告模板后，建议运行一次。

`tools/export_risk_report.py` 默认输出到 `reports/`，适合生成答辩样例、人工复核材料或阶段性归档文件。

## 法规清单与增量评测

v0.3.5 起，项目新增 `knowledge_manifest.json` 作为知识库清单。每部法规或标准应登记：

- `source`：入库 source 名称，需与 Qdrant payload 中的 source 基本一致。
- `file_path`：本地知识文件路径。
- `document_type` / `law_level` / `category` / `domain`：用于过滤、领域路由和增量评测。
- `effective_date` / `version`：用于后续效力和版本管理。
- `expected_anchors`：该文档必须能识别出的关键条文或标准章节。
- `smoke_cases`：该文档对应的轻量验证用例。

轻量题库位于：

```bash
tests/smoke_eval_cases.json
```

新增或修改单部法规后，建议先运行：

```bash
python tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --list-only
python tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --layers rag
```

如果该法规涉及风控场景，也可以运行三层增量评测：

```bash
python tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --layers all --output tests/impact_eval_report.json
```

常用筛选方式：

```bash
python tools/run_impact_eval.py --domain data_export --layers rag
python tools/run_impact_eval.py --document-type 标准 --layers rag
python tools/run_impact_eval.py --changed-only --layers rag
```

这样可以把“每次新增法规都全量测试”改为“平时只跑受影响 smoke case，发布前再跑全量回归”。

## 入库质量门禁

v0.3.6 起，新增 `tools/check_ingestion_quality.py`。该工具直接调用 `src.rag.ingestion.load_txt()`，检查真实入库前会生成的 Document 结构。

```bash
# 检查全部 manifest 文档
python tools/check_ingestion_quality.py --output tests/ingestion_quality_report.json

# 检查单部法规
python tools/check_ingestion_quality.py --source "中华人民共和国个人信息保护法"

# 检查某个领域
python tools/check_ingestion_quality.py --domain data_export
```

检查项包括：
- 源文件是否存在。
- 中文可读率是否过低。
- 是否有疑似 OCR/乱码噪声、目录点线、HTML 标签或页码残留。
- 是否生成 Document。
- 法律法规是否识别出条文。
- 标准类文件是否识别出标准章节。
- 是否生成 citation。
- `knowledge_manifest.json` 中的 `expected_anchors` 是否存在。

新增法规建议顺序：

```bash
python tools/check_ingestion_quality.py --source "法规名称"
python rag_admin.py --add "path/to/law.txt"
python rag_admin.py --inspect "法规名称"
python tools/run_impact_eval.py --source "法规名称" --layers rag
```

## 引用完整性校验

v0.3.7 起，系统会校验回答和报告中的 `[《...》...]` 引用是否真实来自证据链。

新增字段：

```json
{
  "citation_integrity": {
    "passed": true,
    "cited": [],
    "supported": [],
    "unsupported": []
  }
}
```

字段含义：
- `cited`：回答或报告正文中出现的引用。
- `supported`：`evidence_chain` 或 `legal_basis` 中存在的引用。
- `unsupported`：正文中出现但未被证据链支持的引用。

处理规则：
- `/ask` 中如有未支持引用，会设置 `needs_human_review=true`，并追加 `missing_evidence`。
- `/risk/analyze` 会继承 RAG 层引用完整性，并影响人工复核判断。
- `/risk/report` 会再次校验报告摘要、风险发现和行动计划中的引用，并写入 `review_reasons`。

该机制用于防止法律系统中最危险的一类问题：输出了看似权威但并未被检索证据支持的法条引用。

## 风险引擎回归评测

v0.3.1 起，系统提供独立的风险引擎评测脚本：

```bash
python tools/run_risk_eval.py --output tests/risk_eval_report.json
```

该脚本默认读取 `tests/rag_eval_cases.json`，自动筛选包含 `expected_risk_types`、`expected_risk_level` 或 `expected_actions` 的风控场景题，不需要维护第二份题库。

检查项包括：

- `expected_risk_level`：风险等级是否符合预期；对非低风险场景允许更保守的高风险判断。
- `expected_risk_types`：风险类型是否覆盖预期。
- `expected_actions`：整改动作是否覆盖预期。
- `legal_basis_non_empty`：是否返回可展示的法律/标准依据。
- `expected_evidence`：`legal_basis` 是否命中预期条文或标准章节。
- `overall_confidence`：是否返回 `confidence.overall`，也可用 `--min-overall-confidence` 设置阈值。
- `high_risk_has_basis`：高风险场景是否有法律依据和风险类型引用绑定。

常用命令：

```bash
python tools/run_risk_eval.py
python tools/run_risk_eval.py --verbose
python tools/run_risk_eval.py --min-overall-confidence 0.7
```

## RAG 回归评测

题库默认放在：

```bash
tests/rag_eval_cases.json
```

运行评测：

```bash
python tools/run_rag_eval.py --output tests/rag_eval_report.json
```

如果题库中包含场景型风控用例，建议开启风险字段校验：

```bash
python tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json
```

评测脚本会逐条调用 `rag_query(debug=True)`，检查：

- `expected_evidence`：是否命中预期法律/标准来源、条号或章节号
- `expected_answer_keywords`：答案是否覆盖关键概念；脚本内置了少量同义表达，例如“质量原则”可匹配“信息质量”
- `min_confidence_score`：LLM 自评置信度是否达到阈值
- `expected_risk_types`：开启 `--check-risk` 后检查风险类型是否覆盖预期
- `expected_risk_level`：开启 `--check-risk` 后检查风险等级，`low` 要精确匹配，`medium/high` 按保守风控口径允许更高风险判断
- `expected_actions`：开启 `--check-risk` 后检查整改动作是否覆盖预期

`expected_evidence_match` 默认是 `all`；如果某个场景允许多份依据命中其一即可，可以在用例中写：

```json
{
  "expected_evidence_match": "any"
}
```

这套文件用于回归评测，不是模型训练。每次新增法规、标准，或修改 `ingestion.py`、`retriever.py`、Prompt 后，建议跑一次并查看 `tests/rag_eval_report.json`。当前题库包含 25 条用例，其中 15 条为风控场景题。

## 与 ingestion.py 的兼容性

新版 `ingest` 支持旧调用，也支持扩展分类元数据：

```python
def ingest(
    file_path: str,
    collection_name: str = "legal_knowledge",
    source_name: str | None = None,
    law_level: str | None = None,
    category: str = "数据合规",
    version: str = "",
    document_type: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
)
```

不显式传入分类字段时，系统会根据文件名和正文自动推断文档类型与效力层级。
