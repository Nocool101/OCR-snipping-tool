# 把工具打包成单文件 exe：dist\screenshot-ocr.exe
# 用法：powershell -ExecutionPolicy Bypass -File build.ps1
# 可用环境变量 PYTHON 指定解释器（默认 python）。

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

Write-Host "[1/3] 安装打包依赖"
& $python -m pip install -r (Join-Path $root "packaging\requirements.txt")

Write-Host "[2/3] 生成图标"
& $python (Join-Path $root "packaging\make_icon.py")

Write-Host "[3/3] 运行 PyInstaller"
& $python -m PyInstaller --noconfirm --clean `
    --distpath (Join-Path $root "dist") `
    --workpath (Join-Path $root "build") `
    (Join-Path $root "packaging\screenshot-ocr.spec")

Write-Host "完成：$(Join-Path $root 'dist\screenshot-ocr.exe')"
