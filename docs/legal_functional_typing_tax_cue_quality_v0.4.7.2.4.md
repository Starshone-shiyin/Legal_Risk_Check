# Legal Functional Typing Tax Cue Quality v0.4.7.2.4

## 定位

v0.4.7.2.4 是 Legal Functional Typing 质量修复线的一次小步修复。
本版本承接 v0.4.7.2.3 error analysis 的 P1 行动项，处理 `中华人民共和国增值税法` 高未分类比例，但仍保持为离线 grounding quality diagnostics 基建，不接入 RAG 主流程。

## 边界

- 不修 hidden seed。
- 不新增 anchor。
- 不修改 rerank。
- 不改 prompt。
- 不改 risk supplement / term preservation 规则。
- 不改 eval case。
- 不接入 `rag_query` 主流程。
- 不运行 full eval。

## 关键修复

1. 新增正文短文本的结构性材料识别：
   - 法律标题。
   - 通过日期。
   - 目录。
   - 章节/编/部分标题。

   这些文本归入 `unrelated_or_contextual`，避免标题、目录、章节名被误计为义务或程序支撑。

2. 补充财税/税务通用法律功能线索：
   - `operative_rule`：税率、征收率、应纳税额、计税方法、销项税额、进项税额、抵扣、免征、税收优惠、应税交易、扣缴义务人、起征点、组成计税价格、适用税率。
   - `procedural`：申报纳税、办理登记、纳税地点、纳税义务发生时间、扣缴义务发生时间、计税期间、预缴税款、报关进口、征收管理、主管税务机关。

3. 扩展 golden fixtures：
   - 税率规则。
   - 抵扣规则。
   - 免征规则。
   - 申报纳税程序。
   - 办理登记程序。
   - 税务责任优先级。
   - 法律标题、章节标题、目录结构性材料。

## 当前结果

`tests/legal_functional_typing_report.json`：
- Documents：15。
- Chunks：7177。
- Review documents：0。
- `unclassified_ratio=0.25`。
- `operative_support_ratio=0.635`。

`中华人民共和国增值税法`：
- Chunks：156。
- `unclassified_ratio=0.167`，从 v0.4.7.2.3 的 `0.5` 降低。
- `operative_support_ratio=0.628`，从 v0.4.7.2.3 的 `0.353` 提升。
- `review_required=false`。
- `unrelated_or_contextual=15`，用于承载标题、目录、章节等结构性材料。

`tests/legal_functional_typing_error_analysis_report.json`：
- fixture failed cases：0。
- high unclassified documents：0。
- low operative documents：0。
- definition-only documents：0。
- alignment review cases：50。
- alignment missing-primary cases：12。
- alignment unsupported-output cases：48。
- prioritized actions：2。

## 质量含义

本版本只解决 functional typing 层的 P1 高未分类问题，不声称解决 evidence alignment 层的 missing-primary 或 answer-evidence disconnect。
剩余 P2/P3 仍应作为后续 coverage diagnostics 与答案-证据脱节分析的输入。

## 验证

- `py_compile` 通过。
- 相关单测通过。
- Config gate 通过：0 errors、0 warnings。
- Fixture gate 通过：25/25。
- Functional typing audit 通过：15 documents、0 review documents。
- Evidence alignment checker 可在现有 `tests/rag_eval_report.json` 上运行。
- Error analysis report 可基于刷新后的离线报告生成。
- Full eval 未运行。
