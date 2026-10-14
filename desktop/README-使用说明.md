# 识险智控｜比赛演示包使用说明

## 1. 快速开始

本演示包适用于 Windows 10/11 64 位系统。

推荐使用 `RiskFlow-0.5.2-x64-setup.exe` 安装；如果不希望安装，也可以直接运行
`RiskFlow-0.5.2-x64-portable.exe`。

首次启动时，程序会显示启动进度页，依次提示本地运行环境、内置法规库、向量检索服务和
业务服务的准备状态。首次打开可能需要等待约 30–60 秒，请不要重复启动多个实例；如启动
失败，程序会提示查看用户数据目录下的日志文件。

## 2. 环境要求

- Windows 10/11 x64
- 建议预留至少 2 GB 可用磁盘空间
- 不需要另外安装 Python、Node.js、Docker、Qdrant 或浏览器
- 不需要手动配置端口

程序内置 FastAPI 后端、Qdrant 向量检索服务、法规文本、知识库和比赛演示数据，
服务只监听本机地址，不对局域网开放。

## 3. 可直接演示的内容

- 风险总览与产品生命周期
- 法律风险工作台
- 供应链风险与关系图
- 内部风险流程和管理辅助
- 外部风险演示流程
- 内置法规库及证据链展示

演示企业、供应商和风险记录均为比赛模拟数据，不代表真实企业、交易或供应关系。

## 4. API Key 与联网功能

### 4.0 硅基流动简介

硅基流动（SiliconFlow）是一个云端 AI 模型服务平台，提供大模型对话、文本向量化
（Embedding）和重排（Rerank）等 API 接口。它不是需要安装在本机上的软件，也不是本项目的
必需运行组件；本桌面包仅在启用在线 AI 能力时，通过网络调用其接口。

如需启用相关在线能力，请在硅基流动控制台注册或登录并创建 API Key：
<https://cloud.siliconflow.cn/>；接口说明见 <https://docs.siliconflow.cn/>。
API Key 是访问云端模型服务的身份凭证，请由主办方自行申请并妥善保管，
同时根据需要设置账户额度或调用限额。本项目不会代为申请，安装包中也不包含任何真实 Key。

在本项目中，硅基流动主要用于以下两类服务：

- 作为向量服务：将法规或上传材料转换为向量，用于语义检索；对应“向量 API Key”。
- 作为对话模型服务：生成在线问答、风险解释或报告文本；对应“LLM API Key”。

同一硅基流动账户的 API Key 通常可以用于上述两类接口，但程序页面仍要求分别填写两个字段，
因为两者对应不同的服务配置。仅进行固定演示时，可以不配置这两项。

常用服务商的 API Key 申请入口如下。具体注册条件、计费规则、可用区域和模型权限以各服务商
当前页面为准：

- 硅基流动：<https://cloud.siliconflow.cn/>
- DeepSeek：<https://platform.deepseek.com/api_keys>
- OpenAI：<https://platform.openai.com/api-keys>
- 通义千问（DashScope）：<https://dashscope.console.aliyun.com/apiKey>
- 智谱开放平台：<https://open.bigmodel.cn/usercenter/apikeys>
- Moonshot Kimi：<https://platform.moonshot.cn/console/api-keys>
- OpenRouter：<https://openrouter.ai/keys>
- Anthropic：<https://console.anthropic.com/settings/keys>
- Google Gemini：<https://aistudio.google.com/app/apikey>
- Tavily：<https://app.tavily.com/>

不配置 API Key，程序也可以正常启动并运行固定演示功能。尤其是以下内容已经随包内置，
不需要联网或 API Key：

- 风险总览、法律风险工作台和预置演示场景
- 产品生命周期页面
- 供应链关系图、节点连线和设计轨迹流动动画
- 内部风险流程、证据链和本包法规库展示

API Key 只影响需要访问外部服务的能力：

