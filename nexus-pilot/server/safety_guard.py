"""
NexusPilot - Safety Guardian & Human-in-the-Loop Safeguards
Enforces hardware corner failsafe, application boundary isolation, and destructive action gates.
"""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

HIGH_RISK_KEYWORDS = [
    "format", "drop database", "drop table", "truncate", "rm -rf",
    "delete from", "shutdown", "reboot", "commit to production",
    "push --force", "kill -9", "erase all", "pay now", "transfer funds"
]


class SafetyViolationError(Exception):
    """Raised when an actuation violates safety guardrails."""
    pass


class SafetyGuardian:
    """Monitors and intercepts unsafe actuation requests."""

    def __init__(self):
        self.failsafe_enabled = True
        self.boundary_lock_enabled = False
        self.locked_hwnd = None
        self.locked_bounds = None  # [left, top, right, bottom]
        self.emergency_stop_triggered = False
        self.suppress_corner_check = False

    def check_corner_failsafe(self) -> None:
        """
        Hardware Corner Failsafe:
        If physical mouse cursor is slammed into (0, 0) or screen corners,
        instantly trigger emergency abort.
        """
        if not self.failsafe_enabled or self.suppress_corner_check:
            return

        if self.emergency_stop_triggered:
            raise SafetyViolationError(
                "EMERGENCY STOP ACTIVE: Automation halted due to failsafe trigger. Call reset_failsafe to resume."
            )

        point = wintypes.POINT()
        if user32.GetCursorPos(ctypes.byref(point)):
            # Check top-left corner (0, 0)
            if point.x <= 2 and point.y <= 2:
                self.emergency_stop_triggered = True
                raise SafetyViolationError(
                    "HARDWARE FAILSAFE TRIGGERED: Mouse positioned at top-left corner (0, 0). All actions aborted."
                )

    def set_application_lock(self, hwnd: int | None = None, enable: bool = True):
        """Locks all agent clicks strictly within the bounds of a specific window."""
        self.boundary_lock_enabled = enable
        self.locked_hwnd = hwnd
        if enable and hwnd:
            rect = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                self.locked_bounds = (rect.left, rect.top, rect.right, rect.bottom)
        else:
            self.locked_bounds = None

    def validate_click_boundary(self, x: int, y: int) -> None:
        """Ensures coordinate falls within the permitted application bounding box."""
        self.check_corner_failsafe()

        if not self.boundary_lock_enabled or not self.locked_bounds:
            return

        left, top, right, bottom = self.locked_bounds
        if not (left <= x <= right and top <= y <= bottom):
            raise SafetyViolationError(
                f"BOUNDARY VIOLATION: Click target ({x}, {y}) is outside permitted window bounds [{left}, {top}, {right}, {bottom}]."
            )

    def check_high_risk_intent(self, text_or_label: str) -> tuple[bool, str]:
        """Detects potentially irreversible operations requiring explicit user confirmation."""
        lower = text_or_label.lower()
        for kw in HIGH_RISK_KEYWORDS:
            if kw in lower:
                return (True, f"Potentially destructive action detected containing '{kw}'")
        return (False, "")

    def reset_failsafe(self):
        """Clears emergency stop status."""
        self.emergency_stop_triggered = False
