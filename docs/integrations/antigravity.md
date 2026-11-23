# Google Antigravity Integration

**NexusPilot: Desktop** is bundled as an official Antigravity plugin and skill.

---

## Installation in Antigravity

Copy the `nexus-pilot` folder to your global Antigravity plugins directory:

```powershell
New-Item -ItemType Directory -Path "$HOME\.gemini\config\plugins" -Force
Copy-Item -Path "nexus-pilot\*" -Destination "$HOME\.gemini\config\plugins\nexus-pilot" -Recurse -Force
```

Antigravity automatically discovers:
1. **Plugin Manifest**: `plugin.json` (author, logo, starter prompts)
2. **MCP Server**: `mcp_config.json` running `server/pilot_server.py`
3. **Agent Skill**: `skills/desktop-human-pilot/SKILL.md`
4. **Safety Rules**: `rules/AGENTS.md` (active globally while the plugin is enabled)

---

## Managing the Plugin

You can toggle or inspect the plugin in the Antigravity UI:
- Open `customization://nexus-pilot` in the Customizations page.
- All 13 MCP tools (`capture_screen`, `click_element`, `mouse_click`, etc.) are available directly in your chat sessions.
