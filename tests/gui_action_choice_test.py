"""Action Choice requests and results without WPF, Revit or model operations."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from GUI.dialogs.models import ActionChoice
from GUI.dialogs.choice_models import ChoiceState


class ChoiceStateTests(unittest.TestCase):
    def test_model_import_never_loads_a_host(self):
        code = "import sys; sys.path.insert(0, 'lib'); from GUI.dialogs.choice_models import ChoiceState; assert 'wpf' not in sys.modules; assert 'pyrevit' not in sys.modules"
        subprocess.check_call([sys.executable, '-B', '-c', code], cwd=ROOT)

    def test_command_activation_returns_exact_key_with_no_selection_step(self):
        key = object()
        state = ChoiceState([ActionChoice(key, 'Use active view')])
        result = state.choose('command', key)
        self.assertEqual('accept', result.action)
        self.assertIs(key, result.value['key'])
        self.assertEqual({'kind': 'command', 'key': key, 'checked': None}, result.value)

    def test_equal_lookup_keys_resolve_to_the_caller_owned_key(self):
        original = tuple(['caller', 1])
        lookup = tuple(['caller', 1])
        self.assertIsNot(original, lookup)
        state = ChoiceState([ActionChoice(original, 'Use caller key')],
                            default=('command', lookup))
        self.assertIs(original, state.default[1])
        self.assertIs(original, state.choose('command', lookup).value['key'])

    def test_rows_are_cloned_and_duplicate_labels_keep_separate_keys(self):
        rows = [ActionChoice('first', 'Same', 'First explanation'),
                ActionChoice('second', 'Same', 'Second explanation')]
        state = ChoiceState(iter(rows))
        state.choices[0].Label = 'Changed locally'
        state.choices[0].CanSelect = False
        self.assertEqual('Same', rows[0].Label)
        self.assertTrue(rows[0].CanSelect)
        self.assertEqual('second', state.choose('command', 'second').value['key'])

    def test_four_links_are_allowed_but_five_are_rejected(self):
        rows = [ActionChoice(index, 'Action ' + str(index)) for index in range(5)]
        self.assertEqual(4, len(ChoiceState(rows[:4]).choices))
        with self.assertRaises(ValueError):
            ChoiceState(rows)

    def test_invalid_command_identifiers_fail_before_host_loading(self):
        none_key = ActionChoice('placeholder', 'Invalid')
        none_key.Key = None
        for rows in ([none_key], [ActionChoice([], 'Unhashable')],
                     [ActionChoice('same', 'First'), ActionChoice('same', 'Second')]):
            with self.assertRaises(ValueError):
                ChoiceState(rows)

    def test_link_labels_must_be_nonblank_and_single_line(self):
        for label in (None, '', ' \t ', 'First\nSecond', 'Trailing\n', 'A\rB', 'A\vB', 42):
            with self.assertRaises(ValueError):
                ChoiceState([ActionChoice('key', label)])

    def test_standard_buttons_are_unique_validated_and_canonically_ordered(self):
        state = ChoiceState([], buttons=('close', 'cancel', 'retry', 'no', 'yes', 'ok'))
        self.assertEqual(('ok', 'yes', 'no', 'retry', 'cancel', 'close'), state.buttons)
        for buttons in (('save',), ('yes', 'yes'), ('Cancel',), (None,), ([],), None):
            with self.assertRaises(ValueError):
                ChoiceState([], buttons=buttons)

    def test_empty_dialog_has_a_close_action_instead_of_becoming_trapped(self):
        state = ChoiceState([], buttons=())
        self.assertEqual(('close',), state.buttons)
        self.assertEqual(('button', 'close'), state.default)
        self.assertEqual('close', state.choose('button', 'close').action)

    def test_no_enabled_action_requires_an_escape_route(self):
        rows = [ActionChoice('blocked', 'Unavailable', enabled=False)]
        with self.assertRaises(ValueError):
            ChoiceState(rows, buttons=(), allow_cancel=False)
        self.assertTrue(ChoiceState(rows, buttons=(), allow_cancel=True).can_cancel)
        state = ChoiceState(rows, buttons=('cancel',), allow_cancel=False)
        self.assertTrue(state.can_cancel)
        self.assertEqual('cancel', state.choose('button', 'cancel').action)
        empty = ChoiceState([], buttons=(), allow_cancel=False)
        self.assertEqual(('button', 'close'), empty.default)
        self.assertEqual('close', empty.choose('button', 'close').action)

    def test_default_skips_disabled_commands_then_uses_buttons(self):
        state = ChoiceState([ActionChoice('disabled', 'Disabled', enabled=False),
                             ActionChoice('enabled', 'Enabled')], buttons=('no', 'yes'))
        self.assertEqual(('command', 'enabled'), state.default)
        state = ChoiceState([ActionChoice('disabled', 'Disabled', enabled=False)], buttons=('no', 'yes'))
        self.assertEqual(('button', 'yes'), state.default)
        state = ChoiceState([ActionChoice('disabled', 'Disabled', enabled=False)], buttons=())
        self.assertIsNone(state.default)

    def test_caller_default_is_honored_only_for_an_available_target(self):
        rows = [ActionChoice('first', 'First'), ActionChoice('blocked', 'Blocked', enabled=False)]
        state = ChoiceState(rows, buttons=('yes', 'no'), default=('button', 'no'))
        self.assertEqual(('button', 'no'), state.default)
        for target in (('command', 'missing'), ('command', 'blocked'), ('button', 'retry'),
                       ('unknown', 'first'), ('command', []), ('command',), 'first', None):
            state = ChoiceState(rows, buttons=('yes',), default=target)
            self.assertEqual(('command', 'first'), state.default)

    def test_command_key_cannot_be_confused_with_a_standard_button(self):
        state = ChoiceState([ActionChoice('cancel', 'Perform action')],
                            buttons=('cancel',), default=('command', 'cancel'))
        self.assertEqual(('command', 'cancel'), state.default)
        self.assertEqual('accept', state.choose('command', 'cancel').action)
        self.assertEqual('cancel', state.choose('button', 'cancel').action)

    def test_unknown_and_disabled_targets_do_not_return_results(self):
        state = ChoiceState([ActionChoice('blocked', 'Blocked', enabled=False)], buttons=('cancel',))
        for kind, key in (('command', 'blocked'), ('command', 'missing'), ('command', []),
                          ('button', 'yes'), ('button', []), ('unknown', 'cancel')):
            self.assertIsNone(state.choose(kind, key))

    def test_no_cancel_and_close_remain_distinct_with_checkbox_snapshot(self):
        state = ChoiceState([], buttons=('no', 'cancel', 'close'),
                            checkbox_text='Apply to remaining views', checkbox_checked=True)
        no = state.choose('button', 'no')
        cancel = state.choose('button', 'cancel')
        close = state.choose('button', 'close')
        self.assertEqual(('accept', 'cancel', 'close'), (no.action, cancel.action, close.action))
        self.assertFalse(no.is_cancelled)
        self.assertTrue(cancel.is_cancelled)
        self.assertFalse(close.is_cancelled)
        for result, key in ((no, 'no'), (cancel, 'cancel'), (close, 'close')):
            self.assertEqual({'kind': 'button', 'key': key, 'checked': True}, result.value)
        state.checked = False
        self.assertTrue(no.value['checked'], 'Already returned results cannot change with the checkbox')
        self.assertFalse(state.choose('button', 'no').value['checked'])

    def test_checkbox_is_optional_and_never_gates_an_action(self):
        state = ChoiceState([ActionChoice('go', 'Continue')], checkbox_checked=True)
        self.assertIsNone(state.checked)
        self.assertIsNone(state.choose('command', 'go').value['checked'])
        state = ChoiceState([ActionChoice('go', 'Continue')], checkbox_text='Optional setting')
        self.assertFalse(state.checked)
        self.assertEqual('accept', state.choose('command', 'go').action)

    def test_dismissal_obeys_policy_and_preserves_close_escape_distinction(self):
        state = ChoiceState([ActionChoice('go', 'Continue')], buttons=(), allow_cancel=False)
        self.assertFalse(state.can_cancel)
        self.assertIsNone(state.dismiss('cancel'))
        self.assertIsNone(state.dismiss('close'))
        self.assertEqual('accept', state.choose('command', 'go').action)
        state = ChoiceState([], buttons=('yes',), checkbox_text='Option', checkbox_checked=True)
        self.assertTrue(state.can_cancel)
        self.assertEqual({'kind': 'button', 'key': 'cancel', 'checked': True}, state.dismiss().value)
        self.assertEqual('cancel', state.dismiss().action)
        self.assertEqual('close', state.dismiss('close').action)
        with self.assertRaises(ValueError):
            state.dismiss('no')

    def test_cancel_button_overrides_disabled_cancellation(self):
        state = ChoiceState([], buttons=('yes', 'cancel'), allow_cancel=False)
        self.assertTrue(state.can_cancel)
        self.assertEqual('cancel', state.dismiss().action)
        self.assertEqual('close', state.dismiss('close').action)

    def test_explicit_close_button_still_works_when_implicit_dismissal_is_disabled(self):
        state = ChoiceState([], buttons=('close',), allow_cancel=False)
        self.assertFalse(state.can_cancel)
        self.assertIsNone(state.dismiss('close'))
        self.assertEqual('close', state.choose('button', 'close').action)

    def test_each_standard_action_returns_its_exact_button_name(self):
        state = ChoiceState([], buttons=('ok', 'yes', 'no', 'retry', 'cancel', 'close'))
        for key in state.buttons:
            result = state.choose('button', key)
            self.assertEqual(key, result.value['key'])
            self.assertEqual('button', result.value['kind'])
            self.assertEqual(key if key in ('cancel', 'close') else 'accept', result.action)


if __name__ == '__main__':
    unittest.main()
