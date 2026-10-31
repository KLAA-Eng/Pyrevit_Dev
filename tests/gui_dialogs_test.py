"""Host-free contracts for the opt-in dialog APIs."""
import os
import sys
import unittest
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib'))
from GUI.dialogs.models import ActionChoice, DialogResult, SelectionItem, SelectionGroup, SelectionState, validate_text


class DialogModelTests(unittest.TestCase):
    def test_package_import_does_not_load_wpf_or_pyrevit(self):
        code = "import sys; sys.path.insert(0, 'lib'); import GUI.dialogs; assert 'wpf' not in sys.modules; assert 'pyrevit' not in sys.modules"
        subprocess.check_call([sys.executable, '-B', '-c', code], cwd=os.path.dirname(os.path.dirname(__file__)))

    def test_duplicate_labels_keep_identity_and_hidden_checks(self):
        first, second = object(), object()
        rows = [SelectionItem('a', 'Same label', first, groups=('one',)),
                SelectionItem('b', 'Same label', second, groups=('two',)),
                SelectionItem('c', 'Blocked', None, enabled=False)]
        state = SelectionState(rows)
        state.set_checked('a', True)
        state.group = 'two'
        state.set_visible_checked(True)
        self.assertEqual([first, second], state.selected_values)
        self.assertFalse(rows[0].IsChecked, 'Caller-owned rows must remain untouched')
        state.group = None
        state.query = 'blocked'
        state.set_visible_checked(True)
        self.assertEqual([first, second], state.selected_values)

    def test_single_selection_is_exclusive_and_has_no_implicit_first(self):
        state = SelectionState([SelectionItem('a', 'A', 1), SelectionItem('b', 'B', 2)], multiple=False)
        self.assertEqual([], state.selected_values)
        state.set_checked('a', True)
        state.set_checked('b', True)
        self.assertEqual([2], state.selected_values)
        with self.assertRaises(ValueError):
            state.set_visible_checked(True)

    def test_none_descriptions_do_not_break_filtering(self):
        state = SelectionState([SelectionItem('a', 'Alpha', description=None), SelectionItem('b', 'Beta')])
        state.query = 'alp'
        self.assertEqual(['a'], [item.Key for item in state.visible_items])
        self.assertEqual('', ActionChoice('x', 'X', description=None).Description)

    def test_sheet_selector_accepts_an_all_label_override(self):
        import GUI.dialogs as dialogs
        calls = []
        original = dialogs.create_selection
        dialogs.create_selection = lambda title, items, **options: calls.append((title, options))
        try:
            dialogs.create_sheet_selector('Sheets', [])
            dialogs.create_sheet_selector('Sheets', [], all_label='Every Sheet', prompt='Pick')
        finally:
            dialogs.create_selection = original
        self.assertEqual(('All Sheets', 'Select Sheets'), (calls[0][1]['all_label'], calls[0][1]['prompt']))
        self.assertEqual(('Every Sheet', 'Pick'), (calls[1][1]['all_label'], calls[1][1]['prompt']))

    def test_search_covers_description_without_reordering_rows(self):
        state = SelectionState([SelectionItem('b', 'Z', 2, 'Type parameter'),
                                SelectionItem('a', 'A', 1, 'Instance parameter')])
        state.query = ' PARAMETER '
        self.assertEqual(['b', 'a'], [item.Key for item in state.visible_items])
        state.query = 'instance'
        self.assertEqual(['a'], [item.Key for item in state.visible_items])

    def test_visible_none_preserves_hidden_and_initial_checks(self):
        state = SelectionState([SelectionItem('a', 'A', 1, checked=True),
                                SelectionItem('b', 'B', 2, checked=True)])
        state.query = 'B'
        state.set_visible_checked(False)
        self.assertEqual([1], state.selected_values)

    def test_invalid_identifiers_and_ambiguous_initial_selection_fail(self):
        with self.assertRaises(ValueError):
            SelectionState([SelectionItem('a', 'A'), SelectionItem('a', 'Other')])
        with self.assertRaises(ValueError):
            SelectionState([], groups=[SelectionGroup(None, 'Invalid')])
        with self.assertRaises(ValueError):
            SelectionState([SelectionItem('a', 'A', checked=True),
                            SelectionItem('b', 'B', checked=True)], multiple=False)

    def test_disabled_initial_rows_are_never_selected(self):
        state = SelectionState([SelectionItem('x', 'Blocked', checked=True, enabled=False)])
        state.set_checked('x', True)
        self.assertEqual([], state.selected_values)

    def test_accepted_blank_no_and_cancel_are_distinct(self):
        blank = DialogResult('accept', '')
        self.assertFalse(blank.is_cancelled)
        self.assertEqual('', blank.value)
        self.assertFalse(DialogResult('no').is_cancelled)
        self.assertTrue(DialogResult().is_cancelled)

    def test_text_validation_checks_without_normalizing_value(self):
        self.assertIsNone(validate_text('', required=False))
        self.assertEqual('Enter a value.', validate_text('  ', required=True))
        seen = []
        self.assertEqual('Invalid', validate_text(' raw ', validator=lambda value: seen.append(value) or 'Invalid'))
        self.assertEqual([' raw '], seen)

    def test_invalid_message_configuration_fails_before_loading_wpf(self):
        from GUI.dialogs import create_message
        for options in ({'severity': 'mystery'},):
            with self.assertRaises(ValueError):
                create_message('Title', 'Message', **options)

    def test_invalid_action_configuration_fails_before_loading_wpf(self):
        from GUI.dialogs import create_choice
        for options in ({'severity': 'mystery'}, {'buttons': ('unknown',)},
                        {'help_uri': 'file:///local'}, {'help_uri': 'https://'},
                        {'help_uri': 'https://example.com:invalid'},
                        {'help_uri': 'https://exam ple.com'}, {'help_uri': object()},
                        {'buttons': (), 'allow_cancel': False}):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    create_choice('Title', [ActionChoice('blocked', 'Unavailable', enabled=False)], **options)


if __name__ == '__main__':
    unittest.main()
