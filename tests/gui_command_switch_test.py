"""Command switch contracts, independent of WPF and Revit."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from GUI.dialogs.models import ActionChoice
from GUI.dialogs.switch_models import CommandSwitch, SwitchState


class CommandSwitchTests(unittest.TestCase):
    def test_importing_factory_does_not_load_wpf_or_pyrevit(self):
        code = "import sys; sys.path.insert(0, 'lib'); import GUI.dialogs as dialogs; import GUI.dialogs.command_switch_window; assert callable(dialogs.command_switch); assert 'wpf' not in sys.modules; assert 'pyrevit' not in sys.modules"
        subprocess.check_call([sys.executable, '-B', '-c', code], cwd=ROOT)

    def test_filter_preserves_order_and_separate_switch_state(self):
        original = CommandSwitch('pin', 'Pin Result', checked=True)
        state = SwitchState([ActionChoice('b', 'Second', 'Existing Views'),
                             ActionChoice('a', 'First', 'New Views')], [original])
        state.query = ' EXISTING '
        self.assertEqual(['b'], [row.Key for row in state.visible_choices])
        state.set_switch('pin', False)
        state.query = 'no match'
        self.assertEqual([], state.visible_choices)
        self.assertEqual([False], [row.IsChecked for row in state.switches])
        self.assertTrue(original.IsChecked, 'Editing must not mutate caller data')
        state.query = ''
        self.assertEqual(['b', 'a'], [row.Key for row in state.visible_choices])

    def test_enter_requires_command_focus_or_sole_enabled_search_match(self):
        state = SwitchState([ActionChoice('a', 'Active'),
                             ActionChoice('b', 'Choose'),
                             ActionChoice('c', 'Unavailable', enabled=False)])
        self.assertIsNone(state.enter_choice(search_focused=True))
        self.assertEqual('b', state.enter_choice(focused_key='b'))
        self.assertIsNone(state.enter_choice(focused_key='c'))
        state.query = 'Active'
        self.assertIsNone(state.enter_choice(), 'Enter while a toggle is focused must not run')
        self.assertEqual('a', state.enter_choice(search_focused=True))
        self.assertIsNone(state.enter_choice(focused_key='b'), 'A hidden command cannot run via Enter')

    def test_result_retains_stable_duplicate_label_keys_and_switch_values(self):
        state = SwitchState([ActionChoice('first', 'Same'), ActionChoice('second', 'Same')],
                            [CommandSwitch('include', 'Include', checked=True),
                             CommandSwitch('fixed', 'Fixed', checked=True, enabled=False)])
        state.set_switch('fixed', False)
        state.set_switch('include', False)
        result = state.result_for('second')
        self.assertEqual('accept', result.action)
        self.assertEqual({'command': 'second', 'switches': {'include': False, 'fixed': True}}, result.value)
        state.set_switch('include', True)
        self.assertFalse(result.value['switches']['include'], 'Returned states are a snapshot')

    def test_disabled_commands_cannot_produce_an_accepted_result(self):
        state = SwitchState([ActionChoice('disabled', 'Unavailable', enabled=False)])
        with self.assertRaises(ValueError):
            state.result_for('disabled')

    def test_empty_state_is_valid_and_never_implies_a_choice(self):
        state = SwitchState([])
        self.assertEqual([], state.visible_choices)
        self.assertIsNone(state.enter_choice(search_focused=True))

    def test_bad_keys_fail_before_loading_a_window(self):
        for choices, switches in (
                ([ActionChoice('a', 'A'), ActionChoice('a', 'B')], []),
                ([ActionChoice([], 'Unhashable')], []),
                ([], [CommandSwitch(None, 'None')]),
                ([], [CommandSwitch([], 'Unhashable')]),
                ([], [CommandSwitch('x', 'First'), CommandSwitch('x', 'Other')])):
            with self.assertRaises(ValueError):
                SwitchState(choices, switches)


if __name__ == '__main__':
    unittest.main()
