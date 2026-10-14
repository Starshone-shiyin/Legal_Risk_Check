# v0.4.7.9.5 Ready Action Human Closeout Decision Draft

本文件是待用户确认的人工收口草案。它给出 5 条设计轨道的建议方向，但不记录正式人工结论，也不批准任何代码、配置、样例或主流程修改。

## 总览

- Draft status: `draft_pending_user_confirmation`
- Allowed use: `user_confirmation_draft_only`
- Draft tracks: 5
- Design actions: 18
- Source cases: 5
- Pending records excluded: 31
- Requires user confirmation: True
- Formal outcome recorded: False
- Importable decision: False
- Implementation allowed: False
- Code patch authorized: False
- Next design authorized: False

## Draft Matrix

| Order | Priority | Track | Draft option | Suggested next | Status |
|---:|---|---|---|---|---|
| 1 | P0 | 最终证据选择策略评审 | `continue_to_design_spec_draft` | v0.4.8.x | `draft_pending_user_confirmation` |
| 2 | P0 | 主证据测试样例候选评审 | `needs_legal_or_fixture_scope_review` | fixture governance | `draft_pending_user_confirmation` |
| 3 | P0 | 高风险结论证据支撑评审 | `continue_to_design_spec_draft` | manual grounding review | `draft_pending_user_confirmation` |
| 4 | P1 | 场景核心条文范围评审 | `needs_legal_or_fixture_scope_review` | scenario core article review | `draft_pending_user_confirmation` |
| 5 | P1 | 法律功能类型样例评审 | `needs_legal_or_fixture_scope_review` | legal functional typing fixture review | `draft_pending_user_confirmation` |

## Draft Directions

### 1. 最终证据选择策略评审

- 草案方向：建议继续进入 v0.4.8.x 最终证据选择策略设计草案。
- 草案理由：5 个 pilot case 均显示关键证据可能已进入候选池但未进入最终 evidence_chain，是当前最明确的 Harvey-style grounding 质量瓶颈。
- 需要你确认：确认问题主要发生在最终证据选择，而不是召回、场景范围或提示词。
- 候选后续：`v0.4.8.x` / final_evidence_selection_policy_design_spec_draft
- 当前状态：`draft_pending_user_confirmation`
- 草案限制：
  - 这是待用户确认草案，不是正式人工结论。
  - 不能导入 importer，也不能作为 completed manual decision。
  - 任何后续设计或实现必须另开版本并重新确认边界。

### 2. 主证据测试样例候选评审

- 草案方向：建议先进入 fixture governance 范围复核，不直接写入 eval case 或 golden fixture。
- 草案理由：主证据候选对后续评测很重要，但当前只能作为候选池材料，必须先确认通用性和非单案补丁属性。
- 需要你确认：确认候选证据是否能代表通用主争点证据缺口。
- 候选后续：`fixture governance` / primary_evidence_fixture_candidate_scope_review
- 当前状态：`draft_pending_user_confirmation`
- 草案限制：
  - 这是待用户确认草案，不是正式人工结论。
  - 不能导入 importer，也不能作为 completed manual decision。
  - 任何后续设计或实现必须另开版本并重新确认边界。

### 3. 高风险结论证据支撑评审

- 草案方向：建议继续形成高风险结论 grounding 设计草案，但仍不改 prompt 或 risk rule。
- 草案理由：高风险结论、整改动作和法律后果需要可追溯证据支撑，否则企业风控报告会出现结论强、证据弱的问题。
- 需要你确认：确认哪些高风险结论不能被当前 evidence_chain 直接支撑。
- 候选后续：`manual grounding review` / high_risk_grounding_design_spec_draft
- 当前状态：`draft_pending_user_confirmation`
- 草案限制：
  - 这是待用户确认草案，不是正式人工结论。
  - 不能导入 importer，也不能作为 completed manual decision。
  - 任何后续设计或实现必须另开版本并重新确认边界。

### 4. 场景核心条文范围评审

- 草案方向：建议先做场景核心条文范围复核，不直接修改 scenario registry。
- 草案理由：部分缺失证据可能来自场景法律范围边界，而不是最终选择策略；需要人工确认核心条文清单。
- 需要你确认：确认缺失条文是否属于该场景的核心法律依据。
- 候选后续：`scenario core article review` / scenario_core_article_scope_review
- 当前状态：`draft_pending_user_confirmation`
- 草案限制：
  - 这是待用户确认草案，不是正式人工结论。
  - 不能导入 importer，也不能作为 completed manual decision。
  - 任何后续设计或实现必须另开版本并重新确认边界。

### 5. 法律功能类型样例评审

- 草案方向：建议先做 legal functional typing fixture 范围复核，不直接改 config。
- 草案理由：功能类型标签是长期 RAG grounding 基建，当前只能沉淀候选和标注规范，不能直接修改配置。
- 需要你确认：确认条文功能类型是否足够明确，适合进入 fixture 候选池。
- 候选后续：`legal functional typing fixture review` / legal_functional_typing_fixture_scope_review
- 当前状态：`draft_pending_user_confirmation`
- 草案限制：
  - 这是待用户确认草案，不是正式人工结论。
  - 不能导入 importer，也不能作为 completed manual decision。
  - 任何后续设计或实现必须另开版本并重新确认边界。

## Boundaries

- 本 draft 只帮助用户确认或修改收口方向，不记录正式人工结论。
- `requires_user_confirmation=true`、`formal_human_outcome_recorded=false`、`draft_is_importable_decision=false` 必须保持不变。
- `implementation_allowed=false`、`code_patch_authorized=false` 和 `next_design_authorized=false` 必须保持不变。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry、eval case、fixture、schema、importer、dry-run 契约或 RAG 主流程。
- 后续若进入 v0.4.8.x、v0.4.9.x 或 fixture governance，必须另开版本并重新确认边界。

## Source

- Closeout report: `tests\ready_action_design_review_closeout_report.json`
