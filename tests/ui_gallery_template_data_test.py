"""Pure preview state and validation contracts for the template family."""
import unittest
from lib.ui_gallery.template_data import option_data, validate_options, review_rows, review_outcome


class TemplateDataTests(unittest.TestCase):
    def test_options_require_a_category_and_finite_number(self):
        self.assertIn('category', validate_options('', '10').lower())
        for text in ('bad', 'nan', 'inf', ''):
            self.assertTrue(validate_options('Structural', text))
        self.assertEqual('', validate_options('Structural', '-12.5'))

    def test_options_have_actual_empty_and_invalid_samples(self):
        self.assertEqual('', option_data('Empty')['category'])
        data = option_data('Error')
        self.assertTrue(validate_options(data['category'], data['offset']))

    def test_review_distinguishes_selected_ready_and_blocked_items(self):
        rows = review_rows('Normal')
        self.assertIn('1', review_outcome(rows))
        for row in rows:
            row.IsChecked = False
        self.assertIn('Select', review_outcome(rows))
        blocked = review_rows('Error')
        blocked[0].IsChecked = True
        self.assertIn('blocked', review_outcome(blocked).lower())

    def test_unknown_states_are_rejected(self):
        for factory in (option_data, review_rows):
            with self.assertRaises(ValueError):
                factory('unknown')
