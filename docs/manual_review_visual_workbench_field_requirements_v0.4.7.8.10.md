# Manual Review Visual Workbench Field Requirements v0.4.7.8.10

本版本把人工复核台“决策”页的字段要求直接标在界面上，避免 reviewer 误以为每一项都必须填写。

## 字段分层

### 必填

这些字段缺失时，草稿不能算作可用复核结论：

- 复核人
- 复核日期
- 复核结论
- 理由

### 条件必填

这些字段只在特定结论下要求填写：

- 确认的根因

当复核结论为“确认诊断成立”或“确认需要范围校准”时，应至少确认一个主要根因。若选择“驳回诊断”“信息不足”或“暂缓”，可以不填确认根因。

### 可选

这些字段不确定时可以留空，不会阻止草稿导出：

- 驳回的根因
- 确认的后续动作
- 拟进入治理链路的变更目标
- 回归测试样本候选
- 备注

## 更新内容

- 决策页字段新增 `必填 / 条件必填 / 可选` badge。
- Badge 支持简体中文和英文语言切换。
- 每个关键字段新增简短说明，告诉 reviewer 不会填时该如何处理。
- Build report 新增 `supports_field_requirement_labels=true`。

## 边界

本版本只改进离线人工复核台的可理解性，不改变导出 schema，不改变 draft ready 校验规则，不改变 importer、diff、validator、promotion dry run 或 closeout gate。

本版本不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case 或 `rag_query` 主流程；不调用 backend、Qdrant 或 LLM。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI" tools/manual_review_visual_workbench/index.html tools/build_manual_review_visual_workbench.py
```
