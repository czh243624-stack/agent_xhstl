param([string]$ListenAddress = "127.0.0.1", [int]$Port = 1686)

$ErrorActionPreference = "Stop"
$projectDir = $PSScriptRoot
$runtimeDir = Join-Path $projectDir "xiaohongshu-mcp\runtime"
$pagePidPath = Join-Path $projectDir ".page.pid"
$logDir = Join-Path $projectDir ".logs"

try {
    Invoke-RestMethod -Uri "http://127.0.0.1:18060/health" -TimeoutSec 2 | Out-Null
} catch {
    & (Join-Path $runtimeDir "start.ps1")
}

if (Test-Path -LiteralPath $pagePidPath) {
    $savedPid = [int](Get-Content -LiteralPath $pagePidPath -Raw)
    if (Get-Process -Id $savedPid -ErrorAction SilentlyContinue) {
        Write-Host "Research desk is already running (PID $savedPid)."
        Write-Host "Open http://${ListenAddress}:$Port"
        exit 0
    }
    Remove-Item -LiteralPath $pagePidPath -Force
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$process = Start-Process `
    -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "app:app", "--host", $ListenAddress, "--port", $Port) `
    -WorkingDirectory $projectDir `
    -RedirectStandardOutput (Join-Path $logDir "page-stdout.log") `
    -RedirectStandardError (Join-Path $logDir "page-stderr.log") `
    -WindowStyle Hidden `
    -PassThru

Set-Content -LiteralPath $pagePidPath -Value $process.Id
Write-Host "Research desk started (PID $($process.Id))."
Write-Host "Open http://${ListenAddress}:$Port"
