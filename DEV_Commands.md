# 开发常用指令速查表 (Legal_Risk_Check)

> 适用于日常开发：Codex 产出代码后，在本地集成、测试、运行的一连串命令。

## 一、环境准备

```bash
# 进入项目目录
cd D:\Projects\Legal_Risk_Check

# 激活虚拟环境（PowerShell）
.\venv\Scripts\Activate.ps1

# 如果 PowerShell 禁止脚本，用 cmd 激活
cmd /c "venv\Scripts\activate.bat"
```

## 二、代码质量检查（每次改动后）

```bash
# 仅语法检查（不运行代码）
python -m compileall src tests rag_admin.py

# 使用 black 自动格式化（如果安装）
black src/ --line-length 100

# 使用 ruff 检查 lint（如果安装）
ruff check src/
```

## 三、Qdrant 向量数据库

```bash
# 启动 Qdrant 容器（如果未运行）
docker start qdrant

# 查看容器状态
docker ps

# 停止 Qdrant 容器
docker stop qdrant

# 重建 Qdrant 容器（删除后重新创建，会清空数据）
docker rm -f qdrant
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

## 四、知识库管理（法律文本入库 / 重建）

```bash
# 全量重建知识库（先删后加）
python rag_admin.py --rebuild

# 查看集合统计（点数、状态）
python rag_admin.py --stats

# 列出所有 source（法律名称）
python rag_admin.py --list-sources

# 检查全库入库结构（分类、chunk 数、条文/标准章节样例）
python rag_admin.py --inspect

# 检查单个 source 的入库结构
python rag_admin.py --inspect "信息安全技术 个人信息安全规范 GB_T_35273_2020"

# 控制 inspect 样例数量
python rag_admin.py --inspect --inspect-limit 5

# 追加一个法律文件
python rag_admin.py --add "src/knowledge/data_compliance/中华人民共和国数据安全法.txt"

# 追加时指定元数据
python rag_admin.py --add "文件.txt" --law-level "法律" --category "数据安全"

# 追加国家标准/行业标准时指定元数据
python rag_admin.py --add "标准文件.txt" --document-type "标准" --law-level "国家标准" --standard-type "推荐性国家标准" --category "数据合规"
```

## 五、启动 FastAPI 服务（调试模式）

后端入口是 `src.main:app`。日常使用推荐根目录脚本：

开发者调试场景使用专用入口：

```bat
start_backend_debug.bat
```

它优先启动 `8014`；如果端口被占用，会自动选择下一个空闲端口，并开启隔离调试场景、实时行情和 RSS。也可以传入端口号强制指定，例如 `start_backend_debug.bat 8015`。

关闭调试后端：

```bat
stop_backend_debug.bat
```

```powershell
# 最省事：双击 start_backend.bat，或在终端运行
.\start_backend.bat

# 换端口，例如前端占用 8000 时
.\start_backend.bat -Port 8001

# 如果 PowerShell 允许脚本，也可以直接运行 ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_backend.ps1

# 不需要热重载时
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_backend.ps1 -NoReload
```

通过上述脚本在 `127.0.0.1` 启动时，内部风控和风险接入会自动使用受限的本机演示身份，因此普通模式也可以直接联调完整风控流程。部署到 `0.0.0.0` 或其他地址时，演示身份默认关闭，仍需要网关签名身份；本机如需验证该状态，可附加 `-DisableDemoIdentity`。

启动后常用地址：

- Swagger / 接口调试：`http://127.0.0.1:8000/docs`
- OpenAPI schema：`http://127.0.0.1:8000/openapi.json`
- 产品接口前缀：`http://127.0.0.1:8000/product/...`
- RAG 问答接口：`http://127.0.0.1:8000/ask`

如果 `/ask` 需要访问向量库，请先确认 Qdrant 已启动；fixture-backed `/product/*` 接口可用于前端结构联调。

```bash
# 开发模式（热重载，修改代码自动重启）
uvicorn src.main:app --reload

# 指定端口（默认 8000）
uvicorn src.main:app --reload --port 8001

# 启用详细日志
uvicorn src.main:app --reload --log-level debug
```

