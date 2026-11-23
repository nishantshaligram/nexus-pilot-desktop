# Installation & Environment Setup

NexusPilot runs locally on Windows 10 and 11 workstations without requiring external cloud containers.

---

## 1. Prerequisites

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.10+ installed and on system `PATH`
- **Permissions**: Standard user permissions (Administrator rights optional, but recommended for testing with elevated developer tools)

---

## 2. Automated 1-Click Installation

### A. Interactive Menu (Zero Flags)
When double-clicking `nexus-pilot/install-agents.bat` or running without arguments, an interactive menu allows you to choose your exact target environment:

```text
No target environment specified. Choose an option:
  [1] All (Antigravity, Claude, Cursor, Windsurf) [Default]
  [2] Google Antigravity Only
  [3] Claude Only (Desktop & Code CLI)
  [4] Cursor IDE Only
  [5] Windsurf Only
  [6] Antigravity + Claude Only
Enter choice [1-6] (Press Enter for 1):
```

### B. Command-Line Installation (With Flags)
For automated CI or scripted setups, pass the target agent directly:

```powershell
# Install for a specific agent
powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/install-agents.ps1 -TargetAgent Antigravity
powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/install-agents.ps1 -TargetAgent Claude
powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/install-agents.ps1 -TargetAgent Cursor
powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/install-agents.ps1 -TargetAgent Windsurf
```

Or using the npm CLI:
```bash
npx nexus-pilot-desktop install
npx nexus-pilot-desktop install --agent antigravity
npx nexus-pilot-desktop install --ide claude
```

---

## 3. Manual Installation via Pip

```bash
git clone https://github.com/nishantshaligram/nexus-pilot-desktop.git
cd nexus-pilot-desktop
pip install --user -r nexus-pilot/requirements.txt
```

---

## 4. Run Environment Diagnostic

Verify your display setup, DPI scale, and COM accessibility core:

```powershell
powershell -ExecutionPolicy Bypass -File nexus-pilot/scripts/verify-environment.ps1
```
