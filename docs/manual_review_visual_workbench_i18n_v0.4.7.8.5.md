# Manual Review Visual Workbench i18n v0.4.7.8.5

## 定位

本版本修复人工复核可视化工作台的语言能力：语言选择不再只是装饰控件，而是由统一 i18n 配置驱动页面固定文案、队列、标签页、按钮、表单、状态提示和操作指南。

## 新增能力

- 默认界面语言为 `zh-CN`，页面首次打开显示简体中文。
- 语言选择器支持 `简体中文` 与 `English`。
- 用户选择语言后写入浏览器 `localStorage`，刷新后保持选择。
- 左侧队列、状态卡、顶部标题、KPI、案例列表、详情标签、证据表头、复核表单、pipeline 和 guide 均跟随语言切换。
- 操作指南分为侧边栏简表与详情页 `Guide/指南`，两处均读取同一套语言配置。

## 边界

本版本只修改离线静态 visual workbench 生成器、生成物、测试和文档，不接入 `rag_query` 主流程，不访问后端 API，不访问 Qdrant，不调用 LLM，不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation 或 eval case。

## 使用方式

打开：

```powershell
tools\manual_review_visual_workbench\index.html
```

在页面右上角选择 `简体中文` 或 `English`。切换后页面立即重绘，已填写的本地草稿仍保存在浏览器 localStorage 中。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
```