## 六、测试 `/ask` 接口

### 使用 Swagger UI（推荐）
启动服务后打开浏览器：`http://localhost:8000/docs`

### 使用 curl（PowerShell / CMD）

```bash
# 基本请求
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"个人信息保护的核心原则是什么？\",\"k\":3}"

# 带过滤条件
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"数据跨境规则\",\"k\":3,\"law_level\":\"法律\",\"category\":\"数据合规\"}"

# 查询国家标准；系统会自动补充 document_type=标准、law_level=国家标准
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"根据国家标准，提供信息服务一方应当保护哪些信息？\",\"k\":3}"

# 显式限定国家标准
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"个人信息安全规范中的个人敏感信息是什么？\",\"k\":3,\"document_type\":\"标准\",\"law_level\":\"国家标准\"}"

# 开启检索诊断模式，返回 vector_candidates、deterministic_supplements、reranked_candidates 等调试信息
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"根据国家标准，提供信息服务一方应当保护哪些信息？\",\"k\":3,\"debug\":true}"

# Windows 下用双引号转义复杂 JSON（推荐保存为 .ps1 或使用 Swagger）
```

### 使用 PowerShell 的 `Invoke-WebRequest`（适合调试）
```powershell
$body = @{question="个人信息保护的原则"; k=3} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method Post -Body $body -ContentType "application/json"
```

## 七、测试 `/risk/analyze` 风控分析接口

`/risk/analyze` 面向业务场景，不只是回答问题。它会返回风险等级、风险类型、风险分类、法律依据、整改动作、置信度和是否需要人工复核。

```bash
curl -X POST "http://localhost:8000/risk/analyze" -H "Content-Type: application/json" -d "{\"scenario\":\"某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？\",\"k\":5}"

# 开启 debug，查看底层 RAG 候选、确定性锚点和重排结果
curl -X POST "http://localhost:8000/risk/analyze" -H "Content-Type: application/json" -d "{\"scenario\":\"某AI医疗公司使用患者病历训练模型，并同步至境外服务器计算，是否合规？\",\"k\":6,\"debug\":true}"
```

核心返回字段：

- `risk_level`：`low` / `medium` / `high`
- `risk_types`：面向展示的风险类型
- `risk_categories`：标准化风险分类，包含 `id`、`name`、`domain` 和命中关键词
- `legal_basis`：去重后的法律/标准依据
- `confidence.answer`：LLM 自评置信度
- `confidence.retrieval`：检索侧置信度
- `needs_human_review`：是否建议人工或更高阶 Agent 复核

## 八、测试 `/risk/report` 风险报告接口

`/risk/report` 面向前端展示、Demo 和后续 Agent 编排。它会先执行风险分析，再输出更稳定的报告结构，包括摘要、风险发现、行动计划、法律依据、置信度和是否需要人工复核。

```bash
curl -X POST "http://localhost:8000/risk/report" -H "Content-Type: application/json" -d "{\"scenario\":\"某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？\",\"k\":5}"

# 开启 debug 时，报告仍会保留底层 evidence_chain，便于排查引用依据
curl -X POST "http://localhost:8000/risk/report" -H "Content-Type: application/json" -d "{\"scenario\":\"某AI医疗公司使用患者病历训练模型，并同步至境外服务器计算，是否合规？\",\"k\":6,\"debug\":true}"
```

核心返回字段：
- `executive_summary`：适合直接展示给业务方的结论摘要。
- `risk_findings`：结构化风险发现，每项包含风险类型、等级、分析和引用依据。
- `action_plan`：整改行动清单，包含优先级、建议动作和负责方提示。
- `legal_basis`：去重后的法律/标准依据。
- `confidence`：回答、检索和整体置信度。
- `human_review_required` / `review_reasons`：是否建议人工或专家 Agent 复核。

## 九、测试 `/risk/report/export` 报告导出接口

`/risk/report/export` 会在生成风险报告后导出 Markdown 或瘦身 JSON，适合前端预览、答辩 Demo、归档和人工复核流转。

