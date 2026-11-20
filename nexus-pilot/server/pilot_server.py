"""
NexusPilot - Model Context Protocol (MCP) Server
Exposes desktop perception, semantic accessibility inspection, and Win32 actuation tools.
Implements intelligent hybrid actuation:
- Focused application: visual pilot cursor HUD glide, pointer hand, click ripple, visible human-cadence typing.
- Unfocused application: background UIA/Win32 invocation without stealing window focus or moving physical cursor.
- Custom canvas fallback: gracefully falls back to visual HUD and SendInput when controls don't support UIA patterns.
- Application Boundary Guard: strictly prohibits clicking outside designated application bounds.
"""

import sys
import os
import ctypes
from ctypes import wintypes

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

user32 = ctypes.windll.user32

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
    Clicks a UI element using an intelligent hybrid actuation strategy:
    1. If target application is in background (not focused): executes silently via UIA Invoke/Toggle/Select patterns
       or Win32 messages without stealing focus or moving the physical cursor.
    2. If background invocation fails (custom canvas) or application is already focused: focuses window,
       glides visual cursor HUD smoothly, displays ripple animation, and actuates with SendInput.
    Strictly enforces application boundary guard when set_safety_boundary is active.
    """
    try:
        guardian.check_corner_failsafe()

        # Check high-risk destructive action
        is_high_risk, risk_msg = guardian.check_high_risk_intent(query)
        if is_high_risk:
            return {"success": False, "high_risk_detected": True, "warning": risk_msg}

        target_hwnd = None
        target_title = window_title or ""
        if window_title:
            win_match = uia_bridge.find_window_hwnd(window_title)
            if win_match:
                target_hwnd, target_title = win_match

        # Boundary guard verification
        if guardian.boundary_lock_enabled:
            guardian.validate_window_target(target_hwnd, target_title)

        fore_hwnd = user32.GetForegroundWindow()
        is_focused = bool(target_hwnd and fore_hwnd == target_hwnd)

        # 1. Background Invocation Path (if target app is not in focus)
        if not is_focused:
            success, msg, elem_info = uia_bridge.invoke_element_background(query, window_title=window_title)
            if success:
                return {
                    "success": True,
                    "mode": "background_invocation",
                    "target_window": target_title or "Background Window",
                    "clicked_element": (elem_info["name"] if elem_info else query),
                    "details": msg,
                    "focus_stolen": False,
                    "mouse_moved": False
                }
            # Custom canvas fallback: background pattern not supported

        # 2. Foreground Visual Execution Path (Focused or Custom Canvas Fallback)
        if window_title and not is_focused:
            synthesizer.focus_window(window_title)

        elem = uia_bridge.find_element(query, window_title=window_title)
        if not elem:
            return {"success": False, "error": f"Element '{query}' could not be located in UI tree."}

        center_x, center_y = elem["center"]
        guardian.validate_click_boundary(center_x, center_y)

        if synthesizer.hud:
            synthesizer.hud.notify_lock_element(elem["rect"], elem["name"] or query)

        synthesizer.click(center_x, center_y, button=button, clicks=clicks)
        return {
            "success": True,
            "mode": "foreground_visual",
            "fallback_from_canvas": (not is_focused),
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
    Clicks at the specified screen coordinates using intelligent hybrid actuation:
    1. Validates strict application boundary guard.
    2. If target window under coordinate is in background, attempts silent UIA background invocation.
    3. If background invocation is not supported (custom canvas) or window is focused,
       glides visual cursor HUD, displays click ripple, and actuates via SendInput.
    """
    try:
        guardian.validate_click_boundary(x, y)

        pt = wintypes.POINT(x, y)
        wnd_at_pt = user32.WindowFromPoint(pt)
        top_wnd = user32.GetAncestor(wnd_at_pt, 2) or wnd_at_pt  # GA_ROOT
        fore_hwnd = user32.GetForegroundWindow()

        # If targeting a background window, try background invocation at point
        if top_wnd and top_wnd != fore_hwnd:
            guardian.validate_window_target(top_wnd)
            bg_success, bg_msg = uia_bridge.invoke_at_point_background(x, y)
            if bg_success:
                return {
                    "success": True,
                    "mode": "background_invocation",
                    "coordinates": [x, y],
                    "details": bg_msg,
                    "focus_stolen": False,
                    "mouse_moved": False
                }

        synthesizer.click(x, y, button=button, clicks=clicks)
        return {
            "success": True,
            "mode": "foreground_visual",
            "cursor_position": [x, y]
        }
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
    Validates safety boundaries before actuation.
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
    window_title: str | None = None,
    target_element: str | None = None,
    delay_ms: int = 10
) -> dict:
    """
    Sends keyboard input using hybrid actuation:
    1. If application is in background and target_element is specified, sets text silently via UIA ValuePattern
       without stealing focus or interrupting user typing.
    2. If application is focused or control is a custom canvas, animates visual I-beam HUD and keystroke
       floating pill, typing text with human cadence or executing key chord shortcuts.
    """
    try:
        guardian.check_corner_failsafe()

        if text:
            is_risk, msg = guardian.check_high_risk_intent(text)
            if is_risk:
                return {"success": False, "high_risk_detected": True, "warning": msg}

        target_hwnd = None
        target_title = window_title or ""
        if window_title:
            win_match = uia_bridge.find_window_hwnd(window_title)
            if win_match:
                target_hwnd, target_title = win_match

        if guardian.boundary_lock_enabled:
            guardian.validate_window_target(target_hwnd, target_title)

        fore_hwnd = user32.GetForegroundWindow()
        is_focused = bool(target_hwnd and fore_hwnd == target_hwnd)

        # Background text entry path
        if not is_focused and target_element and text and not keys:
            success, msg = uia_bridge.set_element_value_background(
                target_element, text, window_title=window_title
            )
            if success:
                return {
                    "success": True,
                    "mode": "background_invocation",
                    "text": text,
                    "details": msg,
                    "focus_stolen": False
                }
            # Custom canvas fallback: needs focus

        if window_title and not is_focused:
            synthesizer.focus_window(window_title)

        if text:
            synthesizer.type_text(text, delay_ms=delay_ms)

        if keys:
            synthesizer.send_hotkey(keys)

        return {"success": True, "mode": "foreground_visual"}
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
def set_safety_boundary(
    enabled: bool = True,
    hwnd: int | None = None,
    window_title: str | None = None
) -> dict:
    """
    Locks actuation strictly within target application window.
    Prohibits clicking outside permitted window bounds and rejects actions targeting other applications.
    Accepts explicit HWND or window title search keyword.
    """
    if window_title and not hwnd:
        match = uia_bridge.find_window_hwnd(window_title)
        if match:
            hwnd = match[0]

    guardian.set_application_lock(hwnd=hwnd, enable=enabled)
    bounds = guardian.get_locked_bounds()
    return {
        "boundary_lock_enabled": enabled,
        "locked_hwnd": hwnd,
        "locked_bounds": bounds,
        "status": f"Application boundary lock {'ACTIVATED' if enabled else 'DEACTIVATED'} for HWND {hwnd} ({bounds})"
    }


@server.tool()
def reset_safety_failsafe() -> dict:
    """
    Resets emergency corner abort so automation can proceed.
    """
    guardian.reset_failsafe()
    return {"emergency_stop_triggered": False, "status": "Failsafe reset successfully."}


@server.tool()
def set_visual_hud(enabled: bool = True) -> dict:
    """
    Enables or disables the real-time visual pilot cursor overlay, click ripple animations, and keystroke HUD.
    """
    if synthesizer.hud:
        synthesizer.hud.enabled = enabled
        if enabled and not synthesizer.hud.is_running:
            synthesizer.hud.start()
        elif not enabled:
            synthesizer.hud.close()
    return {"visual_hud_enabled": enabled}


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
        "visual_hud_active": synthesizer.hud.is_running if synthesizer.hud else False,
        "safety_failsafe_active": guardian.emergency_stop_triggered,
        "boundary_lock_active": guardian.boundary_lock_enabled
    }


def main():
    """Runs the MCP server over stdio."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
