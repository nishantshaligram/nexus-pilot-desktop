"""
NexusPilot - Visual Pilot Overlay HUD
Renders a transparent, click-through, top-most visual cursor, click animations,
pointing hand on interactive controls, and keystroke visualization.

DYNAMIC ACTIVE-ON-DEMAND LIFECYCLE:
- Idle State: Completely hidden. Nothing is rendered on screen. Zero visual footprint.
- Active State: Manifests smoothly when an action begins (move, click, type, drag).
- Dissolve State: When work is done, trailing ripples and bubbles complete,
  and the cursor vanishes cleanly after an inactivity cooldown.

SAFETY: The overlay window MUST remain click-through at all times.
WS_EX_TRANSPARENT is re-enforced every animation tick to prevent Tkinter
or Windows from silently stripping it, which would create a fullscreen
invisible input-blocking wall.
"""

import sys
import time
import math
import queue
import atexit
import threading
import tkinter as tk
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

# The exact set of extended style flags the overlay MUST maintain
_REQUIRED_EX_FLAGS = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# Cursor visual modes
MODE_ARROW = "arrow"
MODE_POINTER = "pointer"
MODE_IBEAM = "ibeam"


class VisualOverlayHUD:
    """Provides human-visible cursor animations and keystroke HUD.

    Implements a dynamic 'Active-on-Demand' lifecycle:
    - Inactive / Idle: The canvas renders nothing at all (pristine desktop).
    - Active: Awoken by any actuation action (glides, clicks, types).
    - Dissolve: Automatically vanishes after 1.2s of inactivity once ripples finish.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.msg_queue = queue.Queue()
        self.is_running = False
        self._thread = None
        self._root = None
        self._canvas = None
        self._hwnd = None  # Cached native window handle for style enforcement

        # Active-on-Demand Lifecycle State
        self.is_active = False           # False by default -> completely hidden
        self.last_activity = 0.0         # Timestamp of last user/agent action
        self.idle_timeout = 1.2          # Seconds of inactivity before cursor vanishes

        # Current visual coordinates
        self.cur_x = 100
        self.cur_y = 100
        self.target_x = 100
        self.target_y = 100
        self.cur_mode = MODE_ARROW

        # Animation state
        self.ripples = []  # list of {x, y, radius, max_radius, color}
        self.target_box = None  # {rect, label, life}
        self.typed_text = ""
        self.text_bubble_life = 0

        # Tick counter for periodic checks
        self._tick_count = 0

        # Register cleanup on interpreter shutdown
        atexit.register(self._atexit_cleanup)

        if self.enabled:
            self.start()

    def start(self):
        """Starts the overlay loop on a dedicated background thread."""
        if self._thread and self._thread.is_alive():
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._run_gui, daemon=True, name="NexusPilotHUD")
        self._thread.start()

    def _run_gui(self):
        try:
            self._root = tk.Tk()
            self._root.overrideredirect(True)
            self._root.config(bg="#010101")
            self._root.attributes("-transparentcolor", "#010101")

            # Get full virtual screen metrics
            vx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
            vy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
            vw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            vh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            if vw == 0: vw = user32.GetSystemMetrics(0)
            if vh == 0: vh = user32.GetSystemMetrics(1)

            self._root.geometry(f"{vw}x{vh}+{vx}+{vy}")

            # Force Tk to map the window so winfo_id() returns a valid HWND
            self._root.update_idletasks()

            # Resolve the actual top-level native HWND
            inner_id = self._root.winfo_id()
            self._hwnd = user32.GetParent(inner_id) or inner_id

            # Apply click-through flags BEFORE setting topmost
            self._enforce_click_through()

            # Set topmost AFTER extended styles are locked in
            self._root.attributes("-topmost", True)

            # Re-enforce one more time (Tk's -topmost may have reset GWL_EXSTYLE)
            self._enforce_click_through()

            self._canvas = tk.Canvas(
                self._root,
                width=vw,
                height=vh,
                bg="#010101",
                highlightthickness=0
            )
            self._canvas.pack(fill="both", expand=True)

            # Intercept WM_WINDOWPOSCHANGED to re-enforce styles when Windows moves us
            self._root.bind("<Configure>", lambda e: self._enforce_click_through())

            # Start animation tick
            self._root.after(16, self._on_tick)
            self._root.mainloop()
        except Exception:
            pass
        finally:
            self.is_running = False
            self._destroy_window()

    def _enforce_click_through(self):
        """Re-applies WS_EX_TRANSPARENT and related flags on the native HWND.

        This is the critical safety mechanism. Tkinter's internal event processing
        can silently strip WS_EX_TRANSPARENT when it handles window position changes,
        focus events, or attribute updates. If the flag is ever lost, the fullscreen
        overlay becomes an invisible input-blocking wall.
        """
        if not self._hwnd:
            return
        try:
            current_style = user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
            if (current_style & _REQUIRED_EX_FLAGS) != _REQUIRED_EX_FLAGS:
                user32.SetWindowLongW(
                    self._hwnd,
                    GWL_EXSTYLE,
                    current_style | _REQUIRED_EX_FLAGS
                )
        except Exception:
            pass

    def _on_tick(self):
        if not self.is_running or not self._root:
            return

        self._tick_count += 1
        now = time.monotonic()

        # Re-enforce click-through every tick (cheap: one GetWindowLongW + bitwise AND)
        self._enforce_click_through()

        # Process incoming message queue
        while not self.msg_queue.empty():
            try:
                msg = self.msg_queue.get_nowait()
                cmd = msg[0]

                if cmd == "action_start":
                    _, sx, sy = msg
                    if not self.is_active:
                        self.cur_x = sx
                        self.cur_y = sy
                        self.target_x = sx
                        self.target_y = sy
                    self.is_active = True
                    self.last_activity = now

                elif cmd == "action_end":
                    self.last_activity = now

                elif cmd == "hide":
                    self.is_active = False
                    self.ripples.clear()
                    self.target_box = None
                    self.text_bubble_life = 0

                elif cmd == "move":
                    _, tx, ty, mode = msg
                    if not self.is_active:
                        self.cur_x = tx
                        self.cur_y = ty
                    self.target_x = tx
                    self.target_y = ty
                    self.cur_mode = mode
                    self.is_active = True
                    self.last_activity = now

                elif cmd == "click":
                    _, cx, cy, button = msg
                    self.cur_x = cx
                    self.cur_y = cy
                    self.cur_mode = MODE_POINTER
                    self.ripples.append({
                        "x": cx, "y": cy, "r": 8, "max_r": 48,
                        "color": "#00F0FF" if button == "left" else "#FF0077"
                    })
                    self.is_active = True
                    self.last_activity = now

                elif cmd == "type":
                    _, text = msg
                    self.cur_mode = MODE_IBEAM
                    self.typed_text = (self.typed_text + text)[-30:]
                    self.text_bubble_life = 60  # ~1 second
                    self.is_active = True
                    self.last_activity = now

                elif cmd == "lock_element":
                    _, rect, label = msg
                    self.target_box = {
                        "rect": rect, "label": label, "life": 45
                    }
                    self.is_active = True
                    self.last_activity = now

                elif cmd == "set_mode":
                    _, mode = msg
                    self.cur_mode = mode
                    self.last_activity = now

            except queue.Empty:
                break

        # Check Active-on-Demand lifecycle state
        has_pending_animations = bool(
            self.ripples or 
            (self.target_box and self.target_box["life"] > 0) or 
            self.text_bubble_life > 0
        )

        if self.is_active:
            # Check if idle timeout has expired and animations have finished
            if (now - self.last_activity > self.idle_timeout) and not has_pending_animations:
                self.is_active = False

        if self.is_active:
            # Smooth glide cursor toward target while active
            dx = self.target_x - self.cur_x
            dy = self.target_y - self.cur_y
            dist = math.hypot(dx, dy)
            if dist > 1:
                step = max(3.0, dist * 0.35)
                self.cur_x += (dx / dist) * step
                self.cur_y += (dy / dist) * step
            else:
                self.cur_x = self.target_x
                self.cur_y = self.target_y

        self._render()

        if self._root and self.is_running:
            self._root.after(16, self._on_tick)

    def _render(self):
        if not self._canvas:
            return

        self._canvas.delete("all")

        # When idle, draw nothing! Zero artifacts on user's screen.
        if not self.is_active:
            return

        x, y = int(self.cur_x), int(self.cur_y)

        # 1. Render Element Target Lock Box if active
        if self.target_box and self.target_box["life"] > 0:
            tb = self.target_box
            bx, by, bw, bh = tb["rect"]
            self.target_box["life"] -= 1
            # Bounding box
            self._canvas.create_rectangle(
                bx, by, bx + bw, by + bh,
                outline="#00F0FF", width=2, dash=(6, 4)
            )
            if tb.get("label"):
                self._canvas.create_rectangle(
                    bx, max(0, by - 22), bx + len(tb["label"]) * 8 + 14, by,
                    fill="#0F172A", outline="#00F0FF", width=1
                )
                self._canvas.create_text(
                    bx + 7, max(11, by - 11),
                    text=f"AI: {tb['label']}",
                    anchor="w",
                    fill="#38BDF8",
                    font=("Consolas", 9, "bold")
                )

        # 2. Render Click Ripples
        active_ripples = []
        for rip in self.ripples:
            rip["r"] += 3
            r = rip["r"]
            w = max(1, int(3 * (1 - r / rip["max_r"])))
            self._canvas.create_oval(
                rip["x"] - r, rip["y"] - r, rip["x"] + r, rip["y"] + r,
                outline=rip["color"], width=w
            )
            # Center click flash dot
            if r < 18:
                self._canvas.create_oval(
                    rip["x"] - 4, rip["y"] - 4, rip["x"] + 4, rip["y"] + 4,
                    fill="#FFFFFF", outline=rip["color"]
                )
            if rip["r"] < rip["max_r"]:
                active_ripples.append(rip)
        self.ripples = active_ripples

        # 3. Render Cursor according to Mode
        if self.cur_mode == MODE_POINTER:
            self._draw_pointer_hand(x, y)
        elif self.cur_mode == MODE_IBEAM:
            self._draw_text_ibeam(x, y)
        else:
            self._draw_arrow(x, y)

        # 4. Render Floating Keystroke Pill if typing
        if self.text_bubble_life > 0:
            self.text_bubble_life -= 1
            disp = self.typed_text
            pill_w = max(80, len(disp) * 8 + 26)
            pill_h = 24
            px = x + 16
            py = y + 24
            # Background pill
            self._canvas.create_rectangle(
                px, py, px + pill_w, py + pill_h,
                fill="#0F172A", outline="#38BDF8", width=1.5
            )
            self._canvas.create_text(
                px + 10, py + 12,
                text=f"⌨ {disp}",
                anchor="w",
                fill="#F8FAFC",
                font=("Segoe UI", 9, "bold")
            )

    def _draw_arrow(self, x: int, y: int):
        # Ethereal glow polygon
        coords = [
            x, y,
            x, y + 24,
            x + 6, y + 19,
            x + 11, y + 29,
            x + 15, y + 27,
            x + 10, y + 17,
            x + 18, y + 17
        ]
        # Neon outer shadow
        self._canvas.create_polygon(
            [c + 2 for c in coords],
            fill="#0284C7", outline="#00F0FF", width=2
        )
        # Main Arrow Body
        self._canvas.create_polygon(
            coords,
            fill="#FFFFFF", outline="#0F172A", width=1.5
        )

    def _draw_pointer_hand(self, x: int, y: int):
        # Outstretched pointing hand icon
        self._canvas.create_oval(
            x - 3, y - 3, x + 3, y + 3,
            fill="#FF0077", outline="#FFFFFF", width=1.5
        )
        # Hand silhouette
        hand_pts = [
            x, y,
            x + 4, y - 2,
            x + 8, y + 10,
            x + 15, y + 13,
            x + 16, y + 20,
            x + 13, y + 26,
            x + 4, y + 26,
            x - 1, y + 18,
            x, y + 10
        ]
        self._canvas.create_polygon(
            [c + 1 for c in hand_pts],
            fill="#0284C7", outline="#00F0FF", width=2
        )
        self._canvas.create_polygon(
            hand_pts,
            fill="#F8FAFC", outline="#0F172A", width=1.5
        )

    def _draw_text_ibeam(self, x: int, y: int):
        # Upper & Lower serif brackets + vertical stem
        self._canvas.create_line(x - 5, y - 10, x + 5, y - 10, fill="#38BDF8", width=2.5)
        self._canvas.create_line(x, y - 10, x, y + 10, fill="#FFFFFF", width=2)
        self._canvas.create_line(x - 5, y + 10, x + 5, y + 10, fill="#38BDF8", width=2.5)

    # Public API called by InputSynthesizer / MCP tools
    def notify_action_start(self, x: int, y: int):
        """Signals start of an actuation sequence at (x, y). Awakens the HUD."""
        if not self.enabled: return
        self.msg_queue.put(("action_start", x, y))

    def notify_action_end(self):
        """Signals completion of an actuation sequence. Starts the idle countdown."""
        if not self.enabled: return
        self.msg_queue.put(("action_end",))

    def notify_hide(self):
        """Immediately hides the visual cursor overlay."""
        if not self.enabled: return
        self.msg_queue.put(("hide",))

    def notify_move(self, x: int, y: int, is_interactive: bool = False):
        if not self.enabled: return
        mode = MODE_POINTER if is_interactive else MODE_ARROW
        self.msg_queue.put(("move", x, y, mode))

    def notify_click(self, x: int, y: int, button: str = "left"):
        if not self.enabled: return
        self.msg_queue.put(("click", x, y, button))

    def notify_type(self, text: str):
        if not self.enabled: return
        self.msg_queue.put(("type", text))

    def notify_lock_element(self, rect: list[int], label: str):
        if not self.enabled: return
        self.msg_queue.put(("lock_element", rect, label))

    def notify_mode(self, mode: str):
        if not self.enabled: return
        self.msg_queue.put(("set_mode", mode))

    def _destroy_window(self):
        """Safely tears down the Tk window and releases all resources."""
        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass
            self._root = None
        self._canvas = None
        self._hwnd = None

    def _atexit_cleanup(self):
        """Ensures the overlay is torn down when the interpreter exits."""
        self.is_running = False
        self._destroy_window()

    def close(self):
        """Shuts down the overlay HUD cleanly."""
        self.is_running = False
        if self._root:
            try:
                self._root.after(0, self._destroy_window)
            except Exception:
                self._destroy_window()
