# Cursor & Windsurf Integration

Configure **NexusPilot: Desktop** inside Cursor or Windsurf IDE.

---

## 1. Cursor IDE

1. Open **Cursor Settings** (`Ctrl + ,`).
2. Navigate to **Features** $\rightarrow$ **MCP Servers**.
3. Click **Add New MCP Server**:
   - **Name**: `nexus-pilot`
   - **Type**: `command`
   - **Command**: `python F:/Personal/ComputerUse/nexus-pilot/server/pilot_server.py`

Or add directly to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "nexus-pilot": {
      "command": "python",
      "args": ["F:/Personal/ComputerUse/nexus-pilot/server/pilot_server.py"]
    }
  }
}
```

---

## 2. Windsurf (Codeium)

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "nexus-pilot": {
      "command": "python",
      "args": ["F:/Personal/ComputerUse/nexus-pilot/server/pilot_server.py"]
    }
  }
}
```
Reload the IDE window to activate the tools.
