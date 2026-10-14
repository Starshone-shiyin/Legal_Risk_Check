# 消息面与政策面外部风险监测

## 已实现的基础设施

消息与政策监测采用已核验的财经直连源和可配置 HTTPS RSS/Atom 源，不依赖浏览器会话或大模型即时判断。处理链路为：

`来源配置 -> RSS/Atom 解析 -> 规则命中 -> 去重与缓存 -> 外部风险信号 -> 法律检索任务`

每条生成的信号保留来源链接、发布时间、摘要、命中规则、影响领域和 `requires_human_review=true`。新闻和政策只构成需要复核的事实背景，不能直接作为法律结论或法律依据。

缓存文件为 `data/external_risk/intelligence_feed_cache.json`。默认 300 秒内读取缓存，避免市场页面重复访问外部来源；`POST /external-risk/intelligence/refresh` 可用于人工强制刷新。缓存采用临时文件替换，避免并发读取到不完整 JSON。

`GET /external-risk/intelligence/status` 返回每个源的抓取状态、最近检查和成功时间、原始条目数、命中信号数与失败原因。一个源临时失败时，系统保留该源最近成功的可复核信号并标记 `source_stale=true`，其他来源继续更新，不会因单点网络异常清空风险输入。

默认核心订阅包含已核验的财经、监管和政策来源：

1. 财联社电报：`https://www.cls.cn/api/cache` 的公开实时电报接口，按电报 ID 生成可追溯链接。
2. 第一财经全球市场大直播：`https://www.yicai.com/` 的公开快讯区，按文章链接生成可追溯信号。
3. 中国证监会政务信息：`https://www.csrc.gov.cn/csrc/zwxx/index.shtml`，提取监管措施和行政处罚的正式文章链接。
4. 商务部政策发布：`https://www.mofcom.gov.cn/zcfb/`，提取出口管理、贸易救济和贸易政策的正式文章链接。
5. 国家发展改革委通知公告：`https://www.ndrc.gov.cn/xwdt/tzgg/`，提取输配电价、能耗约束和能源供应链相关通知。

所有来源均先经过“行业范围词 + 风险触发词”规则。普通合作、扩产和市场评论不会单独增加风险；出口管制、贸易救济、处罚、调查、供应中断和数据泄露等事件才会进入风险系数。官方来源的信号保留来源可信度与风险相关度：个案监管执法默认作为较低权重的可复核观察，贸易及能源政策按其外部影响范围加权；未完成企业、产品或合同对象映射前，不会将个案处罚等同于目标企业风险。

## 启用方式

在启动后端的环境中配置经审核的 HTTPS 源：

```powershell
$env:EXTERNAL_RISK_INTELLIGENCE_ENABLED = "true"
$env:EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED = "true"
$env:EXTERNAL_RISK_INTELLIGENCE_POLL_SECONDS = "300"
$env:EXTERNAL_RISK_INTELLIGENCE_FEEDS = '[
  {"id":"gov-policy","name":"国务院政策","type":"policy","url":"https://example.gov.cn/policy.rss"},
  {"id":"trade-news","name":"贸易合规快讯","type":"news","url":"https://example.org/trade.atom"}
]'
.\start_backend.ps1 -EnableLiveIntelligence
```

启动脚本默认启用核心订阅和后端内置轮询；启动后立即执行一次抓取，随后按 `EXTERNAL_RISK_INTELLIGENCE_POLL_SECONDS` 轮询。使用 `-DisableLiveIntelligence` 可关闭。自定义源仅接受 HTTPS；无效 JSON、非 HTTPS 地址、未知类型均会被忽略。`type` 只能是 `news` 或 `policy`，`adapter` 可为 `rss_atom`、`cailianshe_telegraph`、`yicai_homepage` 或 `official_policy_html`。可选的 `risk_relevance` 为 `0.1` 至 `1.0`，表示消息对当前外部风险评分的默认相关度，不改变原始证据的可信度。

## 当前规则

内置规则覆盖出口管制、半导体供应链、数据合规、贸易救济与证券披露。命中规则后按来源类型和命中数量计算置信度；包含禁止、限制、制裁、处罚、立案等升级词时，风险级别上调一级。规则标识随信号返回，便于法务复核与后续调整。

## 上线前规划

1. 建立经过法务和业务确认的来源清单，按监管、交易所、主管部门、行业协会、企业公告和国际规则库分类。
2. 生产部署时将当前内置轮询迁移给独立调度器，补充指数退避、失败告警和跨进程单实例锁。
3. 将缓存升级为数据库事实表，记录原文快照哈希、抓取时间、来源版本、去重键和人工处置状态。
4. 为每条规则配置企业、产品、地区、供应链节点和合同类型的适用范围，并通过人工标注样本评估准确率、漏报率与时效。
5. 将已复核事件映射到法律 RAG 查询和风险任务；未复核事件只能显示为外部观察信号。
