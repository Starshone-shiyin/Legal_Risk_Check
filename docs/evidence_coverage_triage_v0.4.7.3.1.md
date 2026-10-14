# Coverage Loss Triage v0.4.7.3.1

## 定位

本版本属于 v0.4.7.3.x Evidence Coverage Quality Series。它读取 v0.4.7.3 生成的 `tests/evidence_coverage_report.json`，对 review cases 做离线二次归因。

它不是样本修补工具，也不是主链路策略变更。目标是回答：coverage 问题更像基础召回不足、anchor 依赖、final evidence 选择流失，还是 scenario core evidence 缺口。

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## Root Causes

- `base_retrieval_gap`：union 层覆盖率低于诊断阈值，提示 dense/sparse 基础召回不足。
- `anchor_dependency`：anchor 层覆盖率高于 union 层，提示 expected evidence 依赖 anchor 才进入候选。
- `final_selection_loss`：rerank_input 覆盖率高于 final 覆盖率，提示 final evidence 选择发生覆盖流失。
- `final_primary_gap`：final evidence_chain 缺少 final expected statutes。
- `scenario_core_gap`：final evidence_chain 缺少 scenario registry core articles。
- `low_final_coverage`：final 覆盖率低于诊断阈值。
- `functional_metadata_not_evaluable`：evidence 缺少正文或 functional type metadata，导致 functional coverage 暂不可评价。
- `functional_support_gap`：当 evidence 可评价时，缺少规范性/程序性/责任性等支撑。

`functional_metadata_not_evaluable` 是报告字段限制。仅该项存在时不会触发 review，避免把 metadata 缺口误判为法律证据缺口。

## 当前报告摘要

基于 `tests/evidence_coverage_report.json`：

- Total cases：60
- OK：24
- Review：24
- High-priority review：12

Root cause summary：
- `base_retrieval_gap=34`
- `anchor_dependency=33`
- `final_primary_gap=8`
- `scenario_core_gap=8`
- `final_selection_loss=7`
- `low_final_coverage=3`
- `functional_metadata_not_evaluable=60`

Coverage flow summary：
- `low_union_coverage_cases=34`
- `anchor_improved_cases=33`
- `final_selection_loss_cases=7`

解释：当前最主要问题不是 prompt 或风险补全输出，而是基础召回覆盖不足和 anchor 依赖；同时少量 high-priority cases 出现 rerank_input 到 final 的覆盖流失。下一步应先补强离线报告字段和人工归因样本，再决定是否需要主链路改动。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\triage_evidence_coverage_loss.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage_triage
.\venv\Scripts\python.exe tools\triage_evidence_coverage_loss.py --coverage-report tests\evidence_coverage_report.json --output tests\evidence_coverage_triage_report.json
```
