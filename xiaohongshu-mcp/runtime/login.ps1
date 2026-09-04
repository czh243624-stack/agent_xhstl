$ErrorActionPreference = "Stop"
$runtimeDir = $PSScriptRoot
$exePath = Join-Path $runtimeDir "xiaohongshu-login.exe"
$dataDir = Join-Path $runtimeDir "data"

if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Missing executable: $exePath"
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$env:COOKIES_PATH = Join-Path $dataDir "cookies.json"
Push-Location $runtimeDir
try {
    & $exePath
} finally {
    Pop-Location
}
