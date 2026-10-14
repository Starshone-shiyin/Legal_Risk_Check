param(
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"
$desktopRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $desktopRoot
$specPath = Join-Path $desktopRoot "backend\riskflow-backend.spec"
$distPath = Join-Path $desktopRoot "runtime-build\backend"
$workPath = Join-Path $desktopRoot "runtime-build\pyinstaller"

if (-not $PythonPath) {
    $PythonPath = Join-Path $projectRoot "venv\Scripts\python.exe"
}
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    $PythonPath = "python"
}

& $PythonPath -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "当前 Python 未安装 PyInstaller。请先在用于构建的环境中安装 PyInstaller，再重新运行本脚本。"
}

New-Item -ItemType Directory -Force -Path $distPath, $workPath | Out-Null
$pyinstallerArgs = @(
    $specPath,
    "--noconfirm",
    "--clean",
    "--distpath", $distPath,
    "--workpath", $workPath
)
& $PythonPath -m PyInstaller @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller 后端构建失败，退出码：$LASTEXITCODE"
}

Write-Host "FastAPI 后端运行时已生成：$distPath\riskflow-backend"
