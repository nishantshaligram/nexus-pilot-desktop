---
layout: home

hero:
  name: "NexusPilot"
  text: "Universal Desktop Computer-Use"
  tagline: "Empower AI agents with human-grade vision, mouse actuation, keyboard input, and Windows UI Automation."
  image:
    src: /assets/brand_logo.jpg
    alt: NexusPilot Logo
  actions:
    - theme: brand
      text: Get Started →
      link: /getting-started/quickstart
    - theme: alt
      text: View on GitHub
      link: https://github.com/nishantshaligram/NexusPilot

features:
  - icon: 🎯
    title: Dual-Modal Perception
    details: Combines sub-30ms hardware screen capture with Windows UI Automation (UIA) COM accessibility tree for 100% coordinate precision.
  - icon: ⚡
    title: Native Win32 SendInput
    details: Low-level actuation with Per-Monitor DPI Awareness v2 normalization eliminates multi-monitor coordinate drift.
  - icon: 🛡️
    title: Hardware Failsafes
    details: Corner slam emergency stop, application boundary isolation lock, and destructive keyword gates.
  - icon: 🔌
    title: Universal MCP Compatible
    details: Works out-of-the-box with Google Antigravity, Claude Code, Cursor, and Windsurf via standard MCP.
---

## Frequently Asked Questions

### What is NexusPilot?
NexusPilot is an open-source Desktop Computer-Use automation suite delivered as a Model Context Protocol (MCP) server and Google Antigravity plugin. It enables AI coding agents to control native Windows desktop applications using mouse actuation, keyboard typing, and accessibility perception.

### How does NexusPilot compare to Anthropic Computer Use?
Anthropic Computer Use runs inside isolated cloud Docker containers with pure vision models. NexusPilot runs **100% locally on your Windows developer workstation** and uses **Dual-Modal Perception**: it combines screen capture with the Windows UI Automation (UIA) accessibility tree to achieve 100% click precision without coordinate guessing.

### Which AI coding agents work with NexusPilot?
NexusPilot adheres to the open Model Context Protocol (MCP) standard and is verified to work out-of-the-box with **Google Antigravity**, **Claude Code CLI**, **Claude Desktop**, **Cursor IDE**, and **Windsurf**.

### How does NexusPilot prevent multi-monitor and DPI scaling errors?
NexusPilot implements **Per-Monitor DPI Awareness v2**. It normalizes coordinates across varying monitor resolutions and display scales (100%, 125%, 150%, 200%) directly into Win32 normalized absolute units ($0 \text{ to } 65535$).

### How does the emergency stop failsafe work?
If an automated agent ever exhibits unexpected behavior, slam the physical mouse cursor into the top-left corner `(0, 0)`. The hardware failsafe immediately pauses all synthetic input and aborts the task.
