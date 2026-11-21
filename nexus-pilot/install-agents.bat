@echo off
setlocal
echo =======================================================
echo    NexusPilot 1-Click Multi-Agent MCP Installer
echo =======================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-agents.ps1" %*
echo.
pause
