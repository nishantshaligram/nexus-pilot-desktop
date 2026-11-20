"""
NexusPilot - Model Context Protocol (MCP) Server
Exposes desktop perception, semantic accessibility inspection, and Win32 actuation tools.
"""

import sys
import os

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from input_synthesizer import InputSynthesizer
from screen_capture import ScreenCaptureEngine
from uia_bridge import UIABridge
from safety_guard import SafetyGuardian, SafetyViolationError

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError:
        raise RuntimeError("mcp Python SDK is required. Run 'pip install mcp'")

# Instantiate core engines
synthesizer = InputSynthesizer()
capture_engine = ScreenCaptureEngine()
uia_bridge = UIABridge()
guardian = SafetyGuardian()

server = MCPServer("nexus-pilot")


@server.tool()
def capture_screen(
    monitor_index: int = 0,
    window_title: str | None = None,
    crop_rect: list[int] | None = None,
    max_dimension: int = 1920
) -> dict:
    """
    Captures a high-resolution screenshot of the desktop or a specific application window.
    Returns base64 PNG data, dimensions, and DPI scale factor.
    """
    try:
        guardian.check_corner_failsafe()
        return capture_engine.capture(
            monitor_index=monitor_index,
            window_title=window_title,
            crop_rect=crop_rect,
            max_dimension=max_dimension
        )
    except SafetyViolationError as se:
        return {"error": str(se), "safety_abort": True}
    except Exception as e:
        return {"error": f"Capture failed: {str(e)}"}


@server.tool()
def inspect_ui_tree(
    window_title: str | None = None,
    max_depth: int = 3,
    interactive_only: bool = True
) -> dict:
    """
    Queries the Windows UI Automation (UIA) accessibility tree for the target application.
    Returns interactive controls (Buttons, Text boxes, Menus) with exact bounding boxes and center coordinates.
    """
    try:
        return uia_bridge.inspect_ui_tree(
            window_title=window_title,
            max_depth=max_depth,
            interactive_only=interactive_only
        )
    except Exception as e:
        return {"elements": [], "error": f"UI inspection failed: {str(e)}"}


@server.tool()
def find_element(query: str, window_title: str | None = None) -> dict:
    """
    Searches for a specific UI control by label, name, or automation ID.
    Returns the control's exact coordinates for zero-guess clicking.
    """
    try:
        match = uia_bridge.find_element(query, window_title=window_title)
        if match:
            return {"found": True, "element": match}
        return {"found": False, "message": f"Element matching '{query}' not found."}
    except Exception as e:
        return {"found": False, "error": str(e)}


@server.tool()
def click_element(
    query: str,
    window_title: str | None = None,
    button: str = "left",
    clicks: int = 1
) -> dict:
    """
    Deterministically clicks a UI element by semantic name or ID.
    Combines UIA coordinate lookup with automatic window focus and click actuation.
    """
    try:
        guardian.check_corner_failsafe()

        # Check high-risk destructive action
        is_high_risk, risk_msg = guardian.check_high_risk_intent(query)
        if is_high_risk:
            return {"success": False, "high_risk_detected": True, "warning": risk_msg}

        if window_title:
            synthesizer.focus_window(window_title)

        elem = uia_bridge.find_element(query, window_title=window_title)
        if not elem:
            return {"success": False, "error": f"Element '{query}' could not be located in UI tree."}

        center_x, center_y = elem["center"]
        guardian.validate_click_boundary(center_x, center_y)

        synthesizer.click(center_x, center_y, button=button, clicks=clicks)
        return {
            "success": True,
            "clicked_element": elem["name"] or elem["id"],
            "coordinates": [center_x, center_y]
        }
    except SafetyViolationError as se:
        return {"success": False, "error": str(se), "safety_abort": True}
    except Exception as e:
        return {"success": False, "error": f"Failed to click element: {str(e)}"}


