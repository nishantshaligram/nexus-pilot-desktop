# Safety Guardian & Application Boundary Isolation

Autonomous desktop actuation requires strict safety guardrails to protect user privacy, prevent unauthorized actions, and avoid disrupting human workflows.

---

## 1. Application Boundary Isolation & Dynamic Window Tracking

To prevent an AI agent from accidentally clicking into personal messaging apps (Slack, WhatsApp, Discord), email clients, or browser password managers:

- **Hard Boundary Lock**: `set_safety_boundary(enabled=True, hwnd=...)` or `set_safety_boundary(enabled=True, window_title="...")` locks all agent actions strictly within the target application window.
- **Dynamic Coordinate Tracking**: If the locked application window is moved or resized by the user, the Safety Guardian automatically refreshes the bounding box in real time via Win32 `GetWindowRect`.
- **Target Window Verification**: Any actuation attempting to interact with a window outside the locked application (or outside its authorized child dialogs) raises `SafetyViolationError` and is immediately blocked.

---

## 2. Hardware Corner Failsafe

**NexusPilot: Desktop** monitors physical mouse cursor coordinates prior to executing any synthetic actuation:

- **Trigger**: Slamming the physical mouse cursor into the top-left corner `(0, 0)` immediately halts all automation.
- **Enforcement**: Any in-flight or subsequent MCP tool call aborts with `safety_abort: true`.
- **Reset**: The failsafe remains locked until the user explicitly calls `reset_safety_failsafe` or approves resumption.

---

## 3. High-Risk Destructive Action Gates

The Safety Guardian inspects typed text and clicked control labels against potentially irreversible keywords:

- `format`, `drop database`, `drop table`, `truncate`, `rm -rf`, `commit to production`, `push --force`, `delete from`, `kill -9`, `pay now`

If detected, the engine flags `high_risk_detected: true` and requests explicit Human-in-the-Loop (HITL) confirmation before proceeding.

---

## 4. Unblocked User Experience

**NexusPilot: Desktop** is designed for seamless human-agent coexistence:
- `BlockInput` is never engaged.
- Background actions execute silently via Windows UI Automation COM patterns without stealing focus or moving the physical mouse.
- The human user can freely use their keyboard and mouse in parallel while **NexusPilot: Desktop** operates.