```bash
# 导出 Markdown 报告
curl -X POST "http://localhost:8000/risk/report/export" -H "Content-Type: application/json" -d "{\"scenario\":\"某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？\",\"k\":5,\"export_format\":\"markdown\"}"

# 导出 JSON，默认不包含 source_analysis，可选择是否保留 evidence_chain
curl -X POST "http://localhost:8000/risk/report/export" -H "Content-Type: application/json" -d "{\"scenario\":\"某APP明确告知用户收集位置信息用于导航服务，并取得单独同意，且用户可随时关闭定位权限，该行为是否合规？\",\"k\":3,\"export_format\":\"json\",\"include_evidence_chain\":false}"
```

导出参数：
- `export_format`：`markdown` 或 `json`。
- `include_evidence_chain`：是否保留底层证据链，默认 `true`。
- `include_source_analysis`：是否保留完整 `/risk/analyze` 原始结果，默认 `false`。

## 十、运行单元测试（如果已实现）

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_rag.py

# 显示详细输出
pytest -v

# 显示 print 输出
pytest -s
```

## 十一、运行 RAG 回归评测（v0.3.9 支持三层评测体系）

```bash
# === 日常开发：只跑 smoke（25 题，秒级完成）===
python tools/run_rag_eval.py --smoke

# === 单领域验证：只跑指定领域（6-10 题）===
python tools/run_rag_eval.py --domain 知识产权 --check-risk
python tools/run_rag_eval.py --domain 公司治理 --check-risk
python tools/run_rag_eval.py --domain 市场秩序 --check-risk
python tools/run_rag_eval.py --domain 财税 --check-risk
python tools/run_rag_eval.py --domain 民商事 --check-risk

# === 发布前：全量回归（60 题）===
python tools/run_rag_eval.py --check-risk --output tests/rag_eval_report.json

# 其他参数：
#   --verbose   输出每个用例的完整答案
#   --fail-fast 遇到失败立即停止
#   --cases     自定义题库路径
```

评测脚本默认检查三类指标：`expected_evidence`、`expected_answer_keywords`、`min_confidence_score`。加入 `--check-risk` 后，还会检查 `expected_risk_types`、`expected_risk_level`、`expected_actions`，用于验证场景型风控输出。这不是模型训练，而是 RAG 回归测试；每次改检索、入库或 Prompt 后建议跑一遍。

v0.2.9 起，评测报告还会记录 RAG 输出契约字段：

- `retrieval_confidence`：检索侧置信度，区别于 LLM 自评。
- `answer_confidence`：LLM 对答案的自评，兼容旧字段 `confidence_score`。
- `needs_human_review`：是否建议人工复核或交给更高阶 Agent。
- `missing_evidence`：证据缺口说明。
- `risk_type_evidence` / `recommended_action_evidence`：风险类型和整改动作对应的引用依据。

## 十二、运行风险引擎回归评测

```bash
# 复用 tests/rag_eval_cases.json 中的风控场景题
python tools/run_risk_eval.py

# 保存风险引擎评测报告
python tools/run_risk_eval.py --output tests/risk_eval_report.json

# 输出更完整的风险类型、整改动作和摘要
python tools/run_risk_eval.py --verbose

# 可选：要求 confidence.overall 达到指定阈值
python tools/run_risk_eval.py --min-overall-confidence 0.7
```

风险评测会自动筛选带有 `expected_risk_types`、`expected_risk_level` 或 `expected_actions` 的用例，检查风险等级、风险类型、整改动作、法律依据、整体置信度和高风险证据绑定。

## 十三、运行风险报告回归评测

```bash
# 检查风险报告结构是否稳定
python tools/run_report_eval.py

# 保存完整报告层评测结果
python tools/run_report_eval.py --output tests/report_eval_report.json

# 输出每个用例的报告摘要
python tools/run_report_eval.py --verbose

