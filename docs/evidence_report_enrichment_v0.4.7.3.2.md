# Evidence Report Enrichment v0.4.7.3.2

## 定位

本版本属于 v0.4.7.3.x Evidence Coverage Quality Series。它补强离线 evidence coverage report 的可评价性，让 evidence item 不再只有 `source/article_no/citation`，而是可以带上本地知识文件中的正文预览和 legal functional type。

它不是主链路修复，也不是样本修补工具。

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

## 实现

`tools/check_evidence_coverage.py` 默认启用离线 enrichment：

1. 读取 `knowledge_manifest.json`。
2. 复用 ingestion loader 读取本地法规/标准文件。
3. 按 `source + article_no/section_no` 建立 evidence enrichment index。
4. 复用 `src/rag/legal_functional_typing.py` 对匹配正文做 functional type 分类。
5. 给 coverage report 中的 final evidence、layer evidence 和 scenario core evidence 补充：
   - `content_preview`
   - `functional_type`
   - `functional_type_confidence`
   - `functional_type_matched_rule`
   - `functional_type_matched_terms`
   - `enrichment_status`

可通过 `--no-enrichment` 关闭该行为，用于回归旧报告结构。

## 当前报告摘要

基于现有 `tests/rag_eval_report.json` 与 `knowledge_manifest.json`：

- Manifest documents：15
- Loaded documents：15
- Indexed keys：2387
- Missing files：0
- Final evidence items：180
- Enriched final evidence：179
- Enrichment matched ratio：`0.994`
- Functional coverage evaluable cases：60/60

Evidence coverage issue summary 保持不变：
- `anchor_dependent_coverage=33`
- `final_primary_gap=8`
- `scenario_core_gap=8`
- `layer_coverage_regression=7`
- `low_final_coverage=3`

Coverage loss triage 中 `functional_metadata_not_evaluable` 已消除，说明 v0.4.7.3.1 暴露的报告字段限制已经被修复。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\check_evidence_coverage.py tools\triage_evidence_coverage_loss.py src\main.py
.\venv\Scripts\python.exe -m unittest tests.test_evidence_coverage tests.test_evidence_coverage_triage
.\venv\Scripts\python.exe tools\check_evidence_coverage.py --rag-report tests\rag_eval_report.json --hidden-report tests\hidden_eval_report.json --scenario-registry config\scenario_registry.json --knowledge-manifest knowledge_manifest.json --functional-type-config config\legal_functional_types.json --output tests\evidence_coverage_report.json
.\venv\Scripts\python.exe tools\triage_evidence_coverage_loss.py --coverage-report tests\evidence_coverage_report.json --output tests\evidence_coverage_triage_report.json
```
