# Project NexusPilot

<p align="center">
  <img src="assets/brand_logo.jpg" width="460" alt="NexusPilot Logo" />
</p>

**NexusPilot** is an open-source, modular **Desktop Human-Grade Automation Suite** delivered as a cross-compatible **Model Context Protocol (MCP) Server** and an **Antigravity Plugin + Skill**.

It provides AI agents with human-like vision, mouse control, keyboard input, and native Windows accessibility perception, enabling autonomous operation of native desktop software.

```mermaid
flowchart TD
    subgraph AgentLayer["Agent Layer (MCP Clients)"]
        A1["Google Antigravity"]
        A2["Claude Code"]
        A3["Cursor / Windsurf"]
    end

    subgraph PluginLayer["NexusPilot Plugin & Skill Layer"]
        B1["SKILL.md (Observe-Plan-Act-Verify)"]
        B2["Safety Guardrails & Boundary Checks"]
    end

    subgraph MCPEngine["NexusPilot MCP Engine (Local Daemon)"]
        C1["Tool Dispatcher (JSON-RPC)"]
        C2["Perception Engine (MSS / DWM Cropping)"]
        C3["Semantic Engine (Windows UI Automation COM)"]
        C4["Actuation Engine (Win32 SendInput / DPI V2)"]
        C5["Failsafe Guardian (Corner Slam / Boundary Lock)"]
    end

    subgraph WindowsOS["Host Operating System (Windows 10 / 11)"]
        D1["Display Surfaces & Window Handles (HWND)"]
        D2["Mouse & Keyboard Event Queue"]
        D3["UI Automation Core (UIAutomationCore.dll)"]
    end

    AgentLayer --> PluginLayer
    PluginLayer --> MCPEngine
    MCPEngine --> WindowsOS
```

---

## Key Highlights

- **Dual-Modal Perception**: Combines sub-30ms screen capture with the Windows UI Automation (UIA) accessibility tree for 100% coordinate precision.
- **DPI-Aware Win32 Actuation**: Low-level `SendInput` mouse and keyboard control with Per-Monitor DPI v2 normalization.
- **Hardware Corner Failsafe**: Slamming the physical mouse cursor to `(0, 0)` immediately halts all automation.
- **Cross-Agent Compatible**: Works out-of-the-box with Google Antigravity, Claude Code, Claude Desktop, Cursor, and Windsurf via standard MCP.
