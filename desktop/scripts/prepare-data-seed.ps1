param(
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$desktopRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $desktopRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $desktopRoot "runtime\data-seed"
}

$files = @(
    "data\internal_risk_workflow.json",
    "data\risk_intake.json",
    "data\supply_chain.json",
    "data\external_risk\workflow_graph.json"
)

New-Item -ItemType Directory -Force -Path $OutputDirectory, (Join-Path $OutputDirectory "external_risk") | Out-Null
foreach ($relativePath in $files) {
    $source = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "演示数据不存在：$source"
    }
    $target = Join-Path $OutputDirectory ($relativePath -replace '^data\\', '')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
}
Write-Host "比赛演示数据种子已准备：$OutputDirectory"
Write-Host "已排除 document_ingest、外部情报缓存和用户 Skill 数据。"
