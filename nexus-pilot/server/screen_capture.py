"""
NexusPilot - High-Speed Screen Perception Engine
Supports multi-monitor desktop capture, targeted window cropping, and DWM frame bounds.
"""

import io
import base64
import ctypes
from ctypes import wintypes
import mss
from PIL import Image

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
DWMWA_EXTENDED_FRAME_BOUNDS = 9
PW_RENDERFULLCONTENT = 0x00000002


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]


class ScreenCaptureEngine:
    """Perception engine for sub-30ms full-screen and window-targeted captures."""

    def __init__(self):
        try:
            self.sct = getattr(mss, "MSS", mss.mss)()
        except Exception:
            self.sct = None

    def _get_window_bounds(self, hwnd: int) -> tuple[int, int, int, int] | None:
        """Retrieves exact visual window bounds using Desktop Window Manager (DWM)."""
        rect = RECT()
        res = dwmapi.DwmGetWindowAttribute(
            hwnd,
            DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect),
            ctypes.sizeof(rect)
        )
        if res == 0:
            return (rect.left, rect.top, rect.right, rect.bottom)

        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return (rect.left, rect.top, rect.right, rect.bottom)
        return None

    def _find_window_by_title(self, keyword: str) -> tuple[int, str] | None:
        """Finds visible window handle by title substring."""
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

    def capture(
        self,
        monitor_index: int = 0,
        window_title: str | None = None,
        crop_rect: list[int] | None = None,
        max_dimension: int | None = 1920
    ) -> dict:
        """
        Captures the screen or a specific application window.
        Returns base64 PNG along with dimensional and DPI metadata.
        """
        window_matched_title = None
        target_bbox = None

        if window_title:
            win_match = self._find_window_by_title(window_title)
            if win_match:
                hwnd, window_matched_title = win_match
                bounds = self._get_window_bounds(hwnd)
                if bounds:
                    left, top, right, bottom = bounds
                    target_bbox = {
                        "left": left,
                        "top": top,
                        "width": max(1, right - left),
                        "height": max(1, bottom - top)
                    }

        dpi = 96
        try:
            dpi = user32.GetDpiForSystem()
        except Exception:
            pass
        dpi_scale = round(dpi / 96.0, 2)

        try:
            if not self.sct:
                self.sct = mss.mss()

            if not target_bbox:
                monitors = self.sct.monitors
                idx = monitor_index if 0 <= monitor_index < len(monitors) else 0
                target_bbox = monitors[idx]

            sct_img = self.sct.grab(target_bbox)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            if crop_rect and len(crop_rect) == 4:
                x, y, w, h = crop_rect
                img = img.crop((x, y, x + w, y + h))

            orig_w, orig_h = img.size
            if max_dimension and (orig_w > max_dimension or orig_h > max_dimension):
                scale = max_dimension / max(orig_w, orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return {
                "success": True,
                "image_base64": img_b64,
                "width": img.width,
                "height": img.height,
                "original_width": orig_w,
                "original_height": orig_h,
                "dpi_scale": dpi_scale,
                "window_title": window_matched_title,
                "capture_bbox": [
                    target_bbox.get("left", 0),
                    target_bbox.get("top", 0),
                    target_bbox.get("width", orig_w),
                    target_bbox.get("height", orig_h)
                ]
            }
        except Exception as e:
            # Fallback for headless/background execution or locked workstation
            dummy_w, dummy_h = 1280, 720
            img = Image.new("RGB", (dummy_w, dummy_h), color=(30, 30, 30))
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return {
                "success": False,
                "warning": f"Screen grab unavailable in current display context: {str(e)}",
                "image_base64": img_b64,
                "width": dummy_w,
                "height": dummy_h,
                "original_width": dummy_w,
                "original_height": dummy_h,
                "dpi_scale": dpi_scale,
                "window_title": window_matched_title,
                "capture_bbox": [0, 0, dummy_w, dummy_h]
            }
