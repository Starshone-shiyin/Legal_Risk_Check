# v0.4.8.3 Final Evidence Selection Policy Human Review Worksheet

本文件是最终证据选择 policy table 的人工复核 worksheet。它只把 v0.4.8.2 的 8 条 policy row 转成审议问题、验收检查点和边界提示；它不记录正式人工结论，也不批准 runtime policy、rerank、prompt、eval case 或 RAG 主流程修改。

## Overview

- Worksheet status: `ready_for_policy_table_human_review_worksheet`
- Allowed use: `human_policy_review_discussion_only`
- Review rows: 8
- Unique cases: 5
- Next version recommendation: `v0.4.8.4 policy table human review closeout`
- Implementation allowed: False
- Runtime policy implementation allowed: False
- Captures formal review outcome: False

## Input Contract

- `policy_table_draft`: `tests\final_evidence_selection_policy_table_draft_report.json` (version `0.4.8.2`)

## Review Worksheet Rows

| Row | Policy | Category | Priority | Cases | Review goal |
|---|---|---|---|---:|---|
| `FES-WORKSHEET-REVIEW-001` | `FES-POLICY-DRAFT-001` | `primary` | P0 | 5 | 确认主证据保留规则是否足以防止核心法律依据在 final evidence 阶段流失。 |
| `FES-WORKSHEET-REVIEW-002` | `FES-POLICY-DRAFT-002` | `operative` | P0 | 4 | 确认义务、禁止、许可、合法性基础等规范条款不会被定义或背景条款替代。 |
| `FES-WORKSHEET-REVIEW-003` | `FES-POLICY-DRAFT-003` | `procedural` | P0 | 3 | 确认告知、评估、申报、同意、申诉等程序性证据被单独审议。 |
| `FES-WORKSHEET-REVIEW-004` | `FES-POLICY-DRAFT-004` | `liability` | P0 | 2 | 确认高风险、责任、处罚、赔偿或整改后果类结论有直接后果依据。 |
| `FES-WORKSHEET-REVIEW-005` | `FES-POLICY-DRAFT-005` | `scenario_core` | P1 | 4 | 确认场景核心条文缺失时，不会被相邻场景或背景证据误判为充分覆盖。 |
| `FES-WORKSHEET-REVIEW-006` | `FES-POLICY-DRAFT-006` | `definition_only` | P1 | 1 | 确认定义条款只能辅助解释概念，不能替代义务、程序、责任或后果依据。 |
| `FES-WORKSHEET-REVIEW-007` | `FES-POLICY-DRAFT-007` | `coverage_floor` | P1 | 2 | 确认 final evidence coverage 下降时，需要人工解释而不是自动通过。 |
| `FES-WORKSHEET-REVIEW-008` | `FES-POLICY-DRAFT-008` | `high_risk_manual_review` | P0 | 5 | 确认高风险缺口必须先人工复核，不能被离线 policy 草案直接转成实现任务。 |

## Review Questions

### FES-POLICY-DRAFT-001 - primary
- 该 policy 是否准确覆盖 primary evidence lost 的真实问题？
- 可接受替代依据是否必须同时满足同法域、同争点和同等规范功能？
- 主证据缺失时是否必须触发人工复核，而不是自动通过？

### FES-POLICY-DRAFT-002 - operative
- 该 policy 是否能区分 operative rule 与说明性材料？
- 当答案输出风险结论或整改动作时，是否要求 final evidence 保留对应规范条款？
- 缺少 operative rule 时是否应该阻断 runtime adoption？

### FES-POLICY-DRAFT-003 - procedural
- 该 policy 是否把程序性要求作为独立证据类型？
- 答案提出流程整改时，是否有对应程序依据？
- 程序条款缺失是否会被实体条款覆盖率掩盖？

### FES-POLICY-DRAFT-004 - liability
- 该 policy 是否应在高风险结论中强制检查 liability evidence？
- 责任条款缺失时，答案置信度或人工复核是否应受影响？
- 义务条款能否替代责任后果条款，边界是什么？

### FES-POLICY-DRAFT-005 - scenario_core
- 该 policy 是否能说明 scenario core evidence 的保留边界？
- 场景核心条文缺失时，是否允许同场景同争点替代？
- 是否需要把该问题留给后续 scenario core article review？

### FES-POLICY-DRAFT-006 - definition_only
- 该 policy 是否清楚阻断 definition-only substitution？
- 定义条款何时可以作为补充证据，而不是主证据？
- 复杂自动化决策或数据出境场景是否需要特别关注定义条款替代问题？

### FES-POLICY-DRAFT-007 - coverage_floor
- coverage floor 是否应该作为阻断信号，而不是普通提示？
- 覆盖率下降是否能区分主争点和次争点？
- 哪些 case 可以证明 coverage floor 不应单独决定通过？

### FES-POLICY-DRAFT-008 - high_risk_manual_review
- 该 policy 是否足以阻断高风险证据缺口的自动采纳？
- 人工复核需要看到哪些最小依据？
- 后续版本是否应先做 closeout，而不是直接实现？

## Acceptance Checks

- `FES-POLICY-DRAFT-001`: 触发条件能被 saved report 中的 case signal 复核。; 替代条件不会放宽到普通背景材料。; 高风险结论时仍保留人工复核入口。
- `FES-POLICY-DRAFT-002`: 至少能解释为什么义务或行为规范应被保留。; 不会把定义条款当作充分规范依据。; manual review trigger 与高风险输出一致。
- `FES-POLICY-DRAFT-003`: 程序证据不会被实体规则自动替代。; 审议项能覆盖告知、评估、申报、同意或申诉类问题。; 缺失时保留人工复核信号。
- `FES-POLICY-DRAFT-004`: 责任或后果判断不能仅由义务条款支撑。; 高风险输出必须进入人工复核清单。; 可接受替代必须覆盖同类责任、后果或救济路径。
- `FES-POLICY-DRAFT-005`: 不会把相邻背景条款当作场景核心条款。; 缺失解释必须能从 saved report 复核。; 不直接修改 scenario registry。
- `FES-POLICY-DRAFT-006`: 定义条款不得单独支撑风险结论。; 规范性条款缺失时必须保留人工复核信号。; 不会把定义条款提升为 runtime policy。
- `FES-POLICY-DRAFT-007`: 低覆盖率触发人工审议。; 覆盖率解释必须结合主争点、场景核心和功能类型。; 不直接改 rerank 或 final selection runtime。
- `FES-POLICY-DRAFT-008`: 高风险缺口必须保留 manual review required。; worksheet 不产生 completed manual decision。; 后续实现仍需要单独版本与明确授权。

## Boundaries

- 本 worksheet 只帮助人工审议 policy table，不记录 formal review outcome。
- `implementation_allowed=false` 和 `code_patch_authorized=false` 必须保持不变。
- 不实现 runtime policy，不修改 final evidence selection runtime，不修改 rerank，不修改 prompt，不改 eval case。
- 不新增 anchor，不修 hidden seed，不改 risk supplement / term preservation / scenario registry / fixture / schema / importer / dry-run 契约。
- 不调用后端、Qdrant、LLM，不运行 full eval，不接入 RAG 主流程。

## Sources

- policy_table_draft: `tests\final_evidence_selection_policy_table_draft_report.json`
