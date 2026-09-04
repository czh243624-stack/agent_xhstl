param(
    [string]$ListenAddress = "127.0.0.1:18060",
    [switch]$Headful
)

$ErrorActionPreference = "Stop"
$runtimeDir = $PSScriptRoot
$exePath = Join-Path $runtimeDir "xiaohongshu-mcp.exe"
$dataDir = Join-Path $runtimeDir "data"
$logDir = Join-Path $runtimeDir "logs"
$pidPath = Join-Path $runtimeDir "xiaohongshu-mcp.pid"

if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Missing executable: $exePath"
}

if (Test-Path -LiteralPath $pidPath) {
    $savedPid = [int](Get-Content -LiteralPath $pidPath -Raw)
    $existing = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "xiaohongshu-mcp is already running (PID $savedPid)."
        exit 0
    }
    Remove-Item -LiteralPath $pidPath -Force
}

New-Item -ItemType Directory -Force -Path $dataDir, $logDir | Out-Null
$env:COOKIES_PATH = Join-Path $dataDir "cookies.json"

$arguments = @("-port", $ListenAddress)
if ($Headful) {
    $arguments += "-headless=false"
}

$process = Start-Process `
    -FilePath $exePath `
    -ArgumentList $arguments `
    -WorkingDirectory $runtimeDir `
    -RedirectStandardOutput (Join-Path $logDir "stdout.log") `
    -RedirectStandardError (Join-Path $logDir "stderr.log") `
    -WindowStyle Hidden `
    -PassThru

Set-Content -LiteralPath $pidPath -Value $process.Id
Write-Host "xiaohongshu-mcp started (PID $($process.Id))."
Write-Host "MCP URL: http://$ListenAddress/mcp"
Write-Host "Health:  http://$ListenAddress/health"
