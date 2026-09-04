$ErrorActionPreference = "Stop"
$runtimeDir = $PSScriptRoot
$exePath = (Join-Path $runtimeDir "xiaohongshu-mcp.exe")
$pidPath = Join-Path $runtimeDir "xiaohongshu-mcp.pid"

if (-not (Test-Path -LiteralPath $pidPath)) {
    Write-Host "xiaohongshu-mcp is not running (no PID file)."
    exit 0
}

$savedPid = [int](Get-Content -LiteralPath $pidPath -Raw)
$process = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item -LiteralPath $pidPath -Force
    Write-Host "xiaohongshu-mcp is not running; removed stale PID file."
    exit 0
}

if ($process.Path -ne $exePath) {
    throw "PID $savedPid belongs to a different executable; refusing to stop it."
}

Stop-Process -Id $savedPid
$process.WaitForExit()
Remove-Item -LiteralPath $pidPath -Force
Write-Host "xiaohongshu-mcp stopped."
