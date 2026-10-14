# v0.4.8.4 Final Evidence Selection Policy Closeout Envelope

本文件是最终证据选择 policy table 的人工收口外壳。它只把 v0.4.8.3 worksheet 转成待人工讨论的 closeout rows、候选收口路径和最低人工依据；它不记录正式人工结论，也不批准 runtime policy、rerank、prompt、eval case 或 RAG 主流程修改。

## Overview

- Closeout status: `pending_policy_table_human_closeout`
- Allowed use: `human_closeout_discussion_only`
- Closeout rows: 8
- Unique cases: 5
- Pending closeout rows: 8
- Next version recommendation: `v0.4.8.5 policy table human closeout decision draft`
- Implementation allowed: False
- Formal human outcome recorded: False
- Captures formal review outcome: False

## Input Contract

- `policy_human_review_worksheet`: `tests\final_evidence_selection_policy_human_review_worksheet_report.json` (version `0.4.8.3`)

## Closeout Rows

| Row | Policy | Category | Status | Candidate route | Recommended option |
|---|---|---|---|---|---|
| `FES-CLOSEOUT-001` | `FES-POLICY-DRAFT-001` | `primary` | `pending_human_closeout` | `future_offline_policy_simulation_primary_evidence_preservation` | `accept_for_future_offline_simulation_design` |
| `FES-CLOSEOUT-002` | `FES-POLICY-DRAFT-002` | `operative` | `pending_human_closeout` | `future_offline_policy_simulation_operative_rule_preservation` | `accept_for_future_offline_simulation_design` |
| `FES-CLOSEOUT-003` | `FES-POLICY-DRAFT-003` | `procedural` | `pending_human_closeout` | `future_offline_policy_simulation_procedural_evidence_preservation` | `accept_for_future_offline_simulation_design` |
| `FES-CLOSEOUT-004` | `FES-POLICY-DRAFT-004` | `liability` | `pending_human_closeout` | `future_offline_policy_simulation_liability_evidence_preservation` | `revise_policy_language_before_closeout` |
| `FES-CLOSEOUT-005` | `FES-POLICY-DRAFT-005` | `scenario_core` | `pending_human_closeout` | `scenario_core_article_review_before_runtime_policy` | `revise_policy_language_before_closeout` |
| `FES-CLOSEOUT-006` | `FES-POLICY-DRAFT-006` | `definition_only` | `pending_human_closeout` | `definition_only_substitution_guard_design` | `accept_for_future_offline_simulation_design` |
| `FES-CLOSEOUT-007` | `FES-POLICY-DRAFT-007` | `coverage_floor` | `pending_human_closeout` | `final_coverage_floor_review_design` | `revise_policy_language_before_closeout` |
| `FES-CLOSEOUT-008` | `FES-POLICY-DRAFT-008` | `high_risk_manual_review` | `pending_human_closeout` | `high_risk_gap_manual_review_gate_design` | `accept_for_future_offline_simulation_design` |

## Closeout Questions

### FES-POLICY-DRAFT-001 - primary
- Closeout question: 是否确认主证据保留规则可以进入后续离线模拟设计？
- Minimum human basis: 至少确认主证据已在候选层出现但未进入 final evidence，并确认替代依据边界不会过宽。

### FES-POLICY-DRAFT-002 - operative
- Closeout question: 是否确认义务、禁止、许可或合法性基础类规范条款必须被 final evidence 优先保留？
- Minimum human basis: 至少确认定义或背景条款不能替代 operative rule，并确认高风险输出需要规范条款支撑。

### FES-POLICY-DRAFT-003 - procedural
- Closeout question: 是否确认程序性证据应作为独立证据类别进入后续模拟？
- Minimum human basis: 至少确认告知、评估、申报、同意或申诉类依据不能被实体条款覆盖率自动替代。

### FES-POLICY-DRAFT-004 - liability
- Closeout question: 是否确认责任、后果、处罚、赔偿或救济依据缺失时必须进入人工复核？
- Minimum human basis: 至少确认高风险或责任判断需要直接后果依据，不能仅由义务条款支撑。

### FES-POLICY-DRAFT-005 - scenario_core
- Closeout question: 是否确认该 policy 需要先与 scenario core article review 保持边界一致？
- Minimum human basis: 至少确认场景核心条文缺失不能被相邻背景条款替代，且本版本不修改 scenario registry。

### FES-POLICY-DRAFT-006 - definition_only
- Closeout question: 是否确认 definition-only substitution guard 是独立策略防线？
- Minimum human basis: 至少确认定义条款只能辅助解释概念，不能单独支撑风险、整改、责任或后果结论。

### FES-POLICY-DRAFT-007 - coverage_floor
- Closeout question: 是否确认 coverage floor 应作为人工阻断信号，而不是自动通过条件？
- Minimum human basis: 至少确认覆盖率下降需要结合主争点、场景核心和规范功能解释。

### FES-POLICY-DRAFT-008 - high_risk_manual_review
- Closeout question: 是否确认高风险证据缺口必须先人工复核，不能直接 runtime adoption？
- Minimum human basis: 至少确认 high-risk gap 与任一 required quality signal 同时出现时必须保留人工入口。

## Closeout Options

- `accept_for_future_offline_simulation_design`: 人工确认该 policy 方向可进入后续离线模拟设计；仍不允许实现。
- `revise_policy_language_before_closeout`: 先调整 policy 文本或验收口径，再进入下一轮 closeout。
- `split_or_merge_policy_row_after_manual_review`: 人工认为该 policy 需要拆分、合并或重排后再继续。
- `defer_until_more_manual_cases_exist`: 当前 5 个 source case 不足以支持收口，等待更多人工复核材料。
- `close_without_followup`: 本轮关闭该 policy 方向，不生成工程任务。

## Boundaries

- 本 closeout envelope 只帮助人工收口讨论，不记录 formal review outcome。
- `implementation_allowed=false` 和 `code_patch_authorized=false` 必须保持不变。
- 不实现 runtime policy，不修改 final evidence selection runtime，不修改 rerank，不修改 prompt，不改 eval case。
- 不新增 anchor，不修 hidden seed，不改 risk supplement / term preservation / scenario registry / fixture / schema / importer / dry-run 契约。
- 不调用后端、Qdrant、LLM，不运行 full eval，不接入 RAG 主流程。

## Sources

- policy_human_review_worksheet: `tests\final_evidence_selection_policy_human_review_worksheet_report.json`
