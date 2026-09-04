$ErrorActionPreference = "Stop"
$projectDir = $PSScriptRoot
$pidPath = Join-Path $projectDir ".page.pid"

if (-not (Test-Path -LiteralPath $pidPath)) {
    Write-Host "Research desk is not running."
    exit 0
}

$savedPid = [int](Get-Content -LiteralPath $pidPath -Raw)
$process = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $savedPid
    $process.WaitForExit()
}
Remove-Item -LiteralPath $pidPath -Force
Write-Host "Research desk stopped."
