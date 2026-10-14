# Manual Review Visual Workbench Manual Save v0.4.7.8.11

本版本为离线人工复核台新增显式 `保存草稿` 按钮。此前页面已经会自动把输入暂存在浏览器本地，但 reviewer 很难确认“到底有没有保存”。本版本给出明确保存动作和保存时间反馈。

## 更新内容

- 决策页按钮区新增 `保存草稿 / Save draft`。
- 点击后写入当前 case 草稿的 `saved_at` 时间戳。
- case header 显示：
  - `尚未手动保存`
  - `上次保存 {time}`
  - `有未手动保存的更新`
- 保留自动暂存机制：输入变化仍会自动写入浏览器 `localStorage`。
- Build report 新增 `supports_manual_draft_save=true`。

## 边界

手动保存只是离线页面的本地草稿确认，不是人工复核结论导入，不写项目文件，不修改原始 decision schema，也不绕过 importer、diff、validator、promotion dry run 或 closeout gate。

本版本不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case 或 `rag_query` 主流程；不调用 backend、Qdrant 或 LLM。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI" tools/manual_review_visual_workbench/index.html tools/build_manual_review_visual_workbench.py
```
