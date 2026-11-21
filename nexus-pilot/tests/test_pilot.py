"""
NexusPilot - Automated Test Suite
Verifies Win32 input synthesizer, screen perception, UIA tree inspection,
hybrid background invocation, and safety guardian boundary enforcement.
"""

import sys
import os
import unittest

# Ensure server module is importable
SERVER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server")
sys.path.insert(0, SERVER_DIR)

from input_synthesizer import InputSynthesizer
from screen_capture import ScreenCaptureEngine
from uia_bridge import UIABridge
from safety_guard import SafetyGuardian, SafetyViolationError


class TestInputSynthesizer(unittest.TestCase):
    def setUp(self):
        self.synth = InputSynthesizer(enable_hud=False)

    def test_screen_metrics(self):
        self.assertGreater(self.synth.virt_w, 0)
        self.assertGreater(self.synth.virt_h, 0)
        pos = self.synth.get_cursor_position()
        self.assertEqual(len(pos), 2)
        print(f"[x] Virtual Screen: {self.synth.virt_w}x{self.synth.virt_h}, Cursor: {pos}")

    def test_active_window(self):
        active = self.synth.get_active_window()
        self.assertTrue(active.get("success"))
        self.assertIn("title", active)
        self.assertIn("hwnd", active)
        self.assertIn("dpi_scale", active)
        print(f"[x] Active Window: '{active.get('title')}' (PID: {active.get('pid')}, DPI: {active.get('dpi_scale')})")


class TestScreenCapture(unittest.TestCase):
    def setUp(self):
        self.cap = ScreenCaptureEngine()

    def test_capture_desktop(self):
        result = self.cap.capture(monitor_index=0, max_dimension=800)
        self.assertIn("image_base64", result)
        self.assertGreater(len(result["image_base64"]), 100)
        self.assertGreater(result["width"], 0)
        self.assertGreater(result["height"], 0)
        print(f"[x] Screen Capture Successful: {result['width']}x{result['height']} (Base64 length: {len(result['image_base64'])})")


class TestUIABridge(unittest.TestCase):
    def setUp(self):
        self.bridge = UIABridge()

    def test_inspect_active_tree(self):
        tree = self.bridge.inspect_ui_tree(max_depth=2, interactive_only=False)
        self.assertIn("elements", tree)
        print(f"[x] UIA Tree Inspection: Found {len(tree['elements'])} elements in '{tree.get('window_title')}'")

    def test_background_invocation_fallback_contract(self):
        # Non-existent or canvas query must return graceful boolean contract without crashing
        success, msg, elem = self.bridge.invoke_element_background("NonExistentButtonXYZ_123")
        self.assertFalse(success)
        self.assertIn("custom canvas", msg.lower())
        print(f"[x] Background Invocation Contract: Handled gracefully ({msg})")

    def test_background_text_setting_contract(self):
        success, msg = self.bridge.set_element_value_background("NonExistentInputXYZ_123", "Sample Text")
        self.assertFalse(success)
        self.assertIn("custom canvas", msg.lower())
        print(f"[x] Background Value Setting Contract: Handled gracefully ({msg})")

    def test_background_at_point_contract(self):
        success, msg = self.bridge.invoke_at_point_background(0, 0)
        self.assertIsInstance(success, bool)
        print(f"[x] Coordinate Background Invocation: Handled gracefully ({msg})")