# 可选：要求 confidence.overall 达到指定阈值
python tools/run_report_eval.py --min-overall-confidence 0.7
```

报告评测会检查：
- 核心字段是否完整：`executive_summary`、`risk_findings`、`action_plan`、`legal_basis`、`confidence` 等。
- 风险等级、风险类型、整改动作是否覆盖题库预期。
- 法律依据是否命中期望条文。
- Markdown 导出是否包含固定章节。
- JSON 瘦身导出是否能按需去掉 `evidence_chain` 和 `source_analysis`。

## 十四、导出单份风险报告

```bash
# 直接输入场景，导出 Markdown 到 reports/
python tools/export_risk_report.py --scenario "某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？" --format markdown

# 从题库按 case_id 导出 Markdown
python tools/export_risk_report.py --case-id risk_app_location_ads_002 --format markdown

# 导出 JSON，并去掉 evidence_chain 以控制体积
python tools/export_risk_report.py --case-id risk_compliant_case_001 --format json --no-include-evidence-chain

# 显式指定输出文件
python tools/export_risk_report.py --case-id risk_app_location_ads_002 --format markdown --output reports/risk_app_location_ads_002.md
```

默认输出目录是 `reports/`。`--case-id` 会读取 `tests/rag_eval_cases.json`，适合快速生成答辩或人工复核样例。

## 十五、多领域检索（v0.3.8 新增）

新增领域后，可通过 `category` 参数限定检索范围：

```bash
# 公司治理
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"股东未按期缴纳出资有什么责任？\",\"k\":3,\"category\":\"公司治理\"}"

# 知识产权
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"哪些行为属于侵犯注册商标专用权？\",\"k\":3,\"category\":\"知识产权\"}"

# 市场秩序
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"反垄断法规定了哪些垄断行为？\",\"k\":3,\"category\":\"市场秩序\"}"

# 民商事
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"格式条款在什么情况下无效？\",\"k\":3,\"category\":\"民商事\"}"

# 财税
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"增值税一般计税方法的应纳税额如何计算？\",\"k\":3,\"category\":\"财税\"}"

# 安全合规
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"国家秘密的定义是什么？\",\"k\":3,\"category\":\"安全合规\"}"
```

当前支持的所有 category 值：`数据合规`、`安全合规`、`公司治理`、`市场秩序`、`知识产权`、`财税`、`民商事`。

## 十六、运行增量影响评测

新增或修改单部法规/标准后，优先运行 impact eval，而不是每次都跑完整 RAG/Risk/Report 回归。

```bash
# 查看某部法规会影响哪些 smoke case，不实际调用模型
python tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --list-only

# 只跑该法规相关 RAG smoke case
python tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --layers rag

# 同时跑 RAG、Risk、Report 三层；只有配置了风险预期的 case 才会跑 Risk/Report
python tools/run_impact_eval.py --source "中华人民共和国个人信息保护法" --layers all --output tests/impact_eval_report.json

# 按领域运行，例如数据出境
python tools/run_impact_eval.py --domain data_export --layers rag

# 按文档类型运行，例如所有标准类文档
python tools/run_impact_eval.py --document-type 标准 --layers rag

# 仅选择 Git 变更涉及的 manifest 文档
python tools/run_impact_eval.py --changed-only --layers rag
```

相关文件：
- `knowledge_manifest.json`：法规/标准清单，记录 source、领域、效力层级、关键锚点和 smoke case。
- `tests/smoke_eval_cases.json`：轻量级增量评测题库。
- `tests/impact_eval_report.json`：增量评测输出报告。

建议日常策略：
- 新增法规：先 `rag_admin.py --inspect`，再 `run_impact_eval.py --source "法规名称"`。
- 修改检索或 Prompt：跑完整 `run_rag_eval.py`。
- 版本发布前：跑 RAG、Risk、Report 三层全量评测。

## 十七、运行入库质量门禁

新增或清洗法规/标准后，先检查本地文件是否能被 `load_txt()` 正确解析，再考虑写入 Qdrant。

```bash
# 检查全部 manifest 文档
python tools/check_ingestion_quality.py --output tests/ingestion_quality_report.json

# 只检查某部法规
python tools/check_ingestion_quality.py --source "中华人民共和国个人信息保护法"

# 按领域检查
python tools/check_ingestion_quality.py --domain data_export