- LLM API Key：在线问答、风险解释和报告生成
- 向量 API Key：硅基流动 Embedding，以及材料增量入库/重建索引时的向量化
- 视觉 API Key：图片材料识别；未单独填写时默认沿用 LLM API Key
- 搜索 API Key：Tavily 受控联网检索

API Key 不包含在本包中，也不要把 Key 写进 README、截图或发送邮件正文。

### 4.1 推荐配置方案：硅基流动仅用于向量服务

该方案配置项最少，适用于优先启用法规库检索和材料向量化能力的场景。

1. 启动“识险智控”，进入左侧菜单“系统配置”。
2. 在“模型与检索 → 推理、向量和存储”区域填写以下内容：

   - 向量服务地址：`https://api.siliconflow.cn/v1`
   - 嵌入模型：`BAAI/bge-m3`
   - 向量 API Key：填写在硅基流动控制台创建的 API Key

3. 点击页面右上角“保存配置”。页面仅显示“已配置/未配置”状态，不会回显完整 Key。
4. 关闭并重新启动程序，再进入“系统配置”，确认“向量 API Key”显示为“已配置”。

向量 API Key 与 LLM API Key 分别对应不同服务。仅填写“向量 API Key”时，程序的固定演示仍可用，
Embedding 相关能力可以使用；在线对话模型是否可用，则取决于 LLM 配置。

### 4.2 配置方案：硅基流动同时用于在线 LLM

如需使在线问答和报告生成使用硅基流动，除完成上述向量配置外，还需完成以下 LLM 配置：

1. 在“系统配置 → 模型与检索 → 推理、向量和存储”中，将“服务渠道”设置为“硅基流动”。
2. 选择后，程序会自动填入 OpenAI 兼容地址：
   `https://api.siliconflow.cn/v1`，以及一个推荐对话模型。
3. 根据硅基流动账户实际可用的模型填写“对话模型”；模型名称应以硅基流动控制台显示的名称为准。
4. 在“LLM API Key”中填写硅基流动 API Key。
5. 如同一个硅基流动 API Key 同时用于 Embedding，可将同一个 Key 再填写至“向量 API Key”；
   两个输入框分别对应两类服务，不能以其中一个字段替代另一个字段。
6. 点击“保存配置”，重启程序后再进行在线问答测试。

如不使用硅基流动提供的 LLM，仅需保留其他 LLM 服务的渠道、地址、模型和 LLM API Key，
硅基流动仍可单独作为向量服务使用。

### 4.3 常用 LLM API Key 配置与调用指南

本程序已对常用云端模型服务进行统一适配。使用时不需要编写代码或手工拼接 HTTP 请求，
只需在“系统配置”中选择服务渠道，确认服务地址和模型名称，再填写“LLM API Key”即可。
下表中的模型名称仅为当前界面提供的示例，最终应以服务商账户实际可用的模型为准。

| 服务商 | 服务渠道 | 默认/示例服务地址 | 模型示例 | Key 填写位置 | 主要用途 |
| --- | --- | --- | --- | --- | --- |
| 硅基流动 | 硅基流动 | `https://api.siliconflow.cn/v1` | `deepseek-ai/DeepSeek-V4-Flash` | LLM API Key | 在线问答、风险解释、报告生成 |
| DeepSeek | DeepSeek | `https://api.deepseek.com/v1` | `deepseek-v4-flash` | LLM API Key | 在线问答、风险解释、报告生成 |
| OpenAI | OpenAI | `https://api.openai.com/v1` | `gpt-5.6-luna` | LLM API Key | 在线问答、风险解释、报告生成 |
| 通义千问 | 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3.8-max` | LLM API Key | 在线问答、风险解释、报告生成 |
| 智谱 | 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-5.2` | LLM API Key | 在线问答、风险解释、报告生成 |
| Kimi | Kimi | `https://api.moonshot.cn/v1` | `kimi-k3` | LLM API Key | 在线问答、风险解释、报告生成 |
| OpenRouter | OpenRouter | `https://openrouter.ai/api/v1` | `openai/gpt-5.6-luna` | LLM API Key | 统一代理多家模型 |
| Anthropic | Anthropic | `https://api.anthropic.com` | `claude-sonnet-5` | LLM API Key | 在线问答、风险解释、报告生成 |
| Google | Google Gemini | `https://generativelanguage.googleapis.com` | `gemini-3.7-flash` | LLM API Key | 在线问答、风险解释、报告生成 |

