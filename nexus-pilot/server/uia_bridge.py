"""
NexusPilot - Windows UI Automation (UIA) Semantic Bridge
Queries native controls, interactive elements, and exact bounding boxes using COM IUIAutomation.
Includes Win32 EnumChildWindows fallback for maximum resilience.
"""

import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# Mapping UIA ControlType IDs to human-readable names
UIA_CONTROL_TYPES = {
    50000: "Button",
    50001: "Calendar",
    50002: "CheckBox",
    50003: "ComboBox",
    50004: "Edit",
    50005: "Hyperlink",
    50006: "Image",
    50007: "ListItem",
    50008: "List",
    50009: "Menu",
    50010: "MenuBar",
    50011: "MenuItem",
    50012: "ProgressBar",
    50013: "RadioButton",
    50014: "ScrollBar",
    50015: "Slider",
    50016: "Spinner",
    50017: "StatusBar",
    50018: "Tab",
    50019: "TabItem",
    50020: "Text",
    50021: "ToolBar",
    50022: "ToolTip",
    50023: "Tree",
    50024: "TreeItem",
    50025: "Custom",
    50026: "Group",
    50028: "ToolBar",
    50030: "Document",
    50032: "Pane",
    50033: "Window"
}

INTERACTIVE_TYPES = {
    "Button", "CheckBox", "ComboBox", "Edit", "Hyperlink",
    "ListItem", "MenuItem", "RadioButton", "TabItem", "TreeItem"
}


class UIABridge:
    """Provides semantic accessibility tree inspection on Windows."""

    def __init__(self):
        self._uia = None
        self._init_uia()

    def _init_uia(self):
        try:
            import comtypes.client
            from comtypes.gen import UIAutomationClient
            self._uia = comtypes.client.CreateObject(
                UIAutomationClient.CUIAutomation,
                interface=UIAutomationClient.IUIAutomation
            )
        except Exception:
            try:
                import comtypes.client
                comtypes.client.GetModule('UIAutomationCore.dll')
                from comtypes.gen import UIAutomationClient
                self._uia = comtypes.client.CreateObject(
                    UIAutomationClient.CUIAutomation,
                    interface=UIAutomationClient.IUIAutomation
                )
            except Exception:
                self._uia = None

    def _find_window_hwnd(self, keyword: str) -> tuple[int, str] | None:
        target_hwnd = None
        target_title = ""

        def enum_windows_callback(hwnd, extra):
            nonlocal target_hwnd, target_title
            if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if keyword.lower() in title.lower():
                        target_hwnd = hwnd
                        target_title = title
                        return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

        if target_hwnd:
            return (target_hwnd, target_title)
        return None

    def inspect_ui_tree(
        self,
        window_title: str | None = None,
        max_depth: int = 3,
        interactive_only: bool = True
    ) -> dict:
        """
        Inspects the UI Automation accessibility tree of the target window or desktop.
        Returns a structured list of UI elements with labels, types, and coordinates.
        """
        target_hwnd = None
        matched_title = ""

        if window_title:
            win_match = self._find_window_hwnd(window_title)
            if win_match:
                target_hwnd, matched_title = win_match
            else:
                return {"elements": [], "error": f"No active window found matching '{window_title}'"}
        else:
            target_hwnd = user32.GetForegroundWindow()

        elements = []

        # Attempt COM UIA traversal
        if self._uia and target_hwnd:
            try:
                from comtypes.gen import UIAutomationClient
                root_elem = self._uia.ElementFromHandle(target_hwnd)
                if root_elem:
                    walker = self._uia.ControlViewWalker
                    self._traverse_uia_node(root_elem, walker, 0, max_depth, interactive_only, elements)
            except Exception:
                pass

        # Fallback to Win32 standard enumeration if UIA yields few or no elements
        if len(elements) == 0 and target_hwnd:
            elements = self._win32_inspect_fallback(target_hwnd, interactive_only)

        return {
            "window_title": matched_title or "Active Window",
            "hwnd": target_hwnd,
            "total_elements": len(elements),
            "elements": elements
        }

    def _traverse_uia_node(self, node, walker, depth: int, max_depth: int, interactive_only: bool, results: list):
        if depth > max_depth or len(results) >= 150:
            return

        try:
            name = node.CurrentName or ""
            ctype_id = node.CurrentControlType
            ctype = UIA_CONTROL_TYPES.get(ctype_id, f"Type_{ctype_id}")
            auto_id = node.CurrentAutomationId or ""
            class_name = node.CurrentClassName or ""

            # Check bounding rectangle
            rect = node.CurrentBoundingRectangle
            # rect is a tagRECT (left, top, right, bottom)
            w = rect.right - rect.left
            h = rect.bottom - rect.top

            is_valid_size = w > 4 and h > 4
            is_candidate = (not interactive_only) or (ctype in INTERACTIVE_TYPES) or (name.strip() and ctype != "Pane")

            if is_valid_size and is_candidate and (name or auto_id):
                results.append({
                    "name": name.strip(),
                    "control_type": ctype,
                    "id": auto_id or f"{ctype}_{len(results)}",
                    "class_name": class_name,
                    "rect": [rect.left, rect.top, w, h],
                    "center": [rect.left + w // 2, rect.top + h // 2]
                })

            # Traverse child nodes
            child = walker.GetFirstChildElement(node)
            while child and len(results) < 150:
                self._traverse_uia_node(child, walker, depth + 1, max_depth, interactive_only, results)
                child = walker.GetNextSiblingElement(child)
        except Exception:
            pass

    def _win32_inspect_fallback(self, parent_hwnd: int, interactive_only: bool) -> list[dict]:
        """Fallback inspection using native Win32 EnumChildWindows."""
        results = []

        def enum_child_proc(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                text = buff.value.strip()

                cls_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buff, 256)
                cls_name = cls_buff.value

                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top

                if w > 4 and h > 4:
                    guessed_type = "Button" if "button" in cls_name.lower() else (
                        "Edit" if "edit" in cls_name.lower() else (
                            "ComboBox" if "combobox" in cls_name.lower() else "Control"
                        )
                    )
                    if not interactive_only or text:
                        results.append({
                            "name": text,
                            "control_type": guessed_type,
                            "id": f"win32_{hwnd}",
                            "class_name": cls_name,
                            "rect": [rect.left, rect.top, w, h],
                            "center": [rect.left + w // 2, rect.top + h // 2]
                        })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumChildWindows(parent_hwnd, WNDENUMPROC(enum_child_proc), 0)
        return results

    def find_element(self, query: str, window_title: str | None = None) -> dict | None:
        """Finds a specific control matching query text or ID within target window."""
        tree = self.inspect_ui_tree(window_title=window_title, max_depth=4, interactive_only=False)
        query_lower = query.lower().strip()

        for el in tree.get("elements", []):
            if query_lower in el.get("name", "").lower() or query_lower == el.get("id", "").lower():
                return el

        return None
