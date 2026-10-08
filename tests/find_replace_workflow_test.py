# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from find_replace.workflow import (case_value, details, new_result,
                                   record, rename_value, summary, unresolved)


class FindReplaceWorkflowTests(unittest.TestCase):
    def test_rename_uses_current_value_and_preserves_case_sensitive_find(self):
        self.assertEqual("A-A-S1", rename_value("A-S1", "", "", "A-", ""))
        self.assertEqual("A-View", rename_value("A-view", "view", "View", "", ""))
        self.assertEqual("A-view", rename_value("A-view", "VIEW", "Name", "", ""))

    def test_replace_without_find_is_rejected(self):
        with self.assertRaises(ValueError):
            rename_value("S1", "", "x", "", "")

    def test_case_and_result_details(self):
        self.assertEqual("SHEET", case_value("Sheet", "upper"))
        self.assertEqual("sheet", case_value("Sheet", "lower"))
        result = new_result("Rename")
        record(result, "changed", "A1")
        record(result, "skipped", "A2", "Number already in use")
        self.assertTrue(unresolved(result))
        self.assertIn("1 skipped", summary(result))
        self.assertIn("A2 - Number already in use", details(result))


if __name__ == "__main__":
    unittest.main()
