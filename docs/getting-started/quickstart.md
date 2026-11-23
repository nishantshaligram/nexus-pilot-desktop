# Quickstart Guide

Get your AI agent to pilot a native desktop application in under 2 minutes.

---

## 1. Verify Health from CLI

Before connecting your agent, test the MCP engine directly from PowerShell:

```powershell
python -c "
import sys; sys.path.insert(0, 'nexus-pilot/server')
from input_synthesizer import InputSynthesizer
from uia_bridge import UIABridge

synth = InputSynthesizer()
print('Active Window:', synth.get_active_window()['title'])

bridge = UIABridge()
tree = bridge.inspect_ui_tree(max_depth=2)
print(f'Detected {len(tree[\"elements\"])} interactive UI controls on screen!')
"
```

---

## 2. Example Agent Prompts

Once **NexusPilot: Desktop** is enabled in your agent (Antigravity, Claude, or Cursor), try these real-world instructions:

### A. Windows Calculator Automation
> *"Open Windows Calculator, click 7, click multiply, click 8, click equals, and verify the displayed result."*

### B. Notepad Note Creation
> *"Open Notepad, type 'Hello from NexusPilot: Desktop', and save the file to my Desktop as test.txt."*

### C. Developer Thick Client Navigation
> *"Bring DBeaver to the front, click Test Connection, and tell me if the database ping succeeded."*

---

## 3. The Emergency Stop

If an agent ever makes an unintended action:
- **Slam your physical mouse into the top-left corner `(0, 0)`.**
- **NexusPilot: Desktop** will immediately trigger the hardware failsafe, halt input, and notify the agent to abort.
