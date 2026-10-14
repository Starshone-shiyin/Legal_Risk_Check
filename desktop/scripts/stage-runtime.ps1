param(
    [string]$BackendBundle,
    [string]$BackendExecutable,
    [Parameter(Mandatory = $true)]
    [string]$QdrantExecutable,
    [string]$QdrantStorageSeed,
    [string]$DataSeed
)

$ErrorActionPreference = "Stop"
$desktopRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $desktopRoot "runtime\backend"
$qdrantDir = Join-Path $desktopRoot "runtime\qdrant"
$dataDir = Join-Path $desktopRoot "runtime\data-seed"

if (-not $BackendBundle -and -not $BackendExecutable) {
    throw "必须提供 BackendBundle 或 BackendExecutable。优先使用 PyInstaller 的 BackendBundle。"
}
if ($BackendBundle -and -not (Test-Path -LiteralPath $BackendBundle -PathType Container)) {
    throw "后端运行时目录不存在：$BackendBundle"
}
if ($BackendExecutable -and -not (Test-Path -LiteralPath $BackendExecutable -PathType Leaf)) {
    throw "后端运行时文件不存在：$BackendExecutable"
}
if (-not (Test-Path -LiteralPath $QdrantExecutable -PathType Leaf)) {
    throw "Qdrant 运行时文件不存在：$QdrantExecutable"
}

New-Item -ItemType Directory -Force -Path $backendDir, $qdrantDir | Out-Null
if ($BackendBundle) {
    Copy-Item -Path (Join-Path $BackendBundle "*") -Destination $backendDir -Recurse -Force
} else {
    Copy-Item -LiteralPath $BackendExecutable -Destination (Join-Path $backendDir "riskflow-backend.exe") -Force
}
Copy-Item -LiteralPath $QdrantExecutable -Destination (Join-Path $qdrantDir "qdrant.exe") -Force

if ($QdrantStorageSeed) {
    if (-not (Test-Path -LiteralPath $QdrantStorageSeed -PathType Container)) {
        throw "Qdrant 知识库种子目录不存在：$QdrantStorageSeed"
    }
    $seedDir = Join-Path $qdrantDir "storage-seed"
    $sourcePath = (Resolve-Path -LiteralPath $QdrantStorageSeed).Path.TrimEnd('\')
    $targetPath = $seedDir.TrimEnd('\')
    if ($sourcePath -ne $targetPath) {
        New-Item -ItemType Directory -Force -Path $seedDir | Out-Null
        Copy-Item -Path (Join-Path $QdrantStorageSeed "*") -Destination $seedDir -Recurse -Force
    } else {
        Write-Host "Qdrant storage seed 已在目标目录，跳过复制。"
    }
}

if ($DataSeed) {
    if (-not (Test-Path -LiteralPath $DataSeed -PathType Container)) {
        throw "比赛演示数据种子目录不存在：$DataSeed"
    }
    $sourcePath = (Resolve-Path -LiteralPath $DataSeed).Path.TrimEnd('\')
    $targetPath = $dataDir.TrimEnd('\')
    if ($sourcePath -ne $targetPath) {
        New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
        Copy-Item -Path (Join-Path $DataSeed "*") -Destination $dataDir -Recurse -Force
    } else {
        Write-Host "比赛演示数据已在目标目录，跳过复制。"
    }
}

Write-Host "已准备 Electron 运行时："
Write-Host "  Backend: $backendDir"
Write-Host "  Qdrant:  $qdrantDir\qdrant.exe"
if ($QdrantStorageSeed) { Write-Host "  Seed:    $qdrantDir\storage-seed" }
if ($DataSeed) { Write-Host "  Data:    $dataDir" }
