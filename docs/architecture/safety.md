# Safety Guardian & Human-in-the-Loop Safeguards

Autonomous desktop actuation requires strict safety guardrails to protect user privacy and prevent destructive mistakes.

---

## 1. Hardware Corner Failsafe

NexusPilot monitors physical mouse cursor coordinates prior to executing any synthetic actuation:

- **Trigger**: Slamming the physical mouse cursor into the top-left corner `(0, 0)` immediately halts all automation.
- **Enforcement**: Any in-flight or subsequent MCP tool call aborts with `safety_abort: true`.
- **Reset**: The failsafe remains locked until the user explicitly calls `reset_safety_failsafe` or approves resumption.

---

## 2. Application Boundary Isolation

To prevent an AI agent from accidentally clicking into personal messaging apps (Slack, WhatsApp, Discord) or browser password vaults:

- **Hard Boundary Lock**: `set_safety_boundary(enabled=True, hwnd=...)` locks clicks strictly within the target window's bounding rectangle `[left, top, right, bottom]`.
- Coordinates outside this rectangle raise a `SafetyViolationError` and are immediately blocked.

---

## 3. High-Risk Confirmation Gates

The Safety Guardian inspects typed text and clicked control labels against potentially irreversible keywords:

- `format`, `drop database`, `drop table`, `rm -rf`, `commit to production`, `push --force`, `delete from`, `kill -9`

If detected, the engine flags `high_risk_detected: true` and requests explicit Human-in-the-Loop (HITL) confirmation before proceeding.
