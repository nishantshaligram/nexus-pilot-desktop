# Installation & Environment Setup

NexusPilot runs locally on Windows 10 and 11 workstations without requiring external cloud containers.

---

## 1. Prerequisites

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.10+ installed and on system `PATH`
- **Permissions**: Standard user permissions (Administrator rights optional, but recommended for testing with elevated developer tools)

---

## 2. Automated 1-Click Installation

Run the universal agent installer script:

```powershell
powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/install-agents.ps1
```

Or double-click `nexus-pilot/install-agents.bat` in Windows Explorer.

The installer will:
1. Detect your local Python binary.
2. Install dependencies from `nexus-pilot/requirements.txt`.
3. Configure MCP settings for Antigravity, Claude Code, Claude Desktop, Cursor, and Windsurf.

---

## 3. Manual Installation via Pip

```bash
git clone https://github.com/nishantshaligram/NexusPilot.git
cd NexusPilot
pip install --user -r nexus-pilot/requirements.txt
```

---

## 4. Run Environment Diagnostic

Verify your display setup, DPI scale, and COM accessibility core:

```powershell
powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/verify-environment.ps1
```
