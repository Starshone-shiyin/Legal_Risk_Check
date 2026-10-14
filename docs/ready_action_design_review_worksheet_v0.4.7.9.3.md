# v0.4.7.9.3 Ready Action Design Review Worksheet

本文件是人工设计评审用的 worksheet。它把 5 条设计轨道整理成可审阅清单，但不记录正式人工结论，也不批准任何代码、配置、样例或主流程修改。

## 总览

- Worksheet status: `ready_for_human_design_review_matrix`
- Allowed use: `human_design_review_discussion_only`
- Review tracks: 5
- Design actions: 18
- Source cases: 5
- Pending records excluded: 31
- Implementation allowed: False
- Code patch authorized: False
- Captures formal review outcome: False

## Review Matrix

| Order | Priority | Track | Plain meaning | Candidates | Next series | Status |
|---:|---|---|---|---:|---|---|
| 1 | P0 | 最终证据选择策略评审 | 最后到底该留下哪些证据 | 5 | v0.4.8.x | `ready_for_human_design_review` |
| 2 | P0 | 主证据测试样例候选评审 | 哪些材料以后可作为测试样例候选 | 5 | fixture governance | `ready_for_human_design_review` |
| 3 | P0 | 高风险结论证据支撑评审 | 高风险结论有没有证据托住 | 3 | manual grounding review | `ready_for_human_design_review` |
| 4 | P1 | 场景核心条文范围评审 | 场景应该绑定哪些核心条文 | 4 | scenario core article review | `ready_for_human_design_review` |
| 5 | P1 | 法律功能类型样例评审 | 法律功能类型标签是否可靠 | 1 | legal functional typing fixture review | `ready_for_human_design_review` |

## Human Review Questions

### 1. 最终证据选择策略评审

- 核心问题：这些 case 的关键证据是否已经进入候选池，但没有进入最终 evidence_chain？
- 评审目标：判断问题是否属于最终证据选择策略，而不是召回、场景范围或提示词问题。
- 可能后续：`v0.4.8.x` / Final evidence selection policy design
- 实现前提：先形成经人工确认的策略草案和 simulator 验证计划。
- 需要讨论：
  - 关键条文是召回阶段没有出现，还是出现后没有进入最终证据链？
  - 答案中的风险结论是否依赖了最终证据链没有保留的条文？
  - 同一类问题是否需要统一的最终证据选择准入标准？
- 当前禁止：
  - `rerank_change`
  - `prompt_change`
  - `runtime_selection_policy_patch`
  - `eval_case_change`

### 2. 主证据测试样例候选评审

- 核心问题：这些候选是否能代表通用主证据缺口，而不是单案补丁？
- 评审目标：判断候选证据是否真是主争点证据，以及是否适合进入 fixture governance。
- 可能后续：`fixture governance` / Primary evidence fixture candidate review
- 实现前提：先有人工确认的候选池规则，不直接写入 eval case 或 golden fixture。
- 需要讨论：
  - 候选证据是否真的是主争点所需证据，而不是补充性材料？
  - 候选材料是否有清楚的来源 case、法律领域和复核理由？
  - 它更适合作为测试样例、知识入库候选，还是人工复核备注？
- 当前禁止：
  - `fixture_write_to_eval`
  - `eval_case_change`
  - `knowledge_base_mutation`
  - `automatic_fixture_promotion`

### 3. 高风险结论证据支撑评审

- 核心问题：高风险结论是否能被当前 evidence_chain 直接支撑？
- 评审目标：判断风险类型、整改动作或结论是否需要更强的人工 grounding 规则。
- 可能后续：`manual grounding review` / High-risk manual grounding review design
- 实现前提：先拆清风险类型、整改动作和法律后果各自的最小证据要求。
- 需要讨论：
  - 答案中的高风险结论对应了哪些具体证据？
  - 整改动作是否能从证据链推出，还是只是模型自行补充？
  - 是否需要人工标注哪些结论必须有强证据才能输出？
- 当前禁止：
  - `risk_rule_change`
  - `answer_policy_change`
  - `prompt_change`
  - `automatic_case_closure`

### 4. 场景核心条文范围评审

- 核心问题：缺失条文是否真是该场景的核心依据？
- 评审目标：判断问题是否属于 scenario registry 核心条文范围，而不是最终证据选择问题。
- 可能后续：`scenario core article review` / Scenario registry core article design review
- 实现前提：先形成只读条文范围清单，不直接修改 scenario registry。
- 需要讨论：
  - 缺失条文是否属于该场景的核心依据，还是只是补充依据？
  - 当前 case 的问题是否真的代表一个通用场景范围缺口？
  - 是否需要法律复核人确认核心条文清单的边界？
- 当前禁止：
  - `scenario_registry_change`
  - `expected_evidence_change`
  - `anchor_change`
  - `eval_case_change`

### 5. 法律功能类型样例评审

- 核心问题：该条文的定义、义务、责任或程序功能是否足够明确？
- 评审目标：判断候选是否适合沉淀为 legal functional typing fixture，而不是直接改 config。
- 可能后续：`legal functional typing fixture review` / Functional typing fixture design review
- 实现前提：先明确条文功能类型和人工标签规范，再考虑 fixture。
- 需要讨论：
  - 候选条文的功能类型是否明确，例如义务、责任、程序或定义？
  - 这个候选是否能帮助未来减少定义条款替代规范条款的问题？
  - 是否需要先补人工标签规范，再考虑 golden fixture？
- 当前禁止：
  - `functional_type_config_change`
  - `golden_fixture_write`
  - `eval_case_change`
  - `automatic_label_change`

## Boundaries

- 本 worksheet 只帮助人工评审设计方向，不记录正式人工结论。
- `implementation_allowed=false` 和 `code_patch_authorized=false` 必须保持不变。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约或 RAG 主流程。
- 后续若进入 v0.4.8.x、v0.4.9.x 或 fixture governance，必须另开版本并重新确认边界。

## Sources

- Gate report: `tests\ready_action_design_review_gate_report.json`
- Brief report: `tests\ready_action_design_review_brief_report.json`
