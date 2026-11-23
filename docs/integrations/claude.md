# Claude Integration (Code CLI & Desktop)

**NexusPilot: Desktop** connects seamlessly to Anthropic's Claude Code CLI and Claude Desktop on Windows.

---

## 1. Claude Code CLI

Add the server to your global Claude CLI config (`~/.claude.json`) or project `.mcp.json`:

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

Or add via the CLI:
```bash
claude mcp add nexus-pilot python "F:/Personal/ComputerUse/nexus-pilot/server/pilot_server.py"
```

---

## 2. Claude Desktop App

Open your Claude Desktop configuration file at `%APPDATA%\Claude\claude_desktop_config.json`:

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

Restart Claude Desktop. The hammer icon will display the **NexusPilot: Desktop** tools.
