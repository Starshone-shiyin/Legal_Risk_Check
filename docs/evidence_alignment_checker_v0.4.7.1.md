# Evidence Alignment Checker v0.4.7.1

## 定位

`tools/check_evidence_alignment.py` 是离线 RAG grounding quality diagnostics 工具。它只读取已经保存的评测报告和可选场景元数据，用于识别 evidence_chain 与风险结论之间的对齐质量问题。

本工具不是 hidden seed 修补器，也不参与运行时主链路。

## 严格边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不调用 LLM、embedding、Qdrant 或任何外部服务。

## 输入

- `tests/rag_eval_report.json`：默认必读输入。
- `tests/hidden_eval_report.json`：可选输入；不存在时跳过并记录到 `skipped_inputs`。
- `config/scenario_registry.json`：可选辅助输入，用于按 `eval_case_ids` 读取场景法域、核心条文和整改动作。

## 输出

默认输出到 `tests/evidence_alignment_report.json`，包含：

- 每个 case 的 `alignment_status`。
- 每个 case 的 `detected_issues`。
- 每个 case 的 `review_reasons`。
- `issue_type_summary`。
- `per_domain_summary`。
- `high_risk_manual_review`。

## 支持的质量信号

1. `domain_contamination`：证据来源法域与预期法域不一致。
2. `missing_primary_evidence`：场景核心条文或报告期望证据未被 evidence 覆盖。
3. `definition_only`：证据只命中定义类材料，缺少义务、程序、权利救济或责任类材料。
4. `answer_evidence_disconnect`：风险类型、整改动作或高风险结论缺少可见 evidence 文本支持。
5. `insufficient_evidence_coverage`：只覆盖少数主要证据，不能支撑主争点。
6. `review_reasons`：出现上述任一信号时，生成可供人工复核使用的原因。

## 使用方式

```powershell
.\venv\Scripts\python.exe tools\check_evidence_alignment.py `
  --rag-report tests\rag_eval_report.json `
  --hidden-report tests\hidden_eval_report.json `
  --scenario-registry config\scenario_registry.json `
  --output tests\evidence_alignment_report.json
```

如果希望在 CI 或发布门禁中遇到 review case 即失败，可追加：

```powershell
--fail-on-review
```

## 解释口径

该工具的输出是诊断信号，不是质量判决的最终法律结论。`review` 表示证据对齐存在需要人工复核的迹象，不代表原答案一定错误。

当前版本优先建立通用度量框架，而不是追求让所有现有报告通过。后续可在不修改 RAG 主链路的前提下，逐步增强法域映射、法条功能类型标注和 issue 覆盖模型。
