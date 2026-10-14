# 识险智控 Electron 桌面封装

这是比赛演示用桌面外壳基础设施。Electron 负责窗口、静态前端、本地 FastAPI
和 Qdrant 进程生命周期；业务逻辑仍由现有 Python 项目提供。

## 开发模式

在项目根目录已有 venv 和本地 Qdrant 的情况下：

~~~powershell
cd desktop
npm install
npm run dev
~~~

开发模式会优先使用根目录 venv\Scripts\python.exe，并尝试连接本机
127.0.0.1:6333 的 Qdrant。可通过环境变量覆盖端口或 Python 路径：

~~~powershell
$env:RISKFLOW_BACKEND_PORT = "8000"
$env:RISKFLOW_FRONTEND_PORT = "8081"
$env:RISKFLOW_QDRANT_PORT = "6333"
$env:RISKFLOW_PYTHON = "D:\Projects\Legal_Risk_Check\venv\Scripts\python.exe"
npm run dev
~~~

## 准备 Windows 运行时

最终包不依赖主办方安装 Python、Node.js、Docker 或浏览器。打包前需要准备：

1. 一个经验证的 riskflow-backend.exe；
2. 一个 Windows x64 qdrant.exe；
3. 与比赛演示一致的 Qdrant storage-seed，尤其是更新后的生态环境法典索引。

当前提交 seed 只包含 `legal_knowledge_staging_20260811`，实测为 14,050 个点、状态
green；其中生态环境法典的 metadata 版本为 2026，生效日期为 2026-08-15。collection
名称中的 `20260811` 是历史构建标签，不代表继续使用旧法规文本。

当前冻结基线为 Qdrant 1.17.1；它与现有知识库服务版本一致。可使用脚本下载并校验
Windows x64 官方程序：

~~~powershell
.\desktop\scripts\download-qdrant.ps1
~~~

如果知识库在本机 Docker 容器 `qdrant` 中，可用脚本在保持容器状态的前提下冻结
当前比赛 collection 的 storage seed。脚本默认只提取
`legal_knowledge_staging_20260811`，会短暂暂停运行中的容器，复制完成后自动恢复：

~~~powershell
.\desktop\scripts\capture-qdrant-seed.ps1
~~~

先构建 FastAPI 后端，再准备比赛演示数据：

~~~powershell
.\desktop\scripts\build-backend.ps1
.\desktop\scripts\prepare-data-seed.ps1
~~~

最后汇总运行时：

~~~powershell
.\desktop\scripts\stage-runtime.ps1 `
  -BackendBundle .\desktop\runtime-build\backend\riskflow-backend `
  -QdrantExecutable .\desktop\runtime-build\qdrant\qdrant.exe `
  -QdrantStorageSeed .\desktop\runtime-build\qdrant-storage-seed `
  -DataSeed .\desktop\runtime\data-seed
~~~

然后在 desktop 目录执行：

~~~powershell
npm run pack:dir
npm run dist:win
~~~

运行时组件不会提交到 Git；.env、API Key、上传材料、日志和用户数据也不会
进入安装包。

## 当前边界

- Electron 方案是“桌面外壳 + 两个本地 sidecar”，不是单一二进制；
- 外部 LLM、Embedding、MineU 仍按演示/联网模式分别配置；
- 安装包首次启动会把只读的 config、法规文本、fixture 和演示数据复制到用户数据目录，
  让后端可以在无 Python 环境的机器上读写；
- 未提供真实 API Key 时，桌面包使用非敏感的本地禁用占位值启动，确定性演示路由仍可用，
  在线 LLM/Embedding 能力需要主办方另行配置环境变量；
- 生态环境法典的法规文本、manifest 和 Qdrant 索引必须作为同一提交基线验证。

## 体积与交付形式

当前实测目录版约 1.42 GB，其中 Electron 壳约 323 MB、Python 后端约 157 MB、
Qdrant 程序约 79 MB、当前比赛 collection 的 seed 约 897 MB。NSIS 安装包和
portable 包实测均约 227 MB；安装或解压后仍应预留至少 2 GB 磁盘空间。建议同时
提交两种包：NSIS 便于安装，portable 便于主办方直接解压演示。

当前没有配置发布证书，因此 Windows 可能显示“未知发布者”或 SmartScreen 提示；
这属于签名状态，不是程序运行错误。正式外发前如有证书，再对两个 exe 做最终签名。
