# Legal Functional Typing Golden Fixtures v0.4.7.2.2

## 定位

v0.4.7.2.2 是 Legal Functional Typing 质量修复线的第二步。

v0.4.7.2.1 已经保护了配置结构；本版本进一步保护分类行为本身，建立小型、可读、可维护的 golden fixtures，防止后续修改规则时把原则条款、义务条款、程序条款、责任条款等核心分类边界改坏。

## 边界

- 不接入 `rag_query` 主流程。
- 不修改 rerank。
- 不修改 prompt。
- 不新增 anchor。
- 不修改 risk supplement / term preservation 规则。
- 不修改 eval case。
- 不运行 full eval。

## 新增 Fixture

`tests/fixtures/legal_functional_typing_golden.json`

当前覆盖：

- `definition`
- `principle`
- `operative_rule`
- `procedural`
- `liability`
- `rights_remedy`
- `scope`
- `technical_standard`
- `unclassified`
- metadata 优先级
- 容易误判的边界样本

这些 fixture 是 functional typing 的小型行为基准，不是 hidden seed，也不参与 RAG Eval。

## 新增工具

`tools/check_legal_functional_typing_fixtures.py`

检查内容：

- fixture 文件结构合法。
- case id 唯一。
- `expected_functional_type` 必须引用已声明功能类型。
- 每条 fixture 必须有文本和 metadata。
- 使用 `src/rag/legal_functional_typing.py` 对每条文本分类。
- 输出 expected/actual type、matched rule、matched terms 和失败分布。

## 本轮质量修复

fixture gate 首轮暴露了一个真实质量问题：

- 原规则会把“处理个人信息应当遵循合法、正当、必要和诚信原则，不得……”误判为 `operative_rule`。

修复方式：

- 不把所有原则词简单提权。
- 新增高优先级“原则组合短语”规则，例如 `合法、正当、必要`、`公开、透明`、`遵循...原则`。
- 保留宽泛原则词为低优先级，避免把普通义务条款中的“必要”“公开”等词误判为原则。

## 当前结果

`tests/legal_functional_typing_fixture_report.json`：

- Fixture cases：16
- Passed：16
- Failed：0

`tests/legal_functional_type_config_report.json`：

- Passed：true
- Errors：0
- Warnings：0
- Functional types：10
- Rules：8
- Contains cues：78
- Regex cues：20

`tests/legal_functional_typing_report.json`：

- Documents：15
- Chunks：7177
- Review documents：1
- `unclassified_ratio=0.288`
- `operative_support_ratio=0.633`

operative support 比例相较上一版略降，是因为部分原则条款不再被误计为义务支撑，属于质量修复后的预期变化。

## 后续方向

下一步可进入 v0.4.7.2.3：误报/漏报分析报告。

重点是基于 golden fixtures、functional typing audit 和 evidence alignment report 输出更清晰的质量归因，例如：

- 高未分类文档。
- 高 definition-only 文档。
- 无 operative support 文档。
- 各 domain 功能类型失衡。
- fixture 边界样本覆盖缺口。
