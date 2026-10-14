# Legal Issue Hierarchy Plan v0.4.7.0

## 定位

v0.4.7.0 是 hidden eval / 企业复杂场景层的设计稿版本。本版本不修改 `rag_query` 主链路，不改变检索、rerank、anchor、risk supplement 或术语保真行为，也不运行评测。目标是把真实手工测试暴露的问题抽象为“法律依据控制系统”的离线设计。

当前 7 条 hidden eval seed 显示：系统已经具备较强的复杂合规推理能力，但 evidence_chain 不能稳定支撑推理结论。核心问题不再只是召回不到，而是法律领域、争点层级、法条功能类型和证据覆盖之间缺少控制。

```text
complex fact → domain routing → issue hierarchy → functional typing → evidence coverage → confidence
```

## 问题归纳

### 1. Syntactic Grounding 不等于 Legal Grounding

当前 citation integrity 主要检查“引用是否来自 evidence_chain”。但 hidden seed 已经证明：即使 citation integrity 通过，evidence_chain 本身也可能在法律上不适用。

典型样本：
- `seed_006_fintech_cross_border_antifraud_scoring`：答案正确提到个保法第24、38、39条，但 evidence_chain 混入公司法第189条、第57条。
- `seed_007_cross_border_ecommerce_after_sales_scoring`：答案正确识别自动化决策和消费者权益，但 evidence_chain 主要覆盖出境规则和安全事件条款。

### 2. Legal Domain Contamination

复杂事实中的“公司、集团、总部、风控、安全”等词会把检索拉向错误法域。

需要识别并约束：
- 数据合规场景不应让公司治理条款进入 top evidence。
- 自动化决策场景不应因“算法/平台”误召回反不正当竞争法网络竞争条款。
- 风控场景不应因“安全”误召回安全事件处置条款作为主证据。

### 3. Issue Hierarchy Failure

系统能识别问题，但不会区分主争点、次争点和边缘争点。

例如跨境电商售后风控：

```json
{
  "primary_issues": [
    "automated_decision",
    "cross_border_transfer",
    "separate_consent",
    "human_review",
    "consumer_rights"
  ],
  "secondary_issues": [
    "data_retention",
    "device_fingerprint",
    "security_audit"
  ],
  "peripheral_issues": [
    "incident_response"
  ]
}
```

如果 evidence_chain 只覆盖 secondary/peripheral issues，不应给出高置信度法律结论。

### 4. Definition 条文替代 Operative Rule

在线教育 AI 评分样本中，系统召回了个保法第73条“自动化决策定义”，但没有召回第24条“自动化决策义务”。这说明系统缺少 legal functional typing。

```text
definition != operative_rule
```

定义条款可以辅助解释概念，但不能替代行为规范条款作为结论依据。

### 5. Answer Generation 强于 Evidence Control

多个样本中，LLM 能生成正确的法律分析，但 evidence_chain 没有对应条文支撑。这是高风险状态：

```text
reasoning_confidence 高
evidence_confidence 低
retrieval_alignment 低
overall_confidence 不应高
```

## Legal Domain Routing

### 目标

在检索前或离线诊断阶段，先识别问题所属法律领域，并检测 evidence_chain 是否混入不一致法域。

### 初始领域集合

| domain | 说明 | 典型法 |
|---|---|---|
| `personal_information_protection` | 个人信息处理、告知、同意、敏感个人信息、自动化决策 | 个保法 |
| `cross_border_data_transfer` | 个人信息/数据出境、安全评估、标准合同 | 个保法、数据出境安全评估办法、个人信息出境标准合同办法 |
| `data_security` | 重要数据、数据分类分级、数据安全管理 | 数据安全法 |
| `consumer_rights` | 退款、格式条款、消费者公平交易和知情权 | 消费者权益保护法、民法典 |
| `employment_privacy` | 员工监控、人脸考勤、工作场所个人信息处理 | 个保法、劳动相关规则 |
| `competition_law` | 不正当竞争、垄断协议、平台竞争行为 | 反不正当竞争法、反垄断法 |
| `corporate_governance` | 股东权利、董监高责任、公司治理 | 公司法 |

