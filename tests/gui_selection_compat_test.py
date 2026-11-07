"""Legacy dictionary-selection contract through the shared dialog boundary."""
from __future__ import unicode_literals

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ROOT = os.environ.get('KLC_SELECTION_SOURCE_ROOT', PROJECT_ROOT)
sys.path.insert(0, os.path.join(SOURCE_ROOT, 'lib'))
import GUI
GUI.__path__.insert(0, os.path.join(PROJECT_ROOT, 'lib', 'GUI'))
from GUI import dialogs
from GUI.dialogs.models import DialogResult, SelectionState
from GUI.selection_compat import select_from_dict


class _Button(object):
    Content = 'Select'


class _Window(object):
    """Fake only the modal boundary; selection behavior uses the real model."""
    def __init__(self, items, options, interaction):
        self.state = SelectionState(items, options['multiple'], options['groups'])
        self.accept_button = _Button()
        self.result = DialogResult()
        self.interaction = interaction

    def update_checks(self):
        pass

    def ShowDialog(self):
        self.interaction(self)


class SelectionCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.original_factory = dialogs.create_selection
        self.calls = []
        self.interaction = lambda window: setattr(window, 'result', DialogResult('accept'))

        def create(title, items, **options):
            window = _Window(items, options, self.interaction)
            self.calls.append((title, options, window))
            return window

        dialogs.create_selection = create

    def tearDown(self):
        dialogs.create_selection = self.original_factory

    def test_default_selects_first_sorted_nonempty_key_and_preserves_values(self):
        first = object()
        self.assertEqual([first], select_from_dict({'Zulu': 2, 'Alpha': first, '': 3}, 'Tool'))
        window = self.calls[0][2]
        self.assertEqual(['Alpha', 'Zulu'], [item.Label for item in window.state.items])

    def test_list_input_deduplicates_and_returns_a_list(self):
        self.assertEqual(['Alpha'], select_from_dict(['Zulu', 'Alpha', 'Alpha'], 'Tool'))

    def test_explicit_empty_initial_selection_accepts_empty(self):
        self.assertEqual([], select_from_dict({'Alpha': 1}, 'Tool', initial_checked_names=[]))
        self.assertFalse(self.calls[0][1]['required'])

    def test_caption_version_and_group_options_reach_shared_window(self):
        select_from_dict({'Alpha': 1}, 'Tool_title', label='Pick_views: ',
                         button_name='Use_views', version='v2.3', SelectMultiple=False)
        title, options, window = self.calls[0]
        self.assertEqual('Tool_title', title)
        self.assertEqual('Pick_views', options['prompt'])
        self.assertEqual('v2.3', options['version'])
        self.assertEqual([], options['groups'])
        self.assertFalse(options['multiple'])
        self.assertEqual('Use__views', window.accept_button.Content)

    def test_cancel_discards_initial_or_edited_checks(self):
        self.interaction = lambda window: None
        self.assertEqual([], select_from_dict({'Alpha': 1}, 'Tool'))

    def test_single_selection_wraps_none_value_in_list(self):
        self.assertEqual([None], select_from_dict({'Alpha': None}, 'Tool', SelectMultiple=False))

    def test_explicit_initial_names_preserve_hidden_checks_and_visible_batches(self):
        def interact(window):
            window.state.query = 'Wood'
            window.state.set_visible_checked(True)
            self.assertEqual(['concrete', 'wood'], window.state.selected_values)
            window.state.set_visible_checked(False)
            window.result = DialogResult('accept')

        self.interaction = interact
        result = select_from_dict({'Concrete': 'concrete', 'Wood': 'wood'}, 'Tool',
                                  initial_checked_names=['Concrete'])
        self.assertEqual(['concrete'], result)

    def test_single_check_clears_hidden_selection(self):
        def interact(window):
            window.state.query = 'Wood'
            window.state.set_checked('Wood', True)
            window.result = DialogResult('accept')

        self.interaction = interact
        self.assertEqual(['wood'], select_from_dict({'Concrete': 'concrete', 'Wood': 'wood'},
                                                  'Tool', SelectMultiple=False))

    def test_legacy_multiple_initial_names_in_single_mode_remain_accepted(self):
        self.assertEqual([1, 2], select_from_dict({'Alpha': 1, 'Beta': 2}, 'Tool',
                                               SelectMultiple=False,
                                               initial_checked_names=['Beta', 'Alpha']))

    def test_empty_input_can_cancel_or_accept_without_invented_values(self):
        self.assertEqual([], select_from_dict({}, 'Tool'))


@unittest.skipUnless(os.environ.get('KLC_SELECTION_WPF') == '1', 'Requires the installed WPF/IronPython host')
class SelectionCompatibilityWpfTests(unittest.TestCase):
    def setUp(self):
        self.original_factory = dialogs.create_selection
        self.windows = []
        self.interaction = lambda window: window.accept_selection()

        def create(title, items, **options):
            from System.Windows import WindowStartupLocation
            window = self.original_factory(title, items, **options)
            window.WindowStartupLocation = WindowStartupLocation.Manual
            window.Left = -10000
            window.Top = -10000
            self.windows.append(window)

            def loaded(sender, args):
                self.interaction(window)

            window.Loaded += loaded
            return window

        dialogs.create_selection = create

    def tearDown(self):
        dialogs.create_selection = self.original_factory
        for window in self.windows:
            window.Close()

    def test_real_modal_accept_preserves_initial_checks_and_custom_caption(self):
        values = select_from_dict({'Alpha': 1, 'Beta': 2}, 'Actual window',
                                  button_name='Use_views', initial_checked_names=['Beta'])
        self.assertEqual([2], values)
        self.assertEqual('Use__views', self.windows[0].accept_button.Content)

    def test_real_single_select_accepts_a_none_value(self):
        self.assertEqual([None], select_from_dict({'Alpha': None}, 'Actual single', SelectMultiple=False))

    def test_real_close_returns_empty(self):
        self.interaction = lambda window: window.Close()
        self.assertEqual([], select_from_dict({'Alpha': 1}, 'Actual cancel'))

    def test_real_single_preserves_legacy_multiple_initial_checks(self):
        self.assertEqual([1, 2], select_from_dict({'Alpha': 1, 'Beta': 2}, 'Actual initial',
                                               SelectMultiple=False,
                                               initial_checked_names=['Alpha', 'Beta']))


if __name__ == '__main__':
    unittest.main()
