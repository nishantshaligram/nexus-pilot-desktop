"""
NexusPilot - Automated Test Suite
Verifies Win32 input synthesizer, screen perception, UIA tree inspection, and safety guardian.
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
        self.synth = InputSynthesizer()

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


if __name__ == "__main__":
    unittest.main()
