# Manual Review Visual Workbench Label Glossary v0.4.7.8.6

## 定位

本版本继续打磨离线人工复核可视化工作台，让非系统设计者也能读懂 case 中的大量内部英文标签。页面不会修改原始诊断数据，导出的 JSON/CSV 仍保留原始枚举代码，以保证 importer、diff、validator、promotion dry run 和 closeout 链路可继续使用。

## 新增能力

- 取消 case detail 中单独的 `Guide/指南` 页签，操作指南只保留在左下角面板。
- 新增 `标签说明 / Glossary` 页签，汇总当前 case 出现的队列标签、诊断问题、建议根因、后续动作、诊断模块、证据上下文、gate blocker、import error 和 guardrail。
- 常见英文枚举显示为“可读名称 / 原始代码”，悬停可查看解释。
- 标签说明卡片提供跳转按钮，可跳到对应的概览、证据、决策或流程页签。
- 浏览器本地记录 `last_exported_at`，导出 JSON/CSV 后自动更新导出状态。
- 草稿更新晚于上次导出时，页面显示“有未导出的更新”。

## 边界

本版本只修改离线静态 visual workbench 生成器、生成物、测试和文档，不接入 `rag_query` 主流程，不访问后端 API，不访问 Qdrant，不调用 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation 或 eval case。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
```
