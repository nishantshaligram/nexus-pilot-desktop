# Win32 Actuation Engine & Kinematics

NexusPilot dispatches low-level mouse and keyboard events directly into the Windows OS event queue using native Win32 `SendInput`.

---

## 1. Per-Monitor DPI v2 Awareness

Multi-monitor setups with varying scale factors (e.g., 4K primary at 150% and 1080p secondary at 100%) often cause coordinate drift in automation tools.

NexusPilot explicitly registers **Per-Monitor DPI Awareness v2** via `SetProcessDpiAwareness(2)`:
- Maps virtual screen space across all connected displays (`SM_XVIRTUALSCREEN`, `SM_YVIRTUALSCREEN`, `SM_CXVIRTUALSCREEN`, `SM_CYVIRTUALSCREEN`).
- Normalizes pixel coordinates to Win32 absolute units ($0 \text{ to } 65535$) using `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.

---

## 2. Window Focus Stealing Prevention

Windows blocks background processes from rudely bringing windows to the foreground. NexusPilot implements the standard Win32 focus handshake:

1. Identifies the foreground thread via `GetWindowThreadProcessId(GetForegroundWindow())`.
2. Attaches thread input: `AttachThreadInput(foreThread, appThread, TRUE)`.
3. Calls `ShowWindow(targetHwnd, SW_RESTORE)` to un-minimize if needed.
4. Executes `SetForegroundWindow` and `BringWindowToTop`.
5. Detaches thread input cleanly.

---

## 3. Human-Grade Mouse Kinematics

- **Bézier Trajectories**: Eases mouse movements over 5-10 intermediate waypoints to avoid triggering rapid-jitter UI glitches.
- **Full Drag-and-Drop**: Emits synchronized `MOUSEEVENTF_LEFTDOWN`, intermediate drag motions, and `MOUSEEVENTF_LEFTUP`.
- **Unicode Keystroke Typing**: Uses `KEYEVENTF_UNICODE` so international characters, emojis, and symbols type reliably regardless of the host keyboard layout.
