# 内部风控企业业务状态

`/internal-risk/business-state/initialize` 仅为已由网关签名的企业创建独立的内部风控业务状态。它不会读取、写入或替换 API Key、RSS 源、Provider 或其他运行时配置。

初始化请求可声明企业名称、行业、业务模式和生命周期阶段。生命周期仅是可选字段，不绑定任何行业；既有 AI 生命周期枚举仍保持可用，确保历史数据和接口兼容。

## 通用工作流模板

模板由企业自行维护，不内置半导体或其他行业固定 Gate。具备 `risk_decision_maker` 角色的签名企业主体可以：

- `POST /internal-risk/workflow-templates` 新建本企业模板；
- `POST /internal-risk/workflow-templates/import` 导入 JSON 模板；
- `POST /internal-risk/workflow-templates/{template_id}/versions` 新建不可变版本；
- 在初始化中传入 `workflow_template_id` 和可选的 `workflow_template_version`，将该版本的 Gate、核验项和责任角色复制到新企业工作流。

模板按企业隔离。模板 Gate 仅描述生命周期、核验项和系统角色（`risk_viewer`、`risk_operator`、`risk_reviewer`、`risk_decision_maker`），不携带人员身份、供应商数据或运行时配置。每个版本保留内容 SHA-256，已应用的工作流保存模板版本和哈希，后续版本不会改写既有工作流。`GET /internal-risk/workflow-templates/{template_id}/audit` 提供创建、导入和版本创建的追加式审计记录。

初始化时系统保存该企业空白业务状态的基线。具备 `risk_decision_maker` 角色的签名企业主体可调用 `/internal-risk/business-state/reset`，并提供整改或测试完成原因。重置只还原该企业的内部风控业务状态；审计记录不会被删除。

`/internal-risk/business-state/audit` 返回追加式审计记录，包含操作者、时间、基线标识以及重置前后业务状态的 SHA-256 摘要，便于验证测试数据已清除而运行配置未受影响。

## 遗留租户基线与阻断说明

已有租户可先调用 `POST /internal-risk/business-state/baseline/proposal` 冻结当前状态和 SHA-256 摘要；另一名 `risk_decision_maker` 必须通过 `POST /internal-risk/business-state/baseline/confirmation` 确认。确认期间如业务状态变更，系统拒绝确认并要求重新提案。确认成功后才允许重置。

闸门放行和风险关闭的 409 响应包含 `error.blockers` 数组（阻断代码、对象、提示和整改建议）；也可通过 `GET /internal-risk/gates/{gate_id}/blockers` 和 `GET /internal-risk/risks/{risk_id}/closure-blockers` 在提交前读取。
