"""
NexusPilot - Win32 Input Synthesizer & Window Management
High-precision, DPI-aware mouse and keyboard actuation using native Win32 SendInput.
"""

import ctypes
from ctypes import wintypes
import time
import math
import psutil

# Enable Per-Monitor DPI Awareness v2
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_ABSOLUTE = 0x8000

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# Virtual key mappings
VK_MAPPINGS = {
    'ctrl': 0x11, 'control': 0x11, 'lctrl': 0xA2, 'rctrl': 0xA3,
    'alt': 0x12, 'lalt': 0xA4, 'ralt': 0xA5,
    'shift': 0x10, 'lshift': 0xA0, 'rshift': 0xA1,
    'win': 0x5B, 'windows': 0x5B, 'cmd': 0x5B,
    'enter': 0x0D, 'return': 0x0D,
    'esc': 0x1B, 'escape': 0x1B,
    'backspace': 0x08, 'tab': 0x09,
    'space': 0x20, 'delete': 0x2E, 'del': 0x2E,
    'insert': 0x2D, 'home': 0x24, 'end': 0x23,
    'pageup': 0x21, 'pagedown': 0x22,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B
}


# Ctypes struct definitions for SendInput
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUTunion)
    ]


class InputSynthesizer:
    """Provides human-grade mouse and keyboard actuation for Windows with Visual Pilot HUD."""

    def __init__(self, enable_hud: bool = True):
        self._refresh_screen_metrics()
        self.hud = None
        try:
            from overlay_hud import VisualOverlayHUD
            self.hud = VisualOverlayHUD(enabled=enable_hud)
        except Exception:
            pass

    def _refresh_screen_metrics(self):
        self.virt_x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        self.virt_y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        self.virt_w = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        self.virt_h = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        if self.virt_w == 0:
            self.virt_w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        if self.virt_h == 0:
            self.virt_h = user32.GetSystemMetrics(1)  # SM_CYSCREEN

    def get_cursor_position(self) -> tuple[int, int]:
        """Returns the current mouse cursor (x, y) coordinates."""
        point = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)

    def _to_normalized_absolute(self, x: int, y: int) -> tuple[int, int]:
        """Converts screen coordinates to normalized absolute units (0-65535)."""
        self._refresh_screen_metrics()
        norm_x = int(((x - self.virt_x) * 65535) / self.virt_w)
        norm_y = int(((y - self.virt_y) * 65535) / self.virt_h)
        return (norm_x, norm_y)

    def _send_inputs(self, inputs: list[INPUT]) -> bool:
        """Sends an array of synthetic inputs to the Windows event queue."""
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        sent = user32.SendInput(n, arr, ctypes.sizeof(INPUT))
        return sent == n

    def move_to(self, x: int, y: int, smooth: bool = True, steps: int = 6, is_interactive: bool = False) -> bool:
        """Moves cursor to target coordinates, animating the visual HUD and moving physical cursor."""
        if self.hud:
            self.hud.notify_move(x, y, is_interactive=is_interactive)

        if not smooth or steps <= 1:
            norm_x, norm_y = self._to_normalized_absolute(x, y)
            inp = INPUT(type=INPUT_MOUSE)
            inp.u.mi = MOUSEINPUT(
                dx=norm_x,
                dy=norm_y,
                mouseData=0,
                dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
                time=0,
                dwExtraInfo=None
            )
            self._send_inputs([inp])
            user32.SetCursorPos(x, y)
            return True

        start_x, start_y = self.get_cursor_position()
        for i in range(1, steps + 1):
            t = i / steps
            ease_t = math.sin(t * math.pi / 2)
            cur_x = int(start_x + (x - start_x) * ease_t)
            cur_y = int(start_y + (y - start_y) * ease_t)
            norm_cx, norm_cy = self._to_normalized_absolute(cur_x, cur_y)
            inp = INPUT(type=INPUT_MOUSE)
            inp.u.mi = MOUSEINPUT(
                dx=norm_cx, dy=norm_cy, mouseData=0,
                dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
                time=0, dwExtraInfo=None
            )
            self._send_inputs([inp])
            user32.SetCursorPos(cur_x, cur_y)
            time.sleep(0.015)
        return True

    def click(self, x: int, y: int, button: str = 'left', clicks: int = 1) -> bool:
        """Moves cursor, morphs to pointer hand, shows click ripple animation, and executes clicks."""
        self.move_to(x, y, smooth=True, steps=4, is_interactive=True)
        time.sleep(0.03)

        if self.hud:
            self.hud.notify_click(x, y, button=button)
            time.sleep(0.04)  # Visual click anticipation

        down_flag = MOUSEEVENTF_LEFTDOWN
        up_flag = MOUSEEVENTF_LEFTUP
        button_lower = button.lower()
        if button_lower == 'right':
            down_flag = MOUSEEVENTF_RIGHTDOWN
            up_flag = MOUSEEVENTF_RIGHTUP
        elif button_lower == 'middle':
            down_flag = MOUSEEVENTF_MIDDLEDOWN
            up_flag = MOUSEEVENTF_MIDDLEUP

        norm_x, norm_y = self._to_normalized_absolute(x, y)

        for _ in range(clicks):
            inp_down = INPUT(type=INPUT_MOUSE)
            inp_down.u.mi = MOUSEINPUT(
                dx=norm_x, dy=norm_y, mouseData=0,
                dwFlags=down_flag | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
                time=0, dwExtraInfo=None
            )
            inp_up = INPUT(type=INPUT_MOUSE)
            inp_up.u.mi = MOUSEINPUT(
                dx=norm_x, dy=norm_y, mouseData=0,
                dwFlags=up_flag | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
                time=0, dwExtraInfo=None
            )
            self._send_inputs([inp_down])
            time.sleep(0.03)
            self._send_inputs([inp_up])
            if clicks > 1:
                time.sleep(0.05)

        return True

    def drag_and_drop(self, start_x: int, start_y: int, end_x: int, end_y: int, speed_ms: int = 300) -> bool:
        """Performs a drag-and-drop gesture from start to destination."""
        self.move_to(start_x, start_y)
        time.sleep(0.05)

        norm_sx, norm_sy = self._to_normalized_absolute(start_x, start_y)
        inp_down = INPUT(type=INPUT_MOUSE)
        inp_down.u.mi = MOUSEINPUT(
            dx=norm_sx, dy=norm_sy, mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
            time=0, dwExtraInfo=None
        )
        self._send_inputs([inp_down])
        time.sleep(0.05)

        steps = max(5, int(speed_ms / 20))
        for i in range(1, steps + 1):
            t = i / steps
            cur_x = int(start_x + (end_x - start_x) * t)
            cur_y = int(start_y + (end_y - start_y) * t)
            norm_cx, norm_cy = self._to_normalized_absolute(cur_x, cur_y)
            inp_move = INPUT(type=INPUT_MOUSE)
            inp_move.u.mi = MOUSEINPUT(
                dx=norm_cx, dy=norm_cy, mouseData=0,
                dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
                time=0, dwExtraInfo=None
            )
            self._send_inputs([inp_move])
            time.sleep(0.02)

        norm_ex, norm_ey = self._to_normalized_absolute(end_x, end_y)
        inp_up = INPUT(type=INPUT_MOUSE)
        inp_up.u.mi = MOUSEINPUT(
            dx=norm_ex, dy=norm_ey, mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
            time=0, dwExtraInfo=None
        )
        self._send_inputs([inp_up])
        return True

    def scroll(self, direction: str = 'down', amount: int = 120, x: int | None = None, y: int | None = None) -> bool:
        """Simulates mouse wheel scrolling."""
        if x is not None and y is not None:
            self.move_to(x, y)

        scroll_amount = amount if direction.lower() == 'up' else -amount
        inp = INPUT(type=INPUT_MOUSE)
        inp.u.mi = MOUSEINPUT(
            dx=0, dy=0,
            mouseData=ctypes.c_ulong(scroll_amount).value,
            dwFlags=MOUSEEVENTF_WHEEL,
            time=0, dwExtraInfo=None
        )
        return self._send_inputs([inp])

    def type_text(self, text: str, delay_ms: int = 10) -> bool:
        """Types Unicode text directly into focused control, rendering floating keystroke HUD."""
        if self.hud:
            self.hud.notify_type(text)

        for char in text:
            code = ord(char)
            inp_down = INPUT(type=INPUT_KEYBOARD)
            inp_down.u.ki = KEYBDINPUT(
                wVk=0, wScan=code,
                dwFlags=KEYEVENTF_UNICODE,
                time=0, dwExtraInfo=None
            )
            inp_up = INPUT(type=INPUT_KEYBOARD)
            inp_up.u.ki = KEYBDINPUT(
                wVk=0, wScan=code,
                dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                time=0, dwExtraInfo=None
            )
            self._send_inputs([inp_down, inp_up])
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        return True

    def send_hotkey(self, keys: list[str]) -> bool:
        """Executes a key combination chord (e.g., ['ctrl', 'shift', 'p'])."""
        vk_codes = []
        for key in keys:
            key_clean = key.lower().strip()
            if key_clean in VK_MAPPINGS:
                vk_codes.append(VK_MAPPINGS[key_clean])
            elif len(key_clean) == 1:
                # Character key
                vk = user32.VkKeyScanW(ord(key_clean)) & 0xFF
                vk_codes.append(vk if vk != 0xFF else ord(key_clean.upper()))
            else:
                continue

        # Press keys down in order
        for vk in vk_codes:
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=None)
            self._send_inputs([inp])
            time.sleep(0.01)

        time.sleep(0.03)

        # Release keys in reverse order
        for vk in reversed(vk_codes):
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
            self._send_inputs([inp])
            time.sleep(0.01)

        return True

    def focus_window(self, title_keyword: str) -> dict:
        """Finds window matching keyword and brings it to foreground with ThreadInput handshake."""
        target_hwnd = None
        target_title = ""

        def enum_windows_callback(hwnd, extra):
            nonlocal target_hwnd, target_title
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if title_keyword.lower() in title.lower():
                        target_hwnd = hwnd
                        target_title = title
                        return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

        if not target_hwnd:
            return {"success": False, "error": f"No window found matching '{title_keyword}'"}

        # Bring window to foreground with focus handshake
        fore_hwnd = user32.GetForegroundWindow()
        if fore_hwnd != target_hwnd:
            fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
            app_thread = kernel32.GetCurrentThreadId()

            user32.AttachThreadInput(fore_thread, app_thread, True)
            user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(target_hwnd)
            user32.BringWindowToTop(target_hwnd)
            user32.AttachThreadInput(fore_thread, app_thread, False)

        time.sleep(0.1)
        return {"success": True, "window_title": target_title, "hwnd": target_hwnd}

    def get_active_window(self) -> dict:
        """Returns details about the currently focused application window."""
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {
                "success": True,
                "hwnd": 0,
                "title": "Windows Shell / Desktop",
                "pid": 0,
                "process_name": "explorer.exe",
                "rect": [0, 0, self.virt_w, self.virt_h],
                "dpi_scale": 1.0
            }

        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        process_name = "unknown"
        try:
            p = psutil.Process(pid.value)
            process_name = p.name()
        except Exception:
            pass

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

        dpi = 96
        try:
            dpi = user32.GetDpiForWindow(hwnd)
        except Exception:
            pass

        return {
            "success": True,
            "hwnd": hwnd,
            "title": title,
            "pid": pid.value,
            "process_name": process_name,
            "rect": [rect.left, rect.top, rect.right, rect.bottom],
            "dpi_scale": round(dpi / 96.0, 2)
        }
