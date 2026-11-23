# MCP Tools Reference

Complete specification of all tools exposed by the **NexusPilot: Desktop** MCP server.

---

### Perception Tools

#### `capture_screen`
Captures high-resolution desktop or window screenshot.
- **Arguments**:
  - `monitor_index` (int, default `0`): Physical monitor index.
  - `window_title` (str, optional): Target window name for automatic cropping.
  - `crop_rect` (list[int], optional): `[x, y, width, height]` region of interest.
  - `max_dimension` (int, default `1920`): Maximum width/height to limit token size.
- **Returns**: `{ image_base64: str, width: int, height: int, dpi_scale: float }`

#### `inspect_ui_tree`
Traverses the Windows UI Automation accessibility tree.
- **Arguments**:
  - `window_title` (str, optional): Target window title.
  - `max_depth` (int, default `3`): Traversal depth.
  - `interactive_only` (bool, default `true`): Filters for interactive controls (Buttons, Text boxes, Menus).
- **Returns**: `{ elements: Array<{ name, control_type, id, rect, center }> }`

#### `find_element`
Searches for a specific control by name, label, or automation ID.
- **Arguments**:
  - `query` (str): Search keyword.
  - `window_title` (str, optional): Target window.
- **Returns**: `{ found: bool, element: { name, rect, center, ... } }`

---

### Actuation Tools

#### `click_element`
Deterministically clicks a control by semantic name or automation ID.
- **Arguments**:
  - `query` (str): Control name or ID.
  - `window_title` (str, optional): Target window title.
  - `button` (str, default `"left"`): `"left"`, `"right"`, or `"middle"`.
  - `clicks` (int, default `1`): Number of clicks.
- **Returns**: `{ success: bool, clicked_element: str, coordinates: [x, y] }`

#### `mouse_click`
Sends raw coordinate clicks via Win32 `SendInput`.
- **Arguments**: `x` (int), `y` (int), `button` (str), `clicks` (int).

#### `mouse_drag`
Performs a smoothed drag-and-drop gesture.
- **Arguments**: `start_x`, `start_y`, `end_x`, `end_y`, `speed_ms`.

#### `mouse_scroll`
Simulates mouse wheel scrolling.
- **Arguments**: `direction` (`"up"` or `"down"`), `amount` (int), `x` (optional), `y` (optional).

#### `send_keystrokes`
Sends Unicode text typing or modifier hotkey chords.
- **Arguments**:
  - `text` (str, optional): Unicode string to type.
  - `keys` (list[str], optional): Key combination (e.g. `['ctrl', 'shift', 'p']`).
  - `delay_ms` (int, default `10`): Inter-key delay in milliseconds.

#### `focus_window`
Restores and brings a window to the foreground with Win32 focus handshake.
- **Arguments**: `title_keyword` (str).

#### `launch_app`
Opens/launches a desktop application by friendly name, executable name, full path, or URI.
- **Arguments**:
  - `app_name` (str): Common name (e.g., `"notepad"`, `"chrome"`, `"code"`, `"settings"`), executable path, or URI (`"ms-settings:display"`).
  - `args` (list[str], optional): Command-line arguments.
  - `working_dir` (str, optional): Working directory for the process.
  - `wait_secs` (float, default `5.0`): Seconds to wait for the application's window to appear.
- **Returns**: `{ success: bool, app_name: str, resolved_path: str, pid: int, launched_via: str, window: { hwnd, title, pid, process_name } }`

#### `get_active_window`
Returns active window details (`title`, `hwnd`, `pid`, `process_name`, `rect`, `dpi_scale`).

---

### Safety & Health Tools

#### `set_safety_boundary`
Locks click actuation exclusively within target window bounds.
- **Arguments**: `enabled` (bool), `hwnd` (int, optional), `window_title` (str, optional).

#### `set_visual_hud`
Enables or disables the real-time visual pilot cursor overlay, click ripple animations, and keystroke HUD.
- **Arguments**: `enabled` (bool, default `true`).

#### `reset_safety_failsafe`
Clears the emergency stop flag so automation can resume.

#### `check_health`
Verifies screen metrics, cursor position, UIA COM status, and active safety guards.
