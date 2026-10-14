# Legal Functional Typing Error Analysis v0.4.7.2.3

## 定位

v0.4.7.2.3 是 Legal Functional Typing 质量修复线的第三步。

v0.4.7.2.1 保护配置结构，v0.4.7.2.2 保护分类行为；本版本把 fixture gate、functional typing audit 和 evidence alignment report 合并成误报/漏报归因报告，输出可行动的优先级清单。

## 边界

- 不接入 `rag_query` 主流程。
- 不修改 rerank。
- 不修改 prompt。
- 不新增 anchor。
- 不修改 risk supplement / term preservation 规则。
- 不修改 eval case。
- 不运行 full eval。

## 新增工具

`tools/analyze_legal_functional_typing_errors.py`

输入：

- `tests/legal_functional_typing_fixture_report.json`
- `tests/legal_functional_typing_report.json`
- `tests/evidence_alignment_report.json`

输出：

- `tests/legal_functional_typing_error_analysis_report.json`

## 分析维度

- fixture 失败：任何 golden fixture 失败都列为 P0。
- 高未分类文档：`unclassified_ratio > 0.35`。
- 低 operative support 文档：非标准类文档且 `operative_support_ratio < 0.25`。
- definition-only 文档。
- evidence alignment 中的 missing-primary、definition-only、unsupported-output、insufficient-coverage cases。
- prioritized action list。

## 当前结果

`tests/legal_functional_typing_error_analysis_report.json`：

- fixture failed cases：0
- high unclassified documents：1
- low operative documents：0
- definition-only documents：0
- alignment review cases：50
- alignment missing-primary cases：12
- alignment definition-only cases：0
- alignment unsupported-output cases：48
- prioritized actions：3

当前行动优先级：

1. P1：降低高未分类文档比例。当前对象是 `中华人民共和国增值税法`，`unclassified_ratio=0.5`。
2. P2：用 missing-primary evidence cases 指导后续 coverage diagnostics，不做 case-specific patch。
3. P3：answer-evidence disconnect 与 functional typing 分开分析，避免过早修改生成规则。

## 质量含义

当前没有 P0，说明 v0.4.7.2.2 的 golden fixtures 仍保持通过。

当前也没有 definition-only 文档或 alignment definition-only cases，说明本轮主要问题不是“只命中定义条款”，而是：

- 财税类语言线索不足，导致未分类比例偏高。
- alignment 层仍有较多 missing-primary 和 unsupported-output 信号，需要后续分别做 coverage diagnostics 和答案-证据脱节分析。

## 后续方向

下一步建议 v0.4.7.2.4：Tax/Domain-Neutral Cue Quality Fix。

重点是优先处理 `中华人民共和国增值税法` 的高未分类比例，但仍应保持规则为领域中性法律语言线索，而不是针对某个 case 或 hidden seed 打补丁。
