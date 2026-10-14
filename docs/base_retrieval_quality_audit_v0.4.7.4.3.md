# Base Retrieval Quality Audit v0.4.7.4.3

## 定位

本版本属于 v0.4.7.4.x Evidence Quality Action Series。目标是只读审计 dense、sparse、union 三个基础召回层的 evidence coverage，不触碰 anchor、rerank、prompt 或风险输出。

这是 RAG grounding quality diagnostics，不是检索调参或样本修补工具。

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

## 新增内容

- `tools/audit_base_retrieval_quality.py`
- `tests/test_base_retrieval_quality_audit.py`
- `tests/base_retrieval_quality_audit_report.json`

## 支持的基础召回质量信号

- `base_retrieval_review_needed`
- `dense_retrieval_gap`
- `sparse_retrieval_gap`
- `union_retrieval_gap`
- `zero_base_recall`
- `sparse_only_support`
- `dense_only_support`
- `no_union_gain`
- `anchor_rescue_pattern`
- `metadata_or_chunking_review_candidate`
- `index_or_source_coverage_review_candidate`

## 当前报告摘要

- Base-gap cases：34
- High-priority review cases：34
- Layer gap summary：
  - `dense_gap_cases=34`
  - `sparse_gap_cases=34`
  - `union_gap_cases=34`
- Issue summary：
  - `zero_base_recall=25`
  - `anchor_rescue_pattern=33`
  - `metadata_or_chunking_review_candidate=33`
  - `no_union_gain=34`
  - `index_or_source_coverage_review_candidate=1`
  - `sparse_only_support=6`
  - `dense_only_support=1`
- Missing union evidence source summary 以个人信息保护法为主，其次为增值税法、民法典、公司法、反垄断法等。

## 解释

当前基础召回问题不是单一 dense 或 sparse 的小幅偏差，而是 dense/sparse/union 对 expected evidence 的覆盖整体偏低。33 个 case 能被 anchor 层恢复，说明后续应优先审计 metadata、chunking、查询词面覆盖和 source/article 标识一致性；只有 1 个 case 在 anchor 后仍不足，更适合进入 source/index coverage review。

本版本不修改召回逻辑。它只把“基础召回缺口”拆成可复核的诊断桶，为后续是否需要 ingestion metadata、chunking 或检索配置治理提供依据。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\audit_base_retrieval_quality.py
.\venv\Scripts\python.exe -m unittest tests.test_base_retrieval_quality_audit
.\venv\Scripts\python.exe tools\audit_base_retrieval_quality.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --output tests\base_retrieval_quality_audit_report.json
```
