# NexusPilot Desktop Safety Guardrails

These rules govern the autonomous execution of desktop actions to ensure user safety and prevent unauthorized or destructive operations.

## Rule 1: Application Boundary Isolation
- Agents MUST only interact with applications explicitly mentioned in or relevant to the user's task.
- NEVER click outside the authorized application window into:
  - Personal messaging apps (Slack, WhatsApp, Discord, Teams).
  - Web browser personal tabs or password managers.
  - Windows notification center or system tray icons.
- When working on a single application, activate `set_safety_boundary(enabled=True, hwnd=...)` to enforce hard operating bounds.

## Rule 2: Hardware Corner Failsafe Respect
- If `safety_abort: true` is returned by any tool, the physical mouse was slammed to `(0, 0)` or the user triggered an emergency stop.
- Immediately halt all further automated actions and return control to the user.
- Do NOT automatically call `reset_safety_failsafe()` without explicit user consent.

## Rule 3: Destructive Action Confirmation Gates
- The following actions require explicit user confirmation before execution:
  - Closing an application with unsaved changes.
  - Formatting drives, deleting partitions, or dropping database tables.
  - Deleting files permanently (bypassing Recycle Bin).
  - Submitting payments, orders, or license agreements.
  - Force-pushing to shared Git branches or deploying to production.

## Rule 4: Credential & PII Protection
- Never type passwords or API tokens into unverified windows.
- Always verify the active window title and process name via `get_active_window()` before injecting sensitive input.
