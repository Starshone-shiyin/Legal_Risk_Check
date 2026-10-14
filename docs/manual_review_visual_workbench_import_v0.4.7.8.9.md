# Manual Review Visual Workbench Import Replay v0.4.7.8.9

本版本补齐离线人工复核台的“续审”能力：reviewer 可以把之前从页面导出的 filled workbench JSON 重新导入，页面会按 `case_id` 把人工复核字段放回对应案例草稿。

维护补充（2026-05-13）：为避免旧草稿、手工 CSV 或 advisory 文件被“转手导出”为正式人工结论，页面导入入口已收紧为 JSON。CSV 仍可导出用于人工阅读和留痕，但不再作为正式导入入口。

## 更新内容

- 新增 `导入复核文件` 控件，位于案例搜索框下方。
- 支持读取页面导出的 `filled_manual_review_workbench.json`；不再导入 CSV。
- 导入正式人工草稿时会先清空当前工作台指纹下的旧本地草稿，避免旧 ready draft 混入下一次导出。
- 页面导出会写入 `workbench_fingerprint` 和 `summary.exported_case_ids`，导出前会弹出将导出的 case 预览。
- 导入逻辑完全在浏览器内完成，使用 `FileReader` 读取用户选择的本地文件。
- 仅回填人工复核字段：
  - `reviewer`
  - `reviewed_at`
  - `decision`
  - `confirmed_root_causes`
  - `rejected_root_causes`
  - `confirmed_follow_up_actions`
  - `proposed_change_targets`
  - `fixture_candidate`
  - `rationale`
  - `notes`
- 导入后刷新队列、侧栏状态、badge 和当前 case detail。
- 页面显示导入摘要：已导入、已清除旧草稿、未匹配、重复、空白跳过与错误信息。
- 未匹配的 `case_id` 不会写入当前草稿。

## 使用方式

1. 打开 `tools/manual_review_visual_workbench/index.html`。
2. 点击案例列表上方的 `导入复核文件`。
3. 选择此前页面导出的 filled workbench JSON 文件。
4. 页面会把匹配到的复核内容放回对应案例的本地草稿。
5. 继续审阅或再次导出。

## 边界

这是 RAG grounding quality diagnostics 的人工审阅辅助工具，不是样本修补工具，也不是治理链路写入器。

本版本不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case 或 `rag_query` 主流程；不调用 backend、Qdrant 或 LLM；不写项目文件。导入结果只存在浏览器 `localStorage` 中，仍需导出后走 importer、diff、validator、promotion dry run 和 closeout gate。

## 输出

- HTML：`tools/manual_review_visual_workbench/index.html`
- Build report：`tests/manual_review_visual_workbench_build_report.json`
- Build report 能力标志：`supports_review_export_import=true`、`supports_scoped_local_drafts=true`、`imports_replace_stale_local_drafts=true`、`supports_json_import_contract=true`、`supports_export_case_preview=true`
- Workbench cases：36
- Gate status：`blocked`

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench.py src\main.py tests\test_manual_review_visual_workbench.py tests\test_manual_review_visual_workbench_build_artifact.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_visual_workbench_build_artifact
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench.py --output tools\manual_review_visual_workbench\index.html --report-output tests\manual_review_visual_workbench_build_report.json
rg -n "fetch\(|XMLHttpRequest|/ask|rag_query\(|ChatOpenAI" tools/manual_review_visual_workbench/index.html tools/build_manual_review_visual_workbench.py
```
