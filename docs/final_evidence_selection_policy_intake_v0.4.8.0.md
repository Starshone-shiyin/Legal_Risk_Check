# v0.4.8.0 Final Evidence Selection Policy Design Intake

本文件是 v0.4.8.x 最终证据选择策略设计系列的入口材料。它只整理已确认的 final evidence selection loss 和既有审计信号，不实现策略、不修改 rerank、不接入主流程。

## Overview

- Intake status: `ready_for_policy_design_intake`
- Allowed use: `final_evidence_selection_policy_design_input_only`
- Confirmed next series: `v0.4.8.x`
- Confirmed cases: 5
- Design actions: 5
- Audit high-priority cases: 5
- Preservation discussion items: 6
- Policy questions: 6
- Implementation allowed: False
- Rerank change allowed: False
- Runtime selection policy patch allowed: False

## Policy Questions

- `primary_evidence_preservation` (P0): 已经进入候选池的主证据，什么情况下必须进入 final evidence_chain？
- `operative_and_procedural_preservation` (P0): 义务、程序、权利或技术支撑类条文是否需要比背景性条文更高的保留优先级？
- `liability_and_consequence_preservation` (P0): 答案涉及处罚、赔偿、责任后果或高风险结论时，是否必须保留责任/后果支撑条款？
- `scenario_core_preservation` (P1): 场景核心条文已进入前序候选层时，final evidence 是否必须保留或给出可解释替代？
- `definition_clause_substitution_guard` (P1): 定义条款是否只能补充解释，不能替代义务、程序、责任或后果条款？
- `final_coverage_floor` (P1): final evidence coverage 低于什么诊断阈值时，必须进入人工复核或 simulator 失败状态？

## Preservation Discussion Items

| Item | Priority | Signals | Design Input |
|---|---|---|---|
| `preserve_primary_evidence` | P0 | primary_evidence_lost, rerank_input_to_final_loss | 主证据如果已在 rerank_input 出现，policy 草案需定义保留或替代解释条件。 |
| `preserve_operative_rule_evidence` | P0 | operative_evidence_lost, operative_rule | 义务、行为规则或合法性基础类证据需要进入 preservation rule 讨论。 |
| `preserve_procedural_evidence` | P0 | procedural | 程序、告知、评估、申报等条款不能被泛化结论替代。 |
| `preserve_liability_evidence` | P0 | liability_evidence_lost, liability | 答案涉及责任、处罚、赔偿或后果时，需要讨论责任条款的保留底线。 |
| `preserve_scenario_core_evidence` | P1 | scenario_core_lost | 场景核心证据丢失需要和 scenario core review 分界，但 policy intake 必须记录该风险。 |
| `final_coverage_safety_floor` | P1 | low_final_coverage_after_selection | final evidence coverage 过低时，后续 simulator 应输出失败或人工复核信号。 |

## Case Intake Matrix

| Case | Priority | Risk | Issues | Lost Evidence | Status |
|---|---|---|---|---:|---|
| `pipl_data_export_conditions_001` | high | high | final_selection_review_needed, rerank_input_to_final_loss, primary_evidence_lost, scenario_core_lost, operative_evidence_lost, low_final_coverage_after_selection | 1 | `policy_design_input_ready` |
| `risk_ai_medical_training_export_001` | high | high | final_selection_review_needed, rerank_input_to_final_loss, anchor_supported_but_final_lost, primary_evidence_lost, scenario_core_lost, operative_evidence_lost | 1 | `policy_design_input_ready` |
| `risk_app_location_ads_002` | high | high | final_selection_review_needed, rerank_input_to_final_loss, anchor_supported_but_final_lost, primary_evidence_lost, operative_evidence_lost | 1 | `policy_design_input_ready` |
| `risk_employee_data_export_001` | high | high | final_selection_review_needed, rerank_input_to_final_loss, anchor_supported_but_final_lost, primary_evidence_lost, scenario_core_lost, liability_evidence_lost, low_final_coverage_after_selection | 2 | `policy_design_input_ready` |
| `risk_employee_facial_001` | high | high | final_selection_review_needed, rerank_input_to_final_loss, anchor_supported_but_final_lost, primary_evidence_lost, scenario_core_lost, operative_evidence_lost | 1 | `policy_design_input_ready` |

## Simulator Plan

- Recommended next version: `v0.4.8.1`
- Plan status: `design_plan_only`
- Runtime integration allowed: False
- Input policy: `saved_reports_only`

## Boundaries

- 本 intake 不是策略实现、rerank 修复、selection policy patch 或主流程接入。
- `implementation_allowed=false`、`code_patch_authorized=false`、`rerank_change_allowed=false` 必须保持不变。
- 不修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer 或 dry-run 契约。
- 不调用后端、Qdrant、LLM，不运行 full eval，不接入 RAG 主流程。

## Sources

- confirmation_record: `tests\ready_action_human_closeout_confirmation_record_report.json`
- decision_draft: `tests\ready_action_human_closeout_decision_draft_report.json`
- closeout_envelope: `tests\ready_action_design_review_closeout_report.json`
- worksheet: `tests\ready_action_design_review_worksheet_report.json`
- design_pack: `tests\ready_action_design_pack_report.json`
- final_selection_audit: `tests\final_evidence_selection_audit_report.json`
