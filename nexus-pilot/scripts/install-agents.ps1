<#
.SYNOPSIS
    NexusPilot Universal Multi-Agent Installer
.DESCRIPTION
    Configures and installs NexusPilot for Antigravity, Claude (Code & Desktop),
    Cursor, Windsurf, and Codex with zero manual JSON editing.
.PARAMETER TargetAgent
    Target agent to install for: 'All', 'Antigravity', 'Claude', 'Cursor', 'Windsurf'. Defaults to 'All'.
#>

param(
    [ValidateSet("All", "Antigravity", "Claude", "Cursor", "Windsurf")]
    [string]$TargetAgent = "All"
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
if ($TargetAgent -eq "All" -or $TargetAgent -eq "Antigravity") {
    Write-Host "[1/4] Installing for Google Antigravity..." -ForegroundColor Cyan
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
if ($TargetAgent -eq "All" -or $TargetAgent -eq "Claude") {
    Write-Host "`n[2/4] Installing for Claude..." -ForegroundColor Cyan
    # A. Claude Code CLI (~/.claude.json)
    $ClaudeCodePath = "$HOME/.claude.json"
    Update-McpConfigFile -FilePath $ClaudeCodePath -AgentName "Claude Code CLI"

    # B. Claude Desktop App (%APPDATA%\Claude\claude_desktop_config.json)
    $ClaudeDesktopPath = "$env:APPDATA/Claude/claude_desktop_config.json"
    Update-McpConfigFile -FilePath $ClaudeDesktopPath -AgentName "Claude Desktop App"
}

# 3. Cursor IDE
if ($TargetAgent -eq "All" -or $TargetAgent -eq "Cursor") {
    Write-Host "`n[3/4] Installing for Cursor IDE..." -ForegroundColor Cyan
    $CursorMcpPath = "$HOME/.cursor/mcp.json"
    Update-McpConfigFile -FilePath $CursorMcpPath -AgentName "Cursor Global MCP"
}

# 4. Windsurf / Codex
if ($TargetAgent -eq "All" -or $TargetAgent -eq "Windsurf") {
    Write-Host "`n[4/4] Installing for Windsurf / Codeium..." -ForegroundColor Cyan
    $WindsurfPath = "$HOME/.codeium/windsurf/mcp_config.json"
    Update-McpConfigFile -FilePath $WindsurfPath -AgentName "Windsurf Global MCP"
}

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "   Installation Complete! Ready to use NexusPilot!     " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Restart your AI agent or reload window to activate the new tools.`n" -ForegroundColor Green
