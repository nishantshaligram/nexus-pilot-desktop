# NexusPilot Desktop Safety Guardrails

These rules govern the autonomous execution of desktop actions to ensure user safety, system integrity, and seamless human-agent coexistence.

## Rule 1: Application Boundary Isolation
- Agents MUST only interact with applications explicitly mentioned in or relevant to the user's task.
- NEVER click outside the authorized application window into:
  - Personal messaging apps (Slack, WhatsApp, Discord, Teams).
  - Web browser personal tabs or password managers.
  - Windows notification center or system tray icons.
- When working on a single application, activate `set_safety_boundary(enabled=True, hwnd=...)` or `set_safety_boundary(enabled=True, window_title="...")` to enforce hard operating bounds. Any click outside will be rejected with `SafetyViolationError`.

## Rule 2: Non-Intrusive Hybrid Actuation Strategy
- **Background Applications**: When target software is in the background (not focused), use background invocation (`IUIAutomationInvokePattern`, `IUIAutomationTogglePattern`, `IUIAutomationSelectionItemPattern`, or Win32 window messages). This executes clicks and input silently without stealing window focus and without moving the physical cursor. The human user can continue typing and moving their mouse unhindered in other applications.
- **Focused Applications**: When the target software is in the foreground, animate the Visual Pilot HUD: glide the cursor arrow smoothly, morph to a pointing hand over interactive elements, trigger visual click ripples, and display typing with an I-beam cursor and keystroke pills.
- **Custom Canvas Fallback**: When an application renders on a custom canvas (DirectX, Electron web canvas, Flutter, game viewport) that does not expose background UIA invocation patterns, gracefully fall back to foreground focus, visual cursor HUD gliding, and `SendInput`.
- **Zero Input Lock**: Windows `BlockInput` must NEVER be called. The human user's mouse and keyboard remain responsive at all times.

## Rule 3: Hardware Corner Failsafe Respect
- If `safety_abort: true` is returned by any tool, the physical mouse was slammed to `(0, 0)` or the user triggered an emergency stop.
- Immediately halt all further automated actions and return control to the user.
- Do NOT automatically call `reset_safety_failsafe()` without explicit user consent.

## Rule 4: Destructive Action Confirmation Gates
- The following actions require explicit user confirmation before execution:
  - Closing an application with unsaved changes.
  - Formatting drives, deleting partitions, or dropping database tables.
  - Deleting files permanently (bypassing Recycle Bin).
  - Submitting payments, orders, or license agreements.
  - Force-pushing to shared Git branches or deploying to production.

## Rule 5: Credential & PII Protection
- Never type passwords or API tokens into unverified windows.
- Always verify the active window title and process name via `get_active_window()` before injecting sensitive input.