配置步骤如下：

1. 在对应服务商的官方控制台注册或登录，创建具备模型调用权限的 API Key，并确认账户额度、
   区域限制及模型权限均满足使用要求。
2. 进入“系统配置 → 模型与检索 → 推理、向量和存储”。
3. 在“服务渠道”中选择相应服务商。对于 OpenAI、DeepSeek、通义千问、智谱、Kimi、
   硅基流动和 OpenRouter，系统使用 OpenAI 兼容协议；Anthropic 和 Google Gemini 使用各自的
   原生协议。
4. 检查自动填入的“LLM 服务地址”和“对话模型”。如服务商控制台提供了不同模型，
   请将“对话模型”改为账户实际可用的模型名称。
5. 在“LLM API Key”中填写对应 Key，点击“保存配置”，然后点击“测试连接”。

需要注意：LLM API Key 仅用于在线对话和文本生成，不会自动替代“向量 API Key”。如果需要
材料增量检索、上传材料向量化或重建索引，还应单独配置向量服务；硅基流动的配置方法见
[4.1](#41-推荐配置方案硅基流动仅用于向量服务)。

#### 4.3.1 图片识别 API Key

如需识别图片材料，请开启“启用图片材料识别”，并填写“视觉模型服务地址”“视觉模型”和
“视觉 API Key”。视觉模型必须具备图像理解能力。若视觉服务与 LLM 使用同一服务商，
“视觉模型服务地址”可以留空；“视觉 API Key”留空时，系统会沿用“LLM API Key”。

图片识别仅用于提取图片中可见的事实信息，不直接构成法律依据；法律结论仍以法规库、
证据链和人工复核为准。

#### 4.3.2 Tavily 搜索 API Key

如需受控联网检索，可使用 Tavily：

1. 在 [Tavily 控制台](https://app.tavily.com/)注册或登录并创建 Search API Key。
2. 在“系统配置 → 联网检索 → 实时法规与外部事实”中，将“搜索服务”设置为“Tavily API”。
3. 开启“启用受控联网检索”，在“搜索 API Key”中填写 Tavily Key。
4. 点击“保存配置”，再点击“测试联网检索”。

联网检索只作为实时事实补充，不能替代本地法规库，也不能将搜索结果直接视为法律依据。

#### 4.3.3 常用服务的 PowerShell 调用配置示例

以下示例用于说明各服务商的调用参数对应关系。实际使用时，建议优先通过“系统配置”页面
完成配置；如需使用 PowerShell 启动，则只需替换服务地址、模型名称和 API Key：

```powershell
# DeepSeek 示例
$env:LLM_BASE_URL = "https://api.deepseek.com/v1"
$env:LLM_MODEL = "控制台中实际可用的模型名称"
$env:LLM_API_KEY = "主办方自己的 DeepSeek Key"

# 如需切换为其他 OpenAI 兼容服务，只替换以下三项：
# OpenAI      https://api.openai.com/v1
# 通义千问    https://dashscope.aliyuncs.com/compatible-mode/v1
# 智谱        https://open.bigmodel.cn/api/paas/v4
# Kimi        https://api.moonshot.cn/v1
# OpenRouter  https://openrouter.ai/api/v1
# 硅基流动    https://api.siliconflow.cn/v1

& ".\RiskFlow-0.5.2-x64-portable.exe"
```

Anthropic 和 Google Gemini 使用原生协议，不能仅通过替换 OpenAI 兼容地址来调用，
应在“服务渠道”中分别选择“Anthropic”或“Google Gemini”，并按照界面自动填入的协议配置
填写模型和 LLM API Key。通过 PowerShell 配置时，协议标识分别为
`anthropic_messages` 和 `gemini_generate_content`。硅基流动的 Embedding 调用仍需单独设置：

```powershell
$env:SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
$env:EMBEDDING_MODEL = "BAAI/bge-m3"
$env:SILICONFLOW_API_KEY = "主办方自己的硅基流动 Key"
```

程序会根据上述配置自动调用对话、Embedding、重排或搜索接口。除 Key 外，通常还需要确认
账户额度、模型权限、网络访问和服务商安全策略；出现 401/403 时，建议优先检查 Key 是否有效、
模型名称是否具备调用权限，以及地址与服务渠道是否匹配。

#### 4.3.4 本地 Ollama（无需 API Key）

如主办方已有本地 Ollama 服务，可在“服务渠道”中选择“Ollama”，地址使用
`http://127.0.0.1:11434/v1`，并填写本机已下载的模型名称；通常不需要 API Key。
但 Ollama 不包含在本桌面包中，需主办方自行安装、下载模型并确保服务已启动。

### 4.4 实时行情与 RSS（按需配置）

在“外部市场与情报 → 数据获取策略”中根据需要开启相应开关。实时行情和 RSS 并非固定演示
的前置条件，建议在比赛现场确认网络和数据源可用后再开启。

### 4.5 配置完成后的检查顺序

建议按照以下顺序进行检查，以便定位配置问题：

1. 进入“系统配置”，确认后端地址已连接。
2. 确认“向量 API Key”显示“已配置”，并检查地址和模型是否分别为
   `https://api.siliconflow.cn/v1`、`BAAI/bge-m3`。
3. 如需在线问答，确认“LLM API Key”也显示“已配置”，并点击“测试连接”。
4. 如需联网检索，再单独配置搜索 API Key 并点击“测试联网检索”。
5. 重启程序，确认配置仍然保留。程序会将已保存配置放在当前用户的运行数据目录中，
   不会写入安装目录或程序包内部。

### 4.6 无法进入系统配置时的备用配置方法（PowerShell）

如暂时无法进入系统配置页面，也可以在启动程序前通过 PowerShell 临时设置环境变量。
以下内容中的 Key 均为示例占位符，请替换为主办方自行申请的 Key：

```powershell
$env:SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
$env:EMBEDDING_MODEL = "BAAI/bge-m3"
$env:SILICONFLOW_API_KEY = "主办方自己的硅基流动 Key"

# 仅在需要使用硅基流动在线问答时设置以下三项
$env:LLM_BASE_URL = "https://api.siliconflow.cn/v1"
$env:LLM_MODEL = "控制台中实际可用的模型名称"
$env:LLM_API_KEY = "主办方自己的硅基流动 Key"

& ".\RiskFlow-0.5.2-x64-portable.exe"
```

该方式仅对当前 PowerShell 窗口有效。通过“系统配置”保存的设置会在程序重启后继续有效；
如果环境变量与页面保存值同时存在，则以当前启动环境变量为准。

如不配置，相关在线能力会保持关闭或返回保守提示，不影响桌面程序启动和固定演示。

## 5. 法规知识库基线

本包使用比赛提交基线知识库 `legal_knowledge_staging_20260811`，包含更新后的
《中华人民共和国生态环境法典》：版本 2026，生效日期 2026-08-15。

## 6. Windows 安全提示

当前版本未配置发布者代码签名证书，Windows 可能显示“未知发布者”或 SmartScreen
提示。确认文件来源后选择继续运行即可；这不代表程序运行失败。

## 7. 演示建议

建议先从首页进入风险总览，再依次查看法律风险、供应链、内部风险和外部风险页面。
如果需要展示在线问答或实时数据，请先配置 API Key 和网络访问权限。
