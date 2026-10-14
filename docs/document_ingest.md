# 文件接入与 MineU

法律工作台的文件接入流程为：上传材料、由 MineU 云端 API 解析为 Markdown、在材料面板中选择附件后随本次问题送入 LLM、预览或下载。支持 PDF、Word、PowerPoint、Excel、图片以及 UTF-8 编码的 TXT、Markdown、CSV。上传的 PDF、Office 和图片会离开本机并发送给 MineU；TXT、Markdown、CSV 仅在本地提取文本。解析结果默认标记为“未入库”，不会自动写入 Qdrant。

每次 LLM 分析最多选择 3 份已完成解析的材料，单份最多带入 12,000 个字符，总量最多 24,000 个字符。上传材料仅作为事实背景，不能代替法律法规证据，也不会覆盖系统的法律依据和引用校验。

## 图片材料识别

默认启用 `deepseek-v4-flash-vision-exp` 对最多 3 张、单张不超过 5 MB 的已选图片提取可见事实，例如主体名称、日期、金额、印章、签名、表格字段和无法辨认之处。视觉模型只会补充用户材料事实，绝不会进入法律依据、证据链或法条引用。根据 DeepSeek 图像理解接口限制，视觉调用仅发送 JPEG、PNG、GIF、WebP；JP2、BMP 仍可上传给 MineU 解析，但不会发送至视觉模型。视觉调用失败时，系统仍会使用 MineU 的 Markdown 解析结果继续回答。

视觉模型默认沿用主 LLM 的 OpenAI 兼容服务地址与 API Key，也可在设置页单独配置。相关环境变量为 `VISION_LLM_ENABLED`、`VISION_LLM_BASE_URL`、`VISION_LLM_MODEL` 与 `VISION_LLM_API_KEY`。旧版 `doc`、`ppt`、`xls` 的云端解析兼容性取决于 MineU；失败时请导出为 `docx`、`pptx` 或 `xlsx` 后重试。

## MineU 轻量 API

轻量 API 不需要 Token，也不需要安装本地模型。根据 MineU 官方文档，单文件不超过 10 MB；本系统对 PDF 额外限制为最多 20 页，适合常规合同审查。其他格式的具体页数或容量限制以 MineU 云端返回为准。默认配置已启用，无需额外操作。

可选配置：

```dotenv
MINEU_MODE=lightweight
MINEU_API_BASE_URL=https://mineru.net
MINEU_TIMEOUT_SECONDS=300
MINEU_API_POLL_SECONDS=2
DOCUMENT_UPLOAD_MAX_BYTES=10485760
```

重启后通过 `GET /documents/capabilities` 查看状态。轻量 API 不使用 Token。

## 可选本地模式

如确需本地解析，可将 `MINEU_MODE=local` 并设置 `MINEU_COMMAND=mineru`。上传大小上限可通过 `DOCUMENT_UPLOAD_MAX_BYTES` 调整；原文件、任务元数据和 MineU 输出保存在 `data/document_ingest/`，该目录已被 Git 忽略。解析失败的合同可在工作台中直接重新解析。
