# Evidence Quality Action Series Baseline v0.4.7.4.0

## 定位

本版本开启 v0.4.7.4.x Evidence Quality Action Series。它读取 v0.4.7.3.5 的 action plan，固化后续小版本执行顺序、输入依赖、输出文件和全局边界。

它不执行修复，不改变主链路。

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

## 执行顺序

1. `0.4.7.4.1` Evidence Report Enrichment Hardening
2. `0.4.7.4.2` Scenario Registry Calibration
3. `0.4.7.4.3` Base Retrieval Quality Audit
4. `0.4.7.4.4` Anchor Dependency Audit
5. `0.4.7.4.5` Final Evidence Selection Audit
6. `0.4.7.4.6` Manual Review Loop

## 当前报告摘要

- Total steps：6
- Planned action count：6
- Series：`0.4.7.4.x Evidence Quality Action Series`

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\build_evidence_action_series_baseline.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_action_series_baseline
.\venv\Scripts\python.exe tools\build_evidence_action_series_baseline.py --action-plan tests\evidence_root_cause_action_plan.json --output tests\evidence_action_series_baseline.json
```
