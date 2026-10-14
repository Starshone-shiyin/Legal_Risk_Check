# 开发者调试环境

开发者调试场景仅用于本地验证，默认关闭。启用后，每次运行都创建 `output/developer_debug_runs/<run-id>/`，其中的供应链、风险接入和内控工作流 JSON 都是夹具的独立副本；不会读写 `data/` 下的默认文件。

## 启动与执行

在本地进程设置 `RISK_DEVELOPER_DEBUG_ENABLED=true` 后，可通过 API 创建、读取和重置运行：

Windows 下可直接运行仓库根目录的 `start_backend_debug.bat`。它会优先使用 `8014`，如果端口被占用则自动顺延到下一个空闲端口，并将实际端口写入 `tmp/developer_debug_port.txt`；也可以传入端口号强制指定，例如 `start_backend_debug.bat 8015`。该入口会开启开发者调试、实时行情和 RSS，并跳过 Qdrant 可用性检查。后端就绪后，它会自动打开前端页面，并把实际后端地址写入 URL 的 `api` 参数；若 `8081` 未运行 RiskFlow 前端，会临时启动静态前端服务。

关闭对应服务运行 `stop_backend_debug.bat`；无参数时读取启动记录中的实际端口，也支持 `stop_backend_debug.bat 8015`。它只会关闭由调试入口临时启动的静态前端，不会关闭原本已存在的前端服务。

```text
POST /developer-debug/scenarios/china-semiconductor-ai-chain/runs
GET  /developer-debug/runs/{run_id}/suppliers
GET  /developer-debug/runs/{run_id}/context
POST /developer-debug/runs/{run_id}/execute
POST /developer-debug/runs/{run_id}/reset
```

首测执行器会走上述 API，并写出可审计的测试报告：

```text
venv\Scripts\python.exe tools\run_developer_debug_scenario.py
venv\Scripts\python.exe tools\judge_developer_debug_run.py output\developer_debug_runs\<run_id>\scenario_report.json
```

`execute` 在三个隔离存储中执行“外部信号 -> 风险接入匹配 -> 人工分诊 -> 风险事件评估 -> 人工确认”的固定调试闭环。评估报告是确定性的测试替身，不是法律意见。

## 场景驱动的全生命周期视图

前端在供应链地图的“开发者调试”区域选择并加载场景。加载后，供应链、外部风险、风险准入、内部风控和生命周期视图都读取同一个 `GET /developer-debug/runs/{run_id}/context` 响应；普通工作区数据不会被改写。

新行业不需要修改前后端代码。夹具至少提供 `scenario.company`、`nodes`、`edges`、`sources` 和 `scenario.risk_profiles`。生命周期阶段默认按产业链节点自动生成；需要自定义分组、名称或顺序时，可添加 `scenario.lifecycle_stages`：

```json
{
  "id": "cell-materials",
  "label": "电芯材料",
  "scope": "材料供应与可得性控制",
  "order": 1,
  "node_ids": ["cathode", "anode"],
  "external_domains": ["supply_chain"]
}
```

节点可用 `lifecycle.stage_id` 指向该阶段；未指向的节点会自动成为独立阶段。运行时会将风险、门禁、整改任务、证据和外部信号按节点/项目映射回阶段。`business_stage` 与 `control_stage` 仍使用系统既有的治理枚举，以保证隔离闭环可执行。

`china-semiconductor-ai-chain` 使用上市公司公开名称和证券代码，覆盖材料、硅片、设备、晶圆代工、封装测试、芯片设计与 AI 服务器。场景中的节点、边和来源对象可在夹具中核对；所有企业间边都是产业位置模拟，不能用于判断真实交易或商业关系。

## 产业链商品期货关联

商品期货不会按某一个行业固定绑定。调试夹具可以在 `scenario.commodity_links` 中声明期货合约、关联节点和关联理由，也可以在节点上声明 `commodity_symbols`；运行时只有当近期 RSS 明确提及该商品线索，且该合约属于当前场景声明的关联集合时，才会请求真实行情并生成 `commodity_futures` 信号。未关联的商品不会被带入产业链风险。

共享目录覆盖金属、能源、航运以及化学品期货，包括乙二醇、聚丙烯、聚乙烯、PVC、甲醇、PTA、烧碱、玻璃、尿素、苯乙烯、对二甲苯、短纤和液化石油气。新增行业只需在场景数据中声明对应的关联节点，不需要修改服务逻辑。
