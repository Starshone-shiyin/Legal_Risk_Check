# Evidence Report Enrichment Hardening v0.4.7.4.1

## 定位

本版本属于 v0.4.7.4.x Evidence Quality Action Series。它对离线 evidence enrichment 做字段稳定性加固，目标是消除 v0.4.7.3.2 中唯一未命中的 final evidence。

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
- 不写回 ingestion metadata。

## 修复内容

v0.4.7.3.2 中唯一未命中 evidence：

- case：`standard_query_right_001`
- citation：`[《信息安全技术 个人信息安全规范》C.1 概述]`
- 原因：report 中 `section_no` 为空，但 citation 中包含标准章节位置；loader metadata 中该位置存于 `section_title`。

本版本新增：

- citation location fallback
- standard section title fallback
- hardening checker

## 当前报告摘要

- Total final evidence：180
- Matched evidence：180
- Unmatched evidence：0
- Matched ratio：1.0
- Missing required field counts：0
- Field stability：passed

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\check_evidence_coverage.py tools\check_evidence_enrichment_hardening.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_enrichment_hardening tests.test_evidence_coverage
.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --knowledge-manifest knowledge_manifest.json --functional-type-config config\legal_functional_types.json --output tests\evidence_coverage_report.json
.\venv\Scripts\python.exe tools\check_evidence_enrichment_hardening.py --coverage-report tests\evidence_coverage_report.json --output tests\evidence_enrichment_hardening_report.json
```