class TestSafetyGuardian(unittest.TestCase):
    def setUp(self):
        self.guardian = SafetyGuardian()
        self.guardian.suppress_corner_check = True

    def test_high_risk_keyword_detection(self):
        is_risk, msg = self.guardian.check_high_risk_intent("DROP DATABASE production;")
        self.assertTrue(is_risk)
        self.assertIn("destructive", msg.lower())

        is_safe, _ = self.guardian.check_high_risk_intent("Click on Save Changes button")
        self.assertFalse(is_safe)
        print("[x] High-Risk Intent Classifier: Verified")

    def test_boundary_lock(self):
        self.guardian.locked_bounds = (100, 100, 500, 500)
        self.guardian.boundary_lock_enabled = True

        # Valid point within bounds
        self.guardian.validate_click_boundary(250, 250)

        # Out-of-bounds point must raise SafetyViolationError
        with self.assertRaises(SafetyViolationError):
            self.guardian.validate_click_boundary(800, 800)
        print("[x] Boundary Lock Enforcement: Verified")

    def test_window_target_validation(self):
        self.guardian.boundary_lock_enabled = True
        self.guardian.locked_hwnd = 12345

        # Matching HWND passes
        self.guardian.validate_window_target(12345, "Target App")

        # Different external HWND raises SafetyViolationError
        with self.assertRaises(SafetyViolationError):
            self.guardian.validate_window_target(99999, "External Slack/Discord")
        print("[x] Window Target Boundary Isolation: Verified")


class TestOverlayHUDSafety(unittest.TestCase):
    """Verifies the overlay HUD click-through safety invariant and active-on-demand lifecycle."""

    def test_enforce_click_through_contract(self):
        """Verify that _enforce_click_through is callable and doesn't crash."""
        from overlay_hud import VisualOverlayHUD
        hud = VisualOverlayHUD(enabled=False)
        # With no HWND, enforce should be a safe no-op
        hud._hwnd = None
        hud._enforce_click_through()
        print("[x] Overlay HUD _enforce_click_through: Safe no-op verified")

    def test_active_on_demand_initial_state(self):
        """Verify that the cursor HUD is inactive/hidden by default."""
        from overlay_hud import VisualOverlayHUD
        hud = VisualOverlayHUD(enabled=False)
        self.assertFalse(hud.is_active)
        self.assertEqual(len(hud.ripples), 0)
        self.assertEqual(hud.text_bubble_life, 0)
        print("[x] Overlay HUD Active-on-Demand: Idle by default verified")

    def test_close_destroys_window(self):
        """Verify close() transitions to is_running=False cleanly."""
        from overlay_hud import VisualOverlayHUD
        hud = VisualOverlayHUD(enabled=False)
        hud.close()
        self.assertFalse(hud.is_running)
        self.assertIsNone(hud._root)
        print("[x] Overlay HUD close: Clean destruction verified")


class TestApplicationLauncher(unittest.TestCase):
    """Verifies the application launcher resolution pipeline."""

    def setUp(self):
        self.synth = InputSynthesizer(enable_hud=False)

    def test_alias_resolution(self):
        """Verify well-known app aliases resolve to executable names."""
        aliases = self.synth._APP_ALIASES
        self.assertEqual(aliases.get("notepad"), "notepad.exe")
        self.assertEqual(aliases.get("chrome"), "chrome.exe")
        self.assertEqual(aliases.get("settings"), "ms-settings:")
        self.assertEqual(aliases.get("code"), "code.exe")
        print(f"[x] App Alias Map: {len(aliases)} aliases defined")

    def test_registry_app_paths_search(self):
        """Verify _find_in_app_paths does not crash and handles missing entries."""
        result = self.synth._find_in_app_paths("NONEXISTENT_APP_XYZ_12345")
        self.assertIsNone(result)
        print("[x] App Paths Registry Search: Graceful miss verified")

    def test_start_menu_shortcut_search(self):
        """Verify _find_start_menu_shortcut does not crash and handles missing entries."""
        result = self.synth._find_start_menu_shortcut("NONEXISTENT_APP_XYZ_12345")
        self.assertIsNone(result)
        print("[x] Start Menu Shortcut Search: Graceful miss verified")

    def test_launch_notepad(self):
        """Smoke-test launching Notepad (guaranteed to exist on Windows)."""
        result = self.synth.launch_application("notepad", wait_for_window_secs=1.0)
        self.assertTrue(result.get("success"), f"Failed to launch notepad: {result}")
        self.assertIn("resolved_path", result)
        print(f"[x] Launch Notepad: PID={result.get('pid')}, resolved={result.get('resolved_path')}")

        # Clean up: close the notepad we just opened
        if result.get("pid"):
            try:
                import psutil
                p = psutil.Process(result["pid"])
                p.kill()
                p.wait(timeout=1.0)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
