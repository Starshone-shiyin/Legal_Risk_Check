# Anchor Dependency Audit v0.4.7.4.4

## 定位

本版本属于 v0.4.7.4.x Evidence Quality Action Series。目标是只读审计 `anchor_dependency`，区分健康 anchor support 与 anchor masking weak base retrieval。

这是 RAG grounding quality diagnostics，不是 anchor 规则修补工具。

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 anchor 规则。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。
- 不调用 LLM、embedding、Qdrant 或 rerank。

## 新增内容

- `tools/audit_anchor_dependency.py`
- `tests/test_anchor_dependency_audit.py`
- `tests/anchor_dependency_audit_report.json`

## 支持的 anchor dependency 信号

- `anchor_dependency_review_needed`
- `healthy_anchor_support_candidate`
- `anchor_masking_base_retrieval_gap`
- `anchor_rescue_success`
- `partial_anchor_recovery`
- `zero_base_to_anchor_recovery`
- `high_anchor_gain`
- `anchor_supported_but_final_lost`
- `metadata_or_chunking_review_candidate`

## 当前报告摘要

- Anchor-dependency cases：33
- High-priority review cases：33
- Issue summary：
  - `anchor_masking_base_retrieval_gap=33`
  - `anchor_rescue_success=33`
  - `high_anchor_gain=33`
  - `metadata_or_chunking_review_candidate=33`
  - `zero_base_to_anchor_recovery=25`
  - `anchor_supported_but_final_lost=6`
- Anchor gain summary：
  - `gain_1_0=25`
  - `gain_0_5_to_0_999=8`

## 解释

当前 33 个 anchor dependency case 全部属于 anchor masking weak base retrieval，而不是健康补充型 anchor support。25 个 case 从 zero base recall 直接被 anchor 恢复到阈值以上，说明 anchor 在兜底，但也暴露基础召回层对 metadata、chunking、query lexical coverage 和 source/article 标识的一致性依赖过强。

本版本不新增或修改 anchor。报告的用途是帮助后续先处理基础召回质量，再判断是否需要更系统地治理 anchor 规则。

## 验证

```powershell
.\venv\Scripts\python.exe -m py_compile tools\audit_anchor_dependency.py
.\venv\Scripts\python.exe -m unittest tests.test_anchor_dependency_audit
.\venv\Scripts\python.exe tools\audit_anchor_dependency.py --coverage-report tests\evidence_coverage_report.json --triage-report tests\evidence_coverage_triage_report.json --base-audit-report tests\base_retrieval_quality_audit_report.json --output tests\anchor_dependency_audit_report.json
```
