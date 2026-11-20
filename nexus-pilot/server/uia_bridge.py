"""
NexusPilot - Windows UI Automation (UIA) Semantic Bridge
Queries native controls, interactive elements, exact bounding boxes, and executes background invocation.
Includes Win32 EnumChildWindows and window message fallbacks.
"""

import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# UIA Constants
UIA_InvokePatternId = 10000
UIA_SelectionItemPatternId = 10010
UIA_ValuePatternId = 10002
UIA_TogglePatternId = 10015

# Win32 Messages
WM_SETTEXT = 0x000C
BM_CLICK = 0x00F5
WM_COMMAND = 0x0111
WM_CHAR = 0x0102

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
    """Provides semantic accessibility tree inspection and background invocation on Windows."""

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

    def find_window_hwnd(self, keyword: str) -> tuple[int, str] | None:
        """Finds window handle and full title by partial keyword match."""
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
            win_match = self.find_window_hwnd(window_title)
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
            native_hwnd = node.CurrentNativeWindowHandle or 0

            rect = node.CurrentBoundingRectangle
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
                    "hwnd": native_hwnd,
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
                            "hwnd": hwnd,
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

    def _find_uia_element_node(self, root_elem, query_lower: str, walker, depth: int = 0, max_depth: int = 4):
        """Recursively traverses UIA tree returning the raw COM IUIAutomationElement node."""
        if depth > max_depth or not root_elem:
            return None

        try:
            name = (root_elem.CurrentName or "").lower()
            auto_id = (root_elem.CurrentAutomationId or "").lower()
            if query_lower in name or query_lower == auto_id:
                return root_elem

            child = walker.GetFirstChildElement(root_elem)
            while child:
                match = self._find_uia_element_node(child, query_lower, walker, depth + 1, max_depth)
                if match:
                    return match
                child = walker.GetNextSiblingElement(child)
        except Exception:
            pass
        return None

    def invoke_element_background(
        self,
        query: str,
        window_title: str | None = None
    ) -> tuple[bool, str, dict | None]:
        """
        Attempts to click/invoke a UI element silently in the background without stealing window focus
        or moving the physical cursor.
        Returns: (success: bool, description: str, element_info: dict | None)
        """
        target_hwnd = None
        matched_title = ""
        if window_title:
            win_match = self.find_window_hwnd(window_title)
            if win_match:
                target_hwnd, matched_title = win_match
        else:
            target_hwnd = user32.GetForegroundWindow()

        elem_info = self.find_element(query, window_title=window_title)
        query_lower = query.lower().strip()

        # 1. Try UIA COM Pattern Invocation
        if self._uia and target_hwnd:
            try:
                from comtypes.gen import UIAutomationClient
                root_elem = self._uia.ElementFromHandle(target_hwnd)
                if root_elem:
                    walker = self._uia.ControlViewWalker
                    node = self._find_uia_element_node(root_elem, query_lower, walker)
                    if node:
                        # Try InvokePattern
                        try:
                            inv = node.GetCurrentPatternAs(
                                UIA_InvokePatternId,
                                UIAutomationClient.IUIAutomationInvokePattern._iid_
                            )
                            if inv:
                                inv.Invoke()
                                return (True, "Invoked via UIA InvokePattern in background without stealing focus.", elem_info)
                        except Exception:
                            pass

                        # Try TogglePattern (checkboxes / toggles)
                        try:
                            tog = node.GetCurrentPatternAs(
                                UIA_TogglePatternId,
                                UIAutomationClient.IUIAutomationTogglePattern._iid_
                            )
                            if tog:
                                tog.Toggle()
                                return (True, "Toggled via UIA TogglePattern in background.", elem_info)
                        except Exception:
                            pass

                        # Try SelectionItemPattern (tabs / radio buttons / list items)
                        try:
                            sel = node.GetCurrentPatternAs(
                                UIA_SelectionItemPatternId,
                                UIAutomationClient.IUIAutomationSelectionItemPattern._iid_
                            )
                            if sel:
                                sel.Select()
                                return (True, "Selected via UIA SelectionItemPattern in background.", elem_info)
                        except Exception:
                            pass
            except Exception:
                pass

        # 2. Try Win32 Message (BM_CLICK) if element has native HWND
        if elem_info and elem_info.get("hwnd", 0) > 0:
            ctrl_hwnd = elem_info["hwnd"]
            user32.SendMessageW(ctrl_hwnd, BM_CLICK, 0, 0)
            return (True, f"Triggered via Win32 BM_CLICK on control HWND {ctrl_hwnd} in background.", elem_info)

        # 3. Canvas fallback: background invocation not supported
        return (
            False,
            "Target control is on a custom canvas or does not support background UIA invocation patterns.",
            elem_info
        )

    def set_element_value_background(
        self,
        query: str,
        text: str,
        window_title: str | None = None
    ) -> tuple[bool, str]:
        """
        Attempts to write text into an input field in the background without stealing focus.
        Returns: (success: bool, description: str)
        """
        target_hwnd = None
        if window_title:
            win_match = self.find_window_hwnd(window_title)
            if win_match:
                target_hwnd = win_match[0]
        else:
            target_hwnd = user32.GetForegroundWindow()

        elem_info = self.find_element(query, window_title=window_title)
        query_lower = query.lower().strip()

        # 1. Try UIA ValuePattern
        if self._uia and target_hwnd:
            try:
                from comtypes.gen import UIAutomationClient
                root_elem = self._uia.ElementFromHandle(target_hwnd)
                if root_elem:
                    walker = self._uia.ControlViewWalker
                    node = self._find_uia_element_node(root_elem, query_lower, walker)
                    if node:
                        try:
                            val = node.GetCurrentPatternAs(
                                UIA_ValuePatternId,
                                UIAutomationClient.IUIAutomationValuePattern._iid_
                            )
                            if val:
                                val.SetValue(text)
                                return (True, f"Value set to '{text}' via UIA ValuePattern in background.")
                        except Exception:
                            pass
            except Exception:
                pass

        # 2. Try Win32 WM_SETTEXT
        if elem_info and elem_info.get("hwnd", 0) > 0:
            ctrl_hwnd = elem_info["hwnd"]
            user32.SendMessageW(ctrl_hwnd, WM_SETTEXT, 0, text)
            return (True, f"Text set via Win32 WM_SETTEXT on control HWND {ctrl_hwnd}.")

        return (
            False,
            "Target control does not support background UIA ValuePattern or Win32 text setting (custom canvas)."
        )

    def invoke_at_point_background(self, x: int, y: int) -> tuple[bool, str]:
        """Attempts to invoke an element at specific coordinates in the background."""
        if not self._uia:
            return (False, "UI Automation COM not available.")
        try:
            from comtypes.gen import UIAutomationClient
            pt = wintypes.POINT(x, y)
            elem = self._uia.ElementFromPoint(pt)
            if elem:
                name = elem.CurrentName or "element"
                try:
                    inv = elem.GetCurrentPatternAs(
                        UIA_InvokePatternId,
                        UIAutomationClient.IUIAutomationInvokePattern._iid_
                    )
                    if inv:
                        inv.Invoke()
                        return (True, f"Invoked '{name}' via UIA InvokePattern in background.")
                except Exception:
                    pass
                try:
                    tog = elem.GetCurrentPatternAs(
                        UIA_TogglePatternId,
                        UIAutomationClient.IUIAutomationTogglePattern._iid_
                    )
                    if tog:
                        tog.Toggle()
                        return (True, f"Toggled '{name}' via UIA TogglePattern in background.")
                except Exception:
                    pass
                try:
                    sel = elem.GetCurrentPatternAs(
                        UIA_SelectionItemPatternId,
                        UIAutomationClient.IUIAutomationSelectionItemPattern._iid_
                    )
                    if sel:
                        sel.Select()
                        return (True, f"Selected '{name}' via UIA SelectionItemPattern in background.")
                except Exception:
                    pass
        except Exception:
            pass
        return (False, "Element at coordinates does not support background invocation (custom canvas).")