### Domain Consistency 规则

- 每个 hidden case 应有 `expected_primary_domains`。
- Evidence 的 `category`、`law_name` 应落在允许法域内。
- 对不允许法域的 evidence 标记 `domain_contamination`。
- 如果 top-3 中存在高权重不允许法域 evidence，应触发 `needs_human_review` 或降低 confidence。

示例：

```json
{
  "case_id": "seed_006_fintech_cross_border_antifraud_scoring",
  "expected_primary_domains": [
    "personal_information_protection",
    "cross_border_data_transfer"
  ],
  "blocked_domains": [
    "corporate_governance"
  ],
  "observed_contamination": [
    "中华人民共和国公司法::189",
    "中华人民共和国公司法::57"
  ]
}
```

## Issue Hierarchy

### Issue 层级

| level | 含义 | 证据要求 |
|---|---|---|
| `primary` | 决定法律结论的核心争点 | 必须有 operative rule 支撑 |
| `secondary` | 影响整改建议或风险等级的辅助争点 | 应有相关证据，但可低于 primary |
| `peripheral` | 语义相关但非本案主依据 | 不应成为 top evidence 的主要依据 |

### 平台自动化风控本体

```text
automated_decision
├── transparency
├── fairness
├── explainability
├── human_review
├── refusal_or_opt_out
└── significant_impact
```

```text
cross_border_transfer
├── overseas_recipient
├── transfer_path
├── separate_consent
├── pipia
├── security_assessment
└── standard_contract
```

```text
sensitive_personal_information
├── biometric
├── financial_account
├── location_or_tracking
├── minors
└── specific_notice_and_consent
```

### Hidden Seed Issue Map

| seed | primary issues | common failure |
|---|---|---|
| `seed_001_pipl_facial_attendance_complex` | sensitive PI, necessity, separate consent, PIPIA | 个保法义务条款未召回 |
| `seed_002_employee_monitoring_software_complex` | employee monitoring, notice scope, minimization | 安全审计/商业秘密语义污染 |
| `seed_003_algorithmic_price_discrimination_complex` | automated pricing, transparency, opt-out | 核心条文命中，但混入无关民法典 |
| `seed_004_online_education_ai_participation_scoring` | automated scoring, student video, minors, PIPIA | 定义条文替代规范条文 |
| `seed_005_supply_chain_cross_border_data_platform` | cross-border transfer, entrusted processing, important data | GB/T 标准替代法律法规 |
| `seed_006_fintech_cross_border_antifraud_scoring` | sensitive PI, cross-border transfer, automated credit denial | 公司法污染，answer/evidence 脱节 |
| `seed_007_cross_border_ecommerce_after_sales_scoring` | automated decision, cross-border transfer, consumer rights | 出境证据有，自动化决策/消费者权益缺 |

## Legal Functional Typing

### functional_type 枚举

| functional_type | 含义 | 示例 |
|---|---|---|
| `principle` | 基本原则 | 个保法第5、6、7条 |
| `definition` | 术语定义 | 个保法第73条 |
| `operative_rule` | 行为规范和义务规则 | 个保法第17、24、28、29、30、38、39、55条 |
| `rights_remedy` | 权利、解释、救济和复核 | 个保法第48条 |
| `procedural` | 程序、评估、备案、合同路径 | 个保法第56条、标准合同办法第5条、出境评估办法第4条 |
| `liability` | 法律责任和处罚 | 个保法第66条 |
| `technical_standard` | 推荐性标准或技术管理要求 | GB/T 35273 |
| `unrelated_or_contextual` | 背景相关但非本案依据 | 与主争点无关的公司法、民法典条款 |

### Evidence Rule

- primary issue 至少需要一个 `operative_rule`。
- `definition` 不得单独支撑法律结论。
- `technical_standard` 可以辅助说明管理要求，但不能替代上位法 operative rule。
- `procedural` 可以支撑路径和评估要求，但不能替代实体义务条款。
- `liability` 不能替代行为规范条款。

