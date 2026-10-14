# Qdrant runtime staging

此目录不提交 Qdrant 二进制文件。打包前使用 `desktop/scripts/download-qdrant.ps1`
下载经过固定 SHA-256 校验的 Windows x64 Qdrant，再使用
`desktop/scripts/stage-runtime.ps1` 放入这里，文件名为 `qdrant.exe`。
`storage-seed/` 是与 Qdrant 版本配套的比赛知识库初始数据；不要手工替换为其他
版本或其他日期的索引。
