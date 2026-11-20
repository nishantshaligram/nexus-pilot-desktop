<#
.SYNOPSIS
    NexusPilot Automated Installer & Environment Setup
.DESCRIPTION
    Installs required Python packages, verifies native Win32/UIA hooks,
    and configures the local MCP server.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "Installing NexusPilot dependencies from $ProjectRoot\requirements.txt..." -ForegroundColor Cyan
& python -m pip install --user -r "$ProjectRoot\requirements.txt"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install some dependencies. Please review pip output above." -ForegroundColor Red
} else {
    Write-Host "All dependencies installed successfully!" -ForegroundColor Green
}

Write-Host "`nRunning environment diagnostic..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$ScriptDir\verify-environment.ps1"