## Evidence Coverage Scoring

### Coverage Signals

```json
{
  "primary_issue_coverage": 0.0,
  "operative_rule_coverage": 0.0,
  "domain_consistency": 0.0,
  "definition_only_penalty": 0.0,
  "unsupported_reasoning_count": 0,
  "unrelated_evidence_count": 0
}
```

### 初始打分思路

| signal | 说明 |
|---|---|
| `primary_issue_coverage` | primary issues 中有多少被 evidence 支撑 |
| `operative_rule_coverage` | primary issues 是否有 operative rules |
| `domain_consistency` | evidence 是否落在 expected domains |
| `functional_type_balance` | operative/principle/procedural/definition 是否合理 |
| `unsupported_reasoning` | answer 中出现但 evidence_chain 未出现的法律依据 |
| `unrelated_evidence_penalty` | top evidence 中不相关法域或边缘争点数量 |

### Confidence 拆分

后续不应只输出一个 `confidence_score`。建议拆成：

```json
{
  "reasoning_confidence": 0.92,
  "evidence_confidence": 0.58,
  "retrieval_alignment": 0.43,
  "citation_integrity": 1.0,
  "overall_confidence": 0.62,
  "needs_human_review": true
}
```

原则：

- `overall_confidence` 不得高于 evidence confidence 太多。
- 出现 domain contamination 时，必须降低 retrieval alignment。
- answer 提到的关键法条不在 evidence_chain 中时，必须降低 evidence confidence。
- top-3 只有 definition/technical_standard 而缺 operative_rule 时，应触发 human review。

## 离线诊断输出草案

未来工具可命名为 `tools/check_hidden_eval_evidence_alignment.py`，输入 hidden seed 标注和一次 RAG 输出，输出：

```json
{
  "case_id": "seed_007_cross_border_ecommerce_after_sales_scoring",
  "primary_issues": [
    "automated_decision",
    "cross_border_transfer",
    "consumer_rights"
  ],
  "covered_primary_issues": [
    "cross_border_transfer"
  ],
  "missing_primary_issues": [
    "automated_decision",
    "consumer_rights"
  ],
  "domain_contamination": [],
  "peripheral_evidence": [
    "GB/T 35273 10.1"
  ],
  "definition_only": false,
  "unsupported_legal_references": [
    "中华人民共和国个人信息保护法::24",
    "中华人民共和国个人信息保护法::17"
  ],
  "recommended_review": true
}
```

## 分阶段路线

### v0.4.7.0a：设计稿与 seed 固化

- 保留 `docs/hidden_eval_seed_cases.md`。
- 新增本设计稿。
- 不改主流程，不运行评测。

### v0.4.7.0b：Hidden Seed 结构化清单

- 已新增 `config/hidden_eval_seed_cases.json`，将 7 条 seed 转为可机器校验的 JSON。
- 每条包含 expected domains、primary issues、secondary issues、peripheral issues、expected statutes、contaminating domains 和 known bad evidence。
- 已新增 `tools/check_hidden_eval_seeds.py` 与 `tests/test_hidden_eval_seed_cases.py`，仅做离线结构校验，不接入 `rag_query`。

### v0.4.7.1：离线 Evidence Alignment Checker

- 输入 seed 标注和保存的 RAG 输出。
- 输出 domain contamination、missing primary issue、definition-only、unsupported legal references。

### v0.4.7.2：Legal Functional Typing 试点

- 先标注个保法核心条文、数据出境规则、GB/T 标准。
- 不接 rerank，只用于诊断。

### v0.4.7.3：Confidence Split 设计与离线报告

- 先在报告中计算 `reasoning_confidence`、`evidence_confidence`、`retrieval_alignment`。
- 不改变 API 输出，先观察。

## 明确暂不做

- 不把 issue hierarchy 接入 `rag_query`。
- 不修改 rerank 排序。
- 不新增 anchor 来定向修 hidden seed。
- 不将 hidden seed 混入公开 RAG Eval。
- 不运行 full eval。
