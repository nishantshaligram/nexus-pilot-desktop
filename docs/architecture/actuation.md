# Intelligent Hybrid Actuation Engine & Kinematics

NexusPilot dispatches low-level mouse and keyboard events using an **Intelligent Hybrid Actuation Strategy**:
- **Background Applications**: Executes silently via Windows UI Automation (UIA) COM patterns (`IUIAutomationInvokePattern`, `IUIAutomationTogglePattern`, `IUIAutomationSelectionItemPattern`, `IUIAutomationValuePattern`) or Win32 window messages. It never steals window focus and never moves the physical cursor, leaving the human user free to continue working in other applications unhindered.
- **Focused Applications**: Glides the Visual Pilot Overlay HUD with smooth Bézier curves, morphs the cursor to a pointer hand over interactive controls, renders click ripples, and types text with human cadence and an animated I-beam cursor.
- **Custom Canvas Fallback**: When an application renders on a custom canvas (DirectX, Electron web canvas, Flutter, game engines) where background UIA patterns are unavailable, it gracefully falls back to bringing the window to focus, gliding the visual HUD, and actuating via native Win32 `SendInput`.

---

## 1. Per-Monitor DPI v2 Awareness

Multi-monitor setups with varying scale factors (e.g., 4K primary at 150% and 1080p secondary at 100%) often cause coordinate drift in automation tools.

NexusPilot explicitly registers **Per-Monitor DPI Awareness v2** via `SetProcessDpiAwareness(2)`:
- Maps virtual screen space across all connected displays (`SM_XVIRTUALSCREEN`, `SM_YVIRTUALSCREEN`, `SM_CXVIRTUALSCREEN`, `SM_CYVIRTUALSCREEN`).
- Normalizes pixel coordinates to Win32 absolute units ($0 \text{ to } 65535$) using `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK`.

---

## 2. Silent Background Invocation vs Foreground Visual HUD

```mermaid
flowchart TD
    Req["Actuation Request (click_element, mouse_click, send_keystrokes)"]
    CheckFocus{"Is Target App Focused?"}
    TryBG{"Supports UIA Background Pattern?"}
    BGInvoke["Silent Background Invocation\n(UIA Invoke/Value Pattern or Win32 Message)\n• Zero focus stealing\n• Physical cursor unmoved\n• User typing unhindered"]
    VisualAct["Visual HUD + SendInput Actuation\n• Visual cursor glide & pointer hand\n• Click ripple / I-beam text bubble\n• Win32 SendInput"]

    Req --> CheckFocus
    CheckFocus -->|Yes| VisualAct
    CheckFocus -->|No| TryBG
    TryBG -->|Yes| BGInvoke
    TryBG -->|No (Custom Canvas)| VisualAct
```

---

## 3. Human-Grade Mouse Kinematics & Visual Pilot HUD

- **Bézier Trajectories**: Eases mouse movements smoothly across intermediate waypoints to avoid triggering rapid-jitter UI glitches.
- **Transparent Click-Through Overlay**: Renders at 60 FPS using Win32 `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE` — never intercepts clicks intended for applications.
- **Zero Input Lock**: Windows `BlockInput` is never called, ensuring the user's physical mouse and keyboard remain 100% responsive.
- **Unicode Keystroke Typing**: Uses `KEYEVENTF_UNICODE` so international characters, emojis, and symbols type reliably regardless of the host keyboard layout.
