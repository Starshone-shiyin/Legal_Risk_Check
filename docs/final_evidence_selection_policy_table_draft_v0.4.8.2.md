# v0.4.8.2 Final Evidence Selection Policy Table Draft

本文档是最终证据选择策略表草案。它只把 v0.4.8.1 saved-report simulator spec 中的 preservation、coverage、definition-only 和 manual-review 信号整理成人工可审阅的策略表；它不是 runtime policy 实现，也不修改 rerank、prompt、eval case 或 RAG 主流程。

## Overview

- Table status: `ready_for_manual_review_policy_table_draft`
- Allowed use: `offline_policy_table_draft_only`
- Confirmed cases: 5
- Policy table rows: 8
- Rows with case signal: 8
- Manual-review cases: 5
- Next version recommendation: `v0.4.8.3 policy table human review worksheet`
- Implementation allowed: False
- Runtime policy implementation allowed: False
- Rerank change allowed: False

## Input Contract

- `policy_simulator_spec`: `tests\final_evidence_selection_policy_simulator_spec_report.json` (version `0.4.8.1`)
- `policy_intake`: `tests\final_evidence_selection_policy_intake_report.json` (version `0.4.8.0`)
- `final_selection_audit`: `tests\final_evidence_selection_audit_report.json` (version `0.4.7.4.5`)
- `human_closeout_confirmation`: `tests\ready_action_human_closeout_confirmation_record_report.json` (version `0.4.7.9.6`)

## Policy Table Rows

| Policy | Category | Priority | Signal | Cases | Manual review trigger |
|---|---|---|---|---:|---|
| `FES-POLICY-DRAFT-001` | `primary` | P0 | `primary_evidence_should_be_preserved` | 5 | 主证据未进入 final evidence_chain，或替代依据的法域、争点、规范功能无法从保存报告中确认。 |
| `FES-POLICY-DRAFT-002` | `operative` | P0 | `operative_rule_should_be_preserved` | 4 | 答案存在风险结论或整改动作，但 final evidence_chain 缺少对应规范性条款。 |
| `FES-POLICY-DRAFT-003` | `procedural` | P0 | `procedural_evidence_should_be_preserved` | 3 | 答案提出整改流程、合规步骤或审查路径，但证据链缺少程序性依据。 |
| `FES-POLICY-DRAFT-004` | `liability` | P0 | `liability_evidence_should_be_preserved` | 2 | 答案存在高风险或责任判断，但 final evidence_chain 缺少直接责任/后果依据。 |
| `FES-POLICY-DRAFT-005` | `scenario_core` | P1 | `scenario_core_should_be_preserved_or_explained` | 4 | 场景核心条文缺失且无法从 saved report 中确认合理替代。 |
| `FES-POLICY-DRAFT-006` | `definition_only` | P1 | `definition_only_must_not_substitute_normative_evidence` | 1 | 答案结论依赖风险、整改、责任或合规动作，但证据链只有定义性支撑。 |
| `FES-POLICY-DRAFT-007` | `coverage_floor` | P1 | `final_coverage_floor_review_needed` | 2 | final evidence 只覆盖次要争点，或主要争点覆盖不足。 |
| `FES-POLICY-DRAFT-008` | `high_risk_manual_review` | P0 | `manual_review_required_for_high_risk_gap` | 5 | 高风险结论与任何 required quality signal 同时出现。 |

## Preservation Rules

| Policy | Preservation requirement | Acceptable substitution |
|---|---|---|
| `FES-POLICY-DRAFT-001` | 最终证据选择草案必须把主证据保留为优先检查对象；如未保留，必须说明可复核的替代依据。 | 只有同一法域、同一核心争点、同等或更强规范功能的证据可以作为替代候选。 |
| `FES-POLICY-DRAFT-002` | 最终证据选择草案必须保留能直接支撑结论的义务或行为规范条款。 | 替代证据必须同样表达可执行的义务、禁止、许可或合法性基础，不能只是背景说明。 |
| `FES-POLICY-DRAFT-003` | 最终证据选择草案必须把程序性要求作为独立证据类型保留或解释。 | 替代证据必须覆盖相同程序环节，且能支撑整改步骤或合规流程。 |
| `FES-POLICY-DRAFT-004` | 最终证据选择草案必须保留责任或后果条款，尤其是答案给出高风险结论时。 | 替代证据必须直接覆盖同类责任、后果或救济路径。 |
| `FES-POLICY-DRAFT-005` | 最终证据选择草案必须保留场景核心条文，或输出可人工复核的缺失解释。 | 替代证据必须覆盖同一场景核心争点，不能只覆盖相邻背景问题。 |
| `FES-POLICY-DRAFT-006` | 最终证据选择草案必须区分定义条款与义务、程序、责任、后果条款。 | 定义条款只能辅助解释；只有同时存在规范性条款时才可作为补充证据。 |
| `FES-POLICY-DRAFT-007` | 最终证据选择草案必须把覆盖率下降作为阻断人工复核信号，而不是自动通过。 | 只有主要争点、场景核心和规范功能均可从保存报告中确认时，才可解释覆盖下降。 |
| `FES-POLICY-DRAFT-008` | 最终证据选择草案必须把高风险缺口列入人工复核清单。 | 高风险缺口不得仅由自动策略解释；必须保留人工复核入口。 |

## Manual Review Gate

- Status: `manual_review_required_before_runtime_policy`
- Policy rows requiring review: 8
- High-risk manual-review cases: 5
- Policy table draft allowed: True
- Runtime policy adoption allowed without review: False

## Boundaries

- 本版本是 RAG grounding quality governance 的 saved-report policy table draft，不是样本修补工具。
- 不实现 runtime policy，不修改 final evidence selection runtime，不修改 rerank，不修改 prompt，不改 eval case。
- 不新增 anchor，不修 hidden seed，不改 risk supplement / term preservation / scenario registry / fixture / schema / importer / dry-run 契约。
- 不调用后端、Qdrant、LLM，不运行 full eval，不接入 RAG 主流程。

## Sources

- policy_simulator_spec: `tests\final_evidence_selection_policy_simulator_spec_report.json`
- policy_intake: `tests\final_evidence_selection_policy_intake_report.json`
- final_selection_audit: `tests\final_evidence_selection_audit_report.json`
- human_closeout_confirmation: `tests\ready_action_human_closeout_confirmation_record_report.json`
