# v0.4.8.1 Final Evidence Selection Policy Simulator Spec

本文档是最终证据选择策略模拟器的离线契约。它只定义未来 saved-report simulator 应如何读取既有报告、输出质量信号和触发人工复核；它不是 runtime policy 实现，也不是 rerank、prompt、eval case 或 RAG 主流程修复。

## Overview

- Spec status: `ready_for_offline_policy_simulator_spec`
- Allowed use: `offline_policy_simulator_spec_only`
- Confirmed cases: 5
- Policy candidate categories: 6
- Failure signals: 8
- Manual-review cases: 5
- Next version recommendation: `v0.4.8.2 policy table draft`
- Implementation allowed: False
- Runtime policy implementation allowed: False
- Rerank change allowed: False

## Input Contract

- `policy_intake`: `tests\final_evidence_selection_policy_intake_report.json` (version `0.4.8.0`)
- `final_selection_audit`: `tests\final_evidence_selection_audit_report.json` (version `0.4.7.4.5`)
- `human_closeout_confirmation`: `tests\ready_action_human_closeout_confirmation_record_report.json` (version `0.4.7.9.6`)

## Policy Candidate Categories

| Category | Signal | Purpose |
|---|---|---|
| `primary` | `primary_evidence_should_be_preserved` | 核心法条已经进入候选层时，模拟器必须检查它是否进入 final evidence_chain，或是否存在可解释替代。 |
| `operative` | `operative_rule_should_be_preserved` | 义务、禁止、许可、合法性基础等规范性条款不能被背景性材料替代。 |
| `procedural` | `procedural_evidence_should_be_preserved` | 告知、评估、申报、同意、程序步骤等证据必须被单独识别，不能被结论性回答概括掉。 |
| `liability` | `liability_evidence_should_be_preserved` | 答案涉及处罚、赔偿、整改责任或高风险结论时，必须检查责任/后果条款是否被保留。 |
| `scenario_core` | `scenario_core_should_be_preserved_or_explained` | 场景核心条文丢失时，模拟器必须输出保留要求或解释性人工复核信号。 |
| `definition_only` | `definition_only_must_not_substitute_normative_evidence` | 定义条款只能辅助解释，不能替代义务、责任、程序或后果条款支撑最终结论。 |

## Case Spec Matrix

| Case | Risk | Domains | Required signals | Simulator status |
|---|---|---|---|---|
| `pipl_data_export_conditions_001` | high | 数据合规 | primary_evidence_should_be_preserved, operative_rule_should_be_preserved, procedural_evidence_should_be_preserved, liability_evidence_should_be_preserved, scenario_core_should_be_preserved_or_explained, final_coverage_floor_review_needed, manual_review_required_for_high_risk_gap | `manual_review_required_before_runtime_policy` |
| `risk_ai_medical_training_export_001` | high | 数据合规 | primary_evidence_should_be_preserved, operative_rule_should_be_preserved, procedural_evidence_should_be_preserved, scenario_core_should_be_preserved_or_explained, manual_review_required_for_high_risk_gap | `manual_review_required_before_runtime_policy` |
| `risk_app_location_ads_002` | high | 数据合规 | primary_evidence_should_be_preserved, operative_rule_should_be_preserved, manual_review_required_for_high_risk_gap | `manual_review_required_before_runtime_policy` |
| `risk_employee_data_export_001` | high | 市场秩序, 数据合规 | primary_evidence_should_be_preserved, liability_evidence_should_be_preserved, scenario_core_should_be_preserved_or_explained, definition_only_must_not_substitute_normative_evidence, final_coverage_floor_review_needed, manual_review_required_for_high_risk_gap | `manual_review_required_before_runtime_policy` |
| `risk_employee_facial_001` | high | 数据合规 | primary_evidence_should_be_preserved, operative_rule_should_be_preserved, procedural_evidence_should_be_preserved, scenario_core_should_be_preserved_or_explained, manual_review_required_for_high_risk_gap | `manual_review_required_before_runtime_policy` |

## Failure Signals

| Signal | Severity | Review reason |
|---|---|---|
| `primary_evidence_should_be_preserved` | P0 | 主证据已进入前序候选层但没有进入最终证据链，可能导致核心法律依据缺失。 |
| `operative_rule_should_be_preserved` | P0 | 义务、禁止、合法性基础等规范性条款丢失，答案可能只剩结论而缺少规则支撑。 |
| `procedural_evidence_should_be_preserved` | P0 | 程序性要求丢失，可能影响整改动作、合规步骤和审查路径。 |
| `liability_evidence_should_be_preserved` | P0 | 责任或后果条款丢失，高风险结论可能缺少直接法律后果支撑。 |
| `scenario_core_should_be_preserved_or_explained` | P1 | 场景核心条文未进入最终证据链，需要确认是选择策略流失还是场景范围需要复核。 |
| `definition_only_must_not_substitute_normative_evidence` | P1 | 定义条款不能替代义务、程序、责任或后果条款，需要人工确认最终证据是否支撑结论。 |
| `final_coverage_floor_review_needed` | P1 | 最终证据覆盖率过低，需要进入人工复核或阻断后续策略草案。 |
| `manual_review_required_for_high_risk_gap` | P0 | 高风险结论下存在证据保留缺口，策略草案前必须人工复核。 |

## Manual Review Gate

- Status: `manual_review_required_before_runtime_policy`
- Manual-review required count: 5
- Design policy table draft allowed: True
- Runtime policy adoption allowed without review: False

## Boundaries

- 本版本是 RAG grounding quality governance 的 saved-report simulator spec，不是样本修补工具。
- 不实现 runtime policy，不修改 final evidence selection runtime，不修改 rerank，不修改 prompt，不改 eval case。
- 不新增 anchor，不修 hidden seed，不改 risk supplement / term preservation / scenario registry / fixture / schema / importer / dry-run 契约。
- 不调用后端、Qdrant、LLM，不运行 full eval，不接入 RAG 主流程。

## Sources

- policy_intake: `tests\final_evidence_selection_policy_intake_report.json`
- final_selection_audit: `tests\final_evidence_selection_audit_report.json`
- human_closeout_confirmation: `tests\ready_action_human_closeout_confirmation_record_report.json`
