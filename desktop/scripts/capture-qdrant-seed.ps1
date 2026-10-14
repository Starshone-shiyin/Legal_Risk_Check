param(
    [string]$ContainerName = "qdrant",
    [string]$CollectionName = "legal_knowledge_staging_20260811",
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$desktopRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $desktopRoot "runtime-build\qdrant-storage-seed"
}

$container = docker inspect $ContainerName 2>$null
if ($LASTEXITCODE -ne 0 -or -not $container) {
    throw "找不到 Docker 容器：$ContainerName"
}
$state = docker inspect $ContainerName --format "{{.State.Status}}"
if ($LASTEXITCODE -ne 0) {
    throw "无法读取 Docker 容器状态：$ContainerName"
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
if (Test-Path -LiteralPath (Join-Path $OutputDirectory "collections")) {
    throw "输出目录已经包含 collections，为避免把历史 collection 混入，请换一个空目录：$OutputDirectory"
}
$pausedByScript = $false
try {
    if ($state -eq "running") {
        docker pause $ContainerName | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "无法暂停 Qdrant 容器，未复制知识库。"
        }
        $pausedByScript = $true
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $OutputDirectory "collections"), (Join-Path $OutputDirectory "aliases"), (Join-Path $OutputDirectory ".deleted") | Out-Null
    docker cp "${ContainerName}:/qdrant/storage/collections/$CollectionName" (Join-Path $OutputDirectory "collections")
    if ($LASTEXITCODE -ne 0) {
        throw "复制 Qdrant collection 失败：$CollectionName"
    }
    docker cp "${ContainerName}:/qdrant/storage/raft_state.json" $OutputDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "复制 Qdrant raft state 失败。"
    }
    docker cp "${ContainerName}:/qdrant/storage/aliases/." (Join-Path $OutputDirectory "aliases")
    if ($LASTEXITCODE -ne 0) {
        throw "复制 Qdrant aliases 失败。"
    }
} finally {
    if ($pausedByScript) {
        docker unpause $ContainerName | Out-Null
    }
}

$collectionsPath = Join-Path $OutputDirectory "collections"
if (-not (Test-Path -LiteralPath $collectionsPath -PathType Container)) {
    throw "复制结果缺少 collections 目录：$OutputDirectory"
}
$collectionPath = Join-Path $collectionsPath $CollectionName
if (-not (Test-Path -LiteralPath $collectionPath -PathType Container)) {
    throw "复制结果缺少目标 collection：$CollectionName"
}
Write-Host "Qdrant storage seed 已冻结：$OutputDirectory"
Write-Host "  Collection: $CollectionName"
Write-Host "容器状态已恢复：$state"
