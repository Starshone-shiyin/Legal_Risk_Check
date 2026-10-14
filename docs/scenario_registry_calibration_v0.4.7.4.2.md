# Scenario Registry Calibration v0.4.7.4.2

## 定位

本版本属于 v0.4.7.4.x Evidence Quality Action Series。目标是只读审计 `scenario_core_gap`，判断缺口更可能来自 registry core articles 过宽、final evidence 真实缺失，还是跨法域核心证据未进入 evidence chain。

这是 RAG grounding quality diagnostics，不是样本修补工具。

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不修改 `config/scenario_registry.json`。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/calibrate_scenario_registry_coverage.py`
- `tests/test_scenario_registry_calibration.py`
- `tests/scenario_registry_calibration_report.json`

## 支持的校准信号

- `registry_core_review_needed`：scenario core gap 需要人工校准。
- `core_missing_from_final_evidence`：scenario core article 未出现在 final evidence。
- `registry_core_scope_review_candidate`：final expected evidence 已覆盖，但 scenario core set 更宽。
- `evidence_chain_gap_candidate`：scenario core gap 与 final primary evidence 缺口重叠。
- `final_primary_gap_overlap`：scenario core gap 同时伴随 final primary gap。
- `cross_domain_core_gap`：缺失的 scenario core 法域未出现在 final evidence。
- `definition_core_candidate`：缺失的 core article 是 definition-only 候选，需判断是否应作为 core。
- `non_operative_core_candidate`：缺失的 core article 缺少义务、程序、责任、救济或技术标准支撑信号。
- `missing_scenario_mapping`：存在 scenario core gap 但找不到 registry 映射。

## 当前报告摘要

- Scenario core gap cases：8
- High-priority review cases：7
- Issue summary：
  - `registry_core_review_needed=8`
  - `core_missing_from_final_evidence=8`
  - `registry_core_scope_review_candidate=4`
  - `evidence_chain_gap_candidate=4`
  - `final_primary_gap_overlap=4`
  - `cross_domain_core_gap=2`
  - `definition_core_candidate=1`
- Domain summary：
  - 数据合规：6 review，5 high priority
  - 市场秩序：2 review，2 high priority

## 解释

本版本没有直接修改 scenario registry。报告显示 8 个 scenario core gap 中，4 个与 final primary gap 重叠，更像 evidence chain 真实缺口；另 4 个 final expected evidence 已覆盖，但 scenario core set 更宽，适合后续人工校准 registry core articles 的必要性。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\calibrate_scenario_registry_coverage.py
.\venv\Scripts\python.exe -m unittest tests.test_scenario_registry_calibration
.\venv\Scripts\python.exe tools\calibrate_scenario_registry_coverage.py --coverage-report tests\evidence_coverage_report.json --manual-review-dataset tests\evidence_manual_review_dataset.json --scenario-registry config\scenario_registry.json --output tests\scenario_registry_calibration_report.json
```
