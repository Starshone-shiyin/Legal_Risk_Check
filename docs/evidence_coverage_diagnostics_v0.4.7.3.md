# Evidence Coverage Diagnostics v0.4.7.3

## 定位

本版本新增离线 evidence coverage diagnostics，用于观察 RAG grounding quality 中的证据覆盖问题。它不是 hidden seed 修补工具，也不是召回、rerank、prompt 或风险补全策略的一部分。

工具只读取已有报告和 metadata：
- `tests/rag_eval_report.json`
- `tests/hidden_eval_report.json`（可选，不存在则跳过）
- `config/scenario_registry.json`（可选辅助 scenario core articles / domain 判断）

输出：
- `tests/evidence_coverage_report.json`

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不运行 full eval；只读取已有 eval report。

## 支持的诊断信号

- `final_primary_gap`：final evidence_chain 未覆盖 final expected statutes。
- `scenario_core_gap`：final evidence_chain 未覆盖 scenario registry 中标注的 core articles。
- `operative_support_gap`：当 evidence 可评价时，final evidence_chain 缺少义务、程序、责任、权利救济或技术标准支撑。
- `functional_type_gap`：当 evidence 可评价时，final evidence_chain 没有可识别的法律功能类型信号。
- `anchor_dependent_coverage`：expected coverage 在 anchor 层之后才明显改善，提示召回对 anchor 依赖较强。
- `layer_coverage_regression`：rerank_input 覆盖高于 final 覆盖，提示 final 截断或排序后的证据选择存在流失。
- `low_final_coverage`：final 层 expected evidence 覆盖率低于阈值。

当 evidence item 缺少正文或 `functional_type` metadata 时，functional type coverage 会记录为 `evaluable=false`，不会把不可评价样本误报为功能类型缺口。

## 当前报告摘要

基于现有 `tests/rag_eval_report.json`：

- Total cases：60
- OK cases：24
- Review cases：36
- Optional hidden report：`tests\hidden_eval_report.json` 不存在，已跳过

Issue summary：
- `anchor_dependent_coverage=33`
- `final_primary_gap=8`
- `scenario_core_gap=8`
- `layer_coverage_regression=7`
- `low_final_coverage=3`

Layer summary：
- dense：`14/104=0.135`
- sparse：`38/104=0.365`
- union：`39/104=0.375`
- anchor：`103/104=0.99`
- rerank_input：`103/104=0.99`
- final：`95/104=0.913`

解释：final 层整体覆盖率较高，但 anchor 依赖明显；同时有少量 expected/core articles 从 rerank_input 到 final 发生覆盖流失。因此下一步应优先做 coverage loss triage，而不是直接修改 prompt、rerank、anchor 或 risk supplement。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\check_evidence_coverage.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage
.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --output tests\evidence_coverage_report.json
```
