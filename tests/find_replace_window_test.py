# -*- coding: utf-8 -*-
"""Verify quiet success and persistent in-dialog issue reporting."""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from find_replace.workflow import new_result, record


class Visibility(object):
    Visible = "Visible"
    Collapsed = "Collapsed"


class TextControl(object):
    def __init__(self):
        self.Text = ""
        self.Visibility = Visibility.Collapsed


class Window(object):
    def __init__(self):
        self.result_panel = TextControl()
        self.result_summary = TextControl()
        self.result_details = TextControl()
        self.Height = 289
        self.closed = False

    def Close(self):
        self.closed = True


def load_present():
    system = types.ModuleType("System")
    windows = types.ModuleType("System.Windows")
    windows.Visibility = Visibility
    source = os.path.join(os.path.dirname(__file__), "..", "lib",
                          "find_replace", "window.py")
    spec = importlib.util.spec_from_file_location("window_under_test", source)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"System": system, "System.Windows": windows}):
        spec.loader.exec_module(module)
    return module.present


class WindowTests(unittest.TestCase):
    def test_clean_case_and_clean_rename_close_without_report(self):
        present = load_present()
        for action in ("UPPERCASE", "Rename"):
            window = Window()
            result = new_result(action)
            record(result, "changed", "A1")
            present(window, result)
            self.assertTrue(window.closed)
            self.assertEqual(Visibility.Collapsed, window.result_panel.Visibility)

    def test_no_change_rename_stays_open(self):
        window = Window()
        result = new_result("Rename")
        record(result, "unchanged", "A1")
        load_present()(window, result)
        self.assertFalse(window.closed)
        self.assertEqual(340, window.Height)
        self.assertIn("1 unchanged", window.result_summary.Text)

    def test_other_action_does_not_hide_prior_issue(self):
        present = load_present()
        window = Window()
        rename = new_result("Rename")
        record(rename, "skipped", "A1", "Number already in use")
        present(window, rename)
        case = new_result("UPPERCASE")
        record(case, "changed", "A2")
        present(window, case)
        self.assertFalse(window.closed)
        self.assertEqual(505, window.Height)
        self.assertIn("A1", window.result_details.Text)
        self.assertIn("UPPERCASE", window.result_summary.Text)

    def test_successful_rerun_clears_prior_issue_and_closes(self):
        present = load_present()
        window = Window()
        first = new_result("Rename")
        record(first, "skipped", "A1", "Conflict")
        present(window, first)
        second = new_result("Rename")
        record(second, "changed", "A1")
        present(window, second)
        self.assertTrue(window.closed)

    def test_resolved_prior_issue_closes_even_if_latest_run_is_unchanged(self):
        present = load_present()
        window = Window()
        first = new_result("Rename")
        record(first, "skipped", "A1", "Conflict")
        present(window, first)
        second = new_result("Rename")
        record(second, "unchanged", "A1")
        present(window, second)
        self.assertTrue(window.closed)


if __name__ == "__main__":
    unittest.main()
