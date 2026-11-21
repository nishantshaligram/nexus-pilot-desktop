<#
.SYNOPSIS
    NexusPilot Universal Multi-Agent Installer
.DESCRIPTION
    Configures and installs NexusPilot for Antigravity, Claude (Code & Desktop),
    Cursor, and Windsurf with zero manual JSON editing.
    Includes an interactive menu when invoked with zero flags.
.PARAMETER TargetAgent
    Target agent to install for: 'All', 'Antigravity', 'Claude', 'Cursor', 'Windsurf', 'Antigravity+Claude'.
#>

param(
    [string]$TargetAgent = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = (Split-Path -Parent $ScriptDir).Replace("\", "/")
$ServerScript = "$ProjectRoot/server/pilot_server.py"

# Detect Python executable
$PyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PyExe) {
    $PyExe = "python"
} else {
    $PyExe = $PyExe.Replace("\", "/")
}

$McpServerDef = @{
    command = $PyExe
    args = @($ServerScript)
    description = "NexusPilot Windows Desktop Computer-Use Engine"
}

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "   NexusPilot Universal Agent MCP & Plugin Installer   " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Server Script: $ServerScript" -ForegroundColor Gray
Write-Host "Python Binary: $PyExe`n" -ForegroundColor Gray

# Interactive Menu when invoked with zero flags
if ([string]::IsNullOrWhiteSpace($TargetAgent)) {
    Write-Host "No target environment specified. Choose an option:" -ForegroundColor Yellow
    Write-Host "  [1] All (Antigravity, Claude, Cursor, Windsurf) [Default]" -ForegroundColor White
    Write-Host "  [2] Google Antigravity Only" -ForegroundColor White
    Write-Host "  [3] Claude Only (Desktop & Code CLI)" -ForegroundColor White
    Write-Host "  [4] Cursor IDE Only" -ForegroundColor White
    Write-Host "  [5] Windsurf Only" -ForegroundColor White
    Write-Host "  [6] Antigravity + Claude Only" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Enter choice [1-6] (Press Enter for 1)"
    switch ($choice.Trim()) {
        "2" { $TargetAgent = "Antigravity" }
        "3" { $TargetAgent = "Claude" }
        "4" { $TargetAgent = "Cursor" }
        "5" { $TargetAgent = "Windsurf" }
        "6" { $TargetAgent = "Antigravity+Claude" }
        Default { $TargetAgent = "All" }
    }
    Write-Host "`nSelected Target: $TargetAgent`n" -ForegroundColor Cyan
}

function Update-McpConfigFile {
    param(
        [string]$FilePath,
        [string]$AgentName
    )

    try {
        $Dir = Split-Path -Parent $FilePath
        if (-not (Test-Path $Dir)) {
            New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        }

        $config = @{}
        if (Test-Path $FilePath) {
            try {
                $raw = Get-Content $FilePath -Raw -ErrorAction Stop
                if ($raw.Trim()) {
                    $config = $raw | ConvertFrom-Json -AsHashtable
                }
            } catch {
                Write-Host "    [!] Warning: Existing $FilePath was malformed; recreating safely." -ForegroundColor Yellow
                $config = @{}
            }
        }

        if (-not $config.ContainsKey("mcpServers") -or ($null -eq $config["mcpServers"])) {
            $config["mcpServers"] = @{}
        }

        $config["mcpServers"]["nexus-pilot"] = $McpServerDef

        $jsonOutput = $config | ConvertTo-Json -Depth 10
        Set-Content -Path $FilePath -Value $jsonOutput -Encoding UTF8 -Force
        Write-Host "    [x] Configured $AgentName successfully!" -ForegroundColor Green
        Write-Host "        Config: $FilePath" -ForegroundColor Gray
    } catch {
        Write-Host "    [-] Failed to configure $AgentName`: $_" -ForegroundColor Red
    }
}

# 1. Antigravity Installation
if ($TargetAgent -in @("All", "Antigravity", "Antigravity+Claude")) {
    Write-Host "[*] Installing for Google Antigravity..." -ForegroundColor Cyan
    $PluginTargetDir = "$HOME/.gemini/config/plugins/nexus-pilot"
    try {
        if (-not (Test-Path $PluginTargetDir)) {
            New-Item -ItemType Directory -Path $PluginTargetDir -Force | Out-Null
        }
        # Copy full plugin contents
        Copy-Item -Path "$ProjectRoot/*" -Destination $PluginTargetDir -Recurse -Force | Out-Null
        Write-Host "    [x] Plugin bundle installed in: $PluginTargetDir" -ForegroundColor Green

        # Also configure global Antigravity MCP server entry
        $AgyMcpPath = "$HOME/.gemini/antigravity/mcp_config.json"
        Update-McpConfigFile -FilePath $AgyMcpPath -AgentName "Antigravity Global MCP"
    } catch {
        Write-Host "    [-] Antigravity plugin installation failed: $_" -ForegroundColor Red
    }
}

# 2. Claude (Claude Code & Claude Desktop)
if ($TargetAgent -in @("All", "Claude", "Antigravity+Claude")) {
    Write-Host "`n[*] Installing for Claude..." -ForegroundColor Cyan
    # A. Claude Code CLI (~/.claude.json)
    $ClaudeCodePath = "$HOME/.claude.json"
    Update-McpConfigFile -FilePath $ClaudeCodePath -AgentName "Claude Code CLI"

    # B. Claude Desktop App (%APPDATA%\Claude\claude_desktop_config.json)
    $ClaudeDesktopPath = "$env:APPDATA/Claude/claude_desktop_config.json"
    Update-McpConfigFile -FilePath $ClaudeDesktopPath -AgentName "Claude Desktop App"
}

# 3. Cursor IDE
if ($TargetAgent -in @("All", "Cursor")) {
    Write-Host "`n[*] Installing for Cursor IDE..." -ForegroundColor Cyan
    $CursorMcpPath = "$HOME/.cursor/mcp.json"
    Update-McpConfigFile -FilePath $CursorMcpPath -AgentName "Cursor Global MCP"
}

# 4. Windsurf / Codeium
if ($TargetAgent -in @("All", "Windsurf")) {
    Write-Host "`n[*] Installing for Windsurf / Codeium..." -ForegroundColor Cyan
    $WindsurfPath = "$HOME/.codeium/windsurf/mcp_config.json"
    Update-McpConfigFile -FilePath $WindsurfPath -AgentName "Windsurf Global MCP"
}

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "   Installation Complete! Ready to use NexusPilot!     " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Restart your AI agent or reload window to activate the new tools.`n" -ForegroundColor Green
