# Manual Review Visual Workbench Contract v0.4.7.8.0

## 定位

本版本开启 v0.4.7.8.x Visual Manual Review Workbench 系列，但只定义离线视觉审阅台的数据契约、UI 信息架构和安全边界，不实现正式前端交互。

它的目标是让非工程背景的 reviewer 更容易看懂 RAG grounding 诊断结果：左侧看队列，中间看 case，右侧看证据、问题和人工复核字段；填完后只能导出 workbench 文件，再走既有 importer / diff / validator / promotion dry run / closeout 工具链。

## UI 参考

参考 `BiliSum Light UI Spec` 的轻量工作台结构：

- 左侧窄导航。
- 顶部状态与统计。
- 主工作区卡片、列表、详情面板。
- 轻量、清晰、低干扰的浅色界面。

本项目不会照搬消费型粉色品牌视觉，而是改为法律风控审美：深青、蓝灰、琥珀风险提示、白色卡片和 8px 圆角。界面应像“审阅台”，不是营销页，也不是 RAG 主流程控制台。

## 数据来源

视觉审阅台只能读取已有离线报告：

- `tests/evidence_manual_review_workbench.json`
- `tests/manual_review_intake_contract_report.json`
- `tests/evidence_manual_review_progress_report.json`
- `tests/evidence_manual_review_governance_report.json`
- `tests/manual_review_workbench_import_report.json`
- `tests/manual_review_decision_diff_report.json`
- `tests/proposed_manual_review_decision_validation_report.json`
- `tests/validated_decision_promotion_dry_run_report.json`
- `tests/manual_review_intake_gate_closeout_report.json`

最小可用 UI 只要求前两个文件存在：workbench 提供 case queue 和 evidence context，intake contract 提供字段权限和枚举值。

## 字段边界

只读上下文字段：

- `case_id`
- `priority_score`
- `risk_level`
- `expected_domains`
- `queue_tags`
- `issue_types`
- `suggested_root_causes`
- `suggested_follow_up_actions`
- `review_question_count`
- `missing_final_expected_count`
- `missing_scenario_core_count`
- `lost_evidence_count`

允许 reviewer 填写的字段：

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

视觉审阅台不得把填写结果直接写回原始 decision schema。它只能导出 filled workbench JSON/CSV。

## 当前契约摘要

- Gate status：`blocked`
- Workbench items：36
- Pending workbench items：36
- High priority items：29
- Imported rows：0
- Rejected rows：36
- Valid proposed records：0
- Promotion candidates：0
- Ready action candidates：0
- Visual contract ready：true

解释：当前 UI 可以用于审阅，但 intake gate 仍然 blocked，因为真实 workbench 尚未填入 reviewer 结论。

## 严格边界

- 不接入 `rag_query` 主流程。
- 不调用后端 API 写入。
- 不覆盖原始 decision schema。
- 不修 hidden seed。
- 不新增或修改 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。

## 新增内容

- `tools/build_manual_review_visual_workbench_contract.py`
- `tests/test_manual_review_visual_workbench_contract.py`
- `tests/manual_review_visual_workbench_contract_report.json`

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_manual_review_visual_workbench_contract.py src\main.py
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench_contract
.\venv\Scripts\python.exe tools\build_manual_review_visual_workbench_contract.py --output tests\manual_review_visual_workbench_contract_report.json
```

Full Eval：本版本不运行。

## 后续影响

v0.4.7.8.1 可以在该契约之上实现静态本地 HTML dashboard。优先做只读 case list/detail 与 gate/status 展示；填写表单和导出功能留到后续小版本逐步加入。