# 按分类检查
python tools/check_ingestion_quality.py --category 数据合规
```

检查内容包括：
- 源文件是否存在。
- 中文可读率是否过低。
- 是否存在疑似 OCR/乱码噪声、目录点线、HTML 标签或页码残留。
- 是否生成可入库 Document。
- 法律文本是否识别出条文，标准文本是否识别出标准章节。
- 是否生成 citation。
- `knowledge_manifest.json` 中配置的 `expected_anchors` 是否都能被解析出来。

建议流程：
```bash
python tools/check_ingestion_quality.py --source "法规名称"
python rag_admin.py --add "path/to/law.txt"
python rag_admin.py --inspect "法规名称"
# v0.3.10: 入库后先跑自检，确认条款号一致
python tools/check_eval_consistency.py
python tools/run_impact_eval.py --source "法规名称" --layers rag
```

## 十七-B、评测自检：条款号一致性（v0.3.10 新增）

每次修改测试用例或入库新法规后，运行此工具检查 expected_evidence 的条款号是否在知识库中实际存在：

```bash
# 检查全部 85 条评测用例
python tools/check_eval_consistency.py

# 保存 JSON 报告
python tools/check_eval_consistency.py --output tests/eval_consistency_report.json
```

自动检查项：
- 每个 expected_evidence 的 (source, article_no) 是否在 Qdrant 中存在
- 每个 expected_evidence 的 (source, section_no) 是否在 Qdrant 中存在
- 如有条款号缺失（如法条修订导致编号变更），会立即提示

## 十八、检查引用完整性

v0.3.7 起，`/ask`、`/risk/analyze`、`/risk/report` 都会返回 `citation_integrity` 字段：

```json
{
  "citation_integrity": {
    "passed": true,
    "cited": [],
    "supported": ["[《中华人民共和国个人信息保护法》第十七条]"],
    "unsupported": []
  }
}
```

含义：
- `cited`：答案或报告正文中实际出现的 `[《...》...]` 引用。
- `supported`：证据链或法律依据中可支持的引用。
- `unsupported`：正文中出现但证据链不支持的引用。

如果 `unsupported` 非空，系统会自动设置：
- `/ask` 与 `/risk/analyze`：`needs_human_review=true`，并写入 `missing_evidence`。
- `/risk/report`：`human_review_required=true`，并写入 `review_reasons`。

建议在高风险场景中重点检查该字段，避免报告出现未由证据支持的法条引用。

## 十九、命令行交互测试（无需前端）

```bash
# 使用 python 直接调用 rag_query
python -c "from src.rag.retriever import rag_query; print(rag_query('个人信息保护的原则')['answer'])"

# 交互式循环（需要 cli_chat.py，可自己写）
python cli_chat.py
```

## 二十、依赖管理

```bash
# 安装/更新依赖
pip install -r requirements.txt   # 如果没有 requirements.txt，可以导出当前环境
pip freeze > requirements.txt

# 安装特定包
pip install gradio
```

## 二十一、日志与调试

```bash
# 查看 uvicorn 实时日志（终端）
# 启动时添加 --log-level debug

# 在 Python 代码中打印变量（临时）
print(f"DEBUG: {variable}")

# 查看 Qdrant 容器日志
docker logs qdrant -f
```

## 二十二、完整工作流示例

```bash
# 1. 激活环境
cd D:\Projects\Legal_Risk_Check
.\venv\Scripts\Activate.ps1

# 2. 启动 Qdrant
docker start qdrant

# 3. 启动 FastAPI
uvicorn src.main:app --reload

# 4. 另开一个终端，发送测试请求
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"个人信息保护的原则\",\"k\":3}"

# 5. 检查返回的 evidence_chain 结构
# 6. 停止服务（Ctrl+C）
# 7. 提交 Git
git add . && git commit -m "功能描述"
```

---

> **提示**：将常用命令保存为批处理脚本（`.bat` 或 `.ps1`）可以一键执行，例如 `start_dev.ps1` 包含激活环境、启动 Qdrant、启动 FastAPI。
```

你可以将以上内容保存为 `DEV_COMMANDS.md`，放在项目根目录。如果还需要其他特定场景的命令（如更新依赖、清理缓存），可以随时补充。
