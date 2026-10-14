# Legal Functional Type Config Gate v0.4.7.2.1

## 定位

v0.4.7.2.1 是 Legal Functional Typing 的质量修复版本。

本版本不扩展 RAG 能力，不修 hidden seed，也不改变 evidence alignment 的判断目标；它只为 `config/legal_functional_types.json` 增加发布前配置门禁，防止 functional typing 基建在后续大量法规入库时因为配置漂移而失真。

## 边界

- 不接入 `rag_query` 主流程。
- 不修改 rerank。
- 不修改 prompt。
- 不新增 anchor。
- 不修改 risk supplement / term preservation 规则。
- 不修改 eval case。
- 不运行 full eval。

## 新增工具

`tools/check_legal_functional_type_config.py`

检查内容：

- `version`、`purpose`、`functional_types`、`operative_support_types`、`rules` 必须存在且结构合法。
- `functional_type.id` 必须唯一，并使用 lowercase snake_case。
- 每个功能类型必须有 `label` 和 `description`。
- 必备功能类型必须存在：`definition`、`operative_rule`、`procedural`、`liability`、`rights_remedy`、`unclassified`。
- `operative_support_types` 必须引用已声明功能类型。
- rule 的 `functional_type` 必须引用已声明功能类型。
- rule 的 `priority` 必须是 0 到 1000 之间的整数。
- rule 的 `confidence` 必须是 `rule_high`、`rule_medium` 或 `rule_low`。
- 每条 rule 必须至少有 `contains` 或 `regex` 线索。
- 所有 regex 必须可以编译。
- 对无规则覆盖的功能类型输出 warning，但不直接失败。

## 使用方式

```powershell
.\venv\Scripts\python.exe tools\check_legal_functional_type_config.py `
  --config config\legal_functional_types.json `
  --report-output tests\legal_functional_type_config_report.json
```

## 当前结果

当前 `config/legal_functional_types.json`：

- Gate status：passed
- Errors：0
- Warnings：0
- Functional types：10
- Rules：7
- Contains cues：73
- Regex cues：19

## 与 v0.4.7.2 的关系

v0.4.7.2 建立了 taxonomy、分类 API 和知识库 audit。

v0.4.7.2.1 将 taxonomy 配置纳入机器门禁，确保后续新增财税、公司治理、知识产权等领域规则时，先通过结构质量检查，再进入 audit 或 evidence alignment 诊断。

## 后续方向

下一步可进入 v0.4.7.2.2：Golden Fixtures。

重点不是让某个 hidden seed 通过，而是建立小型、可读、可维护的法条片段基准集，覆盖定义、原则、义务、程序、责任、权利救济、范围、技术标准等功能类型，并专门加入容易误判的边界样本。
