param(
    [string]$Version = "1.17.1",
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$desktopRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $desktopRoot "runtime-build\qdrant"
}

$assetName = "qdrant-x86_64-pc-windows-msvc.zip"
$downloadUrl = "https://github.com/qdrant/qdrant/releases/download/v$Version/$assetName"
$expectedHashes = @{
    "1.17.1" = "FE28DF5993A9F9830B1E7290E2E341BECF3C91366941B73B4322A05E4F91585C"
}

if (-not $expectedHashes.ContainsKey($Version)) {
    throw "未配置版本 $Version 的固定 SHA-256。请先人工审核发布资产，再把哈希加入本脚本。"
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$zipPath = Join-Path $OutputDirectory $assetName
$extractPath = Join-Path $OutputDirectory "extracted-$Version"
$targetPath = Join-Path $OutputDirectory "qdrant.exe"

if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
    $actual = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
    if ($actual -eq $expectedHashes[$Version]) {
        Write-Host "Qdrant $Version 已存在且哈希匹配：$targetPath"
        exit 0
    }
    throw "已有 qdrant.exe 哈希不匹配：$targetPath。请移走后重新下载，不自动覆盖。"
}

Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath
$zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash
if ($zipHash -ne $expectedHashes[$Version]) {
    throw "Qdrant 压缩包 SHA-256 校验失败：期望 $($expectedHashes[$Version])，实际 $zipHash"
}

Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath -Force
$candidate = Get-ChildItem -LiteralPath $extractPath -Filter "qdrant.exe" -Recurse -File | Select-Object -First 1
if (-not $candidate) {
    throw "压缩包中未找到 qdrant.exe：$zipPath"
}
Copy-Item -LiteralPath $candidate.FullName -Destination $targetPath -Force
$binaryHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
Write-Host "Qdrant $Version 已下载并校验：$targetPath"
Write-Host "  SHA-256: $binaryHash"
