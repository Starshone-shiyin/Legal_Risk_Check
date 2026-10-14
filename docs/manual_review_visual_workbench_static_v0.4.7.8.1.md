# Manual Review Visual Workbench Static UI v0.4.7.8.1

## 定位

本版本在 v0.4.7.8.0 契约之上，生成一个可直接打开的本地静态 HTML 审阅台。

它不是正式 Web 服务，也不接入 FastAPI。生成后的页面把现有离线报告嵌入到单个 HTML 文件中，因此 reviewer 不需要启动数据库、后端、Node 或 RAG 服务。

## 新增内容

- `tools/build_manual_review_visual_workbench.py`
- `tools/manual_review_visual_workbench/index.html`
- `tests/manual_review_visual_workbench_build_report.json`
- `tests/test_manual_review_visual_workbench.py`

## 支持能力

- 左侧队列：全部 cases、高优先级、待复核、blocked gate、本地草稿、可导出草稿。
- 顶部状态：gate status、静态数据状态、版本。
- KPI：cases、pending、high priority、imported、valid proposed、ready actions。
- case list：按 case、issue、queue、domain 搜索。
- case detail：overview、evidence、questions、decision、pipeline。

## 当前摘要

- Workbench cases：36
- Pending：36
- High priority：29
- Gate status：`blocked`
- Ready for static review：true

## 边界

- 不接入 `rag_query`。
- 不调用后端写接口。
- 不访问 Qdrant。
- 不调用 LLM。
- 不修改 hidden seed、anchor、rerank、prompt、risk rule、eval case。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
```
