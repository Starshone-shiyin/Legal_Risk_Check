# Manual Review Visual Workbench Guide & Language v0.4.7.8.4

## 定位

本版本是视觉审阅台的可用性补强：在页面内新增操作指南，并加入统一风格的语言选择器。

当前语言选择器支持 `简体中文`。选择器以统一的 badge/select 样式出现在顶部状态区；由于当前只有一个语言包，控件默认禁用但可见，便于后续扩展英文或其他语言。

## 新增能力

- 左侧新增 `操作指南` 面板。
- 详情区新增 `Guide` 页签。
- 顶部新增语言选择器。
- payload 增加 `ui.default_language`、`ui.supported_languages` 和 `ui.guide_steps`。
- build report 增加 `supports_operation_guide` 和 `supported_languages`。

## 操作指南内容

1. 先在左侧选择队列，例如高优先级或待复核。
2. 在中间列表选择一个 case，查看右侧诊断、证据和复核问题。
3. 在 Decision 页签填写 reviewer、reviewed_at、decision 和 rationale。
4. 确认 root cause、follow-up action 和是否作为 fixture candidate。
5. 后续处理流程只使用 JSON；CSV 只是给人打开表格查看和核对。

## 边界

- 不接入 `rag_query`。
- 不调用后端写接口。
- 不访问 Qdrant。
- 不调用 LLM。
- 不修改 hidden seed、anchor、rerank、prompt、risk rule、eval case。
- 语言选择器当前只提供简体中文，不改变数据字段、导出格式或验证链路。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
```
