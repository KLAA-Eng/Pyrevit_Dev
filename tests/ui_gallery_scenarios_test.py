"""Behavior checks for fictional Gallery data and local-only interactions."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from ui_gallery.scenarios import (STATES, alert_message, filtered_items,
                                  parse_offset, recall_items, rename_samples,
                                  review_items, selection_items, set_checked)


class GalleryScenarioTests(unittest.TestCase):
    def test_each_state_has_independent_rows_and_empty_has_no_rows(self):
        self.assertEqual([], selection_items('Empty'))
        first = selection_items()
        second = selection_items()
        first[0].IsChecked = False
        self.assertTrue(second[0].IsChecked)
        self.assertGreater(len(selection_items('Long content')), len(second))
        for state in STATES:
            self.assertIsInstance(alert_message(state), str)

    def test_filter_and_selection_keep_hidden_rows_intact(self):
        rows = selection_items()
        visible, error = filtered_items(rows, 'Foundation')
        self.assertFalse(error)
        self.assertEqual(['S101 - Foundation Plan'], [row.Name for row in visible])
        set_checked(visible, True)
        self.assertTrue(rows[0].IsChecked)
        self.assertTrue(rows[2].IsChecked)

    def test_recall_search_checks_values_and_reports_invalid_regex(self):
        rows = recall_items()
        visible, error = filtered_items(rows, 'Existing')
        self.assertEqual('Phase Created', visible[0].Name)
        self.assertFalse(error)
        visible, error = filtered_items(rows, '[', regex=True)
        self.assertEqual(rows, visible)
        self.assertIn('invalid regular expression', error)

    def test_sample_rename_rejects_invalid_request_without_modifying_input(self):
        names = ['Office', 'Studio']
        result, error = rename_samples(names, replace='North')
        self.assertEqual(names, result)
        self.assertIn('Find', error)
        result, error = rename_samples(names, find='Office', replace='Studio')
        self.assertEqual(names, result)
        self.assertIn('collide', error)
        self.assertEqual(['Office', 'Studio'], names)

    def test_sample_rename_and_case_conversion_return_new_names(self):
        names, error = rename_samples(['Office'], 'Office', 'Studio', 'A-', '-R1')
        self.assertEqual(['A-Studio-R1'], names)
        self.assertFalse(error)
        self.assertEqual(['OFFICE'], rename_samples(['Office'], action='Uppercase')[0])

    def test_offset_rejects_malformed_and_nonfinite_complete_input(self):
        self.assertEqual(-2.5, parse_offset('-2.5'))
        for value in ('', '1.2.3', 'nan', 'inf', None):
            with self.assertRaises(ValueError):
                parse_offset(value)

    def test_unknown_states_and_actions_fail_explicitly(self):
        with self.assertRaises(ValueError):
            selection_items('Unknown')
        with self.assertRaises(ValueError):
            rename_samples(['A'], action='Delete')

    def test_optional_model_checker_rows_have_real_grid_fields_and_local_status(self):
        self.assertEqual([], review_items('Empty'))
        rows = review_items('Normal')
        self.assertEqual(['Critical', 'Error', 'Warning', 'Information'],
                         [row.Severity for row in rows])
        self.assertEqual('Open', rows[0].Status)
        rows[0].Status = 'Accepted'
        self.assertEqual('Open', review_items('Normal')[0].Status)
        for field in ('Check', 'Category', 'Member', 'End', 'Level', 'Offset',
                      'Measurement', 'Value', 'Related', 'Status', 'Reason'):
            self.assertTrue(hasattr(rows[0], field), field)


if __name__ == '__main__':
    unittest.main()