@server.tool()
def mouse_click(
    x: int,
    y: int,
    button: str = "left",
    clicks: int = 1
) -> dict:
    """
    Clicks at the specified screen coordinates using native Win32 SendInput.
    Validates safety boundaries and failsafe triggers before execution.
    """
    try:
        guardian.validate_click_boundary(x, y)
        synthesizer.click(x, y, button=button, clicks=clicks)
        return {"success": True, "cursor_position": [x, y]}
    except SafetyViolationError as se:
        return {"success": False, "error": str(se), "safety_abort": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.tool()
def mouse_drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    speed_ms: int = 300
) -> dict:
    """
    Performs a drag-and-drop gesture from start to end coordinates.
    """
    try:
        guardian.validate_click_boundary(start_x, start_y)
        guardian.validate_click_boundary(end_x, end_y)
        synthesizer.drag_and_drop(start_x, start_y, end_x, end_y, speed_ms=speed_ms)
        return {"success": True, "dragged_from": [start_x, start_y], "to": [end_x, end_y]}
    except SafetyViolationError as se:
        return {"success": False, "error": str(se), "safety_abort": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.tool()
def mouse_scroll(
    direction: str = "down",
    amount: int = 120,
    x: int | None = None,
    y: int | None = None
) -> dict:
    """
    Simulates mouse wheel scrolling in specified direction ('up' or 'down').
    """
    try:
        if x is not None and y is not None:
            guardian.validate_click_boundary(x, y)
        synthesizer.scroll(direction=direction, amount=amount, x=x, y=y)
        return {"success": True, "scrolled": direction, "amount": amount}
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.tool()
def send_keystrokes(
    text: str | None = None,
    keys: list[str] | None = None,
    delay_ms: int = 10
) -> dict:
    """
    Sends keyboard input. Can type text strings or execute modifier shortcut chords (e.g. ['ctrl', 'shift', 'p']).
    """
    try:
        guardian.check_corner_failsafe()

        if text:
            is_risk, msg = guardian.check_high_risk_intent(text)
            if is_risk:
                return {"success": False, "high_risk_detected": True, "warning": msg}
            synthesizer.type_text(text, delay_ms=delay_ms)

        if keys:
            synthesizer.send_hotkey(keys)

        return {"success": True}
    except SafetyViolationError as se:
        return {"success": False, "error": str(se), "safety_abort": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.tool()
def focus_window(title_keyword: str) -> dict:
    """
    Brings target application window to foreground with Win32 focus handshake.
    """
    try:
        return synthesizer.focus_window(title_keyword)
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.tool()
def get_active_window() -> dict:
    """
    Returns information about currently focused window (title, HWND, process name, bounds, DPI scale).
    """
    try:
        return synthesizer.get_active_window()
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.tool()
def set_safety_boundary(enabled: bool = True, hwnd: int | None = None) -> dict:
    """
    Locks actuation strictly within target window bounding box.
    """
    guardian.set_application_lock(hwnd=hwnd, enable=enabled)
    return {
        "boundary_lock_enabled": enabled,
        "locked_hwnd": hwnd,
        "locked_bounds": guardian.locked_bounds
    }


@server.tool()
def reset_safety_failsafe() -> dict:
    """
    Resets emergency corner abort so automation can proceed.
    """
    guardian.reset_failsafe()
    return {"emergency_stop_triggered": False, "status": "Failsafe reset successfully."}


@server.tool()
def check_health() -> dict:
    """
    Verifies perception, COM UIA availability, screen metrics, and safety guardian status.
    """
    cursor_x, cursor_y = synthesizer.get_cursor_position()
    active_win = synthesizer.get_active_window()
    return {
        "status": "online",
        "cursor_position": [cursor_x, cursor_y],
        "active_window": active_win.get("title", "None"),
        "active_process": active_win.get("process_name", "None"),
        "virtual_screen": [synthesizer.virt_w, synthesizer.virt_h],
        "uia_com_available": uia_bridge._uia is not None,
        "safety_failsafe_active": guardian.emergency_stop_triggered,
        "boundary_lock_active": guardian.boundary_lock_enabled
    }


def main():
    """Runs the MCP server over stdio."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
