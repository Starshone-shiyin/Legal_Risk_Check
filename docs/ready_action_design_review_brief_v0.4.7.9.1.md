# v0.4.7.9.1 Ready Action Design Review Brief

本文件是给人工评审使用的简报。它把上一版设计包中的候选事项翻译成更容易审阅的评审方向、问题清单和退出标准。

它不修 RAG，不改检索、rerank、prompt、hidden seed、anchor、risk supplement、scenario registry、eval case、fixture 或主流程。

## 总览

- 状态：`ready_for_human_design_review`
- 来源设计包版本：`0.4.7.9.0`
- 可进入设计评审的候选事项：18
- 覆盖案例数：5
- 评审方向数：5
- 被排除的 pending records：31
- 是否允许实现：False

## 推荐评审顺序

| 顺序 | 优先级 | 评审方向 | 覆盖候选 | 覆盖案例 | 通俗解释 |
|---|---|---|---:|---:|---|
| 1 | P0 | 最终证据选择策略评审 | 5 | 5 | 系统最后留下哪些证据 |
| 2 | P0 | 主证据测试样例候选评审 | 5 | 5 | 以后可能拿来做测试样例的材料 |
| 3 | P0 | 高风险结论证据支撑评审 | 3 | 3 | 高风险判断有没有证据托住 |
| 4 | P1 | 场景核心条文范围评审 | 4 | 4 | 场景应该看哪些核心法律依据 |
| 5 | P1 | 法律功能类型样例评审 | 1 | 1 | 条文功能标签是否值得补样例 |

## 逐项评审

### 最终证据选择策略评审

- 优先级：`P0`
- 覆盖候选事项：5
- 覆盖案例：pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_app_location_ads_002, risk_employee_data_export_001, risk_employee_facial_001
- 关注点：确认关键法律条文是否在进入最终 evidence_chain 前被筛掉。
- 为什么重要：RAG 可能已经找到了重要条文，但最终答案只引用了次要证据。如果不先审这个方向，后续改样例或改规则都可能只是绕开问题。

需要问的问题：
- 关键条文是召回阶段没有出现，还是出现后没有进入最终证据链？
- 答案中的风险结论是否依赖了最终证据链没有保留的条文？
- 同一类问题是否需要统一的最终证据选择准入标准？

当前禁止：
- `rerank_change`
- `prompt_change`
- `runtime_selection_policy_patch`
- `eval_case_change`

进入后续实现前还需要：
- 实现前先定义 before/after 对照报告。
- 实现前先确认不会改 prompt、rerank、anchor 或 eval case。
- 实现后必须跑目标单测和小集合评估，不能只看单案表现。

### 主证据测试样例候选评审

- 优先级：`P0`
- 覆盖候选事项：5
- 覆盖案例：pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_app_location_ads_002, risk_employee_data_export_001, risk_employee_facial_001
- 关注点：确认哪些缺失证据适合作为未来测试样例候选，但现在不写入 eval。
- 为什么重要：fixture 可以帮助系统长期回归检查，但未经审议直接写入样例，会把当前诊断变成针对少数 case 的硬补丁。

需要问的问题：
- 候选证据是否真的是主争点所需证据，而不是补充性材料？
- 候选材料是否有清楚的来源 case、法律领域和复核理由？
- 它更适合作为测试样例、知识入库候选，还是人工复核备注？

当前禁止：
- `fixture_write_to_eval`
- `eval_case_change`
- `knowledge_base_mutation`
- `automatic_fixture_promotion`

进入后续实现前还需要：
- 实现前先新增候选池验收测试。
- 实现前先定义人工批准字段和回滚方式。
- 实现后必须证明没有修改现有 eval case。

### 高风险结论证据支撑评审

- 优先级：`P0`
- 覆盖候选事项：3
- 覆盖案例：risk_ai_medical_training_export_001, risk_app_location_ads_002, risk_employee_data_export_001
- 关注点：核对风险类型、整改动作和结论是否都有 evidence_chain 支撑。
- 为什么重要：企业风控报告里，高风险结论最容易影响决策。如果结论没有证据支撑，报告看起来完整但可信度会下降。

需要问的问题：
- 答案中的高风险结论对应了哪些具体证据？
- 整改动作是否能从证据链推出，还是只是模型自行补充？
- 是否需要人工标注哪些结论必须有强证据才能输出？

当前禁止：
- `risk_rule_change`
- `answer_policy_change`
- `prompt_change`
- `automatic_case_closure`

进入后续实现前还需要：
- 实现前先定义高风险结论的最小证据门槛。
- 实现前先准备人工复核样例和拒绝样例。
- 实现后必须跑风险报告和证据链一致性检查。

### 场景核心条文范围评审

- 优先级：`P1`
- 覆盖候选事项：4
- 覆盖案例：pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_employee_data_export_001, risk_employee_facial_001
- 关注点：确认 scenario registry 的核心条文范围是否需要人工复核，但现在不修改 registry。
- 为什么重要：场景清单决定系统认为某类问题应优先看哪些法律依据。这个方向很重要，但应先分清是清单范围问题、召回问题还是最终选择问题。

需要问的问题：
- 缺失条文是否属于该场景的核心依据，还是只是补充依据？
- 当前 case 的问题是否真的代表一个通用场景范围缺口？
- 是否需要法律复核人确认核心条文清单的边界？

当前禁止：
- `scenario_registry_change`
- `expected_evidence_change`
- `anchor_change`
- `eval_case_change`

进入后续实现前还需要：
- 实现前先有法律复核后的范围清单。
- 实现前先定义 registry 变更的回归测试。
- 实现后必须验证不会污染其他法域或场景。

### 法律功能类型样例评审

- 优先级：`P1`
- 覆盖候选事项：1
- 覆盖案例：risk_employee_facial_001
- 关注点：确认 legal functional typing 的样例候选是否需要后续评审。
- 为什么重要：legal functional typing 是 RAG 识别定义、义务、责任、程序等条文功能的基础设施。但本轮只有一个候选，应作为附属评审，不抢 P0。

需要问的问题：
- 候选条文的功能类型是否明确，例如义务、责任、程序或定义？
- 这个候选是否能帮助未来减少定义条款替代规范条款的问题？
- 是否需要先补人工标签规范，再考虑 golden fixture？

当前禁止：
- `functional_type_config_change`
- `golden_fixture_write`
- `eval_case_change`
- `automatic_label_change`

进入后续实现前还需要：
- 实现前先定义标签验收标准。
- 实现前先补测试，防止定义条款误替代规范条款。
- 实现后必须跑 typing fixture 检查。

## 术语

- `ready action candidates`：已具备进入设计评审条件的候选事项，不代表已经批准执行。
- `design track`：评审方向，用来把类似问题放在一起讨论。
- `grounding`：答案中的结论、风险和整改建议是否被证据链支撑。
- `fixture`：以后可能作为测试样例或回归检查材料的候选，不等于已经写入测试。
- `scenario registry`：场景与核心法律依据清单，用来帮助系统知道某类问题应关注哪些法律依据。
- `planning gate`：治理门禁；本轮只允许进入设计评审，不允许动手实现。

## 边界

- 本简报只读取上一版 ready action design pack。
- 31 个 pending records 只作为背景统计，不进入评审方向，也不是工程任务。
- 所有后续代码、配置或数据变更都必须另开版本、重新确认边界并补测试。
- Pending policy：Pending records are background only and must not enter this brief as tasks.

## 来源

- Source design pack：`tests\ready_action_design_pack_report.json`
