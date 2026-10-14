# v0.4.7.9.4 Ready Action Design Review Closeout Envelope

本文件是人工设计评审的收口外壳。它列出 5 条设计轨道的候选分流和人工确认问题，但不记录正式人工结论，也不批准任何代码、配置、样例或主流程修改。

## 总览

- Closeout status: `pending_human_design_closeout`
- Allowed use: `human_closeout_discussion_only`
- Closeout tracks: 5
- Design actions: 18
- Source cases: 5
- Pending records excluded: 31
- Formal outcome recorded: False
- Implementation allowed: False
- Code patch authorized: False
- Next design authorized: False

## Closeout Matrix

| Order | Priority | Track | Candidate route | Suggested option | Status |
|---:|---|---|---|---|---|
| 1 | P0 | 最终证据选择策略评审 | 最终证据选择策略设计草案 | `continue_to_design_spec_draft` | `pending_human_closeout` |
| 2 | P0 | 主证据测试样例候选评审 | 主证据 fixture 候选治理 | `needs_legal_or_fixture_scope_review` | `pending_human_closeout` |
| 3 | P0 | 高风险结论证据支撑评审 | 高风险结论人工 grounding 评审 | `continue_to_design_spec_draft` | `pending_human_closeout` |
| 4 | P1 | 场景核心条文范围评审 | 场景核心条文范围复核 | `needs_legal_or_fixture_scope_review` | `pending_human_closeout` |
| 5 | P1 | 法律功能类型样例评审 | 法律功能类型 fixture 评审 | `needs_legal_or_fixture_scope_review` | `pending_human_closeout` |

## Human Closeout Questions

### 1. 最终证据选择策略评审

- 收口问题：是否确认主要问题在最终 evidence_chain 选择，而不是召回、场景范围或提示词？
- 最小人工依据：至少确认关键证据已进入候选池但未进入最终证据链，并说明后续 simulator 的保护口径。
- 候选分流：`v0.4.8.x_final_evidence_selection_policy_design` / 最终证据选择策略设计草案
- 当前状态：`pending_human_closeout`
- 可选收口口径：
  - `continue_to_design_spec_draft`：人工确认方向成立，可进入后续设计草案；仍不允许实现。
  - `needs_legal_or_fixture_scope_review`：需要先补法律范围或 fixture 范围复核；仍不允许实现。
  - `defer_pending_more_cases`：现有 5 个 pilot case 不足以支撑该方向，等待更多人工复核 case。
  - `close_without_followup`：本轮不继续推进该方向；不得生成工程任务。
- 当前禁止：
  - 本报告只提供人工收口外壳。
  - 候选分流不等于实现授权。
  - 任何后续实现必须另开版本并重新确认边界。

### 2. 主证据测试样例候选评审

- 收口问题：是否确认这些候选可代表通用主证据缺口，而不是单案补丁？
- 最小人工依据：至少确认候选证据、主争点、来源 case 和不写入 eval case 的边界。
- 候选分流：`fixture_governance_review` / 主证据 fixture 候选治理
- 当前状态：`pending_human_closeout`
- 可选收口口径：
  - `continue_to_design_spec_draft`：人工确认方向成立，可进入后续设计草案；仍不允许实现。
  - `needs_legal_or_fixture_scope_review`：需要先补法律范围或 fixture 范围复核；仍不允许实现。
  - `defer_pending_more_cases`：现有 5 个 pilot case 不足以支撑该方向，等待更多人工复核 case。
  - `close_without_followup`：本轮不继续推进该方向；不得生成工程任务。
- 当前禁止：
  - 本报告只提供人工收口外壳。
  - 候选分流不等于实现授权。
  - 任何后续实现必须另开版本并重新确认边界。

### 3. 高风险结论证据支撑评审

- 收口问题：是否确认风险类型、整改动作或法律后果需要更强证据支撑规则？
- 最小人工依据：至少说明哪些高风险结论不能被当前 evidence_chain 直接支撑。
- 候选分流：`manual_grounding_review` / 高风险结论人工 grounding 评审
- 当前状态：`pending_human_closeout`
- 可选收口口径：
  - `continue_to_design_spec_draft`：人工确认方向成立，可进入后续设计草案；仍不允许实现。
  - `needs_legal_or_fixture_scope_review`：需要先补法律范围或 fixture 范围复核；仍不允许实现。
  - `defer_pending_more_cases`：现有 5 个 pilot case 不足以支撑该方向，等待更多人工复核 case。
  - `close_without_followup`：本轮不继续推进该方向；不得生成工程任务。
- 当前禁止：
  - 本报告只提供人工收口外壳。
  - 候选分流不等于实现授权。
  - 任何后续实现必须另开版本并重新确认边界。

### 4. 场景核心条文范围评审

- 收口问题：是否确认缺失条文属于该场景的核心法律依据？
- 最小人工依据：至少由人工确认核心条文清单边界；本报告不修改 scenario registry。
- 候选分流：`scenario_core_article_review` / 场景核心条文范围复核
- 当前状态：`pending_human_closeout`
- 可选收口口径：
  - `continue_to_design_spec_draft`：人工确认方向成立，可进入后续设计草案；仍不允许实现。
  - `needs_legal_or_fixture_scope_review`：需要先补法律范围或 fixture 范围复核；仍不允许实现。
  - `defer_pending_more_cases`：现有 5 个 pilot case 不足以支撑该方向，等待更多人工复核 case。
  - `close_without_followup`：本轮不继续推进该方向；不得生成工程任务。
- 当前禁止：
  - 本报告只提供人工收口外壳。
  - 候选分流不等于实现授权。
  - 任何后续实现必须另开版本并重新确认边界。

### 5. 法律功能类型样例评审

- 收口问题：是否确认条文功能类型足够明确，适合进入 fixture 候选池？
- 最小人工依据：至少确认定义、义务、责任或程序功能标签及其人工标注规范。
- 候选分流：`legal_functional_typing_fixture_review` / 法律功能类型 fixture 评审
- 当前状态：`pending_human_closeout`
- 可选收口口径：
  - `continue_to_design_spec_draft`：人工确认方向成立，可进入后续设计草案；仍不允许实现。
  - `needs_legal_or_fixture_scope_review`：需要先补法律范围或 fixture 范围复核；仍不允许实现。
  - `defer_pending_more_cases`：现有 5 个 pilot case 不足以支撑该方向，等待更多人工复核 case。
  - `close_without_followup`：本轮不继续推进该方向；不得生成工程任务。
- 当前禁止：
  - 本报告只提供人工收口外壳。
  - 候选分流不等于实现授权。
  - 任何后续实现必须另开版本并重新确认边界。

## Boundaries

- 本 closeout envelope 只帮助人工收口讨论，不记录正式人工结论。
- `formal_human_outcome_recorded=false`、`implementation_allowed=false`、`code_patch_authorized=false` 和 `next_design_authorized=false` 必须保持不变。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约或 RAG 主流程。
- 后续若进入 v0.4.8.x、v0.4.9.x 或 fixture governance，必须另开版本并重新确认边界。

## Source

- Worksheet report: `tests\ready_action_design_review_worksheet_report.json`
