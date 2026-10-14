# Manual Review Visual Workbench Decision Tab v0.4.7.8.8

本版本只改进离线人工复核台的“决策”页可读性。目标是让法律、合规或业务 reviewer 不需要理解内部工程枚举，也能判断一个 RAG grounding 质量诊断是否成立，并清楚知道后续导出仍要进入 importer、diff、validator、promotion dry run 和 closeout gate。

## 更新内容

- 决策页顶部新增“复核判断摘要”，把案由线索、主要诊断、建议根因、建议后续动作、当前结论和导出状态放在同一个摘要区。
- 新增“建议审阅顺序”：先核对案由/问题/证据是否对齐，再选择复核结论，最后确认根因、后续动作和回归测试样本候选。
- 将复核结论从下拉框改为带说明的单选卡片，显示中文/英文可读名称、说明和原始代码。
- 为复核信息、复核结论、根因判断、后续动作、治理备注五个区块增加区块说明。
- 将原先偏工程化的 `fixture candidate` 表达改成“沉淀为回归测试样本候选”，并明确不会直接写入 eval case。
- 根因和后续动作勾选项继续显示可读名称、说明和原始代码，导出字段仍保持原始枚举值。

## 边界

本版本是 RAG grounding quality 的人工审阅界面改进，不是样本修补工具。它不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、eval case 或 `rag_query` 主流程，也不调用 backend、Qdrant 或 LLM。

## 输出

- HTML：`tools/manual_review_visual_workbench/index.html`
- Build report：`tests/manual_review_visual_workbench_build_report.json`
- Build report 能力标志：`supports_decision_tab_readability=true`
- Workbench cases：36
- Items with case context：36
- Gate status：`blocked`

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
```
