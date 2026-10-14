# 识险智控 · Legal Risk Check

面向企业业务场景的法律风险分析与供应链风险管理原型，包含法律知识检索、证据引用、风险分析、内部风险流程、外部情报接入、材料解析、Web 界面和 Electron 桌面封装。

比赛结束后，以 MIT 许可证公开项目原创源码。当前后端版本为 `0.5.4`，桌面封装版本为 `0.5.2`。

## 能力与结构

- `src/rag`、`src/risk`：法律领域路由、稠密与 BM25 混合检索、重排、引用检查、风险报告。
- `src/internal_risk`、`src/risk_intake`：企业风险接入、评估、复核及流程管理。
- `src/external_risk`、`src/supply_chain`：外部市场/情报提供方与供应链分析。
- `src/document_ingest`、`src/skills`：材料解析与可配置流程。
- `web`：静态 Web 界面；`desktop`：Electron 外壳及 Windows 打包脚本。
- `config`、`tests/fixtures`：规则配置和测试样例；`tools`：评估、诊断及维护工具。

## 本地运行

以下步骤使用 Windows PowerShell。Python 依赖版本来自开发环境 Python 3.13.8；在线模型、Embedding 和材料解析服务需要自行配置。

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，填写自己的 `LLM_API_KEY`、`SILICONFLOW_API_KEY`。占位值可供配置加载，在线问答需要有效密钥。配置文件中的默认模型和 URL 是可调整示例。

启动 Qdrant（需要 Docker）：

```powershell
docker run -d --name legal-risk-qdrant -p 127.0.0.1:6333:6333 -v legal-risk-qdrant-data:/qdrant/storage qdrant/qdrant:v1.17.1
```

首次构建本地知识库会调用 Embedding 服务：

```powershell
.\venv\Scripts\python.exe rag_admin.py --rebuild
.\start_backend.bat
```

接口文档：<http://127.0.0.1:8000/docs>。另开终端启动静态前端：

```powershell
.\venv\Scripts\python.exe -m http.server 8081 --bind 127.0.0.1 --directory web
```

打开 <http://127.0.0.1:8081/website.html>。本地启动脚本提供演示身份；部署前需要配置正式身份与访问控制。Web 界面默认连接本机后端，设置入口可调整连接及模型配置。

桌面开发需要 Node.js：

```powershell
cd desktop
npm ci
npm run dev
```

完整桌面打包流程见 [desktop/README.md](desktop/README.md)。源码仓库不附带向量数据库种子、运行时二进制或安装包。

## 验证与维护

```powershell
.\venv\Scripts\python.exe -m compileall -q src tools tests
```

测试、离线评估和在线评估入口见 `tests`、[开发指令](DEV_Commands.md)、[知识库更新说明](rag_update_guide.md)。部分测试依赖配置、Qdrant 或远程服务，请按各脚本说明运行。

## 公开版本边界

公开源码采用独立的首次提交，保留本地开发历史。公开版本排除密钥、本机工具配置、上传材料、当前业务记录、比赛文档、生成报告和构建产物。`data` 使用空的运行数据与明确的演示样例；它们用于功能演示。

项目输出用于研究和辅助分析，法律事实、时效、引用及行动建议需要人工核对。法律知识文本以项目保存的版本为准，维护者应根据实际使用场景更新。第三方标准全文不随首次开源版本发布，如需要可自行取得授权材料后按入库说明添加。

## 许可证

项目原创源码采用 [MIT](LICENSE)。第三方依赖、法规及外部资料遵循各自适用的授权和使用条件，MIT 不改变它们的权利归属。
