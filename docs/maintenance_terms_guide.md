# 维护术语指南

更新日期：2026-05-13

## 总规则

代码、字段、文件名和 schema 名保留英文；维护说明、roadmap、changelog 和报告正文尽量使用简体中文解释。首次出现英文专名时，可以用“中文解释（英文专名）”。

## 推荐术语

| 推荐中文 | 可保留英文 | 说明 |
|---|---|---|
| 人工复核 | `manual review` | 工具名、文件名、schema 字段中可保留英文。 |
| 正式人工复核结论 | `completed manual decision` | 只有人工填写并通过导入、校验、晋升预演和收尾门禁后，才能这样描述。 |
| 辅助材料 | `advisory` | AI suggestion、prescreen、pilot assist、mobile aid 都属于辅助材料，不是结论。 |
| 预演 | `dry run` | 正文统一写“预演”；文件名中的 `_dry_run` 保留。 |
| 门禁 | `gate` | 专名如 `intake gate`、`stability gate` 可保留。 |
| 收尾报告 | `closeout report` | 用于确认某一阶段是否满足进入下一阶段条件。 |
| 脚手架 | `scaffold` | 指未来目录或结构占位，不代表已经迁移。 |
| 权威路径 | `canonical output path` | 当前权威报告路径仍是 `tests/`；当前权威工具入口仍是 root-level `tools/*.py`。 |
| 布局兼容层 | `Project Layout Compatibility Layer` | 只计算 legacy/future 路径关系，不迁移文件。 |
| 健康检查 | `health check` | 工具名保留 `run_project_health_check.py`。 |
| 乱码 / 误解码 | `mojibake` | 区分文件实际编码污染与 PowerShell 未指定 UTF-8 导致的显示误解码。 |

## 固定边界表述

- 维护工具只输出诊断报告，不自动修复、不移动文件、不改变默认路径。
- `reports/` 仍是未来脚手架，当前不要写成权威输出目录。
- `tests/*.json` 仍是当前主要评测、诊断、人工复核和维护报告路径。
- root-level `tools/*.py` 仍是当前权威 CLI 入口。
- 不把 blocked action candidates、fixture candidates 或 advisory reports 写成工程修复指令。
- 不把 AI suggestion、prefill、pilot assist 或 mobile aid 写成正式人工复核结论。

## 写作禁区

- 不要写“报告已迁移到 reports/”，除非后续版本真的完成兼容迁移。
- 不要写“工具已迁移到子目录”，除非后续版本真的改变入口。
- 不要写“人工复核完成”，当前仍没有真实 completed manual decision。
- 不要把维护系列描述为 RAG 能力提升；它是可维护性、可发现性和边界治理增强。
